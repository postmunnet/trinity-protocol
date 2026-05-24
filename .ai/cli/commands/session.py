import typer
import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..core.state import StateManager, cleanup_stale_lock
from ..core.template_loader import TemplateLoader
from ..core.session_naming import build_session_id, SessionNamingError
from ..core.audit import get_chain_for_project
from ..core.next_action import compute as compute_next, render_one_line

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
                    "gemini": "SANDBOX/02_gemini",
                    "claude": "SANDBOX/03_claude",
                    "codex": "SANDBOX/04_codex",
                    "brainstorm": "SANDBOX/00_BRAINSTORM",
                    "debate": "SANDBOX/01_DEBATE",
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
→ **READY** (waiting for vvv)

## Workflow Progress
- [ ] vvv (5 questions)
- [ ] nnn (plan + budget)
- [ ] gogogo (step execution)
- [ ] ddd (deploy gate)
- [ ] rrr (retro)
- [ ] close

## Next Action
Run `ai next` for current state-aware next-action; or follow the
ritual sequence `sss → vvv → nnn → gogogo → ddd → rrr → close`.

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

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # session_state.json (`legacy_state` = MVP lifecycle; `graph_state` =
    # canonical ritual graph). Keep the names distinct so "state" does not
    # mean two different things in the same document.
    session_state = {
        "version": "1.0",
        "legacy_state": "INIT",
        "graph_state": "READY",
        "created_at": now,
        "updated_at": now,
        "graph_state_updated_at": now,
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

    # 1. Resolve sessions path from SSOT
    sessions_path_str = config.raw_config.get("paths", {}).get("sessions", "${ai_root}/sessions")
    resolved_sessions = Path(sessions_path_str.replace("${ai_root}", str(config.ai_root)).replace("${project_root}", str(config.project_root)))
    resolved_sessions.mkdir(parents=True, exist_ok=True)

    # 2. Generate Session ID (driven by SSOT session_naming rules)
    try:
        session_id, _components = build_session_id(name, resolved_sessions, config.raw_config)
    except SessionNamingError as e:
        console.print(f"[red]Invalid session name:[/red] {e}")
        raise typer.Exit(1)

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

    # Ensure SANDBOX directories exist (numbered-step layout)
    sandbox = session_path / "SANDBOX"
    (sandbox / "00_BRAINSTORM").mkdir(parents=True, exist_ok=True)
    (sandbox / "00_BRAINSTORM" / "archive").mkdir(parents=True, exist_ok=True)
    (sandbox / "01_DEBATE").mkdir(parents=True, exist_ok=True)
    (sandbox / "01_DEBATE" / "archive").mkdir(parents=True, exist_ok=True)
    (sandbox / "02_gemini").mkdir(parents=True, exist_ok=True)
    (sandbox / "03_claude").mkdir(parents=True, exist_ok=True)
    (sandbox / "04_codex").mkdir(parents=True, exist_ok=True)

    # Minimal SANDBOX/README.md if not provided by template
    sb_readme = sandbox / "README.md"
    if not sb_readme.exists():
        sb_readme.write_text(
            (
                "Sandbox (numbered workflow steps)\n\n"
                "00_BRAINSTORM/ → 01_DEBATE/ → 02_gemini | 03_claude | 04_codex/\n"
                "Each agent works in its own seat; merge to DO/dev via sandbox apply.\n"
            ),
            encoding="utf-8",
        )

    # Add WORKSPACE_PROMPT.md for each agent seat if missing
    seat_paths = {
        "02_gemini": "# Gemini Workspace\n\nResearch & analysis go here.",
        "03_claude": "# Claude Workspace\n\nPlanning, governance, and safety reviews.",
        "04_codex": "# Codex Workspace\n\nImplementation, tests, and diffs (patch.diff).",
    }
    for seat_dir, text in seat_paths.items():
        p = sandbox / seat_dir / "WORKSPACE_PROMPT.md"
        if not p.exists():
            p.write_text(text, encoding="utf-8")

    # THINK/CONSENSUS.md placeholder (published verdict)
    consensus = session_path / "THINK" / "CONSENSUS.md"
    if not consensus.exists():
        consensus.write_text("# CONSENSUS\n\nPending. Use `ai debate publish` to generate.", encoding="utf-8")

    # 3. Initialize State Files: legacy (.ai/state) + session-local (.state)
    _init_state_files(session_path)
    _init_session_local_state(session_path)

    # 3a. Snapshot pre-existing untracked files at session-creation time.
    # Consumed by rrr's forbidden-diff to exclude HOLD parallel-session
    # deliverables from this session's violations list
    # (feedback_rrr_cross_session_forbidden_diff, 2026-05-14).
    try:
        from ..core.forbidden_diff import record_baseline_untracked
        record_baseline_untracked(session_path / ".state", config.project_root)
    except Exception:
        # Best-effort: a missing git binary or non-git workspace must not
        # block session creation. rrr will fall back to [] (current behavior)
        # if the file is absent.
        pass

    # 3b. Cleanup any stale session lock
    cleanup_stale_lock(session_path / ".state" / "LOCK", timeout=30)

    # 4. Ensure CONTROL/META reflects sandbox features
    _create_metadata(session_path, name, session_id)

    # 6. Update Global State (F4 fix: increment at system.active_capsules to match close.py)
    current_status = state_mgr.load_status()
    current_status["system"]["status"] = "busy"
    # Store ABSOLUTE path so downstream commands (vvv/nnn/gogogo/ddd/rrr/close)
    # can resolve consistently regardless of caller cwd. Bootstrap-installed
    # projects called us with a relative cwd (e.g., ".") which used to land
    # a relative current_session that broke Path.relative_to() in vvv.
    current_status["current_session"] = str(session_path.resolve())
    current_status["system"]["active_capsules"] = current_status["system"].get("active_capsules", 0) + 1

    # F1: emit session.created via the sss ritual library so the .ai/rituals/sss/
    # pack is honored (RC v1.1-rc Article XII.5 — single canonical pack-honoring
    # site, shared with vvv.py auto-advance).
    # Part 2 (capture wiring): wrap the sss emission in a capture() block so
    # the session.created event picks up a capture_id and the
    # CAPTURE/capture.sqlite is created at session-birth time. The session_dir
    # has been created above (mkdir at line ~218), satisfying the chicken-egg
    # constraint — capture() requires session_dir to exist.
    try:
        from .sss import emit_session_created
        from ..core.recordproxy import capture as _rp_capture
        chain = get_chain_for_project(config.project_root)
        with _rp_capture(
            session_path,
            ritual="sss",
            role="KERNEL",
            kind="ritual_invocation",
        ) as cap:
            cap.input("session_new_params.json", {
                "name": name,
                "session_id": session_id,
            })
            event = emit_session_created(
                chain,
                session_id=session_id,
                name=name,
                session_path_relative=str(
                    session_path.relative_to(config.project_root)
                ),
            )
            cap.output("session_created_event_hash.txt", event["hash"])
            cap.validation("session_path.txt", str(session_path.relative_to(config.project_root)))
        current_status["last_event_hash"] = event["hash"]
    except Exception as e:
        console.print(f"[yellow]⚠ audit chain append failed: {e}[/yellow]")

    state_mgr.save_status(current_status)

    # Success!
    # KI-2026-05-16-002 fix — replace the legacy hardcoded post-create
    # recommendation with the shared next_action formatter so the footer
    # agrees with `ai next` for the same session+state. Newly-created
    # session is at graph_state=READY → compute returns "ai vvv" (vvv
    # auto-fires sss; the snapshot ritual is legacy and not in the
    # canonical workflow anymore).
    next_action = compute_next(
        config.project_root, session_path=session_path
    )
    next_line = render_one_line(next_action)
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
   {next_line}

📝 **Optional:**
   Edit THINK/00_CONTEXT.md to define your goals
""", title="🌌 Trinity Phase 6", border_style="green"))
