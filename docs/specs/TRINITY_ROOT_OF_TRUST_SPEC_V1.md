---
title: "Trinity Root of Trust Spec v1.0"
version: "1.0"
status: "draft"
phase: "14"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes: ["(none -- first canonical version)"]
constitutional-anchor: ["Article XXV", "Article XXIX", "Article III", "Article IV", "Article XIII", "Article XVI", "Article XX"]
amendment-policy: "Article XXIX -- explicit proposal + rationale + impact analysis + human approval + version bump + audit entry."
---

# TRINITY_ROOT_OF_TRUST_SPEC_V1

**Status:** DRAFT v1 (first canonical version -- pending verifier review + ddd)
**Phase:** 14 -- Root of Trust / Ratification
**Organ:** #17 (Root of Trust, genesis-only signing authority -- per Transport Boundary Spec §2 Authority/Transport organ table)
**Constitutional rank:** 5 -- Workflow Contract (per Article XXV)
**Date:** 2026-05-15

## Section 0 -- Rank-5 Authority Disclaimer (Article XXV)

[normative-description]

This document is a **Workflow Contract**. It ranks fifth in the constitutional priority order (full quote in Section 1.2). It is **void where it conflicts with any higher-ranked instrument** -- the parent Constitution, the Ritual Constitution, Canonical Policies under `.ai/policies/**`, and Kernel State Rules under `.ai/cli/**`.

This Spec does **not** mutate any policy file. It declares:

1. The genesis trust posture Trinity boots from before any cryptographic verifier exists.
2. The schema for the **GENESIS_TRUST_ASSUMED** manifest -- the hash-pinned ledger of Layer 0 artifacts.
3. The schema for the **root ratification artifact** -- the per-amendment record produced when Layer 0 changes.
4. The signature roadmap that progresses from HMAC-SHA256 (Tier 1, already operational per Phase 9) to public-key (Tier 2) to hardware-backed (Tier 3) anchors.
5. The verification procedure every Trinity component MUST run when handed an artifact that claims Layer 0 authority.

Amendments to this Spec follow Article XXIX as operationalised by Addendum v1.0.4 (3-tier classification, trace-to-failure, pinned audit format). Any change to a Layer 0 artifact (Constitution v1.0, its Addendums, the Ritual Constitution, or any contract under `docs/constitution/contracts/`) is a **constitutional-tier** amendment per Addendum v1.0.4 §XXIX.3 and cascades into a manifest update governed by Section 10 of this Spec.

---

## Section 1 -- Purpose & Constitutional Anchor

### 1.1 Why a Root of Trust Spec exists

[normative-description]

Trinity's entire governance posture rests on a single load-bearing assumption: **the canonical documents are what they claim to be**. The Constitution has authority because the operator declares it canonical. The verifier has authority because the Constitution authorises Article VIII verification. The kernel rejects illegal transitions because the Constitution authorises Article V kernel governance.

But none of those declarations are self-validating. There is a recursive boot problem: **what verifies the verifier?** The honest answer in v1 is: **the operator does, declaratively, at genesis**. This Spec pins that declarative trust into a hash-pinned manifest so that:

1. Any later artifact claiming Layer 0 authority can be **mechanically verified** against the manifest by recomputing SHA-256.
2. Any **silent rewrite** of a Layer 0 artifact becomes detectable -- the recomputed SHA-256 will diverge from the manifest entry.
3. The schema is **crypto-ready**: as Trinity progresses from single-operator HMAC (Tier 1) toward cross-host public-key (Tier 2) toward hardware-anchored (Tier 3) signing, the manifest accommodates each tier without re-architecting.

The Constitution v1.0 frontmatter (`amendment-policy:` line 14) is the **genesis anchor** of this Spec. That single line -- "Article XXIX -- explicit proposal + rationale + impact analysis + human approval + version bump + audit entry" -- is the canonical declaration that Layer 0 artifacts are governed, not free-floating.

### 1.2 Article XXV -- Constitutional Priority Order (verbatim, PRIMARY ANCHOR)

[normative-description]

Article XXV of the Trinity Constitution v1.0 reads in full:

```text
Article XXV -- Constitutional Priority Order

When conflicts occur, priority order is:

Constitution
-> Canonical Policies
-> Kernel State Rules
-> Workflow Contracts
-> Tool Contracts
-> Runtime Requests
-> Model Suggestions

Lower layers MUST NOT override higher layers.
```

The CLAUDE.md operational expansion (per Addendum v1.0.2) inserts the Ritual Constitution between the parent Constitution and Canonical Policies; the priority order Trinity actually runs is:

(Note: `CLAUDE.md` is the project entrypoint document, present at the repo root as a sibling to `CONSTITUTION.md`; it is loaded automatically by Claude Code when started in this repo.)


```text
Constitution
-> Ritual Constitution       (docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md, v1.1 RATIFIED)
-> Canonical Policies        (.ai/policies/**)
-> Kernel State Rules        (.ai/cli/**, graph transitions)
-> Workflow Contracts        (THIS DOCUMENT)
-> Tool Contracts            (.ai/tools.yaml + sibling tool contracts)
-> Runtime Requests
-> Model Suggestions         (Claude's own opinion, ranked LAST)
```

**Operational consequence for Root of Trust:** Layer 0 of the manifest in Section 4 corresponds **exactly** to the upper two tiers of this stack -- the Constitution, its Addendums, the Ritual Constitution, and the contracts under `docs/constitution/contracts/`. Canonical Policies under `.ai/policies/**` are **rank 3** and are **not** Layer 0 -- they are governed by their own change discipline (verifier-rules.yaml, safety.yaml, gates.yaml ratification cadence). Layer 0 is reserved for the documents that **define the right to govern**, not the day-to-day rules.

### 1.3 Article XXIX -- Constitutional Amendment (verbatim, PRIMARY ANCHOR)

[normative-description]

Article XXIX of the Trinity Constitution v1.0 reads in full:

```text
Article XXIX -- Constitutional Amendment

The Constitution MUST NOT be silently rewritten.

Amendments require:

explicit proposal
rationale
impact analysis
human approval
version bump
audit entry

Prior versions MUST remain inspectable.
```

