"""Phase 7 Session 7-2 — sandbox_gate composition tests."""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from cli.core.audit import AuditChain
from cli.core.sandbox_contract import (
    FsCapability,
    NetCapability,
    ProcCapability,
    SandboxProfile,
    ToolsCapability,
)
from cli.core.sandbox_enforcer import REASON_TOOL_NOT_ALLOWED
from cli.core.sandbox_gate import (
    GatedResult,
    SANDBOX_DENY_EVENT_TYPE,
    run_sandbox_gated_lifecycle,
)
from cli.core.tool_invocation_guard import (
    DENIED_EVENT_TYPE,
    PROPOSED_EVENT_TYPE,
)
from cli.core.tool_registry import load_registry


def _full_tool_entry(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "description": f"{name} description",
        "path": f"/fake/{name}",
        "bin": f"/fake/{name}/bin",
        "schema_version": "1",
        "contract_version": "1.0",
        "capabilities": ["x"],
        "policy_default": "safe",
    }


def _full_cap_entry(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "required_capabilities": ["fs.read"],
        "optional_capabilities": [],
        "default_tier_requirement": "WARM",
        "notes": "",
    }


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


def _profile(allowed=None, forbidden=None) -> SandboxProfile:
    return SandboxProfile(
        id="p_test",
        version="1.0",
        fs=FsCapability(),
        net=NetCapability(),
        proc=ProcCapability(),
        tools=ToolsCapability(allowed=allowed or [], forbidden=forbidden or []),
    )


# ─── A1 import safety ────────────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.sandbox_gate")
    assert hasattr(mod, "run_sandbox_gated_lifecycle")
    assert hasattr(mod, "GatedResult")


# ─── A2 no profile → back-compat ─────────────────────────────────────


def test_no_profile_is_backcompat_lifecycle(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")

    result = run_sandbox_gated_lifecycle(
        session_id="s",
        step_id="S1",
        tool_name="alpha",
        registry=reg,
        chain=chain,
        profile=None,
    )

    assert isinstance(result, GatedResult)
    assert result.sandbox_decision is None
    assert result.sandbox_audit_event is None
    assert result.lifecycle is not None
    assert result.lifecycle.success is True
    assert result.success is True
    types = [e["type"] for e in chain.iter_events()]
    assert PROPOSED_EVENT_TYPE in types
    assert SANDBOX_DENY_EVENT_TYPE not in types


# ─── A3 profile allows tool ──────────────────────────────────────────


def test_profile_allows_tool_runs_lifecycle(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")

    result = run_sandbox_gated_lifecycle(
        session_id="s",
        step_id="S1",
        tool_name="alpha",
        registry=reg,
        chain=chain,
        profile=_profile(allowed=["alpha"]),
    )

    assert result.sandbox_decision is not None
    assert result.sandbox_decision.verdict == "allow"
    assert result.sandbox_audit_event is None
    assert result.lifecycle is not None and result.lifecycle.success is True
    types = [e["type"] for e in chain.iter_events()]
    assert PROPOSED_EVENT_TYPE in types
    assert SANDBOX_DENY_EVENT_TYPE not in types


# ─── A4 profile denies tool → short-circuit ──────────────────────────


def test_profile_denies_tool_short_circuits(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")

    result = run_sandbox_gated_lifecycle(
        session_id="s",
        step_id="S1",
        tool_name="alpha",
        registry=reg,
        chain=chain,
        profile=_profile(allowed=[]),  # tool not in allowlist
    )

    assert result.success is False
    assert result.lifecycle is None
    assert result.sandbox_decision is not None
    assert result.sandbox_decision.verdict == "deny"
    assert result.sandbox_decision.reason == REASON_TOOL_NOT_ALLOWED
    assert result.sandbox_audit_event is not None
    assert result.sandbox_audit_event["type"] == SANDBOX_DENY_EVENT_TYPE
    types = [e["type"] for e in chain.iter_events()]
    assert SANDBOX_DENY_EVENT_TYPE in types
    assert PROPOSED_EVENT_TYPE not in types
    assert DENIED_EVENT_TYPE not in types


# ─── A5 chain integrity over mixed sequence ──────────────────────────


def test_chain_validates_after_mixed_sequence(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")

    allowed_p = _profile(allowed=["alpha"])
    denied_p = _profile(allowed=[])

    run_sandbox_gated_lifecycle(
        session_id="s", step_id="S1", tool_name="alpha",
        registry=reg, chain=chain, profile=allowed_p,
    )
    run_sandbox_gated_lifecycle(
        session_id="s", step_id="S2", tool_name="alpha",
        registry=reg, chain=chain, profile=denied_p,
    )
    run_sandbox_gated_lifecycle(
        session_id="s", step_id="S3", tool_name="alpha",
        registry=reg, chain=chain, profile=allowed_p,
    )

    chain.validate()  # raises on break
    events = list(chain.iter_events())
    assert [e["type"] for e in events] == [
        PROPOSED_EVENT_TYPE,
        SANDBOX_DENY_EVENT_TYPE,
        PROPOSED_EVENT_TYPE,
    ]


# ─── A6 deny envelope shape ──────────────────────────────────────────


def test_sandbox_deny_envelope_carries_axis_and_reason(tmp_path: Path) -> None:
    _write_pair(tmp_path, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    reg = load_registry(tmp_path)
    chain = AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")

    result = run_sandbox_gated_lifecycle(
        session_id="s", step_id="S1", tool_name="alpha",
        registry=reg, chain=chain, profile=_profile(allowed=[]),
    )
    env = result.sandbox_audit_event
    assert env is not None
    details = env["details"]
    assert details["axis"] == "tool.invoke"
    assert details["reason"] == REASON_TOOL_NOT_ALLOWED
    assert details["tool_name"] == "alpha"
    assert details["actor"] == "kernel"
    assert details["decided_by"] == "kernel"
