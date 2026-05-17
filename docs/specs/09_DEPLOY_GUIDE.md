---
title: "Trinity OS Deploy & Operations Guide"
subtitle: "Install · Migrate · Operate · Troubleshoot · Rollback"
version: 1.0.0
status: draft
last-updated: 2026-04-28
audience: Operators, DevOps, Project leads
---

# Trinity OS — Deploy & Operations Guide

> Practical runbook สำหรับ install, migrate, operate, troubleshoot Trinity OS

---

## 0. Status

- **Audience:** ผู้ที่จะ install/migrate/operate Trinity OS
- **Prerequisite:** อ่าน [`00_BLUEPRINT.md`](00_BLUEPRINT.md) แล้ว
- **Use cases:** New project · Migrate <upstream-project> · Multi-project ops

---

## 1. Pre-install Checklist

### 1.1 System Requirements

| Component | Required | Why |
|-----------|----------|-----|
| **bash 4+** or **zsh** | ✅ | Bootstrap script |
| **Python 3.10+** | ✅ | Trinity kernel CLI |
| **Node.js 18+** | ✅ | CLI tools (browser-cli, memory-cli) |
| **Git** | ✅ | State tracking, audit |
| **SQLite 3.30+** | ✅ | memory-cli (FTS5) |
| **jq** | 🟡 recommended | NDJSON log parsing |
| **tmux** | 🟡 recommended | Multi-pane workflow |

### 1.2 AI Vendor Tools

ต้องติดตั้งอย่างน้อย 1 ตัว:

| Vendor | Install |
|--------|---------|
| **Claude Code** | https://claude.com/claude-code (recommended) |
| **Codex CLI** | `npm install -g @openai/codex-cli` |
| **Cursor** | https://cursor.com |
| **Gemini CLI** | `npm install -g @google/gemini-cli` |

### 1.3 Project Repo

```bash
# Project ต้องเป็น git repo
cd my-project
git init  # if not already
```

### 1.4 Verify Pre-conditions

```bash
# Run pre-install checker (when available)
bash trinity-bootstrap-pack/preflight.sh

# Or manual:
node --version    # 18+
python3 --version # 3.10+
git --version
sqlite3 --version
```

---

## 2. Use Case A: Bootstrap New Project (Greenfield)

### 2.1 Steps

```bash
# 1. Clone bootstrap pack (one-time)
cd ~/code
git clone <bootstrap-pack-repo> trinity-bootstrap-pack

# 2. Create new project
mkdir my-new-app
cd my-new-app
git init

# 3. Install Trinity OS
bash ~/code/trinity-bootstrap-pack/install.sh .

# Interactive prompts:
# Project name: my-new-app
# Project type: web-app
# Tech stack: Node+React
# App dir: ./
# Dev folder: dev
# Prod folder: prod

# 4. Verify install
bash ~/code/trinity-bootstrap-pack/verify-install.sh .

# Expected: 18 ✓ checks pass

# 5. Open AI tool
# In Claude Code:
> lll
# → Should show project status + know all short codes
```

### 2.2 First Session

```bash
# In Claude Code or other harness
lll                              # status
vvv "Build user login feature"   # verify (5 questions)
nnn                              # plan
gogogo                           # execute
rrr                              # retro
```

### 2.3 Add CLI Tools

```bash
# Install browser-cli (if needed)
cd ~/code
git clone <browser-cli-repo>
cd browser-cli && npm install

# Register in Trinity
cd /path/to/my-new-app
cat >> .ai/tools.yaml << 'EOF'
  - name: browser-cli
    path: ~/code/browser-cli
    bin: node ~/code/browser-cli/index.js
    schema_version: "2"
    capabilities: [browser, dom, screenshot]
    contract_version: "1.1"
EOF

# Verify
trinity tool verify browser-cli
```

---

## 3. Use Case B: Migrate Existing Project (e.g. <upstream-project>)

