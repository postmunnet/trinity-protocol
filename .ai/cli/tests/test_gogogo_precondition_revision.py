"""S11 gogogo contract_revision precondition tests (Spec line 795).

Verifies the normative MUST: 'gogogo refuses to run when the contract's
contract_revision mismatches the plan envelope.'

Three cases:
  (a) verification_contract.json absent  → no precondition events, gogogo runs
  (b) revisions match (or both default to 0) → gogogo.precondition_ok + run
  (c) revisions mismatch → gogogo.precondition_failed + Exit(1), no step loop
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
import typer
import yaml

from cli.commands.gogogo import _run
from cli.core.audit import AuditChain
from cli.core.loop import Loop

from test_goal_loop import _make_project


VERIFIER_RULES_YAML = (
    Path(__file__).resolve().parent.parent.parent
    / "policies"
    / "verifier-rules.yaml"
).read_text()


def _seed_at_do(tmp_path: Path) -> Tuple[Path, Path]:
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
    assert loop.current() == "DO"
    (sess / ".state" / "vvv_pass").write_text("ok")
    (sess / ".state" / "nnn_pass").write_text("ok")
    return proj, sess


def _write_plan(sess: Path, steps: List[Dict[str, Any]], contract_revision: int = 0) -> None:
    plan = {"steps": steps, "contract_revision": contract_revision}
    (sess / ".state" / "plan.json").write_text(json.dumps(plan))


def _write_verification_contract(sess: Path, contract_revision: int) -> None:
    contract = {
        "id": "vc-test",
        "description": "test contract",
        "version": "1.0",
        "contract_revision": contract_revision,
        "acceptance": [],
    }
    (sess / "THINK" / "verification_contract.json").write_text(json.dumps(contract))


def _chain_events(proj: Path) -> List[Dict[str, Any]]:
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    return list(chain.iter_events())


# ─── (a) verification_contract.json absent → no precondition events ──


def test_no_contract_no_precondition_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_plan(sess, [{"n": 1, "title": "smoke"}])
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "gogogo.precondition_ok" not in types
    assert "gogogo.precondition_failed" not in types


# ─── (b) revisions match → precondition_ok emitted ───────────────────


def test_matching_revisions_emit_precondition_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_plan(sess, [{"n": 1, "title": "smoke"}], contract_revision=3)
    _write_verification_contract(sess, contract_revision=3)
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "gogogo.precondition_ok" in types
    assert "gogogo.precondition_failed" not in types

    ok = [e for e in events if e["type"] == "gogogo.precondition_ok"][0]
    assert ok["details"]["contract_revision"] == 3
    assert ok["details"]["plan_envelope_revision"] == 3


def test_both_defaults_to_zero_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Back-compat: both missing contract_revision keys → default 0 vs 0 = match."""
    proj, sess = _seed_at_do(tmp_path)
    _write_plan(sess, [{"n": 1, "title": "smoke"}])  # no revision
    # Write contract with NO contract_revision key
    contract = {"id": "vc", "description": "x", "version": "1.0", "acceptance": []}
    (sess / "THINK" / "verification_contract.json").write_text(json.dumps(contract))
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "gogogo.precondition_ok" in types
    ok = [e for e in events if e["type"] == "gogogo.precondition_ok"][0]
    assert ok["details"]["contract_revision"] == 0
    assert ok["details"]["plan_envelope_revision"] == 0


# ─── (c) revisions mismatch → precondition_failed + Exit(1) ──────────


def test_mismatched_revisions_refuse_and_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_plan(sess, [{"n": 1, "title": "would-not-run"}], contract_revision=1)
    _write_verification_contract(sess, contract_revision=2)  # mismatch
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "gogogo.precondition_failed" in types
    failed = [e for e in events if e["type"] == "gogogo.precondition_failed"][0]
    assert failed["details"]["reason"] == "contract_revision_mismatch"
    assert failed["details"]["contract_revision"] == 2
    assert failed["details"]["plan_envelope_revision"] == 1

    # Crucially: step loop never ran → no gogogo.step_started
    assert "gogogo.step_started" not in types
    assert "gogogo.completed" not in types


def test_mismatched_revisions_order_chain_invoked_then_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chain ordering: gogogo.invoked precedes precondition_failed."""
    proj, sess = _seed_at_do(tmp_path)
    _write_plan(sess, [{"n": 1, "title": "x"}], contract_revision=5)
    _write_verification_contract(sess, contract_revision=99)
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit):
        _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    invoked_idx = types.index("gogogo.invoked")
    failed_idx = types.index("gogogo.precondition_failed")
    assert invoked_idx < failed_idx
