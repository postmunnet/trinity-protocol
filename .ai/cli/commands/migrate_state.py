"""`ai migrate-state` — move legacy sibling state out of $HOME into central_root.

Dry-run by default (shows the plan, touches nothing). --apply copies legacy ->
central_root (keeps legacy). --cleanup removes legacy that has been copied.
Central_root has a default (~/.trinity-central) so this never errors on an
unconfigured runtime — unlike the old runtime-root behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.migrate_state import build_plan, apply_plan, cleanup_plan

app = typer.Typer(help="Move legacy sibling state from $HOME into central_root.")
console = Console()


@app.callback(invoke_without_command=True)
def migrate_state(
    apply: bool = typer.Option(False, "--apply", help="Copy legacy state into central_root (keeps legacy)."),
    cleanup: bool = typer.Option(False, "--cleanup", help="Remove legacy paths that have already been copied."),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output."),
    home: Optional[Path] = typer.Option(None, "--home", help="Override home dir (mostly for testing)."),
) -> None:
    report = build_plan(home=home)

    if cleanup:
        cleanup_plan(report)
    elif apply:
        apply_plan(report)
    # else: dry-run (report stays mode='dry-run')

    if json_out:
        console.print_json(json.dumps({"ok": True, **report.as_dict()}))
        return

    _render(report)


def _render(report) -> None:
    console.print(f"[bold]migrate-state[/bold] · mode=[cyan]{report.mode}[/cyan] · central={report.central_root}")
    table = Table(show_header=True, header_style="bold")
    table.add_column("sibling")
    table.add_column("legacy")
    table.add_column("→ target")
    table.add_column("status")
    for i in report.items:
        if not i.legacy_exists and i.status in ("pending", "skipped_missing"):
            continue  # don't clutter with absent legacy paths
        table.add_row(i.sibling, str(i.legacy), str(i.target), i.status)
    console.print(table)
    s = report.summary()
    console.print(f"  summary: {s}")
    if report.mode == "dry-run":
        console.print("  [dim]dry-run — nothing changed. Use --apply to copy, then --cleanup to remove legacy.[/dim]")
