"""Tests for cli.core.manifest — final-manifest builder for ai close."""
from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path

import pytest

from cli.core.manifest import (
    build_final_manifest,
    resolve_tier,
    write_external_audit,
)


def _make_session(tmp_path: Path, slug: str = "feat-test") -> Path:
    """Build a minimal session directory structure."""
    session = tmp_path / f"0001_2026-05-13_12_00_pm_{slug}"
    for sub in ("DO/dev", "DO/prod", "DO/snapshot", "SANDBOX", "THINK", "CONTROL", ".state"):
        (session / sub).mkdir(parents=True)
    (session / "THINK" / "plan_envelope.json").write_text(
        json.dumps({"goal": "x", "tier": "WARM", "steps": []})
    )
    (session / "THINK" / "01_PROMPT.md").write_text("# Prompt\n\nbody")
    (session / "DO" / "dev" / "out.txt").write_text("hello")
    (session / "CONTROL" / "META.json").write_text(json.dumps({"id": session.name}))
    return session


def _make_capture_sqlite(session_path: Path, *, capture_count: int = 1, with_audit: bool = False):
    """Create a synthetic CAPTURE/capture.sqlite with minimum tables."""
    capture_dir = session_path / "CAPTURE"
    capture_dir.mkdir(parents=True, exist_ok=True)
    (capture_dir / "blobs" / "sha256").mkdir(parents=True, exist_ok=True)
    (capture_dir / "refs").mkdir(parents=True, exist_ok=True)
    db_path = capture_dir / "capture.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
    CREATE TABLE captures (
      capture_id TEXT PRIMARY KEY,
      schema_version TEXT NOT NULL,
      session_id TEXT NOT NULL,
      ritual TEXT NOT NULL,
      role TEXT,
      branch_id TEXT,
      kind TEXT NOT NULL,
      status TEXT NOT NULL,
      started_at_utc TEXT NOT NULL,
      ended_at_utc TEXT,
      model_provider TEXT,
      model_name TEXT,
      template_hash TEXT,
      context_hash TEXT,
      prompt_hash TEXT
    );
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
    for i in range(capture_count):
        cap_id = f"cap_{i:02d}_{'a'*8}"
        conn.execute(
            "INSERT INTO captures(capture_id, schema_version, session_id, ritual, kind, status, started_at_utc) "
            "VALUES (?, 'trinity.capture.v1', ?, 'gogogo', 'work', 'COMPLETED', '2026-05-13T12:00:00Z')",
            (cap_id, session_path.name),
        )
    if with_audit:
        for seq in (1, 2, 3):
            conn.execute(
                "INSERT INTO audit_events(event_id, schema_version, session_id, seq, event_type, actor, ts_utc, payload_json, payload_hash, prev_hash, hash) "
                "VALUES (?, 'trinity.audit_event.v1', ?, ?, 'session.created', 'kernel', '2026-05-13T12:00:00Z', '{}', ?, ?, ?)",
                (f"evt_{seq:032x}", session_path.name, seq, "a"*64, "0" if seq == 1 else "b"*64, f"{seq:064d}"),
            )
    conn.commit()
    conn.close()
    # Add a blob and a ref to verify counts
    (capture_dir / "blobs" / "sha256" / "ab").mkdir(exist_ok=True)
    (capture_dir / "blobs" / "sha256" / "ab" / "abcd").write_bytes(b"x")
    (capture_dir / "refs" / "cap_00_aaaaaaaa.json").write_text("{}")


# ─────────────── resolve_tier ───────────────


def test_resolve_tier_default_warm(tmp_path: Path):
    session = _make_session(tmp_path)
    (session / "THINK" / "plan_envelope.json").unlink()  # remove tier source
    assert resolve_tier(session) == "WARM"


def test_resolve_tier_from_plan_envelope(tmp_path: Path):
    session = _make_session(tmp_path)
    (session / "THINK" / "plan_envelope.json").write_text(json.dumps({"tier": "COLD"}))
    assert resolve_tier(session) == "COLD"


def test_resolve_tier_from_verifier_strictest_wins(tmp_path: Path):
    session = _make_session(tmp_path)
    (session / ".state" / "verify_dev.json").write_text(json.dumps({"tier": "WARM"}))
    (session / ".state" / "verify_prod.json").write_text(json.dumps({"tier": "COLD"}))
    assert resolve_tier(session) == "COLD"


