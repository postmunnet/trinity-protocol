---
title: "Trinity OS — Complete Glossary"
subtitle: "All terms, A-Z, with cross-references"
version: 1.0.0
status: reference
last-updated: 2026-04-28
audience: Anyone needing to look up a term
read-time: As needed (lookup)
---

# Trinity OS — Complete Glossary

> ทุกคำที่ใช้ในระบบ · เรียงตัวอักษร A-Z · มี cross-reference ไปยัง spec ที่อธิบายลึก

---

## How to Use

- 🔍 **Ctrl+F** เพื่อหาคำเฉพาะ
- 📖 **Cross-ref** = ลิงก์ไปยังเอกสารที่อธิบายลึก
- 🏷 **Category** ช่วยจัดกลุ่ม (Architecture / Workflow / Storage / etc.)
- 💡 **Example** = ตัวอย่างใช้งานคำนั้น

---

## A

### Action namespace
🏷 *Tool Contract*
**Definition:** Canonical namespaced verb format `<tool>.<verb>` (e.g., `memory.search`, `browser.screenshot`)
**Why:** Prevents verb conflicts when multiple tools have same local verb
**Example:** `browser-cli`'s `screenshot` → `browser.screenshot` in audit log
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4a

### Adapter
🏷 *Architecture*
**Definition:** Vendor-specific config/code that bridges trinity-shell to a specific harness
**Examples:** `.claude/skills/`, `AGENTS.md`, `.cursor/rules/`, `GEMINI.md`
**See:** [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md) §4-7

### ai-docs
🏷 *Project Family*
**Definition:** Methodology framework — markdown documentation for AI workflow rituals
**Two locations:**
- `<workspace-root>/ai-docs/` — original v3.0 framework
- `<project>/ai-docs/` — embedded per-project copy
**Role in Trinity:** Knowledge Brain (memory substrate)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §1.2

### Anthropic insight (1.6%/98.4%)
🏷 *Foundational principle*
**Definition:** Public insight from Anthropic — Claude Code is 1.6% AI logic and 98.4% deterministic harness
**Implication:** Production AI = harness, not model
**Trinity application:** Trinity OS ≈ 100% harness, outsources 1.6% to vendor AI
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §1, [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §7.1

### arra-oracle-v3
🏷 *Inspiration*
**Definition:** TypeScript MCP memory server (Soul-Brews-Studio) — hybrid search reference
**License:** BUSL-1.1
**Influence:** memory-cli's SQLite + FTS5 + ChromaDB hybrid architecture (independent implementation)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §2.2

### Artifact
🏷 *Truth / Evidence*
**Definition:** File or data created by a tool, kept as evidence
**Properties:** path, sha256, size, mime, metadata
**Where listed:** Response envelope `artifacts: []` field
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4.4

### Audit (events.ndjson)
🏷 *Persistence / Compliance*
**Definition:** Append-only NDJSON log with hash-chain (each event has prev_hash + hash)
**Location:** `.ai/audit/events.ndjson`
**Property:** Tamper-evident (compliance: SOC2, ISO27001)
**See:** [`08_DIAGRAMS.md`](08_DIAGRAMS.md) §13

### Authority
🏷 *Graph / Decision*
**Definition:** Who has the right to decide a state transition
**Types:** `verifier` / `policy` / `human` / `kernel`
**Rule:** AI may PROPOSE transition. AI may NOT DECIDE transition.
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) §4

---

## B

### BM25
🏷 *Search*
**Definition:** Best Match 25 — relevance ranking algorithm used by SQLite FTS5
**Use:** Default search ranking in memory-cli
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §8.3

### Bootstrap Pack
🏷 *Phase 0.5 / Portability*
**Definition:** Templates + install.sh + verify-install.sh to scaffold Trinity into new project
**Solves:** "Copy ai-docs to new project, AI doesn't know short codes" pain
**Contents:** CLAUDE.md.template, AGENTS.md.template, GEMINI.md.template, minimal ai-docs, minimal `.ai/`
**See:** [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md)

### Brain
🏷 *Architecture / Vocabulary*
**Definition:** ⚠️ **AMBIGUOUS** — use specific term:
- **Knowledge Brain** = ai-docs + memory-cli (recall layer, NOT planner)
- **Reasoning Engine** = Vendor AI (Claude/Codex/Gemini) — does planning
**Common mistake:** Saying "ai-docs is the brain" — too vague
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0 vocabulary

### Browser-CLI
🏷 *Tool / Reference Implementation*
**Definition:** Playwright wrapper CLI tool (Node.js) — first Trinity CLI tool
**Location:** `<workspace-root>/browser-cli/`
**Role:** Reference DNA for all future CLI tools
**Action namespace:** `browser.*`
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §1.4

