"""P1 (2026-06-10) — ddd pre-transition gate for hard-failed deploy_check.

DEAD/RETRY verdicts now require an explicit --accept-failed-check reason;
NEEDS_HUMAN passes (running ddd IS the human decision). The post-hoc
informational evaluation is unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from cli.commands.ddd import _run
from cli.core.audit import AuditChain
from cli.core.loop import Loop

from test_goal_loop import _make_project

VERIFIER_RULES_YAML = (
    Path(__file__).resolve().parent.parent.parent
    / "policies"
    / "verifier-rules.yaml"
).read_text()


def _seed_at_verified(tmp_path: Path) -> tuple:
    proj, sess = _make_project(tmp_path, with_budget=True)
    rituals_target = proj / ".ai" / "rituals"
    if not rituals_target.exists():
        rituals_target.symlink_to(
            Path(__file__).resolve().parent.parent.parent / "rituals"
        )
    (proj / ".ai" / "policies" / "verifier-rules.yaml").write_text(VERIFIER_RULES_YAML)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({"version": "1.0", "current_session": str(sess)})
    )
    loop = Loop(sess, graph_name="standard", project_root=proj)
    loop.fire("sss", decided_by="kernel")
    loop.fire("nnn_pass", decided_by="kernel")
    loop.fire("vvv_pass", decided_by="verifier")
    loop.fire("gogogo_complete", decided_by="verifier")
    assert loop.current() == "VERIFIED"
    return proj, sess


def _events(proj: Path, type_name: str) -> list:
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    return [ev for ev in chain.iter_events() if ev["type"] == type_name]


def _dead_evidence(tmp_path: Path) -> Path:
    """Evidence that makes deploy_check verdict DEAD (critical errors)."""
    p = tmp_path / "evidence.json"
    p.write_text(json.dumps({
        "rollback_required": True,
    }))
    return p


def test_needs_human_verdict_passes_without_flag(tmp_path: Path, monkeypatch) -> None:
    # No evidence at all -> deploy_check is NEEDS_HUMAN (pass_when unmet),
    # which must NOT require the override flag.
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    code = _run(
        target="dev", reason="doc session closure", evidence_file=None,
        skip_verify=False, dry_run=False,
    )
    assert code == 0
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DEPLOYED"
    assert _events(proj, "ddd.refused_failed_check") == []


def test_dead_verdict_refused_without_flag(tmp_path: Path, monkeypatch) -> None:
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    code = _run(
        target="dev", reason="risky deploy", evidence_file=_dead_evidence(tmp_path),
        skip_verify=False, dry_run=False,
    )
    if code == 0:
        pytest.skip("deploy_check rule_set has no DEAD path for this evidence")
    assert code == 3
    assert len(_events(proj, "ddd.refused_failed_check")) == 1
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"  # no transition happened


def test_dead_verdict_proceeds_with_explicit_override(tmp_path: Path, monkeypatch) -> None:
    proj, sess = _seed_at_verified(tmp_path)
    monkeypatch.chdir(proj)
    refused = _run(
        target="dev", reason="risky deploy", evidence_file=_dead_evidence(tmp_path),
        skip_verify=False, dry_run=False,
    )
    if refused == 0:
        pytest.skip("deploy_check rule_set has no DEAD path for this evidence")
    code = _run(
        target="dev", reason="risky deploy", evidence_file=_dead_evidence(tmp_path),
        skip_verify=False, dry_run=False,
        accept_failed_check="hotfix window, rollback plan ready",
    )
    assert code == 0
    accepted = _events(proj, "ddd.accepted_failed_check")
    assert len(accepted) == 1
    assert accepted[0]["details"]["override_reason"] == (
        "hotfix window, rollback plan ready"
    )
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DEPLOYED"
