"""Shared session-path resolver — KI-2026-05-16-001 fix.

Lifts `_resolve_explicit_session` from `commands/rrr.py` into a shared
helper so vvv / nnn / gogogo / rrr can all resolve a session by id or
path the same way, bypassing the global `current_session` pointer that
drifts under concurrent ritual invocation.

Search order is preserved from the original rrr implementation:
  1. literal absolute/relative path that exists
  2. .ai/sessions/<ident>
  3. .ai/sessions/<ident>.archive
  4. .ai/sessions/archive/<ident>  (legacy archive layout)
  5. .ai/sessions/archive/<ident>.archive

Raises `SessionNotFoundError` on miss — callers convert to typer.Exit(2)
plus a console message that lists the search candidates (the original
behaviour was inlined in rrr; centralised here so each ritual prints a
consistent message).

Article XX passive: pure function, no audit emission, no state mutation.
"""
from __future__ import annotations

from pathlib import Path
from typing import List


class SessionNotFoundError(RuntimeError):
    """Raised when no candidate matches the supplied id/path."""

    def __init__(self, ident: str, candidates: List[Path]) -> None:
        self.ident = ident
        self.candidates = candidates
        super().__init__(
            f"session not found: {ident!r} "
            f"(searched: {[str(c) for c in candidates]})"
        )


def _candidates(project_root: Path, ident: str) -> List[Path]:
    sessions = project_root / ".ai" / "sessions"
    return [
        Path(ident),
        sessions / ident,
        sessions / f"{ident}.archive",
        sessions / "archive" / ident,
        sessions / "archive" / f"{ident}.archive",
    ]


def resolve_explicit_session(project_root: Path, ident: str) -> Path:
    """Resolve a session by id, full path, or archive id.

    Returns the first existing candidate. Raises `SessionNotFoundError`
    if none match. Callers should catch the error and convert to a
    typer.Exit + console.print so the operator sees the searched paths.
    """
    candidates = _candidates(project_root, ident)
    for c in candidates:
        if c.exists():
            return c
    raise SessionNotFoundError(ident, candidates)


__all__ = [
    "SessionNotFoundError",
    "resolve_explicit_session",
]
