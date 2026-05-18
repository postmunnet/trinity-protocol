---
title: "Trinity OS — Complete Glossary (English)"
language: English
last-updated: 2026-04-28
note: "Translation of ../12_GLOSSARY.md — English-only entries"
---

# Trinity OS — Glossary (English)

> All Trinity OS terms in alphabetical order with cross-references to specs

---

## How to Use

- 🔍 **Ctrl+F** to find specific terms
- 📖 **Cross-ref** = link to spec doc with full detail
- 🏷 **Category** to group related concepts
- 💡 **Example** shows usage in practice

---

## A

### Action namespace
🏷 *Tool Contract*
**Definition:** Canonical namespaced verb format `<tool>.<verb>` (e.g., `memory.search`, `browser.screenshot`)
**Why:** Prevents verb conflicts when multiple tools share verb names
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4a

### Adapter
🏷 *Architecture*
**Definition:** Vendor-specific config bridging trinity-shell to specific harness
**Examples:** `.claude/skills/`, `AGENTS.md`, `.cursor/rules/`, `GEMINI.md`

### ai-docs
🏷 *Project Family*
**Definition:** Methodology framework — markdown documentation for AI workflow rituals
**Locations:** `/<workspace-root>/ai-docs/` (original) and `<project>/ai-docs/` (per-project)
**Role:** Knowledge Brain (memory substrate)

### Anthropic insight (1.6%/98.4%)
🏷 *Foundational principle*
**Definition:** Claude Code is 1.6% AI logic, 98.4% deterministic harness
**Implication:** Production AI = harness, not model
**Trinity application:** Trinity OS ≈ 100% harness, outsources reasoning to vendor AI

### arra-oracle-v3
🏷 *Inspiration*
**Definition:** TypeScript MCP memory server (Soul-Brews-Studio)
**License:** BUSL-1.1
**Influence:** memory-cli's SQLite + FTS5 + ChromaDB hybrid architecture

### Artifact
🏷 *Truth / Evidence*
**Definition:** File or data created by a tool, kept as evidence
**Properties:** path, sha256, size, mime, metadata

### Audit (events.ndjson)
🏷 *Persistence / Compliance*
**Definition:** Append-only NDJSON log with hash-chain
**Property:** Tamper-evident (compliance: SOC2, ISO27001)

### Authority
🏷 *Graph / Decision*
**Definition:** Who has the right to decide a state transition
**Types:** `verifier` / `policy` / `human` / `kernel`
**Rule:** AI may PROPOSE. AI may NOT DECIDE.

---

## B

### BM25
🏷 *Search*
**Definition:** Best Match 25 — ranking algorithm used by SQLite FTS5

### Bootstrap Pack
🏷 *Phase 0.5 / Portability*
**Definition:** Templates + install.sh + verify-install.sh to scaffold Trinity into new project
**Solves:** "Copy ai-docs to new project, AI doesn't know short codes"

### Brain
🏷 *Architecture / Vocabulary*
**Definition:** ⚠️ AMBIGUOUS — use specific term:
- **Knowledge Brain** = ai-docs + memory-cli (recall, NOT planner)
- **Reasoning Engine** = Vendor AI (planning)

### Browser-CLI
🏷 *Tool / Reference*
**Definition:** Playwright wrapper CLI tool — first Trinity CLI tool
**Action namespace:** `browser.*`

### Budget (loop)
🏷 *Loop / Resource*
**Definition:** Resource cap on a Trinity loop run
**Types:** tokens, duration_ms, retry, tool_calls, iterations

### Bun
🏷 *Runtime*
**Definition:** Fast JavaScript runtime (alternative to Node.js)

---

## C

### Capsule
🏷 *Session*
**Definition:** Isolated workspace for one work session — `.ai/sessions/<id>/`

### CDP (Chrome DevTools Protocol)
🏷 *Browser*
**Definition:** Protocol for connecting to running Chrome instance

### `ccc` (short code)
🏷 *Workflow*
**Definition:** Checkpoint command — save loop state for resume

### Checkpoint
🏷 *Loop / Persistence*
**Definition:** Saved snapshot of loop state for resume after restart

### ChromaDB
🏷 *Storage / Future*
**Definition:** Open-source vector database (Apache-2.0)
**Use:** Phase 9 (hybrid memory)

### Claude Code
🏷 *Vendor Host*
**Definition:** Anthropic's AI coding harness (CLI + IDE)
**Trinity role:** Primary vendor host

