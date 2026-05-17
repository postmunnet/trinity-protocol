"""Tool subprocess dispatcher — Phase 6 Session G.

Executes a registry-declared tool **after** the guard (Session B) has
authorised it and the emitter (Session C) has appended a
`tool.invocation_proposed` row. The dispatcher emits the per-execution
chain rows from `executor.ALLOWED_AUDIT_EVENT_TYPES`:

  tool.invocation.started   — pre-exec
  tool.invocation.completed — exit 0
  tool.invocation.failed    — exit != 0 (non-timeout)
  tool.invocation.timeout   — subprocess.TimeoutExpired

Pure dispatch: no policy decision. Caller is responsible for ensuring
the proposed envelope was emitted first (`emit_decision`).

Spec anchors:
- docs/specs/TRINITY_AUDIT_EVENT_SPEC_V1.md §3 (Tool events)
- docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md §2-§3
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §6 (Executor outputs)
"""
from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from cli.core.audit import AuditChain
from cli.core.executor import ALLOWED_AUDIT_EVENT_TYPES, ExecutionLease
from cli.core.tool_registry import ToolCapabilityRecord


STARTED_EVENT_TYPE = "tool.invocation.started"
COMPLETED_EVENT_TYPE = "tool.invocation.completed"
FAILED_EVENT_TYPE = "tool.invocation.failed"
TIMEOUT_EVENT_TYPE = "tool.invocation.timeout"

# Cross-check at import: these event types MUST exist in the executor
# contract's audit-event closure (Article XVI).
for _et in (
    STARTED_EVENT_TYPE,
    COMPLETED_EVENT_TYPE,
    FAILED_EVENT_TYPE,
    TIMEOUT_EVENT_TYPE,
):
    assert _et in ALLOWED_AUDIT_EVENT_TYPES, (
        f"dispatcher event_type {_et!r} not in executor contract"
    )

TIMEOUT_EXIT_CODE = -1


@dataclass(frozen=True)
class DispatchResult:
    tool_name: str
    lease_id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    audit_events: List[Dict[str, Any]] = field(default_factory=list)


def _substitute_placeholders(s: str, project_root: Path) -> str:
    """Replace ${project_root} with the resolved absolute path."""
    return s.replace("${project_root}", str(project_root))


def _tokenise_bin(bin_str: str, project_root: Path) -> List[str]:
    return shlex.split(_substitute_placeholders(bin_str, project_root))


def dispatch_tool(
    *,
    lease: ExecutionLease,
    record: ToolCapabilityRecord,
    args: List[str],
    chain: AuditChain,
    project_root: Path,
    timeout_seconds: int = 60,
    env: Optional[Dict[str, str]] = None,
    argv_transform: Optional[Callable[[List[str]], List[str]]] = None,
) -> DispatchResult:
    """Subprocess-exec the tool's bin with args; emit lifecycle audit rows.

    Caller MUST have already emitted `tool.invocation_proposed` (the
    happy-path output of `emit_decision` from Session C). This function
    handles only the exec step + start/completion audit rows.

    `argv_transform` is an optional pure function applied to the
    resolved argv (record.bin tokens + args) BEFORE subprocess.run.
    Used by the sandbox runtime hook to prepend `sandbox-exec -f <p>`
    for OS-level fs enforcement. Defaults to None — back-compat: callers
    that omit it get byte-identical behaviour to the pre-hook dispatch.
    """
    cmd = _tokenise_bin(record.bin, project_root) + list(args)
    if argv_transform is not None:
        cmd = argv_transform(cmd)
    audit_events: List[Dict[str, Any]] = []

    started_event = chain.append(
        STARTED_EVENT_TYPE,
        {
            "lease_id": lease.lease_id,
            "session_id": lease.session_id,
            "step_id": lease.step_id,
            "tool_name": record.name,
            "argv": cmd,
            "actor": "executor",
            "decided_by": "kernel",
        },
    )
    audit_events.append(started_event)

    start_t = time.monotonic()
    timed_out = False
    exit_code = 0
    stdout = ""
    stderr = ""

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env if env is not None else os.environ.copy(),
        )
        exit_code = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = TIMEOUT_EXIT_CODE
        stdout = _coerce_text(exc.stdout)
        stderr = _coerce_text(exc.stderr)
    except (OSError, ValueError) as exc:
        timed_out = False
        exit_code = TIMEOUT_EXIT_CODE
        stderr = str(exc)

    duration = time.monotonic() - start_t

    if timed_out:
        event_type = TIMEOUT_EVENT_TYPE
    elif exit_code == 0:
        event_type = COMPLETED_EVENT_TYPE
    else:
        event_type = FAILED_EVENT_TYPE

    finish_event = chain.append(
        event_type,
        {
            "lease_id": lease.lease_id,
            "session_id": lease.session_id,
            "step_id": lease.step_id,
            "tool_name": record.name,
            "exit_code": exit_code,
            "duration_seconds": round(duration, 3),
            "actor": "executor",
            "decided_by": "kernel",
        },
    )
    audit_events.append(finish_event)

    return DispatchResult(
        tool_name=record.name,
        lease_id=lease.lease_id,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=duration,
        timed_out=timed_out,
        audit_events=audit_events,
    )


def _coerce_text(maybe_bytes) -> str:
    if maybe_bytes is None:
        return ""
    if isinstance(maybe_bytes, (bytes, bytearray)):
        return maybe_bytes.decode("utf-8", errors="replace")
    return str(maybe_bytes)


__all__ = [
    "STARTED_EVENT_TYPE",
    "COMPLETED_EVENT_TYPE",
    "FAILED_EVENT_TYPE",
    "TIMEOUT_EVENT_TYPE",
    "TIMEOUT_EXIT_CODE",
    "DispatchResult",
    "dispatch_tool",
]
