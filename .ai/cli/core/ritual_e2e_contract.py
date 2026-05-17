"""Ritual E2E Warm-Path organ — Article XVI declarative contract (Phase 16).

Spec anchors:
- trinity_organ_refactor_prd.md §9 Phase 16 (End-to-End Ritual Integration)
- docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md §9 (tier-aware ritual strictness)
- TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md §B (Decision Velocity Tiers)

This module is **declarative only** (Article XX Passive Core). It encodes
the canonical ritual sequence + the tier-aware strictness matrix as Python
constants so future Phase 16 runtime gating (kernel enforces ritual
required/optional per tier at each gate) can bind against a machine-
checkable contract.

The state graph (`state_graph.py`) and ritual commands (`commands/*.py`)
are NOT modified by this contract. The HOW (per-gate enforcement of
"vvv required on WARM but optional on HOT") is future work.

Article XVI anchor: RITUAL_TIER_STRICTNESS is the closed authority table.
Unknown ritual / tier combination = treated as "optional"; the runtime
enforcer MAY tighten via amendment.

Article IV anchor: each ritual is an organ-coordinator — close ≠ retro ≠
rrr ≠ ddd. The sequence ties their handoff order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


# ─────────── PRD §2 + Ritual Contract §1 — Canonical 7-ritual sequence ───────────

RITUAL_SEQUENCE: Tuple[str, ...] = (
    "sss",       # session new
    "vvv",       # 5-question verification (post-context, pre-plan)
    "nnn",       # plan envelope + budget check
    "gogogo",    # walk plan steps, verifier verdict per step
    "ddd",       # human-decided promote+deploy gate
    "rrr",       # retro envelope + memory-cli index + terminal closure
    "close",     # seal + archive + final manifest
)


# ─────────── Ritual Contract §9 — Tier-aware strictness matrix (21 cells) ───────────
# Per spec line 245-249:
#   HOT  : optional      / optional   / optional   / invoked   / not_required / optional / not_required
#   WARM : required      / required   / required   / required  / required-dev / required / recommended
#   COLD : required      / required   / required   / required  / required-prod-hmac / required / required

RITUAL_TIER_STRICTNESS: Dict[Tuple[str, str], str] = {
    # HOT row
    ("sss",    "HOT"):  "optional",
    ("vvv",    "HOT"):  "optional",
    ("nnn",    "HOT"):  "optional",
    ("gogogo", "HOT"):  "invoked_directly",
    ("ddd",    "HOT"):  "not_required",
    ("rrr",    "HOT"):  "optional",
    ("close",  "HOT"):  "not_required",
    # WARM row
    ("sss",    "WARM"): "required",
    ("vvv",    "WARM"): "required",
    ("nnn",    "WARM"): "required",
    ("gogogo", "WARM"): "required",
    ("ddd",    "WARM"): "required",
    ("rrr",    "WARM"): "required",
    ("close",  "WARM"): "recommended",
    # COLD row
    ("sss",    "COLD"): "required",
    ("vvv",    "COLD"): "required",
    ("nnn",    "COLD"): "required",
    ("gogogo", "COLD"): "required",
    ("ddd",    "COLD"): "required",
    ("rrr",    "COLD"): "required",
    ("close",  "COLD"): "required",
}


# ─────────── Per-path required-ritual closures ───────────

WARM_PATH_REQUIRED_RITUALS: frozenset = frozenset({
    "sss", "vvv", "nnn", "gogogo", "ddd", "rrr",
    # close is "recommended" on WARM, not required
})


COLD_PATH_REQUIRED_RITUALS: frozenset = frozenset({
    "sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "close",
})


HOT_PATH_OPTIONAL_RITUALS: frozenset = frozenset({
    "sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "close",
})


# ─────────── Ritual Contract §9 — DDD target binding per tier ───────────

DDD_TIER_TARGETS: Dict[str, str] = {
    "WARM": "dev",
    "COLD": "prod",
    # HOT: ddd not_required — no target binding
}


# ─────────── RitualLifecycleEvent dataclass ───────────


@dataclass
class RitualLifecycleEvent:
    """One row in the per-session ritual lifecycle log.

    A WARM-path session emits 6 events (sss/vvv/nnn/gogogo/ddd/rrr); a
    COLD-path session emits 7 (adds close). HOT-path events are optional.
    """

    ritual: str                                      # one of RITUAL_SEQUENCE
    ts: str                                          # RFC3339 UTC
    decided_by: str                                  # kernel | verifier | policy | human
    tier: str                                        # HOT | WARM | COLD
    outcome: str                                     # passed | failed | skipped | timeout
    audit_event_id: Optional[str] = None
    notes: str = ""


# ─────────── helper ───────────


def is_required(ritual: str, tier: str) -> bool:
    """Return True iff `ritual` is strictly required under `tier`.

    Per Ritual Contract §9: "required" and "required-dev"/"required-prod"
    are both treated as required; "recommended" / "optional" /
    "not_required" / "invoked_directly" are NOT required.

    Pure function (Article XX passive).
    """
    strictness = RITUAL_TIER_STRICTNESS.get((ritual, tier))
    if strictness is None:
        return False
    return strictness == "required"


__all__ = [
    "RITUAL_SEQUENCE",
    "RITUAL_TIER_STRICTNESS",
    "WARM_PATH_REQUIRED_RITUALS",
    "COLD_PATH_REQUIRED_RITUALS",
    "HOT_PATH_OPTIONAL_RITUALS",
    "DDD_TIER_TARGETS",
    "RitualLifecycleEvent",
    "is_required",
]
