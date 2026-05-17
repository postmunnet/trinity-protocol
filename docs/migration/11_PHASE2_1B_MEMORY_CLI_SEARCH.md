---
title: "Retro — Session G: Phase 2.1b memory-cli search/get/list"
status: locked
last-updated: 2026-04-30
audience: "Trinity team + future Phase 2.2+ sessions"
session-window: "2026-04-30 (single session)"
session-id: "0001_2026-04-30_22_46_pm_feat-phase2-1b-memory-cli-search"
acceptance-evidence: PASS
rrr-contract: PASS
audit-events-added: 35
---

# Session G — Phase 2.1b: memory-cli search / get / list

> **Third session in Trinity history with `RRR contract: PASS`
> verified by machine.** Knowledge Brain is now queryable: `search`
> (FTS5 BM25 + filters + snippets), `get` (full doc + tags +
> supersession), `list` (filter + sort + paginate). 5 of 12 spec verbs
> wired; `learn` ships in 2.2 to close the `ai rrr → memory-cli`
> auto-feed loop.

## Scope

Wire 3 query verbs in memory-cli (`search`, `get`, `list`); keep
trinity_v2 kernel untouched (D13). No `learn` (2.2) or `delete`/
`reindex`/`health-verb` (2.3) — `alpha_scope_guard` enforced.

## Metrics

| Dimension | Value |
|-----------|-------|
| Files NEW (sibling memory-cli/) | 3 lib + 3 tests = 6 |
| Files MODIFY (sibling) | 2 (`index.js`, `package.json`) |
| Files MODIFY (trinity_v2) | 2 (`tools.yaml`, `COMMAND_CONTRACT.md`) |
| memory-cli LOC delta | ~620 (Node.js + tests) |
| trinity_v2 LOC delta | ~140 (registry + contract baseline) |
| memory-cli tests total | 33 (was 11; +22 — search 9, get 4, list 9) |
| trinity_v2 pytest | 94/94 (after close) — no regression |
| Audit events added | 35 (chain depth 153 → 188) |
| Spec changes | 0 |
| Sessions with `RRR contract: PASS` (lifetime) | 3 (E, F, G) |
| Locked decisions enforced | D1, D2, D9, D10, D11, D13 |

## What worked

**Three verbs in one session paid off.** `search`, `get`, `list`
share infrastructure — DB join with tags, filter builder pattern,
`includeSuperseded` default. Splitting would have duplicated
boilerplate; bundling kept the surface area cohesive at ~620 LOC in
~75 min wall time, well under the 180-min override.

**Phase 2.1a's standalone FTS5 paid dividends in 2.1b.** Direct
`SELECT … WHERE documents_fts MATCH ?` joined to documents on
`document_id` text key. No content= shadow rowid juggling. BM25
ranking is one `bm25(documents_fts) AS score` expression. The
"slightly more disk vs simpler invariants" tradeoff from 2.1a was
the right call.

**Sanitizer + parameterized queries blocked FTS5 injection cleanly.**
`sanitizeQuery` strips `^"():*` before binding; the test
`search: query with only special chars sanitizes to empty` proves
input `*"():^` returns no crash, no leak, just `[]` results.

**Filter combinatorics built piece-by-piece.** Each filter (type,
confidence, tag, since) pushes to a `where[]` array + `params[]`;
final SQL joins with ` AND `. No string concatenation of user input.
The `tag` filter uses a correlated subquery
(`EXISTS (SELECT 1 FROM tags WHERE …)`) which is cleaner than the
JOIN+DISTINCT alternative.

**Acceptance gate caught a brittle JSON grep.** A3 originally piped
`get` output through `grep -E '"(bugfix|ui|modal|css)"' | wc -l`
expecting 4 lines — but tags appear twice in the output (once in
`data.tags`, once in `data.metadata.tags`), so grep returned 8.
DRY-RUN gate: FAIL. Fixed in 1 min by switching to
`python3 -c 'json.load → len(d["data"]["tags"])'`. Phase 1.5's gate
keeps preventing self-deception even on minor lints.

## What surprised

**Snippet rendering needed manual implementation.** FTS5's built-in
`snippet()` function operates on column indexes and uses opinionated
delimiters. Hand-rolled `buildSnippet` (~30 LOC) lets us control
ellipsis, max length, and whitespace collapse for predictable output
in retro lookups.

