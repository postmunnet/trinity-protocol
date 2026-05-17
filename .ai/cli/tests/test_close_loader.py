"""close ritual loader-integration tests (Session A — post-Constitution).

Mirrors the per-ritual integration test pattern from test_{sss,vvv,nnn,
gogogo,ddd,rrr}_loader.py. Documents pack/graph state-name drift the
integration cannot fix in this session (`.ai/rituals/**` is in
forbidden_paths):

  - Pack uses conceptual states (DONE/FAILED/ABORTED → SEALED); the
    physical graph uses DONE only as the terminal close-eligible state.
    The integration loads the pack and emits close.invoked +
    close.completed but does NOT pass the physical (current, next) pair
    through assert_transition_allowed (would always raise for SEALED
    since the graph has no such state).
"""
from __future__ import annotations

import inspect

import pytest

from cli.commands import close as close_mod
from cli.core.ritual_pack_loader import (
    StateTransitionError,
    assert_transition_allowed,
    check_transition_allowed,
    load_pack,
    required_audit_events,
)


RITUAL = "close"


# ───────────────────────── code-presence wiring ─────────────────────────


def test_close_module_imports_ritual_pack_loader_symbols():
    assert hasattr(close_mod, "load_pack")
    assert hasattr(close_mod, "assert_transition_allowed")


def test_close_module_source_calls_load_pack_for_close():
    source = inspect.getsource(close_mod)
    assert "load_pack(" in source
    assert '"close"' in source or "'close'" in source


def test_close_module_source_emits_invoked_and_completed_events():
    source = inspect.getsource(close_mod)
    assert '"close.invoked"' in source or "'close.invoked'" in source
    assert '"close.completed"' in source or "'close.completed'" in source


# ───────────────────────── pack semantics ─────────────────────────


def test_close_pack_loads_and_declares_conceptual_transitions():
    pack = load_pack(RITUAL)
    assert set(pack.contract["allowed_current_states"]) == {
        "DONE",
        "FAILED",
        "ABORTED",
    }
    assert pack.contract["allowed_next_states"] == ["SEALED"]


def test_close_pack_declares_lifecycle_events():
    pack = load_pack(RITUAL)
    declared = set(required_audit_events(pack))
    assert {
        "close.invoked",
        "close.proposed",
        "close.completed",
        "close.external_audit_emitted",
        "close.failed",
    } <= declared


def test_close_guard_accepts_conceptual_transitions():
    pack = load_pack(RITUAL)
    assert check_transition_allowed(pack, "DONE", "SEALED") is True
    assert check_transition_allowed(pack, "FAILED", "SEALED") is True
    assert check_transition_allowed(pack, "ABORTED", "SEALED") is True


def test_close_guard_rejects_off_envelope_current_state():
    pack = load_pack(RITUAL)
    # DEPLOYED/VERIFIED/THINK are NOT in the pack's allowed_current_states.
    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        assert_transition_allowed(pack, "DEPLOYED", "SEALED")


def test_close_guard_rejects_off_envelope_next_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_next_states"):
        assert_transition_allowed(pack, "DONE", "DEPLOYED")
