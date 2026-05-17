"""Phase 8 nnn verification_contract gate wire tests.

Source-level + behavior tests for the wire that runs `validate_contract_dict`
+ `precedence_validator` at nnn time when `THINK/verification_contract.json`
is present (per spec TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md §4.6.1).
"""
from __future__ import annotations

import inspect

from cli.commands import nnn as nnn_mod


# ─── source-level wire ───────────────────────────────────────────────


def test_nnn_imports_precedence_validator() -> None:
    """The nnn module body must reference precedence_validator + validate_contract_dict."""
    source = inspect.getsource(nnn_mod)
    assert "verification_contract.json" in source, (
        "nnn must look for THINK/verification_contract.json"
    )
    assert "precedence_validator" in source, (
        "nnn must call precedence_validator from verifier_runtime"
    )
    assert "validate_contract_dict" in source, (
        "nnn must call validate_contract_dict from verification_contract"
    )


def test_nnn_emits_rejection_reason_field() -> None:
    """Per spec §4.6.1, rejection emits nnn.proposed with rejection_reason field."""
    source = inspect.getsource(nnn_mod)
    assert '"rejection_reason"' in source
    assert '"precedence_violation"' in source


def test_nnn_emits_schema_invalid_reason() -> None:
    """Schema validation failure → distinct rejection_reason='schema_invalid'."""
    source = inspect.getsource(nnn_mod)
    assert '"schema_invalid"' in source


def test_nnn_reads_verifier_rules_for_class_membership() -> None:
    """precedence_validator case (b) needs verifier-rules.yaml — wire must load it."""
    source = inspect.getsource(nnn_mod)
    assert "verifier-rules.yaml" in source


# ─── behavior: round-trip schema + precedence ────────────────────────


def test_precedence_validator_blocks_precedence_override() -> None:
    """End-to-end: a contract with precedence_override field → violation list non-empty."""
    from cli.core.verifier_runtime import precedence_validator
    contract = {
        "id": "vc-bad",
        "description": "bad",
        "version": "1.0",
        "acceptance": [
            {
                "id": "A1",
                "description": "x",
                "rule_set": "step_complete",
                "command": "true",
                "expect_exit": 0,
                "required": True,
                "precedence_override": "PASS",  # forbidden
            }
        ],
        "expected_terminal_verdict": "PASS",
    }
    violations = precedence_validator(contract, rules_doc=None)
    assert any("precedence_override" in v for v in violations)
    assert any("A1" in v for v in violations)


def test_precedence_validator_passes_canonical_minimum() -> None:
    """Canonical minimum contract → 0 violations."""
    from cli.core.verifier_runtime import precedence_validator
    contract = {
        "id": "vc-good",
        "description": "good",
        "version": "1.0",
        "acceptance": [
            {
                "id": "A1",
                "description": "smoke",
                "rule_set": "step_complete",
                "command": "true",
                "expect_exit": 0,
                "required": True,
            }
        ],
        "expected_terminal_verdict": "PASS",
        "rationale_for_fallback_divergence": "",
    }
    assert precedence_validator(contract, rules_doc=None) == []


def test_precedence_validator_no_acceptance_returns_empty() -> None:
    """Empty acceptance list is not a violation (handled elsewhere)."""
    from cli.core.verifier_runtime import precedence_validator
    contract = {
        "id": "vc-empty",
        "description": "no-acceptance",
        "version": "1.0",
        "acceptance": [],
    }
    assert precedence_validator(contract, rules_doc=None) == []
