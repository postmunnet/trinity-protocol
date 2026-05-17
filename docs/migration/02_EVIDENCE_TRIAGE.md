---
title: "Commit 0 — Evidence Triage Report"
status: complete
last-updated: 2026-04-28
audience: "Anyone executing Commit 1+"
purpose: "Hard evidence collected before committing to plan. Read this to know exactly what's broken and what's myth."
---

# 2. Evidence Triage (Commit 0 Findings)

> **Methodology:** ก่อน execute commits ที่ "fix bug" — ต้องรันจริง + diff จริง + grep จริง ห้าม assume

## 2.1 Finding 1 — `ai status` พังจริง (root causes ชัด)

### Test 1: direct invocation
```bash
$ python3 .ai/cli/main.py status
ImportError: attempted relative import with no known parent package
```

### Test 2: pytest (3/14 fail)
```
FAILED test_basic.py::test_ssot_exists           — ไม่มี .ai/ssot.yaml
FAILED test_basic.py::test_state_initialized     — ไม่มี .ai/state/
FAILED test_basic.py::test_canaries_exist        — ไม่มี .ai/testing/canaries/canary_with_secrets.py
PASSED 11 tests
```

### Root cause analysis
1. **Direct invocation ผิด pattern** — Trinity CLI ใช้ launcher `bash .ai/cli/ai` ที่จัด `python3 -m cli.main` ให้
2. **ขาดไฟล์ config 3 ตัว:**
   - `.ai/ssot.yaml` (paths config)
   - `.ai/state/*.template` (state initialization)
   - `.ai/testing/canaries/canary_with_secrets.py` (secret-detection test fixture)

### Action (Commit 1)
- ✅ Use `bash .ai/cli/ai status` for invocation (launcher already correct in HEAD)
- ✅ Add 3 missing config files from TRINITY_LEGACY/.ai/ HEAD

## 2.2 Finding 2 — B1-B4 Battle-Tested Rules = MYTH ⭐

### Hypothesis (จาก initial brainstorm)
> "<upstream-project> มี B1-B4 safety rules ที่ผ่าน production จริง — ต้อง port เข้า trinity_v2"

### Evidence
```bash
$ diff <upstream-project>/.ai/policies/safety.yaml TRINITY_LEGACY/.ai/policies/safety.yaml
→ IDENTICAL  ✅ (zero diff)

$ grep -rln "B1\|B2\|B3\|B4\|safety_b" <upstream-project>/.ai/ <upstream-project>/ai-docs/
# matches found ONLY in:
- <upstream-project>/.ai/archive/phase6_docs/PRODUCTION_READINESS_CHECKLIST.md  (legacy)
- <upstream-project>/.ai/sessions/archive/legacy_docs/                          (archived sessions)
- <upstream-project>/.ai/sessions/archive/.../libraries/PHPExcel/*              (3rd-party PHP libraries)
```

### Verdict
**B1-B4 = phantom assumption** จาก feedback chain (Codex → Gemini → friend). <upstream-project> ไม่ได้มี battle-tested rules พิเศษอะไร — ใช้ MVP draft v1 เหมือน TRINITY_LEGACY ทุกประการ

### Action
- ❌ **SKIP** any "B1-B4 port" task
- ✅ Use `TRINITY_LEGACY/.ai/policies/safety.yaml` ตรงๆ

## 2.3 Finding 3 — <upstream-project>/ai-docs/ Survey (Option B chosen)

### Structure (11 ไฟล์ทั้งหมด)
```
<upstream-project>/ai-docs/
├── 01-CORE_PROTOCOL/              (6 ไฟล์)
│   ├── GOD_TEAM_INTERACTION.md
│   ├── HUMAN_AGENT_INTERACTION.md
│   ├── MULTI_AI_COLLABORATION.md
│   ├── SAFETY_GATES.md            ⚠️ contaminated
│   ├── TOOL_USAGE.md
│   └── WORKFLOW.md
├── 02-STANDARDS/                  (4 ไฟล์)
│   ├── ENV_VARS.md                ⚠️ contaminated
│   ├── HUMAN_INTERFACE.md
│   ├── QUICK_REF.md
│   └── UNIVERSAL_RULES.md
├── 03-PROCESS/                    (1 ไฟล์)
│   └── ROLLBACK_PROCEDURES.md     ⚠️ contaminated
└── 04-MEMORY/                     (empty)
```

