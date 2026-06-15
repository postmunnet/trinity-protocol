"""Audit replay + verify-chain logic per TRINITY_AUDIT_EVENT_SPEC_V1 §4-§5.

Read-only inspector for audit chains. Two backends:
  - Per-session SQLite at <session>/CAPTURE/capture.sqlite audit_events table
    (RecordProxy v1 source of truth)
  - Legacy global .ai/audit/events.ndjson (5-field shape per Audit Spec §2.2)

This module is READ-ONLY (Article XX Passive Core). It must NOT mutate any
chain or emit audit events. The kernel command layer (cli.commands.audit)
prints results.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator, Optional

# Canonical event-type registry per TRINITY_AUDIT_EVENT_SPEC_V1 §3 — closed
# namespace (kernel + RecordProxy + sandbox + ddd + close + verifier + tool
# + capture + state + policy + break_glass + plan + memory + llm).
CANONICAL_EVENT_TYPES: frozenset[str] = frozenset({
    # Chain root
    "genesis",
    # Session lifecycle
    "session.created", "session.closed", "session.abandoned",
    "session.archived_retroactive",
    # Operator (RecordProxy §17)
    "operator.input.captured", "operator.approval.recorded",
    "operator.rejection.recorded", "operator.amendment.recorded",
    # Ritual gates
    "sss.invoked",
    "vvv.invoked", "vvv.proposed", "vvv.passed", "vvv.failed",
    "nnn.invoked", "nnn.proposed", "nnn.passed",
    "plan.budget_checked",
    "gogogo.invoked",
    "gogogo.step_started", "gogogo.step_completed", "gogogo.completed",
    "gogogo.step.started", "gogogo.step.completed",
    "gogogo.hmac_rejected", "gogogo.step_passed", "gogogo.step_failed",
    "ddd.packet_emitted", "ddd.approved", "ddd.rejected", "ddd.held",
    "ddd.timeout", "ddd.hmac_rejected", "ddd.invoked", "ddd.completed",
    "ddd.advisory_only_refused",
    "rrr.invoked", "rrr.proposed", "rrr.completed",
    "rrr.delegated_call", "rrr.retroactive",
    # Ritual mechanics
    "ritual.started", "ritual.contract.loaded", "ritual.context.built",
    "ritual.agent.invocation.started", "ritual.agent.invocation.completed",
    "ritual.agent.invocation.failed", "ritual.agent.invocation.timeout",
    "ritual.validation.started", "ritual.validation.completed",
    "ritual.transition.requested", "ritual.transition.completed",
    "ritual.transition.blocked",
    # Verifier
    "verify.invoked", "verify.completed",
    "verifier.consolidated",
    # Graph
    "graph.transition",
    # Close
    "close.invoked", "close.manifest_built", "close.external_audit_emitted",
    "close.completed", "close.proposed", "close.failed",
    # Sandbox
    "sandbox.profile.bound", "sandbox.profile_missing",
    "sandbox.profile_invalid", "sandbox.runtime_unavailable",
    "sandbox.runtime_disabled", "sandbox.allowlist_unenforced",
    "sandbox.deny", "sandbox.applied",
    # Tool
    "tool.invocation_proposed", "tool.invocation_denied",
    "tool.invocation_completed",
    "tool.invocation.started", "tool.invocation.completed",
    "tool.invocation.failed", "tool.invocation.timeout",
    # Capture
    "capture.started", "capture.completed", "capture.failed_partial",
    "capture.reconciled",
    # State / Policy / Break-glass
    "state.changed", "policy.violation.detected", "policy.queried",
    "policy.gate_required", "policy.refused", "break_glass.invoked",
    # Plan
    "plan.amended",
    # Memory
    "memory.write", "memory.promote",
    # LLM (sibling CLIs only)
    "llm.invoked", "llm.completed",
    "llm.call_started", "llm.call_completed", "llm.call_failed",
    # Transport boundary
    "transport.envelope_accepted",
    "transport.envelope_refused.unsigned",
    "transport.envelope_refused.badkey",
    "transport.envelope_refused.replay",
    "transport.envelope_refused.overscope",
    # Agent emissions
    "presentation_synthesizer.invoked",
    "presentation_synthesizer.proposed",
    "presentation_synthesizer.failed",
    "session_bootstrap.invoked", "session_bootstrap.proposed",
    "session_bootstrap.failed",
    "clarification_helper.invoked", "clarification_helper.proposed",
    "clarification_helper.failed",
    "plan_helper.invoked", "plan_helper.proposed", "plan_helper.failed",
    "plan_helper.tool_inferred",
    "executor_helper.invoked", "executor_helper.proposed",
    "executor_helper.failed",
    "retro_writer.invoked", "retro_writer.proposed", "retro_writer.failed",
    # Legacy / pre-RecordProxy kernel events retained as aliases
    "lll.invoked",
    "snapshot.created",
    "ritual_constitution.ratified",
    # Pre-epoch (bootstrap installer) era events — real chains start with
    # these (example_client prefix, 2026-06-10)
    "genesis",
    "scaffold_complete",
    "integration_merge",
})

GENESIS_PREV_HASH = "0"
# Pre-epoch tolerance (2026-06-10): chains born under the bootstrap installer
# start with prev_hash "genesis" and hash their events with
# json.dumps(sort_keys=True) DEFAULT separators (spaces) — proven against
# example_client's real prefix. Both eras verify with full sha256 recomputation;
# nothing is ever rewritten (append-only).
GENESIS_PREV_HASHES = {GENESIS_PREV_HASH, "genesis"}
EXIT_OK = 0
EXIT_SCHEMA_OR_UNKNOWN_TYPE = 1
EXIT_CHAIN_BROKEN = 2


# ─────────────── canonical-form helpers ─────────────────────────────────────
# RecordProxy v1 (recordproxy/capture_store.py:_canonical_json) uses
# `ensure_ascii=False`. The kernel legacy chain (cli/core/audit.py._canonical)
# omits `ensure_ascii` so the default `True` applies (non-ASCII chars are
# \uXXXX-escaped). Different bytes → different hashes; pick per chain_kind.


def _canonical_json_session(obj) -> str:
    """Per-session SQLite (RecordProxy v1) canonical form — UTF-8 raw."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_json_legacy(obj) -> str:
    """Legacy ndjson canonical form — ASCII-escaped per kernel audit.py."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _event_for_hash_session(row: dict) -> dict:
    """11-field session event_for_hash (per AuditWriter.append + Audit Spec §2.1).

    Excludes `payload_json` and `hash`; `payload_hash` stands in for the body.
    """
    return {
        "event_id": row["event_id"],
        "schema_version": row["schema_version"],
        "session_id": row["session_id"],
        "seq": row["seq"],
        "event_type": row["event_type"],
        "ritual": row.get("ritual"),
        "capture_id": row.get("capture_id"),
        "actor": row["actor"],
        "ts_utc": row["ts_utc"],
        "payload_hash": row["payload_hash"],
        "prev_hash": row["prev_hash"],
    }


def _event_for_hash_legacy(row: dict) -> dict:
    """Legacy 5-field event_for_hash — entire row minus `hash`."""
    return {k: v for k, v in row.items() if k != "hash"}


def _canonical_json_pre_epoch(obj) -> str:
    """Bootstrap-installer era canonical form — sorted keys, DEFAULT
    separators (", " / ": "), ascii-escaped. Matches the recipe found on
    real pre-epoch chains (example_client prefix, 2026-06-10)."""
    return json.dumps(obj, sort_keys=True)


def _recompute_hash(event_for_hash: dict, chain_kind: str) -> str:
    if chain_kind == "session":
        canonical = _canonical_json_session(event_for_hash)
    else:
        canonical = _canonical_json_legacy(event_for_hash)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _recompute_hash_pre_epoch(event_for_hash: dict) -> str:
    return hashlib.sha256(
        _canonical_json_pre_epoch(event_for_hash).encode("utf-8")
    ).hexdigest()


# ─────────────── readers ───────────────


def read_session_chain(sqlite_path: Path) -> list[dict]:
    """Read all rows from <session>/CAPTURE/capture.sqlite audit_events
    table, sorted by seq ASC. Returns empty list if file or table missing."""
    if not sqlite_path.is_file():
        return []
    rows: list[dict] = []
    try:
        conn = sqlite3.connect(str(sqlite_path))
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT event_id, schema_version, session_id, seq, event_type, "
                "ritual, capture_id, actor, ts_utc, payload_json, payload_hash, "
                "prev_hash, hash FROM audit_events ORDER BY seq ASC"
            )
            rows = [dict(r) for r in cur.fetchall()]
        except sqlite3.OperationalError:
            # table missing
            rows = []
        conn.close()
    except sqlite3.Error:
        rows = []
    return rows


def read_legacy_ndjson(path: Path) -> list[dict]:
    """Read .ai/audit/events.ndjson line by line. Malformed lines are skipped."""
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


# ─────────────── verification ───────────────


def verify_chain(
    events: list[dict],
    *,
    strict: bool = False,
    chain_kind: str = "session",
) -> tuple[bool, list[str]]:
    """Validate prev_hash linkage + sha256 recomputation across the chain.

    Args:
        events: list of event rows (per-session 13-field shape or legacy 5-field).
        strict: when True, also validate event_type is in the canonical registry.
        chain_kind: "session" (per-session SQLite) or "legacy" (ndjson).

    Returns:
        (ok, errors). ok = bool. errors = list of human-readable strings;
        ordered by where the issue appeared in the chain.
    """
    errors: list[str] = []
    expected_prev = GENESIS_PREV_HASH
    expected_seq = 1
    pre_epoch_count = 0

    for idx, row in enumerate(events):
        # 1. Per-session schema requires seq monotonicity.
        if chain_kind == "session":
            if row.get("seq") != expected_seq:
                errors.append(
                    f"seq gap at idx={idx}: got seq={row.get('seq')!r}, expected {expected_seq}"
                )
                expected_seq = row.get("seq", expected_seq) + 1
            else:
                expected_seq += 1

        # 2. prev_hash linkage.
        actual_prev = row.get("prev_hash")
        if idx == 0 and chain_kind == "legacy" and actual_prev in GENESIS_PREV_HASHES:
            expected_prev = actual_prev  # pre-epoch genesis marker accepted
        if actual_prev != expected_prev:
            seq_label = row.get("seq") if chain_kind == "session" else idx
            errors.append(
                f"prev_hash mismatch at seq/idx={seq_label}: "
                f"got {actual_prev!r}, expected {expected_prev!r}"
            )

        # 3. Hash recomputation.
        try:
            if chain_kind == "session":
                efh = _event_for_hash_session(row)
            else:
                efh = _event_for_hash_legacy(row)
            recomputed = _recompute_hash(efh, chain_kind)
            stored = row.get("hash", "")
            if recomputed != stored and chain_kind == "legacy":
                # Pre-epoch recipe fallback — still a full sha256 over the
                # entire event body, so authenticity strength is identical.
                if _recompute_hash_pre_epoch(efh) == stored:
                    recomputed = stored
                    pre_epoch_count += 1
            if recomputed != stored:
                seq_label = row.get("seq") if chain_kind == "session" else idx
                errors.append(
                    f"hash mismatch at seq/idx={seq_label}: "
                    f"stored={stored!r} recomputed={recomputed!r}"
                )
        except KeyError as e:
            errors.append(f"missing field at idx={idx}: {e}")

        # 4. strict-mode event_type check.
        if strict:
            event_type = row.get("event_type") or row.get("type")
            if event_type and event_type not in CANONICAL_EVENT_TYPES:
                seq_label = row.get("seq") if chain_kind == "session" else idx
                errors.append(
                    f"unknown event_type at seq/idx={seq_label}: {event_type!r}"
                )

        expected_prev = row.get("hash") or expected_prev

    return (len(errors) == 0, errors)


# ─────────────── filtering ───────────────


def iter_events_filtered(
    events: Iterable[dict],
    *,
    from_seq: Optional[int] = None,
    to_seq: Optional[int] = None,
    event_type: Optional[str] = None,
    session: Optional[str] = None,
) -> Iterator[dict]:
    """Generator filtering events by seq range / event_type / session_id."""
    for row in events:
        if from_seq is not None and row.get("seq", 0) < from_seq:
            continue
        if to_seq is not None and row.get("seq", 0) > to_seq:
            continue
        if event_type is not None:
            ev = row.get("event_type") or row.get("type")
            if ev != event_type:
                continue
        if session is not None and row.get("session_id") != session:
            continue
        yield row


# ─────────────── verdict translation for CLI exit codes ───────────────


def classify_verify_errors(errors: list[str]) -> int:
    """Map verifier error list to TRINITY_AUDIT_EVENT_SPEC_V1 §4 exit codes.

    Returns 0 (OK), 1 (schema/unknown-type), or 2 (chain broken).
    Chain-integrity issues (prev_hash/hash/seq) trump unknown-type issues.
    """
    if not errors:
        return EXIT_OK
    chain_errors = [e for e in errors if "hash mismatch" in e
                    or "prev_hash mismatch" in e or "seq gap" in e]
    if chain_errors:
        return EXIT_CHAIN_BROKEN
    return EXIT_SCHEMA_OR_UNKNOWN_TYPE


# ─────────── artifact-reference scanner (Phase 10 acceptance) ───────────


# Payload field names that conventionally carry a project-root-relative
# artifact path. Scanner pulls each candidate from event.payload_json
# (per-session SQLite) or event.details (legacy NDJSON) and reports any
# whose target file is missing on disk.
ARTIFACT_REF_FIELDS: frozenset[str] = frozenset({
    "artifact_ref",
    "path",
    "diff_ref",
    "log_ref",
    "manifest_path",
    "retro_file",
    "memory_path",
    "report_path",
})


def _project_root_from_session(session_id: str, project_root: Path) -> Path:
    """Resolve a session_id to its active or archived directory under project_root."""
    sessions_root = project_root / ".ai" / "sessions"
    active = sessions_root / session_id
    if active.is_dir():
        return active
    archive = sessions_root / "archive" / f"{session_id}.archive"
    if archive.is_dir():
        return archive
    return active  # caller surfaces "missing" via empty result


def _candidate_paths(payload: dict) -> Iterator[tuple[str, str]]:
    """Yield (field_name, path_value) pairs for any ARTIFACT_REF_FIELDS
    present in the payload dict. Non-string values are skipped silently."""
    if not isinstance(payload, dict):
        return
    for k, v in payload.items():
        if k in ARTIFACT_REF_FIELDS and isinstance(v, str) and v:
            yield k, v


def scan_artifact_refs(
    session_id: str,
    *,
    project_root: Optional[Path] = None,
) -> list[dict]:
    """Pure read-only scan of a session's audit chain for dangling artifact refs.

    Walks both backends — per-session SQLite (preferred) and the global
    legacy NDJSON filtered to this session — collecting every event whose
    payload references an artifact path (`ARTIFACT_REF_FIELDS`) that does
    NOT exist on disk relative to `project_root`. Article XX: this scanner
    is passive — no mutation, no gating, no exceptions on dangling refs
    (they are reported, not raised).

    Returns a list of dicts with the shape:
        {
            "session_id": str,
            "seq": int | None,         # per-session seq when available
            "event_type": str,
            "field": str,              # which ARTIFACT_REF_FIELDS key
            "ref_path": str,           # the value referenced
            "resolved_path": str,      # absolute resolved path checked
            "reason": "missing" | "outside_project_root",
        }

    Empty list = chain is clean (or session has no chain on disk).
    """
    root = Path(project_root or Path.cwd())
    session_dir = _project_root_from_session(session_id, root)
    dangling: list[dict] = []

    # ── per-session SQLite backend ──
    sqlite_path = session_dir / "CAPTURE" / "capture.sqlite"
    rows = read_session_chain(sqlite_path)
    for row in rows:
        payload_str = row.get("payload_json") or "{}"
        try:
            payload = json.loads(payload_str)
        except (json.JSONDecodeError, TypeError):
            payload = {}
        for field_name, ref_path in _candidate_paths(payload):
            _record_if_dangling(
                dangling,
                root=root,
                session_id=session_id,
                seq=row.get("seq"),
                event_type=row.get("event_type", ""),
                field_name=field_name,
                ref_path=ref_path,
            )

    # ── legacy NDJSON backend (filtered to this session only) ──
    legacy_path = root / ".ai" / "audit" / "events.ndjson"
    legacy_rows = read_legacy_ndjson(legacy_path)
    for idx, row in enumerate(legacy_rows):
        # Skip rows that don't carry session_id at all (pre-RecordProxy
        # legacy events) OR carry a different session_id. We can't scan
        # for the requested session unless the row asserts membership.
        if row.get("session_id") != session_id:
            continue
        payload = row.get("details") or {}
        if not isinstance(payload, dict):
            payload = {}
        for field_name, ref_path in _candidate_paths(payload):
            _record_if_dangling(
                dangling,
                root=root,
                session_id=session_id,
                seq=None,
                event_type=row.get("type") or row.get("event_type", ""),
                field_name=field_name,
                ref_path=ref_path,
                legacy_idx=idx,
            )

    return dangling


def _record_if_dangling(
    dangling: list[dict],
    *,
    root: Path,
    session_id: str,
    seq: Optional[int],
    event_type: str,
    field_name: str,
    ref_path: str,
    legacy_idx: Optional[int] = None,
) -> None:
    """Resolve ref_path against project root; append to dangling on miss."""
    candidate = (root / ref_path).resolve() if not ref_path.startswith("/") else Path(ref_path)
    try:
        candidate.relative_to(root.resolve())
        inside_root = True
    except ValueError:
        inside_root = False
    if not inside_root:
        dangling.append({
            "session_id": session_id,
            "seq": seq if seq is not None else legacy_idx,
            "event_type": event_type,
            "field": field_name,
            "ref_path": ref_path,
            "resolved_path": str(candidate),
            "reason": "outside_project_root",
        })
        return
    if not candidate.exists():
        dangling.append({
            "session_id": session_id,
            "seq": seq if seq is not None else legacy_idx,
            "event_type": event_type,
            "field": field_name,
            "ref_path": ref_path,
            "resolved_path": str(candidate),
            "reason": "missing",
        })


__all__ = [
    "CANONICAL_EVENT_TYPES",
    "ARTIFACT_REF_FIELDS",
    "EXIT_OK", "EXIT_SCHEMA_OR_UNKNOWN_TYPE", "EXIT_CHAIN_BROKEN",
    "read_session_chain",
    "read_legacy_ndjson",
    "verify_chain",
    "iter_events_filtered",
    "classify_verify_errors",
    "scan_artifact_refs",
]
