import typer
import shutil
import datetime
import tempfile
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..core.state import StateManager
from ..core.ssot import SSOTLoader
from ..core.fs import safe_copy_tree
from .verify import VerificationGates

app = typer.Typer()
console = Console()

# Files to ignore when checking for "real" content
IGNORED_FILES = {".gitkeep", ".DS_Store", ".placeholder"}


def has_real_content(directory: Path) -> bool:
    """Check if directory has real content (ignoring placeholder files)."""
    if not directory.exists():
        return False
    for item in directory.iterdir():
        if item.name not in IGNORED_FILES:
            return True
    return False

@app.callback()
def callback():
    """Safe copy: Prod -> Snapshot -> Dev (Sandbox)."""
    pass

@app.command()
def run(force: bool = False):
    """
    Create a snapshot of the project root into the current session.
    Copies Project Root -> DO/snapshot (Clean)
    Copies DO/snapshot -> DO/dev (Working)
    """
    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(1)

    # 1. Determine active session
    current_session_path = status.get("current_session")
    if not current_session_path:
        console.print("[red]No active session found. Run 'ai session new' first.[/red]")
        raise typer.Exit(1)
    
    session_path = Path(current_session_path)
    if not session_path.exists():
        console.print(f"[red]Active session path not found:[/red] {session_path}")
        raise typer.Exit(1)

    snapshot_dir = session_path / "DO" / "snapshot"
    dev_dir = session_path / "DO" / "dev"

    # 2. Guard: Check if has real content (ignoring .gitkeep)
    if has_real_content(snapshot_dir) or has_real_content(dev_dir):
        if not force:
            console.print("[red]Snapshot/Dev dirs not empty. Use --force to overwrite.[/red]")
            raise typer.Exit(1)
        else:
            # Clean up if forcing (only delete real content)
            for item in snapshot_dir.iterdir():
                if item.name in IGNORED_FILES:
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            for item in dev_dir.iterdir():
                if item.name in IGNORED_FILES:
                    continue
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    # 3. Choose source: prefer DO/prod if it has REAL content, else project root
    prod_dir = session_path / "DO" / "prod"
    source_dir = prod_dir if has_real_content(prod_dir) else config.project_root

    # 4. Pre-flight verification (Safety Clause 1.2)
    # Copy to temp first, then verify the temp copy (excludes .ai from verification)
    console.print("[yellow]Pre-flight verification before snapshot...[/yellow]")
    
    # Create temp copy for verification (excludes .ai directory with canary files)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "verify_copy"
        try:
            safe_copy_tree(source_dir, temp_path, exclude=[".ai", ".git", ".venv", "node_modules", "__pycache__", ".DS_Store", "sessions", "${sessions}", "${ai_root}", ".cursor", ".pytest_cache", "tests", "ai-shortcode", "ai-docs"])
        except Exception as e:
            console.print(f"[red]Pre-flight copy failed:[/red] {e}")
            raise typer.Exit(1)
        
        # Run verification on the clean copy (no .ai canary false positives)
        preflight = VerificationGates(temp_path, config.raw_config)
        if not preflight.run_all(strict=True):
            console.print("[red]Snapshot blocked by verification failure[/red]")
            raise typer.Exit(1)

    # 5. Perform Copy: Project Root → DO/snapshot → DO/dev
    console.print(f"[yellow]Snapshotting source...[/yellow] {source_dir}")
    try:
        safe_copy_tree(source_dir, snapshot_dir, exclude=[".ai", ".git", ".venv", "node_modules", "__pycache__", ".DS_Store", "sessions", "${sessions}", "${ai_root}", ".cursor", ".pytest_cache", "tests", "ai-shortcode", "ai-docs"])
    except Exception as e:
        console.print(f"[red]Copy failed:[/red] {e}")
        raise typer.Exit(1)
    console.print(f"  -> Snapshot: [green]OK[/green]")
    
    console.print(f"[yellow]Creating Dev Environment...[/yellow]")
    try:
        safe_copy_tree(snapshot_dir, dev_dir, exclude=[".DS_Store", "__pycache__"])
    except Exception as e:
        console.print(f"[red]Copy failed:[/red] {e}")
        raise typer.Exit(1)
    console.print(f"  -> Dev Copy: [green]OK[/green]")

    # 6. Update State
    status["last_snapshot"] = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": str(source_dir),
        "session": str(session_path)
    }
    # Optional: record simple content hash (count of files) for MVP tracking
    try:
        file_count = sum(1 for _ in snapshot_dir.rglob("*") if _.is_file())
        state_mgr.set_last_snapshot_hash(str(file_count))
    except Exception:
        pass
    state_mgr.save_status(status)
    
    # Audit logic could go here (append to CONTROL/events.ndjson)
    
    console.print(Panel(f"[green]Snapshot Complete![/green]\n\nYou can now edit files in:\n[blue]{dev_dir}[/blue]", title="Trinity AI"))
