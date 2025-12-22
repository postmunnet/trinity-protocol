# Trinity Protocol - Architecture & Workflow Diagrams

**ASCII Art Visual Guide**

---

## 🏗️ Trinity Architecture - "The 3 Locks"

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TRINITY PROTOCOL                               │
│                   AI-Native Operating System                        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │    HUMAN (Operator)     │
                    │  "Control the Chaos"    │
                    └────────────┬────────────┘
                                 │
                                 │ Commands
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                         CLI ORCHESTRATOR                           │
│                    (Trinity Commands: ai XXX)                      │
└────────────┬───────────────────────────────────────┬───────────────┘
             │                                       │
             │                                       │
    ┌────────▼─────────┐                   ┌────────▼─────────┐
    │   🔒 LOCK 1      │                   │  Multi-AI Agents │
    │   SSOT           │                   │  Claude/Codex/   │
    │  Policy-as-Code  │                   │  Gemini          │
    │                  │                   └──────────────────┘
    │ .ai/policies/    │
    │  ├─ safety.yaml  │
    │  ├─ gates.yaml   │
    │  └─ rbac.yaml    │
    └──────────────────┘
             │
             ▼
    ┌─────────────────────────────────────────────────┐
    │        🚪 LOCK 2: Smart Gates                   │
    │        Automated Enforcement                    │
    ├─────────────────────────────────────────────────┤
    │  ┌──────────────┐  ┌──────────────┐            │
    │  │ Gate 1:      │  │ Gate 2:      │            │
    │  │ Forbidden    │  │ Secret       │            │
    │  │ Files        │  │ Scan         │            │
    │  │              │  │              │            │
    │  │ .env         │  │ api_key=     │            │
    │  │ config/dev/** │  │ password=   │            │
    │  └──────┬───────┘  └──────┬───────┘            │
    │         │                  │                    │
    │         └──────────┬───────┘                    │
    │                    │                            │
    │         ┌──────────▼───────────┐                │
    │         │  Gate 3: Smoke       │                │
    │         │  Hooks (Optional)    │                │
    │         │  lint/test/curl      │                │
    │         └──────────────────────┘                │
    │                    │                            │
    │                    ▼                            │
    │         ┌──────────────────────┐                │
    │         │  PASS    │   FAIL    │                │
    │         │  (0)     │   (1)     │                │
    │         └──────────────────────┘                │
    └─────────────────────────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │   ⛓️ LOCK 3: Audit Trail            │
    │   Tamper-Evident Logs                │
    │                                      │
    │   .ai/audit/events.ndjson            │
    │   ┌────────────────────────┐         │
    │   │ Event 1 → Hash A       │         │
    │   │ Event 2 → Hash B (A)   │         │
    │   │ Event 3 → Hash C (B)   │         │
    │   └────────────────────────┘         │
    │   (Blockchain-style chain)           │
    └──────────────────────────────────────┘
```

---

## 📂 Session Structure (Canonical)

```
sessions/2025-12-21_fix_login/
│
├─┬─ THINK/                      📝 Human Zone (Planning)
│ │                              [Human Editable]
│ ├── 00_CONTEXT.md              ← What/Why/Scope
│ ├── 01_PROMPT.md               ← Problem Statement
│ ├── 02_SCOPE.md                ← Files to Change
│ ├── 03_ACCEPTANCE.md           ← Success Criteria
│ ├── CLAUDE_GOVERNANCE_DECISION.md
│ └── NOTES.md
│
├─┬─ DO/                         💼 Filesystem Truth
│ │                              [Human Works Here]
│ │
│ ├─┬─ snapshot/                 📸 Immutable Backup
│ │ │                            [DO NOT EDIT]
│ │ └── (original files)
│ │
│ ├─┬─ dev/                      ✏️ Working Copy
│ │ │                            [EDIT HERE]
│ │ ├── src/
│ │ ├── tests/
│ │ └── config/
│ │
│ └─┬─ prod/                     🚀 Release Candidate
│   │                            [From promote only]
│   └── (promoted files)
│
├─┬─ CONTROL/                    📊 Control Panel
│ │                              [Human Reads, System Writes]
│ ├── META.json                  ← Workflow State
│ ├── VERIFY.md                  ← Verification Log
│ └── LIVE_MONITOR.md            ← Real-time Status
│
└─┬─ .ai/state/                  🔐 System State
  │                              [NEVER EDIT - System Only]
  ├── status.json                ← Current Phase
  ├── verify_report.json         ← Latest Verify Results
  └── events.ndjson              ← Event Log
```

---

## 🔄 Complete Workflow Diagram

```
                    ┌─────────────────┐
                    │  👤 HUMAN       │
                    │  Starts Task    │
                    └────────┬────────┘
                             │
                             │ ai session new "Task"
                             ▼
            ┌────────────────────────────────┐
            │  📦 SESSION CREATED            │
            │  THINK/ DO/ CONTROL/ .state/   │
            └────────────┬───────────────────┘
                         │
                         │ ai snapshot run
                         ▼
            ┌────────────────────────────────┐
            │  📸 SNAPSHOT                   │
            │  prod → snapshot → dev         │
            │                                │
            │  DO/snapshot/  [Immutable]     │
            │  DO/dev/       [Working Copy]  │
            └────────────┬───────────────────┘
                         │
                         │ Human edits DO/dev/
                         ▼
            ┌────────────────────────────────┐
            │  ✏️ DEVELOPMENT                │
            │  Edit files in DO/dev/         │
            │  (AI can help here)            │
            └────────────┬───────────────────┘
                         │
                         │ ai verify --scope dev
                         ▼
       ┌─────────────────────────────────────────┐
       │  🔍 VERIFICATION (Dev)                  │
       │                                         │
       │  ┌─────────┐  ┌─────────┐  ┌─────────┐│
       │  │ Gate 1  │→ │ Gate 2  │→ │ Gate 3  ││
       │  │Forbidden│  │ Secrets │  │ Smoke   ││
       │  └────┬────┘  └────┬────┘  └────┬────┘│
       │       └────────────┬─────────────┘     │
       │                    │                   │
       │       ┌────────────▼─────────────┐     │
       │       │  PASS      │   FAIL       │     │
       │       └────────────┬─────────────┘     │
       └────────────────────┼───────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼ PASS                      ▼ FAIL
    ┌──────────────────┐         ┌──────────────────┐
    │  ✅ Continue     │         │  ❌ Fix Issues   │
    │                  │         │  Then Re-verify  │
    └────────┬─────────┘         └────────┬─────────┘
             │                            │
             │                            │
             │ ai promote run             │ (loop back)
             ▼                            │
┌─────────────────────────────────────────┘
│  ⬆️ PROMOTION (Dev → Prod)
│
│  ┌──────────────────────────────┐
│  │  Pre-check:                  │
│  │  ✓ Dev verify PASS?          │
│  │  ✓ No forbidden files?       │
│  └──────────┬───────────────────┘
│             │
│             ▼
│  ┌──────────────────────────────┐
│  │  Atomic Copy:                │
│  │  DO/dev/ → prod_new/         │
│  │  (exclude .env, logs, etc)   │
│  └──────────┬───────────────────┘
│             │
│             ▼
│  ┌──────────────────────────────┐
│  │  Swap:                       │
│  │  prod/ → backup/             │
│  │  prod_new/ → prod/           │
│  └──────────┬───────────────────┘
│             │
└─────────────┤
              │
              ▼
    ┌─────────────────────────┐
    │  🚀 PROD READY          │
    │  DO/prod/ populated     │
    └──────────┬──────────────┘
               │
               │ ai verify --scope prod
               ▼
    ┌──────────────────────────────┐
    │  🔍 VERIFICATION (Prod)      │
    │  Same gates, stricter        │
    │                              │
    │  ┌───────┐  ┌───────┐       │
    │  │Gate 1 │→ │Gate 2 │→      │
    │  └───┬───┘  └───┬───┘       │
    │      └──────────┬────        │
    │                 │            │
    │       ┌─────────▼────────┐   │
    │       │  PASS  │  FAIL   │   │
    │       └─────────┬────────┘   │
    └─────────────────┼────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼ PASS                      ▼ FAIL
┌───────────────┐          ┌─────────────────┐
│ ✅ SAFE       │          │ ❌ BLOCKED      │
│                │          │ Must Fix        │
└───────┬───────┘          └─────────────────┘
        │
        │ ai close run
        ▼
┌────────────────────────────┐
│  🏁 CLOSE & ARCHIVE        │
│                            │
│  ✓ Check: Prod verify PASS │
│  ✓ Update META → closed    │
│  ✓ Move to archive/        │
│  ✓ Clear global state      │
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│  ✨ DONE                   │
│  Session archived          │
│  Ready for next task       │
└────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Trinity Data Flow                         │
└──────────────────────────────────────────────────────────────┘

Production Root                    Session Workspace
(Your Project)                     (Isolated)
┌──────────────┐
│ src/         │
│ tests/       │                   ┌─────────────────────────┐
│ config/      │                   │  DO/                    │
│ .env  ⚠️     │  snapshot run     │                         │
│ README.md    │  ─────────────►   │  ├─ snapshot/           │
└──────────────┘                   │  │   └─ (copy 1:1)     │
                                   │  │                      │
                                   │  ├─ dev/                │
                                   │  │   └─ (copy from     │
                                   │  │       snapshot)      │
                                   │  │                      │
                                   │  └─ prod/               │
                                   │      └─ (empty)         │
                                   └──────┬──────────────────┘
                                          │
                                          │ Human edits
                                          ▼
                                   ┌─────────────────────────┐
                                   │  DO/dev/                │
                                   │  ├─ src/ (modified)     │
                                   │  ├─ tests/ (added)      │
                                   │  └─ .env ⚠️ (oops!)    │
                                   └──────┬──────────────────┘
                                          │
                                          │ ai verify dev
                                          ▼
                              ┌───────────────────────┐
                              │  🛡️ VERIFY GATES     │
                              │                       │
                              │  ❌ Found .env        │
                              │  ❌ FAIL              │
                              └───────────────────────┘
                                          │
                                          │ Fix: remove .env
                                          │ ai verify dev
                                          ▼
                              ┌───────────────────────┐
                              │  🛡️ VERIFY GATES     │
                              │                       │
                              │  ✅ No forbidden      │
                              │  ✅ PASS              │
                              └──────┬────────────────┘
                                     │
                                     │ ai promote
                                     ▼
                         ┌──────────────────────────────┐
                         │  ⬆️ PROMOTE                  │
                         │                              │
                         │  DO/dev/ ──► prod_new/       │
                         │  (exclude .env ✓)            │
                         │  prod_new/ ──► DO/prod/      │
                         └──────┬───────────────────────┘
                                │
                                ▼
                         ┌─────────────────────────┐
                         │  DO/prod/               │
                         │  ├─ src/ (clean)        │
                         │  ├─ tests/              │
                         │  └─ NO .env ✅          │
                         └──────┬──────────────────┘
                                │
                                │ ai verify prod
                                ▼
                         ┌─────────────────────────┐
                         │  ✅ PASS               │
                         │  Safe to close          │
                         └──────┬──────────────────┘
                                │
                                │ ai close
                                ▼
                         ┌─────────────────────────┐
                         │  🏁 ARCHIVED            │
                         │  archive/               │
                         │  2025-12-21_xxx/        │
                         └─────────────────────────┘
```

---

## 🎯 Workflow Timeline (Happy Path)

```
Time: 0 min                                              Time: 30 min
│                                                              │
├─ START ─────────────────────────────────────────────────────┤
│
│  [Session New]
│  ┌──────────────────────────────────────────┐
│  │ ai session new "Fix Login Bug"           │
│  │                                          │
│  │ Creates:                                 │
│  │ ✓ THINK/ (6 files)                       │
│  │ ✓ DO/ (3 folders)                        │
│  │ ✓ CONTROL/ (3 files)                     │
│  │ ✓ .ai/state/ (3 files)                   │
│  └──────────────────────────────────────────┘
│  ⏱️ 10 seconds
│
├──────────────────────────────────────────────────────────────
│
│  [Snapshot]
│  ┌──────────────────────────────────────────┐
│  │ ai snapshot run                          │
│  │                                          │
│  │ Copies:                                  │
│  │ project_root → DO/snapshot/              │
│  │ DO/snapshot/ → DO/dev/                   │
│  └──────────────────────────────────────────┘
│  ⏱️ 5-30 seconds (depending on project size)
│
├──────────────────────────────────────────────────────────────
│
│  [Development]
│  ┌──────────────────────────────────────────┐
│  │ Human edits DO/dev/                      │
│  │ AI helps (optional)                      │
│  │                                          │
│  │ Files modified:                          │
│  │ ✓ src/auth.py                            │
│  │ ✓ tests/test_auth.py                     │
│  └──────────────────────────────────────────┘
│  ⏱️ 5-30 minutes (depends on task)
│
├──────────────────────────────────────────────────────────────
│
│  [Verify Dev]
│  ┌──────────────────────────────────────────┐
│  │ ai verify run --scope dev                │
│  │                                          │
│  │ Gates:                                   │
│  │ ✅ Gate 1: No .env                       │
│  │ ✅ Gate 2: No secrets                    │
│  │ ⚠️  Gate 3: Skipped                      │
│  │                                          │
│  │ Result: ✅ PASS                          │
│  └──────────────────────────────────────────┘
│  ⏱️ 5 seconds
│
├──────────────────────────────────────────────────────────────
│
│  [Promote]
│  ┌──────────────────────────────────────────┐
│  │ ai promote run                           │
│  │                                          │
│  │ Actions:                                 │
│  │ ✓ Copy dev → prod_new (atomic)           │
│  │ ✓ Exclude .env, logs, cache              │
│  │ ✓ Backup old prod                        │
│  │ ✓ Rename prod_new → prod                 │
│  └──────────────────────────────────────────┘
│  ⏱️ 5-10 seconds
│
├──────────────────────────────────────────────────────────────
│
│  [Verify Prod]
│  ┌──────────────────────────────────────────┐
│  │ ai verify run --scope prod               │
│  │                                          │
│  │ Gates:                                   │
│  │ ✅ Gate 1: No .env in prod               │
│  │ ✅ Gate 2: No secrets in prod            │
│  │ ⚠️  Gate 3: Skipped                      │
│  │                                          │
│  │ Result: ✅ PASS (Safe!)                  │
│  └──────────────────────────────────────────┘
│  ⏱️ 5 seconds
│
├──────────────────────────────────────────────────────────────
│
│  [Close]
│  ┌──────────────────────────────────────────┐
│  │ ai close run                             │
│  │                                          │
│  │ Checks:                                  │
│  │ ✓ Prod verify PASS? → Yes                │
│  │                                          │
│  │ Actions:                                 │
│  │ ✓ Update META.json → closed              │
│  │ ✓ Archive session                        │
│  │ ✓ Clear global state                     │
│  └──────────────────────────────────────────┘
│  ⏱️ 5 seconds
│
└─ DONE ──────────────────────────────────────────────────────
   Session archived
   Ready for next task
```

---

## 🔐 Security Flow (How Gates Work)

```
                    ┌─────────────────┐
                    │  ai verify dev  │
                    └────────┬────────┘
                             │
                ┌────────────▼────────────┐
                │  Load Safety Rules      │
                │  (.ai/policies/)        │
                └────────────┬────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │         Scan DO/dev/ Files             │
        └────┬───────────┬───────────┬───────────┘
             │           │           │
    ┌────────▼──────┐ ┌──▼────────┐ ┌▼──────────┐
    │ Gate 1:       │ │ Gate 2:   │ │ Gate 3:   │
    │ Forbidden     │ │ Secrets   │ │ Smoke     │
    │ Files         │ │ Scan      │ │ Hooks     │
    └────────┬──────┘ └──┬────────┘ └┬──────────┘
             │           │           │
             ▼           ▼           ▼
    ┌────────────────────────────────────────┐
    │  Check: .env exists?                   │
    │  ├─ Yes → ❌ FAIL                      │
    │  └─ No  → ✅ Next gate                 │
    └────────┬───────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────────┐
    │  Scan: api_key=, secret=, password=    │
    │  ├─ Found → ❌ FAIL (show location)    │
    │  └─ Clean → ✅ Next gate               │
    └────────┬───────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────────┐
    │  Run: lint/test (if configured)        │
    │  ├─ Fail → ⚠️ Warn (permissive)       │
    │  └─ Pass → ✅ Next                     │
    └────────┬───────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────────┐
    │         Generate Report                │
    │  {                                     │
    │    "status": "PASS",                   │
    │    "passed": true,                     │
    │    "checks": {...},                    │
    │    "blocks": [],                       │
    │    "warnings": []                      │
    │  }                                     │
    └────────┬───────────────────────────────┘
             │
             ├─► .ai/state/verify_report.json
             ├─► CONTROL/VERIFY.md (append log)
             └─► Exit Code: 0 (PASS)
```

---

## 📊 State Machine Diagram

```
┌─────────────────────────────────────────────────────────────┐
│               Trinity Session State Machine                  │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────┐
                    │   INIT   │ (session new)
                    └─────┬────┘
                          │
                          ▼
                    ┌──────────┐
                    │ SNAPSHOT │ (ai snapshot)
                    └─────┬────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │        DEV_EDITING              │ (human edits)
        └─────┬───────────────────────────┘
              │
              │ ai verify dev
              ▼
        ┌─────────────────┐
        │  DEV_VERIFIED   │
        └─────┬───────────┘
              │
              │ ai promote
              ▼
        ┌─────────────────┐
        │   PROMOTED      │
        └─────┬───────────┘
              │
              │ ai verify prod
              ▼
        ┌─────────────────┐
        │  PROD_VERIFIED  │
        └─────┬───────────┘
              │
              │ ai close
              ▼
        ┌─────────────────┐
        │   ARCHIVED      │ (terminal state)
        └─────────────────┘


Transitions:
─────────►  Forward (normal flow)
◄─────────  Backward (fix and retry)

Error Handling:
  FAIL at verify dev → Back to DEV_EDITING
  FAIL at verify prod → Back to PROMOTED (fix in dev)
  FAIL at close → Must verify prod again
```

---

## 🔀 Multi-Session View

```
┌──────────────────────────────────────────────────────────────┐
│                  Trinity Multi-Session                        │
└──────────────────────────────────────────────────────────────┘

Global State                    Active Sessions
(.ai/state/)                    (.ai/sessions/)

┌─────────────────┐
│ status.json     │            ┌───────────────────────────┐
│                 │            │ 2025-12-21_fix_login/     │
│ current_session │───────────►│  Status: DEV_VERIFIED     │
│ = fix_login     │            │  Phase: promote           │
│                 │            └───────────────────────────┘
│ active_capsules │
│ = 1             │            ┌───────────────────────────┐
└─────────────────┘            │ 2025-12-20_add_profile/   │
                               │  Status: ARCHIVED         │
        │                      │  (moved to archive/)      │
        │                      └───────────────────────────┘
        │
        │ Commands affect
        │ active session only
        ▼
┌─────────────────────────────────────┐
│  Current Active Session             │
│  = 2025-12-21_fix_login/            │
│                                     │
│  Commands operate here:             │
│  ├─ ai snapshot                     │
│  ├─ ai verify                       │
│  ├─ ai promote                      │
│  └─ ai close                        │
└─────────────────────────────────────┘
```

---

## 🎭 Trinity vs Traditional Workflow

```
┌────────────────────────────────────────────────────────────┐
│            Traditional (Manual) Workflow                    │
└────────────────────────────────────────────────────────────┘

1. Edit files directly           ⚠️ Risk: mess up prod
2. Manual copy to server         ⚠️ Risk: partial copy, wrong files
3. Hope nothing breaks           ⚠️ Risk: .env copied, secrets exposed
4. No verification               ⚠️ Risk: bugs in production
5. No audit trail                ⚠️ Risk: can't rollback easily

Time: ~30-60 min
Risk: HIGH 🔴
Confidence: LOW


┌────────────────────────────────────────────────────────────┐
│              Trinity (Automated) Workflow                   │
└────────────────────────────────────────────────────────────┘

1. ai session new               ✅ Isolated workspace
2. ai snapshot                  ✅ Safe backup
3. Edit DO/dev/                 ✅ Protected environment
4. ai verify dev                ✅ Catch issues early
5. ai promote                   ✅ Atomic copy + exclude rules
6. ai verify prod               ✅ Final safety check
7. ai close                     ✅ Archive with full history

Time: ~5-15 min
Risk: LOW 🟢
Confidence: HIGH
```

---

## 🛡️ Verification Gates Detail

```
┌────────────────────────────────────────────────────────────┐
│                  Verification Pipeline                      │
└────────────────────────────────────────────────────────────┘

Input: DO/dev/ or DO/prod/
│
├─► GATE 1: Forbidden Files Check
│   ┌─────────────────────────────────────┐
│   │ Scan for:                           │
│   │ ✓ .env                              │
│   │ ✓ .env.*                            │
│   │ ✓ config/dev/**                     │
│   │ ✓ **/config.dev.*                   │
│   │                                     │
│   │ Method: glob pattern matching       │
│   │ Action: BLOCK if found              │
│   └──────────┬──────────────────────────┘
│              │
│              ├─ Found → blocks: [".env"] → ❌ FAIL
│              └─ Clean → Next Gate
│
├─► GATE 2: Secret Scan
│   ┌─────────────────────────────────────┐
│   │ Regex patterns:                     │
│   │ ✓ api[_-]?key\s*[:=]                │
│   │ ✓ secret\s*[:=]                     │
│   │ ✓ password\s*[:=]                   │
│   │ ✓ sk-[a-zA-Z0-9]{32,}               │
│   │                                     │
│   │ Method: Full text scan              │
│   │ Action: BLOCK if found              │
│   └──────────┬──────────────────────────┘
│              │
│              ├─ Found → blocks: [{file, line, type}] → ❌ FAIL
│              └─ Clean → Next Gate
│
└─► GATE 3: Smoke Hooks (Optional)
    ┌─────────────────────────────────────┐
    │ Run commands (if configured):       │
    │ ✓ pytest tests/                     │
    │ ✓ eslint .                          │
    │ ✓ curl http://health                │
    │                                     │
    │ Method: Execute commands            │
    │ Action: WARN (permissive) / BLOCK   │
    └──────────┬──────────────────────────┘
               │
               ├─ Fail → warnings: [...] → ⚠️ WARN (permissive)
               └─ Pass → ✅ PASS

