"""Root of Trust helper — Phase 14 genesis manifest + ratification.

Pure-ish builders + verifiers for the §3 GenesisManifest and §5
RatificationArtifact mirrors in `root_of_trust_contract.py`. The only
I/O is reading Layer 0 artifacts to compute their sha256 digest.

Article XX: no module-level side effects. No audit emission, no state
mutation — callers (Kernel / Phase 14 wiring sessions) emit
`root.tier.pre_migration_validated` / `root.ratification_chain.appended`.

Spec anchors:
- docs/specs/TRINITY_ROOT_OF_TRUST_SPEC_V1.md §3-§8
- docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md §A
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cli.core.root_of_trust_contract import (
    MANIFEST_VERSION,
)


# Crockford base32 (mirror lease_minter — no external dep).
_CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_z(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ulid() -> str:
    """Generate a 26-char Crockford-base32 ULID."""
    now_ms = int(_now_utc().timestamp() * 1000) & ((1 << 48) - 1)
    rand_80 = secrets.randbits(80)
    value = (now_ms << 80) | rand_80
    out: List[str] = []
    for _ in range(26):
        out.append(_CROCKFORD_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


# ─────────── Layer 0 hashing ───────────


def compute_layer0_sha256(path: Path) -> str:
    """Read `path` and return lowercase 64-char sha256 hex digest."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_layer0_entry(
    *,
    path: str,
    role: str,
    authority_class: str,
    project_root: Path,
) -> Dict[str, Any]:
    """Build a Layer0Entry dict with sha256 computed from disk."""
    abs_path = (project_root / path).resolve()
    if not abs_path.is_file():
        raise FileNotFoundError(
            f"Layer 0 artifact {path!r} not found under {project_root}"
        )
    return {
        "path": path,
        "sha256": compute_layer0_sha256(abs_path),
        "role": role,
        "authority_class": authority_class,
    }


# ─────────── GenesisManifest builder ───────────


def make_genesis_manifest(
    *,
    asserted_by: str,
    layer_0_artifacts: List[Dict[str, Any]],
    crypto_status: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Construct a GenesisManifest dict per spec §3.

    Default `crypto_status` matches the dev-workstation tier_1_hmac mode
    (Addendum v1.0.1 §A) — no key_id, no verified_at until first verify.
    """
    asserted = now if now is not None else _now_utc()
    if crypto_status is None:
        crypto_status = {
            "tier": "tier_1_hmac",
            "algorithm": "none",
            "key_id": None,
            "verified_at": None,
        }
    return {
        "manifest_version": MANIFEST_VERSION,
        "asserted_at": _iso_z(asserted),
        "asserted_by": asserted_by,
        "layer_0_artifacts": list(layer_0_artifacts),
        "crypto_status": dict(crypto_status),
        "ratification_chain": [],
    }


# ─────────── Layer 0 verifier ───────────


def verify_layer0_against_manifest(
    project_root: Path, manifest: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Recompute sha256 for each layer_0_artifacts entry; return per-entry result.

    Each result dict: {path, expected, actual, ok}.
    """
    results: List[Dict[str, Any]] = []
    for entry in manifest.get("layer_0_artifacts", []) or []:
        path = entry["path"]
        expected = entry["sha256"]
        abs_path = (project_root / path).resolve()
        if not abs_path.is_file():
            results.append(
                {"path": path, "expected": expected, "actual": None, "ok": False}
            )
            continue
        actual = compute_layer0_sha256(abs_path)
        results.append(
            {
                "path": path,
                "expected": expected,
                "actual": actual,
                "ok": (actual == expected),
            }
        )
    return results


# ─────────── ratification chain append ───────────


def append_ratification(
    manifest: Dict[str, Any],
    *,
    ratified_by: str,
    constitutional_articles_invoked: List[str],
    evidence_refs: Optional[List[str]] = None,
    audit_event_id: str = "",
    is_genesis: bool = False,
    now: Optional[datetime] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Append a ratification_id to the manifest's chain.

    Returns (updated_manifest, ratification_artifact).
    """
    rid_body = _ulid()
    ratification_id = f"rat_genesis_{rid_body}" if is_genesis else f"rat_{rid_body}"
    ts = _iso_z(now if now is not None else _now_utc())

    updated = dict(manifest)
    chain = list(updated.get("ratification_chain") or [])
    chain.append(ratification_id)
    updated["ratification_chain"] = chain

    artifact = {
        "ratification_id": ratification_id,
        "manifest_id": f"{updated.get('manifest_version', MANIFEST_VERSION)}:sha256:pending",
        "ts": ts,
        "ratified_by": ratified_by,
        "evidence_refs": list(evidence_refs or []),
        "constitutional_articles_invoked": list(constitutional_articles_invoked),
        "audit_event_id": audit_event_id,
    }
    return updated, artifact


__all__ = [
    "compute_layer0_sha256",
    "make_layer0_entry",
    "make_genesis_manifest",
    "verify_layer0_against_manifest",
    "append_ratification",
]
