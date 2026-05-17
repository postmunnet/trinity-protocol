"""Phase 6 Session G — tool_dispatcher tests."""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

from cli.core.audit import AuditChain
from cli.core.executor import ExecutionLease
from cli.core.tool_dispatcher import (
    COMPLETED_EVENT_TYPE,
    FAILED_EVENT_TYPE,
    STARTED_EVENT_TYPE,
    TIMEOUT_EVENT_TYPE,
    TIMEOUT_EXIT_CODE,
    DispatchResult,
    dispatch_tool,
)
from cli.core.tool_registry import ToolCapabilityRecord


def _fake_lease() -> ExecutionLease:
    return ExecutionLease(
        lease_id="01HXTESTDISPATCH001",
        session_id="0001_test",
        step_id="S1",
        granted_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    )


def _fake_record(name: str, bin_str: str) -> ToolCapabilityRecord:
    return ToolCapabilityRecord(
        name=name,
        required_capabilities=("fs.read",),
        optional_capabilities=(),
        default_tier_requirement="WARM",
        notes="",
        description=f"{name} desc",
        path="/fake",
        bin=bin_str,
        schema_version="1",
        contract_version="1.0",
        declared_capabilities=("x",),
        policy_default="safe",
    )


def _fresh_chain(tmp_path: Path) -> AuditChain:
    return AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")


# ─── A1 import safety ──────────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.tool_dispatcher")
    assert hasattr(mod, "dispatch_tool")


# ─── A2 happy path ─────────────────────────────────────────────────


def test_happy_path_exec_zero_returns_completed(tmp_path: Path) -> None:
    # sh -c '<script>' <arg0> — first appended arg lands in $0 (not $1).
    record = _fake_record("alpha", "/bin/sh -c 'echo hello $0'")
    chain = _fresh_chain(tmp_path)

    result = dispatch_tool(
        lease=_fake_lease(),
        record=record,
        args=["world"],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
    )

    assert isinstance(result, DispatchResult)
    assert result.exit_code == 0
    assert result.timed_out is False
    assert "hello world" in result.stdout

    events = list(chain.iter_events())
    assert len(events) == 2
    assert events[0]["type"] == STARTED_EVENT_TYPE
    assert events[1]["type"] == COMPLETED_EVENT_TYPE
    assert events[1]["details"]["exit_code"] == 0


# ─── A3 non-zero exit ──────────────────────────────────────────────


def test_non_zero_exit_emits_failed_event(tmp_path: Path) -> None:
    record = _fake_record("alpha", "/bin/sh -c 'exit 3'")
    chain = _fresh_chain(tmp_path)

    result = dispatch_tool(
        lease=_fake_lease(),
        record=record,
        args=[],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
    )

    assert result.exit_code == 3
    assert result.timed_out is False
    events = list(chain.iter_events())
    assert events[1]["type"] == FAILED_EVENT_TYPE
    assert events[1]["details"]["exit_code"] == 3


# ─── A4 timeout ────────────────────────────────────────────────────


def test_timeout_emits_timeout_event(tmp_path: Path) -> None:
    record = _fake_record("alpha", "/bin/sh -c 'sleep 5'")
    chain = _fresh_chain(tmp_path)

    result = dispatch_tool(
        lease=_fake_lease(),
        record=record,
        args=[],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=1,
    )

    assert result.timed_out is True
    assert result.exit_code == TIMEOUT_EXIT_CODE
    events = list(chain.iter_events())
    assert events[1]["type"] == TIMEOUT_EVENT_TYPE


# ─── A5 chain validates after multi-dispatch ───────────────────────


def test_chain_validates_after_multi_dispatch(tmp_path: Path) -> None:
    record_ok = _fake_record("alpha", "/bin/sh -c 'echo ok'")
    record_fail = _fake_record("beta", "/bin/sh -c 'exit 7'")
    chain = _fresh_chain(tmp_path)

    dispatch_tool(
        lease=_fake_lease(), record=record_ok, args=[], chain=chain,
        project_root=tmp_path, timeout_seconds=5,
    )
    dispatch_tool(
        lease=_fake_lease(), record=record_fail, args=[], chain=chain,
        project_root=tmp_path, timeout_seconds=5,
    )
    dispatch_tool(
        lease=_fake_lease(), record=record_ok, args=[], chain=chain,
        project_root=tmp_path, timeout_seconds=5,
    )

    chain.validate()  # raises on broken link
    events = list(chain.iter_events())
    assert len(events) == 6  # 3 dispatches × 2 rows
    finishes = [events[1]["type"], events[3]["type"], events[5]["type"]]
    assert finishes == [COMPLETED_EVENT_TYPE, FAILED_EVENT_TYPE, COMPLETED_EVENT_TYPE]


# ─── A6 placeholder substitution ───────────────────────────────────


def test_project_root_placeholder_substitution(tmp_path: Path) -> None:
    bin_str = "/bin/sh -c 'echo ROOT=${project_root}'"
    record = _fake_record("alpha", bin_str)
    chain = _fresh_chain(tmp_path)

    result = dispatch_tool(
        lease=_fake_lease(),
        record=record,
        args=[],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
    )

    # The placeholder must be resolved before exec; the literal
    # ${project_root} should NOT survive into the argv that hits sh.
    started = list(chain.iter_events())[0]
    argv_text = " ".join(started["details"]["argv"])
    assert "${project_root}" not in argv_text
    assert str(tmp_path) in argv_text


# ─── A7 args are appended ──────────────────────────────────────────


def test_args_are_appended_positional_and_flag(tmp_path: Path) -> None:
    # sh -c '<script>' <arg0> <arg1> <arg2> — appended args are $0 $1 $2.
    record = _fake_record("alpha", "/bin/sh -c 'echo $0 $1 $2'")
    chain = _fresh_chain(tmp_path)

    result = dispatch_tool(
        lease=_fake_lease(),
        record=record,
        args=["--flag", "value", "positional"],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
    )

    assert result.exit_code == 0
    # The 3 args appended in order land as $0 $1 $2 to sh.
    assert "--flag value positional" in result.stdout


# ─── A8 env override ───────────────────────────────────────────────


def test_env_override_passes_through(tmp_path: Path) -> None:
    record = _fake_record("alpha", "/bin/sh -c 'echo $MY_VAR'")
    chain = _fresh_chain(tmp_path)

    result = dispatch_tool(
        lease=_fake_lease(),
        record=record,
        args=[],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
        env={"MY_VAR": "hello-from-env", "PATH": "/usr/bin:/bin"},
    )

    assert result.exit_code == 0
    assert "hello-from-env" in result.stdout


def test_dispatch_result_is_frozen(tmp_path: Path) -> None:
    record = _fake_record("alpha", "/bin/sh -c 'true'")
    chain = _fresh_chain(tmp_path)
    result = dispatch_tool(
        lease=_fake_lease(),
        record=record,
        args=[],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
    )
    with pytest.raises(Exception):
        result.exit_code = 99  # type: ignore[misc]