Output:
├─► verify_report.json (machine)
├─► VERIFY.md (human log)
└─► Exit Code: 0 (pass) / 1 (fail) / 2 (error)
```

---

## 📦 Promote Operation (Atomic)

```
┌────────────────────────────────────────────────────────────┐
│              Atomic Promotion Process                       │
└────────────────────────────────────────────────────────────┘

State: BEFORE
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ DO/dev/     │  │ DO/prod/    │  │ prod_new/   │
│ ├─ file1.py │  │ ├─ old1.py  │  │ (empty)     │
│ ├─ file2.js │  │ └─ old2.js  │  │             │
│ └─ .env ⚠️  │  │             │  │             │
└─────────────┘  └─────────────┘  └─────────────┘

Step 1: Copy dev → prod_new (exclude .env)
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ DO/dev/     │  │ DO/prod/    │  │ prod_new/   │
│ ├─ file1.py │  │ ├─ old1.py  │  │ ├─ file1.py │
│ ├─ file2.js │──┼─►(unchanged)│  │ ├─ file2.js │
│ └─ .env ⚠️  │  │             │  │ (no .env ✓) │
└─────────────┘  └─────────────┘  └─────────────┘

Step 2: Backup old prod
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ DO/dev/     │  │ backup_XXX/ │  │ prod_new/   │
│ (unchanged) │  │ ├─ old1.py  │◄─┤ ├─ file1.py │
│             │  │ └─ old2.js  │  │ └─ file2.js │
└─────────────┘  └─────────────┘  └─────────────┘

