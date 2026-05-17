---
title: "Trinity Spec V1.1 Amendment Queue"
version: "1.0"
status: "active"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes:
  - "(none -- first canonical version)"
source: "6-spec review conducted 2026-05-15 against Phase 3, 4, 5, 12, 13, 14 V1 specs"
amendment-policy: "Article XXIX -- per-item classification editorial / operational / constitutional; each item is a candidate for individual amendment session."
---

# Trinity Spec V1.1 Amendment Queue

## Section 0 -- Resolution Status (Batch 2026-05-15)

This queue is **substantially RESOLVED** as of 2026-05-15 via 4 amendment sessions:

| Session | Items addressed | Commit |
|---|---|---|
| Phase 11+13 cross-amendment v1.0.2 | C-13-1, C-13-3 | d74ee6b |
| Phase 12 retro_envelope.md production | C-12-1, C-12-3 | 1cf9122 |
| Phase 5 artifacts + V1.1 re-frame | C-5-1, C-5-3, C-4-2 (FALSE-POSITIVE) | 733b5d6 |
| V1.1 batch cleanup (this commit) | All remaining 12 CRITICAL + 21 NOTABLE + 15 NITPICK | (pending) |

**Outcomes:**
- 12 CRITICAL: 11 RESOLVED + 1 FALSE-POSITIVE (C-4-2 de-listed) + 1 NEW (C-RITUAL-1, also resolved this batch)
- 21 NOTABLE: all RESOLVED via batch
- 15 NITPICK: all RESOLVED via batch
- 7 spec V1 files amended; 3 ai_entry/CLAUDE docs synced (C-RITUAL-1)
- pytest 1063/1063 throughout; audit chain genesis intact

**Per-item RESOLVED tags (batch 2026-05-15 cleanup commit):**
- C-3-1 RESOLVED, C-3-2 RESOLVED, C-3-3 RESOLVED (Phase 3 spec amended)
- C-4-1 RESOLVED, C-4-3 RESOLVED (Phase 4 spec amended; C-4-2 de-listed earlier)
- C-5-2 RESOLVED (Phase 5 spec §8.5 boundary check added)
- C-12-2 RESOLVED (Phase 12 spec §6.3 drift resolution added)
- C-13-2 RESOLVED (Phase 13 spec §8.7 verifier-pyramid integration added)
- C-14-1 RESOLVED, C-14-2 RESOLVED, C-14-3 RESOLVED (Phase 14 spec amended)
- C-RITUAL-1 RESOLVED (SHORT_CODES.md + CLAUDE.md + WORKFLOW.md sequence-order doc-synced to graph)
- N-3-1 RESOLVED, N-3-2 RESOLVED, N-3-3 RESOLVED (Phase 3 NOTABLE batch)
- N-4-1 RESOLVED, N-4-2 RESOLVED, N-4-3 RESOLVED, N-4-4 RESOLVED (Phase 4 NOTABLE batch)
- N-5-1 RESOLVED, N-5-2 RESOLVED, N-5-3 RESOLVED (Phase 5 NOTABLE batch)
- N-12-1 RESOLVED, N-12-2 RESOLVED, N-12-3 RESOLVED (Phase 12 NOTABLE batch)
- N-13-1 RESOLVED, N-13-2 RESOLVED, N-13-3 RESOLVED, N-13-4 RESOLVED (Phase 13 NOTABLE batch)
- N-14-1 RESOLVED, N-14-2 RESOLVED, N-14-3 RESOLVED, N-14-4 RESOLVED (Phase 14 NOTABLE batch)
- NP-3-1 RESOLVED, NP-3-2 RESOLVED (Phase 3 NITPICK)
- NP-4-1 RESOLVED, NP-4-2 RESOLVED (Phase 4 NITPICK)
- NP-9-1 RESOLVED, NP-9-2 RESOLVED, NP-9-3 RESOLVED, NP-9-4 RESOLVED, NP-9-5 RESOLVED (Phase 9 NITPICK)
- NP-13-1 RESOLVED, NP-13-2 RESOLVED, NP-13-3 RESOLVED (Phase 13 NITPICK)
- NP-14-1 RESOLVED, NP-14-2 RESOLVED, NP-14-3 RESOLVED (Phase 14 NITPICK)

