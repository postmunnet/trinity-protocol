---
title: "Trinity Big Evolution Blueprint"
subtitle: "CLI-Native AI Microkernel · Knowledge Brain · Reasoning Engine · Verifier"
version: 2.0.0
status: revised
last-updated: 2026-04-28
revision-notes: "v2 — integrates 10 committed decisions + 5 critical fixes (Brain, Verifier, Goal Tree, Graph Authority, Bootstrap)"
---

# Trinity Big Evolution Blueprint v2

> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

---

## ✅ 10 Committed Decisions

| # | Decision |
|---|----------|
| 1 | Trinity = **Coordinator/Judge**, not full AI harness |
| 2 | ai-docs = **Knowledge Brain**, not autonomous planner |
| 3 | Vendor AI = **Reasoning Engine** |
| 4 | **CLI-first only** for core tools |
| 5 | **MCP external servers ≠ core path** (Playwright/Morphllm/Sequential ตัด) |
| 6 | **Tool Contract** must exist before new tools |
| 7 | **Bootstrap Pack** is mandatory for project portability |
| 8 | **Verifier rules** must be file-based (not embedded) |
| 9 | **Loop must support goal tree** + checkpoints |
| 10 | **Graph transitions** must declare `decided_by` |

---

## 0. แกนเดียว — Vocabulary Locked

