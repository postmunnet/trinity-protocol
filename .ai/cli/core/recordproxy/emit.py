"""RecordProxy v1 NDJSON enrichment adapter (Option C).

Wraps the legacy 5-field NDJSON audit event with RecordProxy v1 schema
markers (schema_version + promoted session_id/ritual/capture_id/actor +
redaction_meta) without changing the storage backend or breaking hash
chain continuity.

Design ref:
    Session 0001_...feat-recordproxy-integration-v1 THINK/recordproxy_integration_points.md §4 Option C.
    Plan envelope step S2 artifact (emit_via_proxy).

Constitutional anchors:
    Article XVI (Least Authority) — pure function, no I/O, no mutation
    of historical events.
    Article XX (Passive Core) — invoked only from AuditChain.append, no
    self-trigger.
    Article XXII (Rollback) — removing this module + reverting the
    AuditChain.append splice restores the pre-proxy behavior; old NDJSON
    events keep validating.

Why "emit_via_proxy" in plan envelope but "enrich" in body:
    The plan envelope name (emit_via_proxy) was authored before Option C
    was selected. In Option C the responsibility is shape enrichment, not
    side-effecting emission — the AuditChain remains the sole writer and
    hash computer. The two names refer to the same function; the export
    is kept under the plan-envelope name for traceability.
"""
from __future__ import annotations

import json
from contextvars import ContextVar
from typing import Any, Dict, Optional

from .redaction import redact_with_metadata
from .schemas import AUDIT_EVENT_SCHEMA_VERSION

_PROMOTABLE_KEYS = ("session_id", "ritual", "capture_id")
_ACTOR_KEYS = ("actor", "decided_by")

# Part 2 (capture wiring): the active capture_id is stashed in a ContextVar
# while inside a ``with capture(...) as cap:`` block. AuditChain.append (via
# emit_via_proxy) reads this contextvar so events emitted during the
# capture lifetime are stamped with the right capture_id automatically.
# capture().__enter__ sets via .set(); capture().__exit__ resets via the
# returned Token. No-op outside any capture block (returns None).
_active_capture_id: ContextVar[Optional[str]] = ContextVar(
    "trinity_active_capture_id", default=None
)


def get_active_capture_id() -> Optional[str]:
    """Read the currently-active capture_id from the contextvar.

    Returns ``None`` when called outside any ``capture()`` block.
    """
    return _active_capture_id.get()


def set_active_capture_id(capture_id: Optional[str]):
    """Set the active capture_id. Returns the contextvars Token so the caller
    can reset it on exit (avoiding cross-invocation leaks)."""
    return _active_capture_id.set(capture_id)


def reset_active_capture_id(token) -> None:
    """Reset via the Token returned by ``set_active_capture_id``."""
    _active_capture_id.reset(token)


def _canonical_json_str(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def emit_via_proxy(
    event_type: str,
    details: Optional[Dict[str, Any]],
    *,
    prev_hash: str,
    ts: str,
    capture_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return an NDJSON event enriched with RecordProxy v1 schema markers.

    Caller (AuditChain.append) computes ``hash`` over the canonical form
    of the returned dict; this function never writes to disk.

    Enrichment:
      - ``schema_version = AUDIT_EVENT_SCHEMA_VERSION``.
      - Promotes ``session_id``, ``ritual``, ``capture_id``, ``actor``
        from ``details`` to top-level fields when present. ``actor``
        falls back to ``decided_by`` for legacy callers that use the
        Decision-D1 vocabulary.
      - Redacts the ``details`` JSON via
        ``recordproxy.redaction.redact_with_metadata`` (11 deny-list
        regex patterns + break-glass via ``TRINITY_RECORDPROXY_RAW=1``).
      - Records ``redaction_meta = {mode, applied_rules, redacted_count}``.

    Backwards-compat:
      Adding fields to NEW events does not invalidate OLD events.
      ``AuditChain.validate()`` recomputes each event's hash from
      ``{k:v for k,v in event.items() if k != "hash"}`` — shape-agnostic.
      Chain linkage via ``prev_hash`` is preserved because ``prev_hash``
      is the previous event's ``hash`` string, independent of either
      event's field count.

    Args:
        event_type: legacy ``type`` field value.
        details: legacy ``details`` payload (may be ``None``).
        prev_hash: previous event's ``hash``, or ``"0"`` for genesis.
        ts: UTC ISO timestamp for the ``ts`` field.

    Returns:
        Event dict WITHOUT ``hash``. Caller computes hash via
        ``sha256(canonical(event))`` per the AuditChain protocol.
    """
    details = details or {}

    details_canonical = _canonical_json_str(details)
    redacted_str, redaction_meta = redact_with_metadata(details_canonical)
    redacted_details = json.loads(redacted_str)

    promoted: Dict[str, Any] = {}
    for key in _PROMOTABLE_KEYS:
        if key in redacted_details:
            promoted[key] = redacted_details[key]
    for key in _ACTOR_KEYS:
        if key in redacted_details:
            promoted.setdefault("actor", redacted_details[key])
            break

    # Part 2: explicit capture_id kwarg wins; otherwise consult the
    # contextvar (populated by an enclosing capture() block). When both
    # are None the field is omitted from the event (cleaner than carrying
    # a null), preserving the part-1 behavior for callers outside any
    # capture block.
    resolved_capture_id = capture_id if capture_id is not None else _active_capture_id.get()
    if resolved_capture_id is not None:
        promoted["capture_id"] = resolved_capture_id

    return {
        "ts": ts,
        "type": event_type,
        "prev_hash": prev_hash,
        "schema_version": AUDIT_EVENT_SCHEMA_VERSION,
        **promoted,
        "redaction_meta": redaction_meta,
        "details": redacted_details,
    }
