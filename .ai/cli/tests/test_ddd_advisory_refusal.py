"""S14 ddd advisory refusal tests (PRD Phase 8 line 800)."""
from __future__ import annotations

import inspect

from cli.commands import ddd as ddd_mod


# ─── source-level wire presence ──────────────────────────────────────


def test_ddd_imports_judge_advisory() -> None:
    source = inspect.getsource(ddd_mod)
    assert "verdict_is_advisory_only" in source, (
        "ddd must import verdict_is_advisory_only from judge_advisory"
    )


def test_ddd_emits_advisory_only_refused_event() -> None:
    source = inspect.getsource(ddd_mod)
    assert "ddd.advisory_only_refused" in source


def test_ddd_guards_advisory_check_with_prod_target() -> None:
    """The refusal MUST only fire for target='prod' (dev is permissive)."""
    source = inspect.getsource(ddd_mod)
    # Source contains a guard like `if target == "prod" and not skip_verify:`
    # in the same block as verdict_is_advisory_only.
    pos_check = source.find("verdict_is_advisory_only")
    assert pos_check > 0
    # Find the closest 'target == "prod"' before the check
    snippet = source[max(0, pos_check - 600): pos_check + 50]
    assert 'target == "prod"' in snippet or "target=='prod'" in snippet
    # And skip_verify guard nearby
    assert "skip_verify" in snippet


def test_ddd_phase_8_acceptance_reference_in_comment() -> None:
    """Code comment cites the PRD acceptance criterion (audit-readable)."""
    source = inspect.getsource(ddd_mod)
    # Either 'PRD Phase 8' or 'AI verdict alone' phrase
    assert "Phase 8" in source or "AI verdict alone" in source
