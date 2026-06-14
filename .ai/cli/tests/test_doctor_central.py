"""R12 — `ai doctor central` central_root health check (read-only)."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from cli.commands.doctor import app as doctor_app


def _seed_central(central: Path) -> None:
    (central / "memory").mkdir(parents=True)
    (central / "registry").mkdir(parents=True)
    (central / "registry" / "projects.json").write_text('{"version":"1","projects":[],"runtimes":{}}')
    (central / "state" / "task-cli").mkdir(parents=True)
    (central / "state" / "task-cli" / "tasks.db").write_text("DB")
    (central / "state" / "judge-cli").mkdir(parents=True)


def test_central_reports_health_clean(tmp_path, monkeypatch):
    central = tmp_path / "central"; _seed_central(central)
    monkeypatch.setenv("TRINITY_CENTRAL", str(central))
    monkeypatch.delenv("TRINITY_HOME", raising=False)
    monkeypatch.chdir(tmp_path)  # no runtime.yaml -> runtime unresolved -> no split

    res = CliRunner().invoke(doctor_app, ["central", "--json"])
    assert res.exit_code == 0, res.stdout
    d = json.loads(res.stdout)
    assert d["ok"] is True
    assert d["central_root"] == str(central)
    assert d["checks"]["memory"] is True
    assert d["checks"]["task_db"] is True
    assert d["checks"]["registry"] is True
    assert d["sibling_state"]["task-cli"] is True
    assert d["sibling_state"]["judge-cli"] is True
    assert d["sibling_state"]["wordpress-cli"] is False  # not seeded
    assert d["has_split_durable_data"] is False


def test_central_detects_split_under_runtime(tmp_path, monkeypatch):
    central = tmp_path / "central"; _seed_central(central)
    runtime = tmp_path / "rt"
    (runtime / "state" / "task-cli").mkdir(parents=True)  # durable still under runtime
    monkeypatch.setenv("TRINITY_CENTRAL", str(central))
    monkeypatch.setenv("TRINITY_HOME", str(runtime))

    res = CliRunner().invoke(doctor_app, ["central", "--json"])
    assert res.exit_code == 0, res.stdout
    d = json.loads(res.stdout)
    assert d["has_split_durable_data"] is True
    assert d["split"]["task_under_runtime"] is True


def test_central_is_read_only(tmp_path, monkeypatch):
    """Passive core: running the check must not create central_root if absent."""
    central = tmp_path / "central"  # NOT created
    monkeypatch.setenv("TRINITY_CENTRAL", str(central))
    monkeypatch.delenv("TRINITY_HOME", raising=False)
    monkeypatch.chdir(tmp_path)

    res = CliRunner().invoke(doctor_app, ["central", "--json"])
    assert res.exit_code == 0, res.stdout
    d = json.loads(res.stdout)
    assert d["checks"]["central_root_exists"] is False
    assert not central.exists(), "doctor central must not create central_root (read-only)"
