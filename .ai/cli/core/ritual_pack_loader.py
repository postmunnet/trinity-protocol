"""Kernel-side ritual pack loader.

Foundation module that any kernel command can import to load + validate
a `.ai/rituals/<r>/` template pack at runtime. This is the bridge between
the static template-pack artifacts that landed in commit `f92b1ee` and
the kernel rituals that will eventually honor them (Article XII.5
empirical ratification path).

Authority:
  - Ritual Constitution v1.1-rc Articles I/IV/V/VI (template pack model)
  - Constitution v1.0 Article XVI (Least Authority — declared capability)
  - Constitution v1.0 Article XX (Passive Core — explicit invocation only)

Distinct from `cli.core.llm_call.load_ritual_pack` which is the AGENT-side
loader (used by sibling agents to read their own prompt scaffolding). This
kernel-side loader adds: schema validation against `.ai/schemas/ritual_*`,
state-transition guard, audit-event accessor, required-artifacts check.

Public API:
  - load_pack(ritual, rituals_root=...) -> RitualPack
  - validate_pack_schemas(pack, schemas_root=...) -> None
  - check_transition_allowed(pack, current_state, next_state) -> bool
  - required_audit_events(pack) -> list[str]
  - required_artifacts_for_check(pack) -> list[str]
  - assert_transition_allowed(pack, current_state, next_state) -> None
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

_log = logging.getLogger(__name__)


class RitualPackError(Exception):
    """Base class for ritual_pack_loader errors."""


class PackNotFoundError(RitualPackError):
    """The requested ritual pack directory or a required file is missing."""


class SchemaValidationError(RitualPackError):
    """A pack file failed JSON-schema validation against the base schemas."""


class StateTransitionError(RitualPackError):
    """An attempted ritual transition is not allowed by the pack's contract."""


_PACK_FILES = (
    "ritual.contract.json",
    "context.schema.json",
    "check.template.json",
    "write.template.md",
)
_DEFAULT_RITUALS_ROOT = Path(".ai/rituals")
_DEFAULT_SCHEMAS_ROOT = Path(".ai/schemas")


def _find_git_root(start: Path) -> Optional[Path]:
    """Walk up from `start` (after resolving symlinks) to find the git root."""
    try:
        real = start.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    for p in [real, *real.parents]:
        if (p / ".git").exists():
            return p
    return None


