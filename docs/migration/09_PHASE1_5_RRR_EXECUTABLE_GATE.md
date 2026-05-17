---
title: "Retro — Session E: Phase 1.5 ai rrr executable gate"
status: locked
last-updated: 2026-04-30
audience: "Trinity team + future Phase 2.1+ sessions"
session-window: "2026-04-30 (single session, ~10 min wall by chain metrics)"
session-id: "0001_2026-04-30_21_53_pm_feat-phase1-5-rrr-executable-gate"
acceptance-evidence: PASS
rrr-contract: PASS
audit-events-added: 30
---

# Session E — Phase 1.5: `ai rrr` executable gate

> **First session in Trinity history with `RRR contract: PASS` verified
> by machine, not self-report.** Closes the gap that Sessions A–D
> closed with `RRR contract: PARTIAL`.

## Scope

Implement `ai rrr` as a **machine-enforced terminal gate**:

1. pull audit slice for the session from the chain
2. compute metrics from the chain
3. parse + execute `THINK/03_ACCEPTANCE.yaml` commands (R11)
4. detect forbidden-path diff vs HEAD baseline
5. write `THINK/RETRO.md` (R9 part 1) + `.ai/memory/retros/<seq>_*.md` (R9 part 2)
6. append `rrr.completed` audit event
7. fire `RETRO → DONE`
8. exit non-zero if any required acceptance fails

R9 + R10 + R11 bundled and shipped together.

## Metrics

| Dimension | Value |
|-----------|-------|
| Files NEW | 5 (`commands/rrr.py`, `core/{acceptance,metrics,forbidden_diff}.py`, `tests/test_rrr.py`) |
| Files MODIFY | 2 (`commands/nnn.py` adds `03_ACCEPTANCE.yaml` writer; `cli/main.py` registers `ai rrr`) |
| Session NEW | 1 (`THINK/03_ACCEPTANCE.yaml` — first real R11 example) |
| LOC actual | ~870 (Python) — close to the ~870 of Phase 1, in less wall time |
| Tests added | 19 (test_rrr.py): acceptance executor (7), forbidden_diff (5), metrics (3), rrr render helpers (4) |
| Tests passing | 94 / 94 (after close) — was 75 / 75 before this session |
| Audit events added | 30 (chain depth 84 → 117 + closure) |
| Spec changes | 0 |
| Locked decisions enforced | D1, D2, D9, D10, D11 |
| Locked decisions consumed | R9 (both retros), R10 (ai rrr CLI), R11 (executable acceptance) |

## What worked

**The acceptance gate caught the gap it was built for, on its own
work.** Session A–D's RRR contract was PARTIAL because no system ran
A6/A7 boundary commands; Session E ran them in subprocess at session
close, both green. The first session with an enforceable verdict
verified its own enforceability.

**Self-host smoke validated the runtime end-to-end.** After step 8
(THINK/03_ACCEPTANCE.yaml authored), step 9 invoked
`ai rrr --auto-deploy --dry-run` against this very session. Result:

```
Acceptance gate          7/7 PASS
forbidden-path diff:     ✅ none
Session metrics          30 events / 6 transitions / 9 iterations
                         {"PASS": 9} verdicts / 0 NEEDS_HUMAN
Final graph_state        DEPLOYED (dry-run; not yet RETRO→DONE)
DRY-RUN gate: PASS
```

Then `ai rrr --auto-deploy` (no flag) fired the real gate, landed at
`graph_state=DONE`, with both verdicts machine-verified. The runtime
built itself, then verified itself.

**Schema-first acceptance forced explicit thinking.** Writing
`THINK/03_ACCEPTANCE.yaml` for this session surfaced 7 distinct
acceptance items (file existence, pytest pass, CLI registration,
spec-untouched, forbidden-paths-untouched). Previous sessions
implicitly verified some of these in the retro prose; now they're
machine-checked at session close.

**`metrics_for_session` reads the chain, not session_state.json.**
Audit chain is the source of truth (D9). The metrics function filters
events by `session_id` and aggregates — same data the retro shows.
This makes the retro frontmatter (`acceptance-evidence: PASS`) provable
from the chain alone, no metadata-store dependency.

**R9 decision (write both retros) showed its value immediately.** The
session-local `THINK/RETRO.md` lives with the capsule (auditors
reading the session see the retro). The `.ai/memory/retros/0006_*.md`
copy lands in the canonical memory index, ready for memory-cli's
`learn` verb (Phase 2.2). Different audiences, both served.

## What surprised

**Dry-run leaked a memory retro on first run.** First implementation
wrote both files even with `--dry-run`. First dry-run minted memory
retro `0005`; real run minted `0006`. Cleaned up: deleted `0005`,
patched `rrr.py` to skip memory copy on dry-run. Session-local copy is
fine to overwrite on each preview; canonical memory must only exist
for runs that fired RETRO→DONE. A version of the test harness should
prevent this regression.

**`git status --porcelain` collapses untracked directories by
default.** Three of the first forbidden_diff tests failed because
`?? .ai/` was the only untracked entry, hiding `.ai/policies/file.yaml`
underneath. `--untracked-files=all` fixes this. Lesson recorded.

**`subprocess.TimeoutExpired.stdout` returns `bytes`, not `str`,**
even when `subprocess.run(text=True, capture_output=True, timeout=...)`
is used. Acceptance executor handles both via isinstance.

