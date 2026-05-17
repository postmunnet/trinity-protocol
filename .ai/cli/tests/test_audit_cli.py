"""Integration tests for `ai audit replay` and `ai audit verify-chain` CLI commands."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.commands.audit import app as audit_app
from cli.core.audit_replay import _canonical_json_legacy, _canonical_json_session

runner = CliRunner()


def _make_session_event(seq: int, prev_hash: str, session_id: str = "sess_t"):
    payload = "{}"
    payload_hash = hashlib.sha256(payload.encode()).hexdigest()
    base = {
        "event_id": f"evt_{seq:032x}",
        "schema_version": "trinity.audit_event.v1",
        "session_id": session_id,
        "seq": seq,
        "event_type": "session.created",
        "ritual": None,
        "capture_id": None,
        "actor": "kernel",
        "ts_utc": "2026-05-13T12:00:00Z",
        "payload_hash": payload_hash,
        "prev_hash": prev_hash,
    }
    h = hashlib.sha256(_canonical_json_session(base).encode()).hexdigest()
    base["payload_json"] = payload
    base["hash"] = h
    return base


def _seed_sqlite(path: Path, rows: list[dict]):
    conn = sqlite3.connect(str(path))
    conn.executescript("""
        CREATE TABLE audit_events (event_id TEXT PRIMARY KEY, schema_version TEXT,
            session_id TEXT, seq INTEGER, event_type TEXT, ritual TEXT,
            capture_id TEXT, actor TEXT, ts_utc TEXT, payload_json TEXT,
            payload_hash TEXT, prev_hash TEXT, hash TEXT,
            UNIQUE(session_id, seq));
    """)
    for r in rows:
        conn.execute(
            "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (r["event_id"], r["schema_version"], r["session_id"], r["seq"],
             r["event_type"], r["ritual"], r["capture_id"], r["actor"], r["ts_utc"],
             r["payload_json"], r["payload_hash"], r["prev_hash"], r["hash"]),
        )
    conn.commit()
    conn.close()


def _make_legacy_ndjson(path: Path, broken: bool = False):
    e1 = {"ts": "t1", "type": "x", "prev_hash": "0", "details": {}}
    e1["hash"] = hashlib.sha256(_canonical_json_legacy(e1).encode()).hexdigest()
    e2 = {"ts": "t2", "type": "y", "prev_hash": e1["hash"], "details": {}}
    e2["hash"] = hashlib.sha256(_canonical_json_legacy(e2).encode()).hexdigest()
    if broken:
        e2["hash"] = "ff" * 32  # tamper
    path.write_text(json.dumps(e1) + "\n" + json.dumps(e2) + "\n")


# ─────────────── verify-chain CLI ───────────────


def test_verify_chain_cli_valid_exit_0(tmp_path: Path):
    """Valid legacy chain → exit 0."""
    p = tmp_path / "events.ndjson"
    _make_legacy_ndjson(p, broken=False)
    result = runner.invoke(audit_app, ["verify-chain", "--legacy-ndjson", str(p)])
    assert result.exit_code == 0
    assert "chain valid" in result.stdout


def test_verify_chain_cli_broken_exit_2(tmp_path: Path):
    """Tampered legacy chain → exit 2."""
    p = tmp_path / "events.ndjson"
    _make_legacy_ndjson(p, broken=True)
    result = runner.invoke(audit_app, ["verify-chain", "--legacy-ndjson", str(p)])
    assert result.exit_code == 2
    assert "chain broken" in result.stdout


def test_verify_chain_cli_missing_source_exit_2(tmp_path: Path):
    result = runner.invoke(audit_app, ["verify-chain", "--legacy-ndjson", str(tmp_path / "noexist.ndjson")])
    assert result.exit_code == 2


def test_verify_chain_cli_session_mode(tmp_path: Path):
    """--session reads <session>/CAPTURE/capture.sqlite path resolved from cwd."""
    e1 = _make_session_event(1, "0")
    e2 = _make_session_event(2, e1["hash"])
    sess_dir = tmp_path / ".ai" / "sessions" / "0001_t_sess"
    capture_dir = sess_dir / "CAPTURE"
    capture_dir.mkdir(parents=True)
    _seed_sqlite(capture_dir / "capture.sqlite", [e1, e2])
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # CliRunner provides its own cwd; recreate the structure inside it
        Path(".ai/sessions/0001_t_sess/CAPTURE").mkdir(parents=True)
        _seed_sqlite(Path(".ai/sessions/0001_t_sess/CAPTURE/capture.sqlite"), [e1, e2])
        result = runner.invoke(audit_app, ["verify-chain", "--session", "0001_t_sess"])
    assert result.exit_code == 0, result.stdout
    assert "chain valid" in result.stdout


def test_verify_chain_cli_strict_unknown_type(tmp_path: Path):
    """Unknown event_type with --strict → exit 1."""
    e1 = _make_session_event(1, "0")
    # Rebuild with bogus type but still-valid hash recomputation
    e1["event_type"] = "bogus.unknown"
    base_for_hash = {k: v for k, v in e1.items() if k not in ("payload_json", "hash")}
    e1["hash"] = hashlib.sha256(_canonical_json_session(base_for_hash).encode()).hexdigest()
    sess = tmp_path / "CAPTURE"
    sess.mkdir(parents=True)
    _seed_sqlite(sess / "capture.sqlite", [e1])
    # Use legacy-ndjson flag with synthetic per-session is not the test target;
    # instead, invoke via direct session arg by isolating the cwd.
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path(".ai/sessions/0001_strict_test/CAPTURE").mkdir(parents=True)
        _seed_sqlite(Path(".ai/sessions/0001_strict_test/CAPTURE/capture.sqlite"), [e1])
        result = runner.invoke(audit_app, [
            "verify-chain", "--session", "0001_strict_test", "--strict",
        ])
    assert result.exit_code == 1, f"expected 1 schema-error, got {result.exit_code}: {result.stdout}"


# ─────────────── replay CLI ───────────────


def test_replay_cli_valid_exit_0(tmp_path: Path):
    p = tmp_path / "events.ndjson"
    _make_legacy_ndjson(p, broken=False)
    result = runner.invoke(audit_app, ["replay", "--legacy-ndjson", str(p)])
    assert result.exit_code == 0
    assert "chain valid" in result.stdout


def test_replay_cli_event_type_filter(tmp_path: Path):
    p = tmp_path / "events.ndjson"
    e1 = {"ts": "t1", "type": "vvv.passed", "prev_hash": "0", "details": {}}
    e1["hash"] = hashlib.sha256(_canonical_json_legacy(e1).encode()).hexdigest()
    e2 = {"ts": "t2", "type": "nnn.passed", "prev_hash": e1["hash"], "details": {}}
    e2["hash"] = hashlib.sha256(_canonical_json_legacy(e2).encode()).hexdigest()
    p.write_text(json.dumps(e1) + "\n" + json.dumps(e2) + "\n")
    result = runner.invoke(audit_app, [
        "replay", "--legacy-ndjson", str(p), "--event-type", "vvv.passed",
    ])
    assert result.exit_code == 0
    assert "vvv.passed" in result.stdout
    # nnn.passed filtered out
    assert "(1 events)" in result.stdout


def test_replay_cli_broken_exit_2(tmp_path: Path):
    p = tmp_path / "events.ndjson"
    _make_legacy_ndjson(p, broken=True)
    result = runner.invoke(audit_app, ["replay", "--legacy-ndjson", str(p)])
    assert result.exit_code == 2


# ─────────────── help / registration ───────────────


def test_audit_help_lists_subcommands():
    result = runner.invoke(audit_app, ["--help"])
    assert result.exit_code == 0
    assert "replay" in result.stdout
    assert "verify-chain" in result.stdout
