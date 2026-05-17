---
title: "Retro — Session I: Phase 0.5 → 10 buildout + UX seamless layer"
status: locked
last-updated: 2026-05-01
audience: "Trinity team + future Phase 11+ sessions; operators onboarding new projects"
session-window: "2026-05-01 (single conversation, seven phases + UX layer)"
session-id: "informal_2026-05-01_feat-phase-0-5-to-10-and-ux-sprint"
acceptance-evidence: PASS
rrr-contract: PASS
audit-events-added: ~70 (lll.invoked, loop.subgraph.entered/exited, ddd.completed, shim.render synthetic, etc.)
---

# Session I — Phase 0.5 → 10 + UX seamless layer

> **First session that closed SEVEN phases plus a cross-cutting UX
> reduction in one window.** Distribution-ready Bootstrap Pack
> shipped, plugin-tool conformance validator shipped, kernel sub-
> graph composition shipped, two new sibling tools (retro-cli +
> trinity-contract-test + trinity-extension-platform) shipped,
> vector embeddings + hybrid search added to memory-cli, read-only
> dashboard server shipped, AND the user's "users won't memorize"
> friction was addressed by reducing the daily surface to "type
> `ai` and trust the footer."
>
> All five phases of the original 11-phase roadmap that were still
> open closed in this window. The roadmap is now done through
> Phase 10; Phase 11+ items (Rust rewrite, Layer 4 LLM router,
> <Upstream-Project> audit) remain as future work.
>
> **Caveat (carried from Session H):** this work also happened
> outside an `ai session`, so no graph_state ran through the
> standard transitions. R14 (`ai rrr --retroactive --session
> <id>`) would let an operator backfill Sessions H + I together.

## Scope

Seven phases + one cross-cutting UX layer in one continuous
conversation:

| Phase | What landed |
|-------|-------------|
| **0.5** | `trinity-bootstrap/` sibling — `install.sh` + `verify-install.sh` + 3 entrypoint templates (CLAUDE/AGENTS/GEMINI) + 5 ai-docs (QUICK_START / SHORT_CODES / CORE_RULES / WORKFLOW / **CHEATSHEET**) + minimal `.ai/` (ssot/tools/policies/graphs). 23-check verifier. |
| **1** | `trinity-contract-test/` sibling — Bronze/Silver/Gold/Platinum tier validator for plugin tools. Memory-cli scores 14/14, retro-cli scores 14/14. 9 self-tests. |
| **6** | Multi-graph composition in trinity_v2 kernel — `enter_subgraph` / `exit_subgraph` on `Loop` with persisted stack, cycle protection, terminal-state guard, `decided_by` validation, audit events. |
| **7** | `retro-cli/` sibling — `validate` / `lint` / `create` / `commit` verbs. Frontmatter schema enforcer; auto-feeds memory-cli on commit. 23 tests. |
| **8** | Shim adapters — `core/shim_render.py` + `commands/shim.py` rendering `.ai/shims/<code>/SHIM.md` into Claude Code skills, Cursor `.mdc` rules, AGENTS.md fragment, Warp workflows. 13 new tests. |
| **9** | Hybrid memory in memory-cli — schema v2 with embedding columns, deterministic `fake` provider, `embed` + `similar` verbs, `--hybrid` flag on `search` (RRF fusion of BM25 + cosine). Pluggable provider interface. 22 new tests. |
| **10** | `trinity-extension-platform/` sibling — read-only HTTP dashboard server (zero deps, `node:http`). 8 endpoints + dashboard HTML. 11 tests. |
| **UX (Layers 3+5)** | `core/next_action.py` + `commands/next.py` + bare `ai` no-arg routing + ritual success footers (vvv/nnn/gogogo/ddd/rrr/lll) + CHEATSHEET.md + error-message audit (8 files patched to suggest literal next command). 21 next-action tests. |

D13 still honored — every new tool is a sibling, kernel internals
stayed at the same shape (additive only). No spec edits.

## Metrics

