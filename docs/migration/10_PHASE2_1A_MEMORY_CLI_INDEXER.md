---
title: "Retro — Session F: Phase 2.1a memory-cli indexer"
status: locked
last-updated: 2026-04-30
audience: "Trinity team + future Phase 2.1b+ sessions"
session-window: "2026-04-30 (single session, ~13 min wall by chain metrics)"
session-id: "0001_2026-04-30_22_19_pm_feat-phase2-1a-memory-cli-indexer"
acceptance-evidence: PASS
rrr-contract: PASS
audit-events-added: 34
---

# Session F — Phase 2.1a: memory-cli indexer (SQLite + FTS5)

> **Second session in Trinity history with `RRR contract: PASS`
> verified by machine.** Memory-cli moves from alpha skeleton (1
> stub verb) to beta (2 wired verbs: `stats` + `index`); SQLite +
> FTS5 schema lives; 3-fixture golden test passes; trinity_v2 kernel
> untouched (D13 confirmed end-to-end).

## Scope

Implement the memory-cli indexer pipeline (Phase 2.1a):

- SQLite + FTS5 schema (documents, documents_fts, tags, supersession, evidence_links)
- markdown + YAML frontmatter parser
- walk + dedupe-by-sha256 + atomic-per-file insert
- `index` verb wired into the dispatcher
- 3 fixture markdown files exercising parser branches
- harness tests + golden E2E test (node:test)
- contract baseline updated; tools.yaml registry bumped

`search` / `get` / `list` ship in Phase 2.1b.

## Metrics

| Dimension | Value |
|-----------|-------|
| Files NEW (sibling memory-cli/) | 3 lib + 2 tests + 3 fixtures = 8 |
| Files MODIFY (sibling) | 2 (`index.js` adds `index` verb + DB-backed `stats`; `package.json` bumps version, drops the briefly-tried better-sqlite3 dep) |
| Files NEW (trinity_v2) | 0 |
| Files MODIFY (trinity_v2) | 2 (`.ai/tools.yaml`, `docs/contracts/memory-cli/COMMAND_CONTRACT.md`) |
| memory-cli LOC actual | ~520 (Node.js + tests + fixtures) |
| trinity_v2 LOC delta | ~80 (registry + contract baseline) |
| memory-cli tests | 11 (8 harness + 3 golden) — all passing |
| trinity_v2 pytest | 94 / 94 (after close) — no regression |
| Audit events added | 34 (chain depth 118 → 152) |
| Spec changes | 0 |
| Sessions with `RRR contract: PASS` (lifetime) | 2 (E and F) |
| Locked decisions enforced | D1, D2, D9, D10, D11, D13 |

## What worked

**`node:sqlite` saved the day.** Initial plan was `better-sqlite3`,
the canonical Node sqlite binding. On Node v25 the native compile via
node-gyp failed (prebuilts don't cover Node 25 yet). Q5 risk register
listed `sql.js` as a fallback. We didn't need it: Node 22+ ships
`node:sqlite` built-in with FTS5 enabled — zero deps, zero compile,
synchronous API close enough to better-sqlite3 that the rewrite took
~5 minutes (`db.transaction(fn)` becomes a small BEGIN/COMMIT
wrapper; `db.pragma(...)` becomes `db.exec('PRAGMA ...')`). The
contract shape (envelope output) didn't change a byte.

**Standalone FTS5 (no `content=` linkage) was the right call.** First
schema used `content=documents content_rowid=rowid`. It broke
immediately: FTS5 expected a `tags` column on `documents`, but tags
live in a separate join table. Switching to standalone FTS5 (FTS owns
its own title/body/tags copy) costs a bit of disk but eliminates an
entire class of trigger/shadow-rowid bugs. The right tradeoff at
file-store scale.

**3-fixture coverage caught a real parser bug.** First `with-broken-yaml.md`
had an unclosed list (`tags: [deploy, postmortem`); my forgiving parser
treated it as a string and returned `ok: true` — exactly what a
forgiving parser should do, but it left the `ok: false` branch untested.
Updated the fixture to have a truly unparseable line (no colon, no
whitespace) — now the parser hits the throw branch and the indexer's
`tolerate_bad_frontmatter` fallback exercises. Lesson: even "obvious"
fixtures need the test to actually walk the branch they claim to walk.

**Phase 1.5 acceptance gate worked as designed.** A3 originally piped
`npm test` through `tail -3 | grep -E 'pass|ok'`, but the last 3 lines
of node:test output are `ℹ skipped 0` / `ℹ todo 0` / `ℹ duration_ms`
— none contain "pass". DRY-RUN gate: FAIL caught it. Fixed in 30 sec
by switching to exit-code: `npm test > /dev/null 2>&1`, `expect_exit:
0`. The gate refused to fire RETRO→DONE on a half-broken acceptance
spec — exactly its job.

**`acceptance` in `plan_envelope.json` flowed end-to-end through
Phase 1.5's R11.** First real exercise of the path:

```
plan_envelope.json {acceptance: [...]}
  → ai nnn writes THINK/03_ACCEPTANCE.yaml
  → ai rrr reads + executes
```

No manual sync between docs. Authoring the executable acceptance once
in the envelope is the source of truth.

**Trinity_v2 kernel stayed at 94/94 with zero kernel changes.** Phase
2.1a is a pure sibling-tool delta from trinity_v2's perspective —
only `.ai/tools.yaml` (registry entry) and `docs/contracts/memory-cli/`
moved. D13's promise (kernel ≠ tools; kernel speaks frozen contract,
tools evolve freely) realized end-to-end.

## What surprised

