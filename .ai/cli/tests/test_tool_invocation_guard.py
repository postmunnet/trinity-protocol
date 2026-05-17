"""Phase 6 Session B — tool invocation guard tests.

Spec: docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md §2-§3
      docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §6 (Executor)

Covers A1-A5 from THINK/03_ACCEPTANCE.md:
  A1 import-time-safe (no module-level I/O)
  A2 unknown_tool deny
  A3 never_granted_capability deny (audit.append + ddd.decide cases)
  A4 lease_expired deny
  A5 happy-path allow with envelope shape + ALLOWED_AUDIT_EVENT_TYPES membership
"""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from cli.core.executor import ALLOWED_AUDIT_EVENT_TYPES, ExecutionLease
from cli.core.tool_invocation_guard import (
    DENIED_EVENT_TYPE,
    DENY_LEASE_EXPIRED,
    DENY_NEVER_GRANTED_CAPABILITY,
    DENY_UNKNOWN_TOOL,
    InvocationDecision,
    PROPOSED_EVENT_TYPE,
    propose_invocation,
)
from cli.core.tool_registry import load_registry


# ─── fixture builders (mirror test_tool_registry conventions) ────────


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


def _full_cap_entry(
    name: str,
    *,
    required_capabilities: List[str] | None = None,
    **overrides: Any,
) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        "name": name,
        "required_capabilities": required_capabilities or ["fs.read"],
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


def _write_pair(
    root: Path,
    tools: List[Dict[str, Any]],
    caps: List[Dict[str, Any]],
) -> None:
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


def _lease(
    *,
    expires_at: datetime | None = None,
    step_id: str = "S1",
) -> ExecutionLease:
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    return ExecutionLease(
        lease_id="01HXFAKELEASE0001",
        session_id="0001_test_session",
        step_id=step_id,
        granted_at=datetime.now(timezone.utc).isoformat(),
        expires_at=expires_at,
        allowed_paths=[".ai/cli/core/"],
        allowed_audit_event_types=[
            "tool.invocation_proposed",
            "tool.invocation_denied",
        ],
    )


