---
title: "Trinity Presentation Protocol v1.0"
version: "1.0"
status: "draft"
phase: "13"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes: ["(none — first canonical version)"]
constitutional-anchor: ["Article XIII", "Article XXIII", "Article III", "Article IV", "Article XVI", "Article XX", "Article XXIX"]
amendment-policy: "Article XXIX — explicit proposal + rationale + impact analysis + human approval + version bump + audit entry."
---

# TRINITY PRESENTATION PROTOCOL V1

**Status:** DRAFT v1.0 (first canonical version — Phase 13)
**Phase:** 13 — Presentation Protocol
**Organ:** #15 (Presentation / Cognitive Compression)
**Constitutional rank:** 5 — Workflow Contract (per Article XXV)
**Date:** 2026-05-15

---

## §0 — Rank-5 Authority Disclaimer (Article XXV)

[normative-description]

This document is a **Workflow Contract** under Article XXV. It is void where it conflicts with the Constitution, the Ritual Constitution, Canonical Policies, or Kernel State Rules. Amendments require Article XXIX (explicit proposal + rationale + impact analysis + human approval + version bump + audit entry).

The two controlling clauses for this protocol are **Article XIII (Human Authority)** and **Article XXIII (Failure Visibility)**. Articles III, IV, XVI, XX, and XXIX provide structural constraints on how presentation may compress, who may present, and how presentation evolves.

This spec pins **shape and behaviour of presentation artefacts only**. It does not redefine authority, does not delegate decision-making, and does not collapse roles. The presentation layer is a **view** over the truth layer; it is never a substitute for it.

---

## §1 — Purpose & Constitutional Anchor

[normative-description]

The Presentation Protocol exists to **protect human judgment from cognitive overload at decision gates**. Trinity workflows produce many artefacts (plans, diffs, verifier reports, audit slices, dissenting analyses). When the human gate (Phase 11 DDD) fires, the operator cannot read every artefact in full. They need a **compressed, faithful, dissent-preserving view** that links back to the raw evidence.

This protocol pins:

1. **`ratification_packet.json`** — the input artefact a presentation pipeline consumes (proposed decision + raw artefacts + dissent + evidence refs).
2. **`presentation_synthesis.json`** — the compressed output handed to the human; includes drill-down links to every raw artefact.
3. **`ratification_decision.json`** — the human's signed decision artefact, citing which dissent points were acknowledged.
4. **The presentation verifier contract** — a deterministic checker that fails any synthesis which erases dissent, breaks raw-link integrity, or claims to be the truth layer.

### §1.1 Verbatim — Article XIII (Human Authority)

[normative-description]

> Humans remain the highest authority.
>
> AI may recommend irreversible actions.
>
> AI MUST NOT silently authorize irreversible actions.
>
> Critical actions SHOULD require explicit human approval.
>
> Critical actions include:
>
> ```text
> production deploy
> destructive operations
> credential changes
> privilege escalation
> irreversible mutations
> external publication
> legal/financial/customer-impacting actions
> ```
>
> Human approval MUST exist as an artifact.

**Operational consequence for Phase 13.** A presentation pipeline that produces a synthesis the human approves is **not** the human's approval. The approval artefact is `ratification_decision.json`, which MUST carry `decided_by: "human:<actor>"` and a typed verdict. A synthesis that suggests "consensus reached" without a decision artefact is a violation of Article XIII.

### §1.2 Verbatim — Article XXIII (Failure Visibility)

[normative-description]

> Failure MUST be visible.
>
> Trinity MUST NOT silently:
>
> ```text
> drop tasks
> hide failed execution
> suppress verifier failure
> mark incomplete work as complete
> lose audit history
> pretend unsafe state is safe
> ```
>
> Invisible failure is unconstitutional.

**Operational consequence for Phase 13.** Compression that erases dissent, suppresses a failed verifier verdict, or hides an incomplete artefact is a **constitutional violation**, not merely a UX bug. The presentation verifier (§8) MUST refuse such synthesis with verdict `FAIL`, and the kernel MUST refuse to emit a `decision_packet` (Phase 11 §3) whose `presentation` is sourced from a `FAIL` synthesis.

### §1.3 Cited Articles (operational relevance)

[normative-description]

| Article | Operational relevance to Phase 13 |
|---|---|
| **III — AI Cannot Govern Itself** | The synthesizer agent MAY draft a presentation; it MUST NOT decide the verdict. A `presentation_synthesis.json` carrying `verdict` is malformed (verifier `FAIL`). |
| **IV — Separation of Responsibilities** | Presentation is its own role (Synthesizer); it MUST NOT collapse into Planner, Executor, Verifier, or Memory. The synthesizer is `actor: "agent:presentation_synthesizer"` in audit; it MUST NOT impersonate any other role. |
| **XVI — Least Authority** | The synthesizer has READ authority over raw artefacts and WRITE authority only over `presentation_synthesis.json`. It MUST NOT mutate raw artefacts, audit chain, or policies. |
| **XX — Passive Core** | Presentation runs on explicit invocation (`ai presentation synthesize <packet_id>`); it MUST NOT self-trigger, watch the filesystem, or pre-compute synthesis "just in case." |
| **XXIX — Constitutional Amendment** | Schema evolution for the three artefacts MUST follow Article XXIX. Past artefacts MUST remain inspectable; renaming or removing fields requires a versioned schema bump (§10). |

---

## §2 — The Cognitive-Overload Threat Model

[normative-description]

