"""ai abort — fire operator_abort (active state -> DEAD, decided_by=human).

ADR-0001 D3: a human may explicitly abort an active session to DEAD. The
transition is reasoned (``--reason`` is required) and audited. DEAD is a
terminal, irreversible state — once aborted, the session can only be sealed
with ``ai close``.

Authority: operator_abort is locked to ``decided_by='human'`` in the graph.
Running this command at the CLI is the human's explicit, present approval; the
graph schema (require_human_approval) plus the required ``--reason`` are the
audit-backed evidence of that approval. (HMAC transport for remote abort —
mirroring ddd — is a deferred follow-up.)

Mirrors the ddd command's session-resolution + fire pattern.
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from ..core.loop import Loop, TerminalStateLocked, TransitionNotFound
from ..core.session_resolver import resolve_current_session
from ..core.ssot import SSOTLoader

app = typer.Typer()
console = Console()

# States that have an operator_abort edge in the standard graph (the graph is
# the source of truth; this list is only used for the friendly error message).
_ABORTABLE = ("THINK", "SANDBOX", "DO", "VERIFIED")


def _abort(session_path: Path, project_root: Path, reason: str) -> str:
    """Fire operator_abort (active -> DEAD, decided_by=human). Returns the new
    graph state. Raises TransitionNotFound if the current state has no
    operator_abort edge, or TerminalStateLocked if the session is already in a
    terminal state (DONE/DEAD) — in both cases the session is not abortable."""
    loop = Loop(session_path, graph_name="standard", project_root=project_root)
    return loop.fire(
        "operator_abort",
        decided_by="human",
        evidence={"reason": reason, "source": "cli"},
    )


def _run(*, reason: str) -> int:
    config = SSOTLoader(Path.cwd()).load()
    session_path = resolve_current_session(config)
    cur = Loop(
        session_path, graph_name="standard", project_root=config.project_root
    ).current()
    try:
        new_state = _abort(session_path, config.project_root, reason)
    except (TransitionNotFound, TerminalStateLocked):
        console.print(
            f"[red]not abortable from {cur!r} — operator_abort is only valid "
            f"from active states ({'/'.join(_ABORTABLE)}); terminal states "
            f"(DONE/DEAD) cannot be aborted.[/red]"
        )
        return 2
    console.print(
        f"[yellow]Session aborted: {cur} -> {new_state} "
        f"(operator_abort, decided_by=human). Reason: {reason}[/yellow]\n"
        f"[dim]DEAD is terminal — seal it with `ai close`.[/dim]"
    )
    return 0


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    reason: str = typer.Option(
        ...,
        "--reason",
        help="Why the session is being aborted (required; recorded in the audit chain).",
    ),
) -> None:
    """Abort the current session: fire operator_abort -> DEAD (decided_by=human)."""
    if ctx.invoked_subcommand is not None:
        return
    raise typer.Exit(_run(reason=reason))
