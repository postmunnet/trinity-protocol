"""Conformance tests for the extended VerifierVerdict shape.

Spec: docs/specs/TRINITY_VERIFIER_CONTRACT_V1.md §5 (verdict-shape consolidation).

These are Tier-0/1 deterministic checks — no network, no LLM. They cover:
- the 4 new spec-§5 fields (layer, tier, capture_refs, audit_event) on
  VerifierVerdict
- TIER_MAP coverage for every rule_set declared in
  .ai/policies/verifier-rules.yaml
- the 4 reserved predicate skeletons raising NotImplementedError
- presence of the `verify.completed` audit event string literal in
  verifier.py source (kernel-side emission anchor — Spec §3 registry)
- backward compatibility with existing positional/keyword construction
"""
from __future__ import annotations

import dataclasses
import datetime
import hashlib
import pathlib
import sqlite3
from typing import Set

import pytest
import yaml

from cli.core import verifier as v
from cli.core.verifier import (
    EVENT_VERIFY_COMPLETED,
    TIER_MAP,
    VerifierVerdict,
    capture_finalize_missing,
    capture_missing_for_artifact,
    orphaned_invocation,
    sandbox_profile_missing,
)


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
RULES_YAML = PROJECT_ROOT / ".ai" / "policies" / "verifier-rules.yaml"
VERIFIER_PY = PROJECT_ROOT / ".ai" / "cli" / "core" / "verifier.py"


# ─────────── VerifierVerdict shape (Spec §5) ───────────


def test_verdict_has_all_four_new_fields() -> None:
    fields = {f.name for f in dataclasses.fields(VerifierVerdict)}
    need = {"layer", "tier", "capture_refs", "audit_event"}
    missing = need - fields
    assert not missing, f"VerifierVerdict missing fields: {missing}"


def test_verdict_default_layer_is_1() -> None:
    v_ = VerifierVerdict(verdict="PASS", reason="ok", rule_set="step_complete")
    assert v_.layer == 1


def test_verdict_default_capture_refs_is_empty_list() -> None:
    v_ = VerifierVerdict(verdict="PASS", reason="ok", rule_set="step_complete")
    assert v_.capture_refs == []
    # Independent instances must not share the default list (dataclass field
    # default_factory contract)
    v2 = VerifierVerdict(verdict="PASS", reason="ok", rule_set="step_complete")
    v_.capture_refs.append("cap_001")
    assert v2.capture_refs == []


def test_verdict_default_audit_event_is_none() -> None:
    v_ = VerifierVerdict(verdict="PASS", reason="ok", rule_set="step_complete")
    assert v_.audit_event is None


# ─────────── Tier auto-resolution from TIER_MAP ───────────


def test_verdict_auto_resolves_tier_from_rule_set() -> None:
    for rule_set, expected_tier in TIER_MAP.items():
        v_ = VerifierVerdict(verdict="PASS", reason="ok", rule_set=rule_set)
        assert v_.tier == expected_tier, f"{rule_set}: got {v_.tier}, want {expected_tier}"


def test_verdict_default_tier_unknown_rule_set_falls_back_to_warm() -> None:
    v_ = VerifierVerdict(verdict="PASS", reason="ok", rule_set="some_unknown_set")
    assert v_.tier == "WARM"


def test_verdict_caller_supplied_tier_is_preserved() -> None:
    v_ = VerifierVerdict(
        verdict="PASS",
        reason="ok",
        rule_set="step_complete",  # would auto-resolve to WARM
        tier="COLD",                # caller override wins
    )
    assert v_.tier == "COLD"


# ─────────── TIER_MAP coverage of policy file ───────────


