"""
WP3: Debate Compiler

Implements multi-agent debate workflow:
- ai debate compile: Collect proposals into debate rounds
- ai debate publish: Validate and publish verdict to CONSENSUS.md

Design Decision Q1: Human writes verdict.md (not AI)
"""
import typer
import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from ..core.state import atomic_write_json

app = typer.Typer()
console = Console()

@app.callback()
def callback():
    """Multi-agent debate workflow commands."""
    pass


def _find_current_session() -> Path:
    """Find current session from global state or CWD."""
    from ..core.ssot import SSOTLoader
    from ..core.state import StateManager

    try:
        loader = SSOTLoader(Path.cwd())
        config = loader.load()
        state_mgr = StateManager(config)
        status = state_mgr.load_status()

        # Get current session from global state
        current_session = status.get("current_session")
        if current_session:
            session_path = Path(current_session)
            if session_path.exists():
                return session_path
    except Exception:
        pass

    # Fallback: check if CWD is inside a session
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".state" / "session_state.json").exists():
            return parent

    console.print("[red]Error: Not in a session. Run from session directory or create one with 'ai session new'[/red]")
    raise typer.Exit(1)


@app.command()
def compile(
    mode: str = typer.Option("fast", help="Debate mode: fast, standard, or deep"),
):
    """
    Compile agent proposals into debate rounds.

    Modes:
      - fast: proposal → verdict (1 round)
      - standard: proposal → critique → verdict (2 rounds)
      - deep: proposal → critique → rebuttal → verdict (3 rounds)

    Creates SANDBOX/DEBATE/round_*.md and verdict.md (template for human to fill).

    Example:
      ai debate compile --mode fast
      ai debate compile --mode standard
    """
    # Validate mode
    valid_modes = ["fast", "standard", "deep"]
    if mode not in valid_modes:
        console.print(f"[red]Error: Invalid mode '{mode}'. Must be: {', '.join(valid_modes)}[/red]")
        raise typer.Exit(1)

    session_path = _find_current_session()
    sandbox_path = session_path / "SANDBOX"
    debate_path = sandbox_path / "DEBATE"

    # Ensure DEBATE folder exists
    debate_path.mkdir(parents=True, exist_ok=True)

    # 1. Collect proposals
    agents = ["gemini", "claude", "codex"]
    proposals = []

    for agent in agents:
        proposal_file = sandbox_path / agent / "proposal.md"
        if proposal_file.exists():
            try:
                content = proposal_file.read_text(encoding="utf-8")
                proposals.append({
                    "agent": agent,
                    "content": content
                })
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {agent}/proposal.md: {e}[/yellow]")

    if not proposals:
        console.print("[red]Error: No proposals found in SANDBOX/gemini|claude|codex/proposal.md[/red]")
        console.print("[yellow]Hint: Agents must create proposal.md files first[/yellow]")
        raise typer.Exit(1)

    # 2. Create round_1.md (all proposals)
    round1_content = f"""# Debate Round 1: Proposals

**Session:** {session_path.name}
**Mode:** {mode.upper()}
**Compiled:** {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
**Proposals:** {len(proposals)}

---

"""

    for i, p in enumerate(proposals, 1):
        round1_content += f"""## Proposal {i}: {p['agent'].capitalize()}

{p['content']}

---

"""

    round1_file = debate_path / "round_1.md"
    round1_file.write_text(round1_content, encoding="utf-8")
    console.print(f"[green]✅ Created round_1.md ({len(proposals)} proposals)[/green]")

    # 3. If mode=standard or deep, collect critiques
    rounds_created = 1

    if mode in ["standard", "deep"]:
        critiques = []
        for agent in agents:
            critique_file = sandbox_path / agent / "critique.md"
            if critique_file.exists():
                try:
                    content = critique_file.read_text(encoding="utf-8")
                    critiques.append({
                        "agent": agent,
                        "content": content
                    })
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not read {agent}/critique.md: {e}[/yellow]")

        if critiques:
            round2_content = f"""# Debate Round 2: Critiques

**Session:** {session_path.name}
**Mode:** {mode.upper()}
**Compiled:** {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
**Critiques:** {len(critiques)}

---

"""

            for i, c in enumerate(critiques, 1):
                round2_content += f"""## Critique {i}: {c['agent'].capitalize()}

{c['content']}

---

"""

            round2_file = debate_path / "round_2.md"
            round2_file.write_text(round2_content, encoding="utf-8")
            console.print(f"[green]✅ Created round_2.md ({len(critiques)} critiques)[/green]")
            rounds_created = 2
        else:
            console.print(f"[yellow]⚠️  No critiques found (mode={mode}, but no critique.md files)[/yellow]")

    # 4. If mode=deep, collect rebuttals
    if mode == "deep":
        rebuttals = []
        for agent in agents:
            rebuttal_file = sandbox_path / agent / "rebuttal.md"
            if rebuttal_file.exists():
                try:
                    content = rebuttal_file.read_text(encoding="utf-8")
                    rebuttals.append({
                        "agent": agent,
                        "content": content
                    })
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not read {agent}/rebuttal.md: {e}[/yellow]")

        if rebuttals:
            round3_content = f"""# Debate Round 3: Rebuttals

**Session:** {session_path.name}
**Mode:** {mode.upper()}
**Compiled:** {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
**Rebuttals:** {len(rebuttals)}

---

"""

            for i, r in enumerate(rebuttals, 1):
                round3_content += f"""## Rebuttal {i}: {r['agent'].capitalize()}

{r['content']}

---

"""

            round3_file = debate_path / "round_3.md"
            round3_file.write_text(round3_content, encoding="utf-8")
            console.print(f"[green]✅ Created round_3.md ({len(rebuttals)} rebuttals)[/green]")
            rounds_created = 3
        else:
            console.print(f"[yellow]⚠️  No rebuttals found (mode=deep, but no rebuttal.md files)[/yellow]")

    # 5. Create verdict.md TEMPLATE (for human to fill)
    verdict_template = f"""# Debate Verdict

**Session:** {session_path.name}
**Date:** {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
**Mode:** {mode.upper()}
**Rounds:** {rounds_created}

---

## Decision

[HUMAN: Write your decision here. What approach did you choose?]

---

## Rationale

[HUMAN: Explain why you made this decision. What were the key factors?]

[HUMAN: Which proposals or critiques influenced your thinking?]

---

## Implementation Notes

[HUMAN: Any guidance for Codex (Implementation Lead)?]

[HUMAN: What are the key requirements or constraints?]

---

## Verdict By

**Name:** [HUMAN: Your name]
**Role:** [HUMAN: Your role, e.g., Architect, Product Owner]
**Date:** {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")}

---

**Instructions:**
1. Read all rounds in SANDBOX/DEBATE/round_*.md
2. Fill this template (replace all [HUMAN: ...] sections)
3. Run: ai debate publish (validates and publishes to THINK/CONSENSUS.md)
"""

    verdict_file = debate_path / "verdict.md"
    verdict_file.write_text(verdict_template, encoding="utf-8")
    console.print(f"[green]✅ Created verdict.md (TEMPLATE)[/green]")

    # 6. Update debate_state.json
    state_dir = session_path / ".state"
    debate_state = {
        "version": "1.0",
        "mode": mode,
        "rounds_compiled": rounds_created,
        "proposals_count": len(proposals),
        "compiled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "awaiting_verdict"  # Human must fill verdict.md
    }
    atomic_write_json(state_dir / "debate_state.json", debate_state)

    # 7. Log event
    event = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": "debate_compile",
        "mode": mode,
        "proposals": len(proposals),
        "rounds": rounds_created
    }
    events_file = state_dir / "events.ndjson"
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # Success message
    console.print(Panel(f"""[green]✅ Debate Compiled Successfully![/green]

📊 **Summary:**
   Mode: {mode.upper()}
   Proposals: {len(proposals)}
   Rounds: {rounds_created}

📂 **Files Created:**
   ✅ SANDBOX/DEBATE/round_1.md
   {'✅ SANDBOX/DEBATE/round_2.md' if rounds_created >= 2 else '⚠️  round_2.md (no critiques found)'}
   {'✅ SANDBOX/DEBATE/round_3.md' if rounds_created >= 3 else '⚠️  round_3.md (no rebuttals found)' if mode == 'deep' else ''}
   ✅ SANDBOX/DEBATE/verdict.md (TEMPLATE)

🎯 **Next Step:**
   1. Read all rounds in SANDBOX/DEBATE/
   2. Edit SANDBOX/DEBATE/verdict.md (fill [HUMAN: ...] sections)
   3. Run: [yellow]ai debate publish[/yellow]

📝 **Important:**
   verdict.md must be filled by HUMAN (not AI)
   Replace all [HUMAN: ...] placeholders with your decisions
""", title=f"🗣️ Debate Compiled ({mode.upper()} mode)", border_style="green"))


