"""Close / Session Finalizer organ — Article IX + X + XVI declarative contract.

Spec anchors:
- docs/specs/TRINITY_SESSION_CLOSE_SPEC_V1.md (Phase 15, DRAFT v2 — 198 lines)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §18 (Close / Session Finalizer)

This module is **declarative only** (Article XX Passive Core). It encodes
the Phase 15 spec §2-§5 surface as closed frozensets + Python dataclasses
so future Phase 15 runtime hardening (per-session AuditWriter integration,
manifest sha256 determinism, capture status validation) can bind against
machine-checkable contracts.

The runtime `commands/close.py` (P0 effc467) is NOT modified by this
contract. The HOW (manifest building, archive move, external audit
emission) lives in the ritual command; this module describes the CLOSED
VOCABULARY of terminal states, tier routing, and audit events.

Article IX anchor: close MUST NOT rewrite audit/retro — it only seals
+ archives. The frozensets here are read-only enumerations of valid
terminal states / tiers / event_types.

Article X anchor: the final manifest is an APPEND ANCHOR, never a
mutator. The dataclass shapes describe what gets appended.

Article XVI anchor: closed frozensets — terminal vocab via get_terminal_states_for_close (graph-derived),
CLOSE_TIERS, EXTERNAL_AUDIT_REQUIRED_TIERS, CAPTURE_STATUS_ALLOWED,
CLOSE_AUDIT_EVENTS — unknown state / tier / status / event = denied.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────── §2 — Final Manifest version pin ───────────

FINAL_MANIFEST_VERSION: str = "1.0"


# ─────────── §1 — Terminal states accepted by close ───────────
#
# Single source of truth = the canonical graph (graphs/standard.yaml
# `terminal_states`). This module no longer declares its own literal
# frozenset — that was the drift (it diverged to {DONE,FAILED,ABORTED}
# while the graph + gate used {DONE,DEAD}). Derive at call time via the
# graph-backed helper; the G11 lock-step test asserts contract == graph.
#
# FAILED / ABORTED are close-ATTEMPT outcomes (not graph terminal states);
# SEALED is archive metadata. They are intentionally absent here.

from .terminal_states import (  # noqa: E402  (re-export, keep near §1)
    get_terminal_states_for_close,
    TerminalStatesError,
)


# ─────────── §4 — Tier routing ───────────

CLOSE_TIERS: frozenset = frozenset({"HOT", "WARM", "COLD"})


# ─────────── §3 — External audit required only on COLD ───────────

EXTERNAL_AUDIT_REQUIRED_TIERS: frozenset = frozenset({"COLD"})


# ─────────── §2.2 — Capture status check ───────────

CAPTURE_STATUS_ALLOWED: frozenset = frozenset({
    "COMPLETED",
    "RECONCILED",
    "ARCHIVED",
})


# ─────────── §5 — Audit events emitted by close ───────────

CLOSE_AUDIT_EVENTS: frozenset = frozenset({
    "close.invoked",
    "close.manifest_built",
    "close.forced",                   # --force close, carries audited reason (D2)
    "close.blocked",                  # declared-ahead: non-terminal close gate (S2 of visibility session emits)
    "close.external_audit_emitted",   # COLD only
    "session.closed",
    "close.completed",
    "close.failed",                   # declared-ahead: failure path (visibility session emits)
    "close.reconciled",               # C-4: stale-pointer recovery (--reconcile)
})


# ─────────── §2 — AuditChainAnchor dataclass ───────────


@dataclass
class AuditChainAnchor:
    """Per-session audit chain anchor embedded in the final manifest.

    Per Phase 15 §3 — replaces the legacy global events_ndjson_hash with a
    per-session chain anchor (RecordProxy v1 alignment). The
    `session_chain_head` is the last hash from the per-session SQLite chain;
    `last_seq` is UNIQUE per session.
    """

    session_id: str
    session_chain_head: str                          # last hash from per-session chain
    last_seq: int                                    # UNIQUE per session
    audit_export_ref: Optional[str] = None           # legacy ndjson path (backward compat)


# ─────────── §2 — CaptureSection dataclass ───────────


@dataclass
class CaptureSection:
    """Captures slice of the final manifest per Phase 15 §2.

    Encodes the CAPTURE evidence layer: capture_store sqlite checkpoint
    hash, blobs CAS root, refs root, ULID list of capture_ids, and the
    capture_manifest sha256 sealing the full set.
    """

    capture_store_sha256: str                        # SQLite snapshot hash
    blobs_root_sha256: str = ""                      # CAS blobs root
    refs_root_sha256: str = ""                       # capture-id refs root
    capture_ids: List[str] = field(default_factory=list)
    capture_manifest_sha256: str = ""


# ─────────── §2 — FinalManifest dataclass ───────────


@dataclass
class FinalManifest:
    """Authoritative Python mirror of `final_manifest.yaml` per Phase 15 §2.

    Written by close.py at session sealing (lives in CONTROL/final_manifest.yaml).
    Article X: append-anchor — the manifest_sha256 over a deterministic
    sorted-path order pins the full session artifact set.
    """

    session_id: str
    closed_at: str                                   # RFC3339 UTC
    tier: str                                        # one of CLOSE_TIERS
    graph_state_final: str                           # one of get_terminal_states_for_close() (or DEPLOYED/VERIFIED for force-close)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    captures: Optional[CaptureSection] = None
    audit: Optional[AuditChainAnchor] = None
    manifest_sha256: str = ""                        # canonical hash over deterministic sorted-path order
    manifest_version: str = FINAL_MANIFEST_VERSION


# ─────────── §3 — ExternalAudit dataclass (COLD only) ───────────


@dataclass
class ExternalAudit:
    """COLD-tier external audit record per Phase 15 §3.

    Lands at `audit/external/<UTC-date>/<session-id>.audit.json`. Preserves
    Addendum v1.0.1 §D fields but rebases audit_chain_anchor on per-session
    AuditWriter (RecordProxy v1 alignment).
    """

    session_id: str
    tier: str                                        # const "COLD"
    final_state: str                                 # one of get_terminal_states_for_close()
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    captures: Optional[CaptureSection] = None
    decision: Optional[Dict[str, Any]] = None        # DDD packet ref
    external_systems_touched: List[str] = field(default_factory=list)
    audit_chain_anchor: Optional[AuditChainAnchor] = None
    emitted_at: str = ""                             # RFC3339 UTC


__all__ = [
    "FINAL_MANIFEST_VERSION",
    "get_terminal_states_for_close",
    "TerminalStatesError",
    "CLOSE_TIERS",
    "EXTERNAL_AUDIT_REQUIRED_TIERS",
    "CAPTURE_STATUS_ALLOWED",
    "CLOSE_AUDIT_EVENTS",
    "AuditChainAnchor",
    "CaptureSection",
    "FinalManifest",
    "ExternalAudit",
]
