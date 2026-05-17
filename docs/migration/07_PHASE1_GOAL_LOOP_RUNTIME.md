---
title: "Retro — Session B: Phase 1 Goal Loop Runtime"
status: locked
last-updated: 2026-04-30
audience: "Trinity team + future Phase 2+ sessions"
session-window: "2026-04-30 (single session, ~25 min wall)"
session-id: "0001_2026-04-30_20_10_pm_feat-phase1-smoke"
audit-events-added: 29        # 1 -> 30 chain depth
short-codes-implemented: 3    # vvv, nnn, gogogo
---

# Session B — Phase 1 Goal Loop Runtime

> Single session, 9-step plan, ~870 LOC across 7 files (5 NEW + 2 MODIFY).
> Audit chain grew 1 → 30 events with `chain.validate()` passing after
> every fire(). Final graph_state DONE.

## Scope

Implement the runtime for the canonical Trinity short-code rituals
driven by `graphs/standard.yaml`:

```
sss → vvv → nnn → gogogo → ddd → rrr
```

End-to-end acceptance: a session must walk this sequence with the audit
chain growing exactly one event per transition and every transition's
`decided_by` matching the graph's declared authority (D10).

## Metrics

| Dimension | Value |
|-----------|-------|
| Files NEW | 5 (`core/loop.py`, `core/budget.py`, `commands/{vvv,nnn,gogogo}.py`, `tests/test_goal_loop.py`) |
| Files MODIFY | 2 (`cli/main.py`, `core/state.py`) |
| LOC actual | ~870 |
| Tests added | 10 (engine 5, budget 3, E2E 2) |
| Tests passing | 66 / 67 (the 1 fail is pre-existing brittleness; see below) |
| Audit events added | 29 (depth 1 → 30) |
| Spec changes | 0 |
| Locked decisions enforced | D1, D2, D9, D10, D11, D12 |
| Pyramid layers wired | 1 (stub-PASS for phase1-smoke; Phase 4 plugs real rules) |

## What worked

**`vvv` before any code caught a real contract conflict.** Q1 of the
5-question ritual surfaced a tension between `.ai/shims/vvv/SHIM.md`
("vvv blocks THINK→SANDBOX without `vvv_pass`") and
`.ai/graphs/standard.yaml` (THINK→SANDBOX is triggered by `nnn_pass`,
not `vvv_pass`). Default (a) — "vvv writes the marker; nnn fires
`nnn_pass` to enter SANDBOX; SANDBOX entry verifier auto-fires
`vvv_pass` to enter DO" — preserved both contracts with zero spec
changes. Without `vvv` first, this would have been an implementation
ambiguity surfacing in test failures days later.

**Schema-agnostic graph engine.** `core/loop.py` indexes transitions
generically — looks up `(from_state, trigger)`, validates `decided_by`
membership in `{verifier, policy, human, kernel}`, falls back to `ANY`
state for system-wide triggers (`policy_violation`, etc). Proven by
`test_loop_uses_fixture_graph` running the same engine against a
3-state `tiny.yaml`. No hardcoded references to `standard.yaml`'s
state names.

**Per-step audit chain bootstrapped cleanly by hand.** Steps 1–8 of
the gogogo plan were executed by-hand (since the gogogo runtime was
itself being built); each step appended `gogogo.step.started` then
`gogogo.step.completed` via inline `python3 -c "from core.audit import
AuditChain; chain = AuditChain(...); chain.append(...)"` calls. The
audit shape exactly matched what the runtime would produce, so step 9
(running the real runtime) was a smooth handoff with no chain break.

**Budget gate fires on its own work.** Phase 1 plan estimated 150-min
duration vs `max_duration_minutes: 30` default → 5× breach. `nnn`
correctly returned `ok=False` until the user explicitly passed
option (A) human override (`max_duration_minutes: 180`, decided_by:
human, reason: "epic-scale"). The override is logged as
`overrides_applied` in `Budget.check()` output and persisted to
`.state/plan.json:budget_override`. D11 is enforced even on the
session that was implementing D11 — the kernel didn't bypass its own
gate.

**E2E test asserts `decided_by` per transition, not just state.** Beyond
asserting the final state, `test_e2e_full_loop` walks each transition
and confirms `event["details"]["decided_by"]` matches the graph's
declared authority for that trigger. Catches future drift if the graph
file changes a `decided_by` field but the runtime doesn't.

## What surprised

**`test_basic::test_state_initialized` is environmentally brittle.**
The assertion `data["system"]["status"] == "idle"` is true only when
no session is active. Session A's run started with no session
(idle ✅). Phase 1's run started with `phase1-smoke` active (busy ❌).
Not a regression — pre-existing fragility, surfaced because Phase 1's
session ran the test suite mid-flight. **Lesson:** tests should accept
both states (`status in {"idle", "busy"}`) or use a fresh project
fixture.