### Budget (loop)
🏷 *Loop / Resource*
**Definition:** Resource cap on a Trinity loop run
**Types:** tokens, duration_ms, retry, tool_calls, iterations
**Default:** 200K tokens, 2h, 10 retries, 200 calls, 50 iterations
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §8

### Bun
🏷 *Runtime*
**Definition:** Fast JavaScript runtime (alternative to Node.js)
**Use:** Optional for memory-cli (under consideration)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §5.4

---

## C

### Capsule
🏷 *Session*
**Definition:** Isolated workspace for one work session — `.ai/sessions/<id>/`
**Phases:** THINK → SANDBOX → DO → ...
**Contents:** 00_CONTEXT, 01_PROMPT, 02_PLAN, 99_SUMMARY, goals.yaml, loop_state.json, etc.
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §3.3

### CDP (Chrome DevTools Protocol)
🏷 *Browser*
**Definition:** Protocol for connecting to running Chrome instance
**Use:** browser-cli's `--cdp` mode (no focus stealing)
**See:** browser-cli/docs/CDP_CONTRACT.md

### `ccc` (short code)
🏷 *Workflow*
**Definition:** Checkpoint command — save loop state for resume
**When:** Auto every 5 iterations or 10 minutes; manual on demand
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §7

### Checkpoint
🏷 *Loop / Persistence*
**Definition:** Saved snapshot of loop state for resume after restart
**Contents:** goal_tree_snapshot, loop_state, artifacts_manifest, events_offset
**Triggers:** Every N iterations, manual `ccc`, before aggressive policy
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §7

### ChromaDB
🏷 *Storage / Future*
**Definition:** Open-source vector database (Apache-2.0)
**Use in Trinity:** Phase 9 (hybrid memory) — semantic search
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §15

### Claude Code
🏷 *Vendor Host*
**Definition:** Anthropic's AI coding harness (CLI + IDE)
**Trinity role:** Primary vendor host — best skills/hooks support
**Adapter:** `.claude/skills/`, `.claude/hooks/`, `.claude/settings.local.json`
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §4.1

### CLI-first
🏷 *Decision*
**Definition:** Decision #4 — Trinity uses CLI tools as core protocol (NOT MCP)
**Why:** Tool-agnostic, debuggable, composable, vendor-neutral
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §9

### Codex CLI
🏷 *Vendor Host*
**Definition:** OpenAI's CLI for AI coding (GPT-4/5 family)
**Trinity role:** Secondary vendor host (fast generation)
**Adapter:** `AGENTS.md`
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §4.2

### Cognition AI (Devin team)
🏷 *Inspiration*
**Definition:** Public posts from Devin team on agent context fragility
**Influence:** Trinity → explicit `decided_by` (no implicit decisions)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §7.7

### Compliance Test
🏷 *Tool Contract*
**Definition:** `trinity-contract-test <tool>` — automated verification of contract adherence
**Levels:** Bronze / Silver / Gold / Platinum
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §16a

### Config (`--config`)
🏷 *Tool Contract*
**Definition:** Universal CLI flag for tool config file
**Format:** JSON (preferred) or YAML
**Resolution:** CLI flag → ENV → `./<tool>.config.json` → `./configs/<tool>.json` → built-in
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §7

### Confidence (memory)
🏷 *Memory / Curation*
**Definition:** Quality tag for indexed documents
**Values:** `verified` | `draft` | `superseded`
**Default:** `draft` (manual upgrade after review)
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §3

### Coordinator
🏷 *Architecture*
**Definition:** Trinity Kernel's role — orchestrate workflow, sessions, state
**NOT:** Reasoning, deciding (those are Reasoning Engine and Judge)
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0 vocabulary

### Cursor
🏷 *Vendor Host*
**Definition:** IDE-based AI coding tool
**Trinity role:** IDE host
**Adapter:** `.cursor/rules/*.mdc`
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §4.4

---

## D

### `decided_by`
🏷 *Graph / Authority*
**Definition:** Required field on every graph transition specifying authority
**Values:** `verifier` | `policy` | `human` | `kernel`
**Critical fix:** Without this, AI may decide transitions (anti-pattern)
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) §4

### Decomposition (goal)
🏷 *Loop / Goal*
**Definition:** Break root goal into sub-goals
**Strategies:** `ai` (vendor AI proposes), `template`, `manual`, `none`
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §4.2

### DEAD (verdict)
🏷 *Verifier*
**Definition:** Verdict — unrecoverable failure, terminate session
**Examples:** Forbidden pattern found, retry budget exhausted
**Action:** Mark session terminated, audit log, escalate
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §2.1

