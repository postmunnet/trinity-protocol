"""Q24.10 step 5 — aaa analyzer route priority + KPI (E1-E3,E5,E9-E12)."""
from __future__ import annotations

import json

from cli.core import aaa_analyzer as aaa


def _seed(tmp_path, *, unconfirmed=False, acceptance=True, plan_steps=None,
          audit_events=None):
    proj = tmp_path / "proj"
    sess = proj / ".ai" / "sessions" / "0001_test"
    (sess / ".state").mkdir(parents=True, exist_ok=True)
    (sess / "THINK").mkdir(parents=True, exist_ok=True)
    (proj / ".ai" / "audit").mkdir(parents=True, exist_ok=True)
    (sess / ".state" / "goal_contract_signal.json").write_text(json.dumps({
        "goal_contract_version": 1,
        "has_unconfirmed_answers": unconfirmed,
        "unconfirmed_questions": ["q2"] if unconfirmed else [],
    }))
    if acceptance:
        (sess / "THINK" / "03_ACCEPTANCE.yaml").write_text("acceptance: []\n")
    if plan_steps is not None:
        (sess / ".state" / "plan.json").write_text(json.dumps({"steps": plan_steps}))
    lines = [json.dumps(e) for e in (audit_events or [])]
    (proj / ".ai" / "audit" / "events.ndjson").write_text("\n".join(lines))
    return proj, sess


def _step_event(verdict="PASS", **details):
    t = "gogogo.step_passed" if verdict == "PASS" else "gogogo.step_failed"
    return {"type": t, "session_id": "0001_test",
            "details": {"session_id": "0001_test", **details}}


# ── E1 ──
def test_unconfirmed_goal_routes_vvv(tmp_path):
    proj, sess = _seed(tmp_path, unconfirmed=True)
    r = aaa.analyze(sess, proj)
    assert r["route"] == "vvv --amend"
    assert r["verdict"] == "RETRY"


# ── E2 ──
def test_missing_acceptance_routes_nnn(tmp_path):
    proj, sess = _seed(tmp_path, unconfirmed=False, acceptance=False)
    r = aaa.analyze(sess, proj)
    assert r["route"] == "nnn --amend"
    assert "acceptance" in " ".join(r["reasons"]).lower()


# ── E3 ──
def test_clean_no_route(tmp_path):
    proj, sess = _seed(tmp_path, unconfirmed=False, acceptance=True, plan_steps=[
        {"n": 1, "title": "harmless", "risk": "low"}
    ])
    r = aaa.analyze(sess, proj)
    assert r["route"] is None
    assert r["verdict"] == "clean"


# ── E9 ──
def test_high_risk_no_verify_routes_nnn(tmp_path):
    proj, sess = _seed(tmp_path, unconfirmed=False, acceptance=True, plan_steps=[
        {"n": 1, "title": "risky step", "risk": "high"}  # no verify.command
    ])
    r = aaa.analyze(sess, proj)
    assert r["route"] == "nnn --amend"
    assert "verify.command" in " ".join(r["reasons"])


# ── E10 ──
def test_evidence_fail_routes_gogogo(tmp_path):
    proj, sess = _seed(
        tmp_path, unconfirmed=False, acceptance=True,
        plan_steps=[{"n": 1, "title": "ok", "risk": "low",
                     "verify": {"command": "true"}}],
        audit_events=[_step_event(
            verdict="FAIL", verifier_mode="evidence_command",
            evidence_mode="evidence_command", structural_pass=False,
            evidence_command_present=True, risk_level="low",
        )],
    )
    r = aaa.analyze(sess, proj)
    assert r["route"] == "gogogo --fix"


# ── E11 ──
def test_route_priority_deterministic(tmp_path):
    # unconfirmed goal + missing acceptance at once → priority 1 (vvv) wins
    proj, sess = _seed(tmp_path, unconfirmed=True, acceptance=False)
    r = aaa.analyze(sess, proj)
    assert r["route"] == "vvv --amend"  # not nnn, despite missing acceptance


# ── E5 ──
def test_kpi_adoption_rate(tmp_path):
    proj, sess = _seed(tmp_path, unconfirmed=False, acceptance=True, audit_events=[
        _step_event(evidence_mode="evidence_command", structural_pass=False,
                    evidence_command_present=True, risk_level="low"),
        _step_event(evidence_mode="structural", structural_pass=True,
                    evidence_command_present=False, risk_level="low"),
        _step_event(evidence_mode="structural", structural_pass=True,
                    evidence_command_present=False, risk_level="low"),
    ])
    r = aaa.analyze(sess, proj)
    assert r["kpi"]["steps_measured"] == 3
    assert r["kpi"]["evidence_command_adoption_rate"] == round(1 / 3, 4)
    assert r["kpi"]["structural_pass_rate"] == round(2 / 3, 4)


# ── E12 ──
def test_kpi_scope_present(tmp_path):
    proj, sess = _seed(tmp_path)
    r = aaa.analyze(sess, proj)
    sc = r["kpi_scope"]
    assert sc["level"] == "session"
    assert sc["session_id"] == "0001_test"
    assert sc["project"] == "proj"
    assert sc["source"] == "audit_events"


def test_high_risk_without_evidence_count(tmp_path):
    proj, sess = _seed(tmp_path, audit_events=[
        _step_event(evidence_mode="structural", structural_pass=True,
                    evidence_command_present=False, risk_level="high"),
    ])
    r = aaa.analyze(sess, proj)
    assert r["kpi"]["high_risk_without_evidence_count"] == 1
