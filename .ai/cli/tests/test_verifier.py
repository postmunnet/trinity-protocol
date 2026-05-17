"""Phase 4 — verifier engine tests.

Covers:
- load_rules / get_rule_set / list_rule_sets
- _truthy semantics (None / False / "" / 0 / [] are no-match)
- step.force_verdict short-circuits the engine
- eval order: dead > needs_human > retry > pass > fallback
- pass_when requires ALL predicates true
- partially-met pass_when degrades to fallback with reason
- unknown rule_set raises VerifierError
- step_complete defaults block keeps existing tests green
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cli.core.verifier import (
    VALID_VERDICTS,
    VerifierError,
    _match_predicates,
    _truthy,
    evaluate_step,
    get_rule_set,
    list_rule_sets,
    load_rules,
)


# ─────────── _truthy ───────────


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        (False, False),
        ("", False),
        (0, False),
        (0.0, False),
        ([], False),
        ({}, False),
        (set(), False),
        (True, True),
        (1, True),
        ("non-empty", True),
        ([0], True),
        ({"a": 0}, True),
    ],
)
def test_truthy_semantics(value, expected):
    assert _truthy(value) is expected


def test_match_predicates_returns_only_truthy_keys():
    evidence = {"a": True, "b": False, "c": None, "d": "x"}
    assert _match_predicates(evidence, ["a", "b", "c", "d"]) == ["a", "d"]
    assert _match_predicates(evidence, []) == []


# ─────────── load_rules / get_rule_set ───────────


def test_load_rules_reads_repo_file():
    doc = load_rules(Path.cwd())
    assert "verifier_rules" in doc
    sets = doc["verifier_rules"]
    # Phase 4 must populate at least these three.
    for name in ("step_complete", "code_change", "memory_promote"):
        assert name in sets, f"rule_set {name!r} should be in verifier-rules.yaml"


def test_get_rule_set_raises_for_unknown():
    doc = load_rules(Path.cwd())
    with pytest.raises(VerifierError):
        get_rule_set(doc, "totally_made_up_rule_set")


def test_list_rule_sets_includes_phase4_set():
    doc = load_rules(Path.cwd())
    names = list_rule_sets(doc)
    assert "step_complete" in names


def test_load_rules_missing_file(tmp_path: Path):
    with pytest.raises(VerifierError):
        load_rules(tmp_path)  # no .ai/policies/verifier-rules.yaml


# ─────────── force_verdict short-circuit ───────────


def test_force_verdict_wins_over_rules():
    doc = load_rules(Path.cwd())
    v = evaluate_step(
        {"force_verdict": "DEAD", "force_reason": "test fixture"},
        "step_complete",
        doc,
    )
    assert v.verdict == "DEAD"
    assert v.mode == "forced"
    assert "fixture" in v.reason


def test_force_verdict_invalid_value_is_ignored():
    doc = load_rules(Path.cwd())
    v = evaluate_step({"force_verdict": "BOGUS"}, "step_complete", doc)
    # Falls through to normal evaluation; step_complete defaults make it PASS
    # only when the gogogo defaults are merged. Here we evaluate the raw step
    # without defaults — so pass_when=[step_done] is unmet → fallback RETRY.
    assert v.verdict == "RETRY"
    assert v.mode == "fallback"


# ─────────── eval order ───────────


def _doc_with(rule_set: dict) -> dict:
    return {"version": "1.0", "verifier_rules": {"sample": rule_set}}


def test_dead_when_wins_over_others():
    doc = _doc_with({
        "pass_when": ["good"],
        "retry_when": ["transient"],
        "needs_human_when": ["sensitive"],
        "dead_when": ["forbidden"],
        "fallback_verdict": "RETRY",
    })
    v = evaluate_step(
        {"good": True, "transient": True, "sensitive": True, "forbidden": True},
        "sample", doc,
    )
    assert v.verdict == "DEAD"
    assert "forbidden" in v.reason


def test_needs_human_wins_over_retry_and_pass():
    doc = _doc_with({
        "pass_when": ["good"],
        "retry_when": ["transient"],
        "needs_human_when": ["sensitive"],
        "fallback_verdict": "RETRY",
    })
    v = evaluate_step(
        {"good": True, "transient": True, "sensitive": True},
        "sample", doc,
    )
    assert v.verdict == "NEEDS_HUMAN"
    assert "sensitive" in v.reason


def test_retry_wins_over_pass():
    doc = _doc_with({
        "pass_when": ["good"],
        "retry_when": ["transient"],
        "fallback_verdict": "RETRY",
    })
    v = evaluate_step({"good": True, "transient": True}, "sample", doc)
    assert v.verdict == "RETRY"


def test_pass_requires_all_pass_when_true():
    doc = _doc_with({
        "pass_when": ["a", "b"],
        "fallback_verdict": "RETRY",
    })
    # All true → PASS
    v = evaluate_step({"a": True, "b": True}, "sample", doc)
    assert v.verdict == "PASS"
    # One missing → fallback RETRY with descriptive reason
    v2 = evaluate_step({"a": True}, "sample", doc)
    assert v2.verdict == "RETRY"
    assert v2.mode == "fallback"
    assert "b" in v2.reason


def test_no_predicates_no_pass_when_returns_fallback():
    doc = _doc_with({"fallback_verdict": "NEEDS_HUMAN"})
    v = evaluate_step({}, "sample", doc)
    assert v.verdict == "NEEDS_HUMAN"
    assert v.mode == "fallback"


def test_invalid_fallback_verdict_raises():
    doc = _doc_with({
        "pass_when": ["x"],
        "fallback_verdict": "MAYBE",
    })
    with pytest.raises(VerifierError):
        evaluate_step({}, "sample", doc)


# ─────────── extra_evidence ───────────


def test_extra_evidence_overrides_step_field():
    doc = _doc_with({
        "pass_when": ["tests_pass"],
        "fallback_verdict": "RETRY",
    })
    # Step says tests_pass=False; extra_evidence overrides to True.
    v = evaluate_step(
        {"tests_pass": False},
        "sample", doc,
        extra_evidence={"tests_pass": True},
    )
    assert v.verdict == "PASS"


# ─────────── step_complete defaults (phase-4 backward-compat) ───────────


def test_step_complete_pass_when_defaults_are_merged_by_caller():
    """The verifier itself does NOT auto-merge defaults; gogogo does
    that before calling. This test asserts that the merged shape works
    end-to-end with the real rule_set."""
    doc = load_rules(Path.cwd())
    rule_set = get_rule_set(doc, "step_complete")
    defaults = rule_set.get("defaults") or {}
    merged = {**defaults, **{}}  # empty step
    v = evaluate_step(merged, "step_complete", doc)
    assert v.verdict == "PASS"


def test_step_complete_negative_evidence_drops_to_dead():
    doc = load_rules(Path.cwd())
    rule_set = get_rule_set(doc, "step_complete")
    defaults = rule_set.get("defaults") or {}
    merged = {**defaults, **{"forbidden_pattern_found": True}}
    v = evaluate_step(merged, "step_complete", doc)
    assert v.verdict == "DEAD"


def test_valid_verdicts_set_is_canonical():
    assert VALID_VERDICTS == {"PASS", "RETRY", "NEEDS_HUMAN", "DEAD"}
