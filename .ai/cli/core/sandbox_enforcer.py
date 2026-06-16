"""Sandbox enforcer — the deterministic tool-axis check.

`check_tool_invoke` evaluates a tool name against a `SandboxProfile`
(declared in `sandbox_contract.py`) and returns a fail-closed
`AxisDecision`. It is wired into `sandbox_gate.run_sandbox_gated_lifecycle`
(and thus gogogo), and is the portable tool-axis gate that works regardless
of OS sandbox availability.

Article XX: no I/O at import, no audit emission. The caller decides whether to
emit `sandbox.deny` / proceed.

History: this module previously also held pure filesystem / network / process
axis checkers. They were never wired — arbitrary tool dispatch does not know the
paths/binaries a tool will touch at runtime, so there was no call site — and
real enforcement of those axes is the macOS `sandbox-exec` runtime hook
(`sandbox_runtime.py`), with fail-closed refusal when a profile declares those
axes and sandbox-exec is unavailable. The dead checkers were removed (T4-AUDIT
follow-up 2) to avoid implying that this module enforces them; see
docs/audits/policy-sandbox-classification.md. Git history preserves them if a
known-path call site (e.g. `ai sandbox apply`) ever needs them.

Spec anchor: docs/specs/TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md §2 (axes).
"""
from __future__ import annotations

from dataclasses import dataclass

from cli.core.sandbox_contract import SandboxProfile


# Deny reason vocabulary for the tool axis (closed set; tests assert literals).
REASON_TOOL_NOT_ALLOWED = "tool_not_in_allowlist"
REASON_TOOL_FORBIDDEN = "tool_forbidden"


@dataclass(frozen=True)
class AxisDecision:
    """Result of one axis check. Fail-closed: only allow/deny verdicts."""

    verdict: str            # "allow" or "deny"
    axis: str               # e.g. "tool.invoke"
    reason: str             # one of REASON_* on deny; "" on allow
    detail: str = ""        # human-readable supplement


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
    "REASON_TOOL_NOT_ALLOWED",
    "REASON_TOOL_FORBIDDEN",
    "AxisDecision",
    "check_tool_invoke",
]
