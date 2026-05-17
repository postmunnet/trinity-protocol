"""Phase 11 — ddd_artifacts builder + writer tests."""
from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cli.core.ddd_artifacts import (
    COGNITIVE_PROTOCOL_VERSION,
    make_approval,
    make_decision_packet,
    make_hold,
    make_rejection,
    write_approval,
    write_decision_packet,
    write_hold,
    write_rejection,
)
from cli.core.ddd_contract import (
    validate_approval,
    validate_decision_packet,
    validate_hold,
    validate_rejection,
)


# ─── A1 import safety ──────────────────────────────────────────────


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.ddd_artifacts")
    assert hasattr(mod, "make_decision_packet")


# ─── A2 packet shape ───────────────────────────────────────────────


def test_make_decision_packet_returns_valid_schema() -> None:
    packet = make_decision_packet(
        session_id="0001_test",
        proposing_role="planner",
        requested_action="promote",
        verifier_reports=[
            {
                "path": ".state/verify_dev.json",
                "hash": "a" * 64,
            }
        ],
        summary="Promote to prod after green verifier sweep.",
    )
    validate_decision_packet(packet)
    assert packet["id"].startswith("dp_")
    assert packet["session"] == "0001_test"


# ─── A3 presentation pinned fields ─────────────────────────────────


def test_presentation_cognitive_protocol_version_pinned() -> None:
    p = make_decision_packet(
        session_id="s",
        proposing_role="executor",
        requested_action="deploy",
        verifier_reports=[],
        summary="x",
    )
    pres = p["presentation"]
    assert pres["cognitive_protocol_version"] == COGNITIVE_PROTOCOL_VERSION == "v1.0.1"
    assert pres["synthesizer_not_in_opinion_panel"] is True
    assert isinstance(pres["capture_refs"], list)


# ─── A4 write_decision_packet atomic + valid ───────────────────────


def test_write_decision_packet_creates_state_file(tmp_path: Path) -> None:
    p = make_decision_packet(
        session_id="0001_test",
        proposing_role="verifier",
        requested_action="amend",
        verifier_reports=[],
        summary="Need re-plan after step 3 failure.",
    )
    out = write_decision_packet(tmp_path, p)
    assert out == tmp_path / ".state" / "decision_packet.json"
    assert out.is_file()
    reread = json.loads(out.read_text())
    assert reread == p
    validate_decision_packet(reread)


# ─── A5 approval shape ─────────────────────────────────────────────


@pytest.mark.parametrize("action", ["promote", "deploy", "amend_approve"])
def test_make_approval_supports_actions(action: str) -> None:
    a = make_approval("dp_abc", action, notes="ok")
    validate_approval(a)
    assert a["decided_by"] == "human"
    assert a["action"] == action


# ─── A6 rejection requires reason ──────────────────────────────────


def test_make_rejection_requires_reason() -> None:
    with pytest.raises(ValueError):
        make_rejection("dp_abc", "")


def test_make_rejection_round_trip(tmp_path: Path) -> None:
    r = make_rejection("dp_abc", "scope drift detected")
    out = write_rejection(tmp_path, r)
    assert out.is_file()
    reread = json.loads(out.read_text())
    validate_rejection(reread)
    assert reread["reason"] == "scope drift detected"


# ─── A7 hold shape ─────────────────────────────────────────────────


def test_make_hold_pinned_action_const() -> None:
    h = make_hold("dp_abc", "2026-12-31T23:59:59Z", notes="awaiting legal")
    validate_hold(h)
    assert h["action"] == "hold"
    assert h["until"] == "2026-12-31T23:59:59Z"


# ─── A8 round-trip approval ────────────────────────────────────────


def test_round_trip_approval_write_and_reread(tmp_path: Path) -> None:
    a = make_approval("dp_xyz", "promote")
    out = write_approval(tmp_path, a)
    reread = json.loads(out.read_text())
    assert reread == a
    validate_approval(reread)


def test_round_trip_hold_write_and_reread(tmp_path: Path) -> None:
    h = make_hold("dp_xyz", "2026-06-01T12:00:00Z")
    out = write_hold(tmp_path, h)
    reread = json.loads(out.read_text())
    assert reread == h
    validate_hold(reread)
