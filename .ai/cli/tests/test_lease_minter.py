"""Phase 6 Session D — lease minter tests.

Covers A1-A8 from THINK/00_CONTEXT:
  A1 import-time safety
  A2 happy-path mint (ULID shape, well-formed lease)
  A3 timestamps (RFC3339 UTC, expires_at - granted_at == ttl)
  A4 defaults (decided_by="kernel", required_artifacts mirror executor contract)
  A5 overrides (allowed_paths / sandbox_profile_ref / allowed_audit_event_types)
  A6 ordering (monotonic now → lexicographic lease_id ordering)
  A7 now injection (deterministic granted_at)
  A8 round-trip with guard + emitter (Session B + C integration)
"""
from __future__ import annotations

import importlib
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from cli.core.audit import AuditChain
from cli.core.executor import (
    ALLOWED_AUDIT_EVENT_TYPES,
    REQUIRED_OUTPUT_ARTIFACTS,
    ExecutionLease,
)
from cli.core.lease_minter import DEFAULT_LEASE_AUDIT_EVENTS, mint_lease
from cli.core.tool_invocation_emitter import emit_decision
from cli.core.tool_invocation_guard import (
    PROPOSED_EVENT_TYPE,
    propose_invocation,
)
from cli.core.tool_registry import load_registry

# Crockford base32 alphabet excludes I, L, O, U.
_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


# ─── shared registry fixture builders ────────────────────────────────


def _full_tool_entry(name: str, **overrides: Any) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        "name": name,
        "description": f"{name} description",
        "path": f"/fake/{name}",
        "bin": f"/fake/{name}/bin",
        "schema_version": "1",
        "contract_version": "1.0",
        "capabilities": ["x"],
        "policy_default": "safe",
    }
    e.update(overrides)
    return e


def _full_cap_entry(name: str, **overrides: Any) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        "name": name,
        "required_capabilities": ["fs.read"],
        "optional_capabilities": [],
        "default_tier_requirement": "WARM",
        "notes": "",
    }
    e.update(overrides)
    return e


def _full_vocabulary() -> Dict[str, List[str]]:
    return {
        "fs": ["fs.read", "fs.write", "fs.delete"],
        "net": ["net.outbound", "net.allowlist"],
        "proc": ["proc.exec", "proc.spawn"],
        "audit": ["audit.read", "audit.append"],
        "policy": ["policy.read"],
        "ddd": ["ddd.propose", "ddd.decide"],
        "tool": ["tool.invoke"],
    }