| Dimension | Value |
|-----------|-------|
| Phases completed in one window | 7 (0.5, 1, 6, 7, 8, 9, 10) + cross-cutting UX |
| New sibling repos | 4 (trinity-bootstrap, trinity-contract-test, retro-cli, trinity-extension-platform) |
| memory-cli verbs | 12 → 14 (`embed` + `similar`); tool_version 0.5.0-beta → 0.6.0-beta; schema_version 1 → 2 |
| memory-cli internal tests | 93 → 115 (+22) |
| trinity_v2 pytest | 180 → 226 (+46) |
| New core modules | `next_action`, `goal_tree` (carried-from H), `loop_state` (carried), `tools_registry` (carried), `verifier` (carried), `shim_render` |
| New CLI commands | `next`, `shim` (+ `loop` and `ddd` from Session H) |
| Bare `ai` invocation | now routes to `ai next` (state-aware prompter) |
| Sibling tests | retro-cli 23, trinity-contract-test 9, trinity-extension-platform 11 |
| Total tests across stack | 226 + 115 + 23 + 9 + 11 = **384 passing** |
| Contract baseline updates | memory-cli v0.5 → v0.6 |
| Spec changes | 0 |
| Error messages improved | 8 files (deploy / close / promote / sandbox / verify / gogogo / ddd / rrr) |
| Locked decisions enforced | D8, D9, D10, D11, D13 (all from H) + D9 read-only-events extended (`lll.invoked`, `loop.checkpoint`, `loop.subgraph.entered/exited`, `ddd.completed`) |

## What worked

**The bootstrap-then-validate-then-feed pipeline scaled.** Phase
0.5 produced the install/verify scripts; Phase 1 immediately had
something to validate against (memory-cli + retro-cli both score
Platinum); retro-cli's `commit` then auto-feeds memory-cli. Each
phase fed the next without spec edits.

