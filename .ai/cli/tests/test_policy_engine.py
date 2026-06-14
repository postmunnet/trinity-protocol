"""Phase 5 PolicyEngine runtime unit tests.

Covers the POC predicate ladder:
  - schema_version drift → deny(schema_invalid)
  - unknown authority_class → deny(unknown_authority) [Article XVI]
  - known authority + advisory pass → allow("")
  - envelope factory shape
  - load_policy_doc fallbacks (missing file, malformed yaml, non-mapping)
  - envelope_to_audit_dict round-trip

Integration with the contract types lives in `policy_contract` — these
tests treat that module as the read-only source of `ALLOWED_AUTHORITY_CLASSES`
+ envelope dataclasses (Article IV — engine and contract are siblings).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.policy_contract import (
    ALLOWED_AUTHORITY_CLASSES,
    PolicyQueryEnvelope,
    VERDICT_SET,
)
from cli.core.policy_engine import (
    POLICY_FILE_PATH,
    build_query_envelope,
    envelope_to_audit_dict,
    load_policy_doc,
    query,
)


# ─── factory ────────────────────────────────────────────────────────


def test_build_query_envelope_minimal_fields() -> None:
    e = build_query_envelope(
        actor_id="kernel",
        authority_class="kernel",
        action_kind="transition",
    )
    assert isinstance(e, PolicyQueryEnvelope)
    assert e.schema_version == "1"
    assert e.actor == {"id": "kernel", "authority_class": "kernel"}
    assert e.action["kind"] == "transition"
    assert e.target == {"type": None, "value": None}
    assert e.context["session_id"] == ""
    # query_id is non-empty + roughly ULID-shaped (26 chars)
    assert isinstance(e.query_id, str)
    assert len(e.query_id) == 26


def test_build_query_envelope_with_target_and_evidence() -> None:
    e = build_query_envelope(
        actor_id="executor",
        authority_class="ai",
        action_kind="tool_invoke",
        action_detail={"tool_name": "alpha"},
        target_type="tool",
        target_value="alpha",
        session_id="s-001",
        ritual_phase="DO",
        evidence_refs=["lease/01KX"],
    )
    assert e.action["detail"] == {"tool_name": "alpha"}
    assert e.target == {"type": "tool", "value": "alpha"}
    assert e.context["session_id"] == "s-001"
    assert e.context["ritual_phase"] == "DO"
    assert e.context["evidence_refs"] == ["lease/01KX"]


# ─── core verdict ladder ─────────────────────────────────────────────


def test_query_unknown_authority_deny() -> None:
    """Article XVI — actor not in ALLOWED_AUTHORITY_CLASSES → default-deny."""
    e = build_query_envelope(
        actor_id="rogue",
        authority_class="bandit",  # not in the closed set
        action_kind="transition",
    )
    v = query(e, policy_doc={})
    assert v.verdict == "deny"
    assert v.reason == "unknown_authority"
    assert v.evidence_ref["rule_id"] == "article.XVI"
    assert v.query_id == e.query_id


def test_query_schema_drift_deny() -> None:
    """schema_version != '1' → deny(schema_invalid)."""
    e = build_query_envelope(
        actor_id="kernel",
        authority_class="kernel",
        action_kind="transition",
    )
    # Replace schema_version with the rogue value
    e.schema_version = "2"
    v = query(e, policy_doc={})
    assert v.verdict == "deny"
    assert v.reason == "schema_invalid"
    assert v.evidence_ref["rule_id"] == "schema.v1"


def test_query_known_authority_advisory_allow() -> None:
    """POC advisory pass — known authority + no rule match → allow."""
    for auth in sorted(ALLOWED_AUTHORITY_CLASSES):
        e = build_query_envelope(
            actor_id="x",
            authority_class=auth,
            action_kind="transition",
        )
        v = query(e, policy_doc={})
        assert v.verdict == "allow", f"expected allow for {auth}"
        assert v.reason == ""
        assert v.evidence_ref["rule_id"] == "advisory.poc"


def test_query_verdict_is_in_closed_set() -> None:
    """Every returned verdict must be drawn from VERDICT_SET (Article XVI closure)."""
    cases = [
        build_query_envelope(actor_id="x", authority_class="kernel", action_kind="t"),
        build_query_envelope(actor_id="x", authority_class="bandit", action_kind="t"),
    ]
    for e in cases:
        v = query(e, policy_doc={})
        assert v.verdict in VERDICT_SET


def test_query_engine_version_pulled_from_doc() -> None:
    e = build_query_envelope(
        actor_id="kernel", authority_class="kernel", action_kind="transition"
    )
    v = query(e, policy_doc={"policy_engine": {"version": "9.9.9"}})
    assert v.engine_version == "9.9.9"


def test_query_engine_version_default_when_missing() -> None:
    e = build_query_envelope(
        actor_id="kernel", authority_class="kernel", action_kind="transition"
    )
    v = query(e, policy_doc={})
    assert v.engine_version == "1.0"


# ─── doc loader ──────────────────────────────────────────────────────


def test_load_policy_doc_missing_falls_back_to_kernel_baseline(tmp_path: Path) -> None:
    # P0-3 (2026-06-10): missing project policy is no longer a silent {} —
    # the kernel-shipped baseline is used (loudly). Default-deny {} remains
    # only when the kernel baseline is absent too (covered below).
    doc = load_policy_doc(tmp_path)
    assert isinstance(doc, dict)
    assert doc != {}


def test_load_policy_doc_default_deny_when_kernel_baseline_absent(
    tmp_path: Path, monkeypatch
) -> None:
    from cli.core import kernel_resource

    monkeypatch.setattr(
        kernel_resource, "_KERNEL_AI_ROOT", tmp_path / "no-kernel-here"
    )
    assert load_policy_doc(tmp_path) == {}


def test_load_policy_doc_returns_dict_on_malformed(tmp_path: Path) -> None:
    p = tmp_path / ".ai" / "policies"
    p.mkdir(parents=True)
    (p / "trinity_policy.yaml").write_text(": not yaml :: at all", encoding="utf-8")
    # Malformed yaml → {} fallback (Article XX passive — no crash)
    assert load_policy_doc(tmp_path) == {}


def test_load_policy_doc_returns_dict_on_non_mapping(tmp_path: Path) -> None:
    p = tmp_path / ".ai" / "policies"
    p.mkdir(parents=True)
    (p / "trinity_policy.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    assert load_policy_doc(tmp_path) == {}


def test_load_policy_doc_parses_real_file(tmp_path: Path) -> None:
    p = tmp_path / ".ai" / "policies"
    p.mkdir(parents=True)
    (p / "trinity_policy.yaml").write_text(
        "policy_engine:\n  version: '2.5'\n", encoding="utf-8"
    )
    doc = load_policy_doc(tmp_path)
    assert doc["policy_engine"]["version"] == "2.5"


# ─── audit dict round-trip ───────────────────────────────────────────


def test_envelope_to_audit_dict_round_trip() -> None:
    e = build_query_envelope(
        actor_id="kernel", authority_class="kernel", action_kind="transition"
    )
    v = query(e, policy_doc={})
    out = envelope_to_audit_dict(v)
    assert out["query_id"] == e.query_id
    assert out["verdict"] == "allow"
    assert out["reason"] == ""
    assert out["evidence_ref"]["rule_file"] == POLICY_FILE_PATH
    assert isinstance(out["emitted_at"], str) and "T" in out["emitted_at"]
    assert out["schema_version"] == "1"


def test_envelope_to_audit_dict_carries_deny_path() -> None:
    e = build_query_envelope(
        actor_id="rogue", authority_class="bandit", action_kind="transition"
    )
    v = query(e, policy_doc={})
    out = envelope_to_audit_dict(v)
    assert out["verdict"] == "deny"
    assert out["reason"] == "unknown_authority"
    assert out["evidence_ref"]["rule_anchor"] == "default_verdict"


# ─── boundaries.forbidden_tools rule (Phase 5 gating) ────────────────


def test_forbidden_tools_rule_match_denies() -> None:
    """When trinity_policy.yaml declares forbidden_tools and target matches → deny(illegal_target)."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="kernel",
        action_kind="tool_invoke",
        target_type="tool",
        target_value="alpha",
    )
    policy_doc = {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {"forbidden_tools": ["alpha", "beta"]},
        }
    }
    v = query(e, policy_doc=policy_doc)
    assert v.verdict == "deny"
    assert v.reason == "illegal_target"
    assert v.evidence_ref["rule_id"] == "boundaries.forbidden_tools"
    assert v.evidence_ref["rule_anchor"] == "forbidden_tools"


