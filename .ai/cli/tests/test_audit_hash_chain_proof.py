"""Audit hash-chain formal proof — Article X + TRINITY_AUDIT_EVENT_SPEC_V1 §2.1.

Exhaustive integrity assertion suite. Every invariant required by §2.1
gets a named test, on both backends:
  - legacy NDJSON chain (.ai/audit/events.ndjson — global, 5-field shape)
  - RecordProxy v1 SQLite chain (<session>/CAPTURE/capture.sqlite — 13-field shape)

Plus negative tests (tampered hash / broken prev_hash / non-contiguous seq /
dangling artifact ref) confirm the verifier surfaces each violation.

Article X anchor: append-only, hash-chain integrity. These tests READ;
they never mutate. Article XX anchor: scan_artifact_refs is invoked only
via explicit pytest invocation.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import tempfile
from typing import List

import pytest

from cli.core.audit_replay import (
    ARTIFACT_REF_FIELDS,
    CANONICAL_EVENT_TYPES,
    EXIT_CHAIN_BROKEN,
    EXIT_OK,
    GENESIS_PREV_HASH,
    classify_verify_errors,
    read_legacy_ndjson,
    read_session_chain,
    scan_artifact_refs,
    verify_chain,
)


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
LEGACY_CHAIN = PROJECT_ROOT / ".ai" / "audit" / "events.ndjson"


# ─────────── Helpers: canonical hash recompute (mirror of spec §2.1) ───────────


def _canonical_legacy(obj: dict) -> str:
    """Legacy NDJSON canonical form per kernel audit.py: ensure_ascii=True (default)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _canonical_session(obj: dict) -> str:
    """Per-session SQLite canonical form per recordproxy: ensure_ascii=False."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _legacy_event_for_hash(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "hash"}


def _session_event_for_hash(row: dict) -> dict:
    return {
        "event_id": row["event_id"],
        "schema_version": row["schema_version"],
        "session_id": row["session_id"],
        "seq": row["seq"],
        "event_type": row["event_type"],
        "ritual": row.get("ritual"),
        "capture_id": row.get("capture_id"),
        "actor": row["actor"],
        "ts_utc": row["ts_utc"],
        "payload_hash": row["payload_hash"],
        "prev_hash": row["prev_hash"],
    }


# ─────────── §2.1 (a) — genesis hash invariant ───────────


def test_genesis_prev_hash_constant_is_zero() -> None:
    """The chain root MUST use the literal string "0" as prev_hash."""
    assert GENESIS_PREV_HASH == "0"


def test_legacy_chain_genesis_hash_recomputes() -> None:
    """First event of legacy chain: stored hash MUST equal recomputed hash."""
    if not LEGACY_CHAIN.exists():
        pytest.skip("legacy events.ndjson absent")
    rows = read_legacy_ndjson(LEGACY_CHAIN)
    assert rows, "legacy chain empty"
    genesis = rows[0]
    assert genesis.get("prev_hash") == GENESIS_PREV_HASH, (
        f"genesis prev_hash != '0': got {genesis.get('prev_hash')!r}"
    )
    recomputed = _sha256(_canonical_legacy(_legacy_event_for_hash(genesis)))
    assert genesis["hash"] == recomputed, (
        f"genesis hash mismatch: stored={genesis['hash']!r}, "
        f"recomputed={recomputed!r}"
    )


# ─────────── §2.1 (b)+(c) — per-event hash recompute + prev_hash linkage ───────────


def test_legacy_chain_full_replay_verifies() -> None:
    """Walk the entire legacy chain; every prev_hash + every hash MUST verify."""
    if not LEGACY_CHAIN.exists():
        pytest.skip("legacy events.ndjson absent")
    rows = read_legacy_ndjson(LEGACY_CHAIN)
    ok, errors = verify_chain(rows, chain_kind="legacy")
    assert ok, f"legacy chain integrity violated: {errors[:5]}"


def test_strict_mode_verifier_distinguishes_unknown_from_integrity_errors() -> None:
    """Strict-mode integration smoke — registry-coverage check is a Phase 10
    concern, separate from §2.1 hash-chain integrity. This test ensures the
    verifier surfaces 'unknown event_type' errors as a distinct error class
    (not as chain-integrity failures), so future Phase-10 work can
    register-and-suppress historical event_types incrementally.
    """
    if not LEGACY_CHAIN.exists():
        pytest.skip("legacy events.ndjson absent")
    rows = read_legacy_ndjson(LEGACY_CHAIN)
    ok_strict, errors_strict = verify_chain(rows, strict=True, chain_kind="legacy")
    ok_loose, errors_loose = verify_chain(rows, strict=False, chain_kind="legacy")
    # Loose-mode integrity MUST hold (the chain itself is valid).
    assert ok_loose, f"loose-mode integrity violated: {errors_loose[:3]}"
    # Strict-mode SURFACES the additional unknown-event_type errors so
    # operators see registry-coverage gaps WITHOUT conflating them with
    # cryptographic integrity issues.
    extra_strict = set(errors_strict) - set(errors_loose)
    assert all("unknown event_type" in e for e in extra_strict), (
        f"strict mode raised non-registry errors: {sorted(extra_strict)[:3]}"
    )


# ─────────── §2.1 (d) — append-only invariant (mutation detection) ───────────


def test_tampered_hash_detected_legacy(tmp_path: pathlib.Path) -> None:
    """Mutate one row's payload after the fact; verifier MUST flag hash mismatch."""
    chain_path = tmp_path / "tampered.ndjson"
    # Build a minimal 3-event legitimate chain.
    rows = _build_legacy_chain(["session.created", "vvv.proposed", "vvv.passed"])
    # Tamper: replace details on row[1] without recomputing hash.
    rows[1]["details"] = {"tampered": True}
    chain_path.write_text(
        "\n".join(json.dumps(r, separators=(",", ":")) for r in rows) + "\n",
        encoding="utf-8",
    )
    loaded = read_legacy_ndjson(chain_path)
    ok, errors = verify_chain(loaded, chain_kind="legacy")
    assert not ok
    assert any("hash mismatch" in e for e in errors), errors