The per-item rows in Sections 3, 4, 5 below are kept as historical record of the issues found in the 2026-05-15 6-spec review. RESOLVED tags inline mark items addressed in pre-batch sessions; the batch cleanup addressed all remaining items en bloc per the operator-approved fix sequence (Section 7).

## Section 1 -- Purpose

This document is the **actionable backlog** of issues found during the 2026-05-15 critical review of six newly-landed Trinity v2 specifications (Phase 3 Verification Contract, Phase 4 Kernel State Transition, Phase 5 Policy Engine, Phase 12 Retro/RRR Split, Phase 13 Presentation Protocol, Phase 14 Root of Trust).

The review was conducted by six parallel reviewer agents, each reading one spec end-to-end and cross-checking against:
- Constitution v1.0 + Addendums v1.0.1 through v1.0.4 (anchor faithfulness).
- Sibling V1 specs (cross-spec coherence).
- Current `.ai/policies/`, `.ai/graphs/`, `.ai/cli/` ground-truth files (spec-vs-implementation alignment).

This queue does **not** amend any spec directly. Each row is a candidate for an individual Article XXIX amendment session per `[[feedback_plan_amendment_vs_subsession]]` discipline.

## Section 2 -- Severity & Article XXIX Classification

**Severity buckets** (from review):
- **CRITICAL** -- blocks future implementation; spec contradicts itself, Constitution, or sibling spec.
- **NOTABLE** -- queue for v1.1; non-blocking but should fix before production deployment.
- **NITPICK** -- cosmetic; editorial typo, ULID example length, semver notation.

**Article XXIX tier classification** (per Addendum v1.0.4 §XXIX 3-tier):
- **editorial** -- typo / formatting / cross-ref correction; no semantic change. Operator may patch directly with audit entry.
- **operational** -- workflow / procedure / schema field clarification; semantic change but backward-compatible. Requires proposal + rationale + audit entry.
- **constitutional** -- changes load-bearing definition or constraint. Requires full Article XXIX 6-step procedure (proposal + rationale + impact + human approval + version bump + audit entry).

## Section 3 -- CRITICAL Items (16 entries + 1 new + 1 false-positive)

