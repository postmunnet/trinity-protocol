# AGENTS.md — Generic Agent Entrypoint for trinity_v2

> For Cursor, Codex CLI, Aider, and other vendor harnesses that read AGENTS.md.
> Claude Code → use [`CLAUDE.md`](CLAUDE.md). Gemini CLI → [`GEMINI.md`](GEMINI.md). Warp → [`WARP.md`](WARP.md).
> Same canonical content; vendor-specific notes per file.

## What is trinity_v2?

CLI-native AI microkernel — Coordinator + Judge for vendor AI. Spec pack v2.0 in `docs/specs/`. Canonical bootstrap/runtime, **not** a project clone.

## Read FIRST (priority order)

1. **For setup work (Commit 0–7):** [`docs/migration/README.md`](docs/migration/README.md)
2. **For Phase 1+ implementation:** [`docs/specs/INDEX.md`](docs/specs/INDEX.md) → [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md)
3. **First time here:** [`docs/ai_entry/QUICK_START.md`](docs/ai_entry/QUICK_START.md)
4. **Always:** [`docs/ai_entry/SHORT_CODES.md`](docs/ai_entry/SHORT_CODES.md) + [`BOUNDARIES.md`](docs/ai_entry/BOUNDARIES.md) + [`WORKFLOW.md`](docs/ai_entry/WORKFLOW.md)

## Short Codes

| Code | Action | When |
|------|--------|------|
| `lll` | Look/List status | Start of session, anytime |
| `sss: <task>` | Start session | New task |
| `vvv` | Verify understanding | Before code |
| `nnn` | New plan with estimates | After vvv pass |
| `gogogo` | Execute plan | After nnn approved |
| `ddd` | Deploy (human gate) | After gogogo + verify |
| `rrr` | Retrospective | End of session |

**Sequence:** `sss → vvv → nnn → gogogo → ddd → rrr` (don't skip)

Detail: [`docs/ai_entry/SHORT_CODES.md`](docs/ai_entry/SHORT_CODES.md)

## CLI Command Rule

Do not guess Trinity commands from ritual names. The ritual short-codes map to executable commands via [`.ai/cli/COMMAND_MANIFEST.yaml`](.ai/cli/COMMAND_MANIFEST.yaml); consult the manifest or run `bash .ai/cli/ai doctor commands` before invoking.

Concrete mappings:

- `sss "<task>"` → `bash .ai/cli/ai sss "<task>"` (alias of `bash .ai/cli/ai session new "<task>"`)
- `status` → `bash .ai/cli/ai status` (alias of `bash .ai/cli/ai status show`)
- `vvv / nnn / gogogo / ddd / rrr / lll / close` → `bash .ai/cli/ai <code>`

If any command fails with `No such command` or `Missing command`, stop and run `bash .ai/cli/ai doctor commands` — do NOT retry random variants.

## Per-channel ritual rendering

<!-- BEGIN R30/R33 per-channel rendering -->
Ritual output layout is template-driven. Before changing `lll`, `vvv`, `nnn`,
`gogogo`, `ddd`, or `rrr` presentation, read the canonical templates at
`.ai/shims/<ritual>/templates/<channel>.md`.

- `desktop.md` may use dense tables and box-drawing where appropriate.
- `mobile.md` must avoid box-drawing and ASCII tables.
- Adapter files only point agents at the templates; the templates own layout.
<!-- END R30/R33 per-channel rendering -->

## Boundaries

- ✅ AI **proposes** — Verifier/Policy/Human **decides**
- ✅ Every action logs to `.ai/audit/events.ndjson` (hash chain)
- ❌ Forbidden: edit `.ai/policies/**`, modify `.ai/audit/**`, auto-deploy, MCP as core, <upstream-project> direct copy

Detail: [`docs/ai_entry/BOUNDARIES.md`](docs/ai_entry/BOUNDARIES.md)

## Pyramid of Judgment

```
verifier (rules)  →  policy (gates)  →  LLM judge (gated)  →  human
```

You are layer 3 — last resort, audited. Never layer 1.

## Vendor-Specific Notes

### Cursor
- `.cursor/rules/` not yet populated (Decision D7 — canonical shims live in `.ai/shims/`)
- Cursor reads this file (AGENTS.md) for context
- After Phase 8: Cursor rules will be **generated** from `.ai/shims/` canonical (not hand-written)

### Codex CLI
- AGENTS.md (this file) is the entry point
- Codex's Rust harness — same Trinity workflow, no special handling

### Aider
- AGENTS.md is the entry point
- Aider's git-aware workflow plays well with Trinity sessions (each session = isolated capsule)
- Use `aider --commit-message-prefix "[trinity-session-id] "` to tag commits

### Generic agent
- If your harness reads AGENTS.md, you're covered
- For multi-AI debate (SANDBOX phase): write only in your role's folder (`02_gemini/`, `03_claude/`, `04_codex/` — pick the closest match or create new with user approval)

## Session Sandbox Rules

You may write to (within active session):
- `SANDBOX/<your_role>/` — pick by vendor (Cursor → 03_claude or new; Codex → 04_codex; Aider → choose with user)
- `DO/dev/` — after `vvv_pass`
- `THINK/*` during THINK phase

You may NOT write to:
- Other agents' SANDBOX folders
- `DO/prod/` (human-promoted only)
- `.ai/policies/`, `.ai/audit/` (modify), `.ai/schemas/`

## Quick Run Commands

```bash
# Status
bash .ai/cli/ai status

# Tests
cd .ai && python3 -m pytest cli/tests -q

# YAML config validation
cd .ai && python3 -m pytest cli/tests/test_yaml_valid.py -v
```

## Quick Links

| What | Where |
|------|-------|
| Spec overview | [`docs/specs/INDEX.md`](docs/specs/INDEX.md) |
| Master vision | [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md) |
| Migration plan | [`docs/migration/README.md`](docs/migration/README.md) |
| Decisions log | [`docs/migration/01_CONTEXT_AND_DECISIONS.md`](docs/migration/01_CONTEXT_AND_DECISIONS.md) |
| Glossary | [`docs/specs/12_GLOSSARY.md`](docs/specs/12_GLOSSARY.md) |

## Don't

- ❌ Edit `.ai/policies/**`
- ❌ Skip `vvv`
- ❌ Auto-deploy
- ❌ Use MCP as core path (Decision #5)
- ❌ Copy <upstream-project> patterns without sanitization
- ❌ `git push --force` without explicit approval

When unsure → ask. NEEDS_HUMAN > confident wrong answer.
