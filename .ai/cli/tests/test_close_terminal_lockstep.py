"""G11 lock-step — close terminal vocabulary derives from the canonical graph.

Guards the doctrine fix (session close-P0-safety, 2026-06-14):
  - graph (graphs/standard.yaml `terminal_states`) is the SINGLE source.
  - close.py gate + close_contract.py must NOT keep an independent literal.
  - FAILED / ABORTED / SEALED must not appear as graph terminal states in
    the contract surface (they are attempt outcomes / archive metadata).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from cli.core.terminal_states import (
    get_terminal_states_for_close,
    TerminalStatesError,
)

# test file: <root>/.ai/cli/tests/<this>  ->  parents[3] == <root> (trinity_v2)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
_GRAPH = PROJECT_ROOT / ".ai" / "graphs" / "standard.yaml"
_CLOSE_PY = PROJECT_ROOT / ".ai" / "cli" / "commands" / "close.py"
_CONTRACT = PROJECT_ROOT / ".ai" / "rituals" / "close" / "ritual.contract.json"

_GHOST_WORDS = ("FAILED", "ABORTED", "SEALED")


def _graph_terminals() -> frozenset:
    data = yaml.safe_load(_GRAPH.read_text(encoding="utf-8"))
    return frozenset(data["terminal_states"])


# ─────────── lock-step: helper == graph ───────────


def test_lockstep_close_terminal_matches_graph() -> None:
    """The helper returns exactly the graph's terminal_states (== {DONE,DEAD})."""
    helper = get_terminal_states_for_close(PROJECT_ROOT)
    graph = _graph_terminals()
    assert helper == graph
    assert helper == frozenset({"DONE", "DEAD"})


# ─────────── no independent literal source in close.py ───────────


def test_no_literal_source() -> None:
    """close.py must not hard-code a {"DONE","DEAD"} set literal (helper-only)."""
    src = _CLOSE_PY.read_text(encoding="utf-8")
    literal = re.compile(r"""\{\s*["']DONE["']\s*,\s*["']DEAD["']\s*\}""")
    assert literal.search(src) is None, (
        "close.py still contains an independent {'DONE','DEAD'} literal — "
        "the gate must derive terminal states from get_terminal_states_for_close()"
    )


# ─────────── two-layer model (Option 3, operator decision 2026-06-14) ───────────
#
# ritual.contract.json INTENTIONALLY keeps a CONCEPTUAL close/ratification
# envelope (DONE/FAILED/ABORTED -> SEALED, Article XII.5, guarded by
# test_close_loader.py). That is NOT drift. The rule we enforce is layer
# SEPARATION: the conceptual envelope must be labelled as such and must never
# feed the PHYSICAL terminal gate (which is graph-derived DONE/DEAD only).


def test_contract_labels_conceptual() -> None:
    """The contract must explicitly mark its close states as a conceptual,
    non-graph layer (so a future reader does not mistake them for graph
    terminal states). The label lives in `purpose` because the contract
    schema (.ai/schemas/ritual_contract.schema.json) is additionalProperties:
    false and forbidden to edit — no new top-level field is allowed."""
    contract = json.loads(_CONTRACT.read_text(encoding="utf-8"))
    purpose = (contract.get("purpose") or "").lower()
    assert "conceptual" in purpose, "purpose must label close states conceptual"
    assert "graphs/standard.yaml" in purpose, (
        "purpose must point the physical terminal source at the graph"
    )
    assert "not" in purpose and "graph state" in purpose, (
        "purpose must state these conceptual states are NOT graph states"
    )


def test_physical_gate_excludes_conceptual() -> None:
    """The physical terminal gate (helper) must never surface conceptual-only
    words (FAILED/ABORTED/SEALED) — the two layers must not bleed."""
    physical = get_terminal_states_for_close(PROJECT_ROOT)
    assert physical.isdisjoint(frozenset(_GHOST_WORDS)), (
        f"physical terminal gate leaked conceptual words: "
        f"{sorted(physical & frozenset(_GHOST_WORDS))}"
    )


def test_no_new_graph_state() -> None:
    """No new graph state introduced — SEALED stays out of the graph; the
    graph remains the canonical 9-state machine with terminals {DONE,DEAD}."""
    data = yaml.safe_load(_GRAPH.read_text(encoding="utf-8"))
    states = set(data["states"])
    assert "SEALED" not in states, "SEALED must NOT be a graph state"
    assert _graph_terminals() == frozenset({"DONE", "DEAD"})


# ─────────── fail-loud (no silent fallback) ───────────


def test_helper_fail_loud_on_missing_terminal(tmp_path: Path) -> None:
    """A graph with no terminal_states must raise, never return a literal."""
    ai = tmp_path / ".ai" / "graphs"
    ai.mkdir(parents=True)
    (ai / "standard.yaml").write_text(
        "name: standard\nstates: [READY]\ninitial_state: READY\n"
        "transitions: []\n",
        encoding="utf-8",
    )
    # NOTE: resolve_ai_resource falls back to kernel source when the project
    # copy is absent; here the project copy EXISTS but lacks terminal_states,
    # so the project file is used and the helper must fail loud.
    try:
        result = get_terminal_states_for_close(tmp_path)
    except TerminalStatesError:
        return  # expected
    raise AssertionError(
        f"expected TerminalStatesError on missing terminal_states, got {result!r}"
    )
