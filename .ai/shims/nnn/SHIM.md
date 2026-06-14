---
short-code: nnn
purpose: "New plan — task breakdown with estimates and risks"
status: stub
spec: docs/specs/07_SHIM_SPEC.md §3.2
last-updated: 2026-04-30
---

# `nnn` — Canonical Shim

## Purpose

Translate the `vvv` understanding into a **concrete, numbered plan** with
estimates, sequencing, and explicit risks. `nnn` is the deliverable that
`gogogo` executes step-by-step.

`nnn` is **proposal-only** — the kernel does not execute anything. Human
(or in Phase 5 a verifier rule set) must approve before transitioning to
`SANDBOX → DO`.

## When to invoke

- Immediately after `vvv_pass`
- When a previously-approved plan needs revision (re-run replaces, doesn't
  append; old plan goes to `THINK/.archive/`)

## Inputs

| Field | Required | Source |
|-------|----------|--------|
| `THINK/01_PROMPT.md` | yes | from `vvv` |
| Knowledge Brain hits | optional | `memory-cli search` (Phase 2) |
| Loop budget | yes | `.ai/policies/loop-budget.yaml` |

## What the kernel does

1. Reads `THINK/01_PROMPT.md` (the answered `vvv`)
2. Optionally queries Knowledge Brain for similar past tasks
3. Produces a numbered task breakdown:
   - **Step N** — single-sentence imperative
   - **Estimate** — time or LOC budget
   - **Risk level** — low/medium/high with one-line mitigation
   - **Spec ref** — what authoritative doc this step traces to
4. Computes a session-wide budget vs `loop-budget.yaml` defaults; flags
   if the plan exceeds either dimension (iterations, duration, tool
   calls) — escalates to NEEDS_HUMAN if so
5. Writes `THINK/02_SCOPE.md` and `THINK/03_ACCEPTANCE.md`
6. Appends `nnn.proposed` audit event

## Behavior contract

**MUST**
- Number every task; no bullet-only plans
- Attach estimate + risk to each step
- Include at least one explicit acceptance criterion (measurable)
- Surface budget breach early — a 30-step plan against `max_iterations: 20`
  must be flagged before `gogogo`
- Reference Trinity boundary docs for any potentially-risky step
- Append `nnn.proposed` to audit chain

**MUST NOT**
- Run any of the steps
- Skip risk analysis ("low risk overall" without per-step assessment)
- Suggest steps that violate boundaries (`.ai/policies/**`, auto-deploy)
- Decide approval ("I think this is fine") — that's `decided_by: human`

## Budget override (NEEDS_HUMAN path)

When the plan's estimates exceed `.ai/policies/loop-budget.yaml`
defaults, `nnn` writes `budget_status: NEEDS_HUMAN` into SCOPE.md and
refuses the transition. The operator (never the worker) may add a
`budget_override` block to the plan envelope and re-run `nnn`:

```json
{
  "budget_override": {
    "max_duration_minutes": 90,
    "decided_by": "human",
    "reason": "discovery-heavy spike; scope bounded to X"
  }
}
```

Rules: `decided_by` MUST be `human` (Show-before-submit applies — draft
+ approval before the label), the reason must bound the scope, and the
override lands in the audit chain via `nnn.proposed`.

## Output shape

```
THINK/02_SCOPE.md          ← numbered steps + estimates + risk per step
THINK/03_ACCEPTANCE.md     ← measurable success criteria
.state/plan.json           ← machine-readable plan envelope (for verifier)
```

## Adapter rendering hints

- Render the plan as a numbered list with risk badges (🟢🟡🔴)
- Surface the budget check prominently — humans miss spreadsheet-style
  warnings
- Provide a clear "approve / revise / reject" affordance at the end
- After approval, the adapter should NOT auto-trigger `gogogo`; the human
  invokes it explicitly

## Anti-patterns

- ❌ One-step plan ("just do the thing") — defeats the purpose
- ❌ Plan that includes "and any other refactors found along the way" —
  scope creep, kernel rejects
- ❌ Estimates that are all "small" — no signal
- ❌ Adapter that auto-approves plans below a budget threshold — Decision
  D2 violation

## Canonical user-facing text

See `docs/ai_entry/SHORT_CODES.md §nnn`.
