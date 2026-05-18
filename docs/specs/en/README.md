---
title: "Trinity OS"
subtitle: "CLI-Native AI Microkernel · Knowledge Brain · Reasoning Engine · Verifier"
language: English
last-updated: 2026-04-28
status: spec-pack-v1.0.0
license: MIT
---

# 🌌 Trinity OS

> **A CLI-native AI microkernel where ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

---

## What is Trinity OS?

Trinity OS is **not** another AI tool. It's a **deterministic harness layer** around vendor AI tools (Claude Code, Codex CLI, Cursor, Gemini CLI) that:

- **Coordinates** AI workflow with hard gates and audit
- **Recalls** past decisions via Knowledge Brain (semantic search)
- **Judges** outcomes deterministically (file-based rules)
- **Persists** state across sessions (capsules + checkpoints)
- **Composes** capabilities through CLI tools (stdin/stdout JSON)

### The Insight

Anthropic's public statement: *"1.6% of Claude Code is AI logic; 98.4% is deterministic harness."*

Trinity OS embraces this: it's **~100% deterministic harness** that delegates the 1.6% reasoning to vendor AI. Your AI doesn't get smarter — your *system around the AI* gets smarter.

---

## Why Trinity OS?

### Problems It Solves

| Pain | Trinity Solution |
|------|------------------|
| AI loses context across sessions | Knowledge Brain (memory-cli) recalls past work |
| AI hallucinates without evidence | Verifier requires artifacts before PASS |
| No audit trail when AI makes mistakes | Hash-chain `events.ndjson` |
| Tools locked to one vendor | CLI-first (works with any AI tool) |
| AI says "done" but isn't | Verdict types (PASS/RETRY/NEEDS_HUMAN/DEAD) |
| Multi-step work breaks halfway | Goal tree + checkpoint/resume |
| Bootstrap new project → AI doesn't know workflow | Bootstrap Pack (templates + install.sh) |

### Who It's For

- **Production AI workflows** needing audit, rollback, compliance
- **Multi-tool teams** (Claude/Codex/Gemini/Cursor — pick your favorite)
- **Long-running tasks** that must "complete" not just "respond"
- **Teams that want discipline** without sacrificing speed

---

## Architecture (5 Layers)

```
┌──────────────────────────────────────────────┐
│ 👤 USER / GOAL                              │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 🪞 VENDOR HARNESS (Reasoning Engine)         │
│ Claude Code · Codex · Cursor · Gemini · Warp │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 🔌 TRINITY SHIM (vendor adapters)            │
│ Skills · AGENTS.md · .cursor/rules · hooks   │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ ⚙️  TRINITY KERNEL (Coordinator + Judge)     │
│ Sessions · Loop · Graph · Policy · Audit     │
└──────────┬───────────────────────┬───────────┘
           ▼                       ▼
┌────────────────────┐  ┌─────────────────────┐
│ 🧠 KNOWLEDGE BRAIN │  │ 🛠 CLI TOOL USERLAND│
│ ai-docs +          │  │ browser-cli         │
│ memory-cli         │  │ memory-cli          │
│ retros · lessons   │  │ verify-cli          │
│ (semantic recall)  │  │ retro-cli           │
│                    │  │ ftp-cli (future)    │
└────────────────────┘  └─────────────────────┘
```

### The Iron Triangle

Every agentic system needs all three:

```
┌──────────┐   ┌──────────┐   ┌──────────┐
│ HARNESS  │ + │   LOOP   │ + │  GRAPH   │
│ Interface│   │   Heart  │   │ Skeleton │
└──────────┘   └──────────┘   └──────────┘
```

- **Harness** — vendor's UI (we don't rebuild)
- **Loop** — runs until done (goal tree + checkpoint)
- **Graph** — workflow state machine (with explicit `decided_by`)

Without any one → system can't complete tasks.

---

## Key Decisions (10 Commitments)

