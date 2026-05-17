---
title: "01 — The 1.6% / 98.4% Rule (AI vs Engineering ratio)"
status: design-note
last-updated: 2026-05-02
audience: "Anyone designing Trinity adapters, sibling tools, or AI integration"
authors: ["operator", "Claude (notes-taker)"]
related:
  - docs/specs/01_TOOL_CONTRACT.md
  - docs/migration/01_CONTEXT_AND_DECISIONS.md (D13, D14)
  - .ai/shim/  (Phase 8 templates)
---

# The 1.6% / 98.4% Rule

> **Production AI systems are <5% LLM, >95% engineering.**
>
> Trinity matches this ratio by design — kernel + filesystem + audit
> chain do the heavy lifting; the AI worker only fills semantic
> placeholders.

## TL;DR

| Layer | Share of work |
|-------|---------------|
| AI composition (LLM call) | **1–5%** |
| Templates (views per channel) | 10–15% |
| Logic gates (validation, schema) | 15–20% |
| State machine + persistence | 20–25% |
| Harness / orchestration glue | 15–20% |
| Error handling + observability | 15–20% |
| Tests | 10–15% |
| Docs + onboarding | 5–10% |

→ AI is a sliver of the value chain.
→ Engineering ("the 98.4%") is what makes it usable in production.

## Real-world reference points

| System | LLM share | Engineering share |
|--------|-----------|-------------------|
| Gmail Smart Reply | ~3% | ~97% (spam, PII filter, lang detect, A/B test, telemetry, …) |
| GitHub Copilot inline | ~5% | ~95% (editor hooks, context window selection, stream parser, telemetry, billing) |
| Stripe fraud detection | ~10% | ~90% (rules, scoring, customer history, manual review queue) |
| Trinity kernel | **0%** | 100% (pure Python stdlib — no LLM in critical path) |
| Trinity workflow (with AI worker) | **~1.6%** | ~98.4% (AI compose; harness, audit, gates dominate) |

## Anti-pattern: "AI does everything"

Several 2023-era projects landed on the wrong ratio:

```
AutoGPT (2023): LLM ~60%, harness ~40%
LangChain v0.x: LLM-driven control flow → brittle, hard to debug
"Just prompt the LLM and trust it" school
```

Symptoms:
- ❌ Inconsistent output (sampling variance)
- ❌ High token cost per task
- ❌ Hallucinated state
- ❌ Hard to audit / replay
- ❌ Provider lock-in
- ❌ Slow (every step = LLM round-trip)

Cure: shrink the LLM surface, expand deterministic engineering.

## Trinity DNA alignment

```
.ai/cli/                 ← kernel (Python stdlib, 0% LLM)
  ├── commands/          ritual entrypoints
  ├── core/              state machine, audit, verifier
  └── policies/*.yaml    contracts (validation rules)

.ai/shim/                ← templates + adapters (Phase 8)
  ├── CLAUDE.md          vendor adapter
  └── templates/         per-ritual × per-channel views

.ai/audit/events.ndjson  ← hash-chained ledger (no LLM)

memory-cli/              ← SQLite + FTS5 + embeddings
  └── 0% LLM in indexing path
```

The AI worker (Claude/GPT/Gemini) only:
- Composes vvv answers from short intent
- Drafts plan envelope from goal
- Renders kernel output per template
- Invokes Bash to call kernel CLI

Everything else is deterministic.

## Template vs Contract

This rule has two complementary surfaces. Don't confuse them.

| Aspect | Template | Contract |
|--------|----------|----------|
| Question | "How is it rendered?" | "What must be true?" |
| Focus | Output format | Interface / invariant |
| Contains | placeholders + style | rules + schema |
| Failure mode | ugly output | system rejects |
| Audience | renderer (AI / function) | both producer + consumer |
| Mutability | changes often | stable, versioned |
| File type | markdown / handlebars | YAML / JSON Schema |
| Trust level | soft guidance | hard requirement |

### Examples in Trinity

**Contracts** (live in `.ai/policies/`):
- `tools-policy.yaml` — every sibling envelope must have `{ok, schema_version, tool, command, data, artifacts, error, meta}`
- D1 forbidden paths (hardcoded in `core/forbidden_diff.py`): `^.ai/policies/`, `^.ai/schemas/`, `^docs/specs/`, `^references/`
- D2 `decided_by:human` invariant (prod writes, ddd target=prod)
- vvv answers schema: Q1–Q5 must be non-empty
- Plan envelope schema: must have `version`, `goal`, `steps`, `acceptance`
- Audit event chain: `prev_hash` must link to previous event hash
- Acceptance criterion: must have `id`, `command`, `expect_*`

**Templates** (live in `.ai/shim/`, mostly to-be-written):
- README example commands
- vvv preview formatting
- `lll` output rendering
- Error message wording
- Retro markdown layout
- Help text

### How they interact

```
Producer (AI / function)
        ↓ produce output
Template
   "render placeholders like THIS"
        ↓ rendered output
Contract gate
   "must satisfy schema X"
   reject if fail · pass if ok
        ↓
Emitted to user / channel / audit
```

**Template = guidance pre-produce.**
**Contract = validation post-produce.**

## Per-channel template pattern

Same data, different presentation per channel. Adopted from web/email/API
content negotiation.

