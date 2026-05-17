"""Tests for `ai ddd --hmac-envelope-file` — Decision Y wire-up.

Mirrors the 6 acceptance gates in the session plan:
  A_FLAG               typer surface exposes --hmac-envelope-file
  A_VALID              good envelope -> exit 0 + audit decided_by=human:tg:bot
  A_INVALID_SIG        bad sig -> exit 79 + ddd.hmac_rejected reason=sig_mismatch
  A_STALE_TS           ts -301s -> exit 79 + reason=ts_skew
  A_MISSING_FLAG_LOCAL no flag -> exit 0 + decided_by=human (legacy path)
  A_REGRESSION_AUTH    covered by test_auth.py (no new code in core/auth.py)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.commands.ddd import _run, app, HMAC_REJECT_EXIT
from cli.core.audit import AuditChain
from cli.core.auth import ENV_NAME, compute_sig, load_hmac_envelope
from cli.core.loop import Loop
from test_ddd import _seed_at_verified

SECRET = "TEST_KERNEL_SECRET_DO_NOT_REUSE"


def _ts_now_iso(offset_seconds: int = 0) -> str:
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.isoformat().replace("+00:00", "Z")


def _make_envelope(
    *,
    secret: str,
    ts_iso: str,
    session: str = "0001_session",
    command: str = "ddd",
    args: list | None = None,
    nonce: str = "abcdef0123456789",
    tamper_sig: bool = False,
    user_id=None,
) -> dict:
    payload = {
        "session": session,
        "command": command,
        "args": args if args is not None else ["target=dev"],
        "ts": ts_iso,
        "nonce": nonce,
    }
    if user_id is not None:
        # Insertion order matches bot's lib/hmac.js v0.3.1 — the user_id
        # key is appended AFTER nonce so canonical bytes are deterministic.
        payload["user_id"] = user_id
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = compute_sig(payload_bytes, secret)
    if tamper_sig:
        sig = "0" * len(sig)
    return {**payload, "sig": sig}


def _write_envelope(tmp_path: Path, envelope: dict) -> Path:
    p = tmp_path / "envelope.json"
    p.write_text(json.dumps(envelope), encoding="utf-8")
    return p


# A_FLAG ----------------------------------------------------------------
def test_hmac_flag_appears_in_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--hmac-envelope-file" in result.stdout


# A_VALID ---------------------------------------------------------------
def test_valid_envelope_stamps_tg_bot_decided_by(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    envelope = _make_envelope(secret=SECRET, ts_iso=_ts_now_iso())
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        target="dev",
        reason="hmac valid path",
        evidence_file=None,
        skip_verify=True,
        dry_run=False,
        hmac_envelope_file=env_path,
    )
    assert code == 0
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DEPLOYED"

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    completed = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.completed"
    ]
    assert len(completed) == 1
    assert completed[0]["details"]["decided_by"] == "human:tg:bot"

    # Graph schema locks decided_by='human' on promote/deploy transitions,
    # so transport identity rides on evidence.via instead.
    transitions = [
        ev for ev in chain.iter_events()
        if ev["type"] == "graph.transition"
        and ev["details"].get("trigger") in {"promote_request", "deploy_request"}
    ]
    assert len(transitions) == 2
    for t in transitions:
        assert t["details"]["decided_by"] == "human"
        assert t["details"]["evidence"]["via"] == "tg-bot:hmac"
        assert t["details"]["evidence"].get("hmac_nonce")


# A_INVALID_SIG ---------------------------------------------------------
def test_invalid_sig_rejects_with_audit_event(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    envelope = _make_envelope(
        secret=SECRET, ts_iso=_ts_now_iso(), tamper_sig=True
    )
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        target="dev",
        reason="hmac bad sig",
        evidence_file=None,
        skip_verify=True,
        dry_run=False,
        hmac_envelope_file=env_path,
    )
    assert code == HMAC_REJECT_EXIT

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"  # no transitions fired

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rejects = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.hmac_rejected"
    ]
    assert len(rejects) == 1
    assert rejects[0]["details"]["reason"] == "sig_mismatch"
    assert rejects[0]["details"]["session_id"] == sess.name


# A_STALE_TS ------------------------------------------------------------
def test_stale_ts_rejects_with_ts_skew_reason(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    stale_ts = _ts_now_iso(offset_seconds=-301)
    envelope = _make_envelope(secret=SECRET, ts_iso=stale_ts)
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        target="dev",
        reason="hmac stale ts",
        evidence_file=None,
        skip_verify=True,
        dry_run=False,
        hmac_envelope_file=env_path,
    )
    assert code == HMAC_REJECT_EXIT

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rejects = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.hmac_rejected"
    ]
    assert len(rejects) == 1
    assert rejects[0]["details"]["reason"] == "ts_skew"
    assert rejects[0]["details"]["ts_iso"] == stale_ts


# A_MISSING_FLAG_LOCAL --------------------------------------------------
def test_no_flag_keeps_local_human_path(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    # Secret intentionally unset — local path should not require it.
    monkeypatch.delenv(ENV_NAME, raising=False)

    code = _run(
        target="dev",
        reason="legacy local",
        evidence_file=None,
        skip_verify=True,
        dry_run=False,
        hmac_envelope_file=None,
    )
    assert code == 0
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DEPLOYED"

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    completed = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.completed"
    ]
    assert completed[0]["details"]["decided_by"] == "human"


# Bonus: bad envelope file shape -> bad_envelope reason ----------------
def test_bad_envelope_file_rejects(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    bad = tmp_path / "broken.json"
    bad.write_text("{ this is not valid JSON ", encoding="utf-8")

    code = _run(
        target="dev",
        reason="bad file",
        evidence_file=None,
        skip_verify=True,
        dry_run=False,
        hmac_envelope_file=bad,
    )
    assert code == HMAC_REJECT_EXIT

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    rejects = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.hmac_rejected"
    ]
    assert len(rejects) == 1
    assert rejects[0]["details"]["reason"] == "bad_envelope"


# R34 — user_id binding -----------------------------------------------
def test_valid_envelope_with_user_id_stamps_concrete_id(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    envelope = _make_envelope(
        secret=SECRET, ts_iso=_ts_now_iso(), user_id=99887766
    )
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        target="dev",
        reason="hmac with user_id",
        evidence_file=None,
        skip_verify=True,
        dry_run=False,
        hmac_envelope_file=env_path,
    )
    assert code == 0

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    completed = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.completed"
    ]
    assert len(completed) == 1
    assert completed[0]["details"]["decided_by"] == "human:tg:99887766"

    transitions = [
        ev for ev in chain.iter_events()
        if ev["type"] == "graph.transition"
        and ev["details"].get("trigger") in {"promote_request", "deploy_request"}
    ]
    assert len(transitions) == 2
    for t in transitions:
        assert t["details"]["evidence"]["hmac_user_id"] == 99887766


def test_envelope_without_user_id_falls_back_to_anonymous_bot(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv(ENV_NAME, SECRET)

    # 5-field envelope (legacy bot v0.3.0) — no user_id key.
    envelope = _make_envelope(secret=SECRET, ts_iso=_ts_now_iso())
    assert "user_id" not in envelope
    env_path = _write_envelope(tmp_path, envelope)

    code = _run(
        target="dev",
        reason="hmac legacy 5-field",
        evidence_file=None,
        skip_verify=True,
        dry_run=False,
        hmac_envelope_file=env_path,
    )
    assert code == 0

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    completed = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.completed"
    ]
    assert completed[0]["details"]["decided_by"] == "human:tg:bot"

    transitions = [
        ev for ev in chain.iter_events()
        if ev["type"] == "graph.transition"
        and ev["details"].get("trigger") in {"promote_request", "deploy_request"}
    ]
    for t in transitions:
        assert t["details"]["evidence"]["hmac_user_id"] is None


# Helper unit: canonical payload byte parity ----------------------------
def test_load_hmac_envelope_strips_sig_and_keeps_order(tmp_path):
    envelope = {
        "session": "s1",
        "command": "ddd",
        "args": ["target=dev"],
        "ts": "2026-05-10T10:00:00Z",
        "nonce": "deadbeef",
        "sig": "ff" * 32,
    }
    p = tmp_path / "env.json"
    p.write_text(json.dumps(envelope), encoding="utf-8")
    raw, payload_bytes, sig, ts_iso = load_hmac_envelope(p)
    expected = json.dumps(
        {k: v for k, v in envelope.items() if k != "sig"},
        separators=(",", ":"),
    ).encode("utf-8")
    assert payload_bytes == expected
    assert sig == envelope["sig"]
    assert ts_iso == envelope["ts"]
    assert raw == envelope
