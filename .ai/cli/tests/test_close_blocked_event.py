"""C-1 / H1+H6 — gate blocks must be VISIBLE as a distinct close.blocked event.

The gate DECISION is unchanged (a non-terminal / unverified close still exits
1 and does not archive); C-1 only adds an audit event so the block is no longer
silent. close.blocked + close.failed must also be declared in the contract's
event vocabulary.
"""
from __future__ import annotations

import inspect

import cli.commands.close as close_mod
from cli.core.close_contract import CLOSE_AUDIT_EVENTS


# ─────────── H6 — events declared ───────────


def test_close_blocked_and_failed_declared() -> None:
    assert "close.blocked" in CLOSE_AUDIT_EVENTS
    assert "close.failed" in CLOSE_AUDIT_EVENTS


# ─────────── H1 — close.blocked emitted at each gate, decision unchanged ───────────


def test_close_blocked_emitted_at_terminal_gate() -> None:
    src = inspect.getsource(close_mod)
    lock = src.find("Session graph is not terminal")
    emit = src.find('"close.blocked"', lock)
    gate = src.find('"gate": "terminal_state"', lock)
    exit1 = src.find("raise typer.Exit(1)", lock)
    assert lock >= 0 and emit >= 0 and gate >= 0 and exit1 >= 0
    # event emitted AFTER the lock message and BEFORE the exit; decision (exit) intact
    assert lock < emit < exit1, "close.blocked must emit before the gate exit"
    assert lock < gate < exit1


def test_close_blocked_emitted_at_prod_verify_gate() -> None:
    src = inspect.getsource(close_mod)
    lock = src.find("Prod verification not passed")
    emit = src.find('"close.blocked"', lock)
    gate = src.find('"gate": "prod_verify"', lock)
    exit1 = src.find("raise typer.Exit(1)", lock)
    assert lock >= 0 and emit >= 0 and gate >= 0 and exit1 >= 0
    assert lock < emit < exit1
    assert lock < gate < exit1


def test_gate_decision_unchanged() -> None:
    """Both gates still raise Exit(1) — C-1 adds visibility, not a new outcome."""
    src = inspect.getsource(close_mod)
    # the terminal gate predicate still guards the exit
    assert "graph_state not in terminal_states" in src
    assert src.count('"close.blocked"') >= 2  # both gates emit