> ดู [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md) สำหรับ specific gap analysis

### 3.1 Pre-migration Backup

```bash
cd <upstream-project>

# Backup current state
git checkout -b backup/pre-trinity-v2-$(date +%Y%m%d)
git add -A
git commit -m "Backup before Trinity OS v2 migration"
git tag pre-trinity-v2

# Backup AI configs
cp -r .claude .claude.backup-$(date +%Y%m%d)
cp -r .ai .ai.backup-$(date +%Y%m%d)
cp -r ai-docs ai-docs.backup-$(date +%Y%m%d)
cp CLAUDE.md CLAUDE.md.backup
cp AGENTS.md AGENTS.md.backup 2>/dev/null || true
```

### 3.2 Diff Against New Spec

```bash
# Compare current vs bootstrap pack
diff -r ai-docs/ ~/code/trinity-bootstrap-pack/ai-docs/ | less
diff CLAUDE.md ~/code/trinity-bootstrap-pack/templates/CLAUDE.md.template | less
```

### 3.3 Selective Migration (Safe)

#### Phase A: Add new structures (additive)

```bash
# 1. Add TRINITY_EVOLUTION/ docs (read-only reference)
cp -r ~/code/trinity-bootstrap-pack/.. /TRINITY_EVOLUTION/ . 2>/dev/null

# 2. Add new policies (don't overwrite existing)
mkdir -p .ai/policies
cp ~/code/trinity-bootstrap-pack/.ai/policies/verifier-rules.yaml .ai/policies/

# 3. Add new graphs
mkdir -p .ai/graphs
cp ~/code/trinity-bootstrap-pack/.ai/graphs/standard.yaml .ai/graphs/

# 4. Add tools.yaml (if missing)
[ -f .ai/tools.yaml ] || cp ~/code/trinity-bootstrap-pack/.ai/tools.yaml .ai/

# Test — old workflow still works
# (Don't break <upstream-project> yet)
```

#### Phase B: Update vocabulary (CLAUDE.md)

```bash
# Manual merge — DO NOT auto-overwrite
# Take from new template:
# - Inline short codes section
# - Trinity vocabulary cheat sheet
# - Updated "READ FIRST" mandatory blockers
# 
# Keep from old:
# - Project-specific paths
# - Custom rules
# - Production environment details

vim CLAUDE.md
# Manually merge — see template at trinity-bootstrap-pack/templates/CLAUDE.md.template
```

#### Phase C: Remove MCP servers (per decision #5)

```bash
# Backup
cp .claude/settings.local.json .claude/settings.local.json.before-mcp-removal

# Remove MCP permissions
# Edit .claude/settings.local.json — remove lines:
# - mcp__playwright__*
# - mcp__morphllm-fast-apply__*
# - mcp__sequential-thinking__*
# Keep: mcp__ide__executeCode (vendor IDE bridge)

# Remove MCP server config (user-level)
# ~/.claude.json or similar — remove playwright/morphllm/sequential entries
```

#### Phase D: Wire CLI tools

```bash
# Install browser-cli (replaces Playwright MCP)
cd ~/code
git clone <browser-cli-repo>
cd browser-cli && npm install

# Register in <upstream-project>
cd /path/to/<upstream-project>
# Edit .ai/tools.yaml to add browser-cli

# Test
node ~/code/browser-cli/index.js --config configs/<upstream-project>.json --cmd "goto /"
# Should work without MCP
```

#### Phase E: Index existing retros (Phase 2)

When memory-cli is built:

```bash
# Install memory-cli
cd ~/code
git clone <memory-cli-repo>
cd memory-cli && npm install

# Index <upstream-project> retros
cd /path/to/<upstream-project>
node ~/code/memory-cli/index.js --cmd "index .claude/retrospectives/"
node ~/code/memory-cli/index.js --cmd "index ai-docs/real_lessons/ --confidence=verified"

# Verify
node ~/code/memory-cli/index.js --cmd "stats"
# → 240+ docs indexed
```

