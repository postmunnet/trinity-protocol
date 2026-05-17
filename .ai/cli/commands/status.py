import typer
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..core.next_action import compute as compute_next, render_one_line
from ..core.project_resolver import ProjectResolutionError, resolve_current_project
from ..core.state import StateManager, SessionLocalState
from ..core.ssot import SSOTLoader

app = typer.Typer(invoke_without_command=True)
console = Console()

@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """Show session status and next action.

    Bare `ai status` is treated as `ai status show` so the ritual
    language (status) and the executable CLI agree without forcing
    users to remember the subcommand.
    """
    if ctx.invoked_subcommand is None:
        show()

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
        if _show_project_only_status(e):
            raise typer.Exit(0)
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(2)

    # Get current session
    current_session_path = status.get("current_session")
    if not current_session_path:
        project_block = _project_status_block()
        console.print(Panel(
            "[yellow]No active session[/yellow]\n\n"
            f"{project_block}"
            "Start a new session:\n"
            "  [cyan]ai session new \"Your Task Name\"[/cyan]",
            title="📊 Trinity Status",
            border_style="yellow"
        ))
        raise typer.Exit(0)

    session_path = Path(current_session_path)
    if not session_path.exists():
        project_block = _project_status_block()
        console.print(Panel(
            "[yellow]Current session path not found[/yellow]\n\n"
            f"{project_block}"
            f"Missing session: {session_path}\n\n"
            "Start a new session:\n"
            "  [cyan]ai session new \"Your Task Name\"[/cyan]",
            title="📊 Trinity Status",
            border_style="yellow",
            padding=(1, 2),
        ))
        raise typer.Exit(0)

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
    graph_state = sls.graph_state(default=session_state) or session_state
    dev_pass = sls.dev_verified()
    prod_pass = sls.prod_verified()
    verify_status = "DEV: PASS" if dev_pass else "DEV: PENDING"

    # The standard goal loop is tracked in graph_state. The older
    # session_state field remains for MVP dev/prod verification, but it
    # can stay INIT while the ritual graph has advanced to DO/VERIFIED.
    current_phase = graph_state
    phase_emoji = {
        "READY": "⚪",
        "THINK": "🧠",
        "SANDBOX": "🧪",
        "DO": "🛠️",
        "VERIFIED": "✅",
        "PROMOTED": "📦",
        "DEPLOYED": "🚀",
        "RETRO": "📝",
        "DONE": "🏁",
        "DEAD": "🔴",
        "SEALED": "🔒",
        "INIT": "🟡",
        "EDITING": "🛠️",
    }.get(current_phase, "❓")
    next_action = render_one_line(
        compute_next(
            config.project_root,
            session_path=session_path,
            graph_state=graph_state,
        )
    )
    project_block = _project_status_block()

    # Workflow progress table
    progress_table = Table(show_header=False, box=None, padding=(0, 1))
    progress_table.add_column("Step", style="cyan")
    progress_table.add_column("Status", style="white")

    standard_steps = [
        ("READY", "⚪ READY"),
        ("THINK", "🧠 THINK"),
        ("SANDBOX", "🧪 SANDBOX"),
        ("DO", "🛠️ DO"),
        ("VERIFIED", "✅ VERIFIED"),
        ("PROMOTED", "📦 PROMOTED"),
        ("DEPLOYED", "🚀 DEPLOYED"),
        ("RETRO", "📝 RETRO"),
        ("DONE", "🏁 DONE"),
        ("SEALED", "🔒 SEALED"),
    ]
    mvp_steps = [
        ("INIT", "🟡 INIT"),
        ("EDITING", "🛠️ EDITING"),
        ("VERIFIED", "✅ VERIFIED"),
        ("DONE", "🏁 DONE"),
    ]
    standard_state_names = {s[0] for s in standard_steps}
    steps = standard_steps if current_phase in standard_state_names else mvp_steps
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
{project_block}

[bold cyan]Workflow Progress:[/bold cyan]


[bold yellow]⚡ Next Action:[/bold yellow]
   {next_action}

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


def _show_project_only_status(error: Exception) -> bool:
    try:
        resolved = resolve_current_project(allow_fallback=False)
    except ProjectResolutionError:
        return False
    except Exception:
        return False
    console.print(Panel(
        "[yellow]No local .ai/ssot.yaml found[/yellow]\n\n"
        f"[bold]Project:[/bold] {resolved.project_slug}\n"
        f"[bold]Name:[/bold] {resolved.project_name}\n"
        f"[bold]Source:[/bold] {resolved.source}\n"
        f"[bold]Root:[/bold] {resolved.root_path}\n"
        f"[bold]Binding:[/bold] {resolved.binding_path or '—'}\n"
        f"[bold]Registry:[/bold] {resolved.registry_path or '—'}\n"
        f"[bold]Memory DB File:[/bold] {resolved.memory_db_path.name}\n"
        f"[bold]Memory DB Path:[/bold] {resolved.memory_db_path}\n\n"
        "[dim]Session commands still require a project-local .ai runtime or "
        "a central Trinity launcher wired to this binding.[/dim]",
        title="📊 Trinity Project Status",
        border_style="cyan",
        padding=(1, 2),
    ))
    return True


def _project_status_block() -> str:
    try:
        resolved = resolve_current_project(allow_fallback=False)
    except Exception:
        return ""
    return (
        f"\n[bold]Project:[/bold] {resolved.project_slug} "
        f"({resolved.source})\n"
        f"[bold]Memory DB File:[/bold] {resolved.memory_db_path.name}\n"
        f"[bold]Memory DB Path:[/bold] {resolved.memory_db_path}\n"
    )

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
