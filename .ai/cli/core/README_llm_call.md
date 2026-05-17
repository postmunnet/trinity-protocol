# `llm_call.py` — LLM-call foundation for Trinity sibling CLIs

**Authority hierarchy:**
- Constitution v1.0 — Articles IX (Memory Discipline), XVI (Least Authority), XVII (Secret Handling), XX (Passive Core)
- Ritual Constitution v1.1-rc — Article XVI (Template Injection Protection)

**Audience:** sibling-CLI authors building `judge-cli`, `presentation-synthesizer-cli`, `plan-helper-cli`, `debate-cli`, `retro-writer-cli`, and any future Trinity tool that calls an external LLM.

**Not for kernel rituals:** the deterministic ritual commands (`sss`/`nnn`/`gogogo`/`ddd`/`rrr`/`close` in `.ai/cli/commands/`) **MUST NOT** import this module. Per Decisions D8/D13 the kernel stays free of LLM dependencies; semantic work happens inside sibling CLIs that wrap `llm_call`.

---

## Public API

```python
from cli.core.llm_call import (
    call_llm, load_ritual_pack, substitute, discover_backends, select_backend,
    LLMRequest, LLMResponse, RitualPack,
    ClaudeCLIBackend, GeminiCLIBackend, CodexCLIBackend, AnthropicAPIBackend, MockBackend,
    LLMError, MissingPlaceholderError, TypeMismatchError, UntypedPlaceholderError,
    BackendUnavailable, BackendError, BackendTimeout, NoBackendAvailable,
)
```

### `call_llm(request, *, backend=None, audit_chain=None, ritual_context=None) -> LLMResponse`

Top-level orchestrator. Emits `llm.call_started` before invoke, `llm.call_completed` on success, `llm.call_failed` on error. All prompt/response strings are redacted via `_redact()` before audit emission.

### `load_ritual_pack(ritual_name, rituals_root=Path('.ai/rituals')) -> RitualPack`

Read the 4-file pack from `.ai/rituals/<ritual_name>/`. Returns a dataclass with `contract`, `context_schema`, `check_template`, `write_template`, `root`. Does NOT validate JSON against schemas — that is `test_ritual_template_packs.py`'s job.

### `substitute(template, context, context_schema) -> str`

Substitute `{{type:identifier}}` placeholders. Fails closed: any non-typed double-brace token raises `UntypedPlaceholderError` (the Article XVI injection canary).

### `select_backend(*, request=None, preference=None, env_override=None, backends=None) -> Backend`

Selection strategy:
1. `request.backend` (explicit request override)
2. `env_override` arg or `LLM_BACKEND` env var
3. `preference` list (default: `claude` > `codex` > `gemini` > `anthropic-api`)

Raises `NoBackendAvailable` when nothing matches; `BackendUnavailable` when a specific name was requested but is unavailable.

---

## Backend matrix

| Backend | Availability check | Auth | Notes |
|---|---|---|---|
| `ClaudeCLIBackend` (default 1) | `shutil.which('claude')` | reuses operator's `claude` CLI session | invokes `claude -p <prompt>` |
| `CodexCLIBackend` (default 2) | `shutil.which('codex')` | reuses operator's `codex` CLI session | invokes `codex exec <prompt>` |
| `GeminiCLIBackend` (default 3) | `shutil.which('gemini')` | reuses operator's `gemini` CLI session | invokes `gemini -p <prompt>` |
| `AnthropicAPIBackend` (default 4) | `import anthropic` success + `ANTHROPIC_API_KEY` env | direct API call | optional dependency; graceful fallback when SDK or key absent |
| `MockBackend` | always | none | testing only — canned response |

CLI backends prefer the operator's existing authenticated session; trinity_v2 does **not** manage API keys for them. The API backend is the optional path for environments where CLIs are unavailable.

---

## RC Article XVI typed placeholders (7 types)

| Type | Substitution behaviour |
|---|---|
| `plain_text` | `str(value)` — identity |
| `markdown_escaped` | `html.escape(value, quote=False)` |
| `json_string` | `json.dumps(value, compact)` |
| `path` | `str(Path(value))` |
| `enum` | identity, **but** value must be in `enum_values` declared in `context.schema.json` |
| `code_block` | wraps in triple-backtick fence |
| `evidence_ref` | dict → compact JSON; non-dict → `str(value)` |

Any double-brace token that does NOT match `\{\{[a-z_]+:[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*\}\}` raises `UntypedPlaceholderError`. The same regex is the single source of truth used by `test_ritual_template_packs.py`.

---

## Article XXVIII capability declaration

| Field | Value |
|---|---|
| Role | external-LLM transport |
| Authority | none (transport-only; never decides verdicts or gates) |
| Inputs | `LLMRequest` (prompt + optional model/backend/timeout/metadata) |
| Outputs | `LLMResponse` (text + model + backend + duration_ms + raw) |
| Artifacts | none (caller decides what to persist) |
| State | stateless per call |
| Failure | raises `BackendUnavailable` / `BackendError` / `BackendTimeout` / `NoBackendAvailable` / `LLMError` subclasses |
| Audit | when `audit_chain` provided, emits `llm.call_started` / `llm.call_completed` / `llm.call_failed` |
| Security | credential redaction (Article XVII) before audit + in error messages |

---

## Example: minimal sibling-CLI usage

```python
from pathlib import Path
from cli.core.audit import AuditChain
from cli.core.llm_call import call_llm, load_ritual_pack, substitute, LLMRequest

pack = load_ritual_pack("vvv", rituals_root=Path(".ai/rituals"))
prompt = substitute(pack.write_template, my_context_dict, pack.context_schema)
chain = AuditChain(Path(".ai/audit/events.ndjson"))

response = call_llm(
    LLMRequest(prompt=prompt, timeout=60.0),
    audit_chain=chain,
    ritual_context={"ritual": "vvv", "session_id": session_id},
)
print(response.text)
```

The sibling CLI then validates `response.text` against `pack.check_template`, emits its own audit events (`<sibling>.completed`), and returns artifacts to the caller.

---

## Out of scope (this module)

- Multi-turn conversation (single-shot only)
- Streaming responses
- Response caching
- Gemini SDK and OpenAI SDK API backends (CLI mode covers these vendors at v0.1)
- Token accounting / cost tracking
- Kernel runtime that loads templates at ritual invocation time (separate session)

---

## Forbidden combinations

- **Calling from `commands/*.py`** — kernel rituals stay deterministic. Violators will be flagged by `forbidden_diff` in future Phase 6 (Executor Tool Capability Declarations).
- **Using `MockBackend` in production** — explicit `backend=MockBackend()` is a test-only construct; verifier will flag it via audit-event inspection.
- **Passing `audit_chain=None` outside tests** — every production call must be audited (Article X).