Addendum v1.0.4 operationalises the six-step procedure into three **tiers** (editorial, operational, constitutional) with tier-differentiated trace-to-failure obligations and a pinned audit-entry format under `.ai/audit/events.ndjson`. Every Layer 0 mutation is a **constitutional-tier** amendment per Addendum v1.0.4 §XXIX.3 -- it adds, removes, or modifies an Article (or operationalises one). The root-ratification artifact in Section 5 is the **durable evidence** that the six steps executed for that amendment; it is the Layer 0 counterpart to the audit event Addendum v1.0.4 §XXIX.5 demands.

### 1.4 Supporting Articles (operational relevance)

[normative-description]

The following Articles bind specific obligations onto this Spec:

#### Article III -- AI Cannot Govern Itself (operational relevance)

```text
AI MUST NOT:
- declare final completion
- approve its own work
- verify its own correctness
- bypass verifier approval
- bypass governance gates
- forge authority
- redefine workflow state
- rewrite constitutional policy
```

A Trinity AI that mutates a Layer 0 artifact (e.g. silently amends `TRINITY_CONSTITUTION_V1.md`) is **rewriting constitutional policy** -- an Article III violation. The manifest in Section 3 is the mechanical detection layer: a recomputed SHA-256 that diverges from the manifest entry exposes the silent rewrite at the next verification pass (Section 8).

#### Article IV -- Separation of Responsibilities (operational relevance)

```text
Kernel    = governance, state, gates, authority
Planner   = reasoning, plans, risk analysis
Executor  = bounded action, mutation, execution artifacts
Verifier  = independent validation
Memory    = evidence retrieval
Audit     = immutable history
Retro     = post-work reflection
Transport = message delivery only
```