| ID | Spec | Section | Description | XXIX tier | Suggested fix |
|---|---|---|---|---|---|
| C-3-1 | Phase 3 | §4.2 line 363 | Cross-ref to "TRINITY_VERIFIER_CONTRACT_V1 Section 4" wrong; tier model lives in Phase 8 §3, not §4 | editorial | Patch §4.2 table header to reference §3 |
| C-3-2 | Phase 3 | §10.5 + §5.4 + §8.3 | policy_snapshot scope incomplete; doesn't cover verifier-rules.yaml; conformance test §8.3 has no guidance on rule-set drift | operational | Expand policy_snapshot field set; add §8.3 drift-detection clause |
| C-3-3 | Phase 3 | §2.5 + §4.3 + §4.6 | Verdict precedence "NOT contract-overridable" but contract validator has no enforcement; predicates ordering unenforced | operational | Add precedence-validator schema in §4.6; reject contracts that violate ordering |
| C-4-1 | Phase 4 | §3.1 row T2 | T2 pre-condition paradox: "vvv_pass exists OR risk tier permits skip" reads as always-required; HOT tier escape hatch ambiguous | operational | Reword T2 pre-condition to explicit disjunct: "(vvv_pass) OR (risk_tier == HOT AND vvv skipped)" |
| C-4-2 | Phase 4 | §3.1 row T3 | ~~**HIGH**: T3 SANDBOX-to-DO transition declared in spec but missing from `.ai/graphs/standard.yaml`; silent divergence~~ \| **FALSE-POSITIVE 2026-05-15** -- T3 IS present in standard.yaml lines 39-42 (verified by direct disk read); original review agent erred. No amendment needed. | editorial (de-listing) | Remove from CRITICAL count; original review report should note read-error |
| C-4-3 | Phase 4 | §3.1 row T9 | T9 close pre-condition requires "verify dev AND verify prod both passed" before close; conflicts with Session Close §2.2 mid-close validation | operational | Split T9 into two-phase model (T9a: DONE-to-in-flight; T9b: validate+capture+seal) |
| C-5-1 | Phase 5 | §3.1 row 4 | trinity_policy.yaml declared as "Phase 5 deliverable" with no schema; engine cannot validate query without rule structure \| RESOLVED 2026-05-15 (.ai/policies/trinity_policy.yaml landed as operator-authored draft, 351 lines) | operational | Add §3.5 trinity_policy.yaml schema reference (file is human-authored per Article XIII) |
| C-5-2 | Phase 5 | §8.4 + §2.1 | NEEDS_HUMAN verdict shared between policy and verifier; Article IV separation boundary not enforced at runtime | operational | Add §8.5 boundary check requiring engine to verify verifier verdicts do not encode policy decisions |
| C-5-3 | Phase 5 | §4.1 | `.ai/schemas/policy_query_envelope.v1.yaml` referenced as mandatory boot gate; file does not exist \| RESOLVED 2026-05-15 (.ai/schemas/policy_query_envelope.v1.yaml landed as operator-authored draft, 378 lines) | operational | Author the schema file in a separate human-authored session (Article III + XIII) |
| C-RITUAL-1 | Phase 4 | `.ai/graphs/standard.yaml` lines 35-42 vs `docs/ai_entry/SHORT_CODES.md` | **NEW 2026-05-15** -- ritual ordering inversion: kernel state graph fires `nnn_pass` (THINK->SANDBOX) BEFORE `vvv_pass` (SANDBOX->DO), but SHORT_CODES.md and CLAUDE.md document the canonical sequence as `sss -> vvv -> nnn -> gogogo` (vvv before nnn). Surfaced by Phase 4 T3 amendment-proposal agent during V1.1 review. Phase 4 spec §3.4 COLD example is chronologically impossible under the actual graph. | constitutional | Either reorder graph (operational risk: existing sessions assume current order) OR amend SHORT_CODES.md + CLAUDE.md to document graph-true sequence (`sss -> nnn -> vvv -> gogogo`) -- recommend the latter as lower risk |
| C-12-1 | Phase 12 | §3 + §4 | retro_envelope.md schema mandated but current rrr.py writes only THINK/RETRO.md; conformance C1-C7 cannot pass \| RESOLVED 2026-05-15 (retro_envelope.md production landed in rrr.py) | operational | Either implement retro_envelope.md production in rrr.py OR mark §3-4 as deferred-implementation in §11 |
| C-12-2 | Phase 12 | §6.2 + Phase 15 §3 | audit_chain_anchor read once at rrr but re-read at close; no specification for drift handling on concurrent sessions | operational | Add §6.3 drift-resolution clause; mirror Phase 15 close-time recheck logic |
| C-12-3 | Phase 12 | §6.2 | rrr.completed payload lists 16+ required fields but current rrr.py emits subset; spec-implementation gap \| RESOLVED 2026-05-15 (retro_envelope.md production landed in rrr.py) | operational | Align rrr.py emission OR mark unimplemented fields as "v1.1 deferred" |
| C-13-1 | Phase 13 | §5 vs Phase 11 §3.1 | **HIGH**: §5 schema overload -- adds dissent_preserved[], compression_ratio, transport_capability, raw_artifact_links[] NOT in Phase 11 DDD contract; presentation_synthesizer/core.py:37-48 validates only 9 DDD fields \| RESOLVED 2026-05-15 (Phase 11 v1.0.2 alias mapping landed) | constitutional | Cross-amend Phase 11 DDD §3.1 to expand schema OR drop 4 extra fields from Phase 13 §5 |
| C-13-2 | Phase 13 | §8 vs Phase 3 | **HIGH**: presentation verifier (13 checks + 17 FAIL_* tokens) overlaps Phase 3 verifier; no integration contract; runtime ambiguity | constitutional | Add Phase 13 §8.7 integration clause specifying presentation verifier as "Layer 1 sub-verifier under Phase 3 pyramid" |
| C-13-3 | Phase 13 | §6 vs Phase 11 §4 | ratification_decision carries verdict/decided_by/signature; Phase 13 §8 verifier rejects them as FORBID-4 if present in synthesis; cross-spec field semantics conflict \| RESOLVED 2026-05-15 (Phase 11 v1.0.2 alias mapping landed) | operational | Clarify §8 forbid scope: applies to synthesis only, not decision; document in §5.3 |
| C-14-1 | Phase 14 | §5.2 vs §5.1 | 7 required fields in §5.1; only 6 mapped to Article XXIX steps in §5.2; field `constitutional_articles_invoked` unmapped | operational | Add 7th XXIX-step mapping for `constitutional_articles_invoked` (likely "step 1 proposal" anchor) |
| C-14-2 | Phase 14 | §7.2 vs Addendum v1.0.4 §XXIX.5 | New event type `root.tier.declared` declared in spec but not registered in parent Addendum v1.0.4 audit-event taxonomy | operational | Either register in Addendum v1.0.4 (constitutional bump) OR remove `root.tier.declared` from §7.2 |
| C-14-3 | Phase 14 | §3.3 + §8.2 | `verified_at` field trigger semantics ambiguous: idempotent (last success) or accumulative (every check)? §8.2 specifies `ai root verify` but not update behavior | operational | Add §3.4 explicit semantics: "verified_at updates on every successful verify call, regardless of outcome change" |