def _write_pair(root: Path, tools: List[Dict[str, Any]], caps: List[Dict[str, Any]]) -> None:
    (root / ".ai").mkdir(parents=True, exist_ok=True)
    (root / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "tools": tools}, sort_keys=False),
        encoding="utf-8",
    )
    (root / ".ai" / "tools.capabilities.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "status": "authoritative",
                "authoritative": True,
                "capability_vocabulary": _full_vocabulary(),
                "tools": caps,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


# ─── A1 import-time safety ────────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.lease_minter")
    assert hasattr(mod, "mint_lease")
    assert hasattr(mod, "DEFAULT_LEASE_AUDIT_EVENTS")


# ─── A2 happy-path mint ──────────────────────────────────────────────


def test_happy_path_mint_returns_well_shaped_lease() -> None:
    lease = mint_lease("0001_test_session", "S1")

    assert isinstance(lease, ExecutionLease)
    assert _ULID_RE.match(lease.lease_id), f"lease_id {lease.lease_id!r} not Crockford-base32 26 chars"
    assert lease.session_id == "0001_test_session"
    assert lease.step_id == "S1"
    assert lease.decided_by == "kernel"


# ─── A3 timestamps ────────────────────────────────────────────────────


def test_timestamps_are_rfc3339_utc_and_ttl_holds() -> None:
    fixed = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
    lease = mint_lease("s", "S1", ttl_seconds=300, now=fixed)

    assert lease.granted_at.endswith("Z")
    assert lease.expires_at.endswith("Z")
    granted = datetime.fromisoformat(lease.granted_at.replace("Z", "+00:00"))
    expires = datetime.fromisoformat(lease.expires_at.replace("Z", "+00:00"))
    assert granted == fixed
    assert (expires - granted).total_seconds() == 300


# ─── A4 defaults ──────────────────────────────────────────────────────


def test_defaults_match_executor_contract() -> None:
    lease = mint_lease("s", "S1")

    assert lease.decided_by == "kernel"
    assert lease.required_artifacts == list(REQUIRED_OUTPUT_ARTIFACTS)
    assert lease.allowed_paths == []
    assert lease.sandbox_profile_ref is None
    # Default audit event types are a subset of executor.ALLOWED_AUDIT_EVENT_TYPES.
    for et in lease.allowed_audit_event_types:
        assert et in ALLOWED_AUDIT_EVENT_TYPES
    # Subset includes at least the guard's two event_types.
    assert "tool.invocation_proposed" in lease.allowed_audit_event_types
    assert "tool.invocation_denied" in lease.allowed_audit_event_types


# ─── A5 overrides ─────────────────────────────────────────────────────


def test_overrides_pass_through() -> None:
    lease = mint_lease(
        "s",
        "S2",
        ttl_seconds=60,
        allowed_paths=[".ai/cli/core/", ".ai/cli/tests/"],
        allowed_audit_event_types=["tool.invocation_proposed"],
        sandbox_profile_ref="/path/to/sandbox.json",
    )

    assert lease.allowed_paths == [".ai/cli/core/", ".ai/cli/tests/"]
    assert lease.allowed_audit_event_types == ["tool.invocation_proposed"]
    assert lease.sandbox_profile_ref == "/path/to/sandbox.json"


# ─── A6 ordering ──────────────────────────────────────────────────────


def test_lease_id_lex_ordering_with_monotonic_now() -> None:
    """Two mints at strictly increasing `now` produce lex-ordered lease_ids."""
    t1 = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(milliseconds=1)
    t3 = t1 + timedelta(seconds=1)

    l1 = mint_lease("s", "S1", now=t1).lease_id
    l2 = mint_lease("s", "S1", now=t2).lease_id
    l3 = mint_lease("s", "S1", now=t3).lease_id

    # Distinct mints, distinct ids (random tail differs even within same ms).
    assert l1 != l2 != l3
    # Monotonic `now` → lex-ordered lease_ids (different timestamp prefix).
    assert l1 < l2 < l3


def test_lease_id_distinct_within_same_millisecond() -> None:
    """Within the same millisecond, random tail tie-breaks; no equality."""
    fixed = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
    ids = {mint_lease("s", "S1", now=fixed).lease_id for _ in range(100)}
    assert len(ids) == 100  # all 100 distinct


# ─── A7 now injection ─────────────────────────────────────────────────


def test_now_injection_produces_deterministic_granted_at() -> None:
    fixed = datetime(2026, 5, 16, 12, 34, 56, 789000, tzinfo=timezone.utc)
    lease = mint_lease("s", "S1", now=fixed)
    parsed = datetime.fromisoformat(lease.granted_at.replace("Z", "+00:00"))
    assert parsed == fixed


def test_naive_datetime_now_is_normalised_to_utc() -> None:
    naive = datetime(2026, 5, 16, 12, 0, 0)
    lease = mint_lease("s", "S1", now=naive)
    parsed = datetime.fromisoformat(lease.granted_at.replace("Z", "+00:00"))
    assert parsed == naive.replace(tzinfo=timezone.utc)


# ─── A8 round-trip with guard + emitter ──────────────────────────────


def test_round_trip_minted_lease_passes_guard_and_emits(tmp_path: Path) -> None:
    """Session B + C integration: mint → propose (allow) → emit → chain.validate()."""
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")

    lease = mint_lease("0001_test_session", "S1")
    decision = propose_invocation(lease, "alpha", reg)

    assert decision.verdict == "allow"
    event = emit_decision(chain, decision)

    assert event is not None
    assert event["type"] == PROPOSED_EVENT_TYPE
    assert event["details"]["lease_id"] == lease.lease_id
    chain.validate()  # raises on broken link
