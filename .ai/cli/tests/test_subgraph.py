"""Phase 6 — sub-graph composition tests.

Covers:
- enter_subgraph pushes a frame and switches active graph
- inner graph runs through transitions normally
- exit_subgraph requires terminal state (unless force=True)
- pop restores outer graph name + outer state
- nested sub-graphs (depth ≥ 2) work
- cycle protection refuses re-entering an active graph
- decided_by validation on enter/exit
- audit chain records loop.subgraph.entered + .exited events
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.audit import AuditChain
from cli.core.loop import (
    Loop,
    SubgraphError,
    VALID_AUTHORITIES,
)

# Reuse goal-loop fixtures
from test_goal_loop import (
    STANDARD_GRAPH_YAML,
    TINY_GRAPH_YAML,
    _make_project,
)


DEPLOY_GRAPH_YAML = """
version: "1.0"
name: deploy
description: "Sub-graph fixture: PRE_DEPLOY -> DEPLOYING -> DEPLOYED"
states:
  - PRE_DEPLOY
  - DEPLOYING
  - DEPLOYED
  - FAILED
initial_state: PRE_DEPLOY
terminal_states: [DEPLOYED, FAILED]
transitions:
  - { from: PRE_DEPLOY, to: DEPLOYING, trigger: deploy_approve, decided_by: human }
  - { from: DEPLOYING, to: DEPLOYED,   trigger: deploy_complete, decided_by: verifier }
  - { from: DEPLOYING, to: FAILED,     trigger: deploy_failed,   decided_by: verifier }
"""


def _proj_with_subgraph(tmp_path: Path):
    return _make_project(
        tmp_path,
        graphs={
            "standard": STANDARD_GRAPH_YAML,
            "deploy":   DEPLOY_GRAPH_YAML,
            "tiny":     TINY_GRAPH_YAML,
        },
    )


# ─────────── enter / exit ───────────


def test_enter_subgraph_pushes_and_switches_graph(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    # Walk to VERIFIED so we have a meaningful outer state
    loop.fire("sss", decided_by="kernel")
    loop.fire("nnn_pass", decided_by="kernel")
    loop.fire("vvv_pass", decided_by="verifier")
    loop.fire("gogogo_complete", decided_by="verifier")
    assert loop.current_graph_name() == "standard"
    assert loop.current() == "VERIFIED"

    new_state = loop.enter_subgraph("deploy", decided_by="kernel")
    assert new_state == "PRE_DEPLOY"
    assert loop.current_graph_name() == "deploy"
    assert loop.current() == "PRE_DEPLOY"
    assert loop.subgraph_depth() == 1


def test_subgraph_runs_through_inner_transitions(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)
    loop.enter_subgraph("deploy", decided_by="kernel")

    loop.fire("deploy_approve", decided_by="human")
    assert loop.current() == "DEPLOYING"
    loop.fire("deploy_complete", decided_by="verifier")
    assert loop.current() == "DEPLOYED"
    assert loop.is_terminal()


def test_exit_subgraph_pops_and_restores_outer(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)

    loop.enter_subgraph("deploy", decided_by="kernel")
    loop.fire("deploy_approve", decided_by="human")
    loop.fire("deploy_complete", decided_by="verifier")

    restored = loop.exit_subgraph(decided_by="kernel")
    assert restored == "VERIFIED"
    assert loop.current_graph_name() == "standard"
    assert loop.current() == "VERIFIED"
    assert loop.subgraph_depth() == 0


def test_exit_subgraph_refuses_when_inner_not_terminal(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)
    loop.enter_subgraph("deploy", decided_by="kernel")
    # Don't advance; PRE_DEPLOY is not terminal
    with pytest.raises(SubgraphError):
        loop.exit_subgraph(decided_by="kernel")


def test_exit_subgraph_force_overrides_terminal_check(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)
    loop.enter_subgraph("deploy", decided_by="kernel")
    restored = loop.exit_subgraph(
        decided_by="human", force=True, evidence={"reason": "user cancel"},
    )
    assert restored == "VERIFIED"
    assert loop.current_graph_name() == "standard"


# ─────────── nesting ───────────


def test_nested_subgraphs(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)

    loop.enter_subgraph("deploy", decided_by="kernel")
    loop.fire("deploy_approve", decided_by="human")
    # Now nested: enter a tiny inner-inner graph
    loop.enter_subgraph("tiny", decided_by="kernel")
    assert loop.subgraph_depth() == 2
    assert loop.current_graph_name() == "tiny"
    assert loop.current() == "A"
    loop.fire("go", decided_by="kernel")
    loop.fire("stop", decided_by="human")
    assert loop.is_terminal()

    # Exit tiny → back to deploy/DEPLOYING
    loop.exit_subgraph(decided_by="kernel")
    assert loop.current_graph_name() == "deploy"
    assert loop.current() == "DEPLOYING"

    # Finish deploy and exit
    loop.fire("deploy_complete", decided_by="verifier")
    loop.exit_subgraph(decided_by="kernel")
    assert loop.current_graph_name() == "standard"
    assert loop.current() == "VERIFIED"
    assert loop.subgraph_depth() == 0


def test_cycle_protection_refuses_active_graph(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    with pytest.raises(SubgraphError):
        loop.enter_subgraph("standard", decided_by="kernel")


def test_cycle_protection_refuses_ancestor(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)
    loop.enter_subgraph("deploy", decided_by="kernel")
    # Try to re-enter standard from inside deploy
    with pytest.raises(SubgraphError):
        loop.enter_subgraph("standard", decided_by="kernel")


# ─────────── authority ───────────


def test_enter_subgraph_validates_decided_by(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    with pytest.raises(SubgraphError):
        loop.enter_subgraph("deploy", decided_by="bogus_authority")


def test_exit_subgraph_validates_decided_by(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)
    loop.enter_subgraph("deploy", decided_by="kernel")
    with pytest.raises(SubgraphError):
        loop.exit_subgraph(decided_by="ai", force=True)


# ─────────── persistence + audit ───────────


def test_subgraph_state_persists_across_loop_reload(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop1 = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop1.fire(trig, decided_by=by)
    loop1.enter_subgraph("deploy", decided_by="kernel")
    loop1.fire("deploy_approve", decided_by="human")
    # Drop loop1; create loop2 — should pick up the sub-graph state
    loop2 = Loop(sess, graph_name="standard", project_root=proj)
    assert loop2.current_graph_name() == "deploy"
    assert loop2.current() == "DEPLOYING"
    assert loop2.subgraph_depth() == 1


def test_audit_records_subgraph_entered_and_exited(tmp_path: Path):
    proj, sess = _proj_with_subgraph(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    for trig, by in [
        ("sss", "kernel"), ("nnn_pass", "kernel"),
        ("vvv_pass", "verifier"), ("gogogo_complete", "verifier"),
    ]:
        loop.fire(trig, decided_by=by)
    loop.enter_subgraph("deploy", decided_by="kernel")
    loop.fire("deploy_approve", decided_by="human")
    loop.fire("deploy_complete", decided_by="verifier")
    loop.exit_subgraph(decided_by="kernel")

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    types = [ev["type"] for ev in chain.iter_events()]
    assert "loop.subgraph.entered" in types
    assert "loop.subgraph.exited" in types
    # entered happens before exited
    assert types.index("loop.subgraph.entered") < types.index("loop.subgraph.exited")
