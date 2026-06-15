"""Pre-epoch tolerance for audit verify-chain (2026-06-10).

Chains born under the bootstrap installer start with prev_hash="genesis"
and hash events with json.dumps(sort_keys=True) DEFAULT separators —
proven against example_client's real prefix. verify_chain must accept those with
FULL sha256 recomputation (no weaker link-only mode), keep failing on
tampered events of either era, and leave pure-modern chains untouched.
"""
from __future__ import annotations

import hashlib
import json

from cli.core.audit_replay import verify_chain


def _pre_epoch_event(etype: str, prev: str, details: dict) -> dict:
    body = {
        "timestamp": "2026-05-22T10:00:00Z",
        "type": etype,
        "details": details,
        "prev_hash": prev,
    }
    h = hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {**body, "hash": h}


def _modern_event(etype: str, prev: str, details: dict) -> dict:
    body = {
        "ts": "2026-06-10T10:00:00Z",
        "type": etype,
        "prev_hash": prev,
        "schema_version": "trinity.audit_event.v1",
        "session_id": None,
        "actor": "human",
        "details": details,
    }
    h = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**body, "hash": h}


def _example_client_shaped_chain() -> list[dict]:
    e0 = _pre_epoch_event("genesis", "genesis", {"note": "scaffold"})
    e1 = _pre_epoch_event("scaffold_complete", e0["hash"], {"files": 10})
    e2 = _pre_epoch_event("integration_merge", e1["hash"], {"merged": True})
    e3 = _modern_event("lll.invoked", e2["hash"], {"decided_by": "human"})
    e4 = _modern_event("session.created", e3["hash"], {"decided_by": "kernel"})
    return [e0, e1, e2, e3, e4]


def test_pre_epoch_prefix_chain_verifies() -> None:
    ok, errors = verify_chain(_example_client_shaped_chain(), chain_kind="legacy")
    assert ok, errors


def test_pre_epoch_chain_verifies_strict_types() -> None:
    ok, errors = verify_chain(
        _example_client_shaped_chain(), chain_kind="legacy", strict=True
    )
    assert ok, errors


def test_tampered_pre_epoch_event_still_fails() -> None:
    chain = _example_client_shaped_chain()
    chain[1]["details"]["files"] = 999  # mutate body, keep stored hash
    ok, errors = verify_chain(chain, chain_kind="legacy")
    assert not ok
    assert any("hash mismatch" in e for e in errors)


def test_tampered_modern_event_still_fails() -> None:
    chain = _example_client_shaped_chain()
    chain[4]["details"]["decided_by"] = "attacker"
    ok, errors = verify_chain(chain, chain_kind="legacy")
    assert not ok


def test_pure_modern_chain_unchanged() -> None:
    e0 = _modern_event("lll.invoked", "0", {"decided_by": "human"})
    e1 = _modern_event("session.created", e0["hash"], {"decided_by": "kernel"})
    ok, errors = verify_chain([e0, e1], chain_kind="legacy")
    assert ok, errors


def test_modern_chain_with_genesis_zero_still_required_at_start() -> None:
    # A chain that starts with a non-genesis prev_hash must still fail.
    e0 = _modern_event("lll.invoked", "deadbeef", {"decided_by": "human"})
    ok, errors = verify_chain([e0], chain_kind="legacy")
    assert not ok
    assert any("prev_hash mismatch" in e for e in errors)