Step 3: Atomic rename (prod_new → prod)
┌─────────────┐  ┌─────────────┐
│ DO/dev/     │  │ DO/prod/    │
│ (unchanged) │  │ ├─ file1.py │ ✅ NEW
│             │  │ └─ file2.js │ ✅ NEW
│             │  │ (no .env!)  │ ✅ SAFE
└─────────────┘  └─────────────┘

Result: Prod updated atomically, no .env leak!
```

---

## 🎯 Decision Tree (What Command to Run)

```
                    ┌─────────────────┐
                    │  Start Here     │
                    │  ai status show │
                    └────────┬────────┘
                             │
                  ┌──────────▼──────────┐
                  │ Have active session?│
                  └──┬──────────────┬───┘
                     │              │
                  NO │              │ YES
                     │              │
         ┌───────────▼──────┐       │
         │ ai session new   │       │
         │ "Task Name"      │       │
         └───────────┬──────┘       │
                     │              │
                     └──────┬───────┘
                            │
                 ┌──────────▼───────────┐
                 │ DO/snapshot empty?   │
                 └──┬──────────────┬────┘
                    │              │
                 YES│              │NO (has files)
                    │              │
         ┌──────────▼──────┐       │
         │ ai snapshot run │       │
         └──────────┬──────┘       │
                    │              │
                    └──────┬───────┘
                           │
                ┌──────────▼──────────┐
                │ Edit DO/dev/ files  │
                │ (make your changes) │
                └──────────┬──────────┘
                           │
                           │
                ┌──────────▼──────────┐
                │ ai verify --scope   │
                │ dev                 │
                └──┬──────────────┬───┘
                   │              │
                PASS│            │FAIL
                   │              │
                   │    ┌─────────▼─────────┐
                   │    │ Fix issues        │
                   │    │ Then verify again │
                   │    └─────────┬─────────┘
                   │              │
                   │◄─────────────┘
                   │
        ┌──────────▼──────────┐
        │ DO/prod empty?      │
        └──┬──────────────┬───┘
           │              │
        YES│              │NO (already promoted)
           │              │
    ┌──────▼──────┐       │
    │ ai promote  │       │
    └──────┬──────┘       │
           │              │
           └──────┬───────┘
                  │
       ┌──────────▼──────────┐
       │ ai verify --scope   │
       │ prod                │
       └──┬──────────────┬───┘
          │              │
       PASS│            │FAIL
          │              │
          │    ┌─────────▼─────────┐
          │    │ Fix in dev        │
          │    │ Promote again     │
          │    └───────────────────┘
          │
   ┌──────▼──────┐
   │  ai close   │
   └──────┬──────┘
          │
          ▼
   ┌──────────────┐
   │   ARCHIVED   │
   └──────────────┘
