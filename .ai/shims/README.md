---
title: "Trinity Shims — Canonical Vendor-Agnostic Layer"
status: stable
last-updated: 2026-04-30
audience: "Adapter authors (Claude Code skills, Codex, Gemini, Cursor, Warp)"
spec: docs/specs/07_SHIM_SPEC.md
---

# Trinity Shims — Canonical Layer

> The **canonical** definition of every Trinity short code. Vendor adapters
> (Claude `.claude/skills/`, Codex AGENTS.md, Cursor `.cursor/rules/`, etc.)
> are **generated** from these — never hand-written, never copied from
> another project.

## Why this layer exists

Without a canonical layer, each vendor harness re-implements `lll`/`vvv`/`nnn`/
`gogogo`/`rrr` slightly differently → behavior drifts → users get inconsistent
results across tools. The canonical SHIM.md files here are **the** definition;
adapters render them into vendor-specific surfaces.

## 2-Layer Pattern (per `07_SHIM_SPEC.md §4`)

```
┌──────────────────────────────────────────┐
│ Vendor Harness (Claude / Codex / ...)    │
│   Vendor Adapter:                        │
│     • Skills / Rules / Instructions      │
│     • Hooks (pre/post response)          │
│     • Context injection                  │
│   ↓ shells out to                        │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│ Trinity Universal Shell (trinity-shell)  │
│   • Single CLI surface for adapters      │
│   • Routes to .ai/cli/ kernel            │
└──────────────┬───────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│ Trinity Kernel (.ai/cli)                 │
└──────────────────────────────────────────┘
```

1. **Universal Shell** (`trinity-shell` — Phase 8 binary) — the single CLI
   that vendor adapters call.
2. **Vendor Adapters** — vendor-specific config (`.claude/skills/`,
   `AGENTS.md` directives, `.cursor/rules/`) that defer to the Universal
   Shell.

## What's IN this folder

Each subfolder is **one short code**. Canonical SHIM.md files describe:

- **Purpose** — what the short code does (vendor-agnostic)
- **Inputs** — args, context the kernel will need
- **Outputs** — artifacts, state transitions, exit codes
- **Behavior contract** — must-do, must-not-do (per Trinity boundaries)
- **Adapter rendering hints** — what vendor adapters should expose to the user

```
.ai/shims/
├── README.md           ← this file
├── lll/SHIM.md         ← Look/List status
├── vvv/SHIM.md         ← Verify understanding
├── nnn/SHIM.md         ← New plan with estimates
├── gogogo/SHIM.md      ← Execute plan
└── rrr/SHIM.md         ← Retrospective
```

Two short codes from the entry files (`sss`, `ddd`) deliberately do **not**
have shims yet — they involve human gates and live policies; they'll land in
Phase 1+ when the kernel implements graph-driven session state.

## What's NOT in this folder (yet)

- ❌ Vendor adapters (`.claude/skills/`, `.cursor/rules/`, `.warp/workflows/`).
  Per Decision **D7**, no adapter is installed in trinity_v2. They're
  **generated** from these canonical shims by Phase 8 tooling.
- ❌ Adapter-rendering scripts. The generator pipeline is Phase 8 work.
- ❌ Any vendor-specific behavior (<upstream-project>'s <upstream-project>/.claude/skills format is
  Claude Code's; Warp uses Workflow YAML; Codex uses AGENTS.md prose). Each
  adapter chooses its own format from the canonical SHIM.md.

## Reference: <upstream-project> skills

`references/shims/upstream-skills/` (added Commit 6) holds <upstream-project>'s actual
Claude Code skill folders as **DNA reference** for how a real project wired
short codes. Use it as a **pattern reference only** — don't copy its
implementation directly (D7).

## How an adapter author uses these

1. Read the canonical SHIM.md for the short code
2. Read `07_SHIM_SPEC.md §4–§9` for vendor-adapter conventions
3. Write a vendor-specific renderer (Claude skill / Cursor rule / etc.) that
   calls `trinity-shell <code>` with the right args
4. Commit the adapter to a vendor-specific subdirectory (`.claude/skills/`,
   `.cursor/rules/`, etc.) — never to this canonical folder

## Boundaries

- ❌ Don't edit canonical SHIM.md to favor a specific vendor's UX
- ❌ Don't install vendor adapters in trinity_v2 (D7)
- ❌ Don't copy from `references/shims/upstream-skills/` directly
- ✅ Do reference Trinity short-code docs (`docs/ai_entry/SHORT_CODES.md`)
  for user-facing wording
- ✅ Do propose updates as PRs against the canonical SHIM.md if behavior
  needs to change globally
