# 🚨 Rollback Procedures - Emergency Recovery Guide

**Purpose**: Step-by-step guide for undoing failed deployments and recovering from errors
**When to Use**: Production issues, failed deployments, breaking changes
**Time to Recovery**: 5-15 minutes (if procedures followed)
**Version**: 1.0.0

---

## Emergency Severity Levels

| Level | Symbol | Description | Response Time |
|-------|--------|-------------|---------------|
| **CRITICAL** | 🔴 | Production down, data loss | Immediate (5m) |
| **HIGH** | 🟠 | Major feature broken, user impact | Urgent (15m) |
| **MEDIUM** | 🟡 | Minor issues, workaround exists | Standard (1h) |
| **LOW** | 🟢 | Cosmetic issues, no user impact | Scheduled |

---

## 🔴 CRITICAL: Production Down

### Symptoms
- Site unreachable (500/404 errors)
- Database connection failed
- Fatal PHP errors
- White screen of death

### Immediate Actions (5 minutes)

**Step 1: Stop Further Damage**
```bash
# If deployment in progress, STOP it
# Kill FTP/SFTP processes
killall lftp
pkill -f "sftp.*{{PROJECT_DOMAIN}}"
```

**Step 2: Identify Last Change**
```bash
# Check recent deployments
ls -lt deploy_prod_*/{{APP_ROOT}}/ | head -5

# Check git log
git log --oneline -5

# Check deployment log
tail -50 .claude/deployment.log
```

**Step 3: Rollback Immediately**

**Option A: Restore from deploy_prod backup**
```bash
# List recent prod folders
ls -d deploy_prod_*/ | sort -r | head -3

# Identify working version (previous date)
GOOD_VERSION="deploy_prod_25_11_2025"
BAD_VERSION="deploy_prod_08_12_2025"

# Deploy good version to production
cd ${GOOD_VERSION}
./scripts/{{DEPLOY_SCRIPT}} {{CONTROLLER_DIR}}/file.php {{PUBLIC_DIR}}/{{CONTROLLER_DIR}}/file.php {{PROJECT_DOMAIN}}
```

**Option B: Restore from git**
```bash
# Find last working commit
git log --oneline --graph -10

# Checkout specific file
git checkout <commit-hash> -- path/to/file.php

# Deploy immediately
```

**Option C: Restore from FTP backup** (if available)
```bash
# Connect via FileZilla
# Server: 139.162.16.206
# User: yai@{{PROJECT_DOMAIN}}
# Navigate to {{PUBLIC_BACKUP}}/ (if exists)
# Download broken file
# Check if it's the working version
# Upload to {{PUBLIC_DIR}}/ to restore
```

**Step 4: Verify Recovery**
```bash
# Test production URL
curl -I https://{{PROJECT_DOMAIN}}/backend/note

# Check for 200 OK
# If still broken, try Option B or C
```

**Step 5: Document Incident**
```bash
# Create incident report
cat > .claude/incidents/$(date +%Y-%m-%d_%H-%M)_production_down.md << 'EOF'
# Incident: Production Down

**Time**: $(date)
**Severity**: CRITICAL
**What happened**: [describe]
**Root cause**: [analysis]
**Rollback action**: [which option used]
**Recovery time**: [minutes]
**Lessons learned**: [key points]
EOF
```

---

## 🟠 HIGH: Major Feature Broken

### Symptoms
- Feature returns errors (but site works)
- User reports functionality broken
- Database queries failing
- UI elements missing

### Recovery Actions (15 minutes)

**Step 1: Assess Impact**
```bash
# Who is affected?
# - All users? → CRITICAL (escalate)
# - Specific user type? → HIGH (continue)
# - Single user? → MEDIUM (deprioritize)

# Check error logs
tail -100 ${LOGS_DIR}/error_log
```

**Step 2: Quick Fix or Rollback?**

**Decision Tree**:
```
Error is simple (typo, missing ;)?
  → YES: Quick fix (5m)
  → NO: Rollback (10m)

Can identify exact file/line?
  → YES: Quick fix
  → NO: Rollback to last known good
```

