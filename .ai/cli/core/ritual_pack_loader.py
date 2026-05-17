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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        raise PackNotFoundError(f"ritual pack directory not found: {pack_dir}")
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