### Deterministic
🏷 *Architecture*
**Definition:** Behavior fully predictable (not AI-driven)
**Trinity stance:** ~100% deterministic harness; AI only in vendor layer
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §1

### Devin
🏷 *Comparison*
**Definition:** Closed-source SaaS coding agent (Cognition AI)
**Trinity stance:** Different architecture (we're open + CLI-native)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §6.3

### DO (state)
🏷 *Workflow*
**Definition:** Standard graph state — apply changes to dev folder
**Transitions:** SANDBOX → DO (vvv_pass) → VERIFIED (code_change_pass)
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) §3.3

### Drizzle ORM
🏷 *Storage / Optional*
**Definition:** TypeScript ORM with type safety
**Use in Trinity:** Considered for memory-cli — likely not used (prefer raw SQL)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §6.6

---

## E

### Envelope (response)
🏷 *Tool Contract*
**Definition:** Standard JSON wrapper for tool responses
**Required fields:** ok, command, action, data, artifacts, error, meta
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4

### Escalation
🏷 *Loop / Verifier*
**Definition:** Pause workflow, ask human or LLM judge
**Triggers:** NEEDS_HUMAN verdict, budget exhausted, deadlock
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §5.3

### Evidence
🏷 *Verifier*
**Definition:** Artifact required for verification verdict
**Types:** diff, test_result, screenshot, http_health_check, log_tail, etc.
**Library:** `verifier-rules.yaml` evidence_types section
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §3.4

### events.ndjson
🏷 *Audit*
**Definition:** Hash-chain audit log file
**Location:** `.ai/audit/events.ndjson`
**See:** "Audit" entry above

### Extension Platform
🏷 *Phase 10 / Future*
**Definition:** Future ecosystem where 3rd parties create Trinity extensions
**Components:** manifest, SDK, test suite, registry, trust levels
**Status:** Future (Phase 10) — not in v0.1
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §12

---

## F

### FTS5
🏷 *Storage*
**Definition:** SQLite Full-Text Search v5 — built-in full-text search engine
**Use:** memory-cli Phase 2 (primary search)
**Tokenizer:** `unicode61 remove_diacritics 1` (Thai/English friendly)
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §3

### ftp-cli
🏷 *Tool / Future*
**Definition:** CLI organ สำหรับ FTP/SFTP — อัปโหลด/ดาวน์โหลดไฟล์ไปยังโฮสต์ระยะไกลแบบมี artifact + audit (Tool Contract)
**Role:** คู่กับ `deploy-cli` — sync สื่อ/ธีม/artifact ไป staging/production โดยไม่พึ่ง MCP
**Status:** 📋 future — namespace มาตรฐาน `ftp.*`
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4a, [`INDEX.md`](INDEX.md) §8

---

## G

### Gemini CLI
🏷 *Vendor Host*
**Definition:** Google's Gemini CLI tool
**Trinity role:** Research/large-context vendor host (1M context)
**Adapter:** `GEMINI.md`
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §4.3

### `gogogo` (short code)
🏷 *Workflow*
**Definition:** Execute the plan — Trinity loop runs
**When:** After `nnn` plan approved
**Behavior:** Decompose, execute sub-goals, verify each
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md)

### Goal
🏷 *Loop*
**Definition:** Unit of work — has id, type, description, status, acceptance criteria
**Types:** `epic` | `feature` | `task` | `subtask`
**Statuses:** pending, running, done, blocked, dead, needs_human
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §2

### Goal Tree
🏷 *Loop*
**Definition:** Hierarchical decomposition of root goal into sub-goals
**Storage:** `.ai/sessions/<id>/goals.yaml`
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §1

### Graph
🏷 *Architecture*
**Definition:** Workflow state machine (NOT a brain — just skeleton)
**Two layers:** Kernel runtime graph (stable) + Domain workflow graph (configurable)
**Storage:** `.ai/graphs/*.yaml`
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md)

---

## H

### Harness
🏷 *Architecture / Critical*
**Definition:** Three meanings — must specify which:
1. **Test Harness** — unit/integration test runner (per-tool)
2. **AI Harness** — vendor's user-facing CLI (Claude Code, Codex, etc.)
3. **Run Harness / Trinity Kernel** — our orchestration layer
**Anthropic insight:** 98.4% of Claude Code = harness
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §3

### Hash chain
🏷 *Audit*
**Definition:** Each event has prev_hash + hash → tamper-evident
**Use:** events.ndjson
**See:** "Audit" entry, [`08_DIAGRAMS.md`](08_DIAGRAMS.md) §13

### Helpers (YAML)
🏷 *Tool Contract*
**Definition:** YAML file defining reusable command compositions
**Example:** `safe-plugin-update` = backup + update + health check
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §13

