"""ai next — "what should I run next?" prompt.

Spec: Layer 3 of the Trinity UX reduction (the 5-short-codes-only
goal). Bare `ai` invokes this command, so users only need to
remember `ai` to get oriented; the kernel tells them which ritual
to run next based on the current graph state.

Output (default human-readable):

    🔍 session : <id>
    📍 state   : THINK   (vvv passed, nnn pending)
    👉 next    : ai nnn --plan-envelope <path>
    💡 why     : nnn budget-checks the plan and fires THINK→SANDBOX→DO

    💡 memory hints (top 3 for this goal):
      - r_2026-04-15_modal-fix
      - r_2026-04-20_no-frontmatter
      - r_with-broken-yaml

    Cheat sheet: ai-docs/CHEATSHEET.md
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.next_action import compute, render_one_line
from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.tools_registry import call as call_tool


app = typer.Typer(help="Print what to run next based on the current session state.")
console = Console()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    json_out: bool = typer.Option(
        False, "--json", help="Return the structured next-action as JSON"
    ),
    no_hints: bool = typer.Option(
        False, "--no-hints", help="Skip memory-cli hint lookup"
    ),
):
    """Print the next-action summary."""
    if ctx.invoked_subcommand is not None:
        return
    code = _run(json_out=json_out, no_hints=no_hints)
    raise typer.Exit(code=code)


def _run(*, json_out: bool, no_hints: bool) -> int:
    config = SSOTLoader(Path.cwd()).load()
    project_root = config.project_root

    sess_path: Optional[Path] = None
    state_mgr = StateManager(config)
    status_doc = state_mgr.load_status()
    cur = status_doc.get("current_session")
    if cur:
        p = Path(cur)
        if p.exists():
            sess_path = p

    action = compute(project_root, session_path=sess_path)

    hints = []
    if not no_hints and sess_path is not None:
        # Use the session id slug as a search query — typically encodes
        # the topic ("feat-phase2-3-memory-cli", "fix-auth", etc.).
        query = sess_path.name
        try:
            inv = call_tool(
                project_root, "memory-cli",
                f"search {json.dumps(query)} --limit=3",
                timeout_seconds=8,
            )
            if inv.ok and inv.envelope:
                data = inv.envelope.get("data") or {}
                hints = data.get("results") or []
        except Exception:
            hints = []

    if json_out:
        out = {
            "session_id": action.session_id,
            "state": action.state,
            "headline": action.headline,
            "command": action.command,
            "why": action.why,
            "terminal": action.terminal,
            "blocked": action.blocked,
            "memory_hints": [
                {"id": h.get("id"), "title": h.get("title")}
                for h in hints
            ],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    # Human-readable
    sess_line = action.session_id or "(none — `ai session new <task>`)"
    state_line = action.state or "(no session)"
    body = [
        f"[cyan]session[/cyan] : {sess_line}",
        f"[cyan]state[/cyan]   : {state_line}",
    ]
    if action.command:
        body.append(f"[cyan]next[/cyan]    : [bold]{action.command}[/bold]")
        body.append(f"[cyan]why[/cyan]     : {action.why}")
    else:
        body.append(f"[cyan]status[/cyan]  : {action.headline}")

    color = "green"
    if action.terminal:
        color = "blue"
    elif action.blocked:
        color = "yellow"

    console.print(
        Panel("\n".join(body), title="👉 ai next", border_style=color)
    )

    if hints:
        hint_lines = [
            f"  - [bold]{h.get('title') or h.get('id')}[/bold]  "
            f"[dim]({h.get('id')})[/dim]"
            for h in hints
        ]
        console.print(
            Panel(
                "\n".join(hint_lines),
                title=f"💡 {len(hints)} memory hint(s)",
                border_style="cyan",
            )
        )

    cheatsheet = project_root / "ai-docs" / "CHEATSHEET.md"
    if cheatsheet.exists():
        console.print(
            f"[dim]cheat sheet: {cheatsheet.relative_to(project_root)}[/dim]"
        )

    return 0