### 3.4 Rollback Migration

```bash
# If anything breaks
cd <upstream-project>

# Restore from backup
rm -rf .claude .ai ai-docs CLAUDE.md
mv .claude.backup-<date> .claude
mv .ai.backup-<date> .ai
mv ai-docs.backup-<date> ai-docs
mv CLAUDE.md.backup CLAUDE.md

# Or git restore
git reset --hard pre-trinity-v2
```

---

## 4. Day 1 Operations

### 4.1 Starting a Session

```bash
# In Claude Code
> lll
```

Expected output:
```
📊 Project: my-new-app
Branch: main (clean)
Active session: none
Recent retros: (none)
Pending: setup project

🔴 Reminders:
- vvv before nnn
- Read actual code
- Approval before prod

Ready — type vvv to begin
```

### 4.2 Standard Workflow

```bash
> vvv "Add login feature"
# → AI asks 5 questions, gathers evidence
# → searches memory for similar past
# → writes verify-report.json

> nnn
# → AI plans (with memory hints)
# → writes 02_PLAN.md
# → asks user to approve

> gogogo
# → Trinity loop starts
# → executes plan steps
# → calls verify-cli after each
# → reports progress

> rrr
# → AI writes retro
# → retro-cli validates
# → memory-cli indexes
```

### 4.3 Ending a Session

```bash
> ccc                    # checkpoint (auto-saved)
> rrr                    # retro
# → session archived to .ai/sessions/<id>/
# → goals marked done
# → memory updated
```

---

## 5. Common Operations

### 5.1 Install a New CLI Tool

```bash
# 1. Clone tool repo
cd ~/code
git clone <tool-repo>
cd <tool-name>

# 2. Install dependencies
npm install   # or pip install, etc.

# 3. Run tests
node tests/harness.js
node tests/golden.js

# 4. Contract compliance check
trinity-contract-test <tool-name>
# → Must hit at least Bronze

# 5. Register in project
cd /path/to/project
cat >> .ai/tools.yaml << EOF
  - name: <tool-name>
    path: ~/code/<tool-name>
    bin: <bin-command>
    schema_version: "1"
    capabilities: [...]
    contract_version: "1.1"
EOF

# 6. Verify
trinity tool list
trinity tool health <tool-name>
```

### 5.2 Add a Custom Verifier Rule

```bash
# Edit rule set
vim .ai/policies/verifier-rules.yaml

# Add new rule
verifier_rules:
  my_custom_rule:
    description: "Custom check for project X"
    required_evidence:
      - my_artifact_type
    pass_when:
      - my_condition
    retry_when: [...]
    needs_human_when: [...]
    dead_when: [...]

# Validate
verify-cli --cmd "lint-rules"

# Test
verify-cli --cmd "dry-run --rule-set=my_custom_rule"
```

### 5.3 Add a Custom Graph (Workflow)

```bash
# Create new graph file
cp .ai/graphs/standard.yaml .ai/graphs/my-workflow.yaml

# Edit
vim .ai/graphs/my-workflow.yaml

# Validate
trinity graph validate my-workflow

# Visualize
trinity graph viz my-workflow > my-workflow.mmd

# Use
trinity loop start --goal "..." --graph=my-workflow
```

### 5.4 Search Memory

```bash
# Find past similar work
memory-cli --cmd "search 'auth bug fix'"

# Recent retros
memory-cli --cmd "list --since=7d"

# Tag-based
memory-cli --cmd "list --tag=critical"

# Get specific doc
memory-cli --cmd "get r_2025-11-25_auth-fix"
```

### 5.5 Manual Checkpoint / Resume

```bash
# Checkpoint current loop
trinity loop checkpoint --session=$(cat .ai/sessions/active/.id)

# Restart system, then:
trinity loop resume --session=<session-id>
# → Picks up from latest checkpoint
```

