"""Generic immutable artifact versioning (Q24.10 step 2 — storage layer).

A semantics-free helper for versioning any per-session JSON artifact
(goal_contract, plan, …). The SEMANTIC owner (vvv.py / nnn.py) decides what
an artifact *means*, what a "change" is, and when an amend is legal — this
module only provides storage / version / history / immutability.

Operator boundary (locked 2026-06-13):
    artifact_version.py = storage / version / history / immutability
    vvv.py / nnn.py      = semantic owner
This module MUST NOT learn that an artifact is a "plan", "goal_contract",
"acceptance" or "deploy". It is name-parameterized only.

Layout inside a session, for artifact `<name>`:
    .state/<name>.json                 active-version snapshot (latest pointer)
    .state/<name>.v1.json              immutable version snapshots
    .state/<name>.v2.json
    .state/<name>_meta.json            { "active_version": N }
    .state/<name>_amendments/0001.json amendment records

The .json snapshot is kept identical to the active version so simple
readers can read it directly; resolve_latest() is the canonical accessor.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _state(session_path: Path) -> Path:
    d = session_path / ".state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _version_re(name: str) -> "re.Pattern[str]":
    return re.compile(rf"^{re.escape(name)}\.v(\d+)\.json$")


def list_versions(session_path: Path, name: str) -> List[int]:
    """Sorted version numbers that have a <name>.vN.json file."""
    rx = _version_re(name)
    out = []
    for p in _state(session_path).glob(f"{name}.v*.json"):
        m = rx.match(p.name)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def active_version(session_path: Path, name: str) -> int:
    """Active version: <name>_meta.json → max(<name>.vN) → 1."""
    meta = _state(session_path) / f"{name}_meta.json"
    if meta.exists():
        try:
            v = int(json.loads(meta.read_text(encoding="utf-8")).get("active_version", 0))
            if v > 0:
                return v
        except (ValueError, json.JSONDecodeError):
            pass
    versions = list_versions(session_path, name)
    return versions[-1] if versions else 1


def resolve_latest(session_path: Path, name: str) -> Dict[str, Any]:
    """Return the active version's payload. Canonical accessor.

    Prefers <name>.v{active}.json; falls back to <name>.json snapshot.
    Raises FileNotFoundError if neither exists.
    """
    state = _state(session_path)
    v = active_version(session_path, name)
    vfile = state / f"{name}.v{v}.json"
    if vfile.exists():
        return json.loads(vfile.read_text(encoding="utf-8"))
    snapshot = state / f"{name}.json"
    if snapshot.exists():
        return json.loads(snapshot.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"no artifact '{name}' in {state}")


def write_version(
    session_path: Path, name: str, payload: Dict[str, Any], version: int
) -> Path:
    """Write <name>.v{version}.json + refresh snapshot + meta.

    Refuses to overwrite an existing version file (immutability).
    """
    state = _state(session_path)
    vfile = state / f"{name}.v{version}.json"
    if vfile.exists():
        raise FileExistsError(
            f"{name}.v{version}.json already exists — versions are immutable"
        )
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    vfile.write_text(body, encoding="utf-8")
    (state / f"{name}.json").write_text(body, encoding="utf-8")
    (state / f"{name}_meta.json").write_text(
        json.dumps({"active_version": version}, indent=2), encoding="utf-8"
    )
    return vfile


def write_amendment_record(
    session_path: Path,
    name: str,
    from_version: int,
    to_version: int,
    reason: str,
    changes: List[str],
) -> Tuple[Path, Dict[str, Any]]:
    """Write the next .state/<name>_amendments/NNNN.json record.

    `changes` is an opaque list supplied by the semantic owner — this
    module does not interpret it.
    """
    adir = _state(session_path) / f"{name}_amendments"
    adir.mkdir(parents=True, exist_ok=True)
    seq = len(list(adir.glob("*.json"))) + 1
    record = {
        "seq": seq,
        "artifact": name,
        "from_version": from_version,
        "to_version": to_version,
        "reason": reason,
        "changes": changes,
        "ts": _now(),
    }
    rfile = adir / f"{seq:04d}.json"
    rfile.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return rfile, record


def list_amendment_records(session_path: Path, name: str) -> List[Dict[str, Any]]:
    adir = _state(session_path) / f"{name}_amendments"
    if not adir.exists():
        return []
    out = []
    for p in sorted(adir.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out
