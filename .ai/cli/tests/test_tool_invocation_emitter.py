"""Phase 6 Session C — tool invocation emitter tests.

Covers A1-A7 from THINK/03_ACCEPTANCE:
  A1 import-time safety
  A2 happy-path emit → tool.invocation_proposed row on chain
  A3 unknown_tool deny → tool.invocation_denied row, reason=unknown_tool
  A4 never_granted_capability deny → reason=never_granted_capability
  A5 lease_expired deny → reason=lease_expired
  A6 round-trip: chain.validate() succeeds after a propose+emit sequence
  A7 empty envelope is a defensive no-op (returns None)

Spec anchors:
- cli.core.audit.AuditChain (hash-chained append)
- cli.core.tool_invocation_guard.propose_invocation (Session B)
"""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from cli.core.audit import AuditChain
from cli.core.executor import ExecutionLease
from cli.core.tool_invocation_emitter import emit_decision
from cli.core.tool_invocation_guard import (
    DENIED_EVENT_TYPE,
    DENY_LEASE_EXPIRED,
    DENY_NEVER_GRANTED_CAPABILITY,
    DENY_UNKNOWN_TOOL,
    InvocationDecision,
    PROPOSED_EVENT_TYPE,
    propose_invocation,
)
from cli.core.tool_registry import (
    ToolCapabilityRecord,
    ToolRegistry,
    load_registry,
)


# ─── fixture builders ────────────────────────────────────────────────


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
        lease_id="01HXTESTLEASE0001",
        session_id="0001_test_session",
        step_id=step_id,
        granted_at=datetime.now(timezone.utc).isoformat(),
        expires_at=expires_at,
    )


def _fresh_chain(tmp_path: Path) -> AuditChain:
    """Create an empty AuditChain rooted at tmp_path."""
    return AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")


def _registry_with_forbidden_cap(forbidden_cap: str) -> ToolRegistry:
    """Bypass load_registry V4 to build a registry with a NEVER-granted cap."""
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
    return ToolRegistry({"alpha": rec})


# ─── A1 import-time safety ────────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.tool_invocation_emitter")
    assert hasattr(mod, "emit_decision")


# ─── A2 happy-path emit ──────────────────────────────────────────────


def test_emit_happy_path_appends_proposed_event(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    decision = propose_invocation(_lease(), "alpha", reg)
    event = emit_decision(chain, decision)

    assert event is not None
    assert event["type"] == PROPOSED_EVENT_TYPE
    assert event["details"]["tool_name"] == "alpha"
    assert event["details"]["lease_id"] == "01HXTESTLEASE0001"
    assert "hash" in event
    assert event["prev_hash"] == "0"  # genesis prev


# ─── A3 unknown_tool emit ────────────────────────────────────────────


def test_emit_unknown_tool_appends_denied_event(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    decision = propose_invocation(_lease(), "ghost", reg)
    event = emit_decision(chain, decision)

    assert event is not None
    assert event["type"] == DENIED_EVENT_TYPE
    assert event["details"]["reason"] == DENY_UNKNOWN_TOOL
    assert event["details"]["tool_name"] == "ghost"


# ─── A4 never_granted_capability emit ────────────────────────────────


@pytest.mark.parametrize("forbidden_cap", ["audit.append", "ddd.decide"])
def test_emit_never_granted_capability_appends_denied_event(
    tmp_path: Path, forbidden_cap: str
) -> None:
    reg = _registry_with_forbidden_cap(forbidden_cap)
    chain = _fresh_chain(tmp_path)

    decision = propose_invocation(_lease(), "alpha", reg)
    event = emit_decision(chain, decision)

    assert event is not None
    assert event["type"] == DENIED_EVENT_TYPE
    assert event["details"]["reason"] == DENY_NEVER_GRANTED_CAPABILITY


# ─── A5 lease_expired emit ───────────────────────────────────────────


def test_emit_lease_expired_appends_denied_event(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    decision = propose_invocation(_lease(expires_at=expired), "alpha", reg)
    event = emit_decision(chain, decision)

    assert event is not None
    assert event["type"] == DENIED_EVENT_TYPE
    assert event["details"]["reason"] == DENY_LEASE_EXPIRED


# ─── A6 round-trip chain validation ──────────────────────────────────


def test_round_trip_chain_validates(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    # Sequential emits: happy + deny + happy — chain must remain valid.
    emit_decision(chain, propose_invocation(_lease(), "alpha", reg))
    emit_decision(chain, propose_invocation(_lease(), "ghost", reg))
    emit_decision(chain, propose_invocation(_lease(step_id="S2"), "alpha", reg))

    chain.validate()  # raises on broken link
    events = list(chain.iter_events())
    assert len(events) == 3
    assert events[0]["type"] == PROPOSED_EVENT_TYPE
    assert events[1]["type"] == DENIED_EVENT_TYPE
    assert events[2]["type"] == PROPOSED_EVENT_TYPE
    # prev_hash linkage
    assert events[1]["prev_hash"] == events[0]["hash"]
    assert events[2]["prev_hash"] == events[1]["hash"]


# ─── A7 empty envelope no-op ─────────────────────────────────────────


def test_empty_envelope_returns_none_and_appends_nothing(tmp_path: Path) -> None:
    chain = _fresh_chain(tmp_path)
    decision = InvocationDecision(verdict="deny", reason="custom", audit_envelope={})

    result = emit_decision(chain, decision)

    assert result is None
    assert not chain.path.exists() or chain.path.stat().st_size == 0


def test_envelope_without_event_type_returns_none(tmp_path: Path) -> None:
    """Defensive: an envelope missing event_type is not emittable."""
    chain = _fresh_chain(tmp_path)
    decision = InvocationDecision(
        verdict="deny",
        reason="custom",
        audit_envelope={"tool_name": "alpha"},  # missing event_type
    )

    result = emit_decision(chain, decision)

    assert result is None
    assert not chain.path.exists() or chain.path.stat().st_size == 0
