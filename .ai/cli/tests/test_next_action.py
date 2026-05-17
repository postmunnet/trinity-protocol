"""Layer 3 tests — next-action computer.

Validates that compute(...) returns the right `command` for every
graph_state in the standard transition table, and degrades cleanly
when there's no session or markers are missing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.core.next_action import compute, render_one_line, NextAction
from cli.core.state import SessionLocalState


def _seed_session(tmp_path: Path, *, graph_state: str | None,
                  vvv_pass: bool = False, nnn_pass: bool = False) -> Path:
    sess = tmp_path / "sess_test"
    state_dir = sess / ".state"
    state_dir.mkdir(parents=True)
    if vvv_pass:
        (state_dir / "vvv_pass").touch()
    if nnn_pass:
        (state_dir / "nnn_pass").touch()
    if graph_state is not None:
        sst = SessionLocalState(sess)
        sst.set_graph_state(graph_state)
    return sess


# ─────────── no session ───────────


def test_no_session_routes_to_session_new(tmp_path: Path):
    a = compute(tmp_path, session_path=None)
    assert a.session_id is None
    assert a.state is None
    assert "session new" in (a.command or "")


# ─────────── per-state coverage (standard graph) ───────────


@pytest.mark.parametrize(
    "state,vvv,nnn,expected_in_cmd",
    [
        ("READY",     False, False, "ai vvv"),
        ("THINK",     False, False, "ai vvv"),                # markers missing
        ("THINK",     True,  False, "ai nnn"),                # vvv done, plan up next
        ("SANDBOX",   True,  True,  "ai gogogo"),
        ("DO",        True,  True,  "ai gogogo"),
        ("VERIFIED",  True,  True,  "ai ddd"),
        ("PROMOTED",  True,  True,  "ai ddd"),
        ("DEPLOYED",  True,  True,  "ai rrr"),
        ("RETRO",     True,  True,  "ai rrr"),
        ("DONE",      True,  True,  "ai close"),
        ("DEAD",      True,  True,  "ai close"),
    ],
)
def test_standard_state_routes(tmp_path, state, vvv, nnn, expected_in_cmd):
    sess = _seed_session(
        tmp_path, graph_state=state, vvv_pass=vvv, nnn_pass=nnn
    )
    a = compute(tmp_path, session_path=sess)
    assert a.command, f"no command computed for state={state}"
    assert expected_in_cmd in a.command, (
        f"state={state} → expected {expected_in_cmd!r} in command, got {a.command!r}"
    )
    assert a.session_id == "sess_test"
    assert a.state == state


# ─────────── terminal + blocked flags ───────────


def test_done_state_is_terminal(tmp_path: Path):
    sess = _seed_session(tmp_path, graph_state="DONE")
    a = compute(tmp_path, session_path=sess)
    assert a.terminal is True


def test_dead_state_is_terminal(tmp_path: Path):
    sess = _seed_session(tmp_path, graph_state="DEAD")
    a = compute(tmp_path, session_path=sess)
    assert a.terminal is True


def test_verified_state_is_blocked_human(tmp_path: Path):
    sess = _seed_session(tmp_path, graph_state="VERIFIED")
    a = compute(tmp_path, session_path=sess)
    assert a.blocked is True
    assert a.terminal is False


def test_promoted_state_is_blocked_human(tmp_path: Path):
    sess = _seed_session(tmp_path, graph_state="PROMOTED")
    a = compute(tmp_path, session_path=sess)
    assert a.blocked is True


# ─────────── unknown state ───────────


def test_unknown_state_returns_no_command(tmp_path: Path):
    sess = _seed_session(tmp_path, graph_state="WEIRD_STATE")
    a = compute(tmp_path, session_path=sess)
    assert a.command is None
    assert "unknown" in a.headline.lower() or "WEIRD_STATE" in a.headline


# ─────────── render_one_line ───────────


def test_render_normal_uses_arrow_prefix():
    a = NextAction(
        headline="In THINK",
        command="ai nnn --plan-envelope p.json",
        why="nnn budget-checks the plan",
        state="THINK",
        session_id="s",
    )
    line = render_one_line(a)
    assert line.startswith("👉 next:")
    assert "ai nnn" in line


def test_render_terminal_uses_flag_prefix():
    a = NextAction(
        headline="DONE",
        command="ai close",
        why="archive",
        state="DONE",
        session_id="s",
        terminal=True,
    )
    line = render_one_line(a)
    assert line.startswith("🏁 done:")


def test_render_blocked_uses_human_prefix():
    a = NextAction(
        headline="VERIFIED",
        command="ai ddd",
        why="awaiting human",
        state="VERIFIED",
        session_id="s",
        blocked=True,
    )
    line = render_one_line(a)
    assert "human" in line.lower()


def test_render_no_command_uses_pause_prefix():
    a = NextAction(
        headline="Unknown state",
        command=None,
        why="?",
        state="?",
        session_id="s",
    )
    line = render_one_line(a)
    assert line.startswith("⏸")


# ─── S17 / KI-002 — coverage for missing graph states ──────────────


from cli.core.next_action import compute, render_one_line, NextAction


def _empty_session(tmp_path):
    """Create a minimal session directory shape so compute can resolve
    markers + graph_state without crashing."""
    sess = tmp_path / "0001_test"
    (sess / ".state").mkdir(parents=True)
    return sess


def test_compute_no_active_session_returns_session_new_recommendation(tmp_path) -> None:
    action = compute(tmp_path, session_path=None)
    assert action.command == "ai session new <task-slug>"
    assert action.state is None
    assert action.session_id is None
    assert "active session" in action.headline.lower()


def test_compute_ready_returns_vvv(tmp_path) -> None:
    sess = _empty_session(tmp_path)
    action = compute(tmp_path, session_path=sess, graph_state="READY")
    assert action.command == "ai vvv"
    assert action.state == "READY"
    assert action.session_id == sess.name


def test_compute_think_without_vvv_pass_returns_vvv(tmp_path) -> None:
    sess = _empty_session(tmp_path)
    action = compute(tmp_path, session_path=sess, graph_state="THINK")
    assert action.command == "ai vvv"


def test_compute_think_with_vvv_pass_returns_nnn(tmp_path) -> None:
    sess = _empty_session(tmp_path)
    (sess / ".state" / "vvv_pass").write_text("ok")
    action = compute(tmp_path, session_path=sess, graph_state="THINK")
    assert "ai nnn" in (action.command or "")


def test_compute_do_returns_gogogo(tmp_path) -> None:
    sess = _empty_session(tmp_path)
    (sess / ".state" / "vvv_pass").write_text("ok")
    (sess / ".state" / "nnn_pass").write_text("ok")
    action = compute(tmp_path, session_path=sess, graph_state="DO")
    assert action.command == "ai gogogo"


def test_compute_deployed_routes_to_rrr(tmp_path) -> None:
    sess = _empty_session(tmp_path)
    action = compute(tmp_path, session_path=sess, graph_state="DEPLOYED")
    # DEPLOYED → rrr is the next step (per transition table)
    assert "rrr" in (action.command or "").lower()


def test_compute_retro_returns_rrr(tmp_path) -> None:
    sess = _empty_session(tmp_path)
    action = compute(tmp_path, session_path=sess, graph_state="RETRO")
    assert action.command == "ai rrr"


def test_render_one_line_for_terminal_uses_done_prefix(tmp_path) -> None:
    sess = _empty_session(tmp_path)
    action = compute(tmp_path, session_path=sess, graph_state="DONE")
    rendered = render_one_line(action)
    assert "🏁" in rendered or "done" in rendered.lower()


def test_render_one_line_no_command_falls_back(tmp_path) -> None:
    """When command=None, render gives a paused (⏸) indicator."""
    action = NextAction(
        headline="weird state",
        command=None,
        why="x",
        state=None,
        session_id=None,
    )
    rendered = render_one_line(action)
    assert rendered.startswith("⏸")
