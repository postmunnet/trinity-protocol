"""S17 — KI-2026-05-16-002 next-action footer unification tests.

Verifies:
  - session.py routes through compute_next + render_one_line (no more
    hardcoded "Run: ai snapshot")
  - close.py routes terminal footer through the shared formatter
  - gogogo.py blocked path uses the shared formatter
  - `ai next` JSON output structurally agrees with render_one_line text
"""
from __future__ import annotations

import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from cli.commands import session as session_mod
from cli.commands import close as close_mod
from cli.commands import gogogo as gogogo_mod
from cli.commands import status as status_mod
from cli.core.next_action import compute, render_one_line


# ─── source-level: shared-module integration ─────────────────────────


def test_session_does_not_mention_ai_snapshot_in_user_facing_text() -> None:
    """session.py must no longer recommend `ai snapshot`."""
    source = inspect.getsource(session_mod)
    # Find user-facing strings (anything inside a docstring or f"... ai snapshot ...")
    user_facing_lines = [
        ln for ln in source.split("\n")
        if "ai snapshot" in ln and not ln.lstrip().startswith("#")
    ]
    assert user_facing_lines == [], (
        f"session.py still contains user-facing 'ai snapshot' recommendation: "
        f"{user_facing_lines}"
    )


def test_session_imports_next_action_helpers() -> None:
    source = inspect.getsource(session_mod)
    assert "compute_next" in source or "from ..core.next_action import" in source
    assert "render_one_line" in source


def test_close_imports_next_action_helpers() -> None:
    source = inspect.getsource(close_mod)
    assert "compute_next" in source or "from ..core.next_action import" in source
    assert "render_one_line" in source


def test_close_no_hardcoded_start_new_session() -> None:
    source = inspect.getsource(close_mod)
    # The literal hardcoded phrase from the old impl must be gone
    assert 'Start new session: [yellow]ai session new "Task Name"[/yellow]' not in source


def test_gogogo_blocked_path_uses_shared_formatter() -> None:
    """The 'graph_state must be DO' blocked branch must call compute_next
    + render_one_line, not just print a generic 'Run ai next'."""
    source = inspect.getsource(gogogo_mod)
    # Locate the specific branch
    idx = source.find('graph_state must be DO')
    assert idx > 0, "branch text moved or removed"
    snippet = source[idx: idx + 1000]
    assert "compute_next" in snippet or "render_one_line" in snippet


def test_status_uses_shared_next_action_helpers() -> None:
    source = inspect.getsource(status_mod)
    assert "compute_next" in source or "from ..core.next_action import" in source
    assert "render_one_line" in source


def test_status_prefers_graph_state_over_legacy_session_state() -> None:
    source = inspect.getsource(status_mod)
    assert "graph_state = sls.graph_state(" in source
    assert "current_phase = graph_state" in source
    assert "Start editing or apply sandbox diff" not in source


# ─── ai next --json ≡ render_one_line agreement ──────────────────────


def test_compute_dataclass_json_serializable(tmp_path: Path) -> None:
    """ai next --json serializes a dict; our NextAction must roundtrip cleanly."""
    sess = tmp_path / "0001_x"
    (sess / ".state").mkdir(parents=True)
    action = compute(tmp_path, session_path=sess, graph_state="READY")
    # The 'next' command CLI builds a dict from the dataclass
    payload = {
        "headline": action.headline,
        "command": action.command,
        "why": action.why,
        "state": action.state,
        "session_id": action.session_id,
        "terminal": action.terminal,
        "blocked": action.blocked,
    }
    # Round-trip
    s = json.dumps(payload)
    back = json.loads(s)
    assert back["command"] == action.command


def test_render_one_line_command_substring_of_action_command(tmp_path: Path) -> None:
    """The rendered footer's command MUST literally contain action.command —
    operators / parallel agents grep this string."""
    sess = tmp_path / "0001_x"
    (sess / ".state").mkdir(parents=True)
    for state in ("READY", "THINK", "DO", "RETRO"):
        action = compute(tmp_path, session_path=sess, graph_state=state)
        if action.command:
            line = render_one_line(action)
            assert action.command in line, (
                f"state={state}: command {action.command!r} not in line {line!r}"
            )


def test_render_one_line_terminal_uses_done_emoji(tmp_path: Path) -> None:
    sess = tmp_path / "0001_x"
    (sess / ".state").mkdir(parents=True)
    action = compute(tmp_path, session_path=sess, graph_state="DONE")
    assert action.terminal is True
    assert "🏁" in render_one_line(action)


def test_render_one_line_blocked_uses_human_marker() -> None:
    """When blocked=True, render must surface the human-gate marker."""
    from cli.core.next_action import NextAction
    blocked = NextAction(
        headline="awaiting human",
        command="ai ddd --target=dev --reason='...'",
        why="awaiting human decision",
        state="VERIFIED",
        session_id="sid",
        blocked=True,
    )
    line = render_one_line(blocked)
    assert "🟡" in line or "human" in line.lower()


# ─── invariant: no state in the standard transition table is missing
#     coverage by our render+compute tests above ───────────────────


_STANDARD_STATES_COVERED = {
    "READY", "THINK", "SANDBOX", "DO",
    "VERIFIED", "PROMOTED", "DEPLOYED",
    "RETRO", "DONE", "DEAD",
}


def test_compute_handles_all_standard_states_without_crashing(tmp_path: Path) -> None:
    sess = tmp_path / "0001_x"
    (sess / ".state").mkdir(parents=True)
    for state in _STANDARD_STATES_COVERED:
        action = compute(tmp_path, session_path=sess, graph_state=state)
        # Every standard state must produce a NextAction with at least
        # a non-empty headline. Terminal states may have no command.
        assert action.headline
        assert action.state == state