**Quick Fix Flow**:
```bash
# 1. Fix locally in deploy_dev
cd ${DEPLOY_ROOT}
# Edit file.php (fix typo/error)

# 2. Syntax check
php -l file.php

# 3. Deploy to dev first
./scripts/{{DEPLOY_SCRIPT}} file.php {{PUBLIC_DIR}}/... {{PROJECT_DOMAIN}}

# 4. Test on dev
curl https://{{PROJECT_DOMAIN}}/backend/...

# 5. If OK, deploy to prod
./scripts/{{DEPLOY_SCRIPT}} file.php {{PUBLIC_DIR}}/... {{PROJECT_DOMAIN}}
```

**Rollback Flow**:
```bash
# 1. Identify broken file(s)
git diff HEAD~1 --name-only

# 2. Restore from previous commit
git show HEAD~1:path/to/file.php > file.php

# 3. Deploy restored version
./scripts/{{DEPLOY_SCRIPT}} file.php {{PUBLIC_DIR}}/... {{PROJECT_DOMAIN}}

# 4. Verify fix
# Test functionality manually
```

**Step 3: User Communication**
```bash
# If users affected, notify:
# - Estimate fix time
# - Workaround if available
# - Apologize for inconvenience
```

---

## 🟡 MEDIUM: Minor Issues

### Symptoms
- UI glitches (cosmetic)
- Performance degradation (minor)
- Non-critical warnings in logs

### Recovery Actions (1 hour)

**Step 1: Document Issue**
```bash
# Create issue tracking
cat > .claude/issues/issue_$(date +%Y%m%d_%H%M).md << 'EOF'
# Issue: [Title]
**Severity**: MEDIUM
**Symptoms**: [describe]
**Affected**: [users/features]
**Workaround**: [if any]
EOF
```

**Step 2: Investigate Root Cause**
```bash
# Use vvv protocol
# 1. Search for related code
rg "function_name" --type php

# 2. Check recent changes
git log -p --since="1 day ago" -- path/to/file

# 3. Review retrospectives
rg "similar_keyword" .claude/retrospectives/
```

**Step 3: Plan Fix**
```bash
# Follow standard workflow:
# lll → vvv → nnn → gogogo → rrr

# Don't rush - this is MEDIUM priority
# Test thoroughly on dev before prod
```

**Step 4: Schedule Deployment**
```bash
# Choose low-traffic time
# Document in deployment plan
# Get user approval
# Execute during scheduled window
```

---

## Git Rollback Strategies

### Rollback Single File
```bash
# Restore specific file from commit
git show <commit-hash>:path/to/file.php > file.php

# Or use checkout
git checkout <commit-hash> -- path/to/file.php

# Deploy restored file
./scripts/{{DEPLOY_SCRIPT}} file.php /remote/path server
```

---

### Rollback Multiple Files
```bash
# List changed files
git diff --name-only HEAD~1

# Restore all
git checkout HEAD~1 -- file1.php file2.php file3.php

# Or restore entire directory
git checkout HEAD~1 -- {{CONTROLLER_DIR}}/backend/
```

---

### Rollback Entire Commit
```bash
# Create revert commit (recommended)
git revert <commit-hash>

# This creates new commit that undoes changes
# Safer than reset (preserves history)

# Deploy reverted files
```

---

### Reset to Previous State (DANGEROUS)
```bash
# ⚠️ USE ONLY IF: Not pushed to remote yet
# ❌ NEVER USE IF: Already pushed (use revert instead)

# Reset to previous commit
git reset --hard HEAD~1

# ⚠️ This DESTROYS uncommitted changes
# Make sure you have backup first!
```

---

## Deployment Rollback

### Two-Server Rollback

**Scenario**: Deployed to prod, found issues

```bash
# Step 1: Identify last working version
# Check deploy_prod folders
ls -dt deploy_prod_*/ | head -3

# Step 2: Re-deploy old version
cd deploy_prod_25_11_2025  # Last known good

# Step 3: Upload to production
./scripts/{{DEPLOY_SCRIPT}} {{APP_ENTRY}} {{PUBLIC_DIR}}/{{APP_ENTRY}} {{PROJECT_DOMAIN}}

# Step 4: Verify
curl -I https://{{PROJECT_DOMAIN}}/backend/...
# Should return 200 OK
```

