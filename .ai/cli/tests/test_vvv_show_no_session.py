"""`ai vvv --show` — true prompt mode (2026-06-12).

The 5 questions are static text; rendering them must not require SSOT,
an active session, or touch the audit chain. This was finding #4 of the
2026-06-12 E2E audit: `_run` resolved the session BEFORE the show_only
branch, so `vvv --show` exited 2 from any cwd without a session.
"""
from __future__ import annotations

from pathlib import Path

from cli.commands.vvv import _run


def test_show_works_without_ssot_or_session(tmp_path: Path, monkeypatch, capsys) -> None:
    # Bare tmp dir: no .ai/, no ssot.yaml, no session, nothing.
    monkeypatch.chdir(tmp_path)
    _run([], None, True)  # show_only=True — must not raise

    out = capsys.readouterr().out
    for marker in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        assert marker in out, f"{marker} missing from --show output"


def test_show_writes_nothing(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    _run([], None, True)
    capsys.readouterr()
    leftovers = [p for p in tmp_path.rglob("*")]
    assert leftovers == [], f"--show must not create files, found: {leftovers}"
