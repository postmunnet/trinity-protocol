"""Tests for cli.core.audit_replay — read-only audit chain inspector."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from cli.core.audit_replay import (
    CANONICAL_EVENT_TYPES,
    EXIT_CHAIN_BROKEN,
    EXIT_OK,
    EXIT_SCHEMA_OR_UNKNOWN_TYPE,
    classify_verify_errors,
    iter_events_filtered,
    read_legacy_ndjson,
    read_session_chain,
    verify_chain,
    _canonical_json_legacy,
    _canonical_json_session,
    _event_for_hash_session,
)


# ─────────────── helpers for synthetic chains ───────────────


def _make_session_event(seq: int, prev_hash: str, session_id: str = "sess_1",
                         event_type: str = "session.created") -> dict:
    """Build a valid per-session audit row whose hash recomputes correctly."""
    payload_canonical = "{}"
    payload_hash = hashlib.sha256(payload_canonical.encode()).hexdigest()
    base = {
        "event_id": f"evt_{seq:032x}",
        "schema_version": "trinity.audit_event.v1",
        "session_id": session_id,
        "seq": seq,
        "event_type": event_type,
        "ritual": None,
        "capture_id": None,
        "actor": "kernel",
        "ts_utc": "2026-05-13T12:00:00Z",
        "payload_hash": payload_hash,
        "prev_hash": prev_hash,
    }
    event_hash = hashlib.sha256(_canonical_json_session(base).encode()).hexdigest()
    base["payload_json"] = payload_canonical
    base["hash"] = event_hash
    return base


def _seed_sqlite(tmp_path: Path, rows: list[dict]) -> Path:
    db = tmp_path / "capture.sqlite"
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE audit_events (
            event_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            session_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            ritual TEXT,
            capture_id TEXT,
            actor TEXT NOT NULL,
            ts_utc TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            prev_hash TEXT,
            hash TEXT NOT NULL,
            UNIQUE(session_id, seq)
        );
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
    return db


def _make_legacy_event(prev_hash: str, event_type: str = "session.created",
                       details: dict | None = None) -> dict:
    base = {
        "ts": "2026-05-13T12:00:00Z",
        "type": event_type,
        "prev_hash": prev_hash,
        "details": details or {},
    }
    h = hashlib.sha256(_canonical_json_legacy(base).encode()).hexdigest()
    base["hash"] = h
    return base


# ─────────────── verify_chain happy path ───────────────


def test_verify_chain_happy(tmp_path: Path):
    e1 = _make_session_event(1, "0")
    e2 = _make_session_event(2, e1["hash"])
    e3 = _make_session_event(3, e2["hash"])
    ok, errs = verify_chain([e1, e2, e3], chain_kind="session")
    assert ok, errs
    assert errs == []


def test_verify_chain_legacy_happy():
    e1 = _make_legacy_event("0")
    e2 = _make_legacy_event(e1["hash"])
    e3 = _make_legacy_event(e2["hash"])
    ok, errs = verify_chain([e1, e2, e3], chain_kind="legacy")
    assert ok, errs


def test_verify_chain_empty():
    ok, errs = verify_chain([], chain_kind="session")
    assert ok and errs == []


# ─────────────── verify_chain failure detection ───────────────


def test_verify_chain_detects_prev_hash_mismatch():
    e1 = _make_session_event(1, "0")
    e2 = _make_session_event(2, "ff" * 32)  # wrong prev_hash
    ok, errs = verify_chain([e1, e2], chain_kind="session")
    assert not ok
    assert any("prev_hash mismatch" in e for e in errs)


def test_verify_chain_detects_seq_gap():
    e1 = _make_session_event(1, "0")
    e3 = _make_session_event(3, e1["hash"])  # skipped seq=2
    ok, errs = verify_chain([e1, e3], chain_kind="session")
    assert not ok
    assert any("seq gap" in e for e in errs)


def test_verify_chain_detects_hash_mismatch():
    e1 = _make_session_event(1, "0")
    e1["hash"] = "deadbeef" * 8  # tampered
    ok, errs = verify_chain([e1], chain_kind="session")
    assert not ok
    assert any("hash mismatch" in e for e in errs)


def test_verify_chain_strict_unknown_type():
    e1 = _make_session_event(1, "0", event_type="bogus.type")
    ok, errs = verify_chain([e1], chain_kind="session", strict=True)
    assert not ok
    assert any("unknown event_type" in e for e in errs)


def test_verify_chain_strict_accepts_current_legacy_kernel_events():
    """Strict legacy replay must accept event names the runtime has
    historically emitted into .ai/audit/events.ndjson. This prevents a
    valid hash chain from becoming unusable solely because the registry
    lagged behind the CLI surface.
    """
    event_types = [
        "sss.invoked",
        "vvv.invoked",
        "nnn.invoked",
        "plan.budget_checked",
        "gogogo.invoked",
        "gogogo.step.started",
        "gogogo.step.completed",
        "verifier.consolidated",
        "ddd.invoked",
        "ddd.completed",
        "rrr.invoked",
        "rrr.delegated_call",
        "rrr.retroactive",
        "snapshot.created",
        "session.archived_retroactive",
        "ritual_constitution.ratified",
        "llm.call_failed",
    ]
    events = []
    prev = "0"
    for typ in event_types:
        ev = _make_legacy_event(prev, event_type=typ)
        events.append(ev)
        prev = ev["hash"]

    ok, errs = verify_chain(events, chain_kind="legacy", strict=True)
    assert ok, errs


def test_current_emitted_events_are_in_canonical_registry():
    needed = {
        "transport.envelope_accepted",
        "transport.envelope_refused.unsigned",
        "transport.envelope_refused.badkey",
        "transport.envelope_refused.replay",
        "transport.envelope_refused.overscope",
        "policy.gate_required",
        "policy.refused",
        "policy.queried",
        "sandbox.applied",
        "sandbox.profile_missing",
        "sandbox.profile_invalid",
        "sandbox.runtime_unavailable",
        "sandbox.runtime_disabled",
        "sandbox.allowlist_unenforced",
        "plan_helper.tool_inferred",
        "ddd.advisory_only_refused",
    }
    missing = needed - CANONICAL_EVENT_TYPES
    assert not missing


def test_verify_chain_non_strict_ignores_unknown_type():
    """Without --strict, unknown types pass (hash still checked)."""
    e1 = _make_session_event(1, "0", event_type="bogus.type")
    ok, errs = verify_chain([e1], chain_kind="session", strict=False)
    assert ok


# ─────────────── classify_verify_errors → exit codes ───────────────


def test_classify_no_errors_returns_ok():
    assert classify_verify_errors([]) == EXIT_OK


def test_classify_chain_error_returns_2():
    assert classify_verify_errors(["hash mismatch at seq=3: ..."]) == EXIT_CHAIN_BROKEN
    assert classify_verify_errors(["prev_hash mismatch at seq=2"]) == EXIT_CHAIN_BROKEN
    assert classify_verify_errors(["seq gap at idx=4"]) == EXIT_CHAIN_BROKEN


def test_classify_schema_error_returns_1():
    """Unknown-type-only errors should be exit code 1 (schema/registry)."""
    assert classify_verify_errors(["unknown event_type at seq=1: 'bogus'"]) == EXIT_SCHEMA_OR_UNKNOWN_TYPE


def test_classify_chain_trumps_schema():
    """If both kinds of errors, chain-broken wins."""
    errs = ["unknown event_type at seq=1: 'bogus'", "hash mismatch at seq=2"]
    assert classify_verify_errors(errs) == EXIT_CHAIN_BROKEN


# ─────────────── readers ───────────────


def test_read_session_chain_empty(tmp_path: Path):
    db = _seed_sqlite(tmp_path, [])
    rows = read_session_chain(db)
    assert rows == []


def test_read_session_chain_multi(tmp_path: Path):
    e1 = _make_session_event(1, "0")
    e2 = _make_session_event(2, e1["hash"])
    db = _seed_sqlite(tmp_path, [e1, e2])
    rows = read_session_chain(db)
    assert [r["seq"] for r in rows] == [1, 2]


def test_read_session_chain_missing_file(tmp_path: Path):
    """Returns [] gracefully when sqlite path doesn't exist."""
    rows = read_session_chain(tmp_path / "nonexistent.sqlite")
    assert rows == []