```

---

## 🔄 Before vs After Trinity

```
╔═══════════════════════════════════════════════════════════╗
║              BEFORE TRINITY (Manual)                      ║
╚═══════════════════════════════════════════════════════════╝

Developer's Mind                     File System
┌──────────────┐                    ┌──────────────┐
│ "Need to fix"│                    │ project/     │
│ "What files?"│                    │ ├─ mixed dev │
│ "Did I test?"│                    │ └─ mixed prod│
│ "Is it safe?"│                    │   (confusing)│
└──────┬───────┘                    └──────────────┘
       │
       │ Manual steps:
       │ 1. Edit files (risky)
       │ 2. Copy to server (manual)
       │ 3. Hope it works (scary)
       ▼
┌──────────────────────────┐
│  😰 Stress Level: HIGH   │
│  ⏱️ Time: 30-60 min     │
│  🔴 Risk: HIGH          │
│  ❌ Audit Trail: None   │
└──────────────────────────┘


╔═══════════════════════════════════════════════════════════╗
║               AFTER TRINITY (Automated)                   ║
╚═══════════════════════════════════════════════════════════╝

Developer's Mind                     Trinity Structure
┌──────────────┐                    ┌──────────────────────┐
│ ai status    │────────────────────►│ 📊 Status:          │
│              │                    │ ⚡ Next: ai verify  │
│ "Do what it  │                    │                      │
│  says!"      │                    │ Phase: verify_dev    │
└──────────────┘                    └──────────────────────┘
                                               │
                                               │
       ┌───────────────────────────────────────┘
       │
       │ Automated flow:
       │ 1. Trinity verifies (gates)
       │ 2. Trinity promotes (atomic)
       │ 3. Trinity logs (audit)
       ▼
