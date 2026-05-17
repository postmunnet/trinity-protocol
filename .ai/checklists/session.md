# Session Checklist

Use this for ordinary Trinity sessions.

Sources:
- `AGENTS.md`
- `docs/ai_entry/QUICK_START.md`
- `docs/ai_entry/SHORT_CODES.md`
- `docs/ai_entry/WORKFLOW.md`
- `.ai/cli/COMMAND_MANIFEST.yaml`

## Start

- [ ] Run `bash .ai/cli/ai lll` or `bash .ai/cli/ai status`.
- [ ] Confirm active session and graph state.
- [ ] If needed, create session with `bash .ai/cli/ai sss "<task>"`.
- [ ] If command mapping is unclear, run `bash .ai/cli/ai doctor commands`.
- [ ] Record scope, constraints, acceptance, and risk through `vvv`.

## Plan

- [ ] Run `vvv` before `nnn`.
- [ ] Plan envelope declares goal, tier, allowed paths, forbidden paths, acceptance, rollback, steps.
- [ ] Budget estimates are present when execution is non-trivial.
- [ ] Forbidden paths include `.ai/policies/**`, `.ai/audit/**`, `.ai/schemas/**` unless explicitly approved by human.
- [ ] Acceptance commands are executable when practical.

## Execute

- [ ] Run `gogogo` only after `nnn` passes.
- [ ] Keep edits inside allowed paths.
- [ ] Do not revert unrelated dirty files.
- [ ] Capture evidence as commands, artifacts, or test output.
- [ ] Stop on verifier, policy, or human gate failures.

## Close

- [ ] Verify acceptance criteria.
- [ ] Run relevant tests.
- [ ] Run `bash .ai/cli/ai audit verify-chain`.
- [ ] For workflow/ritual changes, also run `bash .ai/cli/ai audit verify-chain --strict`.
- [ ] Run `bash .ai/cli/ai doctor commands` after changing CLI command surfaces or `.ai/cli/COMMAND_MANIFEST.yaml`.
- [ ] Run `rrr` before close when the session is complete.
- [ ] Use bare `bash .ai/cli/ai close` for the close ritual; `close run` is backward compatibility.
- [ ] Do not run `ddd` or deploy without explicit human decision.
- [ ] Report remaining risks and dirty worktree entries.

## Runtime Regression Guards

- [ ] `ai next` must recommend executable commands from `.ai/cli/COMMAND_MANIFEST.yaml`; no `Missing command` output is acceptable.
- [ ] `ddd --dry-run` must not append audit events, create captures, or advance graph state.
- [ ] `lll --json` should surface memory hints when shorter fallback queries match prior retros.
- [ ] `close` must refuse archive unless graph state is terminal (`DONE` or `DEAD`) unless `--force` is explicitly used.
- [ ] When `.ai/ssot.yaml` has `sandbox.runtime_enforcement_enabled: true`, sandbox profiles that declare `fs`, `net`, or `proc` constraints must fail closed with `sandbox.runtime_unavailable` if the host cannot enforce OS sandboxing.
- [ ] When `sandbox.runtime_enforcement_enabled: false`, `gogogo` must emit `sandbox.runtime_disabled` before dispatching any tool whose profile declares OS-level axes.
