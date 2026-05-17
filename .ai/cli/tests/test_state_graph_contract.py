"""Conformance tests for the Kernel + State-Graph organ contract.

Spec: docs/specs/TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md
       docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §1+§2
       .ai/graphs/standard.yaml (live source of truth)

Tier-0/1 deterministic. Asserts the contract surface invariants AND the
yaml-vs-Python parity (standard.yaml ⊆ STANDARD_TRANSITIONS).
"""
from __future__ import annotations

import dataclasses
import pathlib

import pytest
import yaml

from cli.core.state_graph import (
    ALLOWED_AUTHORITY_CLASSES,
    CANONICAL_STATES,
    INITIAL_STATE,
    STANDARD_TRANSITIONS,
    StateTransition,
    TERMINAL_STATES,
    find_transition,
    transitions_for,
)


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
STANDARD_YAML = PROJECT_ROOT / ".ai" / "graphs" / "standard.yaml"


# ─────────── canonical state catalog ───────────


def test_canonical_states_is_frozenset() -> None:
    assert isinstance(CANONICAL_STATES, frozenset)


def test_canonical_states_non_empty() -> None:
    assert len(CANONICAL_STATES) >= 9


def test_canonical_states_contains_phase4_minimum() -> None:
    minimum = {"READY", "THINK", "SANDBOX", "DO", "VERIFIED", "PROMOTED", "DEPLOYED", "RETRO", "DONE"}
    missing = minimum - CANONICAL_STATES
    assert not missing, f"CANONICAL_STATES missing Phase 4 minimum: {missing}"


def test_initial_state_in_canonical_states() -> None:
    assert INITIAL_STATE in CANONICAL_STATES


def test_initial_state_is_ready() -> None:
    assert INITIAL_STATE == "READY"


def test_terminal_states_subset_of_canonical() -> None:
    assert TERMINAL_STATES.issubset(CANONICAL_STATES)


def test_terminal_states_includes_done_and_dead() -> None:
    assert {"DONE", "DEAD"} == TERMINAL_STATES


# ─────────── authority closure ───────────


def test_allowed_authority_classes_is_frozenset() -> None:
    assert isinstance(ALLOWED_AUTHORITY_CLASSES, frozenset)


def test_allowed_authority_classes_exactly_four() -> None:
    assert ALLOWED_AUTHORITY_CLASSES == {"kernel", "verifier", "policy", "human"}


# ─────────── StateTransition dataclass ───────────


def test_state_transition_is_frozen_dataclass() -> None:
    fields = {f.name for f in dataclasses.fields(StateTransition)}
    required = {"from_state", "to_state", "trigger", "decided_by", "require_human_approval", "notes"}
    assert required.issubset(fields)
    # frozen=True — instances are hashable
    t = StateTransition(from_state="READY", to_state="THINK", trigger="sss", decided_by="kernel")
    hash(t)  # MUST NOT raise


def test_state_transition_rejects_unknown_from_state() -> None:
    with pytest.raises(ValueError):
        StateTransition(from_state="NONSENSE", to_state="THINK", trigger="x", decided_by="kernel")


def test_state_transition_rejects_unknown_to_state() -> None:
    with pytest.raises(ValueError):
        StateTransition(from_state="READY", to_state="NONSENSE", trigger="x", decided_by="kernel")


def test_state_transition_rejects_unknown_decided_by() -> None:
    with pytest.raises(ValueError):
        StateTransition(from_state="READY", to_state="THINK", trigger="x", decided_by="self")


# ─────────── STANDARD_TRANSITIONS catalog ───────────


def test_standard_transitions_has_at_least_8_rows() -> None:
    assert len(STANDARD_TRANSITIONS) >= 8


def test_standard_transitions_all_use_canonical_states() -> None:
    for t in STANDARD_TRANSITIONS:
        assert t.from_state in CANONICAL_STATES, t
        assert t.to_state in CANONICAL_STATES, t


def test_standard_transitions_all_use_allowed_authority() -> None:
    for t in STANDARD_TRANSITIONS:
        assert t.decided_by in ALLOWED_AUTHORITY_CLASSES, t