### Hono
🏷 *Optional*
**Definition:** Lightweight HTTP framework (Bun/Node)
**Use:** Optional for Phase 10 HTTP bridge
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §6.7

---

## I

### Iron Triangle
🏷 *Architecture / Mental Model*
**Definition:** Harness + Loop + Graph — 3 must-have components for agentic AI
**Without any one:** System cannot work
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §4

### IPC (Inter-Process Communication)
🏷 *Architecture*
**Definition:** Communication between Trinity kernel and CLI tools
**Implementation:** stdin/stdout JSON
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §3

---

## J

### JSON envelope
See "Envelope (response)"

### Judge
🏷 *Architecture*
**Definition:** Verifier component — gives verdict (PASS/RETRY/NEEDS_HUMAN/DEAD)
**Implementation:** `verify-cli` + `.ai/policies/verifier-rules.yaml`
**Rule:** AI is NOT the judge — verifier with file-based rules
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md)

---

## K

### Kernel (Trinity Kernel)
🏷 *Architecture*
**Definition:** Coordinator + Judge layer — orchestrates loops, sessions, state
**Implementation:** Python CLI (`.ai/cli/`)
**Role:** Like microkernel — small, manages everything
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §2

### Knowledge Brain
🏷 *Architecture / Vocabulary*
**Definition:** ai-docs + memory-cli — recall layer
**NOT:** Autonomous planner (that's vendor AI's job)
**Storage:** Markdown + SQLite FTS5
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0, [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md)

---

## L

### LangGraph
🏷 *Comparison*
**Definition:** LangChain's graph-based agent framework (Python)
**Trinity stance:** Different architecture (we're CLI-native, not in-process)
**Inspiration:** Graph state machine pattern (Phase 6)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §6.3

### `lll` (short code)
🏷 *Workflow*
**Definition:** Status report — see project + git + memory state
**When:** Session start, after break, before changes
**Output:** Git status, recent retros, active session, reminders
**See:** [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) §4.2

### LLM Judge (gated)
🏷 *Verifier*
**Definition:** When verifier + policy unsure → spawn dedicated LLM call
**Rule:** Must be audited (full prompt + response logged)
**Use:** Layer 3 of Pyramid of Judgment
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §5.2

### Loop
🏷 *Architecture*
**Definition:** Trinity's heart — observe → think → act → verify → decide → repeat
**Implementation:** `trinity loop --goal "..."`
**Must support:** Goal tree, checkpoints, budget, escalation
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md)

### loop_state.json
🏷 *State*
**Definition:** Runtime state of a Trinity loop
**Contents:** current_goal, queue, iteration, budget, checkpoints
**Location:** `.ai/sessions/<id>/loop_state.json`
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §3

---

## M

### MCP (Model Context Protocol)
🏷 *Decision*
**Definition:** Anthropic's protocol for tool integration
**Trinity stance:** ❌ NOT core path (decision #5)
**Reason:** Vendor lock-in (Claude Code only)
**Replacement:** CLI-first stdin/stdout JSON
**Note:** vendor's built-in MCP tools (Read/Write) = OK to use
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §9

### memory-cli
🏷 *Tool*
**Definition:** Knowledge Brain recall organ (SQLite FTS5)
**Phase:** 2 (next implementation)
**Action namespace:** `memory.*`
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md)

### Microkernel
🏷 *Architecture / Inspiration*
**Definition:** OS architecture — small kernel + userspace services (L4, QNX, Mach)
**Trinity application:** Trinity kernel = small, CLI tools = userland
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §7.3

---

## N

### NDJSON (Newline-Delimited JSON)
🏷 *Storage / Format*
**Definition:** One JSON object per line, separated by `\n`
**Use:** Audit log, tool log, response stream
**Property:** Append-only, easy to grep/jq
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §8

### NEEDS_HUMAN (verdict)
🏷 *Verifier*
**Definition:** Verdict — verifier unsure, sensitive op, escalate to human
**Action:** Pause workflow, show evidence, ask user
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §2.1

### Nervous system
🏷 *Vocabulary*
**Definition:** Metaphor for stdin/stdout JSON between kernel and tools
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0

### `nnn` (short code)
🏷 *Workflow*
**Definition:** Plan — detailed implementation plan
**When:** After `vvv` passes
**Output:** Goal, files to modify, steps, testing, rollback
**See:** [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) §4.2

---

## O

### oh-my-claudecode
🏷 *Reference*
**Definition:** Claude Code customization framework (multi-language)
**Influence:** Phase 8 Trinity Shim pattern
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §3.2

