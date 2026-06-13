"""Plan versioning for `ai nnn --amend` (session loop-back support).

Q24.10 amendment-loop, step 1. Lets a plan be amended in-session without
closing+reopening. Invariants (operator-locked 2026-06-13):

  1. plan.v1 is immutable — amend never mutates an existing version file.
  2. every amend creates a NEW plan.v(N+1).json.
  3. every amendment carries a reason + change summary.
  4. a goal-level change is rejected (caller must use `vvv --amend`).
  5. gogogo executes the latest ACTIVE version via resolve_active_plan().

Layout inside a session:
  .state/plan.json              active-version snapshot (backward-compat; the
                                only file gogogo/rrr historically read)
  .state/plan.v1.json           immutable version snapshots
  .state/plan.v2.json
  .state/plan_meta.json         { "active_version": N }
  .state/plan_amendments/0001.json   machine-readable amendment records
  THINK/AMENDMENTS/0001_*.md         human-readable deltas (written by caller)

`plan.json` is deliberately kept identical to the active version so existing
readers (gogogo.py, rrr.py) need no change to *see* the active plan; the
resolver is the canonical accessor going forward.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

_VERSION_RE = re.compile(r"^plan\.v(\d+)\.json$")

# Recognised change-kinds in an amendment record (invariant #3 vocabulary).
CHANGE_KINDS = (
    "add_step",
    "modify_step",
    "remove_step",
    "add_acceptance",
    "change_scope",
    "add_verify_command",
)


def _state(session_path: Path) -> Path:
    d = session_path / ".state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def list_plan_versions(session_path: Path) -> List[int]:
    """Return sorted version numbers that have a plan.vN.json file."""
    out = []
    for p in _state(session_path).glob("plan.v*.json"):
        m = _VERSION_RE.match(p.name)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def active_version(session_path: Path) -> int:
    """Resolve the active version number.

    Order: plan_meta.json:active_version → max(plan.vN) → 1 (legacy session
    that only has plan.json is treated as version 1).
    """
    meta = _state(session_path) / "plan_meta.json"
    if meta.exists():
        try:
            v = int(json.loads(meta.read_text(encoding="utf-8")).get("active_version", 0))
            if v > 0:
                return v
        except (ValueError, json.JSONDecodeError):
            pass
    versions = list_plan_versions(session_path)
    return versions[-1] if versions else 1


def resolve_active_plan(session_path: Path) -> Dict[str, Any]:
    """Return the active plan dict. Canonical accessor for gogogo/rrr.

    Prefers the active version file; falls back to plan.json (legacy/active
    snapshot). Raises FileNotFoundError if neither exists.
    """
    state = _state(session_path)
    v = active_version(session_path)
    vfile = state / f"plan.v{v}.json"
    if vfile.exists():
        return json.loads(vfile.read_text(encoding="utf-8"))
    snapshot = state / "plan.json"
    if snapshot.exists():
        return json.loads(snapshot.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"no plan found in {state}")


def write_plan_version(
    session_path: Path, plan: Dict[str, Any], version: int
) -> Path:
    """Write plan.v{version}.json + refresh plan.json snapshot + plan_meta.

    Refuses to overwrite an existing version file (invariant #1/#2).
    """
    state = _state(session_path)
    vfile = state / f"plan.v{version}.json"
    if vfile.exists():
        raise FileExistsError(
            f"plan.v{version}.json already exists — versions are immutable"
        )
    body = json.dumps(plan, indent=2, ensure_ascii=False)
    vfile.write_text(body, encoding="utf-8")
    # active snapshot (backward-compat readers)
    (state / "plan.json").write_text(body, encoding="utf-8")
    (state / "plan_meta.json").write_text(
        json.dumps({"active_version": version}, indent=2), encoding="utf-8"
    )
    return vfile


def is_goal_level_change(base: Dict[str, Any], delta: Dict[str, Any]) -> bool:
    """True if the delta changes the top-level goal (invariant #4)."""
    new_goal = delta.get("goal")
    return bool(new_goal) and new_goal.strip() != (base.get("goal") or "").strip()


def diff_changes(base: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
    """Best-effort classification of what an amendment changed.

    Returns a subset of CHANGE_KINDS. Deterministic, no LLM.
    """
    changes: List[str] = []
    bsteps = base.get("steps") or []
    nsteps = new.get("steps") or []
    if len(nsteps) > len(bsteps):
        changes.append("add_step")
    elif len(nsteps) < len(bsteps):
        changes.append("remove_step")
    else:
        if json.dumps(bsteps, sort_keys=True) != json.dumps(nsteps, sort_keys=True):
            changes.append("modify_step")

    # verify command newly present on any step
    def _has_verify(steps):
        return any(isinstance(s, dict) and s.get("verify") for s in steps)

    if _has_verify(nsteps) and not _has_verify(bsteps):
        changes.append("add_verify_command")

    bacc = base.get("acceptance") or []
    nacc = new.get("acceptance") or []
    if len(nacc) > len(bacc) or (
        json.dumps(bacc, sort_keys=True) != json.dumps(nacc, sort_keys=True)
    ):
        changes.append("add_acceptance")

    if (new.get("goal") or "").strip() != (base.get("goal") or "").strip():
        # caught earlier as reject; included for completeness if ever reached
        changes.append("change_scope")

    return changes or ["modify_step"]


def write_amendment_record(
    session_path: Path,
    from_version: int,
    to_version: int,
    reason: str,
    changes: List[str],
) -> Tuple[Path, Dict[str, Any]]:
    """Write the next .state/plan_amendments/NNNN.json record."""
    adir = _state(session_path) / "plan_amendments"
    adir.mkdir(parents=True, exist_ok=True)
    seq = len(list(adir.glob("*.json"))) + 1
    record = {
        "seq": seq,
        "from_version": from_version,
        "to_version": to_version,
        "reason": reason,
        "changes": changes,
        "ts": _now(),
    }
    rfile = adir / f"{seq:04d}.json"
    rfile.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return rfile, record


def list_amendment_records(session_path: Path) -> List[Dict[str, Any]]:
    adir = _state(session_path) / "plan_amendments"
    if not adir.exists():
        return []
    out = []
    for p in sorted(adir.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out