┌──────────────────────────┐
│  😊 Stress Level: LOW    │
│  ⏱️ Time: 5-15 min      │
│  🟢 Risk: LOW           │
│  ✅ Audit Trail: Full   │
└──────────────────────────┘
```

---

## 🌐 System Context Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TRINITY ECOSYSTEM                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Human Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │Developer │  │ Manager  │  │  QA      │                 │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘                 │
└────────┼─────────────┼─────────────┼────────────────────────┘
         │             │             │
         │ Commands    │ Status      │ Reports
         │             │             │
┌────────▼─────────────▼─────────────▼────────────────────────┐
│                   Trinity CLI                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ session │ │snapshot │ │ verify  │ │ promote │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
└───────┼───────────┼───────────┼───────────┼────────────────┘
        │           │           │           │
        │           │           │           │
┌───────▼───────────▼───────────▼───────────▼────────────────┐
│                  Core Systems                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Template  │ │  State   │ │ Verify   │ │File Ops  │      │
│  │Loader    │ │ Manager  │ │ Gates    │ │(Atomic)  │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼─────────────┐
│                   File System Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ sessions/   │  │ templates/  │  │  .ai/state/ │        │
│  │ archive/    │  │ policies/   │  │  audit/     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎬 Animation: Session Lifecycle

```
Frame 1: INIT
═══════════════════════════════════════
┌─────────────────────┐
│  ai session new     │
│  "Fix Login"        │
└──────────┬──────────┘
           │
           ▼
    [Session Created]
    THINK/  DO/  CONTROL/  .state/
    Status: 📝 Planning


