"""Verifier — Pyramid layer 1 deterministic rule engine.

Spec: docs/specs/TRINITY_VERIFIER_CONTRACT_V1.md (canonical contract)
       docs/specs/02_VERIFIER_SPEC.md (Pyramid of Judgment — legacy)
Phase: 4 (replaces the stub_verifier in commands/gogogo.py).

The engine is intentionally small. Verifier rules live in
`.ai/policies/verifier-rules.yaml` under `verifier_rules.<rule_set>`,
with four buckets:

    dead_when:        [predicate, ...]   # checked first; wins → DEAD
    needs_human_when: [predicate, ...]   # 2nd; wins → NEEDS_HUMAN
    retry_when:       [predicate, ...]   # 3rd; wins → RETRY
    pass_when:        [predicate, ...]   # last; ALL must hold → PASS

A "predicate" is a string name. The evaluator looks it up against the
combined evidence dict (step + ad-hoc evidence). Truthy hit = match.
The evaluator never runs arbitrary code — there is no expression
parser. The full set of legal predicate names is whatever appears in
the rule sets you author (and whatever evidence keys your callers
supply).

Eval order is "first decisive layer wins":

    1. step.force_verdict        — fixture / test override
    2. dead_when matches         — DEAD
    3. needs_human_when matches  — NEEDS_HUMAN
    4. retry_when matches        — RETRY
    5. pass_when ALL hold        — PASS
    6. otherwise                 — fallback verdict (RETRY by default)

The fallback exists so an under-specified rule_set degrades to
"retry, please add evidence" rather than blowing up the loop. Author
rule_sets such that pass_when is achievable with the evidence the
caller will actually supply.

## Article IV — Separation of Responsibilities (Spec consolidation, Phase 8)

Per TRINITY_VERIFIER_CONTRACT_V1 §5, the verdict shape carries four
additional fields beyond the legacy v0 surface:

    layer:        1=deterministic | 2=policy | 3=LLM judge | 4=human
    tier:         HOT | WARM | COLD  (operational risk classification)
    capture_refs: list of ULID capture_ids backing the evidence
    audit_event:  reference to the chain row recording the verdict

Defaults preserve backward compatibility — every existing caller continues
to work without modification; the new fields are populated by the kernel-
facing entrypoint and stamped onto the report at emission time.

The kernel exit-path emits a `verify.completed` audit event carrying the
verdict + capture_refs + audit_event reference. The event name appears as a
module-level constant so emission sites and grep-based acceptance checks
stay aligned.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


VALID_VERDICTS = {"PASS", "RETRY", "NEEDS_HUMAN", "DEAD"}

# ─────────── Audit event name (verify.completed) ───────────
# Emitted by kernel commands/* on every evaluate_step() exit per
# TRINITY_AUDIT_EVENT_SPEC_V1 §3 "### Verifier". Pinned here so emission
# sites and grep-based acceptance checks stay aligned.
EVENT_VERIFY_COMPLETED = "verify.completed"

# ─────────── Tier map (TRINITY_VERIFIER_CONTRACT_V1 §4) ───────────
# Per-rule_set operational risk classification. Spec §4 footnote pins
# these values; this map is the in-module mirror of the tier annotation
# proposed for .ai/policies/verifier-rules.yaml (operator-authored).
# Sidesteps the forbidden write to the policy file (Article XVI + Trinity
# Decision D1) — operator may mirror these values into the yaml in a
# separate human-authored amendment per the SANDBOX proposal artifact.
TIER_MAP: Dict[str, str] = {
    "step_complete": "WARM",
    "code_change": "WARM",
    "browser_check": "HOT",
    "deploy_check": "COLD",
    "memory_promote": "WARM",
    # 4 new RecordProxy-alignment predicates (skeleton — not yet wired
    # to evaluate_step):
    "orphaned_invocation": "COLD",
    "capture_finalize_missing": "WARM",
    "capture_missing_for_artifact": "COLD",
    "sandbox_profile_missing": "COLD",
}


_TIER_SENTINEL = "__resolve_from_tier_map__"


@dataclass
class VerifierVerdict:
    verdict: str                              # PASS | RETRY | NEEDS_HUMAN | DEAD
    reason: str
    rule_set: str
    mode: str = "rules"                       # 'rules' | 'forced' | 'fallback'
    matched_predicates: List[str] = field(default_factory=list)
    evidence_keys: List[str] = field(default_factory=list)
    # ─── TRINITY_VERIFIER_CONTRACT_V1 §5 (Article IV consolidation) ───
    layer: int = 1                            # 1=deterministic | 2=policy | 3=llm | 4=human
    tier: str = _TIER_SENTINEL                # HOT | WARM | COLD per TIER_MAP (auto-resolved from rule_set when sentinel)
    capture_refs: List[str] = field(default_factory=list)
    audit_event: Optional[Dict[str, Any]] = None  # 13-field shape per §5

    def __post_init__(self) -> None:
        # Auto-resolve tier from TIER_MAP when caller did not supply one.
        # Caller-supplied tiers (HOT/WARM/COLD) are preserved verbatim;
        # only the sentinel triggers lookup. Defaults to WARM for
        # unknown rule_sets so the field is never empty.
        if self.tier == _TIER_SENTINEL:
            self.tier = TIER_MAP.get(self.rule_set, "WARM")


class VerifierError(Exception):
    pass


# ─────────── RecordProxy-alignment predicates (Spec §4) ───────────


_MUTATION_EVENT_TYPES = frozenset({
    "tool.invocation_proposed",
    "tool.invocation_denied",
    "tool.invocation_completed",
    "tool.invocation.started",
    "tool.invocation.completed",
    "tool.invocation.failed",
    "tool.invocation.timeout",
})

_MUTATION_EVENT_PREFIXES = (
    "tool.invocation.",
    "tool.invocation_",
    "write.",
    "exec.",
    "fs.write.",
    "file.write.",
)


def _capture_db(session_path: Path) -> Path:
    return session_path / "CAPTURE" / "capture.sqlite"


def _parse_utc(raw: Any) -> Optional[datetime.datetime]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _connect_readonly(db_path: Path) -> Optional[sqlite3.Connection]:
    if not db_path.is_file():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        return None


def orphaned_invocation(
    audit_event: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> bool:
    """Return True when a mutation/exec/tool event has no capture_id.

    Predicate (per spec): `audit_event.capture_id IS NULL AND
    audit_event.event_type IN (write/exec/tool.invocation.*)`. COLD-tier
    refusal; HOT/WARM downgrade per §2.1.
    """
    row = audit_event or kwargs.get("event") or kwargs
    if not isinstance(row, dict):
        return False
    event_type = row.get("event_type") or row.get("type")
    if not isinstance(event_type, str):
        return False
    is_mutation = (
        event_type in _MUTATION_EVENT_TYPES
        or event_type.startswith(_MUTATION_EVENT_PREFIXES)
    )
    return is_mutation and not row.get("capture_id")


def capture_finalize_missing(
    session_path: Optional[Path] = None,
    *,
    timeout_seconds: int = 300,
    now: Optional[datetime.datetime] = None,
    **_: Any,
) -> bool:
    """Return True when any capture is stuck in CAPTURING past timeout.

    Predicate (per spec): stuck `captures.status = CAPTURING` past WARM
    threshold; a `capture.started` without a matching `.completed` /
    `.failed_partial` / `.reconciled` after wallclock timeout.
    """
    if session_path is None:
        return False
    conn = _connect_readonly(_capture_db(Path(session_path)))
    if conn is None:
        return False
    try:
        rows = conn.execute(
            "SELECT capture_id, started_at_utc FROM captures WHERE status = ?",
            ("CAPTURING",),
        ).fetchall()
    except sqlite3.Error:
        return False
    finally:
        conn.close()
    if not rows:
        return False
    ref_now = now or datetime.datetime.now(datetime.timezone.utc)
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=datetime.timezone.utc)
    ref_now = ref_now.astimezone(datetime.timezone.utc)
    for row in rows:
        started = _parse_utc(row["started_at_utc"])
        if started is None:
            return True
        if (ref_now - started).total_seconds() >= timeout_seconds:
            return True
    return False


def capture_missing_for_artifact(
    session_path: Optional[Path] = None,
    *,
    artifact_roots: Iterable[str] = ("DO/dev", "DO/prod"),
    **_: Any,
) -> bool:
    """Return True when a DO artifact hash is absent from capture_items.

    Predicate (per spec): artifact in DO/dev/ or DO/prod/ whose hash does
    not appear in any `captures.capture_items.blob_sha256` row. COLD-tier.
    """
    if session_path is None:
        return False
    root = Path(session_path)
    artifact_files: list[Path] = []
    for rel in artifact_roots:
        base = root / rel
        if not base.is_dir():
            continue
        artifact_files.extend(p for p in base.rglob("*") if p.is_file())
    if not artifact_files:
        return False

    conn = _connect_readonly(_capture_db(root))
    if conn is None:
        return True
    try:
        rows = conn.execute("SELECT blob_sha256 FROM capture_items").fetchall()
        captured = {str(r["blob_sha256"]) for r in rows if r["blob_sha256"]}
    except sqlite3.Error:
        return True
    finally:
        conn.close()
    for path in artifact_files:
        try:
            if _sha256_file(path) not in captured:
                return True
        except OSError:
            return True
    return False


def sandbox_profile_missing(
    session_path: Optional[Path] = None,
    **_: Any,
) -> bool:
    """Return True when per-session audit lacks sandbox.profile.bound.

    Predicate (per spec): session has no `sandbox.profile.bound` event in
    its per-session audit chain at close. COLD-tier.
    """
    if session_path is None:
        return False
    root = Path(session_path)
    if not root.exists():
        return False
    conn = _connect_readonly(_capture_db(root))
    if conn is None:
        return True
    try:
        row = conn.execute(
            "SELECT 1 FROM audit_events WHERE event_type = ? LIMIT 1",
            ("sandbox.profile.bound",),
        ).fetchone()
        return row is None
    except sqlite3.Error:
        return True
    finally:
        conn.close()


# ─────────── load ───────────


def load_rules(project_root: Path) -> Dict[str, Any]:
    """Read .ai/policies/verifier-rules.yaml. Returns the parsed dict."""
    p = project_root / ".ai" / "policies" / "verifier-rules.yaml"
    if not p.exists():
        raise VerifierError(f"verifier-rules.yaml missing: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def get_rule_set(rules_doc: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Resolve a rule_set by name. Raises VerifierError if missing."""
    sets = rules_doc.get("verifier_rules") or {}
    if name not in sets:
        raise VerifierError(
            f"rule_set {name!r} not in verifier-rules.yaml; "
            f"known: {sorted(sets)}"
        )
    return sets[name]