### Contamination check
```bash
$ grep -rl "<upstream-project>\|smarty\|deploy_dev_order\|FTP_CRED" <upstream-project>/ai-docs/0[1-4]-*/
→ 3 files contain <upstream-project>-specific terms:
   01-CORE_PROTOCOL/SAFETY_GATES.md
   02-STANDARDS/ENV_VARS.md
   03-PROCESS/ROLLBACK_PROCEDURES.md
```

### Action (Commit 5)
- ✅ Copy 11 ไฟล์ → `trinity_v2/ai-docs/0[1-4]-*/`
- ✅ Scrub 3 ไฟล์ — replace:
  - `<upstream-project>` → `{{PROJECT_NAME}}`
  - `smarty` → `{{TEMPLATE_ENGINE}}`
  - `deploy_dev_order_detail.sh` → `{{DEPLOY_SCRIPT}}`
  - hardcoded paths → relative or `{{APP_DIR}}` placeholders
  - FTP/credential context → remove or generic warning
- ✅ Verify post-scrub: `grep "<upstream-project>\|smarty\|FTP_CRED" trinity_v2/ai-docs/` → 0 matches

## 2.4 Finding 4 — TRINITY_LEGACY Uncommitted Scope (~1,700 lines)

### Untracked files (8 ไฟล์ ของใหม่)
| File | Lines | Purpose |
|------|-------|---------|
| `cli/core/artifacts.py` | 123 | new artifact module |
| `cli/core/kernel.py` | 112 | new kernel module |
| `cli/core/session_naming.py` | 165 | session naming v2 |
| `cli/tests/test_session_naming.py` | 183 | tests for above |
| `docs/SESSION_NAMING.md` | 224 | session naming doc |
| `docs/V2_MIGRATION.md` | 64 | v1→v2 migration guide |
| `memory/KNOWN_ISSUES.md` | 166 | brain seed |
| `memory/TRINITY_IMPROVEMENTS.md` | 367 | brain seed |

### Modified cli files (2 ไฟล์)
- `cli/commands/debate.py` — +24/-24 lines tweak
- `cli/commands/session.py` — +57/-36 lines (likely wires session_naming)

### New SANDBOX templates (numbered v2)
```
templates/session/SANDBOX/
├── 00_BRAINSTORM/
├── 01_DEBATE/
├── 02_gemini/
├── 03_claude/
├── 04_codex/
└── README.md
```

### Deleted (legacy SANDBOX, replaced by numbered)
- `SANDBOX/DEBATE/{README,round_1,round_2,round_3,verdict}.md`
- `SANDBOX/claude/{WORKSPACE_PROMPT,critique,governance,proposal,review}.md`
- `SANDBOX/codex/{WORKSPACE_PROMPT,implementation,patch.diff,proposal}.md`

### Action (Commit 3)
- ✅ Direct file copy from working tree (ไม่ commit ที่ source ก่อน)
- ✅ ใช้ `cp` ไม่ใช่ `git archive` (เพราะ untracked)
- ✅ Acceptance: `bash .ai/cli/ai session new "fix: smoke"` → สร้าง session ที่มี THINK/, SANDBOX/00_BRAINSTORM/, SANDBOX/01_DEBATE/, DO/, CONTROL/ ได้

## 2.5 Summary Table — Decision Inputs

| Question | Hypothesis | Evidence | Verdict | Action |
|----------|-----------|----------|---------|--------|
| ai status broken? | yes | ImportError + 3 test fail | ✅ confirmed | Commit 1: add ssot.yaml + state + canary |
| B1-B4 rules in <upstream-project>? | yes (Codex/Gemini/friend claim) | diff IDENTICAL, no active matches | ❌ MYTH | Skip — use TRINITY_LEGACY safety.yaml |
| <upstream-project>/ai-docs has structure value? | yes | 11 files, clean structure | ✅ true | Commit 5: copy + scrub 3 |
| Uncommitted TRINITY_LEGACY changes are real v2 work? | yes (user claim) | 8 untracked + 2 modified, ~1700 lines | ✅ confirmed | Commit 3: direct file copy |
