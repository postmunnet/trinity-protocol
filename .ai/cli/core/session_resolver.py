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


class SessionsContainerError(RuntimeError):
    """Raised when a resolver would hand back the `.ai/sessions/` container
    itself instead of an individual session capsule.

    Canonical home for the sessions-container guard, shared by every
    session resolver (the 6 `_resolve_session` wrappers, the `--session`
    override path, and `recordproxy.CaptureStore`). Plugs the source of
    the orphan-`CAPTURE/`-at-sessions-root incident: if the container
    leaks out of a resolver, downstream rituals write artifacts to the
    root and `lll` mis-flags them as a stale session.
    """


def is_sessions_container(d: Path) -> bool:
    """True when `d` is the sessions container, not a session capsule.

    Container signature (defensive, not a name whitelist): a directory
    holding BOTH an `active/` and an `archive/` child — the layout only
    the `.ai/sessions/` root has. A real capsule never owns those two
    siblings. `basename == "sessions"` is the cheap secondary signal for
    the canonical path (and catches the root even before `active/` is
    scaffolded).
    """
    d = Path(d)
    if (d / "active").is_dir() and (d / "archive").is_dir():
        return True
    return d.name == "sessions"


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
            if is_sessions_container(c):
                raise SessionsContainerError(
                    f"refusing to resolve {ident!r} to the sessions "
                    f"container {c!s}; pass an individual session capsule"
                )
            return c
    raise SessionNotFoundError(ident, candidates)


def resolve_current_session(config) -> Path:
    """Resolve the active session from the `current_session` pointer.

    Single canonical replacement for the 6 duplicated `_resolve_session`
    functions across ddd/rrr/nnn/vvv/gogogo/loop. Reads the pointer,
    enforces existence, and rejects the sessions container — so a pointer
    that drifted onto `.ai/sessions/` can never be handed to a ritual.

    Prints an operator-facing message and raises `typer.Exit(2)` on every
    failure path, matching the prior inline behaviour. Imports of the CLI
    presentation layer are deferred to keep this core module import-light.
    """
    import typer
    from rich.console import Console

    from .state import StateManager

    console = Console()
    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    if not cur:
        console.print(
            "[red]No active session. Run `ai session new <task>` first.[/red]"
        )
        raise typer.Exit(2)
    p = Path(cur)
    if not p.exists():
        console.print(f"[red]Session path missing: {p}[/red]")
        raise typer.Exit(2)
    if is_sessions_container(p):
        console.print(
            f"[red]current_session points at the sessions container "
            f"{p} — not a session capsule. Re-open a session with "
            f"`ai session new <task>`.[/red]"
        )
        raise typer.Exit(2)
    return p


__all__ = [
    "SessionNotFoundError",
    "SessionsContainerError",
    "is_sessions_container",
    "resolve_explicit_session",
    "resolve_current_session",
]