---

### FTP/SFTP Rollback

**Scenario**: File corrupted during upload

```bash
# Option 1: Download server backup (if exists)
# Via FileZilla:
# - Connect to server
# - Check {{PUBLIC_BACKUP}}/ directory
# - Download working version
# - Upload to {{PUBLIC_DIR}}/ (restore)

# Option 2: Re-upload from local
cd deploy_prod_25_11_2025  # Known good version
./scripts/{{DEPLOY_SCRIPT}} file.php {{PUBLIC_DIR}}/... {{PROJECT_DOMAIN}}

# Option 3: Restore from git
git show HEAD~1:file.php > temp_restore.php
# Upload temp_restore.php to server
```

---

## Database Rollback

### Schema Changes Rollback

**Before Running Migration**:
```bash
# ALWAYS create rollback SQL first
cat > sql/009_add_column_rollback.sql << 'SQL'
-- Rollback for migration 009
START TRANSACTION;

ALTER TABLE `order` DROP COLUMN `shipping_fee_by_qty`;

COMMIT;
SQL
```

**After Bad Migration**:
```bash
# Run rollback SQL
mysql -u user -p database_name < sql/009_add_column_rollback.sql

# Verify
mysql -u user -p database_name -e "DESCRIBE \`order\`"
```

---

### Data Changes Rollback

**If you have backup**:
```bash
# Restore from mysqldump
mysql -u user -p database_name < backups/backup_2025-12-18.sql

# Or restore specific table
mysql -u user -p database_name < backups/table_order.sql
```

**If no backup** (Prevention):
```bash
# Before destructive UPDATE/DELETE:
# 1. Create backup
mysqldump -u user -p database_name table_name > backup_before_change.sql

# 2. Run UPDATE with WHERE clause
# 3. Verify results
# 4. If wrong, restore from backup
```

---

## File-Level Recovery

### Restore from deploy_* Folders

```bash
# Scenario: Accidentally edited production_dir instead of deploy_dir

# Step 1: Identify correct source
ls -la application_25_11_2025/path/to/file.php
ls -la deploy_dev_25_11_2025/path/to/file.php

# Step 2: Copy correct version
cp application_25_11_2025/path/to/file.php \
   deploy_dev_25_11_2025/path/to/file.php

# Step 3: Verify
diff application_25_11_2025/file.php deploy_dev_25_11_2025/file.php
# Should show no differences (or expected differences only)
```

---

### Restore from Git History

```bash
# Find when file was last good
git log --oneline --follow path/to/file.php | head -10

# View specific version
git show <commit-hash>:path/to/file.php

# Restore it
git show <commit-hash>:path/to/file.php > path/to/file.php

# Or use checkout
git checkout <commit-hash> -- path/to/file.php
```

---

## Emergency State Checklist

### When Production is Broken

```markdown
## Emergency Rollback Checklist

**Incident Time**: _____________
**Severity**: 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM
**Reporter**: _____________

### Immediate Actions (< 5 minutes)
- [ ] Stop ongoing deployments (kill FTP processes)
- [ ] Identify last working state (git log, deploy folders)
- [ ] Notify users (if customer-facing)
- [ ] Assign incident lead

### Rollback Execution (< 10 minutes)
- [ ] Choose rollback strategy:
  - [ ] Option A: Restore from deploy_prod_* folder
  - [ ] Option B: Restore from git (previous commit)
  - [ ] Option C: Restore from FTP backup
- [ ] Execute rollback (deploy old version)
- [ ] Verify recovery (curl, manual test)
- [ ] Confirm with users (if applicable)

### Post-Recovery (< 30 minutes)
- [ ] Document what happened (incident report)
- [ ] Root cause analysis (what went wrong)
- [ ] Create retrospective (.claude/retrospectives/)
- [ ] Update SAFETY_GATES.md if new pattern found
- [ ] Schedule post-mortem meeting

### Prevention (Next 24 hours)
- [ ] Review deployment procedure
- [ ] Add automated checks (if missing)
- [ ] Update documentation
- [ ] Test rollback procedure (dry-run)
```

---

## Rollback Decision Tree

