"""Tests for core/auth.py — Decision Y HMAC verify shim."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cli.core.auth import (
    DEFAULT_MAX_SKEW_SECONDS,
    ENV_NAME,
    compute_sig,
    verify_hmac,
)


SECRET = "TEST_KERNEL_SECRET_DO_NOT_REUSE"
PAYLOAD = b'{"session":"s1","command":"ddd","args":["target=prod"],"ts":"2026-05-02T00:00:00Z","nonce":"abc"}'


def _ts_now_iso(offset_seconds: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat().replace("+00:00", "Z")


def test_verify_happy_path(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    sig = compute_sig(PAYLOAD, SECRET)
    ok, reason = verify_hmac(PAYLOAD, sig, _ts_now_iso())
    assert ok is True
    assert reason == "ok"


def test_verify_no_secret(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)
    sig = compute_sig(PAYLOAD, SECRET)
    ok, reason = verify_hmac(PAYLOAD, sig, _ts_now_iso())
    assert ok is False
    assert reason == "no_secret"


def test_verify_sig_mismatch(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    bad_sig = compute_sig(b"different payload", SECRET)
    ok, reason = verify_hmac(PAYLOAD, bad_sig, _ts_now_iso())
    assert ok is False
    assert reason == "sig_mismatch"


def test_verify_wrong_secret_fails(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    sig = compute_sig(PAYLOAD, "WRONG_SECRET")
    ok, reason = verify_hmac(PAYLOAD, sig, _ts_now_iso())
    assert ok is False
    assert reason == "sig_mismatch"


def test_verify_ts_too_old(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    sig = compute_sig(PAYLOAD, SECRET)
    old_ts = _ts_now_iso(-600)  # 10 min ago, beyond 5min window
    ok, reason = verify_hmac(PAYLOAD, sig, old_ts)
    assert ok is False
    assert reason == "ts_skew"


def test_verify_ts_in_future(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    sig = compute_sig(PAYLOAD, SECRET)
    future_ts = _ts_now_iso(600)
    ok, reason = verify_hmac(PAYLOAD, sig, future_ts)
    assert ok is False
    assert reason == "ts_skew"


def test_verify_malformed_ts(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    sig = compute_sig(PAYLOAD, SECRET)
    ok, reason = verify_hmac(PAYLOAD, sig, "not-a-timestamp")
    assert ok is False
    assert reason == "malformed_ts"


def test_verify_bad_input_payload(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    sig = compute_sig(PAYLOAD, SECRET)
    ok, reason = verify_hmac("not bytes", sig, _ts_now_iso())  # type: ignore[arg-type]
    assert ok is False
    assert reason == "bad_input"


def test_verify_bad_input_sig(monkeypatch):
    monkeypatch.setenv(ENV_NAME, SECRET)
    ok, reason = verify_hmac(PAYLOAD, "", _ts_now_iso())
    assert ok is False
    assert reason == "bad_input"


def test_compute_sig_deterministic():
    a = compute_sig(PAYLOAD, SECRET)
    b = compute_sig(PAYLOAD, SECRET)
    assert a == b
    assert len(a) == 64  # sha256 hex
    assert all(c in "0123456789abcdef" for c in a)


def test_default_max_skew_is_300s():
    assert DEFAULT_MAX_SKEW_SECONDS == 300


# R35: shared envelope loader -----------------------------------------
def test_load_hmac_envelope_byte_parity_and_sig_strip(tmp_path):
    """Helper extracted from ddd.py — strips sig key, re-serializes
    canonical bytes matching JS JSON.stringify insertion order."""
    import json
    from cli.core.auth import load_hmac_envelope

    envelope = {
        "session": "s1",
        "command": "ddd",
        "args": ["target=dev"],
        "ts": "2026-05-10T10:00:00Z",
        "nonce": "deadbeef",
        "user_id": 12345,
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


def test_load_hmac_envelope_rejects_missing_sig(tmp_path):
    import json
    from cli.core.auth import load_hmac_envelope

    p = tmp_path / "env.json"
    p.write_text(json.dumps({"session": "s", "ts": "2026-01-01T00:00:00Z"}), encoding="utf-8")
    with pytest.raises(ValueError, match="sig"):
        load_hmac_envelope(p)
