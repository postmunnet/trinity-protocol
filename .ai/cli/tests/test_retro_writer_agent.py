"""Tests for the in-house `retro_writer` agent."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from cli.agents.retro_writer.core import (
    REQUIRED_HEADINGS_ORDER,
    RetroLessons,
    ValidationError,
    _read_session_inputs,
    _session_slug_from_path,
    _summarize_session_audit,
    _validate_lessons,
    compose_retro_lessons,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import MockBackend


def _seed_session(
    tmp_path: Path,
    slug: str = "feat-x",
    retro: str = "# Retro\n\nVerdict: PASS\nMetrics: ok\n",
    envelope: Dict[str, Any] = None,
) -> Path:
    if envelope is None:
        envelope = {"goal": "build", "tier": "WARM", "steps": []}
    session_dir = tmp_path / f"0001_2026-05-13_11_23_am_{slug}"
    (session_dir / "THINK").mkdir(parents=True)
    (session_dir / "THINK" / "RETRO.md").write_text(retro)
    (session_dir / "THINK" / "plan_envelope.json").write_text(json.dumps(envelope))
    return session_dir


def _good_lessons() -> str:
    """A valid lessons body with all 4 headings and ≥200 words."""
    # 8 words × 16 repeats = 128 words per section, × 2 sections = 256 words.
    pad = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 16
    return (
        "## Lessons Learned\n\n"
        f"{pad}\n\n"
        "## Patterns Observed\n\n"
        f"{pad}\n\n"
        "## Doctrine Claims\n\n"
        "(none)\n\n"
        "## Anti-Patterns\n\n"
        "(none)\n"
    )


def test_imports():
    assert callable(compose_retro_lessons)


def test_read_session_inputs_happy(tmp_path: Path):
    s = _seed_session(tmp_path)
    out = _read_session_inputs(s)
    assert "Verdict" in out["retro_md"]
    assert out["plan_envelope"]["tier"] == "WARM"


def test_read_session_inputs_missing_retro(tmp_path: Path):
    d = tmp_path / "session-no-retro"
    (d / "THINK").mkdir(parents=True)
    (d / "THINK" / "plan_envelope.json").write_text("{}")
    with pytest.raises(FileNotFoundError, match="RETRO.md"):
        _read_session_inputs(d)


def test_read_session_inputs_empty_retro(tmp_path: Path):
    s = _seed_session(tmp_path, retro="   \n")
    with pytest.raises(FileNotFoundError, match="empty"):
        _read_session_inputs(s)


def test_session_slug_extract():
    p = Path("/x/0001_2026-05-13_11_23_am_feat-foo")
    assert _session_slug_from_path(p) == "feat-foo"


def test_summarize_audit_no_events(tmp_path: Path):
    out = _summarize_session_audit(tmp_path, "no-match")
    assert out["event_count"] == 0


def test_validate_lessons_well_formed():
    _validate_lessons(_good_lessons())


def test_validate_lessons_missing_heading():
    body = _good_lessons().replace("## Anti-Patterns", "## Some Other Heading")
    with pytest.raises(ValidationError, match="missing required heading.*Anti-Patterns"):
        _validate_lessons(body)


def test_validate_lessons_wrong_order():
    """Swap two required headings."""
    body = (
        "## Lessons Learned\n\n" + ("body " * 50) +
        "\n\n## Doctrine Claims\n\n(none)\n\n"
        "## Patterns Observed\n\n" + ("body " * 50) +
        "\n\n## Anti-Patterns\n\n(none)\n"
    )
    with pytest.raises(ValidationError, match="must be in declared order"):
        _validate_lessons(body)


def test_validate_lessons_rejects_h1_at_top():
    body = "# Retro\n\n" + _good_lessons()
    with pytest.raises(ValidationError, match="NOT start with"):
        _validate_lessons(body)


def test_validate_lessons_rejects_prose_before_first_heading():
    body = "Some preamble.\n\n" + _good_lessons()
    with pytest.raises(ValidationError, match="must start with"):
        _validate_lessons(body)


def test_validate_lessons_rejects_too_short():
    body = (
        "## Lessons Learned\n\nshort\n\n"
        "## Patterns Observed\n\nshort\n\n"
        "## Doctrine Claims\n\n(none)\n\n"
        "## Anti-Patterns\n\n(none)\n"
    )
    with pytest.raises(ValidationError, match="too short"):
        _validate_lessons(body)


def test_validate_lessons_rejects_empty_string():
    with pytest.raises(ValidationError, match="non-empty"):
        _validate_lessons("")


def test_validate_lessons_case_sensitive():
    """Heading text must match exactly — lowercase variant rejected."""
    body = _good_lessons().replace("## Lessons Learned", "## lessons learned")
    with pytest.raises(ValidationError, match="must start with"):
        _validate_lessons(body)


def test_compose_via_mock_backend(tmp_path: Path):
    session = _seed_session(tmp_path)
    backend = MockBackend(canned=_good_lessons())
    lessons = compose_retro_lessons(
        session_path=session, repo_root=tmp_path, backend=backend
    )
    assert isinstance(lessons, RetroLessons)
    assert "## Lessons Learned" in lessons.body
    assert "## Anti-Patterns" in lessons.body


def test_compose_invalid_body_raises(tmp_path: Path):
    session = _seed_session(tmp_path)
    backend = MockBackend(canned="not a valid lessons body")
    with pytest.raises(ValidationError):
        compose_retro_lessons(
            session_path=session, repo_root=tmp_path, backend=backend
        )


def test_compose_audit_emission_success(tmp_path: Path):
    session = _seed_session(tmp_path)
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned=_good_lessons())
    compose_retro_lessons(
        session_path=session, repo_root=tmp_path, backend=backend, audit_chain=chain,
    )
    types = [e["type"] for e in chain.iter_events()]
    assert types == [
        "retro_writer.invoked",
        "llm.call_started",
        "llm.call_completed",
        "retro_writer.proposed",
    ]


def test_compose_audit_emission_failure(tmp_path: Path):
    session = _seed_session(tmp_path)
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned="bad")
    with pytest.raises(ValidationError):
        compose_retro_lessons(
            session_path=session, repo_root=tmp_path, backend=backend, audit_chain=chain,
        )
    types = [e["type"] for e in chain.iter_events()]
    assert "retro_writer.invoked" in types
    assert "retro_writer.failed" in types


def test_cli_happy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.retro_writer import cli as rw_cli

    def _fake(session_path, repo_root, backend=None, audit_chain=None):
        return RetroLessons(body=_good_lessons())

    monkeypatch.setattr(rw_cli, "compose_retro_lessons", _fake)
    session = _seed_session(tmp_path)
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = rw_cli.main(["draft", "--session-path", str(session), "--no-audit"])
    assert rc == 0
    assert "## Lessons Learned" in captured.getvalue()


def test_cli_missing_session_exit_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.retro_writer import cli as rw_cli
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = rw_cli.main([
        "draft", "--session-path", str(tmp_path / "noexist"), "--no-audit",
    ])
    assert rc == 2


def test_required_headings_constant_locked():
    """The 4 required headings are part of the contract — guard against rename."""
    assert REQUIRED_HEADINGS_ORDER == (
        "## Lessons Learned",
        "## Patterns Observed",
        "## Doctrine Claims",
        "## Anti-Patterns",
    )
