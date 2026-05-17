# `plan_helper` agent

**Authority:** RC Article XVIII (Planning Agent row) · Constitution v1.0 Articles III (proposal-only), IV (separation), IX (exact-evidence), XVI (least authority), XVII (secret handling), XX (passive core), XXII (recovery/rollback).

**Third in-house Trinity agent.** Drafts `plan_envelope.json` from an active session's `00_CONTEXT.md` and `01_PROMPT.md` (post-vvv). Output JSON is shape-compatible with `ai nnn --plan-envelope`. Codifies the canonical acceptance-row schema in the validator itself, closing the foot-gun documented in `feedback_nnn_rrr_acceptance_schema_mismatch`.

## What it does

Inputs:
- Active session path (must contain BOTH `THINK/00_CONTEXT.md` AND `THINK/01_PROMPT.md`).

Output to stdout — strict JSON `plan_envelope` with:
- `goal` (one paragraph, concrete)
- `tier` ∈ {HOT, WARM, COLD}
- `allowed_paths[]` (conservative — only paths named in vvv answers)
- `forbidden_paths[]` (D1 boundary set + task-specific)
- `constitutional_notes[]` (anchored to Articles/Decisions)
- `steps[]` with `{id, action, owner_role, expected_artifact, risk}`
- `acceptance[]` with **CANONICAL schema** `{id, description, command, expect_exit, required}` — NOT `criterion/check`
- `rollback[]` (≥3 entries per Article XXII)
- `decided_by: "human"` (Article XIII)

## Usage

### Wrapper (recommended)

Run from **project root** — no `cd .ai &&` prefix needed.

```bash
# Direct invocation
bash .ai/cli/agent plan_helper draft --session-path .ai/sessions/0001_...

# Capture for review then submit
bash .ai/cli/agent plan_helper draft \
    --session-path .ai/sessions/0001_... > /tmp/plan_draft.json
# operator reviews /tmp/plan_draft.json (editor, diff against examples, etc.)
bash .ai/cli/ai nnn --plan-envelope /tmp/plan_draft.json

# Dry-run (no audit; testing only)
bash .ai/cli/agent plan_helper draft --session-path .ai/sessions/0001_... --no-audit
```

### Advanced (direct module invocation)

```bash
cd .ai && python3 -m cli.agents.plan_helper draft --session-path /abs/path/to/session
```

Exit codes:
- `0` — JSON proposal printed to stdout
- `2` — bad args / missing session inputs (no 01_PROMPT.md → run `ai vvv` first)
- `3` — `ValidationError` (LLM produced malformed plan_envelope)
- `4` — `LLMError`
- `5` — unexpected error

## Hard error on missing vvv output

The agent does NOT emit a stub or fallback envelope when `THINK/01_PROMPT.md` is missing or empty. It exits 2 with a stderr message instructing the operator to run `ai vvv` first. This is intentional — a stub envelope downstream is worse than a clear "do vvv first" message.

## Anti-foot-gun: acceptance row schema

The validator EXPLICITLY rejects acceptance rows with `criterion` or `check` keys (the documented schema mismatch from `feedback_nnn_rrr_acceptance_schema_mismatch`). Only the canonical 5-key shape passes:

```json
{
  "id": "A1",
  "description": "human-readable criterion",
  "command": "executable shell snippet",
  "expect_exit": 0,
  "required": true
}
```

If the LLM produces `criterion/check` rows, the agent surfaces a clear `ValidationError` instead of forwarding the broken shape downstream.

## Article XXVIII capability declaration

| Field | Value |
|---|---|
| Role | Planning Agent (RC Article XVIII row) |
| Authority | none — proposal only; operator decides whether to submit |
| Inputs | active session path containing `00_CONTEXT.md` + `01_PROMPT.md` |
| Outputs | JSON `plan_envelope` to stdout |
| Artifacts | none persisted (operator captures stdout for review) |
| State | stateless |
| Failure | raises `ValidationError` / `LLMError`; CLI returns non-zero exit + redacted stderr |
| Audit | emits `plan_helper.invoked` / `.proposed` / `.failed`; inherits `llm.call_*` |
| Security | both context and vvv prompt are `markdown_escaped` data (RC Article XVI); credential redaction inherited from `cli.core.llm_call._redact` (Article XVII) |

## Out of scope (v0.1)

- Auto-submission to `ai nnn` (operator pipes manually)
- Multi-call decomposition (single LLM call for v0.1)
- Golden-fixture test pinning one realistic plan_envelope (shape-only tests are sufficient for v0.1; integration smoke covered in the agent's own creation session)
- Writing to `.ai/sessions/.../THINK/02_PLAN_DRAFT.json` — stdout only

## Bootstrap exception #3 (FINAL)

The session that built this agent (`feat-plan-helper-agent-v0-1`, 2026-05-13) used main-conversation Claude to draft its own plan_envelope, because the agent did not yet exist. That was the third and FINAL bootstrap exception. Together with #1 (`session_bootstrap` own session) and #2 (`clarification_helper` own session), all three pre-execution ritual steps (sss / vvv / nnn) are now fully delegated to agents.

From the next session onward, the operator's workflow is:

```
1. python -m cli.agents.session_bootstrap draft "<task>"     → propose slug/tier/context
2. bash .ai/cli/ai session new <approved-slug>
3. python -m cli.agents.clarification_helper draft \
       --session-path <session> "<task>"                       → propose 5 vvv answers
4. bash .ai/cli/ai vvv --answers-file <reviewed-answers>
5. python -m cli.agents.plan_helper draft \
       --session-path <session>                                 → propose plan_envelope
6. bash .ai/cli/ai nnn --plan-envelope <reviewed-envelope>
7. <execute steps; ddd; rrr; close>
```

Main-conversation Claude's role: coordinate + answer questions + execute steps that don't have agent coverage yet (gogogo executor, ddd presentation, rrr semantic retro — all still TBD).
