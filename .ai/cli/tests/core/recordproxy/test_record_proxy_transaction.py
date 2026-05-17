"""Tests for record_proxy.capture context manager — COMPLETED + FAILED_PARTIAL paths."""

import pytest

from cli.core.recordproxy import capture
from cli.core.recordproxy.audit_writer import AuditWriter
from cli.core.recordproxy.capture_store import CaptureStore


def test_capture_happy_path_finalizes_completed(tmp_path):
    sid = "sess_happy"
    with capture(session_dir=tmp_path, ritual="sss", role="EXECUTOR",
                 kind="agent_invocation", session_id=sid) as cap:
        cap.input("prompt.md", "what to do")
        cap.output("stdout.md", "done")
        cap.validation("validation.json", {"ok": True})
        cid = cap.capture_id

    store = CaptureStore(tmp_path)
    row = store.get_capture(cid)
    assert row["status"] == "COMPLETED"
    assert row["ended_at_utc"] is not None

    # 3 items written
    n = store.conn.execute(
        "SELECT COUNT(*) FROM capture_items WHERE capture_id=?", (cid,)
    ).fetchone()[0]
    assert n == 3
    store.close()


def test_capture_exception_finalizes_failed_partial(tmp_path):
    sid = "sess_fail"
    cid_holder = {}

    with pytest.raises(RuntimeError):
        with capture(session_dir=tmp_path, ritual="sss", role="EXECUTOR",
                     kind="agent_invocation", session_id=sid) as cap:
            cap.input("prompt.md", "starting")
            cid_holder["id"] = cap.capture_id
            raise RuntimeError("simulated agent failure")

    store = CaptureStore(tmp_path)
    row = store.get_capture(cid_holder["id"])
    assert row["status"] == "FAILED_PARTIAL"
    store.close()


def test_capture_audit_events_paired(tmp_path):
    sid = "sess_audit_pair"
    with capture(session_dir=tmp_path, ritual="vvv", role="EXECUTOR",
                 kind="agent_invocation", session_id=sid) as cap:
        cap.input("prompt.md", "x")

    audit = AuditWriter(CaptureStore(tmp_path))
    events = audit.read_chain(sid)
    types = [e["event_type"] for e in events]
    assert "capture.started" in types
    assert "capture.completed" in types
    # capture.started precedes capture.completed
    assert types.index("capture.started") < types.index("capture.completed")


def test_capture_audit_events_failed_partial(tmp_path):
    sid = "sess_audit_fail"
    with pytest.raises(ValueError):
        with capture(session_dir=tmp_path, ritual="vvv", role="EXECUTOR",
                     kind="agent_invocation", session_id=sid) as cap:
            cap.input("prompt.md", "x")
            raise ValueError("kaboom")

    audit = AuditWriter(CaptureStore(tmp_path))
    events = audit.read_chain(sid)
    types = [e["event_type"] for e in events]
    assert "capture.started" in types
    assert "capture.failed_partial" in types
    assert "capture.completed" not in types


def test_schema_version_present_on_every_persisted_row(tmp_path):
    sid = "sess_schema"
    with capture(session_dir=tmp_path, ritual="sss", role="EXECUTOR",
                 kind="agent_invocation", session_id=sid) as cap:
        cap.input("prompt.md", "x")

    store = CaptureStore(tmp_path)
    n_null_capture = store.conn.execute(
        "SELECT COUNT(*) FROM captures WHERE schema_version IS NULL OR schema_version=''"
    ).fetchone()[0]
    n_null_item = store.conn.execute(
        "SELECT COUNT(*) FROM capture_items WHERE schema_version IS NULL OR schema_version=''"
    ).fetchone()[0]
    n_null_audit = store.conn.execute(
        "SELECT COUNT(*) FROM audit_events WHERE schema_version IS NULL OR schema_version=''"
    ).fetchone()[0]
    assert n_null_capture == 0
    assert n_null_item == 0
    assert n_null_audit == 0
    store.close()
