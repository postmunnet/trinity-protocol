# Ritual Template Pack Cross-Check Review

**Authority:** Trinity Ritual Constitution v1.1 (ratified 2026-05-13) + Ritual Contract v1.0 + RRR Delegation Contract v1.0
**Session:** feat-ritual-template-packs-bootstrap (gogogo step S4)
**Reviewed:** 2026-05-13 (UTC)
**Reviewer:** general-purpose agent (Claude Code subagent, S4 cross-check role)
**Correction:** 2026-05-14 — see "Review Correction" section below; the gogogo C4 finding is **stale** (file at HEAD already consumes the placeholders the review claims are missing).

## Review Correction (2026-05-14)

Re-read of `.ai/rituals/gogogo/write.template.md` at HEAD (`f92b1ee`) shows that `session.id` (line 9) and `session.dir` (line 11) are **already consumed**:

```
- Session ID: {{plain_text:session.id}}
- Session Slug: {{plain_text:session.slug}}
- Session Dir: {{path:session.dir}}
```

All 10 required placeholders declared in `context.schema.json` are consumed by `write.template.md`. Article XVI is satisfied. The "FAIL (BLOCKING)" finding below (line ~62) describes a draft state that was fixed before merge; the review note was not refreshed. No code change is required; this correction updates the summary cells only. The detailed gogogo section is preserved verbatim below as historical record, with an inline `[STALE — see Review Correction]` marker.

Resulting verdict deltas:
- BLOCKING gaps: 1 → **0**
- gogogo row verdict: `NEEDS_FIX` → **`PASS_WITH_NOTES`** (C5 state-transition WARN still stands; non-blocking)
- Overall verdict: `NEEDS_FIX` → **`PASS_WITH_NOTES`** (six C5 WARNs across gogogo/ddd/rrr/close remain — Phase 4 state graph work, non-blocking)

## Summary

- Packs reviewed: 7 (sss, vvv, nnn, gogogo, ddd, rrr, close)
- Total cells: 7 × 6 = 42 base checks + per-ritual specifics (sss retry, nnn XXII, gogogo III, ddd XIII+XV, rrr T1–T4, close X)
- BLOCKING gaps: **0** (was 1; corrected 2026-05-14)
- NON-BLOCKING gaps / observations: **6**
- Overall verdict: **PASS_WITH_NOTES** (Article XVI satisfied across all packs; six Article XVII state-transition WARNs remain, all non-blocking and tracked under Phase 4 state graph formalization)

## Cross-check matrix

Legend: `OK` = passes; `WARN` = non-blocking observation; `FAIL` = blocking gap.

| Ritual | C1 schema | C2 Art V | C3 Art VI | C4 Art XVI | C5 Art XVII | C6 Art XVIII | Extra | Verdict |
|---|---|---|---|---|---|---|---|---|
| sss    | OK | OK | OK | OK | OK | OK | retry.max_retries=0 (idempotent) — OK | PASS |
| vvv    | OK | OK | OK | OK | OK (THINK→THINK, intra-state hold, schema permits) | OK | five Q headings present | PASS |
| nnn    | OK | OK | OK | OK | OK | OK | rollback predicate + artifact + forbidden_action all present (Art XXII) | PASS |
| gogogo | OK | OK | OK | OK (verified consumed 2026-05-14: session.id @ L9, session.dir @ L11 of write.template.md) | WARN (non-baseline transitions PLAN→EXECUTE, PLAN→VERIFY, SANDBOX→VERIFY, EXECUTE→SANDBOX present as cross-product) | OK | self-certify predicate present (Art III) | PASS_WITH_NOTES |
| ddd    | OK | OK | OK | OK | WARN (NEEDS_HUMAN→FAILED not in Article XVII baseline) | OK | `decided_by == human` + transport-not-decider both enforced (Art XIII+XV) | PASS_WITH_NOTES |
| rrr    | OK | OK | OK | OK | WARN (DEPLOY→DONE cross-product not in baseline; RETRO→DONE is canonical) | OK | T1/T2/T3/T4 all enforced; `memory-cli learn` + `lessons learned` forbidden; `memory_handling.mode == index` predicate present; `rrr.delegated_call` declared | PASS |
| close  | OK | OK | OK | OK | WARN (FAILED→SEALED, ABORTED→SEALED not in baseline; Article XVII baseline only lists DONE→SEALED) | OK (Kernel-only allowed_roles; Session Finalizer is the contract synonym) | append-only audit predicate + `rewrite_audit_chain` forbidden (Art X) | PASS_WITH_NOTES |

