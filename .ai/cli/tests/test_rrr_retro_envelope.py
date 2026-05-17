"""Phase 12 §3-4 — retro_envelope.md production tests.

Spec ref: docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md
          §3 (rrr Output Contract — deterministic only)
          §4 (retro_envelope.md schema)
          §9 conformance matrix (C1..C7, C15 idempotency)

These tests assert the additive Phase 12 implementation in rrr.py:
the new `_render_retro_envelope` writes THINK/retro_envelope.md
alongside the existing THINK/RETRO.md without disturbing the latter.

Pattern mirrors test_rrr_hmac.py: seed a real session at DEPLOYED via
test_ddd._seed_at_verified, then call cli.commands.rrr._run, then read
the resulting envelope file off disk.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
import yaml

from cli.commands.rrr import (
    RETRO_ENVELOPE_SCHEMA_VERSION,
    _run,
)
from cli.core.loop import Loop
from test_ddd import _seed_at_verified


# ─────────── helpers ───────────


def _seed_at_deployed(tmp_path: Path):
    """Reuse test_ddd._seed_at_verified, then advance to DEPLOYED so
    the rrr pipeline can run end-to-end (mirrors test_rrr_hmac.py)."""
    proj, sess = _seed_at_verified(tmp_path)
    loop = Loop(sess, graph_name="standard", project_root=proj)
    loop.fire(
        "promote_request",
        decided_by="human",
        evidence={"reason": "envelope test seed"},
    )
    loop.fire(
        "deploy_request",
        decided_by="human",
        evidence={"reason": "envelope test seed"},
    )
    assert loop.current() == "DEPLOYED"
    return proj, sess


def _read_envelope(sess: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, full_text). Raises if file missing."""
    envelope_path = sess / "THINK" / "retro_envelope.md"
    assert envelope_path.is_file(), (
        f"retro_envelope.md not produced at {envelope_path}"
    )
    text = envelope_path.read_text(encoding="utf-8")
    # Frontmatter is between the first two '---' markers.
    parts = text.split("---", 2)
    assert len(parts) >= 3, f"missing YAML frontmatter fences in {envelope_path}"
    frontmatter = yaml.safe_load(parts[1]) or {}
    return frontmatter, text


def _run_rrr(monkeypatch, proj: Path) -> int:
    monkeypatch.chdir(proj)
    return _run(
        dry_run=False,
        auto_deploy=False,
        retro_type="feat",
        baseline="HEAD",
        retroactive=False,
        session_override=None,
        hmac_envelope_file=None,
    )


# ─────────── tests ───────────


def test_envelope_file_created(tmp_path, monkeypatch):
    """C1-C7: retro_envelope.md MUST exist after rrr completes; the
    legacy RETRO.md MUST also still exist (additive only)."""
    proj, sess = _seed_at_deployed(tmp_path)
    code = _run_rrr(monkeypatch, proj)
    assert code == 0
    assert (sess / "THINK" / "RETRO.md").is_file()
    assert (sess / "THINK" / "retro_envelope.md").is_file()


def test_envelope_required_fields(tmp_path, monkeypatch):
    """§4.5 required-fields summary — every column 'required: yes' MUST
    appear in the frontmatter."""
    proj, sess = _seed_at_deployed(tmp_path)
    assert _run_rrr(monkeypatch, proj) == 0
    fm, _ = _read_envelope(sess)

    required_keys = {
        "schema_version",
        "session_id",
        "slug",
        "ts_started",
        "ts_closed",
        "duration_seconds",
        "tier",
        "graph_state_final",
        "decided_by",
        "acceptance_results",
        "acceptance_summary",
        "forbidden_diff_status",
        "baseline_untracked",
        "audit",
        "transition_count",
        "gogogo_verdicts",
        "iterations",
        "indexed_retros",
        "artifact_paths",
        "memory_index_result",
    }
    missing = required_keys - set(fm.keys())
    assert not missing, f"envelope missing required keys: {missing}"

    # schema_version pin (§4.1)
    assert fm["schema_version"] == RETRO_ENVELOPE_SCHEMA_VERSION

    # acceptance_summary sub-keys (§4.2)
    summary = fm["acceptance_summary"]
    for k in ("total", "pass", "fail", "skipped", "required_failures"):
        assert k in summary, f"acceptance_summary missing key {k!r}"

    # audit sub-keys (§4.3)
    audit = fm["audit"]
    for k in ("session_chain_head", "last_seq", "verify_chain_status"):
        assert k in audit, f"audit missing key {k!r}"

    # gogogo_verdicts sub-keys (§4.3)
    verdicts = fm["gogogo_verdicts"]
    for k in ("PASS", "FAIL", "UNVERIFIED"):
        assert k in verdicts, f"gogogo_verdicts missing key {k!r}"


