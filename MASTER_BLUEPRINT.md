# 🌌 Trinity Protocol: The AI-Native Operating System

**Vision:** Stop Chatting. Start Orchestrating.  
**Slogan:** "Control the Chaos. Orchestrate the Intelligence."  
**Status:** 🚀 Production Ready (v1.0)
**Adopted Date:** 2025-12-21

---

## 1. 🎯 The Executive Summary (บทสรุปผู้บริหาร)

**The Problem:**
การทำงานกับ AI ในปัจจุบันคือการ "Chat" ซึ่งนำไปสู่ปัญหา 3 ข้อ:
1.  **Amnesia:** คุยไป 100 ข้อความแล้วลืมบริบท (Context Lost)
2.  **Hallucination:** เขียนโค้ดมั่วโดยไม่มีระบบตรวจสอบ (No Safety Net)
3.  **No Audit Trail:** งานเสร็จแต่ไม่รู้ว่าใครทำ แก้ตรงไหน ย้อนกลับไม่ได้ (Black Box)

**The Solution:**
Trinity Protocol ไม่ใช่ Chatbot แต่คือ **Local-First Operating System** ที่เปลี่ยนการทำงานเป็นระบบ **"Capsules"** (กล่องงานที่แยกจากกัน) และบังคับใช้ความปลอดภัยด้วยระบบ **"Glass Box"** ที่โปร่งใสและตรวจสอบได้ 100%

---

## 2. 🔐 The Core Engine: "The 3 Locks"

จุดขายที่แข็งแกร่งที่สุดของ Trinity คือสถาปัตยกรรม Zero-Trust ผ่านระบบล็อค 3 ชั้น:

### 🔒 Lock 1: SSOT (Single Source of Truth)
*   **Concept:** "Policy-as-Code" กฎต้องเป็นโค้ด ไม่ใช่คำพูดลอยๆ
*   **Mechanism:** กฎทั้งหมดถูกเก็บใน `.ai/policies/` เท่านั้น (เช่น `safety.yaml`)
*   **Enforcement:** ระบบจะปฏิเสธการเริ่มงานทันที หากแผนงาน (Plan) ขัดแย้งกับ Policy

### 🚪 Lock 2: Smart Gates (Automated Enforcement)
*   **Concept:** "The Gauntlet" ประตูอัตโนมัติที่ไม่มีความประนีประนอม
*   **Mechanism:**
    *   **Syntax Gate:** `php -l`, `eslint` (ไม่ผ่าน = บล็อก)
    *   **Security Gate:** Scan หา Secret Keys หรือ PII
    *   **Risk Gate:** คำนวณ Risk Score (ถ้าสูงเกินเกณฑ์ ต้องรอคนอนุมัติ)

### ⛓️ Lock 3: Tamper-Evident Audit (The Truth)
*   **Concept:** "Blockchain-style Trust"
*   **Mechanism:** ทุก Action (Plan, Draft, Approve) จะถูก Hash และร้อยเรียงกันใน `audit/events.ndjson`
*   **Effect:** ป้องกันการแอบแก้ไข Log ย้อนหลัง (Compliance Ready: SOC2 / ISO27001)

---

## 3. 🏗️ The Architecture (Deep Hierarchy)

โครงสร้างโฟลเดอร์ที่รวมความละเอียดของ Codex และความปลอดภัยของ Claude ไว้ด้วยกัน:

```text
.ai/
├── 🛡️ policies/                # [Lock 1: The Constitution] (Human-Only Write)
│   ├── safety.yaml             # 🛡️ Risk Matrix (Scoring Rules)
│   ├── gates.yaml              # 🚧 Automated Guardrails definitions
│   ├── rbac.yaml               # 👮 Permissions & Roles
│   └── schemas/                # 📐 JSON Schemas for validation
│
├── 🧠 memory/                  # [Gemini Zone] The Global Brain
│   ├── INDEX.md                # 🧠 Master Knowledge Index (Auto-updated)
│   ├── TOPIC_MAP.md            # 🗺️ Knowledge Graph (Mermaid Visualization)
│   ├── DECISIONS.md            # ⚖️ Architecture Decision Records (ADR)
│   └── context/                # 🗃️ Raw Context Chunks
│
├── 📦 sessions/                # [The Workspaces: Capsules]
│   ├── active/
│   │   └── 2025-12-20_Fix_Auth/
│   │       ├── 00_CONTEXT.md   # 📥 Reality (Git Status + History)
│   │       ├── 01_PROMPT.md    # 🗣️ Human Intent
│   │       ├── 02_PLAN.md      # 📋 Strategy (Signed by Claude)
│   │       ├── 03_DIAGNOSIS.md # 🩺 Debugging Log
│   │       ├── 99_SUMMARY.md   # 📤 Output Metadata
│   │       ├── LIVE_MONITOR.md # 📺 Real-time TUI Status (Codex Feature)
│   │       ├── STOP_BUTTON     # 🛑 Emergency Halt Flag
│   │       └── .capsule_state/ # ⚙️ Local State (JSON)
│   │
│   └── archive/                # 🏛️ Completed History (Zipped)
│
└── 🔒 audit/                   # [Lock 3: The Ledger] (System-Only Write)
    ├── events.ndjson           # 📜 Immutable Hash Chain
    ├── signatures/             # ✍️ Cryptographic Proofs (.sha256)
    └── locks.json              # 🔒 Concurrency Control
```

