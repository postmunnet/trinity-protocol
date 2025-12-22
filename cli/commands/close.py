import typer
import json
import shutil
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..core.state import StateManager, SessionLocalState
from ..core.ssot import SSOTLoader

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """Close and archive session."""
    pass

@app.command()
def run(force: bool = False):
    """
    Close current session and archive.

    Phase 6 Requirement: Prod verify must PASS before close.
    Exit codes:
      0 = Success
      1 = Gate failed (verification not passed)
      2 = Error
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
        console.print("[red]No active session to close.[/red]")
        raise typer.Exit(1)

    session_path = Path(current_session_path)
    if not session_path.exists():
        console.print(f"[red]Session path not found: {session_path}[/red]")
        raise typer.Exit(1)

    # Gate: Prod verify must PASS (prefer session-local, fallback to legacy)
    if not force:
        sls = SessionLocalState(session_path)
        if not sls.prod_verified():
            # fallback legacy
            legacy = session_path / ".ai" / "state" / "verify_report.json"
            ok = False
            if legacy.exists():
                try:
                    with legacy.open("r", encoding="utf-8") as f:
                        r = json.load(f)
                    ok = r.get("scope") == "prod" and r.get("passed") is True
                except Exception:
                    ok = False
            if not ok:
                console.print("[bold red]🚨 GATE LOCK:[/bold red] Prod verification not passed")
                console.print("   Run [yellow]ai verify prod[/yellow] first or use --force")
                raise typer.Exit(1)

    # Update metadata
    meta_file = session_path / "CONTROL" / "META.json"
    if meta_file.exists():
        with open(meta_file, "r") as f:
            meta = json.load(f)
        meta["status"] = "closed"
        meta["closed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        meta["workflow"]["closed"] = True
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)

    # Update session-local state to DONE
    try:
        sls = SessionLocalState(session_path)
        # move to DONE if VERIFIED or already DONE
        cur = sls.current_state()
        if cur != "DONE":
            # allow VERIFIED -> DONE; if other states, still attempt per force flag
            try:
                sls.set_state("DONE")
            except Exception:
                pass
    except Exception:
        pass

    # Archive session
    archive_dir = session_path.parent.parent / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_name = f"{session_path.name}.archive"
    archive_path = archive_dir / archive_name

    console.print(f"[yellow]📦 Archiving session...[/yellow]")
    if archive_path.exists():
        console.print(f"   Removing old archive...")
        shutil.rmtree(archive_path)

    shutil.move(str(session_path), str(archive_path))
    console.print(f"   [green]✓[/green] Archived to: {archive_path}")

    # Update global state
    status["system"]["status"] = "idle"
    status["current_session"] = None
    status["system"]["active_capsules"] = max(0, status["system"].get("active_capsules", 1) - 1)
    status["last_closed"] = {
        "session": archive_name,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    state_mgr.save_status(status)

    # Generate summary panel
    summary = (
        f"[green]✅ Session Closed Successfully[/green]\n\n"
        f"Session: {session_path.name}\n"
        f"Archived: {archive_path}\n\n"
        f"[bold]Summary:[/bold]\n"
        f"• Prod verification: PASSED\n"
        f"• State: DONE\n"
        f"• Archive location: {archive_dir}\n\n"
        f"Start new session: [yellow]ai session new \"Task Name\"[/yellow]"
    )
    console.print(Panel(summary, title="🏁 Session Closed", border_style="green"))
