"""Lease minter — Phase 6 Session D.

Constructs a Kernel-issued `ExecutionLease` (Article XXVIII contract,
Organ Map §6) with a ULID-shaped `lease_id`, RFC3339 UTC timestamps,
and sensible defaults for `required_artifacts` and
`allowed_audit_event_types`.

Pure function: no I/O, no audit append. The caller (Kernel) is
responsible for emitting `lease.minted` to the audit chain (Session E).

Spec anchors:
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §6 (Executor)
- docs/specs/TRINITY_AUDIT_EVENT_SPEC_V1.md §3 (event registry)

Import-time safety: no I/O at import (Article XX Passive Core).
"""
from __future__ import annotations

import secrets
import time as _time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cli.core.executor import (
    ALLOWED_AUDIT_EVENT_TYPES,
    REQUIRED_OUTPUT_ARTIFACTS,
    ExecutionLease,
)


# Crockford base32 (no I, L, O, U).
_CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# Subset of executor.ALLOWED_AUDIT_EVENT_TYPES that an executor invocation
# under a single lease is expected to emit. Composed at module load so
# we never drift from the executor contract.
DEFAULT_LEASE_AUDIT_EVENTS: tuple = tuple(
    e
    for e in (
        "tool.invocation_proposed",
        "tool.invocation_denied",
        "tool.invocation.started",
        "tool.invocation.completed",
        "tool.invocation.failed",
        "tool.invocation.timeout",
        "gogogo.step_started",
        "gogogo.step_completed",
        "gogogo.step_passed",
        "gogogo.step_failed",
    )
    if e in ALLOWED_AUDIT_EVENT_TYPES
)


def _iso_z(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _ulid(now_ms: int, rand_80: int) -> str:
    """Encode a 128-bit ULID as 26 Crockford base32 chars.

    Layout: 48 bits timestamp (ms since unix epoch) | 80 bits random.
    The top 2 bits of the first encoded char are always 0 (130-bit slot
    holds a 128-bit value), so the alphabet only uses values 0..7 for
    the leading position — consistent with the ULID spec.
    """
    value = ((now_ms & ((1 << 48) - 1)) << 80) | (rand_80 & ((1 << 80) - 1))
    out: List[str] = []
    for _ in range(26):
        out.append(_CROCKFORD_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def mint_lease(
    session_id: str,
    step_id: str,
    *,
    ttl_seconds: int = 600,
    allowed_paths: Optional[List[str]] = None,
    allowed_audit_event_types: Optional[List[str]] = None,
    sandbox_profile_ref: Optional[str] = None,
    now: Optional[datetime] = None,
) -> ExecutionLease:
    """Mint a Kernel-issued ExecutionLease for a single executor invocation.

    Pure function: no I/O, no audit append. Caller (Kernel) is
    responsible for emitting `lease.minted` to the audit chain.

    Args:
        session_id: Parent session id (e.g. "0001_2026-05-16_..._slug").
        step_id: Step id within plan (e.g. "S1").
        ttl_seconds: Lease lifetime in seconds (default 600 = 10 minutes).
        allowed_paths: Filesystem write-allowlist for this lease.
            Defaults to an empty list (caller must extend before granting
            write authority).
        allowed_audit_event_types: Audit event-type allowlist. Defaults
            to `DEFAULT_LEASE_AUDIT_EVENTS` (a guard-friendly subset of
            `executor.ALLOWED_AUDIT_EVENT_TYPES`).
        sandbox_profile_ref: Path to a Phase 7 sandbox profile (optional).
        now: Override clock for deterministic minting in tests.

    Returns:
        Fully-populated ExecutionLease with a ULID `lease_id`,
        RFC3339 `granted_at` / `expires_at`, and `decided_by="kernel"`.
    """
    granted = now if now is not None else _now_utc()
    if granted.tzinfo is None:
        granted = granted.replace(tzinfo=timezone.utc)
    expires = granted + timedelta(seconds=ttl_seconds)

    now_ms = int(granted.timestamp() * 1000)
    rand_80 = secrets.randbits(80)
    lease_id = _ulid(now_ms, rand_80)

    return ExecutionLease(
        lease_id=lease_id,
        session_id=session_id,
        step_id=step_id,
        granted_at=_iso_z(granted),
        expires_at=_iso_z(expires),
        allowed_paths=list(allowed_paths) if allowed_paths is not None else [],
        allowed_audit_event_types=(
            list(allowed_audit_event_types)
            if allowed_audit_event_types is not None
            else list(DEFAULT_LEASE_AUDIT_EVENTS)
        ),
        required_artifacts=list(REQUIRED_OUTPUT_ARTIFACTS),
        sandbox_profile_ref=sandbox_profile_ref,
        decided_by="kernel",
    )


__all__ = [
    "DEFAULT_LEASE_AUDIT_EVENTS",
    "mint_lease",
]
