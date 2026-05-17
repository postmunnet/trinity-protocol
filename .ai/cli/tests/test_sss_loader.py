"""sss ritual loader-integration tests (S2 — RC v1.1-rc Article XII.5).

Verifies that the sss ritual code path (split across session.py:new and
vvv.py:91 auto-fire, unified in commands/sss.py) honors the
.ai/rituals/sss/ template pack:

  - emit_session_created emits the pack-declared session.created event
  - fire_sss_transition asserts the pack's transition guard *before* any
    state mutation (Article XX) and emits sss.invoked
  - drift guard raises if pack declares fewer events than code emits
  - set-equality: pack-declared audit_events == events emitted across one
    complete sss flow
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import List, Tuple

import pytest

# Reuse the minimal-project fixture used by every Loop-aware test.
from test_goal_loop import _make_project

from cli.commands.sss import (
    SSS_EVENT_INVOKED,
    SSS_EVENT_SESSION_CREATED,
    SSS_NEXT_STATE,
    PackEventDriftError,
    emit_session_created,
    fire_sss_transition,
)
from cli.core.audit import AuditChain
from cli.core.loop import Loop
from cli.core.ritual_pack_loader import (
    RitualPack,
    StateTransitionError,
    load_pack,
    required_audit_events,
)


# ───────────────────────── helpers ─────────────────────────


# REPO_ROOT/.ai/rituals holds the real packs; symlink into each tmp project so
# the in-band loader (which now resolves rituals_root from project_root, not
# cwd) can find the sss pack regardless of where the test was invoked from.
_REAL_RITUALS = Path(__file__).resolve().parent.parent.parent / "rituals"


def _wire_rituals(project_root: Path) -> None:
    """Make the real .ai/rituals tree available under the tmp project."""
    target = project_root / ".ai" / "rituals"
    if not target.exists():
        target.symlink_to(_REAL_RITUALS)


def _chain_events(project_root: Path) -> List[Tuple[str, dict]]:
    """Return (event_type, details) tuples in append order."""
    chain = AuditChain(project_root / ".ai" / "audit" / "events.ndjson")
    return [(ev["type"], ev.get("details", {})) for ev in chain.iter_events()]


# ───────────────────────── emit_session_created ─────────────────────────


def test_emit_session_created_appends_event_with_correct_fields(tmp_path: Path):
    project, session = _make_project(tmp_path)
    _wire_rituals(project)
    chain = AuditChain(project / ".ai" / "audit" / "events.ndjson")

    event = emit_session_created(
        chain,
        session_id="sess_test",
        name="Fix Login Bug",
        session_path_relative=".ai/sessions/sess_test",
    )

    assert event["type"] == SSS_EVENT_SESSION_CREATED
    assert event["details"]["session_id"] == "sess_test"
    assert event["details"]["name"] == "Fix Login Bug"
    assert event["details"]["session_path"] == ".ai/sessions/sess_test"
    assert "hash" in event and len(event["hash"]) == 64  # sha256 hex
    assert event["prev_hash"] == "0"  # genesis chain


def test_emit_session_created_raises_when_pack_drops_event(
    tmp_path: Path, monkeypatch
):
    """If the sss pack is mutated so session.created is no longer declared,
    emit_session_created must refuse rather than silently emit (drift guard)."""
    project, _session = _make_project(tmp_path)
    chain = AuditChain(project / ".ai" / "audit" / "events.ndjson")

    # Patch load_pack inside sss.py to return a pack with the event stripped.
    real_pack = load_pack("sss")
    tampered_contract = dict(real_pack.contract)
    tampered_contract["audit_events"] = [SSS_EVENT_INVOKED]  # drop session.created
    tampered = dataclasses.replace(real_pack, contract=tampered_contract)

    import cli.commands.sss as sss_mod

    monkeypatch.setattr(sss_mod, "load_pack", lambda *_a, **_kw: tampered)

    with pytest.raises(PackEventDriftError, match="session.created"):
        emit_session_created(
            chain,
            session_id="x",
            name="y",
            session_path_relative=".ai/sessions/x",
        )
    # No audit event was appended.
    assert _chain_events(project) == []


# ───────────────────────── fire_sss_transition positive ─────────────────────────


def test_fire_sss_transition_advances_ready_to_think(tmp_path: Path):
    project, session = _make_project(tmp_path)
    _wire_rituals(project)
    loop = Loop(session, graph_name="standard", project_root=project)
    assert loop.current() == "READY"

    new_state = fire_sss_transition(
        loop,
        session_id=session.name,
        decided_by="kernel",
        evidence={"task": "demo"},
    )

    assert new_state == SSS_NEXT_STATE == "THINK"
    assert loop.current() == "THINK"


def test_fire_sss_transition_emits_invoked_then_graph_transition(tmp_path: Path):
    project, session = _make_project(tmp_path)
    _wire_rituals(project)
    loop = Loop(session, graph_name="standard", project_root=project)

    fire_sss_transition(
        loop,
        session_id=session.name,
        decided_by="kernel",
        evidence={"task": "demo"},
    )

    events = _chain_events(project)
    types = [t for (t, _d) in events]
    # sss.invoked MUST precede graph.transition (Article XX — emit-then-fire).
    assert types == [SSS_EVENT_INVOKED, "graph.transition"]
    invoked_details = events[0][1]
    assert invoked_details["session_id"] == session.name
    assert invoked_details["graph_state"] == "READY"
    assert invoked_details["decided_by"] == "kernel"
    assert invoked_details["evidence"] == {"task": "demo"}


# ───────────────────────── fire_sss_transition negative guard ─────────────────────────


def test_fire_sss_transition_rejects_disallowed_current_state(tmp_path: Path):
    """Article XX: guard must raise BEFORE any audit emission / state mutation.

    We seed a session whose graph_state is already THINK (not READY). The
    sss pack's allowed_current_states=[READY] must reject this attempt.
    """
    project, session = _make_project(tmp_path)
    _wire_rituals(project)
    loop = Loop(session, graph_name="standard", project_root=project)
    # Advance to THINK via the legitimate path first.
    loop.fire("sss", decided_by="kernel")
    assert loop.current() == "THINK"

    # Snapshot chain length so we can confirm no NEW events from the rejected call.
    pre_events = _chain_events(project)

    with pytest.raises(StateTransitionError, match="not in allowed_current_states"):
        fire_sss_transition(
            loop,
            session_id=session.name,
            decided_by="kernel",
        )

    # State unchanged.
    assert loop.current() == "THINK"
    # No new audit events appended after the rejected call.
    post_events = _chain_events(project)
    assert post_events == pre_events


def test_fire_sss_transition_raises_when_pack_drops_invoked(
    tmp_path: Path, monkeypatch
):
    """If the sss pack stops declaring sss.invoked, fire_sss_transition must
    refuse rather than emit an undeclared event (drift guard)."""
    project, session = _make_project(tmp_path)
    _wire_rituals(project)
    loop = Loop(session, graph_name="standard", project_root=project)
    assert loop.current() == "READY"

    real_pack = load_pack("sss")
    tampered_contract = dict(real_pack.contract)
    tampered_contract["audit_events"] = [SSS_EVENT_SESSION_CREATED]  # drop sss.invoked
    tampered = dataclasses.replace(real_pack, contract=tampered_contract)

    import cli.commands.sss as sss_mod

    monkeypatch.setattr(sss_mod, "load_pack", lambda *_a, **_kw: tampered)

    with pytest.raises(PackEventDriftError, match="sss.invoked"):
        fire_sss_transition(loop, session_id=session.name, decided_by="kernel")

    # State unchanged, no audit events appended (Article XX).
    assert loop.current() == "READY"
    assert _chain_events(project) == []


# ───────────────────────── set-equality acceptance ─────────────────────────


def test_sss_pack_declared_events_match_emitted_set_across_full_flow(tmp_path: Path):
    """Full sss flow (dir-creation + transition-fire) must emit exactly the
    pack-declared sss audit events — set equality, not subset.

    Pack-declared: {sss.invoked, session.created}.
    Emitted: emit_session_created → session.created; fire_sss_transition →
    sss.invoked (+ Loop's own graph.transition, which is a kernel-level event
    not declared by the sss pack and so is excluded from the equality check).
    """
    project, session = _make_project(tmp_path)
    _wire_rituals(project)
    chain = AuditChain(project / ".ai" / "audit" / "events.ndjson")
    loop = Loop(session, graph_name="standard", project_root=project)

    # Step 1: session.py:new equivalent
    emit_session_created(
        chain,
        session_id=session.name,
        name="demo",
        session_path_relative=str(session.relative_to(project)),
    )

    # Step 2: vvv.py:91 auto-fire equivalent
    fire_sss_transition(loop, session_id=session.name, decided_by="kernel")

    pack = load_pack("sss")
    declared = set(required_audit_events(pack))

    emitted_types = {t for (t, _d) in _chain_events(project)}
    # graph.transition is Loop machinery, not an sss-pack-declared event.
    sss_pack_emitted = emitted_types - {"graph.transition"}

    assert sss_pack_emitted == declared, (
        f"sss pack/code drift: pack declares {declared!r}, "
        f"code emits {sss_pack_emitted!r}"
    )
