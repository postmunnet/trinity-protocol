"""Trinity hash-chained audit log.

Spec ref: docs/specs/00_BLUEPRINT.md §4 (Hash Chain Audit), Decision D9.

Each event is one JSON line in `.ai/audit/events.ndjson`. Legacy shape
(pre-RecordProxy v1):
    {ts, type, prev_hash, details:{...}, hash}

Enriched shape (RecordProxy v1 Option C, events written from
session feat-recordproxy-integration-v1 onward):
    {ts, type, prev_hash, schema_version, session_id, actor, ritual,
     capture_id, redaction_meta, details, hash}

Both shapes coexist in the same file. `validate()` is shape-agnostic: it
recomputes each event's hash from `{k:v for k,v in event.items() if k !=
"hash"}`, which works for any field set. The chain link via `prev_hash`
references only the previous event's `hash` string, so adding fields to
new events does not invalidate the chain.

`hash` = sha256(canonical(event_without_hash))
`prev_hash` = previous line's `hash`, or "0" for genesis.

Append is atomic-ish (write line, fsync). Reads are line-by-line; no whole
file kept in memory.
"""
from __future__ import annotations

import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional

from .recordproxy.emit import emit_via_proxy


class AuditChainError(Exception):
    pass


class AuditChain:
    """Append-only hash-chained event log."""

    def __init__(self, audit_path: Path):
        self.path = Path(audit_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now_iso() -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _canonical(obj: Dict[str, Any]) -> str:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _hash(canonical_str: str) -> str:
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def last_hash(self) -> Optional[str]:
        """Return hash of last event, or None if file empty/missing."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        # Tail read — small files (<10MB), simple is fine.
        last = None
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last = line
        if not last:
            return None
        try:
            return json.loads(last).get("hash")
        except json.JSONDecodeError:
            raise AuditChainError(f"corrupt last line in {self.path}")

    @contextlib.contextmanager
    def _exclusive_append_lock(self) -> Iterator[None]:
        """Hold a POSIX exclusive lock across the append critical section so
        concurrent appenders (tg-bot + tmux + multi-agent) cannot read the same
        last_hash and fork the chain (T3.1). The lock is taken on a sidecar
        ``events.ndjson.lock`` file, held only for the read-last-hash + write,
        and auto-releases on close / process death — so there is no stale-lock
        concern (unlike the long-held session .state/LOCK). POSIX only
        (darwin/linux); the kernel targets those platforms."""
        lock_path = self.path.parent / (self.path.name + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def append(
        self,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
        ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Append a new event linked to the previous hash. Returns the event.

        Phase 6 Option C: events are enriched with RecordProxy v1 schema
        markers (schema_version, session_id, actor, ritual, capture_id,
        redaction_meta) via ``recordproxy.emit.emit_via_proxy`` before
        hash computation. Public signature is unchanged — callers pass
        ``event_type`` + ``details`` as before; promoted fields are
        extracted from ``details`` when present.
        """
        # T3.1 — serialize the read-last-hash + write so concurrent appenders
        # cannot fork the chain on a shared prev_hash.
        with self._exclusive_append_lock():
            prev = self.last_hash() or "0"
            event = emit_via_proxy(
                event_type,
                details,
                prev_hash=prev,
                ts=ts or self._now_iso(),
            )
            canonical = self._canonical(event)
            event["hash"] = self._hash(canonical)

            line = json.dumps(event, separators=(",", ":")) + "\n"
            # Append + fsync for crash safety.
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
        return event

    def iter_events(self) -> Iterable[Dict[str, Any]]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

    def iter_events_reversed(self) -> Iterable[Dict[str, Any]]:
        """Iterate events from most recent to oldest. Reads the whole file
        then reverses; simple and O(N) memory. For very long chains
        consider a tail-seek file reader. Used by Loop.__init__ to walk
        backwards looking for the latest `graph.transition` event for a
        session (R6 reconciliation)."""
        return reversed(list(self.iter_events()))

    def validate(self) -> None:
        """Walk the chain; raise AuditChainError if any link is broken."""
        prev = "0"
        for i, event in enumerate(self.iter_events()):
            if event.get("prev_hash") != prev:
                raise AuditChainError(
                    f"event #{i} ({event.get('type')}): prev_hash mismatch "
                    f"(got {event.get('prev_hash')!r}, expected {prev!r})"
                )
            recomputed = self._hash(
                self._canonical({k: v for k, v in event.items() if k != "hash"})
            )
            if event.get("hash") != recomputed:
                raise AuditChainError(
                    f"event #{i} ({event.get('type')}): hash mismatch"
                )
            prev = event["hash"]


def get_chain_for_project(project_root: Path) -> AuditChain:
    """Resolve the canonical audit path for a Trinity project."""
    return AuditChain(project_root / ".ai" / "audit" / "events.ndjson")
