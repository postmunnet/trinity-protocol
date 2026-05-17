"""Phase 6 Session E — lease lifecycle helper tests.

Covers A1-A8 from THINK/00_CONTEXT:
  A1 import-time safety
  A2 happy_path: success=True, decision.verdict="allow", chain has proposed row
  A3 unknown_tool: success=False, reason=unknown_tool, chain has denied row
  A4 never_granted_capability: success=False, reason=never_granted_capability
  A5/A6 chain integrity: sequence of allowed + denied; chain.validate() clean
  A7 multi-emit prev_hash linkage
  A8 now injection forwards through to mint_lease
"""
from __future__ import annotations

import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from cli.core.audit import AuditChain
from cli.core.lease_lifecycle import LifecycleResult, run_lease_lifecycle
from cli.core.tool_invocation_guard import (
    DENIED_EVENT_TYPE,
    DENY_NEVER_GRANTED_CAPABILITY,
    DENY_UNKNOWN_TOOL,
    PROPOSED_EVENT_TYPE,
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


def _fresh_chain(tmp_path: Path) -> AuditChain:
    return AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")


def _registry_with_forbidden_cap(forbidden_cap: str) -> ToolRegistry:
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
    mod = importlib.import_module("cli.core.lease_lifecycle")
    assert hasattr(mod, "run_lease_lifecycle")
    assert hasattr(mod, "LifecycleResult")


# ─── A2 happy path ────────────────────────────────────────────────────


def test_happy_path_returns_success_and_appends_proposed(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    result = run_lease_lifecycle(
        session_id="0001_test_session",
        step_id="S1",
        tool_name="alpha",
        registry=reg,
        chain=chain,
    )

    assert isinstance(result, LifecycleResult)
    assert result.success is True
    assert result.decision.verdict == "allow"
    assert result.audit_event is not None
    assert result.audit_event["type"] == PROPOSED_EVENT_TYPE
    assert result.audit_event["details"]["tool_name"] == "alpha"
    assert result.audit_event["details"]["lease_id"] == result.lease.lease_id


# ─── A3 unknown_tool ─────────────────────────────────────────────────


def test_unknown_tool_returns_failure_and_appends_denied(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    result = run_lease_lifecycle(
        session_id="0001_test_session",
        step_id="S1",
        tool_name="ghost",
        registry=reg,
        chain=chain,
    )

    assert result.success is False
    assert result.decision.reason == DENY_UNKNOWN_TOOL
    assert result.audit_event is not None
    assert result.audit_event["type"] == DENIED_EVENT_TYPE
    assert result.audit_event["details"]["reason"] == DENY_UNKNOWN_TOOL
    assert result.audit_event["details"]["tool_name"] == "ghost"


# ─── A4 never_granted_capability ─────────────────────────────────────


@pytest.mark.parametrize("forbidden_cap", ["audit.append", "ddd.decide"])
def test_never_granted_capability_returns_failure(
    tmp_path: Path, forbidden_cap: str
) -> None:
    reg = _registry_with_forbidden_cap(forbidden_cap)
    chain = _fresh_chain(tmp_path)

    result = run_lease_lifecycle(
        session_id="0001_test_session",
        step_id="S1",
        tool_name="alpha",
        registry=reg,
        chain=chain,
    )

    assert result.success is False
    assert result.decision.reason == DENY_NEVER_GRANTED_CAPABILITY
    assert result.audit_event is not None
    assert result.audit_event["details"]["reason"] == DENY_NEVER_GRANTED_CAPABILITY


# ─── A5/A6 chain integrity over mixed sequence ───────────────────────


def test_mixed_sequence_preserves_chain_validate(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    # allow + deny + allow + deny pattern.
    r1 = run_lease_lifecycle(
        session_id="s", step_id="S1", tool_name="alpha", registry=reg, chain=chain
    )
    r2 = run_lease_lifecycle(
        session_id="s", step_id="S2", tool_name="ghost", registry=reg, chain=chain
    )
    r3 = run_lease_lifecycle(
        session_id="s", step_id="S3", tool_name="alpha", registry=reg, chain=chain
    )
    r4 = run_lease_lifecycle(
        session_id="s", step_id="S4", tool_name="phantom", registry=reg, chain=chain
    )

    chain.validate()  # raises if any link broken
    events = list(chain.iter_events())
    assert len(events) == 4
    assert [e["type"] for e in events] == [
        PROPOSED_EVENT_TYPE,
        DENIED_EVENT_TYPE,
        PROPOSED_EVENT_TYPE,
        DENIED_EVENT_TYPE,
    ]
    # The result.audit_event for each call mirrors what we read back.
    assert events[0]["details"]["lease_id"] == r1.lease.lease_id
    assert events[1]["details"]["lease_id"] == r2.lease.lease_id
    assert events[2]["details"]["lease_id"] == r3.lease.lease_id
    assert events[3]["details"]["lease_id"] == r4.lease.lease_id


# ─── A7 prev_hash linkage ────────────────────────────────────────────


def test_prev_hash_links_across_multiple_lifecycles(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    for step in range(1, 6):
        run_lease_lifecycle(
            session_id="s",
            step_id=f"S{step}",
            tool_name="alpha",
            registry=reg,
            chain=chain,
        )

    events = list(chain.iter_events())
    assert len(events) == 5
    assert events[0]["prev_hash"] == "0"
    for i in range(1, len(events)):
        assert events[i]["prev_hash"] == events[i - 1]["hash"]


# ─── A8 now injection forwards to mint_lease ─────────────────────────


def test_now_injection_propagates_to_lease(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = _fresh_chain(tmp_path)

    fixed = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)
    result = run_lease_lifecycle(
        session_id="s",
        step_id="S1",
        tool_name="alpha",
        registry=reg,
        chain=chain,
        now=fixed,
    )

    parsed = datetime.fromisoformat(result.lease.granted_at.replace("Z", "+00:00"))
    assert parsed == fixed
    # ttl default 600s → expires_at = fixed + 600s.
    expires = datetime.fromisoformat(result.lease.expires_at.replace("Z", "+00:00"))
    assert (expires - parsed).total_seconds() == 600
