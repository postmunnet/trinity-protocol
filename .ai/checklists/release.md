# Release Checklist

Use this before marking a phase, ritual, or release complete.

Sources:
- `trinity_organ_refactor_prd.md` sections 12-13
- `docs/migration/03_COMMIT_PLAN.md`
- `.ai/cli/COMMAND_MANIFEST.yaml`

## Scope

- [ ] Release target is named: phase, ritual, PR, or version.
- [ ] Decision velocity tier is declared: HOT, WARM, or COLD.
- [ ] In-scope files are listed.
- [ ] Forbidden paths are listed.
- [ ] Open risks are listed with mitigation or owner.

## Required Artifacts

- [ ] Plan exists where required.
- [ ] Acceptance criteria exist and are measurable.
- [ ] Verification contract or equivalent evidence exists for WARM/COLD work.
- [ ] Execution artifacts exist for changed behavior.
- [ ] Verifier report or test output exists.
- [ ] DDD decision artifact exists when promotion/deploy is involved.
- [ ] RRR closure exists for completed sessions.
- [ ] Final audit or close manifest exists when closing/releasing.

## Verification

- [ ] Acceptance criteria pass.
- [ ] Failure behavior is visible, not silent.
- [ ] No forbidden role absorption was introduced.
- [ ] No production or irreversible action occurred without human gate.
- [ ] Documentation/spec changes landed with code changes when needed.
- [ ] `bash .ai/cli/ai doctor commands` passes.
- [ ] `cd .ai && python3 -m pytest cli/tests -q` passes for runtime changes.
- [ ] `bash .ai/cli/ai audit verify-chain` passes.

## Release Decision

- [ ] Remaining dirty worktree entries are reviewed.
- [ ] Known non-blockers are named.
- [ ] Human decision is recorded when required.
- [ ] Rollback path is documented.
- [ ] Next action is explicit: continue, promote, deploy, close, or hold.