### oh-my-codex (OMX)
🏷 *Reference*
**Definition:** Codex CLI customization (yeachan-heo)
**Influence:** AGENTS.md adapter pattern
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §3.3

### openclaude
🏷 *Reference*
**Definition:** Open-source coding agent CLI (multi-provider)
**Influence:** Multi-vendor harness pattern (we don't do full but learn from it)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §3.5

### Oracle Framework
🏷 *Inspiration*
**Definition:** Philosophical framework (Soul-Brews-Studio)
**Influence:** Append-only memory, "Nothing is Deleted", supersession
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §2.1

### Organ
🏷 *Vocabulary*
**Definition:** Metaphor for CLI tool — eyes (browser), hands (write), memory (recall)
**Examples:** browser-cli, memory-cli, verify-cli
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0

---

## P

### PASS (verdict)
🏷 *Verifier*
**Definition:** Verdict — evidence sufficient, all checks ok, continue
**Most common verdict** in healthy workflow
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §2.1

### Phase
🏷 *Roadmap*
**Definition:** Implementation milestone (Phase 0-10)
**Critical phases:** 0.5 (Bootstrap), 1 (Tool Contract), 2 (memory-cli), 4 (verifier), 5 (loop)
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §13

### Plan 9
🏷 *Inspiration*
**Definition:** Bell Labs distributed OS — "everything is a file"
**Influence:** tools.yaml registry, namespace flexibility
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §7.4

### Playwright
🏷 *Dependency*
**Definition:** Microsoft's browser automation library (Apache-2.0)
**Use:** browser-cli backend
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §5.1

### Policy
🏷 *Architecture*
**Definition:** Rules in `.ai/policies/*.yaml` files
**Examples:** safety.yaml, gates.yaml, rbac.yaml, verifier-rules.yaml, loop-budget.yaml
**Authority:** Project team (committed to git)
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §10

### Policy tier
🏷 *Tool Contract*
**Definition:** Limits which verbs a tool allows
**Tiers:** `safe` (read) | `normal` (+ write) | `aggressive` (+ destructive)
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §9

### POSIX
🏷 *Inspiration*
**Definition:** Portable Operating System Interface — Unix standard
**Trinity application:** Tool Contract = "POSIX of Trinity tools"
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md)

### PROMOTED (state)
🏷 *Workflow*
**Definition:** Standard graph state — code in prod-ready folder
**Authority for transition:** human only (require_human_approval: true)
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) §3.3

### Pyramid of Judgment
🏷 *Verifier*
**Definition:** Escalation chain — Verifier → Policy → LLM Judge → Human
**Rule:** Always escalate, never auto-PASS on uncertainty
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §5

---

## Q

(reserved)

---

## R

### Reasoning Engine
🏷 *Architecture / Vocabulary*
**Definition:** Vendor AI (Claude/Codex/Gemini) — does planning, decomposition, inference
**NOT:** Trinity kernel (kernel coordinates, doesn't reason)
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0

### Recorder (browser)
🏷 *Browser*
**Definition:** browser-cli's bidirectional action recorder
**Use:** Record user actions for replay
**See:** browser-cli/docs/RECORDER_CONTRACT.md

### REPL (Read-Eval-Print Loop)
🏷 *Tool Contract*
**Definition:** Interactive mode of CLI tools
**Required:** All Trinity tools must support REPL
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §3.2

### Resume (loop)
🏷 *Loop*
**Definition:** Continue loop from latest checkpoint after process restart
**Command:** `trinity loop resume --session=<id>`
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §7.3

### retro-cli
🏷 *Tool*
**Definition:** Structured retrospective writer with schema enforcement
**Phase:** 7
**Action namespace:** `retro.*`
**Pipeline:** validate → lint → evidence check → memory-cli index
**See:** [`06_RETRO_CLI_SPEC.md`](06_RETRO_CLI_SPEC.md)

### Retrospective
🏷 *Memory*
**Definition:** Post-task documentation (what happened, lessons, evidence)
**Storage:** `.claude/retrospectives/*.md` or `ai-docs/retrospectives/`
**Indexed by:** memory-cli
**Confidence default:** `draft`
**See:** [`06_RETRO_CLI_SPEC.md`](06_RETRO_CLI_SPEC.md)

### RETRY (verdict)
🏷 *Verifier*
**Definition:** Verdict — recoverable failure, loop again with budget decrement
**Examples:** Test failed, transient error, missing artifact
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §2.1

### `rrr` (short code)
🏷 *Workflow*
**Definition:** Retrospective — write structured retro, update memory
**When:** After task done
**Triggers:** retro-cli + memory-cli index
**See:** [`06_RETRO_CLI_SPEC.md`](06_RETRO_CLI_SPEC.md)

### Run ID
🏷 *Tool Contract*
**Definition:** Unique identifier for a tool invocation
**Format:** `run_<timestamp>_<random>`
**Use:** Correlation across tools and audit log
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §6.1

---

## S

### `safe` (policy tier)
🏷 *Policy*
**Definition:** Most restrictive tier — read-only verbs
**Allows:** search, list, get, describe, health, stats
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §9.1

### SANDBOX (state)
🏷 *Workflow*
**Definition:** Standard graph state — multi-agent isolated work
**Sub-states:** gemini, claude, codex (parallel)
**Transition out:** vvv_pass (verifier) → DO
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) §3.3

