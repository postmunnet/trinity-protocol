"""Conformance tests for the Transport boundary (Article XV / Spec 9).

Spec: docs/specs/TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md §9.1 (TBT-01..TBT-10).

These are Tier-0/1 deterministic checks — no network, no LLM. Every test
exercises the 7-step verify_envelope pipeline (spec §4.5) against a
canned envelope, and asserts the expected (accept | refuse-with-code)
outcome.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import pytest

from cli.core import transport
from cli.core.transport import (
    EVENT_ACCEPTED,
    EVENT_REFUSED_BADKEY,
    EVENT_REFUSED_OVERSCOPE,
    EVENT_REFUSED_REPLAY,
    EVENT_REFUSED_UNSIGNED,
    REFUSAL_BADKEY,
    REFUSAL_CODES,
    REFUSAL_OVERSCOPE,
    REFUSAL_REPLAY,
    REFUSAL_UNSIGNED,
    canonical_signed_bytes,
    compute_envelope_hmac,
    refusal_to_event,
    verify_envelope,
)


# ─────────── fixtures ───────────


SECRET = "kernel-test-secret-2026-05-15"
ISSUER = "human-gate"


def _make_envelope(
    *,
    envelope_id: str = "env_0001",
    ts: Optional[str] = None,
    source_transport: str = "tg-bot",
    claimed_actor: str = "human:tg:817249157",
    payload: Optional[Dict] = None,
    hmac_alg: str = "HMAC-SHA256",
    key_id: str = "human-gate-2026-05",
    expires_ts: Optional[str] = None,
    with_hmac: bool = True,
    secret: str = SECRET,
) -> Dict:
    """Build a canned envelope; HMAC computed last so it stays consistent."""
    env: Dict = {
        "envelope_id": envelope_id,
        "ts": ts or "2026-05-15T10:00:00+00:00",
        "source_transport": source_transport,
        "claimed_actor": claimed_actor,
        "payload": payload or {"kind": "ddd.decision", "action": "approve"},
    }
    if hmac_alg is not None:
        env["hmac_alg"] = hmac_alg
    if key_id is not None:
        env["key_id"] = key_id
    if expires_ts is not None:
        env["expires_ts"] = expires_ts
    if with_hmac:
        env["hmac"] = compute_envelope_hmac(env, secret)
    return env


def _good_key_loader(key_id: str) -> Tuple[Optional[str], Optional[str]]:
    if key_id == "human-gate-2026-05":
        return SECRET, ISSUER
    return None, None


class _StubReplayStore:
    def __init__(self) -> None:
        self.seen_ids: Dict[Tuple[str, str], bool] = {}

    def seen(self, envelope_id: str, issuer: str) -> bool:
        return (envelope_id, issuer) in self.seen_ids

    def mark(self, envelope_id: str, issuer: str) -> None:
        self.seen_ids[(envelope_id, issuer)] = True


# ─────────── TBT-01 .. TBT-05 — UNSIGNED + BADKEY ───────────


def test_tbt01_missing_hmac_on_mutating_envelope_refused_unsigned() -> None:
    env = _make_envelope(with_hmac=False)
    # mutating because hmac_alg/key_id are present; hmac missing → UNSIGNED
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is False
    assert code == REFUSAL_UNSIGNED


def test_tbt02_missing_required_field_refused_unsigned() -> None:
    env = _make_envelope()
    del env["envelope_id"]
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is False
    assert code == REFUSAL_UNSIGNED


def test_tbt03_wrong_algorithm_refused_badkey() -> None:
    env = _make_envelope(hmac_alg="HMAC-SHA512")
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is False
    assert code == REFUSAL_BADKEY


def test_tbt04_unknown_key_id_refused_badkey() -> None:
    env = _make_envelope(key_id="unknown-key")
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is False
    assert code == REFUSAL_BADKEY


def test_tbt05_tampered_payload_refused_badkey() -> None:
    env = _make_envelope()
    # Tamper after signing — invalidate the HMAC
    env["payload"]["action"] = "delete-everything"
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is False
    assert code == REFUSAL_BADKEY


# ─────────── TBT-06 .. TBT-07 — REPLAY ───────────


def test_tbt06_replay_envelope_id_refused() -> None:
    store = _StubReplayStore()
    env = _make_envelope(envelope_id="env_replay_001")
    # First delivery — accepted, store marks it
    ok, code = verify_envelope(env, key_loader=_good_key_loader, replay_store=store)
    assert ok is True
    assert code is None
    # Second delivery of same envelope_id — REPLAY
    env2 = _make_envelope(envelope_id="env_replay_001")
    ok2, code2 = verify_envelope(
        env2, key_loader=_good_key_loader, replay_store=store
    )
    assert ok2 is False
    assert code2 == REFUSAL_REPLAY


def test_tbt07_expired_envelope_refused_replay() -> None:
    past = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    env = _make_envelope(expires_ts=past)
    now = datetime.now(timezone.utc)
    ok, code = verify_envelope(env, key_loader=_good_key_loader, now=now)
    assert ok is False
    assert code == REFUSAL_REPLAY


# ─────────── TBT-08 .. TBT-09 — OVERSCOPE ───────────


def test_tbt08_kernel_class_refused_overscope() -> None:
    env = _make_envelope(claimed_actor="kernel:tg:internal")
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is False
    assert code == REFUSAL_OVERSCOPE


def test_tbt09_unknown_actor_class_refused_overscope() -> None:
    env = _make_envelope(claimed_actor="root:tg:817249157")
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is False
    assert code == REFUSAL_OVERSCOPE


# ─────────── TBT-10 — happy path (mutating ddd.decision accepted) ───────────


def test_tbt10_valid_mutating_envelope_accepted() -> None:
    env = _make_envelope()
    ok, code = verify_envelope(env, key_loader=_good_key_loader)
    assert ok is True
    assert code is None


# ─────────── audit event mapping + module surface ───────────


def test_refusal_codes_constants_present() -> None:
    assert REFUSAL_UNSIGNED == "TRANSPORT_REFUSED_UNSIGNED"
    assert REFUSAL_BADKEY == "TRANSPORT_REFUSED_BADKEY"
    assert REFUSAL_REPLAY == "TRANSPORT_REFUSED_REPLAY"
    assert REFUSAL_OVERSCOPE == "TRANSPORT_REFUSED_OVERSCOPE"
    assert REFUSAL_CODES == {
        REFUSAL_UNSIGNED,
        REFUSAL_BADKEY,
        REFUSAL_REPLAY,
        REFUSAL_OVERSCOPE,
    }


def test_event_constants_present() -> None:
    assert EVENT_ACCEPTED == "transport.envelope_accepted"
    assert EVENT_REFUSED_UNSIGNED == "transport.envelope_refused.unsigned"
    assert EVENT_REFUSED_BADKEY == "transport.envelope_refused.badkey"
    assert EVENT_REFUSED_REPLAY == "transport.envelope_refused.replay"
    assert EVENT_REFUSED_OVERSCOPE == "transport.envelope_refused.overscope"


def test_refusal_to_event_round_trip() -> None:
    assert refusal_to_event(REFUSAL_UNSIGNED) == EVENT_REFUSED_UNSIGNED
    assert refusal_to_event(REFUSAL_BADKEY) == EVENT_REFUSED_BADKEY
    assert refusal_to_event(REFUSAL_REPLAY) == EVENT_REFUSED_REPLAY
    assert refusal_to_event(REFUSAL_OVERSCOPE) == EVENT_REFUSED_OVERSCOPE


def test_refusal_to_event_rejects_unknown_code() -> None:
    with pytest.raises(ValueError):
        refusal_to_event("TRANSPORT_REFUSED_UNICORN")


def test_canonical_signed_bytes_excludes_hmac_field() -> None:
    env = _make_envelope()
    canonical = canonical_signed_bytes(env)
    decoded = json.loads(canonical.decode("utf-8"))
    assert "hmac" not in decoded
    assert decoded["envelope_id"] == env["envelope_id"]


def test_canonical_signed_bytes_is_sort_stable() -> None:
    env_a = _make_envelope()
    env_b = dict(reversed(list(env_a.items())))
    # Different key insertion order but same content — canonical output equal
    assert canonical_signed_bytes(env_a) == canonical_signed_bytes(env_b)


# ─────────── schema artifact existence (A4 anchor) ───────────


def test_transport_envelope_schema_exists_and_valid_json() -> None:
    import pathlib

    schema_path = pathlib.Path(__file__).resolve().parents[2] / "schemas" / "transport_envelope.schema.json"
    assert schema_path.exists(), f"schema missing: {schema_path}"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema.get("$schema")
    assert schema.get("type") == "object"
    props = schema.get("properties", {})
    for required_field in ("envelope_id", "ts", "source_transport", "claimed_actor", "payload", "hmac", "hmac_alg", "key_id"):
        assert required_field in props, f"schema missing property: {required_field}"


# ─────────── ddd.py integration smoke (A12 anchor) ───────────


def test_ddd_imports_transport_module() -> None:
    """A12 anchor — confirm ddd.py wires the new boundary import."""
    import pathlib

    ddd_path = pathlib.Path(__file__).resolve().parents[1] / "commands" / "ddd.py"
    src = ddd_path.read_text(encoding="utf-8")
    assert "from ..core.transport import" in src or "from cli.core.transport import" in src
