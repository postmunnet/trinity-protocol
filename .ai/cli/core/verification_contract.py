"""Verification contract — Article III + IV declarative contract surface.

Spec anchors:
- docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md §2 (verdict vocabulary)
- docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md §3 (Pyramid of Judgment layers)
- docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md §4.6 (contract envelope shape)
- .ai/schemas/verification_contract.schema.json (this session — Phase 3 deliverable)

This module is **declarative only** (Article XX Passive Core). It mirrors the
verification contract envelope shape as Python dataclasses + closed frozensets
so future Phase 3 binding (nnn validator gate + gogogo precondition check)
can bind against a machine-checkable contract surface.

Article III anchor: the verification contract freezes the verification surface
BEFORE execution — the executor cannot widen it mid-run.

Article IV anchor: the contract describes WHAT to verify; the Verifier organ
decides PASS/RETRY/NEEDS_HUMAN/DEAD against it. The two stay orthogonal.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────── §2 — Closed verdict vocabulary ───────────
# Must equal verifier.VALID_VERDICTS (test asserts equality).

VERDICT_VOCABULARY: frozenset = frozenset({
    "PASS",
    "RETRY",
    "NEEDS_HUMAN",
    "DEAD",
})


# ─────────── §3 — Pyramid of Judgment layers ───────────
# 1 = deterministic rule engine (verifier-rules.yaml)
# 2 = policy engine (TRINITY_POLICY_ENGINE_SPEC_V1)
# 3 = gated LLM judge (Phase 8+; layer 3 PASS authority bounded by §6.6)
# 4 = human (Article XIII)

PYRAMID_LAYERS: tuple = (1, 2, 3, 4)


# ─────────── Operational tier classification (mirror of verifier.TIER_MAP values) ───────────

SANDBOX_TIERS: frozenset = frozenset({"HOT", "WARM", "COLD"})


# ─────────── AcceptanceEntry dataclass (mirrors schema acceptance[i]) ───────────


@dataclass
class AcceptanceEntry:
    """One acceptance row of a verification contract.

    Mirrors spec §4.6 — id/description/rule_set/predicates/evidence_keys/
    command/expect_exit/required. Optional fields: notes, on_fire_verdict.

    Note: this AcceptanceEntry is the per-step Pyramid binding (rule_set +
    predicates). It is DIFFERENT from Trinity's `plan_envelope.acceptance[]`
    (rrr-side exit-code checks). The two artifacts may coincide in shape but
    are produced + consumed by different organs.
    """

    id: str                                 # ^A[0-9]+$
    description: str
    rule_set: str
    command: str
    expect_exit: int
    required: bool
    predicates: List[str] = field(default_factory=list)
    evidence_keys: List[str] = field(default_factory=list)
    notes: str = ""
    on_fire_verdict: Optional[Dict[str, str]] = None  # {predicate_name -> verdict in VERDICT_VOCABULARY}


# ─────────── VerificationContract top-level dataclass ───────────


@dataclass
class VerificationContract:
    """Authoritative Python mirror of `.ai/schemas/verification_contract.schema.json`.

    Authored at nnn (Phase 3 binding deferred) and consumed by:
    - Phase 3 nnn validator gate (§4.6.1 precedence-validator clause)
    - gogogo precondition checks (contract presence + revision match)
    - rrr terminal gate (per-acceptance command + expect_exit replay)
    - audit chain payload of `nnn.proposed` / `verify.completed` events
    """

    id: str
    description: str
    version: str                                       # semver MAJOR.MINOR[.PATCH]
    acceptance: List[AcceptanceEntry] = field(default_factory=list)
    expected_terminal_verdict: Optional[str] = None    # one of VERDICT_VOCABULARY
    rationale_for_fallback_divergence: str = ""
    policy_snapshot: Optional[Dict[str, str]] = None   # see schema policy_snapshot


# ─────────── jsonschema validator helper ───────────

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "verification_contract.schema.json"
)
_schema_cache: Optional[Dict[str, Any]] = None


def _load_schema() -> Dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _schema_cache


def validate_contract_dict(contract: Dict[str, Any]) -> None:
    """Validate a verification contract dict against the schema.

    Raises `jsonschema.ValidationError` on schema violation. Pure function:
    no side effects, no audit emission. Article XX passive.

    Note: this validates the SHAPE only. The §4.6.1 precedence-validator
    clause (semantic check that predicate-class membership doesn't get
    inverted) is NOT enforced here — that lives in the future Phase 3 nnn
    validator gate (also deferred per spec §4.6.1).
    """
    import jsonschema   # local import to keep module passive

    schema = _load_schema()
    jsonschema.validate(instance=contract, schema=schema)


__all__ = [
    "VERDICT_VOCABULARY",
    "PYRAMID_LAYERS",
    "SANDBOX_TIERS",
    "AcceptanceEntry",
    "VerificationContract",
    "validate_contract_dict",
]
