"""ai wizard new — v0 session scaffolder tests.

Tests bypass the real `ai session new` subprocess via WIZARD_SKIP_SESSION_NEW=1
and manually construct the project + session fixture so the only logic
under test is wizard's template scaffolding + state resolution.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
import yaml

from cli.commands.wizard import new as wizard_new
from cli.core.wizard_templates import VALID_TYPES, render


def _build_proj_with_session(tmp_path: Path) -> tuple[Path, Path]:
    proj = tmp_path / "proj"
    (proj / ".ai" / "audit").mkdir(parents=True)
    (proj / ".ai" / "policies").mkdir(parents=True)
    (proj / ".ai" / "graphs").mkdir(parents=True)
    (proj / ".ai" / "sessions").mkdir(parents=True)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    sess = proj / ".ai" / "sessions" / "0001_test_session"
    sess.mkdir(parents=True)
    (sess / "THINK").mkdir()
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({"version": "1.0", "current_session": str(sess)})
    )
    return proj, sess


def test_wizard_new_feat_default(tmp_path, monkeypatch):
    """A_WIZARD_NEW_FEAT — default --type=feat scaffolds 01_PROMPT.md."""
    proj, sess = _build_proj_with_session(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv("WIZARD_SKIP_SESSION_NEW", "1")

    code = wizard_new("smoke-feat", type="feat", force=False)
    assert code == 0

    prompt = sess / "THINK" / "01_PROMPT.md"
    assert prompt.exists()
    body = prompt.read_text(encoding="utf-8")
    assert "Q1 — Goal" in body
    assert "type: feat" in body
    assert sess.name in body  # slug substituted


@pytest.mark.parametrize("ttype", sorted(VALID_TYPES))
def test_all_5_types_render_non_empty(ttype, tmp_path):
    """A_TYPES_5 — every valid type renders non-empty content with all 5 Qs."""
    body = render(ttype, slug="some-slug", date="2026-05-10")
    assert len(body) > 500
    for q in range(1, 6):
        assert f"Q{q} —" in body
    assert f"type: {ttype}" in body


def test_invalid_type_errors(tmp_path, monkeypatch):
    """A_INVALID_TYPE_ERRORS — bogus --type → typer.Exit(2)."""
    proj, _sess = _build_proj_with_session(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv("WIZARD_SKIP_SESSION_NEW", "1")

    with pytest.raises(typer.Exit) as exc:
        wizard_new("smoke", type="bogus", force=False)
    assert exc.value.exit_code == 2


def test_force_overrides_existing_prompt(tmp_path, monkeypatch):
    """A_FORCE_FLAG_OVERRIDES_EXISTING_PROMPT — pre-existing PROMPT.md without --force fails; with --force overwrites."""
    proj, sess = _build_proj_with_session(tmp_path)
    monkeypatch.chdir(proj)
    monkeypatch.setenv("WIZARD_SKIP_SESSION_NEW", "1")

    prompt = sess / "THINK" / "01_PROMPT.md"
    prompt.write_text("OPERATOR EDITED")

    # Without --force: refuse with exit 2.
    with pytest.raises(typer.Exit) as exc:
        wizard_new("smoke", type="feat", force=False)
    assert exc.value.exit_code == 2
    assert prompt.read_text() == "OPERATOR EDITED"  # untouched

    # With --force: overwrite.
    code = wizard_new("smoke", type="feat", force=True)
    assert code == 0
    body = prompt.read_text()
    assert "Q1 — Goal" in body
    assert "OPERATOR EDITED" not in body


def test_next_action_footer_in_render_output(tmp_path):
    """A_NEXT_ACTION_FOOTER — rendered template references the next-action.

    The Console panel is the surface; we don't capture stdout (Rich
    requires an explicit fixture). Instead assert the rendered template
    body itself includes the `ai vvv --answers-file` handoff hint that
    wizard.py also prints in its panel.
    """
    body = render("feat", slug="x", date="2026-05-10")
    assert "ai vvv --answers-file=THINK/01_PROMPT.md" in body