def test_standard_transitions_t1_t8_canonical_order() -> None:
    """Spec §3.1 T1..T8 are the canonical ritual lifecycle. Assert the first
    8 rows form the closed cycle READY→THINK→SANDBOX→DO→VERIFIED→PROMOTED→
    DEPLOYED→RETRO→DONE without gaps."""
    expected_sequence = [
        ("READY", "THINK", "sss"),
        ("THINK", "SANDBOX", "nnn_pass"),
        ("SANDBOX", "DO", "vvv_pass"),
        ("DO", "VERIFIED", "gogogo_complete"),
        ("VERIFIED", "PROMOTED", "promote_request"),
        ("PROMOTED", "DEPLOYED", "deploy_request"),
        ("DEPLOYED", "RETRO", "rrr"),
        ("RETRO", "DONE", "rrr_complete"),
    ]
    actual = [(t.from_state, t.to_state, t.trigger) for t in STANDARD_TRANSITIONS[:8]]
    assert actual == expected_sequence, (
        f"T1-T8 sequence drift:\n  expected {expected_sequence}\n  actual   {actual}"
    )


def test_human_transitions_carry_require_human_approval() -> None:
    """Article XIII: human-decided transitions MUST be marked
    require_human_approval=True so future verifier-rules can enforce ddd-gate
    presence on them."""
    for t in STANDARD_TRANSITIONS:
        if t.decided_by == "human":
            assert t.require_human_approval, (
                f"{t.from_state}→{t.to_state} decided_by=human "
                f"but require_human_approval=False"
            )


# ─────────── transitions_for / find_transition helpers ───────────


def test_transitions_for_ready_returns_t1() -> None:
    out = transitions_for("READY")
    assert len(out) == 1
    assert out[0].to_state == "THINK"


def test_transitions_for_terminal_state_returns_empty() -> None:
    assert transitions_for("DONE") == []
    assert transitions_for("DEAD") == []


def test_find_transition_canonical_lookup() -> None:
    t = find_transition("VERIFIED", "promote_request")
    assert t is not None
    assert t.to_state == "PROMOTED"
    assert t.decided_by == "human"


def test_find_transition_returns_none_on_unknown_trigger() -> None:
    assert find_transition("VERIFIED", "nonsense_trigger") is None


# ─────────── yaml-vs-Python parity (load-bearing) ───────────


def test_yaml_transitions_subset_of_standard_transitions() -> None:
    """Every transition row declared in `.ai/graphs/standard.yaml` MUST be
    represented by a matching row in STANDARD_TRANSITIONS. The yaml is the
    runtime source of truth; the Python list mirrors it.

    Permitted asymmetry: STANDARD_TRANSITIONS MAY declare additional
    spec-pinned but not-yet-implemented rows (e.g. T9 close). The reverse —
    yaml declares a row the Python catalog hasn't yet — is a drift bug.
    """
    if not STANDARD_YAML.exists():
        pytest.skip(f"standard.yaml not found at {STANDARD_YAML}")
    doc = yaml.safe_load(STANDARD_YAML.read_text(encoding="utf-8"))
    yaml_keys = {
        (t["from"], t["to"], t["trigger"]) for t in doc.get("transitions", [])
    }
    py_keys = {
        (t.from_state, t.to_state, t.trigger) for t in STANDARD_TRANSITIONS
    }
    missing = yaml_keys - py_keys
    assert not missing, (
        f"standard.yaml has transition rows missing in STANDARD_TRANSITIONS "
        f"(Python catalog drift): {sorted(missing)}"
    )


def test_yaml_states_match_canonical_states() -> None:
    """All states declared in `.ai/graphs/standard.yaml` MUST exist in
    CANONICAL_STATES."""
    if not STANDARD_YAML.exists():
        pytest.skip(f"standard.yaml not found at {STANDARD_YAML}")
    doc = yaml.safe_load(STANDARD_YAML.read_text(encoding="utf-8"))
    yaml_states = set(doc.get("states", []))
    missing = yaml_states - CANONICAL_STATES
    assert not missing, (
        f"standard.yaml declares states absent from CANONICAL_STATES: {missing}"
    )


def test_yaml_initial_state_matches_constant() -> None:
    if not STANDARD_YAML.exists():
        pytest.skip(f"standard.yaml not found at {STANDARD_YAML}")
    doc = yaml.safe_load(STANDARD_YAML.read_text(encoding="utf-8"))
    assert doc.get("initial_state") == INITIAL_STATE
