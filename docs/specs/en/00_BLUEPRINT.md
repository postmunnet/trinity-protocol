---
title: "Trinity Big Evolution Blueprint v2 (English)"
subtitle: "CLI-Native AI Microkernel · Knowledge Brain · Reasoning Engine · Verifier"
language: English
version: 2.0.0
status: revised
last-updated: 2026-04-28
note: "Translation of ../00_BLUEPRINT.md"
---

# Trinity Big Evolution Blueprint v2 (English)

> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

---

## ✅ The 10 Committed Decisions

| # | Decision |
|---|----------|
| 1 | Trinity = **Coordinator/Judge**, not full AI harness |
| 2 | ai-docs = **Knowledge Brain**, not autonomous planner |
| 3 | Vendor AI = **Reasoning Engine** |
| 4 | **CLI-first only** for core tools |
| 5 | **MCP external servers ≠ core path** |
| 6 | **Tool Contract** before new tools |
| 7 | **Bootstrap Pack** mandatory for project portability |
| 8 | **Verifier rules** must be file-based |
| 9 | **Loop must support goal tree** + checkpoints |
| 10 | **Graph transitions** must declare `decided_by` |

---

## 0. Vocabulary Locked

```
Knowledge Brain    = ai-docs + memory-cli  (memory substrate / workflow knowledge)
Reasoning Engine   = Vendor AI              (planning / decomposition / inference)
Coordinator        = Trinity Kernel         (orchestrate / lifecycle / state)
Judge              = Verifier (verify-cli)  (evidence-based verdict)
Truth              = Artifacts + Verdicts   (files / hashes / log)
Organs             = CLI tools              (browser-cli, memory-cli, verify-cli, retro-cli, ftp-cli, ...)
Nervous system     = JSON stdio             (universal IPC)
Audit trace        = NDJSON logs            (events.ndjson, hash-chain)
Worker             = Vendor AI agents       (via vendor harness as host)
```

> **Trinity is not the tool. Trinity is the kernel that makes tools work together safely, intelligently, and verifiably.**

### Forbidden Vocabulary (causes confusion)

- ❌ "ai-docs = Brain" (too vague) → use **"Knowledge Brain"**
- ❌ "Trinity = Brain" → Trinity = **Coordinator + Judge**
- ❌ "Graph = the brain" → Graph = **workflow skeleton**
- ❌ "AI decides" → AI **proposes**, Verifier/Policy/Human **decide**

---

## 1. Why Harness Matters More Than Model

### Anthropic's Insight

```
1.6%  = AI decision logic
98.4% = harness / scaffolding
```

> Source: Public statements from Anthropic Claude Code team

Production AI wins because of **harness**, not model:
- permission gates · context mgmt · tool routing · sandbox · error recovery
- retry loop · budget · state · artifacts · UX · verifier

### Inspirations

Trinity OS architecture synthesizes:
- **Anthropic Claude Code** — 1.6%/98.4% insight (foundational)
- **Oracle Framework** — append-only memory + supersession
- **arra-oracle-v3** — hybrid search (FTS5+vector) reference
- **Unix philosophy + microkernel** — CLI-first, IPC, small kernel
- **<upstream-project> production** — 240 retros + 14 lessons
- **browser-cli** — CLI-native DNA reference

### Trinity Stack = ~100% Deterministic Harness

We **outsource AI decisions** to vendor harness (Claude Code/Codex/Gemini/Cursor)

> **Goal of Trinity: fill the harness gap** — not add AI logic

---

## 2. Stack Layout

```
┌─────────────────────────────────────────────┐
│ USER / WORK GOAL                            │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│ VENDOR HARNESS (Reasoning Engine + Host)    │
│ Claude Code / Codex / Gemini / Cursor       │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│ TRINITY SHIM (vendor-specific adapters)     │
│ - .claude/skills · AGENTS.md · .cursor/rules│
│ - slash commands · brain inject · log       │
└──────────────────────┬──────────────────────┘
                       ▼
┌─────────────────────────────────────────────┐
│ TRINITY MICROKERNEL (Coordinator + Judge)   │
│ - run lifecycle · loop · graph · policy     │
│ - gates · verifier orchestration            │
│ - artifact truth · audit (events.ndjson)    │
└──────────┬───────────────────┬──────────────┘
           ▼                   ▼
┌───────────────────┐   ┌─────────────────────┐
│ KNOWLEDGE BRAIN   │   │ CLI TOOL USERLAND   │
│ ai-docs +         │   │ browser-cli         │
│ memory-cli        │   │ memory-cli          │
│ - retros/lessons  │   │ retro-cli           │
│ - patterns        │   │ verify-cli          │
│ - semantic recall │   │ ftp-cli (future)    │
│                   │   │ + future tools      │
└───────────────────┘   └─────────────────────┘
```

