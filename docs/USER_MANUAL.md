# Trinity Protocol - User Manual

**Version:** v0.5 / Phase 6.1
**Status:** Production Ready
**Last Updated:** 2025-12-21

---

## 📖 Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Daily Workflow](#daily-workflow)
4. [Commands Reference](#commands-reference)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

---

## 🚀 Quick Start

### First Time Setup (5 minutes)

```bash
# 1. Navigate to Trinity directory
cd /path/to/your/project

# 2. Run setup
bash .ai/setup.sh

# 3. Activate environment
source .venv/bin/activate

# 4. Test installation
cd .ai
python3 -m cli.main --help
```

### Your First Session (10 minutes)

```bash
cd .ai

# Create session
python3 -m cli.main session new "My First Task"

# Capture current state
python3 -m cli.main snapshot run

# Check status
python3 -m cli.main status show

# Edit files in: sessions/YYYY-MM-DD_my_first_task/DO/dev/

# Verify
python3 -m cli.main verify run --scope dev

# Done!
```

---

## 💻 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, recommended)

### Install Dependencies

```bash
# Method 1: Using setup script (Recommended)
bash .ai/setup.sh
source .venv/bin/activate

# Method 2: Manual installation
cd .ai
pip3 install -r requirements.txt
```

### Verify Installation

```bash
cd .ai
python3 -m cli.main --help

# Should show:
# Trinity Consoles - The AI-Native Operating System CLI
# Commands: session, snapshot, verify, promote, deploy, close, status
```

---

## 📋 Daily Workflow

### The Complete Workflow

```bash
cd .ai  # Always run from .ai directory

# 1. Start Session
python3 -m cli.main session new "Fix Login Bug"
# Creates: sessions/2025-12-21_fix_login_bug/

# 2. Snapshot (Capture current project state)
python3 -m cli.main snapshot run
# Copies: project_root → DO/snapshot → DO/dev

# 3. Work (Edit files)
# Go to: sessions/2025-12-21_fix_login_bug/DO/dev/
# Edit your code here

# 4. Verify Dev
python3 -m cli.main verify run --scope dev
# Checks: forbidden files, secrets, smoke hooks
# Result: PASS/FAIL

# 5. Promote (Dev → Prod)
python3 -m cli.main promote run
# Syncs: DO/dev → DO/prod (excludes .env, logs, etc)

# 6. Verify Prod
python3 -m cli.main verify run --scope prod
# Final verification before production

# 7. Close Session
python3 -m cli.main close run
# Archives session (requires prod verify PASS)

# Check status anytime
python3 -m cli.main status show
```

---

## 📚 Commands Reference

### Session Management

#### `session new "<title>"`
Create a new work session.

```bash
python3 -m cli.main session new "Fix Login Bug"

# Creates structure:
# sessions/YYYY-MM-DD_fix_login_bug/
# ├── THINK/      (planning documents)
# ├── DO/         (code: snapshot/dev/prod)
# ├── CONTROL/    (status, logs)
# └── .ai/state/  (system state)
```

**When to use:** Start of every task

---

### Snapshot

#### `snapshot run [--force]`
Capture current project state.

```bash
python3 -m cli.main snapshot run

# With force (overwrite existing)
python3 -m cli.main snapshot run --force
```

**What it does:**
1. Copies project_root → DO/snapshot (immutable backup)
2. Copies DO/snapshot → DO/dev (working copy)

**When to use:** After creating session, before editing

---

### Verification

#### `verify run --scope <dev|prod> [--permissive]`
Run safety verification gates.

```bash
# Verify dev (strict mode)
python3 -m cli.main verify run --scope dev

# Verify prod (strict mode)
python3 -m cli.main verify run --scope prod

# Permissive mode (warnings don't block)
python3 -m cli.main verify run --scope dev --permissive
```

**Gates:**
1. **Forbidden Files** - Blocks: `.env`, `config/dev/**`
2. **Secret Scan** - Detects: api_key, password, tokens
3. **Smoke Hooks** - (Skipped in MVP)

**Exit Codes:**
- `0` = PASS (safe to proceed)
- `1` = FAIL (issues found, blocked)
- `2` = ERROR (command/config error)

**When to use:**
- After editing dev → before promote
- After promote → before close

---

### Promotion

#### `promote run [--force]`
Promote dev to prod (atomic sync).

```bash
python3 -m cli.main promote run

# Force (skip verification check)
python3 -m cli.main promote run --force
```

**What it does:**
1. Checks dev verification passed
2. Syncs DO/dev → DO/prod
3. Excludes: `.env`, `config.dev.*`, `logs/`, `cache/`, `tmp/`
4. Atomic operation (temp → rename)

**Safety:**
- Requires dev verify PASS (unless --force)
- Never copies forbidden files

**When to use:** After dev verify passes

---

### Deployment

#### `deploy <dev|prod>`
Deploy to target environment.

```bash
# Deploy dev
python3 -m cli.main deploy dev

# Deploy prod
python3 -m cli.main deploy prod
```

**Configuration:**
Edit `.ai/ssot.yaml`:
```yaml
deploy:
  dev:
    type: local_copy  # or rsync, scp
    path: /path/to/dev/server
  prod:
    type: rsync
    host: user@prod-server
    path: /var/www/app
    options: "-az --delete"
```

**When to use:**
- After snapshot → deploy dev
- After promote → deploy prod

---

### Close Session

#### `close run [--force]`
Close and archive session.

```bash
python3 -m cli.main close run

# Force close (skip prod verify check)
python3 -m cli.main close run --force
```

**Requirements:**
- Prod verify must PASS (unless --force)

**What it does:**
1. Checks prod verification
2. Updates META.json status → closed
3. Archives session to `archive/`
4. Clears global active session

**When to use:** After prod verify passes

---

### Status

#### `status show`
Show current session status and next action.

```bash
python3 -m cli.main status show
```

**Output:**
- Current session info
- Workflow progress (visual)
- Next action recommendation
- File counts

**When to use:** Anytime (especially after resuming work)

---

### Self-Test

#### `verify selftest`
Test verification gates with fixtures.

```bash
python3 -m cli.main verify selftest
```

**Tests:**
- pass_clean → expect PASS
- fail_secret → expect FAIL
- fail_forbidden → expect FAIL

**When to use:**
- After installation (verify setup)
- After changing verification rules
- Debugging verification issues

---

## 🎯 Common Scenarios

### Scenario 1: Fix a Simple Bug

```bash
cd .ai

# Start
python3 -m cli.main session new "Fix Typo in README"
python3 -m cli.main snapshot run

# Work
# Edit: sessions/2025-12-21_fix_typo_in_readme/DO/dev/README.md

# Verify & Promote
python3 -m cli.main verify run --scope dev
python3 -m cli.main promote run

# Final Check & Close
python3 -m cli.main verify run --scope prod
python3 -m cli.main close run
```

**Time:** ~10 minutes

---

### Scenario 2: Add New Feature

```bash
cd .ai

# Start
python3 -m cli.main session new "Add User Profile"
python3 -m cli.main snapshot run

# Work
# Edit multiple files in: sessions/.../DO/dev/
# - Create new components
# - Update API
# - Add tests

# Verify Dev
python3 -m cli.main verify run --scope dev
# If FAIL → fix issues → verify again

# Promote
python3 -m cli.main promote run

# Verify Prod
python3 -m cli.main verify run --scope prod

# Close
python3 -m cli.main close run
```

**Time:** Hours to days (depending on feature)

---

### Scenario 3: Emergency Hotfix

```bash
cd .ai

# Start
python3 -m cli.main session new "HOTFIX: Critical Bug"
python3 -m cli.main snapshot run

# Quick Fix
# Edit: sessions/.../DO/dev/critical_file.py

# Fast Verify (permissive mode)
python3 -m cli.main verify run --scope dev --permissive

# Promote & Deploy
python3 -m cli.main promote run
python3 -m cli.main deploy prod  # If configured

# Strict Verify Prod
python3 -m cli.main verify run --scope prod

# Close
python3 -m cli.main close run
```

**Time:** ~30 minutes (emergency)

---

### Scenario 4: Resume After Interruption

```bash
cd .ai

# Check what you were doing
python3 -m cli.main status show

# Shows:
# - Current session
# - Current phase
# - Next action

# Continue from where you left off
# (Follow the "Next Action" suggestion)
```

---

## 🔧 Troubleshooting

### Error: "SSOT not found"

**Problem:** Running from wrong directory

**Solution:**
```bash
# Must run from .ai directory
cd /path/to/project/.ai
python3 -m cli.main [command]
```

---

### Error: "No active session"

**Problem:** No session created yet

**Solution:**
```bash
python3 -m cli.main session new "Your Task Name"
```

---

### Error: "Snapshot/Dev dirs not empty"

**Problem:** Session already has snapshot

**Solution:**
```bash
# Option 1: Use existing snapshot
# (Skip snapshot, continue working)

# Option 2: Force new snapshot
python3 -m cli.main snapshot run --force
```

---

### Error: "Verification FAILED"

**Problem:** Found forbidden files or secrets

**Solution:**
```bash
# 1. Check report
cat sessions/YYYY-MM-DD_xxx/.ai/state/verify_report.json

# 2. View details
# Look at "blocks" array for specific issues

# 3. Fix issues
# Remove .env files
# Remove hardcoded secrets

# 4. Verify again
python3 -m cli.main verify run --scope dev
```

---

### Error: "GATE LOCK: prod verify not PASS"

**Problem:** Trying to close without prod verification

**Solution:**
```bash
# Run prod verification first
python3 -m cli.main verify run --scope prod

# Then close
python3 -m cli.main close run
```

---

### Error: "ModuleNotFoundError: No module named 'typer'"

**Problem:** Dependencies not installed

**Solution:**
```bash
# Run setup
bash .ai/setup.sh
source .venv/bin/activate

# Or install manually
pip3 install -r .ai/requirements.txt
```

---

## 🎓 Advanced Usage

### Custom Deploy Configuration

Edit `.ai/ssot.yaml`:

```yaml
deploy:
  dev:
    type: rsync
    host: dev-server
    path: /var/www/app-dev
    options: "-az --delete --exclude=.git"

  prod:
    type: rsync
    host: prod-server
    path: /var/www/app
    options: "-az --delete"
```

Supported types:
- `local_copy` - Copy to local path (default)
- `rsync` - Remote sync via rsync
- `scp` - Secure copy via scp

---

### Working with THINK Documents

Before starting work, optionally fill out:

```bash
# Navigate to session
cd sessions/YYYY-MM-DD_xxx/THINK/

# Fill out:
00_CONTEXT.md       - What and why
01_PROMPT.md        - Problem statement
02_SCOPE.md         - What will change
03_ACCEPTANCE.md    - Success criteria
```

**Note:** These are optional but helpful for complex tasks

---

### Monitoring Session Progress

```bash
# Quick status
python3 -m cli.main status show

# View verification log
cat sessions/YYYY-MM-DD_xxx/CONTROL/VERIFY.md

# View live monitor
cat sessions/YYYY-MM-DD_xxx/CONTROL/LIVE_MONITOR.md

# View state
cat sessions/YYYY-MM-DD_xxx/.ai/state/status.json
```

---

### Manual Testing Before Promote

```bash
# After editing DO/dev/, test manually:

# 1. Go to dev directory
cd sessions/YYYY-MM-DD_xxx/DO/dev/

# 2. Run your tests
pytest tests/
npm test
# etc.

# 3. If all pass, verify
cd ../../../..
python3 -m cli.main verify run --scope dev

# 4. Promote
python3 -m cli.main promote run
```

---

## 📁 Session Structure Explained

```
sessions/2025-12-21_your_task/
├── THINK/                     📝 Planning (Optional to fill)
│   ├── 00_CONTEXT.md         What/Why/Scope
│   ├── 01_PROMPT.md          Problem statement
│   ├── 02_SCOPE.md           Files to change
│   ├── 03_ACCEPTANCE.md      Success criteria
│   ├── CLAUDE_GOVERNANCE_DECISION.md  Major decisions
│   └── NOTES.md              Working notes
│
├── DO/                        💼 Where you work
│   ├── snapshot/             🔒 Immutable backup (DO NOT EDIT)
│   ├── dev/                  ✏️ Working copy (EDIT HERE)
│   └── prod/                 🚀 Release (from promote)
│
├── CONTROL/                   📊 Status & Logs (Read-only)
│   ├── META.json             Session metadata
│   ├── VERIFY.md             Verification log
│   └── LIVE_MONITOR.md       Real-time status
│
└── .ai/state/                 🔐 System State (NEVER EDIT)
    ├── status.json           Current phase
    ├── verify_report.json    Latest verify results
    └── events.ndjson         Event log
```

### What to Edit

| Folder | Can Edit? | Purpose |
|--------|-----------|---------|
| **THINK/** | ✅ Yes | Planning documents |
| **DO/dev/** | ✅ Yes | Your working code |
| **DO/snapshot/** | ❌ No | Immutable backup |
| **DO/prod/** | ❌ No | System-managed |
| **CONTROL/** | ❌ No | Read-only logs |
| **.ai/state/** | ❌ Never | System-only state |

---

## 🔒 Safety Features

### Forbidden File Detection
Automatically blocks these from prod:
- `.env` and `.env.*`
- `config/dev/**`
- `**/config.dev.*`

**Tested:** ✅ Working

---

### Secret Scanning
Detects hardcoded secrets:
- API keys (`api_key=...`, `sk-...`)
- Passwords (`password=...`)
- Tokens (`secret=...`, `token=...`)
- AWS keys, Private keys

**Tested:** ✅ Working

---

### Atomic Operations
All critical operations use atomic writes:
- State files: temp → rename
- Promote: prod_new → prod
- No half-copied files

**Tested:** ✅ Working

---

### Gate-Locked Close
Cannot close session unless:
- Prod verification PASSED
- Or use `--force` (not recommended)

**Tested:** ✅ Working

---

## 💡 Tips & Best Practices

### DO
- ✅ Check status before resuming work
- ✅ Verify dev before promote
- ✅ Verify prod before close
- ✅ Use descriptive session names
- ✅ Review CONTROL/VERIFY.md to see history

### DON'T
- ❌ Edit DO/snapshot/ (immutable)
- ❌ Edit .ai/state/ files (system-only)
- ❌ Skip verification (use --force sparingly)
- ❌ Run from random directories (must be in .ai/)
- ❌ Manually copy files between dev/prod

---

## 🧪 Testing Trinity

### Run Self-Test

```bash
cd .ai
python3 -m cli.main verify selftest

# Expected output:
# Test 1: pass_clean    → PASS ✓
# Test 2: fail_secret   → FAIL ✓
# Test 3: fail_forbidden → FAIL ✓
# ✅ All self-tests passed!
```

### Test End-to-End

```bash
# Complete workflow test
python3 -m cli.main session new "Test Run"
python3 -m cli.main snapshot run
python3 -m cli.main verify run --scope dev
python3 -m cli.main promote run
python3 -m cli.main verify run --scope prod
python3 -m cli.main close run

# All should succeed with no errors
```

---

## 📊 Workflow Diagram

```
┌─────────────────┐
│  session new    │ Create session
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  snapshot run   │ Capture state (prod → snapshot → dev)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Edit DO/dev/    │ Make your changes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ verify dev      │ Check safety (forbidden files, secrets)
└────────┬────────┘
         │
    PASS │ FAIL → Fix issues
         ▼
┌─────────────────┐
│  promote run    │ Sync dev → prod (atomic, excludes)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ verify prod     │ Final safety check
└────────┬────────┘
         │
    PASS │ FAIL → Fix issues
         ▼
┌─────────────────┐
│  close run      │ Archive session
└─────────────────┘
```

---

## 📖 Related Documentation

- **PRIMER.md** - 2-minute overview
- **MASTER_BLUEPRINT.md** - Architecture and "3 Locks" concept
- **PHASE6_QUICKSTART.md** - Phase 6 introduction
- **PHASE6_FINAL_REPORT.md** - Implementation details
- **PRODUCTION_READINESS_CHECKLIST.md** - Readiness assessment
- **templates/README.md** - Template system guide
- **tests/verify_fixtures/README.md** - Testing guide

---

## 🆘 Getting Help

### Check Status
```bash
python3 -m cli.main status show
```

### View Logs
```bash
# Verification log
cat sessions/YYYY-MM-DD_xxx/CONTROL/VERIFY.md

# Deploy logs
cat sessions/YYYY-MM-DD_xxx/CONTROL/DEPLOY_DEV.log
cat sessions/YYYY-MM-DD_xxx/CONTROL/DEPLOY_PROD.log

# State
cat sessions/YYYY-MM-DD_xxx/.ai/state/verify_report.json
```

### Common Issues
See [Troubleshooting](#troubleshooting) section above

---

## 🎓 Learning Path

### Day 1: Learn Basics
- Read PRIMER.md (2 min)
- Run setup.sh
- Create first session
- Run selftest

### Day 2: First Real Task
- Pick simple task (doc fix)
- Run complete workflow
- Understand each step

### Week 1: Daily Use
- Use for all small changes
- Get comfortable with commands
- Customize deploy config

### Week 2+: Advanced
- Configure rsync/scp
- Customize verification rules
- Integrate with CI/CD

---

## 🔗 Quick Command Reference

| What | Command |
|------|---------|
| **Setup** | `bash .ai/setup.sh` |
| **New Session** | `python3 -m cli.main session new "Task"` |
| **Snapshot** | `python3 -m cli.main snapshot run` |
| **Verify** | `python3 -m cli.main verify run --scope dev` |
| **Promote** | `python3 -m cli.main promote run` |
| **Close** | `python3 -m cli.main close run` |
| **Status** | `python3 -m cli.main status show` |
| **Test** | `python3 -m cli.main verify selftest` |

---

## 📝 Cheat Sheet

### Full Workflow (Copy-Paste)
```bash
cd .ai
python3 -m cli.main session new "Your Task"
python3 -m cli.main snapshot run
# ... edit DO/dev/ ...
python3 -m cli.main verify run --scope dev
python3 -m cli.main promote run
python3 -m cli.main verify run --scope prod
python3 -m cli.main close run
```

---

**For detailed implementation specs, see PRD v0.4 and technical documentation.**

**Questions?** Check PRODUCTION_READINESS_CHECKLIST.md for testing results.

---

**End of User Manual**