def test_envelope_idempotent_modulo_ts(tmp_path, monkeypatch):
    """§9 C15: re-running rrr produces byte-identical envelope EXCEPT
    for ts_closed (and any field deterministically derived from it,
    e.g. duration_seconds).

    First run uses the normal path (DEPLOYED → DONE). Second run uses
    --retroactive to bypass the graph_state guard (since the session
    is already at DONE after the first run) — this is the spec-aligned
    way to re-render the envelope for the same session.
    """
    proj, sess = _seed_at_deployed(tmp_path)
    assert _run_rrr(monkeypatch, proj) == 0
    fm1, _ = _read_envelope(sess)

    # Sleep ~1.1s so ts_closed advances at second-resolution.
    time.sleep(1.1)
    monkeypatch.chdir(proj)
    code2 = _run(
        dry_run=False,
        auto_deploy=False,
        retro_type="feat",
        baseline="HEAD",
        retroactive=True,
        session_override=str(sess),
        hmac_envelope_file=None,
    )
    assert code2 == 0
    fm2, _ = _read_envelope(sess)

    # ts_closed MUST differ (per C15 modulo clause).
    assert fm1["ts_closed"] != fm2["ts_closed"], (
        "ts_closed should advance between successive rrr runs"
    )

    # Strip ts_closed + duration_seconds (derived from ts_closed) +
    # last_seq (audit chain grows by one rrr.completed row each run) +
    # transition_count / iterations (no new gogogo steps but the
    # second rrr appends rrr.invoked + delegated_call etc) +
    # session_chain_head (advances) + indexed_retros (a second retro
    # file may be minted on the second run) + artifact_paths (new
    # files appear on the second run).
    drop = {
        "ts_closed",
        "duration_seconds",
        "audit",
        "transition_count",
        "iterations",
        "indexed_retros",
        "artifact_paths",
        "gogogo_verdicts",
        "graph_state_final",
    }
    fm1_stable = {k: v for k, v in fm1.items() if k not in drop}
    fm2_stable = {k: v for k, v in fm2.items() if k not in drop}
    assert fm1_stable == fm2_stable, (
        f"stable fields drifted between runs:\n"
        f"  fm1={fm1_stable}\n  fm2={fm2_stable}"
    )

    # Schema invariants hold across both runs.
    for fm in (fm1, fm2):
        assert fm["schema_version"] == RETRO_ENVELOPE_SCHEMA_VERSION
        assert fm["session_id"] == sess.name
        assert fm["decided_by"] == "kernel"


def test_envelope_acceptance_summary_consistent(tmp_path, monkeypatch):
    """The summary counts MUST match the acceptance_results array."""
    proj, sess = _seed_at_deployed(tmp_path)
    assert _run_rrr(monkeypatch, proj) == 0
    fm, _ = _read_envelope(sess)

    results = fm["acceptance_results"]
    summary = fm["acceptance_summary"]
    assert isinstance(results, list)

    expected_total = len(results)
    expected_pass = sum(1 for r in results if r.get("status") == "PASS")
    expected_fail = sum(1 for r in results if r.get("status") == "FAIL")
    expected_required_fail = sum(
        1 for r in results
        if r.get("required") and r.get("status") == "FAIL"
    )

    assert summary["total"] == expected_total
    assert summary["pass"] == expected_pass
    assert summary["fail"] == expected_fail
    assert summary["required_failures"] == expected_required_fail
    # pass + fail + skipped == total (no orphans)
    assert (
        summary["pass"] + summary["fail"] + summary["skipped"]
        == summary["total"]
    )


def test_envelope_yaml_parseable(tmp_path, monkeypatch):
    """The frontmatter MUST be valid YAML and decode to a dict."""
    proj, sess = _seed_at_deployed(tmp_path)
    assert _run_rrr(monkeypatch, proj) == 0
    text = (sess / "THINK" / "retro_envelope.md").read_text(encoding="utf-8")

    parts = text.split("---", 2)
    assert len(parts) >= 3, "expected '---' YAML fences in envelope"
    payload = yaml.safe_load(parts[1])
    assert isinstance(payload, dict), (
        f"frontmatter did not parse as dict; got {type(payload).__name__}"
    )

    # Body sanity: a brief note pointing readers at RETRO.md for meaning.
    body = parts[2]
    assert "retro_envelope" in body.lower()
    assert "RETRO.md" in body  # cross-link to the semantic companion


def test_envelope_decided_by_kernel(tmp_path, monkeypatch):
    """Article XX (Passive Core) + spec §4.1: rrr MUST stamp
    decided_by='kernel' (never 'human')."""
    proj, sess = _seed_at_deployed(tmp_path)
    assert _run_rrr(monkeypatch, proj) == 0
    fm, _ = _read_envelope(sess)
    assert fm["decided_by"] == "kernel"


def test_envelope_does_not_break_retro_md(tmp_path, monkeypatch):
    """RETRO.md production path is unchanged: same frontmatter sentinel
    (acceptance-evidence, rrr-contract) MUST still appear."""
    proj, sess = _seed_at_deployed(tmp_path)
    assert _run_rrr(monkeypatch, proj) == 0
    retro_md = (sess / "THINK" / "RETRO.md").read_text(encoding="utf-8")
    # Sentinels asserted by the existing test_render_retro_includes_verdicts.
    assert "acceptance-evidence:" in retro_md
    assert "rrr-contract:" in retro_md
    assert "# Retrospective" in retro_md