> **Don't build a Claude Code clone** — use vendor harness as **host under Trinity ritual**

---

## 3. Three Levels of "Harness"

### 3.1 Test Harness
For testing tools — `<tool>/tests/harness.js`

### 3.2 AI Harness (vendor)
Claude Code / Codex / Cursor — accepts user input, manages context, calls LLM, dispatches tools

### 3.3 Run Harness / Trinity Kernel (ours)
Receives goal → opens run → consults brain → calls tools → verifies → retry/gate/dead/done → retros

> Trinity v0.1 doesn't replace AI Harness — it's a Run Harness that uses vendor harness as host

---

## 4. Iron Triangle: Harness + Loop + Graph

### 4.1 Harness = Interface/Host
- Use Claude Code/Codex/Gemini/Cursor
- Add Trinity shim
- Bind commands `lll/vvv/nnn/gogogo/rrr`
- Inject memory context from ai-docs
- Log events to Trinity

### 4.2 Loop = Heart of "Get Things Done"

**No linear-only** — must support goal tree:

```
root goal
→ decompose into sub-goals       (decided_by: vendor AI)
→ enqueue sub-goals               (kernel)
→ run each through inner loop     (kernel)
→ verify each                     (verifier)
→ aggregate result                (kernel)
→ final retro                     (rrr)
```

Must have: max iterations · timeout · failure counter · retry scope · human escalation · terminal condition · **checkpoint/resume**

### 4.3 Graph = Workflow Skeleton (NOT a brain!)

**Two layers:**

```
Kernel Runtime Graph = stable / minimal
  READY → SETUP → BUSY → VERIFYING → GATED → TERMINAL

Domain Workflow Graph = configurable / project-specific
  THINK → SANDBOX → DO → VERIFIED → PROMOTED → DEPLOYED → RETRO → DONE
```

**Transition Authority (CRITICAL!):**

```yaml
transitions:
  - from: SANDBOX
    to: DO
    trigger: vvv_pass
    decided_by: verifier              # ← deterministic
    require_human_approval: false
  - from: VERIFIED
    to: PROMOTED
    trigger: promote_request
    decided_by: human                 # ← human only
    require_human_approval: true
```

**Hard rule:**

```
AI may PROPOSE transition.
AI may NOT DECIDE transition.

Authority ∈ {verifier, policy, human, kernel}
```

---

## 5. Knowledge Brain (ai-docs) — Make it Hard

### Currently = Soft Brain
- markdown docs / retros / real_lessons / workflow ritual / patterns

### Problems
- AI doesn't follow templates consistently
- Search only via grep
- No semantic recall
- Memory not auto-injected into lll/vvv/nnn
- New retros not structured enough
- **No curation layer** — garbage in, garbage out

### Goal = Hard Brain
- memory-cli (FTS5 → hybrid)
- retro-cli (additive frontmatter schema)
- structured frontmatter (verified/draft/superseded confidence)
- auto-index after rrr
- evidence-linked memory
- search filters (default = verified only)

### Important Boundary

> **ai-docs = Knowledge Brain** (memory + workflow ritual)
> **NOT autonomous planner** — planning by vendor AI under Trinity coordination

---

## 6. CLI Tool Ecosystem = Userland

```
Trinity         = kernel (Coordinator + Judge)
CLI tools       = userland / organs / drivers
stdin/stdout    = IPC / nervous system
NDJSON log      = audit trace
Schema          = ABI
```

| Unix/Microkernel | Trinity |
|------------------|---------|
| do one thing well | browser-cli does browser, memory-cli does memory |
| pipes | stdin/stdout JSON |
| userland services | CLI tools |
| kernel scheduler | Trinity run/loop/graph |
| syscall ABI | response schema |
| logs | NDJSON events |
| drivers | tool adapters |

