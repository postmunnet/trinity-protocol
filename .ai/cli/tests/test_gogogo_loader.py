"""gogogo ritual loader-integration tests (S5 — RC v1.1-rc Article XII.5).

Documents one pre-existing structural state-name divergence the integration
cannot fix in this session (`.ai/rituals/**` is in forbidden_paths):

  - Pack uses conceptual states (PLAN/SANDBOX/EXECUTE → SANDBOX/EXECUTE/
    VERIFY); the physical graph collapses these into DO → VERIFIED. The
    integration loads the pack but does NOT call assert_transition_allowed
    with the physical pair (would always fail). Test guards the conceptual
    pair independently.

Event-name alignment status: pack `step_started/_passed/_failed` matches code
emission as of the post-Constitution cleanup session (2026-05-13, Session A).
Consumers in metrics.py + tests/test_rrr.py were updated in lockstep.
"""
from __future__ import annotations

import inspect

import pytest

from cli.commands import gogogo as gogogo_mod
from cli.core.ritual_pack_loader import (
    StateTransitionError,
    assert_transition_allowed,
    check_transition_allowed,
    load_pack,
    required_audit_events,
)


RITUAL = "gogogo"


# ───────────────────────── code-presence wiring ─────────────────────────


def test_gogogo_module_imports_ritual_pack_loader_symbols():
    assert hasattr(gogogo_mod, "load_pack")
    assert hasattr(gogogo_mod, "assert_transition_allowed")


def test_gogogo_module_source_calls_load_pack_for_gogogo():
    source = inspect.getsource(gogogo_mod)
    assert "load_pack(" in source
    assert '"gogogo"' in source or "'gogogo'" in source


def test_gogogo_module_source_emits_invoked_event():
    """gogogo.invoked is the new pack-declared event added by this session."""
    source = inspect.getsource(gogogo_mod)
    assert '"gogogo.invoked"' in source or "'gogogo.invoked'" in source


def test_gogogo_module_source_emits_completed_event():
    source = inspect.getsource(gogogo_mod)
    assert '"gogogo.completed"' in source or "'gogogo.completed'" in source


def test_gogogo_module_source_emits_hmac_rejected_event():
    source = inspect.getsource(gogogo_mod)
    assert (
        '"gogogo.hmac_rejected"' in source
        or "'gogogo.hmac_rejected'" in source
    )


# ───────────────────────── pack semantics (conceptual envelope) ─────────────────────────


def test_gogogo_pack_loads_and_declares_conceptual_transitions():
    """Conceptual: PLAN/SANDBOX/EXECUTE → SANDBOX/EXECUTE/VERIFY. Graph drift
    documented in module docstring above."""
    pack = load_pack(RITUAL)
    assert set(pack.contract["allowed_current_states"]) == {
        "PLAN",
        "SANDBOX",
        "EXECUTE",
    }
    assert set(pack.contract["allowed_next_states"]) == {
        "SANDBOX",
        "EXECUTE",
        "VERIFY",
    }


def test_gogogo_pack_declares_lifecycle_events():
    pack = load_pack(RITUAL)
    declared = set(required_audit_events(pack))
    # Note: pack uses snake_case + "passed", code uses dot + "completed" —
    # see module docstring for the cross-consumer naming drift.
    assert "gogogo.invoked" in declared
    assert "gogogo.completed" in declared
    assert "gogogo.hmac_rejected" in declared


def test_gogogo_guard_accepts_conceptual_transition():
    pack = load_pack(RITUAL)
    assert check_transition_allowed(pack, "PLAN", "SANDBOX") is True
    assert check_transition_allowed(pack, "SANDBOX", "EXECUTE") is True
    assert check_transition_allowed(pack, "EXECUTE", "VERIFY") is True


def test_gogogo_guard_rejects_off_envelope_current_state():
    pack = load_pack(RITUAL)
    # DO is the PHYSICAL state used by the kernel; the pack guard does NOT
    # accept it because the pack is conceptual. Documented drift.
    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        assert_transition_allowed(pack, "DO", "VERIFY")


def test_gogogo_guard_rejects_off_envelope_next_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_next_states"):
        assert_transition_allowed(pack, "PLAN", "DEPLOYED")