## Methodology

- **Schema validation method:** `python3 + jsonschema 4.25.1` validated all 21 files (3 per pack × 7 packs) against `.ai/schemas/{ritual_contract, ritual_check_template, ritual_context}.schema.json`. Result: 21/21 OK.
- **Placeholder cross-check method:** regex extraction of `{{type:identifier}}` from each `write.template.md`, intersected with declared placeholders in `context.schema.json`. Verified (a) no untyped raw `{{...}}` remaining; (b) every consumed identifier is declared; (c) every required-true placeholder is consumed; (d) consumed type matches declared type.
- **State-transition legality:** computed Cartesian product `allowed_current_states × allowed_next_states` from each contract and compared against Article XVII baseline transition set. Identity transitions (e.g. `THINK→THINK`) excluded because the schema treats them as "intra-state hold" not full transitions.
- **Role matrix:** parsed `delegated_role` from contracts; matched against Article XVIII writers-per-ritual; confirmed Kernel ∈ allowed_roles and Transport ∈ forbidden_roles for every pack.
- **Audit-event coverage:** verified every contract has at least one event matching `\.invoked$`; verified rrr declares `rrr.delegated_call` (RRR T4).
- **Ritual-specific extras:** structural predicates and forbidden_phrases/actions searched for the article-specific tokens called out in the cross-check matrix.
- **Read Constitution articles in full:** I (Core Ritual Model), III, IV, V, VI, VII, VIII, IX, X, XII, XII.5, XIII, XIV, XIV.1, XV, XV.1, XV.2, XVI, XVII, XVIII; Ritual Contract v1.0 per-ritual rows; RRR Delegation Contract T1/T2/T3/T4 + Pin Suggestion Protocol.

## Detailed findings

### sss
- **PASS** — C1 valid; C2 all 14 Article V fields present and typed; C3 all 13 Article VI fields present; C4 10 typed placeholders, 9 required all consumed, 1 optional (`session.workflow_type`) also consumed; C5 `READY→THINK` matches Article XVII baseline; C6 `Session Initializer` matches Article XVIII row; Transport forbidden; Kernel allowed.
- **PASS (extra)** — `retry_policy.max_retries == 0` per the operator's idempotency expectation; consistent with sss being a deterministic mkdir-style bootstrap.
- Audit events `sss.invoked` + `session.created` declared; check template enforces audit chain append-only predicate.
- Forbidden phrases include `approved`, `verified`, `deployed`, `complete` (Article XIII boundary — sss artifact must not pretend final state).

### vvv
- **PASS** — C1–C6 all OK.
- C5 note: `from=[THINK] to=[THINK]` is an intra-state hold (operator answers 5 questions, kernel writes `.state/vvv_pass`, state stays `THINK` until operator invokes `nnn`). This matches Ritual Contract v1.0 row `vvv → pre-state THINK, post-state THINK→PLAN deferred to nnn`. The Article XVII baseline does not forbid identity transitions, and Article III makes clear that vvv is the clarification gate before planning.
- Five Q-headings (`Q1 Goal`, …, `Q5 Risk`) all required; minimum-length 8 per answer predicate present.
- Forbidden phrases include placeholder-bleed protections (`{{user_input}}`, `TODO: fill in`, `TBD`, `FIXME`, `<insert answer>`, `lorem ipsum`).
- `Human Operator` correctly in allowed_roles (operator authors the answers; AI may only synthesize the question text per Article III).

### nnn
- **PASS** — C1–C6 all OK.
- Article XXII (Constitution v1.0 — Recovery & Reversibility) enforced via three layers: structural predicate `plan_envelope.rollback.length >= 1` (required:true), required artifact `THINK/rollback.md`, and forbidden_action `skip_rollback_declaration`.
- Predicates also enforce `plan_envelope.tier in [HOT,WARM,COLD]`, `allowed_paths.length >= 1`, `acceptance.length >= 1`, `steps.length >= 1`, `verification_contract.predicates.length >= 1`. These collectively close the "planning-without-budget" failure mode.
- vvv→nnn precedence enforced via `required_evidence_refs.vvv_pass` (state sentinel at `.state/vvv_pass`).
- Audit events include `plan.budget_checked` — captures budget-override visibility per Decision Velocity Tiers (Addendum §B).

