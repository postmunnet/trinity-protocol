# `clarification_helper` agent

**Authority:** RC Article XVIII (Clarification Agent row) · Constitution v1.0 Articles III (proposal-only), IV (separation), IX (exact-evidence), XVI (least authority), XVII (secret handling), XX (passive core).

**Second in-house Trinity agent.** Drafts the 5 standard `vvv` answers (Goal / Scope / Constraint / Acceptance / Risk) from an active session's context plus an operator task description. Output is JSON ready to pipe into `ai vvv --answers-file`.

## What it does

Inputs:
- Operator task description (CLI arg or stdin)
- Active session path (must contain `THINK/00_CONTEXT.md`)

Output:
```json
{
  "1": "<Goal answer>",
  "2": "<Scope answer with In scope / Out of scope sections>",
  "3": "<Constraint answer enumerating forbidden paths>",
  "4": "<Acceptance answer with executable A1, A2, A3, ... criteria>",
  "5": "<Risk answer with numbered failure modes + mitigations>"
}
```

The shape is exactly what `ai vvv --answers-file` expects — string keys `"1"` through `"5"`, each value a non-empty string.

## Usage

### Wrapper (recommended)

Run from **project root** (`trinity_v2/`) — no `cd .ai &&` prefix needed.

```bash
# Direct invocation, description as CLI arg
bash .ai/cli/agent clarification_helper draft \
    --session-path .ai/sessions/0001_2026-05-13_..._feat-foo \
    "build a new sibling that does X"

# Description from stdin
echo "my task description" | bash .ai/cli/agent clarification_helper draft \
    --session-path .ai/sessions/0001_... -

# Pipe directly into ai vvv (process substitution)
bash .ai/cli/ai vvv --answers-file <(
  bash .ai/cli/agent clarification_helper draft \
      --session-path .ai/sessions/0001_... "task description"
)

# Dry-run (no audit emission; testing only)
bash .ai/cli/agent clarification_helper draft \
    --session-path .ai/sessions/0001_... "task" --no-audit
```

### Advanced (direct module invocation)

Equivalent — bypasses the wrapper. Requires `cwd=.ai/`. Useful for
power users / scripts that already manage their own cwd discipline.

```bash
cd .ai && python3 -m cli.agents.clarification_helper draft \
    --session-path /abs/path/to/session "task description"
```

Exit codes:
- `0` — JSON proposal printed to stdout
- `2` — bad args / missing session / empty description / session dir not found
- `3` — `ValidationError` (LLM output malformed)
- `4` — `LLMError` (backend unavailable, timeout, etc.)
- `5` — unexpected error (class name printed; no body to avoid credential leak)

## Article XXVIII capability declaration (8 fields)

| Field | Value |
|---|---|
| Role | Clarification Agent (RC Article XVIII row) |
| Authority | none — proposal only; operator decides whether to submit to `ai vvv` |
| Inputs | task description (string) + active session path (Path) |
| Outputs | JSON `{"1"–"5": str}` to stdout |
| Artifacts | none persisted (operator passes JSON into `ai vvv --answers-file`) |
| State | stateless |
| Failure | raises `ValidationError` / `LLMError`; CLI returns non-zero exit + redacted stderr |
| Audit | emits `clarification_helper.invoked` / `.proposed` / `.failed`; inherits `llm.call_*` |
| Security | task description AND session context treated as `markdown_escaped` data (RC Article XVI); credential redaction inherited from `cli.core.llm_call._redact` (Article XVII) |

## Out of scope (v0.1)

- Multi-call decomposition (one prompt per dimension). Single-call prompt for v0.1; multi-call is a separate-session iteration if quality requires it.
- Auto-submission to `ai vvv` (operator pipes JSON manually; agent never invokes kernel).
- Reading `THINK/plan_envelope.json` as additional context (at vvv stage the envelope doesn't yet exist).
- Caching prior drafts (each invocation is independent).

## Bootstrap exception (#2, last in series)

The session that built this agent (`feat-clarification-helper-agent-v0-1`, 2026-05-13) used main-conversation Claude to draft its own vvv answers, because the agent did not yet exist. That was the second and final bootstrap exception. From the next session onward, `python -m cli.agents.clarification_helper draft ...` handles the vvv-drafting step.

The earlier exception (`feat-session-bootstrap-cli-v0-1`, 2026-05-13 03:36) closed the sss-side corner. Together these two exceptions close the role-collapse problem the operator surfaced on 2026-05-13 for the first two ritual steps.

## Why "in-house" instead of `../clarification-helper-cli/`

Same reasoning as `session_bootstrap`:
1. Tightly coupled to kernel state (reads `.ai/sessions/<active>/THINK/00_CONTEXT.md`, emits to `.ai/audit/events.ndjson`).
2. Reuses `cli.core.llm_call` — porting redaction/typed-placeholder/audit logic to a separate-repo JS sibling would duplicate it and create drift risk.
3. Lightweight enough to share kernel language.

See `project_in_house_agents_pattern.md` in operator memory for the canonical decision rule.
