"""Q24.10 step 4 — gogogo risk-graduated evidence enforcement (D1-D11).

opt-A: structural PASS stays allowed for low-risk (backward compat) but is
marked in audit; high-risk without evidence stops as NEEDS_HUMAN. The gate
decision (risk_classifier.evaluate_evidence_gate) is exercised directly;
integration assertions confirm gogogo wires it + the evidence path's
DEAD-on-failure behaviour is unchanged (D11).
"""
from __future__ import annotations

import inspect

from cli.core import risk_classifier as rc
from cli.commands import gogogo


# ── D1 ──
def test_high_risk_no_verify_needs_human():
    g = rc.evaluate_evidence_gate({"risk": "high", "title": "touch kernel"})
    assert g["action"] == "needs_human"
    # gogogo routes needs_human → NEEDS_HUMAN verdict + stop (not structural PASS)
    src = inspect.getsource(gogogo)
    assert 'verifier_verdict": "NEEDS_HUMAN"' in src
    assert "risk_gate" in src


# ── D2 ──
def test_low_risk_no_verify_structural_pass():
    g = rc.evaluate_evidence_gate({"risk": "low", "title": "x"})
    assert g["action"] == "pass"
    assert g["structural_pass"] is True
    assert g["evidence_mode"] == "structural"


# ── D3 ──
def test_verify_command_evidence_mode():
    g = rc.evaluate_evidence_gate(
        {"risk": "low", "title": "x", "verify": {"command": "true", "expect_exit": 0}}
    )
    assert g["evidence_mode"] == "evidence_command"
    assert g["action"] == "evidence_run"


# ── D4 ──
def test_audit_marks_every_step():
    # every gate result carries the machine-readable marking fields, and
    # gogogo stamps them onto each verdict event (**evidence_marking).
    for step in ({"risk": "low"}, {"risk": "medium"}, {"risk": "high"},
                 {"verify": {"command": "true", "expect_exit": 0}}, {}):
        g = rc.evaluate_evidence_gate(step)
        for k in ("risk_level", "risk_source", "evidence_mode",
                  "structural_pass", "evidence_command_present"):
            assert k in g
    src = inspect.getsource(gogogo)
    assert "evidence_marking" in src and "**evidence_marking" in src


# ── D7 ──
def test_structural_pass_rate_computable():
    steps = [
        {"risk": "low"},                                          # structural
        {"risk": "low", "verify": {"command": "true"}},           # evidence
        {"risk": "medium"},                                       # structural
    ]
    gates = [rc.evaluate_evidence_gate(s) for s in steps]
    structural = sum(1 for g in gates if g["structural_pass"])
    rate = structural / len(gates)
    assert structural == 2
    assert abs(rate - 2 / 3) < 1e-9


# ── D8 ──
def test_legacy_missing_risk_unknown():
    g = rc.evaluate_evidence_gate({"title": "harmless readme edit"})
    assert g["risk_level"] == "unknown"
    assert g["risk_source"] == "legacy_missing_risk"
    assert g["action"] == "pass"  # not blocked


# ── D9 ──
def test_medium_risk_no_verify_warns():
    g = rc.evaluate_evidence_gate({"risk": "medium", "title": "x"})
    assert g["action"] == "pass_with_warning"
    assert g["structural_pass"] is True


# ── D10 ──
def test_high_risk_verify_pass():
    g = rc.evaluate_evidence_gate(
        {"risk": "high", "title": "x", "verify": {"command": "true", "expect_exit": 0}}
    )
    assert g["action"] == "evidence_run"
    assert g["structural_pass"] is False  # evidence-backed, not structural


# ── D11 (updated per ADR-0001) ──
def test_high_risk_verify_fail_not_needs_human():
    # high-risk WITH verify → the GATE runs the evidence command (it does not
    # escalate to needs_human at gate time). Per ADR-0001, a *failing* evidence
    # command is a recoverable failure → NEEDS_HUMAN, not DEAD (supersedes the
    # earlier D11 "evidence failure is DEAD" labelling).
    g = rc.evaluate_evidence_gate(
        {"risk": "high", "title": "x", "verify": {"command": "false", "expect_exit": 0}}
    )
    assert g["action"] == "evidence_run"
    assert g["action"] != "needs_human"
    src = inspect.getsource(gogogo)
    # evidence-failure branch emits NEEDS_HUMAN (ADR-0001); reason_code pins it
    assert 'verifier_verdict": "NEEDS_HUMAN"' in src
    assert "evidence_command_failed" in src
