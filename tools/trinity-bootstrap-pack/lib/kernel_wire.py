"""Wire the trinity_v2 kernel into a freshly-installed target.

Modes:
  symlink — symlink `.ai/cli`, `.ai/rituals` from source to target (default)
  copy    — deep copy from source to target (standalone, snapshot)
  none    — no wiring; operator wires manually

A `submodule` mode is reserved for v1.2 (requires target to be a git repo
and orchestration around `git submodule add`).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


KernelWireMode = Literal["symlink", "copy", "none", "submodule"]


# Source paths under trinity_v2 root that must be wired into the target.
# Each entry: (relative-path-under-source, target-relative-path).
KERNEL_BINDINGS: tuple[tuple[str, str], ...] = (
    (".ai/cli", ".ai/cli"),
    (".ai/rituals", ".ai/rituals"),
)

# Files copied verbatim (always copy regardless of wire mode) — required for
# kernel to function. e.g. requirements.txt is small and operator-friendly to
# have at .ai/requirements.txt.
KERNEL_COPY_ALWAYS: tuple[tuple[str, str], ...] = (
    (".ai/requirements.txt", ".ai/requirements.txt"),
)


class KernelWireError(Exception):
    def __init__(self, message: str, exit_code: int = 60):
        super().__init__(message)
        self.exit_code = exit_code


@dataclass
class KernelWireResult:
    mode: str
    source_root: str
    bindings: list[tuple[str, str]]
    warnings: list[str]


def wire_kernel(
    *,
    mode: KernelWireMode,
    source_root: Path,
    target: Path,
    dry_run: bool,
    force: bool,
) -> KernelWireResult:
    """Materialise the kernel inside ``target`` according to ``mode``."""
    if mode == "none":
        return KernelWireResult(
            mode="none",
            source_root=str(source_root),
            bindings=[],
            warnings=["kernel wiring skipped (--with-kernel none)"],
        )

    if mode == "submodule":
        # v1.1 reserves this mode but does not implement it; clean refusal
        # is better than a half-wired attempt.
        raise KernelWireError(
            "--with-kernel submodule is not implemented in v1.1 "
            "(planned for v1.2). Use --with-kernel symlink or copy.",
            exit_code=30,
        )

    if mode not in {"symlink", "copy"}:
        raise KernelWireError(f"unknown kernel wire mode: {mode}", exit_code=30)

    if not source_root.is_dir():
        raise KernelWireError(f"source root not found: {source_root}", exit_code=40)

    # Sanity: source must actually contain a kernel
    for src_rel, _ in KERNEL_BINDINGS:
        src = source_root / src_rel
        if not src.exists():
            raise KernelWireError(
                f"source root missing required kernel path: {src_rel} "
                f"(looked in {source_root})",
                exit_code=40,
            )

    bindings_done: list[tuple[str, str]] = []
    warnings: list[str] = []

    for src_rel, dst_rel in KERNEL_BINDINGS:
        src = source_root / src_rel
        dst = target / dst_rel

        if dst.exists() or dst.is_symlink():
            if not force:
                warnings.append(
                    f"skipped (exists; --force to overwrite): {dst_rel}"
                )
                continue
            if not dry_run:
                if dst.is_dir() and not dst.is_symlink():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()

        if dry_run:
            bindings_done.append((src_rel, dst_rel))
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        if mode == "symlink":
            dst.symlink_to(src.resolve())
        else:  # copy
            shutil.copytree(src, dst, symlinks=False)
        bindings_done.append((src_rel, dst_rel))

    # Files in KERNEL_COPY_ALWAYS are copied (not symlinked) regardless of mode,
    # because they're small + operator-friendly to mutate per-project (e.g.
    # adding extra pip deps for sibling tools).
    for src_rel, dst_rel in KERNEL_COPY_ALWAYS:
        src = source_root / src_rel
        dst = target / dst_rel
        if not src.is_file():
            warnings.append(f"skipped (source missing): {src_rel}")
            continue
        if dst.exists() and not force:
            warnings.append(f"skipped (exists; --force to overwrite): {dst_rel}")
            continue
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        bindings_done.append((src_rel, dst_rel))

    return KernelWireResult(
        mode=mode,
        source_root=str(source_root.resolve()),
        bindings=bindings_done,
        warnings=warnings,
    )