Frame 2: SNAPSHOT
═══════════════════════════════════════
    ai snapshot run
           │
           ▼
    DO/snapshot/ ◄── (Project Root)
           │
           ▼
    DO/dev/ ◄── (Copy from snapshot)

    Status: 📸 Snapshot Complete


Frame 3: DEVELOPMENT
═══════════════════════════════════════
    Human: Edit DO/dev/
           │
           ▼
    DO/dev/
    ├─ auth.py (modified)
    ├─ test.py (added)
    └─ .env ⚠️ (oops!)

    Status: ✏️ Editing


Frame 4: VERIFY DEV
═══════════════════════════════════════
    ai verify dev
           │
           ▼
    🛡️ Gates:
    ├─ Forbidden: ❌ Found .env
    └─ Result: FAIL

    Status: 🔴 Issues Found


Frame 5: FIX & RETRY
═══════════════════════════════════════
    Human: Remove .env
    ai verify dev
           │
           ▼
    🛡️ Gates:
    ├─ Forbidden: ✅
    ├─ Secrets: ✅
    └─ Result: PASS

    Status: ✅ Dev Verified


Frame 6: PROMOTE
═══════════════════════════════════════
    ai promote run
           │
           ▼
    DO/dev/ ──► prod_new/
    (exclude .env)
           │
           ▼
    prod/ → backup/
    prod_new/ → prod/

    Status: ⬆️ Promoted


Frame 7: VERIFY PROD
═══════════════════════════════════════
    ai verify prod
           │
           ▼
    🛡️ Gates on DO/prod/:
    ├─ No .env ✅
    ├─ No secrets ✅
    └─ Result: PASS

    Status: 🚀 Prod Safe


Frame 8: CLOSE
═══════════════════════════════════════
    ai close run
           │
           ▼
    ├─ Update META → closed
    ├─ Move to archive/
    └─ Clear global state

    Status: 🏁 Archived


Frame 9: DONE
═══════════════════════════════════════
    archive/2025-12-21_fix_login.archive/
    └─ (Complete history preserved)

    Global: Ready for next task ✨
```

---

## 🔗 Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│              Trinity Component Interaction                  │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   Commands   │
                    │   (User)     │
                    └───────┬──────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ TemplateLoader│    │ StateManager │    │ VerifyGates  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │ Loads             │ Reads/Writes      │ Scans
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ templates/   │    │ .ai/state/   │    │ DO/dev/      │
│ session/     │    │ status.json  │    │ DO/prod/     │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │   Session    │
                   │   Workspace  │
                   └──────────────┘
```

---

---

## 🆕 v0.5 Architecture - Agent Sandbox System (Phase 6.1)

### Session Structure v0.5 (Hybrid Model)

```
sessions/YYYY-MM-DD_task_name/
│
├─┬─ THINK/                      📝 Human Planning
│ ├── 00_CONTEXT.md
│ ├── 01_PROMPT.md
│ ├── 02_SCOPE.md
│ ├── 03_ACCEPTANCE.md
│ └── CONSENSUS.md               🆕 Published debate verdict
│
├─┬─ SANDBOX/                    🆕 Agent Working Areas (Disposable)
│ │
│ ├─┬─ gemini/                   🧠 Research & Analysis
│ │ ├── WORKSPACE_PROMPT.md
│ │ ├── research.md
│ │ ├── analysis.md
│ │ └── proposal.md              → For debate
│ │
│ ├─┬─ claude/                   🏗️ Planning & Safety
│ │ ├── WORKSPACE_PROMPT.md
│ │ ├── review.md
│ │ ├── proposal.md              → For debate
│ │ └── critique.md
│ │
│ ├─┬─ codex/                    ⚡ Implementation
│ │ ├── WORKSPACE_PROMPT.md
│ │ ├── implementation.md
│ │ ├── proposal.md              → For debate
│ │ └── patch.diff               ⭐ Single ingress to DO/dev
│ │
│ └─┬─ DEBATE/                   💬 Compiled Debate
│   ├── round_1.md               (all proposals)
│   ├── round_2.md               (critiques, if STANDARD/DEEP)
│   └── verdict.md               (human writes decision)
│
├─┬─ DO/                         💼 Execution Workspace
│ ├── snapshot/                  (immutable)
│ ├── dev/                       (single ingress via patch.diff)
│ └── prod/                      (via ai promote only)
│
├─┬─ CONTROL/                    📊 Status & Metadata
│ ├── META.json
│ ├── VERIFY.md
│ └── LIVE_MONITOR.md
│
└─┬─ .state/                     🔐 Session-Local State
  ├── session_state.json         🆕 (INIT/EDITING/VERIFIED/DONE)
  ├── debate_state.json          🆕 (debate progress)
  ├── verify_dev.json            🆕 (dev verification)
  ├── verify_prod.json           🆕 (prod verification)
  └── events.ndjson              (audit log)
```

