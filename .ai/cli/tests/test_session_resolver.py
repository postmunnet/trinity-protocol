"""Shared session-resolver unit tests — KI-2026-05-16-001 fix.

Verifies the 5-tier search order lifted from rrr._resolve_explicit_session
into the shared core.session_resolver module.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.session_resolver import (
    SessionNotFoundError,
    resolve_explicit_session,
)


def _project(tmp_path: Path) -> Path:
    (tmp_path / ".ai" / "sessions").mkdir(parents=True)
    (tmp_path / ".ai" / "sessions" / "archive").mkdir(parents=True)
    return tmp_path


def test_resolve_by_literal_absolute_path(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    sess = proj / ".ai" / "sessions" / "0001_session-a"
    sess.mkdir()
    result = resolve_explicit_session(proj, str(sess.resolve()))
    assert result == Path(str(sess.resolve()))


def test_resolve_by_relative_id_under_sessions(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    sess = proj / ".ai" / "sessions" / "0001_session-b"
    sess.mkdir()
    result = resolve_explicit_session(proj, "0001_session-b")
    assert result == sess


def test_resolve_by_id_archive_suffix(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    archived = proj / ".ai" / "sessions" / "0002_archived.archive"
    archived.mkdir()
    result = resolve_explicit_session(proj, "0002_archived")
    assert result == archived


def test_resolve_by_id_in_archive_subdir(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    archived = proj / ".ai" / "sessions" / "archive" / "0003_old"
    archived.mkdir()
    result = resolve_explicit_session(proj, "0003_old")
    assert result == archived


def test_resolve_by_id_in_archive_subdir_with_suffix(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    archived = proj / ".ai" / "sessions" / "archive" / "0004_legacy.archive"
    archived.mkdir()
    result = resolve_explicit_session(proj, "0004_legacy")
    assert result == archived


def test_resolve_raises_session_not_found(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    with pytest.raises(SessionNotFoundError) as exc:
        resolve_explicit_session(proj, "nonexistent")
    assert exc.value.ident == "nonexistent"
    assert len(exc.value.candidates) == 5  # all 5 tiers searched


def test_resolve_prefers_first_match(tmp_path: Path) -> None:
    """When the id matches in BOTH .ai/sessions/<id> AND .ai/sessions/<id>.archive,
    the live (non-archive) path wins."""
    proj = _project(tmp_path)
    live = proj / ".ai" / "sessions" / "0005_dup"
    live.mkdir()
    archived = proj / ".ai" / "sessions" / "0005_dup.archive"
    archived.mkdir()
    result = resolve_explicit_session(proj, "0005_dup")
    assert result == live  # tier 2 beats tier 3
