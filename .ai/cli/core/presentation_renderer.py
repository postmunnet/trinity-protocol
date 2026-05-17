"""Presentation renderer — Phase 13 close-pack synthesis.

Reads a session subtree and produces a human-readable Markdown "close
pack" summarising scope, acceptance results, audit slice, and retro.

Also exposes `make_presentation_synthesis()` which constructs a
v1.0.1-shaped `PresentationSynthesis` dict honoring the pinned
`PROTOCOL_VERSIONS` from `presentation_contract.py`.

Article XX: only I/O is read-from-session + atomic write of CLOSE_PACK.md.
No audit emission, no state mutation.

Spec anchors:
- docs/specs/TRINITY_PRESENTATION_PROTOCOL_V1.md §3-§5
- .ai/cli/core/presentation_contract.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from cli.core.presentation_contract import PROTOCOL_VERSIONS


DEFAULT_PROTOCOL_VERSION = "v1.0.1"
CLOSE_PACK_FILENAME = "CLOSE_PACK.md"


def _read_text(path: Path, fallback: str = "") -> str:
    if not path.is_file():
        return fallback
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return fallback


def _read_audit_slice(
    audit_path: Path,
    session_id: Optional[str],
    limit: int,
) -> List[Dict[str, Any]]:
    """Read the last `limit` events from audit chain, optionally filtered."""
    if not audit_path.is_file():
        return []
    events: List[Dict[str, Any]] = []
    with audit_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if session_id is None:
                events.append(ev)
            else:
                details = ev.get("details", {}) if isinstance(ev.get("details"), dict) else {}
                if details.get("session_id") == session_id or ev.get("session_id") == session_id:
                    events.append(ev)
    return events[-limit:]


def render_close_pack(
    session_path: Path,
    *,
    audit_event_limit: int = 50,
    audit_chain_path: Optional[Path] = None,
) -> str:
    """Return a Markdown close-pack for the session.

    Pure-ish: reads from session_path and the project audit chain.
    Returns a string; does not write.
    """
    session_id = session_path.name
    think = session_path / "THINK"

    if audit_chain_path is None:
        # Default project-level chain: walk up two levels from .ai/sessions/<id>
        # to find .ai/audit/events.ndjson.
        sessions_dir = session_path.parent
        ai_root = sessions_dir.parent if sessions_dir.name == "sessions" else None
        if ai_root is not None:
            audit_chain_path = ai_root / "audit" / "events.ndjson"

    scope = _read_text(think / "02_SCOPE.md", "_(no THINK/02_SCOPE.md found)_")
    acceptance = _read_text(
        think / "03_ACCEPTANCE.md", "_(no THINK/03_ACCEPTANCE.md found)_"
    )
    retro = _read_text(
        think / "RETRO.md",
        _read_text(think / "retro_envelope.md", "_(no retro yet)_"),
    )
    context = _read_text(think / "00_CONTEXT.md", "_(no THINK/00_CONTEXT.md found)_")

    audit_events: List[Dict[str, Any]] = []
    if audit_chain_path is not None:
        audit_events = _read_audit_slice(
            audit_chain_path, session_id, audit_event_limit
        )

    parts: List[str] = []
    parts.append(f"# Close Pack — `{session_id}`\n")
    parts.append(f"_session path: `{session_path}`_\n")
    parts.append("\n---\n\n")
    parts.append("## §1 Scope\n\n")
    parts.append(scope.strip() + "\n\n")
    parts.append("---\n\n")
    parts.append("## §2 Context\n\n")
    parts.append(context.strip() + "\n\n")
    parts.append("---\n\n")
    parts.append("## §3 Acceptance\n\n")
    parts.append(acceptance.strip() + "\n\n")
    parts.append("---\n\n")
    parts.append(
        f"## §4 Audit slice ({len(audit_events)} of last {audit_event_limit})\n\n"
    )
    if not audit_events:
        parts.append("_(no audit events found for this session)_\n\n")
    else:
        for ev in audit_events:
            ts = ev.get("ts", "?")
            typ = ev.get("type") or ev.get("event_type", "?")
            decided = (ev.get("details", {}) or {}).get("decided_by", "")
            decided_suffix = f" · decided_by={decided}" if decided else ""
            parts.append(f"- `{ts}` **{typ}**{decided_suffix}\n")
        parts.append("\n")
    parts.append("---\n\n")
    parts.append("## §5 Retro\n\n")
    parts.append(retro.strip() + "\n")

    return "".join(parts)


def write_close_pack(
    session_path: Path,
    *,
    audit_event_limit: int = 50,
    audit_chain_path: Optional[Path] = None,
) -> Path:
    """Render + atomic-write CLOSE_PACK.md into session_path."""
    md = render_close_pack(
        session_path,
        audit_event_limit=audit_event_limit,
        audit_chain_path=audit_chain_path,
    )
    target = session_path / CLOSE_PACK_FILENAME
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(md, encoding="utf-8")
    os.replace(tmp, target)
    return target


def make_presentation_synthesis(
    *,
    session_id: str,
    summary: str,
    convergence: Optional[List[str]] = None,
    dissent_flags: Optional[List[str]] = None,
    founder_decisions_required: Optional[List[str]] = None,
    capture_refs: Optional[List[str]] = None,
    panel_diversity: Optional[Dict[str, Any]] = None,
    raw_artifacts_available: bool = True,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> Dict[str, Any]:
    """Construct a PresentationSynthesis-shaped dict (Phase 13 §5).

    The `presentation_contract.PROTOCOL_VERSIONS` frozenset is the
    authoritative version registry; any version outside it raises.
    """
    if protocol_version not in PROTOCOL_VERSIONS:
        raise ValueError(
            f"protocol_version {protocol_version!r} not in PROTOCOL_VERSIONS "
            f"{sorted(PROTOCOL_VERSIONS)}"
        )
    if not summary:
        raise ValueError("summary MUST be non-empty (§3 truth-layer boundary)")
    return {
        "session_id": session_id,
        "cognitive_protocol_version": protocol_version,
        "summary": summary,
        "convergence": list(convergence or []),
        "dissent_flags": list(dissent_flags or []),
        "founder_decisions_required": list(founder_decisions_required or []),
        "raw_artifacts_available": bool(raw_artifacts_available),
        "panel_diversity": dict(
            panel_diversity
            or {"roles": ["planner", "executor", "verifier"], "distinct_models": 1, "distinct_layers": 1}
        ),
        "synthesizer_not_in_opinion_panel": True,
        "capture_refs": list(capture_refs or []),
    }


__all__ = [
    "DEFAULT_PROTOCOL_VERSION",
    "CLOSE_PACK_FILENAME",
    "render_close_pack",
    "write_close_pack",
    "make_presentation_synthesis",
]