```
Is production completely down?
├─ YES → 🔴 CRITICAL
│  ├─ Use Option A (deploy_prod_* folder) - FASTEST
│  └─ Verify in < 5 minutes
│
└─ NO → Is major feature broken?
   ├─ YES → 🟠 HIGH
   │  ├─ Simple fix? → Quick patch (15m)
   │  └─ Complex? → Rollback full (10m)
   │
   └─ NO → 🟡 MEDIUM or 🟢 LOW
      └─ Follow standard workflow (no emergency)
```

---

## Recovery Patterns (From Real Incidents)

### Pattern 1: Wrong File Uploaded (2025-12-01)

**What Happened**: Deployed edited file, got 404

**Root Cause**: File corrupted during FTP upload (error 451)

**Rollback**:
```bash
# 1. Restore from deploy folder (previous version)
cd deploy_25_11_2025
./scripts/{{DEPLOY_SCRIPT}} {{CONTROLLER_DIR}}/backend/note.php \
  {{PUBLIC_DIR}}/{{CONTROLLER_DIR}}/backend/note.php \
  {{PROJECT_DOMAIN}}

# 2. Verify file size matches
# Local: 92,765 bytes
# Remote: Should be 92,765 bytes (via lftp ls -l)

# 3. Test immediately
curl https://{{PROJECT_DOMAIN}}/backend/note
```

**Prevention**: Always verify file size after upload

---

### Pattern 2: SQL Migration Failed (Hypothetical)

**What Happened**: Ran ALTER TABLE, lost data

**Rollback**:
```bash
# 1. Run rollback SQL (prepared beforehand)
mysql -u user -p database < sql/migration_XXX_rollback.sql

# 2. Verify schema
mysql -u user -p database -e "DESCRIBE table_name"

# 3. Check data integrity
mysql -u user -p database -e "SELECT COUNT(*) FROM table_name"
```

**Prevention**:
- Always write rollback SQL BEFORE running migration
- Test on dev database first
- Backup before migration

---

### Pattern 3: Config File Error (2025-11-XX)

**What Happened**: Changed config.php, broke authentication

**Rollback**:
```bash
# 1. Config files are CRITICAL - restore immediately
git show HEAD~1:{{CONFIG_DIR}}/config.php > \
  deploy_dev/{{CONFIG_DIR}}/config.php

# 2. Deploy
./scripts/{{DEPLOY_SCRIPT}} {{CONFIG_DIR}}/config.php \
  {{PUBLIC_DIR}}/{{CONFIG_DIR}}/config.php \
  {{PROJECT_DOMAIN}}

# 3. Clear server cache (if applicable)
# SSH to server and rm -rf {{APP_ROOT}}/cache/*

# 4. Verify auth works
# Test login manually
```

**Prevention**: NEVER edit config files without backup

---

## Prevention: Pre-Deployment Checklist

### Before ANY Production Deployment

```markdown
## Pre-Deployment Safety Checklist

### Preparation
- [ ] Tested on dev server ({{PROJECT_DOMAIN}}) ✅
- [ ] User verified functionality ✅
- [ ] Syntax check passed (php -l) ✅
- [ ] Git committed with clear message ✅
- [ ] Identified rollback strategy ✅

### Backup
- [ ] Backup current production file:
  ```bash
  # Download from server first
  lftp -c "open {{PROJECT_DOMAIN}}; get {{PUBLIC_DIR}}/path/file.php -o backup_$(date +%s).php"
  ```
- [ ] OR: Verify deploy_prod_* has current version
- [ ] Database backup (if schema changes):
  ```bash
  mysqldump -u user -p database table > backup_$(date +%s).sql
  ```

### Deployment
- [ ] Use correct deploy_prod_* folder (not deploy_dev!)
- [ ] Double-check server ({{PROJECT_DOMAIN}}, not {{PROJECT_DOMAIN}})
- [ ] Verify file size after upload
- [ ] Test immediately after deploy

### Post-Deployment
- [ ] Verify via curl/manual test
- [ ] Check error logs for new errors
- [ ] Monitor for 15 minutes
- [ ] Document in deployment log
```

---

## Rollback Tools Reference

