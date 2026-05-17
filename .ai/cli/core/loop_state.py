"""Loop state — checkpoint / resume support for `ai loop`.

Spec: docs/specs/03_GOAL_LOOP_SPEC.md §3.1.

Persists per-session at `<session>/loop_state.json`. Companion to
`goals.yaml` (the goal tree). The split is intentional:
  - `goals.yaml`     — the *what*: tree topology + per-goal status
  - `loop_state.json` — the *where am I*: cursor + iteration count +
                        checkpoints
This keeps audit boundaries clean: goal tree mutations are reasoned
about per-goal; loop cursor advances are reasoned about per-tick.
"""
from __future__ import annotations

import datetime
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@dataclass
class Checkpoint:
    id: str                            # ckpt_001, ckpt_002, ...
    ts: str
    goal_id: Optional[str]
    phase: str
    label: Optional[str] = None        # human-supplied note


@dataclass
class LoopState:
    session_id: str
    started_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    current_goal: Optional[str] = None
    current_phase: str = "IDLE"
    iteration: int = 0
    max_iterations: int = 50
    last_verdict: Optional[str] = None
    last_verdict_ts: Optional[str] = None
    checkpoints: List[Checkpoint] = field(default_factory=list)

    # ─── persistence ───

    @staticmethod
    def path_for(session_path: Path) -> Path:
        return session_path / "loop_state.json"

    @classmethod
    def load(cls, session_path: Path) -> "LoopState":
        p = cls.path_for(session_path)
        if not p.exists():
            raise FileNotFoundError(f"loop_state.json missing: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("version") != SCHEMA_VERSION:
            raise ValueError(
                f"loop_state.json schema_version {data.get('version')!r} "
                f"!= {SCHEMA_VERSION}"
            )
        ckpts = [Checkpoint(**c) for c in (data.get("checkpoints") or [])]
        return cls(
            session_id=data["session_id"],
            started_at=data.get("started_at") or _now(),
            updated_at=data.get("updated_at") or _now(),
            current_goal=data.get("current_goal"),
            current_phase=data.get("current_phase") or "IDLE",
            iteration=int(data.get("iteration", 0)),
            max_iterations=int(data.get("max_iterations", 50)),
            last_verdict=data.get("last_verdict"),
            last_verdict_ts=data.get("last_verdict_ts"),
            checkpoints=ckpts,
        )

    def save(self, session_path: Path) -> Path:
        self.updated_at = _now()
        p = self.path_for(session_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return p

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": SCHEMA_VERSION,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "current_goal": self.current_goal,
            "current_phase": self.current_phase,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "last_verdict": self.last_verdict,
            "last_verdict_ts": self.last_verdict_ts,
            "checkpoints": [asdict(c) for c in self.checkpoints],
        }

    # ─── operations ───

    def tick(
        self,
        *,
        goal_id: Optional[str] = None,
        phase: Optional[str] = None,
        verdict: Optional[str] = None,
    ) -> None:
        """Advance the cursor; called once per loop iteration."""
        self.iteration += 1
        if goal_id is not None:
            self.current_goal = goal_id
        if phase is not None:
            self.current_phase = phase
        if verdict is not None:
            self.last_verdict = verdict
            self.last_verdict_ts = _now()

    def add_checkpoint(self, label: Optional[str] = None) -> Checkpoint:
        seq = len(self.checkpoints) + 1
        ckpt = Checkpoint(
            id=f"ckpt_{seq:03d}",
            ts=_now(),
            goal_id=self.current_goal,
            phase=self.current_phase,
            label=label,
        )
        self.checkpoints.append(ckpt)
        return ckpt

    def latest_checkpoint(self) -> Optional[Checkpoint]:
        return self.checkpoints[-1] if self.checkpoints else None
