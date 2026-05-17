# TRINITY_VERIFIER_CONTRACT_V1

**Status:** DRAFT v2 (S5 of recordproxy alignment patch — pending verifier review + ddd)
**Phase:** 8 — Verifier Harness Consolidation
**Organ:** #8 (Verifier)
**Constitutional rank:** 5 — Workflow Contract (per Article XXV)
**Anchor commit:** main @ 4a6fd80 (RecordProxy v1 foundation)
**Predecessor anchor:** 17e74fa (pre-RecordProxy; superseded 2026-05-13)
**Date:** 2026-05-13

## §0 — Rank-5 Authority Disclaimer (Article XXV)

This document is a **Workflow Contract**. It ranks fifth in the constitutional priority order and is void where it conflicts with the Constitution, Ritual Constitution, Canonical Policies, or Kernel State Rules. Amendments follow Article XXIX. Does not amend `.ai/policies/verifier-rules.yaml` — that file remains the authoritative rule corpus.

## §1 — Purpose

Consolidate the verifier surface — what a verifier verdict means, what evidence backs it, what tier it carries, and what artefact downstream organs (DDD, audit, retro) consume. The Pyramid of Judgment (4 layers) already lives in `.ai/policies/verifier-rules.yaml` §pyramid; this spec pins the **report shape** that every verifier verdict — at any layer — MUST produce.

Goals:

1. Fix a single `verifier_report.json` shape so that Phase 11 DDD can machine-distinguish layer-1 deterministic, layer-2 policy, layer-3 LLM, and layer-4 human verdicts.
2. Add a **tier tag** (HOT / WARM / COLD) to every verifier rule so downstream organs can route accordingly (HOT = ephemeral, WARM = audited reversible, COLD = production-grade with crypto attestation).
3. Stay **specification-only** — runtime aggregator code is deferred to a later gogogo.

Non-goals:

- New verifier *rules*. Existing rule sets in `.ai/policies/verifier-rules.yaml` are unchanged.
- LLM-judge implementation (layer 3 stays opt-in per session per existing pyramid config).

## §2 — Verdict Set (Closed)

```
PASS, RETRY, NEEDS_HUMAN, DEAD
```

This set is fixed by `.ai/policies/verifier-rules.yaml` §verdicts and not re-opened here. The Capture-layer outcomes from RecordProxy v1 (DESIGN.md §6 capture status, §10 ORPHANED_INVOCATION) are MAPPED into this verdict set per §2.1 below — they do not introduce new verdict values.

### §2.1 Verdict Mapping (RecordProxy v1 outcomes → verifier verdicts)

The RecordProxy v1 evidence layer surfaces capture/invocation outcomes that the verifier MUST translate into the closed verdict set, routed by session tier. This table is authoritative:

| RecordProxy outcome | Source | × HOT | × WARM | × COLD |
|---|---|---|---|---|
| `ORPHANED_INVOCATION` | DESIGN.md §10 (no capture_id on mutation) | `RETRY` (with `notes.degraded=true`; reconciliation attempted) | `NEEDS_HUMAN` | `DEAD` |
| `FAILED_PARTIAL` | DESIGN.md §6 (capture aborted mid-transaction) | `NEEDS_HUMAN` | `NEEDS_HUMAN` | `DEAD` |
| `capture_finalize_missing` | new rule (§4); no `capture.completed` for a started capture | `RETRY` | `NEEDS_HUMAN` | `DEAD` |
| `capture_missing_for_artifact` | new rule (§4); artifact present without `capture_id` reference | `RETRY` (with reconciliation) | `NEEDS_HUMAN` | `DEAD` |
| `CAPTURING` (stuck) | DESIGN.md §6 (transaction never finalised) | `RETRY` after wallclock timeout | `NEEDS_HUMAN` | `DEAD` |
| `RECONCILED` | DESIGN.md §6 (orphan back-filled successfully) | `PASS` with `notes.reconciled=true` | `PASS` with `notes.reconciled=true` | `NEEDS_HUMAN` (manual sign-off required) |
| `COMPLETED` | DESIGN.md §6 (normal path) | `PASS` | `PASS` | `PASS` (subject to other gates) |
| `ARCHIVED` | DESIGN.md §6 (post-archive; verify archive hash) | `PASS` if archive hash verifies | `PASS` if archive hash verifies | `PASS` if archive hash verifies |

Every verdict in this table carries `evidence_keys: [capture_status, capture_id]` and `capture_refs[]` per §5.

Per memory `feedback_role_collapse_in_main_conversation` and DESIGN.md §10 invariant "Orphaned invocation cannot be silently accepted" — the verifier MUST NOT silently downgrade an ORPHANED row to PASS on any tier; the table above is the minimum strictness.

