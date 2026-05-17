"""ai shim — render Trinity shim adapters into vendor surfaces.

Spec: docs/specs/07_SHIM_SPEC.md, .ai/shims/<code>/SHIM.md (canonical).

Subcommands:
  - render --target=<vendor>   Render adapters for one vendor
  - render-all                  Render every vendor at once
  - list                        Print canonical shim list

Vendors: claude-code | cursor | agents | warp.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.shim_render import (
    SHORT_CODES,
    VENDORS,
    load_all_shims,
    render_all,
)
from ..core.ssot import SSOTLoader

app = typer.Typer(help="Render Trinity shim adapters for vendor harnesses.")
console = Console()


@app.command()
def render(
    target: str = typer.Option(
        ..., "--target",
        help=f"Vendor surface: one of {', '.join(VENDORS)}",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Print what would be written; don't touch disk",
    ),
):
    """Render adapters for one vendor."""
    config = SSOTLoader(Path.cwd()).load()
    if target not in VENDORS:
        console.print(
            f"[red]--target {target!r} not in {VENDORS}[/red]"
        )
        raise typer.Exit(2)
    out = render_all(config.project_root, target, dry_run=dry_run)
    table = Table(title=f"shim render → {target}", show_header=True)
    table.add_column("path", overflow="fold")
    table.add_column("bytes", justify="right")
    table.add_column("status")
    for rel, body in out.items():
        table.add_row(
            rel, str(len(body)),
            "would-write" if dry_run else "written",
        )
    console.print(table)


@app.command("render-all")
def render_all_cmd(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print what would be written"
    ),
):
    """Render adapters for every vendor."""
    config = SSOTLoader(Path.cwd()).load()
    total = 0
    for vendor in VENDORS:
        out = render_all(config.project_root, vendor, dry_run=dry_run)
        total += len(out)
        console.print(
            f"[cyan]{vendor}[/cyan] — {len(out)} file(s)"
            + (" (dry-run)" if dry_run else "")
        )
    console.print(
        Panel(
            f"rendered {total} adapter file(s) across {len(VENDORS)} vendor(s)",
            title="✅ shim render-all",
            border_style="green",
        )
    )


@app.command("list")
def list_cmd():
    """Print the 5 canonical short codes + their purpose lines."""
    config = SSOTLoader(Path.cwd()).load()
    shims_dir = config.project_root / ".ai" / "shims"
    table = Table(title="Trinity shim catalog", show_header=True)
    table.add_column("code", style="cyan")
    table.add_column("purpose")
    table.add_column("status")
    for spec in load_all_shims(shims_dir):
        table.add_row(spec.code, spec.purpose, spec.status)
    console.print(table)
