"""S14 judge_advisory helper unit tests."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from cli.core.audit import AuditChain
from cli.core.judge_advisory import (
    ADVISORY_DECIDED_BY,
    VERDICT_EVENT_TYPES,
    is_tool_advisory,
    verdict_is_advisory_only,
)
from cli.core.tool_registry import ToolCapabilityRecord


# ─── is_tool_advisory ────────────────────────────────────────────────


def _record(*, declared_capabilities: tuple = ()) -> ToolCapabilityRecord:
    return ToolCapabilityRecord(
        name="test",
        required_capabilities=("fs.read",),
        optional_capabilities=(),
        default_tier_requirement="WARM",
        notes="",
        description="test",
        path="/fake/test",
        bin="/fake/test/bin",
        schema_version="1",
        contract_version="1.0",
        declared_capabilities=declared_capabilities,
        policy_default="safe",
    )


def test_is_tool_advisory_returns_true_when_advisory_tag_present() -> None:
    rec = _record(declared_capabilities=("judge", "llm", "advisory"))
    assert is_tool_advisory(rec) is True


def test_is_tool_advisory_returns_false_when_tag_absent() -> None:
    rec = _record(declared_capabilities=("execute", "fs.write"))
    assert is_tool_advisory(rec) is False


def test_is_tool_advisory_empty_capabilities_returns_false() -> None:
    rec = _record(declared_capabilities=())
    assert is_tool_advisory(rec) is False


# ─── verdict_is_advisory_only ────────────────────────────────────────


def _chain(tmp_path: Path) -> AuditChain:
    chain = AuditChain(tmp_path / "events.ndjson")
    chain.append("genesis", {"v": 1})
    return chain


def test_verdict_is_advisory_only_no_verdicts_returns_false(tmp_path: Path) -> None:
    """No verdict events at all → False (nothing to evaluate)."""
    chain = _chain(tmp_path)
    chain.append("sss.invoked", {"session_id": "s1"})  # not a verdict event
    assert verdict_is_advisory_only(chain, "s1") is False


def test_verdict_is_advisory_only_layer_3_only_returns_true(tmp_path: Path) -> None:
    """Every verdict in chain is layer_3_llm_judge → True."""
    chain = _chain(tmp_path)
    chain.append("verify.completed", {
        "session_id": "s1",
        "decided_by": "layer_3_llm_judge",
        "verdict": "PASS",
    })
    chain.append("gogogo.step_passed", {
        "session_id": "s1",
        "decided_by": "layer_3_llm_judge",
    })
    assert verdict_is_advisory_only(chain, "s1") is True


def test_verdict_is_advisory_only_explicit_advisory_returns_true(tmp_path: Path) -> None:
    """decided_by='advisory' is also in ADVISORY_DECIDED_BY."""
    chain = _chain(tmp_path)
    chain.append("verify.completed", {
        "session_id": "s1",
        "decided_by": "advisory",
    })
    assert verdict_is_advisory_only(chain, "s1") is True


def test_verdict_is_advisory_only_mixed_returns_false(tmp_path: Path) -> None:
    """Any non-advisory verdict → False."""
    chain = _chain(tmp_path)
    chain.append("verify.completed", {
        "session_id": "s1",
        "decided_by": "layer_3_llm_judge",
    })
    chain.append("gogogo.step_passed", {
        "session_id": "s1",
        "decided_by": "verifier",  # NOT advisory
    })
    assert verdict_is_advisory_only(chain, "s1") is False


def test_verdict_is_advisory_only_filters_by_session_id(tmp_path: Path) -> None:
    """Verdicts for other sessions don't affect the answer."""
    chain = _chain(tmp_path)
    chain.append("verify.completed", {
        "session_id": "OTHER",
        "decided_by": "verifier",  # would mark non-advisory for other
    })
    chain.append("gogogo.step_passed", {
        "session_id": "s1",
        "decided_by": "layer_3_llm_judge",
    })
    # Only s1's events are evaluated → only layer_3 → True
    assert verdict_is_advisory_only(chain, "s1") is True


def test_verdict_is_advisory_only_verifier_decided_returns_false(tmp_path: Path) -> None:
    """Default gogogo verdict (decided_by='verifier') counts as authoritative."""
    chain = _chain(tmp_path)
    chain.append("gogogo.step_passed", {
        "session_id": "s1",
        "decided_by": "verifier",  # layer 1 deterministic
    })
    assert verdict_is_advisory_only(chain, "s1") is False


def test_verdict_is_advisory_only_human_decided_returns_false(tmp_path: Path) -> None:
    """Layer-4 human decision is authoritative."""
    chain = _chain(tmp_path)
    chain.append("verify.completed", {
        "session_id": "s1",
        "decided_by": "human",
    })
    assert verdict_is_advisory_only(chain, "s1") is False


def test_advisory_decided_by_closed_set() -> None:
    """The closed advisory set is documented + stable."""
    assert "layer_3_llm_judge" in ADVISORY_DECIDED_BY
    assert "advisory" in ADVISORY_DECIDED_BY
    assert "verifier" not in ADVISORY_DECIDED_BY
    assert "human" not in ADVISORY_DECIDED_BY
    assert "kernel" not in ADVISORY_DECIDED_BY


def test_verdict_event_types_includes_expected() -> None:
    assert "verify.completed" in VERDICT_EVENT_TYPES
    assert "gogogo.step_passed" in VERDICT_EVENT_TYPES
    assert "gogogo.step_failed" in VERDICT_EVENT_TYPES