### gogogo
- **[STALE — see Review Correction at top, 2026-05-14]** ~~FAIL (BLOCKING) — C4 Article XVI violation.~~ Verified at HEAD: `session.id` and `session.dir` ARE consumed in `write.template.md` (lines 9 and 11). C4 = OK. The text below is preserved verbatim as historical record of the draft-state finding.
- **FAIL (BLOCKING) — C4 Article XVI violation.** Two required placeholders are declared in `context.schema.json` but never consumed in `write.template.md`:
  - `session.id` (declared required, source `kernel.session_manifest`) — write template only uses `session.slug`.
  - `session.dir` (declared required, source `kernel.session_manifest`) — write template never references the capsule directory path.
  - Article XVI requires every required placeholder to be consumed; the per-context-schema invariant "required:true means write template MUST consume" is breached. **Fix:** either (a) add `session.id` and `session.dir` references to the write template header (preferred — keeps the step log self-locating), or (b) flip both placeholders to `required:false` in `context.schema.json`.
- **C5 WARN — non-baseline transitions in cross-product.** The contract declares `allowed_current_states=[PLAN, SANDBOX, EXECUTE]` × `allowed_next_states=[SANDBOX, EXECUTE, VERIFY]`. The Cartesian product yields nine pairs, of which Article XVII baseline explicitly lists only four (`PLAN→SANDBOX`, `SANDBOX→EXECUTE`, `EXECUTE→VERIFY`, identity holds). The pairs `PLAN→EXECUTE`, `PLAN→VERIFY`, `SANDBOX→VERIFY`, `EXECUTE→SANDBOX` are not in the baseline. This is consistent with how gogogo's real execution loop compresses or backtracks across sub-steps (e.g. HOT-tier may jump `PLAN→VERIFY` directly), but Article XVII says "Any transition not listed is illegal unless explicitly allowed by signed state policy." Recommend a brief note in the pack's `ritual.contract.json.purpose` or a sibling `state_policy.md` that explicitly authorises the compressed pairs. Non-blocking because the schema permits the values; constitutionally adjacent.
- **C2/C3/C6 PASS.** Article III enforcement is strong: `step.owner_role != decided_by` predicate + `self_certify_step_pass` forbidden_action + `executor_did_not_self_certify` required_check. Evidence requirement (Article VIII) enforced via `verifier_report.evidence_ref is_present` predicate + required_evidence_ref on `verifier_report.evidence_ref`.
- Audit events include `gogogo.hmac_rejected` — preserves transport-failure visibility (Article XV).
- Forbidden phrases include `verdict: PASS_NO_EVIDENCE` (Article VIII) and `auto-certified`/`self-certified` (Article III).

### ddd
- **PASS_WITH_NOTES.**
- Article XIII enforcement: structural predicate `decision.decided_by == human` (required:true), forbidden_phrases include `decided_by: ai` and `decided_by: kernel`, forbidden_actions include `ai_self_decide` and `synthesize_decision_without_human`.
- Article XV enforcement: predicate `transport.role != decision.decider` (required:true), `Transport` in forbidden_roles, forbidden_actions include `transport_side_approval` and `bypass_hmac_verification`, audit event `ddd.hmac_rejected` declared.
- HMAC envelope required as evidence (`required_evidence_refs.operator_signed_envelope.required=true`).
- Three mutually-exclusive outcome artifacts (`approval.json | rejection.json | hold.json`) with predicate `exactly_one(...) is_present`.
- **C5 WARN.** `NEEDS_HUMAN→FAILED` (cross-product pair) is not in the Article XVII baseline (baseline has `NEEDS_HUMAN→PROMOTE` and `NEEDS_HUMAN→PLAN` only; not `→FAILED`). The pair is legitimate (operator rejects after holding), but, like gogogo, it extends the baseline. Worth a documented justification clause.
- Required `Dissent` heading preserves Article XIII dissent-visibility principle even when no dissent exists (forbidden_action `drop_dissent_from_packet`).

