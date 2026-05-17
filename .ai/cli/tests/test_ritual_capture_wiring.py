"""Tests for RecordProxy v1 Part 2: capture() transaction wiring.

Plan ref: session feat-recordproxy-capture-wiring-v1 plan steps S6/S7/S8/S9.

S6 — per-ritual smoke: AuditChain.append called inside a capture() block
     stamps capture_id automatically; capture.sqlite contains a captures
     row after the block exits.

S7 — referential integrity: every NDJSON event with capture_id != None
     resolves to a captures.capture_id row in the session SQLite.

S8 — static-grep singleton: exactly ONE ``with capture(`` block per
     ritual command file (and one in session.py for sss-via-session.new).

S9 — AuditChain.append signature stability (Article XXIX) + capture_id
     contextvar lifecycle (no cross-invocation leak).
"""
from __future__ import annotations

import inspect
import json
import sqlite3
from pathlib import Path

import pytest

from cli.core.audit import AuditChain
from cli.core.recordproxy import capture
from cli.core.recordproxy.emit import (
    emit_via_proxy,
    get_active_capture_id,
    set_active_capture_id,
    reset_active_capture_id,
)
from cli.core.recordproxy.schemas import AUDIT_EVENT_SCHEMA_VERSION


RITUAL_COMMAND_FILES = [
    "cli/commands/vvv.py",
    "cli/commands/nnn.py",
    "cli/commands/gogogo.py",
    "cli/commands/ddd.py",
    "cli/commands/rrr.py",
    "cli/commands/close.py",
    # sss is delegated via session.new — its capture block lives there.
    "cli/commands/session.py",
]


def _project_root() -> Path:
    # this test file lives at .ai/cli/tests/, project root is 3 up.
    return Path(__file__).resolve().parents[3]


# ─── S6: capture() inside a ritual stamps capture_id on AuditChain events ─────


