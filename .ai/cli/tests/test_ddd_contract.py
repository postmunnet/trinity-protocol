"""Conformance tests for the DDD organ contract (Article XIII + IV + XXVIII).

Spec: docs/specs/TRINITY_DDD_HUMAN_GATE_SPEC_V1.md §3-§7
       .ai/schemas/{decision_packet,approval,rejection,hold}.schema.json

Tier-0/1 deterministic. Asserts: closure invariants, dataclass surfaces,
4-schema round-trips, schema rejection of malformed input.
"""
from __future__ import annotations

import dataclasses

import jsonschema
import pytest

from cli.core.ddd_contract import (
    APPROVAL_ACTIONS,
    DDD_AUDIT_EVENTS,
    DECIDED_BY_VALUES,
    PROPOSING_ROLES,
    REQUESTED_ACTIONS,
    VERDICT_ACTIONS,
    Approval,
    DecisionPacket,
    Hold,
    Rejection,
    validate_approval,
    validate_decision_packet,
    validate_hold,
    validate_rejection,
)


# ─────────── closure invariants ───────────


def test_approval_actions_is_frozenset() -> None:
    assert APPROVAL_ACTIONS == frozenset({"promote", "deploy", "amend_approve"})


def test_verdict_actions_is_frozenset() -> None:
    assert VERDICT_ACTIONS == frozenset({"approve", "reject", "hold"})


def test_proposing_roles_is_frozenset() -> None:
    assert PROPOSING_ROLES == frozenset({"planner", "executor", "verifier"})


def test_requested_actions_is_frozenset() -> None:
    assert REQUESTED_ACTIONS == frozenset({"promote", "deploy", "abort", "amend"})


def test_decided_by_values_is_frozenset() -> None:
    assert DECIDED_BY_VALUES == frozenset({"human", "kernel"})


def test_ddd_audit_events_count_five() -> None:
    assert DDD_AUDIT_EVENTS == frozenset({
        "ddd.packet_emitted", "ddd.approved", "ddd.rejected",
        "ddd.held", "ddd.timeout",
    })


# ─────────── dataclass surfaces ───────────


def test_decision_packet_fields() -> None:
    fields = {f.name for f in dataclasses.fields(DecisionPacket)}
    required = {"id", "session", "created_ts", "proposing_role", "requested_action",
                "verifier_reports", "presentation", "expires_ts"}
    assert required.issubset(fields)


def test_approval_fields() -> None:
    fields = {f.name for f in dataclasses.fields(Approval)}
    assert {"packet_id", "decided_by", "decided_at", "action", "notes", "signature"}.issubset(fields)


def test_rejection_fields() -> None:
    fields = {f.name for f in dataclasses.fields(Rejection)}
    assert {"packet_id", "decided_by", "decided_at", "action", "reason", "signature"}.issubset(fields)


def test_hold_fields() -> None:
    fields = {f.name for f in dataclasses.fields(Hold)}
    assert {"packet_id", "decided_by", "decided_at", "action", "until", "notes", "signature"}.issubset(fields)


# ─────────── known-good fixtures (round-trip) ───────────


GOOD_PACKET = {
    "id": "pkt_test_001",
    "session": "0001_test",
    "created_ts": "2026-05-15T00:00:00Z",
    "proposing_role": "verifier",
    "requested_action": "promote",
    "verifier_reports": [{"path": "DO/dev/report.json", "hash": "a" * 64}],
    "presentation": {
        "cognitive_protocol_version": "v1.0.1",
        "summary": "Smoke test packet",
        "convergence": [],
        "dissent_flags": [],
        "founder_decisions_required": [],
        "raw_artifacts_available": True,
        "panel_diversity": {"roles": ["verifier"], "distinct_models": 0, "distinct_layers": 1},
        "synthesizer_not_in_opinion_panel": True,
        "capture_refs": [],
    },
    "expires_ts": "2026-05-15T01:00:00Z",
}


def test_validate_decision_packet_accepts_good_fixture() -> None:
    validate_decision_packet(GOOD_PACKET)


def test_validate_approval_accepts_good_fixture() -> None:
    validate_approval({
        "packet_id": "pkt_test_001",
        "decided_by": "human",
        "decided_at": "2026-05-15T00:30:00Z",
        "action": "promote",
    })


def test_validate_rejection_accepts_good_fixture() -> None:
    validate_rejection({
        "packet_id": "pkt_test_001",
        "decided_by": "human",
        "decided_at": "2026-05-15T00:30:00Z",
        "action": "reject",
        "reason": "Tests fail",
    })


def test_validate_hold_accepts_good_fixture() -> None:
    validate_hold({
        "packet_id": "pkt_test_001",
        "decided_by": "human",
        "decided_at": "2026-05-15T00:30:00Z",
        "action": "hold",
        "until": "2026-05-16T00:00:00Z",
    })


# ─────────── schema rejection tests ───────────


def test_packet_rejects_missing_required() -> None:
    bad = dict(GOOD_PACKET)
    del bad["presentation"]
    with pytest.raises(jsonschema.ValidationError):
        validate_decision_packet(bad)


def test_packet_rejects_unknown_proposing_role() -> None:
    bad = dict(GOOD_PACKET)
    bad["proposing_role"] = "operator"
    with pytest.raises(jsonschema.ValidationError):
        validate_decision_packet(bad)


def test_packet_rejects_unknown_requested_action() -> None:
    bad = dict(GOOD_PACKET)
    bad["requested_action"] = "rollback"
    with pytest.raises(jsonschema.ValidationError):
        validate_decision_packet(bad)


def test_approval_rejects_non_human_decided_by() -> None:
    with pytest.raises(jsonschema.ValidationError):
        validate_approval({
            "packet_id": "pkt", "decided_by": "kernel",
            "decided_at": "2026-05-15T00:00:00Z", "action": "promote",
        })


def test_approval_rejects_unknown_action() -> None:
    with pytest.raises(jsonschema.ValidationError):
        validate_approval({
            "packet_id": "pkt", "decided_by": "human",
            "decided_at": "2026-05-15T00:00:00Z", "action": "yolo",
        })


def test_rejection_requires_reason() -> None:
    with pytest.raises(jsonschema.ValidationError):
        validate_rejection({
            "packet_id": "pkt", "decided_by": "human",
            "decided_at": "2026-05-15T00:00:00Z", "action": "reject",
        })


def test_rejection_rejects_empty_reason() -> None:
    with pytest.raises(jsonschema.ValidationError):
        validate_rejection({
            "packet_id": "pkt", "decided_by": "human",
            "decided_at": "2026-05-15T00:00:00Z", "action": "reject",
            "reason": "",
        })


def test_hold_requires_until() -> None:
    with pytest.raises(jsonschema.ValidationError):
        validate_hold({
            "packet_id": "pkt", "decided_by": "human",
            "decided_at": "2026-05-15T00:00:00Z", "action": "hold",
        })


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.ddd_contract as dc

    importlib.reload(dc)
    assert hasattr(dc, "validate_decision_packet")