**LOC (~870) was on par with Phase 1, in less wall time** (~10 min by
audit-chain metrics vs Phase 1's ~25 min). The agent re-used patterns
from Phase 1 (typer command, AuditChain, F5 merge-safe state writes,
Loop.fire) — building velocity is real.

## What broke (along the way)

| Issue | When | Fix |
|-------|------|-----|
| 3 forbidden_diff tests failed (untracked dir collapse) | first pytest of test_rrr | `git status --porcelain --untracked-files=all` |
| Dry-run minted stale memory retro 0005 | first dogfood run | patched `rrr.py` to skip memory copy on --dry-run; deleted 0005 |
| `test_basic.test_state_initialized` fail under active session | post-gogogo pytest | pre-existing R5 brittleness; resolves on close |

## Decisions enforced

- **D1** — `ai rrr` itself enforces this now. The forbidden-diff check
  refuses to fire RETRO→DONE if `.ai/policies/`, `.ai/schemas/`,
  `docs/specs/`, `references/`, or non-events.ndjson `.ai/audit/` paths
  changed since HEAD. Boundary moved from "agent remembers not to" to
  "kernel refuses to close the session".
- **D2** — every transition this session had explicit `decided_by`.
  Acceptance commands run in subprocess (deterministic); LLM judgment
  not invoked.
- **D9** — chain grew 84 → 117+. `chain.validate()` OK throughout.
  Metrics computed from chain, not session_state.
- **D10** — `Loop.fire` enforced authorities. `--auto-deploy` flag
  fires `promote_request` + `deploy_request` with `decided_by=human`
  (the user invoking ai rrr is the human; opt-in via flag, not
  default).
- **D11** — budget breach (75 vs 30 default = 2.5×) handled via
  explicit human override (`max_duration_minutes: 90`, reason
  logged). nnn refused without override, accepted with override.

## Decisions newly resolved

| ID | Resolution |
|----|------------|
| **R9** | `THINK/RETRO.md` (session-local) + `.ai/memory/retros/<seq>_*.md` (canonical memory) — both written by `ai rrr`. Done. |
| **R10** | `ai rrr` CLI exists and is the terminal gate. Done. |
| **R11** | `THINK/03_ACCEPTANCE.yaml` (executable) is the source of truth; `nnn` writes it from envelope.acceptance; `rrr` reads + executes it. Done. |

## Verdict notation (locked from this session forward)

```
Acceptance evidence: PASS | PARTIAL | FAIL
RRR contract:        PASS | PARTIAL | FAIL
```

Both lines now have machine-verifiable definitions:

- **Acceptance evidence** = every required item in
  `THINK/03_ACCEPTANCE.yaml` returned the expected exit + stdout.
- **RRR contract** = acceptance evidence PASS **and** forbidden-path
  diff has zero violations **and** `ai rrr` fired `RETRO → DONE` (i.e.
  the gate completed without aborting).

Sessions A/B/C/D remain `RRR contract: PARTIAL` permanently. Audit
chain is honest. R14 (open) considers a `--retroactive` mode for
re-running the gate against archived sessions, but that is opt-in
introspection, not history rewriting.

## What's next

| Phase | Adds |
|-------|------|
| **2.1** | SQLite + FTS5 schema; markdown parser; verbs `index/search/list/get` |
| **2.2** | Verbs `learn/tag/supersede/reflect`; `ai rrr` calls `memory-cli learn` after writing the canonical retro |
| **2.3** | Verbs `delete/reindex/health` (verb); integration with `lll/vvv/nnn` per spec §11 |
| **Phase 4** | Real Pyramid layer 1 verifier rules (replaces `step_complete` stub) |
| **Phase 5** | Goal tree + `ai loop` namespace + `ai ddd` proper (replaces `--auto-deploy` flag); non-deploy graph variant |

## Open follow-ups

| ID | Description | Priority |
|----|-------------|----------|
| **R5** | `test_basic` should accept `idle | busy` | low |
| **R6** | (closed Session C — Loop init reconciles graph_state vs audit) | done |
| **R7** | `ai nnn --plan-envelope <relative>` resolve from project_root | low |
| **R8** | `tools-policy.yaml::supported_contract_versions` may need pre-1.0 markers | medium |
| **R9/R10/R11** | (closed THIS session — see "Decisions newly resolved" above) | done |
| **R12 (new)** | `ai ddd` proper CLI (Phase 5) — current `--auto-deploy` flag is a kernel-session convenience, not real ddd | medium |
| **R13 (new)** | `ai rrr --baseline <commit>` for forbidden_diff (currently always HEAD) — useful for multi-commit sessions | low |
| **R14 (new)** | One-shot `ai rrr --retroactive --session <id>` to re-run gate against archived sessions A–D | low |

## Cross-references

- Memory-cli twin: [`.ai/memory/retros/0006_2026-04-30_10_03_pm_feat-phase1-5-rrr-executable-gate.md`](../../.ai/memory/retros/0006_2026-04-30_10_03_pm_feat-phase1-5-rrr-executable-gate.md)
- Phase 2 alpha (where R9/R10/R11 were locked): [`08_PHASE2_MEMORY_CLI_ALPHA.md`](08_PHASE2_MEMORY_CLI_ALPHA.md)
- Phase 1 retro: [`07_PHASE1_GOAL_LOOP_RUNTIME.md`](07_PHASE1_GOAL_LOOP_RUNTIME.md)
- rrr SHIM: [`.ai/shims/rrr/SHIM.md`](../../.ai/shims/rrr/SHIM.md)
- Audit chain (live): `.ai/audit/events.ndjson` (depth ~118 at session close)
