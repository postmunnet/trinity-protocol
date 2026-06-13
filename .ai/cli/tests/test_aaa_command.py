"""Q24.10 step 5 — ai aaa command: JSON+panel (E4) + read-only (E6)."""
from __future__ import annotations

import json

from cli.commands.aaa import _run
from test_ddd import _seed_at_verified


def _seed(tmp_path):
    proj, sess = _seed_at_verified(tmp_path)
    # confirmed goal signal so aaa has a clean baseline to analyze
    (sess / ".state" / "goal_contract_signal.json").write_text(json.dumps({
        "goal_contract_version": 1, "has_unconfirmed_answers": False,
        "unconfirmed_questions": [],
    }))
    return proj, sess


def _audit_lines(proj):
    f = proj / ".ai" / "audit" / "events.ndjson"
    return f.read_text(encoding="utf-8").splitlines() if f.exists() else []


# ── E4 ──
def test_json_and_panel(tmp_path, monkeypatch, capsys):
    proj, sess = _seed(tmp_path)
    monkeypatch.chdir(proj)
    # JSON mode → parseable structured output
    assert _run(json_out=True, session_override=None) == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "verdict" in payload and "route" in payload and "kpi_scope" in payload

    # panel mode → human text contains Verdict
    assert _run(json_out=False, session_override=None) == 0
    out2 = capsys.readouterr().out
    assert "Verdict" in out2


# ── E6 ──
def test_read_only(tmp_path, monkeypatch):
    proj, sess = _seed(tmp_path)
    monkeypatch.chdir(proj)
    before = _audit_lines(proj)
    _run(json_out=True, session_override=None)
    _run(json_out=False, session_override=None)
    after = _audit_lines(proj)
    # aaa must not append any audit event (no state mutation / no transition)
    assert before == after
