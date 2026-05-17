"""Tests for `ai rrr --hmac-envelope-file` — R35 wire-up.

Mirrors the 5 acceptance gates in the session plan:
  A_FLAG               typer surface exposes --hmac-envelope-file
  A_VALID              good envelope -> exit 0 + rrr / rrr_complete
                       transition evidence carries via='tg-bot:hmac'
  A_INVALID_SIG        bad sig -> exit 79 + rrr.hmac_rejected reason=sig_mismatch
  A_STALE_TS           ts -301s -> exit 79 + reason=ts_skew
  A_MISSING_FLAG_LOCAL no flag -> exit 0 + behavior unchanged from baseline
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from cli.commands.rrr import HMAC_REJECT_EXIT, _run, app
from cli.core.audit import AuditChain
from cli.core.auth import ENV_NAME, compute_sig
from cli.core.loop import Loop
from conftest import typer_app_has_option
from test_ddd import _seed_at_verified

SECRET = "TEST_KERNEL_SECRET_DO_NOT_REUSE"


def _ts_now_iso(offset_seconds: int = 0) -> str:
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.isoformat().replace("+00:00", "Z")


def _seed_at_deployed(tmp_path: Path):
    """Reuse test_ddd._seed_at_verified, then advance to DEPLOYED."""
    proj, sess = _seed_at_verified(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    loop.fire(
        "promote_request",
        decided_by="human",
        evidence={"reason": "test seed"},
    )
    loop.fire(
        "deploy_request",
        decided_by="human",
        evidence={"reason": "test seed"},
    )
    assert loop.current() == "DEPLOYED"
    return proj, sess


def _make_envelope(*, secret, ts_iso, tamper_sig=False):
    payload = {
        "session": "0001_session",
        "command": "rrr",
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
def test_hmac_flag_appears_in_rrr_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert typer_app_has_option(app, "--hmac-envelope-file")


# A_VALID --------------------------------------------------------------
def test_valid_envelope_stamps_via_on_rrr_transitions(tmp_path, monkeypatch):
    proj, sess = _seed_at_deployed(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    envelope = _make_envelope(secret=SECRET, ts_iso=_ts_now_iso())
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        dry_run=False,
        auto_deploy=False,
        retro_type="feat",
        baseline="HEAD",
        retroactive=False,
        session_override=None,
        hmac_envelope_file=env_path,
    )
    assert code == 0

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DONE"

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rrr_transitions = [
        ev for ev in chain.iter_events()
        if ev["type"] == "graph.transition"
        and ev["details"].get("trigger") in {"rrr", "rrr_complete"}
    ]
    assert len(rrr_transitions) == 2
    for t in rrr_transitions:
        assert t["details"]["evidence"].get("via") == "tg-bot:hmac"
        assert t["details"]["evidence"].get("hmac_nonce") == envelope["nonce"]


# A_INVALID_SIG --------------------------------------------------------
def test_invalid_sig_rejects_rrr_with_audit_event(tmp_path, monkeypatch):
    proj, sess = _seed_at_deployed(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    envelope = _make_envelope(
        secret=SECRET, ts_iso=_ts_now_iso(), tamper_sig=True
    )
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        dry_run=False,
        auto_deploy=False,
        retro_type="feat",
        baseline="HEAD",
        retroactive=False,
        session_override=None,
        hmac_envelope_file=env_path,
    )
    assert code == HMAC_REJECT_EXIT

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DEPLOYED"  # stayed at pre-rrr state

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rejects = [
        ev for ev in chain.iter_events() if ev["type"] == "rrr.hmac_rejected"
    ]
    assert len(rejects) == 1
    assert rejects[0]["details"]["reason"] == "sig_mismatch"


# A_STALE_TS -----------------------------------------------------------
def test_stale_ts_rejects_rrr(tmp_path, monkeypatch):
    proj, sess = _seed_at_deployed(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    stale_ts = _ts_now_iso(offset_seconds=-301)
    envelope = _make_envelope(secret=SECRET, ts_iso=stale_ts)
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        dry_run=False,
        auto_deploy=False,
        retro_type="feat",
        baseline="HEAD",
        retroactive=False,
        session_override=None,
        hmac_envelope_file=env_path,
    )
    assert code == HMAC_REJECT_EXIT

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rejects = [
        ev for ev in chain.iter_events() if ev["type"] == "rrr.hmac_rejected"
    ]
    assert rejects[0]["details"]["reason"] == "ts_skew"


# A_MISSING_FLAG_LOCAL -------------------------------------------------
def test_no_flag_keeps_rrr_baseline_path(tmp_path, monkeypatch):
    proj, sess = _seed_at_deployed(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.delenv(ENV_NAME, raising=False)

    code = _run(
        dry_run=False,
        auto_deploy=False,
        retro_type="feat",
        baseline="HEAD",
        retroactive=False,
        session_override=None,
        hmac_envelope_file=None,
    )
    assert code == 0

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DONE"

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rrr_transitions = [
        ev for ev in chain.iter_events()
        if ev["type"] == "graph.transition"
        and ev["details"].get("trigger") in {"rrr", "rrr_complete"}
    ]
    for t in rrr_transitions:
        assert "via" not in t["details"]["evidence"]
