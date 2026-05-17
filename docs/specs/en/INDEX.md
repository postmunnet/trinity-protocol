---
title: "Trinity OS — Master Overview & Index (English)"
language: English
last-updated: 2026-04-28
read-time: 15 minutes
note: "Translation of ../INDEX.md — refer to Thai version for latest details"
---

# Trinity OS — Master Overview (English)

> **Read this single document = understand the whole Trinity OS system + every meaning + reading paths**

---

## Table of Contents

1. [Welcome](#1-welcome)
2. [The Big Picture](#2-the-big-picture)
3. [Project Family](#3-project-family)
4. [Vocabulary](#4-vocabulary)
5. [Component Index](#5-component-index)
6. [Roles & Responsibilities](#6-roles--responsibilities)
7. [Workflow Overview](#7-workflow-overview)
8. [Tool Ecosystem](#8-tool-ecosystem)
9. [State & Memory](#9-state--memory)
10. [Architecture Stack](#10-architecture-stack)
11. [Decision Log](#11-decision-log)
12. [Reading Paths](#12-reading-paths)
13. [Cheat Sheets](#13-cheat-sheets)
14. [FAQ](#14-faq)
15. [Spec Pack Index](#15-spec-pack-index)

---

## 1. Welcome

### What is Trinity OS?

> **Trinity OS** = AI-augmented work platform — a kernel that forces AI to work safely, auditably, and to completion.

**It is NOT:**
- ❌ A new AI tool
- ❌ An agent framework
- ❌ An MCP clone
- ❌ A replacement for Claude Code/Codex

**It IS:**
- ✅ A **CLI-native microkernel** for orchestrating AI workflow
- ✅ A **Knowledge Brain** that remembers past work and recalls semantically
- ✅ A **tool ecosystem** that's tool-agnostic (Claude/Codex/Gemini/Cursor all work)
- ✅ A **verifier-first** system that judges with rules, not AI guesses

### For Whom

| Persona | Why this matters |
|---------|-----------------|
| 👨‍💻 Developer | Don't start from zero every session |
| 🛠 DevOps/Operator | Audit trail, rollback, deploy safely |
| 🔍 Reviewer/Manager | See decision history + verifier verdicts |
| 🎓 Researcher | Pattern: deterministic harness > AI logic |
| 🏢 Enterprise | Compliance-ready (hash-chain audit) |

---

## 2. The Big Picture

### One-liner

> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

### One Diagram

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
│ slash commands · brain inject · audit log    │
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
│ retros (240+)      │  │ verify-cli          │
│ lessons (14+)      │  │ retro-cli           │
│                    │  │ ftp-cli (future)    │
└────────────────────┘  └─────────────────────┘
```

### Two Paragraphs

**The Problem:** AI working alone often hallucinates, loses context, and lacks audit trails. Production needs gates, retries, escalation, evidence — all of which Anthropic states comprises 98.4% of Claude Code (only 1.6% is AI logic).

**The Solution:** Trinity OS separates concerns clearly — vendor AI (Claude/Codex) handles "thinking", Trinity kernel handles "control + judgment", CLI tools handle "organs" (eyes/hands/memory), verifier handles "judgment" with file-based rules instead of model guesses. Everything communicates via stdin/stdout JSON — debuggable, tool-agnostic, composable.

---

## 3. Project Family

`<workspace-root>/` contains:

```
yai_project/
├── TRINITY_LEGACY/          ← Trinity kernel (development)
│   ├── .ai/                  ← Trinity runtime: cli, sessions, audit, policies
│   ├── archive/              ← Legacy AI docs
│   ├── references/           ← External AI harness study
│   └── TRINITY_EVOLUTION/    ← v2 specs (you are here!)
│       └── en/               ← English translations
│
├── ai-docs/                  ← Methodology Framework v3.0
│   ├── core/                 ← Workflow, Short codes
│   ├── tools/                ← Multi-tool routing guides
│   ├── prevention/           ← Anti-patterns
│   ├── standards/            ← Git, Code, Security
│   ├── real_lessons/         ← 12 real incidents
│   └── templates/            ← Ready-to-use templates
│
├── browser-cli/              ← Reference implementation
│   ├── index.js              ← single binary
│   ├── lib/                  ← Playwright wrapper
│   ├── docs/                 ← ARCHITECTURE, COMMAND_CONTRACT
│   └── tests/                ← harness, golden, schema
│
├── <upstream-project>/                   ← Production project (largest user)
│   ├── .ai/                  ← Trinity instance (1.7GB)
│   ├── ai-docs/              ← Project-specific methodology
│   ├── .claude/              ← Claude Code config + 240 retros
│   ├── CLAUDE.md / AGENTS.md ← AI entrypoints
│   └── ... (PHP+Smarty codebase)
│
└── (future)
    ├── memory-cli/           ← Phase 2
    ├── verify-cli/           ← Phase 4
    └── retro-cli/            ← Phase 7
```

---

## 4. Vocabulary

### Core Concepts

| Term | Meaning |
|------|---------|
| **Trinity OS** | The whole system (kernel + brain + tools + shim + harness) |
| **Knowledge Brain** | ai-docs + memory-cli (recall, NOT autonomous planner) |
| **Reasoning Engine** | Vendor AI (Claude/Codex/Gemini) — does planning |
| **Coordinator** | Trinity kernel — orchestrates loops, sessions |
| **Judge** | verify-cli + verifier-rules.yaml |
| **Truth** | Artifacts (files) + verdicts + audit log |
| **Organ** | CLI tool — capabilities (eyes/hands/memory) |
| **Worker** | Vendor AI doing actual work |

### Workflow Concepts

| Term | Meaning |
|------|---------|
| **Short codes** | `lll/vvv/nnn/gogogo/rrr` — 5-step workflow |
| **lll** | Status report |
| **vvv** | Verify (5 mandatory questions) |
| **nnn** | Plan |
| **gogogo** | Execute |
| **rrr** | Retrospective |
| **ccc** | Checkpoint |

### Verification Concepts

| Term | Meaning |
|------|---------|
| **Verdict** | PASS / RETRY / NEEDS_HUMAN / DEAD |
| **Pyramid of Judgment** | Verifier → Policy → LLM Judge → Human |
| **Rule Set** | Named verifier rules (e.g., `code_change`) |
| **Evidence** | Required artifact for verification |

### Architecture Layers

| Layer | Component |
|-------|-----------|
| 1 | Vendor Harness (Claude Code/Codex/etc.) |
| 2 | Trinity Shim (adapters) |
| 3 | Trinity Kernel (coordinator+judge) |
| 4a | Knowledge Brain (ai-docs+memory-cli) |
| 4b | CLI Tool Userland (organs) |

---

## 5. Component Index

### Where to find what

| You want... | Look at... |
|-------------|-----------|
| Master vision | `00_BLUEPRINT.md` (Thai) or [`00_BLUEPRINT.md`](00_BLUEPRINT.md) (English) |
| New project scaffold | `00b_BOOTSTRAP_PACK.md` |
| Write a CLI tool | `01_TOOL_CONTRACT.md` (English available) |
| How verifier works | `02_VERIFIER_SPEC.md` |
| How loop works | `03_GOAL_LOOP_SPEC.md` |
| Workflow graph | `04_GRAPH_SPEC.md` |
| memory-cli impl | `05_MEMORY_CLI_SPEC.md` |
| retro-cli impl | `06_RETRO_CLI_SPEC.md` |
| Vendor adapter | `07_SHIM_SPEC.md` |
| Visual diagrams | `08_DIAGRAMS.md` |
| Operations | `09_DEPLOY_GUIDE.md` |
| <upstream-project> migration | `10_UPSTREAM_AUDIT.md` |
| Inspirations | `11_RELATED_PROJECTS.md` |
| Glossary | [`12_GLOSSARY.md`](12_GLOSSARY.md) (English available) |

---

## 6. Roles & Responsibilities

### Component Responsibility Matrix

| Component | Decides | Proposes | Records | Executes |
|-----------|---------|----------|---------|----------|
| Vendor AI | ❌ | ✅ plan | ❌ | ✅ via tools |
| Trinity Kernel | ✅ orchestration | ❌ | ✅ events.ndjson | ✅ tool dispatch |
| Verifier | ✅ verdicts | ❌ | ✅ verdict log | ❌ |
| Policy | ✅ allow/deny | ❌ | ✅ violations | ❌ |
| Human | ✅ final | ❌ | (audit) | (manual) |
| CLI Tools | ❌ | ❌ | ✅ NDJSON | ✅ specific task |

### Authority Hierarchy

```
verifier   → most automated transitions (90%)
policy     → safety/budget enforcement
human      → sensitive ops (promote/deploy/destructive)
kernel     → mechanical (entry/exit, retry)
```

### Pyramid of Judgment

```
Human (final)
  ↑
LLM Judge (gated, audited)
  ↑
Policy Rules
  ↑
Verifier (deterministic)
```

### Anti-pattern

> **AI must NEVER be:** Thinker + Decider + Verifier — separation of concerns is hard rule

---

## 7. Workflow Overview

### Daily Flow

```
Session start:
  lll  → status + memory recall + goals review
  ↓
New task:
  vvv  → 5 questions, search past, evidence
  ↓ (verifier verdict: PASS)
  nnn  → plan with memory hints
  ↓ (human approves)
  gogogo → Trinity loop:
            - decompose to sub-goals
            - execute each via tools
            - verify each (verify-cli)
            - checkpoint
            - retry/escalate as needed
  ↓ (loop terminates)
  rrr  → write retro artifact → memory-cli index
```

### Standard Lifecycle

```
THINK → SANDBOX → DO → VERIFIED → PROMOTED → DEPLOYED → RETRO → DONE
                                                       ↘ FAILED
                                                       ↘ ESCALATED
```

---

## 8. Tool Ecosystem

### Current
- **browser-cli** — Browser automation (Playwright wrapper) ✅

### Planned
- **memory-cli** — Knowledge Brain recall (FTS5) — Phase 2
- **verify-cli** — Judge with file rules — Phase 4
- **retro-cli** — Structured retro writer — Phase 7
- **trinity-shell** — Universal vendor wrapper — Phase 8

### Future
- **wordpress-cli** — WP ops (wraps wp-cli)
- **ftp-cli** — FTP/SFTP file transfer (remote deploy, media sync)
- **seo-cli** — SEO audit
- **deploy-cli** — Deployment + rollback
- **god-team-cli** — Multi-agent dispatcher

### Vendor Tools (used as-is)
- Claude Code's Read/Write/Edit/Bash/Glob/Grep
- Codex CLI built-ins
- Gemini CLI built-ins
- Cursor built-ins

### Tools NOT Used (Decision #5)
- ❌ `mcp__playwright__*` (replaced by browser-cli)
- ❌ `mcp__morphllm-fast-apply__*` (vendor's built-in suffices)
- ❌ `mcp__sequential-thinking__*` (ai-docs ritual replaces)
- ✅ `mcp__ide__executeCode` (kept — vendor IDE bridge)

---

## 9. State & Memory

### Where State Lives

| Type | Location | Format |
|------|----------|--------|
| Session state | `.ai/sessions/<id>/loop_state.json` | JSON |
| Goal tree | `.ai/sessions/<id>/goals.yaml` | YAML |
| Project SSOT | `.ai/ssot.yaml` | YAML |
| Locks | `.ai/state/locks.json` | JSON |
| Audit log | `.ai/audit/events.ndjson` | NDJSON (append-only, hash-chain) |
| Tool registry | `.ai/tools.yaml` | YAML |
| Policies | `.ai/policies/*.yaml` | YAML |
| Graphs | `.ai/graphs/*.yaml` | YAML |

### Where Memory Lives

| Type | Location | Indexed |
|------|----------|---------|
| Retrospectives | `.claude/retrospectives/*.md` | ✅ via memory-cli |
| Real lessons | `ai-docs/real_lessons/*.md` | ✅ via memory-cli |
| Session summaries | `.ai/sessions/*/99_SUMMARY.md` | ✅ via memory-cli |
| Memory DB | `.memory/memory.db` | (the index) |

---

## 10. Architecture Stack

### 4 Layers

```
Layer 4: AI Tool Layer        Claude Code, Codex, Cursor, Gemini
  ↓
Layer 3: Trinity Shim         Adapters (skills, AGENTS.md, rules)
  ↓
Layer 2: Trinity Kernel       Sessions, loop, graph, policy, audit
  ↓
Layer 1: Userland             CLI tools (browser-cli, memory-cli, ...)
```

### Iron Triangle

```
Harness — interface to user (vendor + Trinity shim)
Loop    — heart of "complete the task" (goal tree + checkpoint)
Graph   — workflow skeleton (state machine + authority)

Missing any one → system fails:
- Without Harness → no user interaction
- Without Loop → can't continue till done
- Without Graph → no structure, AI guesses
```

---

## 11. Decision Log

### The 10 Committed Decisions

| # | Decision |
|---|----------|
| 1 | Trinity = Coordinator/Judge, not full AI harness |
| 2 | ai-docs = Knowledge Brain, not autonomous planner |
| 3 | Vendor AI = Reasoning Engine |
| 4 | CLI-first only for core tools |
| 5 | MCP external servers ≠ core path |
| 6 | Tool Contract before new tools |
| 7 | Bootstrap Pack mandatory for portability |
| 8 | Verifier rules file-based |
| 9 | Loop must support goal tree + checkpoints |
| 10 | Graph transitions must declare `decided_by` |

### The 5 Critical Fixes

| # | Issue | Fix |
|---|-------|-----|
| 1 | "Brain" too vague | Vocabulary locked: Knowledge Brain ≠ Brain |
| 2 | Verifier no rules | YAML rules + Pyramid of Judgment |
| 3 | Linear loop only | Goal tree + checkpoint/resume |
| 4 | Graph authority unclear | `decided_by` required |
| 5 | Bootstrap missing | Templates + install.sh |

---

## 12. Reading Paths

### By Persona

#### 👨‍💻 Developer (new)
1. README.md (this folder, public overview)
2. INDEX.md (this — overview)
3. 00_BLUEPRINT.md (vocabulary + decisions)
4. 08_DIAGRAMS.md (visual)
5. 01_TOOL_CONTRACT.md (write a tool)

#### 🛠 Operator
1. README.md
2. INDEX.md
3. 09_DEPLOY_GUIDE.md (full)
4. 10_UPSTREAM_AUDIT.md (migration)

#### 🔍 Reviewer/Manager
1. INDEX.md §1-4 (overview)
2. 00_BLUEPRINT.md §16-17 (decisions + roadmap)
3. 11_RELATED_PROJECTS.md (inspirations)

#### 🎓 Researcher
1. 00_BLUEPRINT.md (full)
2. 02_VERIFIER_SPEC.md (pyramid of judgment)
3. 03_GOAL_LOOP_SPEC.md (agentic loop)
4. 04_GRAPH_SPEC.md (transition authority)

---

## 13. Cheat Sheets

### One-liner

> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

### Vocabulary

```
Knowledge Brain    = ai-docs + memory-cli
Reasoning Engine   = Vendor AI
Coordinator        = Trinity Kernel
Judge              = Verifier
Truth              = Artifacts + Audit log
Organs             = CLI tools
Nerves             = JSON stdio
Worker             = Vendor AI
```

### Daily Commands

```bash
lll                        # Status + memory recall
vvv "task"                 # Verify (mandatory)
nnn                        # Plan
gogogo                     # Execute (Trinity loop)
ccc                        # Checkpoint
rrr                        # Retro + memory index
```

### Verdict Cheat Sheet

```
PASS         → continue (most common)
RETRY        → loop again with budget
NEEDS_HUMAN  → pause, ask user
DEAD         → terminate, audit
```

### Authority Cheat Sheet

```
verifier  → most automated transitions
policy    → safety/budget
human     → sensitive ops
kernel    → mechanical
```

---

## 14. FAQ

### Q: Why don't you use MCP at all?
**A:** MCP locks to Claude Code. Trinity vision = tool-agnostic (Claude/Codex/Gemini/Cursor all work). See [`../00_BLUEPRINT.md`](../00_BLUEPRINT.md) §9.

### Q: Why not build a new AI harness?
**A:** Anthropic uses dozens of devs × 2 years on Claude Code (98.4% harness). Don't replicate. Use vendor + thin shim.

### Q: <upstream-project> uses Trinity v1 — will v2 break it?
**A:** Migration is additive (Phases 0-2 don't affect existing workflow). See [`../10_UPSTREAM_AUDIT.md`](../10_UPSTREAM_AUDIT.md).

### Q: Can AI decide things on its own?
**A:** **No.** AI proposes, verifier/policy/human decides. See [`../02_VERIFIER_SPEC.md`](../02_VERIFIER_SPEC.md).

### Q: Will the loop run autonomously?
**A:** Yes, but with budget caps (tokens/time/retry) + escalation for sensitive ops + checkpoint resume.

### Q: Where does memory live?
**A:** SQLite FTS5 at `.memory/memory.db` (Phase 2) → ChromaDB hybrid (Phase 9 future).

### Q: SOC2/Compliance ready?
**A:** Yes — events.ndjson hash chain = tamper-evident audit.

### Q: Where to start?
**A:** Read this doc, then [`../00_BLUEPRINT.md`](../00_BLUEPRINT.md), then check Reading Paths §12.

---

## 15. Spec Pack Index

### All 16 documents

| # | Document | Purpose | Lines | English |
|---|----------|---------|-------|---------|
| 0 | INDEX.md (this) | Master overview | ~950 | ✅ |
| 1 | 00_BLUEPRINT.md | Master spec | 705 | ✅ |
| 2 | 00b_BOOTSTRAP_PACK.md | Phase 0.5 | 1,071 | ⏳ TBD |
| 3 | 01_TOOL_CONTRACT.md | Tool ABI | 1,298 | ✅ |
| 4 | 02_VERIFIER_SPEC.md | Judge | 710 | ⏳ TBD |
| 5 | 03_GOAL_LOOP_SPEC.md | Loop | 644 | ⏳ TBD |
| 6 | 04_GRAPH_SPEC.md | Graph | 710 | ⏳ TBD |
| 7 | 05_MEMORY_CLI_SPEC.md | Brain CLI | 832 | ⏳ TBD |
| 8 | 06_RETRO_CLI_SPEC.md | Retro CLI | 537 | ⏳ TBD |
| 9 | 07_SHIM_SPEC.md | Shim | 694 | ⏳ TBD |
| 10 | 08_DIAGRAMS.md | Diagrams | 877 | ⏳ TBD |
| 11 | 09_DEPLOY_GUIDE.md | Operations | 1,088 | ⏳ TBD |
| 12 | 10_UPSTREAM_AUDIT.md | Migration | 856 | ⏳ TBD |
| 13 | 11_RELATED_PROJECTS.md | Attributions | 803 | ⏳ TBD |
| 14 | 12_GLOSSARY.md | Glossary | 1,103 | ✅ |
| 15 | CHANGELOG.md | Version history | 340 | ⏳ TBD |
| 16 | CONTRIBUTING.md | Contribute guide | 530 | ✅ |
| 17 | LICENSE_DECISION.md | License rationale | 350 | ✅ |

**Currently in English:** INDEX.md, 00_BLUEPRINT.md, 01_TOOL_CONTRACT.md, 12_GLOSSARY.md, README.md, CONTRIBUTING.md, LICENSE_DECISION.md

**TBD English versions:** Other specs — translation in progress

---

## 16. Project Status

### Done ✅
- 16 documents (Thai-primary)
- 7 English versions (this folder)
- 10 decisions committed
- 5 critical fixes integrated
- Vocabulary locked
- Reading paths mapped

### Next 📋
- **Sprint 1 (P0):** Backup + add structures to <upstream-project>
- **Sprint 2 (P1):** browser-cli contract compliance
- **Sprint 3 (P2):** memory-cli build + index 240 retros
- **Sprint 4 (P3):** Wire memory into lll/vvv/nnn
- **Sprint 5 (P4):** Remove MCP servers
- **Sprint 6+ (P5-P10):** verifier, loop, graph, retro-cli, shim

### Implementation Readiness: 9.5/10

---

## See also

- [`README.md`](README.md) — Public-facing overview
- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master technical spec
- [`12_GLOSSARY.md`](12_GLOSSARY.md) — Complete glossary
- [`../INDEX.md`](../INDEX.md) — Thai version (more detailed)
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — How to contribute

---

> 🌌 **Trinity OS — One brain, many organs, deterministic judgment, audited truth.**
