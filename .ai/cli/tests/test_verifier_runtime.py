"""Phase 8 verifier_runtime unit tests.

Treats `verification_contract.py` as the read-only source of
`VERDICT_VOCABULARY` and `AcceptanceEntry` (Article IV — runtime and
contract are siblings, runtime imports declarative types).
"""
from __future__ import annotations

import pytest

from cli.core.verification_contract import (
    VERDICT_VOCABULARY,
    AcceptanceEntry,
)
from cli.core.verifier_runtime import (
    ACCEPTANCE_ID_PATTERN,
    CONSOLIDATION_PRECEDENCE,
    consolidate_step_verdicts,
    is_terminal_verdict_consistent,
    parse_acceptance_to_entries,
)


# ─── invariants ──────────────────────────────────────────────────────


def test_consolidation_precedence_is_permutation_of_vocabulary() -> None:
    """CONSOLIDATION_PRECEDENCE must cover every member exactly once."""
    assert set(CONSOLIDATION_PRECEDENCE) == VERDICT_VOCABULARY
    assert len(CONSOLIDATION_PRECEDENCE) == len(VERDICT_VOCABULARY)


def test_consolidation_precedence_is_most_severe_first() -> None:
    """Closed ordering — DEAD wins, PASS loses."""
    assert CONSOLIDATION_PRECEDENCE[0] == "DEAD"
    assert CONSOLIDATION_PRECEDENCE[-1] == "PASS"


# ─── consolidate_step_verdicts ───────────────────────────────────────


@pytest.mark.parametrize(
    "verdicts,expected",
    [
        (["PASS"], "PASS"),
        (["PASS", "PASS", "PASS"], "PASS"),
        (["PASS", "RETRY", "PASS"], "RETRY"),
        (["PASS", "NEEDS_HUMAN", "RETRY"], "NEEDS_HUMAN"),
        (["DEAD", "PASS"], "DEAD"),
        (["RETRY", "DEAD", "NEEDS_HUMAN"], "DEAD"),
        (["NEEDS_HUMAN", "PASS"], "NEEDS_HUMAN"),
    ],
)
def test_consolidate_step_verdicts_precedence(verdicts, expected) -> None:
    assert consolidate_step_verdicts(verdicts) == expected


def test_consolidate_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty verdict list"):
        consolidate_step_verdicts([])


def test_consolidate_drift_raises() -> None:
    with pytest.raises(ValueError, match="not in VERDICT_VOCABULARY"):
        consolidate_step_verdicts(["PASS", "MAYBE", "RETRY"])


def test_consolidate_lowercase_drift_raises() -> None:
    """Vocabulary is case-sensitive uppercase per spec §2."""
    with pytest.raises(ValueError, match="not in VERDICT_VOCABULARY"):
        consolidate_step_verdicts(["pass"])


# ─── is_terminal_verdict_consistent ──────────────────────────────────


@pytest.mark.parametrize("v", sorted(VERDICT_VOCABULARY))
def test_terminal_consistent_match_pairs(v: str) -> None:
    assert is_terminal_verdict_consistent(v, v) is True


def test_terminal_consistent_mismatch() -> None:
    assert is_terminal_verdict_consistent("PASS", "RETRY") is False
    assert is_terminal_verdict_consistent("DEAD", "NEEDS_HUMAN") is False


def test_terminal_consistent_unknown_returns_false() -> None:
    assert is_terminal_verdict_consistent("PASS", "MAYBE") is False
    assert is_terminal_verdict_consistent("MAYBE", "PASS") is False
    assert is_terminal_verdict_consistent("maybe", "perhaps") is False


# ─── parse_acceptance_to_entries ─────────────────────────────────────


def _full_row(aid: str = "A1") -> dict:
    return {
        "id": aid,
        "description": f"acceptance {aid}",
        "rule_set": "step_complete",
        "command": "true",
        "expect_exit": 0,
        "required": True,
        "predicates": ["step_done"],
        "evidence_keys": ["evidence/x.json"],
        "notes": "optional note",
    }


def test_parse_minimal_row_produces_entry() -> None:
    entries = parse_acceptance_to_entries([_full_row()])
    assert len(entries) == 1
    e = entries[0]
    assert isinstance(e, AcceptanceEntry)
    assert e.id == "A1"
    assert e.description == "acceptance A1"
    assert e.rule_set == "step_complete"
    assert e.command == "true"
    assert e.expect_exit == 0
    assert e.required is True
    assert e.predicates == ["step_done"]
    assert e.evidence_keys == ["evidence/x.json"]
    assert e.notes == "optional note"
    assert e.on_fire_verdict is None


