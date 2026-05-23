# In-house Trinity Agents

Trinity ships a small set of proposal-only Python agents at `.ai/cli/agents/<name>/`.
They are invoked through the wrapper `.ai/cli/agent` (mirroring `.ai/cli/ai`).

## Agents

| Agent | Purpose |
|---|---|
| `session_bootstrap` | Draft session slug from a raw task description (sss) |
| `clarification_helper` | Draft 5 vvv answers from session context |
| `plan_helper` | Draft a plan envelope (nnn) |
| `executor_helper` | Draft a per-step gogogo proposal |
| `retro_writer` | Draft retrospective body (rrr) |
| `presentation_synthesizer` | Draft a close pack summary |

## Invocation

```bash
bash .ai/cli/agent <agent> [args...]
bash .ai/cli/agent --list           # show available agents
bash .ai/cli/agent --help           # full usage
```

## `--session-path active` (added 2026-05-23)

The wrapper resolves the literal token `active` to whatever
`.ai/state/status.json::current_session` points at, at invocation time.

```bash
bash .ai/cli/agent clarification_helper draft \
    --session-path active "task description"

bash .ai/cli/agent plan_helper draft --session-path active
```

If no session is open (`status.json` missing or unreadable) the wrapper
exits **78** with a message on stderr — no Python traceback.

Resolution is **one-shot**: the wrapper substitutes the path before
dispatching to Python, so a concurrent `sss` in another shell could
race to a different session. Same race-window as KI-2026-05-16-001;
use an explicit session path (or `--session` flag on the kernel command)
when concurrency matters.

## Boundaries

Agents are **proposal-only** (Article III). They write to a session's
`THINK/` or `SANDBOX/` only, never to `.ai/policies/`, `.ai/audit/` (mutate),
`.ai/schemas/`, `docs/specs/`, or `docs/constitution/`.