The Root of Trust organ (#17 per Transport Boundary Spec §2's organ table) is a distinct organ -- it is **not** the Kernel and **not** the Verifier. Its sole responsibility is to **sign canonical artifacts** at genesis and at each Layer 0 amendment. Role collapse -- e.g. the Kernel issuing its own root-of-trust manifest without Operator authorisation -- is a constitutional violation per Article IV.

#### Article XIII -- Human Authority (operational relevance)

```text
Humans remain the highest authority.
Human approval MUST exist as an artifact.
```

The genesis manifest's `asserted_by` field (Section 3) and the root ratification artifact's `ratified_by` field (Section 5) MUST resolve to a human operator id. Crypto signatures, where present (Tier 2/Tier 3 of the roadmap), are **delegated proof** of that human authority -- they do not replace it. A Tier 2 Ed25519 signature without a corresponding human ratification artifact is **incomplete**: per Article XIII, "Human approval MUST exist as an artifact" -- the cryptographic envelope is the wrapper, not the authority itself.

#### Article XVI -- Least Authority (operational relevance)

```text
Every component MUST operate with minimum required authority.
Unknown authority MUST be treated as denied authority.
```

A signing key whose `key_id` does not resolve through the manifest's `ratification_chain` (Section 3) is **unknown authority**. Section 8's verification procedure MUST refuse such artifacts with `root.verify.fail` -- not "warn and continue," not "log and proceed." The Least Authority discipline forbids any fallback that promotes unknown to known.

#### Article XX -- Passive Core Principle (operational relevance)

```text
Core Trinity systems act only through explicit invocation.
Core systems MUST NOT:
- self-trigger
- self-expand authority
- silently mutate policy
- rewrite themselves recursively
```

The Root of Trust organ does **not** run in the background. There is no daemon, no cron, no auto-rotation. The manifest is recomputed only when a kernel command (Section 8) explicitly invokes the verifier, or when an Article XXIX amendment lands and triggers a Section 10 cascade. A Tier 3 hardware-backed key MAY be polled by a kernel verifier on request -- but never on its own initiative.

---

## Section 2 -- The Trust Boot Problem

### 2.1 What does "trusted" mean before crypto exists?

[normative-description]

Before any cryptographic primitive is in scope, "trusted" means **declarative trust asserted by the operator and recorded in a hash-pinned manifest**. The chain runs:

```text
Operator -> declares Constitution v1.0 canonical
         -> writes GENESIS_TRUST_ASSUMED manifest (Section 3)
         -> manifest hash-pins each Layer 0 artifact
         -> any later artifact claiming Layer 0 authority
              is verified by recomputing SHA-256 (Section 8)
              and comparing against the manifest entry
```

The manifest itself is **not** signed at Tier 0 -- it is the genesis anchor, by definition unsignable from inside the system that depends on it. Its trust comes from the operator's explicit ratification act, captured as a root-ratification artifact (Section 5) that an external observer can audit. As the system progresses to Tier 2 (public-key), the manifest will gain a detached signature; at Tier 3 (hardware-backed), the signing key itself becomes externally attestable.

### 2.2 Why Trinity declares trust rather than computes it

[normative-description]

A pure computational trust model would require an external root certificate authority (e.g. a public CA, a TPM endorsement key, a vendor-attested HSM) that Trinity could anchor to. Trinity v1 deliberately does **not** depend on such an authority for two reasons:

1. **Single-operator deployment.** The threat model in v1 (per Transport Boundary Spec §1.4) is a single operator on trusted hardware. Importing a CA dependency adds attack surface (CA compromise, certificate revocation timing) that is disproportionate to the threat being mitigated.
2. **Schema-first discipline (Article XX, Passive Core).** Trinity declares the trust **schema** now and plugs in the **crypto** later. The schema is what governs; the crypto is what verifies. Conflating the two would force a v1 commitment to a specific cryptographic stack that may not survive a 5-year horizon.

The Constitution v1.0 frontmatter's `amendment-policy:` line is the genesis anchor: it states, in plain text, that the Constitution is governed by Article XXIX. Trinity boots from the assertion that this line is true. Every subsequent artifact descends from that assertion. The manifest in Section 3 makes the descent **machine-checkable**.

### 2.3 v1.0 Threat Model Out-of-Scope (normative)

[normative-description]

The v1.0 threat model explicitly does **not** cover:

- **Operator compromise (Tier 1).** A compromised operator workstation can mutate Layer 0 artifacts and re-emit a fresh manifest; Tier 1 declarative trust cannot detect this. Mitigation deferred to Tier 2/Tier 3 (Section 6) where signing keys gain cross-host or hardware backing.
- **Supply-chain attacks (git repo poisoning pre-genesis).** A poisoned clone before the operator runs the genesis-manifest writer pins the poisoned bytes as canonical. Mitigation requires out-of-band attestation of the genesis commit hash (future addendum surface).
- **Transport-layer MITM.** Covered by Phase 9 HMAC discipline (TRINITY_TRANSPORT_BOUNDARY_SPEC_V1 Sec. 4); not re-derived in this Spec.

### 2.4 [non-normative-example] -- the boot sequence in practice

```text
1. Operator clones the Trinity repo at a known commit hash.
2. Operator runs the genesis-manifest writer (manual command, Section 3.4).
3. Writer reads Layer 0 artifacts (Section 4), computes SHA-256 of each,
   writes GENESIS_TRUST_ASSUMED manifest with manifest_version="1.0",
   asserted_by=<operator id>, asserted_at=<timestamp>.
4. Operator emits the genesis root ratification artifact (Section 5)
   recording the act and its evidence.
5. Kernel boots; first read of any Layer 0 artifact passes through the
   verification procedure (Section 8); manifest mismatch refuses the boot.
```

---

## Section 3 -- GENESIS_TRUST_ASSUMED Manifest Schema

### 3.1 Field-by-field schema (normative)

[normative-description]

The GENESIS_TRUST_ASSUMED manifest is a single JSON document at the canonical path `docs/constitution/GENESIS_TRUST_ASSUMED.json` (the path is reserved here; emission is deferred per the Acceptance section). Required fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `manifest_version` | string | yes | const `"1.0"` for this Spec; future versions require Article XXIX amendment |
| `asserted_at` | string (RFC3339 UTC) | yes | When the operator declared genesis trust |
| `asserted_by` | string | yes | Operator id; format `"operator:<stable-id>"` (e.g. `"operator:founder"`) |
| `layer_0_artifacts` | array of objects | yes | One entry per Layer 0 document; shape pinned in §3.2 |
| `ratification_chain` | array of objects | yes | Append-only chain of root ratification artifact ids that have updated this manifest; genesis entry is the manifest's own ratification id |
| `crypto_status` | object | yes | Current signature tier; shape pinned in §3.3 |

### 3.2 layer_0_artifacts entry shape (normative)

[normative-description]

Each entry in `layer_0_artifacts` MUST carry these fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `path` | string | yes | Repo-relative POSIX path (e.g. `"docs/constitution/TRINITY_CONSTITUTION_V1.md"`) |
| `sha256` | string | yes | Lowercase hex SHA-256 of the file's bytes (whitespace-significant, no normalisation) |
| `role` | string | yes | One of `"constitution"`, `"addendum"`, `"ritual_constitution"`, `"organ_map"`, `"contract"` |
| `authority_class` | string | yes | One of `"layer_0_canonical"` (parent Constitution + Ritual Constitution) or `"layer_0_supporting"` (Addendums + contracts) |

Rationale per field:

- **`path`** anchors the artifact to a deterministic location -- the verifier can resolve it without ambiguity. Renaming a Layer 0 file is a constitutional-tier amendment that updates the manifest.
- **`sha256`** is the **mechanical** trust anchor. Whitespace-significant means a single trailing newline change invalidates the entry -- this is intentional. Layer 0 documents are not free to reformat silently.
- **`role`** lets the verifier route different artifact types through different validators in future tiers (e.g. a Ritual Constitution v1.1 carries different schema obligations than an Addendum).
- **`authority_class`** distinguishes the **two top-tier ranks** (parent Constitution + Ritual Constitution) from their **supporting documents** (Addendums + contracts). A Layer 0 supporting document amendment MAY be operational-tier; a Layer 0 canonical amendment is constitutional-tier without exception.

### 3.3 crypto_status object shape (normative)

[normative-description]

The `crypto_status` object MUST carry:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `tier` | string | yes | One of `"tier_1_hmac"`, `"tier_2_public_key"`, `"tier_3_hardware"` |
| `algorithm` | string | yes | Algorithm identifier; v1 with Tier 1 pins `"HMAC-SHA256"` to align with Phase 9 |
| `key_id` | string \| null | conditional | Required for Tier 2/Tier 3; null permitted at Tier 1 declarative posture |
| `verified_at` | string (RFC3339 UTC) \| null | conditional | Last successful Section 8 verification; null permitted if never verified |

The schema accommodates all three tiers from day one. The crypto layer is plug-in (Section 6); the schema is fixed.

### 3.4 verified_at semantics (normative)

[normative-description]

The `crypto_status.verified_at` field carries the timestamp of the **last successful Section 8 verification call**, regardless of whether that call resulted in a tier-promotion outcome. It is `null` until the first successful verify; thereafter it is updated on every successful verify call (including no-op revalidations of the same tier). A failed verify (any `BADPATH`/`BADREAD`/`BADHASH`/`BADKEY`) does NOT update `verified_at`. Cross-link: Sec. 8.2 emits the verify call that updates this field. See also Sec. 4.3 (sha256 placeholder usage at this Spec stage).

### 3.5 [non-normative-example] -- minimal manifest skeleton

```json
{
  "manifest_version": "1.0",
  "asserted_at": "2026-05-15T12:00:00Z",
  "asserted_by": "operator:founder",
  "layer_0_artifacts": [
    {
      "path": "docs/constitution/TRINITY_CONSTITUTION_V1.md",
      "sha256": "<sha256-placeholder>",
      "role": "constitution",
      "authority_class": "layer_0_canonical"
    }
  ],
  "ratification_chain": ["rat_genesis_<ulid>"],
  "crypto_status": {
    "tier": "tier_1_hmac",
    "algorithm": "HMAC-SHA256",
    "key_id": null,
    "verified_at": null
  }
}
```

The genesis manifest writer is a deferred deliverable (see Section 7); this Spec pins the **shape** so the writer can be authored without re-litigating schema.

---

## Section 4 -- Layer 0 Artifacts (hash-pinned)

### 4.1 The closed Layer 0 set (normative)

[normative-description]

Layer 0 is a **closed set** at v1. Adding a document to Layer 0 requires a constitutional-tier amendment (Addendum v1.0.4 §XXIX.3). The current set comprises:

| # | Path | Role | Authority class |
|---|---|---|---|
| 1 | `docs/constitution/TRINITY_CONSTITUTION_V1.md` | constitution | layer_0_canonical |
| 2 | `docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md` | addendum | layer_0_supporting |
| 3 | `docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md` | addendum | layer_0_supporting |
| 4 | `docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md` | addendum | layer_0_supporting |
| 5 | `docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md` | addendum | layer_0_supporting |
| 6 | `docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md` | ritual_constitution | layer_0_canonical |
| 7 | `docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md` | organ_map | layer_0_supporting |
| 8 | `docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md` | contract | layer_0_supporting |
| 9 | `docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md` | contract | layer_0_supporting |

**Note on file naming.** The Ritual Constitution's filename retains the `_V1_1_RC` suffix for stable-reference reasons documented in CLAUDE.md (the file content is v1.1-final per Addendum v1.0.3 ratification on 2026-05-13). The manifest pins the **bytes**, not the filename's semantic suggestion.

### 4.2 Reproducible SHA-256 commands (normative)

[normative-description]

Each Layer 0 artifact's manifest entry MUST be reproducible by the canonical command:

```text
sha256sum docs/constitution/TRINITY_CONSTITUTION_V1.md
sha256sum docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md
sha256sum docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md
sha256sum docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md
sha256sum docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md
sha256sum docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md
sha256sum docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md
sha256sum docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md
sha256sum docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md
```

On macOS where `sha256sum` may be absent, the equivalent is `shasum -a 256 <path>`. The bytes hashed MUST be the on-disk bytes, with no whitespace normalisation, no LF/CRLF conversion, and no encoding transcoding. The verifier (Section 8) MUST recompute using the same byte stream the writer captured.

### 4.3 [non-normative-example] -- placeholder manifest entries

```text
"sha256": "<recompute-with-sha256sum-at-genesis-emit-time>"
```

Placeholders are explicit at this Spec stage because the genesis manifest writer is a deferred deliverable (Acceptance: "Crypto is optional until production, but schema is ready"). The actual hex digests will be inserted when the writer runs at genesis-emit time, not before.

### 4.4 What is deliberately NOT Layer 0 (normative)

[normative-description]

The following are **intentionally excluded** from Layer 0:

- `.ai/policies/**` -- Canonical Policies are rank 3 (Article XXV). They have their own change discipline. Promoting them to Layer 0 would force every policy edit through constitutional-tier amendment, collapsing the velocity tiers in Addendum v1.0.1.
- `docs/specs/**` -- Workflow Contracts (this very document) are rank 5. They are **governed** by Layer 0 (the Constitution authorises them) but are not themselves Layer 0.
- `.ai/cli/**` -- Kernel State Rules are rank 4. The kernel implementation MAY be replaced (Article XXVI: "Protocols SHOULD outlive models"); the Constitution does not.
- `.ai/audit/events.ndjson` -- Audit history is governed by Article X but is **append-only history**, not a normative document. Its hash chain (Phase 10) is a different trust anchor (per-event chain) from the Layer 0 manifest (per-document hash).
- **`CONSTITUTION.md` (root-level pointer).** Per Addendum v1.0.4 Canonical Paths, the root-level `CONSTITUTION.md` is a redirect to `docs/constitution/TRINITY_CONSTITUTION_V1.md`. It is **deliberately excluded** from Layer 0 -- pinning the pointer would force a manifest update on every pointer rewording, while the actual authority surface (the canonical Constitution under `docs/constitution/`) is already pinned by entry #1 of Sec. 4.1. (Promotes Sec. 12 Q3 to an explicit rule.)

---

## Section 5 -- Root Ratification Artifact Schema

### 5.1 Field-by-field schema (normative)

[normative-description]

Each Article XXIX amendment that touches a Layer 0 artifact MUST emit a **root ratification artifact** at the canonical path `docs/constitution/ratifications/<ratification_id>.json`. Required fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `ratification_id` | string | yes | ULID-prefixed `"rat_<ulid>"`; genesis is `"rat_genesis_<ulid>"` |
| `manifest_id` | string | yes | The manifest_version + manifest hash this ratification updates (e.g. `"1.0:sha256:<hex>"`) |
| `ts` | string (RFC3339 UTC) | yes | When the ratification act was performed |
| `ratified_by` | string | yes | Format `"operator:<stable-id>"`; per Article XIII this MUST resolve to a human |
| `evidence_refs` | array of strings | yes | Paths or URIs to supporting evidence (commit hashes, audit event ids, addendum file paths) |
| `constitutional_articles_invoked` | array of strings | yes | The Article numbers cited in the amendment (e.g. `["XXIX", "XXV"]`) |
| `audit_event_id` | string | yes | The `event_id` of the corresponding `constitution.amended.constitutional` audit event per Addendum v1.0.4 §XXIX.5 |

### 5.2 Cross-reference to Article XXIX 6-step protocol

[normative-description]

The root ratification artifact is the **durable artifact counterpart** to the six-step amendment procedure (Article XXIX, operationalised by Addendum v1.0.4):

| Article XXIX step | Where in the ratification artifact |
|---|---|
| 1. explicit proposal | `evidence_refs[]` includes the amendment file path |
| 2. rationale | `evidence_refs[]` includes the rationale section anchor |
| 3. impact analysis | `evidence_refs[]` includes the impact-analysis section anchor |
| 4. human approval | `ratified_by` resolves to a human operator id |
| 5. version bump | `manifest_id` carries the new manifest version + hash |
| 6. audit entry | `audit_event_id` references the audit chain entry |
| (supporting anchor) | `constitutional_articles_invoked` -- Step 1 (Proposal) supporting anchor; the proposal MUST cite which Articles it invokes |

A ratification artifact missing any of the seven required fields above is **invalid** -- it cannot witness all six Article XXIX steps. The verifier (Section 8) MUST refuse such artifacts.

### 5.3 [non-normative-example] -- minimal ratification artifact

```json
{
  "ratification_id": "rat_genesis_01HXXX",
  "manifest_id": "1.0:sha256:<placeholder>",
  "ts": "2026-05-15T12:00:00Z",
  "ratified_by": "operator:founder",
  "evidence_refs": [
    "docs/constitution/TRINITY_CONSTITUTION_V1.md",
    "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md#XXIX.3"
  ],
  "constitutional_articles_invoked": ["XXIX", "XXV", "XIII"],
  "audit_event_id": "evt_<placeholder>"
}
```

---

## Section 6 -- Signature Roadmap

### 6.1 The three tiers (normative)

[normative-description]

Trinity progresses through three signature tiers. Each tier is **schema-compatible** with the manifest in Section 3 -- only the `crypto_status` block changes. Migration between tiers is an Article XXIX amendment (Section 10).

#### Tier 1 -- HMAC-SHA256 (current; aligned with Phase 9)

[normative-description]

Tier 1 reuses the HMAC-SHA256 discipline already operational in Phase 9 Transport Boundary (TRINITY_TRANSPORT_BOUNDARY_SPEC_V1 §4 -- algorithm pinned to `"HMAC-SHA256"`, lowercase hex output, Python `hmac` + `hashlib.sha256`).

- **Threat model fit.** Single operator on trusted hardware; the symmetric secret stays on the operator's machine. Phase 9 §4.2 already establishes that secrets are issued by the Authority organ, not by transports -- the Root of Trust organ (#17) is the Authority organ for Layer 0 secrets at Tier 1.
- **Manifest impact.** `crypto_status.tier = "tier_1_hmac"`, `crypto_status.algorithm = "HMAC-SHA256"`, `crypto_status.key_id` MAY be null (declarative trust) or carry an HMAC `key_id` consistent with Phase 9 §4.2 if the operator chooses to sign the manifest.
- **Limitation.** A symmetric HMAC secret cannot be safely shared cross-host. Tier 1 is sufficient for the v1 single-operator threat model and IS NOT sufficient for cross-host or multi-operator deployments.

#### Tier 2 -- Public-key (Ed25519 / COSE_Sign1)

[normative-description]

Tier 2 introduces asymmetric signing so that the manifest and ratification artifacts can be **verified by any party that holds the public key**, without the verifier needing the secret. Candidate algorithms:

- **Ed25519** (RFC 8032) -- compact, deterministic, widely supported. Likely default.
- **COSE_Sign1** (RFC 8152) -- structured envelope wrapping Ed25519 (or other) signatures with explicit algorithm identifiers and key bindings. Useful when manifest signatures travel across systems.

Manifest impact:

- `crypto_status.tier = "tier_2_public_key"`
- `crypto_status.algorithm = "Ed25519"` (or `"COSE_Sign1+Ed25519"`)
- `crypto_status.key_id` REQUIRED -- resolves to a public key in the kernel's key registry.
- A detached signature file at `docs/constitution/GENESIS_TRUST_ASSUMED.json.sig` MAY be required by the future Tier 2 amendment.

Tier 2 unlocks cross-host verification (e.g. CI/CD systems verifying Layer 0 integrity) without sharing operator secrets.

#### Tier 3 -- Hardware-backed (TPM / Secure Enclave)

[normative-description]

Tier 3 binds the signing key to hardware so that the **key never exists in software memory in extractable form**. Candidate anchors:

- **TPM 2.0** (Trusted Platform Module) -- per-host attestation; signing operations stay inside the TPM.
- **Apple Secure Enclave** -- on macOS / iOS hosts; signing through the SecureEnclave keychain.
- **Cloud HSM** (e.g. AWS KMS, GCP Cloud HSM) -- cloud-managed hardware-backed keys for production deployments.

Manifest impact:

- `crypto_status.tier = "tier_3_hardware"`
- `crypto_status.algorithm` carries the hardware-supported algorithm (e.g. `"ECDSA-P256-SecureEnclave"`).
- `crypto_status.key_id` REQUIRED -- resolves to a hardware-backed key handle, not a raw key.

Tier 3 mitigates against operator-machine compromise: even if the host is rooted, the attacker cannot extract the key. Tier 3 is the **target state for production COLD-tier deployments** per Article XIII (Human Authority requires durable artifacts).

### 6.2 Migration between tiers is an Article XXIX amendment (normative)

[normative-description]

A change from Tier N to Tier N+1 is **constitutional-tier** per Addendum v1.0.4 §XXIX.3 because it modifies the operational meaning of `crypto_status` and therefore the trust posture the kernel runs under. Each migration MUST:

1. Land an Addendum (e.g. `TRINITY_CONSTITUTION_ADDENDUM_V1_0_5.md`) declaring the new tier.
2. Emit a root ratification artifact (Section 5) with `constitutional_articles_invoked = ["XXIX", "XXV"]`.
3. Update the GENESIS_TRUST_ASSUMED manifest's `crypto_status` block.
4. Append a `constitution.amended.constitutional` audit event per Addendum v1.0.4 §XXIX.5.

A Tier change WITHOUT all four steps is an Article III violation ("rewrite constitutional policy") and the manifest verifier (Section 8) MUST refuse the new posture until the cascade completes.

### 6.2.1 Pre-Migration Validation (normative)

[normative-description]

Specifically for the Tier 1 -> Tier 2 migration, the operator MUST emit a `root.tier.pre_migration_validated` audit event **before** the manifest tier bump lands. The event confirms that the public key for Tier 2 has been installed in the kernel's key registry and is resolvable via its `key_id`. Without this pre-transition event, the cascade in Sec. 6.2 is invalid and the verifier MUST refuse the new posture (Article XVI -- unknown authority is denied authority).

---

## Section 7 -- Crypto-Optional Discipline

### 7.1 The schema is required; the crypto is optional (normative)

[normative-description]

Trinity v1 ships with the **manifest schema** (Section 3) and the **ratification artifact schema** (Section 5) as required deliverables. The **cryptographic verification** of the manifest itself is **optional** in non-production deployments and IS REQUIRED in production deployments per Article XIII.

Operationally:

- A development workstation MAY operate at Tier 1 with `crypto_status.key_id = null` (declarative trust, no HMAC over the manifest itself). The Layer 0 hash entries are still computed and verified per Section 8 -- only the manifest's own signature is omitted.
- A production deployment MUST operate at Tier 1 minimum, with `crypto_status.key_id` populated and the manifest itself HMAC-signed; SHOULD progress to Tier 2 for cross-host verification; MAY progress to Tier 3 for hardware-backed assurance.

### 7.2 The choice MUST be audited (normative)

[normative-description]

A deployment that runs at a **lower tier than its risk profile justifies** is making a governance choice. That choice MUST appear in the audit chain as a `root.tier.declared` event (NOTE: this event-type is **not yet registered** in Addendum v1.0.4 Sec. XXIX.5, which only lists 3 `constitution.amended.*` event-types; registration awaits a future Addendum v1.0.5) carrying:

- `tier` -- the declared tier
- `manifest_id` -- the manifest version + hash this declaration applies to
- `actor` -- the operator id making the declaration
- `rationale_ref` -- pointer to the rationale (commit message for editorial; addendum section anchor for operational/constitutional)

Silent tier downgrade (e.g. running production at Tier 1 without recording the choice) violates Article XXIV ("No Silent Success") -- it claims a trust posture without producing the evidence to back it.

### 7.3 [non-normative-example] -- declarative-trust dev workstation

```text
crypto_status:
  tier:        "tier_1_hmac"
  algorithm:   "HMAC-SHA256"
  key_id:      null              # declarative trust; no manifest-HMAC
  verified_at: null              # never verified by signature; layer_0 hashes still verify
```

In this posture, `ai root verify` (Section 8) still recomputes every Layer 0 SHA-256 and refuses on mismatch. What is omitted is the HMAC over the manifest **itself** -- the manifest is trusted because the operator wrote it locally, not because a signature wraps it.

---

## Section 8 -- Verification Procedure

### 8.1 The five-step verification (normative)

[normative-description]

For any artifact claiming Layer 0 authority -- when read by the Kernel, the Verifier, the Memory organ, or any sibling CLI that consumes Layer 0 documents -- the following procedure MUST run:

```text
1. Resolve artifact path against the GENESIS_TRUST_ASSUMED manifest's
   layer_0_artifacts[].path entries. If unresolved -> fail BADPATH.

2. Recompute SHA-256 of the on-disk bytes (no normalisation, no
   transcoding). If recompute fails (e.g. permission denied) -> fail
   BADREAD.

3. Compare against the manifest entry's sha256. If mismatch -> fail
   BADHASH.

4. Verify the manifest's own crypto_status posture per Section 7.
   At Tier 1 with key_id=null -> declarative trust accepted.
   At Tier 1 with key_id populated -> recompute manifest HMAC.
   At Tier 2 -> verify detached signature.
   At Tier 3 -> verify hardware-backed signature.
   If verification fails -> fail BADKEY.

5. Emit one of the following audit events:
   - root.verify.pass  -- all checks passed
   - root.verify.fail  -- include refusal code BADPATH/BADREAD/BADHASH/BADKEY
```

### 8.2 Canonical one-liner (normative)

[normative-description]

Operators and CI systems MAY invoke verification via the canonical one-liner. The exact subcommand is reserved here; emission is deferred to the Phase 14 implementation session. The contract:

```text
bash .ai/cli/ai root verify
  -> reads docs/constitution/GENESIS_TRUST_ASSUMED.json
  -> for each layer_0_artifacts[] entry: runs steps 1-3
  -> runs step 4 against crypto_status
  -> appends step 5 audit event(s) to .ai/audit/events.ndjson
  -> exits 0 on all-pass; non-zero on any fail
```

A POSIX-portable manual equivalent (no Trinity tooling required) for step 3 alone:

```text
sha256sum docs/constitution/TRINITY_CONSTITUTION_V1.md
# -> compare lowercase-hex output against manifest entry
```

### 8.3 Refusal codes (normative)

[normative-description]

| Code | Meaning | Audit event |
|---|---|---|
| `BADPATH` | Artifact path does not appear in the manifest's `layer_0_artifacts[]` | `root.verify.fail` with `code:"BADPATH"` |
| `BADREAD` | Artifact bytes could not be read (permission denied, missing file) | `root.verify.fail` with `code:"BADREAD"` |
| `BADHASH` | Recomputed SHA-256 differs from manifest entry | `root.verify.fail` with `code:"BADHASH"` |
| `BADKEY` | Manifest signature verification failed at the declared tier | `root.verify.fail` with `code:"BADKEY"` |

Per Article XVI (Least Authority), any refusal code MUST cause the consuming organ to treat the artifact as **denied authority**. There is no "warn and proceed" path. A verifier that proceeds on `root.verify.fail` is itself in violation.

### 8.4 [non-normative-example] -- successful verification audit event

```json
{
  "event_type": "root.verify.pass",
  "actor": "kernel",
  "ts_utc": "2026-05-15T12:01:00Z",
  "payload_json": "{\"manifest_id\":\"1.0:sha256:<hex>\",\"artifacts_verified\":9,\"crypto_tier\":\"tier_1_hmac\"}"
}
```

### 8.5 Extended refusal code -- BADPATH_UNREGISTERED (normative)

[normative-description]

| Code | Meaning | Audit event |
|---|---|---|
| `BADPATH_UNREGISTERED` | Verification of an artifact path **not in the current GENESIS_TRUST_ASSUMED manifest** -- the path resolves on disk but no manifest entry exists for it (distinct from `BADPATH` which covers manifest-listed paths that fail registry lookup, and from `BADREAD` which covers file-not-found) | `root.verify.fail` with `code:"BADPATH_UNREGISTERED"` |

---

## Section 9 -- Conformance Test Matrix

### 9.1 Verification outcome matrix (normative)

[normative-description]

The following matrix pins the expected outcome for each combination of artifact state and manifest state. Conformance requires that an implementation produce exactly the listed outcome -- any deviation is a Spec violation.

| # | Artifact state | Manifest entry state | Expected outcome | Audit event |
|---|---|---|---|---|
| RT-01 | Present, bytes unchanged since manifest write | Entry present, sha256 matches | PASS | `root.verify.pass` |
| RT-02 | Present, bytes mutated (any change including whitespace) | Entry present | FAIL `BADHASH` | `root.verify.fail` |
| RT-03 | Absent (file missing or unreadable) | Entry present | FAIL `BADREAD` | `root.verify.fail` |
| RT-04 | Present | Entry absent (path not in manifest) | FAIL `BADPATH` | `root.verify.fail` |
| RT-05 | Present, bytes match | Manifest itself failed signature verify | FAIL `BADKEY` | `root.verify.fail` |
| RT-06 | All Layer 0 entries present, all match | Manifest at Tier 1 with `key_id=null` | PASS (declarative trust) | `root.verify.pass` |
| RT-07 | All Layer 0 entries present, all match | Manifest at Tier 2, signature verifies | PASS | `root.verify.pass` |
| RT-08 | All Layer 0 entries present, all match | Manifest at Tier 3, hardware verifies | PASS | `root.verify.pass` |
| RT-09 | Layer 0 set EXPANDED on disk (new file added) but manifest not updated | Entry absent for new file | FAIL `BADPATH` on the new file (per RT-04) | `root.verify.fail` |
| RT-10 | Layer 0 set REDUCED on disk (file deleted) | Entry present | FAIL `BADREAD` for the deleted file (per RT-03) | `root.verify.fail` |

### 9.2 Tier-classification of conformance tests (normative)

[normative-description]

- **RT-01 through RT-05** are Tier 1 deterministic checks (per Phase 9 Spec §11.4 -- "Tier 1 = deterministic checks against artifacts"). They MUST pass without requiring crypto material beyond the manifest itself at declarative-trust posture.
- **RT-06** is the canonical declarative-trust path at Tier 1 with `key_id=null`. Required for any v1 conformance claim.
- **RT-07 / RT-08** are Tier 2 / Tier 3 paths and are conditional on the deployment having migrated to those tiers (Section 6.2). A v1 implementation that has not migrated is conformant if it returns "TIER_NOT_AVAILABLE" rather than silently falling back.
- **RT-09 / RT-10** are integrity tests for set-membership drift; they MUST run any time `ai root verify` is invoked, not only on per-file lookups.

### 9.3 [non-normative-example] -- conformance test invocation

```text
# RT-01 (golden path)
bash .ai/cli/ai root verify
# expected: exit 0; one root.verify.pass audit event per Layer 0 artifact

# RT-02 (mutation detection)
echo " " >> docs/constitution/TRINITY_CONSTITUTION_V1.md
bash .ai/cli/ai root verify
# expected: exit non-zero; root.verify.fail with code:"BADHASH"
```

---

## Section 10 -- Versioning & Article XXIX Amendment Protocol

### 10.1 Cascade on Layer 0 amendment (normative)

[normative-description]

Any Article XXIX amendment to a Layer 0 artifact (Section 4) triggers a **mandatory cascade**:

```text
1. Amendment lands per Article XXIX 6-step procedure
   (operationalised by Addendum v1.0.4 §XXIX.3 for constitutional tier).

2. Recompute SHA-256 of the modified Layer 0 artifact.

3. Update GENESIS_TRUST_ASSUMED.json:
   - layer_0_artifacts[].sha256 for the modified entry
   - ratification_chain[] -- append the new ratification_id
   - manifest_version BUMP if the schema itself changed (otherwise unchanged)

4. Emit root ratification artifact (Section 5) at
   docs/constitution/ratifications/<ratification_id>.json

5. Append constitution.amended.constitutional audit event
   (Addendum v1.0.4 §XXIX.5) carrying:
   - actor    = operator id
   - diff_sha256 = SHA-256 of the unified diff
   - tier     = "constitutional"
   - rationale_ref = addendum file path + section anchor
```

A Layer 0 amendment that does not complete the full cascade is **invalid**. The next `ai root verify` invocation will fail with `BADHASH` (Section 8) on the modified artifact, exposing the incomplete cascade.

### 10.2 Schema evolution rules (normative)

[normative-description]

- **Adding a field to the manifest schema** (Section 3) is a constitutional-tier amendment. The `manifest_version` MUST bump (e.g. `"1.0"` -> `"1.1"`). Older manifests at the prior version remain inspectable per Article XXIX ("Prior versions MUST remain inspectable").
- **Removing a field** is a constitutional-tier amendment AND a backwards-incompatible break. The `manifest_version` MUST bump major (`"1.0"` -> `"2.0"`). Migration tooling MUST be specified in the landing addendum.
- **Adding a Layer 0 artifact** is a constitutional-tier amendment per Section 4.4. The new entry appears in `layer_0_artifacts[]`; no `manifest_version` bump required (the schema is unchanged).
- **Removing a Layer 0 artifact** is a constitutional-tier amendment AND requires a strategic rationale per Addendum v1.0.4 §XXIX.3 ("the constitutional principle being preserved or extended, named by article"). Removing Layer 0 documents narrows the trust surface and MUST be deliberate.

### 10.3 Adding a new crypto tier (normative)

[normative-description]

Adding a Tier 4 (or any future tier) follows the same Section 6.2 migration protocol but ALSO requires a schema check: if the new tier introduces field shapes not accommodated by the current `crypto_status` schema (Section 3.3), the schema evolution rules in §10.2 apply on top of the tier migration. Both addenda MAY land in the same session provided each is independently witnessed in the audit chain.

### 10.4 Inspectability is non-negotiable (normative)

[normative-description]

Per Article XXIX final clause: **"Prior versions MUST remain inspectable."** This Spec extends that obligation to the manifest itself:

- Prior manifest versions remain at their version-suffixed paths (e.g. `docs/constitution/GENESIS_TRUST_ASSUMED.v1.0.json` after the v1.1 cascade).
- Prior ratification artifacts remain at `docs/constitution/ratifications/<id>.json` indefinitely.
- The `ratification_chain` array in the current manifest enumerates all prior ratifications by id, so the full chain is reachable from the latest manifest in O(N).

A compaction or pruning of historical ratifications is **prohibited** -- it would violate Article XXIX. The chain is append-only by construction.

### 10.5 Compaction Policy (normative)

[normative-description]

For v1.0, **no compaction**: the `ratification_chain[]` array grows unbounded and the SLA for manifest reads scales linearly with chain depth. v1.1+ MAY introduce period-based archival to versioned `GENESIS_TRUST_ASSUMED.archive.<period>.json` files (e.g. yearly buckets) under an Article XXIX amendment that pins the archival schema and migration tooling. Until that amendment lands, any operator-initiated compaction violates Sec. 10.4 and Article XXIX.

### 10.6 [non-normative-example] -- a constitutional-tier amendment cascade in pseudocode

```text
# 1. amendment lands (Addendum v1.0.5 hypothetical)
git add docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_5.md
git commit -m "feat(constitution): Addendum v1.0.5 - new Layer 0 artifact"

# 2. recompute SHA-256
NEW_HASH=$(sha256sum docs/constitution/<modified>.md | cut -d' ' -f1)

# 3. update manifest (writer tool, Section 3.4 deferred)
ai root manifest update --path <modified> --sha256 "$NEW_HASH"

# 4. emit ratification artifact
ai root ratify --articles "XXIX,XXV" \
               --evidence "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_5.md" \
               --by "operator:founder"

# 5. audit event auto-emitted by ai root ratify
#    -> constitution.amended.constitutional in .ai/audit/events.ndjson
```

The exact subcommand surface (`ai root manifest update`, `ai root ratify`, `ai root verify`) is reserved by this Spec; implementation lands in a future Phase 14 wiring session per Article XX (declaring a taxonomy does not register emitters).

---

## Section 11 -- References

[normative-description]

### Constitutional anchors

- [`docs/constitution/TRINITY_CONSTITUTION_V1.md`](TRINITY_CONSTITUTION_V1.md) -- parent Constitution; Articles XXV (priority order) and XXIX (amendment) are PRIMARY anchors
- [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md`](../constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md) -- operationalises Article XXIX with 3-tier classification, trace-to-failure, pinned audit format
- [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md`](../constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md) -- Decision Velocity Tiers (precedent for tiered classification)
- [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md`](../constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md) -- canonical-home relocation (defines `docs/constitution/` as the canonical home referenced by Layer 0 paths)
- [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md`](../constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md) -- Ritual Constitution v1.1 ratification
- [`docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md`](TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md) -- Ritual Constitution v1.1 (RATIFIED 2026-05-13)
- [`docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md`](../constitution/contracts/TRINITY_ORGAN_MAP_V1.md) -- Organ Map (Organ #17 Root of Trust definition)
- [`docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md`](../constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md) -- Ritual Contract
- [`docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md`](../constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md) -- RRR Delegation Contract

### Phase cross-references

- **Phase 9 -- Transport Boundary** ([`TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md`](TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md)) -- HMAC-SHA256 discipline (§4) is the operational basis for Tier 1 of the signature roadmap (Section 6.1 of this Spec). Phase 9 §4.2 ("HMAC secret used to sign an envelope is issued by the Authority organ") names Root of Trust (Organ #17) as the issuing authority for Layer 0 secrets at Tier 1. Phase 9 §4.1 explicitly defers cross-host signature schemes (Ed25519, COSE_Sign1) to Phase 14 -- this Spec accepts that deferral and pins the roadmap.
- **Phase 10 -- Audit Replay / Verify-chain** ([`TRINITY_AUDIT_EVENT_SPEC_V1.md`](TRINITY_AUDIT_EVENT_SPEC_V1.md)) -- the per-session audit chain that Section 8 emits `root.verify.pass` / `root.verify.fail` events into. The `constitution.amended.constitutional` event-type from Addendum v1.0.4 §XXIX.5 is the canonical event for a Layer 0 cascade (Section 10.1 step 5).
- **Phase 11 -- DDD / Human Gate** ([`TRINITY_DDD_HUMAN_GATE_SPEC_V1.md`](TRINITY_DDD_HUMAN_GATE_SPEC_V1.md)) -- the human-authority artifacts (`approval.json`, `rejection.json`, `hold.json`) carry an optional `signature` field per §4 / §5 / §6 of that spec. As Trinity progresses to Tier 2 / Tier 3, those signatures gain cryptographic backing per the roadmap in Section 6 of this Spec, making the Article XIII "human approval MUST exist as an artifact" obligation **machine-verifiable**.

### Operational anchors

- [`CLAUDE.md`](../../CLAUDE.md) -- §Constitutional Authority, §CLI Command Rule (the canonical command surface this Spec's `ai root verify` extends)
- [`.ai/audit/events.ndjson`](../../.ai/audit/events.ndjson) -- the per-session hash-chained audit log Phase 10 governs and Section 8 of this Spec writes into

### Out-of-scope (deliberate)

- Public-key infrastructure beyond the Section 6 roadmap. Specific PKI (X.509, OpenPGP web-of-trust, sigstore) is a future addendum.
- Hardware-backed key issuance procedures (TPM provisioning, Secure Enclave keychain access patterns). Future Tier 3 amendment surface.
- Cross-organisation trust federation. The v1 single-operator threat model does not require federation; introducing it is a Phase >14 concern.

---

## Section 12 -- Open Questions (Author -> Verifier)

[non-normative-example]

These questions are flagged for the verifier review that gates ddd:

- **Q1 -- Manifest emission timing.** Should the GENESIS_TRUST_ASSUMED manifest land in this same session as the Spec, or is the schema-only landing acceptable per the Acceptance criterion ("Crypto is optional until production, but schema is ready")? Tentative: schema-only landing is correct; manifest emission is a follow-up Phase 14 implementation session per Article XX (Passive Core).
- **Q2 -- ratification_chain depth limit.** Should the `ratification_chain[]` array carry an upper bound (e.g. last N entries) with older entries archived to a separate index, or remain truly unbounded? Tentative: unbounded; Article XXIX inspectability obligation argues against any compaction discipline.
- **Q3 -- Layer 0 set membership for the Constitution Pointer.** The root-level `CONSTITUTION.md` is documented as a "pointer only" (Addendum v1.0.4 Canonical Paths section). Does the manifest hash-pin the pointer, or is it deliberately excluded? Tentative: excluded -- it is a redirect, not an authority surface; pinning it would force a manifest update on every pointer rewording.
- **Q4 -- INDEX.md row.** Should INDEX.md gain a row for this Spec in the same session, or is that a separate operational-tier amendment? Per the task constraint "DO NOT TOUCH INDEX.md (handled separately)" -- INDEX.md is left to a separate session.

---

## Section 13 -- Acceptance Mapping

[normative-description]

PRD Phase 14 acceptance criteria (lines 914-918 of `trinity_organ_refactor_prd.md`) map onto this Spec as follows:

| Acceptance criterion | Where satisfied |
|---|---|
| Genesis trust declared | Section 2 (Trust Boot Problem); Section 3 (manifest schema with `asserted_at` / `asserted_by` fields) |
| Layer 0 artifacts hash-pinned | Section 4 (closed Layer 0 set, reproducible SHA-256 commands); Section 8 (verification procedure) |
| Crypto is optional until production, but schema is ready | Section 6 (three-tier roadmap, schema-compatible across tiers); Section 7 (crypto-optional discipline with audited tier choice) |

PRD Phase 14 deliverables map as follows:

| Deliverable | Where satisfied |
|---|---|
| `TRINITY_ROOT_OF_TRUST_SPEC_V1.md` | this document |
| GENESIS_TRUST_ASSUMED manifest schema | Section 3 (full schema); Section 4 (artifact set the schema covers) |
| root ratification artifact schema | Section 5 (full schema with cross-reference to Article XXIX 6-step protocol) |
| signature support roadmap | Section 6 (Tier 1 HMAC current per Phase 9; Tier 2 public-key future; Tier 3 hardware-backed future) |

---

## Section 14 -- Change Log

[normative-description]

| Date | Author | Change |
|---|---|---|
| 2026-05-15 | operator:founder | DRAFT v1 -- first canonical version; pending verifier review + ddd |

---

**End of TRINITY_ROOT_OF_TRUST_SPEC_V1**
