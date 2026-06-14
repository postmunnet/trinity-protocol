"""F3/F3b — close must not manufacture a DONE workflow state.

close is a Seal/Archive layer: DONE is owned by rrr (RETRO -> DONE). close
preserves the incoming terminal graph state (DONE stays DONE, DEAD stays
DEAD) into the final manifest, and never calls set_state("DONE").
(session close-P0-safety, 2026-06-14)
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import cli.commands.close as close_mod
from cli.core.state import SessionLocalState
from cli.core import manifest as manifest_module


# ─────────── G18: no close-owned DONE manufacturing in source ───────────


def test_no_self_set_done_source() -> None:
    src = inspect.getsource(close_mod)
    assert 'set_state("DONE")' not in src, "close must not call set_state('DONE')"
    assert 'graph_state_final="DONE"' not in src, "manifest must not hard-code DONE"


def test_close_derives_graph_state_for_manifest() -> None:
    """close derives the manifest terminal from the real session graph_state."""
    src = inspect.getsource(close_mod)
    assert "graph_state_final = sls.graph_state(" in src
    assert "graph_state_final=graph_state_final" in src


# ─────────── G17: a DEAD close stays DEAD ───────────


def _make_session(tmp_path: Path, slug: str) -> Path:
    session = tmp_path / f"0001_2026-06-14_00_00_am_{slug}"
    for sub in ("DO/dev", "SANDBOX", "THINK", "CONTROL", ".state"):
        (session / sub).mkdir(parents=True)
    (session / "CONTROL" / "META.json").write_text(json.dumps({"id": session.name}))
    return session


def test_dead_preserved(tmp_path: Path) -> None:
    """A session closed at DEAD must record graph_state_final == DEAD, not DONE."""
    session = _make_session(tmp_path, "feat-dead")
    sls = SessionLocalState(session)
    sls.set_graph_state("DEAD")
    # Exactly what close.py derives: graph_state_final = sls.graph_state(default=...)
    derived = sls.graph_state(default=sls.current_state())
    assert derived == "DEAD"
    manifest = manifest_module.build_final_manifest(
        session, "WARM", graph_state_final=derived
    )
    assert manifest["graph_state_final"] == "DEAD", "close rewrote DEAD -> DONE"