The presentation protocol exists because **the human gate is the throughput bottleneck of Trinity**. Every safety property in Trinity depends on the human reading the right thing at the right time. If the human is given a 50-page diff at 11pm, they will skim. If they are given a 3-bullet summary that omits dissent, they will rubber-stamp. Either failure mode is a constitutional violation under Article XIII (silent authorization) and Article XXIII (invisible failure).

### §2.1 Mode failures this protocol guards against

[normative-description]

| Mode | Failure shape | Article violated | Verifier guard (§8) |
|---|---|---|---|
| **Decision fatigue** | Operator approves the 17th gate in a session with the same depth as the 1st. | XIII (silent authorization via exhaustion) | `compression_ratio` floor: synthesis MUST NOT exceed declared bound; over-long synthesis fails with `FAIL_SUMMARY_TOO_LONG`. |
| **Information overload** | Synthesis dumps every raw artefact verbatim, leaving the operator to compress. | XIII | `compression_ratio` ceiling: trivial passthrough fails with `FAIL_NO_COMPRESSION`. |
| **False convergence** | Synthesis claims "verifier and planner agree" when verifier emitted `UNVERIFIED`. | XXIII (suppressing verifier failure) | `dissent_preserved[]` MUST contain the unverified state; failure mode is `FAIL_DISSENT_ERASED`. |
| **Dissent erasure** | A minority position from a panel-of-N analysis is dropped because it would slow the decision. | XXIII | `dissent_preserved[]` MUST list all distinct positions present in the packet; `FAIL_DISSENT_ERASED`. |
| **Truth-layer collapse** | Synthesis becomes the only artefact the operator reads; raw artefacts are not linked or are dead links. | XX (passive core: synthesis MUST NOT replace truth layer) | `raw_artifact_links[]` integrity check; `FAIL_BROKEN_RAW_LINK`. |
| **Synthesizer-as-juror** | The agent that drafts the synthesis is also counted as a "vote" in the convergence claim. | III, IV (role collapse) | `synthesizer_not_in_opinion_panel: true` invariant; `FAIL_SYNTHESIZER_VOTED`. |
| **Rubber-stamp framing** | Synthesis presents only "approve" as the natural action, omitting "reject" and "defer". | XIII (irreversible action without explicit choice) | `founder_decisions_required[]` MUST list ≥1 decision phrased as a question; `FAIL_NO_DECISION_QUESTION`. |

### §2.2 Concrete examples from operator workflow (non-normative)

[non-normative-example]

Example A — **decision fatigue**. Operator runs `ai gogogo` on a 12-step plan. Each step's verifier emits PASS and the synthesizer drafts a 1-line "step OK". By step 9 the operator approves the next step in 2 seconds without reading. **Mitigation:** the synthesizer MUST surface in the synthesis-level summary: "Step 9 differs from steps 1-8 in <axis>." If no difference, the synthesizer MUST flag `convergence_axes: ["identical_to_prior_step"]` so the operator can choose to skip review explicitly rather than implicitly.

Example B — **dissent erasure**. A panel of three verifier instances (A, B, C) evaluates a deploy proposal. A=PASS, B=PASS, C=UNVERIFIED-with-reason. Naive synthesis: "verifier passes." This is a constitutional violation: `dissent_preserved[]` MUST contain `{role: "verifier:C", verdict: "UNVERIFIED", reason: "<C's reason>"}`. The synthesis summary MUST acknowledge "2 of 3 verifier instances passed; 1 returned UNVERIFIED."

Example C — **truth-layer collapse**. Operator opens a Telegram presentation card (per spec 14) and approves. The card showed only the synthesizer's prose. The raw `verifier_report.json` was not retrievable from mobile. **Mitigation:** the presentation card MUST carry a `raw_artifact_links[]` pointer to a kernel-served URL; if the operator is on a transport that cannot resolve the URL, the synthesis MUST be marked `transport_capability: "compressed-only"` and the kernel MUST require a follow-up decision from a transport that can resolve raw links before any irreversible action. (Article XV: transport is not authority; an operator approving a compressed-only view is approving the **synthesis**, not the **artefacts**.)

---

## §3 — The Truth-Layer / Presentation-Layer Boundary

[normative-description]

Article XX (Passive Core) anchors the deepest invariant of this spec: **compressed UI is a view, not a store**. Every `presentation_synthesis.json` MUST link back to the raw artefacts that produced it; the synthesis MUST NOT be referenced by any other Trinity component as the source of truth for what the verifier said, what the planner proposed, or what the executor did.

### §3.1 The boundary stated as invariants

[normative-description]

```text
INV-PRES-1: presentation_synthesis is a VIEW over raw artefacts.
INV-PRES-2: presentation_synthesis MUST link to all raw artefacts in
            its packet, by hash-pinned reference.
INV-PRES-3: presentation_synthesis MUST NOT be the sole record of any
            verifier verdict, planner proposal, or executor mutation.
INV-PRES-4: A consumer that needs ground truth MUST read the raw
            artefact, not the synthesis.
INV-PRES-5: If a raw artefact is mutated (forbidden under append-only
            audit), every synthesis referencing it MUST be invalidated.
INV-PRES-6: A synthesis MUST NOT inherit authority from the artefacts
            it summarises — approving a synthesis is not approving
            the underlying actions; only ratification_decision.json
            grants authority.
```

### §3.2 Why this matters operationally

[normative-description]

In Phase 11 (DDD), the kernel emits a `decision_packet.json` whose `presentation` field is sourced from this protocol's `presentation_synthesis.json`. The DDD spec (TRINITY_DDD_HUMAN_GATE_SPEC_V1 §3.1) requires `raw_artifacts_available: true` and `capture_refs[]`. This protocol is the producer side of that requirement: the synthesizer MUST populate `raw_artifact_links[]` such that DDD can downstream-verify drill-down integrity.

