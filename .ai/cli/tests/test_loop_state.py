"""Phase 5 — loop_state + ai loop command tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.core.goal_tree import Goal, GoalTree
from cli.core.loop_state import LoopState, SCHEMA_VERSION


# ─────────── LoopState core ───────────


def test_loop_state_save_load_roundtrip(tmp_path: Path):
    s = LoopState(session_id="sess1")
    s.tick(goal_id="g1", phase="EXECUTING", verdict="PASS")
    ck = s.add_checkpoint(label="after first goal")
    s.save(tmp_path)

    p = LoopState.path_for(tmp_path)
    assert p.exists()
    raw = json.loads(p.read_text())
    assert raw["version"] == SCHEMA_VERSION
    assert raw["iteration"] == 1
    assert raw["current_goal"] == "g1"
    assert raw["last_verdict"] == "PASS"

    reloaded = LoopState.load(tmp_path)
    assert reloaded.iteration == 1
    assert reloaded.current_goal == "g1"
    assert len(reloaded.checkpoints) == 1
    assert reloaded.checkpoints[0].id == ck.id
    assert reloaded.checkpoints[0].label == "after first goal"


def test_loop_state_load_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        LoopState.load(tmp_path)


def test_loop_state_rejects_unknown_schema(tmp_path: Path):
    p = LoopState.path_for(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"version": 999, "session_id": "s"}))
    with pytest.raises(ValueError):
        LoopState.load(tmp_path)


def test_tick_increments_and_records_verdict():
    s = LoopState(session_id="x")
    assert s.iteration == 0
    s.tick(goal_id="g1")
    s.tick(goal_id="g2", verdict="RETRY")
    assert s.iteration == 2
    assert s.current_goal == "g2"
    assert s.last_verdict == "RETRY"
    assert s.last_verdict_ts is not None


def test_add_checkpoint_assigns_sequential_ids():
    s = LoopState(session_id="x")
    s.tick(goal_id="g1")
    a = s.add_checkpoint()
    b = s.add_checkpoint(label="midway")
    assert a.id == "ckpt_001"
    assert b.id == "ckpt_002"
    assert b.label == "midway"
    assert s.latest_checkpoint().id == "ckpt_002"


def test_latest_checkpoint_when_none():
    s = LoopState(session_id="x")
    assert s.latest_checkpoint() is None


# ─────────── ai loop CLI ───────────


def _make_session(tmp_path: Path) -> Path:
    """Build a minimal Trinity session under tmp/proj with goals.yaml."""
    proj = tmp_path / "proj"
    sess = proj / ".ai" / "sessions" / "active" / "0001_2026-05-01_test"
    sess.mkdir(parents=True)
    (proj / ".ai" / "audit").mkdir(parents=True)
    (proj / ".ai" / "state").mkdir(parents=True)
    import yaml as _yaml
    (proj / ".ai" / "ssot.yaml").write_text(
        _yaml.safe_dump({
            "version": "1.0",
            "paths": {"state": "${ai_root}/state"},
        })
    )
    (proj / ".ai" / "state" / "status.json").write_text(json.dumps({
        "version": "1.0",
        "current_session": str(sess),
        "last_event_hash": None,
    }))

    tree = GoalTree(session_id=sess.name)
    tree.add_goal(Goal(id="g1", type="epic", description="Root"))
    tree.add_goal(Goal(id="g2", type="task", description="First", parent="g1"))
    tree.add_goal(Goal(id="g3", type="task", description="Second", parent="g1"))
    tree.save(sess)
    return proj


def test_loop_checkpoint_creates_state_and_audit_event(tmp_path, monkeypatch):
    proj = _make_session(tmp_path)
    monkeypatch.chdir(proj)
    from cli.commands.loop import checkpoint
    # Typer wraps these in commands; call the underlying fn.
    checkpoint(label="phase-2.3 close")

    # Session path
    sess = proj / ".ai" / "sessions" / "active" / "0001_2026-05-01_test"
    state = LoopState.load(sess)
    assert len(state.checkpoints) == 1
    assert state.checkpoints[0].label == "phase-2.3 close"

    # Audit event written
    from cli.core.audit import get_chain_for_project
    chain = get_chain_for_project(proj)
    types = [ev["type"] for ev in chain.iter_events()]
    assert "loop.checkpoint" in types


def test_loop_resume_returns_next_pending(tmp_path, monkeypatch, capsys):
    proj = _make_session(tmp_path)
    monkeypatch.chdir(proj)
    from cli.commands.loop import resume
    # resume() returns normally (exit 0) when there's a pending goal,
    # and prints the next-up id to the console.
    resume()  # should not raise
    out = capsys.readouterr().out
    assert "g2" in out, f"expected g2 to surface as next executable; got: {out!r}"


def test_loop_resume_exits_when_no_pending(tmp_path, monkeypatch):
    proj = _make_session(tmp_path)
    # Mark all leaf goals done so next_executable returns None.
    sess = proj / ".ai" / "sessions" / "active" / "0001_2026-05-01_test"
    tree = GoalTree.load(sess)
    for tid in ("g2", "g3"):
        tree.set_status(tid, "running")
        tree.set_status(tid, "done")
    tree.save(sess)

    monkeypatch.chdir(proj)
    from cli.commands.loop import resume
    import typer
    with pytest.raises(typer.Exit) as exc_info:
        resume()
    assert exc_info.value.exit_code == 0