**Plan estimated 655 LOC; actual ~870 LOC** (~33% over). Mostly in
`commands/nnn.py` (two render paths — happy + needs_human + envelope
merge logic) and `tests/test_goal_loop.py` (10 tests vs 8 estimated;
added `test_e2e_uses_real_standard_yaml` as drift sanity check).
Comfortably within the 180-min duration override.

**Two `graph.transition` events per `nnn`.** When `nnn` succeeds, it
fires `nnn_pass` (THINK→SANDBOX) AND `vvv_pass` (SANDBOX→DO) in
sequence — SANDBOX is a one-tick verifier checkpoint per Q1 default
(a). Audit chain therefore grows by **two** events per `nnn`, not one.
This was anticipated and tested in `test_e2e_full_loop`.

**Audit chain is the source of truth, not session_state.json.** During
the bootstrap phase, audit events were appended hand for steps 1–8 but
`session_state.json:graph_state` was never updated. When step 9's
runtime asked `Loop.current()`, it read from session_state.json, got
no `graph_state`, fell back to graph initial_state `READY` — wrong.
Reconciled with one explicit `SessionLocalState(...).set_graph_state("DO")`
before firing the rest. **Lesson:** in mixed-mode sessions (some manual
audit, some runtime), session_state.json must be reconciled against
the audit chain at handoff. Future enhancement (R6) — startup
consistency check.

## What broke (along the way)

| Issue | When | Fix |
|-------|------|-----|
| `from ..core.loop import Loop` failed in inline test | step 3 smoke | Use `from cli.commands.vvv import ...` (package path); conftest puts `.ai/` on sys.path |
| `Loop.current()` returned `READY` after manual audit appends | step 9 handoff | Explicit `SessionLocalState.set_graph_state("DO")` to reconcile |
| `test_basic.test_state_initialized` failed under active session | step 8 pytest | Out-of-scope environmental brittleness; not a regression |

## Decisions enforced this session

- **D1** (boundaries) — zero writes to `.ai/policies/**`, `.ai/audit/**`
  (modify), `.ai/schemas/**`, `docs/specs/**`, `references/**`. Verified
  by `git diff --name-only` on session close.
- **D2** (AI proposes, verifier/policy/human decides) — every step
  preceded by vvv + nnn; verifier-stub explicitly logged with rule_set
  + verdict so a Phase 4 swap is a one-line change.
- **D7** (no vendor adapters) — `.claude/skills/`, `.cursor/rules/`,
  `.warp/workflows/` confirmed absent post-session.
- **D9** (hash chain audit) — chain grew 1 → 30 with no batched appends;
  `chain.validate()` ran after every transition.
- **D10** (decided_by required) — `Loop.fire()` raises
  `DecidedByMismatch` on wrong authority; tested directly.
- **D11** (budget breach → NEEDS_HUMAN) — `Budget.check` enforces;
  human override is the only legitimate bypass and is logged with
  authority + reason.
- **D12** (relative paths via SSOT) — `Loop._infer_project_root` walks
  up from session_path; no `<user-home>` literals in code.

## What's next (Phase 2+)

This session closed Phase 1's explicit goal. Deferred:

- **Phase 4** — real Pyramid layer 1 rule sets in `verifier-rules.yaml`
  (replaces `step_complete` stub).
- **Phase 5** — goal tree (`goals.yaml`), decomposer, queue,
  checkpoint primitives, soft (80%) / hard (100%) budget split,
  `ai loop start/resume/...` namespace.
- **Phase 5+** — thin `ai ddd` / `ai rrr` CLI wrappers (currently
  fired via `Loop.fire` directly in tests + manual E2E walks).

## Open follow-ups

| ID | Description | Priority |
|----|-------------|----------|
| **R5** | `test_basic` should accept `idle` or `busy` (pre-existing brittleness) | low |
| **R6** | Startup consistency check: reconcile `session_state.json:graph_state` against audit chain on every Loop init | medium (avoids surprise during mixed-mode sessions) |
| **R1** | (carryover Session A) extend `test_yaml_valid` for `status.json` | nice-to-have |
| **R2** | (carryover Session A) lift path-resolution to `core/path_resolver.py` | nice-to-have |
| **R3** | (carryover Session A) `status.json:last_event_hash` startup check | nice-to-have |

## Cross-references

- Memory-cli twin: [`.ai/memory/retros/0002_2026-04-30_20_34_pm_feat-phase1-goal-loop-runtime.md`](../../.ai/memory/retros/0002_2026-04-30_20_34_pm_feat-phase1-goal-loop-runtime.md)
- Session A retro: [`06_RETRO_TRINITY_V2_SETUP_ARC.md`](06_RETRO_TRINITY_V2_SETUP_ARC.md)
- Decisions log: [`01_CONTEXT_AND_DECISIONS.md`](01_CONTEXT_AND_DECISIONS.md)
- Audit chain (live): `.ai/audit/events.ndjson` (depth 30 at session close)
- Final session: `.ai/sessions/0001_2026-04-30_20_10_pm_feat-phase1-smoke/`
