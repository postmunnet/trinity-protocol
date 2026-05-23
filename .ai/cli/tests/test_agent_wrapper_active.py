"""Tests for `.ai/cli/agent` wrapper `--session-path active` resolution."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / ".ai" / "cli" / "agent"
STATUS_JSON = REPO_ROOT / ".ai" / "state" / "status.json"


def _read_current_session() -> str:
    return json.loads(STATUS_JSON.read_text())["current_session"]


def test_wrapper_exists_and_executable() -> None:
    assert WRAPPER.is_file()
    assert os.access(WRAPPER, os.X_OK)


def test_help_mentions_active_keyword() -> None:
    proc = subprocess.run(
        ["bash", str(WRAPPER), "--help"], capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "active" in proc.stdout
    assert "current_session" in proc.stdout


def test_active_resolves_to_current_session(tmp_path: Path) -> None:
    """Use clarification_helper --help via the wrapper: passing
    --session-path active should reach the python module (which prints
    the help banner). If resolution were broken, the wrapper would exit
    78 before reaching python.
    """
    current = _read_current_session()
    assert current  # precondition: a session must be open for this test
    proc = subprocess.run(
        ["bash", str(WRAPPER), "clarification_helper", "draft",
         "--session-path", "active", "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    # Help banner emitted by the python module; non-zero exit on help is fine
    # for argparse (it exits with 0). What matters: wrapper did NOT fail with 78.
    assert proc.returncode != 78, (
        f"wrapper exit 78 means active-resolution failed.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )


def test_active_fails_cleanly_when_status_missing(tmp_path: Path, monkeypatch) -> None:
    """If .ai/state/status.json is missing, wrapper exits 78 with a message
    on stderr — not a confusing python traceback.
    """
    # Stage a fake repo with no status.json
    fake_repo = tmp_path / "fake_repo"
    (fake_repo / ".ai" / "cli" / "agents" / "dummy").mkdir(parents=True)
    # Mirror the wrapper into the fake repo
    wrapper_copy = fake_repo / ".ai" / "cli" / "agent"
    wrapper_copy.write_text(WRAPPER.read_text())
    wrapper_copy.chmod(0o755)
    # Create a dummy agent with __main__.py so the wrapper passes its existence check
    (fake_repo / ".ai" / "cli" / "agents" / "dummy" / "__main__.py").write_text(
        "print('dummy')\n"
    )

    proc = subprocess.run(
        ["bash", str(wrapper_copy), "dummy", "--session-path", "active"],
        capture_output=True,
        text=True,
        cwd=str(fake_repo),
    )
    assert proc.returncode == 78
    assert "failed to resolve" in proc.stderr or "active" in proc.stderr


def test_non_active_session_path_passes_through(tmp_path: Path) -> None:
    """A literal session path (not 'active') is forwarded as-is."""
    current = _read_current_session()
    proc = subprocess.run(
        ["bash", str(WRAPPER), "clarification_helper", "draft",
         "--session-path", current, "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode != 78