def test_forbidden_tools_rule_no_match_allows() -> None:
    """When target.value NOT in forbidden_tools list → advisory allow path."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="kernel",
        action_kind="tool_invoke",
        target_type="tool",
        target_value="gamma",
    )
    policy_doc = {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {"forbidden_tools": ["alpha", "beta"]},
        }
    }
    v = query(e, policy_doc=policy_doc)
    assert v.verdict == "allow"
    assert v.reason == ""


def test_forbidden_tools_missing_boundaries_key_allows() -> None:
    """No boundaries key at all → engine falls through to advisory allow."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="kernel",
        action_kind="tool_invoke",
        target_type="tool",
        target_value="alpha",
    )
    v = query(e, policy_doc={"policy_engine": {"version": "1.0"}})
    assert v.verdict == "allow"


def test_forbidden_tools_empty_list_allows() -> None:
    """Empty forbidden_tools list → no rule fires → advisory allow."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="kernel",
        action_kind="tool_invoke",
        target_type="tool",
        target_value="alpha",
    )
    policy_doc = {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {"forbidden_tools": []},
        }
    }
    v = query(e, policy_doc=policy_doc)
    assert v.verdict == "allow"


def test_forbidden_tools_no_target_allows() -> None:
    """Query without a target.value cannot match forbidden_tools → allow."""
    e = build_query_envelope(
        actor_id="kernel",
        authority_class="kernel",
        action_kind="transition",
    )
    policy_doc = {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {"forbidden_tools": ["alpha"]},
        }
    }
    v = query(e, policy_doc=policy_doc)
    assert v.verdict == "allow"


# ─── §7 forbidden_mutation_paths rule ────────────────────────────────


def _policy_doc_with_forbidden_paths(entries: list) -> dict:
    return {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {"forbidden_mutation_paths": entries},
        }
    }


def test_forbidden_paths_match_denies_with_pattern() -> None:
    """Spec §7 + §5.4 — matching glob → deny(forbidden_path) + forbidden_pattern in evidence."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="ai",
        action_kind="fs_write",
        target_type="path",
        target_value=".ai/policies/safety.yaml",
    )
    doc = _policy_doc_with_forbidden_paths([
        {
            "pattern": ".ai/policies/**",
            "rationale": "Article III",
            "applies_to_actors": ["ai", "tool"],
            "gate_id": "gate.policy_amendment",
        }
    ])
    v = query(e, policy_doc=doc)
    assert v.verdict == "deny"
    assert v.reason == "forbidden_path"
    assert v.evidence_ref["forbidden_pattern"] == ".ai/policies/**"
    assert v.evidence_ref["gate_id"] == "gate.policy_amendment"
    assert v.evidence_ref["rule_id"] == "boundaries.forbidden_mutation_paths"


