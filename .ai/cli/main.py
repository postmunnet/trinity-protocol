import typer
import sys
from pathlib import Path
from typing import Optional
from .core.ssot import SSOTLoader
from .core.state import StateManager
from .commands import verify, close, snapshot, promote, deploy, session, status, unlock, debate, sandbox, vault
from .commands import project as project_cmd
from .commands import vvv as vvv_cmd, nnn as nnn_cmd, gogogo as gogogo_cmd, rrr as rrr_cmd
from .commands import lll as lll_cmd
from .commands import loop as loop_cmd
from .commands import ddd as ddd_cmd
from .commands import shim as shim_cmd
from .commands import next as next_cmd
from .commands import wizard as wizard_cmd
from .commands import audit as audit_cmd
from .commands import sss as sss_cmd
from .commands import aaa as aaa_cmd
from .commands import doc_drift as doc_drift_cmd
from .commands import doctor as doctor_cmd
from .commands import config as config_cmd
from .commands import migrate_state as migrate_state_cmd
from .commands import abort as abort_cmd

# Layer 3 — bare `ai` invokes `ai next` (state-aware next-step
# prompter), unless --help / -h is passed. We flip
# no_args_is_help=False so the callback runs and we can route
# manually before typer would otherwise show help.
app = typer.Typer(
    help="Trinity Consoles - The AI-Native Operating System CLI",
    add_completion=False,
    no_args_is_help=False,
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
app.add_typer(project_cmd.app, name="project")  # Hybrid central Trinity + local project binding
app.add_typer(config_cmd.app, name="config")  # Runtime State Convention — declare runtime root (no home pollution)
app.add_typer(migrate_state_cmd.app, name="migrate-state")  # Phase D — move legacy home state into runtime
app.add_typer(abort_cmd.app, name="abort")  # ADR-0001 D3 — human operator_abort (active -> DEAD)
# Phase 1 — Goal Loop short-code rituals (driven by graphs/standard.yaml)
app.add_typer(sss_cmd.app, name="sss")        # Ritual alias — `ai sss <task>` ≡ `ai session new <task>`
app.add_typer(vvv_cmd.app, name="vvv")        # 5 questions
app.add_typer(nnn_cmd.app, name="nnn")        # numbered plan + budget check
app.add_typer(gogogo_cmd.app, name="gogogo")  # step-by-step with verifier
app.add_typer(rrr_cmd.app, name="rrr")        # Phase 1.5 — executable retro gate
app.add_typer(lll_cmd.app, name="lll")        # Phase 2.3 — read-only situational snapshot
app.add_typer(aaa_cmd.app, name="aaa")        # Q24.10 step 5 — read-only amendment router + evidence KPI
app.add_typer(doc_drift_cmd.app, name="doc-drift")  # doc-coupling drift guard — read-only check
app.add_typer(loop_cmd.app, name="loop")      # Phase 5 — goal tree + checkpoint/resume
app.add_typer(ddd_cmd.app, name="ddd")        # Phase 5 — deploy decision gate (VERIFIED→PROMOTED→DEPLOYED)
app.add_typer(shim_cmd.app, name="shim")      # Phase 8 — render shim adapters for vendor harnesses
app.add_typer(next_cmd.app, name="next")      # Layer 3 — state-aware "what should I run next?"
app.add_typer(wizard_cmd.app, name="wizard")  # Tier 2 — first-session scaffolder + template picker
app.add_typer(audit_cmd.app, name="audit")    # TRINITY_AUDIT_EVENT_SPEC_V1 §4-§5 — replay + verify-chain (read-only)
app.add_typer(doctor_cmd.app, name="doctor")  # CLI contract sanity checks — `ai doctor commands`

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Trinity CLI: Orchestrate your AI development workflow.
    Global bootstrap: load SSOT and state manager.

    Bare invocation (`ai`) routes to `ai next` so users only need to
    remember `ai` to get oriented. Pass --help to see this list.
    """
    try:
        # Allow certain commands to run without SSOT present (e.g., init)
        argv = sys.argv[1:]
        allow_without_ssot = {"version", "--help", "-h", "project", "status"}
        if ctx.invoked_subcommand in allow_without_ssot or any(
            a in allow_without_ssot for a in argv[:2]
        ):
            return

        loader = SSOTLoader(project_root=Path.cwd())
        config = loader.load()  # raises if missing ← ENFORCEMENT!

        # Store in context for subcommands
        ctx.obj = {
            "config": config,
            "state_manager": StateManager(config)
        }

        # Layer 3 — bare `ai` (no subcommand) → run `ai next`. We
        # detect the no-args case by checking sys.argv length AFTER
        # the global flags have been parsed (typer puts non-flag args
        # in subargs; if there's no subcommand, `ctx.invoked_subcommand`
        # is None at this point).
        if ctx.invoked_subcommand is None:
            # Forward to next._run with default options.
            from .commands.next import _run as _next_run
            code = _next_run(json_out=False, no_hints=False)
            raise typer.Exit(code=code)
    except typer.Exit:
        raise
    except Exception as e:
        # Allow help/version to run without crashing
        if "--help" in sys.argv or "-h" in sys.argv or "version" in sys.argv:
            return

        # `vvv --show` is a pure static prompt (the 5 questions) — it must
        # render from any cwd with no SSOT/session, per the two-phase
        # adapter contract (2026-06-12). vvv._run returns before touching
        # config in show mode, so skipping ctx.obj here is safe.
        if "vvv" in sys.argv and "--show" in sys.argv:
            return

        typer.secho(f"FATAL: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.command()
def version():
    """Show version."""
    print("Trinity CLI v1.0")

if __name__ == "__main__":
    app()