### rrr
- **PASS — all RRR Delegation Contract terms enforced.**
- **T1 (no semantic synthesis):** predicate `rrr.semantic_synthesis == false` (required:true); forbidden_phrases `lessons learned`, `key takeaway`, `canonical truth`, `verified as final truth`, `policy is changed`; forbidden_actions `compose_semantic_synthesis`, `compose_lessons_learned`, `decide_workflow_meaning`. The write template inserts an `AUTO_GENERATED_MARKER:end` separator and a comment forbidding kernel/retro-writer writes below.
- **T2 (memory-cli `index` not `learn`):** predicate `memory_handling.mode == index` + `memory_handling.verb != learn`; forbidden_phrases `memory-cli learn`, `memory learned`; forbidden_actions `memory_cli_learn`; required field `memory_index_result.json: index_called+verb+result` in `.state/rrr/`.
- **T3 (severity-by-tier — runtime concern):** Article expressed correctly as runtime behavior; `audit_events` includes `rrr.index_failed` (visibility surface) and `rrr.completed` (which carries `tier` + `memory_index_severity` per the delegation contract). Static template makes the failure visible without enforcing tier mapping at template level — matches the constitutional design.
- **T4 (`rrr.delegated_call` event):** declared in `audit_events`; required_evidence_ref `rrr.delegated_call_audit_event` (required:true); structural predicate `audit.rrr_delegated_call.count >= 1`.
- **Pin Suggestion Protocol:** auto-pin forbidden (`auto_pin_attempts == 0` predicate + `auto_pin` forbidden_action + `auto-pinned` forbidden_phrase); Pin Suggestion Protocol is correctly delegated to stdout (not enforced in template, matching the operator-facing courtesy-notice spec).
- **C5 WARN** — `DEPLOY→DONE` cross-product pair not in baseline (baseline path is `DEPLOY→RETRO→DONE`); legitimate as a HOT-tier compression but extends the baseline.
- All Article XVIII row obligations satisfied: Retro Writer + Kernel + Memory CLI in allowed_roles; Verifier/Planner/Executor/Presentation Synthesizer/Session Initializer/Clarification Agent + Transport in forbidden_roles.

### close
- **PASS_WITH_NOTES.**
- Article X enforcement: predicate `audit.in_place_modification_count == 0`; forbidden_actions `rewrite_audit_chain`, `modify_audit_chain`, `modify_retro_lessons`, `edit_retro_in_place`; forbidden_phrases include `audit_rewritten`, `retro_edited`, `session_deleted`.
- Kernel-only allowed_roles `["Kernel"]` — even `Human Operator` is in `forbidden_roles`, which is constitutionally correct: close is kernel-mechanical (Article XX, Passive Core; Article X, Audit Discipline). The contract names the role `Session Finalizer` which is a per-pack naming choice; Article XVIII does not enumerate close-writer because no agent writes close. Recommend (non-blocking) adding a one-line `purpose` clarification that `Session Finalizer` == Kernel's close pass.
- **C5 WARN.** `FAILED→SEALED` and `ABORTED→SEALED` are not in Article XVII baseline (baseline lists `DONE→SEALED` only; `FAILED→{PLAN, ABORTED, TERMINAL_FAILED}`; `ABORTED` has no listed out-edge). Pack rationale (allowing close to finalize FAILED/ABORTED sessions for archive purposes) is sensible but extends the baseline. Suggest documenting this in `docs/contracts/` or amending Article XVII's baseline transition table in a future Constitution addendum.
- COLD-tier external audit obligation preserved via conditional predicate `tier == COLD => external_audit.path is_present` (required:false because HOT/WARM omit it) + audit event `close.external_audit_emitted` declared.
- `final_manifest.artifact_hashes.length == count(DO/prod/files)` predicate enforces sha256 capture parity (Article X audit replay).

## Blocking gaps (must fix before ddd)

**None as of 2026-05-14.** The original entry below is preserved as historical record; the finding was stale (file at HEAD already consumes the placeholders). See "Review Correction" at the top of this document.