If an operator-facing transport (Telegram, Slack, browser) shows a compressed view only, that transport has rendered a **partial presentation**. Per Article XV, the transport is not authority — but the **synthesis** also is not authority. Authority is the human's signed `ratification_decision.json`, which MUST cite which dissent points were acknowledged (§7).

### §3.3 What the synthesis is NOT (anti-pattern catalogue)

[normative-description]

| Anti-pattern | Why it violates the boundary |
|---|---|
| Caching the synthesis and serving it without re-reading raw artefacts on next gate | Truth-layer drift: raw may have been amended (e.g., `plan.amended` event). |
| Treating "synthesis approved" as equivalent to "raw artefacts approved" | Authority confusion (Article XIII). The decision artefact must enumerate raw artefacts. |
| Embedding raw artefact CONTENT (not links) in the synthesis | Compression-zero anti-pattern; no compression ratio achieved; defeats purpose. |
| Letting the synthesizer paraphrase verifier verdicts ("looks good" instead of "PASS") | Loses the structured verdict the kernel needs (Article VIII). |
| Allowing a presentation transport (e.g., TG) to write its own synthesis | Role collapse: transport MUST NOT synthesise (Article XV + IV). |

---

## §4 — `ratification_packet.json` Schema

[normative-description]

The packet is the **input** to a presentation pipeline. The kernel (or an orchestrator under kernel governance) assembles it from upstream artefacts and writes it to `<session>/PRESENTATION/packets/<packet_id>.json`. The synthesizer agent is then invoked and consumes this packet read-only.

### §4.0.1 Lifecycle

[normative-description]

The three artefacts in this protocol have distinct lifetimes and persistence scopes:

```text
1. ratification_packet.json
   - Written by the kernel at gogogo-completion (when an irreversible
     action is about to enter the human gate).
   - Passed read-only to the synthesizer agent.
   - Persisted inside the session capsule under
     <session>/PRESENTATION/packets/<packet_id>.json.
   - NOT persisted to permanent kernel state; expires per expires_ts.

2. presentation_synthesis.json
   - Written by the synthesizer agent in response to a packet.
   - Persisted inside the session capsule under
     <session>/PRESENTATION/synthesis/<synthesis_id>.json.
   - NOT persisted to permanent kernel state; lives with the session
     capsule and is referenced by sha256 from the audit chain.

3. ratification_decision.json
   - Written by the human via DDD per Phase 11.
   - Persisted as the canonical decision artefact under
     <session>/PRESENTATION/decisions/<decision_id>.json AND referenced
     by Phase 11's decision_packet.json.
   - This is the only Phase 13 artefact that survives session archival
     as a first-class decision record (Article XIII).
```

### §4.1 Required fields

[normative-description]

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | string | yes | const `"trinity.ratification_packet.v1"` |
| `packet_id` | string | yes | `pkt_<ulid>` |
| `ts` | RFC3339 | yes | when the kernel emitted the packet |
| `source_session` | string | yes | session id that produced the artefacts |
| `proposed_decision` | object | yes | `{action: enum, scope: string, rationale: string}` — the action being proposed for the human gate |
| `raw_artifacts` | array | yes | each entry: `{role: string, path: string, sha256: string, ts: RFC3339}`; ≥1 element required |
| `dissent` | array | yes | each entry: `{role: string, position: string, reason: string, evidence_ref: string}`; MAY be empty (`[]`) only if no dissent existed in upstream sources |
| `evidence_refs` | array | yes | array of `capture_id` ULIDs (per RecordProxy §17) backing the artefacts; subset of audit chain |
| `expires_ts` | RFC3339 | yes | deadline after which the packet is stale and MUST be re-emitted |

### §4.2 Example (non-normative)

[non-normative-example]

```json
{
  "schema_version": "trinity.ratification_packet.v1",
  "packet_id": "pkt_01HZX9KQ7RW3M6VBXR0Q8C7Y2P",
  "ts": "2026-05-15T10:14:22Z",
  "source_session": "S-2026-05-15-deploy-edge",
  "proposed_decision": {
    "action": "deploy",
    "scope": "edge/cdn-rules",
    "rationale": "verifier PASS on staging; rollback path validated"
  },
  "raw_artifacts": [
    {"role": "plan", "path": "DO/dev/plan.json", "sha256": "a1b2...", "ts": "..."},
    {"role": "verifier", "path": "VERIFY/report.json", "sha256": "c3d4...", "ts": "..."}
  ],
  "dissent": [],
  "evidence_refs": ["cap_01HZX9KH4N7Q2VBXR0Q8C7Y2P", "cap_01HZX9KJ8M3R5VBXR0Q8C7Y2P"],
  "expires_ts": "2026-05-15T18:14:22Z"
}
```

### §4.3 Verifier contract for the packet

[normative-description]

A `ratification_packet.json` is INVALID if any of the following hold (kernel MUST refuse to hand it to the synthesizer):

```text
PKT-FAIL-1: schema_version != "trinity.ratification_packet.v1"
PKT-FAIL-2: raw_artifacts is empty
PKT-FAIL-3: any raw_artifacts[*].sha256 does not match the on-disk hash
PKT-FAIL-4: dissent is missing (must be present, may be []; absence != [])
PKT-FAIL-5: evidence_refs contains a capture_id absent from the
            session's audit chain
PKT-FAIL-6: expires_ts is in the past relative to kernel clock
PKT-FAIL-7: proposed_decision.action is outside the closed enum
            {promote, deploy, abort, amend, reject}
```

