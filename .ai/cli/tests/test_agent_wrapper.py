"""Smoke tests for `.ai/cli/agent` wrapper.

Validates:
  - Wrapper resolves AI_ROOT independently of caller cwd
  - All 6 in-house agents are invokable as `bash .ai/cli/agent <name> ...`
  - `--help` returns exit 0 for each agent (no model calls; cheap)
  - Unknown agent names exit 2 with clear stderr
  - Relative `--session-path` does NOT path-double when invoked via wrapper
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / ".ai" / "cli" / "agent"


AGENTS = [
    "clarification_helper",
    "executor_helper",
    "plan_helper",
    "presentation_synthesizer",
    "retro_writer",
    "session_bootstrap",
]


def _run(args, cwd=None, env_extra=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(WRAPPER), *args],
        cwd=str(cwd or REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_wrapper_exists_and_executable():
    assert WRAPPER.is_file(), f"wrapper not found at {WRAPPER}"
    assert os.access(WRAPPER, os.X_OK), f"wrapper not executable: {WRAPPER}"


def test_top_level_help_exit_zero():
    result = _run(["--help"])
    assert result.returncode == 0, result.stderr
    assert "Trinity agent wrapper" in result.stdout


def test_no_args_prints_usage():
    result = _run([])
    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_list_subcommand_lists_all_agents():
    result = _run(["--list"])
    assert result.returncode == 0
    listed = set(result.stdout.split())
    for agent in AGENTS:
        assert agent in listed, f"missing {agent} in --list output"


def test_unknown_agent_exits_two():
    result = _run(["fake_nonexistent_agent"])
    assert result.returncode == 2
    assert "unknown agent" in result.stderr.lower()


@pytest.mark.parametrize("agent", AGENTS)
def test_each_agent_help_from_project_root(agent):
    result = _run([agent, "--help"])
    assert result.returncode == 0, (
        f"{agent} --help failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )


@pytest.mark.parametrize("agent", AGENTS)
def test_each_agent_help_from_unrelated_cwd(agent, tmp_path):
    # Wrapper must work even if caller cwd is outside the repo.
    result = _run([agent, "--help"], cwd=tmp_path)
    assert result.returncode == 0, (
        f"{agent} --help failed from cwd={tmp_path}:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )


def test_wrapper_does_not_leak_cwd_to_caller():
    """After invoking the wrapper, a subsequent kernel call from the same
    shell context must still succeed — i.e. the wrapper's internal `cd`
    must stay in its own subprocess."""
    script = f"""
    set -e
    cd {REPO_ROOT}
    bash {WRAPPER} clarification_helper --help >/dev/null
    bash .ai/cli/ai status >/dev/null 2>&1
    """
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"kernel call after wrapper failed:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )


@pytest.mark.parametrize("agent", [
    "clarification_helper",
    "executor_helper",
    "plan_helper",
    "presentation_synthesizer",
    "retro_writer",
])
def test_relative_session_path_does_not_double(agent, tmp_path):
    """Verify the S3 fix: a relative `--session-path` passed via the
    wrapper is resolved against repo root (NOT cwd-inside-wrapper),
    so paths like `.ai/sessions/<sid>` don't become `.ai/.ai/sessions/<sid>`.

    Each agent has a different `draft` signature, so we use a path that
    deliberately doesn't exist and check the error message references
    the correctly-resolved (non-doubled) path. Run from an unrelated
    cwd to make the test robust.
    """
    # A relative path that does NOT exist anywhere.
    bogus = ".ai/sessions/zzz_test_agent_wrapper_does_not_exist_xyz"
    cmd_args = [agent, "draft", "--session-path", bogus]
    # Some agents need additional positional args; just to reach the
    # session-path validation we pass minimal extras.
    if agent == "clarification_helper":
        cmd_args.append("test task description")
    elif agent == "executor_helper":
        cmd_args.extend(["--step-id", "S1"])
    # plan_helper / presentation_synthesizer / retro_writer: no extra args needed.

    result = _run(cmd_args, cwd=tmp_path)
    # Expect non-zero exit (session path doesn't exist).
    assert result.returncode != 0
    # The error message must reference the path RESOLVED FROM REPO ROOT,
    # NOT a doubled `.ai/.ai/sessions/...` path.
    err = result.stderr + result.stdout
    expected_resolved = str(REPO_ROOT / bogus)
    doubled = str(REPO_ROOT / ".ai" / bogus)
    assert ".ai/.ai/sessions" not in err, (
        f"{agent}: path doubling detected!\nstderr={result.stderr}"
    )
    assert expected_resolved in err, (
        f"{agent}: expected resolved path {expected_resolved!r} not in error.\n"
        f"stderr={result.stderr}"
    )
