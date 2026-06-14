"""Trinity Loop Budget — load + check.

Spec ref: docs/specs/03_GOAL_LOOP_SPEC.md §8 (Budget Management).
          Decision D11 (budget breach -> NEEDS_HUMAN escalation).

Loads `<project_root>/.ai/policies/loop-budget.yaml` (read-only; D1 boundary
forbids edits to .ai/policies/**).

Per-graph overrides via `overrides.<graph_name>` and per-plan overrides via
the `budget_override` field of the plan envelope take precedence in this
order:

  loop-budget.yaml: default_budget
  < loop-budget.yaml: overrides[graph_name]
  < plan.json:        budget_override                 (highest)

`Budget.check(plan_envelope, graph_name)` returns a `BudgetVerdict` listing
breaches and any plan-level overrides that consumed an otherwise-breaching
estimate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


CAPS = ("max_iterations", "max_duration_minutes", "max_tool_calls")
CAP_TO_ESTIMATE = {
    "max_iterations": "estimated_iterations",
    "max_duration_minutes": "estimated_duration_minutes",
    "max_tool_calls": "estimated_tool_calls",
}


@dataclass
class BudgetVerdict:
    ok: bool
    breaches: List[Dict[str, Any]] = field(default_factory=list)
    overrides_applied: List[Dict[str, Any]] = field(default_factory=list)


class Budget:
    def __init__(
        self, policy_path: Path, project_root: Optional[Path] = None
    ):
        self.policy_path = Path(policy_path)
        self.project_root = (
            Path(project_root) if project_root else self.policy_path.parents[2]
        )
        self.policy = self._load()

    @classmethod
    def for_project(cls, project_root: Path) -> "Budget":
        return cls(
            policy_path=project_root / ".ai" / "policies" / "loop-budget.yaml",
            project_root=project_root,
        )

    def _load(self) -> Dict[str, Any]:
        path = self.policy_path
        if not path.exists() and self.project_root is not None:
            # Thin-client fallback (P0-3, 2026-06-10): linked projects strip
            # .ai/policies — fall back loudly to the kernel-shipped budget.
            from .kernel_resource import resolve_ai_resource

            fallback, _source = resolve_ai_resource(
                self.project_root, "policies/loop-budget.yaml", label="budget"
            )
            if fallback is not None:
                path = fallback
        if not path.exists():
            raise FileNotFoundError(f"loop-budget not found: {self.policy_path}")
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def effective_caps(self, graph_name: str) -> Dict[str, int]:
        defaults = dict(self.policy.get("default_budget", {}))
        overrides = (self.policy.get("overrides") or {}).get(graph_name, {})
        return {**defaults, **overrides}

    def check(
        self, plan_envelope: Dict[str, Any], graph_name: str = "standard"
    ) -> BudgetVerdict:
        caps = self.effective_caps(graph_name)
        plan_override = plan_envelope.get("budget_override") or {}
        breaches: List[Dict[str, Any]] = []
        applied_overrides: List[Dict[str, Any]] = []
        for cap in CAPS:
            est_key = CAP_TO_ESTIMATE[cap]
            estimate = plan_envelope.get(est_key)
            if estimate is None:
                continue
            cap_value = caps.get(cap)
            if cap_value is None:
                continue
            override_value = plan_override.get(cap)
            effective_cap = override_value if override_value is not None else cap_value
            if estimate > effective_cap:
                breaches.append(
                    {
                        "cap": cap,
                        "limit": effective_cap,
                        "estimate": estimate,
                        "ratio": round(estimate / effective_cap, 2),
                    }
                )
            elif override_value is not None and estimate > cap_value:
                applied_overrides.append(
                    {
                        "cap": cap,
                        "default_limit": cap_value,
                        "override_limit": override_value,
                        "estimate": estimate,
                        "decided_by": plan_override.get("decided_by", "human"),
                        "reason": plan_override.get("reason", ""),
                    }
                )
        return BudgetVerdict(
            ok=not breaches,
            breaches=breaches,
            overrides_applied=applied_overrides,
        )
