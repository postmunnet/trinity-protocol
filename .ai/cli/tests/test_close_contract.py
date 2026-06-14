"""Conformance tests for the Close / Session Finalizer contract (Phase 15)."""
from __future__ import annotations

import dataclasses

from pathlib import Path

from cli.core.close_contract import (
    AuditChainAnchor,
    CAPTURE_STATUS_ALLOWED,
    CLOSE_AUDIT_EVENTS,
    CLOSE_TIERS,
    CaptureSection,
    EXTERNAL_AUDIT_REQUIRED_TIERS,
    ExternalAudit,
    FINAL_MANIFEST_VERSION,
    FinalManifest,
    get_terminal_states_for_close,
)

# test file: <root>/.ai/cli/tests/<this> -> parents[3] == <root> (trinity_v2)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ─────────── manifest version pin ───────────


def test_final_manifest_version_is_one_dot_zero() -> None:
    assert FINAL_MANIFEST_VERSION == "1.0"


# ─────────── §1 — terminal states ───────────


def test_terminal_states_for_close_canonical_set() -> None:
    # Graph-derived single source of truth (see core/terminal_states.py).
    # FAILED/ABORTED are close-attempt outcomes, not graph terminal states.
    assert get_terminal_states_for_close(_PROJECT_ROOT) == frozenset({"DONE", "DEAD"})


def test_terminal_states_for_close_count_two() -> None:
    assert len(get_terminal_states_for_close(_PROJECT_ROOT)) == 2


# ─────────── §4 — tier routing ───────────


def test_close_tiers_canonical_set() -> None:
    assert CLOSE_TIERS == frozenset({"HOT", "WARM", "COLD"})


def test_external_audit_required_only_on_cold() -> None:
    """Per Phase 15 §3 + §4: external audit fires only on COLD."""
    assert EXTERNAL_AUDIT_REQUIRED_TIERS == frozenset({"COLD"})


def test_external_audit_required_is_subset_of_close_tiers() -> None:
    assert EXTERNAL_AUDIT_REQUIRED_TIERS.issubset(CLOSE_TIERS)


# ─────────── §2.2 — capture status check ───────────


def test_capture_status_allowed_canonical_set() -> None:
    """Per §2.2: capture rows MUST be in one of these statuses at close."""
    assert CAPTURE_STATUS_ALLOWED == frozenset({"COMPLETED", "RECONCILED", "ARCHIVED"})


def test_capture_status_allowed_count_three() -> None:
    assert len(CAPTURE_STATUS_ALLOWED) == 3


# ─────────── §5 — audit events ───────────


def test_close_audit_events_count_nine() -> None:
    assert len(CLOSE_AUDIT_EVENTS) == 9


def test_close_audit_events_canonical_set() -> None:
    expected = {
        "close.invoked",
        "close.manifest_built",
        "close.forced",
        "close.blocked",
        "close.external_audit_emitted",
        "session.closed",
        "close.completed",
        "close.failed",
        "close.reconciled",
    }
    assert CLOSE_AUDIT_EVENTS == expected


# ─────────── dataclass surfaces ───────────


def test_audit_chain_anchor_fields() -> None:
    fields = {f.name for f in dataclasses.fields(AuditChainAnchor)}
    assert {"session_id", "session_chain_head", "last_seq", "audit_export_ref"}.issubset(fields)


def test_capture_section_fields() -> None:
    fields = {f.name for f in dataclasses.fields(CaptureSection)}
    assert {"capture_store_sha256", "blobs_root_sha256", "refs_root_sha256",
            "capture_ids", "capture_manifest_sha256"}.issubset(fields)


def test_final_manifest_fields() -> None:
    fields = {f.name for f in dataclasses.fields(FinalManifest)}
    required = {"session_id", "closed_at", "tier", "graph_state_final",
                "artifacts", "captures", "audit", "manifest_sha256", "manifest_version"}
    assert required.issubset(fields)


def test_final_manifest_default_version_matches_constant() -> None:
    fm = FinalManifest(
        session_id="x", closed_at="t", tier="WARM", graph_state_final="DONE",
    )
    assert fm.manifest_version == FINAL_MANIFEST_VERSION


def test_external_audit_fields() -> None:
    fields = {f.name for f in dataclasses.fields(ExternalAudit)}
    required = {"session_id", "tier", "final_state", "artifacts", "captures",
                "decision", "external_systems_touched", "audit_chain_anchor", "emitted_at"}
    assert required.issubset(fields)


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.close_contract as cc

    importlib.reload(cc)
    assert hasattr(cc, "FINAL_MANIFEST_VERSION")
