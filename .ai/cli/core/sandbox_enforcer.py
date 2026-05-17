"""Sandbox enforcer — Phase 7 Session 7-1 runtime axis checks.

Pure functions that evaluate a proposed action against a `SandboxProfile`
(declared in `sandbox_contract.py`) and return a fail-closed
`AxisDecision`.

Article XX: no I/O at import, no audit emission. The caller decides
whether to emit `sandbox.deny` / proceed.

Spec anchors:
- docs/specs/TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md §2 (axes) + §3 (denial)
- .ai/schemas/sandbox_profile.schema.json
"""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from typing import Iterable

from cli.core.sandbox_contract import SandboxProfile


# Deny reason vocabulary (closed set; tests assert against these literals).
REASON_NO_ROOT = "no_root_configured"
REASON_PATH_OUTSIDE_ROOTS = "path_outside_roots"
REASON_PATH_FORBIDDEN = "path_forbidden"
REASON_NET_DENIED = "net_outbound_denied"
REASON_HOST_NOT_ALLOWED = "host_not_in_allowlist"
REASON_PROTOCOL_NOT_ALLOWED = "protocol_not_in_allowlist"
REASON_BINARY_NOT_ALLOWED = "binary_not_in_allowlist"
REASON_BINARY_FORBIDDEN = "binary_forbidden"
REASON_SPAWN_DISABLED = "spawn_not_allowed"
REASON_TOOL_NOT_ALLOWED = "tool_not_in_allowlist"
REASON_TOOL_FORBIDDEN = "tool_forbidden"


@dataclass(frozen=True)
class AxisDecision:
    """Result of one axis check. Fail-closed: only allow/deny verdicts."""

    verdict: str            # "allow" or "deny"
    axis: str               # e.g. "fs.read", "net.outbound", "proc.exec"
    reason: str             # one of REASON_* on deny; "" on allow
    detail: str = ""        # human-readable supplement


# ─────────── filesystem helpers ───────────


def _normalised(path: str) -> str:
    """Normalise a path for prefix comparison (no realpath — avoid I/O)."""
    return os.path.normpath(path)


def _under_any_root(path: str, roots: Iterable[str]) -> bool:
    p = _normalised(path)
    for root in roots:
        r = _normalised(root)
        # Ensure root boundary (e.g. "/a/b" should not match "/a/bc").
        if p == r or p.startswith(r.rstrip(os.sep) + os.sep):
            return True
    return False


def _matches_forbidden(path: str, forbidden: Iterable[str]) -> bool:
    p = _normalised(path)
    for pattern in forbidden:
        if fnmatch.fnmatchcase(p, pattern):
            return True
    return False


def _check_fs(
    profile: SandboxProfile,
    path: str,
    roots: Iterable[str],
    axis_name: str,
) -> AxisDecision:
    roots_list = list(roots)
    if not roots_list:
        return AxisDecision(
            verdict="deny",
            axis=axis_name,
            reason=REASON_NO_ROOT,
            detail=f"no {axis_name} roots configured",
        )
    if not _under_any_root(path, roots_list):
        return AxisDecision(
            verdict="deny",
            axis=axis_name,
            reason=REASON_PATH_OUTSIDE_ROOTS,
            detail=f"path {path!r} not under any of {roots_list}",
        )
    if _matches_forbidden(path, profile.fs.forbidden_paths):
        return AxisDecision(
            verdict="deny",
            axis=axis_name,
            reason=REASON_PATH_FORBIDDEN,
            detail=f"path {path!r} matches a forbidden glob",
        )
    return AxisDecision(verdict="allow", axis=axis_name, reason="")


def check_fs_read(profile: SandboxProfile, path: str) -> AxisDecision:
    return _check_fs(profile, path, profile.fs.read_roots, "fs.read")


def check_fs_write(profile: SandboxProfile, path: str) -> AxisDecision:
    return _check_fs(profile, path, profile.fs.write_roots, "fs.write")


def check_fs_delete(profile: SandboxProfile, path: str) -> AxisDecision:
    # Spec §2.1: fs.delete_roots is a strict subset of fs.write_roots.
    # The runtime check enforces the configured delete_roots only; the
    # spec invariant ("subset of write_roots") is operator-side.
    return _check_fs(profile, path, profile.fs.delete_roots, "fs.delete")


