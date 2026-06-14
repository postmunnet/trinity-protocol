"""C-4 / H4+H5+H8 — close --reconcile is conservative stale-pointer recovery.

Recovers ONLY when the active session is gone AND its archive is unambiguous.
Intact session = no-op. Missing/ambiguous archive = NEEDS_HUMAN (no guessing).
Never archives.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

import cli.commands.close as close_mod


class _FakeStateMgr:
    def __init__(self):
        self.saved = None

    def save_status(self, status):
        self.saved = status


def _status(current_session: str) -> dict:
    return {
        "system": {"status": "active", "active_capsules": 1},
        "current_session": current_session,
        "last_closed": None,
    }


# ─────────── H5 — intact session is a no-op ───────────


def test_reconcile_noop_when_session_intact(tmp_path) -> None:
    session = tmp_path / "sess"
    session.mkdir()
    sm = _FakeStateMgr()
    status = _status(str(session))
    with pytest.raises(typer.Exit) as e:
        close_mod._run_reconcile(session, SimpleNamespace(project_root=tmp_path), status, sm)
    assert e.value.exit_code == 0
    assert sm.saved is None, "no-op must not mutate status"
    assert status["current_session"] == str(session)


# ─────────── H8 — ambiguous/missing archive blocks (NEEDS_HUMAN) ───────────


def test_reconcile_ambiguous_blocks(tmp_path) -> None:
    stale = tmp_path / ".ai" / "sessions" / "active" / "0001_gone"  # does not exist
    sm = _FakeStateMgr()
    status = _status(str(stale))
    with pytest.raises(typer.Exit) as e:
        close_mod._run_reconcile(stale, SimpleNamespace(project_root=tmp_path), status, sm)
    assert e.value.exit_code == 3, "no unambiguous archive must escalate NEEDS_HUMAN"
    assert sm.saved is None, "must not repair when evidence is ambiguous"


# ─────────── H4 — unambiguous stale pointer is recovered ───────────


def test_reconcile_recovers_stale_pointer(tmp_path) -> None:
    name = "0001_2026-06-14_test_feat-x"
    stale = tmp_path / ".ai" / "sessions" / "active" / name  # not created → gone
    archive = tmp_path / ".ai" / "sessions" / "archive" / (name + ".archive")
    archive.mkdir(parents=True)
    sm = _FakeStateMgr()
    status = _status(str(stale))
    with pytest.raises(typer.Exit) as e:
        close_mod._run_reconcile(stale, SimpleNamespace(project_root=tmp_path), status, sm)
    assert e.value.exit_code == 0
    assert status["current_session"] is None, "stale pointer must be cleared"
    assert status["last_closed"]["session"] == name + ".archive"
    assert sm.saved is status, "repaired status must be persisted"


def test_reconcile_does_not_archive(tmp_path) -> None:
    """Reconcile must never call archive_session (it only repairs the pointer)."""
    import inspect
    src = inspect.getsource(close_mod._run_reconcile)
    assert "archive_session" not in src
