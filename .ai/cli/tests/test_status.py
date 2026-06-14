from __future__ import annotations

from pathlib import Path
import json

from typer.testing import CliRunner

from cli.commands.session import _init_session_local_state
from cli.core.state import SessionLocalState
from cli.main import app


runner = CliRunner()


def test_session_local_state_starts_graph_ready(tmp_path: Path) -> None:
    session_path = tmp_path / "session"

    _init_session_local_state(session_path)

    state = json.loads(
        (session_path / ".state" / "session_state.json").read_text(
            encoding="utf-8"
        )
    )
    assert "state" not in state
    assert state["legacy_state"] == "INIT"
    assert state["graph_state"] == "READY"


def test_set_graph_state_migrates_ambiguous_state_key(tmp_path: Path) -> None:
    session_path = tmp_path / "session"
    state_dir = session_path / ".state"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "session_state.json"
    state_file.write_text(
        json.dumps({"version": "1.0", "state": "INIT", "graph_state": "READY"}),
        encoding="utf-8",
    )

    sls = SessionLocalState(session_path)
    assert sls.current_state() == "INIT"

    sls.set_graph_state("THINK")

    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert "state" not in state
    assert state["legacy_state"] == "INIT"
    assert state["graph_state"] == "THINK"


def test_status_from_bound_project_without_ai_runtime(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "example_project"
    project_root.mkdir()
    env = {
        "TRINITY_HOME": str(tmp_path / "trinity"),
        "MEMORY_HOME": str(tmp_path / "memory"),
    }

    add_result = runner.invoke(
        app,
        ["project", "add", str(project_root), "--name", "Example Project Production"],
        env=env,
    )
    assert add_result.exit_code == 0, add_result.output

    monkeypatch.chdir(project_root)
    status_result = runner.invoke(app, ["status"], env=env)

    assert status_result.exit_code == 0, status_result.output
    assert "Trinity Project Status" in status_result.output
    assert "example_project_production" in status_result.output
    assert "Memory DB File" in status_result.output
    assert "memory.sqlite" in status_result.output  # project-local doctrine (retro-0060)


def test_project_add_current_and_doctor_cli(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "Example Project"
    project_root.mkdir()
    env = {
        "TRINITY_HOME": str(tmp_path / "trinity"),
        "TRINITY_MEMORY_HOME": str(tmp_path / "memory"),
    }

    add_result = runner.invoke(
        app,
        ["project", "add", str(project_root), "--name", "Example Project", "--json"],
        env=env,
    )
    assert add_result.exit_code == 0, add_result.output
    assert (project_root / ".trinity" / "project.yaml").exists()
    assert (project_root / "AGENTS.md").exists()
    assert (project_root / "trinity").exists()
    assert (project_root / "trinity").stat().st_mode & 0o111
    assert "TRINITY_PROJECT_BINDING_START" in (project_root / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    assert (project_root / ".ai" / ".memory" / "memory.sqlite").exists()  # project-local doctrine (retro-0060)

    monkeypatch.chdir(project_root)
    current_result = runner.invoke(app, ["project", "current", "--json"], env=env)
    assert current_result.exit_code == 0, current_result.output
    assert '"project_slug": "example_project"' in current_result.output
    assert '"source": "binding"' in current_result.output

    doctor_result = runner.invoke(app, ["project", "doctor"], env=env)
    assert doctor_result.exit_code == 0, doctor_result.output


def test_project_add_can_skip_agent_shim(tmp_path: Path) -> None:
    project_root = tmp_path / "Example Project"
    project_root.mkdir()
    env = {
        "TRINITY_HOME": str(tmp_path / "trinity"),
        "MEMORY_HOME": str(tmp_path / "memory"),
    }

    result = runner.invoke(
        app,
        [
            "project",
            "add",
            str(project_root),
            "--name",
            "Example Project",
            "--no-agent-shim",
        ],
        env=env,
    )

    assert result.exit_code == 0, result.output
    assert not (project_root / "AGENTS.md").exists()


def test_project_add_can_skip_wrapper(tmp_path: Path) -> None:
    project_root = tmp_path / "Example Project"
    project_root.mkdir()
    env = {
        "TRINITY_HOME": str(tmp_path / "trinity"),
        "MEMORY_HOME": str(tmp_path / "memory"),
    }

    result = runner.invoke(
        app,
        [
            "project",
            "add",
            str(project_root),
            "--name",
            "Example Project",
            "--no-wrapper",
        ],
        env=env,
    )

    assert result.exit_code == 0, result.output
    assert not (project_root / "trinity").exists()


def test_project_add_rejects_path_that_does_not_exist_on_this_machine(tmp_path: Path) -> None:
    env = {
        "TRINITY_HOME": str(tmp_path / "trinity"),
        "MEMORY_HOME": str(tmp_path / "memory"),
    }

    result = runner.invoke(
        app,
        ["project", "add", str(tmp_path / "remote-host-path"), "--name", "example_project"],
        env=env,
    )

    assert result.exit_code != 0
    assert "project path must exist on this machine" in result.output


def test_status_handles_stale_session_path_in_bound_project(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / "example_project"
    project_root.mkdir()
    ai_state = project_root / ".ai" / "state"
    ai_state.mkdir(parents=True)
    (project_root / ".ai" / "ssot.yaml").write_text(
        """
version: "1.0"
paths:
  state: "${ai_root}/state"
""",
        encoding="utf-8",
    )
    (ai_state / "status.json").write_text(
        json.dumps({
            "current_session": str(project_root / ".ai" / "sessions" / "missing"),
            "graph_state": "THINK",
        }),
        encoding="utf-8",
    )
    env = {
        "TRINITY_HOME": str(tmp_path / "trinity"),
        "MEMORY_HOME": str(tmp_path / "memory"),
    }
    add_result = runner.invoke(
        app,
        ["project", "add", str(project_root), "--name", "example_project"],
        env=env,
    )
    assert add_result.exit_code == 0, add_result.output

    monkeypatch.chdir(project_root)
    result = runner.invoke(app, ["status"], env=env)

    assert result.exit_code == 0, result.output
    assert "Current session path not found" in result.output
    assert "example_project" in result.output
