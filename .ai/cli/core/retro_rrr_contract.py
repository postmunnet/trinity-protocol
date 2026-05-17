"""Retro + RRR Terminal Gate organs — Article IV + Article IX declarative contract.

Spec anchors:
- docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md (Phase 12, DRAFT v1.0)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §11 (Retro) + §12 (RRR)

This module is **declarative only** (Article XX Passive Core). It encodes
the mechanical/semantic split between RRR Terminal Gate (Organ #12, kernel-
decided, mechanical) and Retro (Organ #11, advisory, semantic) as closed
frozensets + Python dataclasses, so future runtime evolution can bind
against the spec-§3 invariants.

The runtime `commands/rrr.py` (commit 1cf9122 — retro_envelope.md
production) is NOT modified by this contract. The HOW lives in the ritual
gate; this module describes WHAT mechanical fields rrr MUST produce + WHAT
semantic categories rrr MUST NOT touch.

Article IV anchor: rrr fires the terminal closure transition + emits a
deterministic envelope; the retro_writer agent (sibling, advisory) proposes
semantic interpretation. The two organs do NOT collapse.

Article IX anchor: rrr MUST NOT call `memory-cli learn` — semantic indexing
of meaning is forbidden. RETRO_FORBIDDEN_PATTERNS encodes the source-level
lint substrings per spec §3.2.

Article XX anchor: pinning is human-only — `memory-cli pin` runs through
the operator, never auto-fired from rrr or retro_writer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────── §4.1 — Schema version pin ───────────

RETRO_ENVELOPE_SCHEMA_VERSION: str = "trinity.retro_envelope.v1"


# ─────────── §3.1 — RRR's 13 mechanical output fields ───────────
# Verbatim from spec §3.1 lines 213-225. RRR MUST populate retro_envelope.md
# with each of these. Source of truth = spec. The frozenset is closed —
# adding a field requires an Article XXIX amendment (spec § + this constant).

RRR_OUTPUT_FIELDS: frozenset = frozenset({
    "session_id",
    "ts_started",
    "ts_closed",
    "duration_seconds",
    "acceptance_results",
    "forbidden_diff_status",
    "baseline_untracked",
    "audit_chain_status",
    "transition_count",
    "gogogo_verdicts",
    "tier",
    "memory_index_result",
    "artifact_paths",
})


# ─────────── §3.2 — RRR's forbidden source-level substring patterns ───────────
# Per spec §3.2 lines 249-260 — these substrings MUST NOT appear in rrr.py
# source. Article IX: rrr cannot perform semantic indexing. Article XVI:
# unknown authority denied — any call_tool to memory-cli verbs beyond
# `index` is forbidden.

RETRO_FORBIDDEN_PATTERNS: frozenset = frozenset({
    "memory-cli learn",
    "learn --file=",
    '"memory_learn"',
    "'memory_learn'",
    'call_tool(..., "memory-cli", "pin ...")',
    'call_tool(..., "memory-cli", "promote ...")',
    'call_tool(..., "memory-cli", "verify ...")',
    'call_tool(..., "memory-cli", "trace ...")',
    'call_tool(..., "memory-cli", "embed ...")',
    'call_tool(..., "memory-cli", "similar ...")',
})


# ─────────── §7.3 — Memory-index severity closure ───────────
# Maps to RRR Delegation Contract T3 tier mapping: HOT→warning, WARM→
# degraded, COLD→block, clean→pass.

MEMORY_INDEX_SEVERITY: frozenset = frozenset({
    "pass",
    "warning",
    "degraded",
    "block",
})


# ─────────── §5.2 — RETRO.md (semantic) H2 sections ───────────
# Recommended sections for retro_writer agent's proposal. retro_writer MAY
# extend; rrr MUST NOT propose any.

RETRO_MD_SECTIONS: tuple = (
    "What worked",
    "What failed",
    "Lessons",
    "Followups",
)


# ─────────── §3.3 — Mechanical-vs-semantic classifier ───────────


def mechanical_vs_semantic(field_name: str) -> str:
    """Classify a field name as 'mechanical' or 'semantic' per spec §3.3.

    A field is mechanical iff it appears in RRR_OUTPUT_FIELDS (i.e. derivable
    deterministically from session artifacts by a stateless function). Any
    other field name is semantic by definition.

    This classifier is the load-bearing invariant for the Article IX
    boundary: rrr MUST produce mechanical fields only; retro_writer MAY
    produce semantic fields only.

    Returns one of: "mechanical" | "semantic".
    """
    if field_name in RRR_OUTPUT_FIELDS:
        return "mechanical"
    return "semantic"


# ─────────── §4 — RetroEnvelope dataclass (frontmatter shape) ───────────


@dataclass
class RetroEnvelope:
    """Authoritative Python mirror of retro_envelope.md frontmatter shape per spec §4.

    Produced by rrr.py (commit 1cf9122). YAML frontmatter + Markdown body.
    The dataclass mirrors the frontmatter; the body is rrr-rendered prose
    summarising mechanical results (no semantic interpretation).
    """

    schema_version: str                        # const RETRO_ENVELOPE_SCHEMA_VERSION
    session_id: str
    slug: str
    ts_started: str                            # RFC3339 UTC
    ts_closed: str                             # RFC3339 UTC
    duration_seconds: int
    tier: str                                  # HOT | WARM | COLD
    graph_state_final: str                     # one of CANONICAL_STATES
    decided_by: str = "kernel"                 # const "kernel" — Article XIII
    acceptance_results: List[Dict[str, Any]] = field(default_factory=list)
    forbidden_diff_status: str = ""            # clean | violations
    baseline_untracked: Optional[Dict[str, Any]] = None
    audit_chain_status: Optional[Dict[str, Any]] = None
    transition_count: int = 0
    gogogo_verdicts: Optional[Dict[str, int]] = None  # {total_steps, pass, fail, ...}
    memory_index_result: Optional[Dict[str, Any]] = None
    memory_index_severity: str = "pass"        # one of MEMORY_INDEX_SEVERITY
    indexed_retros: List[Dict[str, Any]] = field(default_factory=list)
    artifact_paths: List[Dict[str, str]] = field(default_factory=list)


# ─────────── §6.2 — RrrCompletedPayload dataclass ───────────


@dataclass
class RrrCompletedPayload:
    """Payload of the `rrr.completed` audit event per spec §6.2.

    13-field row per Audit Event Spec §2; this dataclass mirrors the
    payload_json content (the per-event metadata that rrr-completion writes).
    """

    session_id: str
    ts: str                                    # RFC3339 UTC
    tier: str
    graph_state_final: str
    decided_by: str = "kernel"
    retro_envelope_path: str = ""
    retro_envelope_sha256: str = ""
    retro_md_path: Optional[str] = None
    retro_md_sha256: Optional[str] = None
    indexed_retro_path: str = ""
    indexed_retro_sha256: str = ""
    indexed_chunks: int = 0
    memory_index: Optional[Dict[str, Any]] = None  # verbatim envelope from memory-cli index
    memory_index_severity: str = "pass"        # one of MEMORY_INDEX_SEVERITY
    acceptance_summary: Optional[Dict[str, int]] = None
    forbidden_diff_status: str = ""
    audit_chain_anchor: Optional[Dict[str, Any]] = None


__all__ = [
    "RETRO_ENVELOPE_SCHEMA_VERSION",
    "RRR_OUTPUT_FIELDS",
    "RETRO_FORBIDDEN_PATTERNS",
    "MEMORY_INDEX_SEVERITY",
    "RETRO_MD_SECTIONS",
    "RetroEnvelope",
    "RrrCompletedPayload",
    "mechanical_vs_semantic",
]
