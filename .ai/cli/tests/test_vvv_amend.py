"""Q24.10 step 2 — vvv --amend + answer-source tracking (B1-B10).

vvv is the semantic owner of the goal contract; artifact_version is the
storage layer. Step 2 tracks/queries answer confirmation; it does NOT
enforce. Every test checks observable state (no structural PASS).
"""
from __future__ import annotations

import json

import pytest
import yaml

from test_goal_loop import _make_project
from cli.core import artifact_version as av
from cli.commands import vvv as vvv_mod


ANS = {
    1: "build feature X",
    2: "in: A,B  out: C",
    3: "no policies/schemas",
    4: "pytest green",
    5: "regression",
}


def _seed_contract_v1(tmp_path):
    proj, sess = _make_project(tmp_path)
    contract = vvv_mod._build_goal_contract(ANS, sess.name, 1)
    av.write_version(sess, "goal_contract", contract, 1)
    vvv_mod._write_goal_signal(sess)
    return proj, sess


def _seed_for_cli(tmp_path):
    proj, sess = _seed_contract_v1(tmp_path)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps(
            {"version": "1.0", "current_session": str(sess), "last_event_hash": None}
        )
    )
    return proj, sess


def _audit_types(proj):
    f = proj / ".ai" / "audit" / "events.ndjson"
    if not f.exists():
        return []
    out = []
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln).get("type"))
            except json.JSONDecodeError:
                pass
    return out


# ── B1 ──
def test_initial_creates_v1(tmp_path):
    proj, sess = _seed_contract_v1(tmp_path)
    assert (sess / ".state" / "goal_contract.v1.json").exists()
    c = av.resolve_latest(sess, "goal_contract")
    assert c["version"] == 1
    assert set(c["questions"]) == {"q1", "q2", "q3", "q4", "q5"}
    assert c["questions"]["q1"]["answer"] == "build feature X"


# ── B3 ──
def test_default_answer_source_conservative(tmp_path):
    proj, sess = _seed_contract_v1(tmp_path)
    c = av.resolve_latest(sess, "goal_contract")
    for qid, q in c["questions"].items():
        assert q["answered_by"] == "agent_draft", qid
        assert q["human_confirmed"] is False, qid
        assert q["confirmed_at"] is None, qid


# ── B4 ──
def test_confirm_per_question(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    monkeypatch.chdir(proj)
    vvv_mod._run_confirm("1,2", None)
    c = av.resolve_latest(sess, "goal_contract")
    assert c["questions"]["q1"]["human_confirmed"] is True
    assert c["questions"]["q1"]["answered_by"] == "human"
    assert c["questions"]["q1"]["confirmed_at"] is not None
    assert c["questions"]["q2"]["human_confirmed"] is True
    # q3 untouched
    assert c["questions"]["q3"]["human_confirmed"] is False


# ── B2 ──
def test_amend_creates_v2_preserves_v1(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    v1_before = (sess / ".state" / "goal_contract.v1.json").read_text()
    monkeypatch.chdir(proj)
    vvv_mod._run_amend(["2=new scope: A,B,D"], None, "scope expanded", None)
    # v1 immutable
    assert (sess / ".state" / "goal_contract.v1.json").read_text() == v1_before
    assert (sess / ".state" / "goal_contract.v2.json").exists()
    c = av.resolve_latest(sess, "goal_contract")
    assert c["version"] == 2
    assert c["questions"]["q2"]["answer"] == "new scope: A,B,D"
    # amended answer reverts to unconfirmed
    assert c["questions"]["q2"]["human_confirmed"] is False


# ── B5 ──
def test_amendment_record_fields(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    monkeypatch.chdir(proj)
    vvv_mod._run_amend(["4=new acceptance"], None, "tighten gate", None)
    recs = av.list_amendment_records(sess, "goal_contract")
    assert recs and recs[-1]["reason"] == "tighten gate"
    assert recs[-1]["from_version"] == 1 and recs[-1]["to_version"] == 2
    assert recs[-1]["changes"] == ["q4"]


# ── B6 ──
def test_history_lists_versions(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    monkeypatch.chdir(proj)
    vvv_mod._run_amend(["1=changed goal"], None, "r", None)
    assert av.list_versions(sess, "goal_contract") == [1, 2]
    # --history runs without error
    vvv_mod._run_history(None)


# ── B7 ──
def test_audit_proposed_and_applied(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    monkeypatch.chdir(proj)
    vvv_mod._run_amend(["3=new constraint"], None, "constraint change", None)
    types = _audit_types(proj)
    assert "goal_amend_proposed" in types
    assert "goal_contract_amended" in types
    assert "active_goal_contract_changed" in types


# ── B8 ──
def test_query_unconfirmed(tmp_path):
    proj, sess = _seed_contract_v1(tmp_path)
    c = av.resolve_latest(sess, "goal_contract")
    unconfirmed = vvv_mod._unconfirmed_questions(c)
    assert set(unconfirmed) == {"q1", "q2", "q3", "q4", "q5"}  # all, initially


# ── B9 ──
def test_resolver_latest_and_historical(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    monkeypatch.chdir(proj)
    vvv_mod._run_amend(["5=new risk"], None, "risk update", None)
    assert av.active_version(sess, "goal_contract") == 2
    assert av.resolve_latest(sess, "goal_contract")["version"] == 2
    v1 = json.loads((sess / ".state" / "goal_contract.v1.json").read_text())
    assert v1["version"] == 1 and v1["questions"]["q5"]["answer"] == "regression"


# ── B10 ──
def test_unconfirmed_signal_exposed(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    sig = json.loads((sess / ".state" / "goal_contract_signal.json").read_text())
    assert sig["has_unconfirmed_answers"] is True
    assert set(sig["unconfirmed_questions"]) == {"q1", "q2", "q3", "q4", "q5"}
    # after confirming all, signal flips
    monkeypatch.chdir(proj)
    vvv_mod._run_confirm("1,2,3,4,5", None)
    sig2 = json.loads((sess / ".state" / "goal_contract_signal.json").read_text())
    assert sig2["has_unconfirmed_answers"] is False
    assert sig2["unconfirmed_questions"] == []
