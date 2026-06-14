"""Phase D — ai migrate-state tests."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cli.core.migrate_state import build_plan, apply_plan, cleanup_plan
from cli.commands.migrate_state import app as migrate_app


def _seed(home: Path) -> None:
    (home / ".trinity").mkdir(parents=True)
    (home / ".trinity" / "tasks.db").write_text("DB")
    (home / ".trinity-task-notes").mkdir()
    (home / ".trinity-task-notes" / "n.md").write_text("note")
    (home / ".trinity-brain" / "inbox").mkdir(parents=True)
    (home / ".trinity-brain" / "inbox" / "i.md").write_text("inbox")
    (home / ".config" / "notify-cli").mkdir(parents=True)
    (home / ".config" / "notify-cli" / "channels.json").write_text("{}")


def test_dryrun_reports_plan_no_fs_change(tmp_path):
    home = tmp_path / "home"; home.mkdir(); _seed(home)
    rt = tmp_path / "rt"
    report = build_plan(home=home, central=rt)
    assert report.mode == "dry-run"
    assert not (rt / "state").exists(), "dry-run must not create anything"
    item = next(i for i in report.items if i.legacy.name == "tasks.db")
    assert item.legacy_exists and not item.target_exists


def test_apply_copies_and_keeps_legacy(tmp_path):
    home = tmp_path / "home"; home.mkdir(); _seed(home)
    rt = tmp_path / "rt"
    report = apply_plan(build_plan(home=home, central=rt))
    # copied to runtime
    assert (rt / "state" / "task-cli" / "tasks.db").exists()
    assert (rt / "state" / "task-cli" / "notes" / "n.md").exists()
    assert (rt / "state" / "brain-cli" / "inbox" / "i.md").exists()
    assert (rt / "state" / "notify-cli" / "channels.json").exists()
    # legacy KEPT
    assert (home / ".trinity" / "tasks.db").exists()
    assert "copied" in {i.status for i in report.items if i.legacy_exists}


def test_idempotent_rerun(tmp_path):
    home = tmp_path / "home"; home.mkdir(); _seed(home)
    rt = tmp_path / "rt"
    apply_plan(build_plan(home=home, central=rt))
    report2 = apply_plan(build_plan(home=home, central=rt))
    for i in report2.items:
        assert i.status in ("skipped_exists", "skipped_missing"), i.status


def test_cleanup_removes_only_copied(tmp_path):
    home = tmp_path / "home"; home.mkdir(); _seed(home)
    rt = tmp_path / "rt"
    apply_plan(build_plan(home=home, central=rt))
    cleanup_plan(build_plan(home=home, central=rt))
    # legacy removed
    assert not (home / ".trinity" / "tasks.db").exists()
    assert not (home / ".trinity-task-notes").exists()
    # target preserved
    assert (rt / "state" / "task-cli" / "tasks.db").exists()


def test_cleanup_keeps_uncopied(tmp_path):
    home = tmp_path / "home"; home.mkdir(); _seed(home)
    rt = tmp_path / "rt"
    # cleanup WITHOUT apply -> targets don't exist -> must NOT delete legacy
    report = cleanup_plan(build_plan(home=home, central=rt))
    assert (home / ".trinity" / "tasks.db").exists()
    assert "kept" in {i.status for i in report.items if i.legacy_exists}


def test_command_dryrun_json(tmp_path, monkeypatch):
    home = tmp_path / "home"; home.mkdir(); _seed(home)
    monkeypatch.setenv("TRINITY_CENTRAL", str(tmp_path / "central"))
    res = CliRunner().invoke(migrate_app, ["--home", str(home), "--json"])
    assert res.exit_code == 0, res.stdout
    d = json.loads(res.stdout)
    assert d["ok"] is True
    assert d["mode"] == "dry-run"
    assert d["central_root"] == str(tmp_path / "central")


def test_command_defaults_central_when_unconfigured(tmp_path, monkeypatch):
    """R12: central_root has a default (~/.trinity-central), so the command never
    errors on an unconfigured runtime — it resolves to the default (unlike the old
    runtime-root behaviour which raised). Dry-run is pure (touches nothing)."""
    home = tmp_path / "home"; home.mkdir(); _seed(home)
    monkeypatch.delenv("TRINITY_CENTRAL", raising=False)
    monkeypatch.delenv("TRINITY_HOME", raising=False)
    monkeypatch.chdir(tmp_path)  # no .ai/runtime.yaml
    res = CliRunner().invoke(migrate_app, ["--home", str(home), "--json"])
    assert res.exit_code == 0, res.stdout
    d = json.loads(res.stdout)
    assert d["ok"] is True
    assert d["central_root"].endswith(".trinity-central")


def test_r2_new_mappings_present_in_plan(tmp_path):
    """R2: tg-bot config/db + judge/seo-genie/image/wordpress mappings are wired;
    memory-cli stays absent (cwd-relative doctrine)."""
    home = tmp_path / "home"; home.mkdir()
    rt = tmp_path / "rt"
    report = build_plan(home=home, central=rt)
    targets = {str(i.target.relative_to(rt)) for i in report.items}
    siblings = {i.sibling for i in report.items}
    for t in (
        "state/judge-cli", "state/seo-genie-cli", "state/seo-genie-cli/feed",
        "state/image-cli", "state/wordpress-cli",
        "state/tg-bot/config.json", "state/tg-bot/state.db",
    ):
        assert t in targets, f"missing R2 mapping target: {t}"
    assert {"judge-cli", "seo-genie-cli", "image-cli", "wordpress-cli"} <= siblings
    # doctrine: memory-cli is cwd-relative (.memory), never migrated from home
    assert "memory-cli" not in siblings