### 5.6 Force Human Escalation

```bash
trinity escalate --reason="needs review" --message="..."
# → Pauses loop, sends to user
```

---

## 6. Multi-Project Management

### 6.1 Layout

```
~/code/
├── trinity-bootstrap-pack/      ← shared
├── browser-cli/                  ← shared CLI tool
├── memory-cli/                   ← shared CLI tool
├── verify-cli/                   ← shared
├── retro-cli/                    ← shared
└── projects/
    ├── <upstream-project>/                   ← project A
    │   └── .ai/tools.yaml
    ├── <upstream-domain-short>/               ← project B
    │   └── .ai/tools.yaml
    └── my-new-app/               ← project C
        └── .ai/tools.yaml
```

### 6.2 Per-project Config

แต่ละ project มี:
- `.ai/ssot.yaml` (project paths)
- `.ai/tools.yaml` (tool registry — points to shared CLI tools)
- `.ai/policies/` (project-specific overrides)
- `.ai/graphs/` (project-specific workflows)
- `.claude/settings.local.json` (Claude permissions)
- `.claude/retrospectives/` (per-project memory)

### 6.3 Shared Tool Updates

```bash
# Update browser-cli (affects all projects)
cd ~/code/browser-cli
git pull
npm install
trinity-contract-test browser-cli

# All projects pick up update next invocation
# (because tools.yaml points to shared path)
```

### 6.4 Cross-project Memory (Future Phase 9+)

Currently: memory-cli scoped per-project (`./.memory/`)
Future: federation via shared memory store

---

## 7. Backup Strategy

### 7.1 What to Backup

| Asset | Frequency | Method |
|-------|-----------|--------|
| Project source code | Continuous | git |
| `.ai/sessions/` | Daily | git or rsync |
| `.ai/audit/events.ndjson` | Daily | append-only, git ok |
| `.claude/retrospectives/` | Daily | git |
| `.memory/memory.db` | Weekly | sqlite backup |
| `.ai/policies/` | On change | git |
| `.ai/graphs/` | On change | git |

### 7.2 Backup Commands

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=~/backups/trinity/$(date +%Y%m%d)
mkdir -p "$BACKUP_DIR"

# Archive sessions
tar czf "$BACKUP_DIR/sessions.tar.gz" .ai/sessions/

# Archive audit (append-only, just copy)
cp .ai/audit/events.ndjson "$BACKUP_DIR/events.ndjson"

# Archive retros
tar czf "$BACKUP_DIR/retros.tar.gz" .claude/retrospectives/

# SQLite backup (online)
sqlite3 .memory/memory.db ".backup '$BACKUP_DIR/memory.db'"

# Sync to remote
rsync -av "$BACKUP_DIR/" backup-server:/backups/trinity/$(date +%Y%m%d)/
```

### 7.3 Restore

```bash
# Restore from backup
BACKUP_DIR=~/backups/trinity/20260428

cd /path/to/project

# Sessions
tar xzf "$BACKUP_DIR/sessions.tar.gz" -C .

# Audit
cp "$BACKUP_DIR/events.ndjson" .ai/audit/events.ndjson

# Retros
tar xzf "$BACKUP_DIR/retros.tar.gz" -C .

# Memory DB
cp "$BACKUP_DIR/memory.db" .memory/memory.db

# Verify integrity
sqlite3 .memory/memory.db "PRAGMA integrity_check"
trinity audit verify-chain  # check hash chain
```

---

## 8. Troubleshooting

### 8.1 AI doesn't know short codes

**Symptom:** ใส่ `lll` แล้ว AI ไม่เข้าใจ

**Cause:** `CLAUDE.md` (or `AGENTS.md`/`GEMINI.md`) ไม่มีหรือไม่มี inline short codes

**Fix:**
```bash
# Re-run bootstrap install
bash ~/code/trinity-bootstrap-pack/install.sh .

