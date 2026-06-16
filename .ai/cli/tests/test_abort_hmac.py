"""ai abort --hmac-envelope-file — remote (tg-bot) transport, mirror ddd.

Tests the verification helper directly (no session-pointer setup needed):
a valid envelope yields the human:tg transport tag; a bad envelope or a
tampered signature is rejected (None) with an abort.hmac_rejected audit event;
and direct _abort (no envelope) still fires with decided_by='human'.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cli.commands.abort import _abort, _verify_transport
from cli.core.audit import get_chain_for_project
from cli.core.auth import ENV_NAME, compute_sig
from cli.core.loop import Loop

from test_goal_loop import _make_project
from test_t04_dead_entry import STANDARD_WITH_DEAD

SECRET = "TEST_KERNEL_SECRET_DO_NOT_REUSE"


def _ts_now_iso(offset_seconds: int = 0) -> str:
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.isoformat().replace("+00:00", "Z")


def _make_envelope(*, secret: str, ts_iso: str, user_id=None, tamper_sig: bool = False) -> dict:
    payload = {
        "session": "0001_session",
        "command": "abort",
        "args": ["reason=remote abort"],
        "ts": ts_iso,
        "nonce": "abcdef0123456789",
    }
    if user_id is not None:
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


def _chain(tmp_path: Path):
    project, _ = _make_project(tmp_path, graphs={"standard": STANDARD_WITH_DEAD})
    return get_chain_for_project(project)


def _events(chain, etype):
    return [e for e in chain.iter_events() if e.get("type") == etype]


def test_valid_envelope_returns_tg_user_transport_tag(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    chain = _chain(tmp_path)
    env_path = _write_envelope(tmp_path, _make_envelope(secret=SECRET, ts_iso=_ts_now_iso(), user_id=42))
    extra = _verify_transport(env_path, "sess1", chain)
    assert extra is not None
    assert extra["decided_by_attr"] == "human:tg:42"
    assert extra["via"] == "tg-bot:hmac"
    assert extra["hmac_nonce"] == "abcdef0123456789"


def test_valid_envelope_without_user_id_falls_back_to_bot(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    chain = _chain(tmp_path)
    env_path = _write_envelope(tmp_path, _make_envelope(secret=SECRET, ts_iso=_ts_now_iso()))
    extra = _verify_transport(env_path, "sess1", chain)
    assert extra is not None
    assert extra["decided_by_attr"] == "human:tg:bot"


def test_bad_envelope_rejects_with_audit(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    chain = _chain(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    extra = _verify_transport(bad, "sess1", chain)
    assert extra is None
    assert _events(chain, "abort.hmac_rejected")
    assert _events(chain, "transport.envelope_refused.badkey")


def test_invalid_sig_rejects_with_audit(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    chain = _chain(tmp_path)
    env_path = _write_envelope(
        tmp_path, _make_envelope(secret=SECRET, ts_iso=_ts_now_iso(), tamper_sig=True)
    )
    extra = _verify_transport(env_path, "sess1", chain)
    assert extra is None
    rej = _events(chain, "abort.hmac_rejected")
    assert rej and rej[-1]["details"]["reason"] == "sig_mismatch"


def test_direct_abort_no_envelope_keeps_decided_by_human(tmp_path):
    project, session = _make_project(tmp_path, graphs={"standard": STANDARD_WITH_DEAD})
    Loop(session, graph_name="standard", project_root=project).state.set_graph_state("DO")
    new_state = _abort(session, project, reason="direct cli abort", evidence_extra=None)
    assert new_state == "DEAD"
    loop = Loop(session, graph_name="standard", project_root=project)
    d = [
        e for e in loop.chain.iter_events()
        if e.get("type") == "graph.transition" and e["details"].get("to_state") == "DEAD"
    ][-1]["details"]
    assert d["decided_by"] == "human"  # graph contract unchanged
    assert "decided_by_attr" not in d["evidence"]  # no transport tag for direct CLI
