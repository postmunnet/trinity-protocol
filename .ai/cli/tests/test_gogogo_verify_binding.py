"""P0-4 (2026-06-10) — gogogo per-step evidence binding.

A plan step may declare `verify: {command, expect_exit, timeout_seconds}`.
gogogo executes the command and:
  - records a `gogogo.step_evidence` audit event (command/exit/expectation)
  - fails the step loudly (exit 1) on exit-code mismatch
  - keeps steps WITHOUT verify byte-identical to the structural behaviour
  - warns when a medium/high-risk step has no verify binding

Fixture mirrors `_seed_at_do` from test_gogogo_hmac.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
import yaml

from cli.commands.gogogo import _run, _run_step_verify
from cli.core.audit import AuditChain
from cli.core.loop import Loop

from test_goal_loop import _make_project

VERIFIER_RULES_YAML = (
    Path(__file__).resolve().parent.parent.parent
    / "policies"
    / "verifier-rules.yaml"
).read_text()


def _seed_at_do(tmp_path: Path, steps: list) -> tuple:
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
    (sess / ".state" / "plan.json").write_text(json.dumps({"steps": steps}))
    return proj, sess


def _chain_events(proj: Path, type_name: str) -> list:
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    return [ev for ev in chain.iter_events() if ev["type"] == type_name]


# ─── helper unit ─────────────────────────────────────────────────────


def test_run_step_verify_pass(tmp_path: Path) -> None:
    ev = _run_step_verify({"command": "true"}, tmp_path)
    assert ev["ok"] is True
    assert ev["exit_code"] == 0


def test_run_step_verify_mismatch(tmp_path: Path) -> None:
    ev = _run_step_verify({"command": "false"}, tmp_path)
    assert ev["ok"] is False
    assert ev["exit_code"] == 1


def test_run_step_verify_expect_nonzero(tmp_path: Path) -> None:
    ev = _run_step_verify({"command": "false", "expect_exit": 1}, tmp_path)
    assert ev["ok"] is True


# ─── integration: step loop ──────────────────────────────────────────


def test_verify_pass_records_evidence_and_completes(tmp_path: Path, monkeypatch) -> None:
    proj, sess = _seed_at_do(
        tmp_path,
        [{"n": 1, "title": "evidence step", "verify": {"command": "true"}}],
    )
    monkeypatch.chdir(proj)
    _run("step_complete", False)

    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"
    evidence = _chain_events(proj, "gogogo.step_evidence")
    assert len(evidence) == 1
    d = evidence[0]["details"]
    assert d["command"] == "true"
    assert d["exit_code"] == 0
    assert d["evidence_ok"] is True


def test_verify_fail_terminates_with_step_failed(tmp_path: Path, monkeypatch) -> None:
    proj, sess = _seed_at_do(
        tmp_path,
        [{"n": 1, "title": "doomed step", "verify": {"command": "false"}}],
    )
    monkeypatch.chdir(proj)
    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    failed = _chain_events(proj, "gogogo.step_failed")
    assert any(
        "evidence command exit mismatch" in ev["details"].get("verifier_reason", "")
        for ev in failed
    )
    # loop must NOT have advanced to VERIFIED
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "DO"


def test_step_without_verify_unchanged(tmp_path: Path, monkeypatch) -> None:
    proj, sess = _seed_at_do(
        tmp_path,
        [{"n": 1, "title": "plain structural step"}],
    )
    monkeypatch.chdir(proj)
    _run("step_complete", False)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    assert loop.current() == "VERIFIED"
    assert _chain_events(proj, "gogogo.step_evidence") == []


def test_high_risk_without_verify_needs_human(tmp_path: Path, monkeypatch, capsys) -> None:
    # Q24.10 step 4 (opt-A) — behaviour change: a high-risk step with no
    # verify.command no longer structural-PASSes; it stops as NEEDS_HUMAN.
    proj, sess = _seed_at_do(
        tmp_path,
        [{"n": 1, "title": "risky no-evidence step", "risk": "high"}],
    )
    monkeypatch.chdir(proj)
    with pytest.raises(typer.Exit):
        _run("step_complete", False)
    out = capsys.readouterr().out
    assert "NEEDS_HUMAN" in out
    failed = _chain_events(proj, "gogogo.step_failed")
    assert any(
        e["details"]["verifier_verdict"] == "NEEDS_HUMAN"
        and e["details"]["verifier_mode"] == "risk_gate"
        for e in failed
    )


def test_medium_risk_without_verify_warns(tmp_path: Path, monkeypatch, capsys) -> None:
    # medium-risk no-evidence still PASSes (backward-compat) but is warned +
    # marked structural_pass=true in audit.
    proj, sess = _seed_at_do(
        tmp_path,
        [{"n": 1, "title": "medium no-evidence step", "risk": "medium"}],
    )
    monkeypatch.chdir(proj)
    _run("step_complete", False)
    out = capsys.readouterr().out
    assert "no verify" in out
    passed = _chain_events(proj, "gogogo.step_passed")
    assert passed and passed[0]["details"]["structural_pass"] is True
    assert passed[0]["details"]["evidence_mode"] == "structural"


# ─── step_n correlation (2026-06-12) ─────────────────────────────────
# Real-world plan envelopes (and nnn-written plan.json) key steps by
# `id`, while test fixtures historically used `n` — gogogo's step label
# fell back to "?" for every real session, breaking audit correlation.
# gogogo now falls back n → id → "?".


def test_step_n_falls_back_to_id_key(tmp_path: Path, monkeypatch) -> None:
    proj, sess = _seed_at_do(
        tmp_path,
        [{"id": 7, "title": "id-keyed step", "verify": {"command": "true"}}],
    )
    monkeypatch.chdir(proj)
    _run("step_complete", False)

    evidence = _chain_events(proj, "gogogo.step_evidence")
    assert len(evidence) == 1
    assert evidence[0]["details"]["step_n"] == 7, (
        "step keyed by `id` must surface its number in audit events, not '?'"
    )
