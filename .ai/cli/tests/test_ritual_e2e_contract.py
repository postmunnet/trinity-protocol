"""Conformance tests for the Ritual E2E Warm-Path contract (Phase 16)."""
from __future__ import annotations

import dataclasses

from cli.core.ritual_e2e_contract import (
    COLD_PATH_REQUIRED_RITUALS,
    DDD_TIER_TARGETS,
    HOT_PATH_OPTIONAL_RITUALS,
    RITUAL_SEQUENCE,
    RITUAL_TIER_STRICTNESS,
    RitualLifecycleEvent,
    WARM_PATH_REQUIRED_RITUALS,
    is_required,
)


# ─────────── ritual sequence (canonical user-facing order) ───────────


def test_ritual_sequence_is_seven_tuple() -> None:
    assert isinstance(RITUAL_SEQUENCE, tuple)
    assert len(RITUAL_SEQUENCE) == 7


def test_ritual_sequence_canonical_order() -> None:
    """Per Ritual Contract §1 line 39: sss → vvv → nnn → gogogo → ddd → rrr → close."""
    assert RITUAL_SEQUENCE == ("sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "close")


# ─────────── tier strictness matrix (7 × 3 = 21 cells) ───────────


def test_ritual_tier_strictness_has_twentyone_cells() -> None:
    assert len(RITUAL_TIER_STRICTNESS) == 21


def test_ritual_tier_strictness_covers_all_ritual_tier_combinations() -> None:
    for ritual in RITUAL_SEQUENCE:
        for tier in ("HOT", "WARM", "COLD"):
            assert (ritual, tier) in RITUAL_TIER_STRICTNESS, (ritual, tier)


def test_warm_tier_marks_six_rituals_required() -> None:
    """Per Ritual Contract §9 WARM row: sss/vvv/nnn/gogogo/ddd/rrr required;
    close recommended."""
    warm_required = {r for r in RITUAL_SEQUENCE
                     if RITUAL_TIER_STRICTNESS[(r, "WARM")] == "required"}
    assert warm_required == {"sss", "vvv", "nnn", "gogogo", "ddd", "rrr"}


def test_cold_tier_marks_all_seven_required() -> None:
    """COLD row: every ritual required (including close)."""
    cold_required = {r for r in RITUAL_SEQUENCE
                     if RITUAL_TIER_STRICTNESS[(r, "COLD")] == "required"}
    assert cold_required == {"sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "close"}


def test_hot_tier_marks_no_ritual_required() -> None:
    """HOT row: no ritual is strictly required (all optional / invoked / not_required)."""
    hot_required = {r for r in RITUAL_SEQUENCE
                    if RITUAL_TIER_STRICTNESS[(r, "HOT")] == "required"}
    assert hot_required == set()


def test_close_is_recommended_on_warm() -> None:
    assert RITUAL_TIER_STRICTNESS[("close", "WARM")] == "recommended"


def test_close_is_required_on_cold() -> None:
    assert RITUAL_TIER_STRICTNESS[("close", "COLD")] == "required"


def test_close_is_not_required_on_hot() -> None:
    assert RITUAL_TIER_STRICTNESS[("close", "HOT")] == "not_required"


def test_ddd_is_not_required_on_hot() -> None:
    assert RITUAL_TIER_STRICTNESS[("ddd", "HOT")] == "not_required"


# ─────────── per-path required frozensets ───────────


def test_warm_path_required_rituals_canonical_set() -> None:
    assert WARM_PATH_REQUIRED_RITUALS == frozenset({
        "sss", "vvv", "nnn", "gogogo", "ddd", "rrr",
    })


def test_warm_path_excludes_close() -> None:
    """close is 'recommended' on WARM, not required — must NOT be in WARM_PATH_REQUIRED_RITUALS."""
    assert "close" not in WARM_PATH_REQUIRED_RITUALS


def test_cold_path_required_rituals_includes_close() -> None:
    assert "close" in COLD_PATH_REQUIRED_RITUALS


def test_cold_path_required_rituals_seven_elements() -> None:
    assert COLD_PATH_REQUIRED_RITUALS == frozenset({
        "sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "close",
    })


def test_hot_path_optional_covers_all_seven() -> None:
    assert HOT_PATH_OPTIONAL_RITUALS == frozenset(RITUAL_SEQUENCE)


# ─────────── DDD tier targets ───────────


def test_ddd_tier_targets_warm_dev_cold_prod() -> None:
    assert DDD_TIER_TARGETS == {"WARM": "dev", "COLD": "prod"}


def test_ddd_tier_targets_does_not_include_hot() -> None:
    """HOT does not bind ddd target — ddd is not_required."""
    assert "HOT" not in DDD_TIER_TARGETS


# ─────────── is_required classifier ───────────


def test_is_required_warm_rituals() -> None:
    for r in ("sss", "vvv", "nnn", "gogogo", "ddd", "rrr"):
        assert is_required(r, "WARM") is True, r
    assert is_required("close", "WARM") is False


def test_is_required_cold_rituals_all_seven() -> None:
    for r in RITUAL_SEQUENCE:
        assert is_required(r, "COLD") is True, r


def test_is_required_hot_rituals_none_required() -> None:
    for r in RITUAL_SEQUENCE:
        assert is_required(r, "HOT") is False, r


def test_is_required_unknown_combination_returns_false() -> None:
    """Unknown ritual or tier → not required (Article XVI default-deny applies
    to ENFORCEMENT, not classification; the kernel decides whether to gate)."""
    assert is_required("nonsense", "WARM") is False
    assert is_required("vvv", "UNKNOWN_TIER") is False


# ─────────── RitualLifecycleEvent dataclass ───────────


def test_ritual_lifecycle_event_fields() -> None:
    fields = {f.name for f in dataclasses.fields(RitualLifecycleEvent)}
    required = {"ritual", "ts", "decided_by", "tier", "outcome",
                "audit_event_id", "notes"}
    assert required.issubset(fields)


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.ritual_e2e_contract as rc

    importlib.reload(rc)
    assert hasattr(rc, "RITUAL_SEQUENCE")
