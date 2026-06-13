"""Session debt collector for the rrr closure gate (Q24.10 step 3).

A "debt" is unfinished obligation that should block a clean RETRO→DONE
unless the operator explicitly waives it. This module only *collects and
classifies* debt; rrr.py owns the gate decision and the waiver.

Step-3 scope (operator-locked 2026-06-13): exactly ONE active source —
`unconfirmed_goal_answers` (from .state/goal_contract_signal.json written by
vvv step 2). The structure is intentionally extensible (a list of typed
debts) so later sources (e.g. acceptance_skipped) drop in without reshaping
callers — but only this one source is wired now.

Backward-compat invariant: a session with no goal_contract_signal.json is a
legacy/older session and carries NO debt (must never be blocked).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def collect_debts(session_path: Path) -> List[Dict[str, Any]]:
    """Return the list of typed debts for a session (possibly empty).

    Each debt: {type, severity, source, ...detail}. severity 'blocking'
    means rrr must refuse DONE without a waiver.
    """
    debts: List[Dict[str, Any]] = []

    # Source 1 (only active source) — unconfirmed goal answers.
    signal_path = session_path / ".state" / "goal_contract_signal.json"
    if signal_path.exists():
        try:
            signal = json.loads(signal_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            signal = {}
        if signal.get("has_unconfirmed_answers"):
            debts.append({
                "type": "unconfirmed_goal_answers",
                "severity": "blocking",
                "source": ".state/goal_contract_signal.json",
                "questions": signal.get("unconfirmed_questions", []),
            })
    # (no signal file = legacy session = no debt — backward-compat)

    return debts


def blocking_debts(session_path: Path) -> List[Dict[str, Any]]:
    """Subset of collect_debts whose severity is 'blocking'."""
    return [d for d in collect_debts(session_path) if d.get("severity") == "blocking"]


def evaluate_debt_gate(
    session_path: Path, accept_debt: bool, reason: str | None
) -> Dict[str, Any]:
    """Decide what the rrr closure gate should do about session debt.

    Pure decision (no I/O beyond reading the signal, no audit) so it can be
    unit-tested directly. rrr.py performs the audit/return based on `action`:

      action=clean        no blocking debt → proceed to DONE
      action=block        blocking debt + no waiver → refuse (exit 1)
      action=need_reason  --accept-debt given without --reason → fail (exit 2)
      action=waive        --accept-debt + --reason → proceed, record waiver
    """
    blocking = blocking_debts(session_path)
    if not blocking:
        return {"action": "clean", "debts": [], "waiver": None}
    if not accept_debt:
        return {"action": "block", "debts": blocking, "waiver": None}
    if not (reason or "").strip():
        return {"action": "need_reason", "debts": blocking, "waiver": None}
    waiver = {
        "accepted": True,
        "reason": reason.strip(),
        "waiver_source": "explicit_cli_flag",
        "decided_by": "operator_waiver",
    }
    return {"action": "waive", "debts": blocking, "waiver": waiver}


def debt_summary(session_path: Path, waiver: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Machine-readable debt summary for the retro envelope (C10).

    waiver (if a --accept-debt was supplied) is recorded verbatim so reports
    / aaa can distinguish blocked vs waived without re-deriving it.
    """
    debts = collect_debts(session_path)
    return {
        "debts": debts,
        "blocking_count": sum(1 for d in debts if d.get("severity") == "blocking"),
        "waiver": waiver,
    }
