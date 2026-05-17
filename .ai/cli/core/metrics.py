"""Phase 1.5 — session metrics computed from the audit chain.

Spec ref: .ai/shims/rrr/SHIM.md step 2 (compute and surface session
          metrics from audit events)
          docs/specs/03_GOAL_LOOP_SPEC.md §3.1 (loop_state schema —
          we compute equivalents from the chain instead of reading
          loop_state.json since chain is source of truth, D9)

Pulls a session's slice of `.ai/audit/events.ndjson` (filtered by
session_id) and aggregates: event count, graph transitions, gogogo
verdicts (PASS/RETRY/NEEDS_HUMAN/DEAD), NEEDS_HUMAN count, wall-clock
duration, and iterations completed.
"""
from __future__ import annotations

import datetime
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .audit import AuditChain


@dataclass
class SessionMetrics:
    session_id: str
    event_count: int = 0
    transition_count: int = 0
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    gogogo_verdict_counts: Dict[str, int] = field(default_factory=dict)
    needs_human_count: int = 0
    iterations: int = 0
    first_event_ts: Optional[str] = None
    last_event_ts: Optional[str] = None
    duration_seconds: Optional[float] = None
    final_graph_state: Optional[str] = None


def metrics_for_session(
    chain: AuditChain, session_id: str
) -> SessionMetrics:
    """Walk the chain, filter to events whose details.session_id matches,
    and aggregate."""
    m = SessionMetrics(session_id=session_id)
    verdict_counts: Counter = Counter()

    for ev in chain.iter_events():
        details = ev.get("details") or {}
        if details.get("session_id") != session_id:
            continue
        m.event_count += 1
        ts = ev.get("ts")
        if ts:
            if m.first_event_ts is None:
                m.first_event_ts = ts
            m.last_event_ts = ts

        ev_type = ev.get("type")
        if ev_type == "graph.transition":
            m.transition_count += 1
            m.transitions.append(
                {
                    "from": details.get("from_state"),
                    "to": details.get("to_state"),
                    "trigger": details.get("trigger"),
                    "decided_by": details.get("decided_by"),
                    "ts": ts,
                }
            )
            m.final_graph_state = details.get("to_state")
        elif ev_type in ("gogogo.step_passed", "gogogo.step_failed"):
            verdict = details.get("verifier_verdict")
            if verdict:
                verdict_counts[verdict] += 1
            m.iterations += 1
        elif ev_type == "loop.budget.breach":
            m.needs_human_count += 1

    m.gogogo_verdict_counts = dict(verdict_counts)
    m.needs_human_count += verdict_counts.get("NEEDS_HUMAN", 0)

    if m.first_event_ts and m.last_event_ts:
        try:
            t0 = _parse_iso(m.first_event_ts)
            t1 = _parse_iso(m.last_event_ts)
            m.duration_seconds = (t1 - t0).total_seconds()
        except ValueError:
            m.duration_seconds = None
    return m


def _parse_iso(s: str) -> datetime.datetime:
    # Audit chain uses Z suffix; Python 3.9 datetime.fromisoformat doesn't
    # accept Z directly until 3.11. Normalize.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(s)