### Schema
🏷 *Tool Contract*
**Definition:** JSON Schema definition for envelope/config
**Versioned:** `v1`, `v2`, etc.
**Backward compat:** Tool MUST support older schema
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §11

### Session
🏷 *Persistence*
**Definition:** Workflow capsule — `.ai/sessions/<id>/`
**ID format:** `sess_<date>_<slug>`
**Active link:** `.ai/sessions/active` (symlink)
**See:** [`08_DIAGRAMS.md`](08_DIAGRAMS.md) §17

### sha256
🏷 *Audit / Truth*
**Definition:** Cryptographic hash for artifacts (evidence integrity)
**Use:** Artifact metadata, audit hash chain
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4.4

### Shim (Trinity Shim)
🏷 *Architecture*
**Definition:** Adapter layer between vendor harness and Trinity kernel
**NOT:** Full harness replacement
**Components:** trinity-shell + vendor adapters (skills/AGENTS/rules)
**See:** [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md)

### Short codes
🏷 *Workflow*
**Definition:** 5-step workflow ritual: lll/vvv/nnn/gogogo/rrr
**Plus:** ccc (checkpoint)
**Origin:** ai-docs methodology
**See:** [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) §4.2

### Side effect (state)
🏷 *Graph*
**Definition:** Action triggered on state entry/exit
**Examples:** snapshot_prod, send_notification, run command
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) §9

### Skills (Claude Code)
🏷 *Vendor adapter*
**Definition:** Claude Code's extension model — instructions + slash commands
**Use:** Trinity Shim Phase 8 — bind /lll, /vvv, etc.
**Location:** `.claude/skills/<command>/instructions.md`
**See:** [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md) §4.2

### SQLite
🏷 *Storage*
**Definition:** Embedded relational database
**Use:** memory-cli backend (with FTS5)
**Version required:** 3.30+
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §3

### SSOT (Single Source of Truth)
🏷 *Configuration*
**Definition:** `.ai/ssot.yaml` — canonical project config
**Contains:** project name, paths, defaults, identity
**See:** [`08_DIAGRAMS.md`](08_DIAGRAMS.md) §17

### State machine
🏷 *Graph*
**Definition:** Finite state automaton — defines workflow lifecycle
**Engine:** YAML-defined, executed by Trinity kernel
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md)

### Stdin/stdout JSON
🏷 *Tool Contract / IPC*
**Definition:** Communication protocol for CLI tools
**Format:** Line-delimited JSON (NDJSON) on stdout, plain text on stdin
**Required:** All Trinity tools
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §5

### Supersession
🏷 *Memory*
**Definition:** Mark old document as obsolete, replaced by new
**NOT:** Delete — supersede preserves history
**Storage:** `supersession` table in memory.db
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §3.1

---

## T

### Tag (memory)
🏷 *Memory*
**Definition:** Free-form label on a document
**Examples:** `bugfix`, `auth`, `critical`
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §3.1

### Template (Bootstrap Pack)
🏷 *Bootstrap*
**Definition:** Markdown file with placeholders rendered by install.sh
**Examples:** CLAUDE.md.template, AGENTS.md.template
**Placeholders:** `{{PROJECT_NAME}}`, `{{TECH_STACK}}`, etc.
**See:** [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) §3

### Termination (loop)
🏷 *Loop*
**Definition:** Loop reaches end (terminal state)
**Reasons:** all_done, budget_exhausted, critical_dead, deadlock, cancelled, timeout
**See:** [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) §4.3

### THINK (state)
🏷 *Workflow*
**Definition:** Standard graph initial state — goal analysis + plan creation
**Transitions out:** plan_approved (human) → SANDBOX
**See:** [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) §3.3

### Tool Contract
🏷 *Foundation*
**Definition:** Universal CLI tool specification (POSIX of Trinity)
**Version:** v1.1
**Required for:** Every CLI tool in Trinity ecosystem
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md)

### Tool Registry
🏷 *Configuration*
**Definition:** `.ai/tools.yaml` — list of registered CLI tools
**Per-tool:** name, path, bin, schema_version, capabilities, contract_version
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §16

