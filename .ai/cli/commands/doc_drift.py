"""ai doc-drift — read-only doc-coupling drift check.

Reports which doc-coupling rules a session's changes have triggered and which
required docs were NOT updated (block/warn by severity), plus changelog gaps.
READ-ONLY: never mutates state, never fires a transition, never appends a
state-changing audit event. The enforcing gate lives in `rrr`.
"""
from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core import doc_coupling as dc
from ..core.ssot import SSOTLoader

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    json_out: bool = typer.Option(False, "--json", help="Emit the report as JSON"),
    session: Optional[str] = typer.Option(
        None, "--session", help="Session id or path (defaults to current_session)"
    ),
):
    """Check doc-coupling drift for the active session (read-only)."""
    if ctx.invoked_subcommand is not None:
        return
    raise typer.Exit(code=_run(json_out, session))


def _resolve_session(config, session_override: Optional[str]) -> Optional[Path]:
    project_root = config.project_root
    if session_override:
        from ..core.session_resolver import (
            SessionNotFoundError,
            resolve_explicit_session,
        )
        try:
            return resolve_explicit_session(project_root, session_override)
        except SessionNotFoundError:
            return None
    from ..core.session_resolver import resolve_current_session
    try:
        return resolve_current_session(config)
    except Exception:
        return None


def report_to_dict(report: dc.DocCouplingReport) -> dict:
    return {
        "verdict": report.verdict,
        "skipped": report.skipped,
        "changed": report.changed,
        "findings": [
            {
                "coupling_id": f.coupling_id,
                "severity": f.severity,
                "kind": f.kind,
                "missing": f.missing,
                "reason": f.reason,
                "route": f.route,
            }
            for f in report.findings
        ],
    }


def _run(json_out: bool, session_override: Optional[str]) -> int:
    config = SSOTLoader(Path.cwd()).load()
    project_root = config.project_root
    session_path = _resolve_session(config, session_override)

    if session_path is None:
        if json_out:
            console.print_json(
                _json.dumps({"verdict": "no_session", "skipped": True, "findings": []})
            )
        else:
            console.print("[yellow]no active session — doc-drift needs a session baseline[/yellow]")
        return 0

    state_dir = session_path / ".state"
    report = dc.check(project_root, state_dir, session_path.name)

    if json_out:
        console.print_json(_json.dumps(report_to_dict(report)))
        return 0

    if report.skipped:
        console.print("[dim]doc-coupling: no manifest (.ai/policies/doc_coupling.yaml) — skipped[/dim]")
        return 0

    icon = {"block": "❌", "warn": "⚠", "clean": "✅"}.get(report.verdict, "•")
    lines = [f"verdict: [bold]{report.verdict}[/bold] {icon}"]
    if report.blocking:
        lines.append("\n[red]Blocking[/red] (severity:block — would block rrr):")
        for f in report.blocking:
            lines.append(f"  • [bold]{f.coupling_id}[/bold] · {f.kind}: {', '.join(f.missing)}")
            lines.append(f"      {f.reason}\n      route: {f.route}")
    if report.warnings:
        lines.append("\n[yellow]Warnings[/yellow] (severity:warn — allowed + audited):")
        for f in report.warnings:
            lines.append(f"  • [bold]{f.coupling_id}[/bold] · {f.kind}: {', '.join(f.missing)}")
    if not report.findings:
        lines.append("\nno coupled doc left un-updated · changelogs fresh")
    console.print(
        Panel("\n".join(lines), title="🔗 doc-drift", border_style="cyan")
    )
    return 0