## §3 — Verifier Layers and Tiers

| Layer | Source | Latency | Authority |
|---|---|---|---|
| 1 — deterministic | `.ai/policies/verifier-rules.yaml` rule sets | sub-ms | predicate match |
| 2 — policy | `gates.yaml`, `safety.yaml`, `rbac.yaml` | ms | rule evaluation |
| 3 — LLM judge | gated, audited (max 3/session) | seconds | LLM call (advisory) |
| 4 — human | escalation (NEEDS_HUMAN) | minutes–hours | operator decision |

A **tier** classifies the *operational risk* of the workflow the verifier is gating:

| Tier | Meaning | Authority requirement |
|---|---|---|
| HOT | Ephemeral, UI-side, no persisted side-effects | Layer-1 deterministic only |
| WARM | Audited, reversible, sandbox-bound mutations | Layer 1+2; Layer 3 opt-in |
| COLD | Production-grade, irreversible without rollback | Layer 1+2; Layer 4 required for promote/deploy; Phase 14 crypto attestation when shipped |

## §4 — Tier-Tag Plan for Existing Rule Sets + New Capture Rules

The five existing rule sets in `.ai/policies/verifier-rules.yaml` plus three new capture-layer rule sets MUST receive the following tier metadata (additive, in a sibling file or a Phase-5 consolidated `trinity_policy.yaml` — the rules file itself is not edited by this session):

| Rule set | Tier | Rationale |
|---|---|---|
| `step_complete` | WARM | Default catch-all; assumes session sandbox |
| `code_change` | WARM | Test + sandbox checks; reversible by git |
| `browser_check` | HOT | UI-interactive; no persisted artifact |
| `deploy_check` | COLD | Production-side gate; requires human at Phase 11 |
| `memory_promote` | WARM | Audited memory write; reversible by audit |
| `orphaned_invocation` (new) | COLD | Any kernel-mediated mutation without a `capture_id` is rejected at COLD-tier; downgraded per §2.1 for HOT/WARM. Predicate: `audit_event.capture_id IS NULL AND audit_event.event_type IN (write/exec/tool.invocation.*)`. |
| `capture_finalize_missing` (new) | WARM | A `capture.started` event without a matching `capture.completed` / `capture.failed_partial` / `capture.reconciled` after wallclock timeout. Predicate: stuck `captures.status = CAPTURING` past WARM threshold. |
| `capture_missing_for_artifact` (new) | COLD | Artifact present in `DO/dev/` or `DO/prod/` whose hash does not appear in any `captures.capture_items.blob_sha256` row. Predicate: diff vs capture manifest yields uncovered files. |
| `sandbox_profile_missing` (new) | COLD | Session has no `sandbox.profile.bound` event in its per-session audit chain at close. Predicate: `AuditWriter.read_chain(session_id)` does not contain `event_type = sandbox.profile.bound`. |

When Phase 5 lands the consolidated `trinity_policy.yaml`, every rule set MUST carry a `tier:` field with one of the three values. Until then, this table is the authoritative tier map. The four new rules (`orphaned_invocation`, `capture_finalize_missing`, `capture_missing_for_artifact`, `sandbox_profile_missing`) are reserved names for the rule-set ID; their predicate implementations are deferred to a Phase-8 gogogo.

## §5 — Verifier Report Shape

Every verifier verdict — regardless of layer — MUST emit a JSON report conforming to `.ai/schemas/verifier_report.schema.json`. Minimal required fields:

| Field | Type | Meaning |
|---|---|---|
| `verdict` | enum(PASS/RETRY/NEEDS_HUMAN/DEAD) | closed set from §2 |
| `layer` | enum(1/2/3/4) | which pyramid layer produced this |
| `tier` | enum(HOT/WARM/COLD) | risk classification of the gated workflow |
| `rule_set` | string | rule-set ID from `.ai/policies/verifier-rules.yaml` (or "policy"/"llm_judge"/"human"); includes new IDs from §4 |
| `evidence_keys` | string[] | predicate names evaluated; empty for non-deterministic layers |
| `capture_refs` | string[] | ULIDs of `captures.capture_id` rows that supplied the evidence this verdict rests on; empty when no capture transaction was in scope (e.g. session-level verdicts before any capture started) |
| `ts` | RFC3339 string | UTC timestamp |
| `session` | string | session ID |
| `step_id` | string | nullable; null for session-level verdicts |
| `notes` | string | free-text; required when verdict ∈ {RETRY, NEEDS_HUMAN, DEAD}; for `RECONCILED` source, `notes.reconciled=true` is required; for HOT-degraded ORPHANED, `notes.degraded=true` is required |
| `audit_event` | object | reference: `{event_id, schema_version, seq, hash}` of corresponding event in the **per-session AuditWriter chain** (TRINITY_AUDIT_EVENT_SPEC_V1 §2 — 13-field shape); NOT a hash from the legacy global `events.ndjson` |

