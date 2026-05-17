"""Lease lifecycle — Phase 6 Session E composition helper.

Wraps Sessions A→D in a single declarative call:
  mint → propose → emit → return result.

Pure-ish: the only I/O is the audit chain append (delegated to
`tool_invocation_emitter.emit_decision` → `AuditChain.append`); no
state mutation, no module-level side effects (Article XX Passive Core).

Spec anchors:
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §6 (Executor + Lease)
- docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md (Phase 6)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from cli.core.audit import AuditChain
from cli.core.executor import ExecutionLease
from cli.core.lease_minter import mint_lease
from cli.core.tool_invocation_emitter import emit_decision
from cli.core.tool_invocation_guard import (
    InvocationDecision,
    propose_invocation,
)
from cli.core.tool_registry import ToolRegistry


@dataclass(frozen=True)
class LifecycleResult:
    """Outcome of a single mint → propose → emit cycle.

    `success` mirrors `decision.verdict == "allow"`. `audit_event` is the
    chain row returned by AuditChain.append (with `hash` + `prev_hash`),
    or None when the envelope was empty / malformed (defensive — current
    guard always populates the envelope, so this is a future-proofing
    branch).
    """

    lease: ExecutionLease
    decision: InvocationDecision
    audit_event: Optional[Dict[str, object]]
    success: bool


def run_lease_lifecycle(
    *,
    session_id: str,
    step_id: str,
    tool_name: str,
    registry: ToolRegistry,
    chain: AuditChain,
    ttl_seconds: int = 600,
    allowed_paths: Optional[List[str]] = None,
    allowed_audit_event_types: Optional[List[str]] = None,
    sandbox_profile_ref: Optional[str] = None,
    now: Optional[datetime] = None,
) -> LifecycleResult:
    """Mint a lease, evaluate the tool invocation, and emit the audit row.

    Caller (Kernel) is responsible for inspecting the result and deciding
    whether to actually invoke the tool. This helper does NOT call any
    sibling CLI; it only authorises (or denies) the proposed invocation
    and records the verdict on the audit chain.

    Args:
        session_id: parent session id.
        step_id: step id within plan.
        tool_name: name of the tool the executor wants to call.
        registry: tool capability registry (Session A).
        chain: audit chain to append the decision envelope to.
        ttl_seconds, allowed_paths, allowed_audit_event_types,
        sandbox_profile_ref: forwarded to `mint_lease`.
        now: clock override for deterministic minting in tests.
    """
    lease = mint_lease(
        session_id,
        step_id,
        ttl_seconds=ttl_seconds,
        allowed_paths=allowed_paths,
        allowed_audit_event_types=allowed_audit_event_types,
        sandbox_profile_ref=sandbox_profile_ref,
        now=now,
    )

    decision = propose_invocation(lease, tool_name, registry, now=now)
    audit_event = emit_decision(chain, decision)

    return LifecycleResult(
        lease=lease,
        decision=decision,
        audit_event=audit_event,
        success=decision.verdict == "allow",
    )


__all__ = ["LifecycleResult", "run_lease_lifecycle"]