# ─────────── network ───────────


def check_net_outbound(
    profile: SandboxProfile, host: str, protocol: str
) -> AxisDecision:
    mode = profile.net.outbound
    if mode == "denied":
        return AxisDecision(
            verdict="deny",
            axis="net.outbound",
            reason=REASON_NET_DENIED,
            detail="net.outbound mode is 'denied'",
        )
    if mode == "open":
        return AxisDecision(verdict="allow", axis="net.outbound", reason="")
    # allowlist mode
    if host not in profile.net.allowlist:
        return AxisDecision(
            verdict="deny",
            axis="net.outbound",
            reason=REASON_HOST_NOT_ALLOWED,
            detail=f"host {host!r} not in allowlist {profile.net.allowlist}",
        )
    if profile.net.protocols and protocol not in profile.net.protocols:
        return AxisDecision(
            verdict="deny",
            axis="net.outbound",
            reason=REASON_PROTOCOL_NOT_ALLOWED,
            detail=f"protocol {protocol!r} not in {profile.net.protocols}",
        )
    return AxisDecision(verdict="allow", axis="net.outbound", reason="")


# ─────────── process ───────────


def check_proc_exec(profile: SandboxProfile, binary: str) -> AxisDecision:
    if binary in profile.proc.forbidden_binaries:
        return AxisDecision(
            verdict="deny",
            axis="proc.exec",
            reason=REASON_BINARY_FORBIDDEN,
            detail=f"binary {binary!r} is in forbidden_binaries",
        )
    if binary not in profile.proc.allowed_binaries:
        return AxisDecision(
            verdict="deny",
            axis="proc.exec",
            reason=REASON_BINARY_NOT_ALLOWED,
            detail=f"binary {binary!r} not in allowed_binaries",
        )
    return AxisDecision(verdict="allow", axis="proc.exec", reason="")


def check_proc_spawn(profile: SandboxProfile, binary: str) -> AxisDecision:
    if not profile.proc.spawn_allowed:
        return AxisDecision(
            verdict="deny",
            axis="proc.spawn",
            reason=REASON_SPAWN_DISABLED,
            detail="proc.spawn_allowed is False",
        )
    # spawn implies exec — re-check exec axis.
    exec_decision = check_proc_exec(profile, binary)
    if exec_decision.verdict == "deny":
        return AxisDecision(
            verdict="deny",
            axis="proc.spawn",
            reason=exec_decision.reason,
            detail=exec_decision.detail,
        )
    return AxisDecision(verdict="allow", axis="proc.spawn", reason="")


# ─────────── tool ───────────


def check_tool_invoke(profile: SandboxProfile, tool_name: str) -> AxisDecision:
    if tool_name in profile.tools.forbidden:
        return AxisDecision(
            verdict="deny",
            axis="tool.invoke",
            reason=REASON_TOOL_FORBIDDEN,
            detail=f"tool {tool_name!r} is in tools.forbidden",
        )
    if tool_name not in profile.tools.allowed:
        return AxisDecision(
            verdict="deny",
            axis="tool.invoke",
            reason=REASON_TOOL_NOT_ALLOWED,
            detail=f"tool {tool_name!r} not in tools.allowed",
        )
    return AxisDecision(verdict="allow", axis="tool.invoke", reason="")


__all__ = [
    # constants
    "REASON_NO_ROOT",
    "REASON_PATH_OUTSIDE_ROOTS",
    "REASON_PATH_FORBIDDEN",
    "REASON_NET_DENIED",
    "REASON_HOST_NOT_ALLOWED",
    "REASON_PROTOCOL_NOT_ALLOWED",
    "REASON_BINARY_NOT_ALLOWED",
    "REASON_BINARY_FORBIDDEN",
    "REASON_SPAWN_DISABLED",
    "REASON_TOOL_NOT_ALLOWED",
    "REASON_TOOL_FORBIDDEN",
    # types + functions
    "AxisDecision",
    "check_fs_read",
    "check_fs_write",
    "check_fs_delete",
    "check_net_outbound",
    "check_proc_exec",
    "check_proc_spawn",
    "check_tool_invoke",
]
