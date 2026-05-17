"""SQLite manifest + content-addressed blob storage (design §4, §5, §19).

Per-session ACID capture. CAS blob writer with atomic rename.
"""

import hashlib
import json
import os
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Tuple

from .redaction import redact_with_metadata
from .schemas import (
    CAPTURE_SCHEMA_VERSION,
    CAPTURE_ITEM_SCHEMA_VERSION,
    AUDIT_EVENT_SCHEMA_VERSION,
)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS captures (
  capture_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL,
  session_id TEXT NOT NULL,
  ritual TEXT NOT NULL,
  role TEXT,
  branch_id TEXT,
  kind TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at_utc TEXT NOT NULL,
  ended_at_utc TEXT,
  model_provider TEXT,
  model_name TEXT,
  template_hash TEXT,
  context_hash TEXT,
  prompt_hash TEXT
);

CREATE TABLE IF NOT EXISTS capture_items (
  item_id TEXT PRIMARY KEY,
  capture_id TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  blob_sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  redacted INTEGER NOT NULL DEFAULT 0,
  redaction_mode TEXT,
  path_hint TEXT,
  FOREIGN KEY(capture_id) REFERENCES captures(capture_id)
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL,
  session_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  ritual TEXT,
  capture_id TEXT,
  actor TEXT NOT NULL,
  ts_utc TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  prev_hash TEXT,
  hash TEXT NOT NULL,
  UNIQUE(session_id, seq)
);

CREATE TABLE IF NOT EXISTS blobs (
  sha256 TEXT PRIMARY KEY,
  size_bytes INTEGER NOT NULL,
  storage_path TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  redaction_status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_capture_items_capture ON capture_items(capture_id);
CREATE INDEX IF NOT EXISTS idx_audit_session_seq ON audit_events(session_id, seq);
"""


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class CaptureStore:
    """Per-session SQLite manifest + CAS blob store.

    Source of truth for captures, capture_items, blobs. The companion
    AuditWriter writes the audit_events table under BEGIN IMMEDIATE.
    """

    def __init__(self, session_dir):
        self.session_dir = Path(session_dir)
        self.capture_root = self.session_dir / "CAPTURE"
        self.capture_root.mkdir(parents=True, exist_ok=True)
        self.blobs_root = self.capture_root / "blobs" / "sha256"
        self.blobs_root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.capture_root / "capture.sqlite"
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), isolation_level=None)
            # Part 2 (S10): journal_mode=DELETE so SQLite does not leave
            # *-wal / *-shm sidecar files inside the session dir. WAL
            # would be faster but the sidecars confuse rrr's
            # forbidden-diff (memory: feedback_rrr_cross_session_forbidden_diff)
            # — capture throughput is not the bottleneck here.
            self._conn.execute("PRAGMA journal_mode=DELETE")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self):
        conn = self._connect()
        conn.executescript(_SCHEMA_SQL)

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        return self._connect()

    def write_blob(self, content) -> Tuple[str, int, dict]:
        """Redact and write a blob to CAS. Returns (sha256, size_bytes, redaction_metadata)."""
        if isinstance(content, (dict, list)):
            text = _canonical_json(content)
        elif isinstance(content, bytes):
            text = content.decode("utf-8", errors="replace")
        else:
            text = str(content)

        redacted_text, redaction_meta = redact_with_metadata(text)
        data = redacted_text.encode("utf-8")
        sha = hashlib.sha256(data).hexdigest()

        target_dir = self.blobs_root / sha[:2]
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / sha

        if not target.exists():
            tmp_fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix=".tmp_", suffix=".blob")
            try:
                with os.fdopen(tmp_fd, "wb") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, target)
            except Exception:
                try:
                    os.unlink(tmp_path)
                except FileNotFoundError:
                    pass
                raise

        conn = self._connect()
        conn.execute(
            "INSERT OR IGNORE INTO blobs(sha256, size_bytes, storage_path, created_at_utc, redaction_status) "
            "VALUES(?, ?, ?, ?, ?)",
            (sha, len(data), str(target.relative_to(self.session_dir)), _utc_now_iso(), redaction_meta["mode"]),
        )
        return sha, len(data), redaction_meta

    def start_capture(
        self,
        capture_id: str,
        session_id: str,
        ritual: str,
        kind: str,
        role: Optional[str] = None,
        branch_id: Optional[str] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        template_hash: Optional[str] = None,
        context_hash: Optional[str] = None,
        prompt_hash: Optional[str] = None,
    ):
        conn = self._connect()
        conn.execute(
            "INSERT INTO captures("
            "capture_id, schema_version, session_id, ritual, role, branch_id, "
            "kind, status, started_at_utc, ended_at_utc, model_provider, model_name, "
            "template_hash, context_hash, prompt_hash) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, 'CAPTURING', ?, NULL, ?, ?, ?, ?, ?)",
            (
                capture_id,
                CAPTURE_SCHEMA_VERSION,
                session_id,
                ritual,
                role,
                branch_id,
                kind,
                _utc_now_iso(),
                model_provider,
                model_name,
                template_hash,
                context_hash,
                prompt_hash,
            ),
        )

    def add_capture_item(
        self,
        item_id: str,
        capture_id: str,
        kind: str,
        name: str,
        blob_sha256: str,
        size_bytes: int,
        redaction_meta: dict,
        path_hint: Optional[str] = None,
    ):
        conn = self._connect()
        conn.execute(
            "INSERT INTO capture_items("
            "item_id, capture_id, schema_version, kind, name, blob_sha256, "
            "size_bytes, redacted, redaction_mode, path_hint) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item_id,
                capture_id,
                CAPTURE_ITEM_SCHEMA_VERSION,
                kind,
                name,
                blob_sha256,
                size_bytes,
                1 if redaction_meta.get("redacted_count", 0) > 0 else 0,
                redaction_meta.get("mode"),
                path_hint or name,
            ),
        )

    def finalize_capture(self, capture_id: str, status: str):
        conn = self._connect()
        conn.execute(
            "UPDATE captures SET status=?, ended_at_utc=? WHERE capture_id=?",
            (status, _utc_now_iso(), capture_id),
        )

    def get_capture(self, capture_id: str) -> Optional[dict]:
        conn = self._connect()
        row = conn.execute(
            "SELECT capture_id, schema_version, session_id, ritual, role, branch_id, "
            "kind, status, started_at_utc, ended_at_utc FROM captures WHERE capture_id=?",
            (capture_id,),
        ).fetchone()
        if not row:
            return None
        keys = ["capture_id", "schema_version", "session_id", "ritual", "role",
                "branch_id", "kind", "status", "started_at_utc", "ended_at_utc"]
        return dict(zip(keys, row))
