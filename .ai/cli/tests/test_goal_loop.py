"""Phase 1 — Goal Loop runtime tests.

Spec ref: docs/specs/03_GOAL_LOOP_SPEC.md
          docs/specs/04_GRAPH_SPEC.md
          .ai/shims/{vvv,nnn,gogogo}/SHIM.md
          Decisions D9 (audit chain), D10 (decided_by), D11 (budget breach).

Coverage:

  Loop engine (graph-driven state machine)
    - test_loop_fires_valid_transition
    - test_loop_rejects_unknown_trigger
    - test_loop_rejects_wrong_decided_by (D10)
    - test_loop_validates_graph_schema
    - test_loop_uses_fixture_graph (proves engine isn't standard.yaml-specific)

  Budget
    - test_budget_pass
    - test_budget_breach
    - test_budget_override

  E2E
    - test_e2e_full_loop — sss -> vvv -> nnn -> gogogo -> ddd -> rrr;
      audit chain validates after every transition; chain depth grows by
      exactly the expected count.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest
import yaml

# `.ai/` is on sys.path via conftest.py.
from cli.core.audit import AuditChain
from cli.core.budget import Budget, BudgetVerdict
from cli.core.loop import (
    DecidedByMismatch,
    GraphInvalid,
    Loop,
    TransitionNotFound,
)
from cli.core.state import SessionLocalState


# ─────────── helpers ───────────


STANDARD_GRAPH_YAML = """
version: "1.0"
name: standard
description: "test fixture mirroring real standard.yaml"
states:
  - READY
  - THINK
  - SANDBOX
  - DO
  - VERIFIED
  - PROMOTED
  - DEPLOYED
  - RETRO
  - DONE
initial_state: READY
terminal_states: [DONE]
transitions:
  - { from: READY,    to: THINK,    trigger: sss,              decided_by: kernel }
  - { from: THINK,    to: SANDBOX,  trigger: nnn_pass,         decided_by: kernel }
  - { from: SANDBOX,  to: DO,       trigger: vvv_pass,         decided_by: verifier }
  - { from: DO,       to: VERIFIED, trigger: gogogo_complete,  decided_by: verifier }
  - { from: VERIFIED, to: PROMOTED, trigger: promote_request,  decided_by: human }
  - { from: PROMOTED, to: DEPLOYED, trigger: deploy_request,   decided_by: human }
  - { from: DEPLOYED, to: RETRO,    trigger: rrr,              decided_by: kernel }
  - { from: RETRO,    to: DONE,     trigger: rrr_complete,     decided_by: kernel }
  - { from: VERIFIED, to: RETRO,    trigger: rrr,              decided_by: kernel }
"""


TINY_GRAPH_YAML = """
version: "1.0"
name: tiny
description: "minimal fixture (proves engine isn't standard-specific)"
states: [A, B, C]
initial_state: A
terminal_states: [C]
transitions:
  - { from: A, to: B, trigger: go, decided_by: kernel }
  - { from: B, to: C, trigger: stop, decided_by: human }
"""


LOOP_BUDGET_YAML = """
version: "1.0"
default_budget:
  max_iterations: 20
  max_duration_minutes: 30
  max_tool_calls: 100
  checkpoint_every: 5
escalation:
  on_iterations_exceeded: NEEDS_HUMAN
  on_duration_exceeded: NEEDS_HUMAN
  on_tool_calls_exceeded: NEEDS_HUMAN
  notify_human: true
overrides: {}
"""


def _make_project(
    tmp_path: Path,
    graphs: Dict[str, str] = None,
    with_budget: bool = False,
) -> Tuple[Path, Path]:
    """Build a minimal Trinity project tree under tmp_path. Returns
    (project_root, session_path)."""
    project = tmp_path / "proj"
    (project / ".ai" / "audit").mkdir(parents=True)
    (project / ".ai" / "graphs").mkdir(parents=True)
    (project / ".ai" / "policies").mkdir(parents=True)
    (project / ".ai" / "sessions").mkdir(parents=True)
    graphs = graphs or {"standard": STANDARD_GRAPH_YAML}
    for name, body in graphs.items():
        (project / ".ai" / "graphs" / f"{name}.yaml").write_text(body)
    if with_budget:
        (project / ".ai" / "policies" / "loop-budget.yaml").write_text(
            LOOP_BUDGET_YAML
        )
    session = project / ".ai" / "sessions" / "sess_test"
    (session / ".state").mkdir(parents=True)
    (session / "THINK").mkdir(parents=True)
    return project, session


# ─────────── Loop engine ───────────


def test_loop_fires_valid_transition(tmp_path: Path):
    project, session = _make_project(tmp_path)
    loop = Loop(session, graph_name="standard", project_root=project)
    assert loop.current() == "READY"
    new = loop.fire("sss", decided_by="kernel", evidence={"task": "demo"})
    assert new == "THINK"
    assert loop.current() == "THINK"


def test_loop_rejects_unknown_trigger(tmp_path: Path):
    project, session = _make_project(tmp_path)
    loop = Loop(session, graph_name="standard", project_root=project)
    with pytest.raises(TransitionNotFound):
        loop.fire("totally_made_up", decided_by="kernel")


def test_loop_rejects_wrong_decided_by(tmp_path: Path):
    project, session = _make_project(tmp_path)
    loop = Loop(session, graph_name="standard", project_root=project)
    # sss requires decided_by=kernel; passing 'human' is a D10 violation
    with pytest.raises(DecidedByMismatch):
        loop.fire("sss", decided_by="human")


def test_loop_validates_graph_schema(tmp_path: Path):
    bad_yaml = """
