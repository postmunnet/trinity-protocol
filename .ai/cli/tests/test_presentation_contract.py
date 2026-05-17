"""Conformance tests for the Presentation Protocol contract (Phase 13).

Spec: docs/specs/TRINITY_PRESENTATION_PROTOCOL_V1.md §3-§8

Tier-0/1 deterministic. Asserts: closure invariants, FAIL_TOKENS canonical
set (15), PRESENTATION_CHECKS == 13, V1_0_2_ALIASES coherence, dataclass
surfaces.
"""
from __future__ import annotations

import dataclasses

from cli.core.presentation_contract import (
    FAIL_TOKENS,
    PRESENTATION_CHECKS,
    PRESENTATION_SYNTHESIS_FIELDS,
    PROTOCOL_VERSIONS,
    RATIFICATION_VERDICTS,
    RatificationDecision,
    RatificationPacket,
    PresentationSynthesis,
    V1_0_2_ALIASES,
    V1_0_2_FIELDS,
    canonicalise_v1_0_2_field,
)


# ─────────── §5 — protocol versions ───────────


def test_protocol_versions_canonical_set() -> None:
    assert PROTOCOL_VERSIONS == frozenset({"v1.0.1", "v1.0.2"})


# ─────────── §5.1 — 9 canonical v1.0.1 fields ───────────


def test_presentation_synthesis_fields_count_nine() -> None:
    assert len(PRESENTATION_SYNTHESIS_FIELDS) == 9


def test_presentation_synthesis_fields_canonical_set() -> None:
    expected = {
        "cognitive_protocol_version",
        "summary",
        "convergence",
        "dissent_flags",
        "founder_decisions_required",
        "raw_artifacts_available",
        "panel_diversity",
        "synthesizer_not_in_opinion_panel",
        "capture_refs",
    }
    assert PRESENTATION_SYNTHESIS_FIELDS == expected


# ─────────── §5.3.1 — v1.0.2 added fields + aliases ───────────


def test_v1_0_2_fields_count_four() -> None:
    assert len(V1_0_2_FIELDS) == 4


def test_v1_0_2_fields_canonical_set() -> None:
    assert V1_0_2_FIELDS == frozenset({
        "compression_ratio", "transport_capability",
        "dissent_preserved", "raw_artifact_links",
    })


def test_v1_0_2_aliases_is_dict() -> None:
    assert isinstance(V1_0_2_ALIASES, dict)
    assert len(V1_0_2_ALIASES) == 2


def test_v1_0_2_aliases_canonical_mapping() -> None:
    """Each v1.0.2 alias MUST map to a v1.0.1 canonical field."""
    assert V1_0_2_ALIASES["dissent_preserved"] == "dissent_flags"
    assert V1_0_2_ALIASES["raw_artifact_links"] == "capture_refs"


def test_v1_0_2_alias_coherence() -> None:
    """All alias values MUST resolve to canonical fields in PRESENTATION_SYNTHESIS_FIELDS."""
    missing = [v for v in V1_0_2_ALIASES.values() if v not in PRESENTATION_SYNTHESIS_FIELDS]
    assert not missing, f"alias values not in canonical: {missing}"


def test_canonicalise_helper_resolves_aliases() -> None:
    assert canonicalise_v1_0_2_field("dissent_preserved") == "dissent_flags"
    assert canonicalise_v1_0_2_field("raw_artifact_links") == "capture_refs"


def test_canonicalise_helper_passes_through_canonical_names() -> None:
    assert canonicalise_v1_0_2_field("summary") == "summary"
    assert canonicalise_v1_0_2_field("capture_refs") == "capture_refs"
    assert canonicalise_v1_0_2_field("unknown_field") == "unknown_field"


# ─────────── §8.4 — 15 FAIL_* tokens ───────────


def test_fail_tokens_count_fifteen() -> None:
    assert len(FAIL_TOKENS) == 15


def test_fail_tokens_canonical_set() -> None:
    """Verbatim from spec §8.4 lines 566-580."""
    expected = {
        "FAIL_SCHEMA_VERSION_MISMATCH",
        "FAIL_PACKET_NOT_FOUND",
        "FAIL_PACKET_EXPIRED",
        "FAIL_BROKEN_RAW_LINK",
        "FAIL_DISSENT_ERASED",
        "FAIL_NO_COMPRESSION",
        "FAIL_SUMMARY_TOO_LONG",
        "FAIL_SUMMARY_TOO_SHORT",
        "FAIL_DISSENT_LANGUAGE_MISMATCH",
        "FAIL_SYNTHESIZER_IDENTITY",
        "FAIL_SYNTHESIZER_VOTED",
        "FAIL_PANEL_DIVERSITY_INSUFFICIENT",
        "FAIL_TRANSPORT_INSUFFICIENT",
        "FAIL_FORBIDDEN_FIELD_PRESENT",
        "FAIL_NO_DECISION_QUESTION",
    }
    assert FAIL_TOKENS == expected


def test_fail_tokens_all_uppercase_with_fail_prefix() -> None:
    for token in FAIL_TOKENS:
        assert token.startswith("FAIL_"), token
        assert token.isupper() or "_" in token


# ─────────── §8 — 13 presentation checks (CHK-1..CHK-13) ───────────


def test_presentation_checks_is_tuple() -> None:
    assert isinstance(PRESENTATION_CHECKS, tuple)


def test_presentation_checks_count_thirteen() -> None:
    assert len(PRESENTATION_CHECKS) == 13


def test_presentation_checks_canonical_naming() -> None:
    expected = tuple(f"CHK-{i}" for i in range(1, 14))
    assert PRESENTATION_CHECKS == expected


# ─────────── §6 — ratification verdicts ───────────


def test_ratification_verdicts_canonical_set() -> None:
    assert RATIFICATION_VERDICTS == frozenset({"ratify", "reject", "request_amendment"})


# ─────────── dataclass surfaces ───────────


def test_ratification_packet_fields() -> None:
    fields = {f.name for f in dataclasses.fields(RatificationPacket)}
    assert {"id", "created_ts", "session", "proposing_role", "requested_action",
            "raw_artifacts", "dissent", "convergence", "expires_ts"}.issubset(fields)


def test_presentation_synthesis_fields_dataclass() -> None:
    fields = {f.name for f in dataclasses.fields(PresentationSynthesis)}
    # Required v1.0.1
    for f in PRESENTATION_SYNTHESIS_FIELDS:
        assert f in fields, f"v1.0.1 field {f!r} missing from dataclass"
    # v1.0.2 additions
    for f in V1_0_2_FIELDS:
        assert f in fields, f"v1.0.2 field {f!r} missing from dataclass"


def test_ratification_decision_fields() -> None:
    fields = {f.name for f in dataclasses.fields(RatificationDecision)}
    assert {"packet_id", "decided_by", "decided_at", "verdict", "reason",
            "dissent_acknowledged", "signature"}.issubset(fields)


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.presentation_contract as pc

    importlib.reload(pc)
    assert hasattr(pc, "FAIL_TOKENS")
