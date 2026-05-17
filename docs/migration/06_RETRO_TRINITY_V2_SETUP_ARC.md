---
title: "Retro — Session A: trinity_v2 setup + runtime gap fixes"
status: locked
last-updated: 2026-04-30
audience: "Trinity team + future migration sessions"
session-window: "2026-04-28 (Commit 0) → 2026-04-30 (F1+F3+F4+F5 fixes)"
commits-included:
  - 868017f init
  - 6958005 docs(migration)
  - e689eb8 docs(ai-entry)
  - 23d0b17 commit1: make core runnable
  - ce6be2f commit2: Phase 0.5 stubs
  - 3b74574 commit3: v2 workflow
  - fef01d6 commit4: browser-cli contract baseline
  - c72934e commit4.5: plugin tool registry (D13)
  - 23d09c1 commit5: Knowledge Brain (D6)
  - 152b7ac commit6: shim foundation (D7)
  - 0c7ee1f commit7: brain seed + external refs
  - 88fb253 fix(verify): F2 — exclude references/ from secret scan
  - 4a272b4 fix(runtime): F1+F3+F4+F5 — audit chain, archive path, counters, timestamps
---

# Session A — Retrospective

> 13 commits, 11 days of conversation, 4 vvv-level decisions added (D6, D7,
> D12, D13), one full E2E test pass over the runtime. Setup arc closed.

## Scope

Stand up `trinity_v2/` as a clean canonical bootstrap repo by selectively
porting from `TRINITY_LEGACY/`, `<upstream-project>/`, `browser-cli/`, and
`ai-docs/` — sanitized at every step so the result is **generic, not a
<upstream-project> clone**.

## Metrics

| Dimension | Value |
|-----------|-------|
| Commits | 13 (11 setup + 2 runtime fixes) |
| Files tracked | ~1230 |
| Repo size | 22 MB |
| Tests passing | 57 / 57 |
| Locked decisions added | 4 (D6, D7, D12, D13) |
| Spec changes | 0 (all fixes were impl drift vs existing spec) |
| E2E session | 6-event audit chain, fully validated |
| Pyramid layers wired | 1 of 4 (deterministic — verifier-rules.yaml stub) |
| Short codes implemented runtime | 0 of 7 (all canonical SHIM.md only) |

## What worked

**vvv before any commit.** Every architecture-touching decision (Option C
plugin registry, ai-docs sanitization scope, runtime gap fixes) was
preceded by 5-question understanding + spec impact analysis. Caught
mismatches early — e.g., `B1-B4 was MYTH` discovered before any port
work, saved an unnecessary commit.

**Spec impact analysis as a default.** User's Q3 "เสนอส่วนต่างมาก่อน"
forced us to articulate **what changes if we do this** vs **what
breaks if we don't**. Result: every fix in this session ended up
needing **0 spec changes** — confirming the spec was right and runtime
was just behind.

**E2E test before commit (Q4).** F1+F3+F4+F5 ran the full lifecycle
once before the single atomic commit. Caught `created_at` clobber on
the second state transition — would have been a hidden regression
otherwise.

**Sequencing simplest-first.** F4 (counter key path bug) → F5 (state
merge) → F3 (archive path) → F1 (audit chain). When the largest fix
(F1) landed, everything else was already stable, so debugging was
isolated to the new code.

**Hybrid session boundaries (Q5).** Setup arc + runtime fixes in one
session; Phase 1 (Goal Loop) deferred to a fresh session. Keeps each
session's vvv tight to its scope. Worked well.

## What surprised

**B1-B4 was a phantom.** Triage round showed `<upstream-project>/.ai/policies/safety.yaml`
was IDENTICAL to TRINITY_LEGACY's. Three AI reviewers (friend, Codex,
Gemini) all assumed <upstream-project> had battle-tested rules; `diff` settled it in
one command. **Lesson: verify "battle-tested" claims with evidence, not
authority.**

**ai-docs cleanup needed 3 scrub passes.** First pass caught `<upstream-project>` and
`Smarty`. Second pass caught `<upstream-domain-2>` and `application/controllers/`.
Third pass caught `{{PROJECT_NAME}}hr.com` (the placeholder created by
pass 1 that was itself project-domain-shaped). **Lesson: scrub patterns
need iterative grep verification, not single-shot regex.**

**`active_capsules` counter bug had been silent for 11 commits.** F4 root
cause was a wrong key path (`status.active_capsules` vs
`status.system.active_capsules`). Increment landed in the wrong key,
decrement read the right key, so the counter never went anywhere
visible. **Lesson: schemas (`session_state.schema.json` etc.) need to
include status.json — the test_yaml_valid pattern should extend.**

