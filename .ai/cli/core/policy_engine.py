"""Phase 5 PolicyEngine runtime — first runtime caller of policy_contract types.

Closes the "policy_contract.py 0 callers" gap. Reads
`.ai/policies/trinity_policy.yaml` (operator-authored, Article III write-locked)
and answers `PolicyQueryEnvelope` queries with a `PolicyVerdictEnvelope`
honoring Article XVI default-deny + the closed 4-tier precedence.

Runtime coverage. The engine evaluates these deterministic predicates:

  1. `envelope.schema_version == "1"`              → else deny(schema_invalid)
  2. `actor.authority_class in ALLOWED_*`          → else deny(unknown_authority)
  3. `boundaries.forbidden_mutation_paths` glob    → deny(forbidden_path)
  4. `boundaries.critical_gates` match             → NEEDS_HUMAN
  5. `boundaries.forbidden_tools` match            → deny(illegal_target)

When no rule matches, the engine returns `allow` with an empty reason
and `evidence_ref.rule_id = "advisory.poc"`. Richer semantic checks
(quota windows, staleness, policy-amendment flows) remain follow-on work.

Pure read-only:
- `load_policy_doc` opens the policy file in read mode and returns {}
  on missing / malformed (Article XX passive: no self-repair, no writes).
- `query` is pure over (envelope, policy_doc) — no I/O.
- No module-level state, no background threads (Article XX).

Spec anchors:
- docs/specs/TRINITY_POLICY_ENGINE_SPEC_V1.md (Phase 5)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §3 (Policy organ)
"""
from __future__ import annotations

import fnmatch
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from cli.core.policy_contract import (
    ALLOWED_AUTHORITY_CLASSES,
    PolicyQueryEnvelope,
    PolicyVerdictEnvelope,
)


POLICY_FILE_PATH = ".ai/policies/trinity_policy.yaml"


def load_policy_doc(project_root: Path) -> Dict[str, Any]:
    """Read `.ai/policies/trinity_policy.yaml` and return parsed dict.

    Returns `{}` on missing file, parse error, or non-mapping root —
    engine then falls back to Article XVI default-deny when queried.
    Read-only file open per Article III.
    """
    p = (project_root / POLICY_FILE_PATH).resolve()
    if not p.is_file():
        return {}
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_query_id() -> str:
    """Generate a ULID-shaped opaque id without external deps.

    Format: 10-char Crockford-base32 timestamp + 16-char random ⇒ 26 chars,
    same shape as `lease_minter.mint_lease` ULIDs so audit consumers can
    treat them as one symbol class.
    """
    crockford = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    ts_ms = int(time.time() * 1000)
    ts_chars: List[str] = []
    for _ in range(10):
        ts_chars.append(crockford[ts_ms & 0x1F])
        ts_ms >>= 5
    rand = "".join(crockford[secrets.randbelow(32)] for _ in range(16))
    return "".join(reversed(ts_chars)) + rand


def build_query_envelope(
    *,
    actor_id: str,
    authority_class: str,
    action_kind: str,
    action_detail: Optional[Dict[str, Any]] = None,
    target_type: Optional[str] = None,
    target_value: Optional[str] = None,
    session_id: Optional[str] = None,
    ritual_phase: Optional[str] = None,
    evidence_refs: Optional[List[str]] = None,
) -> PolicyQueryEnvelope:
    """Typed factory for `PolicyQueryEnvelope` — keeps callers terse."""
    return PolicyQueryEnvelope(
        schema_version="1",
        query_id=_new_query_id(),
        actor={"id": actor_id, "authority_class": authority_class},
        action={"kind": action_kind, "detail": action_detail or {}},
        target={"type": target_type, "value": target_value},
        context={
            "session_id": session_id or "",
            "ritual_phase": ritual_phase or "",
            "evidence_refs": evidence_refs or [],
        },
    )


def _engine_version(doc: Dict[str, Any]) -> str:
    engine_meta = doc.get("policy_engine", {}) if isinstance(doc, dict) else {}
    return str(engine_meta.get("version", "1.0"))


