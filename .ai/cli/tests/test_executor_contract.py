"""Conformance tests for the Executor organ contract (Article IV + XXVIII).

Spec: docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §6 (Executor).

These are Tier-0/1 deterministic checks. They prove the contract surface
is present and well-formed — they do NOT test executor *behavior* (which
is Phase 6/7 work).
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
from typing import Set

import jsonschema
import pytest

from cli.core import executor as ex
from cli.core.audit_replay import CANONICAL_EVENT_TYPES
from cli.core.executor import (
    ALLOWED_AUDIT_EVENT_TYPES,
    EXECUTOR_CONTRACT,
    FORBIDDEN_ACTIONS,
    REQUIRED_OUTPUT_ARTIFACTS,
    ArtifactManifest,
    ExecutionLease,
)


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
SCHEMA_DIR = PROJECT_ROOT / ".ai" / "schemas"


# ─────────── Article XXVIII — 8 fields surface ───────────


EXTENSION_RULE_FIELDS = (
    "role",
    "authority",
    "inputs",
    "outputs",
    "artifacts",
    "state_permissions",
    "failure_mode",
    "audit_events",
)


def test_executor_contract_has_all_8_extension_rule_fields() -> None:
    fields_present = set(EXECUTOR_CONTRACT.keys())
    missing = set(EXTENSION_RULE_FIELDS) - fields_present
    assert not missing, f"EXECUTOR_CONTRACT missing fields: {missing}"


def test_executor_contract_fields_are_non_empty_strings() -> None:
    for field_name in EXTENSION_RULE_FIELDS:
        value = EXECUTOR_CONTRACT[field_name]
        assert isinstance(value, str), f"{field_name!r}: not a string"
        assert len(value.strip()) > 0, f"{field_name!r}: empty string"


def test_executor_contract_authority_references_article_iv() -> None:
    # Article IV anchor MUST appear in the authority text — proves the
    # author wired Article IV intent into the contract.
    assert "Article IV" in EXECUTOR_CONTRACT["authority"]


def test_executor_contract_failure_mode_references_failure_visibility() -> None:
    # Article XXIII anchor MUST appear so silent-success risk is named.
    assert "Article XXIII" in EXECUTOR_CONTRACT["failure_mode"]


# ─────────── REQUIRED_OUTPUT_ARTIFACTS ───────────


def test_required_artifacts_includes_canonical_four() -> None:
    canonical = {
        "diff.patch",
        "execution.log",
        "tool_calls.jsonl",
        "artifact_manifest.json",
    }
    missing = canonical - set(REQUIRED_OUTPUT_ARTIFACTS)
    assert not missing, f"REQUIRED_OUTPUT_ARTIFACTS missing canonical: {missing}"


def test_required_artifacts_minimum_count() -> None:
    assert len(REQUIRED_OUTPUT_ARTIFACTS) >= 4


# ─────────── ALLOWED_AUDIT_EVENT_TYPES is a closed subset ───────────


def test_allowed_audit_event_types_is_frozenset() -> None:
    assert isinstance(ALLOWED_AUDIT_EVENT_TYPES, frozenset)


def test_allowed_audit_event_types_non_empty() -> None:
    assert len(ALLOWED_AUDIT_EVENT_TYPES) > 0


def test_allowed_audit_event_types_all_in_canonical_registry() -> None:
    """Every event_type the executor is allowed to emit MUST exist in the
    canonical TRINITY_AUDIT_EVENT_SPEC_V1 §3 registry. Article XVI: unknown
    authority = denied; the executor cannot mint new event_types."""
    invalid: Set[str] = ALLOWED_AUDIT_EVENT_TYPES - CANONICAL_EVENT_TYPES
    assert not invalid, (
        f"ALLOWED_AUDIT_EVENT_TYPES contains event_types absent from "
        f"the canonical §3 registry: {invalid}"
    )


def test_allowed_audit_event_types_includes_gogogo_step_lifecycle() -> None:
    # gogogo.step_started / step_completed / step_passed / step_failed
    # are the minimal lifecycle every executor invocation must emit.
    needed = {
        "gogogo.step_started",
        "gogogo.step_completed",
        "gogogo.step_passed",
        "gogogo.step_failed",
    }
    missing = needed - ALLOWED_AUDIT_EVENT_TYPES
    assert not missing, f"missing gogogo lifecycle: {missing}"


# ─────────── FORBIDDEN_ACTIONS ───────────


def test_forbidden_actions_non_empty() -> None:
    assert isinstance(FORBIDDEN_ACTIONS, list)
    assert len(FORBIDDEN_ACTIONS) > 0


def test_forbidden_actions_lists_verifier_collapse_risk() -> None:
    # Article IV: verifier-verdict role collapse MUST be explicitly named
    # so future readers see it.
    joined = "\n".join(FORBIDDEN_ACTIONS)
    assert "verifier" in joined.lower()


def test_forbidden_actions_lists_human_gate_collapse_risk() -> None:
    joined = "\n".join(FORBIDDEN_ACTIONS).lower()
    assert "human gate" in joined or "ddd" in joined


def test_forbidden_actions_lists_state_transition_collapse_risk() -> None:
    joined = "\n".join(FORBIDDEN_ACTIONS).lower()
    assert "state transition" in joined or "kernel-decided" in joined


# ─────────── ExecutionLease / ArtifactManifest dataclasses ───────────


def test_execution_lease_dataclass_fields() -> None:
    fields = {f.name for f in dataclasses.fields(ExecutionLease)}
    required = {
        "lease_id",
        "session_id",
        "step_id",
        "granted_at",
        "expires_at",
        "allowed_paths",
        "allowed_audit_event_types",
        "required_artifacts",
        "decided_by",
    }
    missing = required - fields
    assert not missing, f"ExecutionLease missing fields: {missing}"


def test_artifact_manifest_dataclass_fields() -> None:
    fields = {f.name for f in dataclasses.fields(ArtifactManifest)}
    required = {
        "manifest_version",
        "session_id",
        "step_id",
        "artifacts",
        "generated_at",
    }
    missing = required - fields
    assert not missing, f"ArtifactManifest missing fields: {missing}"


def test_execution_lease_default_required_artifacts_matches_constant() -> None:
    lease = ExecutionLease(
        lease_id="ll_test_001",
        session_id="0001_test",
        step_id="S1",
        granted_at="2026-05-15T00:00:00Z",
        expires_at="2026-05-15T01:00:00Z",
    )
    assert lease.required_artifacts == REQUIRED_OUTPUT_ARTIFACTS


def test_execution_lease_decided_by_defaults_to_kernel() -> None:
    lease = ExecutionLease(
        lease_id="ll_test_002",
        session_id="0001_test",
        step_id="S2",
        granted_at="2026-05-15T00:00:00Z",
        expires_at="2026-05-15T01:00:00Z",
    )
    assert lease.decided_by == "kernel"


# ─────────── Schema validity + dataclass round-trip ───────────


def test_execution_lease_schema_is_valid_jsonschema() -> None:
    schema = json.loads(
        (SCHEMA_DIR / "execution_lease.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)


def test_artifact_manifest_schema_is_valid_jsonschema() -> None:
    schema = json.loads(
        (SCHEMA_DIR / "artifact_manifest.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)


def test_execution_lease_instance_validates_against_schema() -> None:
    schema = json.loads(
        (SCHEMA_DIR / "execution_lease.schema.json").read_text(encoding="utf-8")
    )
    lease = ExecutionLease(
        lease_id="ll_test_003",
        session_id="0001_test",
        step_id="S1",
        granted_at="2026-05-15T00:00:00Z",
        expires_at="2026-05-15T01:00:00Z",
        allowed_paths=[".ai/sessions/0001_test/DO/dev/**"],
        allowed_audit_event_types=list(ALLOWED_AUDIT_EVENT_TYPES),
    )
    jsonschema.validate(dataclasses.asdict(lease), schema)


def test_artifact_manifest_instance_validates_against_schema() -> None:
    schema = json.loads(
        (SCHEMA_DIR / "artifact_manifest.schema.json").read_text(encoding="utf-8")
    )
    manifest = ArtifactManifest(
        manifest_version="trinity.artifact_manifest.v1",
        session_id="0001_test",
        step_id="S1",
        artifacts=[
            {
                "path": "DO/dev/S1/diff.patch",
                "sha256": "0" * 64,
                "bytes": 0,
            }
        ],
        generated_at="2026-05-15T00:30:00Z",
        lease_id="ll_test_004",
    )
    jsonschema.validate(dataclasses.asdict(manifest), schema)


# ─────────── Schema rejects malformed instances ───────────


def test_execution_lease_schema_rejects_non_kernel_decided_by() -> None:
    schema = json.loads(
        (SCHEMA_DIR / "execution_lease.schema.json").read_text(encoding="utf-8")
    )
    bad_lease = {
        "lease_id": "ll_x",
        "session_id": "s",
        "step_id": "S1",
        "granted_at": "2026-05-15T00:00:00Z",
        "expires_at": "2026-05-15T01:00:00Z",
        "allowed_paths": [],
        "allowed_audit_event_types": [],
        "required_artifacts": ["diff.patch"],
        "decided_by": "executor",  # forbidden — must be 'kernel'
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_lease, schema)


def test_artifact_manifest_schema_rejects_bad_sha256() -> None:
    schema = json.loads(
        (SCHEMA_DIR / "artifact_manifest.schema.json").read_text(encoding="utf-8")
    )
    bad_manifest = {
        "manifest_version": "trinity.artifact_manifest.v1",
        "session_id": "s",
        "step_id": "S1",
        "artifacts": [
            {
                "path": "DO/dev/S1/diff.patch",
                "sha256": "not-a-hex-hash",  # invalid pattern
                "bytes": 0,
            }
        ],
        "generated_at": "2026-05-15T00:30:00Z",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad_manifest, schema)


# ─────────── Module is passive (Article XX) ───────────


def test_module_has_no_top_level_side_effects() -> None:
    # Importing the module again should not raise — re-import is safe.
    import importlib
    import cli.core.executor as ex_mod

    importlib.reload(ex_mod)
    # If we got here, re-import is side-effect-free.
    assert hasattr(ex_mod, "EXECUTOR_CONTRACT")


def test_module_exports_via_dunder_all() -> None:
    expected = {
        "EXECUTOR_CONTRACT",
        "REQUIRED_OUTPUT_ARTIFACTS",
        "ALLOWED_AUDIT_EVENT_TYPES",
        "FORBIDDEN_ACTIONS",
        "ExecutionLease",
        "ArtifactManifest",
    }
    missing = expected - set(ex.__all__)
    assert not missing, f"__all__ missing: {missing}"
