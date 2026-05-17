"""RecordProxy capture transaction context manager (design §3).

Lifecycle:
    CAPTURING (on __enter__)
      ↓ happy path
    COMPLETED
      ↓ exception in with-block
    FAILED_PARTIAL
"""

import hashlib
import os
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Optional

from .audit_writer import AuditWriter
from .capture_store import CaptureStore, _canonical_json
from .emit import set_active_capture_id, reset_active_capture_id
from .schemas import CAPTURE_ITEM_KIND

# ─── ULID-like monotonic capture_id (design §11) ──────────────────────────────

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32

_lock = threading.Lock()
_last_ts_ms = 0
_last_rand = 0


def _encode_base32(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        out.append(_ULID_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def new_capture_id() -> str:
    """Generate a ULID-style monotonic capture_id.

    Same-process monotonic: if two calls land in the same millisecond,
    the randomness component is incremented (no collision, monotonic order).
    Cross-process monotonicity is NOT guaranteed in v1 (design §11 scope).
    """
    global _last_ts_ms, _last_rand
    with _lock:
        ts_ms = int(time.time() * 1000)
        if ts_ms <= _last_ts_ms:
            ts_ms = _last_ts_ms
            _last_rand = (_last_rand + 1) & ((1 << 80) - 1)
        else:
            _last_ts_ms = ts_ms
            _last_rand = int.from_bytes(os.urandom(10), "big")
        ts_part = _encode_base32(ts_ms, 10)
        rand_part = _encode_base32(_last_rand, 16)
    return ts_part + rand_part


def _item_id() -> str:
    return f"itm_{uuid.uuid4().hex}"


# ─── capture context manager (design §3) ──────────────────────────────────────


class _Capture:
    """In-flight capture transaction. Use via the ``capture`` context manager."""

    def __init__(
        self,
        store: CaptureStore,
        audit: AuditWriter,
        capture_id: str,
        session_id: str,
        ritual: str,
        kind: str,
        role: Optional[str],
        branch_id: Optional[str],
    ):
        self.store = store
        self.audit = audit
        self.capture_id = capture_id
        self.session_id = session_id
        self.ritual = ritual
        self.kind = kind
        self.role = role
        self.branch_id = branch_id
        self._items: list = []

    def _add_item(self, kind: str, name: str, content):
        sha, size, redaction_meta = self.store.write_blob(content)
        iid = _item_id()
        self.store.add_capture_item(
            item_id=iid,
            capture_id=self.capture_id,
            kind=kind,
            name=name,
            blob_sha256=sha,
            size_bytes=size,
            redaction_meta=redaction_meta,
        )
        self._items.append({"item_id": iid, "kind": kind, "name": name, "sha": sha})
        return sha

    def input(self, name: str, content):
        return self._add_item("input", name, content)

    def output(self, name: str, content):
        return self._add_item("output", name, content)

    def validation(self, name: str, content):
        return self._add_item("validation", name, content)

    def runtime(self, name: str, content):
        return self._add_item("runtime", name, content)

    def model(self, name: str, content):
        return self._add_item("model", name, content)


@contextmanager
def capture(
    session_dir,
    ritual: str,
    role: Optional[str] = None,
    kind: str = "agent_invocation",
    branch_id: Optional[str] = None,
    session_id: Optional[str] = None,
    model_provider: Optional[str] = None,
    model_name: Optional[str] = None,
):
    """RecordProxy capture transaction (design §3).

    Yields a Capture object with cap.input/output/validation API. On normal exit,
    capture row is finalized as COMPLETED. On exception inside the with-block,
    finalized as FAILED_PARTIAL and the exception is re-raised.

    Audit events emitted (via AuditWriter):
        - capture.started
        - capture.completed (happy)  OR  capture.failed_partial (exception)
    """
    store = CaptureStore(session_dir)
    audit = AuditWriter(store)
    capture_id = new_capture_id()
    sid = session_id or os.path.basename(str(session_dir))

    store.start_capture(
        capture_id=capture_id,
        session_id=sid,
        ritual=ritual,
        kind=kind,
        role=role,
        branch_id=branch_id,
        model_provider=model_provider,
        model_name=model_name,
    )
    audit.append(
        event_type="capture.started",
        actor=role or "executor",
        session_id=sid,
        ritual=ritual,
        capture_id=capture_id,
        payload={"kind": kind, "branch_id": branch_id},
    )

    cap = _Capture(
        store=store,
        audit=audit,
        capture_id=capture_id,
        session_id=sid,
        ritual=ritual,
        kind=kind,
        role=role,
        branch_id=branch_id,
    )

    # Part 2: publish capture_id on the contextvar so legacy
    # AuditChain.append (via emit_via_proxy) automatically stamps every
    # event emitted during this block with the right capture_id. Reset
    # via the returned Token on every exit path so back-to-back
    # invocations in the same process don't leak.
    token = set_active_capture_id(capture_id)

    try:
        yield cap
    except BaseException:
        store.finalize_capture(capture_id, "FAILED_PARTIAL")
        try:
            audit.append(
                event_type="capture.failed_partial",
                actor=role or "executor",
                session_id=sid,
                ritual=ritual,
                capture_id=capture_id,
                payload={"item_count": len(cap._items)},
            )
        finally:
            reset_active_capture_id(token)
            store.close()
        raise

    store.finalize_capture(capture_id, "COMPLETED")
    audit.append(
        event_type="capture.completed",
        actor=role or "executor",
        session_id=sid,
        ritual=ritual,
        capture_id=capture_id,
        payload={"item_count": len(cap._items)},
    )
    reset_active_capture_id(token)
    store.close()