def test_read_legacy_ndjson(tmp_path: Path):
    p = tmp_path / "events.ndjson"
    e1 = _make_legacy_event("0")
    e2 = _make_legacy_event(e1["hash"])
    p.write_text(json.dumps(e1) + "\n" + json.dumps(e2) + "\n")
    rows = read_legacy_ndjson(p)
    assert len(rows) == 2


def test_read_legacy_ndjson_skips_malformed(tmp_path: Path):
    p = tmp_path / "events.ndjson"
    e1 = _make_legacy_event("0")
    p.write_text(json.dumps(e1) + "\n{not-valid-json\n" + json.dumps(e1) + "\n")
    rows = read_legacy_ndjson(p)
    # malformed line skipped; 2 valid rows survive
    assert len(rows) == 2


def test_read_legacy_ndjson_missing_file(tmp_path: Path):
    rows = read_legacy_ndjson(tmp_path / "nonexistent.ndjson")
    assert rows == []


# ─────────────── iter_events_filtered ───────────────


def test_iter_events_filtered_from_to():
    events = [_make_session_event(i, "0") for i in (1, 2, 3, 4, 5)]
    out = list(iter_events_filtered(events, from_seq=2, to_seq=4))
    assert [e["seq"] for e in out] == [2, 3, 4]


def test_iter_events_filtered_event_type():
    e1 = _make_session_event(1, "0", event_type="vvv.passed")
    e2 = _make_session_event(2, e1["hash"], event_type="nnn.passed")
    e3 = _make_session_event(3, e2["hash"], event_type="vvv.passed")
    out = list(iter_events_filtered([e1, e2, e3], event_type="vvv.passed"))
    assert [e["seq"] for e in out] == [1, 3]


def test_iter_events_filtered_session():
    e1 = _make_session_event(1, "0", session_id="sess_A")
    e2 = _make_session_event(2, e1["hash"], session_id="sess_B")
    e3 = _make_session_event(3, e2["hash"], session_id="sess_A")
    out = list(iter_events_filtered([e1, e2, e3], session="sess_A"))
    assert [e["session_id"] for e in out] == ["sess_A", "sess_A"]


# ─────────────── canonical-form invariants ───────────────


def test_canonical_session_vs_legacy_differ_on_unicode():
    """Confirm the two canonical forms produce different bytes for non-ASCII."""
    obj = {"a": "café"}
    session_form = _canonical_json_session(obj)
    legacy_form = _canonical_json_legacy(obj)
    assert session_form != legacy_form  # ensure_ascii diverges them
    assert "café" in session_form
    assert r"\u" in legacy_form


def test_canonical_event_types_registry_size():
    """Registry should be ≥40 distinct event types (kernel + RecordProxy unified)."""
    assert len(CANONICAL_EVENT_TYPES) >= 40
