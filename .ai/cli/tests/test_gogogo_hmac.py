"""Tests for `ai gogogo --hmac-envelope-file` — R35 wire-up.

Mirrors the 5 acceptance gates in the session plan:
  A_FLAG               typer surface exposes --hmac-envelope-file
  A_VALID              good envelope -> exit 0 + gogogo_complete transition
                       evidence carries via='tg-bot:hmac'
  A_INVALID_SIG        bad sig -> exit 79 + gogogo.hmac_rejected reason=sig_mismatch
  A_STALE_TS           ts -301s -> exit 79 + reason=ts_skew
  A_MISSING_FLAG_LOCAL no flag -> exit 0 + behavior unchanged from baseline
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import typer
import yaml
from typer.testing import CliRunner

from cli.commands.gogogo import HMAC_REJECT_EXIT, _run, app
from cli.core.audit import AuditChain
from cli.core.auth import ENV_NAME, compute_sig
from cli.core.loop import Loop
from conftest import typer_app_has_option
from test_goal_loop import LOOP_BUDGET_YAML, STANDARD_GRAPH_YAML, _make_project

# Reuse the same verifier-rules.yaml loaded in test_ddd.py.
VERIFIER_RULES_YAML = (
    Path(__file__).resolve().parent.parent.parent / "policies" / "verifier-rules.yaml"
).read_text()

SECRET = "TEST_KERNEL_SECRET_DO_NOT_REUSE"


def _ts_now_iso(offset_seconds: int = 0) -> str:
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.isoformat().replace("+00:00", "Z")


def _seed_at_do(tmp_path: Path):
    """Build project + session, advance to DO state, write a tiny plan."""
    proj, sess = _make_project(tmp_path, with_budget=True)
    # Wire the real rituals tree into the tmp project so gogogo.py's
    # load_pack call (which resolves rituals_root from project_root since
    # the per-ritual loader integration in this session) finds the pack.
    rituals_target = proj / ".ai" / "rituals"
    if not rituals_target.exists():
        rituals_target.symlink_to(
            Path(__file__).resolve().parent.parent.parent / "rituals"
        )
    (proj / ".ai" / "policies" / "verifier-rules.yaml").write_text(VERIFIER_RULES_YAML)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({"version": "1.0", "current_session": str(sess)})
    )

    loop = Loop(sess, graph_name="standard", project_root=proj)
    loop.fire("sss", decided_by="kernel")
    loop.fire("nnn_pass", decided_by="kernel")
    loop.fire("vvv_pass", decided_by="verifier")
    assert loop.current() == "DO"

    (sess / ".state" / "vvv_pass").write_text("ok")
    (sess / ".state" / "nnn_pass").write_text("ok")
    (sess / ".state" / "plan.json").write_text(
        json.dumps({"steps": [{"n": 1, "title": "smoke step"}]})
    )
    return proj, sess


def _make_envelope(*, secret, ts_iso, tamper_sig=False):
    payload = {
        "session": "0001_session",
        "command": "gogogo",
        "args": [],
        "ts": ts_iso,
        "nonce": "abcdef0123456789",
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = compute_sig(payload_bytes, secret)
    if tamper_sig:
        sig = "0" * len(sig)
    return {**payload, "sig": sig}


def _write_envelope(tmp_path: Path, envelope: dict) -> Path:
    p = tmp_path / "envelope.json"
    p.write_text(json.dumps(envelope), encoding="utf-8")
    return p


# A_FLAG ---------------------------------------------------------------
def test_hmac_flag_appears_in_gogogo_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert typer_app_has_option(app, "--hmac-envelope-file")


# A_VALID --------------------------------------------------------------
def test_valid_envelope_stamps_via_on_gogogo_complete(tmp_path, monkeypatch):
    proj, sess = _seed_at_do(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    envelope = _make_envelope(secret=SECRET, ts_iso=_ts_now_iso())
    env_path = _write_envelope(tmp_path, envelope)

    _run("step_complete", False, hmac_envelope_file=env_path)

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    transitions = [
        ev for ev in chain.iter_events()
        if ev["type"] == "graph.transition"
        and ev["details"].get("trigger") == "gogogo_complete"
    ]
    assert len(transitions) == 1
    ev = transitions[0]["details"]["evidence"]
    assert ev.get("via") == "tg-bot:hmac"
    assert ev.get("hmac_nonce") == envelope["nonce"]


# A_INVALID_SIG --------------------------------------------------------
def test_invalid_sig_rejects_gogogo_with_audit_event(tmp_path, monkeypatch):
    proj, sess = _seed_at_do(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    envelope = _make_envelope(
        secret=SECRET, ts_iso=_ts_now_iso(), tamper_sig=True
    )
    env_path = _write_envelope(tmp_path, envelope)

    with pytest.raises(typer.Exit) as exc:
        _run("step_complete", False, hmac_envelope_file=env_path)
    assert exc.value.exit_code == HMAC_REJECT_EXIT

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DO"  # no transition fired

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rejects = [
        ev for ev in chain.iter_events() if ev["type"] == "gogogo.hmac_rejected"
    ]
    assert len(rejects) == 1
    assert rejects[0]["details"]["reason"] == "sig_mismatch"


# A_STALE_TS -----------------------------------------------------------
def test_stale_ts_rejects_gogogo(tmp_path, monkeypatch):
    proj, sess = _seed_at_do(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    stale_ts = _ts_now_iso(offset_seconds=-301)
    envelope = _make_envelope(secret=SECRET, ts_iso=stale_ts)
    env_path = _write_envelope(tmp_path, envelope)

    with pytest.raises(typer.Exit) as exc:
        _run("step_complete", False, hmac_envelope_file=env_path)
    assert exc.value.exit_code == HMAC_REJECT_EXIT

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rejects = [
        ev for ev in chain.iter_events() if ev["type"] == "gogogo.hmac_rejected"
    ]
    assert rejects[0]["details"]["reason"] == "ts_skew"


# A_MISSING_FLAG_LOCAL -------------------------------------------------
def test_no_flag_keeps_gogogo_baseline_path(tmp_path, monkeypatch):
    proj, sess = _seed_at_do(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.delenv(ENV_NAME, raising=False)

    _run("step_complete", False, hmac_envelope_file=None)

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    transitions = [
        ev for ev in chain.iter_events()
        if ev["type"] == "graph.transition"
        and ev["details"].get("trigger") == "gogogo_complete"
    ]
    assert len(transitions) == 1
    ev = transitions[0]["details"]["evidence"]
    # No HMAC stamping when flag absent.
    assert "via" not in ev
