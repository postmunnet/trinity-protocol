"""Tests for kernel-side ritual_pack_loader."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from cli.core.ritual_pack_loader import (
    PackNotFoundError,
    RitualPack,
    RitualPackError,
    SchemaValidationError,
    StateTransitionError,
    assert_transition_allowed,
    check_transition_allowed,
    load_pack,
    required_artifacts_for_check,
    required_audit_events,
    validate_pack_schemas,
)


REPO_ROOT = Path.cwd()
REAL_RITUALS_ROOT = REPO_ROOT / ".ai" / "rituals"
REAL_SCHEMAS_ROOT = REPO_ROOT / ".ai" / "schemas"

ALL_RITUALS = ("sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "close")


# ───────────────────────── load_pack happy path ─────────────────────────


@pytest.mark.parametrize("ritual", ALL_RITUALS)
def test_load_pack_succeeds_for_every_real_ritual(ritual: str):
    """Loader reads every real .ai/rituals/<r>/ pack without error."""
    pack = load_pack(ritual, rituals_root=REAL_RITUALS_ROOT)
    assert isinstance(pack, RitualPack)
    assert pack.ritual == ritual
    assert pack.contract["ritual"] == ritual
    assert pack.context_schema["ritual"] == ritual
    assert pack.write_template  # non-empty
    assert pack.check_template["check_template_version"] == "1.0"


def test_load_pack_returns_correct_root(tmp_path: Path):
    """RitualPack.root points at the dir on disk."""
    _seed_minimal_pack(tmp_path, "test_ritual")
    pack = load_pack("test_ritual", rituals_root=tmp_path)
    assert pack.root == tmp_path / "test_ritual"


def _seed_minimal_pack(rituals_root: Path, ritual: str) -> None:
    pack_dir = rituals_root / ritual
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "ritual.contract.json").write_text(json.dumps({
        "ritual": ritual,
        "version": "1.0",
        "purpose": "test purpose",
        "delegated_role": None,
        "input_context": "context.schema.json",
        "write_template": "write.template.md",
        "check_template": "check.template.json",
        "output_artifacts": ["foo.md"],
        "required_checks": [],
        "forbidden_actions": [],
        "allowed_current_states": ["READY"],
        "allowed_next_states": ["THINK"],
        "audit_events": [f"{ritual}.invoked"],
        "retry_policy": {
            "max_retries": 0,
            "retry_owner": "kernel",
            "escalate_to": "NEEDS_HUMAN",
            "preserve_failed_attempts": True,
            "audit_each_attempt": True,
        },
    }))
    (pack_dir / "context.schema.json").write_text(json.dumps({
        "context_schema_version": "1.0",
        "ritual": ritual,
        "placeholders": [],
    }))
    (pack_dir / "check.template.json").write_text(json.dumps({
        "check_template_version": "1.0",
        "required_artifacts": ["foo.md"],
        "required_headings": [],
        "required_fields": {},
        "required_evidence_refs": {},
        "required_structural_predicates": [],
        "required_phrases": [],
        "forbidden_phrases": ["{{user_input}}"],
        "forbidden_actions": [],
        "allowed_roles": [],
        "forbidden_roles": [],
        "state_transition": {"from": ["READY"], "to": ["THINK"]},
        "failure_behavior": {
            "on_missing_artifact": "BLOCK",
            "on_missing_evidence": "BLOCK",
            "on_forbidden_phrase": "BLOCK",
            "on_optional_failure": "WARN",
        },
    }))
    (pack_dir / "write.template.md").write_text(f"# {ritual}\nbody\n")


# ───────────────────────── load_pack error paths ─────────────────────────


def test_load_pack_missing_dir_raises(tmp_path: Path):
    with pytest.raises(PackNotFoundError, match="not found"):
        load_pack("no_such", rituals_root=tmp_path)


def test_load_pack_missing_file_raises(tmp_path: Path):
    """Pack dir exists but one of the 4 required files is missing."""
    pack_dir = tmp_path / "broken"
    pack_dir.mkdir()
    (pack_dir / "ritual.contract.json").write_text("{}")
    # other 3 files missing
    with pytest.raises(PackNotFoundError, match="required pack file missing"):
        load_pack("broken", rituals_root=tmp_path)


def test_load_pack_malformed_json_raises(tmp_path: Path):
    _seed_minimal_pack(tmp_path, "ok")
    # Corrupt one JSON file.
    (tmp_path / "ok" / "ritual.contract.json").write_text("not JSON")
    with pytest.raises(RitualPackError, match="JSON parse failed"):
        load_pack("ok", rituals_root=tmp_path)


def test_load_pack_ritual_mismatch_raises(tmp_path: Path):
    """contract.ritual must match the directory name."""
    _seed_minimal_pack(tmp_path, "expected_name")
    # Tamper: change contract.ritual to something else.
    cpath = tmp_path / "expected_name" / "ritual.contract.json"
    contract = json.loads(cpath.read_text())
    contract["ritual"] = "wrong_name"
    cpath.write_text(json.dumps(contract))
    with pytest.raises(RitualPackError, match="does not match dir"):
        load_pack("expected_name", rituals_root=tmp_path)


# ───────────────────────── validate_pack_schemas ─────────────────────────


@pytest.mark.parametrize("ritual", ALL_RITUALS)
def test_validate_pack_schemas_passes_for_every_real_pack(ritual: str):
    """Every real pack validates against its base schema."""
    pack = load_pack(ritual, rituals_root=REAL_RITUALS_ROOT)
    validate_pack_schemas(pack, schemas_root=REAL_SCHEMAS_ROOT)  # should not raise


def test_validate_pack_schemas_rejects_invalid_contract(tmp_path: Path):
    """Pack with a contract that violates the base schema is rejected."""
    _seed_minimal_pack(tmp_path, "sss")
    cpath = tmp_path / "sss" / "ritual.contract.json"
    contract = json.loads(cpath.read_text())
    # Break the schema: inject an extra field (additionalProperties=false
    # in the base schema rejects it).
    contract["unknown_extra_key"] = "this should not be here"
    cpath.write_text(json.dumps(contract))
    pack = load_pack("sss", rituals_root=tmp_path)
    with pytest.raises(SchemaValidationError):
        validate_pack_schemas(pack, schemas_root=REAL_SCHEMAS_ROOT)


def test_validate_pack_schemas_missing_base_schema_raises(tmp_path: Path):
    """If base schema is missing from schemas_root, raises clearly."""
    _seed_minimal_pack(tmp_path, "sss")
    pack = load_pack("sss", rituals_root=tmp_path)
    empty_schemas = tmp_path / "empty_schemas"
    empty_schemas.mkdir()
    with pytest.raises(SchemaValidationError, match="base schema missing"):
        validate_pack_schemas(pack, schemas_root=empty_schemas)


# ───────────────────────── transition guard ─────────────────────────


def test_check_transition_allowed_legal():
    """sss READY → THINK is legal per its contract."""
    pack = load_pack("sss", rituals_root=REAL_RITUALS_ROOT)
    # sss allows READY → THINK per Article XVII baseline.
    assert "READY" in pack.contract["allowed_current_states"]
    assert "THINK" in pack.contract["allowed_next_states"]
    assert check_transition_allowed(pack, "READY", "THINK") is True


def test_check_transition_allowed_illegal():
    """sss does NOT allow DEPLOYED → SEALED (way outside its envelope)."""
    pack = load_pack("sss", rituals_root=REAL_RITUALS_ROOT)
    assert check_transition_allowed(pack, "DEPLOYED", "SEALED") is False


def test_assert_transition_allowed_legal_no_raise():
    pack = load_pack("sss", rituals_root=REAL_RITUALS_ROOT)
    assert_transition_allowed(pack, "READY", "THINK")  # no raise


def test_assert_transition_allowed_illegal_current_raises():
    pack = load_pack("sss", rituals_root=REAL_RITUALS_ROOT)
    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        assert_transition_allowed(pack, "FAILED", "THINK")


def test_assert_transition_allowed_illegal_next_raises():
    pack = load_pack("sss", rituals_root=REAL_RITUALS_ROOT)
    with pytest.raises(StateTransitionError, match="not in allowed_next_states"):
        assert_transition_allowed(pack, "READY", "DEPLOYED")


# ───────────────────────── accessor helpers ─────────────────────────


def test_required_audit_events_returns_list():
    pack = load_pack("sss", rituals_root=REAL_RITUALS_ROOT)
    events = required_audit_events(pack)
    assert isinstance(events, list)
    assert any(e.endswith(".invoked") for e in events)
    assert "sss.invoked" in events


def test_required_artifacts_for_check_returns_list():
    pack = load_pack("nnn", rituals_root=REAL_RITUALS_ROOT)
    artifacts = required_artifacts_for_check(pack)
    assert isinstance(artifacts, list)
    # nnn requires several artifacts including plan_envelope.json
    assert any("plan_envelope" in a for a in artifacts)


def test_required_audit_events_rejects_non_list(tmp_path: Path):
    _seed_minimal_pack(tmp_path, "sss")
    cpath = tmp_path / "sss" / "ritual.contract.json"
    contract = json.loads(cpath.read_text())
    contract["audit_events"] = "not a list"
    cpath.write_text(json.dumps(contract))
    pack = load_pack("sss", rituals_root=tmp_path)
    with pytest.raises(RitualPackError, match="audit_events must be a list"):
        required_audit_events(pack)


# ───────────────────────── coverage sanity ─────────────────────────


def test_all_seven_real_rituals_pass_full_pipeline():
    """End-to-end: load + schema validation + audit accessor + artifacts
    accessor for every real ritual, in one test."""
    for ritual in ALL_RITUALS:
        pack = load_pack(ritual, rituals_root=REAL_RITUALS_ROOT)
        validate_pack_schemas(pack, schemas_root=REAL_SCHEMAS_ROOT)
        events = required_audit_events(pack)
        artifacts = required_artifacts_for_check(pack)
        assert events, f"{ritual} declares no audit events"
        assert artifacts is not None  # may be empty for some rituals