1. **Trinity = Coordinator/Judge**, not full AI harness
2. **ai-docs = Knowledge Brain**, not autonomous planner
3. **Vendor AI = Reasoning Engine**
4. **CLI-first only** for core tools
5. **MCP external servers ≠ core path** (we replaced Playwright/Morphllm/Sequential MCP with CLI tools)
6. **Tool Contract** must exist before new tools
7. **Bootstrap Pack** mandatory for project portability
8. **Verifier rules** must be file-based (YAML — not in code)
9. **Loop must support goal tree** + checkpoints (not just linear)
10. **Graph transitions** must declare `decided_by` (verifier/policy/human/kernel)

---

## Core Workflow (5 Short Codes)

```bash
lll      # Status report (project + git + memory recall)
vvv      # Verify — 5 mandatory questions, evidence-based (BEFORE nnn)
nnn      # Plan — detailed implementation plan
gogogo   # Execute — Trinity loop runs to completion
rrr      # Retrospective — write structured retro, update memory
```

**Critical Rule:** `vvv` MUST come before `nnn`. Skipping = invalid session.

> **Real evidence:** Skipping vvv = 3+ days wasted. Using vvv = 30 minutes, correct first time.

---

## Vocabulary (Memorize These)

| Term | Meaning |
|------|---------|
| **Knowledge Brain** | ai-docs + memory-cli (recall layer) |
| **Reasoning Engine** | Vendor AI (Claude/Codex/Gemini) |
| **Coordinator** | Trinity Kernel (orchestration) |
| **Judge** | Verifier (verify-cli with file rules) |
| **Truth** | Artifacts + verdicts + audit log |
| **Organ** | CLI tool (browser-cli, memory-cli, etc.) |
| **Worker** | Vendor AI under coordination |

### Verdict Types

```
PASS         → continue (most common)
RETRY        → loop again with budget
NEEDS_HUMAN  → pause, ask user
DEAD         → terminate, audit
```

### Authority (for graph transitions)

```
verifier  → most automated transitions (90%)
policy    → safety/budget enforcement
human     → sensitive (promote/deploy/destructive)
kernel    → mechanical (entry/exit, retry)
```

---

## Quick Start

### 1. Prerequisites

```bash
bash 4+ · Python 3.10+ · Node 18+ · Git · SQLite 3.30+
+ at least one AI vendor tool (Claude Code recommended)
```

### 2. Bootstrap a New Project

```bash
mkdir my-project && cd my-project && git init

# (When Bootstrap Pack ships — Phase 0.5)
bash ~/code/trinity-bootstrap-pack/install.sh .

# Verify
bash ~/code/trinity-bootstrap-pack/verify-install.sh
```

### 3. First Session

```bash
# In your AI tool
> lll
# → Status report appears
# → AI knows the workflow

> vvv "Build a feature"
# → 5 mandatory questions
# → Search past similar work

> nnn
# → Plan with memory hints

> gogogo
# → Trinity loop runs, verifies each step

> rrr
# → Retro auto-indexed into memory
```

---

## Tool Ecosystem

### Current
- **browser-cli** — Browser automation (Playwright wrapper)

### Coming (Phase 1-7)
- **memory-cli** — Knowledge Brain recall (SQLite + FTS5)
- **verify-cli** — Judge with file-based rules
- **retro-cli** — Structured retrospective writer
- **trinity-shell** — Universal vendor adapter

### Future
- **wordpress-cli** — WP operations (wraps wp-cli)
- **ftp-cli** — FTP/SFTP file transfer (remote deploy, media sync)
- **seo-cli** — SEO audit
- **deploy-cli** — Deployment + rollback
- **god-team-cli** — Multi-agent dispatcher

All tools follow the same Tool Contract: stdin/stdout JSON, schema-locked, NDJSON logs, policy tiers.

---

## Project Structure

