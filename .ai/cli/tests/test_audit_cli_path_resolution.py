"""Regression tests for `ai audit *` path resolution.

Pre-existing bug class — fixed 2026-05-14 by switching from raw
``Path.cwd()`` to ``SSOTLoader(Path.cwd()).project_root``:

Before:
  - The kernel wrapper script (.ai/cli/ai) ``cd``s into ``<repo>/.ai/``
    before invoking ``python -m cli.main``.
  - ``audit.py:_resolve_chain_source`` did ``repo_root = Path.cwd()``
    then ``repo_root / ".ai" / "audit" / "events.ndjson"`` — producing
    ``<repo>/.ai/.ai/audit/events.ndjson`` (double ``.ai``).
  - The file does not exist at that doubled path, so the command exited
    with ``Source not found:`` — even though the chain was healthy.

After:
  - ``SSOTLoader(Path.cwd()).project_root`` walks upward looking for
    ``.ai/ssot.yaml`` and returns the actual repo root. The doubled
    ``.ai`` no longer occurs.

The pre-existing ``test_audit_cli.py`` did not catch this bug because
every test passed ``--legacy-ndjson <explicit path>`` or
``--session <id>`` inside ``runner.isolated_filesystem``, both of which
bypass the bug's code path. This file tests the no-explicit-path branch
that the bug actually lived in.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.commands.audit import _project_root, _resolve_chain_source, app as audit_app
from cli.core.audit_replay import _canonical_json_legacy


runner = CliRunner()


# ---------------------------------------------------------------------------
# Unit: _project_root resilient to cwd-inside-.ai (the wrapper's reality)
# ---------------------------------------------------------------------------


def test_project_root_resolves_from_repo_root(tmp_path: Path):
    """When cwd IS the repo root and a .ai/ssot.yaml marker exists,
    _project_root returns the repo root."""
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "ssot.yaml").write_text("# marker\n", encoding="utf-8")

    got = _project_root(tmp_path)

    assert got.resolve() == tmp_path.resolve()


def test_project_root_resolves_when_cwd_is_dot_ai(tmp_path: Path):
    """Reproduces the wrapper script's cwd. The wrapper does
    ``cd "$AI_ROOT"`` so cwd ends up as ``<repo>/.ai/``. _project_root
    MUST walk up and return ``<repo>/``, NOT ``<repo>/.ai/`` (the
    pre-fix bug doubled .ai by prepending again)."""
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "ssot.yaml").write_text("# marker\n", encoding="utf-8")

    # Simulate `cd <repo>/.ai/` then call _project_root from inside
    got = _project_root(tmp_path / ".ai")

    assert got.resolve() == tmp_path.resolve(), (
        f"expected repo root {tmp_path}; "
        f"got {got} (double-.ai bug not regressed?)"
    )


def test_project_root_falls_back_to_start_when_no_marker(tmp_path: Path):
    """No ssot.yaml anywhere → fall back to the start path (don't crash).
    This is the CliRunner.isolated_filesystem scenario."""
    got = _project_root(tmp_path)
    assert got.resolve() == tmp_path.resolve()


# ---------------------------------------------------------------------------
# Unit: _resolve_chain_source returns the un-doubled path
# ---------------------------------------------------------------------------


def test_resolve_chain_source_legacy_from_dot_ai_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """When cwd is ``<repo>/.ai/`` (wrapper's reality), the resolved
    legacy ndjson path MUST be ``<repo>/.ai/audit/events.ndjson`` — one
    ``.ai`` segment, not two."""
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "ssot.yaml").write_text("# marker\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path / ".ai")

    chain_kind, path = _resolve_chain_source(session=None, legacy_ndjson=None)

    assert chain_kind == "legacy"
    expected = tmp_path / ".ai" / "audit" / "events.ndjson"
    assert path.resolve() == expected.resolve(), (
        f"path-doubling regression — expected {expected}, got {path}"
    )
    # Sanity check the doubled-.ai pattern is NOT present
    parts = path.parts
    ai_count = sum(1 for p in parts if p == ".ai")
    assert ai_count == 1, (
        f"resolved path contains {ai_count} .ai segments: {path}"
    )


def test_resolve_chain_source_session_from_dot_ai_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Same anti-doubling guarantee for session-mode resolution."""
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "ssot.yaml").write_text("# marker\n", encoding="utf-8")
    sess_dir = tmp_path / ".ai" / "sessions" / "0001_test_sess"
    sess_dir.mkdir(parents=True)

    monkeypatch.chdir(tmp_path / ".ai")

    chain_kind, path = _resolve_chain_source(
        session="0001_test_sess", legacy_ndjson=None
    )

    assert chain_kind == "session"
    expected = (
        tmp_path
        / ".ai"
        / "sessions"
        / "0001_test_sess"
        / "CAPTURE"
        / "capture.sqlite"
    )
    assert path.resolve() == expected.resolve(), (
        f"session-mode path-doubling regression — "
        f"expected {expected}, got {path}"
    )


def test_resolve_chain_source_legacy_override_preserved(tmp_path: Path):
    """--legacy-ndjson explicit path MUST still bypass cwd resolution
    entirely (existing test_audit_cli.py contract)."""
    explicit = tmp_path / "explicit.ndjson"
    explicit.write_text("")

    chain_kind, path = _resolve_chain_source(
        session=None, legacy_ndjson=explicit
    )

    assert chain_kind == "legacy"
    assert path == explicit


# ---------------------------------------------------------------------------
# Integration: verify-chain + replay no-arg CLI invocation end-to-end
# ---------------------------------------------------------------------------


def _seed_minimal_chain(audit_path: Path):
    """Write a single self-consistent legacy genesis event using the same
    canonical-JSON helper the verifier uses, so verify-chain accepts it.

    Mirrors the pattern in test_audit_cli.py::_make_legacy_ndjson: genesis
    has ``prev_hash: "0"`` and the hash is computed via
    ``_canonical_json_legacy`` to guarantee byte-for-byte agreement.
    """
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": "2026-05-14T00:00:00Z",
        "type": "genesis",
        "prev_hash": "0",
        "details": {},
    }
    event["hash"] = hashlib.sha256(
        _canonical_json_legacy(event).encode()
    ).hexdigest()
    audit_path.write_text(json.dumps(event) + "\n", encoding="utf-8")


def test_verify_chain_no_arg_from_dot_ai_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """End-to-end: simulate the wrapper's cwd, invoke `audit verify-chain`
    with no flags, and confirm exit 0 (the actual bug failure mode)."""
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "ssot.yaml").write_text("# marker\n", encoding="utf-8")
    _seed_minimal_chain(tmp_path / ".ai" / "audit" / "events.ndjson")

    monkeypatch.chdir(tmp_path / ".ai")
    result = runner.invoke(audit_app, ["verify-chain"])

    assert result.exit_code == 0, (
        f"audit verify-chain regressed: rc={result.exit_code}\n"
        f"output={result.output!r}"
    )
    assert "Source not found" not in (result.output or ""), (
        "path-doubling bug re-introduced — "
        "'Source not found' should not appear"
    )


def test_replay_no_arg_from_dot_ai_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """End-to-end: same setup, exercise `audit replay`."""
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "ssot.yaml").write_text("# marker\n", encoding="utf-8")
    _seed_minimal_chain(tmp_path / ".ai" / "audit" / "events.ndjson")

    monkeypatch.chdir(tmp_path / ".ai")
    result = runner.invoke(audit_app, ["replay"])

    assert result.exit_code == 0, (
        f"audit replay regressed: rc={result.exit_code}\n"
        f"output={result.output!r}"
    )
    assert "Source not found" not in (result.output or "")
