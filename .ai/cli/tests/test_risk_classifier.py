"""Q24.10 step 4 — deterministic risk classifier tests.

Risk is explicit (step.risk) or deterministic (hotlist) only; never
LLM-judged. Missing risk is 'unknown'/'legacy_missing_risk', not silent low.
"""
from __future__ import annotations

from cli.core import risk_classifier as rc


def test_explicit_risk_wins():
    assert rc.classify_risk({"risk": "low", "title": "deploy to prod"}) == (
        "low", "explicit"
    )
    assert rc.classify_risk({"risk": "high"}) == ("high", "explicit")
    assert rc.classify_risk({"risk": "medium"}) == ("medium", "explicit")


def test_hotlist_path_marks_high():
    lvl, src = rc.classify_risk({"title": "edit core/trinity_v2/.ai/cli/commands/rrr.py"})
    assert lvl == "high" and src == "deterministic_hotlist"


def test_hotlist_command_marks_high():
    lvl, src = rc.classify_risk({"title": "cleanup", "command": "rm -rf build"})
    assert lvl == "high" and src == "deterministic_hotlist"
    lvl2, _ = rc.classify_risk({"title": "rsync --delete to mirror"})
    assert lvl2 == "high"


def test_missing_risk_is_unknown_not_low():
    lvl, src = rc.classify_risk({"title": "write a harmless readme paragraph"})
    assert lvl == "unknown"
    assert src == "legacy_missing_risk"


def test_invalid_explicit_falls_through_to_hotlist():
    # garbage explicit value is ignored → deterministic path
    lvl, src = rc.classify_risk({"risk": "spicy", "title": "touch deploy script"})
    assert lvl == "high" and src == "deterministic_hotlist"


# ── evaluate_evidence_gate ──
def test_gate_high_no_verify_needs_human():
    g = rc.evaluate_evidence_gate({"risk": "high", "title": "x"})
    assert g["action"] == "needs_human"
    assert g["structural_pass"] is True
    assert g["evidence_command_present"] is False


def test_gate_low_no_verify_pass_structural():
    g = rc.evaluate_evidence_gate({"risk": "low", "title": "x"})
    assert g["action"] == "pass"
    assert g["evidence_mode"] == "structural"
    assert g["structural_pass"] is True


def test_gate_medium_no_verify_warns():
    g = rc.evaluate_evidence_gate({"risk": "medium", "title": "x"})
    assert g["action"] == "pass_with_warning"


def test_gate_verify_present_evidence_run():
    g = rc.evaluate_evidence_gate(
        {"risk": "high", "title": "x", "verify": {"command": "true", "expect_exit": 0}}
    )
    assert g["action"] == "evidence_run"
    assert g["evidence_mode"] == "evidence_command"
    assert g["structural_pass"] is False
    assert g["evidence_command_present"] is True


def test_gate_unknown_no_verify_pass_not_blocked():
    g = rc.evaluate_evidence_gate({"title": "harmless readme"})
    assert g["risk_level"] == "unknown"
    assert g["risk_source"] == "legacy_missing_risk"
    assert g["action"] == "pass"  # not blocked (backward-compat)


def test_gate_returns_all_marking_fields():
    g = rc.evaluate_evidence_gate({"risk": "low", "title": "x"})
    for k in ("risk_level", "risk_source", "evidence_mode",
              "structural_pass", "evidence_command_present", "action"):
        assert k in g
