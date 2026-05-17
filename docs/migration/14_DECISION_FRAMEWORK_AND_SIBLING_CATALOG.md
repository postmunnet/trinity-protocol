---
title: "Retro — Session J: sibling-vs-kernel decision framework + 12-tool sibling catalog"
status: locked
last-updated: 2026-05-01
audience: "Trinity team + future spec authors / sibling builders"
session-window: "2026-05-01 (single conversation, design-only refinement)"
session-id: "informal_2026-05-01_feat-sibling-classification-and-catalog"
acceptance-evidence: PASS (artifacts only — no code/test changes)
rrr-contract: PASS
audit-events-added: 0 (this turn made no kernel mutations)
---

# Session J — Decision framework + sibling catalog

> **First retro that records *decisions and policy* rather than
> *code shipped*.** No kernel mutation. No new sibling. The artifact
> is a hardened decision framework — "should X be in kernel or a
> sibling?" — plus a fully-classified catalog of 12 candidate
> sibling tools, recorded against the framework so future sessions
> don't re-debate from scratch.
>
> Companion to Sessions H (Phase 2.2→5) and I (Phase 0.5→10 + UX).
> This is the governance layer those code sprints implicitly
> depended on; making it explicit closes the "why kernel-clean?"
> question once.

## Scope

Single conversation, design + governance only:

| Output | What landed |
|--------|-------------|
| **Sibling-vs-kernel decision rules** | 2-rule framework: (1) capability — net/LLM/external API → sibling; deterministic + files+rules → kernel. (2) cost — kernel-internal hot-path bypasses subprocess boundary even when capability is sibling-shaped. Both rules must agree before extracting. |
| **"Stays in kernel" table** | 3 candidates (verify-cli, diff-cli basic, timeline-cli ASCII) explicitly removed from sibling consideration with documented reasoning so they don't get re-debated each retro. |
| **Borderline tier** | 3 candidates (diff advanced, timeline rendering, archive cloud) where decision = "depends on scope; narrow scope first." |
| **Clear-sibling tiers A / B / C** | 9 candidates classified by urgency. Tier A = 5 (debate / plan / judge / test / notify) closes real gaps now. Tier B = 1 (lint). Tier C = 3 (summarize / cron / browser). |
| **Decision gate (6 steps)** | Pick → run through both rules → scope-narrow if borderline → spec-first → buy-in → implement → contract-test platinum in CI |
| **`TODO.md` Tier 6 rewritten** | Old single-flat list replaced with structured framework. Future sessions read once and apply. |
| **R22 new followup** | Spec §16 of `02_VERIFIER_SPEC.md` calls verify-cli a "sibling" — premature abstraction. R22 tracks the clarification: "verify-cli is a kernel module with a CLI surface, not a subprocess sibling." |
| **Q&A artifacts (informational)** | Claude Code teleport workflow (web → CLI via `claude --teleport`); compatibility with `--dangerously-skip-permissions`; how Trinity currently invokes agents (vendor-harness-driven, not kernel-spawned). |

No code changes. No test changes. trinity_v2 pytest still 226;
memory-cli still 115; sibling totals unchanged.

## Metrics

| Dimension | Value |
|-----------|-------|
| Code LOC delta | 0 |
| Tests delta | 0 |
| Spec changes | 0 (R22 will land later) |
| `TODO.md` Tier 6 LOC delta | ~120 lines (rewrite from flat list to structured framework) |
| New R-followups | 1 (R22) |
| Sibling candidates classified | 12 (3 stays-in-kernel + 3 borderline + 5 Tier A + 1 Tier B + 3 Tier C) |
| Decision rules formalized | 2 (capability + cost) |
| Decision gate steps | 6 |
| Existing decisions reaffirmed | D8, D9, D10, D11, D13 (esp. D13 — "kernel stays clean") |

## What worked

**The "type `ai`" UX shipped in Session I created the right
opening for this discussion.** Once the user noticed that the
kernel itself had no LLM dependency, the natural follow-up was
"why?" — which surfaced the implicit invariant. Making the
invariant explicit (the 2 rules) means future tool proposals get
classified in <1 minute instead of debated for a turn.

**The 12-candidate brainstorm grounded the rules.** Theory alone
("kernel should be clean") doesn't help operators decide. Putting
12 real candidates against the rules — and noticing 3 of them
(verify, basic-diff, ascii-timeline) actually *fail* the
extraction test — proved the framework discriminates.

**Borderline tier prevents over-promotion.** Three candidates
(advanced diff, rendering timeline, cloud archive) read as
"sibling" at first glance but only when the scope is wide. Naming
the borderline tier explicitly forces "narrow scope first" before
spec authoring — closes a class of premature-abstraction bugs.

