"""Tests for the in-house `plan_helper` agent (shape-only, v0.1)."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

from cli.agents.plan_helper.core import (
    PlanDraft,
    ValidationError,
    _parse_llm_json,
    _read_session_inputs,
    _session_slug_from_path,
    _validate_envelope,
    draft_plan_envelope,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import MockBackend


# ───────────────────────── helpers ─────────────────────────


def _seed_session(
    tmp_path: Path,
    slug: str,
    context: str = "# Context\n\nbody",
    prompt: str = "# vvv prompt\n\n5 answers",
) -> Path:
    session_dir = tmp_path / f"0001_2026-05-13_10_42_am_{slug}"
    (session_dir / "THINK").mkdir(parents=True)
    (session_dir / "THINK" / "00_CONTEXT.md").write_text(context, encoding="utf-8")
    (session_dir / "THINK" / "01_PROMPT.md").write_text(prompt, encoding="utf-8")
    return session_dir


def _good_envelope() -> Dict[str, Any]:
    return {
        "goal": "Build foo at .ai/cli/agents/foo/. Mirror sibling layout.",
        "tier": "WARM",
        "allowed_paths": [".ai/cli/agents/foo/**"],
        "forbidden_paths": [".ai/policies/**", ".ai/audit/**"],
        "constitutional_notes": ["Article III — proposal only"],
        "steps": [
            {
                "id": "S1",
                "action": "Create skeleton",
                "owner_role": "EXECUTOR",
                "expected_artifact": "package files",
                "risk": "LOW",
            }
        ],
        "acceptance": [
            {
                "id": "A1",
                "description": "imports clean",
                "command": "python3 -c 'import x'",
                "expect_exit": 0,
                "required": True,
            }
        ],
        "rollback": ["restore S1", "rerun tests", "git restore changes"],
        "decided_by": "human",
    }


# ───────────────────────── imports ─────────────────────────


def test_imports_module_surface():
    assert callable(draft_plan_envelope)
    assert callable(_validate_envelope)


# ───────────────────────── _read_session_inputs ─────────────────────────


def test_read_session_inputs_happy(tmp_path: Path):
    session = _seed_session(tmp_path, "feat-x")
    out = _read_session_inputs(session)
    assert "body" in out["context_md"]
    assert "5 answers" in out["vvv_prompt_md"]


def test_read_session_inputs_missing_session_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="session path"):
        _read_session_inputs(tmp_path / "no_exist")


def test_read_session_inputs_missing_prompt_raises(tmp_path: Path):
    """Missing 01_PROMPT.md is hard error — operator must run ai vvv first."""
    session_dir = tmp_path / "session-no-vvv"
    (session_dir / "THINK").mkdir(parents=True)
    (session_dir / "THINK" / "00_CONTEXT.md").write_text("ctx")
    # 01_PROMPT.md intentionally NOT written.
    with pytest.raises(FileNotFoundError, match="vvv prompt not found"):
        _read_session_inputs(session_dir)


def test_read_session_inputs_empty_context_raises(tmp_path: Path):
    session = _seed_session(tmp_path, "feat-e", context="   \n")
    with pytest.raises(FileNotFoundError, match="empty"):
        _read_session_inputs(session)


def test_read_session_inputs_empty_prompt_raises(tmp_path: Path):
    session = _seed_session(tmp_path, "feat-ep", prompt="\n\n  ")
    with pytest.raises(FileNotFoundError, match="empty"):
        _read_session_inputs(session)


# ───────────────────────── _session_slug_from_path ─────────────────────────


def test_session_slug_extract():
    p = Path("/x/0001_2026-05-13_10_42_am_feat-plan-helper")
    assert _session_slug_from_path(p) == "feat-plan-helper"


# ───────────────────────── _validate_envelope ─────────────────────────


def test_validate_envelope_accepts_well_formed():
    _validate_envelope(_good_envelope())


def test_validate_envelope_rejects_missing_top_key():
    d = _good_envelope()
    del d["tier"]
    with pytest.raises(ValidationError, match="missing top-level"):
        _validate_envelope(d)


def test_validate_envelope_rejects_bad_tier():
    d = _good_envelope()
    d["tier"] = "WARMISH"
    with pytest.raises(ValidationError, match="tier must be"):
        _validate_envelope(d)


def test_validate_envelope_rejects_empty_allowed_paths():
    d = _good_envelope()
    d["allowed_paths"] = []
    with pytest.raises(ValidationError, match="non-empty"):
        _validate_envelope(d)


def test_validate_envelope_rejects_empty_steps():
    d = _good_envelope()
    d["steps"] = []
    with pytest.raises(ValidationError, match="non-empty"):
        _validate_envelope(d)


def test_validate_envelope_rejects_bad_step_owner_role():
    d = _good_envelope()
    d["steps"][0]["owner_role"] = "BOSS"
    with pytest.raises(ValidationError, match="owner_role"):
        _validate_envelope(d)


def test_validate_envelope_rejects_bad_step_risk():
    d = _good_envelope()
    d["steps"][0]["risk"] = "EXTREME"
    with pytest.raises(ValidationError, match="risk must be"):
        _validate_envelope(d)


# ───────────────────────── acceptance schema (the foot-gun) ─────────────────────────


def test_validate_envelope_rejects_acceptance_with_criterion_key():
    """T-FOOTGUN — the documented foot-gun must be rejected with a clear message."""
    d = _good_envelope()
    d["acceptance"] = [{
        "id": "A1",
        "criterion": "imports clean",
        "check": "python -c 'import x'",
    }]
    with pytest.raises(ValidationError) as exc:
        _validate_envelope(d)
    msg = str(exc.value)
    assert "criterion" in msg or "forbidden keys" in msg


def test_validate_envelope_rejects_acceptance_with_check_key():
    """T-FOOTGUN-B — `check` key is rejected even when all 5 canonical keys are also present."""
    d = _good_envelope()
    d["acceptance"] = [{
        "id": "A1",
        "description": "imports clean",
        "command": "python -c 'import x'",
        "expect_exit": 0,
        "required": True,
        "check": "python -c 'import x'",  # forbidden duplicate
    }]
    with pytest.raises(ValidationError, match="forbidden keys"):
        _validate_envelope(d)


def test_validate_envelope_rejects_acceptance_missing_command():
    """Wrong_acceptance — missing the required 'command' key."""
    d = _good_envelope()
    d["acceptance"] = [{
        "id": "A1",
        "description": "imports clean",
        "expect_exit": 0,
        "required": True,
    }]
    with pytest.raises(ValidationError, match="missing required keys"):
        _validate_envelope(d)


def test_validate_envelope_rejects_acceptance_non_bool_required():
    d = _good_envelope()
    d["acceptance"][0]["required"] = "yes"
    with pytest.raises(ValidationError, match="must be a boolean"):
        _validate_envelope(d)


def test_validate_envelope_rejects_acceptance_non_int_expect_exit():
    d = _good_envelope()
    d["acceptance"][0]["expect_exit"] = "0"
    with pytest.raises(ValidationError, match="integer"):
        _validate_envelope(d)


def test_validate_envelope_rejects_too_short_rollback():
    d = _good_envelope()
    d["rollback"] = ["only one entry"]
    with pytest.raises(ValidationError, match="at least 3"):
        _validate_envelope(d)


def test_validate_envelope_rejects_non_human_decided_by():
    d = _good_envelope()
    d["decided_by"] = "kernel"
    with pytest.raises(ValidationError, match="Article XIII"):
        _validate_envelope(d)


def test_validate_envelope_rejects_non_dict():
    with pytest.raises(ValidationError, match="must be a dict"):
        _validate_envelope("not a dict")


# ───────────────────────── drift-pattern rejection (3 patterns) ─────────────────────────


def test_validate_envelope_rejects_drift_wrong_test_path():
    """Drift A — acceptance.command uses cli/agents/<name>/tests (wrong)."""
    d = _good_envelope()
    d["acceptance"][0]["command"] = "cd .ai && python3 -m pytest cli/agents/foo/tests -q"
    with pytest.raises(ValidationError, match="drift pattern \\(test path\\)"):
        _validate_envelope(d)


def test_validate_envelope_rejects_drift_audit_in_git_diff():
    """Drift B — acceptance.command runs git diff against .ai/audit/."""
    d = _good_envelope()
    d["acceptance"][0]["command"] = "git diff --name-only main -- .ai/audit .ai/policies"
    with pytest.raises(ValidationError, match="drift pattern \\(audit-events not exempt\\)"):
        _validate_envelope(d)


def test_validate_envelope_rejects_drift_backend_flag():
    """Drift C — acceptance.command passes --backend flag (no agent has it)."""
    d = _good_envelope()
    d["acceptance"][0]["command"] = "python -m cli.agents.X draft --backend mock"
    with pytest.raises(ValidationError, match="drift pattern \\(fake --backend flag\\)"):
        _validate_envelope(d)


def test_validate_envelope_drift_audit_only_rejects_with_git_diff():
    """Positive test — .ai/audit/ in a NON-git-diff context is NOT rejected.

    The canonical genesis-hash check reads from .ai/audit/events.ndjson but
    doesn't run git diff against the dir. That must pass.
    """
    d = _good_envelope()
    d["acceptance"][0]["command"] = (
        "python3 -c 'import json,hashlib;e=json.loads(open(\".ai/audit/events.ndjson\").readline())'"
    )
    _validate_envelope(d)  # Should NOT raise


def test_validate_envelope_drift_backend_only_rejects_flag_form():
    """Positive test — the word `backend` alone (not as a CLI flag) is OK."""
    d = _good_envelope()
    d["acceptance"][0]["command"] = (
        "echo 'test the backend integration' && exit 0"
    )
    _validate_envelope(d)  # Should NOT raise


def test_validate_envelope_drift_test_path_only_rejects_agent_pattern():
    """Positive test — generic mention of `tests/` directory is OK; only
    `cli/agents/<name>/tests` is rejected."""
    d = _good_envelope()
    d["acceptance"][0]["command"] = "ls tests/ && pytest cli/tests/test_foo.py -q"
    _validate_envelope(d)  # Should NOT raise


# ───────────────────────── _parse_llm_json ─────────────────────────


def test_parse_llm_json_strips_fence():
    assert _parse_llm_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_llm_json_bare():
    assert _parse_llm_json('{"a": 1}') == {"a": 1}


def test_parse_llm_json_rejects_garbage():
    with pytest.raises(ValidationError):
        _parse_llm_json("not JSON")


# ───────────────────────── full pipeline ─────────────────────────


def _mock_envelope_response() -> str:
    return json.dumps(_good_envelope())


def test_draft_plan_envelope_via_mock_backend(tmp_path: Path):
    session = _seed_session(tmp_path, "feat-mock")
    backend = MockBackend(canned=_mock_envelope_response())
    draft = draft_plan_envelope(session_path=session, backend=backend)
    assert isinstance(draft, PlanDraft)
    assert draft.envelope["tier"] == "WARM"
    assert draft.envelope["acceptance"][0]["command"].startswith("python3")


def test_draft_plan_envelope_malformed_json_raises(tmp_path: Path):
    session = _seed_session(tmp_path, "feat-bad")
    backend = MockBackend(canned="not JSON")
    with pytest.raises(ValidationError):
        draft_plan_envelope(session_path=session, backend=backend)


def test_draft_plan_envelope_validation_propagates(tmp_path: Path):
    """LLM produces JSON dict but with the foot-gun shape → ValidationError."""
    session = _seed_session(tmp_path, "feat-foot")
    bad = _good_envelope()
    bad["acceptance"] = [{"id": "A1", "criterion": "x", "check": "y"}]
    backend = MockBackend(canned=json.dumps(bad))
    with pytest.raises(ValidationError) as exc:
        draft_plan_envelope(session_path=session, backend=backend)
    assert "criterion" in str(exc.value) or "forbidden" in str(exc.value)


# ───────────────────────── audit emission ─────────────────────────


def test_audit_emission_on_success(tmp_path: Path):
    session = _seed_session(tmp_path, "feat-a")
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned=_mock_envelope_response())
    draft_plan_envelope(session_path=session, backend=backend, audit_chain=chain)
    types = [e["type"] for e in chain.iter_events()]
    assert types == [
        "plan_helper.invoked",
        "llm.call_started",
        "llm.call_completed",
        "plan_helper.proposed",
    ]


def test_audit_emission_on_failure(tmp_path: Path):
    session = _seed_session(tmp_path, "feat-af")
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned="garbage")
    with pytest.raises(ValidationError):
        draft_plan_envelope(session_path=session, backend=backend, audit_chain=chain)
    types = [e["type"] for e in chain.iter_events()]
    assert "plan_helper.invoked" in types
    assert "plan_helper.failed" in types


# ───────────────────────── CLI entry ─────────────────────────


def test_cli_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.plan_helper import cli as ph_cli

    def _fake_draft(session_path, backend=None, audit_chain=None):
        return PlanDraft(envelope=_good_envelope())

    monkeypatch.setattr(ph_cli, "draft_plan_envelope", _fake_draft)
    session = _seed_session(tmp_path, "feat-cli")
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = ph_cli.main(["draft", "--session-path", str(session), "--no-audit"])
    assert rc == 0
    parsed = json.loads(captured.getvalue())
    assert parsed["tier"] == "WARM"


def test_cli_missing_session_exit_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.plan_helper import cli as ph_cli
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = ph_cli.main([
        "draft", "--session-path", str(tmp_path / "noexist"), "--no-audit",
    ])
    assert rc == 2


def test_cli_validation_error_exit_3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.plan_helper import cli as ph_cli

    def _raises(session_path, backend=None, audit_chain=None):
        raise ValidationError("forced")

    monkeypatch.setattr(ph_cli, "draft_plan_envelope", _raises)
    session = _seed_session(tmp_path, "feat-v")
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = ph_cli.main(["draft", "--session-path", str(session), "--no-audit"])
    assert rc == 3