# ─────────── eval ───────────


def _truthy(v: Any) -> bool:
    """Predicate match semantics. None / False / "" / 0 → no-match;
    everything else (including non-empty strings, non-zero numbers,
    non-empty containers) → match."""
    if v is None or v is False:
        return False
    if isinstance(v, (str, bytes)) and len(v) == 0:
        return False
    if isinstance(v, (int, float)) and v == 0:
        return False
    if isinstance(v, (list, tuple, dict, set)) and len(v) == 0:
        return False
    return True


def _match_predicates(
    evidence: Dict[str, Any], names: Iterable[str]
) -> List[str]:
    """Return the names whose value in `evidence` is truthy."""
    return [n for n in (names or []) if _truthy(evidence.get(n))]


def evaluate_step(
    step: Dict[str, Any],
    rule_set_name: str,
    rules_doc: Dict[str, Any],
    extra_evidence: Optional[Dict[str, Any]] = None,
) -> VerifierVerdict:
    """Evaluate a single step against a named rule_set.

    `step` is the plan-step dict (from .state/plan.json). It can carry
    evidence keys directly, plus the special `force_verdict` field
    used by test fixtures.

    `extra_evidence` lets the caller layer in dynamic evidence (e.g.
    test_result, diff, http_health_check) without mutating the step.
    """
    # 1. Forced verdict (test fixtures / explicit operator override)
    forced = step.get("force_verdict")
    if isinstance(forced, str) and forced in VALID_VERDICTS:
        return VerifierVerdict(
            verdict=forced,
            reason=step.get("force_reason", "fixture-forced"),
            rule_set=rule_set_name,
            mode="forced",
            matched_predicates=[],
            evidence_keys=sorted(step.keys()),
        )

    rule_set = get_rule_set(rules_doc, rule_set_name)
    fallback = (rule_set.get("fallback_verdict") or "RETRY").upper()
    if fallback not in VALID_VERDICTS:
        raise VerifierError(
            f"rule_set {rule_set_name!r} fallback_verdict={fallback!r} "
            f"not in {sorted(VALID_VERDICTS)}"
        )

    evidence: Dict[str, Any] = dict(step or {})
    if extra_evidence:
        evidence.update(extra_evidence)
    evidence_keys = sorted(evidence.keys())

    # 2. dead_when — first match wins
    dead_hits = _match_predicates(evidence, rule_set.get("dead_when") or [])
    if dead_hits:
        return VerifierVerdict(
            verdict="DEAD",
            reason=f"dead_when matched: {dead_hits[0]}",
            rule_set=rule_set_name,
            mode="rules",
            matched_predicates=dead_hits,
            evidence_keys=evidence_keys,
        )

    # 3. needs_human_when
    nh_hits = _match_predicates(
        evidence, rule_set.get("needs_human_when") or []
    )
    if nh_hits:
        return VerifierVerdict(
            verdict="NEEDS_HUMAN",
            reason=f"needs_human_when matched: {nh_hits[0]}",
            rule_set=rule_set_name,
            mode="rules",
            matched_predicates=nh_hits,
            evidence_keys=evidence_keys,
        )

    # 4. retry_when
    retry_hits = _match_predicates(
        evidence, rule_set.get("retry_when") or []
    )
    if retry_hits:
        return VerifierVerdict(
            verdict="RETRY",
            reason=f"retry_when matched: {retry_hits[0]}",
            rule_set=rule_set_name,
            mode="rules",
            matched_predicates=retry_hits,
            evidence_keys=evidence_keys,
        )

    # 5. pass_when — ALL must be truthy
    pass_predicates = list(rule_set.get("pass_when") or [])
    if pass_predicates:
        unmet = [p for p in pass_predicates if not _truthy(evidence.get(p))]
        if not unmet:
            return VerifierVerdict(
                verdict="PASS",
                reason="all pass_when predicates satisfied",
                rule_set=rule_set_name,
                mode="rules",
                matched_predicates=pass_predicates,
                evidence_keys=evidence_keys,
            )
        # Some pass_when predicates are unmet — fall through to fallback
        # so the caller learns *what* is missing.
        return VerifierVerdict(
            verdict=fallback,
            reason=f"pass_when unmet: {', '.join(unmet)}",
            rule_set=rule_set_name,
            mode="fallback",
            matched_predicates=[],
            evidence_keys=evidence_keys,
        )

    # 6. No rules matched and no pass_when defined — fallback.
    return VerifierVerdict(
        verdict=fallback,
        reason="no predicates matched; rule_set has no pass_when",
        rule_set=rule_set_name,
        mode="fallback",
        matched_predicates=[],
        evidence_keys=evidence_keys,
    )


def list_rule_sets(rules_doc: Dict[str, Any]) -> List[str]:
    return sorted((rules_doc.get("verifier_rules") or {}).keys())
