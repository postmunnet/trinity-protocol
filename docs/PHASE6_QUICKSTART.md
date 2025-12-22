# Phase 6 Quick Start Guide

**Trinity Protocol - Session-based Dev→Prod Execution**

Version: 1.0
Date: 2025-12-21
Status: ✅ Implemented

---

## 🎯 What is Phase 6?

Phase 6 ทำให้ Trinity ใช้งานจริงได้ ด้วย workflow แบบ **session-based** ที่:
- แยก dev/prod ชัดเจน
- มี verification gates ที่ทำงานจริง
- ไม่ต้อง manual copy
- zero-byte state files ไม่เกิด

---

## 🚀 Happy Path Workflow

```bash
# 1. เริ่ม Session ใหม่
ai session new "Fix Login Bug"

# 2. Snapshot โปรเจคปัจจุบัน
ai snapshot

# 3. แก้ไขใน DO/dev/ (edit files)
# ... work work work ...

# 4. Deploy Dev
ai deploy dev

# 5. Verify Dev
ai verify dev

# 6. Promote Dev → Prod
ai promote

# 7. Deploy Prod
ai deploy prod

# 8. Verify Prod
ai verify prod

# 9. Close Session (ต้อง verify prod pass)
ai close
```

---

## 📂 Session Structure

```
sessions/2025-12-21_fix_login_bug/
├── THINK/              # Context & Acceptance Criteria
│   ├── 00_CONTEXT.md
│   └── 01_ACCEPTANCE.md
│
├── DO/                 # Filesystem Truth
│   ├── snapshot/       (immutable backup)
│   ├── dev/            (working copy)
│   └── prod/           (release candidate)
│
├── CONTROL/            # Human-visible Control
│   ├── META.json       (workflow state)
│   ├── VERIFY.md       (verification log)
│   └── LIVE_MONITOR.md (real-time status)
│
└── .ai/state/          # System-only State
    ├── status.json
    ├── verify_report.json
    └── events.ndjson
```

---

## 🔒 Verification Gates

### Gate 1: Forbidden Files
Blocks: `.env`, `config/dev/**`

### Gate 2: Secret Scan
Detects: `api_key`, `secret`, `password`, AWS keys, OpenAI keys

### Gate 3: Smoke Hooks
(Phase 6 MVP: skipped, future: lint/test/curl)

---

## 🛡️ Safety Rules

### ✅ DO

- Deploy dev → only from `DO/dev`
- Deploy prod → only from `DO/prod`
- Promote must exclude `.env`, `config.dev.*`
- Close requires prod verify PASS

### ❌ DON'T

- Never deploy dev directly to prod
- Never skip verification (use --force sparingly)
- Never edit `.ai/state/` manually

---

## 📊 Commands Reference

### Session Management

```bash
# Create new session
ai session new "Task Name"

# Show current status
ai status show

# Get session path (for scripting)
ai status path
```

### Workflow Commands

```bash
# Snapshot project
ai snapshot [--force]

# Deploy
ai deploy dev [--force]
ai deploy prod [--force]

# Verify
ai verify dev [--strict|--permissive]
ai verify prod [--strict|--permissive]

# Promote
ai promote [--force]

# Close
ai close [--force]
```

### Testing

```bash
# Run verification self-test
ai verify selftest
```

---

## 🧪 Verification Self-Test

Phase 6 มี test fixtures สำหรับทดสอบ verification:

```bash
ai verify selftest
```

Test cases:
1. **pass_clean** → expect PASS (clean code)
2. **fail_secret** → expect FAIL (hardcoded API key)
3. **fail_forbidden** → expect FAIL (.env file)

---

## 🎯 Next Action Indicator

ใช้ `ai status show` เพื่อดูว่าต้องทำอะไรต่อ (5-second glance):

```
📊 Trinity Session Status

Session: Fix Login Bug
Phase: 🔍 verify_dev

Workflow Progress:
  ✓ Snapshot
  ✓ Deploy Dev
  ○ Verify Dev      ← You are here
  ○ Promote
  ○ Deploy Prod
  ○ Verify Prod
  ○ Close

⚡ Next Action:
   ai verify dev
   Verify dev before promotion
```

---

## 🚨 Common Issues

### Issue: "No active session"
```bash
ai session new "Your Task"
```

### Issue: "Dev directory empty"
```bash
ai snapshot
```

### Issue: "Verification failed"
Check report:
```bash
cat sessions/<session>/.ai/state/verify_report.json
```

Fix issues and re-run:
```bash
ai verify dev
```

### Issue: "Can't close - verification not passed"
```bash
# Fix issues in DO/prod
ai verify prod

# Then close
ai close
```

---

## 📝 File Locations

```
.ai/
├── testing/verify_fixtures/    Test fixtures for selftest
├── cli/commands/                Command implementations
│   ├── session.py              ✅ Phase 6
│   ├── verify.py               ✅ Phase 6 (actual gates)
│   ├── deploy.py               ✅ Phase 6
│   ├── status.py               ✅ Phase 6
│   └── close.py                ✅ Phase 6 (gate-locked)
└── .gitignore                  ✅ Phase 6
```

---

## ✅ Phase 6 Acceptance Criteria

- [x] One real job runs end-to-end with zero manual copy
- [x] `.env` in dev never appears in prod after promote
- [x] verify blocks secrets/forbidden files
- [x] prod verify must PASS before close
- [x] no state file is ever 0 bytes
- [x] `ai status` shows clear next action

---

## 🎓 Implementation Notes

### What Was Implemented

1. **Session Command** (`session.py`)
   - Phase 6 canonical structure
   - Workflow tracking in META.json
   - State initialization (never empty)

2. **Verification** (`verify.py`)
   - Forbidden file detection
   - Secret scanning with regex
   - Self-test with fixtures
   - Atomic report writing

3. **Deploy** (`deploy.py`)
   - Dev/Prod separation
   - Path enforcement
   - Verification check

4. **Status** (`status.py`)
   - 5-second glance
   - Workflow progress
   - Next action indicator

5. **Close** (`close.py`)
   - Gate-locked (requires prod verify PASS)
   - Archive to sessions/archive/
   - State cleanup

6. **Test Fixtures**
   - pass_clean/
   - fail_secret/
   - fail_forbidden/

### What's Out of Scope (Not Implemented)

- Actual deployment to remote servers (MVP: simulated)
- Smoke hooks execution (MVP: skipped)
- Cryptographic signatures
- Enterprise RBAC
- Multi-repo orchestration

---

## 🔗 Next Steps

1. **Test the workflow:**
   ```bash
   cd /path/to/your/project
   python -m .ai.cli.main session new "Test Phase 6"
   ```

2. **Run self-test:**
   ```bash
   python -m .ai.cli.main verify selftest
   ```

3. **Check status:**
   ```bash
   python -m .ai.cli.main status show
   ```

---

**End of Phase 6 Quick Start Guide**

For issues or questions, refer to:
- MASTER_BLUEPRINT.md
- PRIMER.md
- PROTOCOL.md
