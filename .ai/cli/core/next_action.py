"""Layer 3 — state-aware "what should I run next" computer.

Spec: docs/specs/04_GRAPH_SPEC.md (transition table) + each ritual's
preconditions (.state/vvv_pass, .state/nnn_pass markers).

The contract: given a project_root + an optional active session
path, return a `NextAction` with:
  - headline:  one-sentence description ("the loop is at SANDBOX")
  - command:   the literal shell command the user should type next
  - why:       why this is the right next step
  - state:     the current graph_state (or None if no session)
  - terminal:  True when the loop is done (state == DONE / DEAD)

This module is the single source of truth used by:
  - `ai next`       (the user-facing command + bare `ai` invocation)
  - every ritual's success-footer (vvv/nnn/gogogo/ddd/rrr/lll)

The transition table is hard-coded against the standard graph
because the rituals are also hard-coded for the standard graph;
when a session opts into a non-standard graph we degrade to
"check `.ai/graphs/<name>.yaml` for legal transitions".
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class NextAction:
    headline: str
    command: Optional[str]   # the literal `ai ...` line; None means "no
                             # automatic next step" (terminal or unknown)
    why: str
    state: Optional[str]
    session_id: Optional[str]
    terminal: bool = False
    blocked: bool = False    # True when the next step needs human input


# ─────────── transition table (standard graph only) ───────────


def _standard_next(
    state: str,
    has_vvv_pass: bool,
    has_nnn_pass: bool,
) -> NextAction:
    if state == "READY":
        return NextAction(
            headline="No work in flight yet — start with `vvv`",
            command="ai vvv",
            why="vvv auto-fires sss (READY→THINK) and asks the 5 questions",
            state=state,
            session_id=None,
        )
    if state == "THINK":
        if not has_vvv_pass:
            return NextAction(
                headline="In THINK; vvv answers not captured yet",
                command="ai vvv",
                why="`.state/vvv_pass` marker missing — answer the 5 questions",
                state=state,
                session_id=None,
            )
        return NextAction(
            headline="In THINK; vvv passed — author the plan",
            command="ai nnn --plan-envelope <path/to/plan.json>",
            why="nnn budget-checks the plan and fires THINK→SANDBOX→DO",
            state=state,
            session_id=None,
        )
    if state == "SANDBOX":
        if not has_nnn_pass:
            return NextAction(
                headline="In SANDBOX; vvv passed — author the plan",
                command="ai nnn --plan-envelope <path/to/plan.json>",
                why="nnn budget-checks the plan and fires SANDBOX→DO",
                state=state,
                session_id=None,
            )
        return NextAction(
            headline="In SANDBOX; plan committed",
            command="ai gogogo",
            why="gogogo runs each plan step with verifier checkpoints",
            state=state,
            session_id=None,
        )
    if state == "DO":
        return NextAction(
            headline="In DO; ready to execute",
            command="ai gogogo",
            why="gogogo walks `.state/plan.json` step by step",
            state=state,
            session_id=None,
        )
    if state == "VERIFIED":
        return NextAction(
            headline="VERIFIED; close non-deploy work or run ddd for deploy-bound work",
            command="ai rrr",
            why=(
                "rrr closes standard non-deploy sessions; run "
                "`ai ddd --target=dev --reason='...'` first only when shipping a deploy artifact"
            ),
            state=state,
            session_id=None,
        )
    if state == "PROMOTED":
        return NextAction(
            headline="PROMOTED; awaiting deploy decision",
            command="ai ddd --target=dev --reason='...'",
            why="ddd will fire deploy_request (PROMOTED→DEPLOYED, decided_by=human)",
            state=state,
            session_id=None,
            blocked=True,
        )
    if state == "DEPLOYED":
        return NextAction(
            headline="DEPLOYED; close the loop with the retro gate",
            command="ai rrr",
            why="rrr runs acceptance + forbidden-diff, writes retro, auto-feeds memory-cli",
            state=state,
            session_id=None,
        )
    if state == "RETRO":
        return NextAction(
            headline="In RETRO; finalize the gate",
            command="ai rrr",
            why="rrr fires RETRO→DONE after gate passes; --dry-run to preview",
            state=state,
            session_id=None,
        )
    if state == "DONE":
        return NextAction(
            headline="Session DONE — nothing pending",
            command="ai close",
            why="archive the session capsule and free up active/",
            state=state,
            session_id=None,
            terminal=True,
        )
    if state == "DEAD":
        return NextAction(
            headline="Session DEAD — terminal failure",
            command="ai close",
            why="archive (DEAD is terminal); start a new session for retry",
            state=state,
            session_id=None,
            terminal=True,
        )
    return NextAction(
        headline=f"Unknown graph_state: {state!r}",
        command=None,
        why="not in the standard transition table; check .ai/graphs/<name>.yaml",
        state=state,
        session_id=None,
    )


# ─────────── public API ───────────


def compute(
    project_root: Path,
    session_path: Optional[Path] = None,
    graph_state: Optional[str] = None,
) -> NextAction:
    """Resolve the next action.

    Caller passes:
      - project_root (always)
      - session_path: the active session's path (None if no session)
      - graph_state: short-circuit when caller already knows it

    Returns a populated NextAction. Never raises — when input is
    incomplete, the headline says so and command=None.
    """
    if session_path is None:
        return NextAction(
            headline="No active session",
            command="ai session new <task-slug>",
            why="every ritual requires an active session capsule",
            state=None,
            session_id=None,
        )

    sid = session_path.name

    has_vvv_pass = (session_path / ".state" / "vvv_pass").exists()
    has_nnn_pass = (session_path / ".state" / "nnn_pass").exists()

    if graph_state is None:
        # Best-effort read of session-local state.
        try:
            from .state import SessionLocalState
            sst = SessionLocalState(session_path)
            graph_state = sst.graph_state(default="READY")
        except Exception:
            graph_state = "READY"

    action = _standard_next(graph_state, has_vvv_pass, has_nnn_pass)
    action.session_id = sid
    return action


def render_one_line(action: NextAction) -> str:
    """Compact terminal-friendly footer used by ritual success panels.

    Example outputs:
      "👉 next: ai nnn --plan-envelope <path>  · vvv passed, plan up next"
      "👉 next: ai close  · session DONE — nothing pending"
      "👉 next: (decide) ai ddd --target=dev --reason='...'  · awaiting human"
    """
    if action.command is None:
        return f"⏸  {action.headline}"
    prefix = "👉 next:"
    if action.terminal:
        prefix = "🏁 done:"
    elif action.blocked:
        prefix = "🟡 next (human):"
    short_why = action.why.split(";")[0]
    return f"{prefix} {action.command}  · {short_why}"
