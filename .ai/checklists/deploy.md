# Deploy Checklist

Use this before promotion or deployment.

Sources:
- `docs/specs/09_DEPLOY_GUIDE.md`
- `docs/specs/TRINITY_DDD_HUMAN_GATE_SPEC_V1.md`
- `.ai/graphs/deploy.yaml`
- `AGENTS.md`

## Environment

- [ ] Required shell is available: bash 4+ or zsh.
- [ ] Python 3.10+ is available.
- [ ] Node.js 18+ is available when sibling CLI tools are involved.
- [ ] Git is available.
- [ ] SQLite 3.30+ is available when memory-cli is involved.
- [ ] At least one vendor AI harness is available.
- [ ] Target environment is named: dev, staging, or prod.

## Pre-Deploy Evidence

- [ ] Session is in a deploy-eligible state.
- [ ] Dev verification passed.
- [ ] Prod verification passed when prod is in scope.
- [ ] Decision packet exists for DDD.
- [ ] Presentation or summary includes what changed, evidence, risks, and rollback.
- [ ] Health/smoke checks are defined.
- [ ] Rollback plan is concrete.

## Human Gate

- [ ] Human explicitly approved promotion/deploy.
- [ ] Approval reason is recorded.
- [ ] `decided_by: human` is present where required.
- [ ] No AI or tool self-approved deployment.
- [ ] Production writes are blocked until the gate is satisfied.

## Deploy Execution

- [ ] Run the canonical deploy command from `.ai/cli/COMMAND_MANIFEST.yaml` or `ai next`.
- [ ] Capture deploy logs.
- [ ] Run health check.
- [ ] Run smoke tests.
- [ ] Inspect critical error logs.
- [ ] Emit or verify deploy audit events.

## Post-Deploy

- [ ] Confirm final graph state.
- [ ] Record any degraded behavior.
- [ ] Run `bash .ai/cli/ai audit verify-chain`.
- [ ] Run `rrr` and include deploy result.
- [ ] Close or hold session explicitly.
