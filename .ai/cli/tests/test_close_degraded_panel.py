"""C-3 / H2+H3 — close panel tells the truth: degraded visibility + real state.

degraded is CLOSE-QUALITY (fail-soft steps that produced no artifact) — it
never mutates graph state. The panel shows the real terminal state (DEAD stays
DEAD, never hard-coded DONE) and flags degradation.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import cli.commands.close as close_mod
from cli.core.state import SessionLocalState


def _make_session(tmp_path: Path, slug: str) -> Path:
    session = tmp_path / f"0001_2026-06-14_00_00_am_{slug}"
    for sub in ("DO/dev", "SANDBOX", "THINK", "CONTROL", ".state"):
        (session / sub).mkdir(parents=True)
    (session / "CONTROL" / "META.json").write_text(
        json.dumps({"id": session.name, "workflow": {}})
    )
    return session


class _FakeCap:
    def input(self, *a, **k): pass
    def output(self, *a, **k): pass
    def validation(self, *a, **k): pass
    def runtime(self, *a, **k): pass


def _stub_tier(monkeypatch):
    """Keep tier resolution out of the way (WARM) so _close_pre_archive runs."""
    monkeypatch.setattr(close_mod.manifest_module, "resolve_tier", lambda *_a, **_k: "WARM")


# ─────────── H3 — DEAD close stays DEAD in the panel state ───────────


def test_dead_state_preserved_in_pre_archive(tmp_path, monkeypatch) -> None:
    _stub_tier(monkeypatch)
    session = _make_session(tmp_path, "feat-dead")
    SessionLocalState(session).set_graph_state("DEAD")
    pre = close_mod._close_pre_archive(session, SimpleNamespace(project_root=tmp_path), _FakeCap())
    assert pre["graph_state_final"] == "DEAD", "close rewrote DEAD in the panel state"


def test_panel_uses_real_state_not_hardcoded_dead_state() -> None:
    src = inspect.getsource(close_mod)
    assert "• State: {graph_state_final}" in src, "panel must use derived graph_state_final"
    assert '"• State: DONE\\n"' not in src and "State: DONE\\n" not in src, (
        "panel must not hard-code State: DONE"
    )


# ─────────── H2 — degraded tracked + panel branches yellow/green ───────────


def test_degraded_tracked_on_close_pack_failure(tmp_path, monkeypatch) -> None:
    _stub_tier(monkeypatch)
    session = _make_session(tmp_path, "feat-degraded")
    SessionLocalState(session).set_graph_state("DONE")

    def _boom(*_a, **_k):
        raise RuntimeError("close pack render exploded")

    monkeypatch.setattr(close_mod, "write_close_pack", _boom)
    pre = close_mod._close_pre_archive(session, SimpleNamespace(project_root=tmp_path), _FakeCap())
    assert "close_pack" in pre["degraded"], "fail-soft close_pack must register as degraded"


def test_degraded_returns_list_type(tmp_path, monkeypatch) -> None:
    _stub_tier(monkeypatch)
    session = _make_session(tmp_path, "feat-deglist")
    SessionLocalState(session).set_graph_state("DONE")
    pre = close_mod._close_pre_archive(session, SimpleNamespace(project_root=tmp_path), _FakeCap())
    assert isinstance(pre.get("degraded"), list)


def test_panel_degraded_branch_source() -> None:
    """Panel switches to a yellow DEGRADED presentation when degraded is non-empty."""
    src = inspect.getsource(close_mod)
    assert "DEGRADED" in src
    assert "panel_border" in src and "border_style=panel_border" in src
    assert 'panel_border = "yellow"' in src and 'panel_border = "green"' in src
