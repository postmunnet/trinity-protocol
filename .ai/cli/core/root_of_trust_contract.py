"""Root of Trust / Ratification organ — Article XVI + Article XXIX declarative contract.

Spec anchors:
- docs/specs/TRINITY_ROOT_OF_TRUST_SPEC_V1.md (Phase 14, DRAFT v1.0 — 872 lines)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §17 (Root of Trust / Ratification)
- docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md §A (GENESIS_TRUST_ASSUMED)

This module is **declarative only** (Article XX Passive Core). It encodes
the Phase 14 spec §3-§8 surface — genesis_manifest shape, Layer 0 closed
set, 3-tier signature roadmap, 5-step verification procedure — so the
future manifest writer + `ai root verify` command can bind against
machine-checkable contracts.

Article XVI anchor: closed frozensets — LAYER_0_PATHS, SIGNATURE_TIERS,
CRYPTO_ALGORITHMS, VERIFY_FAILURE_CODES — unknown path / tier / algorithm
/ failure code = denied.

Article XXIX anchor: tier migration (HMAC→Ed25519→TPM) is a constitutional-
tier amendment per Addendum v1.0.4. The migration discipline is
spec-anchored; this module enumerates the tier vocabulary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────── §3 — Manifest version pin ───────────

MANIFEST_VERSION: str = "1.0"


# ─────────── §4 — Layer 0 closed artifact set (9 docs) ───────────
# Verbatim from spec §4 — the constitutional Layer 0 closed set. Source of
# truth = spec; the genesis manifest's layer_0_artifacts[] MUST enumerate
# exactly these paths (under docs/constitution/).

LAYER_0_PATHS: frozenset = frozenset({
    "docs/constitution/TRINITY_CONSTITUTION_V1.md",
    "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md",
    "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md",
    "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md",
    "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md",
    "docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md",
    "docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md",
    "docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md",
    "docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md",
})


# ─────────── §3.2 — Layer 0 entry authority classes ───────────

AUTHORITY_CLASSES: frozenset = frozenset({
    "constitution",
    "addendum",
    "ritual_constitution",
    "organ_map",
    "ritual_contract",
    "rrr_delegation_contract",
})


# ─────────── §6 — Signature tier roadmap (3 tiers) ───────────

SIGNATURE_TIERS: frozenset = frozenset({
    "tier_1_hmac",         # current — symmetric HMAC-SHA256
    "tier_2_public_key",   # future — Ed25519 / COSE_Sign1
    "tier_3_hardware",     # future — TPM / Secure Enclave / Cloud HSM
})


# ─────────── §6 — Cryptographic algorithm vocabulary ───────────

CRYPTO_ALGORITHMS: frozenset = frozenset({
    "HMAC-SHA256",                       # tier 1
    "Ed25519",                            # tier 2
    "COSE_Sign1+Ed25519",                 # tier 2 alt
    "ECDSA-P256-SecureEnclave",           # tier 3 example
})


# ─────────── §8 — Verification failure codes (4 codes) ───────────

VERIFY_FAILURE_CODES: frozenset = frozenset({
    "BADPATH",   # artifact path not in manifest's layer_0_artifacts[]
    "BADREAD",   # IO failure reading the artifact bytes
    "BADHASH",   # recomputed sha256 != manifest entry's sha256
    "BADKEY",    # signature verify failed (tier 2+); HMAC verify failed (tier 1 signed)
})


# ─────────── Audit events (per spec §8.5 + §6.2.1 + Organ Map §17) ───────────

ROT_AUDIT_EVENTS: frozenset = frozenset({
    "root.verify.pass",
    "root.verify.fail",
    "ratification.signed",
    "ratification.revoked",
    "root.tier.declared",
    "root.tier.pre_migration_validated",
})


# ─────────── §3.2 — Layer0Entry dataclass ───────────


@dataclass
class Layer0Entry:
    """One entry in the genesis manifest's layer_0_artifacts[] array.

    Per spec §3.2 — each Layer 0 document is pinned by path + sha256 + role
    + authority_class. Reading the artifact and recomputing sha256 against
    this entry is the §8 verification procedure.
    """

    path: str                                        # one of LAYER_0_PATHS
    sha256: str                                      # ^[0-9a-f]{64}$
    role: str
    authority_class: str                             # one of AUTHORITY_CLASSES


# ─────────── §3.3 — CryptoStatus dataclass ───────────


@dataclass
class CryptoStatus:
    """Per spec §3.3 — pins the manifest's current signature tier + algorithm.

    `key_id` MAY be null at tier_1_hmac (declarative trust, no manifest-HMAC
    signing for dev workstations). REQUIRED at tier_2_public_key and above.
    `verified_at` is null until first successful §8 verify call.
    """

    tier: str                                        # one of SIGNATURE_TIERS
    algorithm: str                                   # one of CRYPTO_ALGORITHMS
    key_id: Optional[str] = None
    verified_at: Optional[str] = None                # RFC3339 UTC, null until first verify


# ─────────── §3 — GenesisManifest dataclass ───────────


@dataclass
class GenesisManifest:
    """Authoritative Python mirror of `GENESIS_TRUST_ASSUMED.json` per spec §3.

    Written once at genesis (declared by operator); read by verifier on every
    Layer 0 consume. Amendments to layer_0_artifacts[] are constitutional-
    tier per Article XXIX (each amendment appends to ratification_chain[]).
    """

    manifest_version: str                            # const MANIFEST_VERSION
    asserted_at: str                                 # RFC3339 UTC
    asserted_by: str                                 # "operator:<stable-id>"
    layer_0_artifacts: List[Layer0Entry] = field(default_factory=list)
    crypto_status: Optional[CryptoStatus] = None
    ratification_chain: List[str] = field(default_factory=list)   # ULIDs append-only


# ─────────── §5 — RatificationArtifact dataclass ───────────


@dataclass
class RatificationArtifact:
    """Per spec §5 — Article XXIX 6-step procedure witness for a Layer 0 amendment.

    Each amendment to a Layer 0 document emits one RatificationArtifact
    cross-referencing the constitutional articles invoked + the operator
    who signed off + the audit event recording the amendment.
    """

    ratification_id: str                             # "rat_<ulid>" or "rat_genesis_<ulid>"
    manifest_id: str                                 # "1.0:sha256:<hex>"
    ts: str                                          # RFC3339 UTC
    ratified_by: str                                 # "operator:<id>"
    evidence_refs: List[str] = field(default_factory=list)
    constitutional_articles_invoked: List[str] = field(default_factory=list)
    audit_event_id: str = ""


__all__ = [
    "MANIFEST_VERSION",
    "LAYER_0_PATHS",
    "AUTHORITY_CLASSES",
    "SIGNATURE_TIERS",
    "CRYPTO_ALGORITHMS",
    "VERIFY_FAILURE_CODES",
    "ROT_AUDIT_EVENTS",
    "Layer0Entry",
    "CryptoStatus",
    "GenesisManifest",
    "RatificationArtifact",
]