The schema closes `additionalProperties` and pins to draft-07.

### §5.1 capture_refs semantics

`capture_refs[]` is the bridge from a verifier verdict back to the raw evidence that produced it. Every COLD-tier verdict MUST include at least one capture_ref unless the verdict explicitly fires on a `sandbox_profile_missing` / `capture_missing_for_artifact` rule (which by definition has no capture to reference; in that case `capture_refs: []` is allowed and the `notes` field MUST explain).

## §6 — Consumption by Downstream Organs

- **DDD (TRINITY_DDD_HUMAN_GATE_SPEC_V1):** the decision packet `decided_by` field must be derivable from the verifier report's `layer` (`1/2` → kernel; `3` → llm; `4` → human). DDD MUST refuse to promote a tier=COLD step on a layer-3 verdict alone. DDD MUST propagate `verifier_report.capture_refs[]` into the decision packet's `presentation.capture_refs[]` so the operator can trace the raw evidence.
- **Audit (TRINITY_AUDIT_EVENT_SPEC_V1):** every verifier report is hashed into the per-session audit chain as a `verify.completed` event via per-session AuditWriter (NOT direct ndjson write). The event row carries `payload_json = {report_path, report_hash, capture_refs}` and obeys the 13-field shape (§2 of Audit Event Spec). The legacy ndjson MAY receive a mirrored 5-field row for compatibility.
- **Retro (RRR, Article XII.5):** retro acceptance ingests the report's `evidence_keys`, `capture_refs`, and `notes` for the gogogo verdicts table.
- **Close (TRINITY_SESSION_CLOSE_SPEC_V1):** the final-manifest hash MUST cover every verifier report file produced during the session AND the `captures.*` block (CAPTURE/capture.sqlite + blobs + refs + capture_ids list). `verifier_report.capture_refs` MUST be a subset of the final manifest's `captures.capture_ids` (close blocks otherwise).
- **Sandbox (TRINITY_SANDBOX_CAPABILITY_SPEC_V1 §3.1):** `ORPHANED_INVOCATION` originates as a `sandbox.deny` event with `reason: ORPHANED_INVOCATION`; this verifier translates it per §2.1 mapping.
- **Tool (TRINITY_TOOL_CAPABILITY_MODEL_V1 §4.5):** `tool.invocation_denied` with `reason: ORPHANED_INVOCATION` translates per §2.1 mapping.

## §7 — Cross-references

- **TRINITY_SANDBOX_CAPABILITY_SPEC_V1 §3.1** — sandbox capability denials surface as `sandbox_violation` evidence keys for layer-1 rules; ORPHAN integration cross-feeds §2.1 here.
- **TRINITY_TOOL_CAPABILITY_MODEL_V1 §4.5** — tool ORPHAN denials cross-feed §2.1 here.
- **TRINITY_AUDIT_EVENT_SPEC_V1 §2, §3** — 13-field audit event shape; `verify.completed` registered in §3 registry; per-session chain is the write target.
- **TRINITY_SESSION_CLOSE_SPEC_V1 §2, §2.1** — close manifests verifier reports + capture_refs subset rule.
- **TRINITY_DDD_HUMAN_GATE_SPEC_V1 §3** — DDD presentation propagates `capture_refs[]`.
- **`.ai/policies/trinity_policy.yaml capture_policy`** — orphaned_invocation routing matches §2.1 table.
- **DESIGN.md §6, §10, §22** — capture status model + ORPHANED_INVOCATION definition + invariants.

## §8 — Open Questions

- Should layer-3 LLM judge verdicts carry the LLM's tier (Opus/Sonnet/Haiku) in the report? Proposed: yes, under `notes.llm_model`. Resolution at ddd.
- Hash algorithm for `audit_event.hash`: existing chain uses SHA-256; this spec inherits unless Phase 14 elects otherwise.

## §9 — Out of Scope

- Runtime aggregator at `.ai/cli/core/verifier.py` (already exists; this spec does not modify it).
- New rule sets — none added here.
- Article XXIX amendments — none.

---

**Authors:** Trinity Executor (operator direct-draft, executor_helper drift); pending Verifier + Human review per Articles III, XIII.
