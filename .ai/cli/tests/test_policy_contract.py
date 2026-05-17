"""Conformance tests for the Policy organ contract (Article IV + XXVIII).

Spec: docs/specs/TRINITY_POLICY_ENGINE_SPEC_V1.md §2 (verdict set + precedence)
       + §2.4 (closed reason codes — 9)
       + §4.1 (QueryEnvelope) + §4.2 (VerdictEnvelope)

Tier-0/1 deterministic. Asserts: VERDICT_SET closure (4), REASON_CODES
closure (9), precedence rule (deny > NEEDS_HUMAN > conditional > allow),
dataclass surfaces, helper semantics.
"""
from __future__ import annotations

import dataclasses

import pytest

from cli.core.policy_contract import (
    ACTION_KINDS,
    ALLOWED_AUTHORITY_CLASSES,
    PolicyQueryEnvelope,
    PolicyVerdictEnvelope,
    REASON_CODES,
    TARGET_TYPES,
    VERDICT_PRECEDENCE,
    VERDICT_SET,
    resolve_precedence,
)


# ─────────── §2.1 — VERDICT_SET closure ───────────


def test_verdict_set_is_frozenset() -> None:
    assert isinstance(VERDICT_SET, frozenset)


def test_verdict_set_exactly_four_canonical_values() -> None:
    expected = {"allow", "deny", "conditional", "NEEDS_HUMAN"}
    assert VERDICT_SET == expected


# ─────────── §2.2 — Precedence rule ───────────


def test_verdict_precedence_is_tuple() -> None:
    assert isinstance(VERDICT_PRECEDENCE, tuple)


def test_verdict_precedence_covers_all_verdicts() -> None:
    assert set(VERDICT_PRECEDENCE) == VERDICT_SET


def test_verdict_precedence_ordered_deny_wins() -> None:
    assert VERDICT_PRECEDENCE == ("deny", "NEEDS_HUMAN", "conditional", "allow")


# ─────────── §2.4 — REASON_CODES closure (9 codes) ───────────


def test_reason_codes_is_frozenset() -> None:
    assert isinstance(REASON_CODES, frozenset)


def test_reason_codes_exactly_nine() -> None:
    assert len(REASON_CODES) == 9


def test_reason_codes_canonical_set() -> None:
    """All 9 canonical codes from spec §2.4 must be present, NO extras."""
    expected = {
        "unknown_authority",
        "forbidden_path",
        "secret_pattern_detected",
        "human_gate_required",
        "illegal_actor",
        "illegal_target",
        "schema_invalid",
        "quota_exceeded",
        "amendment_required",
    }
    assert REASON_CODES == expected


# ─────────── §4.1 — closed authority / action / target enumerations ───────────


def test_allowed_authority_classes_includes_five_canonical_classes() -> None:
    assert ALLOWED_AUTHORITY_CLASSES == {"ai", "human", "kernel", "tool", "transport"}


def test_action_kinds_includes_canonical_set() -> None:
    needed = {
        "transition", "tool_invoke", "fs_read", "fs_write", "fs_delete",
        "net_outbound", "proc_exec", "policy_read", "policy_write",
        "ddd_propose", "ddd_decide",
    }
    assert ACTION_KINDS == needed


def test_target_types_includes_canonical_set() -> None:
    needed = {
        "path", "host", "binary", "transition", "tool_name",
        "audit_event", "policy_file", "none",
    }
    assert TARGET_TYPES == needed


# ─────────── §4.1 + §4.2 — envelope dataclasses ───────────


def test_query_envelope_required_fields() -> None:
    fields = {f.name for f in dataclasses.fields(PolicyQueryEnvelope)}
    required = {"schema_version", "query_id", "actor", "action", "target", "context"}
    assert required.issubset(fields)


def test_verdict_envelope_required_fields() -> None:
    fields = {f.name for f in dataclasses.fields(PolicyVerdictEnvelope)}
    required = {
        "schema_version", "query_id", "verdict", "reason",
        "evidence_ref", "emitted_at", "engine_version",
    }
    assert required.issubset(fields)


def test_query_envelope_round_trip_through_asdict() -> None:
    env = PolicyQueryEnvelope(
        schema_version="1",
        query_id="qry_01J0000000000000",
        actor={"id": "executor_helper", "authority_class": "ai"},
        action={"kind": "fs_write", "detail": {"path": "DO/dev/foo.py", "bytes": 0}},
        target={"type": "path", "value": "DO/dev/foo.py"},
        context={
            "session_id": "0001_test",
            "ritual_phase": "EXECUTE",
            "declared_authority": "executor",
            "evidence_refs": [],
        },
    )
    d = dataclasses.asdict(env)
    assert d["actor"]["authority_class"] in ALLOWED_AUTHORITY_CLASSES
    assert d["action"]["kind"] in ACTION_KINDS
    assert d["target"]["type"] in TARGET_TYPES


def test_verdict_envelope_round_trip_through_asdict() -> None:
    env = PolicyVerdictEnvelope(
        schema_version="1",
        query_id="qry_01J0000000000000",
        verdict="deny",
        reason="forbidden_path",
        evidence_ref={
            "rule_id": "rule_pol_001",
            "rule_file": ".ai/policies/trinity_policy.yaml",
            "rule_anchor": "L42-L48",
        },
        emitted_at="2026-05-15T00:00:00Z",
    )
    d = dataclasses.asdict(env)
    assert d["verdict"] in VERDICT_SET
    assert d["reason"] in REASON_CODES
    assert d["engine_version"] == "1.0"


# ─────────── resolve_precedence helper ───────────


def test_resolve_precedence_deny_wins() -> None:
    assert resolve_precedence(["allow", "deny"]) == "deny"
    assert resolve_precedence(["allow", "conditional", "deny"]) == "deny"
    assert resolve_precedence(["NEEDS_HUMAN", "deny"]) == "deny"


def test_resolve_precedence_needs_human_beats_conditional_and_allow() -> None:
    assert resolve_precedence(["allow", "NEEDS_HUMAN"]) == "NEEDS_HUMAN"
    assert resolve_precedence(["conditional", "NEEDS_HUMAN"]) == "NEEDS_HUMAN"


def test_resolve_precedence_conditional_beats_allow() -> None:
    assert resolve_precedence(["conditional", "allow"]) == "conditional"


def test_resolve_precedence_allow_only() -> None:
    assert resolve_precedence(["allow"]) == "allow"
    assert resolve_precedence(["allow", "allow"]) == "allow"


def test_resolve_precedence_empty_raises() -> None:
    with pytest.raises(ValueError):
        resolve_precedence([])


def test_resolve_precedence_unknown_verdicts_raise() -> None:
    """Unknown strings outside VERDICT_SET MUST NOT silently degrade to allow."""
    with pytest.raises(ValueError):
        resolve_precedence(["unknown_verdict_x", "another_bogus"])


def test_resolve_precedence_ignores_unknown_but_keeps_known() -> None:
    # If at least one known verdict is present alongside unknowns, the known
    # one is returned (defense in depth — partial drift surfaces but the
    # known signal still wins).
    assert resolve_precedence(["unknown_bogus", "deny"]) == "deny"


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_is_idempotent() -> None:
    """Re-importing must not raise — module is import-only declarative."""
    import importlib

    import cli.core.policy_contract as pc

    importlib.reload(pc)
    assert hasattr(pc, "VERDICT_SET")
    assert hasattr(pc, "resolve_precedence")