version: "1.0"
name: bad
states: [A, B]
initial_state: A
transitions:
  - { from: A, to: B, trigger: x }
"""  # missing decided_by → D10 violation
    project, session = _make_project(tmp_path, graphs={"bad": bad_yaml})
    with pytest.raises(GraphInvalid):
        Loop(session, graph_name="bad", project_root=project)


def test_loop_uses_fixture_graph(tmp_path: Path):
    """Engine must work with any well-formed graph, not just standard.yaml."""
    project, session = _make_project(tmp_path, graphs={"tiny": TINY_GRAPH_YAML})
    loop = Loop(session, graph_name="tiny", project_root=project)
    assert loop.current() == "A"
    loop.fire("go", decided_by="kernel")
    assert loop.current() == "B"
    loop.fire("stop", decided_by="human")
    assert loop.current() == "C"
    assert loop.is_terminal()


# ─────────── Budget ───────────


def test_budget_pass(tmp_path: Path):
    policy = tmp_path / "loop-budget.yaml"
    policy.write_text(LOOP_BUDGET_YAML)
    b = Budget(policy_path=policy, project_root=tmp_path)
    v = b.check(
        {
            "estimated_iterations": 10,
            "estimated_duration_minutes": 20,
            "estimated_tool_calls": 50,
        },
        graph_name="standard",
    )
    assert v.ok is True
    assert v.breaches == []


def test_budget_breach(tmp_path: Path):
    policy = tmp_path / "loop-budget.yaml"
    policy.write_text(LOOP_BUDGET_YAML)
    b = Budget(policy_path=policy, project_root=tmp_path)
    v = b.check(
        {
            "estimated_iterations": 25,
            "estimated_duration_minutes": 60,
            "estimated_tool_calls": 50,
        },
        graph_name="standard",
    )
    assert v.ok is False
    breach_caps = sorted(br["cap"] for br in v.breaches)
    assert breach_caps == ["max_duration_minutes", "max_iterations"]


def test_budget_override(tmp_path: Path):
    policy = tmp_path / "loop-budget.yaml"
    policy.write_text(LOOP_BUDGET_YAML)
    b = Budget(policy_path=policy, project_root=tmp_path)
    v = b.check(
        {
            "estimated_iterations": 10,
            "estimated_duration_minutes": 150,
            "estimated_tool_calls": 50,
            "budget_override": {
                "max_duration_minutes": 180,
                "decided_by": "human",
                "reason": "epic-scale Phase 1",
            },
        },
        graph_name="standard",
    )
    assert v.ok is True
    assert len(v.overrides_applied) == 1
    assert v.overrides_applied[0]["cap"] == "max_duration_minutes"


# ─────────── E2E ───────────


def test_e2e_full_loop(tmp_path: Path):
    """Walk sss -> THINK -> SANDBOX -> DO -> VERIFIED -> PROMOTED -> DEPLOYED
    -> RETRO -> DONE. Assert chain.validate() after every transition and
    chain depth grows by exactly one per fire()."""
    project, session = _make_project(tmp_path)
    loop = Loop(session, graph_name="standard", project_root=project)
    chain = loop.chain

    transitions = [
        ("sss", "kernel", "THINK"),
        ("nnn_pass", "kernel", "SANDBOX"),
        ("vvv_pass", "verifier", "DO"),
        ("gogogo_complete", "verifier", "VERIFIED"),
        ("promote_request", "human", "PROMOTED"),
        ("deploy_request", "human", "DEPLOYED"),
        ("rrr", "kernel", "RETRO"),
        ("rrr_complete", "kernel", "DONE"),
    ]

    pre_count = sum(1 for _ in chain.iter_events())

    for i, (trigger, authority, expected) in enumerate(transitions, start=1):
        new = loop.fire(trigger, decided_by=authority, evidence={"i": i})
        assert new == expected, f"step {i}: expected {expected} got {new}"
        chain.validate()  # raises on any chain break
        depth = sum(1 for _ in chain.iter_events())
        assert depth == pre_count + i, (
            f"step {i}: chain depth {depth} != expected {pre_count + i}"
        )

    assert loop.current() == "DONE"
    assert loop.is_terminal()

    # Final assertion: every recorded transition lists the right authority.
    events = list(chain.iter_events())[-len(transitions):]
    for ev, (trigger, authority, _) in zip(events, transitions):
        assert ev["type"] == "graph.transition"
        assert ev["details"]["trigger"] == trigger
        assert ev["details"]["decided_by"] == authority


def test_e2e_nondeploy_loop_skips_ddd(tmp_path: Path):
    """Walk sss -> vvv -> nnn -> gogogo -> rrr -> DONE without a ddd
    promote/deploy pair. This covers documentation/refactor/admin work."""
    project, session = _make_project(tmp_path)
    loop = Loop(session, graph_name="standard", project_root=project)

    transitions = [
        ("sss", "kernel", "THINK"),
        ("nnn_pass", "kernel", "SANDBOX"),
        ("vvv_pass", "verifier", "DO"),
        ("gogogo_complete", "verifier", "VERIFIED"),
        ("rrr", "kernel", "RETRO"),
        ("rrr_complete", "kernel", "DONE"),
    ]

    for i, (trigger, authority, expected) in enumerate(transitions, start=1):
        new = loop.fire(trigger, decided_by=authority, evidence={"i": i})
        assert new == expected

    assert loop.current() == "DONE"
    events = list(loop.chain.iter_events())
    triggers = [ev["details"]["trigger"] for ev in events]
    assert "promote_request" not in triggers
    assert "deploy_request" not in triggers


def test_loop_reconciles_from_audit_on_init(tmp_path: Path):
    """R6 — Loop.__init__ should pick up the latest graph.transition for
    its session_id from the audit chain even when session_state.json was
    never updated (manual-bootstrap scenario)."""
    project, session = _make_project(tmp_path)
    chain = AuditChain(project / ".ai" / "audit" / "events.ndjson")
    # Simulate a manual session walk that wrote audit but skipped state
    chain.append(
        "graph.transition",
        {
            "session_id": session.name,
            "graph": "standard",
            "from_state": "READY",
            "to_state": "THINK",
            "trigger": "sss",
            "decided_by": "kernel",
        },
    )
    chain.append(
        "graph.transition",
        {
            "session_id": session.name,
            "graph": "standard",
            "from_state": "THINK",
            "to_state": "SANDBOX",
            "trigger": "nnn_pass",
            "decided_by": "kernel",
        },
    )
    # session_state.json never written → graph_state should still be None
    assert SessionLocalState(session).graph_state() is None
    loop = Loop(session, graph_name="standard", project_root=project)
    # After init, reconciliation should have set graph_state to SANDBOX
    assert loop.current() == "SANDBOX"
    assert SessionLocalState(session).graph_state() == "SANDBOX"


def test_loop_reconciles_only_for_matching_session_id(tmp_path: Path):
    """Reconciliation must filter by session_id; transitions for OTHER
    sessions must not affect this Loop."""
    project, session = _make_project(tmp_path)
    chain = AuditChain(project / ".ai" / "audit" / "events.ndjson")
    # Other session's transition — must be ignored
    chain.append(
        "graph.transition",
        {
            "session_id": "some_other_session",
            "graph": "standard",
            "from_state": "READY",
            "to_state": "DONE",
            "trigger": "sss",
            "decided_by": "kernel",
        },
    )
    loop = Loop(session, graph_name="standard", project_root=project)
    # No matching event for this session → falls back to initial_state
    assert loop.current() == "READY"


def test_e2e_uses_real_standard_yaml():
    """Sanity check: the project's actual standard.yaml passes Loop's
    schema validation (catches drift between graph file and engine)."""
    repo_root = Path(__file__).resolve().parents[3]
    standard = repo_root / ".ai" / "graphs" / "standard.yaml"
    if not standard.exists():
        pytest.skip(f"missing {standard}")
    data = yaml.safe_load(standard.read_text())
    # We don't need a session — just verify the schema parses.
    # Use Loop's validators by constructing a synthetic project.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        proj = tmp_p / "proj"
        (proj / ".ai" / "graphs").mkdir(parents=True)
        (proj / ".ai" / "audit").mkdir(parents=True)
        (proj / ".ai" / "graphs" / "standard.yaml").write_text(
            standard.read_text()
        )
        sess = proj / ".ai" / "sessions" / "x"
        (sess / ".state").mkdir(parents=True)
        Loop(sess, graph_name="standard", project_root=proj)  # raises on bad
    assert data["name"] == "standard"
