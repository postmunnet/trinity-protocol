"""sandbox_enforcer — the deterministic tool-axis check.

(The fs/net/proc axis checkers were removed in T4-AUDIT follow-up 2 — they were
never wired; real fs/net/proc enforcement is the sandbox_runtime OS hook. Only
check_tool_invoke / AxisDecision remain, consumed by sandbox_gate.)
"""
from __future__ import annotations

import importlib

import pytest

from cli.core.sandbox_contract import (
    FsCapability,
    NetCapability,
    ProcCapability,
    SandboxProfile,
    ToolsCapability,
)
from cli.core.sandbox_enforcer import (
    REASON_TOOL_FORBIDDEN,
    REASON_TOOL_NOT_ALLOWED,
    AxisDecision,
    check_tool_invoke,
)


def _profile(**overrides) -> SandboxProfile:
    """Build a permissive SandboxProfile with overrides per axis."""
    defaults = {
        "id": "p_test",
        "version": "1.0",
        "fs": FsCapability(),
        "net": NetCapability(),
        "proc": ProcCapability(),
        "tools": ToolsCapability(),
    }
    defaults.update(overrides)
    return SandboxProfile(**defaults)


# ─── import-time safety ─────────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.sandbox_enforcer")
    assert hasattr(mod, "AxisDecision")
    assert hasattr(mod, "check_tool_invoke")


# ─── tool.invoke ────────────────────────────────────────────────────


def test_tool_invoke_allowed() -> None:
    p = _profile(tools=ToolsCapability(allowed=["alpha"]))
    assert check_tool_invoke(p, "alpha").verdict == "allow"


def test_tool_invoke_not_in_allowlist() -> None:
    p = _profile(tools=ToolsCapability(allowed=["alpha"]))
    d = check_tool_invoke(p, "beta")
    assert d.verdict == "deny" and d.reason == REASON_TOOL_NOT_ALLOWED


def test_tool_invoke_forbidden_overrides() -> None:
    p = _profile(tools=ToolsCapability(allowed=["alpha"], forbidden=["alpha"]))
    d = check_tool_invoke(p, "alpha")
    assert d.verdict == "deny" and d.reason == REASON_TOOL_FORBIDDEN


def test_axis_decision_is_frozen() -> None:
    d = AxisDecision(verdict="allow", axis="tool.invoke", reason="")
    with pytest.raises(Exception):
        d.verdict = "deny"  # type: ignore[misc]