def test_forbidden_paths_no_match_allows() -> None:
    """Target outside any forbidden pattern → advisory allow."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="ai",
        action_kind="fs_write",
        target_type="path",
        target_value=".ai/sessions/0001/DO/dev/myfile.txt",
    )
    doc = _policy_doc_with_forbidden_paths([
        {"pattern": ".ai/policies/**", "rationale": "Article III"}
    ])
    v = query(e, policy_doc=doc)
    assert v.verdict == "allow"


def test_forbidden_paths_actor_filter_blocks_listed_actor() -> None:
    """applies_to_actors: ['ai'] — only ai is blocked."""
    doc = _policy_doc_with_forbidden_paths([
        {
            "pattern": ".ai/policies/**",
            "applies_to_actors": ["ai"],
            "rationale": "Article III",
        }
    ])
    ai_e = build_query_envelope(
        actor_id="agent", authority_class="ai", action_kind="fs_write",
        target_type="path", target_value=".ai/policies/x.yaml",
    )
    assert query(ai_e, policy_doc=doc).verdict == "deny"


def test_forbidden_paths_actor_filter_allows_unlisted_actor() -> None:
    """applies_to_actors: ['ai'] — kernel actor NOT in list → allow (no match)."""
    doc = _policy_doc_with_forbidden_paths([
        {
            "pattern": ".ai/policies/**",
            "applies_to_actors": ["ai", "tool"],  # excludes kernel
            "rationale": "Article III",
        }
    ])
    kernel_e = build_query_envelope(
        actor_id="kernel", authority_class="kernel", action_kind="fs_write",
        target_type="path", target_value=".ai/policies/x.yaml",
    )
    assert query(kernel_e, policy_doc=doc).verdict == "allow"


def test_forbidden_paths_action_kinds_denied_filter() -> None:
    """action_kinds_denied: ['fs_write'] — fs_read allowed, fs_write denied."""
    doc = _policy_doc_with_forbidden_paths([
        {
            "pattern": ".ai/audit/**",
            "applies_to_actors": ["ai", "tool"],
            "action_kinds_denied": ["fs_write", "fs_delete"],
            "rationale": "Article X audit immutability",
        }
    ])
    read_e = build_query_envelope(
        actor_id="a", authority_class="ai", action_kind="fs_read",
        target_type="path", target_value=".ai/audit/events.ndjson",
    )
    write_e = build_query_envelope(
        actor_id="a", authority_class="ai", action_kind="fs_write",
        target_type="path", target_value=".ai/audit/events.ndjson",
    )
    assert query(read_e, policy_doc=doc).verdict == "allow"  # fs_read not denied
    assert query(write_e, policy_doc=doc).verdict == "deny"  # fs_write denied


def test_forbidden_paths_first_match_wins() -> None:
    """Multiple entries — first matching pattern wins."""
    doc = _policy_doc_with_forbidden_paths([
        {"pattern": ".ai/policies/**", "rationale": "first", "gate_id": "g1"},
        {"pattern": ".ai/**", "rationale": "second", "gate_id": "g2"},
    ])
    e = build_query_envelope(
        actor_id="a", authority_class="ai", action_kind="fs_write",
        target_type="path", target_value=".ai/policies/safety.yaml",
    )
    v = query(e, policy_doc=doc)
    assert v.evidence_ref["gate_id"] == "g1"


def test_forbidden_paths_missing_target_value_allows() -> None:
    """Query without target.value cannot match → allow."""
    e = build_query_envelope(
        actor_id="kernel", authority_class="kernel", action_kind="transition",
    )
    doc = _policy_doc_with_forbidden_paths([
        {"pattern": ".ai/policies/**", "rationale": "Article III"}
    ])
    assert query(e, policy_doc=doc).verdict == "allow"


def test_forbidden_paths_takes_precedence_over_forbidden_tools() -> None:
    """Spec §7 evaluation order — forbidden_paths checked BEFORE forbidden_tools."""
    doc = {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {
                "forbidden_mutation_paths": [
                    {"pattern": "alpha", "rationale": "trap"}
                ],
                "forbidden_tools": ["alpha"],
            },
        }
    }
    e = build_query_envelope(
        actor_id="a", authority_class="ai", action_kind="tool_invoke",
        target_type="tool", target_value="alpha",
    )
    v = query(e, policy_doc=doc)
    # Both rules match the same target. forbidden_paths should win.
    assert v.reason == "forbidden_path"  # not "illegal_target"


# ─── §6 critical_gates — NEEDS_HUMAN path ────────────────────────────


def _policy_doc_with_critical_gates(entries: list) -> dict:
    return {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {"critical_gates": entries},
        }
    }


def test_critical_gate_match_returns_needs_human() -> None:
    """Spec §6.1 — matching gate → NEEDS_HUMAN + gate_id in evidence."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="kernel",
        action_kind="deploy",
        target_type="env",
        target_value="production",
    )
    doc = _policy_doc_with_critical_gates([
        {
            "gate_id": "gate.production_deploy",
            "action_kinds": ["deploy", "promote"],
        }
    ])
    v = query(e, policy_doc=doc)
    assert v.verdict == "NEEDS_HUMAN"
    assert v.reason == "human_gate_required"
    assert v.evidence_ref["gate_id"] == "gate.production_deploy"
    assert v.evidence_ref["rule_id"] == "boundaries.critical_gates"
    assert v.human_gate == {"gate_id": "gate.production_deploy"}


