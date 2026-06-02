"""nnn ritual loader-integration tests (S4 — RC v1.1-rc Article XII.5)."""
from __future__ import annotations

import inspect

import pytest

from cli.commands import nnn as nnn_mod
from cli.core.ritual_pack_loader import (
    StateTransitionError,
    assert_transition_allowed,
    check_transition_allowed,
    load_pack,
    required_audit_events,
)


RITUAL = "nnn"


# ───────────────────────── code-presence wiring ─────────────────────────


def test_nnn_module_imports_ritual_pack_loader_symbols():
    assert hasattr(nnn_mod, "load_pack")
    assert hasattr(nnn_mod, "assert_transition_allowed")


def test_nnn_module_source_calls_load_pack_for_nnn():
    source = inspect.getsource(nnn_mod)
    assert "load_pack(" in source
    assert '"nnn"' in source or "'nnn'" in source


def test_nnn_module_source_calls_assert_transition_allowed():
    source = inspect.getsource(nnn_mod)
    assert "assert_transition_allowed(" in source


def test_nnn_module_source_emits_pack_declared_lifecycle_events():
    """nnn.invoked, nnn.proposed, nnn.passed, nnn.failed, plan.budget_checked."""
    source = inspect.getsource(nnn_mod)
    for event in (
        "nnn.invoked",
        "nnn.proposed",
        "nnn.passed",
        "nnn.failed",
        "plan.budget_checked",
    ):
        assert f'"{event}"' in source or f"'{event}'" in source, (
            f"nnn.py source must contain emission of pack-declared event "
            f"{event!r}"
        )


# ───────────────────────── pack semantics ─────────────────────────


def test_nnn_pack_loads_and_declares_expected_transitions():
    """Pack envelope is conceptual: SANDBOX→PLAN. Graph collapses PLAN into
    DO (graphs/standard.yaml: nnn_pass: SANDBOX→DO) — per RITUALS.md canonical
    order, vvv has already fired THINK→SANDBOX when nnn is invoked."""
    pack = load_pack(RITUAL)
    assert pack.contract["allowed_current_states"] == ["SANDBOX"]
    assert pack.contract["allowed_next_states"] == ["PLAN"]


def test_nnn_pack_audit_events_cover_full_lifecycle():
    pack = load_pack(RITUAL)
    declared = set(required_audit_events(pack))
    assert {
        "nnn.invoked",
        "nnn.proposed",
        "nnn.passed",
        "nnn.failed",
        "plan.budget_checked",
    } <= declared


def test_nnn_guard_accepts_canonical_transition():
    pack = load_pack(RITUAL)
    assert check_transition_allowed(pack, "SANDBOX", "PLAN") is True
    assert_transition_allowed(pack, "SANDBOX", "PLAN")


def test_nnn_guard_rejects_off_envelope_current_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        assert_transition_allowed(pack, "READY", "PLAN")


def test_nnn_guard_rejects_off_envelope_next_state():
    pack = load_pack(RITUAL)
    with pytest.raises(StateTransitionError, match="not in allowed_next_states"):
        assert_transition_allowed(pack, "SANDBOX", "DEPLOYED")
