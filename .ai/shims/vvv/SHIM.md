---
short-code: vvv
purpose: "Verify understanding — clarify before code"
status: stub
spec: docs/specs/07_SHIM_SPEC.md §3.2
last-updated: 2026-04-30
---

# `vvv` — Canonical Shim

## Purpose

Force a **pause-and-clarify** ritual before any code is written. The agent
proposes 5 understanding questions; the human answers (or skips). Output is
a written-down baseline that `nnn` will plan against and `gogogo` will
execute against.

`vvv` is the gate that stops "agent ran ahead and built the wrong thing."

## When to invoke

- After `sss:` before any plan or code
- Whenever scope, acceptance, or constraints feel ambiguous mid-session
- **Always** before destructive or wide-reaching operations
- Skipping `vvv` is a Trinity **D2** boundary violation — the kernel
  refuses to transition `THINK → SANDBOX` without `vvv_pass`

## Inputs

| Field | Required | Source |
|-------|----------|--------|
| task description | yes | session metadata (set by `sss:`) |
| session id | yes | active session |

## What the kernel does

1. Loads the active session's `THINK/00_CONTEXT.md` (or empty)
2. Generates **5 understanding questions** covering:
   - Goal — what success looks like
   - Scope — what's in/out
   - Constraints — what can't be touched (policies, boundaries)
   - Acceptance — measurable signal of "done"
   - Risk — most likely failure mode
3. Produces a list of files the agent expects to change
4. Waits for human answers (or explicit "skip" with reasons)
5. On answer, writes `THINK/01_PROMPT.md` and a `vvv_pass` marker
6. Records `vvv.proposed` and `vvv.passed` events to audit chain

## Behavior contract

**MUST**
- Produce exactly 5 questions (not 3, not 7) — 5 is the contract
- Block the `THINK → SANDBOX` transition until `vvv_pass` exists
- Quote any constraint from `.ai/policies/` verbatim if relevant
- List concrete files (paths) the agent expects to touch
- Append `vvv.proposed` and (on pass) `vvv.passed` to audit

**MUST NOT**
- Skip itself ("task is simple") — Decision D2 violation
- Generate code in the same response
- Mutate any file outside `THINK/`
- Decide `vvv_pass` autonomously (only human or verifier rule sets it)

## Output shape

```
THINK/01_PROMPT.md
├── ## Questions (5)
├── ## Files expected to change
├── ## Acceptance criteria
└── ## Constraints from policies
```

## Adapter rendering hints

Adapters should:
- Display all 5 questions at once (don't drip one-by-one)
- Show "files expected" list for human spot-check
- Make answers easy: numbered prompts, default-on options where sensible
- After human responds, render the `vvv_pass` marker visibly

## Anti-patterns

- ❌ Agent writes code in the same response as the questions (skip)
- ❌ Adapter wraps `vvv` with an LLM judge that auto-approves easy tasks
- ❌ Adapter omits a question because "it's obvious" — kernel verifier
  checks for 5

## Canonical user-facing text

See `docs/ai_entry/SHORT_CODES.md §vvv` for ritual wording. The
**5-question contract** is reinforced in `BOUNDARIES.md`.
