"""Kernel + State-Graph organ — Article IV + Article XXVIII declarative contract.

Spec anchors:
- docs/specs/TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md (Phase 4)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §1 (Kernel) + §2 (State Graph)
- .ai/graphs/standard.yaml (live source of truth for the runtime graph)

This module is **declarative only** (Article XX Passive Core). It encodes the
canonical state list + transition catalog as Python constants so future
Phase 6/10 work (audit replay against spec, drift detection, T9 close pattern
landing) can assert "does the live graph match the spec?".

The runtime engines (`core/loop.py` + `core/kernel.py` + `core/state.py`) are
NOT modified by this contract. The single load-bearing claim of this module
is: **standard.yaml ⊆ STANDARD_TRANSITIONS**. The yaml is the source of truth;
the Python list is its mirror, intentionally permitted to declare additional
spec-pinned but not-yet-implemented rows (e.g. T9 close, T17 REOPENED) for
forward parity.

Article IV anchor: The kernel decides STATE TRANSITIONS (which target state is
legal). The Policy organ decides ALLOW/DENY (whether the transition may
proceed). The Verifier organ decides PASS/FAIL (whether evidence supports
the transition). These three axes do NOT collapse — the state-graph contract
here only enumerates the legal target states + decided_by attribution; it
does NOT decide ALLOW or PASS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ─────────── Canonical state catalog (Phase 4 §2.1) ───────────

CANONICAL_STATES: frozenset = frozenset({
    "READY",
    "THINK",
    "SANDBOX",
    "DO",
    "VERIFIED",
    "PROMOTED",
    "DEPLOYED",
    "RETRO",
    "DONE",
    "DEAD",     # universal terminal failure state per Phase 4 spec §2.2
})

TERMINAL_STATES: frozenset = frozenset({"DONE", "DEAD"})

INITIAL_STATE: str = "READY"


# ─────────── Authority closure (Article XVI + §6.1) ───────────

ALLOWED_AUTHORITY_CLASSES: frozenset = frozenset({
    "kernel",
    "verifier",
    "policy",
    "human",
})


# ─────────── StateTransition dataclass ───────────


@dataclass(frozen=True)
class StateTransition:
    """One row of the canonical transition catalog.

    Mirror of a `transitions:` entry in `.ai/graphs/standard.yaml`. The dataclass
    is frozen so STANDARD_TRANSITIONS may be safely cached / re-exposed.
    """

    from_state: str
    to_state: str
    trigger: str
    decided_by: str
    require_human_approval: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        # Light validation — catches obvious typos at module-load time.
        # NOTE: this runs once at import; it is NOT runtime gating.
        if self.from_state not in CANONICAL_STATES:
            raise ValueError(
                f"StateTransition.from_state {self.from_state!r} not in CANONICAL_STATES"
            )
        if self.to_state not in CANONICAL_STATES:
            raise ValueError(
                f"StateTransition.to_state {self.to_state!r} not in CANONICAL_STATES"
            )
        if self.decided_by not in ALLOWED_AUTHORITY_CLASSES:
            raise ValueError(
                f"StateTransition.decided_by {self.decided_by!r} not in "
                f"ALLOWED_AUTHORITY_CLASSES"
            )


# ─────────── STANDARD_TRANSITIONS — mirror of standard.yaml ───────────

STANDARD_TRANSITIONS: List[StateTransition] = [
    StateTransition(
        from_state="READY",
        to_state="THINK",
        trigger="sss",
        decided_by="kernel",
        notes="T1 — session start; sss ritual fires READY→THINK",
    ),
    StateTransition(
        from_state="THINK",
        to_state="SANDBOX",
        trigger="vvv_pass",
        decided_by="verifier",
        notes="T2 — verification questions answered; THINK→SANDBOX (vvv fires this; see RITUALS.md canonical order)",
    ),
    StateTransition(
        from_state="SANDBOX",
        to_state="DO",
        trigger="nnn_pass",
        decided_by="kernel",
        notes="T3 — plan accepted; SANDBOX→DO after nnn budget-check (vvv ran first; see RITUALS.md canonical order)",
    ),
    StateTransition(
        from_state="DO",
        to_state="VERIFIED",
        trigger="gogogo_complete",
        decided_by="verifier",
        notes="T4 — all gogogo steps verified; DO→VERIFIED",
    ),
    StateTransition(
        from_state="VERIFIED",
        to_state="PROMOTED",
        trigger="promote_request",
        decided_by="human",
        require_human_approval=True,
        notes="T5 — operator approves promote; VERIFIED→PROMOTED",
    ),
    StateTransition(
        from_state="PROMOTED",
        to_state="DEPLOYED",
        trigger="deploy_request",
        decided_by="human",
        require_human_approval=True,
        notes="T6 — operator approves deploy; PROMOTED→DEPLOYED",
    ),
    StateTransition(
        from_state="DEPLOYED",
        to_state="RETRO",
        trigger="rrr",
        decided_by="kernel",
        notes="T7 — rrr ritual fires DEPLOYED→RETRO",
    ),
    StateTransition(
        from_state="RETRO",
        to_state="DONE",
        trigger="rrr_complete",
        decided_by="kernel",
        notes="T8 — retro accepted; RETRO→DONE (terminal)",
    ),
    StateTransition(
        from_state="VERIFIED",
        to_state="RETRO",
        trigger="rrr",
        decided_by="kernel",
        notes=(
            "T8a — non-deploy closure path; VERIFIED→RETRO lets "
            "documentation/refactor/admin sessions close without ddd"
        ),
    ),
]


# ─────────── helpers ───────────


def transitions_for(from_state: str) -> List[StateTransition]:
    """Return the list of transitions whose `from_state` matches `from_state`.

    Returns an empty list if `from_state` has no outgoing transitions (e.g.
    `from_state` is a terminal state). Article XX: pure function, no side
    effects.
    """
    return [t for t in STANDARD_TRANSITIONS if t.from_state == from_state]


def find_transition(
    from_state: str, trigger: str
) -> Optional[StateTransition]:
    """Return the unique transition matching (from_state, trigger), or None.

    The yaml schema permits multiple outgoing transitions from a single state
    only when they have distinct triggers; this helper assumes that invariant
    and returns the first match.
    """
    for t in STANDARD_TRANSITIONS:
        if t.from_state == from_state and t.trigger == trigger:
            return t
    return None


__all__ = [
    "CANONICAL_STATES",
    "TERMINAL_STATES",
    "INITIAL_STATE",
    "ALLOWED_AUTHORITY_CLASSES",
    "StateTransition",
    "STANDARD_TRANSITIONS",
    "transitions_for",
    "find_transition",
]
