"""Tool invocation emitter — Phase 6 Session C audit-chain binding.

Bridges the Session B guard (`tool_invocation_guard`) to the existing
hash-chained `AuditChain.append()` interface (Phase 1 audit organ).

The emitter is a pure caller-side helper: it converts an
`InvocationDecision.audit_envelope` (NDJSON-shaped dict produced by
`propose_invocation`) into the two-argument shape that `AuditChain.append`
expects — `event_type` (top-level) plus `details` (everything else).

The emitter is the ONLY layer that turns a guard decision into an audit
row. It does NOT write `.ai/audit/events.ndjson` directly (Article IV —
AuditChain is the only valid writer; emitter calls it).

Spec anchors:
- docs/specs/00_BLUEPRINT.md §4 (hash-chain audit)
- docs/specs/TRINITY_AUDIT_EVENT_SPEC_V1.md §3 (event registry)
- docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md §2 (Phase 6 spec)

Import-time safety: no I/O at import (Article XX Passive Core).
"""
from __future__ import annotations

from typing import Dict, Optional

from cli.core.audit import AuditChain
from cli.core.tool_invocation_guard import InvocationDecision


def emit_decision(
    chain: AuditChain, decision: InvocationDecision
) -> Optional[Dict[str, object]]:
    """Append the decision's audit envelope to the chain.

    Returns the appended event row (with `hash` + `prev_hash`) on success,
    or None when the envelope is empty (defensive — current guard always
    populates `audit_envelope`, but a future deny-with-no-envelope branch
    must not crash here).
    """
    envelope = decision.audit_envelope
    if not envelope:
        return None

    # Split envelope into AuditChain.append() shape: event_type + details.
    payload = dict(envelope)
    event_type = payload.pop("event_type", None)
    if event_type is None:
        return None

    return chain.append(event_type, payload)


__all__ = ["emit_decision"]
