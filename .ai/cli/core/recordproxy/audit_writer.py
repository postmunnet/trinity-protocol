"""AuditWriter — per-session hash chain with BEGIN IMMEDIATE (design §7).

Invariants:
    - Only AuditWriter may claim seq.
    - AuditWriter must claim seq under BEGIN IMMEDIATE.
    - No caller may precompute final prev_hash outside the transaction.
"""

import hashlib
import json
import time
import uuid
from typing import Optional

from .capture_store import CaptureStore, _canonical_json, _utc_now_iso
from .schemas import AUDIT_EVENT_SCHEMA_VERSION

GENESIS_PREV_HASH = "0"


def _event_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def _payload_hash(payload_canonical: str) -> str:
    return hashlib.sha256(payload_canonical.encode("utf-8")).hexdigest()


class AuditWriter:
    """Append-only per-session audit chain writer."""

    def __init__(self, store: CaptureStore):
        self.store = store

    def append(
        self,
        event_type: str,
        actor: str,
        session_id: str,
        ritual: Optional[str] = None,
        capture_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> dict:
        """Append one audit event under BEGIN IMMEDIATE.

        Returns the full event row (with seq, prev_hash, hash) on success.
        Raises sqlite3.OperationalError on lock timeout (busy_timeout=5000ms).
        """
        payload = payload or {}
        payload_canonical = _canonical_json(payload)
        pay_hash = _payload_hash(payload_canonical)
        ts = _utc_now_iso()
        eid = _event_id()

        conn = self.store.conn
        try:
            conn.execute("BEGIN IMMEDIATE")

            row = conn.execute(
                "SELECT seq, hash FROM audit_events WHERE session_id=? "
                "ORDER BY seq DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            if row:
                next_seq = row[0] + 1
                prev_hash = row[1]
            else:
                next_seq = 1
                prev_hash = GENESIS_PREV_HASH

            event_for_hash = {
                "event_id": eid,
                "schema_version": AUDIT_EVENT_SCHEMA_VERSION,
                "session_id": session_id,
                "seq": next_seq,
                "event_type": event_type,
                "ritual": ritual,
                "capture_id": capture_id,
                "actor": actor,
                "ts_utc": ts,
                "payload_hash": pay_hash,
                "prev_hash": prev_hash,
            }
            event_canonical = _canonical_json(event_for_hash)
            event_hash = hashlib.sha256(event_canonical.encode("utf-8")).hexdigest()

            conn.execute(
                "INSERT INTO audit_events("
                "event_id, schema_version, session_id, seq, event_type, ritual, capture_id, "
                "actor, ts_utc, payload_json, payload_hash, prev_hash, hash) "
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    eid,
                    AUDIT_EVENT_SCHEMA_VERSION,
                    session_id,
                    next_seq,
                    event_type,
                    ritual,
                    capture_id,
                    actor,
                    ts,
                    payload_canonical,
                    pay_hash,
                    prev_hash,
                    event_hash,
                ),
            )
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise

        return {
            **event_for_hash,
            "payload_json": payload_canonical,
            "hash": event_hash,
        }

    def read_chain(self, session_id: str):
        """Return chain rows (oldest first) for a session. Read-only."""
        conn = self.store.conn
        rows = conn.execute(
            "SELECT event_id, schema_version, session_id, seq, event_type, ritual, "
            "capture_id, actor, ts_utc, payload_json, payload_hash, prev_hash, hash "
            "FROM audit_events WHERE session_id=? ORDER BY seq ASC",
            (session_id,),
        ).fetchall()
        keys = ["event_id", "schema_version", "session_id", "seq", "event_type",
                "ritual", "capture_id", "actor", "ts_utc", "payload_json",
                "payload_hash", "prev_hash", "hash"]
        return [dict(zip(keys, r)) for r in rows]

    def verify_chain(self, session_id: str):
        """Recompute hashes and verify prev_hash linkage. Returns (ok, errors)."""
        errors = []
        chain = self.read_chain(session_id)
        expected_prev = GENESIS_PREV_HASH
        expected_seq = 1
        for row in chain:
            if row["seq"] != expected_seq:
                errors.append(f"seq gap at seq={row['seq']}, expected={expected_seq}")
            if row["prev_hash"] != expected_prev:
                errors.append(f"prev_hash mismatch at seq={row['seq']}")
            event_for_hash = {
                "event_id": row["event_id"],
                "schema_version": row["schema_version"],
                "session_id": row["session_id"],
                "seq": row["seq"],
                "event_type": row["event_type"],
                "ritual": row["ritual"],
                "capture_id": row["capture_id"],
                "actor": row["actor"],
                "ts_utc": row["ts_utc"],
                "payload_hash": row["payload_hash"],
                "prev_hash": row["prev_hash"],
            }
            recomputed = hashlib.sha256(
                _canonical_json(event_for_hash).encode("utf-8")
            ).hexdigest()
            if recomputed != row["hash"]:
                errors.append(f"hash mismatch at seq={row['seq']}: stored={row['hash']} recomputed={recomputed}")
            expected_prev = row["hash"]
            expected_seq += 1
        return (len(errors) == 0, errors)
