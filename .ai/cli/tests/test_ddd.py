"""Phase 5 — `ai ddd` deploy decision gate tests.

Validates:
  - dry-run prints plan and does NOT advance the graph
  - real run advances VERIFIED → PROMOTED → DEPLOYED via decided_by=human
  - deploy_check verifier verdict is captured (PASS when evidence
    supplies all predicates)
  - --target validation
  - rejects when graph_state != VERIFIED
  - --skip-verify omits the verifier evaluation
  - ddd.completed event is appended
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

# Reuse the goal-loop test fixtures (they already build a real graph
# directory + session shape).
from test_goal_loop import STANDARD_GRAPH_YAML, _make_project
from cli.core.audit import AuditChain
from cli.core.loop import Loop


VERIFIER_RULES_YAML = (
    Path(__file__).resolve().parent.parent.parent / "policies" / "verifier-rules.yaml"
).read_text()


def _seed_at_verified(tmp_path: Path):
    """Build a project, seed status.json/ssot.yaml, and advance the
    Loop to VERIFIED. Returns (project_root, session_path)."""
    proj, sess = _make_project(tmp_path)
    # Wire the real rituals tree into the tmp project so ddd.py's load_pack
    # call (which resolves rituals_root from project_root since the
    # per-ritual loader integration in this session) finds the pack.
    rituals_target = proj / ".ai" / "rituals"
    if not rituals_target.exists():
        rituals_target.symlink_to(
            Path(__file__).resolve().parent.parent.parent / "rituals"
        )
    # Drop verifier-rules.yaml + ssot.yaml + status.json so ddd's
    # SSOTLoader and rules loader can find their files.
    (proj / ".ai" / "policies" / "verifier-rules.yaml").write_text(
        VERIFIER_RULES_YAML
    )
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({
            "version": "1.0",
            "paths": {"state": "${ai_root}/state"},
        })
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({
            "version": "1.0",
            "current_session": str(sess),
            "last_event_hash": None,
        })
    )

    # Walk the standard graph to VERIFIED.
    loop = Loop(sess, graph_name="standard", project_root=proj)
    loop.fire("sss", decided_by="kernel")
    loop.fire("nnn_pass", decided_by="kernel")
    loop.fire("vvv_pass", decided_by="verifier")
    loop.fire("gogogo_complete", decided_by="verifier")
    assert loop.current() == "VERIFIED"
    return proj, sess


def test_ddd_dry_run_does_not_advance(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    from cli.commands.ddd import _run

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    before_types = [ev["type"] for ev in chain.iter_events()]
    code = _run(target="dev", reason="dry test", evidence_file=None,
                skip_verify=True, dry_run=True)
    assert code == 0
    # Still VERIFIED — no transition fired
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"
    after_types = [ev["type"] for ev in chain.iter_events()]
    assert after_types == before_types
    assert not (sess / "CAPTURE" / "capture.sqlite").exists()


def test_ddd_advances_to_deployed(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    from cli.commands.ddd import _run

    code = _run(target="dev", reason="real test", evidence_file=None,
                skip_verify=True, dry_run=False)
    assert code == 0
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DEPLOYED"

    # ddd.completed event present
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    types = [ev["type"] for ev in chain.iter_events()]
    assert "ddd.completed" in types


def test_ddd_rejects_invalid_target(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    from cli.commands.ddd import _run

    code = _run(target="staging", reason="x", evidence_file=None,
                skip_verify=True, dry_run=False)
    assert code == 2
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"


def test_ddd_rejects_when_not_verified(tmp_path, monkeypatch):
    proj, sess = _make_project(tmp_path)
    (proj / ".ai" / "policies" / "verifier-rules.yaml").write_text(
        VERIFIER_RULES_YAML
    )
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({"version": "1.0", "current_session": str(sess)})
    )
    monkeypatch.chdir(proj)
    from cli.commands.ddd import _run

    # No transitions fired — still READY
    code = _run(target="dev", reason="x", evidence_file=None,
                skip_verify=True, dry_run=False)
    assert code == 2


def test_ddd_runs_verifier_with_evidence(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)

    # Author evidence that satisfies the deploy_check pass_when set.
    evidence = proj / "deploy_evidence.json"
    evidence.write_text(json.dumps({
        "health_check_ok": True,
        "smoke_tests_pass": True,
        "no_critical_errors_in_log": True,
    }))

    from cli.commands.ddd import _run
    code = _run(target="prod", reason="post-prod check",
                evidence_file=evidence, skip_verify=False, dry_run=False)
    assert code == 0

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    completed = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.completed"
    ]
    assert len(completed) == 1
    verifier = completed[0]["details"]["verifier"]
    assert verifier["verdict"] == "PASS"
    assert verifier["rule_set"] == "deploy_check"


def test_ddd_skip_verify_records_no_verdict(tmp_path, monkeypatch):
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    from cli.commands.ddd import _run
    code = _run(target="dev", reason="skip", evidence_file=None,
                skip_verify=True, dry_run=False)
    assert code == 0
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    completed = [
        ev for ev in chain.iter_events() if ev["type"] == "ddd.completed"
    ]
    assert completed[0]["details"]["verifier"] is None