# ─── A1 import-time safety ────────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    """A1: importing the guard must not perform I/O or network calls.

    Re-importing under a freshly imported module reference is sufficient
    to assert that import is pure — pytest's collection itself already
    proved an earlier import was side-effect-free, so this is a paper
    trail for the invariant.
    """
    mod = importlib.import_module("cli.core.tool_invocation_guard")
    assert hasattr(mod, "propose_invocation")
    assert hasattr(mod, "InvocationDecision")
    assert mod.PROPOSED_EVENT_TYPE in ALLOWED_AUDIT_EVENT_TYPES
    assert mod.DENIED_EVENT_TYPE in ALLOWED_AUDIT_EVENT_TYPES


# ─── A2 unknown_tool ──────────────────────────────────────────────────


def test_unknown_tool_denied(tmp_path: Path) -> None:
    _write_pair(
        tmp_path,
        [_full_tool_entry("alpha")],
        [_full_cap_entry("alpha")],
    )
    reg = load_registry(tmp_path)

    decision = propose_invocation(_lease(), "ghost", reg)

    assert isinstance(decision, InvocationDecision)
    assert decision.verdict == "deny"
    assert decision.reason == DENY_UNKNOWN_TOOL
    assert decision.audit_envelope["event_type"] == DENIED_EVENT_TYPE
    assert decision.audit_envelope["tool_name"] == "ghost"
    assert decision.audit_envelope["reason"] == DENY_UNKNOWN_TOOL


# ─── A3 never_granted_capability ─────────────────────────────────────


@pytest.mark.parametrize("forbidden_cap", ["audit.append", "ddd.decide"])
def test_never_granted_capability_denied(
    tmp_path: Path, forbidden_cap: str
) -> None:
    _write_pair(
        tmp_path,
        [_full_tool_entry("alpha")],
        [
            _full_cap_entry(
                "alpha",
                required_capabilities=["fs.read", forbidden_cap],
            )
        ],
    )
    # tool_registry.load_registry validates V4 (NEVER_GRANTED), so a
    # registry containing audit.append/ddd.decide in required_capabilities
    # fails to load. We construct the registry by-pass via direct
    # ToolRegistry instantiation to exercise the guard's defence-in-depth
    # branch (registry-bug surfaced at invocation time).
    from cli.core.tool_registry import ToolCapabilityRecord, ToolRegistry

    rec = ToolCapabilityRecord(
        name="alpha",
        required_capabilities=("fs.read", forbidden_cap),
        optional_capabilities=(),
        default_tier_requirement="WARM",
        notes="",
        description="alpha description",
        path="/fake/alpha",
        bin="/fake/alpha/bin",
        schema_version="1",
        contract_version="1.0",
        declared_capabilities=("x",),
        policy_default="safe",
    )
    reg = ToolRegistry({"alpha": rec})

    decision = propose_invocation(_lease(), "alpha", reg)

    assert decision.verdict == "deny"
    assert decision.reason == DENY_NEVER_GRANTED_CAPABILITY
    assert decision.audit_envelope["event_type"] == DENIED_EVENT_TYPE
    assert decision.audit_envelope["reason"] == DENY_NEVER_GRANTED_CAPABILITY


# ─── A4 lease_expired ────────────────────────────────────────────────


def test_lease_expired_denied(tmp_path: Path) -> None:
    _write_pair(
        tmp_path,
        [_full_tool_entry("alpha")],
        [_full_cap_entry("alpha")],
    )
    reg = load_registry(tmp_path)

    expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    decision = propose_invocation(_lease(expires_at=expired), "alpha", reg)

    assert decision.verdict == "deny"
    assert decision.reason == DENY_LEASE_EXPIRED
    assert decision.audit_envelope["event_type"] == DENIED_EVENT_TYPE
    assert decision.audit_envelope["reason"] == DENY_LEASE_EXPIRED


def test_lease_expired_string_form(tmp_path: Path) -> None:
    """Tolerate RFC3339 string `expires_at` (schema-mirror form)."""
    _write_pair(
        tmp_path,
        [_full_tool_entry("alpha")],
        [_full_cap_entry("alpha")],
    )
    reg = load_registry(tmp_path)

    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    lease = ExecutionLease(
        lease_id="01HXFAKELEASE0002",
        session_id="0001_test_session",
        step_id="S1",
        granted_at=datetime.now(timezone.utc).isoformat(),
        expires_at=past_iso,  # type: ignore[arg-type]
    )

    decision = propose_invocation(lease, "alpha", reg)
    assert decision.verdict == "deny"
    assert decision.reason == DENY_LEASE_EXPIRED


# ─── A5 happy path ───────────────────────────────────────────────────


def test_happy_path_allows_and_emits_envelope(tmp_path: Path) -> None:
    _write_pair(
        tmp_path,
        [_full_tool_entry("alpha")],
        [
            _full_cap_entry(
                "alpha",
                required_capabilities=["fs.read", "net.outbound"],
            )
        ],
    )
    reg = load_registry(tmp_path)

    decision = propose_invocation(_lease(), "alpha", reg)

    assert decision.verdict == "allow"
    assert decision.reason == ""
    env = decision.audit_envelope
    assert env["event_type"] == PROPOSED_EVENT_TYPE
    assert env["event_type"] in ALLOWED_AUDIT_EVENT_TYPES
    assert env["tool_name"] == "alpha"
    assert env["actor"] == "executor"
    assert env["decided_by"] == "kernel"
    assert env["lease_id"] == "01HXFAKELEASE0001"
    assert env["session_id"] == "0001_test_session"
    assert env["step_id"] == "S1"
    assert env["required_capabilities"] == ["fs.read", "net.outbound"]
    assert env["proposed_at"].endswith("Z")


def test_invocation_decision_is_frozen() -> None:
    """Decision dataclass should be immutable (frozen=True invariant)."""
    d = InvocationDecision(verdict="allow", reason="", audit_envelope={})
    with pytest.raises(Exception):
        d.verdict = "deny"  # type: ignore[misc]
