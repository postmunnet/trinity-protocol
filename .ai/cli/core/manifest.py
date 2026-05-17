"""Final-manifest builder for `ai close` (TRINITY_SESSION_CLOSE_SPEC_V1 §2-§3).

Owns:
    - resolve_tier(session_path) -> str
        Tier resolution priority per §4: sandbox profile > verifier reports >
        plan_envelope.tier > default WARM.

    - build_final_manifest(session_path, tier, *, graph_state_final, closed_at)
            -> dict
        Build manifest body per §2 covering DO/{dev,prod,snapshot}/, SANDBOX/,
        THINK/, CONTROL/ + the captures.* block when <session>/CAPTURE/
        exists. Result has deterministic manifest_sha256.

    - write_external_audit(session_path, manifest, *, audit_root, legacy_ndjson)
            -> Path
        Write audit/external/<UTC-date>/<session_id>.audit.json per §3 with
        audit_chain_anchor = {session_id, session_chain_head, last_seq,
        audit_export_ref(optional)}.

RecordProxy v1 (.ai/cli/core/recordproxy/**) is read-only ground truth here.
This module reads the per-session SQLite via sqlite3 directly — public
surface (CaptureStore/AuditWriter) is intentionally not imported to keep
this module independent of recordproxy module initialization.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

# Directories under the session root whose files get hashed into the manifest.
_MANIFEST_DIRS = ("DO/dev", "DO/prod", "DO/snapshot", "SANDBOX", "THINK", "CONTROL")

_TIERS = ("HOT", "WARM", "COLD")
_DEFAULT_TIER = "WARM"
_TIER_STRICTNESS = {"HOT": 0, "WARM": 1, "COLD": 2}


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _utc_now_rfc3339() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_tier(session_path: Path) -> str:
    """Tier resolution per Close Spec §4: sandbox profile > verifier reports
    (strictest wins) > plan_envelope.tier > default WARM."""

    # 1. Sandbox profile bound (highest priority)
    sandbox_path = session_path / ".state" / "sandbox_profile.json"
    if sandbox_path.is_file():
        try:
            sp = json.loads(sandbox_path.read_text(encoding="utf-8"))
            tier = sp.get("tier")
            if tier in _TIERS:
                return tier
        except Exception:
            pass

    # 2. Verifier reports — strictest tier wins
    state_dir = session_path / ".state"
    if state_dir.is_dir():
        tiers_seen = []
        for f in state_dir.glob("verify_*.json"):
            try:
                r = json.loads(f.read_text(encoding="utf-8"))
                t = r.get("tier")
                if t in _TIERS:
                    tiers_seen.append(t)
            except Exception:
                pass
        if tiers_seen:
            return max(tiers_seen, key=lambda x: _TIER_STRICTNESS[x])

    # 3. plan_envelope.tier
    envelope = session_path / "THINK" / "plan_envelope.json"
    if envelope.is_file():
        try:
            pe = json.loads(envelope.read_text(encoding="utf-8"))
            tier = pe.get("tier")
            if tier in _TIERS:
                return tier
        except Exception:
            pass

    return _DEFAULT_TIER


def _walk_artifacts(session_path: Path) -> list[dict]:
    """Walk files under MANIFEST_DIRS, sorted by relative path."""
    rows: list[dict] = []
    for sub in _MANIFEST_DIRS:
        root = session_path / sub
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("*")):
            if not f.is_file():
                continue
            # Skip the final_manifest.yaml itself if it already exists
            # (chicken-and-egg: manifest covers everything but itself).
            if f.name == "final_manifest.yaml" and f.parent.name == "CONTROL":
                continue
            try:
                rel = f.relative_to(session_path).as_posix()
            except ValueError:
                continue
            rows.append({
                "path": rel,
                "sha256": _sha256_file(f),
                "size_bytes": f.stat().st_size,
            })
    # Already sorted by sorted(root.rglob) per directory, but globally need
    # cross-directory sort:
    rows.sort(key=lambda r: r["path"])
    return rows


def _build_captures_block(session_path: Path) -> Optional[dict]:
    """Return captures.* block iff <session>/CAPTURE/capture.sqlite exists.
    None when CAPTURE/ absent (sessions predating RecordProxy v1)."""
    capture_root = session_path / "CAPTURE"
    sqlite_path = capture_root / "capture.sqlite"
    if not sqlite_path.is_file():
        return None

    capture_store_sha = _sha256_file(sqlite_path)
    capture_ids: list[str] = []
    try:
        conn = sqlite3.connect(str(sqlite_path))
        cur = conn.execute("SELECT capture_id FROM captures ORDER BY capture_id ASC")
        capture_ids = [r[0] for r in cur.fetchall()]
        conn.close()
    except Exception:
        # SQLite read failure yields empty capture_ids; still emit the block
        # so close can detect a CAPTURE/ that exists but is unreadable.
        pass

    blobs_root = capture_root / "blobs" / "sha256"
    blob_count = 0
    total_bytes = 0
    if blobs_root.is_dir():
        for f in blobs_root.rglob("*"):
            if f.is_file():
                blob_count += 1
                try:
                    total_bytes += f.stat().st_size
                except OSError:
                    pass

    refs_root = capture_root / "refs"
    ref_count = 0
    if refs_root.is_dir():
        ref_count = sum(1 for child in refs_root.iterdir() if child.is_file())

    block = {
        "capture_store": {
            "path": "CAPTURE/capture.sqlite",
            "sha256": capture_store_sha,
            "size_bytes": sqlite_path.stat().st_size,
        },
        "blobs_root": {
            "path": "CAPTURE/blobs/sha256",
            "blob_count": blob_count,
            "total_bytes": total_bytes,
        },
        "refs_root": {
            "path": "CAPTURE/refs",
            "ref_count": ref_count,
        },
        "capture_ids": capture_ids,
    }
    block["capture_manifest_sha256"] = hashlib.sha256(
        _canonical_json(block).encode("utf-8")
    ).hexdigest()
    return block


def _read_session_chain_head(session_path: Path) -> Tuple[Optional[str], Optional[int]]:
    """Read (session_chain_head, last_seq) from per-session SQLite. (None, None) if absent."""
    sqlite_path = session_path / "CAPTURE" / "capture.sqlite"
    if not sqlite_path.is_file():
        return None, None
    try:
        conn = sqlite3.connect(str(sqlite_path))
        cur = conn.execute(
            "SELECT seq, hash FROM audit_events ORDER BY seq DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None, None
        return row[1], int(row[0])  # (hash, seq)
    except Exception:
        return None, None


def build_final_manifest(
    session_path: Path,
    tier: str,
    *,
    graph_state_final: str = "DONE",
    closed_at: Optional[str] = None,
) -> dict:
    """Build final_manifest body per TRINITY_SESSION_CLOSE_SPEC_V1 §2.

    Args:
        session_path: directory under .ai/sessions/<...>
        tier: HOT / WARM / COLD
        graph_state_final: terminal state recorded in the manifest
        closed_at: optional RFC3339 string; defaults to UTC now

    Returns:
        Dict with manifest_sha256 set. captures.* block included iff
        <session>/CAPTURE/capture.sqlite exists.
    """
    if tier not in _TIERS:
        raise ValueError(f"tier must be in {_TIERS}; got {tier!r}")

    artifacts = _walk_artifacts(session_path)
    captures = _build_captures_block(session_path)
    chain_head, last_seq = _read_session_chain_head(session_path)

    body: dict = {
        "session_id": session_path.name,
        "closed_at": closed_at or _utc_now_rfc3339(),
        "tier": tier,
        "graph_state_final": graph_state_final,
        "artifacts": artifacts,
        "audit": {
            "session_chain_head": chain_head,
            "last_seq": last_seq,
            "capture_chain_consistent": chain_head is not None,
        },
    }
    if captures is not None:
        body["captures"] = captures

    body["manifest_sha256"] = hashlib.sha256(
        _canonical_json({k: v for k, v in body.items()}).encode("utf-8")
    ).hexdigest()
    return body


def write_external_audit(
    session_path: Path,
    manifest: dict,
    *,
    audit_root: Path,
    legacy_ndjson: Optional[Path] = None,
) -> Path:
    """Write `audit/external/<UTC-date>/<session_id>.audit.json` per Close Spec §3.

    Args:
        session_path: source session dir (used for session_id)
        manifest: the body from build_final_manifest (must have audit + tier)
        audit_root: parent directory (typically <repo>/audit/external)
        legacy_ndjson: optional path to .ai/audit/events.ndjson for cross-reference

    Returns:
        Path to the written audit JSON file.

    Raises:
        ValueError if manifest is missing required fields.
    """
    if "session_id" not in manifest or "audit" not in manifest or "tier" not in manifest:
        raise ValueError("manifest missing required fields (session_id/audit/tier)")

    session_id = manifest["session_id"]
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out_dir = audit_root / today
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{session_id}.audit.json"

    audit_chain_anchor: dict = {
        "session_id": session_id,
        "session_chain_head": manifest["audit"].get("session_chain_head"),
        "last_seq": manifest["audit"].get("last_seq"),
    }
    if legacy_ndjson is not None and legacy_ndjson.is_file():
        audit_chain_anchor["audit_export_ref"] = {
            "path": str(legacy_ndjson),
            "sha256": _sha256_file(legacy_ndjson),
        }

    payload = {
        "session_id": session_id,
        "tier": manifest["tier"],
        "final_state": manifest["graph_state_final"],
        "artifacts": manifest["artifacts"],
        "audit_chain_anchor": audit_chain_anchor,
    }
    if "captures" in manifest:
        payload["captures"] = {
            "capture_store_sha256": manifest["captures"]["capture_store"]["sha256"],
            "capture_ids": manifest["captures"]["capture_ids"],
            "capture_manifest_sha256": manifest["captures"]["capture_manifest_sha256"],
        }

    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return out_path


__all__ = [
    "build_final_manifest",
    "resolve_tier",
    "write_external_audit",
]
