"""Tests for the in-house `executor_helper` agent."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from cli.agents.executor_helper.core import (
    ExecutionProposal,
    StepNotFoundError,
    ValidationError,
    _find_step,
    _parse_llm_json,
    _read_session_inputs,
    _session_slug_from_path,
    _summarize_other_steps,
    _validate_proposal,
    draft_step_implementation,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import MockBackend


# ───────────────────────── helpers ─────────────────────────


def _seed_session(
    tmp_path: Path,
    slug: str = "feat-x",
    context: str = "# Context\n\nbody",
    envelope: Dict[str, Any] = None,
) -> Path:
    if envelope is None:
        envelope = {
            "goal": "build something",
            "tier": "WARM",
            "steps": [
                {"id": "S1", "action": "create skeleton", "owner_role": "EXECUTOR", "expected_artifact": "files", "risk": "LOW"},
                {"id": "S2", "action": "write tests", "owner_role": "VERIFIER", "expected_artifact": "test file", "risk": "LOW"},
            ],
        }
    session_dir = tmp_path / f"0001_2026-05-13_10_56_am_{slug}"
    (session_dir / "THINK").mkdir(parents=True)
    (session_dir / ".state").mkdir(parents=True)
    (session_dir / "THINK" / "00_CONTEXT.md").write_text(context, encoding="utf-8")
    (session_dir / ".state" / "plan.json").write_text(
        json.dumps(envelope), encoding="utf-8"
    )
    return session_dir


def _good_proposal(step_id: str = "S1") -> Dict[str, Any]:
    return {
        "step_id": step_id,
        "files_to_create": [
            {"path": "foo.py", "content": "print('hi')\n"}
        ],
        "files_to_edit": [
            {"path": "bar.py", "old": "x = 1", "new": "x = 2"}
        ],
        "commands_to_run": [
            {"cmd": "echo hi", "cwd": ".", "expect_exit": 0}
        ],
        "notes": "Implements step",
    }


# ───────────────────────── imports ─────────────────────────


def test_imports():
    assert callable(draft_step_implementation)


# ───────────────────────── _read_session_inputs ─────────────────────────


def test_read_session_inputs_happy(tmp_path: Path):
    session = _seed_session(tmp_path)
    out = _read_session_inputs(session)
    assert "body" in out["context_md"]
    assert out["plan_envelope"]["tier"] == "WARM"


def test_read_session_inputs_missing_plan_error_mentions_path_and_ai_nnn(tmp_path: Path):
    """A3 regression: when .state/plan.json is missing, the raised error must
    name both the canonical path `.state/plan.json` AND recommend `ai nnn` so
    operators know exactly which kernel ritual to run."""
    session_dir = tmp_path / "session-no-plan"
    (session_dir / "THINK").mkdir(parents=True)
    (session_dir / "THINK" / "00_CONTEXT.md").write_text("ctx")
    with pytest.raises(FileNotFoundError) as exc_info:
        _read_session_inputs(session_dir)
    msg = str(exc_info.value)
    assert ".state/plan.json" in msg, f"error must name `.state/plan.json`; got: {msg!r}"
    assert "ai nnn" in msg, f"error must recommend `ai nnn`; got: {msg!r}"


def test_read_session_inputs_accepts_kernel_meta_fields(tmp_path: Path):
    """S4 regression: kernel `ai nnn` writes plan with extra meta fields
    (`approved_by`, `approved_at`, `budget_status`). The consumer must accept
    these duck-typed extras without rejection — they pass straight through
    into the returned `plan_envelope` dict for downstream use."""
    envelope_with_meta = {
        "goal": "build something",
        "tier": "WARM",
        "steps": [
            {"id": "S1", "action": "x", "owner_role": "EXECUTOR", "expected_artifact": "y", "risk": "LOW"},
        ],
        "approved_by": "kernel",
        "approved_at": "2026-05-14T12:00:00+00:00",
        "budget_status": "within_default",
    }
    session = _seed_session(tmp_path, envelope=envelope_with_meta)
    out = _read_session_inputs(session)
    env = out["plan_envelope"]
    assert env["approved_by"] == "kernel"
    assert env["approved_at"] == "2026-05-14T12:00:00+00:00"
    assert env["budget_status"] == "within_default"
    assert env["steps"][0]["id"] == "S1"


# ───────────────────────── _find_step ─────────────────────────


def test_find_step_happy():
    envelope = {"steps": [{"id": "S1", "action": "a"}, {"id": "S2", "action": "b"}]}
    step = _find_step(envelope, "S2")
    assert step["action"] == "b"


def test_find_step_missing_raises():
    envelope = {"steps": [{"id": "S1", "action": "a"}]}
    with pytest.raises(StepNotFoundError, match="not found"):
        _find_step(envelope, "S99")


# ───────────────────────── _summarize_other_steps ─────────────────────────


def test_summarize_other_steps_excludes_target():
    envelope = {
        "steps": [
            {"id": "S1", "action": "alpha"},
            {"id": "S2", "action": "beta"},
            {"id": "S3", "action": "gamma"},
        ]
    }
    out = _summarize_other_steps(envelope, "S2")
    assert "S1" in out
    assert "S3" in out
    assert "S2" not in out


def test_summarize_other_steps_truncates_long_plans():
    envelope = {"steps": [{"id": f"S{i}", "action": "x" * 250} for i in range(50)]}
    out = _summarize_other_steps(envelope, "S0", max_chars=500)
    assert "truncated" in out
    assert len(out) < 1000  # not fully expanded


# ───────────────────────── _validate_proposal ─────────────────────────


def test_validate_proposal_well_formed():
    _validate_proposal(_good_proposal())


def test_validate_proposal_missing_top_key():
    p = _good_proposal()
    del p["notes"]
    with pytest.raises(ValidationError, match="missing top-level"):
        _validate_proposal(p)


def test_validate_proposal_rejects_plain_string_command():
    """commands_to_run items MUST be structured dicts, not plain strings."""
    p = _good_proposal()
    p["commands_to_run"] = ["echo hi"]
    with pytest.raises(ValidationError, match="must be a dict"):
        _validate_proposal(p)


def test_validate_proposal_rejects_files_to_create_missing_path():
    p = _good_proposal()
    p["files_to_create"][0] = {"content": "x"}  # missing 'path'
    with pytest.raises(ValidationError, match="missing keys"):
        _validate_proposal(p)


def test_validate_proposal_rejects_files_to_edit_missing_old():
    p = _good_proposal()
    p["files_to_edit"][0] = {"path": "x.py", "new": "y"}
    with pytest.raises(ValidationError, match="missing keys"):
        _validate_proposal(p)


def test_validate_proposal_rejects_empty_old():
    p = _good_proposal()
    p["files_to_edit"][0]["old"] = ""
    with pytest.raises(ValidationError, match="non-empty"):
        _validate_proposal(p)


def test_validate_proposal_rejects_commands_missing_expect_exit():
    p = _good_proposal()
    del p["commands_to_run"][0]["expect_exit"]
    with pytest.raises(ValidationError, match="missing keys"):
        _validate_proposal(p)


def test_validate_proposal_rejects_non_int_expect_exit():
    p = _good_proposal()
    p["commands_to_run"][0]["expect_exit"] = "0"
    with pytest.raises(ValidationError, match="integer"):
        _validate_proposal(p)


def test_validate_proposal_rejects_empty_notes():
    p = _good_proposal()
    p["notes"] = "   "
    with pytest.raises(ValidationError, match="non-empty"):
        _validate_proposal(p)


def test_validate_proposal_accepts_pure_verify_with_notes():
    """Pure-verification step: all arrays empty, but notes non-empty → valid."""
    p = _good_proposal()
    p["files_to_create"] = []
    p["files_to_edit"] = []
    p["commands_to_run"] = []
    p["notes"] = "This is a verification-only step; operator runs the check manually."
    _validate_proposal(p)


# ───────────────────────── _parse_llm_json ─────────────────────────


def test_parse_llm_json_fence():
    assert _parse_llm_json('```json\n{"a":1}\n```') == {"a": 1}


def test_parse_llm_json_bare():
    assert _parse_llm_json('{"a":1}') == {"a": 1}


def test_parse_llm_json_garbage_raises():
    with pytest.raises(ValidationError):
        _parse_llm_json("not JSON")


# ───────────────────────── full pipeline ─────────────────────────


def test_draft_via_mock_backend(tmp_path: Path):
    session = _seed_session(tmp_path)
    backend = MockBackend(canned=json.dumps(_good_proposal("S1")))
    proposal = draft_step_implementation(
        session_path=session, step_id="S1", backend=backend
    )
    assert isinstance(proposal, ExecutionProposal)
    assert proposal.proposal["step_id"] == "S1"
    assert proposal.proposal["files_to_create"][0]["path"] == "foo.py"


def test_draft_step_not_found_raises(tmp_path: Path):
    session = _seed_session(tmp_path)
    with pytest.raises(StepNotFoundError):
        draft_step_implementation(
            session_path=session, step_id="S99", backend=MockBackend(canned="{}")
        )


def test_draft_rejects_wrong_step_id_in_proposal(tmp_path: Path):
    """LLM returns proposal but with wrong step_id (drift guard)."""
    session = _seed_session(tmp_path)
    bad = _good_proposal("S2")  # but caller asked for S1
    backend = MockBackend(canned=json.dumps(bad))
    with pytest.raises(ValidationError, match="does not match"):
        draft_step_implementation(
            session_path=session, step_id="S1", backend=backend
        )


def test_draft_malformed_json_raises(tmp_path: Path):
    session = _seed_session(tmp_path)
    backend = MockBackend(canned="not JSON")
    with pytest.raises(ValidationError):
        draft_step_implementation(
            session_path=session, step_id="S1", backend=backend
        )


# ───────────────────────── audit emission ─────────────────────────


def test_audit_emission_success(tmp_path: Path):
    session = _seed_session(tmp_path)
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned=json.dumps(_good_proposal("S1")))
    draft_step_implementation(
        session_path=session, step_id="S1", backend=backend, audit_chain=chain
    )
    types = [e["type"] for e in chain.iter_events()]
    assert types == [
        "executor_helper.invoked",
        "llm.call_started",
        "llm.call_completed",
        "executor_helper.proposed",
    ]


def test_audit_emission_failure(tmp_path: Path):
    session = _seed_session(tmp_path)
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned="bad")
    with pytest.raises(ValidationError):
        draft_step_implementation(
            session_path=session, step_id="S1", backend=backend, audit_chain=chain
        )
    types = [e["type"] for e in chain.iter_events()]
    assert "executor_helper.invoked" in types
    assert "executor_helper.failed" in types


# ───────────────────────── CLI entry ─────────────────────────


def test_cli_happy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.executor_helper import cli as eh_cli

    def _fake(session_path, step_id, backend=None, audit_chain=None):
        return ExecutionProposal(proposal=_good_proposal(step_id))

    monkeypatch.setattr(eh_cli, "draft_step_implementation", _fake)
    session = _seed_session(tmp_path)
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = eh_cli.main([
        "draft",
        "--session-path", str(session),
        "--step-id", "S1",
        "--no-audit",
    ])
    assert rc == 0
    parsed = json.loads(captured.getvalue())
    assert parsed["step_id"] == "S1"


def test_cli_step_not_found_exit_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.executor_helper import cli as eh_cli

    def _raises(session_path, step_id, backend=None, audit_chain=None):
        raise StepNotFoundError("nope")

    monkeypatch.setattr(eh_cli, "draft_step_implementation", _raises)
    session = _seed_session(tmp_path)
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = eh_cli.main([
        "draft", "--session-path", str(session), "--step-id", "S99", "--no-audit",
    ])
    assert rc == 2


def test_cli_validation_error_exit_3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.executor_helper import cli as eh_cli

    def _raises(session_path, step_id, backend=None, audit_chain=None):
        raise ValidationError("forced")

    monkeypatch.setattr(eh_cli, "draft_step_implementation", _raises)
    session = _seed_session(tmp_path)
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = eh_cli.main([
        "draft", "--session-path", str(session), "--step-id", "S1", "--no-audit",
    ])
    assert rc == 3