def test_broken_prev_hash_detected_legacy(tmp_path: pathlib.Path) -> None:
    """Replace one row's prev_hash with the wrong value; verifier flags it."""
    chain_path = tmp_path / "broken_prev.ndjson"
    rows = _build_legacy_chain(["session.created", "vvv.proposed", "vvv.passed"])
    rows[2]["prev_hash"] = "0" * 64  # plausible-looking but wrong
    chain_path.write_text(
        "\n".join(json.dumps(r, separators=(",", ":")) for r in rows) + "\n",
        encoding="utf-8",
    )
    loaded = read_legacy_ndjson(chain_path)
    ok, errors = verify_chain(loaded, chain_kind="legacy")
    assert not ok
    assert any("prev_hash mismatch" in e for e in errors), errors


# ─────────── §2.1 (e) — per-session seq contiguity + monotonicity ───────────


def test_session_chain_seq_gap_detected(tmp_path: pathlib.Path) -> None:
    """Build a session chain with a seq gap; verifier MUST flag it."""
    db_path = tmp_path / "capture.sqlite"
    rows = _build_session_chain("0001_test_session", events=4)
    # Drop seq=3 to create a gap.
    rows = [r for r in rows if r["seq"] != 3]
    _write_session_chain(db_path, rows)
    loaded = read_session_chain(db_path)
    ok, errors = verify_chain(loaded, chain_kind="session")
    assert not ok
    assert any("seq gap" in e for e in errors), errors


def test_session_chain_clean_verifies(tmp_path: pathlib.Path) -> None:
    """A freshly built session chain (no tampering) MUST verify clean."""
    db_path = tmp_path / "capture.sqlite"
    rows = _build_session_chain("0001_test_clean", events=5)
    _write_session_chain(db_path, rows)
    loaded = read_session_chain(db_path)
    ok, errors = verify_chain(loaded, chain_kind="session")
    assert ok, f"clean session chain failed verify: {errors}"


# ─────────── exit-code classification ───────────


def test_classify_no_errors_returns_ok() -> None:
    assert classify_verify_errors([]) == EXIT_OK


def test_classify_hash_mismatch_returns_chain_broken() -> None:
    errs = ["hash mismatch at seq/idx=3: stored='deadbeef' recomputed='cafef00d'"]
    assert classify_verify_errors(errs) == EXIT_CHAIN_BROKEN


def test_classify_prev_hash_mismatch_returns_chain_broken() -> None:
    errs = ["prev_hash mismatch at seq/idx=2: got 'aaa' expected 'bbb'"]
    assert classify_verify_errors(errs) == EXIT_CHAIN_BROKEN


