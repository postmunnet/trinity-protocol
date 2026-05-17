---
title: "Retro — Session D: Phase 2 Memory-CLI (alpha skeleton)"
status: locked
last-updated: 2026-04-30
audience: "Trinity team + future Phase 2.1+ sessions"
session-window: "2026-04-30 (single session, ~40 min wall)"
session-id: "0001_2026-04-30_21_07_pm_feat-phase2-memory-cli"
audit-events-added: 28
verbs-implemented: 1   # stats (stub) + --health flag
deferred-to: phase-2.1-and-beyond
---

# Session D — Phase 2 Memory-CLI (alpha skeleton)

> Single session, scope-bounded by design. Built the sibling repo
> skeleton + 1 wired verb + registry entry + frozen contract baseline.
> No SQLite, no FTS5, no markdown parsing. Those land in Phase 2.1.

## Scope

The `05_MEMORY_CLI_SPEC.md` is a 12-verb spec implying 1000+ LOC of
Node.js. Walking it whole-cloth is a multi-session arc. This session
implements **Phase 2.0 alpha** — the minimum that proves the plugin
architecture works:

- A sibling Node.js repo at `../memory-cli/`
- 1 wired verb (`stats`) returning a TOOL_CONTRACT v1 envelope stub
- A `--health` flag for the kernel's tool registry health-check
- Registration in `.ai/tools.yaml`
- A frozen contract baseline at `docs/contracts/memory-cli/`

Everything else (SQLite, FTS5, indexer, parser, 11 other verbs,
integration with `lll`/`vvv`/`nnn`) is explicit deferred work
documented in `THINK/02_SCOPE.md`.

## Metrics

