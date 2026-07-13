"""B2 — `ai nnn --plan-envelope <missing>` must fail cleanly.

Regression coverage: before this fix, a missing/unreadable plan-envelope
path made `_nnn_inner` call `envelope_path.read_text()` unguarded, which
raised a raw `FileNotFoundError` traceback (with a locals dump) straight
through the CLI — a newcomer who mistyped the path saw a crash instead of
a friendly message.

This test drives `nnn` the same way `test_nnn_amend.py` does (direct
function call against a seeded session, not a subprocess/CliRunner), and
asserts:

  (a) no unhandled exception escapes — only `typer.Exit` (the project's
      existing clean-exit idiom, matched from callback()'s own
      `raise typer.Exit(2)` calls for other missing-input cases)
  (b) the process exit path is nonzero
  (c) a single friendly line is printed (not a traceback / locals dump)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
import yaml

from test_goal_loop import _make_project


def _seed_for_cli(tmp_path: Path):
    """Seed ssot.yaml + status.json + a passed vvv marker so `_run`
    resolves this session from cwd and clears the vvv_pass gate,
    mirroring test_nnn_amend.py's `_seed_for_cli` helper."""
    proj, sess = _make_project(tmp_path)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps(
            {"version": "1.0", "current_session": str(sess), "last_event_hash": None}
        )
    )
    (sess / ".state" / "vvv_pass").write_text("ok")
    return proj, sess


def test_missing_plan_envelope_exits_cleanly(tmp_path, monkeypatch, capsys):
    proj, sess = _seed_for_cli(tmp_path)
    monkeypatch.chdir(proj)

    missing_path = tmp_path / "does_not_exist.json"
    assert not missing_path.exists()

    from cli.commands.nnn import _run

    # (a) only the project's own clean-exit idiom escapes — never a raw
    # FileNotFoundError / unhandled traceback.
    with pytest.raises(typer.Exit) as exc:
        _run(missing_path, None, None, None, None)

    # (b) nonzero exit code
    assert exc.value.exit_code != 0

    # (c) friendly single-line message, not a traceback/locals dump
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "plan envelope not found" in combined
    # rich may soft-wrap the long path across lines, so match the
    # basename rather than the exact (possibly wrapped) full path.
    assert missing_path.name in combined
    assert "Traceback" not in combined
    assert "FileNotFoundError" not in combined


def test_missing_plan_envelope_via_callback(tmp_path, monkeypatch, capsys):
    """Same scenario, but entered through the public `callback()` — the
    real `ai nnn --plan-envelope <missing>` entrypoint — to prove the
    guard is reachable from the actual CLI surface, not just `_run`."""
    proj, sess = _seed_for_cli(tmp_path)
    monkeypatch.chdir(proj)

    missing_path = tmp_path / "also_missing.json"

    from cli.commands import nnn

    class _FakeCtx:
        invoked_subcommand = None

    with pytest.raises(typer.Exit) as exc:
        nnn.callback(
            ctx=_FakeCtx(),
            plan_envelope=missing_path,
            amend=False,
            history=False,
            scope_md=None,
            acceptance_md=None,
            hmac_envelope_file=None,
            session=None,
        )

    assert exc.value.exit_code != 0
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "plan envelope not found" in combined
    assert "Traceback" not in combined
