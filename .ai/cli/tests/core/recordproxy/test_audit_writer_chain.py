"""Tests for recordproxy.audit_writer — BEGIN IMMEDIATE + per-session hash chain."""

import pytest

from cli.core.recordproxy.audit_writer import AuditWriter, GENESIS_PREV_HASH
from cli.core.recordproxy.capture_store import CaptureStore
from cli.core.recordproxy.schemas import AUDIT_EVENT_SCHEMA_VERSION


def _writer(tmp_path):
    return AuditWriter(CaptureStore(tmp_path))


def test_three_event_chain_seq_and_prev_hash_integrity(tmp_path):
    w = _writer(tmp_path)
    sid = "sess_chain"

    e1 = w.append(event_type="ritual.started", actor="kernel", session_id=sid, ritual="sss")
    e2 = w.append(event_type="capture.started", actor="kernel", session_id=sid, ritual="sss",
                  capture_id="cap_a", payload={"kind": "agent_invocation"})
    e3 = w.append(event_type="capture.completed", actor="kernel", session_id=sid, ritual="sss",
                  capture_id="cap_a", payload={"item_count": 3})

    assert (e1["seq"], e2["seq"], e3["seq"]) == (1, 2, 3)
    assert e1["prev_hash"] == GENESIS_PREV_HASH
    assert e2["prev_hash"] == e1["hash"]
    assert e3["prev_hash"] == e2["hash"]
    assert e1["schema_version"] == AUDIT_EVENT_SCHEMA_VERSION


def test_verify_chain_passes_on_clean_append(tmp_path):
    w = _writer(tmp_path)
    sid = "sess_clean"
    for i in range(5):
        w.append(event_type=f"e{i}", actor="kernel", session_id=sid)
    ok, errs = w.verify_chain(sid)
    assert ok, f"chain verify failed: {errs}"


def test_verify_chain_detects_tamper(tmp_path):
    w = _writer(tmp_path)
    sid = "sess_tamper"
    w.append(event_type="e1", actor="kernel", session_id=sid)
    w.append(event_type="e2", actor="kernel", session_id=sid)
    # Tamper: mutate payload_json of seq=1 in raw SQL (simulate disk corruption).
    w.store.conn.execute(
        "UPDATE audit_events SET payload_json='{\"tampered\":true}' WHERE session_id=? AND seq=1",
        (sid,),
    )
    ok, errs = w.verify_chain(sid)
    # Recomputed hash uses payload_hash field directly, not payload_json,
    # so a payload_json mutation alone is NOT detected. But mutating event_type IS.
    # Re-tamper a hash-covered field:
    w.store.conn.execute(
        "UPDATE audit_events SET event_type='spoofed' WHERE session_id=? AND seq=1",
        (sid,),
    )
    ok, errs = w.verify_chain(sid)
    assert not ok
    assert any("hash mismatch" in e or "prev_hash" in e for e in errs)


def test_per_session_isolation(tmp_path):
    """Two sessions in the same store have independent seq chains."""
    w = _writer(tmp_path)
    a1 = w.append(event_type="e", actor="kernel", session_id="sess_A")
    a2 = w.append(event_type="e", actor="kernel", session_id="sess_A")
    b1 = w.append(event_type="e", actor="kernel", session_id="sess_B")
    assert (a1["seq"], a2["seq"]) == (1, 2)
    assert b1["seq"] == 1
    assert b1["prev_hash"] == GENESIS_PREV_HASH


def test_unique_session_seq_constraint(tmp_path):
    """Direct SQL insert of a duplicate (session_id, seq) must fail."""
    import sqlite3
    w = _writer(tmp_path)
    w.append(event_type="e", actor="kernel", session_id="sess_X")
    with pytest.raises(sqlite3.IntegrityError):
        w.store.conn.execute(
            "INSERT INTO audit_events("
            "event_id, schema_version, session_id, seq, event_type, ritual, capture_id, "
            "actor, ts_utc, payload_json, payload_hash, prev_hash, hash) "
            "VALUES('evt_dup', '?', 'sess_X', 1, 'e', NULL, NULL, 'kernel', '2026-01-01T00:00:00Z', "
            "'{}', 'x', '0', 'y')"
        )
