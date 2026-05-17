"""Presentation Protocol organ — Article IV + Article XXIII declarative contract.

Spec anchors:
- docs/specs/TRINITY_PRESENTATION_PROTOCOL_V1.md (Phase 13, DRAFT v1.0 — 818 lines)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §16 (Presentation / Cognitive Compression)
- docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md §E (Cognitive Presentation Protocol)

This module is **declarative only** (Article XX Passive Core). It encodes the
Phase 13 spec §3-§8 surface as closed frozensets + Python dataclasses so
future evolution (presentation_synthesizer v1.0.2 emission upgrade, kernel
presentation verifier wiring) can bind against machine-checkable contracts.

Article IV anchor: presentation = VIEW; synthesizer drafts the VIEW; the
truth layer (raw artifacts) is the SOURCE. The two stay separated — the
synthesizer MUST NOT vote in its own convergence panel (FAIL_SYNTHESIZER_VOTED).

Article XXIII anchor: dissent MUST be preserved, not erased. The
RULE-D1..5 dissent-preservation rule in spec §7 is encoded here via the
FAIL_TOKENS frozenset (which closes the failure vocabulary).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────── Phase 13 §5 — Protocol versions ───────────

PROTOCOL_VERSIONS: frozenset = frozenset({"v1.0.1", "v1.0.2"})


# ─────────── §5.1 — v1.0.1 canonical presentation_synthesis fields (9) ───────────

PRESENTATION_SYNTHESIS_FIELDS: frozenset = frozenset({
    "cognitive_protocol_version",
    "summary",
    "convergence",
    "dissent_flags",
    "founder_decisions_required",
    "raw_artifacts_available",
    "panel_diversity",
    "synthesizer_not_in_opinion_panel",
    "capture_refs",
})


# ─────────── §5.3.1 — v1.0.2 added fields (Phase 11+13 cross-amendment, 2026-05-15) ───────────

V1_0_2_FIELDS: frozenset = frozenset({
    "compression_ratio",
    "transport_capability",
    "dissent_preserved",     # alias of dissent_flags
    "raw_artifact_links",    # alias of capture_refs
})


# ─────────── §5.3.1 — v1.0.2 alias mapping (canonical wins on byte-mismatch) ───────────

V1_0_2_ALIASES: Dict[str, str] = {
    "dissent_preserved": "dissent_flags",
    "raw_artifact_links": "capture_refs",
}


# ─────────── §8.4 + §7.2 — Closed FAIL_* token vocabulary (15 tokens) ───────────

FAIL_TOKENS: frozenset = frozenset({
    "FAIL_SCHEMA_VERSION_MISMATCH",        # CHK-1
    "FAIL_PACKET_NOT_FOUND",               # CHK-2
    "FAIL_PACKET_EXPIRED",                 # CHK-2
    "FAIL_BROKEN_RAW_LINK",                # CHK-3
    "FAIL_DISSENT_ERASED",                 # CHK-4, CHK-13
    "FAIL_NO_COMPRESSION",                 # CHK-5 upper bound
    "FAIL_SUMMARY_TOO_LONG",               # CHK-6 upper
    "FAIL_SUMMARY_TOO_SHORT",              # CHK-6 lower
    "FAIL_DISSENT_LANGUAGE_MISMATCH",      # CHK-7 (§7.2 grep)
    "FAIL_SYNTHESIZER_IDENTITY",           # CHK-8
    "FAIL_SYNTHESIZER_VOTED",              # CHK-9
    "FAIL_PANEL_DIVERSITY_INSUFFICIENT",   # CHK-10
    "FAIL_TRANSPORT_INSUFFICIENT",         # CHK-11
    "FAIL_FORBIDDEN_FIELD_PRESENT",        # CHK-12
    "FAIL_NO_DECISION_QUESTION",           # founder_decisions_required parity
})


# ─────────── §8 — Presentation verifier checks (CHK-1..13) ───────────

PRESENTATION_CHECKS: tuple = (
    "CHK-1",   # schema_version pin
    "CHK-2",   # packet existence + expiry
    "CHK-3",   # raw artifact link integrity
    "CHK-4",   # dissent presence (cardinality)
    "CHK-5",   # compression-ratio upper bound (no trivial passthrough)
    "CHK-6",   # summary length bounds
    "CHK-7",   # dissent language coherence (§7.2)
    "CHK-8",   # synthesizer identity in packet metadata
    "CHK-9",   # synthesizer not in opinion panel
    "CHK-10",  # panel diversity floor (distinct_layers >= 2 on COLD)
    "CHK-11",  # transport capability declared
    "CHK-12",  # no forbidden field present (§5.3 closed set)
    "CHK-13",  # dissent preserved verbatim across normalisation
)


# ─────────── §6 — Ratification decision verdicts ───────────

RATIFICATION_VERDICTS: frozenset = frozenset({
    "ratify",
    "reject",
    "request_amendment",
})


# ─────────── §4 — RatificationPacket dataclass ───────────


@dataclass
class RatificationPacket:
    """Authoritative Python mirror of `ratification_packet.json` per Phase 13 §4.

    The packet is the INPUT to the presentation synthesizer — it carries the
    raw artifacts + the convergence/dissent evidence that the synthesizer
    will compress into a presentation_synthesis.
    """

    id: str                                          # packet identifier
    created_ts: str                                  # RFC3339 UTC
    session: str
    proposing_role: str                              # one of {planner, executor, verifier}
    requested_action: str                            # one of {promote, deploy, abort, amend}
    raw_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    dissent: List[Dict[str, Any]] = field(default_factory=list)
    convergence: List[str] = field(default_factory=list)
    expires_ts: str = ""


# ─────────── §5 — PresentationSynthesis dataclass ───────────


@dataclass
class PresentationSynthesis:
    """Authoritative Python mirror of `presentation_synthesis.json` per Phase 13 §5.

    The synthesizer output. v1.0.1 carries 9 canonical fields; v1.0.2 adds 4
    fields (2 of which are aliases — see V1_0_2_ALIASES).
    """

    cognitive_protocol_version: str                  # one of PROTOCOL_VERSIONS
    summary: str
    convergence: List[str] = field(default_factory=list)
    dissent_flags: List[str] = field(default_factory=list)
    founder_decisions_required: List[str] = field(default_factory=list)
    raw_artifacts_available: bool = False
    panel_diversity: Dict[str, Any] = field(default_factory=dict)
    synthesizer_not_in_opinion_panel: bool = True
    capture_refs: List[str] = field(default_factory=list)
    # v1.0.2 additions (optional)
    compression_ratio: Optional[float] = None
    transport_capability: Optional[str] = None
    dissent_preserved: Optional[List[str]] = None    # alias of dissent_flags
    raw_artifact_links: Optional[List[str]] = None   # alias of capture_refs


# ─────────── §6 — RatificationDecision dataclass ───────────


@dataclass
class RatificationDecision:
    """Authoritative Python mirror of `ratification_decision.json` per Phase 13 §6.

    The operator's verdict on a ratification packet. Article XIII: decided_by
    MUST be "human"; reason MUST be non-empty for non-ratify verdicts.
    """

    packet_id: str
    decided_by: str                                  # const "human" per Article XIII
    decided_at: str                                  # RFC3339 UTC
    verdict: str                                     # one of RATIFICATION_VERDICTS
    reason: str = ""
    dissent_acknowledged: bool = False
    signature: Optional[str] = None


# ─────────── helpers ───────────


def canonicalise_v1_0_2_field(field_name: str) -> str:
    """Resolve a v1.0.2 alias to its canonical v1.0.1 name.

    If `field_name` is not an alias, return it unchanged. Pure function;
    Article XX passive.
    """
    return V1_0_2_ALIASES.get(field_name, field_name)


__all__ = [
    "PROTOCOL_VERSIONS",
    "PRESENTATION_SYNTHESIS_FIELDS",
    "V1_0_2_FIELDS",
    "V1_0_2_ALIASES",
    "FAIL_TOKENS",
    "PRESENTATION_CHECKS",
    "RATIFICATION_VERDICTS",
    "RatificationPacket",
    "PresentationSynthesis",
    "RatificationDecision",
    "canonicalise_v1_0_2_field",
]