def test_parse_multiple_rows() -> None:
    rows = [_full_row("A1"), _full_row("A2"), _full_row("A3")]
    entries = parse_acceptance_to_entries(rows)
    assert [e.id for e in entries] == ["A1", "A2", "A3"]


def test_parse_with_on_fire_verdict() -> None:
    row = _full_row()
    row["on_fire_verdict"] = {"orphan": "DEAD", "missing": "NEEDS_HUMAN"}
    entries = parse_acceptance_to_entries([row])
    assert entries[0].on_fire_verdict == {"orphan": "DEAD", "missing": "NEEDS_HUMAN"}


def test_parse_missing_id_raises() -> None:
    row = _full_row()
    del row["id"]
    with pytest.raises(ValueError, match="missing required key: id"):
        parse_acceptance_to_entries([row])


def test_parse_bad_id_pattern_raises() -> None:
    row = _full_row("X1")  # must match ^A[0-9]+$
    with pytest.raises(ValueError, match="does not match schema pattern"):
        parse_acceptance_to_entries([row])


def test_parse_missing_required_keys_raises() -> None:
    for key in ("description", "command", "expect_exit", "required", "rule_set"):
        row = _full_row()
        del row[key]
        with pytest.raises(ValueError, match=f"missing required key: {key}"):
            parse_acceptance_to_entries([row])


def test_parse_on_fire_verdict_drift_raises() -> None:
    row = _full_row()
    row["on_fire_verdict"] = {"orphan": "MAYBE"}
    with pytest.raises(ValueError, match="not in VERDICT_VOCABULARY"):
        parse_acceptance_to_entries([row])


def test_parse_on_fire_verdict_non_dict_raises() -> None:
    row = _full_row()
    row["on_fire_verdict"] = ["DEAD"]  # type: ignore[assignment]
    with pytest.raises(ValueError, match="on_fire_verdict must be a mapping"):
        parse_acceptance_to_entries([row])


def test_parse_optional_fields_default_safely() -> None:
    """predicates / evidence_keys / notes are optional with safe defaults."""
    minimal = {
        "id": "A1",
        "description": "x",
        "rule_set": "step_complete",
        "command": "true",
        "expect_exit": 0,
        "required": True,
    }
    e = parse_acceptance_to_entries([minimal])[0]
    assert e.predicates == []
    assert e.evidence_keys == []
    assert e.notes == ""
    assert e.on_fire_verdict is None


# ─── pattern smoke ───────────────────────────────────────────────────


def test_acceptance_id_pattern_accepts_valid() -> None:
    for aid in ("A1", "A12", "A123"):
        assert ACCEPTANCE_ID_PATTERN.match(aid)


def test_acceptance_id_pattern_rejects_invalid() -> None:
    for aid in ("a1", "A", "Ax", "1A", "A1.2", ""):
        assert not ACCEPTANCE_ID_PATTERN.match(aid)


# ─── §4.6.1 precedence_validator (Phase 8 nnn gate) ──────────────────


from cli.core.verifier_runtime import precedence_validator


