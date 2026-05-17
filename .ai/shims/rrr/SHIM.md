---
short-code: rrr
purpose: "Retrospective — capture lessons, update memory, close session"
status: stub
spec: docs/specs/07_SHIM_SPEC.md §3.2
last-updated: 2026-04-30
---

# `rrr` — Canonical Shim

## Purpose

Close the session loop with a **structured retrospective**: what worked,
what didn't, what to remember next time. The retro is the **only** way
the Knowledge Brain grows from active sessions.

`rrr` runs **after** the work is verified and (if applicable) deployed.
It transitions the session from `RETRO → DONE`.

## When to invoke

- After `gogogo` produced verified artifacts (i.e., session reached
  `VERIFIED` or `DEPLOYED`)
- After a session was aborted (DEAD) — even failures get a retro,
  especially failures
- **Never** mid-execution — `gogogo` must finish or pause first

## Inputs

| Field | Required | Source |
|-------|----------|--------|
| active session | yes | session state machine |
| audit chain | yes | `.ai/audit/events.ndjson` (filtered by session id) |
| verifier log | optional | `CONTROL/VERIFY.md` |
| loop state | yes | `.state/loop_state.json` |

## What the kernel does

1. Pulls the session's audit slice (all events with this session id)
2. Computes session metrics: iterations used, duration, tool calls,
   verifier pass/retry/fail counts, NEEDS_HUMAN count
3. Prompts the agent with retrospective questions:
   - **What worked?** (specific, not "things went well")
   - **What broke / what surprised you?** (with the exact failure mode)
   - **What's the one thing future-you should remember?**
   - **Any new boundary, anti-pattern, or guideline to record?**
4. Writes `THINK/RETRO.md` (or appends to existing)
5. **Phase 2**: hands the retro to `memory-cli` for indexing
6. Appends `rrr.completed` audit event
7. Transitions session `RETRO → DONE`
8. Archives the session to `.ai/sessions/archive/<session-id>/`

## Behavior contract

**MUST**
- Run on every session, including failed/aborted ones
- Produce a written `THINK/RETRO.md` (no in-memory-only retros)
- Compute and surface the session metrics from audit events
- Append `rrr.completed` to audit chain before archiving
- Move the session folder to `.ai/sessions/archive/` only after audit
  append succeeds

**MUST NOT**
- Skip itself ("nothing notable happened")
- Re-run `gogogo` from inside `rrr` — that's a new session
- Modify `THINK/01_PROMPT.md` or `THINK/02_SCOPE.md` (those are signed
  baselines; retros are append-only)
- Decide that the session is "fine" without reading the audit chain

## Output shape

```
THINK/RETRO.md
├── ## Metrics (auto-filled)
├── ## What worked
├── ## What broke
├── ## Remember next time
└── ## New boundary / anti-pattern (if any)

.ai/sessions/archive/<session-id>/  ← session folder moved here
```

## Adapter rendering hints

- Show the metrics as a table at the top — gives the retro shape before
  the prose
- For aborted sessions, surface the abort reason prominently
- After completion, render a brief 1-line summary the human can paste
  into a status update
- For "new boundary or anti-pattern," prompt the human to confirm — those
  upgrade the canonical knowledge base in Phase 2

## Anti-patterns

- ❌ Auto-generated retro full of platitudes ("the team did a great job")
- ❌ Retro that omits the failed steps (those are the most valuable!)
- ❌ Adapter that auto-archives the session before audit append succeeds
- ❌ Skipping retros on small sessions — the brain needs the small wins too

## Canonical user-facing text

See `docs/ai_entry/SHORT_CODES.md §rrr`. Phase 2 will wire this to
`memory-cli` for automatic Knowledge Brain growth.
