"""ai loop — Goal-loop introspection + checkpoint/resume.

Spec ref: docs/specs/03_GOAL_LOOP_SPEC.md (Phase 5).

Subcommands:
  - status              — print goal tree + loop_state summary
  - checkpoint [--label] — save a checkpoint and update loop_state
  - resume              — show the next executable goal (if any)

The goal tree (`goals.yaml`) is the source of truth for *what to do
next*; loop_state.json is the *cursor* into that tree. `ai loop
resume` does not auto-execute — it prints the next-up goal so the
operator can choose to invoke `ai gogogo` (or another worker) on it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.audit import get_chain_for_project
from ..core.goal_tree import GoalTree, GoalTreeError
from ..core.loop_state import LoopState
from ..core.ssot import SSOTLoader
from ..core.state import StateManager

app = typer.Typer(
    help="Goal-loop introspection: status, checkpoint, resume."
)
console = Console()


# ─────────── status ───────────


@app.command()
def status():
    """Print goal tree + loop cursor summary."""
    config = SSOTLoader(Path.cwd()).load()
    sess = _resolve_session(config)
    tree = _try_load_tree(sess)
    state = _try_load_state(sess)

    if tree is None and state is None:
        console.print(
            "[yellow]No goals.yaml or loop_state.json — "
            "create them with `ai loop checkpoint` after first goal "
            "or by hand.[/yellow]"
        )
        raise typer.Exit(0)

    if tree is not None:
        _print_tree(tree)
    if state is not None:
        _print_state(state)


# ─────────── checkpoint ───────────


@app.command()
def checkpoint(
    label: Optional[str] = typer.Option(
        None, "--label", help="Human label for this checkpoint"
    ),
):
    """Save a checkpoint and append a loop.checkpoint event."""
    config = SSOTLoader(Path.cwd()).load()
    sess = _resolve_session(config)

    state = _load_or_init_state(sess)
    ckpt = state.add_checkpoint(label=label)
    state.save(sess)

    chain = get_chain_for_project(config.project_root)
    chain.append(
        "loop.checkpoint",
        {
            "session_id": sess.name,
            "decided_by": "human",
            "checkpoint_id": ckpt.id,
            "goal_id": ckpt.goal_id,
            "phase": ckpt.phase,
            "label": ckpt.label,
        },
    )

    console.print(
        Panel(
            f"checkpoint [bold]{ckpt.id}[/bold]\n"
            f"  ts: {ckpt.ts}\n"
            f"  goal: {ckpt.goal_id or '—'}\n"
            f"  phase: {ckpt.phase}\n"
            f"  label: {ckpt.label or '—'}",
            title="✅ ai loop checkpoint",
            border_style="green",
        )
    )


# ─────────── resume ───────────


@app.command()
def resume():
    """Print the next executable goal and the latest checkpoint."""
    config = SSOTLoader(Path.cwd()).load()
    sess = _resolve_session(config)

    tree = _try_load_tree(sess)
    state = _try_load_state(sess)

    if tree is None:
        console.print(
            "[red]No goals.yaml in this session. Create a goal tree "
            "first.[/red]"
        )
        raise typer.Exit(2)

    nxt = tree.next_executable()
    last_ckpt = state.latest_checkpoint() if state else None

    body = []
    body.append(
        f"[bold]next executable goal:[/bold] "
        f"{nxt.id + ' — ' + nxt.description if nxt else '—'}"
    )
    if last_ckpt:
        body.append(
            f"[bold]last checkpoint:[/bold] "
            f"{last_ckpt.id} (goal={last_ckpt.goal_id or '—'}, "
            f"phase={last_ckpt.phase}, label={last_ckpt.label or '—'})"
        )
    else:
        body.append("[bold]last checkpoint:[/bold] —")
    body.append(
        f"[bold]root status:[/bold] "
        f"{tree.aggregate_status(tree.root_goal_id) if tree.root_goal_id else '—'}"
    )

    console.print(
        Panel(
            "\n".join(body),
            title="↻ ai loop resume",
            border_style="cyan",
        )
    )

    if not nxt:
        # Nothing pending — exit 0 so scripts can branch.
        raise typer.Exit(0)


# ─────────── helpers ───────────


def _resolve_session(config) -> Path:
    state_mgr = StateManager(config)
    status_doc = state_mgr.load_status()
    cur = status_doc.get("current_session")
    if not cur:
        console.print(
            "[red]No active session. Run `ai session new <task>` first.[/red]"
        )
        raise typer.Exit(2)
    p = Path(cur)
    if not p.exists():
        console.print(f"[red]Session path missing: {p}[/red]")
        raise typer.Exit(2)
    return p


def _try_load_tree(sess: Path):
    try:
        return GoalTree.load(sess)
    except GoalTreeError:
        return None


def _try_load_state(sess: Path):
    try:
        return LoopState.load(sess)
    except (FileNotFoundError, ValueError):
        return None


def _load_or_init_state(sess: Path) -> LoopState:
    try:
        return LoopState.load(sess)
    except (FileNotFoundError, ValueError):
        return LoopState(session_id=sess.name)


def _print_tree(tree: GoalTree) -> None:
    table = Table(title=f"goals.yaml — {tree.session_id}", show_header=True)
    table.add_column("id", style="cyan")
    table.add_column("type")
    table.add_column("status")
    table.add_column("agg.status")
    table.add_column("parent")
    table.add_column("description", overflow="fold")
    for g in tree.all_goals():
        agg = tree.aggregate_status(g.id)
        table.add_row(
            g.id, g.type, g.status, agg, g.parent or "—", g.description
        )
    console.print(table)


def _print_state(state: LoopState) -> None:
    body = (
        f"[cyan]session[/cyan]   {state.session_id}\n"
        f"[cyan]current[/cyan]   goal={state.current_goal or '—'} "
        f"phase={state.current_phase}\n"
        f"[cyan]iter[/cyan]      {state.iteration} / {state.max_iterations}\n"
        f"[cyan]verdict[/cyan]   "
        f"{state.last_verdict or '—'} "
        f"({state.last_verdict_ts or '—'})\n"
        f"[cyan]ckpts[/cyan]     {len(state.checkpoints)}"
    )
    console.print(Panel(body, title="loop_state.json", border_style="cyan"))
