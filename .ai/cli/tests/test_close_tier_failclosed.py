"""G7/G15 — tier resolution failure is FAIL-CLOSED, never a silent WARM default.

A mis-resolved tier under the old `except: tier = "WARM"` would skip COLD
external audit. close now escalates NEEDS_HUMAN (exit 3) instead.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

import cli.commands.close as close_mod


def _make_session(tmp_path: Path, slug: str) -> Path:
    session = tmp_path / f"0001_2026-06-14_00_00_am_{slug}"
    for sub in ("DO/dev", "SANDBOX", "THINK", "CONTROL", ".state"):
        (session / sub).mkdir(parents=True)
    (session / "CONTROL" / "META.json").write_text(json.dumps({"id": session.name, "workflow": {}}))
    return session


class _FakeCap:
    """No-op capture stand-in (close's pre-archive only writes evidence)."""

    def input(self, *a, **k): pass
    def output(self, *a, **k): pass
    def validation(self, *a, **k): pass
    def runtime(self, *a, **k): pass


# ─────────── source: no silent WARM fallback ───────────


def test_no_warm_default_on_tier_failure_source() -> None:
    src = inspect.getsource(close_mod)
    assert "defaulting to WARM" not in src, "tier failure must not fall back to WARM"
    # the tier except block must escalate
    assert "tier resolution failed" in src
    assert "NEEDS_HUMAN (exit 3)" in src


# ─────────── functional: tier exception → Exit(3), no archive ───────────


def test_tier_failure_escalates_needs_human(tmp_path, monkeypatch) -> None:
    session = _make_session(tmp_path, "feat-tier")
    config = SimpleNamespace(project_root=tmp_path)

    def _boom(*_a, **_k):
        raise RuntimeError("tier probe exploded")

    monkeypatch.setattr(close_mod.manifest_module, "resolve_tier", _boom)

    with pytest.raises(typer.Exit) as exc:
        close_mod._close_pre_archive(session, config, _FakeCap())
    assert exc.value.exit_code == 3, "tier failure must escalate NEEDS_HUMAN (exit 3)"
