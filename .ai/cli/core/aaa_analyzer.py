"""aaa — read-only amendment-loop router + evidence-adoption KPI (Q24.10 step 5).

Closes the loop built in steps 1-4: it READS the session's signals and tells
the operator which amendment command to go back to. It never mutates state,
never fires a transition, never enforces — gating stays with rrr/gogogo.

Route priority (deterministic, operator-locked 2026-06-13 — first match wins):
  1. unconfirmed goal answers        -> vvv --amend   (or vvv --confirm)
  2. missing executable acceptance   -> nnn --amend
  3. high-risk step w/o verify.command -> nnn --amend  (add the binding first)
  4. verify present but evidence failed -> gogogo --fix (re-run the step)
  5. other blocking debt             -> human         (rrr --accept-debt waiver)
  6. nothing                         -> clean         (no route)

KPI is SESSION-SCOPE only (no fleet/global aggregation); every payload
carries kpi_scope so a reader can never mistake it for a global number
(lesson Q24.9).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from . import debt as debt_mod
from . import plan_version
from .risk_classifier import evaluate_evidence_gate

_STEP_EVENTS = {"gogogo.step_passed", "gogogo.step_failed"}


def _session_events(project_root: Path, session_id: str) -> List[Dict[str, Any]]:
    f = project_root / ".ai" / "audit" / "events.ndjson"
    out = []
    if not f.exists():
        return out
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            ev = json.loads(ln)
        except json.JSONDecodeError:
            continue
        d = ev.get("details", ev)
        if (ev.get("session_id") or d.get("session_id")) == session_id:
            out.append(ev)
    return out


def _read_signal(session_path: Path) -> Dict[str, Any]:
    p = session_path / ".state" / "goal_contract_signal.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def compute_kpi(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Session-scope evidence KPIs from gogogo step verdict events."""
    steps = [
        (e.get("details", e))
        for e in events
        if e.get("type") in _STEP_EVENTS and "evidence_mode" in e.get("details", e)
    ]
    total = len(steps)
    evidence = sum(1 for d in steps if d.get("evidence_mode") == "evidence_command")
    structural = sum(1 for d in steps if d.get("structural_pass") is True)
    high_no_ev = sum(
        1
        for d in steps
        if d.get("risk_level") == "high" and not d.get("evidence_command_present")
    )
    rate = (lambda num: round(num / total, 4) if total else 0.0)
    return {
        "steps_measured": total,
        "evidence_command_adoption_rate": rate(evidence),
        "structural_pass_rate": rate(structural),
        "high_risk_without_evidence_count": high_no_ev,
    }


def _high_risk_without_verify(session_path: Path) -> bool:
    try:
        plan = plan_version.resolve_active_plan(session_path)
    except FileNotFoundError:
        return False
    for step in plan.get("steps", []):
        if isinstance(step, dict) and evaluate_evidence_gate(step)["action"] == "needs_human":
            return True
    return False


def _evidence_failed(events: List[Dict[str, Any]]) -> bool:
    for e in events:
        if e.get("type") == "gogogo.step_failed":
            d = e.get("details", e)
            if d.get("verifier_mode") == "evidence_command":
                return True
    return False


def analyze(session_path: Path, project_root: Path) -> Dict[str, Any]:
    """Return {verdict, route, reasons[], kpi{}, kpi_scope{}} — read-only."""
    session_id = session_path.name
    events = _session_events(project_root, session_id)
    signal = _read_signal(session_path)
    acceptance_yaml = session_path / "THINK" / "03_ACCEPTANCE.yaml"

    reasons: List[str] = []
    route = None

    # Deterministic route priority — first match wins.
    if signal.get("has_unconfirmed_answers"):
        route = "vvv --amend"
        qs = signal.get("unconfirmed_questions", [])
        reasons.append(f"goal contract has unconfirmed answers: {qs}")
    elif not acceptance_yaml.exists():
        route = "nnn --amend"
        reasons.append("no executable acceptance (THINK/03_ACCEPTANCE.yaml missing)")
    elif _high_risk_without_verify(session_path):
        route = "nnn --amend"
        reasons.append("high-risk plan step has no verify.command (add evidence binding)")
    elif _evidence_failed(events):
        route = "gogogo --fix"
        reasons.append("a step's verify.command evidence failed")
    else:
        blocking = debt_mod.blocking_debts(session_path)
        # unconfirmed-goal debt is already covered above; any *other* blocking
        # debt routes to a human closure decision.
        other = [d for d in blocking if d.get("type") != "unconfirmed_goal_answers"]
        if other:
            route = "human"
            reasons.append(f"blocking debt requires a closure decision: {[d['type'] for d in other]}")

    verdict = "RETRY" if route else "clean"

    return {
        "verdict": verdict,
        "route": route,
        "reasons": reasons,
        "kpi": compute_kpi(events),
        "kpi_scope": {
            "level": "session",
            "session_id": session_id,
            "project": project_root.name,
            "source": "audit_events",
        },
    }