## Section 4 -- NOTABLE Items (queue v1.1)

| ID | Spec | Section | Description | XXIX tier |
|---|---|---|---|---|
| N-3-1 | Phase 3 | §10.3 | Glossary cross-ref "02_VERIFIER_SPEC.md" inconsistent format with hierarchy convention | editorial |
| N-3-2 | Phase 3 | §5.2 + §7.2 | policy.violation.detected event payload missing from verify.completed downstream consumers | operational |
| N-3-3 | Phase 3 | §6.6 | Layer-3 PASS authority justification not pinned in contract envelope schema | operational |
| N-4-1 | Phase 4 | cover + §2.1 | "16 states" claim vs §2.1 lists 17 states (DEGRADED inclusion ambiguous) | editorial |
| N-4-2 | Phase 4 | §2.5 | Sub-graph stack not in canonical transition table; T6 deploy mechanics unclear | operational |
| N-4-3 | Phase 4 | §3.1 audit column | Audit event names not cross-referenced to Phase 10 registry | operational |
| N-4-4 | Phase 4 | §3.1 T7 + T7b | rrr ordering ambiguous (post-VERIFIED vs post-DEPLOYED); HOT/WARM tier path unclear | operational |
| N-5-1 | Phase 5 | §3.1 + verifier-rules.yaml line 46 | rbac.yaml referenced but not in §3 catalog | operational |
| N-5-2 | Phase 5 | §9.3 + §9.4 | Amendment query_id traceability ambiguous; no spec for query session-context carry | operational |
| N-5-3 | Phase 5 | §9.5 | Stale-rule detection requires "no fires in window" audit query — manual today | operational |
| N-12-1 | Phase 12 | §7.3 vs Phase 15 §4 | memory_index severity tier resolution not cross-ref'd to Session Close priority order | operational |
| N-12-2 | Phase 12 | §3.1 + §4.3 | gogogo_verdicts schema informal; no explicit `{total, pass, fail, unverified}` block | editorial |
| N-12-3 | Phase 12 | §4.3 | baseline_untracked cross-session reconciliation logic opaque | operational |
| N-13-1 | Phase 13 | §2.1 + §5.1 | convergence_axes object shape under-specified for Example A pattern | operational |
| N-13-2 | Phase 13 | §4 + Phase 11 §2 | ratification_packet lifecycle unclear (intermediate vs persisted); writer/timing undefined | operational |
| N-13-3 | Phase 13 | §7.3 vs §8 | Dissent-reason similarity check references "Layer 3 fallback" but spec claims §8 deterministic; contradiction | operational |
| N-13-4 | Phase 13 | §8.3 CHK-10 vs Phase 11 §3.1 | "HOT-tier" vs "COLD-tier" terminology inconsistency between Phase 13 and Phase 11 | editorial |
| N-14-1 | Phase 14 | §2.2 | Threat-model out-of-scope items (operator compromise, supply-chain, MITM) not explicitly anchored | operational |
| N-14-2 | Phase 14 | §4.1 vs §8 refusal codes | Layer 0 closed-set enforcement has no refusal code; new files silently land in BADPATH | operational |
| N-14-3 | Phase 14 | §10.4 | Manifest compaction / retention SLA not specified; ratification_chain[] grows unbounded | operational |
| N-14-4 | Phase 14 | §6.2 | Tier 1-to-2 migration ceremony lacks pre-transition key-installation validation | operational |