```
workspace-root/
├── TRINITY_LEGACY/              ← Trinity kernel + specs
│   ├── .ai/                      ← Production runtime
│   └── TRINITY_EVOLUTION/        ← v2 specs (16 docs, 13K lines)
│       ├── INDEX.md              ← Start here
│       ├── 00_BLUEPRINT.md       ← Master spec
│       ├── 00b_BOOTSTRAP_PACK.md ← Phase 0.5 scaffolding
│       ├── 01_TOOL_CONTRACT.md   ← POSIX of Trinity tools
│       ├── 02-07_*.md            ← Component specs
│       ├── 08_DIAGRAMS.md        ← 20 visual diagrams
│       ├── 09_DEPLOY_GUIDE.md    ← Operations runbook
│       ├── 10_UPSTREAM_AUDIT.md    ← Migration plan
│       ├── 11_RELATED_PROJECTS.md← Inspirations + attributions
│       ├── 12_GLOSSARY.md        ← A-Z glossary
│       ├── CHANGELOG.md
│       ├── CONTRIBUTING.md
│       ├── LICENSE_DECISION.md
│       └── en/                   ← English translations (THIS FOLDER)
│
├── ai-docs/                       ← Methodology framework v3
├── browser-cli/                   ← Reference CLI tool
└── <upstream-project>/                        ← Production project (largest user)
```

---

## Contributing

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) (Thai-primary) or [`./CONTRIBUTING_EN.md`](CONTRIBUTING_EN.md) (English — TBD).

### TL;DR
1. Read [`./INDEX.md`](INDEX.md) (English) or [`../INDEX.md`](../INDEX.md) (Thai)
2. Use Trinity workflow (lll → vvv → nnn → gogogo → rrr)
3. Follow Tool Contract for new tools
4. Submit PR with evidence + retro

---

## Inspirations

Trinity OS is built on shoulders of giants:

- **Anthropic Claude Code** — 1.6%/98.4% architecture insight (foundational)
- **Oracle Framework** (Soul-Brews-Studio) — append-only memory + supersession
- **arra-oracle-v3** (Soul-Brews-Studio) — hybrid SQLite/ChromaDB search reference
- **Unix philosophy** (Eric Raymond, 1978) — pipes, do-one-thing-well
- **Microkernel architecture** (L4, QNX, Plan 9) — small kernel + userspace
- **Cognition AI** (Devin team) — agent context fragility
- **<upstream-project>** — 240 retros + 14 lessons production data

See [`./11_RELATED_PROJECTS.md`](../11_RELATED_PROJECTS.md) for full attributions.

---

## Spec Pack Stats

```
16 documents · 13,000+ lines · 412 KB · ~5 hours full read
10 committed decisions · 5 critical fixes · 11 phases
20+ Mermaid diagrams · 100+ glossary terms
17-week realistic migration plan (<upstream-project>)
```

---

## License

MIT — see [`/LICENSE`](../../../LICENSE) (root) or [`./LICENSE_DECISION.md`](../LICENSE_DECISION.md) for rationale.

---

## Status

| Aspect | Score |
|--------|------|
| **Architecture Direction** | 9.5/10 — Vision crystallized |
| **Implementation Readiness** | 9.5/10 — Specs complete, ready to code |
| **Operational Readiness** | 9/10 — Runbook + troubleshooting |
| **Migration Readiness** | 9/10 — <upstream-project> 17-week plan |
| **Documentation Coverage** | 10/10 — 16 docs all aspects |

**Current phase:** Spec pack complete — ready for Sprint 1 implementation

---

## Reading Paths (English)

> The full English translation is in progress. Currently available in this folder:
> - `README.md` (this file) — public overview
> - `INDEX.md` — translated entry point
> - `00_BLUEPRINT.md` — translated master spec
> - `01_TOOL_CONTRACT.md` — translated tool contract
> - `12_GLOSSARY.md` — translated glossary

For full content, see Thai versions in parent directory:
- `../INDEX.md`
- `../00_BLUEPRINT.md`
- `../01_TOOL_CONTRACT.md` ... etc.

---

## Get In Touch

- 📖 Documentation: This folder + parent directory
- 🐛 Issues: (TBD — when public repo)
- 💬 Discussions: (TBD)
- 📜 Changelog: [`./CHANGELOG.md`](../CHANGELOG.md)

---

> 🌌 **Trinity OS — One brain, many organs, deterministic judgment, audited truth.**