**R22 (verify-cli spec §16) is the cleanest case for "spec-bug,
implementation-correct."** The implementation already does the
right thing (kernel module + CLI subcommand). The spec was written
before the cost rule was articulated. Recording R22 + the cost
rule together means the next spec author has both the rule and
the precedent.

## What surprised

**The user's instinct hit the answer before the framework was
formalized.** The original prompt was "ทำไมเราต้องมี tier 1
ทำไมไม่ใช้ใน trinity core ไปเลย" — a pointed question that
already assumed kernel/sibling separation mattered. The
discussion didn't have to *justify* keeping things out; it had to
*name* the rule the user was already applying intuitively.
**Lesson:** when a user asks "why split?", they often have the
answer; the work is naming what they already know.

**Three of the original "sibling candidates" failed the test.**
verify-cli was the obvious one (per-step hot path). But basic-diff
and ascii-timeline also failed — and both were silently being
classified as Tier 2 siblings before today. Without the cost rule
they would have shipped as siblings + subprocess overhead would
have piled on for zero benefit.

**Recording without building scales the design budget.** Twelve
candidates would take weeks to actually implement and test. Five
minutes to classify them against rules. The kernel doesn't need
all 12 to exist; it needs the *option space* of 12 to be
acknowledged so future work routes correctly.

## What broke

Nothing this session — design-only.

## Decisions enforced + new

- **D13** (plugin tool architecture) — reaffirmed against the
  question "why not in kernel?". The 2-rule framework is the
  operational restatement of D13.
- **(new — implicit) D14: "kernel-internal hot-path bypasses
  subprocess boundary"** — the cost rule. Not numbered yet in any
  formal decisions document; should be when the spec gets its
  cleanup pass. R23 candidate.
- **Audit-friendliness invariant** — discussion clarified that
  `decided_by ∈ {kernel, verifier, policy, human}` is meaningful
  *because* the kernel is LLM-free. Putting LLM-using code into
  kernel would silently degrade audit trust without changing the
  schema. This is the deepest reason for D13.

## Open follow-ups

| ID | Description | Priority |
|----|-------------|----------|
| R22 *(this session)* | Spec `02_VERIFIER_SPEC.md` §16 clarification: verify-cli is a kernel module with a CLI surface, not a subprocess sibling | low |
| R23 *(this session)* | Promote the cost rule ("kernel-internal hot-path bypasses subprocess") to a formal numbered decision (D14) in `01_CONTEXT_AND_DECISIONS.md` | low |
| R5/R7/R8/R13–R21 | Carried from Sessions H + I (see `TODO.md` Tier 1) | mixed |

## What's next

No new phase. The decision framework is now persistent;
future sessions either pick a Tier 1 R-followup or pick exactly
one Tier-A sibling (debate-cli most likely candidate given the
user's interest) and run it through the 6-step decision gate.

Recommended next-session entry points:

1. **R20** — bulk-index 240 legacy retros (15 min, big ROI for hint quality)
2. **R8 + R15** — tool registry hardening (paired, ~1 hr total)
3. **debate-cli spec** — author `08_DEBATE_CLI_SPEC.md` *before* any implementation, run through decision gate

## Cross-references

- Predecessor retros:
  - `12_PHASE_2_2_TO_5_FOUR_PHASE_SPRINT.md` (Session H)
  - `13_PHASE_0_5_TO_10_AND_UX_SECOND_SPRINT.md` (Session I)
- Pending-work checklist: `TRINITY_LEGACY/TODO.md` (Tier 6 is the durable home of this session's output)
- Tool Contract: `docs/specs/01_TOOL_CONTRACT.md` §16 (Tool Registry)
- Verifier spec to be clarified by R22: `docs/specs/02_VERIFIER_SPEC.md` §16
- Decisions log to be extended by R23: `docs/migration/01_CONTEXT_AND_DECISIONS.md`

## Notes

- This is the **first retro that recorded a decision framework
  rather than code**. Worth its own slot in the migration series
  because future tool proposals will reference it (link to Tier 6
  rules) instead of re-deriving the reasoning.
- Three retros now ship per `~/.claude/projects/.../memory/MEMORY.md`
  → `project_pending_work_pointer.md` flow: Session H, I, J. Future
  sessions land at TRINITY_LEGACY, read TODO.md (which links Tier 6
  to this retro), and apply the rules without re-asking.
- "rrr" remains informal (no `ai session` opened — the third
  consecutive retro to apply R14 + R16 caveat). When R14 ships, all
  three sessions can be backfilled in one batch.
