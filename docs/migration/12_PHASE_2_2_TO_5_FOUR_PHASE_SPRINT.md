---
title: "Retro — Session H: Phase 2.2 → 5 four-phase sprint"
status: locked
last-updated: 2026-05-01
audience: "Trinity team + future Phase 0.5 / 1 / 6 / 7 / 8 / 9 / 10 sessions"
session-window: "2026-04-30 → 2026-05-01 (single conversation, four phases)"
session-id: "informal_2026-05-01_feat-phases-2-2-to-5-sprint"
acceptance-evidence: PASS
rrr-contract: PASS
audit-events-added: ~50 (lll.invoked, loop.checkpoint, ddd.completed, etc., across new commands)
---

# Session H — Phase 2.2 → 5 (consolidated four-phase sprint)

> **First session that closed FOUR phases in one window.** Knowledge
> Brain auto-fed on every retro (2.2), recall wired into
> `lll/vvv/nnn` (2.3), Pyramid layer-1 verifier became real (4),
> goal-tree + `ai loop` + `ai ddd` proper (5). All 12 memory-cli
> spec verbs are live. trinity_v2 pytest passed every gate from
> 94 → 180 with zero spec changes.
>
> **Caveat:** this work happened outside an `ai session`, so no
> graph_state ran through the standard transitions. The retro is
> recorded informally; R14 (`ai rrr --retroactive --session <id>`)
> would let a future operator stitch it into the audit chain.

## Scope

Four phases, one continuous conversation:

| Phase | What landed |
|-------|-------------|
| **2.2** | memory-cli `learn` / `tag` / `supersede` / `reflect` (4 verbs); `core/tools_registry.py`; `ai rrr` auto-feed via subprocess |
| **2.3** | memory-cli `delete` / `reindex` / `health` (3 verbs); `commands/lll.py` (read-only snapshot); `vvv` + `nnn` query memory for past-incident hints |
| **4** | `core/verifier.py` rule engine (file-driven Pyramid layer 1); 5 rule_sets in `verifier-rules.yaml`; `gogogo.py` swapped from stub to real engine; `force_verdict` kept for fixtures |
| **5** | `core/goal_tree.py` (epic→feature→task hierarchy + status state machine + aggregation); `commands/loop.py` (status / checkpoint / resume); `core/loop_state.py`; `commands/ddd.py` proper (deprecates `--auto-deploy` flag in `rrr.py`) |

D13 was honored throughout — memory-cli stayed sibling, kernel
unchanged in shape. Specs were never edited.

## Metrics

| Dimension | Value |
|-----------|-------|
| Phases completed in one window | 4 (2.2, 2.3, 4, 5) |
| memory-cli verbs | 5 → 12 (all spec verbs live) |
| memory-cli LOC delta | ~1,400 (lib + tests) |
| memory-cli internal tests | 33 → 93 (+60) |
| memory-cli tool_version | 0.3.0-beta → 0.5.0-beta |
| trinity_v2 LOC delta | ~2,100 (core + commands + tests) |
| trinity_v2 pytest | 94 → 180 (+86) |
| New core modules | `tools_registry`, `verifier`, `goal_tree`, `loop_state` |
| New CLI commands | `lll`, `loop` (status/checkpoint/resume), `ddd` |
| Contract baseline updates | v0.3 → v0.4 → v0.5 |
| Spec changes | 0 |
| Locked decisions enforced | D8, D9, D10, D11, D13 |

## What worked

**Stacking phases pays off when specs are this clean.** Each phase
added one tractable layer (verbs → integration → engine → goal
model). Tests for the prior layer immediately caught regressions in
the next. No phase needed a spec change.

**`tools_registry` was the right abstraction at the right time.**
Once `ai rrr → memory-cli learn` was wired in 2.2, the same
`call_tool(project_root, name, cmd)` helper unlocked
`vvv/nnn/lll → memory-cli search` in 2.3 with no extra plumbing.
Building the helper deliberately small (no fancy retry, no streaming)
kept the audit footprint clean: one subprocess, one envelope, one
optional summary in the appended event.

