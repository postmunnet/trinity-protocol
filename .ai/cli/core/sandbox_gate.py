"""Sandbox gate — Phase 7 Session 7-2 composition with lease_lifecycle.

Layer between the kernel and `run_lease_lifecycle` (Session E). When a
sandbox profile is bound to the call, the gate runs `check_tool_invoke`
against `profile.tools.allowed/forbidden` BEFORE proposing the invocation
to the guard. If sandbox denies, the gate emits a `sandbox.deny` audit
envelope and short-circuits — guard layer is never reached.

Spec anchors:
- TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md §3 (denial semantics)
- TRINITY_AUDIT_EVENT_SPEC_V1.md §3 (sandbox events)

Pure-ish: only I/O is the audit append (delegated to AuditChain).
Article XX-safe at import.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from cli.core.audit import AuditChain
from cli.core.lease_lifecycle import LifecycleResult, run_lease_lifecycle
from cli.core.sandbox_contract import SandboxProfile
from cli.core.sandbox_enforcer import AxisDecision, check_tool_invoke
from cli.core.tool_registry import ToolRegistry


SANDBOX_DENY_EVENT_TYPE: str = "sandbox.deny"


@dataclass(frozen=True)
class GatedResult:
    """Outcome of a sandbox-gated lifecycle attempt.

    `sandbox_decision` is None iff no profile was provided (back-compat
    bypass). `lifecycle` is None when sandbox denied (short-circuit).
    `success` mirrors `lifecycle.success` when sandbox allowed, or False
    when sandbox denied.
    """

    sandbox_decision: Optional[AxisDecision]
    lifecycle: Optional[LifecycleResult]
    sandbox_audit_event: Optional[Dict[str, Any]]
    success: bool


def _deny_envelope(
    *,
    session_id: str,
    step_id: str,
    tool_name: str,
    decision: AxisDecision,
) -> Dict[str, Any]:
    return {
        "event_type": SANDBOX_DENY_EVENT_TYPE,
        "actor": "kernel",
        "decided_by": "kernel",
        "session_id": session_id,
        "step_id": step_id,
        "tool_name": tool_name,
        "axis": decision.axis,
        "reason": decision.reason,
        "detail": decision.detail,
    }


def run_sandbox_gated_lifecycle(
    *,
    session_id: str,
    step_id: str,
    tool_name: str,
    registry: ToolRegistry,
    chain: AuditChain,
    profile: Optional[SandboxProfile] = None,
    ttl_seconds: int = 600,
    allowed_paths: Optional[List[str]] = None,
    allowed_audit_event_types: Optional[List[str]] = None,
    sandbox_profile_ref: Optional[str] = None,
    now: Optional[datetime] = None,
) -> GatedResult:
    """Sandbox-gate then run the lease lifecycle.

    When `profile is None` this is identical to calling
    `run_lease_lifecycle(...)` (back-compat with Session E callers).

    When a profile is provided, the gate checks `tool.invoke` axis FIRST.
    On deny: emit `sandbox.deny` audit row and return early (no mint,
    no propose, no propose-row). On allow: delegate to lease_lifecycle.
    """
    if profile is None:
        lifecycle = run_lease_lifecycle(
            session_id=session_id,
            step_id=step_id,
            tool_name=tool_name,
            registry=registry,
            chain=chain,
            ttl_seconds=ttl_seconds,
            allowed_paths=allowed_paths,
            allowed_audit_event_types=allowed_audit_event_types,
            sandbox_profile_ref=sandbox_profile_ref,
            now=now,
        )
        return GatedResult(
            sandbox_decision=None,
            lifecycle=lifecycle,
            sandbox_audit_event=None,
            success=lifecycle.success,
        )

    decision = check_tool_invoke(profile, tool_name)
    if decision.verdict == "deny":
        envelope = _deny_envelope(
            session_id=session_id,
            step_id=step_id,
            tool_name=tool_name,
            decision=decision,
        )
        payload = dict(envelope)
        payload.pop("event_type", None)
        event = chain.append(SANDBOX_DENY_EVENT_TYPE, payload)
        return GatedResult(
            sandbox_decision=decision,
            lifecycle=None,
            sandbox_audit_event=event,
            success=False,
        )

    lifecycle = run_lease_lifecycle(
        session_id=session_id,
        step_id=step_id,
        tool_name=tool_name,
        registry=registry,
        chain=chain,
        ttl_seconds=ttl_seconds,
        allowed_paths=allowed_paths,
        allowed_audit_event_types=allowed_audit_event_types,
        sandbox_profile_ref=sandbox_profile_ref,
        now=now,
    )
    return GatedResult(
        sandbox_decision=decision,
        lifecycle=lifecycle,
        sandbox_audit_event=None,
        success=lifecycle.success,
    )


__all__ = [
    "SANDBOX_DENY_EVENT_TYPE",
    "GatedResult",
    "run_sandbox_gated_lifecycle",
]
