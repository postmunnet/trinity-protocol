# 🛡️ Safety Gates - Enforcement Levels

**Purpose**: Define safety rules with automated enforcement levels
**For**: AI agents and `scripts/enforce.sh` automation
**Updated**: 2025-12-18
**Version**: 2.0.0 (Enforcement-Ready)

---

## Enforcement Legend

| Level | Symbol | Behavior | Script Action |
|-------|--------|----------|---------------|
| **BLOCKER** | 🔴 | Must comply or stop | `exit 1` (halt execution) |
| **WARNING** | 🟡 | Should comply, continue with caution | Print warning, continue |
| **MANUAL** | 🔵 | Cannot automate, requires human judgment | Document only (vvv protocol) |

---

## 🔴 BLOCKER Gates (Script MUST Exit)

### Gate B1: No Direct Production Edits
**Enforcement**: 🔴 BLOCKER
**Trigger**: Before any file write operation
**Rule**: Never write to production/snapshot directories

**Check**:
```bash
# enforce.sh checks:
if [[ "$target_path" =~ application_[0-9]{2}_[0-9]{2}_[0-9]{4}/ ]]; then
  echo "🔴 BLOCKER: Cannot edit production snapshot"
  exit 1
fi
```

**Examples**:
- ❌ `application_25_11_2025/` (production snapshot - READ ONLY)
- ❌ Direct edit in `deploy_prod_*/` (production configs)
- ✅ `deploy_dev_*/` (safe working directory)

**Penalty**: Script exits immediately

---

### Gate B2: No Force Push to Main
**Enforcement**: 🔴 BLOCKER
**Trigger**: Before `git push` operations
**Rule**: Never force push to main/master branches

**Check**:
```bash
# enforce.sh checks:
if git rev-parse --abbrev-ref HEAD | grep -qE '^(main|master)$'; then
  if [[ "$git_args" =~ --force|-f ]]; then
    echo "🔴 BLOCKER: Force push to main branch blocked"
    exit 1
  fi
fi
```

**Examples**:
- ❌ `git push --force origin main`
- ❌ `git push -f origin master`
- ✅ `git push origin feature/branch`

**Penalty**: Script exits, push aborted

---

### Gate B3: SQL Injection Prevention
**Enforcement**: 🔴 BLOCKER
**Trigger**: Before committing PHP files with database queries
**Rule**: No raw user input in SQL queries

**Check**:
```bash
# enforce.sh checks for dangerous patterns:
rg -n '\$_(GET|POST|REQUEST)\[.*?\].*?->query\(' --type php
rg -n '"SELECT.*?\$_(GET|POST|REQUEST)' --type php
```

**Examples**:
- ❌ `$this->db->query("SELECT * WHERE id = " . $_GET['id'])`
- ❌ `$sql = "DELETE FROM users WHERE name = '{$_POST['name']}'"`
- ✅ `$this->db->where('id', $this->input->get('id'))`
- ✅ `$this->db->query($sql, [$id, $name])` (prepared statements)

**Penalty**: Commit blocked until fixed

---

### Gate B4: Missing File Verification (vvv)
**Enforcement**: 🔴 BLOCKER
**Trigger**: Before planning (nnn) phase
**Rule**: Evidence of file/function existence required
**Binding contract**: [../protocols/VVV_CONTRACT.md](../protocols/VVV_CONTRACT.md) (v1.0, 2026-04-23)
**Template**: [../templates/vvv_report_v1.md](../templates/vvv_report_v1.md)
**Examples**: [../templates/vvv_report_v1_examples.md](../templates/vvv_report_v1_examples.md)

**Check**:
```bash
# enforce.sh validates conversation contains:
grep -q "grep.*function_name" conversation.log || exit 1
grep -q "Found at:" conversation.log || exit 1
```

**Examples**:
- ❌ Plan to edit `user_model.php` without verifying it exists
- ✅ Run `rg "class User_model" --type php` → Found at line 15
- ✅ Document: "Verified: models/User_model.php:15"

**Penalty**: AI must run vvv before proceeding to nnn

**Note**: This is partially MANUAL (requires AI to execute vvv) but can be validated programmatically

---

## 🟡 WARNING Gates (Continue with Caution)

### Gate W1: Large File Changes
**Enforcement**: 🟡 WARNING
**Trigger**: Before committing files >500 lines changed
**Rule**: Review recommended for large changes

