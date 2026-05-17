"""DDD artifacts — Phase 11 packet/approval/rejection/hold builders + writers.

Constructs schema-valid dicts mirrored on the §3-§6 dataclasses in
`ddd_contract.py`, validates via `ddd_contract.validate_*`, and writes
to the session's `.state/` directory with atomic semantics.

Article XX: builders are pure (no I/O at import). Writers perform a
single file create + replace (POSIX atomic) — no audit emission, no
state mutation outside the session subtree.

Spec anchors:
- docs/specs/TRINITY_DDD_HUMAN_GATE_SPEC_V1.md §3-§6
- .ai/schemas/{decision_packet,approval,rejection,hold}.schema.json
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from cli.core.ddd_contract import (
    validate_approval,
    validate_decision_packet,
    validate_hold,
    validate_rejection,
)


COGNITIVE_PROTOCOL_VERSION = "v1.0.1"


# ─────────── time helpers ───────────


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    # Schema accepts RFC3339; use the format produced by str(datetime) with offset.
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─────────── packet builder ───────────


def make_decision_packet(
    *,
    session_id: str,
    proposing_role: str,
    requested_action: str,
    verifier_reports: List[Dict[str, Any]],
    summary: str,
    convergence: Optional[List[str]] = None,
    dissent_flags: Optional[List[str]] = None,
    founder_decisions_required: Optional[List[str]] = None,
    raw_artifacts_available: bool = True,
    panel_diversity: Optional[Dict[str, Any]] = None,
    capture_refs: Optional[List[str]] = None,
    ttl_seconds: int = 86400,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Construct a schema-valid decision_packet dict.

    Auto-fills the §3.1 (Addendum v1.0.1 §E) presentation pinned fields:
    `cognitive_protocol_version`, `synthesizer_not_in_opinion_panel`,
    `capture_refs[]`. Callers supply `summary` (required, non-empty);
    other text fields default to empty lists per §3.1 ("explicitly no
    dissent flagged" semantics).
    """
    created = now if now is not None else _now_utc()
    expires = created + timedelta(seconds=ttl_seconds)

    if panel_diversity is None:
        panel_diversity = {
            "roles": ["planner", "executor", "verifier"],
            "distinct_models": 1,
            "distinct_layers": 1,
        }
    packet: Dict[str, Any] = {
        "id": f"dp_{uuid.uuid4().hex}",
        "session": session_id,
        "created_ts": _iso(created),
        "proposing_role": proposing_role,
        "requested_action": requested_action,
        "verifier_reports": verifier_reports,
        "presentation": {
            "cognitive_protocol_version": COGNITIVE_PROTOCOL_VERSION,
            "summary": summary,
            "convergence": list(convergence or []),
            "dissent_flags": list(dissent_flags or []),
            "founder_decisions_required": list(founder_decisions_required or []),
            "raw_artifacts_available": bool(raw_artifacts_available),
            "panel_diversity": dict(panel_diversity),
            "synthesizer_not_in_opinion_panel": True,
            "capture_refs": list(capture_refs or []),
        },
        "expires_ts": _iso(expires),
    }
    validate_decision_packet(packet)
    return packet


# ─────────── approval / rejection / hold builders ───────────


def make_approval(
    packet_id: str,
    action: str,
    notes: str = "",
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Construct a schema-valid approval dict (Article XIII)."""
    decided_at = now if now is not None else _now_utc()
    obj: Dict[str, Any] = {
        "packet_id": packet_id,
        "decided_by": "human",
        "decided_at": _iso(decided_at),
        "action": action,
    }
    if notes:
        obj["notes"] = notes
    validate_approval(obj)
    return obj


def make_rejection(
    packet_id: str,
    reason: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    if not reason:
        raise ValueError("rejection reason MUST be non-empty (Article XIII)")
    decided_at = now if now is not None else _now_utc()
    obj: Dict[str, Any] = {
        "packet_id": packet_id,
        "decided_by": "human",
        "decided_at": _iso(decided_at),
        "action": "reject",
        "reason": reason,
    }
    validate_rejection(obj)
    return obj


def make_hold(
    packet_id: str,
    until_iso: str,
    notes: str = "",
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    decided_at = now if now is not None else _now_utc()
    obj: Dict[str, Any] = {
        "packet_id": packet_id,
        "decided_by": "human",
        "decided_at": _iso(decided_at),
        "action": "hold",
        "until": until_iso,
    }
    if notes:
        obj["notes"] = notes
    validate_hold(obj)
    return obj


# ─────────── writers (atomic) ───────────


def _atomic_write(target: Path, payload: Dict[str, Any]) -> Path:
    """Write JSON atomically: tmp file then os.replace()."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, target)
    return target


def write_decision_packet(session_path: Path, packet: Dict[str, Any]) -> Path:
    validate_decision_packet(packet)
    return _atomic_write(session_path / ".state" / "decision_packet.json", packet)


def write_approval(session_path: Path, approval: Dict[str, Any]) -> Path:
    validate_approval(approval)
    return _atomic_write(session_path / ".state" / "approval.json", approval)


def write_rejection(session_path: Path, rejection: Dict[str, Any]) -> Path:
    validate_rejection(rejection)
    return _atomic_write(session_path / ".state" / "rejection.json", rejection)


def write_hold(session_path: Path, hold: Dict[str, Any]) -> Path:
    validate_hold(hold)
    return _atomic_write(session_path / ".state" / "hold.json", hold)


__all__ = [
    "COGNITIVE_PROTOCOL_VERSION",
    "make_decision_packet",
    "make_approval",
    "make_rejection",
    "make_hold",
    "write_decision_packet",
    "write_approval",
    "write_rejection",
    "write_hold",
]