def test_capture_block_stamps_capture_id_on_audit_chain(tmp_path):
    """Open a capture block, append an event via AuditChain (the same path
    every ritual uses), then assert the written event carries capture_id."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    chain = AuditChain(tmp_path / "events.ndjson")

    with capture(session_dir, ritual="test_ritual", role="KERNEL") as cap:
        cap.input("params.json", {"k": "v"})
        event = chain.append("test_ritual.invoked", {"session_id": "s1"})
        cap.output("result.json", {"ok": True})

    assert event["schema_version"] == AUDIT_EVENT_SCHEMA_VERSION
    assert event.get("capture_id") == cap.capture_id

    db = session_dir / "CAPTURE" / "capture.sqlite"
    assert db.exists()
    conn = sqlite3.connect(str(db))
    rows = conn.execute("SELECT capture_id, ritual, status FROM captures").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == cap.capture_id
    assert rows[0][1] == "test_ritual"
    assert rows[0][2] == "COMPLETED"

    items = conn.execute("SELECT kind, name FROM capture_items").fetchall()
    kinds = {k for k, _ in items}
    assert "input" in kinds
    assert "output" in kinds


def test_capture_failed_partial_when_exception(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    with pytest.raises(RuntimeError):
        with capture(session_dir, ritual="failing_ritual", role="KERNEL") as cap:
            cap.input("params.json", {"k": "v"})
            raise RuntimeError("simulated ritual failure")

    db = session_dir / "CAPTURE" / "capture.sqlite"
    conn = sqlite3.connect(str(db))
    rows = conn.execute("SELECT ritual, status FROM captures").fetchall()
    assert rows == [("failing_ritual", "FAILED_PARTIAL")]


# ─── S7: referential integrity NDJSON.capture_id ↔ captures.capture_id ────────


def test_referential_integrity_after_capture_block(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    chain = AuditChain(tmp_path / "events.ndjson")

    captured_ids = []
    with capture(session_dir, ritual="r1", role="KERNEL") as cap1:
        chain.append("r1.evt_a", {"session_id": "s"})
        chain.append("r1.evt_b", {"session_id": "s"})
        captured_ids.append(cap1.capture_id)
    with capture(session_dir, ritual="r2", role="KERNEL") as cap2:
        chain.append("r2.evt_a", {"session_id": "s"})
        captured_ids.append(cap2.capture_id)
    # An event outside any capture has no capture_id.
    chain.append("orphan.evt", {"session_id": "s"})

    db = session_dir / "CAPTURE" / "capture.sqlite"
    conn = sqlite3.connect(str(db))
    known_ids = {r[0] for r in conn.execute("SELECT capture_id FROM captures")}
    assert known_ids == set(captured_ids)

    events_with_cid = []
    events_without_cid = []
    for line in (tmp_path / "events.ndjson").read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("capture_id") is not None:
            events_with_cid.append(e)
        else:
            events_without_cid.append(e)

    assert all(e["capture_id"] in known_ids for e in events_with_cid)
    assert any(e["type"] == "orphan.evt" for e in events_without_cid)


# ─── S8: static-grep singleton — one `with capture(` per ritual command ───────


@pytest.mark.parametrize("ritual_rel", RITUAL_COMMAND_FILES)
def test_exactly_one_capture_block_per_ritual_file(ritual_rel):
    """Exactly ONE ``with capture(`` block per ritual command file.
    Defends against double-wraps that would produce nested capture
    rows per invocation (plan Risk #6)."""
    p = _project_root() / ".ai" / ritual_rel
    src = p.read_text(encoding="utf-8")
    # Count any form: `with capture(`, `with _rp_capture(`,
    # `with recordproxy.capture(` — alias-tolerant.
    import re

    matches = re.findall(r"\bwith\s+([\w\.]*capture)\s*\(", src)
    assert len(matches) == 1, (
        f"{ritual_rel}: expected exactly 1 capture block, found {len(matches)}: {matches}"
    )


# ─── S9: AuditChain.append signature stability + contextvar lifecycle ─────────


def test_audit_chain_append_signature_stable():
    """Article XXIX no-silent-rewrites: AuditChain.append must keep its
    pre-existing public parameter names with the same kind/order."""
    sig = inspect.signature(AuditChain.append)
    expected = ["self", "event_type", "details", "ts"]
    actual = list(sig.parameters.keys())
    assert actual == expected, f"signature drift: expected {expected}, got {actual}"


def test_emit_via_proxy_signature_additive_only():
    """emit_via_proxy gained optional capture_id kwarg in Part 2.
    All pre-existing parameters MUST remain present."""
    sig = inspect.signature(emit_via_proxy)
    params = list(sig.parameters.keys())
    for name in ("event_type", "details", "prev_hash", "ts"):
        assert name in params, f"emit_via_proxy missing {name}"
    assert "capture_id" in params
    assert sig.parameters["capture_id"].default is None


def test_capture_contextvar_no_cross_invocation_leak(tmp_path):
    """Back-to-back captures in the same process: the second's capture_id
    must differ from the first's, and no orphan capture_id leaks after
    the second exits."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    assert get_active_capture_id() is None

    with capture(session_dir, ritual="first", role="KERNEL") as cap_a:
        first_id = get_active_capture_id()
        assert first_id == cap_a.capture_id
    assert get_active_capture_id() is None, "leak after first capture exit"

    with capture(session_dir, ritual="second", role="KERNEL") as cap_b:
        second_id = get_active_capture_id()
        assert second_id == cap_b.capture_id
        assert second_id != first_id
    assert get_active_capture_id() is None, "leak after second capture exit"


def test_capture_contextvar_resets_on_exception(tmp_path):
    """An exception inside the with-block must still reset the
    contextvar (no leak even on failure)."""
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    assert get_active_capture_id() is None
    with pytest.raises(RuntimeError):
        with capture(session_dir, ritual="failing", role="KERNEL") as cap:
            assert get_active_capture_id() == cap.capture_id
            raise RuntimeError("simulated")
    assert get_active_capture_id() is None


def test_explicit_kwarg_wins_over_contextvar():
    """If both an explicit capture_id kwarg AND a contextvar value are
    present, the kwarg wins (least-surprise for downstream callers)."""
    token = set_active_capture_id("CTX_ID")
    try:
        out = emit_via_proxy(
            "x", {}, prev_hash="0", ts="2026-05-13T00:00:00Z",
            capture_id="EXPLICIT_ID",
        )
        assert out["capture_id"] == "EXPLICIT_ID"

        out2 = emit_via_proxy(
            "x", {}, prev_hash="0", ts="2026-05-13T00:00:00Z",
        )
        assert out2["capture_id"] == "CTX_ID"
    finally:
        reset_active_capture_id(token)
    out3 = emit_via_proxy("x", {}, prev_hash="0", ts="2026-05-13T00:00:00Z")
    assert "capture_id" not in out3
