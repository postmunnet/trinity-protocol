"""Tests for `ai rrr --retroactive` auto-archive guards.

Covers `_is_archivable` — the safety check that decides whether
retroactive rrr is allowed to move a session into the archive dir.

Refusal cases:
  - session is the kernel's current_session (user may still be on it)
  - session has a `.state/LOCK` file
  - session is already inside the archive dir
  - session path does not exist

Pass case:
  - session is a non-current sibling in sessions/ root
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from cli.commands.rrr import _is_archivable
from cli.core.session_archive import archive_session
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


def _make_session(proj: Path, name: str) -> Path:
    sess = proj / ".ai" / "sessions" / name
    (sess / ".state").mkdir(parents=True)
    (sess / "THINK").mkdir(parents=True)
    (sess / "THINK" / "01_PROMPT.md").write_text("ghost")
    return sess


# ─────────── _is_archivable ───────────


def test_is_archivable_true_for_stale_sibling(tmp_path: Path):
    proj = _make_project(tmp_path)
    sess = _make_session(proj, "0009_ghost")
    config = SSOTLoader(proj).load()
    assert _is_archivable(sess, proj, config) is True


def test_is_archivable_false_when_session_is_current(tmp_path: Path):
    proj = _make_project(tmp_path)
    sess = _make_session(proj, "0001_active")
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({
            "version": "1.0",
            "current_session": str(sess),
            "last_event_hash": None,
        })
    )
    config = SSOTLoader(proj).load()
    assert _is_archivable(sess, proj, config) is False


def test_is_archivable_false_when_lock_present(tmp_path: Path):
    proj = _make_project(tmp_path)
    sess = _make_session(proj, "0009_locked")
    (sess / ".state" / "LOCK").write_text("held")
    config = SSOTLoader(proj).load()
    assert _is_archivable(sess, proj, config) is False


def test_is_archivable_false_when_already_archived(tmp_path: Path):
    proj = _make_project(tmp_path)
    sess = _make_session(proj, "0009_ghost")
    config = SSOTLoader(proj).load()
    archived = archive_session(sess, config)
    assert _is_archivable(archived, proj, config) is False


def test_is_archivable_false_when_path_missing(tmp_path: Path):
    proj = _make_project(tmp_path)
    config = SSOTLoader(proj).load()
    sess = proj / ".ai" / "sessions" / "ghost-that-doesnt-exist"
    assert _is_archivable(sess, proj, config) is False


# ─────────── archive_session helper ───────────


def test_archive_session_moves_into_archive_dir(tmp_path: Path):
    proj = _make_project(tmp_path)
    sess = _make_session(proj, "0009_ghost")
    config = SSOTLoader(proj).load()
    archived = archive_session(sess, config)
    assert archived.name == "0009_ghost.archive"
    assert archived.parent.name == "archive"
    assert not sess.exists()
    assert archived.exists()
    assert (archived / "THINK" / "01_PROMPT.md").read_text() == "ghost"


def test_archive_session_overwrites_existing_archive(tmp_path: Path):
    proj = _make_project(tmp_path)
    sess1 = _make_session(proj, "0009_ghost")
    config = SSOTLoader(proj).load()
    archive_session(sess1, config)

    sess2 = _make_session(proj, "0009_ghost")
    (sess2 / "THINK" / "01_PROMPT.md").write_text("v2")
    archived = archive_session(sess2, config)
    assert (archived / "THINK" / "01_PROMPT.md").read_text() == "v2"