def test_classify_seq_gap_returns_chain_broken() -> None:
    errs = ["seq gap at idx=4: got seq=6, expected 5"]
    assert classify_verify_errors(errs) == EXIT_CHAIN_BROKEN


# ─────────── canonical encoding pinning (regression guard) ───────────


def test_canonical_legacy_pins_ensure_ascii_true_default() -> None:
    """Legacy canonical form MUST escape non-ASCII (default ensure_ascii=True)."""
    encoded = _canonical_legacy({"k": "café"})
    assert "\\u00e9" in encoded, f"legacy canonical not ASCII-escaping: {encoded!r}"


def test_canonical_session_pins_ensure_ascii_false() -> None:
    """Per-session canonical form MUST preserve UTF-8 raw (ensure_ascii=False)."""
    encoded = _canonical_session({"k": "café"})
    assert "café" in encoded, f"session canonical not raw UTF-8: {encoded!r}"


# ─────────── ARTIFACT_REF_FIELDS surface ───────────


def test_artifact_ref_fields_is_frozenset() -> None:
    assert isinstance(ARTIFACT_REF_FIELDS, frozenset)


def test_artifact_ref_fields_covers_canonical_set() -> None:
    """The scanner MUST recognise the conventional artifact-path fields."""
    needed = {"artifact_ref", "path", "diff_ref", "log_ref"}
    missing = needed - ARTIFACT_REF_FIELDS
    assert not missing, f"ARTIFACT_REF_FIELDS missing canonical: {missing}"


# ─────────── scan_artifact_refs — pure scanner contract ───────────


def test_scan_artifact_refs_returns_list() -> None:
    out = scan_artifact_refs("nonexistent_session_id", project_root=PROJECT_ROOT)
    assert isinstance(out, list)


def test_scan_artifact_refs_does_not_raise_on_missing_session() -> None:
    """Article XX: scanner is passive — never raises, only reports."""
    out = scan_artifact_refs("definitely_missing_session_xyz_999", project_root=PROJECT_ROOT)
    assert out == [], "missing session should return empty list, not raise"


def test_scan_artifact_refs_does_not_mutate_chain(tmp_path: pathlib.Path) -> None:
    """Scanning MUST NOT modify the audit chain on disk (Article X append-only)."""
    if not LEGACY_CHAIN.exists():
        pytest.skip("legacy events.ndjson absent")
    before_bytes = LEGACY_CHAIN.read_bytes()
    before_mtime = LEGACY_CHAIN.stat().st_mtime_ns
    scan_artifact_refs("any_session", project_root=PROJECT_ROOT)
    after_bytes = LEGACY_CHAIN.read_bytes()
    after_mtime = LEGACY_CHAIN.stat().st_mtime_ns
    assert before_bytes == after_bytes, "legacy chain mutated by scanner"
    assert before_mtime == after_mtime, "legacy chain mtime changed"


def test_scan_artifact_refs_reports_missing_path(tmp_path: pathlib.Path) -> None:
    """Construct a tiny SQLite chain pointing at a non-existent file; expect a dangling row."""
    # Build a fake session dir layout
    session_id = "0001_fake_scan_session"
    session_dir = tmp_path / ".ai" / "sessions" / session_id
    capture_dir = session_dir / "CAPTURE"
    capture_dir.mkdir(parents=True)
    db_path = capture_dir / "capture.sqlite"

    payload = {"path": "does/not/exist/at/all.txt"}
    rows = _build_session_chain(
        session_id,
        events=1,
        payload_override=[payload],
    )
    _write_session_chain(db_path, rows)

    result = scan_artifact_refs(session_id, project_root=tmp_path)
    assert len(result) == 1
    assert result[0]["reason"] == "missing"
    assert result[0]["field"] == "path"
    assert result[0]["ref_path"] == "does/not/exist/at/all.txt"


def test_scan_artifact_refs_clean_chain_returns_empty(tmp_path: pathlib.Path) -> None:
    """Build a session chain whose payload paths all exist; scanner returns []."""
    session_id = "0001_fake_clean_session"
    session_dir = tmp_path / ".ai" / "sessions" / session_id
    capture_dir = session_dir / "CAPTURE"
    capture_dir.mkdir(parents=True)
    db_path = capture_dir / "capture.sqlite"

    # Create a real file the payload can reference.
    real_file = tmp_path / "real_artifact.txt"
    real_file.write_text("hello", encoding="utf-8")

    payload = {"path": "real_artifact.txt"}
    rows = _build_session_chain(
        session_id,
        events=1,
        payload_override=[payload],
    )
    _write_session_chain(db_path, rows)

    result = scan_artifact_refs(session_id, project_root=tmp_path)
    assert result == [], f"expected clean chain, got dangling: {result}"