---

## 4. ⚡ The Trinity Workflow (The Assembly Line)

การผสานงานของ 3 Agents (Gemini, Claude, Codex) ให้เป็นหนึ่งเดียว:

```text
USER (CEO) 👤
     │ "ai session new 'Fix Auth Bug'"
     ▼
┌─────────────────── ORCHESTRATOR (CLI) ────────────────────┐
│                                                           │
│  [PHASE 1: RESEARCH] 🧠 Gemini (Librarian)                │
│  • Reads .ai/memory/INDEX.md                              │
│  • Injects Context -> 00_CONTEXT.md                       │
│                                                           │
│          │ (Context Ready)                                │
│          ▼                                                │
│  [PHASE 2: PLANNING] 🏗️ Claude (Architect)                │
│  • Checks .ai/policies/safety.yaml (Lock 1)               │
│  • Drafts 02_PLAN.md & Signs it ✍️                        │
│                                                           │
│          │ (Plan Approved)                                │
│          ▼                                                │
│  [PHASE 3: EXECUTION] ⚡ Codex (Builder)                  │
│  • Writes Code -> draft.diff (Isolated)                   │
│  • Runs Local Tests (Sandboxed)                           │
│  • Signs Artifact ✍️                                      │
│                                                           │
│          │ (Draft Ready)                                  │
│          ▼                                                │
│  [PHASE 4: VERIFICATION] 🛡️ Smart Gates (Lock 2)          │
│  • [Lint] -> [Secret Scan] -> [Test] -> [Risk Score]      │
│  • Result: ✅ PASS or ❌ BLOCK                            │
│                                                           │
└───────────────────────────────────────────────────────────┘
            │
            ▼
    🚀 MERGE TO MAIN (Lock 3: Log & Sign)
            │
            ▼
   [PHASE 5: LEARNING] 🎓
   Gemini updates .ai/memory/INDEX.md
   (The System gets smarter with every merge)
```

---

## 5. 🆕 Session Model v0.5: Hybrid Architecture (Phase 6.1)

**Evolution:** Phase-Based (v0.4) + Agent Sandboxes (v0.5) = Best of Both Worlds

**Design Goals:**
- ✅ Parallel agent work (reduce bias via debate)
- ✅ Execution safety (phase-based gates)
- ✅ Crash recovery (session-local state)
- ✅ Single ingress to DO/dev (prevent race conditions)

---

### 5.1 The Hybrid Session Structure

```text
sessions/YYYY-MM-DD_task_name/
├── THINK/              [Phase-Based] Human Planning
│   ├── 00_CONTEXT.md
│   ├── 01_PROMPT.md
│   ├── 02_SCOPE.md
│   ├── 03_ACCEPTANCE.md
│   └── CONSENSUS.md    🆕 Published debate verdict (required for promote)
│
├── SANDBOX/            🆕 [Agent Sandboxes] Parallel Work + Debate
│   ├── gemini/         Gemini's workspace (research & analysis)
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── research.md
│   │   ├── proposal.md
│   │   └── critique.md
│   ├── claude/         Claude's workspace (planning & safety)
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── review.md
│   │   ├── proposal.md
│   │   └── critique.md
│   ├── codex/          Codex's workspace (implementation)
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── implementation.md
│   │   ├── proposal.md
│   │   └── patch.diff  ⭐ ONLY ingress to DO/dev
│   └── DEBATE/         Compiled debate artifacts
│       ├── round_1.md  (all proposals)
│       ├── round_2.md  (all critiques, if STANDARD/DEEP)
│       └── verdict.md  (human writes decision)
│
├── DO/                 [Phase-Based] Execution (unchanged from v0.4)
│   ├── snapshot/       Immutable backup
│   ├── dev/            Working copy (single ingress via patch.diff)
│   └── prod/           Release candidate (via ai promote)
│
├── CONTROL/            [Phase-Based] Status (unchanged from v0.4)
│   ├── META.json
│   ├── VERIFY.md
│   └── LIVE_MONITOR.md
│
└── .state/             🆕 Session-Local State (system-only)
    ├── session_state.json    # Phase tracking (INIT/EDITING/VERIFIED/DONE)
    ├── debate_state.json     # Debate progress
    ├── verify_dev.json       # Dev verification results
    ├── verify_prod.json      # Prod verification results
    └── events.ndjson         # Append-only event log
```