---

## §5 — `presentation_synthesis.json` Schema

[normative-description]

The synthesis is the **output** of the presentation pipeline. It is written by the synthesizer agent (`agent:presentation_synthesizer`) at `<session>/PRESENTATION/synthesis/<synthesis_id>.json`. It is consumed by Phase 11 (DDD) when the kernel constructs `decision_packet.json`.

### §5.1 Required fields

[normative-description]

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | string | yes | const `"trinity.presentation_synthesis.v1"` |
| `synthesis_id` | string | yes | `syn_<ulid>` |
| `packet_id` | string | yes | references the input `ratification_packet.packet_id` |
| `ts` | RFC3339 | yes | when synthesizer wrote the file |
| `synthesizer` | string | yes | const `"agent:presentation_synthesizer"` (Article IV — role identity) |
| `summary` | string | yes | 1–3 sentence précis of what is being decided; ASCII-only |
| `dissent_preserved` | array | yes | each entry: `{role, position, reason, raw_link}`; MUST contain every distinct dissent position from `ratification_packet.dissent[]`; empty `[]` only if packet's dissent was `[]` |
| `convergence_axes` | array | yes | each entry: `{axis: string, agreement_basis: string, dissent_indices?: int[]}`; describes what was agreed on (and which `dissent_preserved[]` indices remain unresolved on this axis, if any); may be empty |
| `raw_artifact_links` | array | yes | each entry: `{role, path, sha256}`; MUST contain every entry from `ratification_packet.raw_artifacts[]` (no omission permitted) |
| `compression_ratio` | number | yes | `len(summary + dissent_preserved + convergence_axes) / sum(len(raw_artifacts))`; bounded `(0.0, 0.5]` per §8 verifier |
| `transport_capability` | string | yes | enum: `"full"` (raw drill-down resolvable) \| `"compressed-only"` (operator on capability-limited transport) |
| `panel_diversity` | object | yes | `{distinct_roles: int, distinct_models: int, distinct_layers: int}`; mirrors DDD §3.1 |
| `synthesizer_not_in_opinion_panel` | boolean | yes | MUST be `true`; the synthesizer MUST NOT vote in convergence/dissent (Article III + IV) |

### §5.2 Example (non-normative)

[non-normative-example]

```json
{
  "schema_version": "trinity.presentation_synthesis.v1",
  "synthesis_id": "syn_01HZX9M7T8K4P9VBXR0Q8C7Y2P",
  "packet_id": "pkt_01HZX9KQ7RW3M6VBXR0Q8C7Y2P",
  "ts": "2026-05-15T10:14:30Z",
  "synthesizer": "agent:presentation_synthesizer",
  "summary": "Deploy edge/cdn-rules; verifier PASS; 1 dissenting note on rollback timing.",
  "dissent_preserved": [
    {"role": "verifier:C", "position": "UNVERIFIED",
     "reason": "rollback rehearsal not captured", "raw_link": "VERIFY/report-c.json"}
  ],
  "convergence_axes": [{"axis": "static-analysis", "agreement_basis": "verifier A+B PASS"}],
  "raw_artifact_links": [{"role": "plan", "path": "DO/dev/plan.json", "sha256": "a1b2..."}],
  "compression_ratio": 0.18,
  "transport_capability": "full",
  "panel_diversity": {"distinct_roles": 3, "distinct_models": 2, "distinct_layers": 2},
  "synthesizer_not_in_opinion_panel": true
}
```

### §5.3 Forbidden fields

[normative-description]

The synthesis MUST NOT contain:

```text
FORBID-1: verdict — only ratification_decision.json may carry a verdict
FORBID-2: decided_by — synthesis is not a decision artefact
FORBID-3: signature — synthesis is unsigned; only the human's decision is signed
FORBID-4: any field that paraphrases a verifier verdict (e.g., "looks good"
          instead of structured PASS/FAIL/UNVERIFIED) — verbatim verdict only
FORBID-5: any extra/unknown field (additionalProperties: false)
```

### §5.3.1 Cross-spec acceptance (Phase 11 v1.0.2 alignment, 2026-05-15)

[normative-description]

As of cognitive_protocol_version v1.0.2 (cross-amended 2026-05-15 per V1.1 Amendment Queue items C-13-1 and C-13-3), the four §5 fields `dissent_preserved`, `raw_artifact_links`, `compression_ratio`, and `transport_capability` are accepted by Phase 11 §3.1 v1.0.2. The alias mapping in Phase 11 §3.1.1 is normative: `dissent_preserved` is an alias of Phase 11's canonical `dissent_flags`, and `raw_artifact_links` is the URL/path form of Phase 11's canonical `capture_refs`. Synthesizers conforming to Phase 13 §5 MAY emit these fields; downstream Phase 11 validators MUST accept them. The FORBID-1..5 list above is unaffected by this acceptance and remains in force for the four explicitly-forbidden field categories.

The FORBID-4 and FORBID-5 scopes apply to **synthesis-only** (`presentation_synthesis.json`); they do NOT apply to `ratification_decision.json`, which legitimately carries `verdict`, `decided_by`, and `signature` per §6 (Authority lives in the decision artefact). See §8 verifier scope clarification.

---

## §6 — `ratification_decision.json` Schema

[normative-description]

The decision artefact is the **human's signed verdict**. It is the only artefact in this protocol that carries authority. It is produced by the human (via direct write, CLI, or transport per Article XV) at `<session>/PRESENTATION/decisions/<decision_id>.json`.

