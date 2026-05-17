"""Sandbox organ — Article XVI + Article XXVIII declarative contract.

Spec anchors:
- docs/specs/TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md (Phase 7 — DRAFT v2)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §7 (Sandbox)
- .ai/schemas/sandbox_profile.schema.json (operator-authored)

This module is **declarative only** (Article XX Passive Core). It mirrors the
operator-authored `sandbox_profile.schema.json` as Python dataclasses + closed
frozensets, so the future Phase 7 runtime hook (`core/sandbox.py` — deferred)
can bind against a machine-checkable contract surface.

The runtime enforcement engine is NOT in this module. This contract describes
WHAT a sandbox profile looks like + the closed vocabulary of capability axes,
tiers, net-outbound modes, and denial reasons. The HOW (filesystem-level
denial, network egress firewall, process spawn blocking) lives in Phase 7.

Article XVI anchor: capabilities are a closed frozenset; an axis not declared
in CAPABILITY_AXES is "unknown authority" and MUST be denied at Phase 7
binding. The schema already enforces additionalProperties: false; this
module mirrors that closure into Python.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────── Capability axes (matches sandbox_profile.schema.json) ───────────

CAPABILITY_AXES: frozenset = frozenset({
    "fs",
    "net",
    "proc",
    "tools",
    "authority",
    "audit",     # optional axis added in RecordProxy alignment v2
    "policy",    # optional axis added in RecordProxy alignment v2
})


# ─────────── Sandbox tier classification (matches verifier TIER_MAP) ───────────

SANDBOX_TIERS: frozenset = frozenset({"HOT", "WARM", "COLD"})


# ─────────── Net outbound modes (matches schema net.outbound enum) ───────────

NET_OUTBOUND_MODES: frozenset = frozenset({"denied", "allowlist", "open"})


# ─────────── Deny reasons (spec §3 — kernel-emitted at sandbox.deny) ───────────

DENY_REASONS: frozenset = frozenset({
    "fs_read_outside_roots",
    "fs_write_outside_roots",
    "fs_delete_outside_roots",
    "fs_forbidden_path",
    "fs_size_limit_exceeded",
    "net_outbound_denied",
    "net_host_not_allowlisted",
    "net_protocol_not_allowed",
    "proc_binary_not_allowed",
    "proc_binary_forbidden",
    "proc_spawn_denied",
    "proc_wallclock_exceeded",
    "tool_not_allowed",
    "tool_forbidden",
    "authority_promote_denied",
    "authority_deploy_denied",
    "authority_policy_modify_denied",
    "authority_ddd_propose_denied",
    "audit_read_denied",
    "policy_read_denied",
})


# ─────────── Axis sub-dataclasses (mirror schema property shapes) ───────────


@dataclass
class FsCapability:
    """Filesystem axis — read/write/delete roots + forbidden globs + byte caps."""

    read_roots: List[str] = field(default_factory=list)
    write_roots: List[str] = field(default_factory=list)
    forbidden_paths: List[str] = field(default_factory=list)
    delete_roots: List[str] = field(default_factory=list)
    max_bytes_per_file: int = 0     # 0 = no per-file limit
    max_total_bytes: int = 0        # 0 = no session-total limit


@dataclass
class NetCapability:
    """Network axis — outbound mode + host allowlist + protocol filter."""

    outbound: str = "denied"        # one of NET_OUTBOUND_MODES
    allowlist: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)


@dataclass
class ProcCapability:
    """Process axis — binary allowlist + spawn permission + wallclock cap."""

    allowed_binaries: List[str] = field(default_factory=list)
    forbidden_binaries: List[str] = field(default_factory=list)
    spawn_allowed: bool = False
    max_wallclock_seconds: int = 0  # 0 = no limit


@dataclass
class ToolsCapability:
    """Tools axis — allowed/forbidden tool contract IDs (Article XVI closure)."""

    allowed: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)


@dataclass
class AuthorityCapability:
    """Authority axis — promote/deploy/policy-modify/ddd-propose grants.

    All default false (Article XVI default-deny + Article III: AI cannot
    grant itself authority).
    """

    may_promote: bool = False
    may_deploy: bool = False
    may_modify_policies: bool = False
    ddd_propose_allowed: bool = False


@dataclass
class AuditCapability:
    """Audit axis — read-only access to audit chain (optional v2)."""

    read_allowed: bool = False


@dataclass
class PolicyCapability:
    """Policy axis — read-only access to .ai/policies/** (optional v2)."""

    read_allowed: bool = False


# ─────────── Top-level SandboxProfile dataclass ───────────


@dataclass
class SandboxProfile:
    """Authoritative Python mirror of `.ai/schemas/sandbox_profile.schema.json`.

    A profile is bound to a session at `vvv` (emits `sandbox.profile.bound`);
    the Phase 7 runtime hook reads this object and enforces the declared
    capability surface at every kernel-mediated IO.
    """

    id: str                                            # ^[a-z0-9_-]{1,64}$
    version: str                                       # semver MAJOR.MINOR[.PATCH]
    fs: FsCapability = field(default_factory=FsCapability)
    net: NetCapability = field(default_factory=NetCapability)
    proc: ProcCapability = field(default_factory=ProcCapability)
    tools: ToolsCapability = field(default_factory=ToolsCapability)
    authority: AuthorityCapability = field(default_factory=AuthorityCapability)
    audit: Optional[AuditCapability] = None
    policy: Optional[PolicyCapability] = None
    description: str = ""


# ─────────── jsonschema validator helper ───────────

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "schemas" / "sandbox_profile.schema.json"
)
_schema_cache: Optional[Dict[str, Any]] = None


def _load_schema() -> Dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _schema_cache


def validate_profile_dict(profile: Dict[str, Any]) -> None:
    """Validate a sandbox profile dict against the operator-authored schema.

    Raises `jsonschema.ValidationError` on schema violation. Pure function:
    no side effects, no audit emission. Article XX passive.

    The schema is loaded lazily on first call and cached at module level for
    subsequent calls; the cache is read-only.
    """
    import jsonschema   # local import to keep module import-only and side-effect-free

    schema = _load_schema()
    jsonschema.validate(instance=profile, schema=schema)


__all__ = [
    "CAPABILITY_AXES",
    "SANDBOX_TIERS",
    "NET_OUTBOUND_MODES",
    "DENY_REASONS",
    "FsCapability",
    "NetCapability",
    "ProcCapability",
    "ToolsCapability",
    "AuthorityCapability",
    "AuditCapability",
    "PolicyCapability",
    "SandboxProfile",
    "validate_profile_dict",
]