def test_critical_gate_no_match_allows() -> None:
    """action_kind not in gate list → allow."""
    e = build_query_envelope(
        actor_id="executor",
        authority_class="kernel",
        action_kind="tool_invoke",
        target_type="tool",
        target_value="alpha",
    )
    doc = _policy_doc_with_critical_gates([
        {"gate_id": "gate.production_deploy", "action_kinds": ["deploy"]}
    ])
    v = query(e, policy_doc=doc)
    assert v.verdict == "allow"


def test_critical_gate_action_kinds_filter_required() -> None:
    """Entry without action_kinds is skipped (action_kinds is required)."""
    e = build_query_envelope(
        actor_id="x", authority_class="kernel", action_kind="deploy",
        target_type="env", target_value="prod",
    )
    doc = _policy_doc_with_critical_gates([
        {"gate_id": "gate.bad_entry"}  # missing action_kinds
    ])
    v = query(e, policy_doc=doc)
    assert v.verdict == "allow"


def test_critical_gate_applies_to_actors_filter() -> None:
    """applies_to_actors filters by authority_class."""
    doc = _policy_doc_with_critical_gates([
        {
            "gate_id": "gate.ai_only",
            "action_kinds": ["transition"],
            "applies_to_actors": ["ai"],
        }
    ])
    ai_e = build_query_envelope(actor_id="a", authority_class="ai", action_kind="transition")
    kernel_e = build_query_envelope(actor_id="k", authority_class="kernel", action_kind="transition")
    assert query(ai_e, policy_doc=doc).verdict == "NEEDS_HUMAN"
    assert query(kernel_e, policy_doc=doc).verdict == "allow"


