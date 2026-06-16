from __future__ import annotations
from pathlib import Path
from typing import Tuple, Dict
import pytest
import yaml
from unittest.mock import patch

from cli.core.loop import Loop, GraphInvalid, LoopError

# Reuse helpers from test_goal_loop or redefine minimally
def _make_project(
    tmp_path: Path,
    graphs: Dict[str, str] = None,
) -> Tuple[Path, Path]:
    project = tmp_path / "proj"
    (project / ".ai" / "audit").mkdir(parents=True)
    (project / ".ai" / "graphs").mkdir(parents=True)
    (project / ".ai" / "sessions").mkdir(parents=True)
    graphs = graphs or {}
    for name, body in graphs.items():
        (project / ".ai" / "graphs" / f"{name}.yaml").write_text(body)
    session = project / ".ai" / "sessions" / "sess_test"
    (session / ".state").mkdir(parents=True)
    return project, session

STANDARD_GRAPH_WITH_DEAD = """
version: "1.0"
name: standard
states: [READY, DONE, DEAD]
initial_state: READY
terminal_states: [DONE, DEAD]
transitions:
  - { from: READY, to: DONE, trigger: finish, decided_by: kernel }
  - { from: ANY, to: DEAD, trigger: kill, decided_by: kernel }
"""

def test_loop_fire_does_not_advance_state_when_audit_append_fails(tmp_path: Path):
    """T0.1 regression: audit MUST be written before state update."""
    project, session = _make_project(tmp_path, graphs={"std": STANDARD_GRAPH_WITH_DEAD})
    loop = Loop(session, graph_name="std", project_root=project)
    
    assert loop.current() == "READY"
    
    with patch.object(loop.chain, "append", side_effect=Exception("Audit failure")):
        with pytest.raises(Exception, match="Audit failure"):
            loop.fire("finish", decided_by="kernel")
            
    # If T0.1 is present, state would have advanced to DONE despite audit failure.
    # We want it to STAY at READY.
    assert loop.current() == "READY"

def test_loop_fire_keeps_graph_transition_payload_keys_for_reconcile(tmp_path: Path):
    """T0.1 check: Payload keys must remain compatible with Loop._reconcile_from_audit."""
    project, session = _make_project(tmp_path, graphs={"std": STANDARD_GRAPH_WITH_DEAD})
    loop = Loop(session, graph_name="std", project_root=project)
    
    with patch.object(loop.chain, "append") as mock_append:
        loop.fire("finish", decided_by="kernel")
        
        # Verify the call to append has the expected keys used by reconcile
        args, _ = mock_append.call_args
        assert args[0] == "graph.transition"
        details = args[1]
        assert "session_id" in details
        assert "to_state" in details
        assert details["to_state"] == "DONE"
        assert details["session_id"] == session.name

def test_loop_fire_blocks_done_state(tmp_path: Path):
    """T0.2 regression: DONE state is terminal."""
    project, session = _make_project(tmp_path, graphs={"std": STANDARD_GRAPH_WITH_DEAD})
    loop = Loop(session, graph_name="std", project_root=project)
    
    loop.fire("finish", decided_by="kernel")
    assert loop.current() == "DONE"
    assert loop.is_terminal()
    
    with pytest.raises(LoopError, match="terminal state 'DONE'"):
        # Even if a transition exists (like 'kill' from ANY), it should be blocked
        loop.fire("kill", decided_by="kernel")

def test_loop_fire_blocks_dead_state(tmp_path: Path):
    """T0.2 regression: DEAD state is terminal."""
    project, session = _make_project(tmp_path, graphs={"std": STANDARD_GRAPH_WITH_DEAD})
    loop = Loop(session, graph_name="std", project_root=project)
    
    loop.fire("kill", decided_by="kernel")
    assert loop.current() == "DEAD"
    assert loop.is_terminal()
    
    with pytest.raises(LoopError, match="terminal state 'DEAD'"):
        loop.fire("kill", decided_by="kernel")

def test_loop_fire_blocks_terminal_even_when_any_transition_exists(tmp_path: Path):
    """T0.2 deep check: terminal guard MUST win over 'from: ANY'."""
    graph_with_any = """
version: "1.0"
name: test
states: [A, B]
initial_state: A
terminal_states: [A]
transitions:
  - { from: ANY, to: B, trigger: jump, decided_by: kernel }
"""
    project, session = _make_project(tmp_path, graphs={"any": graph_with_any})
    loop = Loop(session, graph_name="any", project_root=project)
    
    assert loop.current() == "A"
    assert loop.is_terminal()
    
    with pytest.raises(LoopError, match="terminal state 'A'"):
        loop.fire("jump", decided_by="kernel")

def test_terminal_states_must_be_declared_in_states(tmp_path: Path):
    """T0.3 regression: terminal_states ⊆ states."""
    bad_graph = """
version: "1.0"
name: bad
states: [READY]
initial_state: READY
terminal_states: [READY, GHOST]
transitions:
  - { from: READY, to: READY, trigger: loop, decided_by: kernel }
"""
    project, session = _make_project(tmp_path, graphs={"bad": bad_graph})
    with pytest.raises(GraphInvalid, match=r"terminal_states not declared in states: \['GHOST'\]"):
        Loop(session, graph_name="bad", project_root=project)