**Node v25 made our `>=18` engines field a lie.** better-sqlite3
prebuilds don't cover bleeding-edge Node yet. Bumped to `>=22.5.0` to
match `node:sqlite` availability. New follow-up R15: tool registry
should pin `engines.node` per tool contract — sibling tools may drift
Node versions independently and the kernel should know.

**Auto-generated retro by `ai rrr` was substantial enough as-is.**
The Phase 1.5 retro renderer produces frontmatter + verdict + metrics
+ acceptance table + transitions + forbidden-diff section. Manual
"What worked / surprised / broke" sections were genuinely additive
this time, not paraphrases of the auto content. Retros become more
useful per-LOC of human writing.

**`docs/contracts/memory-cli/` evolution worked smoothly.** Bumping
the contract from v0.1-alpha to v0.2-beta required: edit the version
line, append a changelog entry, add §2.2 for the new `index` verb,
add new error codes. No directory split, no breaking change. The
"frozen baseline" model evolves without churn.

## What broke (along the way)

| Issue | When | Fix |
|-------|------|-----|
| `${line!r=line}` Python f-string syntax in JS parser | first parser smoke | replace with `JSON.stringify(line)` |
| better-sqlite3 native compile fails on Node 25 | npm install | switch to `node:sqlite` (built-in, FTS5, zero deps) |
| FTS5 `content=documents` broke on `tags` column | first index run | drop `content=` linkage; standalone FTS5 with own copy |
| `node --test tests/` ran zero tests | first npm test | explicit glob `node --test tests/*.test.js` |
| broken-yaml fixture wasn't actually broken | first harness test run | rewrote with no-colon line |
| A3 grep brittle (no "pass" in last 3 lines of npm test) | first ai rrr dry-run | switch to exit-code check |

## Decisions enforced

- **D1** — `ai rrr` itself enforced. forbidden_diff: 0 violations
  verified at session close. ✅
- **D2** — vvv (5Q with α/β/γ scope discussion) → nnn (budget
  override + executable acceptance) → gogogo → rrr. Every gate
  human-decided.
- **D9** — chain grew 118 → 152+. `chain.validate()` OK throughout.
- **D10** — `Loop.fire` enforced authorities; `--auto-deploy` fires
  promote/deploy with decided_by=human.
- **D11** — budget breach (90 vs 30 default = 3×) handled via
  explicit human override (`max_duration_minutes: 120`, reason
  logged). Phase 1.5's machine-enforced gate confirmed the override
  was respected (acceptance evidence: PASS).
- **D13** — memory-cli at `../memory-cli/` (sibling); registry pinned
  to contract_version 1.0; tool_version bumped 0.1.0-alpha →
  0.2.0-beta. Implementation evolved; contract did not (envelope
  shape stable).

## What's next

| Phase | Adds |
|-------|------|
| **2.1b** | `search` (FTS5 BM25 + filters) + `get` (by id, with body + tags + supersession) + `list` (filter by type/confidence/tag/since/sort) |
| **2.2** | `learn` (single-doc add) + `tag` + `supersede` + `reflect`; **`ai rrr` calls `memory-cli learn`** after writing canonical retro — Knowledge Brain grows automatically |
| **2.3** | `delete` (rare) + `reindex` (rebuild) + `health` verb (DB integrity); integration with `lll/vvv/nnn` per spec §11 (vvv searches past incidents; nnn pulls memory hints) |
| **Phase 4** | Real Pyramid layer 1 verifier rules (replaces `step_complete` stub) |
| **Phase 5** | Goal tree + `ai loop` namespace + `ai ddd` proper (replaces `--auto-deploy` flag) |

## Open follow-ups

| ID | Description | Priority |
|----|-------------|----------|
| **R5** | `test_basic` should accept `idle | busy` | low |
| **R7** | `ai nnn --plan-envelope <relative>` resolve from project_root | low |
| **R8** | `tools-policy.yaml::supported_contract_versions` may need pre-1.0 markers | medium |
| **R9/R10/R11** | (closed Session E — `ai rrr` executable gate shipped) | done |
| **R12** | `ai ddd` proper CLI (Phase 5); replaces `--auto-deploy` flag | medium |
| **R13** | `ai rrr --baseline <commit>` for forbidden_diff (currently always HEAD) | low |
| **R14** | One-shot `ai rrr --retroactive --session <id>` for archived sessions A–D | low |
| **R15 (new)** | Tool registry should pin `engines.node` per tool contract — sibling tools may drift Node versions independently | medium |

## Cross-references

- Memory-cli twin: [`.ai/memory/retros/0007_2026-04-30_10_32_pm_feat-phase2-1a-memory-cli-indexer.md`](../../.ai/memory/retros/0007_2026-04-30_10_32_pm_feat-phase2-1a-memory-cli-indexer.md)
- Phase 1.5 retro (executable gate): [`09_PHASE1_5_RRR_EXECUTABLE_GATE.md`](09_PHASE1_5_RRR_EXECUTABLE_GATE.md)
- Phase 2 alpha retro: [`08_PHASE2_MEMORY_CLI_ALPHA.md`](08_PHASE2_MEMORY_CLI_ALPHA.md)
- Spec: [`../specs/05_MEMORY_CLI_SPEC.md`](../specs/05_MEMORY_CLI_SPEC.md)
- Frozen baseline: [`../contracts/memory-cli/COMMAND_CONTRACT.md`](../contracts/memory-cli/COMMAND_CONTRACT.md)
- Tool source: `../memory-cli/` (sibling repo)
- Audit chain (live): `.ai/audit/events.ndjson` (depth ~153 at session close)
