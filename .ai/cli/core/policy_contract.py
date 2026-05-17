"""Policy organ — Article IV + Article XXVIII declarative contract.

Spec anchors:
- docs/specs/TRINITY_POLICY_ENGINE_SPEC_V1.md (Phase 5)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §3 (Policy Engine)
- .ai/schemas/policy_query_envelope.v1.yaml (operator-authored envelope schema)

This module is **declarative only** (Article XX Passive Core). It encodes the
policy organ's contract surface — verdict set, precedence rule, closed reason
codes, query/verdict envelope dataclasses — so future Phase 6+ runtime wiring
(`Loop.fire()` → `policy.query()` → kernel decision) can bind against a
machine-checkable contract.

The runtime stub (`core/policy.py`) is NOT modified by this contract;
`policy_contract.py` is its declarative sibling.

Article IV anchor: Policy decides ALLOW / DENY / CONDITIONAL / NEEDS_HUMAN.
It does NOT decide PASS / FAIL (Verifier's job) and does NOT fire transitions
(Kernel's job). The three axes stay orthogonal.

Article XVI anchor: Default-deny — unknown authority → deny with reason
`unknown_authority`. The VERDICT_SET frozenset is closed; the engine MUST
NOT return a fifth verdict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────── §2.1 — Closed verdict set ───────────

VERDICT_SET: frozenset = frozenset({
    "allow",
    "deny",
    "conditional",
    "NEEDS_HUMAN",
})


# ─────────── §2.2 — Deny-wins precedence ───────────

# Highest-precedence FIRST. Order is normative:
#   deny > NEEDS_HUMAN > conditional > allow
VERDICT_PRECEDENCE: tuple = (
    "deny",
    "NEEDS_HUMAN",
    "conditional",
    "allow",
)


# ─────────── §2.4 — Closed reason-code enumeration (9 codes) ───────────

REASON_CODES: frozenset = frozenset({
    "unknown_authority",          # default-deny (Article XVI)
    "forbidden_path",             # target matches forbidden_paths glob (§7)
    "secret_pattern_detected",    # payload matches secret regex / entropy threshold (§7)
    "human_gate_required",        # Critical Gate Rule triggered (§6)
    "illegal_actor",              # actor lacks declared authority (Article IV / XVI)
    "illegal_target",             # target outside actor's allowed surface (Article XVI)
    "schema_invalid",             # query envelope failed schema validation (§4)
    "quota_exceeded",             # actor exceeded a declared quota (e.g. retry budget)
    "amendment_required",         # rule exists but is marked stale; human must refresh
})


# ─────────── §4.1 — Closed authority / action / target enumerations ───────────

ALLOWED_AUTHORITY_CLASSES: frozenset = frozenset({
    "ai",
    "human",
    "kernel",
    "tool",
    "transport",
})


ACTION_KINDS: frozenset = frozenset({
    "transition",
    "tool_invoke",
    "fs_read",
    "fs_write",
    "fs_delete",
    "net_outbound",
    "proc_exec",
    "policy_read",
    "policy_write",
    "ddd_propose",
    "ddd_decide",
})


TARGET_TYPES: frozenset = frozenset({
    "path",
    "host",
    "binary",
    "transition",
    "tool_name",
    "audit_event",
    "policy_file",
    "none",
})


# ─────────── §4.1 — Query envelope dataclass ───────────


@dataclass
class PolicyQueryEnvelope:
    """Kernel → Policy Engine query envelope.

    Schema mirror: `.ai/schemas/policy_query_envelope.v1.yaml` (operator-authored DRAFT).
    """

    schema_version: str           # pinned "1"
    query_id: str                 # caller-generated ULID
    actor: Dict[str, str]         # {id, authority_class}
    action: Dict[str, Any]        # {kind, detail}
    target: Dict[str, Optional[str]]   # {type, value}
    context: Dict[str, Any]       # {session_id, ritual_phase, declared_authority, evidence_refs}


# ─────────── §4.2 — Verdict envelope dataclass ───────────


@dataclass
class PolicyVerdictEnvelope:
    """Policy Engine → Kernel verdict envelope.

    Schema mirror: `.ai/schemas/policy_query_envelope.v1.yaml` (operator-authored DRAFT).
    """

    schema_version: str           # pinned "1"
    query_id: str                 # echoed from query
    verdict: str                  # one of VERDICT_SET
    reason: str                   # one of REASON_CODES (or "" for allow)
    evidence_ref: Dict[str, str]  # {rule_id, rule_file, rule_anchor}
    emitted_at: str               # RFC3339 UTC
    engine_version: str = "1.0"
    conditions: List[Dict[str, Any]] = field(default_factory=list)   # only when verdict == conditional
    human_gate: Optional[Dict[str, str]] = None                       # only when verdict == NEEDS_HUMAN


# ─────────── helpers ───────────


def resolve_precedence(verdicts: List[str]) -> str:
    """Return the highest-precedence verdict from a non-empty list.

    Per spec §2.2 — deny wins, then NEEDS_HUMAN, then conditional, then allow.
    Unknown verdict strings are ignored (not in VERDICT_SET); if the resulting
    candidate pool is empty, ValueError is raised so the caller surfaces the
    drift rather than silently treating it as `allow`.
    """
    if not verdicts:
        raise ValueError("resolve_precedence requires a non-empty verdict list")
    candidates = [v for v in verdicts if v in VERDICT_SET]
    if not candidates:
        raise ValueError(
            f"resolve_precedence: no candidate matched VERDICT_SET: {verdicts!r}"
        )
    for tier in VERDICT_PRECEDENCE:
        if tier in candidates:
            return tier
    # Unreachable — VERDICT_PRECEDENCE covers all VERDICT_SET by construction.
    raise AssertionError(
        "VERDICT_PRECEDENCE does not cover VERDICT_SET — module-level invariant broken"
    )


__all__ = [
    "VERDICT_SET",
    "VERDICT_PRECEDENCE",
    "REASON_CODES",
    "ALLOWED_AUTHORITY_CLASSES",
    "ACTION_KINDS",
    "TARGET_TYPES",
    "PolicyQueryEnvelope",
    "PolicyVerdictEnvelope",
    "resolve_precedence",
]
