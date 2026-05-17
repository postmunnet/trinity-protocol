import typer
import shutil
import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..core.state import StateManager
from ..core.ssot import SSOTLoader
import subprocess
import shlex

app = typer.Typer()
console = Console()

# Files to ignore when checking for "real" content (same as snapshot.py)
IGNORED_FILES = {".gitkeep", ".DS_Store", ".placeholder"}


def has_real_content(directory: Path) -> bool:
    """Check if directory has real content (ignoring placeholder files)."""
    if not directory.exists():
        return False
    return any(p.name not in IGNORED_FILES for p in directory.iterdir())

@app.callback()
def callback():
    """Deploy commands (dev/prod)."""
    pass

@app.command()
def dev(force: bool = False):
    """
    Deploy from DO/dev to development environment.

    Phase 6 Rule: Deploy ONLY from DO/dev (not from DO/prod)

    This is a placeholder for actual deployment logic.
    In real scenario, this would:
      - Copy DO/dev → actual dev server
      - Run deployment scripts
      - Update deployment logs
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
        console.print("[red]No active session found. Run `ai session new <task>` first.[/red]")
        raise typer.Exit(1)

    session_path = Path(current_session_path)
    dev_dir = session_path / "DO" / "dev"

    if not dev_dir.exists():
        console.print(f"[red]DEV directory not found: {dev_dir}[/red]")
        raise typer.Exit(1)

    # Check if dev has REAL content (not just .gitkeep)
    if not has_real_content(dev_dir):
        console.print("[red]DEV directory has no real content. Run 'ai snapshot' first.[/red]")
        raise typer.Exit(1)

    # Phase 6 Guard: Must deploy from DO/dev only
    console.print(f"[yellow]📦 Deploying from DO/dev...[/yellow]")
    console.print(f"   Source: {dev_dir}")

    # Config-driven deployment
    deploy_cfg = config.raw_config.get("deploy", {}).get("dev", {})
    success = _perform_deploy(dev_dir, deploy_cfg, session_path / "CONTROL" / "DEPLOY_DEV.log", scope="dev", console=console, config=config)
    
    if not success:
        console.print("[red]Deployment failed[/red]")
        raise typer.Exit(1)
    
    # Track active environment
    state_mgr.set_active_environment("dev")

    # Update session metadata
    meta_file = session_path / "CONTROL" / "META.json"
    if meta_file.exists():
        with open(meta_file, "r") as f:
            meta = json.load(f)
        meta["workflow"]["dev_deployed"] = True
        meta["phase"] = "verify_dev"
        meta["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)

    console.print(Panel(
        f"[green]✅ Dev Deployment Complete[/green]\n\n"
        f"Source: DO/dev\n"
        f"Next: Run [yellow]ai verify dev[/yellow] before promotion",
        title="📦 Deploy Dev",
        border_style="green"
    ))

@app.command()
def prod(force: bool = False):
    """
    Deploy from DO/prod to production environment.

    Phase 6 Rule: Deploy ONLY from DO/prod (not from DO/dev)
    Phase 6 Guard: Must NOT deploy dev directly to prod

    Safety: Requires verification to pass first (in strict workflow)
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
        console.print("[red]No active session found. Run `ai session new <task>` first.[/red]")
        raise typer.Exit(1)

    session_path = Path(current_session_path)
    prod_dir = session_path / "DO" / "prod"
    dev_dir = session_path / "DO" / "dev"

    if not prod_dir.exists():
        console.print(f"[red]PROD directory not found: {prod_dir}[/red]")
        console.print("[yellow]Hint:[/yellow] Run 'ai promote' first")
        raise typer.Exit(1)

    # Check if prod has REAL content (not just .gitkeep)
    if not has_real_content(prod_dir):
        console.print("[red]PROD directory has no real content. Run 'ai promote' first.[/red]")
        raise typer.Exit(1)

    # Phase 6 Guard: Prevent direct dev→prod deployment
    console.print(f"[yellow]📦 Deploying from DO/prod...[/yellow]")
    console.print(f"   Source: {prod_dir}")
    console.print(f"   [green]✓[/green] Phase 6 Guard: Deploying from DO/prod (not DO/dev)")

    # Check verification (optional in MVP, but recommended)
    verify_report = session_path / ".ai" / "state" / "verify_report.json"
    if verify_report.exists() and not force:
        with open(verify_report, "r") as f:
            report = json.load(f)
        # PRD v0.4 schema: use "passed" (boolean)
        if report.get("session_id", "").endswith("_prod") and report.get("passed") != True:
            console.print("[bold yellow]⚠️  Warning:[/bold yellow] Prod verification not passed")
            console.print("   Use --force to deploy anyway (not recommended)")
            if not typer.confirm("Continue deployment?"):
                raise typer.Exit(1)

    # Config-driven deployment
    deploy_cfg = config.raw_config.get("deploy", {}).get("prod", {})
    success = _perform_deploy(prod_dir, deploy_cfg, session_path / "CONTROL" / "DEPLOY_PROD.log", scope="prod", console=console, config=config)
    
    if not success:
        console.print("[red]Deployment failed[/red]")
        raise typer.Exit(1)
    
    state_mgr.set_active_environment("prod")

    # Update session metadata
    meta_file = session_path / "CONTROL" / "META.json"
    if meta_file.exists():
        with open(meta_file, "r") as f:
            meta = json.load(f)
        meta["workflow"]["prod_deployed"] = True
        meta["phase"] = "verify_prod"
        meta["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)

    console.print(Panel(
        f"[green]✅ Production Deployment Complete[/green]\n\n"
        f"Source: DO/prod\n"
        f"Next: Run [yellow]ai verify prod[/yellow] before closing",
        title="🚀 Deploy Prod",
        border_style="green"
    ))


def _perform_deploy(source: Path, deploy_cfg: dict, log_file: Path, scope: str, console: Console, config) -> bool:
    """Perform deployment according to deploy config.

    Supports types: local_copy (default), rsync, scp.
    Returns True on success, False on failure.
    """
    dtype = deploy_cfg.get("type", "local_copy")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    def resolve_path(p: str) -> Path:
        return Path(p.replace("${ai_root}", str(config.ai_root)).replace("${project_root}", str(config.project_root)))

    success = True
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"Deploy {scope.upper()} {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")
        log.write(f"Type: {dtype}\nSource: {source}\n")

        if dtype == "local_copy":
            dest = resolve_path(deploy_cfg.get("path", str(config.project_root / ".ai" / "deploy" / scope)))
            log.write(f"Dest: {dest}\n")
            dest.mkdir(parents=True, exist_ok=True)
            copied_count = 0
            for item in source.iterdir():
                # Skip placeholder files
                if item.name in IGNORED_FILES:
                    continue
                target = dest / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, target)
                copied_count += 1
            console.print(f"   [green]✓[/green] Deployed {copied_count} item(s) to: " + str(dest))

        elif dtype == "rsync":
            host = deploy_cfg.get("host")
            path = deploy_cfg.get("path")
            opts = deploy_cfg.get("options", "-az --delete")
            if not host or not path:
                console.print("[red]rsync config requires host and path[/red]")
                success = False
            else:
                src = str(source) + "/"
                dest = f"{host}:{path}"
                cmd = f"rsync {opts} {shlex.quote(src)} {shlex.quote(dest)}"
                log.write(f"Cmd: {cmd}\n")
                try:
                    subprocess.run(cmd, shell=True, check=True)
                    console.print("   [green]✓[/green] rsync complete → " + dest)
                except Exception as e:
                    console.print(f"[red]rsync failed:[/red] {e}")
                    success = False

        elif dtype == "scp":
            host = deploy_cfg.get("host")
            path = deploy_cfg.get("path")
            opts = deploy_cfg.get("options", "-r")
            if not host or not path:
                console.print("[red]scp config requires host and path[/red]")
                success = False
            else:
                # scp -r source/* user@host:path
                cmd = f"scp {opts} {shlex.quote(str(source))}/* {shlex.quote(host + ':' + path)}"
                log.write(f"Cmd: {cmd}\n")
                try:
                    subprocess.run(cmd, shell=True, check=True)
                    console.print("   [green]✓[/green] scp complete → " + f"{host}:{path}")
                except Exception as e:
                    console.print(f"[red]scp failed:[/red] {e}")
                    success = False

        else:
            console.print(f"[yellow]Unknown deploy type '{dtype}', nothing executed[/yellow]")
            success = False

    return success
