import typer
import json
import shutil
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ..core.ssot import SSOTLoader
from ..core.state import StateManager, acquire_lock, release_lock, SessionLocalState
from ..core.fs import safe_copy_tree, atomic_replace
from ..core.patch import PatchError, validate_scope, apply_unified_diff
from ..core.audit import get_chain_for_project

app = typer.Typer()
console = Console()


@app.callback()
def callback():
    """Apply sandbox diffs into DO/dev via a single safe ingress."""
    pass


@app.command()
def apply(agent: str, dry_run: bool = typer.Option(False, help="Validate and preview without applying")):
    """
    Apply SANDBOX/<agent>/patch.diff into DO/dev atomically and safely.

    - Validates unified diff format (no binary patches)
    - Scope-guards against THINK/, CONTROL/, .state/ and path escapes
    - Applies into a temp copy of DO/dev, then atomically swaps
    - Logs event and updates minimal state machine to EDITING
    """
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(1)

    session_path_str = status.get("current_session")
    if not session_path_str:
        console.print("[red]No active session found. Run `ai session new <task>` first.[/red]")
        raise typer.Exit(1)

    session_path = Path(session_path_str)
    dev_dir = session_path / "DO" / "dev"
    if not dev_dir.exists():
        console.print("[red]Dev environment not found.[/red]")
        raise typer.Exit(1)

    patch_path = session_path / "SANDBOX" / agent / "patch.diff"
    if not patch_path.exists():
        console.print(f"[red]Patch not found:[/red] {patch_path}")
        raise typer.Exit(1)

    diff_text = patch_path.read_text(encoding="utf-8")

    # Validate scope and format
    try:
        validate_scope(diff_text, dev_dir)
    except PatchError as e:
        console.print(f"[bold red]Patch rejected:[/bold red] {e}")
        raise typer.Exit(1)

    if dry_run:
        console.print(Panel(f"[green]Patch is valid[/green]\nAgent: {agent}\nMode: DRY-RUN", title="Sandbox Apply"))
        raise typer.Exit(0)

    # Acquire session lock
    lock_path = session_path / ".state" / "LOCK"
    try:
        acquire_lock(lock_path, timeout=30)
    except Exception as e:
        console.print(f"[bold red]LOCK ERROR:[/bold red] {e}")
        raise typer.Exit(1)

    temp_dir = session_path / "DO" / f"dev_apply_tmp_{datetime.datetime.now().strftime('%H%M%S')}"
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        safe_copy_tree(dev_dir, temp_dir)
        # Apply diff into temp dir
        try:
            apply_unified_diff(diff_text, temp_dir, dry_run=False)
        except PatchError as e:
            console.print(f"[bold red]Apply failed:[/bold red] {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise typer.Exit(1)

        # Atomic swap
        atomic_replace(temp_dir, dev_dir)

        # State update
        sls = SessionLocalState(session_path)
        if sls.current_state() == "INIT":
            sls.set_state("EDITING")

        # Log event (session-local, legacy)
        event = {
            "type": "sandbox_apply",
            "agent": agent,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "patch": str(patch_path.relative_to(session_path)),
        }
        events_file = session_path / ".state" / "events.ndjson"
        events_file.parent.mkdir(parents=True, exist_ok=True)
        with events_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        # F1: append sandbox.applied to global audit chain (D9)
        try:
            chain = get_chain_for_project(config.project_root)
            global_event = chain.append("sandbox.applied", {
                "session_id": session_path.name,
                "agent": agent,
                "patch": str(patch_path.relative_to(session_path)),
            })
            status["last_event_hash"] = global_event["hash"]
            state_mgr.save_status(status)
        except Exception as e:
            console.print(f"[yellow]⚠ audit chain append failed: {e}[/yellow]")

        console.print(Panel(f"[green]Patch applied successfully[/green]\nAgent: {agent}\nTarget: DO/dev", title="Sandbox Apply"))
    finally:
        # Ensure lock is always released; clean temp if still around
        release_lock(lock_path)
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.command()
def clean(remove: bool = typer.Option(False, help="Permanently delete SANDBOX instead of archiving"), yes: bool = typer.Option(False, "-y", help="Confirm destructive action")):
    """Archive SANDBOX/ artifacts (soft delete) or remove if confirmed."""
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(1)

    session_path_str = status.get("current_session")
    if not session_path_str:
        console.print("[yellow]No active session found. Run `ai session new <task>` first.[/yellow]")
        raise typer.Exit(0)

    session_path = Path(session_path_str)
    sandbox_dir = session_path / "SANDBOX"
    if not sandbox_dir.exists():
        console.print("[green]No SANDBOX directory to clean.[/green]")
        raise typer.Exit(0)

    if remove:
        if not yes:
            console.print("[red]Refusing to remove without -y confirmation.[/red]")
            raise typer.Exit(1)
        shutil.rmtree(sandbox_dir)
        action = "removed"
    else:
        archive_name = f"SANDBOX_archive_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_dir = session_path / archive_name
        if archive_dir.exists():
            shutil.rmtree(archive_dir)
        shutil.move(str(sandbox_dir), str(archive_dir))
        action = f"archived to {archive_name}"

    # Log event
    event = {
        "type": "sandbox_clean",
        "action": action,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    events_file = session_path / ".state" / "events.ndjson"
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    console.print(Panel(f"[green]SANDBOX {action}[/green]", title="Sandbox Clean", border_style="green"))
