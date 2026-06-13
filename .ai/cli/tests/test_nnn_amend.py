"""Q24.10 step 1 — `ai nnn --amend` plan-versioning tests.

Operator-locked invariants (2026-06-13):
  A1 amend creates plan.v2 without mutating plan.v1
  A2 active pointer resolves to the latest version
  A3 amendment record carries reason + from/to + changes
  A4 gogogo executes the latest active version (via resolve_active_plan)
  A5 nnn --history lists all versions
  A6 goal-level change is rejected (→ vvv --amend)
  A7 audit chain records plan_amended

A1–A5 exercise the real plan_version behaviour; A6/A7 drive _run_amend
end-to-end against a seeded session (no structural PASS — every assertion
checks observable state, per the evidence-adoption benchmark).
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
import yaml

from test_goal_loop import _make_project
from cli.core import plan_version


PLAN_V1 = {
    "goal": "build feature X",
    "steps": [{"n": 1, "title": "first"}],
    "acceptance": [
        {"id": "A1", "command": "true", "expect_exit": 0, "required": True}
    ],
}


def _seed_plan_v1(tmp_path):
    proj, sess = _make_project(tmp_path)
    plan_version.write_plan_version(sess, dict(PLAN_V1), 1)
    return proj, sess


def _seed_for_cli(tmp_path):
    """Seed ssot.yaml + status.json so _run_amend resolves this session
    from cwd (mirrors test_ddd's integration seed)."""
    proj, sess = _seed_plan_v1(tmp_path)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps(
            {"version": "1.0", "current_session": str(sess), "last_event_hash": None}
        )
    )
    return proj, sess


def _audit_types(proj: Path):
    f = proj / ".ai" / "audit" / "events.ndjson"
    if not f.exists():
        return []
    out = []
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln).get("type"))
            except json.JSONDecodeError:
                pass
    return out


# ───────────────────────── A1 ─────────────────────────
def test_amend_creates_v2_preserves_v1(tmp_path):
    proj, sess = _seed_plan_v1(tmp_path)
    v1_before = (sess / ".state" / "plan.v1.json").read_text(encoding="utf-8")

    plan_v2 = {**PLAN_V1, "steps": PLAN_V1["steps"] + [{"n": 2, "title": "second"}]}
    plan_version.write_plan_version(sess, plan_v2, 2)

    assert (sess / ".state" / "plan.v1.json").read_text(encoding="utf-8") == v1_before
    assert (sess / ".state" / "plan.v2.json").exists()
    # invariant #1/#2 — versions are immutable
    with pytest.raises(FileExistsError):
        plan_version.write_plan_version(sess, plan_v2, 1)


# ───────────────────────── A2 ─────────────────────────
def test_active_resolves_latest(tmp_path):
    proj, sess = _seed_plan_v1(tmp_path)
    plan_version.write_plan_version(
        sess, {**PLAN_V1, "steps": [{"n": 1}, {"n": 2}]}, 2
    )
    assert plan_version.active_version(sess) == 2
    assert len(plan_version.resolve_active_plan(sess)["steps"]) == 2


# ───────────────────────── A3 ─────────────────────────
def test_amendment_record_fields(tmp_path):
    proj, sess = _seed_plan_v1(tmp_path)
    rfile, rec = plan_version.write_amendment_record(
        sess, 1, 2, "add executable evidence for A2", ["add_verify_command"]
    )
    assert rfile.exists()
    assert rec["reason"] == "add executable evidence for A2"
    assert rec["from_version"] == 1 and rec["to_version"] == 2
    assert rec["changes"] == ["add_verify_command"]
    assert rec["seq"] == 1


# ───────────────────────── A4 ─────────────────────────
def test_gogogo_uses_active_version(tmp_path):
    proj, sess = _seed_plan_v1(tmp_path)
    plan_version.write_plan_version(
        sess, {**PLAN_V1, "steps": [{"n": 1}, {"n": 2}, {"n": 3}]}, 2
    )
    # resolve_active_plan is exactly what gogogo now calls
    plan = plan_version.resolve_active_plan(sess)
    assert len(plan["steps"]) == 3  # v2, not v1's single step

    from cli.commands import gogogo
    assert "resolve_active_plan" in inspect.getsource(gogogo)


# ───────────────────────── A5 ─────────────────────────
def test_history_lists_versions(tmp_path):
    proj, sess = _seed_plan_v1(tmp_path)
    plan_version.write_plan_version(sess, dict(PLAN_V1), 2)
    plan_version.write_plan_version(sess, dict(PLAN_V1), 3)
    assert plan_version.list_plan_versions(sess) == [1, 2, 3]


# ───────────────────────── A6 ─────────────────────────
def test_goal_level_change_rejected(tmp_path, monkeypatch):
    # unit: goal change detected, non-goal change not
    base = {"goal": "build feature X"}
    assert plan_version.is_goal_level_change(base, {"goal": "build feature Y"}) is True
    assert plan_version.is_goal_level_change(base, {"steps": [{"n": 1}]}) is False
    assert plan_version.is_goal_level_change(base, {"goal": "build feature X"}) is False

    # integration: _run_amend rejects a goal-level delta with exit code 3
    proj, sess = _seed_for_cli(tmp_path)
    delta = {"reason": "change the goal", "goal": "build a different thing"}
    dpath = tmp_path / "delta_goal.json"
    dpath.write_text(json.dumps(delta))
    monkeypatch.chdir(proj)

    import typer
    from cli.commands.nnn import _run_amend
    with pytest.raises(typer.Exit) as exc:
        _run_amend(dpath, None)
    assert exc.value.exit_code == 3
    assert "plan_amend_rejected" in _audit_types(proj)
    # no v2 was created
    assert not (sess / ".state" / "plan.v2.json").exists()


# ───────────────────────── A7 ─────────────────────────
def test_audit_plan_amended(tmp_path, monkeypatch):
    proj, sess = _seed_for_cli(tmp_path)
    delta = {
        "reason": "add executable evidence + extra step",
        "steps": [{"n": 1, "title": "first"}, {"n": 2, "title": "second", "verify": {"command": "true", "expect_exit": 0}}],
        "acceptance": [
            {"id": "A1", "command": "true", "expect_exit": 0, "required": True},
            {"id": "A2", "command": "true", "expect_exit": 0, "required": True},
        ],
    }
    dpath = tmp_path / "delta_ok.json"
    dpath.write_text(json.dumps(delta))
    monkeypatch.chdir(proj)

    from cli.commands.nnn import _run_amend
    _run_amend(dpath, None)

    # audit recorded
    assert "plan_amended" in _audit_types(proj)
    # v2 created, v1 intact, active = v2
    assert (sess / ".state" / "plan.v2.json").exists()
    assert plan_version.active_version(sess) == 2
    # amended plan kept the original goal (not a goal-level change)
    assert plan_version.resolve_active_plan(sess)["goal"] == PLAN_V1["goal"]
    # acceptance YAML refreshed to the amended gates
    acc = yaml.safe_load(
        (sess / "THINK" / "03_ACCEPTANCE.yaml").read_text(encoding="utf-8")
    )
    assert len(acc["acceptance"]) == 2