### CLI-first
🏷 *Decision*
**Definition:** Decision #4 — Trinity uses CLI as core protocol (NOT MCP)

### Codex CLI
🏷 *Vendor Host*
**Definition:** OpenAI's CLI for AI coding
**Adapter:** `AGENTS.md`

### Cognition AI (Devin team)
🏷 *Inspiration*
**Definition:** Public posts on agent context fragility
**Influence:** Trinity → explicit `decided_by`

### Compliance Test
🏷 *Tool Contract*
**Definition:** `trinity-contract-test <tool>` — automated contract verification
**Levels:** Bronze / Silver / Gold / Platinum

### Config (`--config`)
🏷 *Tool Contract*
**Definition:** Universal CLI flag for tool config file

### Confidence (memory)
🏷 *Memory / Curation*
**Definition:** Quality tag for indexed documents
**Values:** `verified` | `draft` | `superseded`

### Coordinator
🏷 *Architecture*
**Definition:** Trinity Kernel's role — orchestrate workflow, sessions, state
**NOT:** Reasoning, deciding

### Cursor
🏷 *Vendor Host*
**Definition:** IDE-based AI coding tool
**Adapter:** `.cursor/rules/*.mdc`

---

## D

### `decided_by`
🏷 *Graph / Authority*
**Definition:** Required field on every graph transition specifying authority
**Values:** `verifier` | `policy` | `human` | `kernel`

### Decomposition (goal)
🏷 *Loop / Goal*
**Definition:** Break root goal into sub-goals
**Strategies:** `ai`, `template`, `manual`, `none`

### DEAD (verdict)
🏷 *Verifier*
**Definition:** Verdict — unrecoverable, terminate session

### Deterministic
🏷 *Architecture*
**Definition:** Behavior fully predictable (not AI-driven)
**Trinity stance:** ~100% deterministic harness

### Devin
🏷 *Comparison*
**Definition:** Closed-source SaaS coding agent (Cognition AI)
**Trinity stance:** Different architecture (open + CLI-native)

### DO (state)
🏷 *Workflow*
**Definition:** Standard graph state — apply changes to dev folder

---

## E

### Envelope (response)
🏷 *Tool Contract*
**Definition:** Standard JSON wrapper for tool responses
**Fields:** ok, command, action, data, artifacts, error, meta

### Escalation
🏷 *Loop / Verifier*
**Definition:** Pause workflow, ask human or LLM judge

### Evidence
🏷 *Verifier*
**Definition:** Artifact required for verification verdict
**Types:** diff, test_result, screenshot, http_health_check, log_tail

### events.ndjson
🏷 *Audit*
**Definition:** Hash-chain audit log file
**Location:** `.ai/audit/events.ndjson`

---

## F

### FTS5
🏷 *Storage*
**Definition:** SQLite Full-Text Search v5
**Use:** memory-cli Phase 2 (primary search)

### ftp-cli
🏷 *Tool / Future*
**Definition:** CLI organ for FTP/SFTP — upload/download to remote hosts with Tool Contract envelopes, artifacts, and NDJSON audit
**Role:** Complements `deploy-cli` for media/theme/sync paths without external MCP
**Status:** 📋 future — reserved action namespace `ftp.*`
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4a, [`INDEX.md`](INDEX.md) §8

---

## G

### Gemini CLI
🏷 *Vendor Host*
**Definition:** Google's Gemini CLI tool
**Trinity role:** Research/large-context (1M context)

### `gogogo` (short code)
🏷 *Workflow*
**Definition:** Execute the plan — Trinity loop runs

### Goal
🏷 *Loop*
**Definition:** Unit of work — has id, type, description, status, acceptance criteria
**Types:** `epic` | `feature` | `task` | `subtask`

### Goal Tree
🏷 *Loop*
**Definition:** Hierarchical decomposition of root goal into sub-goals

### Graph
🏷 *Architecture*
**Definition:** Workflow state machine (NOT a brain — just skeleton)
**Layers:** Kernel runtime + Domain workflow

---

## H

### Harness
🏷 *Architecture / Critical*
**Definition:** Three meanings:
1. Test Harness — unit/integration runner
2. AI Harness — vendor's user-facing CLI
3. Run Harness / Trinity Kernel — our orchestration

### Hash chain
🏷 *Audit*
**Definition:** Each event has prev_hash + hash → tamper-evident

### Helpers (YAML)
🏷 *Tool Contract*
**Definition:** YAML file defining reusable command compositions

