"""Conformance tests for the Root of Trust contract (Phase 14).

Spec: docs/specs/TRINITY_ROOT_OF_TRUST_SPEC_V1.md §3-§8

Tier-0/1 deterministic. Asserts: MANIFEST_VERSION pin, LAYER_0_PATHS == 9
canonical doc set, SIGNATURE_TIERS == 3 tiers, CRYPTO_ALGORITHMS coverage,
VERIFY_FAILURE_CODES == 4 codes, dataclass surfaces.
"""
from __future__ import annotations

import dataclasses
import pathlib

from cli.core.root_of_trust_contract import (
    AUTHORITY_CLASSES,
    CRYPTO_ALGORITHMS,
    CryptoStatus,
    GenesisManifest,
    LAYER_0_PATHS,
    Layer0Entry,
    MANIFEST_VERSION,
    RatificationArtifact,
    ROT_AUDIT_EVENTS,
    SIGNATURE_TIERS,
    VERIFY_FAILURE_CODES,
)


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


# ─────────── §3 — manifest version pin ───────────


def test_manifest_version_is_one_dot_zero() -> None:
    assert MANIFEST_VERSION == "1.0"


# ─────────── §4 — Layer 0 closed set (9 docs) ───────────


def test_layer_0_paths_count_nine() -> None:
    assert len(LAYER_0_PATHS) == 9


def test_layer_0_paths_all_under_constitution() -> None:
    """All Layer 0 documents live under docs/constitution/."""
    for path in LAYER_0_PATHS:
        assert path.startswith("docs/constitution/"), path


def test_layer_0_paths_include_constitution() -> None:
    assert "docs/constitution/TRINITY_CONSTITUTION_V1.md" in LAYER_0_PATHS


def test_layer_0_paths_include_ritual_constitution() -> None:
    assert "docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md" in LAYER_0_PATHS


def test_layer_0_paths_include_four_addendums() -> None:
    """4 addendums (v1.0.1, v1.0.2, v1.0.3, v1.0.4) per spec §4."""
    addendums = [p for p in LAYER_0_PATHS if "addendum" in p.lower()]
    assert len(addendums) == 4


def test_layer_0_paths_include_three_contracts() -> None:
    """3 contracts: Organ Map, Ritual Contract, RRR Delegation Contract."""
    contracts = [p for p in LAYER_0_PATHS if "/contracts/" in p]
    assert len(contracts) == 3


def test_layer_0_paths_exist_on_disk() -> None:
    """Every declared Layer 0 path MUST exist on disk in the repo."""
    missing = [p for p in LAYER_0_PATHS if not (PROJECT_ROOT / p).is_file()]
    assert not missing, f"Layer 0 paths absent from disk: {missing}"


# ─────────── §3.2 — authority classes ───────────


def test_authority_classes_non_empty_frozenset() -> None:
    assert isinstance(AUTHORITY_CLASSES, frozenset)
    assert len(AUTHORITY_CLASSES) >= 4


# ─────────── §6 — signature tiers (3 tiers) ───────────


def test_signature_tiers_canonical_set() -> None:
    assert SIGNATURE_TIERS == frozenset({
        "tier_1_hmac",
        "tier_2_public_key",
        "tier_3_hardware",
    })


def test_signature_tiers_count_three() -> None:
    assert len(SIGNATURE_TIERS) == 3


# ─────────── §6 — crypto algorithms ───────────


def test_crypto_algorithms_includes_tier_1_hmac() -> None:
    assert "HMAC-SHA256" in CRYPTO_ALGORITHMS


def test_crypto_algorithms_includes_tier_2_ed25519() -> None:
    assert "Ed25519" in CRYPTO_ALGORITHMS


def test_crypto_algorithms_count_at_least_four() -> None:
    assert len(CRYPTO_ALGORITHMS) >= 4


# ─────────── §8 — verify failure codes (4 codes) ───────────


def test_verify_failure_codes_canonical_set() -> None:
    assert VERIFY_FAILURE_CODES == frozenset({
        "BADPATH", "BADREAD", "BADHASH", "BADKEY",
    })


def test_verify_failure_codes_count_four() -> None:
    assert len(VERIFY_FAILURE_CODES) == 4


# ─────────── §8.5 — audit events ───────────


def test_rot_audit_events_non_empty_frozenset() -> None:
    assert isinstance(ROT_AUDIT_EVENTS, frozenset)
    assert len(ROT_AUDIT_EVENTS) >= 4


def test_rot_audit_events_include_verify_pass_fail() -> None:
    assert "root.verify.pass" in ROT_AUDIT_EVENTS
    assert "root.verify.fail" in ROT_AUDIT_EVENTS


def test_rot_audit_events_include_ratification_signed() -> None:
    assert "ratification.signed" in ROT_AUDIT_EVENTS


# ─────────── dataclass surfaces ───────────


def test_layer_0_entry_fields() -> None:
    fields = {f.name for f in dataclasses.fields(Layer0Entry)}
    assert {"path", "sha256", "role", "authority_class"}.issubset(fields)


def test_crypto_status_fields() -> None:
    fields = {f.name for f in dataclasses.fields(CryptoStatus)}
    assert {"tier", "algorithm", "key_id", "verified_at"}.issubset(fields)


def test_crypto_status_key_id_defaults_null() -> None:
    """Tier 1 HMAC dev workstation MAY have key_id=null."""
    cs = CryptoStatus(tier="tier_1_hmac", algorithm="HMAC-SHA256")
    assert cs.key_id is None
    assert cs.verified_at is None


def test_genesis_manifest_fields() -> None:
    fields = {f.name for f in dataclasses.fields(GenesisManifest)}
    required = {"manifest_version", "asserted_at", "asserted_by",
                "layer_0_artifacts", "crypto_status", "ratification_chain"}
    assert required.issubset(fields)


def test_ratification_artifact_fields() -> None:
    fields = {f.name for f in dataclasses.fields(RatificationArtifact)}
    required = {"ratification_id", "manifest_id", "ts", "ratified_by",
                "evidence_refs", "constitutional_articles_invoked", "audit_event_id"}
    assert required.issubset(fields)


# ─────────── module passivity (Article XX) ───────────


def test_module_re_import_idempotent() -> None:
    import importlib
    import cli.core.root_of_trust_contract as rot

    importlib.reload(rot)
    assert hasattr(rot, "LAYER_0_PATHS")
