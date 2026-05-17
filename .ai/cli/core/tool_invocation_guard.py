"""Tool invocation guard — Phase 6 Session B runtime gate.

Turns the Phase 6 Session A `tool_registry` loader into an enforced
fail-closed gate. The guard evaluates a proposed tool invocation against:

  (1) registry membership (Article XVI Least Authority — unknown is denied)
  (2) NEVER_GRANTED_CAPABILITIES (Article IV — audit.append / ddd.decide
      may never be required by a tool invocation)
  (3) ExecutionLease lifetime (lease.expires_at must be in the future)

The guard PROPOSES audit envelopes (NDJSON-shaped dicts) for the caller
to forward to the AuditWriter; it does NOT append, mutate state, or
decide verifier verdicts (Article IV, Article XX, Article XVI).

Spec anchors:
- docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md §2-§3
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §6 (Executor)
- docs/specs/TRINITY_AUDIT_EVENT_SPEC_V1.md §3 (event registry)

Import-time safety: this module performs no I/O at import (Article XX
Passive Core); all behaviour is gated behind `propose_invocation()`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cli.core.executor import ALLOWED_AUDIT_EVENT_TYPES, ExecutionLease
from cli.core.tool_registry import NEVER_GRANTED_CAPABILITIES, ToolRegistry


# Deny-reason vocabulary (closed set; tests assert against these literals).
DENY_UNKNOWN_TOOL: str = "unknown_tool"
DENY_NEVER_GRANTED_CAPABILITY: str = "never_granted_capability"
DENY_LEASE_EXPIRED: str = "lease_expired"

# Audit event types proposed by the guard. Both MUST be members of
# executor.ALLOWED_AUDIT_EVENT_TYPES; an assertion below pins this.
PROPOSED_EVENT_TYPE: str = "tool.invocation_proposed"
DENIED_EVENT_TYPE: str = "tool.invocation_denied"

assert PROPOSED_EVENT_TYPE in ALLOWED_AUDIT_EVENT_TYPES, (
    "guard event_type drift from executor contract"
)
assert DENIED_EVENT_TYPE in ALLOWED_AUDIT_EVENT_TYPES, (
    "guard deny event_type drift from executor contract"
)


@dataclass(frozen=True)
class InvocationDecision:
    """Result of a guard evaluation. Fail-closed: only allow/deny verdicts.

    `audit_envelope` is the NDJSON-shaped payload the caller hands to the
    AuditWriter. On allow it is a `tool.invocation_proposed` envelope; on
    deny it is a `tool.invocation_denied` envelope carrying the reason
    code. The guard NEVER writes to `.ai/audit/**` (Article IV).
    """

    verdict: str
    reason: str
    audit_envelope: Dict[str, Any] = field(default_factory=dict)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _deny_envelope(
    lease: ExecutionLease,
    tool_name: str,
    reason: str,
    *,
    now: datetime,
) -> Dict[str, Any]:
    return {
        "event_type": DENIED_EVENT_TYPE,
        "actor": "executor",
        "decided_by": "kernel",
        "lease_id": lease.lease_id,
        "session_id": lease.session_id,
        "step_id": lease.step_id,
        "tool_name": tool_name,
        "reason": reason,
        "ts_utc": _iso(now),
    }


def _allow_envelope(
    lease: ExecutionLease,
    tool_name: str,
    required_capabilities: tuple,
    *,
    now: datetime,
) -> Dict[str, Any]:
    return {
        "event_type": PROPOSED_EVENT_TYPE,
        "actor": "executor",
        "decided_by": "kernel",
        "lease_id": lease.lease_id,
        "session_id": lease.session_id,
        "step_id": lease.step_id,
        "tool_name": tool_name,
        "required_capabilities": list(required_capabilities),
        "proposed_at": _iso(now),
    }


def propose_invocation(
    lease: ExecutionLease,
    tool_name: str,
    registry: ToolRegistry,
    *,
    now: Optional[datetime] = None,
) -> InvocationDecision:
    """Evaluate a proposed tool invocation. Pure, fail-closed.

    Order of evaluation (deterministic):
      1. lease expiry          → deny/lease_expired
      2. registry membership   → deny/unknown_tool
      3. never-granted caps    → deny/never_granted_capability
      4. otherwise             → allow + proposed envelope

    `now` is injectable for tests; defaults to `datetime.now(timezone.utc)`.
    """
    evaluated_at = now if now is not None else _utc_now()

    # (1) Lease must still be valid. A naive datetime would crash the
    # comparison; we normalise to UTC if needed for hardened callers.
    expires_at = lease.expires_at
    if isinstance(expires_at, str):
        # Tolerate string form from the schema mirror, parsing RFC3339.
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < evaluated_at:
        return InvocationDecision(
            verdict="deny",
            reason=DENY_LEASE_EXPIRED,
            audit_envelope=_deny_envelope(
                lease, tool_name, DENY_LEASE_EXPIRED, now=evaluated_at
            ),
        )

    # (2) Tool must be declared in the registry.
    if tool_name not in registry:
        return InvocationDecision(
            verdict="deny",
            reason=DENY_UNKNOWN_TOOL,
            audit_envelope=_deny_envelope(
                lease, tool_name, DENY_UNKNOWN_TOOL, now=evaluated_at
            ),
        )

    record = registry.require(tool_name)
    required = frozenset(record.required_capabilities)

    # (3) NEVER-granted capabilities (audit.append / ddd.decide) MUST NOT
    # appear in a tool's required_capabilities — that is a registry-bug
    # surfaced at invocation time.
    if required & NEVER_GRANTED_CAPABILITIES:
        return InvocationDecision(
            verdict="deny",
            reason=DENY_NEVER_GRANTED_CAPABILITY,
            audit_envelope=_deny_envelope(
                lease,
                tool_name,
                DENY_NEVER_GRANTED_CAPABILITY,
                now=evaluated_at,
            ),
        )

    # (4) Happy path — propose envelope for AuditWriter.
    return InvocationDecision(
        verdict="allow",
        reason="",
        audit_envelope=_allow_envelope(
            lease, tool_name, record.required_capabilities, now=evaluated_at
        ),
    )


__all__ = [
    "DENY_UNKNOWN_TOOL",
    "DENY_NEVER_GRANTED_CAPABILITY",
    "DENY_LEASE_EXPIRED",
    "PROPOSED_EVENT_TYPE",
    "DENIED_EVENT_TYPE",
    "InvocationDecision",
    "propose_invocation",
]