**Permissive `step_complete` defaults kept Phase 4 backward-
compatible.** The verifier engine is real (file-driven rules, eval
order, fallback), but `step_complete.defaults: { step_done: true }`
means existing flows that don't supply rich evidence keep producing
PASS. The ramp to "real" rule_sets (`code_change`, `deploy_check`)
is opt-in per-session — operators flip the rule_set once they're
authoring evidence.

**Goal tree decoupled from loop_state was correct.** `goals.yaml`
owns *what to do*; `loop_state.json` owns *where am I*. Audit
boundaries stay clean — goal mutations are reasoned per-goal, loop
cursor advances per-tick.

**Per-verb tier table beats blanket `policy_default`.** memory-cli's
COMMAND_CONTRACT.md §5 now lists every verb's tier (safe / normal /
aggressive). `delete` and `reindex` are explicitly aggressive; the
RBAC layer can reason about them per-call instead of inheriting the
tool-wide default.

## What surprised

**Nested transactions don't work in `node:sqlite`.** Phase 2.3
`reindex --from-source` originally wrapped the per-file indexer in
an outer `BEGIN/COMMIT`, but `indexFile` itself uses a transaction —
inner BEGIN errored silently and the whole FTS table came up empty
on success. Fix: dropped the outer txn, accept per-file atomicity,
documented "reindex is idempotent — re-run to pick up where it
stopped" in the contract.

**`PRAGMA foreign_key_check` and a hand-rolled `supersession_refs`
check overlap.** I left both in `health` because they catch the
same bug at different severities (FAIL vs WARN). The operator gets
a layered report — pragma raises the alarm, supersession_refs names
the broken row directly. Redundant, but cheap and informative.

**The `_truthy` predicate semantics needed care.** Empty string,
0, [] should NOT match a verifier predicate (those are typically
"evidence absent" markers); a non-empty list of warnings SHOULD
match. The unit-test grid in `test_verifier.py::test_truthy_semantics`
is now the spec for that.

**LOC came in roughly as estimated.** The plan called for ~3,500 LOC
across the four phases; actual was ~3,500. The verifier engine is
~150 LOC (smaller than expected because predicate matching is
literally a dict lookup); the goal tree is ~280 LOC (larger because
the cycle detection + status state machine added breadth).

## What broke (along the way) and the fix

| Issue | Phase | Fix |
|-------|-------|-----|
| FK-protected fixtures couldn't seed an orphan tag for `health` test | 2.3 | `PRAGMA foreign_keys = OFF` around the inject; assert overall=`fail` because the FK pragma also catches it |
| Nested DB transactions in `reindex --from-source` left FTS empty | 2.3 | dropped the outer txn; per-file atomicity is sufficient |
| Untracked `.ai/` files showed `dirty_count > 0` in lll's git test | 2.3 | `git add .` before commit so test_path resolves clean |
| Test expected `typer.Exit` from `ai loop resume` happy path | 5 | `resume()` returns normally on hit; only `Exit(0)` on no-pending — split into two tests |
| Stray `.memory/memory.db` in `trinity_v2/` after smoke | 2.2 | `rm -rf .memory/` cleanup |
| A3 brittle JSON grep in earlier session (8 hits not 4) | (carried from G) | confirmed not re-introduced by this sprint |

## Decisions enforced

- **D8** — Pyramid of Judgment: layer-1 deterministic rules now
  real (`core/verifier.py` + populated `verifier-rules.yaml`).
  Layers 2–4 still use placeholder shapes per spec.
- **D9** — read-only events still append. New: `lll.invoked`,
  `loop.checkpoint`. The chain depth grew without anyone bypassing
  the audit gate.
- **D10** — every transition has `decided_by`. `ai ddd` fires
  `promote_request` + `deploy_request` as `decided_by=human`,
  matching the standard graph contract.
- **D11** — budget breach = `NEEDS_HUMAN` (gogogo.py per-step
  recheck unchanged).
- **D13** — plugin tool architecture: `tools_registry.py` is the
  kernel side of the contract; memory-cli stays sibling under
  `${project_root}/../memory-cli/`. `tool_version` bumps did NOT
  require a `contract_version` bump (envelope shape unchanged).

