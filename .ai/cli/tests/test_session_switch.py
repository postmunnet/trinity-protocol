"""`ai session switch <sid|path>` — pointer switch, audited (2026-06-12).

Replaces the error-prone manual edit of `.ai/state/status.json`
(current_session is a top-level key; `ai close` nulls it). Covers:
  - switch by session id (folder name) and by full path
  - missing session → typer.Exit(2)
  - archived capsule (.archive suffix / archive/ parent) → typer.Exit(2)
  - status.json current_session updated + `session.switched` audit event
  - no-op switch to the already-current session → exit 0, no audit event
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
import yaml

from cli.commands.session import switch
from cli.core.audit import AuditChain


def _make_switch_project(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    (proj / ".ai" / "audit").mkdir(parents=True)
    (proj / ".ai" / "state").mkdir(parents=True)
    (proj / ".ai" / "sessions" / "archive").mkdir(parents=True)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    for sid in ("0001_feat-alpha", "0002_feat-beta"):
        (proj / ".ai" / "sessions" / sid / ".state").mkdir(parents=True)
    (proj / ".ai" / "sessions" / "0003_feat-old.archive").mkdir(parents=True)
    (proj / ".ai" / "sessions" / "archive" / "0004_feat-older").mkdir(parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({
            "version": "1.0",
            "system": {"status": "idle"},
            "current_session": str(proj / ".ai" / "sessions" / "0001_feat-alpha"),
        })
    )
    return proj


def _status(proj: Path) -> dict:
    return json.loads((proj / ".ai" / "state" / "status.json").read_text())


def _events(proj: Path, type_name: str) -> list:
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    return [ev for ev in chain.iter_events() if ev["type"] == type_name]


def test_switch_by_id_updates_pointer_and_audits(tmp_path, monkeypatch) -> None:
    proj = _make_switch_project(tmp_path)
    monkeypatch.chdir(proj)
    switch("0002_feat-beta")

    assert _status(proj)["current_session"] == str(
        (proj / ".ai" / "sessions" / "0002_feat-beta").resolve()
    )
    events = _events(proj, "session.switched")
    assert len(events) == 1
    d = events[0]["details"]
    assert d["session_id"] == "0002_feat-beta"
    assert d["to"].endswith("0002_feat-beta")
    assert d["from"].endswith("0001_feat-alpha")
    assert d["decided_by"] == "human"


def test_switch_by_full_path(tmp_path, monkeypatch) -> None:
    proj = _make_switch_project(tmp_path)
    monkeypatch.chdir(proj)
    switch(str(proj / ".ai" / "sessions" / "0002_feat-beta"))
    assert _status(proj)["current_session"].endswith("0002_feat-beta")


def test_switch_missing_session_exits_2(tmp_path, monkeypatch) -> None:
    proj = _make_switch_project(tmp_path)
    monkeypatch.chdir(proj)
    with pytest.raises(typer.Exit) as exc_info:
        switch("0099_feat-nope")
    assert exc_info.value.exit_code == 2
    # pointer untouched
    assert _status(proj)["current_session"].endswith("0001_feat-alpha")


@pytest.mark.parametrize("ident", ["0003_feat-old", "0004_feat-older"])
def test_switch_archived_refused(tmp_path, monkeypatch, ident) -> None:
    proj = _make_switch_project(tmp_path)
    monkeypatch.chdir(proj)
    with pytest.raises(typer.Exit) as exc_info:
        switch(ident)
    assert exc_info.value.exit_code == 2
    assert _status(proj)["current_session"].endswith("0001_feat-alpha")
    assert _events(proj, "session.switched") == []


def test_switch_noop_same_session_exit_0_no_audit(tmp_path, monkeypatch) -> None:
    proj = _make_switch_project(tmp_path)
    monkeypatch.chdir(proj)
    with pytest.raises(typer.Exit) as exc_info:
        switch("0001_feat-alpha")
    assert exc_info.value.exit_code == 0
    assert _events(proj, "session.switched") == []