~~1. **gogogo/write.template.md — Article XVI required-placeholder consumption violation.**~~ **[RESOLVED — STALE FINDING, 2026-05-14]**
   - File: `<workspace-root>/trinity_v2/.ai/rituals/gogogo/write.template.md`
   - ~~Missing consumption: `{{plain_text:session.id}}` and `{{path:session.dir}}`~~ — both placeholders verified present at L9 and L11 of write.template.md (`f92b1ee`); review note was drafted against a pre-merge state.
   - Declared as required in `<workspace-root>/trinity_v2/.ai/rituals/gogogo/context.schema.json` (placeholders[0] and placeholders[2])
   - **Recommended fix:** prepend a Session Identity block to the write template, e.g.:
     ```
     ## 0. Session Identity
     - Session ID: {{plain_text:session.id}}
     - Session Directory: {{path:session.dir}}
     ```
     (matches the pattern used in `sss/write.template.md` §1 Session Identity). **Note (2026-05-14):** the actual template uses an equivalent `## 1. Session Identity` block — the fix-by-equivalent is already in place.
   - **Alternative fix:** flip both placeholders to `required:false` in `context.schema.json` (less preferred — session.dir is load-bearing for cross-session-writes detection and step path resolution; making it optional weakens the static check).

## Non-blocking observations

1. **gogogo state-transition envelope wider than Article XVII baseline.** Cross-product yields `PLAN→EXECUTE`, `PLAN→VERIFY`, `SANDBOX→VERIFY`, `EXECUTE→SANDBOX` which are not in the baseline. The contract author likely intends these as tier-compressed paths. Recommend an inline `purpose`-paragraph or `state_policy.md` sibling that authorises them per Article XVII's "signed state policy" exception.
2. **ddd `NEEDS_HUMAN→FAILED` not in baseline.** Legitimate path (operator rejects after holding), but should be either added to Article XVII as a future amendment, or annotated in the ddd contract.
3. **rrr `DEPLOY→DONE` cross-product pair.** Baseline routes `DEPLOY→RETRO→DONE`. The `DEPLOY→DONE` direct edge is a HOT-tier compression; suggest documenting.
4. **close `FAILED→SEALED` and `ABORTED→SEALED` not in baseline.** Pack rationale is sensible (close finalizes any terminal state) but extends Article XVII's baseline which only lists `DONE→SEALED`. Worth a Constitution addendum or in-pack rationale.
5. **close `delegated_role: "Session Finalizer"` is a name not in Article XVIII.** Article XVIII does not list any agent for close because Kernel writes it. `allowed_roles: ["Kernel"]` is correct, but a one-line `purpose` clarification that "Session Finalizer" == Kernel-mode would prevent future-reader confusion.
6. **`required_headings` format inconsistency between packs.** sss and rrr use unprefixed headings (`"Session Identity"`, `"Verdict"`); vvv/nnn/gogogo/ddd/close use markdown-prefixed (`"# Step"`, `"## Verdict"`). The check-template schema does not constrain format. Pick one convention and apply uniformly to make the kernel check implementation simpler (suggestion: prefer unprefixed; the kernel can match either `# Foo` or `## Foo` against `"Foo"`).

## Closing note

**Original (2026-05-13):** Six of seven packs are constitutionally complete and ready for kernel implementation. **gogogo** has one Article XVI blocking gap (required placeholders not consumed) that the author agent should fix before `ddd`. The non-blocking state-transition observations (items 1–4 above) are not gates — they reflect legitimate compressions across the canonical state machine that the Constitution's Article XVII "signed state policy" exception is designed to permit, but they should be made explicit so future reviewers don't read them as illegal transitions.

~~After the gogogo write-template fix, verdict graduates to **PASS** and the pack set is ready for `ddd` approval.~~

**Correction (2026-05-14):** Re-verification of `gogogo/write.template.md` at HEAD confirms `session.id` and `session.dir` are consumed (L9, L11). The Article XVI blocker was stale; no code change required. All seven packs are constitutionally complete (Article XVI satisfied). The six non-blocking C5 state-transition WARNs (gogogo cross-product, ddd `NEEDS_HUMAN→FAILED`, rrr `DEPLOY→DONE`, close `FAILED→SEALED` / `ABORTED→SEALED`) remain and will be resolved as part of Phase 4 state graph formalization. Pack set is ready for `ddd` and beyond; gate status: **PASS_WITH_NOTES**.