def _self_heal_pack_files(pack_dir: Path) -> List[str]:
    """Restore pack files that drifted from git HEAD.

    `.ai/rituals/**` is in `forbidden_paths` for Trinity rituals, but external
    tooling (sibling CLIs, editor plugins, sync scripts) occasionally writes
    to these files anyway — typically leaving `allowed_current_states` in a
    wrong state. Detect via `git diff HEAD` and restore from the committed
    blob. No-op when:
      - pack_dir is not inside a git repo
      - a pack file is untracked (new ritual not yet committed)
      - the file is already clean

    Returns the list of file names that were restored (empty on no-op).
    Logs a single WARNING when one or more files are restored.

    Trade-off (accepted, session ritual-pack-self-heal-land): an operator who
    deliberately edits a tracked ritual pack file in the working tree will see
    it reverted to HEAD on the next load — commit the edit first.
    """
    repo_root = _find_git_root(pack_dir)
    if repo_root is None:
        return []
    try:
        pack_real = pack_dir.resolve(strict=True)
    except (OSError, RuntimeError):
        return []
    # Fast path (P1, 2026-06-10): one `git diff --quiet` for the whole pack
    # dir replaces 4 per-file `git show` spawns on the ~99% clean path.
    # Dirty or any git hiccup falls through to the existing full loop.
    try:
        rel_dir = pack_real.relative_to(repo_root)
        clean = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--quiet", "HEAD", "--",
             rel_dir.as_posix()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if clean:
            return []
    except (ValueError, OSError):
        pass
    restored: List[str] = []
    for fname in _PACK_FILES:
        fpath = pack_real / fname
        if not fpath.is_file():
            continue
        try:
            rel = fpath.relative_to(repo_root)
        except ValueError:
            continue
        try:
            head_bytes = subprocess.check_output(
                ["git", "-C", str(repo_root), "show", f"HEAD:{rel.as_posix()}"],
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # File not in HEAD (new ritual / uncommitted) or git missing — skip
            continue
        try:
            current = fpath.read_bytes()
        except OSError:
            continue
        if current != head_bytes:
            try:
                fpath.write_bytes(head_bytes)
                restored.append(fname)
            except OSError as e:
                _log.warning(
                    "ritual_pack_loader: drift in %s/%s could not be restored: %s",
                    pack_real.name, fname, e,
                )
    if restored:
        _log.warning(
            "ritual_pack_loader: drift detected in pack %r — restored from git HEAD: %s",
            pack_real.name, ", ".join(restored),
        )
    return restored


@dataclass
class RitualPack:
    ritual: str
    contract: Dict[str, Any]
    context_schema: Dict[str, Any]
    check_template: Dict[str, Any]
    write_template: str
    root: Path


def load_pack(
    ritual: str,
    rituals_root: Path = _DEFAULT_RITUALS_ROOT,
) -> RitualPack:
    """Load the 4-file template pack for `ritual`.

    Raises PackNotFoundError if the directory or any required file is
    missing. Does NOT validate against base schemas — call
    `validate_pack_schemas` for that (separate concern).
    """
    pack_dir = Path(rituals_root) / ritual
    if not pack_dir.is_dir():
        # Thin-client fallback (mirrors TemplateLoader.from_ssot, retro-0061):
        # a thin-linked project strips its vendored `.ai/rituals`, so the
        # caller-supplied project-local pack is absent. Fall back to the
        # kernel's own packs (this file lives at <kernel>/.ai/cli/core/, so
        # parents[2] is the kernel `.ai`). Without this the ritual runs
        # un-audited — the caller swallows PackNotFoundError and the audit
        # chain never appends (retro-0062, silent integrity hole).
        kernel_pack = Path(__file__).resolve().parents[2] / "rituals" / ritual
        if kernel_pack.is_dir():
            pack_dir = kernel_pack
    if not pack_dir.is_dir():
        raise PackNotFoundError(f"ritual pack directory not found: {pack_dir}")
    # Defensive: external writers (sibling CLIs, editor plugins, sync scripts)
    # occasionally mutate `.ai/rituals/<r>/{ritual.contract,check.template}.json`
    # despite the path being in forbidden_paths. Restore from git HEAD before
    # parsing so a downstream State/Transition check sees the canonical pack.
    _self_heal_pack_files(pack_dir)
    files: Dict[str, Path] = {}
    for fname in _PACK_FILES:
        fpath = pack_dir / fname
        if not fpath.is_file():
            raise PackNotFoundError(
                f"required pack file missing: {fpath}"
            )
        files[fname] = fpath
    try:
        contract = json.loads(files["ritual.contract.json"].read_text(encoding="utf-8"))
        context_schema = json.loads(files["context.schema.json"].read_text(encoding="utf-8"))
        check_template = json.loads(files["check.template.json"].read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RitualPackError(
            f"pack JSON parse failed for ritual {ritual!r}: {e.msg} at pos {e.pos}"
        ) from e
    write_template = files["write.template.md"].read_text(encoding="utf-8")

    # Cross-check the ritual field for parity (contract + context_schema
    # both should name `ritual` matching the directory).
    contract_ritual = contract.get("ritual")
    context_ritual = context_schema.get("ritual")
    if contract_ritual != ritual:
        raise RitualPackError(
            f"contract.ritual {contract_ritual!r} does not match dir {ritual!r}"
        )
    if context_ritual != ritual:
        raise RitualPackError(
            f"context_schema.ritual {context_ritual!r} does not match dir {ritual!r}"
        )

    return RitualPack(
        ritual=ritual,
        contract=contract,
        context_schema=context_schema,
        check_template=check_template,
        write_template=write_template,
        root=pack_dir,
    )


def validate_pack_schemas(
    pack: RitualPack,
    schemas_root: Path = _DEFAULT_SCHEMAS_ROOT,
) -> None:
    """Validate the pack's JSON files against the base schemas at
    `.ai/schemas/ritual_*.schema.json`. Raises SchemaValidationError on any
    deviation; raises ImportError if `jsonschema` library is missing.
    """
    try:
        import jsonschema
    except ImportError as e:
        raise ImportError(
            "jsonschema library required for pack schema validation; "
            "install via `pip install jsonschema`"
        ) from e

    schema_files = {
        "contract": schemas_root / "ritual_contract.schema.json",
        "check": schemas_root / "ritual_check_template.schema.json",
        "context": schemas_root / "ritual_context.schema.json",
    }
    schemas: Dict[str, Dict[str, Any]] = {}
    for kind, path in schema_files.items():
        if not path.is_file():
            raise SchemaValidationError(
                f"base schema missing: {path}"
            )
        schemas[kind] = json.loads(path.read_text(encoding="utf-8"))

    pairs = (
        ("ritual.contract.json", pack.contract, schemas["contract"]),
        ("context.schema.json", pack.context_schema, schemas["context"]),
        ("check.template.json", pack.check_template, schemas["check"]),
    )
    for label, instance, schema in pairs:
        try:
            jsonschema.validate(instance, schema)
        except jsonschema.ValidationError as e:
            raise SchemaValidationError(
                f"pack {pack.ritual!r} file {label!r} failed schema "
                f"validation: {e.message} (at {list(e.absolute_path)})"
            ) from e


def required_audit_events(pack: RitualPack) -> List[str]:
    """Return the audit-event names declared in ritual.contract.json."""
    events = pack.contract.get("audit_events", [])
    if not isinstance(events, list):
        raise RitualPackError(
            f"pack {pack.ritual!r}.audit_events must be a list; "
            f"got {type(events).__name__}"
        )
    return list(events)


def required_artifacts_for_check(pack: RitualPack) -> List[str]:
    """Return required_artifacts from check.template.json."""
    artifacts = pack.check_template.get("required_artifacts", [])
    if not isinstance(artifacts, list):
        raise RitualPackError(
            f"pack {pack.ritual!r}.check_template.required_artifacts must "
            f"be a list; got {type(artifacts).__name__}"
        )
    return list(artifacts)


def check_transition_allowed(
    pack: RitualPack,
    current_state: str,
    next_state: str,
) -> bool:
    """Return True if `current_state → next_state` is allowed per
    `ritual.contract.json.{allowed_current_states, allowed_next_states}`.

    Does NOT raise; for an error-raising variant use `assert_transition_allowed`.
    """
    allowed_from = pack.contract.get("allowed_current_states", [])
    allowed_to = pack.contract.get("allowed_next_states", [])
    return current_state in allowed_from and next_state in allowed_to


def assert_transition_allowed(
    pack: RitualPack,
    current_state: str,
    next_state: str,
) -> None:
    """Raise StateTransitionError if the transition is not allowed."""
    allowed_from = pack.contract.get("allowed_current_states", [])
    allowed_to = pack.contract.get("allowed_next_states", [])
    if current_state not in allowed_from:
        raise StateTransitionError(
            f"ritual {pack.ritual!r}: current_state {current_state!r} not in "
            f"allowed_current_states {allowed_from!r}"
        )
    if next_state not in allowed_to:
        raise StateTransitionError(
            f"ritual {pack.ritual!r}: next_state {next_state!r} not in "
            f"allowed_next_states {allowed_to!r}"
        )


__all__ = [
    "load_pack",
    "validate_pack_schemas",
    "check_transition_allowed",
    "assert_transition_allowed",
    "required_audit_events",
    "required_artifacts_for_check",
    "RitualPack",
    "RitualPackError",
    "PackNotFoundError",
    "SchemaValidationError",
    "StateTransitionError",
]
