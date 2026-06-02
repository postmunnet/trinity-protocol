"""Tests for `_git_pull_preflight` in `cli.commands.sss`.

The SSOT doctrine (Q4 = pull on sss only) wires `ai sss` to
auto-fetch + fast-forward pull from `origin/main` before scaffolding
a new session. The preflight is fail-soft on every error path so sss
keeps working offline / in non-git workspaces / under conflicts.

Coverage matrix (one test per guard):

  test_skip_when_env_opt_out
    TRINITY_SKIP_PULL=1 → no subprocess call, no output

  test_skip_when_not_git_repo
    cwd has no `.git/` in any ancestor → no subprocess call, no output

  test_clean_pull_already_up_to_date
    git available + repo present + fetch ok + pull says
    "Already up to date." → emits up-to-date note, no exception

  test_pull_conflict_proceeds
    fetch ok + pull --ff-only returns non-zero (conflict) → emits
    warning, function returns (no raise · sss proceeds to scaffold)

  test_fetch_offline_skips_pull
    fetch returns non-zero (offline / refused) → emits warning,
    pull is NOT called, function returns

  test_timeout_proceeds
    subprocess raises TimeoutExpired → emits timeout note, no raise

  test_git_binary_missing_skips
    subprocess raises FileNotFoundError (no git on PATH) → emits
    skipped note, no raise
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cli.commands.sss import _git_pull_preflight


# ─────────────────────────── helpers ───────────────────────────


def _fake_completed(returncode: int, stdout: str = "", stderr: str = ""):
    """Build a minimal CompletedProcess-like object."""
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


@pytest.fixture
def in_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """cwd → a temp dir that contains a `.git/` marker (no real repo
    machinery — preflight only checks existence of `.git/`)."""
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TRINITY_SKIP_PULL", raising=False)
    return tmp_path


@pytest.fixture
def not_in_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """cwd → a temp dir with no `.git/` anywhere up the tree.

    We chdir into a fresh subdir of a /tmp ancestor that we control;
    the existing test runner's repo `.git/` could otherwise leak in via
    parent walk, so we deliberately use the tmp_path root."""
    sub = tmp_path / "no_git" / "sub"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    monkeypatch.delenv("TRINITY_SKIP_PULL", raising=False)
    return sub


# ─────────────────────────── tests ───────────────────────────


def test_skip_when_env_opt_out(
    in_git_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    monkeypatch.setenv("TRINITY_SKIP_PULL", "1")
    with patch("subprocess.run") as run:
        _git_pull_preflight()
    run.assert_not_called()
    err = capsys.readouterr().err
    assert err == "", f"expected no stderr output, got: {err!r}"


def test_skip_when_not_git_repo(not_in_git_repo: Path, capsys):
    # Sanity: confirm fixture really put us outside any .git ancestor.
    cwd = Path.cwd()
    assert not any((p / ".git").exists() for p in [cwd, *cwd.parents])

    with patch("subprocess.run") as run:
        _git_pull_preflight()
    run.assert_not_called()
    err = capsys.readouterr().err
    assert err == "", f"expected no stderr output, got: {err!r}"


def test_clean_pull_already_up_to_date(in_git_repo: Path, capsys):
    fake_fetch = _fake_completed(0, stdout="", stderr="")
    fake_pull = _fake_completed(
        0, stdout="Already up to date.\n", stderr=""
    )
    with patch(
        "subprocess.run", side_effect=[fake_fetch, fake_pull]
    ) as run:
        _git_pull_preflight()
    assert run.call_count == 2
    err = capsys.readouterr().err
    assert "already up to date" in err.lower()


def test_pull_fast_forwarded(in_git_repo: Path, capsys):
    fake_fetch = _fake_completed(0)
    fake_pull = _fake_completed(
        0,
        stdout=(
            "Updating ad8ba6f..88b5957\n"
            "Fast-forward\n"
            " docs/quickstart.md | 2 +-\n"
            " 1 file changed, 1 insertion(+), 1 deletion(-)\n"
        ),
    )
    with patch("subprocess.run", side_effect=[fake_fetch, fake_pull]):
        _git_pull_preflight()
    err = capsys.readouterr().err
    assert "pulled origin/main" in err
    # last line of stdout should appear (truncated to 200 chars max)
    assert "insertion" in err or "deletion" in err


def test_pull_conflict_proceeds(in_git_repo: Path, capsys):
    fake_fetch = _fake_completed(0)
    fake_pull = _fake_completed(
        1, stderr="fatal: Not possible to fast-forward, aborting.\n"
    )
    # Must not raise; function returns silently after warning
    with patch("subprocess.run", side_effect=[fake_fetch, fake_pull]):
        _git_pull_preflight()
    err = capsys.readouterr().err
    assert "ff-only failed" in err
    assert "proceeding" in err


def test_fetch_offline_skips_pull(in_git_repo: Path, capsys):
    fake_fetch = _fake_completed(
        128,
        stderr="fatal: unable to access 'https://...': Could not resolve host\n",
    )
    with patch("subprocess.run", side_effect=[fake_fetch]) as run:
        _git_pull_preflight()
    # Only fetch should have been called; pull is skipped.
    assert run.call_count == 1
    err = capsys.readouterr().err
    assert "fetch skipped" in err


def test_timeout_proceeds(in_git_repo: Path, capsys):
    def boom(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=5)

    with patch("subprocess.run", side_effect=boom):
        _git_pull_preflight()
    err = capsys.readouterr().err
    assert "timeout" in err
    assert "proceeding" in err


def test_git_binary_missing_skips(in_git_repo: Path, capsys):
    def boom(*args, **kwargs):
        raise FileNotFoundError("No such file or directory: 'git'")

    with patch("subprocess.run", side_effect=boom):
        _git_pull_preflight()
    err = capsys.readouterr().err
    assert "binary missing" in err.lower()
