"""ai aaa — amendment-loop router + evidence-adoption KPI (Q24.10 step 5).

READ-ONLY quality overlay. Reads the active session's signals (debt,
unconfirmed goal, evidence gaps, acceptance) and prints a Verdict + Route +
Reasons so the operator knows which amendment command to go back to. It does
NOT mutate state, fire a transition, enforce, or close — and it does NOT
append a state-changing audit event (default read-only; see invariant E6).
"""
from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.aaa_analyzer import analyze
from ..core.ssot import SSOTLoader

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    json_out: bool = typer.Option(
        False, "--json", help="Emit the structured analysis as JSON"
    ),
    session: Optional[str] = typer.Option(
        None, "--session", help="Session id or path (defaults to current_session)"
    ),
):
    """Analyze the active session and route to the right amendment command."""
    if ctx.invoked_subcommand is not None:
        return
    raise typer.Exit(code=_run(json_out, session))


def _run(json_out: bool, session_override: Optional[str]) -> int:
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    project_root = config.project_root

    if session_override:
        from ..core.session_resolver import (
            SessionNotFoundError,
            resolve_explicit_session,
        )
        try:
            session_path = resolve_explicit_session(project_root, session_override)
        except SessionNotFoundError as exc:
            console.print(f"[red]session not found: {session_override}[/red]")
            return 2
    else:
        from ..core.session_resolver import resolve_current_session
        session_path = resolve_current_session(config)

    result = analyze(session_path, project_root)

    if json_out:
        console.print_json(_json.dumps(result))
        return 0

    kpi = result["kpi"]
    sc = result["kpi_scope"]
    route_line = (
        f"[bold]Route:[/bold] [cyan]ai {result['route']}[/cyan]"
        if result["route"]
        else "[bold]Route:[/bold] [green]— (clean)[/green]"
    )
    verdict_color = "green" if result["verdict"] == "clean" else "yellow"
    body = (
        f"[bold]Verdict:[/bold] [{verdict_color}]{result['verdict']}[/{verdict_color}]\n"
        f"{route_line}\n"
    )
    if result["reasons"]:
        body += "[bold]Reasons:[/bold]\n" + "\n".join(
            f"  • {r}" for r in result["reasons"]
        ) + "\n"
    body += (
        f"\n[bold]Evidence KPI[/bold] [dim](scope: {sc['level']} · "
        f"{sc['session_id']} · {sc['project']})[/dim]\n"
        f"  evidence_command_adoption_rate: {kpi['evidence_command_adoption_rate']}\n"
        f"  structural_pass_rate: {kpi['structural_pass_rate']}\n"
        f"  high_risk_without_evidence_count: {kpi['high_risk_without_evidence_count']}"
        f"  [dim](n={kpi['steps_measured']})[/dim]"
    )
    console.print(Panel(body, title="🧭 aaa — amendment router", border_style="cyan"))
    return 0
