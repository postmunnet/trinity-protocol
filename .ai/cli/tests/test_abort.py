"""ai abort — operator_abort CLI (ADR-0001 D3).

_abort fires operator_abort (active -> DEAD, decided_by=human) with the reason
recorded in the audit evidence; it refuses non-active states (READY has no
edge -> TransitionNotFound; DONE/DEAD are terminal -> TerminalStateLocked).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.commands.abort import _abort
from cli.core.loop import Loop, TerminalStateLocked, TransitionNotFound

from test_goal_loop import _make_project
from test_t04_dead_entry import STANDARD_WITH_DEAD


def _seed(tmp_path: Path, state: str):
    project, session = _make_project(tmp_path, graphs={"standard": STANDARD_WITH_DEAD})
    loop = Loop(session, graph_name="standard", project_root=project)
    loop.state.set_graph_state(state)
    return project, session


@pytest.mark.parametrize("state", ["THINK", "SANDBOX", "DO", "VERIFIED"])
def test_abort_fires_dead_from_active_states(tmp_path: Path, state: str):
    project, session = _seed(tmp_path, state)
    new_state = _abort(session, project, reason="operator decided to abort")
    assert new_state == "DEAD"

    loop = Loop(session, graph_name="standard", project_root=project)
    assert loop.current() == "DEAD"

    dead_tx = [
        e for e in loop.chain.iter_events()
        if e.get("type") == "graph.transition"
        and e["details"].get("to_state") == "DEAD"
    ]
    assert dead_tx, "no graph.transition to DEAD emitted"
    d = dead_tx[-1]["details"]
    assert d["trigger"] == "operator_abort"
    assert d["decided_by"] == "human"
    assert d["evidence"]["reason"] == "operator decided to abort"
    assert d["evidence"]["source"] == "cli"


def test_abort_reason_is_audited(tmp_path: Path):
    project, session = _seed(tmp_path, "DO")
    _abort(session, project, reason="ran out of runway")
    loop = Loop(session, graph_name="standard", project_root=project)
    d = [
        e for e in loop.chain.iter_events()
        if e.get("type") == "graph.transition"
        and e["details"].get("to_state") == "DEAD"
    ][-1]["details"]
    assert d["evidence"]["reason"] == "ran out of runway"


def test_abort_rejected_from_ready_no_edge(tmp_path: Path):
    project, session = _seed(tmp_path, "READY")
    with pytest.raises(TransitionNotFound):
        _abort(session, project, reason="x")
    loop = Loop(session, graph_name="standard", project_root=project)
    assert loop.current() == "READY"


@pytest.mark.parametrize("state", ["DONE", "DEAD"])
def test_abort_rejected_from_terminal_states(tmp_path: Path, state: str):
    project, session = _seed(tmp_path, state)
    with pytest.raises(TerminalStateLocked):
        _abort(session, project, reason="x")
    loop = Loop(session, graph_name="standard", project_root=project)
    assert loop.current() == state
