"""Executor organ — Article IV + Article XXVIII declarative contract.

Spec anchors:
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §6 (Executor)
- docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md (Phase 6 — DRAFT v2)
- docs/specs/TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md (Phase 7 — DRAFT v2)

This module is **declarative only** (Article XX Passive Core). It enumerates
the executor organ's contract surface — the 8 Extension-Rule fields from
Article XXVIII, the required output artifact set, the audit event types the
executor is permitted to emit, the forbidden-action list, and the input /
output schemas via the `ExecutionLease` + `ArtifactManifest` dataclasses.

It deliberately ships **no behavior**. The runtime executor binding (Phase 6:
`.ai/tools.capabilities.yaml` + sibling CLI dispatch; Phase 7: sandbox profile
runtime hook) consumes this contract; nothing in this module mutates state,
emits audit events, or opens external resources at import time.

Article IV anchor: Executor decides bounded action; it MUST NOT decide
verification (that is the Verifier organ, Organ #8) nor mutate state
(that is the Kernel, Organ #1). The `FORBIDDEN_ACTIONS` list below codifies
this separation.

Article XVI anchor: ALLOWED_AUDIT_EVENT_TYPES is a closed frozenset; any
emission outside this set is "unknown authority" and MUST be refused by
the audit organ (Phase 10 verify-chain strict mode).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ─────────── Article XXVIII Extension Rule — 8 fields ───────────
# Encoded verbatim from TRINITY_ORGAN_MAP_V1.md §6 Executor entry. The
# dict keys MUST exist (constants are checked by test_executor_contract);
# the values document the constitutional contract — they are NOT runtime
# config.

EXECUTOR_CONTRACT: Dict[str, str] = {
    "role": "Bounded action — file edits, shell/tool calls, execution logs, diffs.",
    "authority": (
        "Mutates artifacts within scope of an approved plan + execution lease + "
        "sandbox profile. NEVER decides verification, approval, final completion, "
        "or state transition (Article IV)."
    ),
    "inputs": (
        "approved plan envelope (.state/plan.json after nnn_pass) + execution "
        "lease (issued by Kernel against the active session, scoped to step_id) + "
        "sandbox profile (Phase 7 runtime hook)."
    ),
    "outputs": (
        "diff.patch (unified diff of file edits) + execution.log (free-form "
        "text + JSON Lines mix) + tool_calls.jsonl (NDJSON of tool invocations) "
        "+ artifact_manifest.json (per-step manifest of produced artifacts with "
        "sha256 hashes)."
    ),
    "artifacts": (
        "The four output files above PLUS the actual file changes inside "
        "DO/dev/ (after vvv_pass). Writes to DO/prod/ are forbidden — "
        "promotion is human-decided (Article XIII)."
    ),
    "state_permissions": (
        "May write inside session DO/dev/ subtree after vvv_pass marker exists. "
        "Cannot write DO/prod/ (operator-only) or .ai/policies/** / .ai/audit/** "
        "/ .ai/schemas/** / docs/constitution/** / docs/specs/** "
        "(constitutional forbidden writes — Article XVI Least Authority)."
    ),
    "failure_mode": (
        "Execution error MUST emit gogogo.step_failed with diff and log "
        "attached as evidence (Article XXIII Failure Visibility). Silent "
        "success is FORBIDDEN — every step exit MUST be visible in the audit "
        "chain via either gogogo.step_passed or gogogo.step_failed."
    ),
    "audit_events": (
        "gogogo.step_started / gogogo.step_completed / gogogo.step_passed / "
        "gogogo.step_failed for ritual gate boundaries; tool.invocation.started "
        "/ tool.invocation.completed / tool.invocation.failed / "
        "tool.invocation.timeout for per-tool calls. All event_types MUST "
        "exist in TRINITY_AUDIT_EVENT_SPEC_V1 §3 registry."
    ),
}


# ─────────── Required output artifacts (Organ Map §6) ───────────
# Per-step artifact set. Each future executor invocation MUST produce these
# four files in its working directory (typically DO/dev/<step_id>/). The
# artifact manifest cross-links them via sha256.

REQUIRED_OUTPUT_ARTIFACTS: List[str] = [
    "diff.patch",
    "execution.log",
    "tool_calls.jsonl",
    "artifact_manifest.json",
]


# ─────────── Allowed audit event types (Article XVI closure) ───────────
# Subset of TRINITY_AUDIT_EVENT_SPEC_V1 §3 registry that the executor is
# permitted to cause-to-be-emitted. The audit organ (Phase 10 strict
# mode) MAY refuse any event_type outside this set when the actor is
# declared as `executor`.

ALLOWED_AUDIT_EVENT_TYPES: frozenset = frozenset({
    "gogogo.step_started",
    "gogogo.step_completed",
    "gogogo.step_passed",
    "gogogo.step_failed",
    "tool.invocation_proposed",
    "tool.invocation_denied",
    "tool.invocation.started",
    "tool.invocation.completed",
    "tool.invocation.failed",
    "tool.invocation.timeout",
    "capture.started",
    "capture.completed",
    "capture.failed_partial",
})


# ─────────── Forbidden actions (Article IV codification) ───────────
# Non-exhaustive list of role-collapse risks. Verifier (Phase 8) may
# enforce these via deterministic predicates against the audit chain.

FORBIDDEN_ACTIONS: List[str] = [
    "decide verifier verdict (PASS / FAIL / NEEDS_HUMAN / DEAD) — verdicts come from the Verifier organ (#8)",
    "approve DDD / Human Gate — approvals come from the Human Gate (#13)",
    "fire state transitions (e.g. promote_request, deploy_request) — transitions are Kernel-decided (#1)",
    "write to .ai/policies/** (operator-only — Article XVI)",
    "mutate .ai/audit/events.ndjson rows (append-only chain — Article X)",
    "write to .ai/schemas/** arbitrarily (spec-mandated additions only — Article XXIX)",
    "write to docs/constitution/** or docs/specs/** (canonical artifacts — Article XXIX)",
    "bypass sandbox profile (Phase 7 boundary — Article XVI)",
    "self-trigger or auto-retry without explicit Kernel re-invocation (Article XX Passive Core)",
    "claim authority beyond execution lease scope (lease.step_id binding — Article XVI)",
]


# ─────────── Input / output dataclasses ───────────


@dataclass
class ExecutionLease:
    """Kernel-issued authority token for a single executor invocation.

    The Kernel mints a lease when transitioning a step into EXECUTE. The
    lease binds the executor's authority to a specific step within a
    specific session, with an explicit allowed-paths list and audit-event
    closure. The lease is consumed by the executor and recorded as
    evidence in the audit chain.

    Schema mirror: .ai/schemas/execution_lease.schema.json
    """

    lease_id: str                                 # ULID-shaped opaque id
    session_id: str                               # parent session
    step_id: str                                  # step id within plan
    granted_at: str                               # RFC3339 UTC
    expires_at: str                               # RFC3339 UTC; hard deadline
    allowed_paths: List[str] = field(default_factory=list)
    allowed_audit_event_types: List[str] = field(default_factory=list)
    required_artifacts: List[str] = field(default_factory=lambda: list(REQUIRED_OUTPUT_ARTIFACTS))
    sandbox_profile_ref: Optional[str] = None     # path to Phase 7 sandbox profile
    decided_by: str = "kernel"                    # always kernel-issued


@dataclass
class ArtifactManifest:
    """Per-step manifest of artifacts produced by a single executor invocation.

    Written by the executor at step completion; consumed by Verifier
    (Phase 8) for artifact-existence checks and by Audit (Phase 10) for
    artifact-reference validation (`scan_artifact_refs`).

    Schema mirror: .ai/schemas/artifact_manifest.schema.json
    """

    manifest_version: str                         # pinned "trinity.artifact_manifest.v1"
    session_id: str
    step_id: str
    artifacts: List[Dict[str, object]] = field(default_factory=list)
    generated_at: str = ""                        # RFC3339 UTC
    lease_id: Optional[str] = None                # back-ref to ExecutionLease


__all__ = [
    "EXECUTOR_CONTRACT",
    "REQUIRED_OUTPUT_ARTIFACTS",
    "ALLOWED_AUDIT_EVENT_TYPES",
    "FORBIDDEN_ACTIONS",
    "ExecutionLease",
    "ArtifactManifest",
]
