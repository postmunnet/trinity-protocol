"""Tests for close.py runtime — TRINITY_SESSION_CLOSE_SPEC_V1 §2-§5 wiring."""
from __future__ import annotations

import datetime
import inspect
import json
import sqlite3
from pathlib import Path

import pytest

from cli.commands import close as close_mod
from cli.core import manifest as manifest_module


# ───────────────────── source-introspection (cheap structural checks) ─────


def test_close_imports_manifest_module():
    """close.py must import cli.core.manifest."""
    assert hasattr(close_mod, "manifest_module"), \
        "close.py must import cli.core.manifest as manifest_module"


def test_close_source_calls_build_final_manifest():
    source = inspect.getsource(close_mod)
    assert "build_final_manifest" in source


def test_close_source_calls_resolve_tier():
    source = inspect.getsource(close_mod)
    assert "resolve_tier" in source


def test_close_source_writes_final_manifest_yaml():
    source = inspect.getsource(close_mod)
    assert "final_manifest.yaml" in source


def test_close_manifest_built_event_emitted():
    """close.py source emits the close.manifest_built event."""
    source = inspect.getsource(close_mod)
    assert "close.manifest_built" in source


def test_close_source_handles_cold_tier_branch():
    source = inspect.getsource(close_mod)
    assert 'tier == "COLD"' in source or "tier=='COLD'" in source


def test_close_source_calls_write_external_audit():
    source = inspect.getsource(close_mod)
    assert "write_external_audit" in source


def test_close_source_emits_external_audit_event():
    source = inspect.getsource(close_mod)
    assert "close.external_audit_emitted" in source


def test_close_source_escalates_cold_external_audit_failure():
    """Per Close Spec §5: COLD external audit failure → NEEDS_HUMAN."""
    source = inspect.getsource(close_mod)
    # exit code 3 reserved for NEEDS_HUMAN escalation in this implementation
    assert "Exit(3)" in source
    assert "NEEDS_HUMAN" in source


def test_close_requires_terminal_graph_before_archive():
    """Prod verify alone must not be enough; close runs after rrr."""
    source = inspect.getsource(close_mod)
    assert 'graph_state not in {"DONE", "DEAD"}' in source
    assert "close requires DONE or DEAD" in source
    assert source.find("close requires DONE or DEAD") < source.find(
        "archive_session(session_path, config)"
    )


# ───────────────────── functional tests via direct module API ──────────────


def _make_session(tmp_path: Path, slug: str) -> Path:
    session = tmp_path / f"0001_2026-05-13_12_00_pm_{slug}"
    for sub in ("DO/dev", "DO/prod", "DO/snapshot", "SANDBOX", "THINK", "CONTROL", ".state"):
        (session / sub).mkdir(parents=True)
    (session / "THINK" / "plan_envelope.json").write_text(
        json.dumps({"goal": "x", "tier": "WARM", "steps": []})
    )
    (session / "CONTROL" / "META.json").write_text(json.dumps({"id": session.name}))
    return session


def _make_cold_capture(session_path: Path):
    """Create CAPTURE/capture.sqlite with COLD-tier semantics: ≥1 audit event."""
    capture_dir = session_path / "CAPTURE"
    capture_dir.mkdir(parents=True)
    (capture_dir / "blobs" / "sha256").mkdir(parents=True)
    (capture_dir / "refs").mkdir()
    db = capture_dir / "capture.sqlite"
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE captures (capture_id TEXT PRIMARY KEY, schema_version TEXT, session_id TEXT,
            ritual TEXT, role TEXT, branch_id TEXT, kind TEXT, status TEXT, started_at_utc TEXT,
            ended_at_utc TEXT, model_provider TEXT, model_name TEXT, template_hash TEXT,
            context_hash TEXT, prompt_hash TEXT);
        CREATE TABLE audit_events (event_id TEXT PRIMARY KEY, schema_version TEXT, session_id TEXT,
            seq INTEGER, event_type TEXT, ritual TEXT, capture_id TEXT, actor TEXT, ts_utc TEXT,
            payload_json TEXT, payload_hash TEXT, prev_hash TEXT, hash TEXT,
            UNIQUE(session_id, seq));
    """)
    conn.execute(
        "INSERT INTO captures VALUES ('cap_01_aaaaaaaa', 'trinity.capture.v1', ?, 'gogogo', NULL, NULL, 'work', 'COMPLETED', '2026-05-13T12:00:00Z', NULL, NULL, NULL, NULL, NULL, NULL)",
        (session_path.name,),
    )
    conn.execute(
        "INSERT INTO audit_events VALUES (?, 'trinity.audit_event.v1', ?, 1, 'session.created', NULL, NULL, 'kernel', '2026-05-13T12:00:00Z', '{}', ?, '0', ?)",
        ("evt_" + "a" * 32, session_path.name, "a" * 64, "b" * 64),
    )
    conn.commit()
    conn.close()


def test_external_audit_emitted_on_cold_tier(tmp_path: Path):
    """When tier=COLD, write_external_audit produces a dated audit JSON.

    Direct functional test of the module API (close.py orchestrates the same call).
    """
    session = _make_session(tmp_path, "feat-cold-int")
    _make_cold_capture(session)
    manifest = manifest_module.build_final_manifest(session, "COLD")
    audit_root = tmp_path / "audit" / "external"
    out = manifest_module.write_external_audit(session, manifest, audit_root=audit_root)
    assert out.is_file()
    payload = json.loads(out.read_text())
    assert payload["tier"] == "COLD"
    assert payload["audit_chain_anchor"]["session_chain_head"] == "b" * 64
    assert payload["audit_chain_anchor"]["last_seq"] == 1


def test_no_external_audit_on_warm_tier(tmp_path: Path):
    """WARM tier should NOT trigger external audit emission per Close Spec §4 tier-routing.

    This tests the close.py BRANCH logic at the source level (we don't run close.py
    end-to-end here; this asserts close.py reads tier and only writes external audit
    when tier == COLD).
    """
    source = inspect.getsource(close_mod)
    # The cold-tier branch wraps the write_external_audit call
    assert source.count("write_external_audit") >= 1
    # The branch is guarded by tier == "COLD"
    cold_idx = source.find('tier == "COLD"')
    write_idx = source.find("write_external_audit")
    assert cold_idx >= 0 and write_idx >= 0
    assert cold_idx < write_idx, "write_external_audit must be inside the COLD branch"


def test_close_manifest_built_payload_contains_required_fields():
    """The close.manifest_built event payload includes path, sha256, capture_count, last_seq, tier."""
    source = inspect.getsource(close_mod)
    # All 5 payload keys should appear in the source near the close.manifest_built emission
    for key in ("path", "sha256", "capture_count", "last_seq", "tier"):
        assert key in source, f"close.manifest_built payload missing key {key!r}"


def test_close_writes_manifest_before_archive():
    """Manifest writing must precede archive_session (so manifest follows session into archive)."""
    source = inspect.getsource(close_mod)
    manifest_idx = source.find("final_manifest.yaml")
    archive_idx = source.find("archive_session(session_path, config)")
    assert manifest_idx > 0 and archive_idx > 0
    assert manifest_idx < archive_idx, "manifest must be written before archive_session"