> browser-cli = **reference DNA** of the ecosystem

---

## 7. Core Tool Set

| Tool | Role | Status | Phase |
|------|------|--------|-------|
| `browser-cli` | eyes + hands (executor/observer) | ✅ | - |
| `memory-cli` | Knowledge Brain recall | 🆕 | 2 |
| `retro-cli` | structured memory writer | 🆕 | 7 |
| `verify-cli` | deterministic Judge | 🆕 | 4 |
| `wordpress-cli` | WP operations | 📋 | future |
| `ftp-cli` | FTP/SFTP transfer (artifacts, remote sync) | 📋 | future |
| `seo-cli` | SEO audit | 📋 | future |
| `deploy-cli` | deployment | 📋 | future |

### ⚠️ browser-cli Gap (from MCP migration)

Before removing Playwright MCP — add to browser-cli:
- `tabs` (multi-tab management)
- `handle-dialog` (alert/confirm/prompt)

---

## 8. Tool Contract = POSIX of Trinity

Every CLI tool must have:
1. stdin/stdout JSON protocol
2. Versioned response schema
3. `--config / --run-id / --log-file`
4. Policy tier (safe/normal/aggressive)
5. Command contract doc
6. **Action namespace** (e.g., `memory.search`, `browser.screenshot`)
7. Tests for command + schema
8. **Contract compliance test** (`trinity-contract-test`)

### Common Envelope (success)

```json
{
  "ok": true,
  "command": "search",
  "action": "memory.search",
  "data": {},
  "artifacts": [],
  "error": null,
  "meta": {
    "tool": "memory-cli",
    "schema_version": "1",
    "run_id": "run_123",
    "duration_ms": 42,
    "timestamp": "2026-04-28T12:34:56Z"
  }
}
```

See: [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md)

---

## 9. MCP Stance — LOCKED

```
Core protocol           = CLI-first ONLY
External MCP servers    = ❌ NOT used (Playwright/Morphllm/Sequential removed)
Vendor built-in tools   = ✅ Used normally (Read/Write/Edit/Bash from Claude Code)
HTTP/API                = optional bridge (future)
```

### Replacement Mapping

| Old MCP | Replaced With |
|---------|---------------|
| `mcp__playwright__*` (13 tools) | `browser-cli` |
| `mcp__morphllm-fast-apply__*` (8 tools) | Vendor's Read/Write/Edit/Glob |
| `mcp__sequential-thinking__*` | ai-docs workflow + Trinity loop |
| `mcp__ide__executeCode` | Kept (vendor IDE bridge) |

### Reasoning
- <upstream-project> used Playwright MCP — but browser-cli replaces it ~100%
- CLI-first = truly tool-agnostic (Claude/Codex/Gemini/Cursor all work)
- MCP locks to Claude Code only — contradicts vision

---

## 10. Governance / Gates

```
Goal Boundary Gate
Evidence / VVV Gate
Scope / Sandbox Gate
Capability Grant Gate
Policy Preflight Gate
Runtime Safety Gate
Verifier Gate                         (← needs rules)
Human Approval Gate
Budget / Timeout / Concurrency Gate
Terminal Freeze Gate
Override Gate
Memory Promotion Gate
```

### Pyramid of Judgment (CRITICAL!)

```
1. Deterministic verifier   (verify-cli + verifier-rules.yaml)
   ↓ unsure
2. Policy rule              (.ai/policies/*.yaml)
   ↓ unsure
3. LLM judge (gated)        (last resort, audit log)
   ↓ unsure
4. Human escalation
```

> AI **must NEVER be sole judge** — verifier must have real rules, not "AI thinks so"

---

## 11. Browser Layer = Reality Interface

**Why:** AI doesn't see what user sees — browser-cli lets AI read facts (click/submit/nav/devtools/screenshot/DOM/AJAX/outline)

### Scope (don't expand)
- Browser CLI = **executor / observer / fact-provider**
- NOT: judge / workflow planner / autonomous agent
- User Action Log = opt-in / privacy-safe / fact-first / local-only

---

## 12. Extension Platform Vision (Save for Later)

