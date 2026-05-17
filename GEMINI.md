# GEMINI.md — Gemini CLI Entrypoint for trinity_v2

> For Gemini CLI sessions in this repo. Same canonical content as CLAUDE.md / AGENTS.md / WARP.md; Gemini-specific notes here.

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

**Sequence:** `sss → vvv → nnn → gogogo → ddd → rrr`

Detail: [`docs/ai_entry/SHORT_CODES.md`](docs/ai_entry/SHORT_CODES.md)

## CLI Command Rule

Do not guess Trinity commands from ritual names. Ritual short-codes map to executable CLI via [`.ai/cli/COMMAND_MANIFEST.yaml`](.ai/cli/COMMAND_MANIFEST.yaml); consult it or run `bash .ai/cli/ai doctor commands` before invoking.

- `sss "<task>"` → `bash .ai/cli/ai sss "<task>"` (alias of `bash .ai/cli/ai session new "<task>"`)
- `status` → `bash .ai/cli/ai status` (alias of `bash .ai/cli/ai status show`)
- `vvv / nnn / gogogo / ddd / rrr / lll / close` → `bash .ai/cli/ai <code>`

If a command fails with `No such command` or `Missing command`, stop and run `bash .ai/cli/ai doctor commands` — do NOT retry random variants.

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
- ❌ Forbidden: edit `.ai/policies/**`, auto-deploy, MCP as core, <upstream-project> direct copy

Detail: [`docs/ai_entry/BOUNDARIES.md`](docs/ai_entry/BOUNDARIES.md)

## Pyramid of Judgment

```
verifier (rules)  →  policy (gates)  →  LLM judge (gated)  →  human
```

You are layer 3 — gated, audited, last resort.

## Gemini-Specific Notes

### Strengths to leverage
- **Large context window** — load multiple specs at once when planning (`00_BLUEPRINT.md` + `INDEX.md` + relevant phase spec together)
- **Knowledge Brain / Librarian role** — per `00_BLUEPRINT.md` §6, Gemini is often the brain that summarizes past retros, cross-references patterns, builds memory hints

### Role in multi-AI debate (SANDBOX phase)
In `templates/session/SANDBOX/02_gemini/`, your role is:
- `analysis.md` — analyze proposal from research/historical context
- `proposal.md` — propose alternative or refinement
- `research.md` — provide background research

Other agents work in:
- `03_claude/` — Claude's role (review, governance, critique)
- `04_codex/` — Codex's role (implementation, patch.diff)

Each agent **isolated until** `01_DEBATE/` rolls up. **Do not write outside `02_gemini/`.**

### `.gemini/` directory
Not yet populated. No active config/skills. Canonical shim definitions live in `.ai/shims/` (added Commit 6); Gemini-specific config will be generated from canonical per `07_SHIM_SPEC.md` (Phase 8).

### Reference (DO NOT copy directly)
`references/shims/upstream-skills/` (added Commit 6) — <upstream-project>'s actual `lll/vvv/nnn/gogogo/rrr` skill definitions. Use as **pattern reference only**, must genericize before any active install.

## Session Sandbox Rules

You may write to (within active session):
- `SANDBOX/02_gemini/{analysis,proposal,research}.md` — your role only
- `DO/dev/` — after `vvv_pass`
- `THINK/*` during THINK phase

You may NOT write to:
- `SANDBOX/03_claude/`, `SANDBOX/04_codex/` (other agents' folders)
- `DO/prod/` (human-promoted only)
- `.ai/policies/`, `.ai/audit/` (modify), `.ai/schemas/`

## Quick Run Commands

```bash
# Status
bash .ai/cli/ai status

# Tests
cd .ai && python3 -m pytest cli/tests -q

# Knowledge Brain query (after Phase 2)
# memory-cli search "auth pattern"   ← not yet implemented (Phase 2)
```

## Quick Links

| What | Where |
|------|-------|
| Spec overview | [`docs/specs/INDEX.md`](docs/specs/INDEX.md) |
| Master vision | [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md) |
| Migration plan | [`docs/migration/README.md`](docs/migration/README.md) |
| Decisions log | [`docs/migration/01_CONTEXT_AND_DECISIONS.md`](docs/migration/01_CONTEXT_AND_DECISIONS.md) |
| Glossary | [`docs/specs/12_GLOSSARY.md`](docs/specs/12_GLOSSARY.md) |
| Memory CLI spec (Phase 2) | [`docs/specs/05_MEMORY_CLI_SPEC.md`](docs/specs/05_MEMORY_CLI_SPEC.md) |

## Don't

- ❌ Use MCP servers (Trinity is CLI-first per Decision #5)
- ❌ Edit other AI's sandbox folder (only `02_gemini/` is yours)
- ❌ Decide PROMOTED/DEPLOYED transition (human-only)
- ❌ Skip `vvv`
- ❌ Copy <upstream-project> patterns without scrubbing

When unsure → ask. NEEDS_HUMAN > confident wrong answer.