def test_resolve_tier_sandbox_profile_wins(tmp_path: Path):
    """Sandbox profile beats verifier reports beats plan envelope."""
    session = _make_session(tmp_path)
    (session / "THINK" / "plan_envelope.json").write_text(json.dumps({"tier": "COLD"}))
    (session / ".state" / "verify_dev.json").write_text(json.dumps({"tier": "WARM"}))
    (session / ".state" / "sandbox_profile.json").write_text(json.dumps({"tier": "HOT"}))
    assert resolve_tier(session) == "HOT"


def test_tier_resolution_priority(tmp_path: Path):
    """End-to-end priority chain: sandbox > verifier > plan > default."""
    s1 = _make_session(tmp_path, slug="p1-default")
    (s1 / "THINK" / "plan_envelope.json").unlink()
    assert resolve_tier(s1) == "WARM"

    s2 = _make_session(tmp_path, slug="p2-plan")
    (s2 / "THINK" / "plan_envelope.json").write_text(json.dumps({"tier": "HOT"}))
    assert resolve_tier(s2) == "HOT"

    s3 = _make_session(tmp_path, slug="p3-verifier")
    (s3 / "THINK" / "plan_envelope.json").write_text(json.dumps({"tier": "HOT"}))
    (s3 / ".state" / "verify_prod.json").write_text(json.dumps({"tier": "COLD"}))
    assert resolve_tier(s3) == "COLD"

    s4 = _make_session(tmp_path, slug="p4-sandbox")
    (s4 / "THINK" / "plan_envelope.json").write_text(json.dumps({"tier": "HOT"}))
    (s4 / ".state" / "verify_prod.json").write_text(json.dumps({"tier": "COLD"}))
    (s4 / ".state" / "sandbox_profile.json").write_text(json.dumps({"tier": "WARM"}))
    assert resolve_tier(s4) == "WARM"


# ─────────────── build_final_manifest ───────────────


def test_manifest_required_top_level_keys(tmp_path: Path):
    session = _make_session(tmp_path)
    m = build_final_manifest(session, "WARM")
    required = {"session_id", "closed_at", "tier", "graph_state_final",
                "artifacts", "audit", "manifest_sha256"}
    missing = required - set(m.keys())
    assert not missing, f"missing keys: {missing}"


def test_manifest_invalid_tier(tmp_path: Path):
    session = _make_session(tmp_path)
    with pytest.raises(ValueError, match="tier must be in"):
        build_final_manifest(session, "EXTRA")


def test_manifest_sha256_deterministic(tmp_path: Path):
    session = _make_session(tmp_path)
    # Pin closed_at so the only variance source is the hash itself
    m1 = build_final_manifest(session, "WARM", closed_at="2026-05-13T12:00:00Z")
    m2 = build_final_manifest(session, "WARM", closed_at="2026-05-13T12:00:00Z")
    assert m1["manifest_sha256"] == m2["manifest_sha256"]


def test_manifest_artifacts_sorted_by_path(tmp_path: Path):
    session = _make_session(tmp_path)
    (session / "THINK" / "zzz.md").write_text("z")
    (session / "THINK" / "aaa.md").write_text("a")
    m = build_final_manifest(session, "WARM")
    paths = [a["path"] for a in m["artifacts"]]
    assert paths == sorted(paths)


def test_manifest_excludes_final_manifest_yaml_itself(tmp_path: Path):
    session = _make_session(tmp_path)
    # Simulate a prior manifest already on disk
    (session / "CONTROL" / "final_manifest.yaml").write_text("# stale")
    m = build_final_manifest(session, "WARM")
    paths = [a["path"] for a in m["artifacts"]]
    assert "CONTROL/final_manifest.yaml" not in paths


def test_manifest_with_capture_block(tmp_path: Path):
    session = _make_session(tmp_path)
    _make_capture_sqlite(session, capture_count=2, with_audit=True)
    m = build_final_manifest(session, "WARM")
    assert "captures" in m
    caps = m["captures"]
    assert caps["capture_store"]["path"] == "CAPTURE/capture.sqlite"
    assert caps["capture_store"]["sha256"] == "" or len(caps["capture_store"]["sha256"]) == 64
    assert len(caps["capture_ids"]) == 2
    assert caps["capture_ids"] == sorted(caps["capture_ids"])
    assert caps["blobs_root"]["blob_count"] == 1
    assert caps["refs_root"]["ref_count"] == 1
    assert "capture_manifest_sha256" in caps
    assert len(caps["capture_manifest_sha256"]) == 64
    # Audit block should reflect the session_chain_head/last_seq
    assert m["audit"]["session_chain_head"] is not None
    assert m["audit"]["last_seq"] == 3
    assert m["audit"]["capture_chain_consistent"] is True