@app.command()
def publish():
    """
    Publish verdict to THINK/CONSENSUS.md (after human fills verdict).

    Validates:
      - verdict.md exists
      - No [HUMAN: ] placeholders remain

    Actions:
      - Copies verdict.md → THINK/CONSENSUS.md
      - Updates debate_state.json → complete
      - Updates session_state.json → DEV_EDITING (ready for implementation)

    Example:
      ai debate publish
    """
    session_path = _find_current_session()
    verdict_file = session_path / "SANDBOX" / "DEBATE" / "verdict.md"
    consensus_file = session_path / "THINK" / "CONSENSUS.md"
    state_dir = session_path / ".state"

    # 1. Check verdict exists
    if not verdict_file.exists():
        console.print("[red]Error: SANDBOX/DEBATE/verdict.md not found[/red]")
        console.print("[yellow]Hint: Run 'ai debate compile' first[/yellow]")
        raise typer.Exit(1)

    # 2. Read verdict
    try:
        verdict_content = verdict_file.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]Error reading verdict.md: {e}[/red]")
        raise typer.Exit(1)

    # 3. Validate: No [HUMAN: ] placeholders
    if "[HUMAN:" in verdict_content:
        console.print("[red]Error: verdict.md still contains [HUMAN: ] placeholders[/red]")
        console.print("[yellow]Please fill all sections marked [HUMAN: ...] before publishing[/yellow]")
        console.print("")
        console.print("[cyan]Unfilled sections found:[/cyan]")

        # Show which placeholders remain
        import re
        placeholders = re.findall(r'\[HUMAN:.*?\]', verdict_content)
        for placeholder in placeholders[:5]:  # Show first 5
            console.print(f"  - {placeholder}")
        if len(placeholders) > 5:
            console.print(f"  ... and {len(placeholders) - 5} more")

        raise typer.Exit(1)

    # 4. Copy verdict to THINK/CONSENSUS.md
    try:
        consensus_file.parent.mkdir(parents=True, exist_ok=True)
        consensus_file.write_text(verdict_content, encoding="utf-8")
        console.print(f"[green]✅ Published verdict to THINK/CONSENSUS.md[/green]")
    except Exception as e:
        console.print(f"[red]Error writing CONSENSUS.md: {e}[/red]")
        raise typer.Exit(1)

    # 5. Update debate_state.json
    debate_state_file = state_dir / "debate_state.json"
    if debate_state_file.exists():
        try:
            with debate_state_file.open("r", encoding="utf-8") as f:
                debate_state = json.load(f)
        except Exception:
            debate_state = {}
    else:
        debate_state = {}

    debate_state.update({
        "status": "complete",
        "verdict_published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "consensus_file": "THINK/CONSENSUS.md"
    })
    atomic_write_json(debate_state_file, debate_state)

    # 6. Update session_state.json → DEV_EDITING (ready for implementation)
    # Note: This assumes debate happens before coding. If session is already in EDITING, keep it there.
    session_state_file = state_dir / "session_state.json"
    if session_state_file.exists():
        try:
            with session_state_file.open("r", encoding="utf-8") as f:
                session_state = json.load(f)
        except Exception:
            session_state = {}
    else:
        session_state = {}

    current_state = session_state.get("legacy_state") or session_state.get("state", "INIT")

    # Only transition to EDITING if we're still in INIT (haven't started coding yet)
    if current_state == "INIT":
        session_state.pop("state", None)
        session_state["legacy_state"] = "EDITING"
        session_state["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        atomic_write_json(session_state_file, session_state)
        console.print("[green]✅ Session state updated: INIT → EDITING[/green]")
    else:
        console.print(f"[cyan]Session state: {current_state} (unchanged)[/cyan]")

    # 7. Log event
    event = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "action": "debate_publish",
        "verdict_size_bytes": len(verdict_content)
    }
    events_file = state_dir / "events.ndjson"
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # Success message
    console.print(Panel(f"""[green]✅ Verdict Published Successfully![/green]

📄 **Published To:**
   THINK/CONSENSUS.md

📊 **Debate Summary:**
   Status: Complete
   Verdict: {len(verdict_content)} bytes

🎯 **Next Step:**
   1. Codex reads THINK/CONSENSUS.md
   2. Codex implements decision
   3. Codex creates SANDBOX/codex/patch.diff
   4. Run: [yellow]ai sandbox apply codex[/yellow]

📝 **Reminder:**
   THINK/CONSENSUS.md is now required for 'ai promote'
   (Session Contract Rule 4)
""", title="🗣️ Debate Published", border_style="green"))


