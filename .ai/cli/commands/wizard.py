"""ai wizard — interactive session scaffolder (v0).

`ai wizard new <slug> [--type=feat|fix|ops|docs|refactor] [--force]`
delegates session creation to `ai session new <slug>` and then writes a
type-specific 5-question skeleton into `THINK/01_PROMPT.md`. Operator
edits the placeholders and runs `ai vvv --answers-file=<path>` to enter
the normal Trinity ritual flow.

This is the first-session friction reducer; it doesn't pretend to know
the work. It just removes blank-page paralysis.
"""
from __future__ import annotations

import datetime
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.wizard_templates import VALID_TYPES, render

app = typer.Typer(help="Session scaffolder — pick a template + start the ritual flow")
console = Console()


@app.command()
def new(
    slug: str,
    type: str = typer.Option(
        "feat",
        "--type",
        help=f"Template type. One of: {sorted(VALID_TYPES)}",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing THINK/01_PROMPT.md if present",
    ),
):
    """Create a new Trinity session + scaffold the vvv answers skeleton.

    Example:
      ai wizard new fix-login-bug --type=fix
      ai wizard new ship-task-cli-mvp --type=feat
    """
    if type not in VALID_TYPES:
        console.print(
            f"[red]Invalid --type {type!r}. "
            f"Valid types: {sorted(VALID_TYPES)}[/red]"
        )
        raise typer.Exit(2)

    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
    except Exception as e:
        console.print(f"[red]Error loading SSOT: {e}[/red]")
        raise typer.Exit(1)

    project_root = config.project_root

    # Step 1 — create the session via `ai session new <slug>`. Tests
    # bypass this with WIZARD_SKIP_SESSION_NEW=1 + manual fixture.
    if not os.environ.get("WIZARD_SKIP_SESSION_NEW"):
        ai_bin = os.environ.get(
            "TRINITY_AI_BIN",
            str(project_root.parent / "trinity_v2" / ".ai" / "cli" / "ai"),
        )
        proc = subprocess.run(
            [ai_bin, "session", "new", slug],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            console.print(
                f"[red]ai session new failed: exit={proc.returncode}\n"
                f"{proc.stderr or proc.stdout}[/red]"
            )
            raise typer.Exit(proc.returncode or 1)

    # Step 2 — resolve the just-created session path via StateManager.
    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    if not cur:
        console.print(
            "[red]Wizard could not resolve the new session via "
            "StateManager. Try `ai status` to inspect.[/red]"
        )
        raise typer.Exit(1)
    session_path = Path(cur)
    if not session_path.exists():
        console.print(f"[red]Session path missing: {session_path}[/red]")
        raise typer.Exit(1)

    # Step 3 — write THINK/01_PROMPT.md template.
    prompt_path = session_path / "THINK" / "01_PROMPT.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    if prompt_path.exists() and not force:
        console.print(
            f"[red]{prompt_path} already exists. Pass --force to overwrite.[/red]"
        )
        raise typer.Exit(2)
    today = datetime.date.today().isoformat()
    body = render(type, slug=session_path.name, date=today)
    prompt_path.write_text(body, encoding="utf-8")

    console.print(
        Panel(
            f"session:    {session_path.name}\n"
            f"type:       {type}\n"
            f"prompt:     THINK/01_PROMPT.md (scaffolded)\n\n"
            f"👉 next: edit THINK/01_PROMPT.md, then\n"
            f"   ai vvv --answers-file={prompt_path}",
            title="✅ ai wizard new",
            border_style="green",
        )
    )
    return 0