def test_tier_map_covers_all_existing_rule_sets() -> None:
    """Every rule_set declared in verifier-rules.yaml MUST have a TIER_MAP entry."""
    if not RULES_YAML.exists():
        pytest.skip(f"verifier-rules.yaml not found at {RULES_YAML}")
    with RULES_YAML.open("r", encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    yaml_rule_sets: Set[str] = set((doc.get("verifier_rules") or {}).keys())
    missing = yaml_rule_sets - set(TIER_MAP.keys())
    assert not missing, f"TIER_MAP missing tier for rule_sets in yaml: {missing}"


def test_tier_map_values_are_valid_tier_strings() -> None:
    valid_tiers = {"HOT", "WARM", "COLD"}
    invalid = {k: t for k, t in TIER_MAP.items() if t not in valid_tiers}
    assert not invalid, f"TIER_MAP has invalid tier values: {invalid}"


# ─────────── RecordProxy-alignment predicates (Spec §4) ───────────


def test_orphaned_invocation_detects_mutation_without_capture() -> None:
    assert callable(orphaned_invocation)
    assert orphaned_invocation({
        "event_type": "tool.invocation.started",
        "capture_id": None,
    }) is True
    assert orphaned_invocation({
        "event_type": "tool.invocation.started",
        "capture_id": "cap_01",
    }) is False
    assert orphaned_invocation({
        "event_type": "session.created",
        "capture_id": None,
    }) is False


def _capture_db(session: pathlib.Path) -> pathlib.Path:
    db = session / "CAPTURE" / "capture.sqlite"
    db.parent.mkdir(parents=True)
    return db


def test_capture_finalize_missing_detects_stuck_capture(tmp_path: pathlib.Path) -> None:
    assert callable(capture_finalize_missing)
    session = tmp_path / "sess"
    db = _capture_db(session)
    conn = sqlite3.connect(str(db))
    conn.execute(
        "CREATE TABLE captures (capture_id TEXT, status TEXT, started_at_utc TEXT)"
    )
    conn.execute(
        "INSERT INTO captures VALUES (?, ?, ?)",
        ("cap_stuck", "CAPTURING", "2026-05-13T12:00:00Z"),
    )
    conn.commit()
    conn.close()

    now = datetime.datetime(2026, 5, 13, 12, 10, tzinfo=datetime.timezone.utc)
    assert capture_finalize_missing(
        session,
        timeout_seconds=300,
        now=now,
    ) is True


def test_capture_finalize_missing_ignores_fresh_capture(tmp_path: pathlib.Path) -> None:
    session = tmp_path / "sess"
    db = _capture_db(session)
    conn = sqlite3.connect(str(db))
    conn.execute(
        "CREATE TABLE captures (capture_id TEXT, status TEXT, started_at_utc TEXT)"
    )
    conn.execute(
        "INSERT INTO captures VALUES (?, ?, ?)",
        ("cap_fresh", "CAPTURING", "2026-05-13T12:09:00Z"),
    )
    conn.commit()
    conn.close()

    now = datetime.datetime(2026, 5, 13, 12, 10, tzinfo=datetime.timezone.utc)
    assert capture_finalize_missing(
        session,
        timeout_seconds=300,
        now=now,
    ) is False


def test_capture_missing_for_artifact_detects_uncaptured_file(tmp_path: pathlib.Path) -> None:
    assert callable(capture_missing_for_artifact)
    session = tmp_path / "sess"
    out = session / "DO" / "dev" / "artifact.txt"
    out.parent.mkdir(parents=True)
    out.write_text("artifact", encoding="utf-8")
    assert capture_missing_for_artifact(session) is True


def test_capture_missing_for_artifact_accepts_captured_hash(tmp_path: pathlib.Path) -> None:
    session = tmp_path / "sess"
    out = session / "DO" / "dev" / "artifact.txt"
    out.parent.mkdir(parents=True)
    out.write_text("artifact", encoding="utf-8")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()

    db = _capture_db(session)
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE capture_items (blob_sha256 TEXT)")
    conn.execute("INSERT INTO capture_items VALUES (?)", (digest,))
    conn.commit()
    conn.close()

    assert capture_missing_for_artifact(session) is False


def test_sandbox_profile_missing_detects_missing_bound_event(tmp_path: pathlib.Path) -> None:
    assert callable(sandbox_profile_missing)
    session = tmp_path / "sess"
    session.mkdir()
    assert sandbox_profile_missing(session) is True


def test_sandbox_profile_missing_accepts_bound_event(tmp_path: pathlib.Path) -> None:
    session = tmp_path / "sess"
    db = _capture_db(session)
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE audit_events (event_type TEXT)")
    conn.execute("INSERT INTO audit_events VALUES (?)", ("sandbox.profile.bound",))
    conn.commit()
    conn.close()

    assert sandbox_profile_missing(session) is False


def test_all_four_reserved_predicates_accessible_from_module() -> None:
    for name in (
        "orphaned_invocation",
        "capture_finalize_missing",
        "capture_missing_for_artifact",
        "sandbox_profile_missing",
    ):
        assert hasattr(v, name), f"verifier module missing predicate skeleton: {name}"
        assert callable(getattr(v, name))


# ─────────── verify.completed emission anchor ───────────


def test_verify_completed_event_constant_present() -> None:
    assert EVENT_VERIFY_COMPLETED == "verify.completed"


def test_verify_completed_string_literal_in_source() -> None:
    """A8 acceptance anchor — grep-based check that the kernel emission
    site name is present in verifier.py source so future emission sites
    can be located deterministically."""
    src = VERIFIER_PY.read_text(encoding="utf-8")
    assert "verify.completed" in src, (
        "verifier.py source must contain 'verify.completed' literal "
        "(Spec §3 audit registry anchor)"
    )


# ─────────── backward compatibility ───────────


def test_legacy_construction_still_works() -> None:
    """Existing callers passing only the 6 v0 fields must continue to work
    (rollback risk per plan_envelope.rollback bullet 3)."""
    v_ = VerifierVerdict(
        verdict="PASS",
        reason="legacy caller",
        rule_set="code_change",
    )
    assert v_.verdict == "PASS"
    assert v_.reason == "legacy caller"
    assert v_.rule_set == "code_change"
    assert v_.mode == "rules"
    assert v_.matched_predicates == []
    assert v_.evidence_keys == []


def test_legacy_construction_with_all_v0_fields() -> None:
    v_ = VerifierVerdict(
        verdict="RETRY",
        reason="pending",
        rule_set="step_complete",
        mode="fallback",
        matched_predicates=["foo"],
        evidence_keys=["bar"],
    )
    assert v_.mode == "fallback"
    assert v_.matched_predicates == ["foo"]
    assert v_.evidence_keys == ["bar"]
    # New fields populated with defaults
    assert v_.layer == 1
    assert v_.tier == "WARM"  # auto from step_complete
    assert v_.capture_refs == []
    assert v_.audit_event is None


# ─────────── evaluate_step round-trip (no regression) ───────────


def test_evaluate_step_returns_verdict_with_new_fields_populated() -> None:
    """The kernel evaluate_step() path must produce verdicts that satisfy
    the extended shape (auto-tier from rule_set + layer default)."""
    rules_doc = {
        "verifier_rules": {
            "step_complete": {
                "pass_when": ["done"],
                "fallback_verdict": "RETRY",
            }
        }
    }
    step = {"done": True}
    verdict = v.evaluate_step(step, "step_complete", rules_doc)
    assert verdict.verdict == "PASS"
    assert verdict.layer == 1
    assert verdict.tier == "WARM"  # step_complete → WARM per TIER_MAP
    assert isinstance(verdict.capture_refs, list)
    assert verdict.audit_event is None