## Open follow-ups

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| **R5** | `test_basic` should accept `idle | busy` | low | open |
| **R7** | `ai nnn --plan-envelope <relative>` resolve from project_root | low | open |
| **R8** | `tools-policy::supported_contract_versions` may need pre-1.0 markers | medium | open |
| **R12** | `ai ddd` proper CLI (Phase 5) | medium | ✅ closed |
| **R13** | `ai rrr --baseline <commit>` for forbidden_diff | low | open |
| **R14** | `ai rrr --retroactive --session <id>` for sessions A–D + this informal H | low | open |
| **R15** | Tool registry should pin `engines.node` per tool contract | medium | open |
| **R16** (new) | This session's work was not stitched into the audit chain via `ai rrr`. R14 implementation would let a future operator backfill | low | open |
| **R17** (new) | `verifier-rules.yaml.defaults` block is documented only inline; spec §3.3 doesn't mention it. Worth a one-paragraph clarification next time the spec is edited | low | open |

## What's next

| Phase | Adds |
|-------|------|
| **0.5** | Bootstrap Pack — `install.sh` + portable CLAUDE.md / AGENTS.md / GEMINI.md templates. Solves "AI doesn't know short codes after `cp -r`". |
| **1** | `trinity-contract-test` CLI — Bronze/Silver/Gold tier validation against any plugin tool's binary. |
| **6** | Multi-graph composition + sub-graph (kernel-level). |
| **7** | `retro-cli` sibling tool (structured retro writer with schema enforcement). Closes the auto-feed loop with 2.2's `learn`. |
| **8** | Trinity Shim adapters — render `.ai/shims/{lll,vvv,nnn,rrr,gogogo}/SHIM.md` into Claude Code skills, Cursor rules, AGENTS.md directives, Warp workflows. |
| **9** | Hybrid memory — vector embeddings + ChromaDB hybrid ranking on top of FTS5. |
| **10** | Extension Platform (registry view + dashboard). |

## Cross-references

- Memory-cli twin retro:
  [`.ai/memory/retros/0009_2026-05-01_<time>_feat-phase-2-2-to-5-sprint.md`](../../.ai/memory/retros/) (this entry's canonical memory copy)
- Phase 2.1b retro: [`11_PHASE2_1B_MEMORY_CLI_SEARCH.md`](11_PHASE2_1B_MEMORY_CLI_SEARCH.md)
- Phase 1.5 retro: [`09_PHASE1_5_RRR_EXECUTABLE_GATE.md`](09_PHASE1_5_RRR_EXECUTABLE_GATE.md)
- memory-cli spec: [`../specs/05_MEMORY_CLI_SPEC.md`](../specs/05_MEMORY_CLI_SPEC.md)
- Verifier spec (Phase 4): [`../specs/02_VERIFIER_SPEC.md`](../specs/02_VERIFIER_SPEC.md)
- Goal-loop spec (Phase 5): [`../specs/03_GOAL_LOOP_SPEC.md`](../specs/03_GOAL_LOOP_SPEC.md)
- Frozen contract baseline: [`../contracts/memory-cli/COMMAND_CONTRACT.md`](../contracts/memory-cli/COMMAND_CONTRACT.md)
- Tool source: `../memory-cli/` (sibling repo)
- Audit chain (live): `.ai/audit/events.ndjson` (depth ~189 at start of this session; informal events not appended because no `ai session` was opened — see R16)

## Notes

- The four-phase sprint validated that Trinity's spec-first approach
  scales: each phase took its frozen spec at face value and added
  the missing implementation layer. No spec edits required.
- `tools_registry` becoming the kernel-side contract handler is the
  reusable beachhead for Phase 7 (`retro-cli`) and any future plugin
  tool — they'll just register in `tools.yaml` and the kernel calls
  them through the same envelope path.
- The `ai loop` namespace is intentionally introspection-only — it
  does NOT auto-execute the next goal. That stays the human's
  decision (or, in Phase 9+, an explicit `ai loop run` opt-in).
