# Trinity Checklists Index

Status: operational index

This directory collects the checklist surfaces that are currently spread across
the spec pack, migration docs, and PRD. It is an index and extraction layer, not
a replacement for the source documents.

## Checklist Set

| Checklist | Use When | Source Authority |
|---|---|---|
| [release.md](release.md) | Marking a phase, ritual, or release as done | `trinity_organ_refactor_prd.md` release criteria; `docs/migration/03_COMMIT_PLAN.md` acceptance gates |
| [tool.md](tool.md) | Creating/registering a CLI organ; memory-cli health maintenance | `docs/specs/01_TOOL_CONTRACT.md`; `docs/specs/CONTRIBUTING.md`; memory-cli v0.1 health surface |
| [policy.md](policy.md) | Changing `.ai/policies/**` or policy behavior | `docs/specs/TRINITY_POLICY_ENGINE_SPEC_V1.md` |
| [session.md](session.md) | Running normal Trinity work sessions; workflow runtime regression guards | `AGENTS.md`; `docs/ai_entry/*`; `.ai/cli/COMMAND_MANIFEST.yaml` |
| [deploy.md](deploy.md) | Preparing promotion/deploy decisions | `docs/specs/09_DEPLOY_GUIDE.md`; `docs/specs/TRINITY_DDD_HUMAN_GATE_SPEC_V1.md` |
| [prd-handoff.md](prd-handoff.md) | Assigning PRD/organ refactor work | `trinity_organ_refactor_prd.md` |

## Use Rules

- Treat source specs as canonical when this index disagrees.
- Keep checklist items concrete enough to verify.
- Link every new checklist category back to a source authority.
- Do not use these checklists to bypass `sss -> vvv -> nnn -> gogogo`.
- Do not turn checklist completion into self-certification; verifier, policy,
  and human gates still decide.

## Common Final Checks

- [ ] `bash .ai/cli/ai doctor commands` passes.
- [ ] `cd .ai && python3 -m pytest cli/tests -q` passes for code changes.
- [ ] If `.ai/memory/retros/**` changed, `memory-cli health` is PASS after reindexing stale artifacts.
- [ ] `bash .ai/cli/ai audit verify-chain` passes.
- [ ] Workflow/ritual changes also pass `bash .ai/cli/ai audit verify-chain --strict`.
- [ ] `git status --short` is reviewed and unrelated dirty files are named.
- [ ] Any skipped check has a concrete reason recorded in the session output.
