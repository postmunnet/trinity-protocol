"""Goal Tree — hierarchical goal decomposition for the Phase 5 loop.

Spec: docs/specs/03_GOAL_LOOP_SPEC.md §2 (Goal Schema).

A goal tree lives at `.ai/sessions/<session>/goals.yaml`. It is a
flat list of goals plus a `root_goal_id`; parent/child relations are
edges (`parent: <id>` on each non-root goal) so the tree can be
mutated without rewriting deeply nested YAML.

This Phase 5 MVP intentionally implements the tractable subset of
the spec:

  - schema fields covered: id, type, description, parent, status,
    acceptance_criteria, estimated_effort, evidence_required,
    retry_budget, timeout_seconds, created_at, updated_at,
    completed_at, last_verdict
  - status state machine: pending → running → done | blocked |
    needs_human | dead
  - aggregate status: a parent rolls up to `done` once *all*
    children are `done`; `dead` if any child is `dead`; otherwise
    inherits the worst-leaf state
  - cycle protection on add_child / set_parent
  - `list_pending(after=goal_id)` for the Phase 5 `ai loop` resume

What's deliberately NOT here yet:

  - decomposition_strategy=ai (LLM-driven sub-goal generation)
  - dependency edges beyond parent/child
  - context_refs auto-resolution
  - timeline / Gantt / cost estimation
  - LLM-judged aggregation
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import yaml


VALID_STATUSES: Set[str] = {
    "pending", "running", "done", "blocked", "needs_human", "dead"
}
TERMINAL_STATUSES: Set[str] = {"done", "dead"}
VALID_TYPES: Set[str] = {"epic", "feature", "task", "subtask"}

# State machine: from → allowed-to set
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "pending":     {"running", "blocked", "dead"},
    "running":     {"done", "blocked", "needs_human", "dead"},
    "blocked":     {"running", "dead"},
    "needs_human": {"running", "dead"},
    "done":        set(),
    "dead":        set(),
}


class GoalTreeError(Exception):
    pass


@dataclass
class Goal:
    id: str
    type: str
    description: str
    parent: Optional[str] = None
    status: str = "pending"
    acceptance_criteria: List[str] = field(default_factory=list)
    estimated_effort: Dict[str, Any] = field(default_factory=dict)
    evidence_required: Dict[str, Any] = field(default_factory=dict)
    retry_budget: int = 3
    timeout_seconds: int = 1800
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    last_verdict: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "parent": self.parent,
            "status": self.status,
            "acceptance_criteria": list(self.acceptance_criteria),
            "estimated_effort": dict(self.estimated_effort),
            "evidence_required": dict(self.evidence_required),
            "retry_budget": self.retry_budget,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "last_verdict": self.last_verdict,
            "artifacts": list(self.artifacts),
        }
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Goal":
        if "id" not in d or "type" not in d or "description" not in d:
            raise GoalTreeError(
                f"goal record missing required field(s): {sorted(d.keys())}"
            )
        if d["type"] not in VALID_TYPES:
            raise GoalTreeError(
                f"goal {d['id']!r} has invalid type {d['type']!r}; "
                f"must be one of {sorted(VALID_TYPES)}"
            )
        status = d.get("status", "pending")
        if status not in VALID_STATUSES:
            raise GoalTreeError(
                f"goal {d['id']!r} has invalid status {status!r}"
            )
        return cls(
            id=d["id"],
            type=d["type"],
            description=d["description"],
            parent=d.get("parent"),
            status=status,
            acceptance_criteria=list(d.get("acceptance_criteria") or []),
            estimated_effort=dict(d.get("estimated_effort") or {}),
            evidence_required=dict(d.get("evidence_required") or {}),
            retry_budget=int(d.get("retry_budget", 3)),
            timeout_seconds=int(d.get("timeout_seconds", 1800)),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            completed_at=d.get("completed_at"),
            last_verdict=d.get("last_verdict"),
            artifacts=list(d.get("artifacts") or []),
        )


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class GoalTree:
    """In-memory goal tree with on-disk YAML persistence."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        session_id: str,
        root_goal_id: Optional[str] = None,
        goals: Optional[Iterable[Goal]] = None,
    ):
        self.session_id = session_id
        self.root_goal_id = root_goal_id
        self._goals: Dict[str, Goal] = {}
        for g in goals or []:
            self._goals[g.id] = g

    # ─── persistence ───

    @classmethod
    def path_for(cls, session_path: Path) -> Path:
        return session_path / "goals.yaml"

    @classmethod
    def load(cls, session_path: Path) -> "GoalTree":
        p = cls.path_for(session_path)
        if not p.exists():
            raise GoalTreeError(f"goals.yaml missing: {p}")
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if data.get("version") != cls.SCHEMA_VERSION:
            raise GoalTreeError(
                f"goals.yaml schema_version {data.get('version')!r} != "
                f"{cls.SCHEMA_VERSION}"
            )
        goals = [Goal.from_dict(g) for g in (data.get("goals") or [])]
        tree = cls(
            session_id=data.get("session_id") or session_path.name,
            root_goal_id=data.get("root_goal_id"),
            goals=goals,
        )
        tree._validate_topology()
        return tree

    def save(self, session_path: Path) -> Path:
        self._validate_topology()
        p = self.path_for(session_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "version": self.SCHEMA_VERSION,
            "session_id": self.session_id,
            "root_goal_id": self.root_goal_id,
            "goals": [g.to_dict() for g in self._goals.values()],
        }
        p.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return p

    # ─── CRUD ───

    def add_goal(self, goal: Goal, *, set_root: bool = False) -> Goal:
        if goal.id in self._goals:
            raise GoalTreeError(f"goal id {goal.id!r} already exists")
        if goal.parent and goal.parent not in self._goals:
            raise GoalTreeError(
                f"goal {goal.id!r} parent={goal.parent!r} does not exist"
            )
        if goal.parent == goal.id:
            raise GoalTreeError(f"goal {goal.id!r} cannot be its own parent")
        if not goal.created_at:
            goal.created_at = _now()
        goal.updated_at = goal.created_at
        self._goals[goal.id] = goal
        if set_root or self.root_goal_id is None:
            self.root_goal_id = goal.id
        return goal

    def get(self, goal_id: str) -> Goal:
        if goal_id not in self._goals:
            raise GoalTreeError(f"unknown goal id: {goal_id!r}")
        return self._goals[goal_id]

    def all_goals(self) -> List[Goal]:
        return list(self._goals.values())

    def children(self, goal_id: str) -> List[Goal]:
        return [g for g in self._goals.values() if g.parent == goal_id]

    # ─── status mutation ───

    def set_status(
        self, goal_id: str, new_status: str, *, last_verdict: Optional[str] = None
    ) -> Goal:
        g = self.get(goal_id)
        if new_status not in VALID_STATUSES:
            raise GoalTreeError(f"invalid status: {new_status!r}")
        if new_status == g.status:
            return g  # no-op
        allowed = ALLOWED_TRANSITIONS.get(g.status, set())
        if new_status not in allowed:
            raise GoalTreeError(
                f"goal {goal_id!r}: illegal transition "
                f"{g.status!r} → {new_status!r} "
                f"(allowed from {g.status!r}: {sorted(allowed) or '<terminal>'})"
            )
        g.status = new_status
        g.updated_at = _now()
        if last_verdict:
            g.last_verdict = last_verdict
        if new_status in TERMINAL_STATUSES:
            g.completed_at = g.updated_at
        return g

    # ─── aggregation ───

    def aggregate_status(self, goal_id: str) -> str:
        """Compute the rolled-up status for a goal based on its children.

        Rules:
          - any child `dead`           → `dead`
          - all children `done`        → `done`
          - any child `running`        → `running`
          - any child `needs_human`    → `needs_human`
          - any child `blocked`        → `blocked`
          - otherwise                  → `pending`
          - leaf goals return their own status
        """
        g = self.get(goal_id)
        kids = self.children(goal_id)
        if not kids:
            return g.status
        statuses = [self.aggregate_status(k.id) for k in kids]
        if "dead" in statuses:
            return "dead"
        if all(s == "done" for s in statuses):
            return "done"
        if "running" in statuses:
            return "running"
        if "needs_human" in statuses:
            return "needs_human"
        if "blocked" in statuses:
            return "blocked"
        return "pending"

    # ─── queue / resume ───

    def list_pending(self) -> List[Goal]:
        """Leaf goals in `pending` or `running` status, in insertion order."""
        out: List[Goal] = []
        for g in self._goals.values():
            if self.children(g.id):
                continue  # only leaves
            if g.status in ("pending", "running"):
                out.append(g)
        return out

    def next_executable(self) -> Optional[Goal]:
        """First leaf goal whose status is `pending`. Skips `blocked` and
        `needs_human` (those need external resolution)."""
        for g in self._goals.values():
            if self.children(g.id):
                continue
            if g.status == "pending":
                return g
        return None

    # ─── private ───

    def _validate_topology(self) -> None:
        # Every parent reference resolves
        for g in self._goals.values():
            if g.parent and g.parent not in self._goals:
                raise GoalTreeError(
                    f"goal {g.id!r} references missing parent {g.parent!r}"
                )
        if self.root_goal_id and self.root_goal_id not in self._goals:
            raise GoalTreeError(
                f"root_goal_id {self.root_goal_id!r} not in goals list"
            )
        # No cycles (walk parents from each goal up to a root or known ancestor)
        for g in self._goals.values():
            seen: Set[str] = set()
            cur: Optional[str] = g.parent
            while cur is not None:
                if cur in seen or cur == g.id:
                    raise GoalTreeError(f"cycle detected at goal {g.id!r}")
                seen.add(cur)
                cur = self._goals[cur].parent
