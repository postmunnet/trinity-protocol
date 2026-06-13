"""Q24.10 step 3 — debt collector + gate-decision unit tests.

debt.py is the collector/decider; rrr.py owns the audit/return. One active
source only: unconfirmed_goal_answers from goal_contract_signal.json.
"""
from __future__ import annotations

import json

from cli.core import debt


def _write_signal(tmp_path, has_unconfirmed, questions):
    state = tmp_path / ".state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "goal_contract_signal.json").write_text(json.dumps({
        "goal_contract_version": 1,
        "has_unconfirmed_answers": has_unconfirmed,
        "unconfirmed_questions": questions,
    }))


def test_collect_unconfirmed_yields_blocking_debt(tmp_path):
    _write_signal(tmp_path, True, ["q2", "q5"])
    debts = debt.collect_debts(tmp_path)
    assert len(debts) == 1
    assert debts[0]["type"] == "unconfirmed_goal_answers"
    assert debts[0]["severity"] == "blocking"
    assert debts[0]["questions"] == ["q2", "q5"]


def test_collect_confirmed_no_debt(tmp_path):
    _write_signal(tmp_path, False, [])
    assert debt.collect_debts(tmp_path) == []


def test_legacy_no_signal_no_debt(tmp_path):
    # no goal_contract_signal.json at all → legacy session → no debt
    assert debt.collect_debts(tmp_path) == []
    assert debt.blocking_debts(tmp_path) == []


def test_evaluate_gate_clean(tmp_path):
    _write_signal(tmp_path, False, [])
    assert debt.evaluate_debt_gate(tmp_path, False, None)["action"] == "clean"


def test_evaluate_gate_block(tmp_path):
    _write_signal(tmp_path, True, ["q1"])
    g = debt.evaluate_debt_gate(tmp_path, False, None)
    assert g["action"] == "block"
    assert g["debts"][0]["type"] == "unconfirmed_goal_answers"


def test_evaluate_gate_need_reason(tmp_path):
    _write_signal(tmp_path, True, ["q1"])
    g = debt.evaluate_debt_gate(tmp_path, True, None)
    assert g["action"] == "need_reason"
    g2 = debt.evaluate_debt_gate(tmp_path, True, "   ")  # whitespace only
    assert g2["action"] == "need_reason"


def test_evaluate_gate_waive_records_explicit_source(tmp_path):
    _write_signal(tmp_path, True, ["q1"])
    g = debt.evaluate_debt_gate(tmp_path, True, "soak-test deferral")
    assert g["action"] == "waive"
    assert g["waiver"]["reason"] == "soak-test deferral"
    # not overclaiming human authority
    assert g["waiver"]["waiver_source"] == "explicit_cli_flag"
    assert g["waiver"]["decided_by"] == "operator_waiver"


def test_debt_summary_machine_readable(tmp_path):
    _write_signal(tmp_path, True, ["q3"])
    s = debt.debt_summary(tmp_path)
    assert isinstance(s, dict)
    assert s["blocking_count"] == 1
    assert isinstance(s["debts"], list)
    assert s["waiver"] is None