**Check**:
```bash
# enforce.sh checks git diff:
if git diff --cached --stat | awk '{if($1 > 500) exit 1}'; then
  echo "🟡 WARNING: Large file changes detected (>500 lines)"
  echo "Consider: Break into smaller commits"
fi
```

**Action**: Prints warning, allows commit to proceed

---

### Gate W2: Missing Code Comments
**Enforcement**: 🟡 WARNING
**Trigger**: Before committing complex functions (>30 lines, no docblock)
**Rule**: Functions should have documentation

**Check**:
```bash
# enforce.sh checks for functions without docblocks:
rg -U 'function \w+\([^)]*\)\s*\{[^*]{30,}' --type php
```

**Action**: Warns developer, doesn't block

---

### Gate W3: Deprecated Pattern Usage
**Enforcement**: 🟡 WARNING
**Trigger**: Before committing code with old patterns
**Rule**: Prefer modern alternatives

**Check**:
```bash
# enforce.sh checks for deprecated patterns:
rg 'mysql_query|mysql_connect' --type php  # Old MySQL
rg '\$this->load->database\(\)' --type php  # Should use autoload
```

**Examples**:
- ⚠️ `mysql_query()` → Use `$this->db->query()`
- ⚠️ Manual database loading → Use autoload in config

**Action**: Warns but allows (legacy code may exist)

---

### Gate W4: Hardcoded Paths in New Code
**Enforcement**: 🟡 WARNING
**Trigger**: Before committing new files
**Rule**: Use environment variables for paths

**Check**:
```bash
# enforce.sh detects hardcoded paths in diffs:
git diff --cached | rg 'deploy_[0-9]{2}_[0-9]{2}_[0-9]{4}'
git diff --cached | rg 'application_[0-9]{2}_[0-9]{2}_[0-9]{4}'
```

**Action**: Warns to use `${DEPLOY_ROOT}` instead

---

## 🔵 MANUAL Gates (Human Judgment Required)

### Gate M1: Business Logic Verification
**Enforcement**: 🔵 MANUAL (vvv protocol)
**Trigger**: Before implementing calculations, pricing, inventory logic
**Rule**: Verify requirements with user first

**Why Manual**:
- Cannot automate understanding of business rules
- Requires domain knowledge
- May have edge cases only user knows

**Process**:
1. Ask clarifying questions (5 mandatory questions)
2. Get examples from user
3. Document understanding
4. Confirm before implementing

**Examples**:
- Shipping fee calculations
- Stock weighted averages
- Discount logic
- Tax computations

---

### Gate M2: User Impact Assessment
**Enforcement**: 🔵 MANUAL
**Trigger**: Before breaking changes to UI/UX
**Rule**: Consider user workflow disruption

**Why Manual**:
- UI/UX changes need user validation
- Accessibility considerations
- Cultural/language nuances (Thai vs English)

**Process**:
1. Identify affected users
2. Document changes clearly
3. Get user approval before deploy
4. Test on dev first (Two-Server workflow)

---

### Gate M3: Performance Impact
**Enforcement**: 🔵 MANUAL
**Trigger**: Before database schema changes, adding indexes, query modifications
**Rule**: Consider performance implications

**Why Manual**:
- Performance depends on data volume (unknown to AI)
- Production load patterns
- Index strategy requires DB knowledge

**Process**:
1. Explain query changes
2. Mention potential impacts (positive/negative)
3. Recommend testing on staging
4. Let user decide

---

### Gate M4: Third-Party Integration
**Enforcement**: 🔵 MANUAL
**Trigger**: Before calling external APIs, payment gateways, shipping providers
**Rule**: Verify API credentials, rate limits, contracts

**Why Manual**:
- Credentials not in codebase
- Rate limits vary per account
- Contract terms AI cannot know

**Process**:
1. Ask for API documentation
2. Verify credentials available
3. Check rate limits
4. Test in sandbox first

---

## 📋 Enforcement Matrix

| Gate ID | Name | Level | Automated | Script Check |
|---------|------|-------|-----------|--------------|
| B1 | No Production Edits | 🔴 BLOCKER | ✅ Yes | Path regex match |
| B2 | No Force Push Main | 🔴 BLOCKER | ✅ Yes | Git branch + args |
| B3 | SQL Injection Prevention | 🔴 BLOCKER | ✅ Yes | Regex patterns |
| B4 | vvv Before nnn | 🔴 BLOCKER | ⚠️ Partial | Conversation log validation |
| W1 | Large File Changes | 🟡 WARNING | ✅ Yes | Git diff stats |
| W2 | Missing Comments | 🟡 WARNING | ✅ Yes | Function docblock check |
| W3 | Deprecated Patterns | 🟡 WARNING | ✅ Yes | Pattern matching |
| W4 | Hardcoded Paths | 🟡 WARNING | ✅ Yes | Path regex in diff |
| M1 | Business Logic | 🔵 MANUAL | ❌ No | Human vvv protocol |
| M2 | User Impact | 🔵 MANUAL | ❌ No | Human judgment |
| M3 | Performance | 🔵 MANUAL | ❌ No | Human assessment |
| M4 | Third-Party API | 🔵 MANUAL | ❌ No | Human verification |

