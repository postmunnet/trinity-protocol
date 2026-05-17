"""Trinity Tool Capability Registry — Phase 6 loader/validator.

Spec ref: docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md §2-§3
         docs/specs/01_TOOL_CONTRACT.md §16.1 (tools.yaml schema)
PRD ref: trinity_organ_refactor_prd.md §Phase 6

Loads `.ai/tools.yaml` (authoritative tool registry) and
`.ai/tools.capabilities.yaml` (per-tool capability axes) from a project
root and FAILS CLOSED on any inconsistency. Article XXV — spec wins over
runtime; unknown authority is denied (Article XVI). Loader does NOT
invoke tools, decide verdicts, mutate policy, or write audit (Article
III, IV, XX).

Validation rules (FAIL CLOSED — all are deterministic, no LLM):
  V1: every tools.yaml entry has the 8 required attrs per
      01_TOOL_CONTRACT.md §16.1
  V2: bidirectional 1:1 — every capabilities.yaml entry has a matching
      tools.yaml entry and vice versa
  V3: every required_/optional_capabilities token is in the closed
      CAPABILITY_VOCABULARY (spec §2)
  V4: audit.append and ddd.decide are NEVER in any tool's
      required_capabilities (kernel-only / human-only invariants per
      spec §2.1)
  V5: default_tier_requirement is in {HOT, WARM, COLD}
  Vocab: if capabilities.yaml declares capability_vocabulary it must
      match CAPABILITY_VOCABULARY exactly (no silent drift)

This module is import-time safe — no I/O or side effects until
`load_registry` is explicitly invoked (Article XX — Passive Core).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Tuple

import yaml


# Closed capability vocabulary, mirroring spec §2 table.
CAPABILITY_VOCABULARY: FrozenSet[str] = frozenset({
    "fs.read", "fs.write", "fs.delete",
    "net.outbound", "net.allowlist",
    "proc.exec", "proc.spawn",
    "audit.read", "audit.append",
    "policy.read",
    "ddd.propose", "ddd.decide",
    "tool.invoke",
})

# §2.1 NEVER-granted invariants — must never appear in required_capabilities.
NEVER_GRANTED_CAPABILITIES: FrozenSet[str] = frozenset({
    "audit.append",
    "ddd.decide",
})

# 8 required attrs per tools.yaml entry (01_TOOL_CONTRACT.md §16.1).
REQUIRED_TOOL_YAML_ATTRS: Tuple[str, ...] = (
    "name",
    "description",
    "path",
    "bin",
    "schema_version",
    "contract_version",
    "capabilities",
    "policy_default",
)

VALID_TIERS: FrozenSet[str] = frozenset({"HOT", "WARM", "COLD"})


class ToolRegistryError(Exception):
    """Base for tool registry failures."""


class UnknownToolError(ToolRegistryError):
    """Caller asked for a tool that is not declared in the registry."""


class RegistryValidationError(ToolRegistryError):
    """Registry failed one of the V1-V5 / vocabulary invariants."""


@dataclass(frozen=True)
class ToolCapabilityRecord:
    """Joined view of one tool across tools.yaml + tools.capabilities.yaml."""

    name: str
    required_capabilities: Tuple[str, ...]
    optional_capabilities: Tuple[str, ...]
    default_tier_requirement: str
    notes: str
    # Joined from tools.yaml.
    description: str
    path: str
    bin: str
    schema_version: str
    contract_version: str
    declared_capabilities: Tuple[str, ...]
    policy_default: str


class ToolRegistry:
    """In-memory registry produced by `load_registry`. Read-only."""

    def __init__(self, records: Dict[str, ToolCapabilityRecord]):
        self._records: Dict[str, ToolCapabilityRecord] = dict(records)

    def lookup(self, tool_name: str) -> Optional[ToolCapabilityRecord]:
        return self._records.get(tool_name)

    def require(self, tool_name: str) -> ToolCapabilityRecord:
        rec = self._records.get(tool_name)
        if rec is None:
            raise UnknownToolError(
                f"tool {tool_name!r} is not declared in the registry "
                "(see .ai/tools.yaml + .ai/tools.capabilities.yaml)"
            )
        return rec

    def names(self) -> Tuple[str, ...]:
        return tuple(sorted(self._records.keys()))

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._records

    def __len__(self) -> int:
        return len(self._records)


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise RegistryValidationError(f"missing registry file: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise RegistryValidationError(
            f"registry file {path} must be a top-level mapping; got {type(data).__name__}"
        )
    return data


def _validate_vocabulary(caps_doc: dict) -> None:
    vocab_section = caps_doc.get("capability_vocabulary")
    if not vocab_section:
        return  # vocabulary block is optional; absent means "trust the spec"
    if not isinstance(vocab_section, dict):
        raise RegistryValidationError(
            "capabilities.yaml: 'capability_vocabulary' must be a mapping"
        )
    declared = {
        item
        for family in vocab_section.values()
        for item in (family or [])
    }
    if declared != CAPABILITY_VOCABULARY:
        missing = CAPABILITY_VOCABULARY - declared
        extra = declared - CAPABILITY_VOCABULARY
        raise RegistryValidationError(
            "capabilities.yaml vocabulary drift from spec §2 — "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )


def _validate_tools_yaml(tools_doc: dict) -> Dict[str, dict]:
    tools_list = tools_doc.get("tools") or []
    if not isinstance(tools_list, list):
        raise RegistryValidationError("tools.yaml: 'tools' must be a list")
    indexed: Dict[str, dict] = {}
    for entry in tools_list:
        if not isinstance(entry, dict):
            raise RegistryValidationError(
                f"tools.yaml: non-dict entry encountered: {entry!r}"
            )
        missing = [a for a in REQUIRED_TOOL_YAML_ATTRS if a not in entry]
        if missing:
            name = entry.get("name", "<unnamed>")
            raise RegistryValidationError(
                f"V1 violation: tools.yaml entry {name!r} missing required "
                f"attrs {missing}"
            )
        name = entry["name"]
        if name in indexed:
            raise RegistryValidationError(
                f"tools.yaml: duplicate tool name {name!r}"
            )
        indexed[name] = entry
    return indexed


def _validate_capabilities_yaml(caps_doc: dict) -> Dict[str, dict]:
    caps_list = caps_doc.get("tools") or []
    if not isinstance(caps_list, list):
        raise RegistryValidationError(
            "tools.capabilities.yaml: 'tools' must be a list"
        )
    indexed: Dict[str, dict] = {}
    for entry in caps_list:
        if not isinstance(entry, dict):
            raise RegistryValidationError(
                f"tools.capabilities.yaml: non-dict entry: {entry!r}"
            )
        if "name" not in entry:
            raise RegistryValidationError(
                f"tools.capabilities.yaml: entry missing 'name': {entry!r}"
            )
        name = entry["name"]
        if name in indexed:
            raise RegistryValidationError(
                f"tools.capabilities.yaml: duplicate tool name {name!r}"
            )
        indexed[name] = entry
    return indexed


def _cross_check_names(
    tools_by_name: Dict[str, dict], caps_by_name: Dict[str, dict]
) -> None:
    only_in_tools = set(tools_by_name) - set(caps_by_name)
    only_in_caps = set(caps_by_name) - set(tools_by_name)
    if only_in_tools or only_in_caps:
        raise RegistryValidationError(
            "V2 violation: tools.yaml and tools.capabilities.yaml must declare "
            f"the same set of tools — only_in_tools.yaml={sorted(only_in_tools)} "
            f"only_in_capabilities.yaml={sorted(only_in_caps)}"
        )


def _build_record(
    name: str, cap_entry: dict, tools_entry: dict
) -> ToolCapabilityRecord:
    req = tuple(cap_entry.get("required_capabilities") or [])
    opt = tuple(cap_entry.get("optional_capabilities") or [])

    # V3 — closed vocabulary.
    for token in (*req, *opt):
        if token not in CAPABILITY_VOCABULARY:
            raise RegistryValidationError(
                f"V3 violation: tool {name!r} declares capability {token!r} "
                "not in CAPABILITY_VOCABULARY (spec §2)"
            )

    # V4 — kernel-only / human-only invariants.
    forbidden = set(req) & NEVER_GRANTED_CAPABILITIES
    if forbidden:
        raise RegistryValidationError(
            f"V4 violation: tool {name!r} requires kernel-only/human-only "
            f"capabilities {sorted(forbidden)} (spec §2.1 NEVER-granted rows)"
        )

    # V5 — tier.
    tier = cap_entry.get("default_tier_requirement", "WARM")
    if tier not in VALID_TIERS:
        raise RegistryValidationError(
            f"V5 violation: tool {name!r} default_tier_requirement {tier!r} "
            f"not in {sorted(VALID_TIERS)}"
        )

    return ToolCapabilityRecord(
        name=name,
        required_capabilities=req,
        optional_capabilities=opt,
        default_tier_requirement=tier,
        notes=str(cap_entry.get("notes", "")),
        description=str(tools_entry["description"]),
        path=str(tools_entry["path"]),
        bin=str(tools_entry["bin"]),
        schema_version=str(tools_entry["schema_version"]),
        contract_version=str(tools_entry["contract_version"]),
        declared_capabilities=tuple(tools_entry.get("capabilities") or []),
        policy_default=str(tools_entry["policy_default"]),
    )


def load_registry(project_root: Path) -> ToolRegistry:
    """Load and validate the Trinity tool capability registry.

    Reads `<project_root>/.ai/tools.yaml` and
    `<project_root>/.ai/tools.capabilities.yaml` and FAILS CLOSED on any
    V1-V5 / vocabulary violation. Returns a frozen `ToolRegistry`.
    """
    project_root = Path(project_root)
    tools_doc = _load_yaml(project_root / ".ai" / "tools.yaml")
    caps_doc = _load_yaml(project_root / ".ai" / "tools.capabilities.yaml")

    _validate_vocabulary(caps_doc)
    tools_by_name = _validate_tools_yaml(tools_doc)
    caps_by_name = _validate_capabilities_yaml(caps_doc)
    _cross_check_names(tools_by_name, caps_by_name)

    records: Dict[str, ToolCapabilityRecord] = {}
    for name, cap_entry in caps_by_name.items():
        records[name] = _build_record(name, cap_entry, tools_by_name[name])
    return ToolRegistry(records)