def test_manifest_without_capture_block(tmp_path: Path):
    """Backward-compat: sessions without CAPTURE/ still produce valid manifest."""
    session = _make_session(tmp_path)
    m = build_final_manifest(session, "WARM")
    assert "captures" not in m
    assert m["audit"]["session_chain_head"] is None
    assert m["audit"]["last_seq"] is None
    assert m["audit"]["capture_chain_consistent"] is False


def test_manifest_with_capture_but_no_audit_events(tmp_path: Path):
    """CAPTURE/capture.sqlite exists but audit_events table is empty."""
    session = _make_session(tmp_path)
    _make_capture_sqlite(session, capture_count=1, with_audit=False)
    m = build_final_manifest(session, "WARM")
    assert "captures" in m
    assert m["audit"]["session_chain_head"] is None
    assert m["audit"]["last_seq"] is None


def test_manifest_graph_state_default_done(tmp_path: Path):
    session = _make_session(tmp_path)
    m = build_final_manifest(session, "WARM")
    assert m["graph_state_final"] == "DONE"


def test_manifest_graph_state_override(tmp_path: Path):
    session = _make_session(tmp_path)
    m = build_final_manifest(session, "COLD", graph_state_final="DEPLOYED")
    assert m["graph_state_final"] == "DEPLOYED"


# ─────────────── write_external_audit ───────────────


def test_external_audit_written_to_dated_dir(tmp_path: Path):
    session = _make_session(tmp_path, slug="feat-cold")
    _make_capture_sqlite(session, capture_count=1, with_audit=True)
    m = build_final_manifest(session, "COLD")
    audit_root = tmp_path / "audit_external"
    out = write_external_audit(session, m, audit_root=audit_root)
    assert out.is_file()
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    assert today in str(out)
    assert out.name == f"{session.name}.audit.json"


def test_external_audit_shape_includes_chain_anchor(tmp_path: Path):
    session = _make_session(tmp_path, slug="feat-cold2")
    _make_capture_sqlite(session, capture_count=1, with_audit=True)
    m = build_final_manifest(session, "COLD")
    audit_root = tmp_path / "audit_external"
    out = write_external_audit(session, m, audit_root=audit_root)
    payload = json.loads(out.read_text())
    assert payload["session_id"] == session.name
    assert payload["tier"] == "COLD"
    assert payload["final_state"] == "DONE"
    anchor = payload["audit_chain_anchor"]
    assert anchor["session_id"] == session.name
    assert anchor["session_chain_head"] is not None
    assert anchor["last_seq"] == 3
    # captures block propagated
    assert "captures" in payload
    assert payload["captures"]["capture_ids"] == m["captures"]["capture_ids"]


def test_external_audit_with_legacy_ndjson_reference(tmp_path: Path):
    session = _make_session(tmp_path, slug="feat-cold3")
    _make_capture_sqlite(session, capture_count=1, with_audit=True)
    m = build_final_manifest(session, "COLD")
    audit_root = tmp_path / "audit_external"
    legacy = tmp_path / "legacy_events.ndjson"
    legacy.write_text('{"type":"x","prev_hash":"0","hash":"h"}\n')
    out = write_external_audit(session, m, audit_root=audit_root, legacy_ndjson=legacy)
    payload = json.loads(out.read_text())
    anchor = payload["audit_chain_anchor"]
    assert "audit_export_ref" in anchor
    assert anchor["audit_export_ref"]["path"] == str(legacy)
    assert len(anchor["audit_export_ref"]["sha256"]) == 64


def test_external_audit_no_capture_omits_block(tmp_path: Path):
    session = _make_session(tmp_path, slug="feat-cold4")
    m = build_final_manifest(session, "COLD")  # no CAPTURE/
    audit_root = tmp_path / "audit_external"
    out = write_external_audit(session, m, audit_root=audit_root)
    payload = json.loads(out.read_text())
    assert "captures" not in payload
    assert payload["audit_chain_anchor"]["session_chain_head"] is None


def test_external_audit_missing_manifest_fields_raises(tmp_path: Path):
    session = _make_session(tmp_path)
    with pytest.raises(ValueError, match="missing required fields"):
        write_external_audit(session, {"session_id": "x"}, audit_root=tmp_path)