### Hono
🏷 *Optional*
**Definition:** Lightweight HTTP framework (Bun/Node)

---

## I

### Iron Triangle
🏷 *Architecture / Mental Model*
**Definition:** Harness + Loop + Graph — 3 must-have for agentic AI

### IPC (Inter-Process Communication)
🏷 *Architecture*
**Definition:** Communication between Trinity kernel and CLI tools
**Implementation:** stdin/stdout JSON

---

## J

### Judge
🏷 *Architecture*
**Definition:** Verifier component — gives verdict
**Implementation:** `verify-cli` + `verifier-rules.yaml`

---

## K

### Kernel (Trinity Kernel)
🏷 *Architecture*
**Definition:** Coordinator + Judge layer — Python CLI in `.ai/cli/`

### Knowledge Brain
🏷 *Architecture / Vocabulary*
**Definition:** ai-docs + memory-cli — recall layer
**NOT:** Autonomous planner

---

## L

### LangGraph
🏷 *Comparison*
**Definition:** LangChain's graph-based agent framework (Python)
**Trinity stance:** Different architecture (CLI-native)

### `lll` (short code)
🏷 *Workflow*
**Definition:** Status report — see project + git + memory state

### LLM Judge (gated)
🏷 *Verifier*
**Definition:** When verifier + policy unsure → spawn dedicated LLM call
**Rule:** Must be audited

### Loop
🏷 *Architecture*
**Definition:** Trinity's heart — observe → think → act → verify → decide → repeat

### loop_state.json
🏷 *State*
**Definition:** Runtime state of a Trinity loop
**Location:** `.ai/sessions/<id>/loop_state.json`

---

## M

