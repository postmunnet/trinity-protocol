"""T0.4 — DEAD entry (ADR-0001, Option A).

Covers:
  - graph: the 6 Option-A DEAD transitions are valid, DEAD is reachable, no
    ANY->DEAD, every DEAD transition carries decided_by (verifier|human) and
    human transitions carry require_human_approval.
  - terminal path: a Loop fires verify_dead DO->DEAD and emits a graph.transition
    audit (the mechanism gogogo uses to close the orphaned-terminal-DEAD gap).
  - routing: gogogo._dead_is_terminal is rule-derived, default false.
  - operator_abort: DO->DEAD requires decided_by=human (verifier rejected).
  - close: DEAD is in the close terminal set (sealable as failure).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cli.commands.gogogo import _dead_is_terminal
from cli.core.loop import DecidedByMismatch, Loop
from cli.core.terminal_states import get_terminal_states_for_close

from test_goal_loop import _make_project


REAL_STANDARD = Path(__file__).resolve().parents[2] / "graphs" / "standard.yaml"


# Fixture graph: the test-goal-loop standard mirror + Option-A DEAD entry.
STANDARD_WITH_DEAD = """
version: "1.0"
name: standard
description: "fixture with ADR-0001 DEAD entry"
states: [READY, THINK, SANDBOX, DO, VERIFIED, PROMOTED, DEPLOYED, RETRO, DONE, DEAD]
initial_state: READY
terminal_states: [DONE, DEAD]
transitions:
  - { from: READY,    to: THINK,    trigger: sss,             decided_by: kernel }
  - { from: SANDBOX,  to: DO,       trigger: nnn_pass,        decided_by: kernel }
  - { from: THINK,    to: SANDBOX,  trigger: vvv_pass,        decided_by: verifier }
  - { from: DO,       to: VERIFIED, trigger: gogogo_complete, decided_by: verifier }
  - { from: VERIFIED, to: RETRO,    trigger: rrr,             decided_by: kernel }
  - { from: RETRO,    to: DONE,     trigger: rrr_complete,    decided_by: kernel }
  - { from: DO,       to: DEAD,     trigger: verify_dead,            decided_by: verifier }
  - { from: THINK,    to: DEAD,     trigger: operator_abort,         decided_by: human, require_human_approval: true }
  - { from: SANDBOX,  to: DEAD,     trigger: operator_abort,         decided_by: human, require_human_approval: true }
  - { from: DO,       to: DEAD,     trigger: operator_abort,         decided_by: human, require_human_approval: true }
  - { from: VERIFIED, to: DEAD,     trigger: operator_abort,         decided_by: human, require_human_approval: true }
  - { from: RETRO,    to: DEAD,     trigger: retro_integrity_failed, decided_by: verifier }
