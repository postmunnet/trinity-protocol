# `session_bootstrap` agent

**Authority:** RC Article XVIII (Session Initializer support role) · Constitution v1.0 Articles III (proposal-only), IX (exact-evidence retrieval), XVI (least authority), XVII (secret handling).

The first **in-house Trinity agent**. Lives inside the kernel folder (`.ai/cli/agents/`) because it is tightly coupled to kernel state (reads `.ai/sessions/archive/`, emits to `.ai/audit/events.ndjson`). External siblings (`../browser-cli/`, `../memory-cli/`, etc.) remain in their own repos per Decision D12/D13.

## What it does

Operator types a task description; agent calls an LLM (via `cli.core.llm_call`) to propose:

| Field | Type | Notes |
|---|---|---|
| `slug` | kebab-case string | collision-checked against existing archives; `-2`/`-3`/... auto-appended |
| `tier` | enum `HOT` / `WARM` / `COLD` | per Addendum v1.0.1 Decision Velocity Tiers |
| `tier_reasoning` | one sentence | why this tier |
| `context_draft` | markdown | initial body for `THINK/00_CONTEXT.md` |
| `related_sessions` | list of `{slug, archive_path}` | top-N recent archives by mtime |
| `related_sessions_brief` | one sentence | LLM-written pointer to anything topically related |

The operator reads the proposal, edits if needed, and **explicitly** runs `ai session new <approved-slug>`. The agent never invokes the kernel.

## Usage

### Wrapper (recommended)

Run from **project root** — no `cd .ai &&` prefix needed.

```bash
# From a plain string
bash .ai/cli/agent session_bootstrap draft "build a sibling that helps with vvv answers"

# From stdin
echo "task description here" | bash .ai/cli/agent session_bootstrap draft -

# Dry-run (no audit chain mutation; for testing only)
bash .ai/cli/agent session_bootstrap draft "..." --no-audit
```

### Advanced (direct module invocation)

```bash
cd .ai && python3 -m cli.agents.session_bootstrap draft "task description"
```

Exit codes:
- `0` — proposal emitted to stdout as JSON
- `2` — empty/missing description
- `3` — `ValidationError` (LLM output malformed)
- `4` — `LLMError` (backend unavailable, timeout, etc.)
- `5` — unexpected error

## Article XXVIII capability declaration (8 fields)

| Field | Value |
|---|---|
| Role | Session Initializer support (Article XVIII row) |
| Authority | none — proposal only; operator decides |
| Inputs | task description (string, from CLI arg or stdin) |
| Outputs | JSON proposal `{slug, tier, tier_reasoning, context_draft, related_sessions, related_sessions_brief}` to stdout |
| Artifacts | none persisted (operator may copy `context_draft` into the eventual `THINK/00_CONTEXT.md`) |
| State | stateless |
| Failure | raises `ValidationError` / `LLMError`; CLI returns non-zero exit + redacted stderr |
| Audit | emits `session_bootstrap.invoked` / `.proposed` / `.failed`; inherits `llm.call_*` from the foundation |
| Security | task description treated as `markdown_escaped` (RC Article XVI) — never instruction; credential redaction inherited from `cli.core.llm_call._redact` (Article XVII) |

## Out of scope (v0.1)

- Semantic embedding of archive (just slug-regex match; `memory-cli` covers the embedding surface in a future iteration)
- Auto-invocation from `ai sss` (operator still runs `ai session new` explicitly)
- Multi-language support (Thai input works as markdown-escaped data; LLM responds in whatever language matches the description)
- Caching of recent proposals
- Integration with `notify-cli` to push proposals to mobile

## Why "in-house" instead of `../session-bootstrap-cli/`

External siblings (per Decision D12/D13) live outside the trinity_v2 repo so they can iterate independently and be reused across multiple Trinity instances. They are typically Node.js (browser-cli, memory-cli) and speak the contract documented in `docs/specs/01_TOOL_CONTRACT.md`.

`session_bootstrap` differs because:
1. It reads kernel-internal state (`.ai/sessions/archive/`, `.ai/audit/events.ndjson`) which would be brittle across repo boundaries.
2. It reuses `cli.core.llm_call` (Python) — porting that to JS for an external sibling would duplicate the redaction/typed-placeholder/audit logic and create drift risk.
3. It is lightweight enough that an external repo would be over-architected.

The operator approved this "in-house agents" category on 2026-05-13. Future agents that match the same profile (`clarification_helper`, `plan_helper`, `retro_writer` semantic layer, etc.) belong in `.ai/cli/agents/` too.

## Bootstrap exception

This agent's own creation session (`feat-session-bootstrap-cli-v0.1`, 2026-05-13) used main-conversation Claude to draft the slug, vvv answers, and plan body, because the agent did not yet exist. That was a **one-time, explicit, operator-approved** exception. From the next session onward, the slug/tier/context proposal step is delegated to this agent.
