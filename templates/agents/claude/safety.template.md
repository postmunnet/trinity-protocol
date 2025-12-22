# Claude Safety Check Template

**Purpose:** Pre-execution safety verification for Trinity Phase 6 sessions

---

## 🛡️ Safety Checklist

### 1. Scope Validation
- [ ] Changes are within defined scope (check THINK/00_CONTEXT.md)
- [ ] No unauthorized file modifications
- [ ] Database changes reviewed and approved
- [ ] API contract changes documented

### 2. Security Review
- [ ] No hardcoded secrets or API keys
- [ ] No sensitive data in logs
- [ ] Authentication/authorization unchanged (unless intended)
- [ ] SQL injection risks addressed
- [ ] XSS vulnerabilities checked

### 3. Data Safety
- [ ] No destructive database operations without backup
- [ ] Migration scripts have rollback plan
- [ ] Data validation in place
- [ ] No PII exposed in new code

### 4. Breaking Changes
- [ ] Backward compatibility maintained
- [ ] No API breaking changes (or versioned)
- [ ] No removed public methods/fields
- [ ] Database migrations reversible

### 5. Dependencies
- [ ] New dependencies vetted for security
- [ ] License compatibility checked
- [ ] Version pinning applied
- [ ] No known vulnerabilities in deps

---

## ⚠️ Hazards Identified

- [ ] **Hazard 1**: [Description]
  - **Risk Level:** Low / Medium / High / Critical
  - **Mitigation:** [Action to take]
  - **Owner:** [Who will address this]

- [ ] **Hazard 2**: [Description]
  - **Risk Level:** Low / Medium / High / Critical
  - **Mitigation:** [Action to take]
  - **Owner:** [Who will address this]

---

## 🚨 Risk Assessment

**Overall Risk Level:** Low / Medium / High / Critical

### Risk Factors
```
File Count: [X] files (>5 = higher risk)
Impact Zones: [frontend/backend/db/config]
Reversibility: [Easy/Medium/Hard]
Test Coverage: [X]%
```

### High-Risk Indicators
- [ ] Database schema changes
- [ ] Authentication/authorization changes
- [ ] Payment processing code
- [ ] Data migration scripts
- [ ] Production config changes

---

## ✅ Phase 6 Safety Gates

### Pre-Execution
- [ ] Plan reviewed and approved
- [ ] Scope clearly defined
- [ ] Risk assessment complete
- [ ] All risky operations have rollback plan

### During Execution
- [ ] `ai verify dev` passes before promote
- [ ] No forbidden files in dev (.env)
- [ ] No secrets detected in code

### Pre-Production
- [ ] `ai verify prod` passes
- [ ] Manual smoke tests completed
- [ ] Rollback plan documented and ready
- [ ] Monitoring alerts configured

---

## 🔒 Decision

**Safety Status:** ✅ APPROVED / ⚠️ CONDITIONAL / ❌ BLOCKED

**Conditions (if conditional):**
1. [Condition to meet before proceeding]
2. [Additional review required]
3. [Monitoring to enable]

**Blockers (if blocked):**
1. [Issue that must be resolved]
2. [Why this blocks execution]
3. [Who can approve override]

**Recommendations:**
- [Safety improvement suggestion]
- [Risk mitigation advice]
- [Additional testing needed]

---

**Reviewed By:** Claude AI
**Timestamp:** {{TIMESTAMP}}
**Session:** {{SESSION_ID}}
**Next Review:** [If conditional, when to re-review]
