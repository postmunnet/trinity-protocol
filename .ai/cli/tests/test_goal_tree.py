"""Phase 5 — goal tree tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.goal_tree import (
    ALLOWED_TRANSITIONS,
    Goal,
    GoalTree,
    GoalTreeError,
    VALID_STATUSES,
    VALID_TYPES,
)


def _g(id_: str, parent: str = None, status: str = "pending", type_: str = "task") -> Goal:
    return Goal(id=id_, type=type_, description=id_, parent=parent, status=status)


# ─────────── add / get / children ───────────


def test_add_goal_sets_root_when_first():
    tree = GoalTree(session_id="s")
    root = tree.add_goal(_g("g1", type_="epic"))
    assert tree.root_goal_id == "g1"
    assert tree.get("g1") is root


def test_add_goal_rejects_self_parent():
    tree = GoalTree(session_id="s")
    bad = Goal(id="g1", type="task", description="x", parent="g1")
    with pytest.raises(GoalTreeError):
        tree.add_goal(bad)


def test_add_goal_requires_existing_parent():
    tree = GoalTree(session_id="s")
    tree.add_goal(_g("g1", type_="epic"))
    with pytest.raises(GoalTreeError):
        tree.add_goal(_g("g2", parent="ghost"))


def test_children_returns_only_direct():
    tree = GoalTree(session_id="s")
    tree.add_goal(_g("g1", type_="epic"))
    tree.add_goal(_g("g2", parent="g1", type_="feature"))
    tree.add_goal(_g("g3", parent="g2"))
    tree.add_goal(_g("g4", parent="g1", type_="feature"))
    assert {c.id for c in tree.children("g1")} == {"g2", "g4"}
    assert {c.id for c in tree.children("g2")} == {"g3"}


def test_invalid_type_rejected():
    with pytest.raises(GoalTreeError):
        Goal.from_dict({"id": "g1", "type": "saga", "description": "x"})


# ─────────── status state machine ───────────


def test_status_transition_legal():
    tree = GoalTree(session_id="s")
    tree.add_goal(_g("g1"))
    tree.set_status("g1", "running")
    assert tree.get("g1").status == "running"
    tree.set_status("g1", "done")
    assert tree.get("g1").status == "done"
    assert tree.get("g1").completed_at is not None


def test_status_transition_illegal():
    tree = GoalTree(session_id="s")
    tree.add_goal(_g("g1"))
    # pending → done is NOT allowed (must pass through running)
    with pytest.raises(GoalTreeError):
        tree.set_status("g1", "done")


def test_status_terminal_cannot_change():
    tree = GoalTree(session_id="s")
    tree.add_goal(_g("g1"))
    tree.set_status("g1", "running")
    tree.set_status("g1", "done")
    with pytest.raises(GoalTreeError):
        tree.set_status("g1", "running")


def test_set_status_records_last_verdict():
    tree = GoalTree(session_id="s")
    tree.add_goal(_g("g1"))
    tree.set_status("g1", "running", last_verdict="PASS")
    assert tree.get("g1").last_verdict == "PASS"


def test_allowed_transitions_cover_all_statuses():
    assert set(ALLOWED_TRANSITIONS) == VALID_STATUSES
    for src, dests in ALLOWED_TRANSITIONS.items():
        for dst in dests:
            assert dst in VALID_STATUSES


# ─────────── aggregation ───────────


def _build_tree() -> GoalTree:
    tree = GoalTree(session_id="s")
    tree.add_goal(_g("e1", type_="epic"))
    tree.add_goal(_g("f1", parent="e1", type_="feature"))
    tree.add_goal(_g("t1", parent="f1"))
    tree.add_goal(_g("t2", parent="f1"))
    tree.add_goal(_g("f2", parent="e1", type_="feature"))
    tree.add_goal(_g("t3", parent="f2"))
    return tree


def test_aggregate_leaf_returns_self():
    tree = _build_tree()
    assert tree.aggregate_status("t1") == "pending"


def test_aggregate_all_done_rolls_up_done():
    tree = _build_tree()
    for tid in ("t1", "t2", "t3"):
        tree.set_status(tid, "running")
        tree.set_status(tid, "done")
    assert tree.aggregate_status("f1") == "done"
    assert tree.aggregate_status("e1") == "done"


def test_aggregate_any_dead_rolls_up_dead():
    tree = _build_tree()
    tree.set_status("t1", "dead")
    assert tree.aggregate_status("f1") == "dead"
    assert tree.aggregate_status("e1") == "dead"


def test_aggregate_running_takes_priority_over_blocked():
    tree = _build_tree()
    tree.set_status("t1", "running")
    tree.set_status("t2", "blocked")
    assert tree.aggregate_status("f1") == "running"


def test_aggregate_needs_human_beats_blocked_pending():
    tree = _build_tree()
    tree.set_status("t1", "running")
    tree.set_status("t1", "needs_human")
    tree.set_status("t2", "blocked")
    assert tree.aggregate_status("f1") == "needs_human"


# ─────────── queue / resume ───────────


def test_next_executable_returns_first_pending_leaf():
    tree = _build_tree()
    n = tree.next_executable()
    assert n is not None and n.id == "t1"


def test_next_executable_skips_running_and_blocked():
    tree = _build_tree()
    tree.set_status("t1", "running")
    tree.set_status("t2", "blocked")
    n = tree.next_executable()
    assert n is not None and n.id == "t3"


def test_list_pending_includes_running_leaves():
    tree = _build_tree()
    tree.set_status("t1", "running")
    pending = [g.id for g in tree.list_pending()]
    assert "t1" in pending
    assert "t2" in pending
    assert "t3" in pending
    assert "e1" not in pending  # not a leaf
    assert "f1" not in pending


# ─────────── persistence ───────────


def test_save_and_load_roundtrip(tmp_path: Path):
    tree = _build_tree()
    tree.set_status("t1", "running")
    tree.set_status("t1", "done", last_verdict="PASS")
    tree.save(tmp_path)
    p = GoalTree.path_for(tmp_path)
    assert p.exists()

    reloaded = GoalTree.load(tmp_path)
    assert reloaded.session_id == tree.session_id
    assert reloaded.root_goal_id == "e1"
    assert {g.id for g in reloaded.all_goals()} == {
        "e1", "f1", "t1", "t2", "f2", "t3"
    }
    assert reloaded.get("t1").status == "done"
    assert reloaded.get("t1").last_verdict == "PASS"
    assert reloaded.get("t1").completed_at


def test_load_missing_file_errors(tmp_path: Path):
    with pytest.raises(GoalTreeError):
        GoalTree.load(tmp_path)


def test_load_rejects_unknown_schema_version(tmp_path: Path):
    p = GoalTree.path_for(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("version: 999\nsession_id: s\nroot_goal_id: null\ngoals: []\n")
    with pytest.raises(GoalTreeError):
        GoalTree.load(tmp_path)


def test_load_validates_orphan_parent_reference(tmp_path: Path):
    import yaml as _yaml
    p = GoalTree.path_for(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_yaml.safe_dump({
        "version": 1,
        "session_id": "s",
        "root_goal_id": "g1",
        "goals": [
            {"id": "g1", "type": "epic", "description": "x", "parent": None},
            {"id": "g2", "type": "task", "description": "y", "parent": "ghost"},
        ],
    }))
    with pytest.raises(GoalTreeError):
        GoalTree.load(tmp_path)


def test_valid_types_set_is_canonical():
    assert VALID_TYPES == {"epic", "feature", "task", "subtask"}
