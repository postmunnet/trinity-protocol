"""Tests for recordproxy.capture_store — SQLite schema + CAS atomic blob write."""

import hashlib
import sqlite3

import pytest

from cli.core.recordproxy.capture_store import CaptureStore
from cli.core.recordproxy.schemas import (
    CAPTURE_SCHEMA_VERSION,
    CAPTURE_ITEM_SCHEMA_VERSION,
)


def test_capture_store_initializes_schema(tmp_path):
    store = CaptureStore(tmp_path)
    assert (tmp_path / "CAPTURE" / "capture.sqlite").exists()
    tables = {
        r[0]
        for r in store.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    }
    assert "captures" in tables
    assert "capture_items" in tables
    assert "audit_events" in tables
    assert "blobs" in tables
    store.close()


def test_pragmas_set(tmp_path):
    store = CaptureStore(tmp_path)
    jm = store.conn.execute("PRAGMA journal_mode").fetchone()[0].lower()
    bt = store.conn.execute("PRAGMA busy_timeout").fetchone()[0]
    fk = store.conn.execute("PRAGMA foreign_keys").fetchone()[0]
    # Part 2 (S10): journal_mode pinned to DELETE so SQLite does not
    # leave *-wal / *-shm sidecars inside the session dir (which would
    # confuse rrr's forbidden-diff per memory:
    # feedback_rrr_cross_session_forbidden_diff).
    assert jm == "delete"
    assert bt == 5000
    assert fk == 1
    store.close()


def test_write_blob_uses_content_addressed_path(tmp_path):
    store = CaptureStore(tmp_path)
    content = "hello, recordproxy"
    sha, size, meta = store.write_blob(content)

    expected_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert sha == expected_sha
    assert size == len(content.encode("utf-8"))

    blob_path = tmp_path / "CAPTURE" / "blobs" / "sha256" / sha[:2] / sha
    assert blob_path.exists()
    assert blob_path.read_text(encoding="utf-8") == content
    store.close()


def test_write_blob_deduplicates(tmp_path):
    store = CaptureStore(tmp_path)
    sha1, _, _ = store.write_blob("same content")
    sha2, _, _ = store.write_blob("same content")
    assert sha1 == sha2
    rows = store.conn.execute("SELECT COUNT(*) FROM blobs WHERE sha256=?", (sha1,)).fetchone()
    assert rows[0] == 1
    store.close()


def test_write_blob_redacts_before_storage(tmp_path, monkeypatch):
    """Design §12 invariant: redaction happens BEFORE blob hits disk."""
    monkeypatch.delenv("TRINITY_RECORDPROXY_RAW", raising=False)
    store = CaptureStore(tmp_path)
    raw_secret = "Authorization: Bearer the_actual_secret_value_abc123"
    sha, _, meta = store.write_blob(raw_secret)
    blob_path = tmp_path / "CAPTURE" / "blobs" / "sha256" / sha[:2] / sha
    on_disk = blob_path.read_text(encoding="utf-8")
    assert "the_actual_secret_value_abc123" not in on_disk
    assert meta["mode"] == "REDACTED"
    store.close()


def test_capture_lifecycle_status_progression(tmp_path):
    store = CaptureStore(tmp_path)
    cap_id = "cap_test_001"
    store.start_capture(
        capture_id=cap_id, session_id="sess_test", ritual="sss", kind="agent_invocation"
    )
    cap = store.get_capture(cap_id)
    assert cap["status"] == "CAPTURING"
    assert cap["schema_version"] == CAPTURE_SCHEMA_VERSION

    store.finalize_capture(cap_id, "COMPLETED")
    cap = store.get_capture(cap_id)
    assert cap["status"] == "COMPLETED"
    assert cap["ended_at_utc"] is not None
    store.close()


def test_capture_item_schema_version_pinned(tmp_path):
    store = CaptureStore(tmp_path)
    cap_id = "cap_test_002"
    store.start_capture(
        capture_id=cap_id, session_id="sess_test", ritual="sss", kind="agent_invocation"
    )
    sha, size, meta = store.write_blob("dummy content")
    store.add_capture_item(
        item_id="itm_001",
        capture_id=cap_id,
        kind="input",
        name="prompt.md",
        blob_sha256=sha,
        size_bytes=size,
        redaction_meta=meta,
    )
    row = store.conn.execute(
        "SELECT schema_version FROM capture_items WHERE item_id=?", ("itm_001",)
    ).fetchone()
    assert row[0] == CAPTURE_ITEM_SCHEMA_VERSION
    store.close()


def test_no_tmp_files_remain_after_blob_write(tmp_path):
    """Atomic rename: no leftover .tmp_ files in the CAS dir."""
    store = CaptureStore(tmp_path)
    store.write_blob("payload-A")
    store.write_blob("payload-B")
    blobs_dir = tmp_path / "CAPTURE" / "blobs" / "sha256"
    leftover = [p for p in blobs_dir.rglob(".tmp_*")]
    assert leftover == []
    store.close()