## Section 5 -- NITPICK Items (cosmetic)

| ID | Spec | Section | Description | XXIX tier |
|---|---|---|---|---|
| NP-3-1 | Phase 3 | §10.1 line 930 | Self-referential glossary entry for "Verdict" | editorial |
| NP-3-2 | Phase 3 | §4.4 line 400 | Example sentence formatting artifact | editorial |
| NP-4-1 | Phase 4 | §1.2 frontmatter | Article XXIX listed as anchor but not quoted in §1.2 | editorial |
| NP-4-2 | Phase 4 | §2.3 | Terminal-state definition note buried; reword for clarity | editorial |
| NP-9-1 | Phase 9 | §1.2 | "Verbatim" Article XV uses ASCII -- instead of em-dash (acceptable per ASCII constraint, document the choice) | editorial |
| NP-9-2 | Phase 9 | §5.5 | Expiry conflated into TRANSPORT_REFUSED_REPLAY; semantically distinct (consider TRANSPORT_REFUSED_EXPIRED in v2.0) | operational |
| NP-9-3 | Phase 9 | §4.1 | Pins Python `hmac` module; should be language-agnostic | editorial |
| NP-9-4 | Phase 9 | §9 TBT-22 | "kernel:boundary:refusal" authority class not defined in §6 | editorial |
| NP-9-5 | Phase 9 | §4.1 | Wrong-algorithm maps to BADKEY (semantic stretch -- BADKEY about keys, not algos) | editorial |
| NP-13-1 | Phase 13 | §4.2 + §5.2 | ULID examples truncated (not 26-char) | editorial |
| NP-13-2 | Phase 13 | §10.2 | Semver notation unclear (dot vs underscore in suffix) | editorial |
| NP-13-3 | Phase 13 | §9.1 row 16 | Multi-operator quorum row contradicts Phase 11 v1 single-operator scope | editorial |
| NP-14-1 | Phase 14 | §1.2 | CLAUDE.md reference forward-looking; pre-genesis verifiability ambiguous | editorial |
| NP-14-2 | Phase 14 | §3.4 | `<sha256-placeholder>` usage clarification | editorial |
| NP-14-3 | Phase 14 | §12 Q3 | Constitution Pointer membership decision deferred to Open Questions; should move to §4.4 | editorial |

## Section 6 -- Cross-Spec Coherence Themes

Three recurring themes emerged from the 6-spec review:

### 6.1 Schema overload across spec boundaries
- **Phase 13 § 5 vs Phase 11 §3.1** -- presentation_synthesis adds 4 fields not in DDD contract (C-13-1, C-13-3).
- **Phase 12 §6.2 vs current rrr.py** -- 16+ required payload fields, current emit is subset (C-12-3).
- **Phase 5 §3.1 vs trinity_policy.yaml** -- schema referenced but file does not exist (C-5-1).

**Mitigation**: each new spec MUST cross-reference sibling specs at field level, not just document level. Add §11 "Cross-Spec Schema Compatibility Matrix" template for future spec authoring.

### 6.2 Spec-vs-implementation drift
- **Phase 4 T3 vs `.ai/graphs/standard.yaml`** -- spec declares transition not in graph (C-4-2).
- **Phase 12 retro_envelope.md vs rrr.py** -- spec mandates deterministic envelope; rrr.py writes only RETRO.md (C-12-1).
- **Phase 5 trinity_policy.yaml + policy_query_envelope.schema.yaml** -- both referenced as boot gates; both missing (C-5-1, C-5-3).