### §6.1 Required fields

[normative-description]

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | string | yes | const `"trinity.ratification_decision.v1"` |
| `decision_id` | string | yes | `dec_<ulid>` |
| `synthesis_id` | string | yes | references the `presentation_synthesis.synthesis_id` reviewed |
| `packet_id` | string | yes | references the originating `ratification_packet.packet_id` (redundant for verifier integrity check) |
| `ts` | RFC3339 | yes | operator decision timestamp |
| `verdict` | string | yes | enum: `APPROVE` \| `REJECT` \| `DEFER` |
| `decided_by` | string | yes | format `"human:<actor>"`; e.g., `"human:operator"`, `"human:tg:42"` (Article XIII) |
| `reason` | string | yes | required, ≥1 char; the *why* (mandatory even on APPROVE) |
| `dissent_acknowledged` | array | yes | array of dissent entry indices (from synthesis.dissent_preserved) the human explicitly read; MUST cover all when verdict=APPROVE |
| `signature` | object | yes | nullable when written directly by operator at trusted CLI; HMAC envelope via Phase 9 transport boundary when transport-mediated (Article XV) |

### §6.2 Example (non-normative)

[non-normative-example]

```json
{
  "schema_version": "trinity.ratification_decision.v1",
  "decision_id": "dec_01HZX9N3P2...",
  "synthesis_id": "syn_01HZX9M7T8...",
  "packet_id": "pkt_01HZX9KQ7R...",
  "ts": "2026-05-15T10:18:05Z",
  "verdict": "APPROVE",
  "decided_by": "human:operator",
  "reason": "rollback note acknowledged; deploy in low-traffic window",
  "dissent_acknowledged": [0],
  "signature": null
}
```

### §6.3 Authority rules

[normative-description]

```text
AUTH-1: decided_by MUST start with "human:" (Article XIII;
        no agent string permitted).
AUTH-2: verdict APPROVE on a synthesis with non-empty dissent_preserved
        REQUIRES dissent_acknowledged to enumerate every entry index.
AUTH-3: signature MUST be present and HMAC-valid when the decision was
        delivered via transport (Article XV); kernel verifies via
        .ai/cli/core/auth.py before audit emission.
AUTH-4: A decision file with verdict=APPROVE on a synthesis whose
        underlying packet has expired (expires_ts < ts) is INVALID;
        kernel MUST reject and re-emit a fresh packet.
AUTH-5: reason is required even on APPROVE — silent approval is a
        violation of Article XIII (silent authorization).
```

---

## §7 — The Dissent-Preservation Rule

[normative-description]

Dissent preservation is the hardest invariant in this protocol. It is the mechanism by which Trinity refuses to reduce a panel disagreement to a false consensus. Article XXIII anchors it: **invisible failure is unconstitutional**, and an unsurfaced minority position is an invisible failure of the upstream pipeline.

### §7.1 The rule

[normative-description]

```text
RULE-D1: Every distinct dissent position present in
         ratification_packet.dissent[] MUST appear, verbatim or
         losslessly normalised, in
         presentation_synthesis.dissent_preserved[].

RULE-D2: Synthesis MUST NOT use the words "consensus", "agreement",
         "all agree", or semantic equivalents in `summary` if
         dissent_preserved[] is non-empty.

RULE-D3: If verifier emitted ANY non-PASS verdict (FAIL, UNVERIFIED,
         RETRY, NEEDS_HUMAN), that verdict MUST appear in
         dissent_preserved[] regardless of whether other verifiers
         emitted PASS.

RULE-D4: A quorum decision (e.g., 2-of-3 verifiers PASS) MUST list
         the minority position; the synthesis MUST NOT claim "verifier
         passed" — it MUST claim "verifier passed by quorum;
         dissent: <count>".

RULE-D5: A "no dissent" claim is permissible ONLY when packet.dissent
         was [] AND no upstream verifier emitted non-PASS. The verifier
         (§8) MUST cross-check this against the audit chain.
```

### §7.2 Conformance grep test (non-normative)

[non-normative-example]

```bash
# A synthesis is suspect if its summary uses convergence language
# while its dissent_preserved is non-empty.
jq -r '.summary' synthesis.json \
  | grep -Eiq 'consensus|all agree|unanimous|agreed' \
  && jq -e '.dissent_preserved | length > 0' synthesis.json \
  && echo "FAIL_DISSENT_LANGUAGE_MISMATCH"
```

The verifier (§8) runs a structured equivalent (not literal grep) over normalised summary tokens.

### §7.3 Why "lossless normalisation" is permitted but bounded

[normative-description]

The synthesizer MAY rephrase a dissent position for clarity (e.g., joining two sentences) but MUST preserve:

```text
- the dissenting role identity (e.g., "verifier:C")
- the verbatim verdict token if structured (PASS/FAIL/UNVERIFIED)
- the reason in semantically equivalent form
- the raw_link to the source artefact
```

Rephrasing that drops any of the above is a constitutional violation, not stylistic compression. The verifier checks role identity, verdict token, and raw_link integrity bit-exactly; it checks `reason` for length-floor and strict embedding-similarity bounds via deterministic embedding-hash compare. The strict similarity check is **Layer 1 (deterministic)** per the Pyramid of Judgment, consistent with §8's "deterministic checker" framing. Only when Layer 1 returns `UNVERIFIED` (e.g., embedding model unavailable, or similarity score ambiguous within an explicit dead-band) does the kernel escalate to **Layer 3 (gated LLM judge)** per Phase 3 §2; Layer 3 is never the default path for §7.3.