```
Trinity Core    = OS
Browser CLI     = Runtime
Extensions      = Apps
Manifest        = Contract
Permission      = Boundary
Test Suite      = Law
Registry        = Ecosystem
```

Order:
```
build organs first → tool registry → SDK → manifest → test suite → registry
```

> Don't build Android before having an app

---

## 13. Revised Roadmap (10 Phases)

### Phase 0 — Vocabulary + Architecture Lock ✅
- Vocabulary locked
- Transition authority concept
- Goal schema concept
- 10 decisions committed

### Phase 0.5 — Bootstrap Pack 🆕 (CRITICAL)
- `BOOTSTRAP_PACK.md`
- `install.sh` + `verify-install.sh`
- `CLAUDE.md / AGENTS.md / GEMINI.md` templates (inline short codes)
- ai-docs minimal + .ai/ minimal

→ **Trinity portable to new projects, AI knows workflow immediately**

### Phase 1 — Tool Contract + Compliance Test
- `TOOL_CONTRACT.md` (exists — refine)
- Common response/error schema
- Action namespace convention
- `trinity-contract-test` CLI

### Phase 2 — memory-cli v0.1
- Clone browser-cli pattern (Node + SQLite FTS5)
- Commands: index/learn/search/get/list/stats/supersede/reflect
- Confidence tags (verified/draft/superseded)
- Index `.claude/retrospectives/` + `ai-docs/real_lessons/`

→ **ai-docs becomes searchable Knowledge Brain**

### Phase 3 — Wire memory-cli into lll/vvv/nnn
- `lll` retrieves relevant retros
- `vvv` searches previous incidents
- `nnn` uses memory hints
- Write context artifact

→ **AI doesn't start from scratch every session**

### Phase 4 — verify-cli + verifier-rules.yaml 🆕 (CRITICAL)
- `.ai/policies/verifier-rules.yaml` (file-based rules)
- `verify-cli` (deterministic checks)
- Evidence type rules
- Verdict schema (PASS/RETRY/NEEDS_HUMAN/DEAD)
- Pyramid of judgment

→ **Judge has real rules**

### Phase 5 — Goal Tree + Loop State 🆕 (CRITICAL)
- Goal schema (yaml)
- `loop_state.json` per session
- Sub-goal queue
- Checkpoint/resume
- Retry budget

→ **Trinity loop handles big tasks, not just goal strings**

### Phase 6 — Graph YAML + Transition Authority 🆕 (CRITICAL)
- `.ai/graphs/standard.yaml`
- `.ai/graphs/deploy.yaml`
- Transitions specify `decided_by`
- `graph validate / status / transition`

→ **Workflow can branch/recover with clear authority**

### Phase 7 — retro-cli v0.1
- Additive frontmatter schema
- Validate required fields
- Evidence checker
- Auto `memory-cli index` for deterministic retro artifacts

→ **rrr → real memory update**

### Phase 8 — Trinity Shim (Universal + Adapters)
- `trinity-shell` universal CLI wrapper
- Vendor adapters (.claude/skills, AGENTS.md, .cursor/rules, GEMINI.md)

→ **Vendor harness becomes host under Trinity ritual**

### Phase 9 — Hybrid Memory (vector)
- ChromaDB integration
- Hybrid ranking (FTS5 + vector)
- `similar`, clustering, viz (optional)

### Phase 10 — Extension Platform
- Manifest · SDK · test suite · registry · trust levels

---

## 14. Strategic Order

```
Phase 0 → 0.5 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
```

**Critical path:** Phase 0.5 (Bootstrap) → Phase 1 (Contract) → Phase 2 (memory-cli) → Phase 4 (verifier) → Phase 5 (loop)

**Reasoning:**
- Bootstrap = solves portability (the original pain)
- Contract = blocker for all tools
- memory-cli = immediate ROI (240 retros)
- verifier = blocker for any judge logic in loop
- loop = blocker for "complete task"

---

## 15. Don't Do These Now

- ❌ Full AI harness (openclaude-style)
- ❌ Full MCP server as core
- ❌ Platform registry (Phase 10)
- ❌ Android-style extension SDK
- ❌ Big dashboard
- ❌ Multi-agent graphs (complex)
- ❌ ChromaDB before FTS5
- ❌ Auto deploy / auto PR
- ❌ GitHub issue as core workflow
- ❌ Linear loop only
- ❌ Graph without `decided_by`
- ❌ Verifier without rules