---

### v0.5 Multi-Agent Workflow (Debate-Driven)

```
┌─────────────────────────────────────────────────────────────────┐
│                    HUMAN CREATES SESSION                        │
│                  ai session new "Task"                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ 🧠 GEMINI      │ │ 🏗️ CLAUDE      │ │ ⚡ CODEX       │
│ Research Lead  │ │ Safety Lead    │ │ Impl Lead      │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘
        │                  │                  │
        │ Works in         │ Works in         │ Works in
        ▼                  ▼                  ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│SANDBOX/gemini/ │ │SANDBOX/claude/ │ │SANDBOX/codex/  │
│ proposal.md    │ │ proposal.md    │ │ proposal.md    │
│ research.md    │ │ review.md      │ │ patch.diff     │
└───────┬────────┘ └───────┬────────┘ └───────┬────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │ Parallel work (no conflicts)
                           ▼
                  ┌─────────────────┐
                  │  ai debate      │
                  │  compile        │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────────────┐
                  │ SANDBOX/DEBATE/         │
                  │ ├── round_1.md          │
                  │ └── verdict.md          │
                  │     (TEMPLATE)          │
                  └────────┬────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ HUMAN DECIDES   │
                  │ (Reads all      │
                  │  proposals)     │
                  │                 │
                  │ Writes:         │
                  │ - Decision      │
                  │ - Rationale     │
                  │ - Impl Notes    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ ai debate       │
                  │ publish         │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ THINK/          │
                  │ CONSENSUS.md    │
                  │ (Published)     │
                  └────────┬────────┘
                           │
                           │ Codex implements
                           ▼
                  ┌─────────────────┐
                  │ SANDBOX/codex/  │
                  │ patch.diff      │
                  │ (unified diff)  │
                  └────────┬────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │    ai sandbox apply codex       │
         │    (Single Ingress to DO/dev)   │
         └────────┬────────────────────────┘
                  │
                  │ ⭐ ONLY entry point
                  │ ⭐ Scope validated
                  │ ⭐ Atomic operation
                  ▼
         ┌─────────────────┐
         │   DO/dev/       │
         │   (modified)    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  ai verify dev  │
         │  (Gates check)  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  ai promote     │
         │  (Requires:     │
         │   verify PASS + │
         │   CONSENSUS.md) │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   DO/prod/      │
         │   (promoted)    │
         └─────────────────┘
```

**Key Innovations v0.5:**
- 🤖 Parallel agent research (SANDBOX/)
- 💬 Structured debate (reduce bias)
- 👤 Human authority (verdict)
- ⭐ Single ingress (prevent conflicts)
- 🔒 Consensus requirement (planning discipline)

---

### v0.5 Single Ingress Flow (Rule 2)

```
┌─────────────────────────────────────────────────────┐
│           Multiple Agents Working                   │
│                                                     │
│  SANDBOX/gemini/   SANDBOX/claude/   SANDBOX/codex/│
│     (research)        (planning)      (code)       │
│         │                 │              │         │
│         └─────────────────┼──────────────┘         │
│                           │                        │
│                  All create proposals              │
│                           │                        │
└───────────────────────────┼────────────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ Human Decides  │
                   │ (Debate)       │
                   └────────┬───────┘
                            │
                            │ Chooses approach
                            ▼
                   ┌────────────────┐
                   │ Codex Creates  │
                   │ patch.diff     │
                   └────────┬───────┘
                            │
                            │ Unified diff only
                            │ No binary, <10MB
                            │ Scope validated
                            ▼
              ┌──────────────────────────┐
              │  ai sandbox apply codex  │
              │                          │
              │  ⭐ SINGLE INGRESS ⭐    │
              │  (Only way to DO/dev)    │
              └────────┬─────────────────┘
                       │
                       │ Validates:
                       │ ✓ Scope (only DO/dev)
                       │ ✓ Format (unified)
                       │ ✓ Size (<10MB)
                       │ ✓ No symlinks
                       │
                       ▼
              ┌─────────────────┐
              │   DO/dev/       │
              │   (updated)     │
              └─────────────────┘

Why Single Ingress Matters:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Prevents race conditions (agents don't conflict)
2. Audit trail clear (know what was applied)
3. Atomic operation (rollback on failure)
4. Scope validation (can't touch THINK/, CONTROL/)
5. Predictable state (no surprises)
```

---

### v0.5 State Machine (Session-Local)

```
┌──────────┐
│   INIT   │  Session created, no work yet
└────┬─────┘
     │
     │ ai sandbox apply OR manual edit
     ▼
┌──────────┐
│ EDITING  │  Code changes in DO/dev/
└────┬─────┘
     │
     │ ai verify dev PASS
     ▼
┌──────────┐
│ VERIFIED │  Dev verified, ready for prod
└────┬─────┘
     │
     │ ai close (requires verify_prod PASS)
     ▼
┌──────────┐
│   DONE   │  Session closed
└──────────┘

State Transitions:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• System-only (agents cannot modify .state/)
• Enforced by commands (not suggestions)
• Atomic writes (never 0-byte files)
• Crash-resumable (state persisted)
```