---

## §8 — Presentation Verifier Contract

[normative-description]

The presentation verifier is a **deterministic** checker invoked by the kernel after a synthesis is written and before any `decision_packet.json` referencing it is emitted. It corresponds to Phase 3's verifier pyramid (TRINITY_VERIFIER_CONTRACT_V1) at **Layer 1 (deterministic rules)**; semantic-similarity checks for dissent reason fall back to Layer 2 (policy engine) when the rule cannot be decided deterministically.

### §8.1 Inputs

[normative-description]

```text
- presentation_synthesis.json (under check)
- the referenced ratification_packet.json
- the per-session audit chain (read-only) for cross-checks
```

### §8.1.1 Verifier scope clarification (2026-05-15 cross-amendment)

[normative-description]

The §8 verifier (CHK-1..13 + FAIL-* tokens) operates on `presentation_synthesis.json` artefacts ONLY. It does NOT inspect `ratification_decision.json` artefacts.

Per V1.1 Amendment Queue item C-13-3 (resolved 2026-05-15): the FORBID-1..5 checks of §5.3 reject `verdict`, `decided_by`, and `signature` only when they appear inside a synthesis. The same fields are REQUIRED by §6 inside a `ratification_decision.json` (Authority lives in the decision artefact). The presentation verifier MUST NOT cross-fail decision artefacts on FORBID-N grounds; decision-side checks are scoped under §6.3 AUTH-1..5 and consumed by Phase 11 (DDD) downstream.

Operationally: a synthesizer that accidentally writes a `verdict` field into `presentation_synthesis.json` is FORBID-1 violation (synthesis verdict FAIL); a human writing `verdict: "APPROVE"` into `ratification_decision.json` is the normative path and is NOT a §8 concern.

### §8.2 Verdicts

[normative-description]

| Verdict | Meaning |
|---|---|
| `PASS` | All §8.3 checks pass; kernel may emit `decision_packet` referencing this synthesis. |
| `FAIL` | At least one §8.3 check failed; kernel MUST NOT emit `decision_packet`; synthesizer MUST regenerate. |
| `UNVERIFIED` | A check could not be decided at Layer 1 and Layer 2 was disabled or unavailable; treated as FAIL by the kernel for gate purposes (Article XXIII: invisible failure is failure). |

### §8.3 Checks (closed list)

[normative-description]

```text
CHK-1  schema_version == "trinity.presentation_synthesis.v1"
CHK-2  packet_id resolves to a present, non-expired ratification_packet
CHK-3  every raw_artifacts[] entry from packet appears in
       raw_artifact_links[] with matching sha256
CHK-4  every dissent[] entry from packet appears in
       dissent_preserved[] with matching role + verdict token
CHK-5  compression_ratio is in (0.0, 0.5]
CHK-6  summary length is in [40, 1200] ASCII chars
CHK-7  if dissent_preserved[] is non-empty, summary token-set does not
       contain {"consensus", "unanimous", "all agree"} (RULE-D2)
CHK-8  synthesizer == "agent:presentation_synthesizer"
CHK-9  synthesizer_not_in_opinion_panel == true
CHK-10 panel_diversity.distinct_layers >= 2 when proposed_decision.action
       is in {deploy, promote} (COLD-tier requirement, per Phase 11 §3.1)
CHK-11 transport_capability is "full" OR proposed_decision.action is
       not in {deploy, promote} (compressed-only is forbidden for
       irreversible actions; Article XIII)
CHK-12 no FORBID-1..5 fields are present (additionalProperties: false)
CHK-13 cross-check: every non-PASS verifier verdict in audit chain since
       packet.ts appears in dissent_preserved[] (RULE-D3)
```

### §8.4 Failure tokens

[normative-description]

Each failed check MUST emit a structured failure token in the verifier's audit event payload:

```text
FAIL_SCHEMA_VERSION_MISMATCH   (CHK-1)
FAIL_PACKET_NOT_FOUND          (CHK-2)
FAIL_PACKET_EXPIRED            (CHK-2)
FAIL_BROKEN_RAW_LINK           (CHK-3)
FAIL_DISSENT_ERASED            (CHK-4, CHK-13)
FAIL_NO_COMPRESSION            (CHK-5 upper bound)
FAIL_SUMMARY_TOO_LONG          (CHK-6 upper)
FAIL_SUMMARY_TOO_SHORT         (CHK-6 lower)
FAIL_DISSENT_LANGUAGE_MISMATCH (CHK-7)
FAIL_SYNTHESIZER_IDENTITY      (CHK-8)
FAIL_SYNTHESIZER_VOTED         (CHK-9)
FAIL_PANEL_DIVERSITY_INSUFFICIENT (CHK-10)
FAIL_TRANSPORT_INSUFFICIENT    (CHK-11)
FAIL_FORBIDDEN_FIELD_PRESENT   (CHK-12)
FAIL_NO_DECISION_QUESTION      (no founder_decisions_required parity
                                 with DDD §3.1)
```

### §8.5 Audit emission

[normative-description]

The verifier MUST emit one audit event per invocation, namespaced under the Phase 10 registry as `presentation.verified` (event_type added via Article XXIX amendment of TRINITY_AUDIT_EVENT_SPEC_V1 §3, filed alongside this spec). Payload shape:

```json
{
  "synthesis_id": "syn_...",
  "packet_id": "pkt_...",
  "verdict": "PASS|FAIL|UNVERIFIED",
  "checks_run": ["CHK-1", "CHK-2", "..."],
  "failures": ["FAIL_DISSENT_ERASED", "..."],
  "verifier_version": "v1.0"
}
```

