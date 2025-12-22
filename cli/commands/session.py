import typer
import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..core.state import StateManager, cleanup_stale_lock
from ..core.template_loader import TemplateLoader

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """Session management commands."""
    pass

def _create_metadata(session_path: Path, name: str, session_id: str):
    """Initialize CONTROL/META.json with Phase 6 canonical structure"""
    meta = {
        "id": session_id,
        "name": name,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "active",
        "phase": "snapshot",  # Phase 6: start with snapshot
        "workflow": {
            "snapshot": False,
            "dev_deployed": False,
            "dev_verified": False,
            "promoted": False,
            "prod_deployed": False,
            "prod_verified": False,
            "closed": False
        },
        # Features are additive; include sandbox to reflect Agent Sandboxes (WP1)
        "features": {
            "sandbox": {
                "enabled": True,
                "agents": ["gemini", "claude", "codex"],
                "paths": {
                    "gemini": "SANDBOX/gemini",
                    "claude": "SANDBOX/claude",
                    "codex": "SANDBOX/codex",
                },
            }
        },
    }
    meta_file = session_path / "CONTROL" / "META.json"
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

def _create_verify_log(session_path: Path):
    """Initialize CONTROL/VERIFY.md"""
    content = f"""# Verification Log for {session_path.name}

| Timestamp | Scope | Result | Details |
| :--- | :--- | :--- | :--- |
"""
    verify_file = session_path / "CONTROL" / "VERIFY.md"
    verify_file.parent.mkdir(parents=True, exist_ok=True)
    with open(verify_file, "w", encoding="utf-8") as f:
        f.write(content)

def _create_live_monitor(session_path: Path, name: str):
    """Initialize CONTROL/LIVE_MONITOR.md for real-time status"""
    content = f"""# Live Monitor: {name}

**Session ID:** {session_path.name}
**Created:** {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
**Status:** 🟡 Active

---

## Current Phase
→ **snapshot** (waiting)

## Workflow Progress
- [ ] snapshot
- [ ] deploy dev
- [ ] verify dev
- [ ] promote dev→prod
- [ ] deploy prod
- [ ] verify prod
- [ ] close

## Next Action
Run: `ai snapshot` to capture current project state

---
Last updated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
"""
    monitor_file = session_path / "CONTROL" / "LIVE_MONITOR.md"
    with open(monitor_file, "w", encoding="utf-8") as f:
        f.write(content)

