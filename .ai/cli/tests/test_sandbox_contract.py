"""Conformance tests for the Sandbox organ contract (Article XVI + XXVIII).

Spec: docs/specs/TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md
       .ai/schemas/sandbox_profile.schema.json (operator-authored)

Tier-0/1 deterministic. Asserts: closure invariants, dataclass surface,
jsonschema validate round-trip on known-good fixture, schema rejection of
known-bad fixture.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

import jsonschema
import pytest

from cli.core.sandbox_contract import (
    CAPABILITY_AXES,
    DENY_REASONS,
    NET_OUTBOUND_MODES,
    SANDBOX_TIERS,
    AuditCapability,
    AuthorityCapability,
    FsCapability,
    NetCapability,
    PolicyCapability,
    ProcCapability,
    SandboxProfile,
    ToolsCapability,
    validate_profile_dict,
)


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCHEMA_PATH = PROJECT_ROOT / ".ai" / "schemas" / "sandbox_profile.schema.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ─────────── closure invariants ───────────


def test_capability_axes_is_frozenset() -> None:
    assert isinstance(CAPABILITY_AXES, frozenset)


def test_capability_axes_covers_schema_top_level_properties() -> None:
    """Every property in `sandbox_profile.schema.json` (except id/version/description)
    MUST appear in CAPABILITY_AXES — Python is a superset (or equal) of schema."""
    schema = _load_schema()
    schema_props = set(schema.get("properties", {}).keys())
    schema_axes = schema_props - {"id", "version", "description"}
    missing = schema_axes - CAPABILITY_AXES
    assert not missing, (
        f"CAPABILITY_AXES missing schema axes: {missing}"
    )


def test_sandbox_tiers_is_frozenset() -> None:
    assert SANDBOX_TIERS == frozenset({"HOT", "WARM", "COLD"})


def test_net_outbound_modes_matches_schema_enum() -> None:
    schema = _load_schema()
    enum_vals = set(schema["properties"]["net"]["properties"]["outbound"]["enum"])
    assert NET_OUTBOUND_MODES == enum_vals


def test_deny_reasons_non_empty_frozenset() -> None:
    assert isinstance(DENY_REASONS, frozenset)
    assert len(DENY_REASONS) >= 10


# ─────────── dataclass surface ───────────


def test_sandbox_profile_fields() -> None:
    fields = {f.name for f in dataclasses.fields(SandboxProfile)}
    required = {"id", "version", "fs", "net", "proc", "tools", "authority", "audit", "policy", "description"}
    assert required.issubset(fields)


def test_fs_capability_fields() -> None:
    fields = {f.name for f in dataclasses.fields(FsCapability)}
    required = {"read_roots", "write_roots", "forbidden_paths", "delete_roots", "max_bytes_per_file", "max_total_bytes"}
    assert required.issubset(fields)


def test_net_capability_fields() -> None:
    fields = {f.name for f in dataclasses.fields(NetCapability)}
    assert {"outbound", "allowlist", "protocols"}.issubset(fields)


def test_proc_capability_fields() -> None:
    fields = {f.name for f in dataclasses.fields(ProcCapability)}
    assert {"allowed_binaries", "forbidden_binaries", "spawn_allowed", "max_wallclock_seconds"}.issubset(fields)


def test_tools_capability_fields() -> None:
    fields = {f.name for f in dataclasses.fields(ToolsCapability)}
    assert {"allowed", "forbidden"}.issubset(fields)


def test_authority_capability_defaults_to_default_deny() -> None:
    auth = AuthorityCapability()
    assert auth.may_promote is False
    assert auth.may_deploy is False
    assert auth.may_modify_policies is False
    assert auth.ddd_propose_allowed is False


def test_audit_capability_defaults_to_no_read() -> None:
    assert AuditCapability().read_allowed is False


def test_policy_capability_defaults_to_no_read() -> None:
    assert PolicyCapability().read_allowed is False


# ─────────── validate_profile_dict round-trip ───────────


GOOD_FIXTURE = {
    "id": "hot-test",
    "version": "1.0",
    "fs": {"read_roots": ["."], "write_roots": [], "forbidden_paths": []},
    "net": {"outbound": "denied"},
    "proc": {"allowed_binaries": [], "forbidden_binaries": []},
    "tools": {"allowed": [], "forbidden": []},
    "authority": {
        "may_promote": False,
        "may_deploy": False,
        "may_modify_policies": False,
    },
}


def test_validate_profile_dict_accepts_minimum_required() -> None:
    validate_profile_dict(GOOD_FIXTURE)


def test_validate_profile_dict_accepts_full_v2_axes() -> None:
    full = {
        **GOOD_FIXTURE,
        "id": "full-v2",
        "description": "with v2 axes",
        "audit": {"read_allowed": True},
        "policy": {"read_allowed": False},
    }
    validate_profile_dict(full)


def test_validate_profile_dict_rejects_missing_required() -> None:
    bad = dict(GOOD_FIXTURE)
    del bad["fs"]
    with pytest.raises(jsonschema.ValidationError):
        validate_profile_dict(bad)


def test_validate_profile_dict_rejects_unknown_net_outbound() -> None:
    bad = dict(GOOD_FIXTURE)
    bad["net"] = {"outbound": "promiscuous"}
    with pytest.raises(jsonschema.ValidationError):
        validate_profile_dict(bad)


def test_validate_profile_dict_rejects_additional_top_level_property() -> None:
    bad = dict(GOOD_FIXTURE)
    bad["surprise_axis"] = {"x": True}
    with pytest.raises(jsonschema.ValidationError):
        validate_profile_dict(bad)


def test_validate_profile_dict_rejects_bad_id_pattern() -> None:
    bad = dict(GOOD_FIXTURE)
    bad["id"] = "Has Uppercase And Spaces"
    with pytest.raises(jsonschema.ValidationError):
        validate_profile_dict(bad)


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.sandbox_contract as sc

    importlib.reload(sc)
    assert hasattr(sc, "validate_profile_dict")
