"""Runtime pointer-pin pre-flight (warn-only in-flight engine-drift detection).

Covers the session acceptance contract:
  A1 sss stamps runtime_pinned_hash into CONTROL/META.json
  A2 gogogo pre-flight: live != pinned -> warn + audit event, exit 0 (no block)
  A3 live == pinned -> no warn / no event
  A4 unreadable / missing / source-mode -> fail-soft silent
  A5 (this suite green)

Helper read_engine_source_sha resolves the engine hash via the instance's
.ai/runtime.yaml runtime_code: pointer -> <engine>/.trinity-runtime.json source_sha.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from cli.commands import gogogo, lll, session
from cli.core.audit import get_chain_for_project
from cli.core.runtime_home import read_engine_source_sha


def _make_instance(tmp_path: Path, *, live_sha: str | None) -> tuple[Path, Path]:
    """Build a thin-instance layout: project with .ai/runtime.yaml -> engine.
    live_sha=None means the provenance file is absent. Returns (project, session)."""
    engine = tmp_path / "engine"
    engine.mkdir()
    if live_sha is not None:
        (engine / ".trinity-runtime.json").write_text(
            json.dumps({"source_sha": live_sha, "mode": "patch"})
        )
    proj = tmp_path / "proj"
    (proj / ".ai" / "audit").mkdir(parents=True)
    (proj / ".ai" / "runtime.yaml").write_text(f"runtime_code: {engine}\n")
    sess = proj / ".ai" / "sessions" / "0001_x"
    (sess / "CONTROL").mkdir(parents=True)
    return proj, sess


def _drift_events(project_root: Path) -> list:
    return [
        e
        for e in get_chain_for_project(project_root).iter_events()
        if e.get("type") == "runtime.drift_detected"
    ]


# ── read_engine_source_sha ──────────────────────────────────────────────
def test_helper_happy_path(tmp_path):
    _, sess = _make_instance(tmp_path, live_sha="fp-abc123")
    assert read_engine_source_sha(sess) == "fp-abc123"


def test_helper_source_mode_returns_none(tmp_path):
    # no .ai/runtime.yaml anywhere -> source-mode -> None
    bare = tmp_path / "bare"
    bare.mkdir()
    assert read_engine_source_sha(bare) is None


def test_helper_missing_provenance_failsoft(tmp_path):
    _, sess = _make_instance(tmp_path, live_sha=None)
    assert read_engine_source_sha(sess) is None


def test_helper_malformed_provenance_failsoft(tmp_path):
    proj, sess = _make_instance(tmp_path, live_sha="fp-x")
    engine_prov = (proj / ".ai" / "runtime.yaml").read_text().split(": ", 1)[1].strip()
    (Path(engine_prov) / ".trinity-runtime.json").write_text("{not json")
    assert read_engine_source_sha(sess) is None


# ── A1: sss stamp ───────────────────────────────────────────────────────
def test_sss_stamps_pinned_hash(tmp_path):
    proj, sess = _make_instance(tmp_path, live_sha="fp-pinned1")
    session._create_metadata(sess, "demo", "0001_x")
    meta = json.loads((sess / "CONTROL" / "META.json").read_text())
    assert meta["runtime_pinned_hash"] == "fp-pinned1"


def test_sss_stamp_source_mode_is_none(tmp_path):
    bare = tmp_path / "bare"
    (bare / "CONTROL").mkdir(parents=True)
    session._create_metadata(bare, "demo", "0002_y")
    meta = json.loads((bare / "CONTROL" / "META.json").read_text())
    assert meta["runtime_pinned_hash"] is None


# ── A2/A3/A4: gogogo pre-flight ─────────────────────────────────────────
def test_preflight_mismatch_warns_and_audits(tmp_path):
    proj, sess = _make_instance(tmp_path, live_sha="fp-live")
    (sess / "CONTROL" / "META.json").write_text(
        json.dumps({"runtime_pinned_hash": "fp-pinned"})
    )
    gogogo._runtime_drift_preflight(sess, SimpleNamespace(project_root=proj))
    evs = _drift_events(proj)
    assert len(evs) == 1
    assert evs[0]["details"]["pinned_hash"] == "fp-pinned"
    assert evs[0]["details"]["live_hash"] == "fp-live"
    assert evs[0]["details"]["blocking"] is False


def test_preflight_match_is_silent(tmp_path):
    proj, sess = _make_instance(tmp_path, live_sha="fp-same")
    (sess / "CONTROL" / "META.json").write_text(
        json.dumps({"runtime_pinned_hash": "fp-same"})
    )
    gogogo._runtime_drift_preflight(sess, SimpleNamespace(project_root=proj))
    assert _drift_events(proj) == []


def test_preflight_null_pin_failsoft(tmp_path):
    proj, sess = _make_instance(tmp_path, live_sha="fp-live")
    (sess / "CONTROL" / "META.json").write_text(
        json.dumps({"runtime_pinned_hash": None})
    )
    gogogo._runtime_drift_preflight(sess, SimpleNamespace(project_root=proj))
    assert _drift_events(proj) == []


def test_preflight_source_mode_no_crash(tmp_path):
    bare = tmp_path / "bare"
    (bare / ".ai" / "audit").mkdir(parents=True)
    s = bare / ".ai" / "sessions" / "0003"
    (s / "CONTROL").mkdir(parents=True)
    (s / "CONTROL" / "META.json").write_text(json.dumps({"runtime_pinned_hash": "fp-x"}))
    gogogo._runtime_drift_preflight(s, SimpleNamespace(project_root=bare))
    assert _drift_events(bare) == []


# ── lll read-only surface ───────────────────────────────────────────────
def test_lll_drift_true(tmp_path):
    proj, sess = _make_instance(tmp_path, live_sha="fp-live")
    (sess / "CONTROL" / "META.json").write_text(
        json.dumps({"runtime_pinned_hash": "fp-pinned"})
    )
    d = lll._runtime_drift(sess)
    assert d == {"pinned": "fp-pinned", "live": "fp-live", "drifted": True}


def test_lll_drift_false_when_match(tmp_path):
    proj, sess = _make_instance(tmp_path, live_sha="fp-same")
    (sess / "CONTROL" / "META.json").write_text(
        json.dumps({"runtime_pinned_hash": "fp-same"})
    )
    assert lll._runtime_drift(sess)["drifted"] is False


def test_lll_drift_none_source_mode(tmp_path):
    bare = tmp_path / "bare"
    (bare / "CONTROL").mkdir(parents=True)
    (bare / "CONTROL" / "META.json").write_text(json.dumps({"runtime_pinned_hash": "fp-x"}))
    assert lll._runtime_drift(bare) is None