---

## 16. Five Locked Insights

1. **Trinity = 100% deterministic harness** — strength, not weakness
2. **Don't build full harness** — use vendor + shim
3. **Harness + Loop + Graph + Goal Tree + Verifier** = all required
4. **CLI-native** = debuggable, tool-agnostic, composable, auditable, versionable
5. **Knowledge Brain / Reasoning Engine / Coordinator / Judge** = 4 distinct layers

---

## 17. First 30-90 Days (Realistic)

### Sprint 1 (Week 1-2): Bootstrap Pack
- Templates (CLAUDE.md/AGENTS.md/GEMINI.md inline short codes)
- install.sh
- Minimal `.ai/` + ai-docs/

→ Trinity portable to new projects

### Sprint 2 (Week 3-4): Tool Contract + Compliance Test
- TOOL_CONTRACT v1.0 frozen
- trinity-contract-test
- browser-cli upgrade (tabs, handle-dialog, contract compliance)

### Sprint 3 (Week 5-6): memory-cli skeleton + index
- memory-cli v0.1 (FTS5)
- Index 240 retros + 14 lessons

### Sprint 4 (Week 7-8): Wire memory + verifier basic
- `lll`/`vvv` pull memory
- verify-cli + verifier-rules.yaml (basic)

### Sprint 5 (Week 9-10): Goal Tree + Minimal Loop
- Goal schema + loop_state.json
- `trinity loop --goal`

### Sprint 6 (Week 11-12): Graph YAML + retro-cli
- `.ai/graphs/standard.yaml`
- Transition authority
- retro-cli + deterministic memory index

---

## 18. Final Picture

```
User:
  "Audit SEO and fix this article"

Vendor Harness (Reasoning Engine):
  Claude Code / Codex receives + decomposes

Trinity Shim:
  calls memory-cli for context
  calls vvv preflight
  creates plan (vendor proposes)

Trinity Kernel (Coordinator):
  opens run · loads goal tree · drives loop · checks gates
  · calls browser-cli/tools per graph

Browser CLI (Organ):
  opens real web · reads DOM · screenshots · asserts

Verify CLI (Judge):
  checks artifacts per verifier-rules.yaml
  → PASS / RETRY / NEEDS_HUMAN / DEAD

Retro CLI:
  writes retro artifact · memory-cli index

Knowledge Brain:
  smarter on the next real task
```

---

## 19. Communication Vocabulary

### One-liner (LOCKED)

> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

### Cheat Sheet (LOCKED)

```
Knowledge Brain    = ai-docs + memory-cli
Reasoning Engine   = Vendor AI
Coordinator        = Trinity Kernel
Judge              = Verifier
Truth              = Artifacts + Verdicts
Organs             = CLI tools
Nerves             = JSON stdio
Audit              = NDJSON logs
```

---

## 20. Open Questions (For Brainstorm)

1. Tool contract common envelope schema — final?
2. memory-cli use Node or Python?
3. FTS5 schema fields?
4. Existing 240 retros — how to parse?
5. Retro frontmatter required fields?
6. lll/vvv/nnn — when to call memory-cli?
7. Loop human gate at which step?
8. First workflow graph — standard or deploy?
9. Trinity shim — start with Claude Code skills or shell wrapper?
10. Verifier rules YAML format — final?
11. Goal tree storage — JSON file or SQLite?
12. Graph engine — Python lib or build custom?

---

## Final

> **Trinity Big Evolution = Turn the discipline you do manually into a system that automates that discipline**

> **Architecture Direction: 9.5/10**
> **Implementation Readiness: 9/10** (becomes 9.5/10 after closing 3 specs: Bootstrap, Contract+Test, Verifier Rules)

---

## See also

- [`README.md`](README.md) — Public-facing overview
- [`INDEX.md`](INDEX.md) — Master overview
- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) — Tool ABI (English)
- [`12_GLOSSARY.md`](12_GLOSSARY.md) — Glossary (English)
- [`../00_BLUEPRINT.md`](../00_BLUEPRINT.md) — Thai version (more detail)

---

## Changelog

- **v2.0.0 (2026-04-28)** — English translation of v2.0.0 blueprint
