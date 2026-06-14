"""G1/G12 — close gates on physical terminals and blocks non-terminal closes
BEFORE any session/archive/status mutation.

close.invoked is appended before the gate (Article XX) — that is allowed; the
gate must prevent everything downstream (pre-archive work, archive, status).
"""
from __future__ import annotations

import inspect
from pathlib import Path

import cli.commands.close as close_mod
from cli.core.terminal_states import get_terminal_states_for_close

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ─────────── G1 — DONE/DEAD pass the gate ───────────


def test_terminal_pass() -> None:
    terms = get_terminal_states_for_close(PROJECT_ROOT)
    assert {"DONE", "DEAD"} <= terms


# ─────────── G12 — non-terminal blocks before any mutation ───────────


def test_nonterminal_blocks_before_any_mutation() -> None:
    src = inspect.getsource(close_mod)
    gate = src.find("graph_state not in terminal_states")
    assert gate >= 0, "terminal gate predicate missing"
    lock = src.find("Session graph is not terminal", gate)
    exit1 = src.find("raise typer.Exit(1)", gate)
    pre_archive = src.find("_close_pre_archive(session_path, config, cap)")
    archive = src.find("archive_session(session_path, config)")
    assert gate < lock < exit1, "gate must lock + exit on non-terminal"
    # The blocking exit must precede ALL mutating work: pre-archive + archive.
    assert exit1 < pre_archive, "gate must block before pre-archive mutation"
    assert exit1 < archive, "gate must block before archive"


def test_nonterminal_gate_under_not_force() -> None:
    """--force bypasses the terminal gate (the gate lives under `if not force:`)."""
    src = inspect.getsource(close_mod)
    gate = src.find("graph_state not in terminal_states")
    guard = src.rfind("if not force:", 0, gate)
    assert guard >= 0, "terminal gate must be guarded by `if not force:`"