```text
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

### ⚠️ Vocabulary ที่ห้ามใช้ผิด

- ❌ **"ai-docs = Brain"** (สั้นเกิน, สับสน) → ใช้ **"Knowledge Brain"**
- ❌ **"Trinity = Brain"** → Trinity = **Coordinator + Judge**
- ❌ **"Graph = สมอง"** → Graph = **workflow skeleton**
- ❌ **"AI ตัดสิน"** → AI **propose**, Verifier/Policy/Human **decide**

---

## 1. Harness สำคัญกว่า Model (Anthropic Insight)

```text
1.6%  = AI decision logic
98.4% = harness / scaffolding
```

> ที่มา: Anthropic Claude Code team's public insight — ดู [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §7.1

Production AI ชนะเพราะ **harness** ไม่ใช่ model:
- permission gates · context mgmt · tool routing · sandbox · error recovery
- retry loop · budget · state · artifacts · UX · verifier

### Inspirations Note

Trinity OS architecture synthesizes:
- **Anthropic Claude Code** — 1.6%/98.4% insight (foundational)
- **Oracle Framework** — append-only memory + supersession ([`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §2.1)
- **arra-oracle-v3** — hybrid search (FTS5+vector) reference ([`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §2.2)
- **Unix philosophy + microkernel** — CLI-first, IPC, small kernel
- **<upstream-project> production** — 240 retros + 14 lessons (Knowledge Brain seed)
- **browser-cli (yai)** — CLI-native DNA reference

### Trinity stack = ~100% deterministic harness

เพราะ **outsource AI decision** ให้ vendor harness (Claude Code/Codex/Gemini/Cursor)

> **เป้าหมาย Trinity: เติม harness gap** — ไม่ใช่เพิ่ม AI logic

---

## 2. Stack Layout

```text
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

> ไม่สร้าง Claude Code clone — ใช้ vendor harness เป็น **host ที่อยู่ใต้ Trinity ritual**

---

## 3. นิยาม Harness 3 ระดับ

### 3.1 Test Harness
ใช้ทดสอบ tool — `<tool>/tests/harness.js`

### 3.2 AI Harness (vendor)
Claude Code / Codex / Cursor — รับ user input · จัดการ context · เรียก LLM · stream · dispatch tools

### 3.3 Run Harness / Trinity Kernel (ของเรา)
รับ goal → เปิด run → consult brain → call tools → verify → retry/gate/dead/done → retro

> Trinity v0.1 **ไม่แทน AI Harness** — เป็น Run Harness ที่ใช้ vendor harness เป็น host

---

## 4. Iron Triangle: Harness + Loop + Graph

### 4.1 Harness = Interface/Host
- vendor harness ต่อ + Trinity shim adapter
- ผูกคำสั่ง `lll/vvv/nnn/gogogo/rrr`
- inject memory context จาก ai-docs
- log events เข้า Trinity

### 4.2 Loop = หัวใจของ "ทำจนจบ"
**ห้าม linear-only** — ต้องรองรับ goal tree:
```text
root goal
→ decompose into sub-goals       (decided_by: vendor AI)
→ enqueue sub-goals               (kernel)
→ run each through inner loop     (kernel)
→ verify each                     (verifier)
→ aggregate result                (kernel)
→ final retro                     (rrr)
```

ต้องมี: max iterations · timeout · failure counter · retry scope · human escalation · terminal condition · **checkpoint/resume**

ดู: [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md)

### 4.3 Graph = workflow skeleton (ไม่ใช่สมอง!)

**2 ชั้น:**
```text
Kernel Runtime Graph = stable / minimal
  READY → SETUP → BUSY → VERIFYING → GATED → TERMINAL

Domain Workflow Graph = configurable / project-specific
  THINK → SANDBOX → DO → VERIFIED → PROMOTED → DEPLOYED → RETRO → DONE
```

**Transition Authority (ใหม่!):**
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

**Rule หลัก:**
```text
AI may PROPOSE transition.
AI may NOT DECIDE transition.

Authority ∈ {verifier, policy, human, kernel}
```

ดู: [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md)

---

## 5. Knowledge Brain (ai-docs) — ทำให้ hard ขึ้น

### ai-docs ปัจจุบัน = soft brain
- markdown docs / retros / real_lessons / workflow ritual / patterns

### ปัญหา
- AI ไม่ทำตาม template เสมอ
- ค้นได้แค่ grep
- ไม่มี semantic recall
- memory ไม่ถูก inject อัตโนมัติเข้า lll/vvv/nnn
- retro ใหม่ไม่ structured พอ
- **ไม่มี curation layer** — garbage in, garbage out

### เป้าหมาย — hard brain
- memory-cli (FTS5 → hybrid)
- retro-cli (additive frontmatter schema)
- structured frontmatter (verified/draft/superseded confidence)
- auto-index after rrr
- evidence-linked memory
- filter ใน search (default = verified only)

### ⚠️ ขอบเขตที่สำคัญ
> **ai-docs = Knowledge Brain** (memory + workflow ritual)
> **NOT autonomous planner** — planning ทำโดย vendor AI ภายใต้ Trinity coordination

---

## 6. CLI Tool Ecosystem = Userland

```text
Trinity         = kernel (Coordinator + Judge)
CLI tools       = userland / organs / drivers
stdin/stdout    = IPC / nervous system
NDJSON log      = audit trace
Schema          = ABI
```

| Unix/Microkernel | Trinity |
|-------------------|---------|
| do one thing well | browser-cli ทำ browser, memory-cli ทำ memory |
| pipes | stdin/stdout JSON |
| userland services | CLI tools |
| kernel scheduler | Trinity run/loop/graph |
| syscall ABI | response schema |
| logs | NDJSON events |
| drivers | tool adapters |

> browser-cli = **reference DNA** ของ ecosystem

---

## 7. Core Tool Set

| Tool | Role | Status | Phase |
|------|------|--------|-------|
| `browser-cli` | eyes + hands (executor/observer/fact-provider) | ✅ มีแล้ว | - |
| `memory-cli` | Knowledge Brain recall organ | 🆕 | Phase 2 |
| `retro-cli` | structured memory writer | 🆕 | Phase 3 |
| `verify-cli` | deterministic Judge organ | 🆕 | Phase 4 |
| `wordpress-cli` | WP operations (wraps wp-cli) | 📋 future | - |
| `ftp-cli` | FTP/SFTP transfer (artifacts, remote sync) | 📋 future | - |
| `seo-cli` | SEO audit | 📋 future | - |
| `deploy-cli` | deployment | 📋 future | - |
| `grep-cli` | smart search | 📋 future | - |
| `god-team-cli` | multi-agent dispatch | 📋 future | - |

### ⚠️ Browser-CLI gap (จาก MCP migration)

ก่อนเลิก Playwright MCP — เพิ่มใน browser-cli:
- `tabs` (multi-tab management)
- `handle-dialog` (alert/confirm/prompt)

---

## 8. Tool Contract = POSIX ของ Trinity

ทุก CLI tool ต้องมี:
1. stdin/stdout JSON protocol
2. versioned response schema
3. `--config / --run-id / --log-file`
4. policy tier (safe/normal/aggressive)
5. command contract doc
6. **action namespace** (e.g. `memory.search`, `browser.screenshot`) — **ใหม่!**
7. tests for command + schema
8. **contract compliance test** (`trinity-contract-test`) — **ใหม่!**

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

ดู: [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md)

---

## 9. MCP Stance — LOCKED

```text
Core protocol           = CLI-first ONLY
External MCP servers    = ❌ ไม่ใช้ (Playwright/Morphllm/Sequential ตัด)
Vendor built-in tools   = ✅ ใช้ตามปกติ (Read/Write/Edit/Bash ของ Claude Code)
HTTP/API                = optional bridge (อนาคต)
```

### Replacement Mapping (committed)

| MCP เดิม | แทนด้วย |
|---------|---------|
| `mcp__playwright__*` (13 tools) | `browser-cli` |
| `mcp__morphllm-fast-apply__*` (8 tools) | Vendor's Read/Write/Edit/Glob |
| `mcp__sequential-thinking__*` | ai-docs workflow + Trinity loop |
| `mcp__ide__executeCode` | คงไว้ (vendor IDE bridge) |

### เหตุผล
- <upstream-project> ใช้ Playwright MCP — แต่ browser-cli replace ได้เกือบ 100%
- CLI-first = tool-agnostic จริง (Claude/Codex/Gemini/Cursor ใช้ตัวเดียวกัน)
- MCP ผูกกับ Claude Code อย่างเดียว — ขัด vision

---

## 10. Governance / Gates

```text
Goal Boundary Gate
Evidence / VVV Gate
Scope / Sandbox Gate
Capability Grant Gate
Policy Preflight Gate
Runtime Safety Gate
Verifier Gate                         (← ต้องมี rules)
Human Approval Gate
Budget / Timeout / Concurrency Gate
Terminal Freeze Gate
Override Gate
Memory Promotion Gate
```

### Pyramid of Judgment (ใหม่ — สำคัญ!)

```text
1. Deterministic verifier   (verify-cli + verifier-rules.yaml)
   ↓ unsure
2. Policy rule              (.ai/policies/*.yaml)
   ↓ unsure
3. LLM judge แบบ gated      (last resort, audit log)
   ↓ unsure
4. Human escalation
```

> AI **ห้ามเป็น sole judge** — verifier ต้องมีกฎจริง ไม่ใช่ "AI คิดว่าผ่าน"

ดู: [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md)

### Port จาก <upstream-project>/ai-docs
- `vvv` → evidence gate
- Safety B1-B4 → policy rules
- override + audit quota
- `rrr` → retro/memory update
- `{{APP_DIR}}` → path abstraction
- hash-chain events → audit truth

### ไม่ port เป็น core
- multi-AI ritual · GitHub issue flow · auto PR · fluid leadership

---

## 11. Browser Layer = Reality Interface

**Why:** AI ไม่เห็นสิ่งที่ user เห็น — browser-cli ให้ AI อ่าน facts (click/submit/nav/devtools/screenshot/DOM/AJAX/outline)

### Scope (ห้ามขยาย)
- Browser CLI = **executor / observer / fact-provider**
- ไม่ใช่: judge / workflow planner / autonomous agent
- User Action Log = opt-in / privacy-safe / fact-first / local-only

---

## 12. Extension Platform Vision (เก็บไว้ทีหลัง)

```text
Trinity Core    = OS
Browser CLI     = Runtime
Extensions      = Apps
Manifest        = Contract
Permission      = Boundary
Test Suite      = Law
Registry        = Ecosystem
```

ลำดับ:
```text
build organs first → tool registry → SDK → manifest → test suite → registry
```

> อย่าสร้าง Android ก่อนมี app

---

## 13. Revised Roadmap (10 Phases)

### Phase 0 — Vocabulary + Architecture Lock ✅
- ปรับ blueprint vocabulary
- เพิ่ม transition authority concept
- เพิ่ม goal schema concept
- Decisions 10 ข้อ committed

### Phase 0.5 — Bootstrap Pack 🆕 (CRITICAL)
- `BOOTSTRAP_PACK.md`
- `install.sh` + `verify-install.sh`
- `CLAUDE.md / AGENTS.md / GEMINI.md` templates (inline short codes)
- ai-docs minimal (QUICK_START + SHORT_CODES + CORE_RULES)
- `.ai/` minimal (ssot.yaml + policies + tools.yaml + graphs)

→ **เอา Trinity ไป project ใหม่แล้ว AI รู้วิธีทำงานทันที**

ดู: [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md)

### Phase 1 — Tool Contract + Compliance Test
- `TOOL_CONTRACT.md` (มีแล้ว — ปรับเพิ่ม)
- common response/error schema
- action namespace convention
- `trinity-contract-test` CLI

→ **CLI tools มี ABI เดียวกัน + ทดสอบ compliance ได้**

### Phase 2 — memory-cli v0.1
- Clone browser-cli pattern (Node + SQLite FTS5)
- Commands: index/learn/search/get/list/stats/supersede/reflect
- Confidence tags (verified/draft/superseded)
- Index `.claude/retrospectives/` + `ai-docs/real_lessons/` + `.ai/sessions/*/99_SUMMARY.md`

→ **ai-docs เป็น searchable Knowledge Brain**

### Phase 3 — Wire memory-cli into lll/vvv/nnn
- `lll` ดึง relevant retros
- `vvv` หา previous incidents
- `nnn` ใช้ memory hints
- write context artifact

→ **AI ไม่เริ่มจากศูนย์ทุก session**

### Phase 4 — verify-cli + verifier-rules.yaml 🆕 (CRITICAL)
- `.ai/policies/verifier-rules.yaml` (file-based rules)
- `verify-cli` (deterministic checks)
- evidence type rules
- verdict schema (PASS/RETRY/NEEDS_HUMAN/DEAD)
- pyramid of judgment

→ **Judge มีกฎจริง**

### Phase 5 — Goal Tree + Loop State 🆕 (CRITICAL)
- goal schema (`yaml`)
- `loop_state.json` per session
- sub-goal queue
- checkpoint/resume
- retry budget

→ **Trinity loop รองรับงานใหญ่ ไม่ใช่ goal string เดียว**

### Phase 6 — Graph YAML + Transition Authority 🆕 (CRITICAL)
- `.ai/graphs/standard.yaml`
- `.ai/graphs/deploy.yaml`
- transitions ระบุ `decided_by`
- `graph validate / status / transition`

→ **workflow branch/recovery ได้ + authority ชัด**

### Phase 7 — retro-cli v0.1
- Additive frontmatter schema
- Validate required fields
- Evidence checker
- ไม่ break old retros
- Auto `memory-cli index` for deterministic retro artifacts

→ **rrr → memory update จริง**

### Phase 8 — Trinity Shim (Universal + Adapters)
- `trinity-shell` universal CLI wrapper
- Vendor adapters:
  - `.claude/skills/` (Claude Code)
  - `AGENTS.md` (Codex)
  - `.cursor/rules/` (Cursor)
- inject memory context · call Trinity CLI · write events

→ **Vendor harness = host ใต้ Trinity ritual**

### Phase 9 — Hybrid Memory (vector)
- ChromaDB หรือ similar
- Hybrid ranking (FTS5 + vector)
- `similar`, clustering, viz (optional)

→ **Brain ค้นทั้ง keyword + semantic**

### Phase 10 — Extension Platform
- manifest · SDK · test suite · registry · trust levels

→ **คนอื่นสร้าง capability เสียบ Trinity**

---

## 14. Strategic Order

```text
Phase 0 → 0.5 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
```

**Critical path:** Phase 0.5 (Bootstrap) → Phase 1 (Contract) → Phase 2 (memory-cli) → Phase 4 (verifier) → Phase 5 (loop)

**ทำไมลำดับนี้:**
- Bootstrap = **แก้ปัญหา portability ตั้งต้น**
- Contract = blocker ของทุก tool
- memory-cli = ROI ทันที (240 retros)
- verifier = blocker ของ loop ที่ตัดสินอะไรได้
- loop = blocker ของ "ทำจนจบ"

---

## 15. ห้ามทำตอนนี้

- ❌ Full AI harness แบบ openclaude
- ❌ Full MCP server เป็น core
- ❌ Platform registry (Phase 10)
- ❌ Android-style extension SDK
- ❌ Dashboard ใหญ่
- ❌ Multi-agent graph ซับซ้อน
- ❌ ChromaDB/vector ก่อน FTS5
- ❌ Auto deploy / auto PR
- ❌ GitHub issue เป็น core workflow
- ❌ Linear loop only
- ❌ Graph ที่ไม่มี `decided_by`
- ❌ Verifier ที่ไม่มี rules

---

## 16. 5 Insights ที่ Lock (revised)

1. **Trinity = 100% deterministic harness** — ข้อดี ไม่ใช่ข้อเสีย
2. **ยังไม่ต้อง full harness** — ใช้ vendor + shim ก่อน
3. **Harness + Loop + Graph + Goal Tree + Verifier** = ขาดไม่ได้
4. **CLI-native** = debuggable, tool-agnostic, composable, auditable, versionable
5. **Knowledge Brain / Reasoning Engine / Coordinator / Judge** = 4 layer แยกชัด

---

## 17. 30-90 วันแรก (revised — realistic)

### Sprint 1 (สัปดาห์ 1-2): Bootstrap Pack
- Templates (CLAUDE.md/AGENTS.md/GEMINI.md inline short codes)
- install.sh
- minimal `.ai/` + ai-docs/

→ **Trinity port ไป project ใหม่ได้**

### Sprint 2 (สัปดาห์ 3-4): Tool Contract + Compliance Test
- TOOL_CONTRACT v1.0 frozen
- trinity-contract-test
- browser-cli upgrade (tabs, handle-dialog, contract compliance)

→ **CLI tools มี ABI**

### Sprint 3 (สัปดาห์ 5-6): memory-cli skeleton + index
- memory-cli v0.1 (FTS5)
- Index 240 retros + 14 lessons
- Commands: index/search/get/list/stats

→ **ค้น retros ได้จาก CLI**

### Sprint 4 (สัปดาห์ 7-8): Wire memory + verifier basic
- `lll`/`vvv` ดึง memory
- verify-cli + verifier-rules.yaml (basic)

→ **AI มี context + Judge มีกฎ**

### Sprint 5 (สัปดาห์ 9-10): Goal Tree + Minimal Loop
- goal schema + loop_state.json
- `trinity loop --goal` (linear + sub-goal queue)
- max iter, escalation, terminal

→ **Trinity semi-auto**

### Sprint 6 (สัปดาห์ 11-12): Graph YAML + retro-cli
- `.ai/graphs/standard.yaml`
- transition authority
- retro-cli + deterministic memory index

→ **Workflow + retro loop ครบ**

---

## 18. ภาพสุดท้าย

```text
User:
  "ช่วยตรวจ SEO และแก้บทความนี้"

Vendor Harness (Reasoning Engine):
  Claude Code / Codex รับ + decompose

Trinity Shim:
  เรียก memory-cli หา context
  เรียก vvv preflight
  สร้าง plan (vendor proposes)

Trinity Kernel (Coordinator):
  เปิด run · load goal tree · คุม loop · ตรวจ gates
  · เรียก browser-cli/tools ตาม graph

Browser CLI (Organ):
  เปิดเว็บจริง · อ่าน DOM · screenshot · assert

Verify CLI (Judge):
  ตรวจ artifacts ตาม verifier-rules.yaml
  → PASS / RETRY / NEEDS_HUMAN / DEAD

Retro CLI:
  เขียน retro artifact · memory-cli index

Knowledge Brain:
  ฉลาดขึ้นจากงานจริงครั้งถัดไป
```

---

## 19. Communication Vocabulary

### One-liner (LOCKED)
> **Trinity is a CLI-native AI microkernel: ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, and artifacts are truth.**

### ภาษาไทย (LOCKED)
> **Trinity คือ CLI-native AI microkernel — ai-docs เป็น Knowledge Brain, vendor AI เป็น Reasoning Engine, CLI tools เป็นอวัยวะ, verifier เป็น Judge, artifacts เป็นความจริง**

### Cheat Sheet (LOCKED)
```text
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

## 20. Open Questions (เพื่อ brainstorm ต่อ)

1. Tool contract common envelope schema — final?
2. memory-cli ใช้ Node หรือ Python?
3. FTS5 schema fields?
4. Existing 240 retros parse ยังไง?
5. retro frontmatter required fields?
6. lll/vvv/nnn เรียก memory-cli จุดไหน?
7. Loop human gate ที่ step ไหน?
8. workflow graph แรก = standard หรือ deploy?
9. Trinity shim เริ่มจาก Claude Code skills หรือ shell wrapper?
10. Verifier rules — YAML format final?
11. Goal tree storage — JSON file หรือ SQLite?
12. Graph engine — Python lib (transitions/xstate-py) หรือ build เอง?

---

## Final

> **Trinity Big Evolution = ทำให้สิ่งที่คุณทำเองด้วยวินัย กลายเป็นระบบที่ช่วยคุณทำวินัยนั้นโดยอัตโนมัติ**

> **Architecture Direction: 9.5/10**
> **Implementation Readiness: 7.5/10** (จะเป็น 9/10 หลัง close 3 specs: Bootstrap, Contract+Test, Verifier Rules)

---

## See also

- [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) — Phase 0.5 (project portability) ⭐
- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) — Phase 1 (CLI tool ABI) ⭐
- [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) — Phase 4 (Judge with rules) ⭐ [TODO]
- [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) — Phase 5 (goal tree + loop state) [TODO]
- [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) — Phase 6 (graph + transition authority) [TODO]
- [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) — Phase 2 (memory-cli) [TODO]
- [`06_RETRO_CLI_SPEC.md`](06_RETRO_CLI_SPEC.md) — Phase 7 (retro-cli) [TODO]
- [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md) — Phase 8 (Trinity shim) [TODO]

---

## Changelog

- **v2.0.0 (2026-04-28)** — Major revision: 10 decisions committed, vocabulary locked, 5 critical fixes integrated (Brain redefined, Verifier rules introduced, Goal tree mandated, Graph authority enforced, Bootstrap Pack added). MCP stance hardened to "CLI-first only".
- **v1.0.0 (2026-04-28)** — Initial draft based on user's blueprint synthesis