---

### v0.5 Trust Boundaries (Who Writes What)

```
┌────────────────────────────────────────────────────────────┐
│                    TRUST BOUNDARIES                        │
│                (v0.5 Agent Sandbox Model)                  │
└────────────────────────────────────────────────────────────┘

Zone                Human      Gemini     Claude     Codex      System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THINK/              ✅ Write   👁️ Read   👁️ Read   👁️ Read   👁️ Read
SANDBOX/gemini/     👁️ Read   ✅ Write   👁️ Read   👁️ Read   👁️ Read
SANDBOX/claude/     👁️ Read   👁️ Read   ✅ Write   👁️ Read   👁️ Read
SANDBOX/codex/      👁️ Read   👁️ Read   👁️ Read   ✅ Write   👁️ Read
SANDBOX/DEBATE/     👁️ Read   ❌ None   ❌ None   ❌ None   ✅ Write*
DO/snapshot/        ❌ None   ❌ None   ❌ None   ❌ None   ✅ Write
DO/dev/             ✅ Write   ❌ None   ❌ None   ❌ None   ✅ Write**
DO/prod/            ❌ None   ❌ None   ❌ None   ❌ None   ✅ Write***
CONTROL/            👁️ Read   👁️ Read   👁️ Read   👁️ Read   ✅ Write
.state/             👁️ Read   ❌ None   ❌ None   ❌ None   ✅ Write

* via: ai debate compile
** via: ai sandbox apply (single ingress)
*** via: ai promote (only)

Key Principles:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Each agent has exclusive write to their SANDBOX/
✅ Agents can read other sandboxes (collaboration)
✅ DO/dev has ONE entry point (ai sandbox apply)
✅ Human has final authority (verdict, promote)
✅ System enforces rules (not just guidelines)
```

---

### v0.5 Debate Workflow Detail

```
Step 1: Research Phase (Parallel)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Gemini                Claude               Codex
     │                     │                   │
     │ Researches          │ Analyzes          │ Prototypes
     │ best practices      │ safety risks      │ implementation
     │                     │                   │
     ▼                     ▼                   ▼
SANDBOX/gemini/      SANDBOX/claude/     SANDBOX/codex/
  proposal.md          proposal.md         proposal.md
  research.md          review.md           implementation.md


Step 2: Compilation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

         ai debate compile --mode fast
                     │
                     ▼
            ┌─────────────────┐
            │ SANDBOX/DEBATE/ │
            │ round_1.md      │ ← All proposals compiled
            │ verdict.md      │ ← TEMPLATE for human
            └─────────────────┘


Step 3: Human Decision (Single Authority)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                 ┌─────────────┐
                 │   HUMAN     │
                 │  (Reads)    │
                 └──────┬──────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    Proposal 1     Proposal 2     Proposal 3
    (Gemini)       (Claude)       (Codex)
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   HUMAN     │
                 │  (Decides)  │
                 └──────┬──────┘
                        │
                        │ Fills verdict:
                        │ • Decision: What to do
                        │ • Rationale: Why
                        │ • Impl Notes: How
                        ▼
            ┌─────────────────┐
            │ verdict.md      │
            │ (Filled)        │
            └─────────────────┘


Step 4: Publication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

         ai debate publish
                │
                │ Validates (no [HUMAN: ] placeholders)
                ▼
         ┌──────────────┐
         │THINK/        │
         │CONSENSUS.md  │ ⭐ Single source of decision
         └──────────────┘
                │
                │ Required for: ai promote
                └─→ Planning discipline enforced
```

---

### v0.5 Comparison: v0.4 vs v0.5

```
┌────────────────────────────────────────────────────────────┐
│               Feature Comparison                           │
├────────────────┬──────────────────┬────────────────────────┤
│ Feature        │ v0.4             │ v0.5 (Current)         │
├────────────────┼──────────────────┼────────────────────────┤
│ Multi-Agent    │ ❌ No            │ ✅ Yes (SANDBOX/)      │
│ Parallel Work  │ ❌ Manual        │ ✅ Agent isolation     │
│ Debate         │ ❌ No            │ ✅ Structured workflow │
│ Consensus      │ ⚠️ Optional      │ ✅ Required (default)  │
│ State Tracking │ ⚠️ Global only   │ ✅ Session-local       │
│ Crash Recovery │ ⚠️ Limited       │ ✅ Full resume         │
│ Single Ingress │ ⚠️ Manual        │ ✅ Enforced (Rule 2)   │
│ Verify Reports │ ⚠️ Single file   │ ✅ Separate dev/prod   │
│ Safety Gates   │ ✅ Yes           │ ✅ Enhanced            │
│ Audit Trail    │ ✅ Yes           │ ✅ Enhanced            │
└────────────────┴──────────────────┴────────────────────────┘

Evolution Path:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v0.4: Phase-based workflow (safety focus)
  ↓
v0.5: Hybrid (Phase-based + Agent Sandboxes)
  ↓
v0.6: Session hygiene (gc, prune, archive) - Planned
  ↓
v0.7: Automation (WP8/WP9, API layer) - Planned
```

---

**สรุป:**
- Trinity = ระบบที่มี architecture ชัดเจน
- Workflow มี safety gates ทุก step
- v0.5 เพิ่ม multi-agent support (human-orchestrated)
- Component ทำงานร่วมกันอย่างมีระบบ
- Result = ปลอดภัย, ลด bias, ตรวจสอบได้

**Read more:**
- SESSION_CONTRACT.md (v0.5 spec)
- docs/USER_GUIDE.md (workflows)
- docs/GETTING_STARTED_v0.5.md (quick start)