**`since` filter sorts by lex string compare on ISO dates.** Works
because ISO 8601 strings sort the same lexically as they would as
dates. No alter table needed. The indexer normalizes input dates so
this assumption holds.

**LOC came in under estimate.** Plan said ~640 LOC; actual ~620.
`lib/get.js` is only ~70 LOC because the supersession join is two
small queries, not a fancy CTE. Sometimes simple is honest.

## What broke (along the way)

| Issue | When | Fix |
|-------|------|-----|
| A3 brittle grep on JSON (counted tags+metadata.tags = 8 not 4) | first ai rrr dry-run | switch to `python3 -c json.load` |
| `test_basic` fail under active session | post-gogogo pytest | pre-existing R5 brittleness; resolves on close |

## Decisions enforced

- **D1** — `ai rrr` forbidden_diff: 0 violations at session close.
- **D2** — vvv (5Q) → nnn (executable acceptance + budget override) →
  gogogo → rrr. Every gate human-decided.
- **D9** — chain grew 153 → 188 with no batched appends;
  `chain.validate()` OK throughout.
- **D10** — `Loop.fire` enforced authorities; `--auto-deploy` fires
  promote/deploy with decided_by=human.
- **D11** — budget breach (120 vs 30 default = 4×) handled via
  explicit human override (`max_duration_minutes: 180`, reason
  logged).
- **D13** — memory-cli at `../memory-cli/`; tool_version bumped
  0.2.0-beta → 0.3.0-beta; `contract_version` stays 1.0 (envelope
  shape unchanged). Contract baseline updated with §2.3-2.5.

## What's next

| Phase | Adds |
|-------|------|
| **2.2** | `learn` + `tag` + `supersede` + `reflect`; **`ai rrr` calls `memory-cli learn`** after writing canonical retro — the Knowledge Brain auto-grows on every closed session |
| **2.3** | `delete` + `reindex` + `health` (verb); integration with `lll/vvv/nnn` per spec §11 (vvv pulls past incidents; nnn pulls memory hints) |
| **Phase 4** | Real Pyramid layer 1 verifier rules (replaces `step_complete` stub) |
| **Phase 5** | Goal tree + `ai loop` namespace + `ai ddd` proper |

## Open follow-ups

| ID | Description | Priority |
|----|-------------|----------|
| **R5** | `test_basic` should accept `idle | busy` | low |
| **R7** | `ai nnn --plan-envelope <relative>` resolve from project_root | low |
| **R8** | `tools-policy::supported_contract_versions` may need pre-1.0 markers | medium |
| **R9/R10/R11** | (closed Session E — `ai rrr` shipped) | done |
| **R12** | `ai ddd` proper CLI (Phase 5); replaces `--auto-deploy` flag | medium |
| **R13** | `ai rrr --baseline <commit>` for forbidden_diff | low |
| **R14** | `ai rrr --retroactive --session <id>` for archived A–D | low |
| **R15** | Tool registry should pin `engines.node` per tool contract | medium |

## Cross-references

- Memory-cli twin: [`.ai/memory/retros/0008_2026-04-30_10_52_pm_feat-phase2-1b-memory-cli-search.md`](../../.ai/memory/retros/0008_2026-04-30_10_52_pm_feat-phase2-1b-memory-cli-search.md)
- Phase 2.1a (indexer): [`10_PHASE2_1A_MEMORY_CLI_INDEXER.md`](10_PHASE2_1A_MEMORY_CLI_INDEXER.md)
- Phase 1.5 (executable rrr): [`09_PHASE1_5_RRR_EXECUTABLE_GATE.md`](09_PHASE1_5_RRR_EXECUTABLE_GATE.md)
- Spec: [`../specs/05_MEMORY_CLI_SPEC.md`](../specs/05_MEMORY_CLI_SPEC.md)
- Frozen baseline: [`../contracts/memory-cli/COMMAND_CONTRACT.md`](../contracts/memory-cli/COMMAND_CONTRACT.md)
- Tool source: `../memory-cli/` (sibling repo)
- Audit chain (live): `.ai/audit/events.ndjson` (depth ~189 at session close)
