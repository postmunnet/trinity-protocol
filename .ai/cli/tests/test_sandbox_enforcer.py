"""Phase 7 Session 7-1 — sandbox_enforcer per-axis tests."""
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
    REASON_BINARY_FORBIDDEN,
    REASON_BINARY_NOT_ALLOWED,
    REASON_HOST_NOT_ALLOWED,
    REASON_NET_DENIED,
    REASON_NO_ROOT,
    REASON_PATH_FORBIDDEN,
    REASON_PATH_OUTSIDE_ROOTS,
    REASON_PROTOCOL_NOT_ALLOWED,
    REASON_SPAWN_DISABLED,
    REASON_TOOL_FORBIDDEN,
    REASON_TOOL_NOT_ALLOWED,
    AxisDecision,
    check_fs_delete,
    check_fs_read,
    check_fs_write,
    check_net_outbound,
    check_proc_exec,
    check_proc_spawn,
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


# ─── A1 import-time safety ──────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.sandbox_enforcer")
    assert hasattr(mod, "AxisDecision")
    assert hasattr(mod, "check_fs_read")


# ─── A2 fs.read ─────────────────────────────────────────────────────


def test_fs_read_no_roots_denies() -> None:
    d = check_fs_read(_profile(), "/anywhere")
    assert d.verdict == "deny" and d.reason == REASON_NO_ROOT


def test_fs_read_under_root_allows() -> None:
    p = _profile(fs=FsCapability(read_roots=["/safe"]))
    d = check_fs_read(p, "/safe/sub/file")
    assert d.verdict == "allow" and d.axis == "fs.read"


def test_fs_read_outside_roots_denies() -> None:
    p = _profile(fs=FsCapability(read_roots=["/safe"]))
    d = check_fs_read(p, "/other/file")
    assert d.verdict == "deny" and d.reason == REASON_PATH_OUTSIDE_ROOTS


def test_fs_read_forbidden_glob_denies() -> None:
    p = _profile(
        fs=FsCapability(read_roots=["/safe"], forbidden_paths=["/safe/secret*"])
    )
    d = check_fs_read(p, "/safe/secret.txt")
    assert d.verdict == "deny" and d.reason == REASON_PATH_FORBIDDEN


def test_fs_read_root_boundary_not_prefix() -> None:
    """Ensure /safe does not allow /safe2/file (boundary check)."""
    p = _profile(fs=FsCapability(read_roots=["/safe"]))
    d = check_fs_read(p, "/safe2/file")
    assert d.verdict == "deny" and d.reason == REASON_PATH_OUTSIDE_ROOTS


# ─── A3 fs.write parallel coverage ──────────────────────────────────


def test_fs_write_separate_roots_from_read() -> None:
    p = _profile(fs=FsCapability(read_roots=["/r"], write_roots=["/w"]))
    assert check_fs_read(p, "/r/x").verdict == "allow"
    assert check_fs_read(p, "/w/x").verdict == "deny"
    assert check_fs_write(p, "/w/x").verdict == "allow"
    assert check_fs_write(p, "/r/x").verdict == "deny"


# ─── A4 fs.delete ───────────────────────────────────────────────────


def test_fs_delete_uses_delete_roots() -> None:
    p = _profile(
        fs=FsCapability(write_roots=["/w"], delete_roots=["/w/trash"])
    )
    assert check_fs_delete(p, "/w/trash/old").verdict == "allow"
    assert check_fs_delete(p, "/w/keep").verdict == "deny"


# ─── A5 net.outbound ────────────────────────────────────────────────


def test_net_outbound_denied_mode() -> None:
    d = check_net_outbound(_profile(net=NetCapability(outbound="denied")), "h", "https")
    assert d.verdict == "deny" and d.reason == REASON_NET_DENIED


def test_net_outbound_open_mode_allows_any_host() -> None:
    d = check_net_outbound(_profile(net=NetCapability(outbound="open")), "any.host", "https")
    assert d.verdict == "allow"


def test_net_outbound_allowlist_host_match() -> None:
    p = _profile(
        net=NetCapability(
            outbound="allowlist", allowlist=["api.x.com"], protocols=["https"]
        )
    )
    assert check_net_outbound(p, "api.x.com", "https").verdict == "allow"


def test_net_outbound_allowlist_host_miss() -> None:
    p = _profile(
        net=NetCapability(
            outbound="allowlist", allowlist=["api.x.com"], protocols=["https"]
        )
    )
    d = check_net_outbound(p, "evil.com", "https")
    assert d.verdict == "deny" and d.reason == REASON_HOST_NOT_ALLOWED


def test_net_outbound_allowlist_protocol_miss() -> None:
    p = _profile(
        net=NetCapability(
            outbound="allowlist", allowlist=["api.x.com"], protocols=["https"]
        )
    )
    d = check_net_outbound(p, "api.x.com", "ftp")
    assert d.verdict == "deny" and d.reason == REASON_PROTOCOL_NOT_ALLOWED


# ─── A6 proc.exec ───────────────────────────────────────────────────


def test_proc_exec_allowlist() -> None:
    p = _profile(proc=ProcCapability(allowed_binaries=["python3"]))
    assert check_proc_exec(p, "python3").verdict == "allow"
    d = check_proc_exec(p, "rm")
    assert d.verdict == "deny" and d.reason == REASON_BINARY_NOT_ALLOWED


def test_proc_exec_forbidden_overrides_allowed() -> None:
    p = _profile(
        proc=ProcCapability(allowed_binaries=["python3"], forbidden_binaries=["python3"])
    )
    d = check_proc_exec(p, "python3")
    assert d.verdict == "deny" and d.reason == REASON_BINARY_FORBIDDEN


# ─── A7 proc.spawn ──────────────────────────────────────────────────


def test_proc_spawn_disabled() -> None:
    p = _profile(proc=ProcCapability(spawn_allowed=False, allowed_binaries=["x"]))
    d = check_proc_spawn(p, "x")
    assert d.verdict == "deny" and d.reason == REASON_SPAWN_DISABLED


def test_proc_spawn_requires_exec_pass() -> None:
    p = _profile(proc=ProcCapability(spawn_allowed=True, allowed_binaries=[]))
    d = check_proc_spawn(p, "rm")
    assert d.verdict == "deny" and d.reason == REASON_BINARY_NOT_ALLOWED


def test_proc_spawn_happy() -> None:
    p = _profile(proc=ProcCapability(spawn_allowed=True, allowed_binaries=["python3"]))
    assert check_proc_spawn(p, "python3").verdict == "allow"


# ─── A8 tool.invoke ─────────────────────────────────────────────────


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
    d = AxisDecision(verdict="allow", axis="fs.read", reason="")
    with pytest.raises(Exception):
        d.verdict = "deny"  # type: ignore[misc]
