"""Conformance tests for the Verification Contract (Article III + IV + XXVIII).

Spec: docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md §2 + §3 + §4.6
       .ai/schemas/verification_contract.schema.json (this session)

Tier-0/1 deterministic. Asserts: VERDICT_VOCABULARY closure (4), parity with
verifier.VALID_VERDICTS, PYRAMID_LAYERS = (1,2,3,4), dataclass surface,
schema validity, fixture round-trip, schema rejection of malformed input.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

import jsonschema
import pytest

from cli.core.verification_contract import (
    PYRAMID_LAYERS,
    SANDBOX_TIERS,
    VERDICT_VOCABULARY,
    AcceptanceEntry,
    VerificationContract,
    validate_contract_dict,
)
from cli.core.verifier import VALID_VERDICTS


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCHEMA_PATH = PROJECT_ROOT / ".ai" / "schemas" / "verification_contract.schema.json"


# ─────────── §2 — verdict vocabulary closure ───────────


def test_verdict_vocabulary_is_frozenset() -> None:
    assert isinstance(VERDICT_VOCABULARY, frozenset)


def test_verdict_vocabulary_exactly_four_canonical_values() -> None:
    assert VERDICT_VOCABULARY == frozenset({"PASS", "RETRY", "NEEDS_HUMAN", "DEAD"})


def test_verdict_vocabulary_equals_verifier_valid_verdicts() -> None:
    """Verification contract verdict vocabulary MUST equal verifier.py's
    VALID_VERDICTS. Drift between the two breaks Article IV (verifier is
    the source of truth for the verdict set; contract mirrors it)."""
    assert set(VERDICT_VOCABULARY) == set(VALID_VERDICTS)


# ─────────── §3 — pyramid layers ───────────


def test_pyramid_layers_is_tuple_of_4() -> None:
    assert PYRAMID_LAYERS == (1, 2, 3, 4)


# ─────────── tier classification mirror ───────────


def test_sandbox_tiers_canonical_set() -> None:
    assert SANDBOX_TIERS == frozenset({"HOT", "WARM", "COLD"})


# ─────────── §4.6 — dataclass surface ───────────


def test_acceptance_entry_required_fields() -> None:
    fields = {f.name for f in dataclasses.fields(AcceptanceEntry)}
    required = {"id", "description", "rule_set", "command", "expect_exit", "required"}
    assert required.issubset(fields)


def test_acceptance_entry_optional_fields() -> None:
    fields = {f.name for f in dataclasses.fields(AcceptanceEntry)}
    optional = {"predicates", "evidence_keys", "notes", "on_fire_verdict"}
    assert optional.issubset(fields)


def test_verification_contract_required_fields() -> None:
    fields = {f.name for f in dataclasses.fields(VerificationContract)}
    required = {"id", "description", "version", "acceptance"}
    assert required.issubset(fields)


def test_verification_contract_optional_fields() -> None:
    fields = {f.name for f in dataclasses.fields(VerificationContract)}
    optional = {"expected_terminal_verdict", "rationale_for_fallback_divergence", "policy_snapshot"}
    assert optional.issubset(fields)


# ─────────── schema validity ───────────


def test_verification_contract_schema_is_valid_jsonschema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_schema_pins_additional_properties_false_at_top_level() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema.get("additionalProperties") is False


def test_schema_pins_additional_properties_false_at_acceptance_level() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    accept_schema = schema["properties"]["acceptance"]["items"]
    assert accept_schema.get("additionalProperties") is False


# ─────────── known-good fixture round-trip ───────────


GOOD_FIXTURE = {
    "id": "p2-contract-test",
    "description": "Smoke fixture for verification contract validator",
    "version": "1.0",
    "acceptance": [
        {
            "id": "A1",
            "description": "Tests pass",
            "rule_set": "code_change",
            "predicates": ["tests_pass"],
            "evidence_keys": ["test_result.json"],
            "command": "pytest -q",
            "expect_exit": 0,
            "required": True,
        },
        {
            "id": "A2",
            "description": "No forbidden-path delta",
            "rule_set": "code_change",
            "command": "git diff --name-only main -- .ai/policies",
            "expect_exit": 0,
            "required": True,
            "notes": "Article XVI guardrail",
        },
    ],
    "expected_terminal_verdict": "PASS",
    "policy_snapshot": {
        "safety_yaml_sha256": "0" * 64,
        "gates_yaml_sha256": "0" * 64,
    },
}


def test_validate_contract_dict_accepts_good_fixture() -> None:
    validate_contract_dict(GOOD_FIXTURE)


def test_validate_contract_dict_minimum_required() -> None:
    minimal = {
        "id": "min",
        "description": "Minimum required fields only",
        "version": "1.0",
        "acceptance": [
            {
                "id": "A1",
                "description": "Smoke",
                "rule_set": "step_complete",
                "command": "true",
                "expect_exit": 0,
                "required": True,
            }
        ],
    }
    validate_contract_dict(minimal)


# ─────────── schema rejection tests ───────────


def test_validate_contract_dict_rejects_missing_required_top_level() -> None:
    bad = dict(GOOD_FIXTURE)
    del bad["acceptance"]
    with pytest.raises(jsonschema.ValidationError):
        validate_contract_dict(bad)


def test_validate_contract_dict_rejects_empty_acceptance_array() -> None:
    bad = dict(GOOD_FIXTURE)
    bad["acceptance"] = []
    with pytest.raises(jsonschema.ValidationError):
        validate_contract_dict(bad)


def test_validate_contract_dict_rejects_additional_top_level_property() -> None:
    bad = dict(GOOD_FIXTURE)
    bad["precedence_override"] = "PASS"  # forbidden per §4.6.1
    with pytest.raises(jsonschema.ValidationError):
        validate_contract_dict(bad)


def test_validate_contract_dict_rejects_bad_acceptance_id_pattern() -> None:
    bad = json.loads(json.dumps(GOOD_FIXTURE))   # deep copy
    bad["acceptance"][0]["id"] = "wrong-format"  # MUST match ^A[0-9]+$
    with pytest.raises(jsonschema.ValidationError):
        validate_contract_dict(bad)


def test_validate_contract_dict_rejects_bad_version_pattern() -> None:
    bad = dict(GOOD_FIXTURE)
    bad["version"] = "not-a-version"
    with pytest.raises(jsonschema.ValidationError):
        validate_contract_dict(bad)


def test_validate_contract_dict_rejects_bad_expected_terminal_verdict() -> None:
    bad = dict(GOOD_FIXTURE)
    bad["expected_terminal_verdict"] = "MAYBE"
    with pytest.raises(jsonschema.ValidationError):
        validate_contract_dict(bad)


def test_validate_contract_dict_rejects_on_fire_verdict_outside_vocabulary() -> None:
    bad = json.loads(json.dumps(GOOD_FIXTURE))
    bad["acceptance"][0]["on_fire_verdict"] = {"tests_pass": "MAYBE"}
    with pytest.raises(jsonschema.ValidationError):
        validate_contract_dict(bad)


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.verification_contract as vc

    importlib.reload(vc)
    assert hasattr(vc, "validate_contract_dict")