---

## Automation Patterns for enforce.sh

### Pattern Detection (Regex)

**For BLOCKER gates**:
```bash
# B1: Production directory detection
PROD_PATTERN='application_[0-9]{2}_[0-9]{2}_[0-9]{4}/'

# B3: SQL injection patterns
SQL_INJECTION_PATTERNS=(
  '\$_(GET|POST|REQUEST|COOKIE)\[.*?\].*?->query\('
  '"SELECT.*?\$_(GET|POST|REQUEST)'
  '"INSERT.*?\$_(GET|POST|REQUEST)'
  '"UPDATE.*?\$_(GET|POST|REQUEST)'
  '"DELETE.*?\$_(GET|POST|REQUEST)'
)

# B4: vvv evidence patterns
VVV_EVIDENCE_PATTERNS=(
  'grep.*function'
  'rg.*class'
  'Found at:.*line [0-9]+'
  'Verified:.*\.php:[0-9]+'
)
```

**For WARNING gates**:
```bash
# W3: Deprecated function patterns
DEPRECATED_PATTERNS=(
  'mysql_query'
  'mysql_connect'
  '\$HTTP_GET_VARS'
  'ereg\('
)

# W4: Hardcoded path patterns
HARDCODED_PATH_PATTERNS=(
  'deploy_[0-9]{2}_[0-9]{2}_[0-9]{4}'
  'application_[0-9]{2}_[0-9]{2}_[0-9]{4}'
  '<user-home>/]+/.*{{PROJECT_NAME}}'
)
```

---

## Exit Codes for enforce.sh

```bash
# Success
exit 0  # All gates passed

# BLOCKER violations
exit 1  # One or more BLOCKER gates failed

# WARNING only
exit 0  # Warnings printed but execution continues

# Usage errors
exit 2  # Script misconfiguration or invalid usage
```

---

## Usage in Workflow

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

./scripts/enforce.sh --mode=pre-commit

# Exit code 1 = BLOCKER → abort commit
# Exit code 0 = Pass or WARNING only → allow commit
```

---

### CI/CD Pipeline
```bash
# In CI pipeline
./scripts/enforce.sh --mode=ci --strict

# In strict mode:
# - All WARNINGS become BLOCKERS
# - Exit 1 on any violation
```

---

### Manual Pre-flight Check
```bash
# Before starting work (lll command integration)
./scripts/enforce.sh --mode=pre-flight

