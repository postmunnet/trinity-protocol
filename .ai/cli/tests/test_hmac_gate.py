"""Phase 9 — shared hmac_gate helper tests."""
from __future__ import annotations

import hashlib
import hmac as _hmac
import importlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import typer

from cli.core.audit import AuditChain
from cli.core.hmac_gate import HMAC_REJECT_EXIT, enforce_hmac_or_exit

SECRET = "TEST_KERNEL_SECRET_DO_NOT_REUSE"
ENV = "TRINITY_KERNEL_HMAC_SECRET"


def _ts_now_iso(offset_seconds: int = 0) -> str:
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.isoformat().replace("+00:00", "Z")


def _make_envelope_file(tmp_path: Path, secret: str = SECRET, ts: str = None) -> Path:
    ts = ts or _ts_now_iso()
    # Insertion-order matters: load_hmac_envelope canonicalises by removing
    # 'sig' and re-serialising WITHOUT sort_keys — so the signing-side and
    # loading-side must use the same dict key order.
    payload = {
        "session": "0001_test",
        "command": "sss",
        "args": ["my-task"],
        "ts": ts,
        "nonce": "abcdef0123456789",
        "user_id": "operator:test",
    }
    canonical = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = _hmac.new(secret.encode(), canonical, hashlib.sha256).hexdigest()
    envelope = dict(payload, sig=sig)
    p = tmp_path / "envelope.json"
    p.write_text(json.dumps(envelope), encoding="utf-8")
    return p


def _fresh_chain(tmp_path: Path) -> AuditChain:
    return AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.hmac_gate")
    assert hasattr(mod, "enforce_hmac_or_exit")
    assert HMAC_REJECT_EXIT == 79


def test_none_envelope_returns_none_bypass(tmp_path: Path) -> None:
    chain = _fresh_chain(tmp_path)
    result = enforce_hmac_or_exit(
        hmac_envelope_file=None,
        chain=chain,
        ritual="sss",
        session_id="0001_test",
    )
    assert result is None
    # No audit row appended on bypass.
    assert not chain.path.exists() or chain.path.stat().st_size == 0


def test_bad_envelope_path_rejects(tmp_path: Path) -> None:
    chain = _fresh_chain(tmp_path)
    with pytest.raises(typer.Exit) as exc:
        enforce_hmac_or_exit(
            hmac_envelope_file=tmp_path / "nonexistent.json",
            chain=chain,
            ritual="sss",
            session_id="0001_test",
        )
    assert exc.value.exit_code == HMAC_REJECT_EXIT
    rows = list(chain.iter_events())
    assert len(rows) == 1
    assert rows[0]["type"] == "sss.hmac_rejected"
    assert rows[0]["details"]["reason"] == "bad_envelope"


def test_invalid_signature_rejects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(ENV, SECRET)
    env_path = _make_envelope_file(tmp_path, secret="WRONG_SECRET")
    chain = _fresh_chain(tmp_path)
    with pytest.raises(typer.Exit) as exc:
        enforce_hmac_or_exit(
            hmac_envelope_file=env_path,
            chain=chain,
            ritual="vvv",
            session_id="0001_test",
        )
    assert exc.value.exit_code == HMAC_REJECT_EXIT
    rows = list(chain.iter_events())
    assert rows[0]["type"] == "vvv.hmac_rejected"


def test_valid_signature_returns_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(ENV, SECRET)
    env_path = _make_envelope_file(tmp_path)
    chain = _fresh_chain(tmp_path)
    evidence = enforce_hmac_or_exit(
        hmac_envelope_file=env_path,
        chain=chain,
        ritual="nnn",
        session_id="0001_test",
    )
    assert evidence is not None
    assert evidence["via"] == "tg-bot:hmac"
    assert evidence["hmac_user_id"] == "operator:test"
    assert "hmac_ts" in evidence
    assert "hmac_nonce" in evidence
    # No reject row.
    assert not chain.path.exists() or all(
        "hmac_rejected" not in e["type"] for e in chain.iter_events()
    )


@pytest.mark.parametrize("ritual", ["sss", "vvv", "nnn", "close"])
def test_ritual_name_flows_into_event_type(tmp_path: Path, ritual: str) -> None:
    chain = _fresh_chain(tmp_path)
    with pytest.raises(typer.Exit):
        enforce_hmac_or_exit(
            hmac_envelope_file=tmp_path / "absent.json",
            chain=chain,
            ritual=ritual,
            session_id="0001_test",
        )
    rows = list(chain.iter_events())
    assert rows[0]["type"] == f"{ritual}.hmac_rejected"