### §8.6 Cross-reference: Pyramid of Judgment

[normative-description]

This verifier is **Layer 1** (deterministic rules) of the pyramid declared in CLAUDE.md (`Pyramid of Judgment`). When CHK-7 (semantic dissent-language detection) cannot be decided by token lookup, it falls back to Layer 2 (policy engine via `.ai/policies/safety.yaml`). Layer 3 (gated LLM judge) is **explicitly out of scope** for this verifier — a presentation that requires LLM judgment to validate is itself suspect (Article XVIII: determinism over emergence).

### §8.7 Integration with Phase 3 Verifier Pyramid

[normative-description]

The presentation verifier defined in §8 does NOT stand alongside the Phase 3 verifier as a peer; it is a **Layer 1 sub-verifier** under the pyramid declared in TRINITY_VERIFICATION_CONTRACT_SPEC_V1 (Phase 3). This subordination is normative and resolves the apparent overlap between §8 and Phase 3.

```text
INT-V3-1: The presentation verifier is a Layer-1 sub-verifier whose
          domain is presentation_synthesis.json artefacts only.
INT-V3-2: Each CHK-1..CHK-13 evaluation MUST emit an audit event of
          type `verifier.layer1.presentation.<check>` (e.g.,
          `verifier.layer1.presentation.chk_4`) into the Phase 10
          audit chain, in addition to the §8.5 `presentation.verified`
          summary event.
INT-V3-3: These per-check events flow into the standard Phase 3
          verifier verdict envelope (PASS / FAIL / UNVERIFIED) per
          Phase 3 §2; the kernel reads the envelope, not the
          per-check events, when gating decision_packet emission.
INT-V3-4: §8.4 FAIL_* tokens and §8 refusal codes are LAYER-1 outputs.
          They are NOT standalone verdicts; they are FAIL evidence
          rolled up by the Phase 3 envelope. A FAIL_* token without
          an enveloping Phase 3 verdict is malformed.
INT-V3-5: Layer 2 (policy engine) and Layer 3 (gated LLM judge)
          fallbacks are governed by Phase 3, not by this spec; §7.3
          and §8.6 reference them but do not redefine them.
```

A Phase 3 verifier implementation that consumes presentation artefacts MUST treat the §8 checks as one of its Layer-1 sub-verifiers; conversely, the §8 checks MUST NOT be invoked outside the Phase 3 envelope (no standalone gating).

---

## §9 — Conformance Test Matrix

[normative-description]

The matrix below pins the minimum behaviour an implementation MUST satisfy. Each row is one black-box test: given an input artefact, observe the synthesizer's behaviour, then run the verifier and assert the verdict. Tests live at `.ai/cli/tests/test_presentation_protocol.py` (to be added by implementation phase, not by this spec).

### §9.1 Matrix

[normative-description]

| # | Input artefact (packet shape) | Synthesizer behaviour | Expected verifier verdict | Failure token (if FAIL) |
|---|---|---|---|---|
| 1 | Well-formed packet, no dissent | Emits summary + empty `dissent_preserved`; convergence_axes populated; ratio 0.20 | PASS | — |
| 2 | Well-formed packet, 2 dissent entries | Preserves both entries verbatim; summary acknowledges "2 of 3 verifiers PASS" | PASS | — |
| 3 | Well-formed packet, 2 dissent entries | Drops 1 dissent entry from `dissent_preserved` | FAIL | `FAIL_DISSENT_ERASED` |
| 4 | Well-formed packet, 1 dissent entry | Preserves entry but `summary` says "consensus reached" | FAIL | `FAIL_DISSENT_LANGUAGE_MISMATCH` |
| 5 | Well-formed packet, deploy action | Emits synthesis with `panel_diversity.distinct_layers = 1` | FAIL | `FAIL_PANEL_DIVERSITY_INSUFFICIENT` |
| 6 | Well-formed packet, deploy action | Emits synthesis with `transport_capability = "compressed-only"` | FAIL | `FAIL_TRANSPORT_INSUFFICIENT` |
| 7 | Packet with raw_artifacts hash drift on disk | Synthesizer copies links faithfully | FAIL | `FAIL_BROKEN_RAW_LINK` |
| 8 | Packet expired (expires_ts < now) | Synthesizer emits valid synthesis | FAIL | `FAIL_PACKET_EXPIRED` |
| 9 | Synthesizer adds field `verdict: "APPROVE"` | — | FAIL | `FAIL_FORBIDDEN_FIELD_PRESENT` |
| 10 | Synthesizer sets `synthesizer_not_in_opinion_panel: false` | — | FAIL | `FAIL_SYNTHESIZER_VOTED` |
| 11 | Synthesizer claims `synthesizer: "agent:planner"` | — | FAIL | `FAIL_SYNTHESIZER_IDENTITY` |
| 12 | Compression ratio = 0.95 (near passthrough) | — | FAIL | `FAIL_NO_COMPRESSION` |
| 13 | Summary length 12 chars | — | FAIL | `FAIL_SUMMARY_TOO_SHORT` |
| 14 | Summary length 4000 chars | — | FAIL | `FAIL_SUMMARY_TOO_LONG` |
| 15 | Audit chain shows verifier UNVERIFIED since packet.ts; synthesis omits it | — | FAIL | `FAIL_DISSENT_ERASED` (via CHK-13) |
| 16 | Decision: APPROVE with empty `dissent_acknowledged` while synthesis has dissent (out-of-scope v1, see Phase 11 §9 Q1 — multi-operator quorum is not modelled in v1; single-operator AUTH-2 enforcement only) | — (decision-side check; not verifier of synthesis) | DDD-side reject | (per AUTH-2) |
| 17 | Decision: APPROVE with `decided_by: "agent:foo"` | — | DDD-side reject | (per AUTH-1) |
| 18 | Decision: APPROVE on expired packet | — | DDD-side reject | (per AUTH-4) |
| 19 | Decision: APPROVE with `reason: ""` | — | DDD-side reject | (per AUTH-5) |

