"""Trinity bootstrap pack installer (python core).

Invoked by install.sh (bash entry). Pure function-call surface for tests.

Exit codes:
  0  — success (install or dry-run)
  10 — preflight failure (env/python/git/sqlite)
  20 — target unsafe (non-empty without --force; self-install without flag)
  30 — detection refused (unknown / unsupported mode)
  40 — pack source missing or corrupt
  50 — unexpected error
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

from .detector import detect
from .kernel_wire import KernelWireError, wire_kernel
from .pack_manifest import PACK_VERSION, build_manifest
from .receipt import build_receipt, write_receipt


PACK_DIR_NAME = "pack"


class InstallError(Exception):
    def __init__(self, message: str, exit_code: int):
        super().__init__(message)
        self.exit_code = exit_code


def _resolve_source_root(installer_file: Path) -> Path:
    return installer_file.resolve().parent.parent.parent.parent


def _resolve_pack_dir(installer_file: Path) -> Path:
    return installer_file.resolve().parent.parent / PACK_DIR_NAME


def _target_is_non_empty(target: Path) -> bool:
    if not target.exists():
        return False
    if not target.is_dir():
        return True
    return any(target.iterdir())


def run_install(
    *,
    target: Path,
    mode_override: str | None,
    dry_run: bool,
    force: bool,
    allow_self_install: bool,
    project_name: str | None,
    installer_file: Path,
    kernel_wire_mode: str = "symlink",
) -> dict:
    target = target.resolve()
    pack_dir = _resolve_pack_dir(installer_file)
    source_root = _resolve_source_root(installer_file)

    if not pack_dir.is_dir():
        raise InstallError(f"pack source missing: {pack_dir}", exit_code=40)

    detected = detect(target, source_root)
    mode = mode_override or detected.mode

    if detected.is_self() and not allow_self_install:
        msg = (
            f"self-install refused: target {target} appears to be trinity_v2 itself "
            f"(reasons: {', '.join(detected.reasons)}). "
            f"Pass --allow-self-install to override."
        )
        raise InstallError(msg, exit_code=20)

    if not dry_run and _target_is_non_empty(target) and not force:
        if mode == "greenfield":
            raise InstallError(
                f"target {target} is non-empty; use --force to overwrite or pick an empty dir",
                exit_code=20,
            )

    manifest = build_manifest(pack_dir)
    files_installed: list[str] = []
    warnings: list[str] = []

    if mode == "greenfield":
        warnings_extra = _install_greenfield(
            pack_dir=pack_dir,
            target=target,
            manifest=manifest,
            dry_run=dry_run,
            project_name=project_name or target.name,
            files_installed=files_installed,
        )
        warnings.extend(warnings_extra)
    elif mode == "upgrade-v1":
        warnings_extra = _install_upgrade_v1(
            pack_dir=pack_dir,
            target=target,
            manifest=manifest,
            dry_run=dry_run,
            project_name=project_name or target.name,
            files_installed=files_installed,
        )
        warnings.extend(warnings_extra)
    elif mode == "upgrade-v2":
        warnings_extra = _install_upgrade_v2(
            pack_dir=pack_dir,
            target=target,
            manifest=manifest,
            dry_run=dry_run,
            project_name=project_name or target.name,
            files_installed=files_installed,
        )
        warnings.extend(warnings_extra)
    elif mode == "self":
        warnings.append("self-install: only emitting receipt; kernel files left untouched")
    else:
        raise InstallError(f"unknown mode: {mode}", exit_code=30)

    # Phase 2 — kernel wiring. Source root = trinity_v2 (where install.sh lives).
    kernel_wire_info: dict = {"mode": kernel_wire_mode, "source_root": None, "bindings": []}
    if mode != "self":
        source_root = _resolve_source_root(installer_file)
        try:
            wire_result = wire_kernel(
                mode=kernel_wire_mode,  # type: ignore[arg-type]
                source_root=source_root,
                target=target,
                dry_run=dry_run,
                force=force,
            )
        except KernelWireError as kw_exc:
            raise InstallError(str(kw_exc), exit_code=kw_exc.exit_code) from kw_exc
        kernel_wire_info = {
            "mode": wire_result.mode,
            "source_root": wire_result.source_root,
            "bindings": [{"src": s, "dst": d} for s, d in wire_result.bindings],
        }
        warnings.extend(wire_result.warnings)

    receipt = build_receipt(
        mode=mode,
        target=target,
        dry_run=dry_run,
        files_installed=files_installed,
        warnings=warnings + [f"detected={detected.mode}"] + list(detected.reasons),
        kernel_wire=kernel_wire_info,
    )

    if not dry_run:
        write_receipt(receipt, target)
    else:
        # For dry-run, write receipt anyway so smoke tests can grep it,
        # but mark dry_run=True in the JSON body.
        write_receipt(receipt, target)

    return asdict(receipt)


def _install_greenfield(
    *,
    pack_dir: Path,
    target: Path,
    manifest,
    dry_run: bool,
    project_name: str,
    files_installed: list[str],
) -> list[str]:
    target.mkdir(parents=True, exist_ok=True)
    for entry in manifest:
        src = pack_dir / entry.relpath
        dst_rel = _template_path(entry.relpath)
        dst = target / dst_rel
        _copy_one(src, dst, dry_run=dry_run, project_name=project_name)
        files_installed.append(dst_rel)
    return []


def _install_upgrade_v1(
    *,
    pack_dir: Path,
    target: Path,
    manifest,
    dry_run: bool,
    project_name: str,
    files_installed: list[str],
) -> list[str]:
    warnings: list[str] = []
    target.mkdir(parents=True, exist_ok=True)
    for entry in manifest:
        src = pack_dir / entry.relpath
        dst_rel = _template_path(entry.relpath)
        dst = target / dst_rel
        if dst.exists():
            warnings.append(f"skipped (exists, upgrade-v1 keeps existing): {dst_rel}")
            continue
        _copy_one(src, dst, dry_run=dry_run, project_name=project_name)
        files_installed.append(dst_rel)
    return warnings


def _install_upgrade_v2(
    *,
    pack_dir: Path,
    target: Path,
    manifest,
    dry_run: bool,
    project_name: str,
    files_installed: list[str],
) -> list[str]:
    warnings: list[str] = ["upgrade-v2: only laying down NEW files; existing kernel paths preserved"]
    target.mkdir(parents=True, exist_ok=True)
    for entry in manifest:
        src = pack_dir / entry.relpath
        dst_rel = _template_path(entry.relpath)
        dst = target / dst_rel
        if dst.exists():
            warnings.append(f"skipped (v2 preserves existing): {dst_rel}")
            continue
        _copy_one(src, dst, dry_run=dry_run, project_name=project_name)
        files_installed.append(dst_rel)
    return warnings


def _template_path(relpath: str) -> str:
    if relpath.startswith("templates/"):
        stripped = relpath[len("templates/"):]
        if stripped.endswith(".template"):
            return stripped[: -len(".template")]
        return stripped
    return relpath


def _copy_one(src: Path, dst: Path, *, dry_run: bool, project_name: str) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    raw = src.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        dst.write_bytes(raw)
        return
    rendered = text.replace("{{PROJECT_NAME}}", project_name)
    dst.write_text(rendered, encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trinity-bootstrap-pack",
        description="Install Trinity OS into a target project directory.",
    )
    # Target: positional OR keyword. Positional preferred (`install.sh ~/code/x`).
    p.add_argument("target_pos", nargs="?", type=Path, help="target project root (positional)")
    p.add_argument(
        "--target",
        dest="target_kw",
        type=Path,
        help="target project root (keyword form; equivalent to positional)",
    )
    p.add_argument(
        "--mode",
        choices=["greenfield", "upgrade-v1", "upgrade-v2", "self", "auto"],
        default="auto",
        help="install mode (default: auto-detect)",
    )
    p.add_argument(
        "--with-kernel",
        choices=["symlink", "copy", "submodule", "none"],
        default="symlink",
        help="wire trinity_v2 kernel into target (default: symlink). "
        "Use `none` for bootstrap-layer-only install.",
    )
    p.add_argument("--no-kernel", action="store_true", help="alias for --with-kernel none")
    p.add_argument(
        "--ref",
        default=None,
        help="git ref of trinity_v2 to use (informational at install time; "
        "honoured by bootstrap.sh upstream).",
    )
    p.add_argument("--dry-run", action="store_true", help="plan only; do not write target")
    p.add_argument("--force", action="store_true", help="overwrite non-empty target")
    p.add_argument(
        "--allow-self-install",
        action="store_true",
        help="permit install into trinity_v2 itself (refused by default)",
    )
    p.add_argument("--project-name", default=None, help="project name for template substitution")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Resolve target: positional wins over keyword if both present, but error
    # if neither was supplied.
    target = args.target_pos or args.target_kw
    if target is None:
        parser.error("a target directory is required (positional or --target)")

    installer_file = Path(__file__).resolve()
    mode_override = None if args.mode == "auto" else args.mode

    kernel_wire_mode = "none" if args.no_kernel else args.with_kernel

    try:
        receipt = run_install(
            target=target,
            mode_override=mode_override,
            dry_run=args.dry_run,
            force=args.force,
            allow_self_install=args.allow_self_install,
            project_name=args.project_name,
            installer_file=installer_file,
            kernel_wire_mode=kernel_wire_mode,
        )
    except InstallError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover — defensive
        print(f"UNEXPECTED ERROR: {exc!r}", file=sys.stderr)
        return 50

    print(f"OK [{receipt['mode']}{' dry-run' if receipt['dry_run'] else ''}] "
          f"{receipt['file_count']} files -> {receipt['target']}")
    print(f"  receipt: {Path(receipt['target']) / '.trinity-install-receipt.json'}")
    print(f"  pack:    {PACK_VERSION}")
    kw = receipt.get("kernel_wire") or {}
    if kw.get("mode") and kw["mode"] != "none":
        print(f"  kernel:  {kw['mode']} <- {kw.get('source_root', '?')}")
        next_target = receipt["target"]
        print()
        print("Next:")
        print(f"  cd {next_target}")
        print(f"  pip install -r .ai/requirements.txt   # one-time")
        print(f"  bash .ai/cli/ai lll                   # smoke")
    elif kw.get("mode") == "none":
        print(f"  kernel:  not wired (--with-kernel none); wire manually")
    return 0


if __name__ == "__main__":
    sys.exit(main())
