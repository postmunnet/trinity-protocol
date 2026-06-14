"""Single source of truth for close-eligible terminal states.

Doctrine (locked 2026-06-14, session close-P0-safety):
  - close is a Seal/Archive layer; it consumes terminal graph states only.
  - The canonical terminal vocabulary lives in graphs/<name>.yaml
    `terminal_states` — NOT a hand-maintained literal scattered across
    close.py / close_contract.py / ritual.contract.json.
  - FAILED / ABORTED are close-attempt outcomes; SEALED is archive
    metadata. None of them are graph terminal states.

This module derives the close terminal set from the canonical graph and is
FAIL-LOUD: if the graph cannot be read, is malformed, or does not declare
the required close terminals, it raises. It MUST NOT silently fall back to a
literal {"DONE", "DEAD"} — a silent fallback would make the G11 lock-step
test pass while the drift it guards against still exists.
"""
from __future__ import annotations

from pathlib import Path
from typing import FrozenSet

import yaml

from .kernel_resource import resolve_ai_resource

# Required close terminals. The graph MUST declare at least these; the helper
# returns exactly the graph's terminal_states (which today == this set).
_REQUIRED_CLOSE_TERMINALS = frozenset({"DONE", "DEAD"})

# Words that are close-attempt outcomes / archive metadata, never graph
# terminal states. If the graph ever lists one of these as terminal, that is
# a doctrine violation and we fail loud rather than seal against it.
_NON_GRAPH_OUTCOME_WORDS = frozenset({"FAILED", "ABORTED", "SEALED"})


class TerminalStatesError(RuntimeError):
    """Raised when canonical close terminal states cannot be derived.

    Fail-loud sentinel — callers must not swallow this into a literal default.
    """


def get_terminal_states_for_close(
    project_root: Path, graph_name: str = "standard"
) -> FrozenSet[str]:
    """Return the terminal graph states a close may seal, derived from the graph.

    Raises TerminalStatesError on any of:
      - graph file not found (thin-client fallback already attempted),
      - graph unreadable / not a mapping,
      - graph declares no terminal_states,
      - graph omits a required close terminal (DONE/DEAD),
      - graph lists a non-graph outcome word (FAILED/ABORTED/SEALED) as terminal.
    """
    path, source = resolve_ai_resource(
        project_root,
        f"graphs/{graph_name}.yaml",
        label=f"graph:{graph_name}",
        quiet=True,
    )
    if path is None:
        raise TerminalStatesError(
            f"cannot derive close terminal states: graph {graph_name!r} "
            f"not found (source={source})"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:  # malformed YAML / IO
        raise TerminalStatesError(f"cannot parse graph {path}: {e}") from e
    if not isinstance(data, dict):
        raise TerminalStatesError(f"graph {path} is not a mapping")
    terminals = data.get("terminal_states")
    if not isinstance(terminals, list) or not terminals:
        raise TerminalStatesError(
            f"graph {path} declares no terminal_states (got {terminals!r})"
        )
    result = frozenset(str(s) for s in terminals)
    missing = _REQUIRED_CLOSE_TERMINALS - result
    if missing:
        raise TerminalStatesError(
            f"graph {graph_name} terminal_states missing required close "
            f"terminals: {sorted(missing)} (has {sorted(result)})"
        )
    smuggled = _NON_GRAPH_OUTCOME_WORDS & result
    if smuggled:
        raise TerminalStatesError(
            f"graph {graph_name} terminal_states contains non-graph close "
            f"outcome words: {sorted(smuggled)} — these are attempt "
            f"outcomes/metadata, not graph terminal states"
        )
    return result


__all__ = ["get_terminal_states_for_close", "TerminalStatesError"]
