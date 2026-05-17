"""Trinity Goal Loop — graph engine.

Spec ref: docs/specs/04_GRAPH_SPEC.md (state machine + transition authority)
          docs/specs/03_GOAL_LOOP_SPEC.md (loop drives graph)
          Decision D9 (audit chain), D10 (decided_by enforcement).

Loads `<project_root>/.ai/graphs/<graph_name>.yaml` and exposes a `Loop` class
whose `fire(trigger, decided_by, evidence)` method enforces:

  - the (current_state, trigger) pair maps to a declared transition
  - the caller-claimed `decided_by` matches the transition's authority (D10)

Each successful fire() updates `session_state.json:graph_state` (merge-safe;
F5 lesson) and appends exactly one `graph.transition` event to the audit
chain (D9). No batch appends, no implicit transitions.

Engine is schema-agnostic: it walks `transitions[]` and validates required
keys, so future graphs (`deploy.yaml`, `seo.yaml`) work without code changes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .audit import AuditChain
from .state import SessionLocalState


class LoopError(Exception):
    """Base for loop/graph engine failures."""


class TransitionNotFound(LoopError):
    """No declared transition matches the (state, trigger) pair."""


class DecidedByMismatch(LoopError):
    """Caller's claimed authority differs from the transition's decided_by."""


class GraphInvalid(LoopError):
    """Graph YAML failed schema validation."""


class SubgraphError(LoopError):
    """Sub-graph composition failed (cycle, terminal mismatch, etc.)."""


VALID_AUTHORITIES = {"verifier", "policy", "human", "kernel"}


class Loop:
    """Drive a session through a graph YAML, one transition at a time."""

    def __init__(
        self,
        session_path: Path,
        graph_name: str = "standard",
        project_root: Optional[Path] = None,
        chain: Optional[AuditChain] = None,
    ):
        self.session_path = Path(session_path)
        self.graph_name = graph_name
        self.project_root = (
            Path(project_root)
            if project_root
            else self._infer_project_root(self.session_path)
        )
        self.state = SessionLocalState(self.session_path)
        self.chain = chain or AuditChain(
            self.project_root / ".ai" / "audit" / "events.ndjson"
        )
        # Phase 6 — if a sub-graph stack is persisted, the active graph
        # at __init__ time may differ from `graph_name` (the constructor
        # arg names the *initial* / outer graph; sub-graph state from
        # session_state.json wins on reload). Track the outermost
        # graph_name in `_outermost_graph_name` so exit_subgraph can
        # restore it after the stack empties.
        self._outermost_graph_name = graph_name
        active = self.state.active_graph()
        if active:
            self.graph_name = active
        self.graph = self._load_graph()
        self._validate_graph()
        self._index = self._build_index()
        self._reconcile_from_audit()

    @staticmethod
    def _infer_project_root(session_path: Path) -> Path:
        # Conventional layout: <project_root>/.ai/sessions/<session_id>
        return session_path.parent.parent.parent

    def _load_graph(self) -> Dict[str, Any]:
        graph_path = (
            self.project_root / ".ai" / "graphs" / f"{self.graph_name}.yaml"
        )
        if not graph_path.exists():
            raise GraphInvalid(f"graph not found: {graph_path}")
        with graph_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise GraphInvalid(f"graph must be a mapping: {graph_path}")
        return data

    def _validate_graph(self) -> None:
        g = self.graph
        for key in ("name", "states", "initial_state", "transitions"):
            if key not in g:
                raise GraphInvalid(f"graph missing key: {key!r}")
        if not isinstance(g["transitions"], list) or not g["transitions"]:
            raise GraphInvalid("graph 'transitions' must be a non-empty list")
        if g["initial_state"] not in g["states"]:
            raise GraphInvalid(
                f"initial_state {g['initial_state']!r} not in states"
            )
        for i, t in enumerate(g["transitions"]):
            for key in ("from", "to", "trigger", "decided_by"):
                if key not in t:
                    raise GraphInvalid(
                        f"transition #{i}: missing {key!r} (D10 violation)"
                    )
            if t["decided_by"] not in VALID_AUTHORITIES:
                raise GraphInvalid(
                    f"transition #{i}: decided_by {t['decided_by']!r} "
                    f"not in {VALID_AUTHORITIES}"
                )
            if t["from"] != "ANY" and t["from"] not in g["states"]:
                raise GraphInvalid(
                    f"transition #{i}: from-state {t['from']!r} not declared"
                )
            if t["to"] not in g["states"]:
                raise GraphInvalid(
                    f"transition #{i}: to-state {t['to']!r} not declared"
                )

    def _build_index(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        idx: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for i, t in enumerate(self.graph["transitions"]):
            key = (t["from"], t["trigger"])
            if key in idx:
                raise GraphInvalid(
                    f"transition #{i}: conflicting trigger for "
                    f"state={t['from']!r}, trigger={t['trigger']!r}"
                )
            idx[key] = t
        return idx

    def current(self) -> str:
        return self.state.graph_state(default=self.graph["initial_state"])

    def fire(
        self,
        trigger: str,
        decided_by: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Apply a transition; raise on missing match or wrong authority."""
        cur = self.current()
        # Try state-specific match first; fall back to ANY (e.g. policy_violation)
        transition = self._index.get((cur, trigger)) or self._index.get(
            ("ANY", trigger)
        )
        if transition is None:
            raise TransitionNotFound(
                f"no transition for state={cur!r} trigger={trigger!r} "
                f"in graph {self.graph_name!r}"
            )
        expected = transition["decided_by"]
        if decided_by != expected:
            raise DecidedByMismatch(
                f"transition {cur} -> {transition['to']} via {trigger!r} "
                f"requires decided_by={expected!r}, got {decided_by!r}"
            )
        new_state = transition["to"]
        self._set_graph_state(new_state)
        self.chain.append(
            "graph.transition",
            {
                "session_id": self.session_path.name,
                "graph": self.graph_name,
                "from_state": cur,
                "to_state": new_state,
                "trigger": trigger,
                "decided_by": decided_by,
                "evidence": evidence or {},
            },
        )
        return new_state

    def _set_graph_state(self, new_state: str) -> None:
        self.state.set_graph_state(new_state)

    def transitions_from(self, state: str) -> List[Dict[str, Any]]:
        return [t for t in self.graph["transitions"] if t["from"] == state]

    def _reconcile_from_audit(self) -> None:
        """If the audit chain shows a more recent `graph.transition` for
        this session than what `session_state.json` knows, update
        `session_state.json:graph_state`. Audit is source of truth (D9 —
        append-only + hash-chained). Walks chain from tail; early-exits
        on first matching session_id event. (Phase 1 retro R6.)"""
        sid = self.session_path.name
        last_to_state: Optional[str] = None
        for ev in self.chain.iter_events_reversed():
            if ev.get("type") != "graph.transition":
                continue
            if ev.get("details", {}).get("session_id") != sid:
                continue
            last_to_state = ev["details"].get("to_state")
            break
        if last_to_state is None:
            return
        current_recorded = self.state.graph_state()
        if current_recorded != last_to_state:
            self.state.set_graph_state(last_to_state)

    def is_terminal(self, state: Optional[str] = None) -> bool:
        s = state or self.current()
        terminals = self.graph.get("terminal_states", [])
        return s in terminals

    # ─────────── Phase 6: sub-graph composition ───────────

    def current_graph_name(self) -> str:
        """Active graph name (top of sub-graph stack, else this graph)."""
        return self.graph_name

    def subgraph_depth(self) -> int:
        return len(self.state.subgraph_stack())

    def enter_subgraph(
        self,
        inner_graph_name: str,
        *,
        decided_by: str = "kernel",
        evidence: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Push a sub-graph onto the stack.

        The current state of the *outer* graph is recorded as
        `prior_state` so we can restore it on `exit_subgraph`. The
        active graph switches to the inner graph, and graph_state
        becomes the inner graph's `initial_state`.

        Cycles (a graph re-entering its own ancestor) are refused —
        Trinity sub-graphs are a stack, not arbitrary recursion.
        """
        if decided_by not in VALID_AUTHORITIES:
            raise SubgraphError(
                f"enter_subgraph decided_by={decided_by!r} not in {VALID_AUTHORITIES}"
            )
        if inner_graph_name == self.graph_name:
            raise SubgraphError(
                f"refusing to re-enter the active graph {inner_graph_name!r}"
            )
        # Cycle protection: walk the stack — none of the ancestors
        # (the outer_graph of any frame, plus the immediate parent
        # which is the active graph_name) may equal inner_graph_name.
        for frame in self.state.subgraph_stack():
            if (
                frame.get("inner_graph") == inner_graph_name
                or frame.get("outer_graph") == inner_graph_name
            ):
                raise SubgraphError(
                    f"refusing to enter sub-graph {inner_graph_name!r}: "
                    f"already on the stack (cycle)"
                )

        prior_state = self.current()
        prior_graph = self.graph_name

        # Switch graphs
        self.state.push_subgraph(
            outer_graph=prior_graph,
            outer_state=prior_state,
            inner_graph=inner_graph_name,
        )
        self.graph_name = inner_graph_name
        self.graph = self._load_graph()
        self._validate_graph()
        self._index = self._build_index()

        new_state = self.graph["initial_state"]
        self._set_graph_state(new_state)

        self.chain.append(
            "loop.subgraph.entered",
            {
                "session_id": self.session_path.name,
                "outer_graph": prior_graph,
                "outer_state": prior_state,
                "inner_graph": inner_graph_name,
                "inner_state": new_state,
                "decided_by": decided_by,
                "evidence": evidence or {},
            },
        )
        return new_state

    def exit_subgraph(
        self,
        *,
        decided_by: str = "kernel",
        evidence: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> str:
        """Pop the top sub-graph frame and restore the outer graph.

        Refuses to pop unless the inner graph is at a terminal state
        (so the workflow has actually completed). `force=True` bypasses
        the terminal check — use only for cancellations / errors with
        a recorded reason.
        """
        if decided_by not in VALID_AUTHORITIES:
            raise SubgraphError(
                f"exit_subgraph decided_by={decided_by!r} not in {VALID_AUTHORITIES}"
            )
        stack = self.state.subgraph_stack()
        if not stack:
            raise SubgraphError("not in a sub-graph; nothing to exit")
        if not force and not self.is_terminal():
            raise SubgraphError(
                f"sub-graph {self.graph_name!r} state {self.current()!r} "
                f"is not terminal; pass force=True to exit anyway"
            )

        frame = self.state.pop_subgraph()
        if frame is None:
            raise SubgraphError("pop_subgraph returned no frame (race?)")
        inner_graph = self.graph_name
        inner_terminal_state = self.current()

        # Restore the outer graph
        outer_graph = frame.get("outer_graph") or self._outermost_graph_name
        outer_state = frame.get("outer_state") or None

        self.graph_name = outer_graph
        self.graph = self._load_graph()
        self._validate_graph()
        self._index = self._build_index()
        if outer_state is None:
            outer_state = self.graph["initial_state"]
        self._set_graph_state(outer_state)

        self.chain.append(
            "loop.subgraph.exited",
            {
                "session_id": self.session_path.name,
                "inner_graph": inner_graph,
                "inner_terminal_state": inner_terminal_state,
                "outer_graph": self.graph_name,
                "outer_state": outer_state,
                "decided_by": decided_by,
                "forced": bool(force),
                "evidence": evidence or {},
            },
        )
        return outer_state