def test_critical_gate_target_pattern_filter() -> None:
    """target_pattern glob filters by target.value."""
    doc = _policy_doc_with_critical_gates([
        {
            "gate_id": "gate.prod_only",
            "action_kinds": ["deploy"],
            "target_pattern": "prod*",
        }
    ])
    prod = build_query_envelope(
        actor_id="x", authority_class="kernel", action_kind="deploy",
        target_type="env", target_value="production",
    )
    dev = build_query_envelope(
        actor_id="x", authority_class="kernel", action_kind="deploy",
        target_type="env", target_value="dev",
    )
    assert query(prod, policy_doc=doc).verdict == "NEEDS_HUMAN"
    assert query(dev, policy_doc=doc).verdict == "allow"


def test_critical_gate_first_match_wins() -> None:
    doc = _policy_doc_with_critical_gates([
        {"gate_id": "gate.first", "action_kinds": ["deploy"]},
        {"gate_id": "gate.second", "action_kinds": ["deploy"]},
    ])
    e = build_query_envelope(
        actor_id="x", authority_class="kernel", action_kind="deploy",
    )
    v = query(e, policy_doc=doc)
    assert v.evidence_ref["gate_id"] == "gate.first"


def test_critical_gate_takes_precedence_over_forbidden_tools() -> None:
    """Spec §2.2 precedence — NEEDS_HUMAN beats deny(illegal_target).
    Actually deny dominates NEEDS_HUMAN per spec §2.2; the rule
    is that whichever evaluates FIRST in our query() short-circuits.
    forbidden_paths runs before critical_gates which runs before
    forbidden_tools. Test: a query that would hit BOTH critical_gates
    AND forbidden_tools should hit the gate first."""
    doc = {
        "policy_engine": {
            "version": "1.0",
            "boundaries": {
                "critical_gates": [
                    {"gate_id": "gate.alpha_review", "action_kinds": ["tool_invoke"]}
                ],
                "forbidden_tools": ["alpha"],
            },
        }
    }
    e = build_query_envelope(
        actor_id="x", authority_class="kernel", action_kind="tool_invoke",
        target_type="tool", target_value="alpha",
    )
    v = query(e, policy_doc=doc)
    # critical_gates evaluated before forbidden_tools → NEEDS_HUMAN wins
    assert v.verdict == "NEEDS_HUMAN"
    assert v.evidence_ref["gate_id"] == "gate.alpha_review"