### Trinity Kernel
🏷 *Architecture*
**Definition:** Coordinator + Judge layer — Python CLI in `.ai/cli/`
**Role:** Orchestrate workflow, sessions, state, audit
**See:** "Kernel" entry above

### Trinity OS
🏷 *Top-level*
**Definition:** Whole system — kernel + brain + tools + shim + harness
**Vision:** "AI-native operating system"
**Status:** v2 (this spec pack)
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md)

### trinity-shell
🏷 *Tool*
**Definition:** Universal CLI wrapper for vendor harnesses
**Phase:** 8
**Action namespace:** `trinity.*`
**See:** [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md) §3

### Truth
🏷 *Vocabulary / Architecture*
**Definition:** Metaphor for verifiable evidence — artifacts + verdicts + audit
**Trinity rule:** Truth lives in files, not in AI's claim
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0

---

## U

### Unicode61 tokenizer
🏷 *Search*
**Definition:** SQLite FTS5 tokenizer — Unicode-aware (handles Thai)
**Setting:** `unicode61 remove_diacritics 1`
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §3.1

### Unix philosophy
🏷 *Inspiration*
**Definition:** "Do one thing well" + pipes + text streams (Eric Raymond, 1978)
**Trinity application:** CLI tools as organs, JSON IPC, microkernel
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §7.2

### Userland
🏷 *Architecture*
**Definition:** CLI tools layer — like Unix userspace
**Examples:** browser-cli, memory-cli, verify-cli, retro-cli
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §6

---

## V