**`tools_registry` (built in Session H) paid for itself again.**
Phase 7's `retro-cli` discovers memory-cli through the same
sibling-walk mechanism that Session H's `ai rrr → memory-cli
learn` used. The dashboard (Phase 10) shells out to `memory-cli
stats` through the registered entry. Three call-sites, one
helper.

**Sub-graph composition (Phase 6) was small once the state engine
was right.** ~80 LOC kernel addition + 12 tests. The trick was
storing `{outer_graph, outer_state, inner_graph}` per stack frame
so `exit_subgraph` could restore both axes; cycle-detection then
reduced to "is this name already on the stack?".

**Hybrid search (Phase 9) was tractable because the schema had
already reserved `embedding BLOB` since v1.** Migration was just
ALTER TABLE for four columns + INSERT-ON-NULL semantics. The
deterministic `fake` provider made testing tight (no LLM
dependency), and reciprocal-rank-fusion gave hybrid scoring with
zero tunable parameters.

**Layer 3 (bare `ai` → `ai next`) was a cheap, high-impact UX
move.** `core/next_action.py` is ~150 LOC; the integration was
adding `console.print(render_one_line(compute(...)))` to six
ritual success panels. Now users only have to remember `ai`.

**The error-message audit caught laggers without breaking
anything.** A grep + 5 simple replaces upgraded "No active
session found." → "No active session found. Run `ai session new
<task>` first." across 5 files in 5 minutes. Tier 5(c) of the UX
plan was real — it's not the LLM router that lowers cognitive
load, it's the suggestions that ride alongside every error.

**Persistent TODO.md + memory pointer closed the "what's left"
gap.** Future sessions land at `TRINITY_LEGACY/`, the auto-
memory entry tells them to read `TODO.md` first; the file groups
items into 5 priority tiers. No need to re-discover the open list
from chat history.

## What surprised

**The dashboard's tools.yaml parser hit a real edge case live.**
The hand-rolled YAML reader treated indented `- item` lines from
nested `capabilities:` arrays as new tool entries, producing 11
ghost rows in `/api/tools`. Fix: pin `toolsItemIndent` from the
first dash and bucket deeper-indented dashes as block-array items
on the active tool. Caught by `curl /api/tools` after the user
asked to see the dashboard live — automated tests didn't have a
fixture with block-array capabilities, so they passed.
**Lesson:** integration smoke (`curl` against a live server) finds
parser bugs that table-driven unit tests miss.

**`node:sqlite` returns BLOB as `Uint8Array`, not `Buffer`.**
Phase 9's `unpackEmbedding` called `buf.readFloatLE` which is a
Buffer-only method. First test crashed with `TypeError:
buf.readFloatLE is not a function`. Fix: promote `Uint8Array →
Buffer.from(buf.buffer, buf.byteOffset, buf.byteLength)`
zero-copy. Documented inline so the next person doesn't trip.

**Typer's `no_args_is_help=True` is sticky.** Layer 3 wanted bare
`ai` to route to `ai next`, not show help. Fixing it required
flipping `no_args_is_help=False` AND adding
`invoke_without_command=True` to the global callback AND manually
checking `ctx.invoked_subcommand is None`. The CLI framework
defaulted to "show help" loudly enough that getting the routing
right took two iterations.

**`render` template substitution overwrites by default.** The
bootstrap pack's `render()` shell function uses `>` (not `>>` or
`-n`), so a re-install would clobber a hand-edited CLAUDE.md.
TRINITY_LEGACY had no entrypoint files yet, so this didn't
matter — but for a project with custom CLAUDE.md content, the
installer should `cp -n` or backup first. **Open as a Tier 1
followup if anyone hits it.**

**Test counts compounded faster than expected.** Phase 6 added
12, Phase 7 added 23, Phase 8 added 13, Phase 9 added 22, Phase
10 added 11, UX added 21. Total +102 tests across the stack in
this window — with zero failures. Spec-first paid off.

## What broke (along the way) and the fix

| Issue | Phase | Fix |
|-------|-------|-----|
| Outer txn around per-file indexer in reindex --from-source produced empty FTS | 2.3 (carried from H) | dropped outer txn; per-file atomic; documented "reindex is idempotent" |
| `tools.yaml` parser created ghost tool rows from block-array `capabilities:` items | 10 | pinned `toolsItemIndent` + bucketed deeper dashes as block-array items |
| `node:sqlite` BLOB ≠ Buffer; `readFloatLE` undefined | 9 | wrapped Uint8Array → Buffer zero-copy |
| Typer `no_args_is_help=True` blocked bare-`ai` routing | UX | flipped to False + `invoke_without_command=True` + manual `ctx.invoked_subcommand` check |
| `f-string` with backslashes in Python tests for `curl | python3 -c` smoke | 10 | rewrote inline scripts to avoid backslash-in-f-string |
| FK-protected fixtures couldn't seed orphan rows for health tests | 2.3 (carried) | `PRAGMA foreign_keys = OFF` around inject |
| Bare-test running outer txn in reindex from H | 2.3 | already fixed in H; not regressed |

## Decisions enforced

- **D8** (Pyramid layer 1) — extended via `verifier-rules.yaml` to
  the new `deploy_check` set; `ai ddd` invokes verifier with
  evidence file (informational only — transition is human-decided).
- **D9** (read-only events still append) — three new event types
  in this window: `lll.invoked`, `loop.checkpoint`,
  `loop.subgraph.entered`, `loop.subgraph.exited`,
  `ddd.completed`. None mutate state outside the chain.
- **D10** (`decided_by` enforcement) — `ai ddd` fires
  `promote_request` + `deploy_request` as `decided_by=human`
  exactly per the standard graph; `enter_subgraph` validates
  `decided_by ∈ VALID_AUTHORITIES` before pushing the stack.
- **D11** (budget breach = NEEDS_HUMAN) — gogogo per-step recheck
  unchanged; verifier engine swap-in honored the existing budget
  hooks.
- **D13** (plugin tool architecture) — four new sibling tools
  registered in trinity_v2's tools.yaml + TRINITY_LEGACY's
  tools.yaml. Kernel never imports sibling code; everything goes
  through `core/tools_registry.py::call(...)`.

## Open follow-ups

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| R5 | `test_basic` accept `idle | busy` | low | open |
| R7 | `ai nnn --plan-envelope <relative>` resolve from project_root | low | open |
| R8 | `tools-policy::supported_contract_versions` pre-1.0 markers | medium | open |
| R12 | `ai ddd` proper CLI | medium | ✅ closed (Session H) |
| R13 | `ai rrr --baseline <commit>` | low | open |
| R14 | `ai rrr --retroactive --session <id>` | low | open (gates R16) |
| R15 | Tool registry pin `engines.node` | medium | open |
| R16 | Sessions H + I not stitched into audit chain | low | open (depends on R14) |
| R17 | Document `verifier-rules.yaml.defaults` block | low | open |
| **R18 (new)** | Bootstrap `install.sh` `render` clobbers existing entrypoints | low | open — surface before users hit it |
| **R19 (new)** | tools.yaml parser in extension-platform should match contract-test's parser exactly (DRY) | medium | open |
| **R20 (new)** | Bulk-index 240 legacy retros into memory-cli so `lll/vvv/nnn` hints have breadth | medium | open — 15 min job |
| **R21 (new)** | Old `TRINITY_LEGACY/.ai/cli/` (v1 kernel) not pruned; alias points to trinity_v2 anyway | low | open — symlink, deprecate, or delete |

## What's next (post-Phase 10 roadmap)

Roadmap items 0.5 → 10 are now CLOSED. The remaining open work is
in five tiers, tracked durably at `TRINITY_LEGACY/TODO.md`:

| Tier | Theme | First item to pick |
|------|-------|--------------------|
| 1 | Small fixes (R5–R21) | R8 + R15 (tool-registry hardening) |
| 2 | UX deepening | R20 (bulk-index legacy retros) |
| 3 | Distribution / packaging | npm publish 5 siblings |
| 4 | Workspace cleanup | dashboard bg process cleanup |
| 5 | Docs / governance | license decision (MIT vs Apache-2.0) |

Phase 11+ items (Rust rewrite, Layer 4 LLM router, <Upstream-Project> audit)
remain as future work. No Phase 11 is currently planned.

## Cross-references

- Memory-cli twin: `.ai/memory/retros/0010_2026-05-01_08_06_pm_feat-phase-0-5-to-10-and-ux-sprint.md`
- Predecessor retro: `12_PHASE_2_2_TO_5_FOUR_PHASE_SPRINT.md`
- Pending-work checklist: `<workspace-root>/TRINITY_LEGACY/TODO.md`
- Bootstrap Pack spec: `docs/specs/00b_BOOTSTRAP_PACK.md`
- Tool Contract: `docs/specs/01_TOOL_CONTRACT.md` (§16a Compliance Test)
- Verifier spec: `docs/specs/02_VERIFIER_SPEC.md`
- Goal Loop spec: `docs/specs/03_GOAL_LOOP_SPEC.md`
- Graph spec (Phase 6): `docs/specs/04_GRAPH_SPEC.md` §6
- memory-cli spec: `docs/specs/05_MEMORY_CLI_SPEC.md` §15 (hybrid)
- retro-cli spec: `docs/specs/06_RETRO_CLI_SPEC.md`
- Shim spec: `docs/specs/07_SHIM_SPEC.md`
- Sibling tools: `<workspace-root>/{memory-cli,retro-cli,trinity-bootstrap,trinity-contract-test,trinity-extension-platform}/`
- Audit chain (live): `.ai/audit/events.ndjson`

## Notes

- This sprint validated that Trinity's spec-first approach scales
  *across siblings* too. Four new tools shipped without touching
  `01_TOOL_CONTRACT.md`; the contract was the spec.
- The Layer 3 + 5 UX work was the user's idea and the right one.
  Counted from "ai vvv → next" to "type `ai` and trust the
  footer", the daily surface dropped from "memorize 5 codes + when
  to run them" to "memorize `ai`". The 5 codes are still there for
  power users.
- `TRINITY_LEGACY/TODO.md` is the source of truth for open work
  going forward. The auto-memory pointer at
  `~/.claude/projects/.../memory/project_pending_work_pointer.md`
  ensures fresh sessions read it.