---

### 5.2 The "5 Non-Negotiable Rules" (v0.5)

**Rule 1: SANDBOX = Disposable**
- Agent sandboxes are for drafts only (not deployed)
- Can be deleted without breaking session
- NOT subject to verification gates

**Rule 2: DO/dev = Single Ingress** ⭐
- ONLY `ai sandbox apply <agent>` writes to `DO/dev/`
- Applies `SANDBOX/<agent>/patch.diff` (unified diff only, no binary, <10MB)
- Scope guard: cannot touch THINK/, CONTROL/, `.state/` or escape `DO/dev`
- Process: temp copy → apply → atomic swap
- Prevents race conditions from parallel agents; logs to `.state/events.ndjson`

**Rule 3: DO/prod = Promote-Only**
- ONLY `ai promote` writes to `DO/prod/`
- NO direct writes (human or agent)

**Rule 4: THINK/CONSENSUS.md = Required**
- `ai promote` requires consensus by default
- Contains published verdict from debate
- Can override with `--force` (logged)

**Rule 5: .state/ = System-Only**
- Atomic writes only
- Never 0 bytes (sentinel JSON)
- Agents cannot write (read-only)
 - Locks: `.state/LOCK`; use `ai unlock` only as last resort

---

### 5.3 Multi-Agent Workflow (v0.5)

**Pattern: Debate-Driven Development**

```text
1️⃣ CREATE SESSION
   ai session new "Build Feature X"

2️⃣ AGENTS WORK IN PARALLEL
   ├── Gemini → SANDBOX/gemini/proposal.md (research-based)
   ├── Claude → SANDBOX/claude/proposal.md (safety-first)
   └── Codex → SANDBOX/codex/proposal.md (implementation)

3️⃣ COMPILE DEBATE
   ai debate compile --mode standard
   → Creates SANDBOX/DEBATE/round_1.md (all proposals)
   → Creates SANDBOX/DEBATE/verdict.md (TEMPLATE)

4️⃣ HUMAN DECIDES
   vim SANDBOX/DEBATE/verdict.md
   → Read proposals → Make decision → Document rationale

5️⃣ PUBLISH CONSENSUS
   ai debate publish
   → Validates verdict → Copies to THINK/CONSENSUS.md

6️⃣ IMPLEMENT DECISION
   Codex creates SANDBOX/codex/patch.diff
   → Unified diff format
   → Based on verdict guidance

7️⃣ APPLY & VERIFY
   ai sandbox apply codex  # Single ingress to DO/dev
   ai verify dev           # Run safety gates

8️⃣ PROMOTE & DEPLOY
   ai promote              # Requires CONSENSUS.md ✅
   ai verify prod
   ai deploy prod

9️⃣ CLOSE SESSION
   ai close                # Requires verify_prod PASS
```

---

### 5.4 Comparison: v0.4 vs v0.5

| Feature | v0.4 (Phase-Based) | v0.5 (Hybrid) |
|---------|-------------------|---------------|
| **Multi-Agent Support** | ❌ No | ✅ Yes (SANDBOX/) |
| **Parallel Work** | ❌ Manual | ✅ Agent sandboxes |
| **Debate Workflow** | ❌ No | ✅ Yes (DEBATE/) |
| **Crash Recovery** | ⚠️ Limited | ✅ Session-local state |
| **Single Ingress** | ⚠️ Manual | ✅ Enforced (patch.diff) |
| **Safety Gates** | ✅ Yes | ✅ Yes (enhanced) |
| **Audit Trail** | ✅ Yes | ✅ Yes (enhanced) |

---

### 5.5 For Full Specification

**Read:** `.ai/SESSION_CONTRACT.md` - Canonical session specification

**Includes:**
- Complete folder structure
- Trust boundaries matrix
- State machine definition
- Patch.diff validation rules
- Debate mode specifications
- Design decisions (Q1-Q4)
- Usage examples

**This contract is LOCKED** - all WP implementations must comply.
