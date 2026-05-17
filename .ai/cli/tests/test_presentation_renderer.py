"""Phase 13 — presentation_renderer tests."""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from cli.core.presentation_renderer import (
    CLOSE_PACK_FILENAME,
    DEFAULT_PROTOCOL_VERSION,
    make_presentation_synthesis,
    render_close_pack,
    write_close_pack,
)


def _seed_session(tmp_path: Path, with_scope: str = "", with_accept: str = "", with_retro: str = "") -> Path:
    sess = tmp_path / ".ai" / "sessions" / "0001_test_sess"
    (sess / "THINK").mkdir(parents=True)
    if with_scope:
        (sess / "THINK" / "02_SCOPE.md").write_text(with_scope, encoding="utf-8")
    if with_accept:
        (sess / "THINK" / "03_ACCEPTANCE.md").write_text(with_accept, encoding="utf-8")
    if with_retro:
        (sess / "THINK" / "RETRO.md").write_text(with_retro, encoding="utf-8")
    return sess


def _seed_audit(tmp_path: Path, events) -> Path:
    audit = tmp_path / ".ai" / "audit"
    audit.mkdir(parents=True)
    p = audit / "events.ndjson"
    p.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return p


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.presentation_renderer")
    assert hasattr(mod, "render_close_pack")
    assert hasattr(mod, "write_close_pack")


def test_render_empty_session_has_headers(tmp_path: Path) -> None:
    sess = _seed_session(tmp_path)
    md = render_close_pack(sess)
    assert "# Close Pack" in md
    assert "## §1 Scope" in md
    assert "## §3 Acceptance" in md
    assert "## §4 Audit slice" in md
    assert "## §5 Retro" in md


def test_scope_content_included(tmp_path: Path) -> None:
    sess = _seed_session(tmp_path, with_scope="# SCOPE\n\nDeliver X.")
    md = render_close_pack(sess)
    assert "Deliver X." in md


def test_acceptance_content_included(tmp_path: Path) -> None:
    sess = _seed_session(tmp_path, with_accept="A1 PASS\nA2 PASS")
    md = render_close_pack(sess)
    assert "A1 PASS" in md


def test_retro_content_included(tmp_path: Path) -> None:
    sess = _seed_session(tmp_path, with_retro="## What went well\n- shipped clean")
    md = render_close_pack(sess)
    assert "shipped clean" in md


def test_audit_slice_respects_limit_and_session_filter(tmp_path: Path) -> None:
    sess = _seed_session(tmp_path)
    other_events = [
        {"ts": "2026-05-16T01:00:00Z", "type": "x", "details": {"session_id": "OTHER"}},
    ]
    own_events = [
        {"ts": f"2026-05-16T01:{i:02d}:00Z", "type": "sss.opened",
         "details": {"session_id": "0001_test_sess"}}
        for i in range(5)
    ]
    audit_p = _seed_audit(tmp_path, other_events + own_events)
    md = render_close_pack(sess, audit_event_limit=3, audit_chain_path=audit_p)
    # Only own events show up; limited to 3.
    assert "OTHER" not in md
    assert md.count("sss.opened") == 3


def test_write_close_pack_creates_file(tmp_path: Path) -> None:
    sess = _seed_session(tmp_path, with_scope="x")
    out = write_close_pack(sess)
    assert out == sess / CLOSE_PACK_FILENAME
    assert out.is_file()
    assert "Close Pack" in out.read_text(encoding="utf-8")


def test_make_presentation_synthesis_v101_defaults() -> None:
    s = make_presentation_synthesis(session_id="0001", summary="ship X")
    assert s["cognitive_protocol_version"] == DEFAULT_PROTOCOL_VERSION == "v1.0.1"
    assert s["synthesizer_not_in_opinion_panel"] is True
    assert s["raw_artifacts_available"] is True
    assert isinstance(s["panel_diversity"], dict)


def test_make_presentation_synthesis_rejects_unknown_protocol_version() -> None:
    with pytest.raises(ValueError, match="protocol_version"):
        make_presentation_synthesis(
            session_id="0001", summary="x", protocol_version="v9.9.9"
        )


def test_make_presentation_synthesis_requires_summary() -> None:
    with pytest.raises(ValueError, match="summary"):
        make_presentation_synthesis(session_id="0001", summary="")
