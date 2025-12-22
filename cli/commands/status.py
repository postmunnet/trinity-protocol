import typer
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from ..core.state import StateManager, SessionLocalState
from ..core.ssot import SSOTLoader

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """Show session status and next action."""
    pass

@app.command()
def show():
    """
    Show current session status and next action.

    Phase 6 Requirement: 5-second glance to know what to do next.
    """
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(2)

    # Get current session
    current_session_path = status.get("current_session")
    if not current_session_path:
        console.print(Panel(
            "[yellow]No active session[/yellow]\n\n"
            "Start a new session:\n"
            "  [cyan]ai session new \"Your Task Name\"[/cyan]",
            title="📊 Trinity Status",
            border_style="yellow"
        ))
        raise typer.Exit(0)

    session_path = Path(current_session_path)
    if not session_path.exists():
        console.print(f"[red]Session path not found: {session_path}[/red]")
        raise typer.Exit(1)

    # Load session metadata
    meta_file = session_path / "CONTROL" / "META.json"
    if not meta_file.exists():
        console.print("[red]Session metadata not found[/red]")
        raise typer.Exit(1)

    with open(meta_file, "r") as f:
        meta = json.load(f)

    # Prefer session-local state (WP2); fallback to legacy .ai/state
    sls = SessionLocalState(session_path)
    session_state = sls.current_state()
    dev_pass = sls.dev_verified()
    prod_pass = sls.prod_verified()
    verify_status = "DEV: PASS" if dev_pass else "DEV: PENDING"

    # Determine current phase and next action
    # Minimal state machine view
    current_phase = session_state
    if session_state == "INIT":
        phase_emoji = "🟡"
        next_action = "[yellow]Start editing or apply sandbox diff[/yellow]"
        next_desc = "Begin work; this moves state to EDITING"
    elif session_state == "EDITING":
        phase_emoji = "🛠️"
        next_action = "[yellow]ai verify dev[/yellow]"
        next_desc = "Run verification on DO/dev"
    elif session_state == "VERIFIED":
        phase_emoji = "✅"
        next_action = "[yellow]ai promote[/yellow]"
        next_desc = "Promote dev → prod, then verify prod"
    elif session_state == "DONE":
        phase_emoji = "🏁"
        next_action = "[yellow]No further actions[/yellow]"
        next_desc = "Session complete"
    else:
        phase_emoji = "❓"
        next_action = "[yellow]ai status[/yellow]"
        next_desc = "Unknown state; check .state files"

    # Workflow progress table
    progress_table = Table(show_header=False, box=None, padding=(0, 1))
    progress_table.add_column("Step", style="cyan")
    progress_table.add_column("Status", style="white")

    # Progress based on MVP state machine
    steps = [
        ("INIT", "🟡 INIT"),
        ("EDITING", "🛠️ EDITING"),
        ("VERIFIED", "✅ VERIFIED"),
        ("DONE", "🏁 DONE"),
    ]
    past = True
    for key, label in steps:
        if past:
            icon = "[green]✓[/green]" if key != current_phase else "[yellow]●[/yellow]"
            progress_table.add_row(label, icon)
            if key == current_phase:
                past = False
        else:
            progress_table.add_row(label, "[dim]○[/dim]")

    # Main status panel
    status_content = f"""[bold]Session:[/bold] {meta.get('name', 'Unknown')}
[bold]ID:[/bold] {meta.get('id', 'Unknown')}
[bold]Created:[/bold] {meta.get('created_at', 'Unknown')[:19]}
[bold]Phase:[/bold] {phase_emoji} {current_phase}

[bold cyan]Workflow Progress:[/bold cyan]


[bold yellow]⚡ Next Action:[/bold yellow]
   {next_action}
   {next_desc}

[bold]Paths:[/bold]
   Session: {session_path.name}
   Dev: DO/dev/
   Prod: DO/prod/
   Local State: .state/session_state.json
"""

    console.print(Panel(
        status_content,
        title="📊 Trinity Session Status",
        border_style="cyan",
        padding=(1, 2)
    ))

    # Show workflow progress table separately for correct Rich rendering
    console.print(progress_table)

    # Quick stats
    stats = Table(show_header=False, box=None)
    stats.add_column("Metric", style="dim")
    stats.add_column("Value", style="cyan")

    # Count files in dev/prod
    dev_dir = session_path / "DO" / "dev"
    prod_dir = session_path / "DO" / "prod"

    dev_files = len(list(dev_dir.rglob("*"))) if dev_dir.exists() else 0
    prod_files = len(list(prod_dir.rglob("*"))) if prod_dir.exists() else 0

    stats.add_row("Dev Files:", str(dev_files))
    stats.add_row("Prod Files:", str(prod_files))
    stats.add_row("Verify Status:", verify_status.upper())

    console.print(stats)
    console.print()

@app.command()
def path():
    """Show current session path only (for scripting)."""
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise typer.Exit(2)

    current_session_path = status.get("current_session")
    if current_session_path:
        print(current_session_path)
    else:
        raise typer.Exit(1)