def _match_critical_gates(
    envelope: PolicyQueryEnvelope,
    boundaries: Dict[str, Any],
) -> Optional[Tuple[str, str]]:
    """Spec §6 — evaluate boundaries.critical_gates.

    Returns `(gate_id, rule_id)` on first match, or None. Match
    semantics (POC, simpler than spec §6.1 which has rich semantic
    triggers like "transition with to: DEPLOY AND target_env != local"):

      Each entry: {
        gate_id: "<gate.*>",
        action_kinds: ["<kind>", ...],      # required, matches action.kind
        applies_to_actors: ["<class>", ...], # optional, matches actor.authority_class
        target_pattern: "<glob>",            # optional, fnmatch against target.value
      }

    First-match-wins. Empty/absent `applies_to_actors` → all actors.
    Empty/absent `target_pattern` → any target value.

    Returns NEEDS_HUMAN at the caller; this helper just identifies the
    matching gate.
    """
    entries = boundaries.get("critical_gates", [])
    if not isinstance(entries, list):
        return None
    actor = envelope.actor or {}
    auth_class = actor.get("authority_class", "")
    action = envelope.action or {}
    action_kind = action.get("kind", "")
    target = envelope.target or {}
    target_value = target.get("value") or ""

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        action_kinds = entry.get("action_kinds")
        if not isinstance(action_kinds, list) or not action_kinds:
            continue
        if action_kind not in action_kinds:
            continue

        applies_to = entry.get("applies_to_actors")
        if (
            isinstance(applies_to, list)
            and applies_to
            and auth_class not in applies_to
        ):
            continue

        target_pattern = entry.get("target_pattern")
        if target_pattern and isinstance(target_pattern, str):
            if not (target_value and fnmatch.fnmatch(target_value, target_pattern)):
                continue

        gate_id = str(entry.get("gate_id", ""))
        if not gate_id:
            continue
        return (gate_id, "boundaries.critical_gates")

    return None


def _match_forbidden_mutation_paths(
    envelope: PolicyQueryEnvelope,
    boundaries: Dict[str, Any],
) -> Optional[Tuple[str, str, str]]:
    """Spec §7 + §5.4 — evaluate boundaries.forbidden_mutation_paths.

    Returns `(forbidden_pattern, gate_id, rationale)` on first match, or
    None if no entry matches. Match semantics (spec §7 line 609):
      - literal glob via fnmatch.fnmatch (no regex, no semantic interpretation)
      - target.value is the candidate path
      - applies_to_actors filter (absent → all actors)
      - action_kinds_denied filter (absent → all action kinds)

    Operator-authored entries in `.ai/policies/trinity_policy.yaml`:
      boundaries:
        forbidden_mutation_paths:
          - pattern: ".ai/policies/**"
            rationale: "Article III ..."
            applies_to_actors: ["ai", "tool", "transport"]
            action_kinds_denied: ["fs_write", "fs_delete", ...]   # optional
            gate_id: "gate.policy_amendment"
    """
    entries = boundaries.get("forbidden_mutation_paths", [])
    if not isinstance(entries, list):
        return None
    target = envelope.target or {}
    target_value = target.get("value") or ""
    if not target_value:
        return None
    actor = envelope.actor or {}
    auth_class = actor.get("authority_class", "")
    action = envelope.action or {}
    action_kind = action.get("kind", "")

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        pattern = entry.get("pattern")
        if not pattern or not isinstance(pattern, str):
            continue

        # Filter by actor
        applies_to = entry.get("applies_to_actors")
        if (
            isinstance(applies_to, list)
            and applies_to
            and auth_class not in applies_to
        ):
            continue

        # Filter by action kind (when entry declares the filter)
        action_kinds = entry.get("action_kinds_denied")
        if (
            isinstance(action_kinds, list)
            and action_kinds
            and action_kind not in action_kinds
        ):
            continue

        # Spec §7 line 609: literal glob match — no regex
        if fnmatch.fnmatch(target_value, pattern):
            return (
                pattern,
                str(entry.get("gate_id", "")),
                str(entry.get("rationale", ""))[:500],
            )

    return None