@app.command()
def status():
    """
    Show current debate status.

    Example:
      ai debate status
    """
    session_path = _find_current_session()
    state_dir = session_path / ".state"
    debate_state_file = state_dir / "debate_state.json"

    if not debate_state_file.exists():
        console.print("[yellow]No debate started yet[/yellow]")
        console.print("[cyan]Hint: Run 'ai debate compile --mode fast' to start[/cyan]")
        return

    try:
        with debate_state_file.open("r", encoding="utf-8") as f:
            debate_state = json.load(f)
    except Exception as e:
        console.print(f"[red]Error reading debate_state.json: {e}[/red]")
        raise typer.Exit(1)

    mode = debate_state.get("mode", "unknown")
    status_val = debate_state.get("status", "unknown")
    rounds = debate_state.get("rounds_compiled", 0)
    proposals = debate_state.get("proposals_count", 0)

    # Check verdict status
    verdict_file = session_path / "SANDBOX" / "DEBATE" / "verdict.md"
    verdict_status = "not created"
    if verdict_file.exists():
        content = verdict_file.read_text(encoding="utf-8")
        if "[HUMAN:" in content:
            verdict_status = "template (needs human input)"
        else:
            verdict_status = "filled (ready to publish)"

    # Check consensus
    consensus_file = session_path / "THINK" / "CONSENSUS.md"
    consensus_exists = consensus_file.exists()

    console.print(Panel(f"""[cyan]📊 Debate Status[/cyan]

**Mode:** {mode.upper()}
**Status:** {status_val}
**Proposals:** {proposals}
**Rounds Compiled:** {rounds}

**Verdict:** {verdict_status}
**Consensus:** {'✅ Published' if consensus_exists else '❌ Not published'}

---

**Next Action:**
{_get_next_action(status_val, verdict_status, consensus_exists)}
""", title="🗣️ Debate Status", border_style="cyan"))


def _get_next_action(status: str, verdict_status: str, consensus_exists: bool) -> str:
    """Determine next action based on debate state."""
    if status == "complete" and consensus_exists:
        return "[green]✅ Debate complete, consensus published[/green]"
    elif status == "awaiting_verdict":
        if verdict_status == "template (needs human input)":
            return "[yellow]→ Edit SANDBOX/DEBATE/verdict.md (fill [HUMAN: ] sections)[/yellow]"
        elif verdict_status == "filled (ready to publish)":
            return "[yellow]→ Run: ai debate publish[/yellow]"

    return "[yellow]→ Run: ai debate compile --mode fast[/yellow]"