### Git Commands
```bash
# View file history
git log --follow path/to/file.php

# Show specific version
git show <commit>:file.php

# Restore from commit
git checkout <commit> -- file.php

# Revert commit (safe)
git revert <commit>

# Reset (dangerous!)
git reset --hard <commit>  # Only if not pushed!
```

---

### FTP/SFTP Commands
```bash
# Download backup
lftp -c "open server; get /path/file.php -o backup.php"

# Upload restore
lftp -c "open server; put file.php -o /path/file.php"

# Verify file size
lftp -c "open server; ls -l /path/file.php"
```

---

### Database Commands
```bash
# Backup table
mysqldump -u user -p db table > backup.sql

# Restore table
mysql -u user -p db < backup.sql

# Rollback migration
mysql -u user -p db < migration_rollback.sql
```

---

## Post-Rollback Actions

### Mandatory Follow-up

1. **Create Retrospective**
```bash
# Use rrr command
# Document:
# - What failed
# - Why it failed
# - How we recovered
# - How to prevent
```

2. **Update Safety Gates**
```bash
# If new failure pattern discovered:
# Add to SAFETY_GATES.md
# Update enforce.sh with new check
```

3. **Review Deployment Procedure**
```bash
# Did we skip any steps?
# - vvv before nnn? ✅
# - Test on dev first? ✅
# - User verification? ✅
# - Backup before deploy? ✅
```

4. **Test Rollback Procedure**
```bash
# Dry-run rollback on dev:
# 1. Deploy "broken" version to dev
# 2. Practice rollback procedure
# 3. Verify rollback works
# 4. Document timing
```

---

## Emergency Contacts

### When to Escalate

**Escalate to User If**:
- Cannot identify root cause (30+ min)
- Rollback attempts failed (2+ attempts)
- Data integrity concerns
- Need production database access

**Escalate to Team If**:
- Multiple AI agents needed (complex issue)
- Architectural decision required
- Business logic unclear

---

## Rollback Verification

### How to Confirm Rollback Successful

```bash
# 1. Functionality Test
# - Test broken feature manually
# - Should work now

# 2. Error Log Check
tail -50 ${LOGS_DIR}/error_log
# No new errors related to rolled-back change

# 3. User Confirmation
# - Ask user to verify
# - Get explicit "OK" before closing incident

# 4. Monitoring
# - Watch for 30 minutes
# - Ensure no related errors appear
```

---

## Prevention: Backup Strategy

### What to Backup, When

**Before Every Production Deploy**:
- ✅ Files being replaced (download from server)
- ✅ Git commit current state
- ✅ deploy_prod_* folder has current version

**Before Database Changes**:
- ✅ Full database dump (if small, <100MB)
- ✅ Affected tables only (if large database)
- ✅ Test data set (for rollback testing)

**Weekly/Monthly**:
- ✅ Full server backup (if possible)
- ✅ Git repository backup (push to GitHub/GitLab)
- ✅ Documentation backup (.claude/ folder)

---

## Rollback Time Estimates

| Scenario | Best Case | Worst Case | Average |
|----------|-----------|------------|---------|
| Single file restore | 2m | 10m | 5m |
| Multiple files restore | 5m | 20m | 10m |
| Database rollback | 3m | 30m | 15m |
| Full system rollback | 10m | 60m | 30m |
| Unknown issue investigation | 15m | 180m | 45m |

**Goal**: Keep all rollbacks < 15 minutes with proper preparation

---

## Summary

**Key Principles**:
1. **Stop First**: Halt damage before investigating
2. **Known Good State**: Always have identifiable restore point
3. **Document Everything**: Incident report mandatory
4. **Learn & Prevent**: Update safety gates after recovery
5. **Practice Rollbacks**: Test procedures on dev quarterly

**Quick Reference**:
```
🔴 CRITICAL → Restore from deploy_prod_* (5m)
🟠 HIGH → Quick fix or git rollback (15m)
🟡 MEDIUM → Standard workflow (1h)
```

---

**Version**: 1.0.0
**Created**: 2025-12-18
**By**: Claude (AI Trinity - Safety Officer)
**Based On**: Real incidents from .claude/retrospectives/
**Status**: Ready for use
