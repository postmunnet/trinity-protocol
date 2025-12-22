import typer
import sys
from pathlib import Path
from typing import Optional
from .core.ssot import SSOTLoader
from .core.state import StateManager
from .commands import verify, close, snapshot, promote, deploy, session, status, unlock, debate, sandbox, vault

app = typer.Typer(
    help="Trinity Consoles - The AI-Native Operating System CLI",
    add_completion=False,
    no_args_is_help=True
)

# Register subcommands (v0.5)
app.add_typer(session.app, name="session")  # Session management
app.add_typer(verify.app, name="verify")    # Verification gates
app.add_typer(close.app, name="close")      # Gate-locked close
app.add_typer(snapshot.app, name="snapshot")
app.add_typer(promote.app, name="promote")
app.add_typer(deploy.app, name="deploy")  # Phase 6: dev/prod deploy
app.add_typer(status.app, name="status")  # Phase 6: workflow status
app.add_typer(unlock.app, name="unlock")  # Phase 6: force-break lock
app.add_typer(sandbox.app, name="sandbox")  # Phase 6: single ingress apply
app.add_typer(debate.app, name="debate")  # WP3: debate compiler
app.add_typer(vault.app, name="vault")    # v0.5: local secrets vault (demo)

@app.callback()
def main(ctx: typer.Context):
    """
    Trinity CLI: Orchestrate your AI development workflow.
    Global bootstrap: load SSOT and state manager.
    """
    try:
        # Allow certain commands to run without SSOT present (e.g., init)
        argv = sys.argv[1:]
        allow_without_ssot = {"version", "--help", "-h"}
        if any(a in allow_without_ssot for a in argv[:2]):
            return

        loader = SSOTLoader(project_root=Path.cwd())
        config = loader.load()  # raises if missing ← ENFORCEMENT!

        # Store in context for subcommands
        ctx.obj = {
            "config": config,
            "state_manager": StateManager(config)
        }
    except Exception as e:
        # Allow help/version to run without crashing
        if "--help" in sys.argv or "-h" in sys.argv or "version" in sys.argv:
            return

        typer.secho(f"FATAL: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.command()
def version():
    """Show version."""
    print("Trinity CLI v1.0")

if __name__ == "__main__":
    app()
