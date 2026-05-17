# `executor_helper` agent

**Authority:** RC Article XVIII (Executor Agent row) · Constitution v1.0 Articles III (proposal-only), IV (separation: Planner ≠ Executor), IX (exact-evidence), XVI (least authority), XVII (secret handling), XX (passive core).

**Fourth in-house Trinity agent.** Drafts a structured implementation proposal for a single `plan_envelope` step. Operator reviews before applying.

## What it does

Inputs:
- `--session-path PATH` (required) — must contain `THINK/00_CONTEXT.md` and `.state/plan.json` (the kernel-protected canonical plan envelope written by `ai nnn`)
- `--step-id ID` (required) — must exist in the plan_envelope's `steps[]`

Output to stdout — strict JSON:
```json
{
  "step_id": "S1",
  "files_to_create": [{"path": "...", "content": "..."}],
  "files_to_edit": [{"path": "...", "old": "...", "new": "..."}],
  "commands_to_run": [{"cmd": "...", "cwd": ".", "expect_exit": 0}],
  "notes": "rationale for the proposal"
}
```

## Discipline

- **PROPOSAL ONLY.** Agent NEVER writes files, runs commands, or invokes the kernel.
- `files_to_edit` uses Edit-tool exact-match semantics: `old` MUST occur exactly once at apply time.
- `commands_to_run` items are STRUCTURED objects (`cmd` + `cwd` + `expect_exit`), not plain strings — so future verifier can interpret them.
- Pure-verification step convention: empty arrays + mandatory `notes` explaining why no writes.
- Step ID validation: agent rejects proposal if LLM returns wrong `step_id` (drift guard).

## Usage

### Wrapper (recommended)

Run from **project root** — no `cd .ai &&` prefix needed.

```bash
# Direct
bash .ai/cli/agent executor_helper draft \
    --session-path .ai/sessions/0001_... --step-id S1

# Capture for review then apply (operator handles application separately)
bash .ai/cli/agent executor_helper draft \
    --session-path .ai/sessions/0001_... --step-id S2 > /tmp/step_proposal.json
# operator reviews /tmp/step_proposal.json
# (future "applier" agent would consume this; for now operator applies manually)

# Dry-run (no audit)
bash .ai/cli/agent executor_helper draft \
    --session-path .ai/sessions/0001_... --step-id S1 --no-audit
```

### Advanced (direct module invocation)

```bash
cd .ai && python3 -m cli.agents.executor_helper draft \
    --session-path /abs/path/to/session --step-id S1
```

Exit codes:
- `0` — JSON proposal printed
- `2` — bad args / missing session / step not found
- `3` — `ValidationError` (LLM produced malformed proposal)
- `4` — `LLMError`
- `5` — unexpected

## Article XXVIII capability declaration

| Field | Value |
|---|---|
| Role | Executor Agent (RC Article XVIII row) |
| Authority | none — proposal only |
| Inputs | session path + step id |
| Outputs | JSON proposal to stdout |
| Artifacts | none persisted |
| State | stateless |
| Failure | `ValidationError` / `StepNotFoundError` / `LLMError` → non-zero exit + redacted stderr |
| Audit | emits `executor_helper.invoked` / `.proposed` / `.failed` + inherited `llm.call_*` |
| Security | step body + context are `markdown_escaped` data (RC Article XVI); credential redaction inherited from `cli.core.llm_call` (Article XVII) |

## Out of scope (v0.1)

- Applying the proposal (separate "applier" session — must include forbidden-path check, dry-run preview, rollback on partial-apply failure)
- Multi-step batching (one step per invocation)
- Diff-based edit semantics (Edit-tool exact-match only; fuzzy/anchor-based deferred)

## Position in the agent chain

```
sss → session_bootstrap (slug)
nnn → plan_helper (plan_envelope)
vvv → clarification_helper (5 vvv answers)
gogogo → executor_helper (per-step proposal) ← THIS
ddd → presentation_synthesizer (TBD)
rrr → retro_writer (TBD, semantic layer)
```