def query(
    envelope: PolicyQueryEnvelope,
    policy_doc: Optional[Dict[str, Any]] = None,
) -> PolicyVerdictEnvelope:
    """Answer a policy query under Article XVI default-deny.

    POC predicate ladder:
      1. envelope.schema_version != "1"           → deny(schema_invalid)
      2. actor.authority_class ∉ ALLOWED_*        → deny(unknown_authority)
      3. otherwise (advisory pass)                → allow("")

    The verdict envelope is always fully-populated so it can be appended
    to the audit chain via `AuditChain.append("policy.queried", dict)`.
    """
    doc = policy_doc or {}
    engine_version = _engine_version(doc)

    if envelope.schema_version != "1":
        return PolicyVerdictEnvelope(
            schema_version="1",
            query_id=envelope.query_id,
            verdict="deny",
            reason="schema_invalid",
            evidence_ref={
                "rule_id": "schema.v1",
                "rule_file": POLICY_FILE_PATH,
                "rule_anchor": "schema_version",
            },
            emitted_at=_now_iso(),
            engine_version=engine_version,
        )

    actor = envelope.actor or {}
    auth_class = actor.get("authority_class", "")
    if auth_class not in ALLOWED_AUTHORITY_CLASSES:
        return PolicyVerdictEnvelope(
            schema_version="1",
            query_id=envelope.query_id,
            verdict="deny",
            reason="unknown_authority",
            evidence_ref={
                "rule_id": "article.XVI",
                "rule_file": POLICY_FILE_PATH,
                "rule_anchor": "default_verdict",
            },
            emitted_at=_now_iso(),
            engine_version=engine_version,
        )

    engine_meta = doc.get("policy_engine", {}) if isinstance(doc, dict) else {}
    boundaries = engine_meta.get("boundaries", {}) if isinstance(engine_meta, dict) else {}

    # Spec §7 — boundaries.forbidden_mutation_paths rule (literal glob).
    # Evaluated BEFORE forbidden_tools because spec §7 line 663 ordering:
    # "Forbidden-path check (deny on forbidden_path)" is layer-1 in the
    # fixed evaluation order. Returns deny(forbidden_path) with §5.4
    # normative forbidden_pattern field in evidence_ref.
    if isinstance(boundaries, dict):
        fpath_match = _match_forbidden_mutation_paths(envelope, boundaries)
        if fpath_match is not None:
            forbidden_pattern, gate_id, rationale = fpath_match
            ev = {
                "rule_id": "boundaries.forbidden_mutation_paths",
                "rule_file": POLICY_FILE_PATH,
                "rule_anchor": "forbidden_mutation_paths",
                "forbidden_pattern": forbidden_pattern,
            }
            if gate_id:
                ev["gate_id"] = gate_id
            if rationale:
                ev["rationale"] = rationale
            return PolicyVerdictEnvelope(
                schema_version="1",
                query_id=envelope.query_id,
                verdict="deny",
                reason="forbidden_path",
                evidence_ref=ev,
                emitted_at=_now_iso(),
                engine_version=engine_version,
            )

    # Spec §6 — boundaries.critical_gates (NEEDS_HUMAN per Article XIII).
    # Evaluated AFTER forbidden_paths (deny dominates per spec §2.2:
    # deny > NEEDS_HUMAN > conditional > allow) but BEFORE forbidden_tools
    # (NEEDS_HUMAN gates a class of actions; forbidden_tools is a
    # narrower per-tool deny).
    if isinstance(boundaries, dict):
        gate_match = _match_critical_gates(envelope, boundaries)
        if gate_match is not None:
            gate_id, rule_id = gate_match
            return PolicyVerdictEnvelope(
                schema_version="1",
                query_id=envelope.query_id,
                verdict="NEEDS_HUMAN",
                reason="human_gate_required",
                evidence_ref={
                    "rule_id": rule_id,
                    "rule_file": POLICY_FILE_PATH,
                    "rule_anchor": "critical_gates",
                    "gate_id": gate_id,
                },
                emitted_at=_now_iso(),
                engine_version=engine_version,
                human_gate={"gate_id": gate_id},
            )

    # boundaries.forbidden_tools rule (Phase 5 gating, Session 7).
    forbidden_tools = (
        boundaries.get("forbidden_tools", []) if isinstance(boundaries, dict) else []
    )
    target = envelope.target or {}
    target_value = target.get("value")
    if (
        isinstance(forbidden_tools, list)
        and target_value
        and target_value in forbidden_tools
    ):
        return PolicyVerdictEnvelope(
            schema_version="1",
            query_id=envelope.query_id,
            verdict="deny",
            reason="illegal_target",
            evidence_ref={
                "rule_id": "boundaries.forbidden_tools",
                "rule_file": POLICY_FILE_PATH,
                "rule_anchor": "forbidden_tools",
            },
            emitted_at=_now_iso(),
            engine_version=engine_version,
        )

    return PolicyVerdictEnvelope(
        schema_version="1",
        query_id=envelope.query_id,
        verdict="allow",
        reason="",
        evidence_ref={
            "rule_id": "advisory.poc",
            "rule_file": POLICY_FILE_PATH,
            "rule_anchor": "no_rule_matched",
        },
        emitted_at=_now_iso(),
        engine_version=engine_version,
    )


def envelope_to_audit_dict(verdict: PolicyVerdictEnvelope) -> Dict[str, Any]:
    """Flatten a verdict envelope to an `AuditChain.append` payload dict."""
    return {
        "schema_version": verdict.schema_version,
        "query_id": verdict.query_id,
        "verdict": verdict.verdict,
        "reason": verdict.reason,
        "evidence_ref": dict(verdict.evidence_ref),
        "emitted_at": verdict.emitted_at,
        "engine_version": verdict.engine_version,
    }


__all__ = [
    "POLICY_FILE_PATH",
    "build_query_envelope",
    "envelope_to_audit_dict",
    "load_policy_doc",
    "query",
]
