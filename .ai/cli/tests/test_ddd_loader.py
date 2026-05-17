"""ddd ritual loader-integration tests (S6 — RC v1.1-rc Article XII.5).

Documents two pre-existing structural drifts the integration cannot fix
in this session (`.ai/rituals/**` is in forbidden_paths):

  - Pack uses conceptual states (VERIFY/NEEDS_HUMAN → PROMOTE/NEEDS_HUMAN/
    FAILED); the physical graph uses VERIFIED → PROMOTED → DEPLOYED.
  - Pack declares `ddd.approved` / `ddd.rejected` / `ddd.held`; the kernel
    emits `ddd.completed` (and `ddd.hmac_rejected`). Aligning these names
    is a separate-session refactor.
"""
from __future__ import annotations

import inspect

import pytest

from cli.commands import ddd as ddd_mod
from cli.core.ritual_pack_loader import (
    StateTransitionError,
    assert_transition_allowed,
    check_transition_allowed,
    load_pack,
    required_audit_events,
)


RITUAL = "ddd"


# ───────────────────────── code-presence wiring ─────────────────────────


def test_ddd_module_imports_ritual_pack_loader_symbols():
    assert hasattr(ddd_mod, "load_pack")
    assert hasattr(ddd_mod, "assert_transition_allowed")


def test_ddd_module_source_calls_load_pack_for_ddd():
    source = inspect.getsource(ddd_mod)
    assert "load_pack(" in source
    assert '"ddd"' in source or "'ddd'" in source


def test_ddd_module_source_emits_invoked_event():
    source = inspect.getsource(ddd_mod)
    assert '"ddd.invoked"' in source or "'ddd.invoked'" in source


def test_ddd_module_source_emits_hmac_rejected_event():
    source = inspect.getsource(ddd_mod)
    assert (
        '"ddd.hmac_rejected"' in source or "'ddd.hmac_rejected'" in source
    )


# ───────────────────────── pack semantics ─────────────────────────


def test_ddd_pack_loads_and_declares_conceptual_transitions():
    pack = load_pack(RITUAL)
    assert set(pack.contract["allowed_current_states"]) == {"VERIFY", "NEEDS_HUMAN"}
    assert set(pack.contract["allowed_next_states"]) == {
        "PROMOTE",
        "NEEDS_HUMAN",
        "FAILED",
    }


def test_ddd_pack_declares_lifecycle_events():
    pack = load_pack(RITUAL)
    declared = set(required_audit_events(pack))
    assert {
        "ddd.invoked",
        "ddd.proposed",
        "ddd.approved",
        "ddd.rejected",
        "ddd.held",
        "ddd.hmac_rejected",
    } <= declared


def test_ddd_guard_accepts_conceptual_transition():
    pack = load_pack(RITUAL)
    assert check_transition_allowed(pack, "VERIFY", "PROMOTE") is True
    assert check_transition_allowed(pack, "NEEDS_HUMAN", "FAILED") is True


def test_ddd_guard_rejects_off_envelope_current_state():
    pack = load_pack(RITUAL)
    # VERIFIED is the PHYSICAL state; pack uses VERIFY (conceptual).
    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        assert_transition_allowed(pack, "VERIFIED", "PROMOTE")


def test_ddd_guard_rejects_off_envelope_next_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_next_states"):
        assert_transition_allowed(pack, "VERIFY", "DEPLOYED")