# Checks:
# - File structure intact
# - No forbidden patterns in recent changes
# - Config files valid
```

---

## Gate Severity Reference

### When to Use BLOCKER 🔴
**Criteria**:
- Security vulnerability (SQL injection, XSS)
- Data loss risk (delete without backup)
- Production safety (force push, direct prod edits)
- Compliance requirement (vvv before nnn)

**Philosophy**: "If this fails, everything fails"

---

### When to Use WARNING 🟡
**Criteria**:
- Code quality issues (missing comments)
- Maintainability concerns (deprecated patterns)
- Best practices (hardcoded paths)
- Non-breaking improvements

**Philosophy**: "Should fix, but won't break production"

---

### When to Use MANUAL 🔵
**Criteria**:
- Requires domain knowledge (business logic)
- Needs human judgment (UX decisions)
- Context-dependent (performance, third-party)
- Cannot be rule-based (varies per situation)

**Philosophy**: "AI cannot know this - ask human"

---

## Additional Safety Rules

### Deployment Safety

**[🔴 BLOCKER] Two-Server Workflow**
```bash
# Must deploy to dev before prod
# Check: Has ${DEPLOY_ROOT} been deployed to DEV_URL?
# If not → exit 1
```

**[🔴 BLOCKER] Test Before Production**
```bash
# Production deploy requires dev testing confirmation
# Check: User confirmation "Tested on dev? [y/N]"
# If N → exit 1
```

**[🟡 WARNING] Missing Backup**
```bash
# Recommend backup before deployment
# Check: Does backup of target file exist?
# If not → warn "Consider backing up first"
```

---

### Code Quality

**[🔴 BLOCKER] Syntax Errors**
```bash
# PHP files must pass syntax check
php -l "${file}" || exit 1
```

**[🟡 WARNING] No Error Handling**
```bash
# Database operations should have try-catch
rg 'db->query.*\);\s*$' --type php  # No error check after query
# Warn but allow (legacy code may not have)
```

**[🟡 WARNING] Magic Numbers**
```bash
# Hardcoded numbers in business logic
rg '\b(if|while|for).*[0-9]{3,}' --type php
# Warn to use constants
```

---

### Security

**[🔴 BLOCKER] Credentials in Code**
```bash
# No passwords, API keys in committed code
rg -i 'password\s*=\s*["\047](?!{{).+["\047]' --type php
rg -i 'api[_-]?key\s*=\s*["\047](?!{{).+["\047]' --type php
# Exit 1 if found
```

**[🔴 BLOCKER] Direct Superglobal Usage**
```bash
# Must use input->get() / input->post(), not $_GET / $_POST directly
rg '\$_(GET|POST|REQUEST|COOKIE)\[' --type php
# Exception: Framework core files only
```

**[🟡 WARNING] Weak Session Settings**
```bash
# session.cookie_httponly should be true
rg 'ini_set.*session\.cookie_httponly.*false' --type php
```

---

### Git Safety

**[🔴 BLOCKER] Large Binary Files**
```bash
# No files >10MB in git
git diff --cached --name-only | while read f; do
  if [[ -f "$f" ]] && [[ $(stat -f%z "$f") -gt 10485760 ]]; then
    echo "🔴 BLOCKER: File too large: $f (>10MB)"
    exit 1
  fi
done
```

**[🟡 WARNING] Sensitive Files**
```bash
# Warn if committing .env, credentials, etc.
git diff --cached --name-only | rg -q '\.(env|credentials|secrets)$'
# Warn but allow (may be templates)
```

---

## Integration with vvv Protocol

### BLOCKER B4: vvv Before nnn (Hybrid Enforcement)

**Automated Part** (enforce.sh):
```bash
# Check conversation history for vvv evidence:
REQUIRED_EVIDENCE=(
  "grep -r"      # File search performed
  "Found at:"    # Location identified
  "line [0-9]+"  # Line number specified
)

for pattern in "${REQUIRED_EVIDENCE[@]}"; do
  if ! grep -q "$pattern" .claude/conversation.log; then
    echo "🔴 BLOCKER: Missing vvv evidence for '$pattern'"
    exit 1
  fi
done
```

**Manual Part** (AI responsibility):
- AI must actually run grep/rg commands
- AI must document findings
- Cannot automate "understanding" - only validate "execution"

**Hybrid Approach**:
- Script validates evidence exists
- Human (or AI) produces the evidence
- Best of both worlds

---

## Override Mechanism

### Emergency Override (Use Sparingly)

```bash
# For BLOCKER gates only, in emergency situations:
./scripts/enforce.sh --override=B1 --reason="Hotfix approved by CTO"

# Logs override to audit trail:
# [2025-12-18 19:45] OVERRIDE B1 by user (reason: Hotfix approved by CTO)
```

**Restrictions**:
- Must provide `--reason`
- Logged to `.claude/violations.log`
- BLOCKER overrides count toward monthly quota (max 3/month)
- Requires post-mortem retrospective

**Cannot Override**:
- B3 (SQL Injection) - NEVER
- B2 (Force Push Main) - NEVER
- B4 (vvv Protocol) - NEVER (fundamental to workflow)

---

## Enforcement in Practice

### Example: Pre-commit Flow

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running safety gates..."

# Run enforcement script
./scripts/enforce.sh --mode=pre-commit

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 1 ]]; then
  echo ""
  echo "❌ Commit BLOCKED by safety gates"
  echo "Fix violations above and try again"
  echo ""
  exit 1
elif [[ $EXIT_CODE -eq 0 ]]; then
  echo "✅ Safety gates passed"
  exit 0
else
  echo "⚠️ Enforcement script error"
  exit $EXIT_CODE
fi
```

---

### Example: AI Workflow Integration

**Step 0: Pre-flight** (lll command)
```bash
# AI runs at session start:
./scripts/enforce.sh --mode=pre-flight

# Checks:
# - File structure intact?
# - No violations in last commit?
# - Config files valid?
```