def _valid_contract_minimum() -> dict:
    return {
        "id": "vc-001",
        "description": "minimal valid contract",
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


def test_precedence_validator_empty_contract_returns_empty() -> None:
    """Bare contract with no rules_doc → no violations detectable."""
    contract = _valid_contract_minimum()
    assert precedence_validator(contract, rules_doc=None) == []


def test_precedence_validator_detects_precedence_override_field() -> None:
    """Case (a) §4.6.1 — forbidden precedence_override field present."""
    contract = _valid_contract_minimum()
    contract["acceptance"][0]["precedence_override"] = "PASS"
    violations = precedence_validator(contract, rules_doc=None)
    assert len(violations) == 1
    assert "precedence_override" in violations[0]
    assert "A1" in violations[0]


def test_precedence_validator_detects_on_fire_verdict_contradiction() -> None:
    """Case (b) §4.6.1 — on_fire_verdict maps dead_when predicate to PASS."""
    contract = _valid_contract_minimum()
    contract["acceptance"][0]["on_fire_verdict"] = {"orphan_invocation": "PASS"}
    rules_doc = {
        "rule_sets": {
            "step_complete": {
                "dead_when": {"orphan_invocation": {}},
                "pass_when": {"step_done": {}},
                "fallback_verdict": "PASS",
            }
        }
    }
    violations = precedence_validator(contract, rules_doc=rules_doc)
    assert len(violations) == 1
    assert "orphan_invocation" in violations[0]
    assert "dead_when" in violations[0]
    assert "PASS" in violations[0]


def test_precedence_validator_allows_on_fire_verdict_matching_class() -> None:
    """on_fire_verdict matches rule_set class → no violation."""
    contract = _valid_contract_minimum()
    contract["acceptance"][0]["on_fire_verdict"] = {"orphan_invocation": "DEAD"}
    rules_doc = {
        "rule_sets": {
            "step_complete": {
                "dead_when": {"orphan_invocation": {}},
                "pass_when": {"step_done": {}},
                "fallback_verdict": "PASS",
            }
        }
    }
    assert precedence_validator(contract, rules_doc=rules_doc) == []


def test_precedence_validator_detects_fallback_divergence_without_rationale() -> None:
    """Case (c) §4.6.1 — fallback_verdict ≠ expected_terminal + no rationale."""
    contract = _valid_contract_minimum()
    contract["expected_terminal_verdict"] = "PASS"
    contract["rationale_for_fallback_divergence"] = ""
    rules_doc = {
        "rule_sets": {
            "step_complete": {
                "fallback_verdict": "RETRY",  # diverges from PASS
            }
        }
    }
    violations = precedence_validator(contract, rules_doc=rules_doc)
    assert len(violations) == 1
    assert "fallback_verdict" in violations[0]
    assert "RETRY" in violations[0]
    assert "PASS" in violations[0]


def test_precedence_validator_allows_fallback_divergence_with_rationale() -> None:
    """Divergence + rationale present → no violation."""
    contract = _valid_contract_minimum()
    contract["rationale_for_fallback_divergence"] = (
        "Intentional: RETRY is the safe default for transient failures."
    )
    rules_doc = {
        "rule_sets": {
            "step_complete": {"fallback_verdict": "RETRY"}
        }
    }
    assert precedence_validator(contract, rules_doc=rules_doc) == []


def test_precedence_validator_multiple_violations() -> None:
    """A contract with two issues returns two violation messages."""
    contract = _valid_contract_minimum()
    contract["acceptance"].append({
        "id": "A2",
        "description": "second entry",
        "rule_set": "step_complete",
        "command": "true",
        "expect_exit": 0,
        "required": True,
        "precedence_override": "PASS",
    })
    rules_doc = {
        "rule_sets": {
            "step_complete": {"fallback_verdict": "RETRY"}
        }
    }
    contract["rationale_for_fallback_divergence"] = ""  # forces case (c) twice
    violations = precedence_validator(contract, rules_doc=rules_doc)
    # case (a) on A2 + case (c) on both A1 and A2 = 3 violations
    assert len(violations) >= 2
    assert any("precedence_override" in v for v in violations)
    assert any("fallback_verdict" in v for v in violations)


# ─── Phase 8 tier-mapping (S13) ──────────────────────────────────────


from cli.core.verifier_runtime import (
    TIER_SEVERITY,
    consolidate_step_tiers,
)
from cli.core.verification_contract import SANDBOX_TIERS


def test_tier_severity_is_permutation_of_sandbox_tiers() -> None:
    """TIER_SEVERITY must cover every member of SANDBOX_TIERS exactly once."""
    assert set(TIER_SEVERITY) == SANDBOX_TIERS
    assert len(TIER_SEVERITY) == len(SANDBOX_TIERS)


def test_tier_severity_cold_first() -> None:
    """COLD is the most-severe (deploy/orphan/critical-boundary)."""
    assert TIER_SEVERITY[0] == "COLD"
    assert TIER_SEVERITY[-1] == "HOT"


@pytest.mark.parametrize(
    "tiers,expected",
    [
        (["HOT"], "HOT"),
        (["WARM"], "WARM"),
        (["COLD"], "COLD"),
        (["HOT", "WARM"], "WARM"),
        (["HOT", "HOT", "WARM"], "WARM"),
        (["WARM", "COLD"], "COLD"),
        (["HOT", "COLD", "WARM"], "COLD"),
        (["COLD", "COLD"], "COLD"),
    ],
)
def test_consolidate_step_tiers_precedence(tiers, expected) -> None:
    assert consolidate_step_tiers(tiers) == expected


def test_consolidate_step_tiers_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty tier list"):
        consolidate_step_tiers([])


def test_consolidate_step_tiers_drift_raises() -> None:
    with pytest.raises(ValueError, match="not in SANDBOX_TIERS"):
        consolidate_step_tiers(["WARM", "ULTRACOLD"])


def test_consolidate_step_tiers_sentinel_drift_raises() -> None:
    """The verifier sentinel value should surface as drift, not silently accept."""
    with pytest.raises(ValueError, match="not in SANDBOX_TIERS"):
        consolidate_step_tiers(["__resolve_from_tier_map__"])


def test_consolidate_step_tiers_lowercase_drift_raises() -> None:
    """SANDBOX_TIERS is uppercase per the dataclass — case-sensitive."""
    with pytest.raises(ValueError, match="not in SANDBOX_TIERS"):
        consolidate_step_tiers(["warm"])
