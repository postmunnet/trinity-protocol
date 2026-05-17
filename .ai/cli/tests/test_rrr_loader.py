"""rrr ritual loader-integration tests (S7 — RC v1.1-rc Article XII.5).

Documents pack/graph state-name drift the integration cannot fix in this
session (`.ai/rituals/**` is in forbidden_paths):

  - Pack uses conceptual states (DEPLOY/RETRO → RETRO/DONE); the physical
    graph admits VERIFIED/PROMOTED/DEPLOYED/RETRO as legal current states.
    The integration loads the pack and emits rrr.invoked but does NOT
    pass the physical current_state through assert_transition_allowed
    (would always fail). Test guards the conceptual pair independently.
"""
from __future__ import annotations

import inspect

import pytest

from cli.commands import rrr as rrr_mod
from cli.core.ritual_pack_loader import (
    StateTransitionError,
    assert_transition_allowed,
    check_transition_allowed,
    load_pack,
    required_audit_events,
)


RITUAL = "rrr"


# ───────────────────────── code-presence wiring ─────────────────────────


def test_rrr_module_imports_ritual_pack_loader_symbols():
    assert hasattr(rrr_mod, "load_pack")
    assert hasattr(rrr_mod, "assert_transition_allowed")


def test_rrr_module_source_calls_load_pack_for_rrr():
    source = inspect.getsource(rrr_mod)
    assert "load_pack(" in source
    assert '"rrr"' in source or "'rrr'" in source


def test_rrr_module_source_emits_invoked_event():
    source = inspect.getsource(rrr_mod)
    assert '"rrr.invoked"' in source or "'rrr.invoked'" in source


def test_rrr_module_source_emits_hmac_rejected_event():
    source = inspect.getsource(rrr_mod)
    assert (
        '"rrr.hmac_rejected"' in source or "'rrr.hmac_rejected'" in source
    )


# ───────────────────────── pack semantics ─────────────────────────


def test_rrr_pack_loads_and_declares_conceptual_transitions():
    pack = load_pack(RITUAL)
    assert set(pack.contract["allowed_current_states"]) == {"DEPLOY", "RETRO"}
    assert set(pack.contract["allowed_next_states"]) == {"RETRO", "DONE"}


def test_rrr_pack_declares_lifecycle_events():
    pack = load_pack(RITUAL)
    declared = set(required_audit_events(pack))
    assert {
        "rrr.invoked",
        "rrr.proposed",
        "rrr.delegated_call",
        "rrr.completed",
        "rrr.index_failed",
    } <= declared


def test_rrr_guard_accepts_conceptual_transition():
    pack = load_pack(RITUAL)
    assert check_transition_allowed(pack, "DEPLOY", "RETRO") is True
    assert check_transition_allowed(pack, "RETRO", "DONE") is True


def test_rrr_guard_rejects_off_envelope_current_state():
    pack = load_pack(RITUAL)
    # DEPLOYED/VERIFIED/PROMOTED are PHYSICAL states; pack uses DEPLOY/RETRO
    # (conceptual). Documented drift.
    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        assert_transition_allowed(pack, "DEPLOYED", "RETRO")


def test_rrr_guard_rejects_off_envelope_next_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_next_states"):
        assert_transition_allowed(pack, "RETRO", "SEALED")
