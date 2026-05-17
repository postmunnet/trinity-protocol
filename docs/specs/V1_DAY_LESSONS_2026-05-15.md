---
title: "V1 Spec Corpus Day-Lessons (2026-05-15)"
version: "1.0"
status: "lessons-learned"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: false
purpose: "Cross-session retro for the day Phase 0-16 V1 specs + V1.1 queue closed; durable reference for future spec-corpus or large-batch sessions."
---

# V1 Spec Corpus Day-Lessons -- 2026-05-15

## Context

In a single day, 16 commits across 4 sessions landed PRD Phase 3-14 V1 specs (~8,838 lines) plus the Phase 16 E2E integration milestone (V1.1 Amendment Queue), then resolved all 48 V1.1 items via 4 follow-up sessions. This doc captures the patterns that worked, the patterns that broke, and the discipline that should carry forward.

Per-session retros are at `.ai/memory/retros/0137*` through `.ai/memory/retros/0145*` (mechanical) and `.ai/sessions/archive/0001_2026-05-15_*/THINK/RETRO.md` (semantic). This doc is the **cross-session synthesis**; per-session retros are the per-event record.

## What worked

### Parallel-agent batching for cross-spec work
Spawning 3-8 general-purpose agents in a single Trinity session to author or amend independent spec files in parallel was the highest-leverage technique of the day. Three patterns in particular:
- **3 parallel for spec authoring**: Phase 3+4+5 bundle (3 specs ~3,081 lines) and Phase 12+13+14 bundle (3 specs ~2,550 lines) each wrote substantive specs in one shot. Each agent owned one file; allowed_paths whitelist made conflict impossible by construction.
- **8 parallel for batch cleanup**: V1.1 batch cleanup landed 47 items across 7 spec files + 3 ai_entry/CLAUDE docs in a single session. Each agent owned one file; main Claude consolidated by editing only the queue afterward.
- **Background-agent drafts (Article XIII path)**: For files the operator must author (`.ai/policies/`, `.ai/schemas/`), background agents drafted to `/tmp/` while main Claude continued with other sessions. Operator approved drafts wholesale; main Claude copied to canonical paths in a follow-up session.

The pattern works because: (a) Trinity session-state is single-active but sub-agent execution is naturally parallel; (b) per-file allowed_paths whitelisting makes parallel writes safe; (c) main Claude's role becomes coordinator/consolidator, not author -- which matches `[[feedback_role_collapse_in_main_conversation]]`.

### Spec-authoring template discipline
Every V1 spec used the same 10-section structure (Anchor + 8 normative sections + Cross-References + Versioning) with frontmatter pinning Article anchors. This made parallel agents produce coherent output without coordination -- they all knew where each kind of content goes.

### Background-agent drafts for forbidden writes
For paths I cannot touch directly (`.ai/policies/`, `.ai/schemas/`), spawning a background agent that drafts to `/tmp/` proposals avoided blocking the main flow. The operator reviews `/tmp/` drafts as a batch, then I copy approved drafts to canonical paths in a session that explicitly carves out the forbidden path via plan_envelope allowed_paths + operator-recorded authorization.

### Cross-amendment over field-dropping
When Phase 13 spec added 4 fields not accepted by Phase 11's strict schema, the right resolution was to expand Phase 11 (additive, backward-compatible v1.0.1 -> v1.0.2) rather than drop fields from Phase 13. Preserving operator-facing value (dissent_preserved, raw_artifact_links) was worth a Phase 11 schema bump.

## What broke

### plan_helper drift -- 3 new patterns surfaced
plan_helper drafted 3 new species of drift not caught by validator: path-prefix missing `.ai/`, column-format assumption for grep, obsolete `.ai/sessions/active/` path. Each manifested as rrr-FAIL requiring in-session patch of `THINK/03_ACCEPTANCE.yaml` + `.state/plan.json` followed by re-run. See `[[feedback_plan_helper_drift_corrections]]` Patterns 4-6.

**Discipline going forward:** spot-check plan_helper acceptance commands BEFORE submitting to nnn -- specifically grep for `:!sessions/`, `^| CRITICAL `, `sessions/active/`, and any reference to a kernel-state field (e.g. `transitions`) that may not exist in current schema.

### Review-agent false-positive (C-4-2)
The Phase 4 reviewer agent confidently flagged "T3 missing from standard.yaml" as a HIGH-severity constitutional gap. T3 was present (lines 39-42). A constitutional amendment session would have been wasted if not caught by the proposal-drafting agent's verify-against-disk discipline. See `[[feedback_review_agent_verify_against_disk]]`.

**Discipline going forward:** for HIGH-severity reviewer findings, require disk-verification with line numbers before queueing.

### Multi-session bash cwd drift
After `cd .ai && python3 -m pytest`, the bash cwd persisted, breaking the next `bash .ai/cli/ai ...` call from project-root. Caught and fixed inline each time, but cost rituals 30-60 sec per occurrence. See `[[feedback_bash_cwd_persists_kernel_vs_agent]]`.

### Acceptance commands testing kernel state without verifying schema
A6/A7/A8 acceptance commands several times encoded assumptions about session_state.json shape (`transitions` field, `active/` subdir) that were stale. Cost was always one rrr-FAIL + manual patch + re-rrr.

## Discoveries that surfaced during work

### Ritual ordering inversion (C-RITUAL-1)
Found by Phase 4 amendment-proposal agent during V1.1 review: the kernel state graph fires `nnn_pass` (THINK -> SANDBOX) BEFORE `vvv_pass` (SANDBOX -> DO), but SHORT_CODES.md and CLAUDE.md document `sss -> vvv -> nnn -> gogogo` (vvv before nnn). Resolution: amend docs to graph-true sequence (lower risk than reordering graph). Phase 4 spec §3.4 COLD example was chronologically impossible under actual graph -- now corrected.

### Background-agent draft + operator-review path is real
Memory previously didn't have a clear pattern for "I cannot write to `.ai/policies/` but operator can authorize my draft for direct copy." Today established: agent drafts to `/tmp/`, operator approves verbally in conversation, main Claude copies in a session that explicitly cites the authorization in commit message + plan_envelope. Article XXIX 6-step satisfied: proposal (the draft), rationale (V1.1 queue item), impact (named in commit), approval (operator turn), version bump (file is v1.0), audit (kernel auto-emits on file write).

## Recurring patterns worth keeping

- **Read PRD section before authoring spec** (every V1 spec agent's first step)
- **Cite Constitution articles VERBATIM** in §1 of every spec (acceptance gate guards this)
- **`additionalProperties: false` is load-bearing** -- Phase 11's strict schema caught Phase 13's drift early
- **Each session has its own forbidden_paths constraint** even if a file is touchable elsewhere -- drives clean diffs
- **Two-commit-per-session pattern** (`feat(...)` for work, `chore(session)` for audit + archive) makes git log readable
- **`ai close run` requires both verify dev AND verify prod** even if dev was implicit at ddd time

## Pivot

PRD Phase 0-16 V1 spec authoring is **complete**. Future work in this repo is **implementation**, not spec authoring -- the specs are now the contract. See `[[project_v1_corpus_complete.md]]` for the operator-only and engineering backlog that remains.
