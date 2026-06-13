"""Q24.10 step 3 — rrr debt gate integration (C1-C6, C9, C10).

Drives the real rrr pipeline (reusing test_ddd._seed_at_verified) with a
goal_contract_signal.json present, asserting observable closure behaviour:
block / waiver / legacy-compat / envelope summary.
"""
from __future__ import annotations

import json

import pytest
import yaml

from cli.commands.rrr import _run
from test_ddd import _seed_at_verified


def _write_signal(sess, has_unconfirmed, questions):
    (sess / ".state").mkdir(parents=True, exist_ok=True)
    (sess / ".state" / "goal_contract_signal.json").write_text(json.dumps({
        "goal_contract_version": 1,
        "has_unconfirmed_answers": has_unconfirmed,
        "unconfirmed_questions": questions,
    }))


def _run_rrr(monkeypatch, proj, *, accept_debt=False, reason=None):
    monkeypatch.chdir(proj)
    return _run(
        dry_run=False, auto_deploy=False, retro_type="feat", baseline="HEAD",
        retroactive=False, session_override=None, hmac_envelope_file=None,
        with_lessons=False, accept_debt=accept_debt, reason=reason,
    )


def _audit_types(proj):
    f = proj / ".ai" / "audit" / "events.ndjson"
    out = []
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln).get("type"))
            except json.JSONDecodeError:
                pass
    return out


def _final_state(proj, sess):
    st = json.loads((proj / ".ai" / "state" / "status.json").read_text())
    return st  # not strictly needed; DONE asserted via Loop below


# ── C1 ──
def test_block_when_unconfirmed(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    _write_signal(sess, True, ["q2", "q5"])
    code = _run_rrr(monkeypatch, proj)
    assert code == 1  # blocked, exit != 0
    # graph not advanced to DONE
    from cli.core.loop import Loop
    assert Loop(sess, graph_name="standard", project_root=proj).current() != "DONE"


# ── C5 ──
def test_audit_blocked_on_debt(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    _write_signal(sess, True, ["q1"])
    _run_rrr(monkeypatch, proj)
    assert "rrr.blocked_on_debt" in _audit_types(proj)


# ── C2 ──
def test_accept_debt_with_reason(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    _write_signal(sess, True, ["q2"])
    code = _run_rrr(monkeypatch, proj, accept_debt=True, reason="soak-test deferral")
    assert code == 0
    types = _audit_types(proj)
    assert "closed_with_debt" in types
    from cli.core.loop import Loop
    assert Loop(sess, graph_name="standard", project_root=proj).current() == "DONE"


# ── C9 ──
def test_accept_debt_requires_reason(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    _write_signal(sess, True, ["q1"])
    code = _run_rrr(monkeypatch, proj, accept_debt=True, reason=None)
    assert code == 2  # missing reason fails


# ── C3 ──
def test_legacy_no_signal_no_block(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    # no goal_contract_signal.json written → legacy session
    code = _run_rrr(monkeypatch, proj)
    assert code == 0
    assert "rrr.blocked_on_debt" not in _audit_types(proj)


# ── C4 ──
def test_no_block_when_confirmed(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    _write_signal(sess, False, [])
    code = _run_rrr(monkeypatch, proj)
    assert code == 0
    assert "rrr.blocked_on_debt" not in _audit_types(proj)


# ── C6 + C10 ──
def test_debt_summary_in_envelope(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    _write_signal(sess, True, ["q3"])
    _run_rrr(monkeypatch, proj, accept_debt=True, reason="waive for test")
    env_text = (sess / "THINK" / "retro_envelope.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(env_text.split("---", 2)[1])
    # C6: debt summary present  ·  C10: machine-readable structure
    assert "debt" in frontmatter
    assert isinstance(frontmatter["debt"], dict)
    assert frontmatter["debt"]["blocking_count"] == 1
    assert frontmatter["debt"]["debts"][0]["type"] == "unconfirmed_goal_answers"


def test_debt_summary_machine_readable(tmp_path, monkeypatch):
    # C10 explicit — envelope debt block parses as JSON-compatible dict
    proj, sess = _seed_at_verified(tmp_path)
    _write_signal(sess, False, [])  # clean → empty debts list, still structured
    _run_rrr(monkeypatch, proj)
    env_text = (sess / "THINK" / "retro_envelope.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(env_text.split("---", 2)[1])
    assert frontmatter["debt"]["debts"] == []
    assert frontmatter["debt"]["blocking_count"] == 0
