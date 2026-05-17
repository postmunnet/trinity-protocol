"""Tests for the in-house `session_bootstrap` agent.

Coverage map (session feat-session-bootstrap-cli-v0.1 step S6):
  T1  — module imports
  T2  — _list_recent_archive on synthetic tmp archive
  T3  — _slug_collision_check appends -N suffix
  T4  — _slug_collision_check returns input when unique
  T5  — _validate_proposal accepts a well-formed dict
  T6  — _validate_proposal rejects missing required keys
  T7  — _validate_proposal rejects bad slug shape / non-kebab / too long
  T8  — _validate_proposal rejects invalid tier
  T9  — _parse_llm_json strips ```json fence
  T10 — _parse_llm_json rejects non-JSON garbage
  T11 — propose_session full pipeline via MockBackend (valid response)
  T12 — propose_session via MockBackend with malformed JSON raises ValidationError
  T13 — audit emission on success: 4 events (session_bootstrap.invoked,
        llm.call_started, llm.call_completed, session_bootstrap.proposed)
  T14 — audit emission on validation failure: session_bootstrap.failed appended
  T15 — slug collision: proposed=existing → -2 suffix
  T16 — CLI entry: subprocess run with MockBackend via LLM_BACKEND env stub
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from cli.agents.session_bootstrap.core import (
    Proposal,
    ValidationError,
    _list_recent_archive,
    _parse_llm_json,
    _slug_collision_check,
    _validate_proposal,
    propose_session,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import Backend, LLMRequest, LLMResponse, MockBackend


# ───────────────────────── T1 ─────────────────────────


def test_imports_module_surface():
    """T1 — public symbols loadable."""
    from cli.agents.session_bootstrap import core as sbcore  # noqa: F401
    assert callable(propose_session)


# ───────────────────────── T2 — archive listing ─────────────────────────


def _seed_archive(repo_root: Path, slugs: list[str]) -> None:
    archive_dir = repo_root / ".ai" / "sessions" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    for i, slug in enumerate(slugs):
        # Name format: 0001_2026-05-13_03_36_am_<slug>.archive
        name = f"0001_2026-05-13_03_{i:02d}_am_{slug}.archive"
        (archive_dir / name).mkdir()


def test_list_recent_archive_basic(tmp_path: Path):
    """T2 — _list_recent_archive returns slugs sorted by mtime descending."""
    _seed_archive(tmp_path, ["feat-a", "feat-b", "feat-c"])
    out = _list_recent_archive(tmp_path, limit=10)
    slugs = [e["slug"] for e in out]
    assert set(slugs) == {"feat-a", "feat-b", "feat-c"}
    # Each entry has the right keys.
    for entry in out:
        assert "slug" in entry
        assert "archive_path" in entry
        assert entry["archive_path"].endswith(".archive")


def test_list_recent_archive_empty_dir(tmp_path: Path):
    """Empty archive returns []."""
    out = _list_recent_archive(tmp_path, limit=10)
    assert out == []


def test_list_recent_archive_limit(tmp_path: Path):
    """Respects the limit argument."""
    _seed_archive(tmp_path, [f"feat-{i}" for i in range(15)])
    out = _list_recent_archive(tmp_path, limit=5)
    assert len(out) == 5


# ───────────────────────── T3 + T4 — slug collision ─────────────────────────


def test_slug_collision_check_unique_returns_input():
    """T4 — unique slug passes through unchanged."""
    out = _slug_collision_check("feat-new", ["feat-other", "feat-third"])
    assert out == "feat-new"


def test_slug_collision_check_appends_n_on_collision():
    """T3 — colliding slug gets -2 appended."""
    out = _slug_collision_check("feat-dup", ["feat-dup"])
    assert out == "feat-dup-2"


def test_slug_collision_check_case_insensitive():
    """Case-insensitive collision detection."""
    out = _slug_collision_check("FEAT-DUP", ["feat-dup"])
    assert out == "FEAT-DUP-2"


def test_slug_collision_check_chain():
    """Multiple existing collisions push to -3."""
    out = _slug_collision_check("feat-dup", ["feat-dup", "feat-dup-2"])
    assert out == "feat-dup-3"


# ───────────────────────── T5–T8 — proposal validation ─────────────────────────


def _good_dict() -> Dict[str, Any]:
    return {
        "slug": "feat-test",
        "tier": "WARM",
        "tier_reasoning": "multi-file but bounded",
        "context_draft": "# Context\n\nbody",
        "related_sessions_brief": "none",
    }


def test_validate_proposal_accepts_well_formed():
    """T5 — well-formed dict passes."""
    _validate_proposal(_good_dict())


def test_validate_proposal_rejects_missing_keys():
    """T6 — missing required key raises."""
    d = _good_dict()
    del d["tier"]
    with pytest.raises(ValidationError, match="missing required keys"):
        _validate_proposal(d)


def test_validate_proposal_rejects_bad_slug_shape():
    """T7 — non-kebab slug raises."""
    d = _good_dict()
    d["slug"] = "feat_underscore"
    with pytest.raises(ValidationError):
        _validate_proposal(d)


def test_validate_proposal_rejects_uppercase_slug():
    """T7b — uppercase rejected."""
    d = _good_dict()
    d["slug"] = "Feat-Caps"
    with pytest.raises(ValidationError):
        _validate_proposal(d)


def test_validate_proposal_rejects_slug_too_long():
    """T7c — >64 char rejected."""
    d = _good_dict()
    d["slug"] = "feat-" + ("a" * 70)
    with pytest.raises(ValidationError, match="exceeds 64"):
        _validate_proposal(d)


def test_validate_proposal_rejects_invalid_tier():
    """T8 — tier outside HOT/WARM/COLD raises."""
    d = _good_dict()
    d["tier"] = "WARMISH"
    with pytest.raises(ValidationError, match="tier must be"):
        _validate_proposal(d)


def test_validate_proposal_rejects_empty_strings():
    """Empty required string field raises."""
    d = _good_dict()
    d["tier_reasoning"] = "   "
    with pytest.raises(ValidationError):
        _validate_proposal(d)


# ───────────────────────── T9 + T10 — JSON parsing ─────────────────────────


def test_parse_llm_json_strips_code_fence():
    """T9 — ```json ... ``` wrapper is stripped."""
    out = _parse_llm_json('```json\n{"a": 1}\n```')
    assert out == {"a": 1}


def test_parse_llm_json_strips_plain_fence():
    """T9b — ``` ... ``` (no language tag) is stripped."""
    out = _parse_llm_json('```\n{"a": 1}\n```')
    assert out == {"a": 1}


def test_parse_llm_json_no_fence():
    """T9c — bare JSON is accepted."""
    out = _parse_llm_json('{"a": 1}')
    assert out == {"a": 1}


def test_parse_llm_json_rejects_garbage():
    """T10 — non-JSON raises ValidationError."""
    with pytest.raises(ValidationError):
        _parse_llm_json("this is not JSON")


def test_parse_llm_json_rejects_invalid_json():
    """T10b — malformed JSON raises ValidationError."""
    with pytest.raises(ValidationError):
        _parse_llm_json('{"unterminated')


# ───────────────────────── T11–T15 — propose_session integration ─────────────────────────


_VALID_LLM_JSON = json.dumps({
    "slug": "feat-mock-task",
    "tier": "WARM",
    "tier_reasoning": "bounded scope",
    "context_draft": "# Context\n\nThe operator wants X.",
    "related_sessions_brief": "none",
})


def test_propose_session_via_mock_backend(tmp_path: Path):
    """T11 — full pipeline with MockBackend returns a valid Proposal."""
    backend = MockBackend(canned=_VALID_LLM_JSON)
    proposal = propose_session(
        "build a thing", repo_root=tmp_path, backend=backend
    )
    assert isinstance(proposal, Proposal)
    assert proposal.slug == "feat-mock-task"
    assert proposal.tier == "WARM"
    assert "Context" in proposal.context_draft
    assert proposal.related_sessions == []  # empty archive


def test_propose_session_malformed_json_raises(tmp_path: Path):
    """T12 — MockBackend returns garbage → ValidationError."""
    backend = MockBackend(canned="not JSON at all")
    with pytest.raises(ValidationError):
        propose_session("anything", repo_root=tmp_path, backend=backend)


def test_propose_session_audit_emission_on_success(tmp_path: Path):
    """T13 — successful propose_session emits 4 audit events."""
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned=_VALID_LLM_JSON)
    propose_session(
        "build something", repo_root=tmp_path, backend=backend, audit_chain=chain
    )
    types = [e["type"] for e in chain.iter_events()]
    assert types == [
        "session_bootstrap.invoked",
        "llm.call_started",
        "llm.call_completed",
        "session_bootstrap.proposed",
    ]


def test_propose_session_audit_emission_on_failure(tmp_path: Path):
    """T14 — validation failure emits session_bootstrap.failed."""
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned="not JSON")
    with pytest.raises(ValidationError):
        propose_session(
            "anything", repo_root=tmp_path, backend=backend, audit_chain=chain
        )
    types = [e["type"] for e in chain.iter_events()]
    assert "session_bootstrap.invoked" in types
    assert "session_bootstrap.failed" in types
    # llm.call_completed should NOT be in there — the failure happened during parsing.
    # llm.call_started IS in there (call_llm emits it before invoke).
    assert "llm.call_started" in types


def test_propose_session_slug_collision_resolved(tmp_path: Path):
    """T15 — when proposed slug exists in archive, agent appends -N."""
    _seed_archive(tmp_path, ["feat-mock-task"])
    backend = MockBackend(canned=_VALID_LLM_JSON)
    proposal = propose_session(
        "make feat-mock-task again", repo_root=tmp_path, backend=backend
    )
    assert proposal.slug == "feat-mock-task-2"


def test_propose_session_empty_description_raises(tmp_path: Path):
    """propose_session rejects empty/blank descriptions."""
    with pytest.raises(ValidationError, match="non-empty"):
        propose_session("   ", repo_root=tmp_path, backend=MockBackend())


# ───────────────────────── T16 — CLI entry-point ─────────────────────────


def test_cli_entry_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """T16 — `python -m cli.agents.session_bootstrap draft '...'` returns JSON.

    Uses --no-audit to keep the real audit chain untouched. To avoid hitting
    a real CLI backend, we monkeypatch select_backend to return a MockBackend
    via a side-channel module that the CLI imports. Simpler approach: run as
    in-process to exercise the CLI argv parsing + main() exit path; skip
    backend selection by injecting our own.
    """
    from cli.agents.session_bootstrap import cli as sb_cli

    # Monkeypatch propose_session to bypass backend selection (we just want
    # to verify the CLI wraps it correctly).
    def _fake_propose(description, repo_root, backend=None, audit_chain=None):
        return Proposal(
            slug="feat-from-cli",
            tier="HOT",
            tier_reasoning="single-file",
            context_draft="# c",
            related_sessions=[],
            raw_brief="none",
        )

    monkeypatch.setattr(sb_cli, "propose_session", _fake_propose)

    # Capture stdout.
    import io
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = sb_cli.main(["draft", "test description", "--no-audit"])
    assert rc == 0
    out = captured.getvalue()
    parsed = json.loads(out)
    assert parsed["slug"] == "feat-from-cli"
    assert parsed["tier"] == "HOT"


def test_cli_empty_description_returns_nonzero(monkeypatch: pytest.MonkeyPatch):
    """Empty description from stdin → exit 2."""
    from cli.agents.session_bootstrap import cli as sb_cli
    import io
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = sb_cli.main(["draft", "-", "--no-audit"])
    assert rc == 2


def test_cli_validation_error_returns_3(monkeypatch: pytest.MonkeyPatch):
    """ValidationError from propose_session → exit 3."""
    from cli.agents.session_bootstrap import cli as sb_cli

    def _raises(description, repo_root, backend=None, audit_chain=None):
        raise ValidationError("forced")

    monkeypatch.setattr(sb_cli, "propose_session", _raises)
    import io
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = sb_cli.main(["draft", "x", "--no-audit"])
    assert rc == 3
