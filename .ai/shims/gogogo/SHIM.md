---
short-code: gogogo
purpose: "Execute the approved plan, incrementally, with verifier checkpoints"
status: stub
spec: docs/specs/07_SHIM_SPEC.md §3.2
last-updated: 2026-04-30
---

# `gogogo` — Canonical Shim

## Purpose

Run the **approved** `nnn` plan step-by-step. Each step is implemented in
`SANDBOX/<seat>/` first, verified against acceptance criteria, then
promoted to `DO/dev/`. The verifier runs after each step (Pyramid layer 1);
if any step fails, the loop pauses for a verdict (PASS / RETRY / NEEDS_HUMAN
/ DEAD).

`gogogo` is the **only** short code that mutates files in `DO/`. Everything
else proposes.

## When to invoke

- After `nnn_pass` (plan was approved)
- Resuming a paused loop (`gogogo --resume`)
- **Never** without an approved plan — kernel rejects

## Inputs

| Field | Required | Source |
|-------|----------|--------|
| approved plan | yes | `THINK/02_SCOPE.md` + `.state/plan.json` |
| loop budget | yes | `.ai/policies/loop-budget.yaml` |
| verifier rules | yes | `.ai/policies/verifier-rules.yaml` (Pyramid) |
| active session | yes | session state machine |

## What the kernel does

For each numbered step in the plan:

1. Open work area in `SANDBOX/<seat>/` (seat picked by who's executing —
   Claude → `03_claude/`, Codex → `04_codex/`, etc.)
2. Implement the step (this is where the agent writes code)
3. Run verifier (Pyramid layer 1 — deterministic rules)
   - PASS → promote artifact to `DO/dev/`
   - RETRY → re-prompt the agent with the verifier's reason, retry once
   - NEEDS_HUMAN → pause, surface the artifact + reason
   - DEAD → mark step failed, escalate, stop the loop
4. Append `gogogo.step.{started,completed|failed}` audit events
5. Check loop budget; escalate to NEEDS_HUMAN if any cap exceeded
6. Repeat for next step

After the final step:
- All `DO/dev/` artifacts are present
- `CONTROL/VERIFY.md` has the running verifier log
- State transitions `DO → VERIFIED`

## Behavior contract

**MUST**
- Operate one step at a time; checkpoint between steps
- Run the verifier after every step
- Honor the loop budget (`max_iterations`, `max_duration_minutes`,
  `max_tool_calls`) — escalate on breach
- Leave `THINK/` and `CONTROL/META.json` immutable during execution
- Append a `gogogo.step.*` event for every step transition

**MUST NOT**
- Skip the verifier ("the change is small")
- Promote `DO/dev/ → DO/prod/` (that's `ddd`, with `decided_by: human`)
- Mutate `.ai/policies/`, `.ai/audit/`, or `.ai/schemas/` (D1 boundary)
- Run more steps than the approved plan (no "bonus refactors")

## Output shape

```
SANDBOX/<seat>/<step-N-artifacts>
DO/dev/<promoted-artifacts>
CONTROL/VERIFY.md            ← per-step verifier log (append-only)
.state/loop_state.json       ← progress, last-checkpoint, retry count
```

## Adapter rendering hints

- Stream step-by-step progress; don't dump the whole loop at once
- Surface the verifier verdict prominently after each step (badge +
  reason)
- On NEEDS_HUMAN, freeze the surface and prompt clearly with the
  artifact path + verifier reason
- Provide an obvious "abort" affordance (kernel writes `loop.aborted`
  event, transitions to a clean DEAD state)

## Anti-patterns

- ❌ Adapter that hides verifier failures behind retries until something
  passes — defeats Pyramid layer 1
- ❌ Skipping the per-step audit append — chain breaks
- ❌ Auto-promoting verified artifacts to `DO/prod/` — that's a human gate
- ❌ Continuing past `max_iterations` ("just one more step") — Decision
  D11 violation

## Canonical user-facing text

See `docs/ai_entry/SHORT_CODES.md §gogogo` and
`docs/ai_entry/WORKFLOW.md` for state-machine details.
