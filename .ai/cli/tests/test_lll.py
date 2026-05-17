"""Phase 2.3 — `ai lll` snapshot tests.

Covers:

  - `_git_state` returns available=False outside a git repo, and a
    structured branch/dirty record inside one.
  - `_session_state` returns active=False when no session is active.
  - `_open_work` counts files in THINK/SANDBOX/DO.
  - `_recent_audit` walks the chain and returns last N entries (most
    recent first).
  - `_memory_hints` returns [] when memory-cli is unreachable.
  - The full `_run` writes a `lll.invoked` event to the audit chain
    (D9: read-only events still append).
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from cli.commands.lll import (
    _git_state,
    _memory_hints,
    _memory_query_variants,
    _open_work,
    _recent_audit,
    _render_human,  # smoke import only
    _session_state,
)
from cli.core.audit import get_chain_for_project
from cli.core.ssot import SSOTLoader


# ─────────── helpers ───────────


def _make_project(tmp: Path) -> Path:
    """Build a minimal Trinity project skeleton at tmp/proj."""
    proj = tmp / "proj"
    (proj / ".ai" / "audit").mkdir(parents=True)
    (proj / ".ai" / "state").mkdir(parents=True)
    (proj / ".ai" / "sessions" / "active").mkdir(parents=True)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({
            "version": "1.0",
            "paths": {"state": "${ai_root}/state"},
        })
    )
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({
            "version": "1.0",
            "current_session": None,
            "last_event_hash": None,
        })
    )
    return proj


def _seed_chain(proj: Path, events: list) -> None:
    chain = get_chain_for_project(proj)
    for typ, details in events:
        chain.append(typ, details)


# ─────────── git ───────────


def test_git_state_returns_unavailable_outside_repo(tmp_path: Path):
    proj = _make_project(tmp_path)
    state = _git_state(proj)
    assert state.get("available") is False


def test_git_state_in_clean_init_repo(tmp_path: Path):
    proj = _make_project(tmp_path)
    subprocess.run(["git", "init", "-b", "main"], cwd=str(proj), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=str(proj), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(proj), check=True, capture_output=True)
    (proj / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "."], cwd=str(proj), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=str(proj), check=True, capture_output=True)
    state = _git_state(proj)
    assert state.get("available") is True
    assert state.get("branch") == "main"
    assert state.get("dirty_count") == 0
    assert state.get("head"), "short HEAD should be present after first commit"


# ─────────── session ───────────


def test_session_state_inactive(tmp_path: Path):
    proj = _make_project(tmp_path)
    config = SSOTLoader(proj).load()
    s = _session_state(config)
    assert s["active"] is False
    assert s["session_id"] is None


def test_session_state_active(tmp_path: Path):
    proj = _make_project(tmp_path)
    sess_dir = (
        proj / ".ai" / "sessions" / "active"
        / "0001_2026-05-01_test_lll-smoke"
    )
    sess_dir.mkdir(parents=True)
    status_path = proj / ".ai" / "state" / "status.json"
    status_path.write_text(
        json.dumps({
            "version": "1.0",
            "current_session": str(sess_dir),
            "last_event_hash": None,
            "graph_state": "THINK",
        })
    )
    config = SSOTLoader(proj).load()
    s = _session_state(config)
    assert s["active"] is True
    assert s["session_id"] == "0001_2026-05-01_test_lll-smoke"
    assert s["graph_state"] == "THINK"


# ─────────── open work ───────────


def test_open_work_counts_files(tmp_path: Path):
    sess = tmp_path / "sess"
    (sess / "THINK").mkdir(parents=True)
    (sess / "THINK" / "01.md").write_text("a")
    (sess / "THINK" / "02.md").write_text("b")
    (sess / "SANDBOX" / "01_DEBATE").mkdir(parents=True)
    (sess / "SANDBOX" / "01_DEBATE" / "x.md").write_text("c")
    out = _open_work(sess)
    assert out["think_files"] == 2
    assert out["sandbox_files"] == 1
    assert out["do_dev_files"] == 0


# ─────────── audit ───────────


def test_recent_audit_returns_last_n_in_reverse_order(tmp_path: Path):
    proj = _make_project(tmp_path)
    _seed_chain(proj, [
        ("event.a", {"session_id": "s1", "decided_by": "kernel"}),
        ("event.b", {"session_id": "s1", "decided_by": "human"}),
        ("event.c", {"session_id": "s2", "decided_by": "verifier"}),
    ])
    out = _recent_audit(proj, n=2)
    assert len(out) == 2
    # Most recent first
    assert out[0]["type"] == "event.c"
    assert out[1]["type"] == "event.b"
    assert out[0]["decided_by"] == "verifier"


# ─────────── memory hints ───────────


def test_memory_hints_returns_empty_on_no_query(tmp_path: Path):
    proj = _make_project(tmp_path)
    assert _memory_hints(proj, "") == []


def test_memory_hints_returns_empty_when_memory_cli_unregistered(tmp_path: Path):
    # No tools.yaml → call_tool returns ok=False; helper returns [].
    proj = _make_project(tmp_path)
    assert _memory_hints(proj, "auth bug") == []


def test_memory_query_variants_shorten_long_session_prompt():
    variants = _memory_query_variants(
        "fix workflow bugs from lll-to-close audit "
        "0001_2026-05-16_19_17_pm_fix-workflow-bugs"
    )
    assert variants[0].startswith("fix workflow bugs")
    assert "workflow bugs lll close audit" in variants
    assert "workflow bugs lll" in variants
    assert "workflow" in variants


def test_memory_hints_falls_back_to_shorter_query(tmp_path: Path, monkeypatch):
    proj = _make_project(tmp_path)
    calls = []

    class FakeInvocation:
        def __init__(self, results):
            self.ok = True
            self.envelope = {"data": {"results": results}}

    def fake_call_tool(project_root, tool_name, command, timeout_seconds):
        calls.append(command)
        if 'search "workflow"' in command:
            return FakeInvocation([{"id": "retro-1", "title": "Workflow fix"}])
        return FakeInvocation([])

    monkeypatch.setattr("cli.commands.lll.call_tool", fake_call_tool)
    out = _memory_hints(
        proj,
        "fix workflow bugs from lll-to-close audit",
    )
    assert out == [{"id": "retro-1", "title": "Workflow fix"}]
    assert len(calls) > 1


# ─────────── full run (audit append) ───────────


def test_run_appends_lll_invoked_event(tmp_path: Path, monkeypatch):
    proj = _make_project(tmp_path)
    monkeypatch.chdir(proj)
    from cli.commands.lll import _run  # late import: cwd matters

    # Suppress rendering output to keep test stdout clean.
    code = _run(json_out=True, audit_n=3)
    assert code == 0

    chain = get_chain_for_project(proj)
    types = [ev["type"] for ev in chain.iter_events()]
    assert types == ["lll.invoked"]
    last = list(chain.iter_events())[-1]
    assert last["details"]["audit_n"] == 3
    assert last["details"]["decided_by"] == "human"


def test_run_json_includes_project_signal(tmp_path: Path, monkeypatch, capsys):
    proj = _make_project(tmp_path)
    retro = proj / ".claude" / "retrospectives" / "2026-05" / "0001.md"
    retro.parent.mkdir(parents=True)
    retro.write_text(
        """# Retro

### Pending Items / §30

- [ ] PROD bundle deploy plan write

### Regression Watch / §31

- Watch order_model.php RC transitions.
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(proj)
    from cli.commands.lll import _run

    code = _run(json_out=True, audit_n=1)

    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert "git" in out
    assert "session" in out
    assert out["project_signal"]["available"] is True
    assert out["project_signal"]["pending"][0]["source"] == ".claude/retrospectives/2026-05/0001.md"