def _init_state_files(session_path: Path):
    """Initialize .ai/state/ with sentinel JSON (never empty)"""
    state_dir = session_path / ".ai" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    # status.json (sentinel)
    status = {
        "version": "1.0",
        "phase": "snapshot",
        "initialized_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    with open(state_dir / "status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    # verify_report.json (sentinel)
    verify_report = {
        "version": "1.0",
        "result": "pending",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gates": {}
    }
    with open(state_dir / "verify_report.json", "w", encoding="utf-8") as f:
        json.dump(verify_report, f, indent=2)

    # events.ndjson (empty but exists)
    (state_dir / "events.ndjson").touch()

def _init_session_local_state(session_path: Path):
    """Initialize session-local .state/ with sentinel JSON (never empty).

    This complements legacy session/.ai/state and aligns with WP1/WP0 contract.
    """
    sdir = session_path / ".state"
    sdir.mkdir(parents=True, exist_ok=True)

    # session_state.json (INIT state)
    session_state = {
        "version": "1.0",
        "state": "INIT",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(sdir / "session_state.json", "w", encoding="utf-8") as f:
        json.dump(session_state, f, indent=2, ensure_ascii=False)

    # debate_state.json (empty shell)
    debate_state = {
        "version": "1.0",
        "mode": None,
        "round": 0,
        "status": "PENDING",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(sdir / "debate_state.json", "w", encoding="utf-8") as f:
        json.dump(debate_state, f, indent=2, ensure_ascii=False)

    # verify_dev.json / verify_prod.json (separate reports)
    verify_dev = {
        "version": "1.0",
        "scope": "dev",
        "passed": False,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checks": {},
    }
    with open(sdir / "verify_dev.json", "w", encoding="utf-8") as f:
        json.dump(verify_dev, f, indent=2, ensure_ascii=False)

    verify_prod = {
        "version": "1.0",
        "scope": "prod",
        "passed": False,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checks": {},
    }
    with open(sdir / "verify_prod.json", "w", encoding="utf-8") as f:
        json.dump(verify_prod, f, indent=2, ensure_ascii=False)

@app.command()
def new(name: str):
    """
    Create a new session with Phase 6 canonical structure.

    Example: ai session new "Fix Login Bug"

    Creates:
      THINK/          - reasoning, scope, acceptance
      DO/             - filesystem truth (snapshot/dev/prod)
      CONTROL/        - human-visible control (META, VERIFY, LIVE_MONITOR)
      .ai/state/      - system-only canonical state
    """
    from ..core.ssot import SSOTLoader

    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
    except Exception as e:
        console.print(f"[red]Error loading SSOT:[/red] {e}")
        raise typer.Exit(1)

    # 1. Generate Session ID
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    slug = name.lower().replace(" ", "_").replace("/", "-")[:50]  # limit slug length
    session_id = f"{date_str}_{slug}"

    # Get sessions path from SSOT
    sessions_path_str = config.raw_config.get("paths", {}).get("sessions", "${ai_root}/sessions")
    resolved_sessions = Path(sessions_path_str.replace("${ai_root}", str(config.ai_root)).replace("${project_root}", str(config.project_root)))

    session_path = resolved_sessions / session_id

    if session_path.exists():
        console.print(f"[bold red]Session already exists:[/bold red] {session_path}")
        raise typer.Exit(1)

    # 2. Scaffold Phase 6 Canonical Structure (from templates)
    console.print(f"[yellow]Scaffolding Phase 6 session:[/yellow] {session_id}")

    tpl = TemplateLoader.from_ssot(config)
    variables = {
        "SESSION_ID": session_id,
        "SESSION_NAME": name,
        "TIMESTAMP": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # Copy session template structure (THINK/ CONTROL/ DO/). Exclude template .state; we init below.
    tpl.copy_structure(
        src_rel_dir="session",
        dst_dir=session_path,
        variables=variables,
        exclude=[
            "session/.state",  # keep per-session state initialized below
        ],
    )

    # Ensure DO directories exist (in case template moves)
    (session_path / "DO" / "snapshot").mkdir(parents=True, exist_ok=True)
    (session_path / "DO" / "dev").mkdir(parents=True, exist_ok=True)
    (session_path / "DO" / "prod").mkdir(parents=True, exist_ok=True)

    # Ensure SANDBOX directories exist (Agent Sandboxes; WP1)
    sandbox = session_path / "SANDBOX"
    (sandbox / "gemini").mkdir(parents=True, exist_ok=True)
    (sandbox / "claude").mkdir(parents=True, exist_ok=True)
    (sandbox / "codex").mkdir(parents=True, exist_ok=True)
    (sandbox / "DEBATE").mkdir(parents=True, exist_ok=True)

    # Minimal SANDBOX/README.md if not provided by template
    sb_readme = sandbox / "README.md"
    if not sb_readme.exists():
        sb_readme.write_text(
            (
                "Agent Sandbox\n\n"
                "Each agent works in its own sandbox (gemini/ claude/ codex/).\n"
                "Merge changes to DO/dev via the sandbox apply workflow.\n"
            ),
            encoding="utf-8",
        )

    # Add WORKSPACE_PROMPT.md for each agent if missing
    prompts = {
        "gemini": "# Gemini Workspace\n\nResearch & analysis go here.",
        "claude": "# Claude Workspace\n\nPlanning, governance, and safety reviews.",
        "codex": "# Codex Workspace\n\nImplementation, tests, and diffs (patch.diff).",
    }
    for agent, text in prompts.items():
        p = sandbox / agent / "WORKSPACE_PROMPT.md"
        if not p.exists():
            p.write_text(text, encoding="utf-8")

    # THINK/CONSENSUS.md placeholder (published verdict)
    consensus = session_path / "THINK" / "CONSENSUS.md"
    if not consensus.exists():
        consensus.write_text("# CONSENSUS\n\nPending. Use `ai debate publish` to generate.", encoding="utf-8")

    # 3. Initialize State Files: legacy (.ai/state) + session-local (.state)
    _init_state_files(session_path)
    _init_session_local_state(session_path)

    # 3b. Cleanup any stale session lock
    cleanup_stale_lock(session_path / ".state" / "LOCK", timeout=30)

    # 4. Ensure CONTROL/META reflects sandbox features
    _create_metadata(session_path, name, session_id)

    # 6. Update Global State
    current_status = state_mgr.load_status()
    current_status["system"]["status"] = "busy"
    current_status["current_session"] = str(session_path)
    current_status["active_capsules"] = current_status["system"].get("active_capsules", 0) + 1
    state_mgr.save_status(current_status)

    # Success!
    console.print(Panel(f"""[green]✅ Session Created Successfully![/green]

📁 **Path:** {session_path}

📂 **Structure:**
├── THINK/          Context & Acceptance Criteria
├── DO/
│   ├── snapshot/   (immutable backup)
│   ├── dev/        (working copy)
│   └── prod/       (release candidate)
├── CONTROL/
│   ├── META.json
│   ├── VERIFY.md
│   └── LIVE_MONITOR.md
└── .ai/state/      System state (never edit)

🎯 **Next Step:**
   Run: [yellow]ai snapshot[/yellow] to capture current project state

📝 **Optional:**
   Edit THINK/00_CONTEXT.md to define your goals
""", title="🌌 Trinity Phase 6", border_style="green"))