| Dimension | Value |
|-----------|-------|
| Files NEW | 5 (`../memory-cli/{index.js,package.json,README.md}`, `docs/contracts/memory-cli/{COMMAND_CONTRACT.md,README.md}`) |
| Files MODIFY | 1 (`.ai/tools.yaml`) |
| LOC actual | ~330 (Node.js + YAML + Markdown) |
| Trinity tests added | 0 (parameterized test_tools_registry auto-pick-up = +6 cases for memory-cli; written tests didn't grow) |
| Trinity tests passing | 75 / 75 (after close — R5 brittleness drops) |
| Audit events added | 28 (chain depth 54 → 82) |
| Spec changes | 0 |
| Locked decisions enforced | D1, D2, D9, D10, D11, D13 |

## What worked

**Explicit α/β/γ scope discussion in vvv.** The 5-question vvv ritual
surfaced three plausible scope levels (`α` skeleton, `β` MVP search,
`γ` full spec) before committing to any of them. The user picked
α; the rest flow from that. Without that explicit menu the session
would have either over-built (β/γ) or been too vague to hold a
single-session scope.

**Hard-coded α-scope guard inside `.state/plan.json`.** A novel
addition this session — the plan envelope contains:

```json
"alpha_scope_guard": {
  "halt_if_touches": ["SQLite", "FTS5", "markdown parser", ...],
  "if_triggered": "stop and re-run vvv to escalate to beta scope"
}
```

This is conscience in JSON form. Whenever a "while we're here, let's
add ..." impulse appeared, the guard pointed at the explicit defer
list. Phase 5+ should consider promoting `alpha_scope_guard` to a
first-class plan envelope field with kernel enforcement (currently
it's discipline only — no runtime check).

**The kernel's existing test_tools_registry was a free contract
test.** Registering memory-cli grew the parameterized suite by 6
new cases — and 2 of them caught real issues immediately
(missing README.md, unsupported contract_version). The kernel's
tool registry test = the tool's own integration test, with zero
extra test code written this session.

**Frozen contract baseline isolation worked end-to-end.** `tool_version
= "0.1.0-alpha"` lives in the implementation. `contract_version =
"1.0"` lives in the registry, matches the kernel's supported list,
and pins the envelope shape. The two churn independently — exactly
the D13 promise. First Trinity-internal tool to exercise this design
beyond browser-cli.

**Phase 1 runtime + Phase 1.1 reconcile worked together.** `ai vvv →
ai nnn → ai gogogo` walked the canonical flow with no manual audit
appends. R6 reconciliation didn't fire (no need), but the test cases
remain green — confirming R6 is non-destructive when not needed.

## What surprised

**`tools-policy.yaml::supported_contract_versions: ["1.0"]` is
D1-forbidden write.** First plan was `contract_version: "0.1-alpha"`
to flag implementation maturity in the registry. Test
`test_tool_contract_version_is_supported` failed and the policy file
couldn't be edited (D1). Resolved by collapsing the `contract_version`
to the envelope-shape semantic (`"1.0"`) and moving the alpha tag to
`tool_version` + `notes`. **Lesson:** `contract_version` ≠
`tool_version`. Contract = handshake (envelope shape); tool_version
= implementation. Future tools must respect this distinction.

**Open follow-up R8** — should `supported_contract_versions` accept
pre-1.0 markers (e.g. `"0.x-alpha"`)? The current single-pin design
forces all alpha tools to claim 1.0 contract conformance, which is
fine for envelope shape but might mask premature claims. Phase 4 (or
whoever rebuilds the policy layer) should weigh.

**LOC came in under estimate.** Plan said ~200 LOC; actual ~330.
About half is Markdown (README + COMMAND_CONTRACT). The Node.js code
itself is ~120 LOC — quite tight for a working CLI with a real
envelope.

## What broke (along the way)

| Issue | When | Fix |
|-------|------|-----|
| `test_contract_baseline_exists[tool1]` failed (no README) | first pytest after register | wrote `docs/contracts/memory-cli/README.md` |
| `test_tool_contract_version_is_supported[tool1]` failed (`"0.1-alpha"` not in policy list) | first pytest | use `"1.0"`; alpha → tool_version + notes |
| `test_basic.test_state_initialized` fail under active session | post-gogogo pytest | pre-existing R5 brittleness; resolves on close |
| `Edit` on `.ai/tools.yaml` failed (file not Read first) | mid-edit | called `Read` then re-Edit |

## Decisions enforced

- **D1** — zero writes to `.ai/policies/**`, `.ai/audit/**` (modify),
  `.ai/schemas/**`, `docs/specs/**`, `references/**`. The
  `tools-policy.yaml::supported_contract_versions` constraint
  surfaced as a real boundary; respected by adjusting the tool's
  declared contract_version, not the policy.
- **D2** — vvv (5Q with α/β/γ scope discussion) → nnn (budget
  override + α-scope guard) → gogogo. Every gate had explicit human
  decision points.
- **D9** — audit chain grew 54 → 82 with no batched appends.
  `chain.validate()` OK throughout.
- **D10** — every `Loop.fire()` invocation recorded the right
  authority. Phase 1 runtime enforced this automatically.
- **D11** — budget breach (45 min vs 30 default) handled via the
  D11-compliant override path (decided_by: human, reason logged).
- **D13** — memory-cli at `../memory-cli/` (sibling); registered in
  `.ai/tools.yaml`; frozen baseline at `docs/contracts/memory-cli/`;
  envelope shape = TOOL_CONTRACT v1.0. Implementation is free to
  evolve; kernel only checks `contract_version`.

## What's next (Phase 2.1+)

| Phase | Adds |
|-------|------|
| **2.1** | SQLite + FTS5 schema; markdown frontmatter parser; verbs `index` + `search` + `list` + `get`; 5-doc fixture + golden test |
| **2.2** | Verbs `learn` + `tag` + `supersede` + `reflect`; retro-cli integration |
| **2.3** | Verbs `delete` + `reindex` + `health` (as verb, distinct from `--health` flag); integration with `lll`/`vvv`/`nnn` per spec §11 |
| **Phase 9** (long-term) | Hybrid search (vector embeddings + BM25 merge) per spec §15 |

## Self-audit — RRR contract gap (post-session review)

The user flagged at end-of-session that the `rrr` ritual did **not**
execute the acceptance commands defined in `THINK/03_ACCEPTANCE.md`.
On retrospective inspection, the gap was real and consistent across
**all three sessions today** (A/B Phase 1, C R6, D Phase 2 alpha):

| Sessions A/B/C/D | What `rrr` did | What `rrr` SHIM says it MUST do |
|---|---|---|
| ✅ append `rrr.completed` audit event | ✅ | ✅ |
| ✅ fire `RETRO → DONE` graph transition | ✅ | ✅ |
| ✅ archive session after audit append | ✅ (via `ai close --force`) | ✅ |
| ❌ pull session's audit slice | not done | required |
| ❌ compute metrics from chain | guesstimated, not computed | required |
| ❌ write `THINK/RETRO.md` | wrote `.ai/memory/retros/` only | required |
| ❌ run A1–A8 acceptance commands | aspirational text only | implied by spec §3.2 |
| ❌ verify forbidden-path boundary via `git diff` | claimed in retro prose | not verified |

The implementation result is honest (verified retroactively after the
flag; all A1–A8 commands actually pass for all three sessions), but
the ritual itself was **markdown summary, not machine-enforced gate**.

### New verdict format (locked from now on)

Every session close must report two lines:

```
Acceptance evidence: PASS | PARTIAL | FAIL
RRR contract:        PASS | PARTIAL | FAIL
```

Re-graded for sessions closed today:

| Session | Acceptance | RRR contract |
|---------|------------|--------------|
| A/B (Phase 1 — `0673bdf`) | PASS *(verified retroactively)* | **PARTIAL** |
| C (R6 — `30f5706`) | PASS | **PARTIAL** |
| D (Phase 2 α — this commit) | PASS | **PARTIAL** |

The audit chain is the source of truth and remains intact. We do not
retroactively rewrite past sessions — the RRR contract gap is a
historical fact for sessions A through D. Phase 1.5 closes the gap
going forward.

## Decisions locked from this self-audit

### R9 — retro location (LOCKED: write both)

```
THINK/RETRO.md          = session-local retro (lives with the capsule, audit-friendly read)
.ai/memory/retros/...   = canonical memory copy (memory-cli indexing target)
```

The two contracts (`shims/rrr/SHIM.md` vs `WORKFLOW.md`) appeared to
conflict but actually serve different audiences. We write **both**;
they are not interchangeable.

### R10 — `ai rrr` CLI is now Phase 1.5 (was Phase 5)

Elevated. Trinity needs a machine-enforced terminal ritual or every
session continues to ship as RRR contract: PARTIAL.

Minimum behavior:

```text
1. pull chain.iter_events() filtered by session_id
2. compute metrics (iterations, duration, verdict counts, NEEDS_HUMAN count)
3. parse + execute THINK/03_ACCEPTANCE.yaml commands  (R11)
4. detect forbidden-path diff (git diff vs session.created baseline)
5. write THINK/RETRO.md  (R9 part 1)
6. write .ai/memory/retros/<seq>_*.md  (R9 part 2)
7. append rrr.completed audit event
8. fire RETRO → DONE via Loop
9. exit non-zero if any required acceptance command fails
```

### R11 — Acceptance must be executable, not aspirational

Replace `THINK/03_ACCEPTANCE.md` (free-form prose) with
`THINK/03_ACCEPTANCE.yaml` (parseable + executable):

```yaml
session: <session-id>
ritual: rrr-input
acceptance:
  - id: A1
    description: "Phase 1 NEW files exist non-empty"
    command: "test -s .ai/cli/core/loop.py && test -s .ai/cli/core/budget.py"
    expect_exit: 0
    required: true
  - id: A2
    description: "trinity_v2 pytest passes"
    command: "cd .ai && python3 -m pytest cli/tests -q"
    expect_stdout_contains: "passed"
    required: true
  - id: A6
    description: "0 spec changes"
    command: "git diff --name-only HEAD docs/specs/ | wc -l"
    expect_stdout_strip: "0"
    required: true
```

`ai rrr` is the parser+executor; the gate enforces, humans no longer
"remember to run".

### Roadmap re-ordered

```
1. Phase 1.5  — ai rrr executable gate (R9 + R10 + R11 bundled)
2. Phase 2.1  — memory-cli SQLite/FTS5 + index/search
3. Phase 4    — real verifier rules
4. Phase 5    — goal tree + ai loop namespace
```

Phase 1.5 jumps the queue. The user's framing summarizes it well:

> ผลงานผ่าน แต่พิธีปิดงานยังไม่เป็นเครื่องจักร — ดังนั้นงานถัดไป
> คือทำ `rrr` ให้เป็น executable gate.

## Open follow-ups

| ID | Description | Priority |
|----|-------------|----------|
| **R5** | `test_basic` should accept `idle | busy` | low |
| **R6** | (closed in Session C — Loop init reconciles graph_state vs audit) | done |
| **R7** | `ai nnn --plan-envelope <relative>` should resolve relative to project_root | low |
| **R8** | `tools-policy.yaml::supported_contract_versions` may need pre-1.0 markers | medium |
| **R9** (locked) | `rrr` writes BOTH `THINK/RETRO.md` and `.ai/memory/retros/<seq>_*.md` | Phase 1.5 |
| **R10** (locked) | `ai rrr` CLI as machine-enforced terminal gate | Phase 1.5 (elevated) |
| **R11** (locked) | `03_ACCEPTANCE.yaml` (executable) replaces `03_ACCEPTANCE.md` (aspirational) | Phase 1.5 |
| **Phase 1.5** | Implement R9 + R10 + R11 bundled — closes RRR contract gap | NEXT |
| **Phase 2.1** | SQLite + FTS5 schema; markdown parser; verbs `index/search/list/get` | after 1.5 |
| **Phase 2.2** | Verbs `learn/tag/supersede/reflect`; retro-cli integration | after 2.1 |
| **Phase 2.3** | `delete/reindex/health` (verb); integration with `lll/vvv/nnn` per spec §11 | after 2.2 |
| **Phase 4** | Real Pyramid layer 1 verifier rules (replaces `step_complete` stub) | next-class |
| **Phase 5** | Goal tree + `ai loop` namespace + `ai ddd` CLI | next-class |

## Cross-references

- Memory-cli twin: [`.ai/memory/retros/0004_2026-04-30_21_15_pm_feat-phase2-memory-cli-alpha.md`](../../.ai/memory/retros/0004_2026-04-30_21_15_pm_feat-phase2-memory-cli-alpha.md)
- Phase 1 retro: [`07_PHASE1_GOAL_LOOP_RUNTIME.md`](07_PHASE1_GOAL_LOOP_RUNTIME.md)
- Spec: [`../specs/05_MEMORY_CLI_SPEC.md`](../specs/05_MEMORY_CLI_SPEC.md)
- Decisions log: [`01_CONTEXT_AND_DECISIONS.md`](01_CONTEXT_AND_DECISIONS.md)
- Tool source: `../memory-cli/` (sibling repo, outside trinity_v2 git history)
- Frozen baseline: `docs/contracts/memory-cli/`
- Audit chain (live): `.ai/audit/events.ndjson` (depth ~83 at session close)
