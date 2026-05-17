"""Conformance tests for the Retro + RRR Terminal Gate contract (Article IV + IX + XXVIII).

Spec: docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md §3.1 + §3.2 + §5.2 + §7.3

Tier-0/1 deterministic. Asserts:
  - RETRO_ENVELOPE_SCHEMA_VERSION pin
  - RRR_OUTPUT_FIELDS spec parity (13 mechanical fields verbatim from §3.1)
  - RETRO_FORBIDDEN_PATTERNS spec parity (substring lint from §3.2)
  - MEMORY_INDEX_SEVERITY closure (4 levels per §7.3)
  - RETRO_MD_SECTIONS spec parity (4 H2 sections from §5.2)
  - mechanical_vs_semantic classifier correctness
  - dataclass surfaces (RetroEnvelope + RrrCompletedPayload)
"""
from __future__ import annotations

import dataclasses

from cli.core.retro_rrr_contract import (
    MEMORY_INDEX_SEVERITY,
    RETRO_ENVELOPE_SCHEMA_VERSION,
    RETRO_FORBIDDEN_PATTERNS,
    RETRO_MD_SECTIONS,
    RRR_OUTPUT_FIELDS,
    RetroEnvelope,
    RrrCompletedPayload,
    mechanical_vs_semantic,
)


# ─────────── schema version pin ───────────


def test_retro_envelope_schema_version_is_pinned() -> None:
    assert RETRO_ENVELOPE_SCHEMA_VERSION == "trinity.retro_envelope.v1"


# ─────────── §3.1 — 13 mechanical fields parity ───────────


def test_rrr_output_fields_is_frozenset() -> None:
    assert isinstance(RRR_OUTPUT_FIELDS, frozenset)


def test_rrr_output_fields_exactly_thirteen() -> None:
    assert len(RRR_OUTPUT_FIELDS) == 13


def test_rrr_output_fields_canonical_set() -> None:
    """Verbatim from spec §3.1 lines 213-225."""
    expected = {
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
    }
    assert RRR_OUTPUT_FIELDS == expected


# ─────────── §3.2 — forbidden substring patterns ───────────


def test_retro_forbidden_patterns_is_non_empty_frozenset() -> None:
    assert isinstance(RETRO_FORBIDDEN_PATTERNS, frozenset)
    assert len(RETRO_FORBIDDEN_PATTERNS) >= 8


def test_retro_forbidden_patterns_includes_memory_cli_learn() -> None:
    """Per spec §3.2 + RRR Delegation Contract T1."""
    assert "memory-cli learn" in RETRO_FORBIDDEN_PATTERNS
    assert "learn --file=" in RETRO_FORBIDDEN_PATTERNS


def test_retro_forbidden_patterns_includes_pin_promote_verbs() -> None:
    """Article IX + XX: rrr MUST NOT call memory-cli pin/promote/verify."""
    assert 'call_tool(..., "memory-cli", "pin ...")' in RETRO_FORBIDDEN_PATTERNS
    assert 'call_tool(..., "memory-cli", "promote ...")' in RETRO_FORBIDDEN_PATTERNS


# ─────────── §7.3 — memory-index severity closure ───────────


def test_memory_index_severity_canonical_set() -> None:
    """Per spec §7.3 + RRR Delegation Contract T3 tier mapping."""
    assert MEMORY_INDEX_SEVERITY == frozenset({"pass", "warning", "degraded", "block"})


# ─────────── §5.2 — RETRO.md semantic H2 sections ───────────


def test_retro_md_sections_is_tuple_of_four() -> None:
    assert RETRO_MD_SECTIONS == ("What worked", "What failed", "Lessons", "Followups")


# ─────────── §3.3 — mechanical_vs_semantic classifier ───────────


def test_classifier_recognises_all_mechanical_fields() -> None:
    for f in RRR_OUTPUT_FIELDS:
        assert mechanical_vs_semantic(f) == "mechanical", f


def test_classifier_marks_unknown_field_as_semantic() -> None:
    """Article IX boundary: any field not in spec §3.1 is semantic and rrr
    MUST NOT write it."""
    for semantic in ("lessons_learned", "root_cause", "doctrine_candidate",
                     "what_worked", "future_recommendations", "embedding_vector"):
        assert mechanical_vs_semantic(semantic) == "semantic", semantic


def test_classifier_returns_only_two_labels() -> None:
    """Sanity: classifier vocabulary is closed at 2 labels."""
    for name in (
        "session_id", "tier", "audit_chain_status",          # mechanical
        "lessons_learned", "doctrine", "random_field_xyz",   # semantic
    ):
        assert mechanical_vs_semantic(name) in {"mechanical", "semantic"}


# ─────────── dataclass surfaces ───────────


def test_retro_envelope_required_fields() -> None:
    fields = {f.name for f in dataclasses.fields(RetroEnvelope)}
    required = {
        "schema_version", "session_id", "slug", "ts_started", "ts_closed",
        "duration_seconds", "tier", "graph_state_final", "decided_by",
        "acceptance_results", "forbidden_diff_status", "baseline_untracked",
        "audit_chain_status", "transition_count", "gogogo_verdicts",
        "memory_index_result", "memory_index_severity", "indexed_retros",
        "artifact_paths",
    }
    assert required.issubset(fields)


def test_retro_envelope_default_decided_by_kernel() -> None:
    env = RetroEnvelope(
        schema_version=RETRO_ENVELOPE_SCHEMA_VERSION,
        session_id="0001_test",
        slug="t",
        ts_started="2026-05-15T00:00:00Z",
        ts_closed="2026-05-15T00:01:00Z",
        duration_seconds=60,
        tier="WARM",
        graph_state_final="DONE",
    )
    assert env.decided_by == "kernel"


def test_retro_envelope_default_severity_pass() -> None:
    env = RetroEnvelope(
        schema_version=RETRO_ENVELOPE_SCHEMA_VERSION,
        session_id="x", slug="x",
        ts_started="t", ts_closed="t",
        duration_seconds=0, tier="HOT", graph_state_final="DONE",
    )
    assert env.memory_index_severity == "pass"


def test_rrr_completed_payload_fields() -> None:
    fields = {f.name for f in dataclasses.fields(RrrCompletedPayload)}
    required = {
        "session_id", "ts", "tier", "graph_state_final", "decided_by",
        "retro_envelope_path", "retro_envelope_sha256",
        "retro_md_path", "retro_md_sha256",
        "indexed_retro_path", "indexed_retro_sha256", "indexed_chunks",
        "memory_index", "memory_index_severity",
        "acceptance_summary", "forbidden_diff_status", "audit_chain_anchor",
    }
    assert required.issubset(fields)


def test_rrr_completed_payload_default_decided_by_kernel() -> None:
    p = RrrCompletedPayload(
        session_id="x", ts="t", tier="WARM", graph_state_final="DONE",
    )
    assert p.decided_by == "kernel"


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.retro_rrr_contract as rc

    importlib.reload(rc)
    assert hasattr(rc, "mechanical_vs_semantic")
