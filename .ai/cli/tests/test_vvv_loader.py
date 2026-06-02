"""vvv ritual loader-integration tests (S3 — RC v1.1-rc Article XII.5).

Two-layer evidence:

1. Code-presence — `cli.commands.vvv` imports the loader API and emits the
   pack-declared vvv-prefixed audit events. This is the empirical artifact
   the meta-rule requires.
2. Pack semantics — the .ai/rituals/vvv/ pack loads cleanly, declares the
   expected (current, next) transition envelope (THINK → THINK), and the
   guard rejects an off-envelope attempt.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from cli.commands import vvv as vvv_mod
from cli.core.ritual_pack_loader import (
    StateTransitionError,
    assert_transition_allowed,
    check_transition_allowed,
    load_pack,
    required_audit_events,
)


RITUAL = "vvv"


# ───────────────────────── code-presence wiring ─────────────────────────


def test_vvv_module_imports_ritual_pack_loader_symbols():
    """vvv must import load_pack + assert_transition_allowed (XII.5 wiring)."""
    assert hasattr(vvv_mod, "load_pack")
    assert hasattr(vvv_mod, "assert_transition_allowed")


def test_vvv_module_source_calls_load_pack_for_vvv():
    source = inspect.getsource(vvv_mod)
    assert "load_pack(" in source
    assert '"vvv"' in source or "'vvv'" in source


def test_vvv_module_source_calls_assert_transition_allowed():
    source = inspect.getsource(vvv_mod)
    assert "assert_transition_allowed(" in source


def test_vvv_module_source_emits_invoked_and_failed_events():
    """vvv.invoked is emitted on the happy path; vvv.failed on missing-answers."""
    source = inspect.getsource(vvv_mod)
    assert '"vvv.invoked"' in source or "'vvv.invoked'" in source
    assert '"vvv.failed"' in source or "'vvv.failed'" in source


# ───────────────────────── pack semantics ─────────────────────────


def test_vvv_pack_loads_and_declares_expected_transitions():
    pack = load_pack(RITUAL)
    # Per RITUALS.md canonical order, vvv accepts both fresh THINK state
    # and re-run SANDBOX state (re-answering questions on an already-
    # transitioned session). Conceptual next-state remains THINK (the
    # clarification artifact stays in the THINK folder); physical
    # transition THINK->SANDBOX is fired by loop.fire("vvv_pass").
    assert pack.contract["allowed_current_states"] == ["THINK", "SANDBOX"]
    assert pack.contract["allowed_next_states"] == ["THINK"]


def test_vvv_pack_audit_events_cover_invoked_proposed_passed_failed():
    pack = load_pack(RITUAL)
    declared = set(required_audit_events(pack))
    # All four lifecycle events must be declared so empirical ratification
    # has a single source of truth for the event vocabulary.
    assert {"vvv.invoked", "vvv.proposed", "vvv.passed", "vvv.failed"} <= declared


def test_vvv_guard_accepts_canonical_transition():
    pack = load_pack(RITUAL)
    assert check_transition_allowed(pack, "THINK", "THINK") is True
    assert_transition_allowed(pack, "THINK", "THINK")  # no raise


def test_vvv_guard_rejects_off_envelope_current_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        assert_transition_allowed(pack, "PLAN", "THINK")


def test_vvv_guard_rejects_off_envelope_next_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_next_states"):
        assert_transition_allowed(pack, "THINK", "DEPLOYED")