# Or manual:
diff CLAUDE.md ~/code/trinity-bootstrap-pack/templates/CLAUDE.md.template
# Merge missing sections
```

### 8.2 Tool returns invalid envelope

**Symptom:** `Error: Failed to parse tool response as JSON`

**Cause:** Tool not contract-compliant

**Fix:**
```bash
trinity-contract-test <tool-name>
# → Shows which tests fail

# Update tool to fix
```

### 8.3 Loop stuck (not progressing)

**Symptom:** `trinity loop status` shows same state for > 10 min

**Diagnose:**
```bash
trinity loop status --session=<id> --verbose
trinity loop history --session=<id> --tail=50
```

**Common causes:**
- `NEEDS_HUMAN` waiting (check escalation queue)
- Deadlock (all goals blocked)
- Infinite retry (check `failure_count`)

**Fix:**
```bash
# Force human escalation
trinity escalate --session=<id>

# Or terminate
trinity loop stop --session=<id> --reason="manual"
```

### 8.4 memory-cli search returns nothing

**Symptom:** `search` returns empty results despite indexed docs

**Diagnose:**
```bash
memory-cli --cmd "stats"
# → Check total_docs > 0

memory-cli --cmd "list --limit=5"
# → Check docs exist
```

**Common causes:**
- Index not built — run `index <path>`
- FTS query syntax — try simpler keywords
- Confidence filter — try `--confidence=draft`

**Fix:**
```bash
# Rebuild
memory-cli --cmd "reindex"

# Health check
memory-cli --health
```

### 8.5 Verifier always returns NEEDS_HUMAN

**Symptom:** Workflow stuck at human escalation

**Cause:** Rule too strict OR evidence missing

**Diagnose:**
```bash
verify-cli --cmd "verify --rule-set=<set> --verbose"
# → Shows which checks failed
```

**Fix:**
- Add evidence (artifacts/logs)
- Or relax rule (with audit)
- Or override with explicit human approval

### 8.6 Audit chain corrupted

**Symptom:** `trinity audit verify-chain` reports mismatch

**Cause:** Manual edit to `events.ndjson` or filesystem corruption

**Severity:** 🔴 HIGH — compliance issue

**Fix:**
```bash
# DO NOT auto-fix
# Instead:
1. Stop all running sessions
2. Investigate: which event corrupted?
3. Restore from backup if possible
4. Document incident in retro
5. Audit corrupted segment marked in audit log
```

---

## 9. Updates / Upgrades

### 9.1 Trinity OS Version Upgrade

```bash
# Check current version
trinity --version
# → trinity-kernel@2.0.0

# Pull updates
cd ~/code/trinity-kernel
git pull

# Run migration if needed
trinity migrate --from=2.0.0 --to=2.1.0 --dry-run
trinity migrate --from=2.0.0 --to=2.1.0 --apply

# Verify
trinity --version
trinity self-test
```

### 9.2 CLI Tool Upgrade

```bash
# Update individual tool
cd ~/code/browser-cli
git pull
npm install

# Run tests
node tests/harness.js
trinity-contract-test browser-cli

# Tools are shared — all projects benefit immediately
```

### 9.3 Bootstrap Pack Update

```bash
cd ~/code/trinity-bootstrap-pack
git pull

# For new projects: install.sh now uses latest