"""


# ─────────── graph-level (A1) ───────────


def _real_dead_transitions():
    d = yaml.safe_load(REAL_STANDARD.read_text())
    return [t for t in d["transitions"] if t["to"] == "DEAD"]


def test_graph_dead_transitions_present_and_valid():
    """Real standard.yaml declares the 6 Option-A DEAD edges, no ANY, decided_by."""
    edges = {(t["from"], t["trigger"], t["decided_by"]) for t in _real_dead_transitions()}
    expected = {
        ("DO", "verify_dead", "verifier"),
        ("THINK", "operator_abort", "human"),
        ("SANDBOX", "operator_abort", "human"),
        ("DO", "operator_abort", "human"),
        ("VERIFIED", "operator_abort", "human"),
        ("RETRO", "retro_integrity_failed", "verifier"),
    }
    assert expected <= edges
    assert all(f != "ANY" for f, _, _ in edges)


def test_graph_dead_reachable_and_human_aborts_gated():
    d = yaml.safe_load(REAL_STANDARD.read_text())
    assert "DEAD" in d["states"]
    assert "DEAD" in d["terminal_states"]
    for t in _real_dead_transitions():
        assert t.get("decided_by") in ("verifier", "human")
        if t["decided_by"] == "human":
            assert t.get("require_human_approval") is True


def test_graph_no_any_into_dead():
    assert all(t["from"] != "ANY" for t in _real_dead_transitions())


# ─────────── terminal path mechanism (A2) ───────────


def test_loop_fire_verify_dead_terminal_transitions_do_to_dead(tmp_path):
    """The terminal mechanism: fire verify_dead DO->DEAD + graph.transition audit."""
    project, session = _make_project(tmp_path, graphs={"standard": STANDARD_WITH_DEAD})
    loop = Loop(session, graph_name="standard", project_root=project)
    loop.state.set_graph_state("DO")
    loop.fire("verify_dead", decided_by="verifier", evidence={"rule_set": "rs_x"})
    assert loop.current() == "DEAD"
    evs = [e for e in loop.chain.iter_events() if e.get("type") == "graph.transition"]
    assert any(
        e["details"].get("to_state") == "DEAD"
        and e["details"].get("trigger") == "verify_dead"
        for e in evs
    )


def test_loop_dead_is_terminal_sink(tmp_path):
    """DEAD is a true sink — terminal guard blocks firing out of it."""
    project, session = _make_project(tmp_path, graphs={"standard": STANDARD_WITH_DEAD})
    loop = Loop(session, graph_name="standard", project_root=project)
    loop.state.set_graph_state("DEAD")
    assert loop.is_terminal("DEAD")


# ─────────── routing helper (A2 terminal / A3 non-terminal) ───────────


def test_dead_is_terminal_routing_terminal_rule():
    doc = {"verifier_rules": {"rs_fatal": {"dead_is_terminal": True, "dead_when": []}}}
    assert _dead_is_terminal("rs_fatal", doc) is True


def test_dead_is_terminal_routing_non_terminal_when_flag_absent():
    doc = {"verifier_rules": {"rs_plain": {"dead_when": []}}}
    assert _dead_is_terminal("rs_plain", doc) is False


def test_dead_is_terminal_routing_non_terminal_when_flag_false():
    doc = {"verifier_rules": {"rs_soft": {"dead_is_terminal": False}}}
    assert _dead_is_terminal("rs_soft", doc) is False


def test_dead_is_terminal_routing_unknown_rule_defaults_false():
    assert _dead_is_terminal("missing", {"verifier_rules": {}}) is False
    assert _dead_is_terminal("missing", {}) is False


# ─────────── operator_abort authority (A4) ───────────


def test_operator_abort_requires_human(tmp_path):
    project, session = _make_project(tmp_path, graphs={"standard": STANDARD_WITH_DEAD})
    loop = Loop(session, graph_name="standard", project_root=project)
    loop.state.set_graph_state("DO")
    loop.fire("operator_abort", decided_by="human")
    assert loop.current() == "DEAD"


def test_operator_abort_rejects_non_human_authority(tmp_path):
    project, session = _make_project(tmp_path, graphs={"standard": STANDARD_WITH_DEAD})
    loop = Loop(session, graph_name="standard", project_root=project)
    loop.state.set_graph_state("DO")
    with pytest.raises(DecidedByMismatch):
        loop.fire("operator_abort", decided_by="verifier")
    assert loop.current() == "DO"


# ─────────── close (A4) ───────────


def test_close_terminal_set_includes_dead():
    """close seals DEAD as a terminal failure archive (never re-marked success)."""
    project_root = Path(__file__).resolve().parents[3]
    terminals = get_terminal_states_for_close(project_root)
    assert "DEAD" in terminals
    assert "DONE" in terminals


# ─────────── production classification liveness (rule-classification batch) ───────────


REAL_RULES = Path(__file__).resolve().parents[2] / "policies" / "verifier-rules.yaml"


def test_production_rules_terminal_classification_is_live():
    """The production verifier-rules.yaml classifies the three operator-ruled
    terminal rule-sets (true). step_complete is now per-predicate; with no
    matched predicate it is non-terminal. browser_check stays non-terminal."""
    doc = yaml.safe_load(REAL_RULES.read_text())
    assert _dead_is_terminal("code_change", doc) is True
    assert _dead_is_terminal("deploy_check", doc) is True
    assert _dead_is_terminal("memory_promote", doc) is True
    assert _dead_is_terminal("step_complete", doc) is False
    assert _dead_is_terminal("browser_check", doc) is False


# ─────────── per-predicate granularity (overload bool|list) ───────────


def _doc(cfg):
    return {"verifier_rules": {"rs": {"dead_is_terminal": cfg}}}


def test_overload_bool_true_all_predicates_terminal():
    # backward compat: true means any matched predicate is terminal
    assert _dead_is_terminal("rs", _doc(True), ["anything"]) is True
    assert _dead_is_terminal("rs", _doc(True), []) is True
    assert _dead_is_terminal("rs", _doc(True)) is True  # default ()


def test_overload_bool_false_and_missing_non_terminal():
    assert _dead_is_terminal("rs", _doc(False), ["x"]) is False
    assert _dead_is_terminal("rs", _doc(None), ["x"]) is False
    assert _dead_is_terminal("rs", {"verifier_rules": {"rs": {}}}, ["x"]) is False


def test_overload_list_hit_is_terminal():
    cfg = ["sandbox_violation", "forbidden_pattern_found"]
    assert _dead_is_terminal("rs", _doc(cfg), ["sandbox_violation"]) is True
    assert _dead_is_terminal("rs", _doc(cfg), ["other", "forbidden_pattern_found"]) is True


def test_overload_list_miss_is_non_terminal():
    cfg = ["sandbox_violation", "forbidden_pattern_found"]
    assert _dead_is_terminal("rs", _doc(cfg), ["retry_budget_exhausted"]) is False
    assert _dead_is_terminal("rs", _doc(cfg), []) is False


def test_overload_invalid_type_is_conservative_non_terminal():
    # a string / dict / int is neither bool nor list → conservative False, never DEAD
    assert _dead_is_terminal("rs", _doc("sandbox_violation"), ["sandbox_violation"]) is False
    assert _dead_is_terminal("rs", _doc({"x": 1}), ["x"]) is False
    assert _dead_is_terminal("rs", _doc(1), ["x"]) is False


def test_step_complete_per_predicate_live_over_real_rules():
    """Production step_complete: boundary/security predicates terminal,
    retry_budget_exhausted non-terminal; the 3 true rule-sets stay terminal."""
    doc = yaml.safe_load(REAL_RULES.read_text())
    assert _dead_is_terminal("step_complete", doc, ["sandbox_violation"]) is True
    assert _dead_is_terminal("step_complete", doc, ["forbidden_pattern_found"]) is True
    assert _dead_is_terminal("step_complete", doc, ["retry_budget_exhausted"]) is False
    for rs in ("code_change", "deploy_check", "memory_promote"):
        assert _dead_is_terminal(rs, doc, ["whatever"]) is True
