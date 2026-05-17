"""Phase 6 tool capability registry tests.

Covers V1-V5 + vocabulary drift + UnknownToolError + happy path.
Spec: docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md §2-§3.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from cli.core.tool_registry import (
    CAPABILITY_VOCABULARY,
    NEVER_GRANTED_CAPABILITIES,
    REQUIRED_TOOL_YAML_ATTRS,
    RegistryValidationError,
    ToolCapabilityRecord,
    ToolRegistry,
    UnknownToolError,
    load_registry,
)


# ─── fixture builders ────────────────────────────────────────────────


def _full_tool_entry(name: str, **overrides: Any) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        "name": name,
        "description": f"{name} description",
        "path": f"/fake/{name}",
        "bin": f"/fake/{name}/bin",
        "schema_version": "1",
        "contract_version": "1.0",
        "capabilities": ["x"],
        "policy_default": "safe",
    }
    e.update(overrides)
    return e


def _full_cap_entry(name: str, **overrides: Any) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        "name": name,
        "required_capabilities": ["fs.read"],
        "optional_capabilities": [],
        "default_tier_requirement": "WARM",
        "notes": "",
    }
    e.update(overrides)
    return e


def _write_tools_yaml(root: Path, entries: List[Dict[str, Any]]) -> Path:
    p = root / ".ai" / "tools.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump({"version": "1.0", "tools": entries}, sort_keys=False),
        encoding="utf-8",
    )
    return p


def _full_vocabulary() -> Dict[str, List[str]]:
    return {
        "fs": ["fs.read", "fs.write", "fs.delete"],
        "net": ["net.outbound", "net.allowlist"],
        "proc": ["proc.exec", "proc.spawn"],
        "audit": ["audit.read", "audit.append"],
        "policy": ["policy.read"],
        "ddd": ["ddd.propose", "ddd.decide"],
        "tool": ["tool.invoke"],
    }


def _write_caps_yaml(
    root: Path,
    entries: List[Dict[str, Any]],
    vocab: Dict[str, List[str]] | None = None,
) -> Path:
    p = root / ".ai" / "tools.capabilities.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    doc: Dict[str, Any] = {
        "version": "1.0",
        "status": "authoritative",
        "authoritative": True,
        "capability_vocabulary": vocab if vocab is not None else _full_vocabulary(),
        "tools": entries,
    }
    p.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return p


# ─── happy path ───────────────────────────────────────────────────────


def test_load_registry_happy_path(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(tmp_path, [_full_cap_entry("alpha")])

    reg = load_registry(tmp_path)
    rec = reg.require("alpha")
    assert isinstance(rec, ToolCapabilityRecord)
    assert rec.name == "alpha"
    assert "fs.read" in rec.required_capabilities
    assert rec.default_tier_requirement == "WARM"
    assert rec.policy_default == "safe"
    assert "alpha" in reg
    assert len(reg) == 1


def test_lookup_returns_none_for_missing(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(tmp_path, [_full_cap_entry("alpha")])

    reg = load_registry(tmp_path)
    assert reg.lookup("nonexistent") is None


def test_require_raises_unknown_tool_error(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(tmp_path, [_full_cap_entry("alpha")])

    reg = load_registry(tmp_path)
    with pytest.raises(UnknownToolError):
        reg.require("nonexistent")


def test_names_returns_sorted(tmp_path: Path) -> None:
    _write_tools_yaml(
        tmp_path, [_full_tool_entry("zulu"), _full_tool_entry("alpha")]
    )
    _write_caps_yaml(
        tmp_path, [_full_cap_entry("zulu"), _full_cap_entry("alpha")]
    )

    reg = load_registry(tmp_path)
    assert reg.names() == ("alpha", "zulu")


# ─── V1: 8 required tools.yaml attrs ──────────────────────────────────


@pytest.mark.parametrize("missing_attr", list(REQUIRED_TOOL_YAML_ATTRS))
def test_v1_missing_required_attr_fails(
    tmp_path: Path, missing_attr: str
) -> None:
    bad = _full_tool_entry("alpha")
    del bad[missing_attr]
    _write_tools_yaml(tmp_path, [bad])
    _write_caps_yaml(tmp_path, [_full_cap_entry("alpha")])

    with pytest.raises(RegistryValidationError, match="V1"):
        load_registry(tmp_path)


# ─── V2: bidirectional 1:1 ────────────────────────────────────────────


def test_v2_orphan_capabilities_entry_fails(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(
        tmp_path,
        [_full_cap_entry("alpha"), _full_cap_entry("orphan-only-in-caps")],
    )
    with pytest.raises(RegistryValidationError, match="V2"):
        load_registry(tmp_path)


def test_v2_orphan_tools_entry_fails(tmp_path: Path) -> None:
    _write_tools_yaml(
        tmp_path,
        [_full_tool_entry("alpha"), _full_tool_entry("orphan-only-in-tools")],
    )
    _write_caps_yaml(tmp_path, [_full_cap_entry("alpha")])
    with pytest.raises(RegistryValidationError, match="V2"):
        load_registry(tmp_path)


# ─── V3: closed capability vocabulary ─────────────────────────────────


def test_v3_unknown_capability_in_required_fails(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(
        tmp_path,
        [_full_cap_entry("alpha", required_capabilities=["fs.bogus"])],
    )
    with pytest.raises(RegistryValidationError, match="V3"):
        load_registry(tmp_path)


def test_v3_unknown_capability_in_optional_fails(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(
        tmp_path,
        [
            _full_cap_entry(
                "alpha",
                required_capabilities=["fs.read"],
                optional_capabilities=["net.invented"],
            )
        ],
    )
    with pytest.raises(RegistryValidationError, match="V3"):
        load_registry(tmp_path)


# ─── V4: NEVER-granted invariants ─────────────────────────────────────


@pytest.mark.parametrize("forbidden", sorted(NEVER_GRANTED_CAPABILITIES))
def test_v4_never_granted_in_required_fails(
    tmp_path: Path, forbidden: str
) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(
        tmp_path,
        [_full_cap_entry("alpha", required_capabilities=[forbidden])],
    )
    with pytest.raises(RegistryValidationError, match="V4"):
        load_registry(tmp_path)


# ─── V5: tier ─────────────────────────────────────────────────────────


def test_v5_invalid_tier_fails(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(
        tmp_path,
        [_full_cap_entry("alpha", default_tier_requirement="MELTED")],
    )
    with pytest.raises(RegistryValidationError, match="V5"):
        load_registry(tmp_path)


# ─── vocabulary drift ─────────────────────────────────────────────────


def test_vocabulary_drift_fails(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    truncated_vocab = {"fs": ["fs.read"]}  # missing fs.write, fs.delete, etc.
    _write_caps_yaml(
        tmp_path, [_full_cap_entry("alpha")], vocab=truncated_vocab
    )
    with pytest.raises(RegistryValidationError, match="vocabulary"):
        load_registry(tmp_path)


# ─── duplicates ───────────────────────────────────────────────────────


def test_duplicate_name_in_tools_yaml_fails(tmp_path: Path) -> None:
    _write_tools_yaml(
        tmp_path, [_full_tool_entry("alpha"), _full_tool_entry("alpha")]
    )
    _write_caps_yaml(tmp_path, [_full_cap_entry("alpha")])
    with pytest.raises(RegistryValidationError, match="duplicate"):
        load_registry(tmp_path)


def test_duplicate_name_in_caps_yaml_fails(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    _write_caps_yaml(
        tmp_path, [_full_cap_entry("alpha"), _full_cap_entry("alpha")]
    )
    with pytest.raises(RegistryValidationError, match="duplicate"):
        load_registry(tmp_path)


# ─── missing files ────────────────────────────────────────────────────


def test_missing_tools_yaml_fails(tmp_path: Path) -> None:
    _write_caps_yaml(tmp_path, [_full_cap_entry("alpha")])
    with pytest.raises(RegistryValidationError, match="missing"):
        load_registry(tmp_path)


def test_missing_capabilities_yaml_fails(tmp_path: Path) -> None:
    _write_tools_yaml(tmp_path, [_full_tool_entry("alpha")])
    with pytest.raises(RegistryValidationError, match="missing"):
        load_registry(tmp_path)


# ─── real-repo smoke ──────────────────────────────────────────────────


def test_real_repo_registry_loads() -> None:
    """Smoke check against the actual trinity_v2 repo on disk.

    After Phase 6 S5, capabilities.yaml has been promoted authoritative
    and the orphan trinity-tg-bot entry removed; tools.yaml still
    declares browser-cli + memory-cli.
    """
    project_root = Path(__file__).resolve().parents[3]
    if not (project_root / ".ai" / "tools.yaml").is_file():
        pytest.skip("not running from a project root with tools.yaml")
    reg = load_registry(project_root)
    assert reg.lookup("browser-cli") is not None
    assert reg.lookup("memory-cli") is not None
