import typer
from pathlib import Path
from rich.console import Console
from ..core.ssot import SSOTLoader
from ..core.state import StateManager, cleanup_stale_lock, release_lock

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """Force-break session lock (.state/LOCK)."""
    pass

@app.command()
def run(force: bool = False, timeout: int = 30):
    """Remove session .state/LOCK (stale) or force if requested."""
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(1)

    session_path_str = status.get("current_session") if isinstance(status, dict) else None
    if not session_path_str:
        console.print("[yellow]No active session found[/yellow]")
        raise typer.Exit(0)

    lock_path = Path(session_path_str) / ".state" / "LOCK"
    if not lock_path.exists():
        console.print("[green]No lock present[/green]")
        raise typer.Exit(0)

    if force:
        release_lock(lock_path)
        console.print("[green]Lock removed (force).[/green]")
        return

    cleanup_stale_lock(lock_path, timeout=timeout)
    if not lock_path.exists():
        console.print("[green]Stale lock cleaned up.[/green]")
    else:
        console.print("[yellow]Lock still present. Use --force to remove.[/yellow]")

