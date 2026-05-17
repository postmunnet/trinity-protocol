"""DDD / Human Gate organ — Article XIII + Article XXVIII declarative contract.

Spec anchors:
- docs/specs/TRINITY_DDD_HUMAN_GATE_SPEC_V1.md (Phase 11, DRAFT v2)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §13 (DDD / Human Gate)
- .ai/schemas/decision_packet.schema.json
- .ai/schemas/approval.schema.json
- .ai/schemas/rejection.schema.json
- .ai/schemas/hold.schema.json

This module is **declarative only** (Article XX Passive Core). It mirrors the
4 operator-authored DDD schemas + spec §3-§7 surface as closed frozensets +
Python dataclasses so future Phase 11 hardening (HMAC signing on operator-
side, multi-operator quorum, audit field enforcement) can bind against a
machine-checkable kernel-side contract.

Runtime `commands/ddd.py` is NOT modified by this contract. The HOW (verdict
emission, audit chain wiring, transport-boundary dual-emit) lives in the
ritual gate; this module describes WHAT shapes the artifacts have.

Article XIII anchor: DDD verdicts are HUMAN-decided artifacts. AI may
construct a decision_packet (proposing_role = planner/executor/verifier) but
the approval/rejection/hold MUST carry `decided_by: "human"` per Article XIII.

Article XVI anchor: closed frozensets — APPROVAL_ACTIONS / VERDICT_ACTIONS /
REQUESTED_ACTIONS — encode the policy-engine-style verdict closure. Unknown
action = denied.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────── §4 — Approval action enum (mirror of approval.schema.json) ───────────

APPROVAL_ACTIONS: frozenset = frozenset({
    "promote",
    "deploy",
    "amend_approve",
})


# ─────────── §3-§6 — Top-level verdict action vocabulary ───────────
# This is the closed set of operator-decision-action verdicts across the three
# verdict files. Each verdict file pins its `action` enum to a single value:
#   approval.json  → "promote" | "deploy" | "amend_approve"  (APPROVAL_ACTIONS)
#   rejection.json → "reject"
#   hold.json      → "hold"

VERDICT_ACTIONS: frozenset = frozenset({
    "approve",   # umbrella label — actual action ∈ APPROVAL_ACTIONS
    "reject",
    "hold",
})


# ─────────── §3 — Proposing-role enum (mirror of decision_packet.proposing_role) ───────────

PROPOSING_ROLES: frozenset = frozenset({
    "planner",
    "executor",
    "verifier",
})


# ─────────── §3 — Requested-action enum (mirror of decision_packet.requested_action) ───────────

REQUESTED_ACTIONS: frozenset = frozenset({
    "promote",
    "deploy",
    "abort",
    "amend",
})


# ─────────── §4-§6 — Decided-by closure (Article XIII) ───────────
# `decided_by` on approval/rejection/hold MUST be "human" per Article XIII.
# `decided_by` on packet_emitted/timeout events is "kernel" (auto-generated).

DECIDED_BY_VALUES: frozenset = frozenset({
    "human",
    "kernel",
})


# ─────────── §7 — Audit event registry (5 events) ───────────

DDD_AUDIT_EVENTS: frozenset = frozenset({
    "ddd.packet_emitted",
    "ddd.approved",
    "ddd.rejected",
    "ddd.held",
    "ddd.timeout",
})


# ─────────── §3 + §3.1 — DecisionPacket dataclass + Presentation sub-shape ───────────


@dataclass
class DecisionPacket:
    """Authoritative Python mirror of `.ai/schemas/decision_packet.schema.json`.

    Bundle presented to the human operator at the DDD gate. Constructed by the
    kernel after verifier_report consolidation; consumed by the operator-side
    UI (TG bot, web, CLI) to elicit approve/reject/hold.
    """

    id: str
    session: str
    created_ts: str                                # RFC3339 UTC
    proposing_role: str                            # one of PROPOSING_ROLES
    requested_action: str                          # one of REQUESTED_ACTIONS
    verifier_reports: List[Dict[str, Any]] = field(default_factory=list)
    presentation: Dict[str, Any] = field(default_factory=dict)
    expires_ts: str = ""                           # RFC3339 UTC


# ─────────── §4 — Approval dataclass ───────────


@dataclass
class Approval:
    """Authoritative Python mirror of `.ai/schemas/approval.schema.json`."""

    packet_id: str
    decided_by: str                                # const "human" per Article XIII
    decided_at: str                                # RFC3339 UTC
    action: str                                    # one of APPROVAL_ACTIONS
    notes: str = ""
    signature: Optional[str] = None                # operator-side signature (Phase 14)


# ─────────── §5 — Rejection dataclass ───────────


@dataclass
class Rejection:
    """Authoritative Python mirror of `.ai/schemas/rejection.schema.json`."""

    packet_id: str
    decided_by: str                                # const "human"
    decided_at: str                                # RFC3339 UTC
    action: str = "reject"                         # const
    reason: str = ""                               # minLength 1 — operator MUST give reason
    signature: Optional[str] = None


# ─────────── §6 — Hold dataclass ───────────


@dataclass
class Hold:
    """Authoritative Python mirror of `.ai/schemas/hold.schema.json`."""

    packet_id: str
    decided_by: str                                # const "human"
    decided_at: str                                # RFC3339 UTC
    action: str = "hold"                           # const
    until: str = ""                                # RFC3339 — when hold lifts
    notes: str = ""
    signature: Optional[str] = None


# ─────────── jsonschema validator helpers ───────────

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
_schema_cache: Dict[str, Dict[str, Any]] = {}


def _load_schema(name: str) -> Dict[str, Any]:
    if name not in _schema_cache:
        path = _SCHEMA_DIR / f"{name}.schema.json"
        _schema_cache[name] = json.loads(path.read_text(encoding="utf-8"))
    return _schema_cache[name]


def validate_decision_packet(packet: Dict[str, Any]) -> None:
    """Validate a decision packet against the operator-authored schema.

    Raises `jsonschema.ValidationError` on failure. Pure function — no audit
    emission, no side effects (Article XX).
    """
    import jsonschema
    jsonschema.validate(instance=packet, schema=_load_schema("decision_packet"))


def validate_approval(approval: Dict[str, Any]) -> None:
    import jsonschema
    jsonschema.validate(instance=approval, schema=_load_schema("approval"))


def validate_rejection(rejection: Dict[str, Any]) -> None:
    import jsonschema
    jsonschema.validate(instance=rejection, schema=_load_schema("rejection"))


def validate_hold(hold: Dict[str, Any]) -> None:
    import jsonschema
    jsonschema.validate(instance=hold, schema=_load_schema("hold"))


__all__ = [
    "APPROVAL_ACTIONS",
    "VERDICT_ACTIONS",
    "PROPOSING_ROLES",
    "REQUESTED_ACTIONS",
    "DECIDED_BY_VALUES",
    "DDD_AUDIT_EVENTS",
    "DecisionPacket",
    "Approval",
    "Rejection",
    "Hold",
    "validate_decision_packet",
    "validate_approval",
    "validate_rejection",
    "validate_hold",
]