### MCP (Model Context Protocol)
🏷 *Decision*
**Definition:** Anthropic's protocol for tool integration
**Trinity stance:** ❌ NOT core path (decision #5)
**Replacement:** CLI-first stdin/stdout JSON

### memory-cli
🏷 *Tool*
**Definition:** Knowledge Brain recall organ (SQLite FTS5)
**Phase:** 2
**Action namespace:** `memory.*`

### Microkernel
🏷 *Architecture / Inspiration*
**Definition:** OS architecture — small kernel + userspace services (L4, QNX, Mach)

---

## N

### NDJSON (Newline-Delimited JSON)
🏷 *Storage / Format*
**Definition:** One JSON object per line, separated by `\n`

### NEEDS_HUMAN (verdict)
🏷 *Verifier*
**Definition:** Verdict — verifier unsure, escalate to human

### Nervous system
🏷 *Vocabulary*
**Definition:** Metaphor for stdin/stdout JSON between kernel and tools

### `nnn` (short code)
🏷 *Workflow*
**Definition:** Plan — detailed implementation plan

---

## O

### oh-my-claudecode
🏷 *Reference*
**Definition:** Claude Code customization framework
**Influence:** Phase 8 Trinity Shim pattern

### oh-my-codex (OMX)
🏷 *Reference*
**Definition:** Codex CLI customization (yeachan-heo)

### openclaude
🏷 *Reference*
**Definition:** Open-source coding agent CLI (multi-provider)

### Oracle Framework
🏷 *Inspiration*
**Definition:** Philosophical framework (Soul-Brews-Studio)
**Influence:** Append-only memory, supersession

### Organ
🏷 *Vocabulary*
**Definition:** Metaphor for CLI tool — eyes, hands, memory

---

## P

### PASS (verdict)
🏷 *Verifier*
**Definition:** Verdict — evidence sufficient, all checks ok, continue

### Phase
🏷 *Roadmap*
**Definition:** Implementation milestone (Phase 0-10)

### Plan 9
🏷 *Inspiration*
**Definition:** Bell Labs distributed OS — "everything is a file"

### Playwright
🏷 *Dependency*
**Definition:** Microsoft's browser automation library (Apache-2.0)

### Policy
🏷 *Architecture*
**Definition:** Rules in `.ai/policies/*.yaml` files

### Policy tier
🏷 *Tool Contract*
**Definition:** Limits which verbs a tool allows
**Tiers:** `safe` | `normal` | `aggressive`

### POSIX
🏷 *Inspiration*
**Definition:** Portable Operating System Interface — Unix standard

### PROMOTED (state)
🏷 *Workflow*
**Definition:** Standard graph state — code in prod-ready folder
**Authority:** human only

### Pyramid of Judgment
🏷 *Verifier*
**Definition:** Escalation chain — Verifier → Policy → LLM Judge → Human

---

## Q

(reserved)

---

## R

### Reasoning Engine
🏷 *Architecture*
**Definition:** Vendor AI — does planning, decomposition
**NOT:** Trinity kernel

### Recorder (browser)
🏷 *Browser*
**Definition:** browser-cli's bidirectional action recorder

### REPL (Read-Eval-Print Loop)
🏷 *Tool Contract*
**Definition:** Interactive mode of CLI tools

### Resume (loop)
🏷 *Loop*
**Definition:** Continue loop from latest checkpoint after restart

### retro-cli
🏷 *Tool*
**Definition:** Structured retrospective writer
**Phase:** 7
**Action namespace:** `retro.*`

### Retrospective
🏷 *Memory*
**Definition:** Post-task documentation
**Storage:** `.claude/retrospectives/*.md`
**Indexed by:** memory-cli

### RETRY (verdict)
🏷 *Verifier*
**Definition:** Verdict — recoverable failure, loop again

### `rrr` (short code)
🏷 *Workflow*
**Definition:** Retrospective — write structured retro, update memory

### Run ID
🏷 *Tool Contract*
**Definition:** Unique identifier for a tool invocation
**Format:** `run_<timestamp>_<random>`

---

## S

### `safe` (policy tier)
🏷 *Policy*
**Definition:** Most restrictive tier — read-only verbs

### SANDBOX (state)
🏷 *Workflow*
**Definition:** Standard graph state — multi-agent isolated work

### Schema
🏷 *Tool Contract*
**Definition:** JSON Schema definition for envelope/config
**Versioned:** `v1`, `v2`

### Session
🏷 *Persistence*
**Definition:** Workflow capsule — `.ai/sessions/<id>/`

### sha256
🏷 *Audit / Truth*
**Definition:** Cryptographic hash for artifacts

### Shim (Trinity Shim)
🏷 *Architecture*
**Definition:** Adapter layer between vendor harness and Trinity kernel
**NOT:** Full harness replacement

### Short codes
🏷 *Workflow*
**Definition:** 5-step workflow ritual: lll/vvv/nnn/gogogo/rrr

### Side effect (state)
🏷 *Graph*
**Definition:** Action triggered on state entry/exit

### Skills (Claude Code)
🏷 *Vendor adapter*
**Definition:** Claude Code's extension model
**Use:** Trinity Shim Phase 8

### SQLite
🏷 *Storage*
**Definition:** Embedded relational database
**Use:** memory-cli backend (with FTS5)

### SSOT (Single Source of Truth)
🏷 *Configuration*
**Definition:** `.ai/ssot.yaml` — canonical project config

### State machine
🏷 *Graph*
**Definition:** Finite state automaton — defines workflow lifecycle

### Stdin/stdout JSON
🏷 *Tool Contract / IPC*
**Definition:** Communication protocol for CLI tools
**Format:** Line-delimited JSON on stdout

### Supersession
🏷 *Memory*
**Definition:** Mark old document as obsolete
**NOT:** Delete — preserves history

---

## T

### Tag (memory)
🏷 *Memory*
**Definition:** Free-form label on a document

### Template (Bootstrap Pack)
🏷 *Bootstrap*
**Definition:** Markdown file with placeholders rendered by install.sh

### Termination (loop)
🏷 *Loop*
**Definition:** Loop reaches end (terminal state)

### THINK (state)
🏷 *Workflow*
**Definition:** Standard graph initial state — goal analysis + plan

### Tool Contract
🏷 *Foundation*
**Definition:** Universal CLI tool specification (POSIX of Trinity)
**Version:** v1.1

### Tool Registry
🏷 *Configuration*
**Definition:** `.ai/tools.yaml` — list of registered CLI tools

### Trinity Kernel
🏷 *Architecture*
**Definition:** Coordinator + Judge — Python CLI in `.ai/cli/`

### Trinity OS
🏷 *Top-level*
**Definition:** Whole system — kernel + brain + tools + shim + harness

### trinity-shell
🏷 *Tool*
**Definition:** Universal CLI wrapper for vendor harnesses
**Phase:** 8
**Action namespace:** `trinity.*`

### Truth
🏷 *Vocabulary / Architecture*
**Definition:** Metaphor for verifiable evidence
**Trinity rule:** Truth lives in files, not in AI's claim

---

## U

### Unicode61 tokenizer
🏷 *Search*
**Definition:** SQLite FTS5 tokenizer — Unicode-aware (handles Thai)

### Unix philosophy
🏷 *Inspiration*
**Definition:** "Do one thing well" + pipes (Eric Raymond, 1978)

### Userland
🏷 *Architecture*
**Definition:** CLI tools layer — like Unix userspace

---

## V

### <upstream-project>
🏷 *Project Family*
**Definition:** Production e-commerce project (PHP+Smarty+MySQL)
**Role:** Largest user of Trinity v1; migration target for v2

### Vector embedding
🏷 *Storage / Future*
**Definition:** Numeric representation of text for semantic similarity
**Use:** Phase 9 hybrid memory

### Vendor harness
🏷 *Architecture*
**Definition:** Vendor's AI tool (Claude Code, Codex, Gemini, Cursor)
**Trinity role:** Reasoning Engine + UI host

### Verb
🏷 *Tool Contract*
**Definition:** Action a tool exposes
**Local:** `search`
**Canonical:** `memory.search`

### Verdict
🏷 *Verifier*
**Definition:** Output of verify-cli
**Values:** PASS / RETRY / NEEDS_HUMAN / DEAD

### verify-cli
🏷 *Tool*
**Definition:** Judge organ — deterministic verdict with file rules
**Phase:** 4
**Action namespace:** `verify.*`

### Verifier
🏷 *Architecture*
**Definition:** Component giving verdict (= verify-cli)

### Verifier rules
🏷 *Policy*
**Definition:** YAML rules in `.ai/policies/verifier-rules.yaml`

### Vocabulary lock
🏷 *Decision*
**Definition:** Fixed terminology to prevent drift

### `vvv` (short code)
🏷 *Workflow*
**Definition:** Verify — 5 mandatory questions before planning
**Critical:** vvv MUST come before nnn

---

## W

### Warp
🏷 *Vendor Host*
**Definition:** Terminal with AI integration
**Adapter:** WARP.md → CLAUDE.md (symlink)

### Worker
🏷 *Vocabulary*
**Definition:** Vendor AI doing actual work (under coordination)

### Workflow Graph
See "Graph"

### wp-cli
🏷 *Dependency / Future*
**Definition:** Official WordPress CLI (PHP, MIT)
**Use:** wordpress-cli wraps it (future)

---

## X

### xstate
🏷 *Optional*
**Definition:** TypeScript state machine library
**Use:** Optional graph engine for Phase 6

---

## Y / Z

(reserved)

---

## Index by Category

### Architecture (15 terms)
Brain, Coordinator, Graph, Harness, Iron Triangle, Judge, Kernel, Knowledge Brain, Microkernel, Nervous system, Organ, Reasoning Engine, Shim, Trinity Kernel, Userland

### Workflow (12 terms)
ccc, gogogo, lll, nnn, rrr, vvv, Goal, Goal Tree, DO, SANDBOX, THINK, PROMOTED

### Verifier (10 terms)
DEAD, Evidence, Escalation, Judge, LLM Judge, NEEDS_HUMAN, PASS, Pyramid of Judgment, RETRY, Verdict

### Storage (10 terms)
Audit, ChromaDB, Drizzle ORM, FTS5, Hash chain, NDJSON, SQLite, SSOT, Vector embedding, events.ndjson

### Tool Contract (12 terms)
Action namespace, Compliance Test, Config, Envelope, Helpers, Policy tier, REPL, Run ID, Schema, Stdin/stdout JSON, Tool Registry, Verb

### Decisions (5 terms)
CLI-first, MCP, decided_by, Vocabulary lock, Anthropic insight

### Loop (8 terms)
Budget, Checkpoint, Decomposition, Loop, Resume, Termination, loop_state.json, Goal Tree

### Inspirations (8 terms)
Anthropic insight, arra-oracle-v3, Cognition AI, LangGraph, Microkernel, Oracle Framework, Plan 9, Unix philosophy

### Vendor (6 terms)
Claude Code, Codex CLI, Cursor, Gemini CLI, Vendor harness, Warp

### Tools (9 terms)
browser-cli, ftp-cli, memory-cli, retro-cli, trinity-shell, verify-cli, wordpress-cli, Tool Contract, Tool Registry

---

## See also

- [`README.md`](README.md) — Public overview
- [`INDEX.md`](INDEX.md) — Master index
- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master spec (terms originate here)
- [`../12_GLOSSARY.md`](../12_GLOSSARY.md) — Thai version (more detail)

## Changelog

- **v1.0.0 (2026-04-28)** — English glossary