### <upstream-project>
🏷 *Project Family*
**Definition:** Production e-commerce project (PHP+Smarty+MySQL)
**Role:** Largest user of Trinity v1; migration target for v2
**Renamed:** member-vbth3.com (2026-04-25)
**Retros:** 240+ in `.claude/retrospectives/`
**See:** [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md), [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §1.3

### Vector embedding
🏷 *Storage / Future*
**Definition:** Numeric representation of text for semantic similarity
**Use:** Phase 9 hybrid memory (ChromaDB)
**See:** [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §15

### Vendor harness
🏷 *Architecture*
**Definition:** Vendor's AI tool (Claude Code, Codex CLI, Gemini, Cursor)
**Trinity role:** Reasoning Engine + UI host
**See:** "Harness" entry, [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §4

### Verb
🏷 *Tool Contract*
**Definition:** Action a tool exposes (e.g., search, learn, screenshot)
**Local form:** `search`
**Canonical (action namespace):** `memory.search`
**See:** [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) §4a

### Verdict
🏷 *Verifier*
**Definition:** Output of verify-cli — one of: PASS / RETRY / NEEDS_HUMAN / DEAD
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §2.1

### verify-cli
🏷 *Tool*
**Definition:** Judge organ — deterministic verdict with file-based rules
**Phase:** 4
**Action namespace:** `verify.*`
**Rule file:** `.ai/policies/verifier-rules.yaml`
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md)

### Verifier
🏷 *Architecture*
**Definition:** Component that gives verdict (= verify-cli)
**Role:** Judge in Brain/Judge/Truth model
**See:** "Judge" entry above

### Verifier rules
🏷 *Policy*
**Definition:** YAML rules in `.ai/policies/verifier-rules.yaml`
**Per rule set:** required_evidence, pass_when, retry_when, needs_human_when, dead_when
**See:** [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) §3

### Vocabulary lock
🏷 *Decision*
**Definition:** Fixed terminology to prevent drift
**Core terms:** Knowledge Brain, Reasoning Engine, Coordinator, Judge, Truth, Organs
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0

### `vvv` (short code)
🏷 *Workflow*
**Definition:** Verify — 5 mandatory questions before planning
**Critical rule:** vvv MUST come before nnn (skipping = invalid session)
**Real case:** Skipping vvv = 3+ days wasted; using vvv = 30 min
**See:** [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) §4.2

---

## W

### Warp
🏷 *Vendor Host*
**Definition:** Terminal with AI integration
**Trinity role:** Lightweight terminal host
**Adapter:** WARP.md → CLAUDE.md (symlink)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §4.5

### Worker
🏷 *Vocabulary*
**Definition:** Vendor AI doing actual work (under Trinity coordination)
**See:** [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §0

### Workflow Graph
See "Graph" entry

### wp-cli
🏷 *Dependency / Future*
**Definition:** Official WordPress CLI (PHP, MIT)
**Use:** wordpress-cli wraps it (future)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §5.6

---

## X

### xstate
🏷 *Optional*
**Definition:** TypeScript state machine library
**Use:** Optional graph engine for Phase 6 (alternative: pytransitions, custom)
**See:** [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §6.4

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
CLI-first, MCP, Decided_by, Vocabulary lock, Anthropic insight

### Loop (8 terms)
Budget, Checkpoint, Decomposition, Loop, Resume, Termination, loop_state.json, Goal Tree

### Inspirations (8 terms)
Anthropic insight, arra-oracle-v3, Cognition AI, LangGraph, Microkernel, Oracle Framework, Plan 9, Unix philosophy

### Project Family (5 terms)
ai-docs, browser-cli, <upstream-project>, Trinity OS, TRINITY_EVOLUTION

### Vendor (6 terms)
Claude Code, Codex CLI, Cursor, Gemini CLI, Vendor harness, Warp

### Tools (9 terms)
browser-cli, ftp-cli, memory-cli, retro-cli, trinity-shell, verify-cli, wordpress-cli, Tool Contract, Tool Registry

---

## Cross-Reference Index (by Spec Doc)

### Terms defined in 00_BLUEPRINT
Brain, Coordinator, Iron Triangle, Knowledge Brain, MCP, Reasoning Engine, Trinity OS, Truth, Vocabulary lock

### Terms defined in 01_TOOL_CONTRACT
Action namespace, Compliance Test, Config, Envelope, Helpers, Policy tier, REPL, Run ID, Schema, Tool Contract, Verb

### Terms defined in 02_VERIFIER_SPEC
DEAD, Evidence, Judge, LLM Judge, NEEDS_HUMAN, PASS, Pyramid of Judgment, RETRY, Verdict, verify-cli, Verifier rules

### Terms defined in 03_GOAL_LOOP_SPEC
Budget, Checkpoint, Decomposition, Goal, Goal Tree, Loop, loop_state.json, Resume, Termination

### Terms defined in 04_GRAPH_SPEC
Authority, decided_by, Graph, Side effect, State machine, Trigger

### Terms defined in 05_MEMORY_CLI_SPEC
BM25, Confidence, FTS5, memory-cli, Supersession, Tag, Unicode61

### Terms defined in 06_RETRO_CLI_SPEC
retro-cli, Retrospective (frontmatter schema)

### Terms defined in 07_SHIM_SPEC
Adapter, Shim, Skills, trinity-shell

### Terms defined in 11_RELATED_PROJECTS
arra-oracle-v3, Cognition AI, LangGraph, Microkernel, Oracle Framework, Plan 9, Unix philosophy, oh-my-claudecode, etc.

---

## Quick Lookup by First Letter

```
A: Action namespace, Adapter, ai-docs, Anthropic, arra-oracle-v3, Artifact, Audit, Authority
B: BM25, Bootstrap Pack, Brain, browser-cli, Budget, Bun
C: Capsule, ccc, CDP, ChromaDB, Claude Code, CLI-first, Codex, Cognition AI, Compliance Test, 
   Confidence, Coordinator, Cursor
D: decided_by, Decomposition, DEAD, Deterministic, Devin, DO, Drizzle
E: Envelope, Escalation, Evidence, events.ndjson, Extension Platform
F: FTS5
G: Gemini CLI, gogogo, Goal, Goal Tree, Graph
H: Harness, Hash chain, Helpers, Hono
I: Iron Triangle, IPC
J: Judge
K: Kernel, Knowledge Brain
L: LangGraph, lll, LLM Judge, Loop, loop_state.json
M: MCP, memory-cli, Microkernel
N: NDJSON, NEEDS_HUMAN, Nervous system, nnn
O: oh-my-claudecode/codex, openclaude, Oracle Framework, Organ
P: PASS, Phase, Plan 9, Playwright, Policy, Policy tier, POSIX, PROMOTED, Pyramid of Judgment
R: Reasoning Engine, Recorder, REPL, Resume, retro-cli, Retrospective, RETRY, rrr, Run ID
S: safe, SANDBOX, Schema, Session, sha256, Shim, Short codes, Side effect, Skills, SQLite,
   SSOT, State machine, Stdin/stdout JSON, Supersession
T: Tag, Template, Termination, THINK, Tool Contract, Tool Registry, Trinity Kernel, Trinity OS,
   trinity-shell, Truth
U: Unicode61, Unix philosophy, Userland
V: <upstream-project>, Vector embedding, Vendor harness, Verb, Verdict, verify-cli, Verifier, vvv
W: Warp, Worker, wp-cli
X: xstate
```

---

## See also

- [`INDEX.md`](INDEX.md) — Master overview
- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master spec (definitions originate here)
- [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) — External project terms

## Changelog

- **v1.0.0 (2026-04-28)** — Initial complete glossary covering all spec docs