**Step 1: After vvv** (Before nnn)
```bash
# Validate vvv evidence exists:
./scripts/enforce.sh --mode=validate-vvv --log=.claude/conversation.log

# If exit 1 → AI must redo vvv
# If exit 0 → AI can proceed to nnn
```

**Step 5: Before commit** (After gogogo)
```bash
# Standard pre-commit checks:
./scripts/enforce.sh --mode=pre-commit

# All BLOCKER gates evaluated
# Exit 1 = stop, fix violations
```

---

## Customization

### Project-Specific Gates

Add to `02-STANDARDS/PROJECT_GATES.md`:
```markdown
## [🔴 BLOCKER] Custom Rule X
- Pattern: ...
- Check: ...
- Penalty: exit 1
```

Then reference in `enforce.sh`:
```bash
# Source project-specific gates
source scripts/project_gates.sh
```

---

### Adjusting Severity

**To Make WARNING → BLOCKER**:
```bash
# In enforce.sh or via config:
STRICT_MODE=true

# In strict mode (e.g., CI):
# All WARNINGS treated as BLOCKERS
```

**To Disable Specific Gate**:
```bash
# In .ai/context_config.json:
{
  "agent_settings": {
    "disabled_gates": ["W2", "W3"]
  }
}
```

---

## Maintenance

### Adding New Gates

1. **Define in this file** (SAFETY_GATES.md)
   - Assign ID (B5, W5, M5)
   - Specify level (🔴/🟡/🔵)
   - Provide check pattern

2. **Implement in enforce.sh** (for BLOCKER/WARNING only)
   - Add detection logic
   - Test with sample violations
   - Document in enforce.sh comments

3. **Update Matrix** (Enforcement Matrix table above)

4. **Test thoroughly** before enabling

---

### Deprecating Gates

1. **Mark as deprecated** in this file:
   ```markdown
   ### Gate W2: Missing Comments
   **Status**: ⚠️ DEPRECATED (use linter instead)
   ```

2. **Disable in enforce.sh**:
   ```bash
   # Commented out - deprecated 2025-12-18
   # check_missing_comments
   ```

3. **Keep for 6 months** then remove

---

## Summary for enforce.sh

**Machine-Readable Summary** (for script parsing):

```yaml
# BLOCKERS (exit 1)
blockers:
  - id: B1
    name: no_production_edits
    pattern: 'application_[0-9]{2}_[0-9]{2}_[0-9]{4}/'
    check: path_regex
  - id: B2
    name: no_force_push_main
    pattern: '^(main|master)$'
    check: git_branch_and_args
  - id: B3
    name: sql_injection_prevention
    patterns:
      - '\$_(GET|POST|REQUEST)\[.*?\].*?->query\('
      - '"SELECT.*?\$_(GET|POST|REQUEST)'
    check: regex_in_php
  - id: B4
    name: vvv_before_nnn
    patterns:
      - 'grep -r'
      - 'Found at:'
      - 'line [0-9]+'
    check: conversation_log

# WARNINGS (print warning, continue)
warnings:
  - id: W1
    name: large_file_changes
    threshold: 500
    check: git_diff_stat
  - id: W2
    name: missing_comments
    pattern: 'function \w+\([^)]*\)\s*\{[^*]{30,}'
    check: regex_in_php
  - id: W3
    name: deprecated_patterns
    patterns:
      - 'mysql_query'
      - 'mysql_connect'
    check: regex_in_php
  - id: W4
    name: hardcoded_paths
    patterns:
      - 'deploy_[0-9]{2}_[0-9]{2}_[0-9]{4}'
      - 'application_[0-9]{2}_[0-9]{2}_[0-9]{4}'
    check: regex_in_diff

# MANUAL (documented only)
manual:
  - M1: business_logic_verification
  - M2: user_impact_assessment
  - M3: performance_impact
  - M4: third_party_integration
```

---

## References

- **vvv Protocol**: [VERIFICATION.md](./VERIFICATION.md)
- **Workflow**: [WORKFLOW.md](./WORKFLOW.md)
- **Standards**: [../02-STANDARDS/UNIVERSAL_RULES.md](../02-STANDARDS/UNIVERSAL_RULES.md)
- **Environment**: [../02-STANDARDS/ENV_VARS.md](../02-STANDARDS/ENV_VARS.md)

---

**Version**: 2.0.0 (Enforcement-Ready)
**Created**: 2025-12-18
**By**: Claude (AI Trinity - Safety Officer)
**Ready For**: `scripts/enforce.sh` implementation (Codex)