**Mitigation**: spec authoring MUST include "Implementation Status" section per spec, declaring each artifact as `landed` / `deferred-to-implementation-session` / `human-authored-pending`. Future Phase 16 integration runs MUST verify spec-implementation alignment before declaring acceptance.

### 6.3 Article XXIX tier classification gaps
- **Phase 14 §7.2 root.tier.declared** -- audit event added in spec but not registered in parent Addendum (C-14-2).
- **Phase 4 T3** -- spec adds transition to constitutional graph file (constitutional change unrecorded as such) (C-4-2).
- **Phase 13 §5 schema overload** -- semantic schema change without cross-amendment of Phase 11 (C-13-1).

**Mitigation**: every spec V1 amendment that adds events / states / schema fields to a sibling spec MUST land as a paired amendment session (one spec amendment + one sibling cross-amendment), not as a unilateral addition.

## Section 7 -- Suggested Fix Sessions Sequence

Recommended ordering for v1.1 amendment sessions (highest leverage first):

1. **Cross-amendment Phase 11 + Phase 13 schema alignment** (~~C-13-1~~, C-13-2, ~~C-13-3~~) -- C-13-1 + C-13-3 RESOLVED 2026-05-15 via Phase 11 v1.0.2 alias mapping (DDD §3.1 + §3.1.1 expanded; presentation_synthesizer validator updated; verifier scope clarified in Phase 13 §5.3.1 + §8.1.1). Only C-13-2 (verifier overlap with Phase 3 pyramid) remains in step 1; constitutional.
2. **Phase 4 T3 graph alignment** (C-4-2) -- either add T3 to standard.yaml or remove from spec; constitutional decision required.
3. **Phase 5 missing artifact authoring** (C-5-1, C-5-3) -- author trinity_policy.yaml shape reference + policy_query_envelope.schema.yaml; human-authored Article XIII session.
4. **Phase 12 implementation alignment** (C-12-1, C-12-3) -- decide deferred-vs-implement for retro_envelope.md; if implement, separate code session.
5. **Phase 14 audit event + field mapping** (C-14-1, C-14-2, C-14-3) -- closure-only; can be a single editorial+operational batch amendment.
6. **Phase 3 cross-ref + policy_snapshot** (C-3-1, C-3-2, C-3-3) -- low-risk editorial + operational batch.
7. **Phase 4 T2 + T9 reword** (C-4-1, C-4-3) -- operational reword; can batch with Phase 4 T3 decision session.
8. **Phase 5 boundary check** (C-5-2) -- operational addition.
9. **All NOTABLE items** -- quarterly v1.1 sweep; batch by spec.
10. **All NITPICKS** -- editorial PR; batch into single chore commit.

## Section 8 -- Process Followup

This review surfaced one new plan_helper drift pattern (Pattern 4: path-prefix missing `.ai/`) which has been recorded in `[[feedback_plan_helper_drift_corrections]]`. No new validator drift patterns expected from this review, but reviewer agents are instructed to flag any future drift discovery in their punch list outputs.

## Section 9 -- References

- 6 reviewer-agent transcripts: see session `0001_2026-05-15_13_56_pm_feat-phase-16-e2e-integration-and-v1-1-amendm/SANDBOX/` if archived; otherwise the punch lists are reconstructable from this queue.
- Addendum v1.0.4 §XXIX 3-tier classification: `docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md`.
- PRD §9 Phase 16 acceptance: `trinity_organ_refactor_prd.md` lines 941-961.
- Source specs reviewed: docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md, TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md, TRINITY_POLICY_ENGINE_SPEC_V1.md, TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md, TRINITY_PRESENTATION_PROTOCOL_V1.md, TRINITY_ROOT_OF_TRUST_SPEC_V1.md (all landed 2026-05-15).

---

**Authors:** Trinity Operator (compiled from 6 parallel reviewer agents).
**Total items:** 17 CRITICAL, 21 NOTABLE, 15 NITPICK = 53 amendment candidates.
**Estimated v1.1 amendment work:** 8-10 amendment sessions if batched per spec; 3-4 sessions if grouped by theme (schema cross-coherence, implementation alignment, editorial sweep).
