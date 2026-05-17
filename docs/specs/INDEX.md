---
title: "Trinity OS — Master Overview & Index"
subtitle: "Single entry point · Glossary · Component map · Reading paths"
version: 1.0.0
status: master-reference
last-updated: 2026-04-28
audience: Everyone (developers, operators, reviewers, managers)
read-time: 15 minutes
---

# Trinity OS — Master Overview

> **อ่านเอกสารนี้ที่เดียว = เข้าใจทั้งระบบ Trinity OS + ทุกความหมาย + อ่านอะไรต่อตามจุดประสงค์**

---

## 📑 Table of Contents

1. [Welcome](#1-welcome) — What this is, For whom
2. [The Big Picture](#2-the-big-picture) — One diagram, two paragraphs
3. [Project Family](#3-project-family) — All `yai_project/` folders
4. [Vocabulary (Glossary)](#4-vocabulary-glossary) — ทุกคำมีความหมาย
5. [Component Index](#5-component-index) — Where to find what
6. [Roles & Responsibilities](#6-roles--responsibilities) — Who does what
7. [Workflow Overview](#7-workflow-overview) — Short codes + lifecycle
8. [Tool Ecosystem](#8-tool-ecosystem) — All CLI tools
9. [State & Memory](#9-state--memory) — Where things live
10. [Architecture Stack](#10-architecture-stack) — 4-layer model
11. [Decision Log](#11-decision-log) — 10 commitments
12. [Reading Paths](#12-reading-paths) — By persona
13. [Cheat Sheets](#13-cheat-sheets) — Quick reference
14. [FAQ](#14-faq) — Common questions
15. [Spec Pack Index](#15-spec-pack-index) — All 12 documents

---

## 1. Welcome

### 1.1 What is this?

> **Trinity OS** = AI-augmented work platform — kernel ที่บังคับให้ AI ทำงานปลอดภัย ตรวจสอบได้ และทำงานจนเสร็จ

ไม่ใช่:
- ❌ AI tool ตัวใหม่
- ❌ Agent framework
- ❌ MCP clone
- ❌ ระบบทดแทน Claude Code/Codex

ใช่:
- ✅ **CLI-native microkernel** สำหรับ orchestrate AI workflow
- ✅ **Knowledge Brain** ที่จำงานเก่าและ recall ได้ semantic
- ✅ **Tool ecosystem** ที่ tool-agnostic (Claude/Codex/Gemini/Cursor ใช้ได้หมด)
- ✅ **Verifier-first** ตัดสินด้วยกฎ ไม่ใช่ AI เดา

### 1.2 For Whom

| Persona | Why this matters |
|---------|-----------------|
| 👨‍💻 **Developer** | ทำงานกับ AI โดยไม่ต้องเริ่มจากศูนย์ทุก session |
| 🛠 **DevOps/Operator** | Audit trail, rollback, deploy safely |
| 🔍 **Reviewer/Manager** | เห็น decision history + verifier verdicts |
| 🎓 **Researcher** | Pattern: deterministic harness > AI logic |
| 🏢 **Enterprise** | Compliance-ready (hash-chain audit) |

### 1.3 Reading Paths

```text
Just want overview?       → Read this doc only (15 min)
Going to implement?        → INDEX → 00 → 01 → start coding
Going to operate?          → INDEX → 09 → 10
Going to review?           → INDEX → 00 → 11 (Decision Log)
Going to migrate <upstream-project>?   → INDEX → 10 → 09
```

---

## 2. The Big Picture

### One-liner

> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

### One Diagram

```text
┌──────────────────────────────────────────────────┐
│ 👤 USER / GOAL                                   │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 🪞 VENDOR HARNESS (Reasoning Engine)             │
│ Claude Code · Codex · Cursor · Gemini · Warp     │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 🔌 TRINITY SHIM (vendor adapters)                │
│ slash commands · brain inject · audit log        │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ ⚙️  TRINITY KERNEL (Coordinator + Judge)         │
│ Sessions · Loop · Graph · Policy · Audit         │
└──────────┬────────────────────────┬──────────────┘
           ▼                        ▼
┌──────────────────────┐  ┌─────────────────────────┐
│ 🧠 KNOWLEDGE BRAIN   │  │ 🛠 CLI TOOL USERLAND   │
│ ai-docs + memory-cli │  │ browser-cli, memory-cli │
│ retros (240+)        │  │ verify-cli, retro-cli   │
│ lessons (14+)        │  │ ftp-cli (future)        │
│                      │  │ wordpress-cli (future)  │
└──────────────────────┘  └─────────────────────────┘
```

### Two Paragraphs

**The Problem:** AI ที่ทำงานคนเดียวมัก hallucinate, ลืม context, และไม่มี audit. Production ต้องมี gate, retry, escalation, evidence — ทั้งหมดนี้ Anthropic บอกว่า 98.4% ของ Claude Code คือ harness ไม่ใช่ AI logic.

**The Solution:** Trinity OS แยกชั้นชัด — vendor AI (Claude/Codex) ทำหน้าที่ "คิด", Trinity kernel ทำหน้าที่ "ควบคุม + ตัดสิน", CLI tools ทำหน้าที่ "อวัยวะ" (ตา/มือ/ความจำ), verifier ทำหน้าที่ "ตุลาการ" ด้วยกฎที่อยู่ในไฟล์ ไม่ใช่ในโมเดล. ทั้งหมดทำงานผ่าน stdin/stdout JSON — debuggable, tool-agnostic, composable.

---

## 3. Project Family

`<workspace-root>/` มีโฟลเดอร์เกี่ยวข้องดังนี้:

```text
yai_project/
├── TRINITY_LEGACY/          ← Trinity kernel (development)
│   ├── .ai/                  ← Trinity runtime: cli, sessions, audit, policies, schemas
│   ├── archive/              ← Legacy AI docs, old sessions
│   ├── references/           ← External AI harness references (claw-code, openclaude, etc.)
│   ├── sessions/             ← Active development sessions
│   └── TRINITY_EVOLUTION/    ← 🆕 v2 specs (you are here!)
│       ├── INDEX.md          ← (this document)
│       ├── 00_BLUEPRINT.md
│       ├── 00b_BOOTSTRAP_PACK.md
│       ├── 01_TOOL_CONTRACT.md
│       ├── 02-07_*.md        ← per-component specs
│       └── 08-10_*.md        ← visuals, deploy, audit
│
├── ai-docs/                  ← Methodology Framework v3.0
│   ├── core/                 ← Workflow, Short codes, Verification
│   ├── tools/                ← Multi-tool routing guides
│   ├── prevention/           ← Anti-patterns, best practices
│   ├── standards/            ← Git, Code, Security
│   ├── real_lessons/         ← 12 real incidents
│   └── templates/            ← Ready-to-use templates
│
├── browser-cli/              ← Reference implementation
│   ├── index.js              ← single binary
│   ├── lib/                  ← Playwright wrapper, JSON contract
│   ├── docs/                 ← ARCHITECTURE, COMMAND_CONTRACT, etc.
│   └── tests/                ← harness, golden, schema tests
│
├── <upstream-project>/                   ← Production project (largest user of Trinity)
│   ├── .ai/                  ← Trinity instance (1.7GB)
│   ├── ai-docs/              ← Project-specific methodology
│   ├── .claude/              ← Claude Code config + 240 retros
│   ├── CLAUDE.md / AGENTS.md ← AI entrypoints
│   └── ... (PHP+Smarty codebase)
│
└── (future)
    ├── memory-cli/           ← Phase 2
    ├── verify-cli/           ← Phase 4
    ├── retro-cli/            ← Phase 7
    ├── wordpress-cli/        ← Future
    ├── ftp-cli/              ← Future (FTP/SFTP organ)
    └── trinity-shell/        ← Phase 8
```

### Cross-relationships

```text
TRINITY_LEGACY/           ← Source of truth for kernel + specs
        ↓ used by
<upstream-project>/                    ← Real production project
        ↓ informs
TRINITY_EVOLUTION/         ← v2 specs (lessons from <upstream-project>)
        ↓ defines
(future CLI tools)         ← memory-cli, verify-cli, retro-cli

browser-cli/               ← Reference DNA for all CLI tools
        ↓ pattern for
(future CLI tools)

ai-docs/                   ← Methodology (workflow knowledge)
        ↓ embedded in
<upstream-project>/ai-docs/            ← Customized per project
        ↓ same pattern as
Bootstrap Pack             ← Template for new projects
```

---

## 4. Vocabulary (Glossary)

### 4.1 Core Concepts

| Term | Meaning | Example |
|------|---------|---------|
| **Trinity OS** | The whole system — kernel + brain + tools + shim + harness | "We use Trinity OS for <upstream-project>" |
| **Knowledge Brain** | ai-docs + memory-cli — recall layer (NOT autonomous planner) | "Search the brain for past auth bugs" |
| **Reasoning Engine** | Vendor AI (Claude/Codex/Gemini) — does planning + decomposition | "Reasoning engine proposed 5 sub-goals" |
| **Coordinator** | Trinity kernel — orchestrates loops, sessions, state | "Kernel coordinated 12 tool calls" |
| **Judge** | verify-cli + verifier-rules.yaml — gives verdicts | "Judge returned PASS for code change" |
| **Truth** | Artifacts (files) + verdicts + audit log | "Truth = what's in events.ndjson" |
| **Organs** | CLI tools — capabilities (eyes/hands/memory) | "browser-cli is the eyes organ" |
| **Nervous system** | stdin/stdout JSON between kernel and tools | "Tool replied via the nerves" |
| **Audit trace** | events.ndjson hash-chain log | "Audit shows transition at 12:34" |
| **Worker** | Vendor AI doing the actual work | "Worker (Claude) generated the diff" |

### 4.2 Workflow Concepts

| Term | Meaning |
|------|---------|
| **Short codes** | `lll/vvv/nnn/gogogo/rrr` — 5-step workflow ritual |
| **lll** | Status report — see project + git + memory state |
| **vvv** | Verify — 5 mandatory questions, evidence-based |
| **nnn** | Plan — detailed implementation plan |
| **gogogo** | Execute — Trinity loop runs |
| **rrr** | Retrospective — write structured retro, update memory |
| **ccc** | Checkpoint — save loop state |
| **Goal** | Unit of work (epic / feature / task / subtask) |
| **Goal Tree** | Hierarchical decomposition of a root goal |
| **Sub-goal** | Child goal under a parent |
| **Loop** | Trinity iteration — observe → think → act → verify → decide |
| **Loop State** | `loop_state.json` — current goal, pending, done, blocked |
| **Iteration** | One pass of the loop |
| **Checkpoint** | Saved snapshot of loop state for resume |
| **Resume** | Continue from latest checkpoint after restart |
| **Termination** | Loop end (done / dead / escalated / cancelled) |

### 4.3 Verification Concepts

| Term | Meaning |
|------|---------|
| **Verifier** | Component that gives verdict (verify-cli) |
| **Verdict** | One of: PASS / RETRY / NEEDS_HUMAN / DEAD |
| **PASS** | Evidence sufficient + checks ok → continue |
| **RETRY** | Recoverable failure → loop again |
| **NEEDS_HUMAN** | Verifier unsure / sensitive op → ask user |
| **DEAD** | Unrecoverable → terminate session |
| **Rule Set** | Named collection of verifier rules (e.g. `code_change`) |
| **Evidence** | Artifact required for verification (file, log, screenshot) |
| **Pyramid of Judgment** | Verifier → Policy → LLM Judge → Human (escalation chain) |

### 4.4 Graph & Authority

| Term | Meaning |
|------|---------|
| **Graph** | Workflow state machine (YAML-defined) |
| **State** | Node in graph (e.g. THINK, SANDBOX, DO, VERIFIED) |
| **Transition** | Edge between states |
| **Trigger** | Event that fires a transition |
| **decided_by** | Authority for transition: `verifier / policy / human / kernel` |
| **Authority** | Who has the right to change state |
| **Conditions** | Pre-conditions for transition (e.g. tests pass) |
| **Side effects** | Actions on state entry/exit (commands, notifications) |

### 4.5 Architecture Layers

| Layer | Term | What it does |
|-------|------|--------------|
| 1 | **Vendor Harness** | Claude Code / Codex / Cursor / Gemini / Warp |
| 2 | **Trinity Shim** | Adapter layer (skills, AGENTS.md, rules) |
| 3 | **Trinity Kernel** | Sessions, loop, graph, policy, audit |
| 4a | **Knowledge Brain** | ai-docs + memory-cli (recall) |
| 4b | **CLI Tool Userland** | browser-cli, memory-cli, verify-cli, retro-cli, ftp-cli, ... |

### 4.6 File & Tool Concepts

| Term | Meaning |
|------|---------|
| **Tool Contract** | POSIX-equivalent for Trinity CLI tools — universal contract |
| **Action namespace** | `tool.verb` (e.g. `memory.search`, `browser.screenshot`) |
| **Envelope** | Standard JSON response wrapper (ok/data/artifacts/error/meta) |
| **Schema version** | Version of response format (`v1`, `v2`) |
| **Run ID** | Unique identifier for a tool invocation (correlation) |
| **Policy tier** | safe / normal / aggressive — limits which verbs allowed |
| **Helper** | YAML composition of commands (reusable workflow) |
| **Bootstrap Pack** | Templates + script to scaffold Trinity into new project |

### 4.7 Storage & Persistence

| Term | Meaning |
|------|---------|
| **Session** | Capsule of work (`.ai/sessions/<id>/`) |
| **Sandbox** | Isolated workspace per AI agent |
| **THINK** | Session phase — planning |
| **SANDBOX** | Session phase — agents work in isolation |
| **DO** | Session phase — apply changes to dev |
| **PROMOTED** | Session phase — code in prod-ready folder |
| **DEPLOYED** | Session phase — live in production |
| **events.ndjson** | Append-only hash-chain audit log |
| **Hash chain** | Each event has prev_hash + hash (tamper-evident) |
| **SSOT** | Single Source of Truth (`.ai/ssot.yaml`) |

### 4.8 Anthropic Insight

| Term | Meaning |
|------|---------|
| **1.6% / 98.4%** | AI logic (1.6%) vs deterministic harness (98.4%) in Claude Code |
| **Harness** | Deterministic scaffolding around AI (permissions, routing, sandbox) |
| **Iron Triangle** | Harness + Loop + Graph (must-have for agentic AI) |

---

## 5. Component Index

### 5.1 Where to find what

| You want... | Look at... |
|-------------|-----------|
| **Master vision** | `00_BLUEPRINT.md` |
| **How to scaffold new project** | `00b_BOOTSTRAP_PACK.md` |
| **How to write a CLI tool** | `01_TOOL_CONTRACT.md` |
| **How verifier works** | `02_VERIFIER_SPEC.md` |
| **How loop works** | `03_GOAL_LOOP_SPEC.md` |
| **How workflow graph works** | `04_GRAPH_SPEC.md` |
| **memory-cli implementation** | `05_MEMORY_CLI_SPEC.md` |
| **retro-cli implementation** | `06_RETRO_CLI_SPEC.md` |
| **vendor adapter (shim)** | `07_SHIM_SPEC.md` |
| **Visual diagrams** | `08_DIAGRAMS.md` |
| **Operations runbook** | `09_DEPLOY_GUIDE.md` |
| **<upstream-project> migration** | `10_UPSTREAM_AUDIT.md` |
| **All vocabulary** | This doc §4 |
| **Reading paths** | This doc §12 |

### 5.2 Code locations (current + future)

| Component | Location | Status |
|-----------|----------|--------|
| Trinity kernel | `<upstream-project>/.ai/cli/` (existing) | ✅ Production |
| Trinity kernel (canonical) | (future: `~/code/trinity-kernel/`) | 📋 |
| browser-cli | `~/yai_project/browser-cli/` | ✅ Production |
| memory-cli | (future: `~/yai_project/memory-cli/`) | 📋 Phase 2 |
| verify-cli | (future: `~/yai_project/verify-cli/`) | 📋 Phase 4 |
| retro-cli | (future: `~/yai_project/retro-cli/`) | 📋 Phase 7 |
| trinity-shell | (future: `~/yai_project/trinity-shell/`) | 📋 Phase 8 |
| Bootstrap Pack | (future: `~/yai_project/trinity-bootstrap-pack/`) | 📋 Phase 0.5 |

### 5.3 Per-project Trinity instance

```
<project-root>/
├── CLAUDE.md / AGENTS.md / GEMINI.md  ← AI entrypoints (Bootstrap Pack)
├── .ai/                                ← Trinity instance
│   ├── ssot.yaml                       ← project paths
│   ├── tools.yaml                      ← tool registry
│   ├── policies/
│   │   ├── safety.yaml
│   │   ├── verifier-rules.yaml
│   │   └── loop-budget.yaml
│   ├── graphs/
│   │   ├── standard.yaml
│   │   └── deploy.yaml
│   ├── schemas/                        ← JSON Schemas
│   ├── sessions/                       ← session capsules
│   ├── audit/events.ndjson             ← hash-chain log
│   └── cli/                            ← Trinity Python CLI
├── ai-docs/                            ← Knowledge Brain (markdown)
│   ├── retrospectives/                 ← past retros (memory-cli indexes)
│   ├── real_lessons/                   ← incidents
│   ├── core/                           ← methodology
│   ├── tools/                          ← tool routing guides
│   ├── prevention/                     ← anti-patterns
│   ├── standards/                      ← code standards
│   └── templates/                      ← retro/plan templates
├── .claude/                            ← Claude Code config
│   ├── settings.local.json             ← permissions
│   ├── skills/                         ← Trinity Shim adapters
│   └── retrospectives/                 ← (or ai-docs/retrospectives/)
└── .memory/                            ← memory-cli SQLite DB
    └── memory.db
```

---

## 6. Roles & Responsibilities

### 6.1 Component Responsibility Matrix

| Component | Decides | Proposes | Records | Executes |
|-----------|---------|----------|---------|----------|
| **Vendor AI** | ❌ | ✅ plan, decomposition | ❌ | ✅ via tools |
| **Trinity Kernel** | ✅ orchestration | ❌ | ✅ events.ndjson | ✅ tool dispatch |
| **Verifier** | ✅ verdicts | ❌ | ✅ verdict log | ❌ |
| **Policy** | ✅ allow/deny | ❌ | ✅ violations | ❌ |
| **Human** | ✅ final | ❌ | (audit) | (manual) |
| **CLI Tools** | ❌ | ❌ | ✅ NDJSON | ✅ specific task |
| **Brain (memory-cli)** | ❌ | ✅ context | ❌ | ❌ |

### 6.2 Authority Hierarchy (for transitions)

```text
verifier   → most automated transitions (90%)
policy     → safety/budget enforcement
human      → sensitive ops (promote/deploy/destructive)
kernel     → mechanical (entry/exit, retry)
```

### 6.3 Pyramid of Judgment

```
   Human (final)
      ↑
   LLM Judge (gated, audited)
      ↑
   Policy Rules
      ↑
   Verifier (deterministic)
```

### 6.4 Anti-pattern (don't do this)

> **AI must NEVER be:** Thinker + Decider + Verifier — separation of concerns is hard rule

---

## 7. Workflow Overview

### 7.1 Daily Flow

```text
Session start:
  lll  → status, memory recall, goals review
  ↓
New task:
  vvv  → 5 questions, search past, evidence
  ↓ (verify-cli verdict: PASS)
  nnn  → plan with memory hints
  ↓ (human approves)
  gogogo → Trinity loop:
            - decompose to sub-goals
            - execute each via tools
            - verify each (verify-cli)
            - checkpoint
            - retry/escalate as needed
  ↓ (loop terminates: all done)
  rrr  → write retro artifact → memory-cli index
  ↓
Session end (auto checkpoint)
```

### 7.2 Lifecycle States (Standard Graph)

```
THINK → SANDBOX → DO → VERIFIED → PROMOTED → DEPLOYED → RETRO → DONE
                                                      ↘ FAILED
                                                      ↘ ESCALATED
```

### 7.3 Verdict Flow

```text
Tool execute → verify-cli → 
  PASS         → next state
  RETRY        → requeue (with budget)
  NEEDS_HUMAN  → pause, ask user
  DEAD         → terminate
```

---

## 8. Tool Ecosystem

### 8.1 All CLI Tools

| Tool | Purpose | Status | Phase | Action namespace |
|------|---------|--------|-------|-----------------|
| **browser-cli** | Browser automation (Playwright wrapper) | ✅ | - | `browser.*` |
| **memory-cli** | Knowledge Brain recall (FTS5) | 🆕 | 2 | `memory.*` |
| **verify-cli** | Judge with file rules | 🆕 | 4 | `verify.*` |
| **retro-cli** | Structured retro writer | 🆕 | 7 | `retro.*` |
| **trinity-shell** | Universal vendor harness wrapper | 🆕 | 8 | `trinity.*` |
| **wordpress-cli** | WP ops (wraps wp-cli) | 📋 | future | `wordpress.*` |
| **ftp-cli** | FTP/SFTP file transfer (remote deploy, sync) | 📋 | future | `ftp.*` |
| **seo-cli** | SEO audit | 📋 | future | `seo.*` |
| **deploy-cli** | Deployment + rollback | 📋 | future | `deploy.*` |
| **grep-cli** | Smart code search | 📋 | future | `code.*` |
| **god-team-cli** | Multi-agent dispatcher | 📋 | future | `god.*` |

### 8.2 Vendor Tools (used as-is)

```text
Claude Code built-in:  Read, Write, Edit, Bash, Glob, Grep, ...
Codex built-in:        File ops, shell exec
Gemini built-in:       File ops, web search
Cursor built-in:       File ops, terminal
```

→ ใช้ของ vendor ตามปกติ (decision: don't replicate)

### 8.3 Tools NOT Used (Decision #5)

```text
❌ mcp__playwright__*        (replaced by browser-cli)
❌ mcp__morphllm-fast-apply__* (replaced by vendor built-in)
❌ mcp__sequential-thinking__* (replaced by ai-docs workflow)
✅ mcp__ide__executeCode      (kept — vendor IDE bridge)
```

---

## 9. State & Memory

### 9.1 Where State Lives

| Type | Location | Format | TTL |
|------|----------|--------|-----|
| **Session state** | `.ai/sessions/<id>/loop_state.json` | JSON | per-session |
| **Goal tree** | `.ai/sessions/<id>/goals.yaml` | YAML | per-session |
| **Project SSOT** | `.ai/ssot.yaml` | YAML | persistent |
| **Locks** | `.ai/state/locks.json` | JSON | runtime |
| **Audit log** | `.ai/audit/events.ndjson` | NDJSON | append-only forever |
| **Tool registry** | `.ai/tools.yaml` | YAML | persistent |
| **Policies** | `.ai/policies/*.yaml` | YAML | persistent |
| **Graphs** | `.ai/graphs/*.yaml` | YAML | persistent |

### 9.2 Where Memory Lives

| Type | Location | Format | Indexable |
|------|----------|--------|-----------|
| **Retrospectives** | `.claude/retrospectives/*.md` | Markdown + frontmatter | ✅ via memory-cli |
| **Real lessons** | `ai-docs/real_lessons/*.md` | Markdown | ✅ via memory-cli |
| **Session summaries** | `.ai/sessions/*/99_SUMMARY.md` | Markdown | ✅ via memory-cli |
| **Memory DB** | `.memory/memory.db` | SQLite + FTS5 | (the index) |
| **Decisions** | `ai-docs/decisions/*.md` | Markdown | ✅ via memory-cli |
| **Patterns** | `ai-docs/patterns/*.md` | Markdown | ✅ via memory-cli |

### 9.3 Audit Truth

```text
.ai/audit/events.ndjson:
  • Append-only NDJSON
  • Every event = JSON line
  • Each line has prev_hash + hash (chain)
  • Tampering detectable
  • Compliance-ready (SOC2, ISO27001)
```

---

## 10. Architecture Stack

### 10.1 4 Layers

```
Layer 4: AI Tool Layer        Claude Code, Codex, Cursor, Gemini
  ↓
Layer 3: Trinity Shim         Adapters (skills, AGENTS.md, rules)
  ↓
Layer 2: Trinity Kernel       Sessions, loop, graph, policy, audit
  ↓
Layer 1: Userland             CLI tools (browser-cli, memory-cli, ...)
```

### 10.2 Iron Triangle

```text
Harness + Loop + Graph

Harness — interface to user (vendor harness + Trinity shim)
Loop    — heart of "ทำจนจบ" (goal tree + checkpoint)
Graph   — workflow skeleton (state machine + authority)

ขาดไหนก็ไม่ทำงาน:
- Without Harness → no user interaction
- Without Loop → can't continue till done
- Without Graph → no structure, AI guesses
```

### 10.3 Brain / Judge / Truth

```text
Brain  = ai-docs + memory-cli   → recall
Judge  = verify-cli + rules     → verdict
Truth  = artifacts + audit log  → evidence

Vendor AI = thinker (under Trinity coordination)
Trinity   = coordinator + judge orchestrator
```

---

## 11. Decision Log

### 11.1 The 10 Committed Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Trinity = **Coordinator/Judge**, not full AI harness | Don't replicate Anthropic's 98.4% harness |
| 2 | ai-docs = **Knowledge Brain**, not autonomous planner | Brain = recall, not reasoning |
| 3 | Vendor AI = **Reasoning Engine** | Use what's good, don't rebuild |
| 4 | **CLI-first only** for core tools | Tool-agnostic + debuggable + composable |
| 5 | **MCP external servers ≠ core path** | Don't lock to Claude Code |
| 6 | **Tool Contract** before new tools | Prevent integration hell |
| 7 | **Bootstrap Pack** mandatory | Solve portability (the original pain) |
| 8 | **Verifier rules** file-based | AI can't be sole judge |
| 9 | **Loop must support goal tree** + checkpoints | Real work isn't linear |
| 10 | **Graph transitions** must declare `decided_by` | Authority must be explicit |

### 11.2 The 5 Critical Fixes (from feedback)

| # | Issue | Fix |
|---|-------|-----|
| 1 | "Brain" too vague | Vocabulary locked: Knowledge Brain ≠ Brain |
| 2 | Verifier no rules | YAML rules + Pyramid of Judgment |
| 3 | Linear loop only | Goal tree + sub-goals + checkpoint/resume |
| 4 | Graph authority unclear | `decided_by` required (verifier/policy/human/kernel) |
| 5 | Bootstrap missing | Templates + install.sh + verify-install.sh |

### 11.3 What's Not in v0.1 (Deferred)

```text
- Full AI harness (use vendor's)
- Full MCP server as core
- Platform registry (Phase 10)
- Android-style extension SDK
- Big dashboard
- Multi-agent graphs (complex)
- ChromaDB before FTS5
- Auto deploy / auto PR
```

---

## 12. Reading Paths

### 12.1 By Persona

#### 👨‍💻 Developer (new to project)
```
1. INDEX.md (this) — overview
2. 00_BLUEPRINT.md — vocabulary + decisions
3. 08_DIAGRAMS.md — visual mental model
4. 01_TOOL_CONTRACT.md — how to write a tool
5. 09_DEPLOY_GUIDE.md §2 — first install
```

#### 🛠 Operator / DevOps
```
1. INDEX.md (this)
2. 00_BLUEPRINT.md §1-3 — what it is
3. 09_DEPLOY_GUIDE.md (full) — operations
4. 10_UPSTREAM_AUDIT.md — migration plan
```

#### 🔍 Reviewer / Manager
```
1. INDEX.md (this) §1-4 — overview
2. 00_BLUEPRINT.md §16-17 — decisions + roadmap
3. 11 (this doc §11) — decision log
4. 10_UPSTREAM_AUDIT.md §1, §10 — exec summary + metrics
```

#### 🎓 Researcher / Architect
```
1. 00_BLUEPRINT.md (full)
2. 02_VERIFIER_SPEC.md — pyramid of judgment
3. 03_GOAL_LOOP_SPEC.md — agentic loop design
4. 04_GRAPH_SPEC.md — transition authority
5. 07_SHIM_SPEC.md — vendor neutrality strategy
```

#### 🏢 Compliance / Audit
```
1. 00_BLUEPRINT.md §10 — Governance/Gates
2. 02_VERIFIER_SPEC.md §7 — Audit Trail
3. 04_GRAPH_SPEC.md §10 — Audit & Replay
4. 09_DEPLOY_GUIDE.md §10, §13 — Security + DR
```

### 12.2 By Goal

| You want to... | Read in this order |
|----------------|-------------------|
| **Understand** the whole system | INDEX → 00 → 08 |
| **Implement** Phase 1 (Tool Contract) | 01 → 05 (memory-cli example) |
| **Implement** Phase 2 (memory-cli) | 05 → 01 → browser-cli reference |
| **Implement** Phase 4 (verifier) | 02 → 03 → 04 |
| **Migrate** <upstream-project> | 10 → 09 → 00b |
| **Set up** new project | 00b → 09 §2 |
| **Train** team on vocabulary | INDEX §4 → 13 (cheat sheets) |
| **Audit** compliance | 11 → 02 §7 → 04 §10 |
| **Troubleshoot** an issue | 09 §8 |
| **Plan** a sprint | 00 §17 → 10 §3 |

### 12.3 Time Budget

| Read time | What you'll know |
|-----------|------------------|
| 5 min | This doc §1-§4 → vocabulary basics |
| 15 min | This doc (full) → overview + reading paths |
| 30 min | INDEX + 00_BLUEPRINT → architecture |
| 1 hour | INDEX + 00 + 08 + relevant spec → ready to implement |
| 4 hours | All 12 specs → expert |

---

## 13. Cheat Sheets

### 13.1 One-liner

> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

### 13.2 Vocabulary (Memorize)

```text
Knowledge Brain    = ai-docs + memory-cli
Reasoning Engine   = Vendor AI (Claude/Codex/Gemini)
Coordinator        = Trinity Kernel
Judge              = Verifier (verify-cli)
Truth              = Artifacts + Audit log
Organs             = CLI tools
Nerves             = JSON stdio
Worker             = Vendor AI (under coordination)
```

### 13.3 Daily Commands

```bash
lll                        # Status + memory recall
vvv "task description"     # Verify (mandatory before nnn)
nnn                        # Plan
gogogo                     # Execute (Trinity loop)
ccc                        # Checkpoint
rrr                        # Retrospective + memory index
```

### 13.4 Decision Tree

```text
Need to start work?           → lll
Have a goal?                  → vvv
Verified evidence?            → nnn
Plan approved?                → gogogo
Loop running?                 → (Trinity handles)
Verdict NEEDS_HUMAN?          → answer prompt
Done?                         → rrr
```

### 13.5 Verdict Cheat Sheet

```text
PASS         → continue (most common)
RETRY        → loop again with budget
NEEDS_HUMAN  → pause, ask user
DEAD         → terminate, audit
```

### 13.6 Authority Cheat Sheet

```text
verifier  → most automated transitions (90%)
policy    → safety/budget
human     → sensitive (promote/deploy/destructive)
kernel    → mechanical (entry/exit, retry)
```

### 13.7 Tool Contract Essentials

```text
Every tool MUST have:
1. stdin/stdout JSON
2. Schema-locked envelope
3. --config / --run-id / --log-file
4. Policy tier (safe/normal/aggressive)
5. NDJSON logging
6. Action namespace (tool.verb)
7. --health endpoint
8. Tests (harness + golden)
9. Documentation suite
10. Contract compliance test
```

### 13.8 Phase Roadmap

```text
Phase 0    Vocabulary Lock          ✅ Done
Phase 0.5  Bootstrap Pack            🆕 Start here
Phase 1    Tool Contract             🔧 Critical
Phase 2    memory-cli                🧠 ROI highest
Phase 3    Wire memory               🔗
Phase 4    verify-cli                ⚖️ Critical
Phase 5    Goal Tree + Loop          🌀 Critical
Phase 6    Graph YAML                🕸 Critical
Phase 7    retro-cli                 📝
Phase 8    Trinity Shim              🔌
Phase 9    Hybrid memory (vector)    🚀 Future
Phase 10   Extension Platform        🌐 Future
```

---

## 14. FAQ

### Q: ทำไมไม่ใช้ MCP เลย?
**A:** MCP ผูกกับ Claude Code อย่างเดียว — vision คือ tool-agnostic ที่ Claude/Codex/Gemini/Cursor ใช้ได้หมด ผ่าน CLI ดู [`00_BLUEPRINT.md` §9](00_BLUEPRINT.md#9-mcp-stance--locked).

### Q: ทำไมไม่สร้าง AI harness ใหม่ล่ะ?
**A:** Anthropic ใช้ทีมหลายสิบคน + 2 ปีทำ Claude Code (98.4% harness) — เราไม่ควรทำซ้ำ ใช้ของ vendor + ทำ shim บาง ๆ ดู [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md).

### Q: <upstream-project> ใช้ Trinity v1 อยู่ — เปลี่ยน v2 พังไหม?
**A:** Migration เป็น additive (Phase 0-2) ไม่กระทบ workflow เก่า ดู [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md) §3 + §6.

### Q: AI ตัดสินเองได้ไหม?
**A:** **ไม่ได้** AI proposes, verifier/policy/human decides ดู [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §5.

### Q: Loop จะทำงานเองตลอดเลยเหรอ?
**A:** มี budget cap (tokens/time/retry) + escalation ทุก sensitive op + checkpoint resume ดู [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §4-5.

### Q: เก็บ memory ที่ไหน?
**A:** SQLite FTS5 ที่ `.memory/memory.db` (Phase 2) → ChromaDB hybrid (Phase 9 future) ดู [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md).

### Q: ต้อง Python หรือ Node?
**A:** Trinity kernel = Python (existing <upstream-project>). CLI tools = Node (browser-cli pattern) — แต่ tool ต่อไปเขียนภาษาอะไรก็ได้ตราบที่ตาม Tool Contract.

### Q: Compliance / SOC2 ทำได้ไหม?
**A:** ได้ — events.ndjson hash chain = tamper-evident audit ดู [`00_BLUEPRINT.md` §10](00_BLUEPRINT.md) + [`02_VERIFIER_SPEC.md` §7](02_VERIFIER_SPEC.md).

### Q: ต้องติดตั้งอะไรบ้าง?
**A:** Bash 4+ · Python 3.10+ · Node 18+ · Git · SQLite 3.30+ · Vendor AI tool (Claude Code recommended) ดู [`09_DEPLOY_GUIDE.md` §1](09_DEPLOY_GUIDE.md).

### Q: เริ่มที่ไหน?
**A:** Read this doc first, then [`00_BLUEPRINT.md`](00_BLUEPRINT.md), then check Reading Paths §12 above based on your role.

---

## 15. Spec Pack Index

### Complete document list (12 files, 10,007 lines)

| # | Document | Purpose | Lines | Read time |
|---|----------|---------|-------|-----------|
| 0 | [`INDEX.md`](INDEX.md) | This document — master overview | ~700 | 15 min |
| 1 | [`00_BLUEPRINT.md`](00_BLUEPRINT.md) | Master spec v2 | 693 | 30 min |
| 2 | [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) | Phase 0.5 portability | 1,071 | 25 min |
| 3 | [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) | Universal CLI contract | 1,298 | 30 min |
| 4 | [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) | Judge with rules | 710 | 20 min |
| 5 | [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) | Goal tree + loop | 644 | 20 min |
| 6 | [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) | Workflow + authority | 710 | 20 min |
| 7 | [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) | Knowledge Brain CLI | 830 | 25 min |
| 8 | [`06_RETRO_CLI_SPEC.md`](06_RETRO_CLI_SPEC.md) | Structured retro | 537 | 15 min |
| 9 | [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md) | Vendor adapter | 693 | 20 min |
| 10 | [`08_DIAGRAMS.md`](08_DIAGRAMS.md) | Visual diagrams | 877 | 20 min |
| 11 | [`09_DEPLOY_GUIDE.md`](09_DEPLOY_GUIDE.md) | Operations | 1,088 | 30 min |
| 12 | [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md) | Migration plan | 856 | 25 min |
| 13 | [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) | Inspirations + attributions | 803 | 15 min |
| 14 | [`12_GLOSSARY.md`](12_GLOSSARY.md) | Complete A-Z glossary | ~1000 | (lookup) |
| 15 | [`13_NOTIFY_CLI_SPEC.md`](13_NOTIFY_CLI_SPEC.md) | Audit-event bridge sibling (Tier 0) | ~480 | 15 min |
| 16 | [`14_TRINITY_TG_BOT_SPEC.md`](14_TRINITY_TG_BOT_SPEC.md) | Telegram remote-dev bot sibling (Tier 0) | ~720 | 25 min |
| — | [`../constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md`](../constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md) | Ritual Constitution v1.1-rc *(RC_PENDING_EMPIRICAL_RATIFICATION, Article XII.5)* — meta-rule layer above Ritual Contract v1.0; **relocated to `docs/constitution/`** per Addendum v1.0.2 | ~1,985 | 45 min |
| 17 | [`CHANGELOG.md`](CHANGELOG.md) | Version history of spec pack | ~350 | 10 min |
| Ph3 | [`TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md`](TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md) | Phase 3 — Verification Contract (pyramid + verdicts + audit hooks) | ~1023 | 30 min |
| Ph4 | [`TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md`](TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md) | Phase 4 — Kernel State Machine (states, transitions, guards, decided-by) | ~1006 | 30 min |
| Ph5 | [`TRINITY_POLICY_ENGINE_SPEC_V1.md`](TRINITY_POLICY_ENGINE_SPEC_V1.md) | Phase 5 — Policy Engine (query API, blocking semantics, independence from state graph) | ~1052 | 30 min |
| Ph9 | [`TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md`](TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md) | Phase 9 — Transport Boundary (Article XV anchor, signed envelope, HMAC-SHA256, refusal codes) | ~927 | 25 min |
| Ph12 | [`TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md`](TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md) | Phase 12 — Retro/RRR Split (Article IX + IV; deterministic closure vs semantic reflection; rrr.completed event; human-only pin) | ~981 | 25 min |
| Ph13 | [`TRINITY_PRESENTATION_PROTOCOL_V1.md`](TRINITY_PRESENTATION_PROTOCOL_V1.md) | Phase 13 — Presentation Protocol (Article XIII + XXIII; ratification packet/synthesis/decision; dissent preservation; UI never truth-layer) | ~738 | 20 min |
| Ph14 | [`TRINITY_ROOT_OF_TRUST_SPEC_V1.md`](TRINITY_ROOT_OF_TRUST_SPEC_V1.md) | Phase 14 — Root of Trust (Article XXV + XXIX; GENESIS_TRUST_ASSUMED manifest; Layer 0 hash-pinning; signature roadmap HMAC→Ed25519→TPM) | ~831 | 25 min |
| Ph16 | [`V1_1_AMENDMENT_QUEUE.md`](V1_1_AMENDMENT_QUEUE.md) | Phase 16 E2E integration artifact — v1.1 amendment backlog (17 CRITICAL + 21 NOTABLE + 15 NITPICK) from 6-spec review 2026-05-15; batched fix sessions sequence | ~280 | 15 min |

> **Note (2026-05-13 · Addendum v1.0.2):** All Trinity **constitutional documents** (Constitution v1.0, Addendum v1.0.1+v1.0.2, Organ Map, Ritual Constitution v1.1-rc, Ritual Contract v1.0, RRR Delegation Contract v1.0) have been relocated from `docs/specs/` to [`docs/constitution/`](../constitution/INDEX.md) to separate the authority layer from technical specs. Technical specs 00–19 remain here. See [`/docs/constitution/INDEX.md`](../constitution/INDEX.md) for the canonical constitutional index.

**Total: 13,000+ lines · 420+ KB · 16 documents · ~4-5 hours full read**

---

## 16. Project Health Status

### What's Done ✅
- 12 documents (this spec pack)
- 10 decisions committed
- 5 critical fixes integrated
- 4 layers defined
- Vocabulary locked
- Reading paths mapped

### What's Next 📋
- **Sprint 1 (P0):** Backup + add structures to <upstream-project>
- **Sprint 2 (P1):** browser-cli contract compliance
- **Sprint 3 (P2):** memory-cli build + index 240 retros
- **Sprint 4 (P3):** Wire memory into lll/vvv/nnn
- **Sprint 5 (P4):** Remove MCP servers
- **Sprint 6+ (P5-P10):** verifier, loop, graph, retro-cli, shim

### Implementation Readiness
> **9.5/10** — architectural rough edges all closed, ready to code

### Operational Readiness
> **9/10** — runbook complete, troubleshooting documented

### Migration Readiness (<upstream-project>)
> **9/10** — gap analysis complete, 17-week plan with risks identified

---

## 17. Key Insights (the Wisdom)

### From Anthropic
> *"1.6% AI logic, 98.4% deterministic harness"* — production AI = harness, not model

### From Browser-CLI Pattern
> *Stdin/stdout JSON + schema lock = tool-agnostic + debuggable + composable*

### From Oracle Framework
> *Append-only memory + supersession chain = "Nothing is Deleted"*

### From <upstream-project> Production
> *240 retros + 14 lessons = invaluable Knowledge Brain raw data*

### From Friend's Feedback
> *"Brain / Judge / Truth"* model + *"AI must not be sole judge"*

### From This Synthesis
> **Trinity OS = Unix philosophy + Microkernel + AI brain layer + Hash-chain audit**
> ทำให้สิ่งที่คุณทำเองด้วยวินัย กลายเป็นระบบที่ช่วยคุณทำวินัยนั้นโดยอัตโนมัติ

---

## 18. Final Notes

### Where to Find Updates

```text
TRINITY_EVOLUTION/INDEX.md    ← this doc, master overview
TRINITY_EVOLUTION/00-10_*.md  ← all spec docs
TRINITY_EVOLUTION/CHANGELOG.md ← (future) version history
```

### How to Contribute

```text
1. Read INDEX.md (this)
2. Pick a phase to implement
3. Read relevant spec
4. Implement with browser-cli as reference
5. Run trinity-contract-test (when available)
6. Submit PR with tests + retros
```

### How to Get Help

- 📖 Read FAQ (§14)
- 🔍 Check `09_DEPLOY_GUIDE.md` §8 (Troubleshooting)
- 💬 Open question in team chat
- 📝 Log incident retro

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master technical spec (read after this)
- [`08_DIAGRAMS.md`](08_DIAGRAMS.md) — Visual mental model
- [`09_DEPLOY_GUIDE.md`](09_DEPLOY_GUIDE.md) — Operations
- [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md) — <upstream-project> migration
- [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) — Inspirations, dependencies, attributions
- [`12_GLOSSARY.md`](12_GLOSSARY.md) — Complete A-Z glossary (lookup)
- [`CHANGELOG.md`](CHANGELOG.md) — Version history
- All other specs (per-component)

---

## Changelog

- **v1.0.0 (2026-04-28)** — Initial master overview index combining vocabulary, components, roles, reading paths, FAQ, and full spec pack index

---

> 🌌 **Trinity OS — One brain, many organs, deterministic judgment, audited truth.**