**Archive path drift since TRINITY_LEGACY.** `close.py` used
`session_path.parent.parent / "archive"` (== `.ai/archive/`) but
`ssot.yaml` declared `archive_sessions: ${sessions}/archive` (==
`.ai/sessions/archive/`). Two sources of truth, one wrong, no test caught
it. **Lesson: ssot-derived paths need a runtime resolver in core/, not
ad-hoc string surgery in each command.**

**Soft-fail audit append matters.** AuditChain wraps every append in
try/except. If a future deploy locks the audit dir read-only, kernel
keeps working with a warn line instead of cratering every session
operation. **Lesson: kernel I/O paths to non-policy state should
degrade soft.**

## What broke (along the way)

| Issue | When | Fix |
|-------|------|-----|
| `python3 .ai/cli/main.py status` ImportError | Triage | Use `bash .ai/cli/ai` launcher (already in HEAD) |
| 3 pytest failures (ssot, state, canary) | Commit 0 | Commit 1 ports those files |
| test_yaml_valid REPO_ROOT off by one | Commit 2 | 4-level `dirname` instead of 3 |
| `cd .ai && pytest` cwd mismatch with `test_basic.py` | Commit 3 | `conftest.py` pins cwd + sys.path |
| `snapshot run` blocked by 13 false-positive secrets | Commit 7 → F2 | safety.yaml `exclude_paths` + verify.py wired (88fb253) |
| `created_at` lost on every state mutation | F5 discovery | `set_state` merges with existing dict |
| audit chain stayed at 1 event throughout E2E | F1 discovery | New `core/audit.py` AuditChain wired into 5 commands |

## Decisions enforced this session

- **D2** (AI proposes; verifier/policy/human decides) — every short code
  ritual; never wrote code on first response without `vvv`.
- **D6** (ai-docs source = <upstream-project> with scrub) — Commit 5; 19-token
  placeholder dictionary; 0 contamination after triple-pass.
- **D7** (no vendor adapters in trinity_v2) — Commit 6; canonical
  `.ai/shims/` only; `.claude/skills/` etc. confirmed absent.
- **D9** (hash chain audit) — F1 fix; chain now grows on every kernel
  write.
- **D12** (relative paths via SSOT) — F3 fix; archive resolves through
  `${sessions}/${ai_root}/${project_root}` substitution.
- **D13** (plugin tool architecture) — Commit 4.5; browser-cli registered;
  contract baseline frozen.

## What's next (Phase 1+)

Setup arc closed; runtime kernel covers session lifecycle (create →
edit → verify → close → archive) with hash-chain audit and accurate
counters. **None** of the seven short codes (`lll`, `sss`, `vvv`, `nnn`,
`gogogo`, `ddd`, `rrr`) have a runtime ritual yet — only canonical
`SHIM.md` definitions. Next session opens `Phase 1 — Goal Loop runtime`:

- State machine driven by `graphs/standard.yaml`
- `vvv` ritual produces `THINK/01_PROMPT.md` + `vvv_pass` marker
- `nnn` produces `THINK/02_SCOPE.md` with budget check vs
  `loop-budget.yaml`
- `gogogo` per-step verifier checkpoint (Pyramid layer 1)
- All transitions require `decided_by` matching the graph (D10)

## Open follow-ups (not blockers)

- **R1** — extend `test_yaml_valid.py` to include `status.json` schema so
  F4-style key-path bugs surface in tests.
- **R2** — promote `path_resolution.py` from inline string-substitution
  in `close.py` to a `core/` helper that all commands use.
- **R3** — wire `last_event_hash` from status.json into a startup
  consistency check (compare to `chain.last_hash()`).
- **R4** — write a memory-cli-friendly index of this retro at
  `.ai/memory/retros/` (done; cross-link below).

## Cross-references

- Memory-cli twin: [`.ai/memory/retros/0001_2026-04-30_19_30_pm_ops-trinity-v2-setup-arc.md`](../../.ai/memory/retros/0001_2026-04-30_19_30_pm_ops-trinity-v2-setup-arc.md)
- Decisions log: [`01_CONTEXT_AND_DECISIONS.md`](01_CONTEXT_AND_DECISIONS.md)
- Commit plan: [`03_COMMIT_PLAN.md`](03_COMMIT_PLAN.md)
- Review log: [`05_REVIEW_LOG.md`](05_REVIEW_LOG.md)
- Audit chain (live): `.ai/audit/events.ndjson`
