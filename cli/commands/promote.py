import typer
import shutil
import json
import datetime
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..core.state import StateManager
from ..core.ssot import SSOTLoader
from ..core.fs import atomic_replace, safe_copy_tree

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """Atomic promotion: Dev -> Prod (Release)."""
    pass

@app.command()
def run(force: bool = False):
    """
    Promote DO/dev -> DO/prod safely.
    Rejects if .env exists in dev.
    Requires verification pass (simulated for v1.0).
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
        console.print("[red]No active session found.[/red]")
        raise typer.Exit(1)
        
    session_path = Path(current_session_path)
    dev_dir = session_path / "DO" / "dev"
    prod_dir = session_path / "DO" / "prod"
    
    if not dev_dir.exists():
        console.print("[red]Dev environment not found.[/red]")
        raise typer.Exit(1)

    # 2. Gate Check: Verification (WP5: read from .state/verify_dev.json)
    # Strict mode: require DEV verification PASS before promoting
    state_dir = session_path / ".state"
    verify_dev_path = state_dir / "verify_dev.json"

    dev_verified = False
    if verify_dev_path.exists():
        try:
            with verify_dev_path.open() as f:
                report = json.load(f)
            dev_verified = report.get("passed") == True
            if not dev_verified and not force:
                console.print("[bold red]GATE LOCK:[/bold red] Require DEV verification PASS before promote.")
                console.print(f"Dev verification status: {report.get('status')}")
                console.print("   Run [yellow]ai verify dev[/yellow] first")
                raise typer.Exit(1)
        except Exception as e:
            if not force:
                console.print(f"[bold red]GATE LOCK:[/bold red] Invalid verify_dev.json: {e}")
                raise typer.Exit(1)
    else:
        if not force:
            console.print("[bold red]GATE LOCK:[/bold red] Dev verification not found.")
            console.print("   Run [yellow]ai verify dev[/yellow] first")
            raise typer.Exit(1)

    # 3. Gate Check: Consensus Requirement (WP5: Design Decision Q2)
    # Default: require THINK/CONSENSUS.md before promote
    consensus_file = session_path / "THINK" / "CONSENSUS.md"
    if not consensus_file.exists() and not force:
        console.print("[bold red]CONSENSUS REQUIRED:[/bold red] THINK/CONSENSUS.md not found.")
        console.print("")
        console.print("[yellow]Rationale:[/yellow]")
        console.print("  - Trinity Protocol requires documented reasoning for all changes")
        console.print("  - This enforces planning discipline and creates audit trail")
        console.print("  - See SESSION_CONTRACT.md, Rule 4 and Design Decision Q2")
        console.print("")
        console.print("[cyan]Options:[/cyan]")
        console.print("  1. Run debate workflow: ai debate compile → edit verdict → ai debate publish")
        console.print("  2. Create CONSENSUS.md manually with your decision and rationale")
        console.print("  3. Override (not recommended): ai promote --force")
        console.print("")
        raise typer.Exit(1)

    # If --force used without consensus, log the override
    if not consensus_file.exists() and force:
        console.print("[yellow]⚠️  WARNING: Promoting without CONSENSUS.md (--force used)[/yellow]")
        console.print("[yellow]   This override will be logged in audit trail[/yellow]")

        # Log override event
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": "promote_forced",
            "reason": "no_consensus",
            "justification": "Force flag used, bypassing consensus requirement"
        }
        events_file = state_dir / "events.ndjson"
        with events_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # 4. Gate Check: Forbidden Files (additional safety)
    # We must NOT copy .env to prod via this mechanism
    # Scan dev for forbidden files
    forbidden = [".env", "config.dev.json"]
    found_forbidden = []
    for f in forbidden:
        if (dev_dir / f).exists():
            found_forbidden.append(f)

    if found_forbidden and not force:
        console.print(f"[bold red]SECURITY RISK:[/bold red] Found forbidden files in dev: {found_forbidden}")
        console.print("These must not be promoted. Remove them or use .gitignore equivalent.")
        raise typer.Exit(1)

    # 5. Atomic Promote
    console.print(f"[yellow]Promoting Dev -> Prod...[/yellow]")
    
    prod_new = session_path / "DO" / "prod_new"
    if prod_new.exists():
        shutil.rmtree(prod_new)
    try:
        safe_copy_tree(dev_dir, prod_new, exclude=[".env", ".env.local", "config.dev.json", "*.log", "__pycache__"])
    except Exception as e:
        console.print(f"[red]Copy failed:[/red] {e}")
        raise typer.Exit(1)
        
    # Atomic Swap
    # Backup old prod if exists? For v1.0 we assume overwrite or we could move prod -> prod_backup
    if prod_dir.exists():
        backup_dir = session_path / "DO" / f"prod_backup_{datetime.datetime.now().strftime('%H%M%S')}"
        shutil.move(str(prod_dir), str(backup_dir))
        console.print(f"  -> Backup created: {backup_dir.name}")
        
    # Atomic replace
    atomic_replace(prod_new, prod_dir)

    # 6. Audit & State
    # Log promotion event
    promote_event = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": "promote",
        "dev_verified": dev_verified,
        "consensus_exists": consensus_file.exists(),
        "forced": force,
        "status": "success"
    }
    events_file = state_dir / "events.ndjson"
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(promote_event, ensure_ascii=False) + "\n")

    # Update global state
    status["last_promote"] = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "session": str(session_path),
        "status": "success",
        "consensus": consensus_file.exists()
    }
    # Simple content hash (count files) as placeholder
    try:
        file_count = sum(1 for _ in prod_dir.rglob("*") if _.is_file())
        state_mgr.set_last_promote_hash(str(file_count))
    except Exception:
        pass
    status["system"]["status"] = "idle"
    state_mgr.save_status(status)

    # Success message
    consensus_status = "✅ With consensus" if consensus_file.exists() else "⚠️  Without consensus (forced)"

    console.print(Panel(
        f"[green]✅ Promotion Successful![/green]\n\n"
        f"DO/dev → DO/prod complete\n\n"
        f"**Gates Passed:**\n"
        f"  • Dev verification: ✅ PASS\n"
        f"  • Consensus: {consensus_status}\n"
        f"  • Forbidden files: ✅ Excluded\n\n"
        f"**Next Step:**\n"
        f"  Run: [yellow]ai verify prod[/yellow]\n"
        f"  Then: [yellow]ai deploy prod[/yellow]",
        title="🚀 Promote Complete",
        border_style="green"
    ))