# For existing projects: manual diff
diff -r ~/code/trinity-bootstrap-pack/ai-docs/ /path/to/project/ai-docs/
# Selectively pull updates
```

---

## 10. Security & Permissions

### 10.1 File Permissions

```bash
# Sensitive files (gitignored, restricted)
chmod 600 .claude/settings.local.json
chmod 600 .ai/policies/*.yaml
chmod 700 .ai/audit/

# Audit log = append-only
chattr +a .ai/audit/events.ndjson  # Linux
# Or rely on git history for tamper detection
```

### 10.2 Tool Permissions

```bash
# Per-project Claude permissions
vim .claude/settings.local.json
# Use minimum necessary
# Audit: trinity tool permissions <project>
```

### 10.3 Credentials

```bash
# Never commit
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "credentials.json" >> .gitignore
echo ".memory/" >> .gitignore  # may contain sensitive search results

# Use environment variables
export TRINITY_DB_PASSWORD=$(security find-generic-password ...)
```

---

## 11. Performance Tips

### 11.1 memory-cli with Large DBs

```bash
# Optimize SQLite
memory-cli --cmd "vacuum"
memory-cli --cmd "analyze"

# Or
sqlite3 .memory/memory.db "VACUUM; ANALYZE;"
```

### 11.2 Speed Up Tool Calls

```bash
# Reuse REPL session for many calls
echo "search auth
get r_xyz
list --tag=critical
exit" | memory-cli --config configs/<upstream-project>-memory.json
```

### 11.3 Parallel Tool Execution

```bash
# Run multiple tools simultaneously
(memory-cli --cmd "search 'A'" > result-a.json) &
(memory-cli --cmd "search 'B'" > result-b.json) &
wait
```

---

## 12. Monitoring & Observability

### 12.1 Daily Health Check

```bash
#!/bin/bash
# trinity-health.sh — run daily

cd /path/to/project

# Tool health
for tool in browser-cli memory-cli verify-cli; do
  trinity tool health $tool
done

# Memory stats
memory-cli --cmd "stats"

# Audit chain integrity
trinity audit verify-chain

# Disk usage
du -sh .ai/audit/
du -sh .memory/

# Recent errors
grep -c "ERROR" .ai/audit/events.ndjson
```

### 12.2 Metrics to Track

| Metric | Healthy Range |
|--------|---------------|
| Memory DB size | < 1GB (FTS5) |
| events.ndjson size | < 100MB / month |
| Avg tool call duration | < 1000ms |
| Verify NEEDS_HUMAN rate | < 10% |
| Loop completion rate | > 80% |
| Retro per session | 1 |

### 12.3 Future: Dashboard (Phase 10+)

(Not in v0.1 — minimum stats only)

---

## 13. Disaster Recovery

### 13.1 Total Loss Scenario

If `.ai/` directory deleted:

```bash
# 1. Restore from backup
cp -r ~/backups/trinity/$(latest)/ai/. .ai/

# 2. Verify integrity
sqlite3 .memory/memory.db "PRAGMA integrity_check"
trinity audit verify-chain

# 3. Re-register tools
trinity tool list
# Re-add if missing

# 4. Smoke test
trinity loop status
memory-cli --cmd "stats"
```

### 13.2 Memory DB Corrupted

```bash
# Backup current
cp .memory/memory.db .memory/memory.db.corrupt

# Try integrity check
sqlite3 .memory/memory.db "PRAGMA integrity_check"

# If fixable
sqlite3 .memory/memory.db ".recover" | sqlite3 .memory/memory.db.new
mv .memory/memory.db.new .memory/memory.db

# If not, rebuild from source files
rm .memory/memory.db
memory-cli --cmd "index .claude/retrospectives/"
memory-cli --cmd "index ai-docs/real_lessons/"
```

### 13.3 Audit Chain Tampered

🔴 **CRITICAL** — compliance issue

```bash
# 1. Halt all sessions
trinity loop stop --all --reason="audit_compromised"

# 2. Identify tampered range
trinity audit verify-chain --verbose
# → Shows from_line and hash mismatch

# 3. Document in incident retro
retro-cli --cmd "create --type=incident --severity=critical"

# 4. Restore from backup
cp ~/backups/trinity/<date>/events.ndjson .ai/audit/events.ndjson

# 5. Continue with new chain (note in audit metadata)
```

---

## 14. Common Recipes

### 14.1 "Quick verify before deploy"

```bash
# Before deploy
verify-cli --cmd "verify --rule-set=deploy_check --session=$(cat .ai/sessions/active/.id)"

# If PASS → proceed
# If RETRY/NEEDS_HUMAN → don't deploy
```

### 14.2 "Find similar past bug"

```bash
memory-cli --cmd "search 'modal black screen' --type=retro --limit=5"
```

### 14.3 "Resume after laptop crash"

```bash
trinity loop list
# → shows interrupted sessions

trinity loop resume --session=<id>
```

### 14.4 "Audit who did what last week"

```bash
grep -l "$(date -d '1 week ago' +%Y-%m)" .ai/audit/events.ndjson \
  | xargs cat \
  | jq 'select(.event=="tool_call") | {ts, tool, command}'
```

### 14.5 "Migrate retros from old format"

```bash
find .claude/retrospectives -name "*.md" \
  | xargs -I {} retro-cli --cmd "migrate {} --dry-run"
# Review output, then:
find .claude/retrospectives -name "*.md" \
  | xargs -I {} retro-cli --cmd "migrate {}"
```

---

## 15. Workflow Examples

### 15.1 New Feature Development

```text
1. lll                          → see status
2. vvv "Add user dashboard"     → 5 questions, search past
3. nnn                          → plan with memory hints
4. (user approves plan)
5. gogogo                       → loop:
                                    → decompose to sub-goals
                                    → execute each
                                    → verify each
                                    → checkpoint
6. (verifier returns PASS)
7. rrr                          → retro + memory index
```

### 15.2 Bug Fix

```text
1. lll                          → status
2. vvv "Fix login redirect"     → search past similar bugs
                                  ↳ found: r_2025-11-25 (similar issue)
3. (read past retro for context)
4. nnn                          → plan with prior knowledge
5. gogogo                       → execute
6. verify-cli                   → run tests
7. (PASS)
8. rrr                          → memory updated
```

### 15.3 Production Deployment

```text
1. lll                          → status
2. vvv "Deploy v2.0.0"          → check prerequisites
3. nnn                          → deploy plan
4. (user approves CONSENSUS.md)
5. gogogo --graph=deploy        → uses deploy.yaml graph
                                  → BACKUP_DB
                                  → DEPLOY (human approval gate)
                                  → HEALTH_CHECK (verifier)
                                  → MONITOR (verifier)
6. (all PASS)
7. rrr                          → record metrics
```

---

## 16. Quick Reference Card

```text
╔═══════════════════════════════════════════════════════╗
║  TRINITY OS — QUICK REFERENCE                         ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  📋 Daily Commands                                    ║
║  ────────────────────────────────────────────────     ║
║  lll        Status (start of session)                 ║
║  vvv        Verify (5 questions, mandatory)           ║
║  nnn        Plan (after vvv)                          ║
║  gogogo     Execute (after plan approved)             ║
║  rrr        Retrospective (after task done)           ║
║  ccc        Checkpoint (auto)                         ║
║                                                       ║
║  🛠 Common Ops                                         ║
║  ────────────────────────────────────────────────     ║
║  trinity tool list                                    ║
║  trinity tool health <name>                           ║
║  trinity loop status                                  ║
║  trinity loop resume --session=<id>                   ║
║  memory-cli --cmd "search '...'"                      ║
║  verify-cli --cmd "verify --rule-set=..."             ║
║                                                       ║
║  🔧 Maintenance                                       ║
║  ────────────────────────────────────────────────     ║
║  trinity audit verify-chain                           ║
║  memory-cli --cmd "stats"                             ║
║  trinity self-test                                    ║
║                                                       ║
║  🚨 Emergency                                         ║
║  ────────────────────────────────────────────────     ║
║  trinity loop stop --all                              ║
║  trinity escalate --reason="..."                      ║
║  bash ~/backups/restore.sh <date>                     ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master spec
- [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) — Install scripts
- [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md) — <upstream-project> specific migration
- All other specs

## Changelog

- **v1.0.0 (2026-04-28)** — Initial deploy & operations guide
