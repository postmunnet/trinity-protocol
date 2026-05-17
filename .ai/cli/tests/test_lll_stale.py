"""Tests for `ai lll` stale-session detection.

`_stale_sessions` scans `sessions/` root and returns directory
names that are neither the current session nor reserved subdirs
(`active`, `archive`). These are "ghost" folders typically left
by retroactive rrr or aborted sessions.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from cli.commands.lll import _stale_sessions
from cli.core.ssot import SSOTLoader


def _make_project(tmp: Path) -> Path:
    proj = tmp / "proj"
    (proj / ".ai" / "audit").mkdir(parents=True)
    (proj / ".ai" / "state").mkdir(parents=True)
    (proj / ".ai" / "sessions" / "active").mkdir(parents=True)
    (proj / ".ai" / "sessions" / "archive").mkdir(parents=True)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({
            "version": "1.0",
            "paths": {"state": "${ai_root}/state"},
        })
    )
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({
            "version": "1.0",
            "current_session": None,
            "last_event_hash": None,
        })
    )
    return proj


def test_stale_sessions_empty_when_only_reserved_subdirs(tmp_path: Path):
    proj = _make_project(tmp_path)
    config = SSOTLoader(proj).load()
    assert _stale_sessions(config) == []


def test_stale_sessions_finds_ghost_folders(tmp_path: Path):
    proj = _make_project(tmp_path)
    (proj / ".ai" / "sessions" / "0009_ghost-a").mkdir()
    (proj / ".ai" / "sessions" / "0010_ghost-b").mkdir()
    config = SSOTLoader(proj).load()
    out = _stale_sessions(config)
    assert "0009_ghost-a" in out
    assert "0010_ghost-b" in out
    # Sorted, deterministic
    assert out == sorted(out)


def test_stale_sessions_excludes_current(tmp_path: Path):
    proj = _make_project(tmp_path)
    cur = proj / ".ai" / "sessions" / "0001_current-work"
    cur.mkdir()
    (proj / ".ai" / "sessions" / "0009_ghost").mkdir()
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({
            "version": "1.0",
            "current_session": str(cur),
            "last_event_hash": None,
        })
    )
    config = SSOTLoader(proj).load()
    out = _stale_sessions(config)
    assert "0001_current-work" not in out
    assert "0009_ghost" in out


def test_stale_sessions_excludes_reserved_subdirs(tmp_path: Path):
    proj = _make_project(tmp_path)
    (proj / ".ai" / "sessions" / "0009_ghost").mkdir()
    config = SSOTLoader(proj).load()
    out = _stale_sessions(config)
    assert "active" not in out
    assert "archive" not in out
    assert out == ["0009_ghost"]


def test_stale_sessions_ignores_files_at_root(tmp_path: Path):
    proj = _make_project(tmp_path)
    (proj / ".ai" / "sessions" / ".gitkeep").write_text("")
    (proj / ".ai" / "sessions" / "0009_ghost").mkdir()
    config = SSOTLoader(proj).load()
    out = _stale_sessions(config)
    assert ".gitkeep" not in out
    assert out == ["0009_ghost"]