```
trinity_v2/.ai/shim/templates/
├── lll/
│   ├── desktop.md     verbose, full markdown, tables
│   ├── mobile.md      compact, emoji anchors, drill-down
│   ├── slack.md       slack blocks
│   └── _data-schema.md  required kernel data
├── vvv/
│   ├── desktop.md
│   └── mobile.md
├── nnn/
├── gogogo/
├── rrr/
└── ddd/
```

When the AI worker renders ritual output:
1. Detect channel (chat vs TG vs Slack vs IDE)
2. Read corresponding template
3. Fill placeholders with kernel data
4. Validate against contract
5. Emit

## Architecture A vs B (two valid paths)

### Architecture A — "Refined prompt templates as 1-shot tools"
```
User: "vvv X"
  ↓ harness loads template "vvv-prompt.md"
  ↓ AI receives prompt + intent
  ↓ AI composes answers + writes file + updates state
```
**Used by:** Aider modes, Cline tasks, oh-my-claudecode agents,
Claude Code skills (`/vvv`, `/lll`, etc.)

### Architecture B — "CLI + filesystem state machine"
```
User: "vvv"
  ↓ AI drafts answers in chat
  ↓ User approves
  ↓ AI runs `ai vvv --answers-file` (Python typer)
  ↓ Kernel renders template + writes file + emits audit + transitions state
```
**Used by:** Trinity (current).

### Why Trinity picked B

- AI-agnostic (any LLM works)
- Reproducible (no LLM in critical path)
- Auditable (hash-chained event log)
- Cheap (no API cost in kernel)
- Offline capable
- Multiple AI sessions see consistent state

### Why A is also valuable

- Bot-friendly (structured)
- Single round-trip (faster)
- Better for non-interactive automation
- Aligns with mainstream harness UX

### How Trinity layers them

Phase 8 shim already exists for this: each vendor adapter
(`shim/CLAUDE.md`, `shim/AGENTS.md`, …) is essentially Architecture A
glued onto Architecture B's filesystem.

The next step (per the per-channel template pattern above) is to
extend shim with `shim/templates/{ritual}/{channel}.md` so the AI
worker has refined templates to render against, not just informal
chat output.

## External references (prior art in `references/github_examples/`)

| Repo | Pattern |
|------|---------|
| `oh-my-claudecode/agents/*.md` | 15 agent prompt templates (planner, executor, critic, …) |
| `oh-my-claudecode/missions/*` | Per-task mission templates with Role + Constraints + Investigation Protocol |
| `thClaws/user-manual-th/ch10-slash-commands.md` | 4-tier dispatch: built-in → skill → `commands/*.md` template → unknown |
| `autoresearch/` | Skill-based research workflow patterns |
| Claude Code itself | Ships `/vvv`, `/nnn`, `/lll`, `/gogogo`, `/rrr` as skills |

## Action items (post this design note)

- [ ] **R30** — Add `shim/templates/{ritual}/{channel}.md` per ritual × channel
  (lll first, then vvv/nnn/gogogo/rrr/ddd)
- [ ] **R31** — Memory rule `feedback_compact_ritual_format` so AI defaults
  to drill-down preview format (already drafted 2026-05-02)
- [ ] **R32** — Document the AI/engineering ratio in
  `01_TOOL_CONTRACT.md` so future sibling builds know not to put LLM in
  hot path
- [ ] **R33** — Update `shim/CLAUDE.md` adapter to instruct AI to read
  per-channel templates before rendering ritual output

## Anti-rules to lock in

1. **Never put LLM in kernel hot path.** Kernel = stdlib Python only.
2. **Never let AI author its own governance artifacts.** Memory rule
   `show-before-submit` forbids this.
3. **Templates change often, contracts rarely.** Bump contract version
   on breaking changes; templates can update silently.
4. **If a pattern recurs > 3 times, replace ad-hoc compose with template.**
   (This whole design note exists because vvv/nnn drafts kept being
   re-invented per session.)

## Glossary

- **Ratio (1.6% / 98.4%)** — share of total system effort attributable
  to LLM compose vs. deterministic engineering. Aspirational; varies
  per workload but should never invert.
- **Architecture A** — prompt template as a 1-shot tool. AI receives
  template + input → produces output in one inference.
- **Architecture B** — CLI commands + filesystem state machine. AI
  invokes tools, reads/writes files; kernel is the source of truth.
- **Template** — view/format definition; soft guidance for renderer.
- **Contract** — interface/invariant; hard rule that validators check.
- **Channel** — output destination with its own UX constraints
  (desktop chat, TG mobile, Slack, IDE inline, web, …).

## Provenance

This design note crystallized in conversation 2026-05-02 between
operator and Claude. Key turning points in the discussion:

1. Operator asked: "How does Trinity control the AI worker?"
2. Realized: Trinity does not directly control — it gates artifacts,
   not actions. AI is free between gates; rejected at gates.
3. Operator asked: "What about prompt injection?" — recognized that
   Trinity is governance, not sandbox.
4. Operator asked: "Are vvv/nnn/etc. 1-shot prompt templates?"
   — uncovered Architecture A vs B mental models.
5. Operator proposed: intent compiler with preview-approve, per-ritual
   gate. Compatible with Trinity DNA (Architecture B + A overlay).
6. Operator coined the ratio: "1.6% AI, 98.4% template + logic gate +
   harness." This crystallized the architectural philosophy.
7. Operator asked: "Template vs Contract?" — surfaced the two
   complementary surfaces.
8. This document = the durable record.