### §9.2 Conformance harness invocation (non-normative)

[non-normative-example]

```bash
# Run the matrix; each row is a pytest case
cd .ai && python3 -m pytest cli/tests/test_presentation_protocol.py -v

# Spot-check one synthesis manually
bash .ai/cli/ai presentation verify <synthesis_id>
```

---

## §10 — Versioning & Article XXIX Amendment Protocol

[normative-description]

This protocol owns three persistent artefact schemas. Each evolves independently under Article XXIX, and **past artefacts MUST remain inspectable** (Article XXIX final clause).

### §10.1 Schema version pins

[normative-description]

```text
trinity.ratification_packet.v1
trinity.presentation_synthesis.v1
trinity.ratification_decision.v1
```

The constant string is part of the schema (CHK-1, PKT-FAIL-1, equivalent for decision). A reader MUST refuse a file whose `schema_version` is unknown to it.

### §10.2 Adding a field (backward-compatible)

[normative-description]

Adding a field requires:

```text
1. Article XXIX proposal at docs/constitution/addendums/<id>.md
2. Field MUST be optional in the new version
3. schema_version bumped using DOT form (never underscore):
   trinity.presentation_synthesis.v1 -> trinity.presentation_synthesis.v1.1
   (the suffix is `.v1.1`, not `.v1_1`; this is the canonical notation
   used across §10 and the schema-pin table at §10.1)
4. Verifier (§8) updated to accept both v1 and v1.1
5. Matrix (§9) gains rows covering the new field
6. Audit event presentation.verified payload gains
   verifier_version: "v1.1"
```

### §10.3 Removing or renaming a field (breaking)

[normative-description]

Breaking changes require:

```text
1. Article XXIX proposal with explicit "BREAKING" tag
2. New schema_version (e.g., trinity.presentation_synthesis.v2)
3. Migration plan for past artefacts (read-only inspection guaranteed)
4. Past artefacts NEVER rewritten in place; new artefacts use new schema
5. Verifier supports both versions in parallel for ≥1 release cycle
6. Audit event registry (Phase 10) updated to reflect new event_type
   (e.g., presentation.verified.v2) if payload shape changed
```

### §10.4 Forbidden silent changes

[normative-description]

```text
FORBID-AMEND-1: Changing the meaning of an existing field without
                version bump.
FORBID-AMEND-2: Tightening a verifier check without version bump
                (past synthesis files would silently fail).
FORBID-AMEND-3: Loosening a dissent-preservation rule (RULE-D1..D5)
                under any version — dissent preservation is a
                constitutional invariant under Article XXIII and
                requires a CONSTITUTIONAL amendment, not a workflow-
                contract amendment.
FORBID-AMEND-4: Permitting verdict in presentation_synthesis.json
                under any version — this would collapse Articles III,
                IV, and XIII; requires constitutional amendment.
```

### §10.5 Inspectability guarantee

[normative-description]

Per Article XXIX, prior versions remain inspectable. Operationally:

```text
- All schema files (when generated) live at .ai/schemas/presentation/
  with versioned filenames (packet.v1.schema.json, etc.).
- Past artefacts in <session>/PRESENTATION/ are append-only; the audit
  chain references them by sha256.
- The verifier MUST be able to load any prior schema version and
  produce a verdict; "schema too old" is itself a verdict, not a
  refusal-to-load.
```

### §10.6 Cross-spec dependencies (informational)

[normative-description]

This protocol composes with:

```text
- TRINITY_DDD_HUMAN_GATE_SPEC_V1 §3 (decision_packet consumes synthesis)
- TRINITY_AUDIT_EVENT_SPEC_V1 §3 (presentation.verified registered)
- 02_VERIFIER_SPEC.md (Pyramid of Judgment Layer 1+2 fallback)
- 14_TRINITY_TG_BOT_SPEC.md (transport-side rendering of synthesis)
- TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md (ddd ritual gate consumes
  presentation_synthesis via decision_packet)
```

A change to any of these specs that affects presentation contract MUST file a co-amendment under Article XXIX.

---

## §11 — Final Invariants Recap

[normative-description]

```text
INV-1: Compressed UI is a VIEW; never the truth layer (Article XX).
INV-2: Dissent is preserved verbatim or losslessly normalised
       (Article XXIII).
INV-3: Synthesizer drafts; human decides; kernel governs (Articles
       III + IV + XIII).
INV-4: Authority lives in ratification_decision.json; nowhere else
       in this protocol (Article XIII).
INV-5: Presentation runs on explicit invocation; never self-triggered
       (Article XX).
INV-6: Schema evolution follows Article XXIX; dissent rule cannot be
       loosened by workflow amendment (Article XXIX + XXIII).
INV-7: Synthesizer authority is READ-ONLY over raw artefacts and
       WRITE-ONLY over presentation_synthesis.json; nothing else
       (Article XVI).
```

```text
No synthesis = No human-readable view.
No verifier PASS = No decision_packet.
No human signature = No authority.
No raw_artifact_links = No truth-layer linkage.
No dissent preservation = No Trinity.
```