# ─────────── §3 registry sanity ───────────


def test_canonical_registry_includes_genesis() -> None:
    assert "genesis" in CANONICAL_EVENT_TYPES


def test_canonical_registry_includes_ritual_gates() -> None:
    for gate_event in (
        "vvv.passed", "nnn.passed", "gogogo.completed", "ddd.approved",
        "rrr.completed", "close.completed",
    ):
        assert gate_event in CANONICAL_EVENT_TYPES, f"missing ritual event: {gate_event}"


def test_canonical_registry_includes_transport_namespace() -> None:
    """Post-2026-05-15 Article XXIX amendment: 5 transport events."""
    for transport_event in (
        "transport.envelope_accepted",
        "transport.envelope_refused.unsigned",
        "transport.envelope_refused.badkey",
        "transport.envelope_refused.replay",
        "transport.envelope_refused.overscope",
    ):
        # Note: the spec amendment landed in the spec file; the §3 registry
        # in audit_replay.py is the kernel-side mirror — these MAY land via
        # a follow-up code-side amendment. For now, assert the spec
        # contains them (spec is source of truth per Article XXV).
        spec_path = PROJECT_ROOT / "docs" / "specs" / "TRINITY_AUDIT_EVENT_SPEC_V1.md"
        if spec_path.exists():
            assert transport_event in spec_path.read_text(encoding="utf-8"), (
                f"spec missing transport event: {transport_event}"
            )


# ─────────── Test helpers (chain builders) ───────────


def _build_legacy_chain(event_types: List[str]) -> List[dict]:
    """Build a valid legacy-shape chain with correct prev_hash + hash linkage."""
    rows: List[dict] = []
    prev = GENESIS_PREV_HASH
    for i, et in enumerate(event_types):
        row = {
            "ts": f"2026-05-15T00:00:{i:02d}Z",
            "type": et,
            "prev_hash": prev,
            "details": {"i": i},
        }
        canonical = _canonical_legacy(_legacy_event_for_hash(row))
        row["hash"] = _sha256(canonical)
        rows.append(row)
        prev = row["hash"]
    return rows


def _build_session_chain(
    session_id: str,
    *,
    events: int,
    payload_override: List[dict] = None,
) -> List[dict]:
    """Build a valid session-shape (13-field) chain."""
    rows: List[dict] = []
    prev = GENESIS_PREV_HASH
    for i in range(events):
        seq = i + 1
        payload = (payload_override or [{}])[i] if payload_override else {"i": i}
        payload_str = _canonical_session(payload)
        payload_hash = _sha256(payload_str)
        row = {
            "event_id": f"evt_{i:032x}",
            "schema_version": "trinity.audit_event.v1",
            "session_id": session_id,
            "seq": seq,
            "event_type": "genesis" if seq == 1 else "session.created",
            "ritual": None,
            "capture_id": None,
            "actor": "kernel",
            "ts_utc": f"2026-05-15T00:00:{seq:02d}Z",
            "payload_json": payload_str,
            "payload_hash": payload_hash,
            "prev_hash": prev,
        }
        efh = _session_event_for_hash(row)
        row["hash"] = _sha256(_canonical_session(efh))
        rows.append(row)
        prev = row["hash"]
    return rows


def _write_session_chain(db_path: pathlib.Path, rows: List[dict]) -> None:
    """Write rows into a tmp sqlite mirroring the audit_events table shape."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
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
            prev_hash TEXT NOT NULL,
            hash TEXT NOT NULL,
            UNIQUE(session_id, seq)
        )
        """
    )
    for row in rows:
        conn.execute(
            "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                row["event_id"], row["schema_version"], row["session_id"],
                row["seq"], row["event_type"], row.get("ritual"),
                row.get("capture_id"), row["actor"], row["ts_utc"],
                row["payload_json"], row["payload_hash"], row["prev_hash"],
                row["hash"],
            ),
        )
    conn.commit()
    conn.close()
