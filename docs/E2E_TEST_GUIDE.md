# E2E Test Guide - Trinity Protocol v0.5

**Purpose:** End-to-end testing scenarios for WP0-WP6 validation
**Version:** v0.5 / Phase 6.1
**Date:** 2025-12-21

---

## Test Scenario 1: Complete Debate Workflow

**Objective:** Test full multi-agent debate workflow from start to finish

### Prerequisites
- Trinity CLI installed
- Python 3.8+ venv activated
- Working directory: `.ai/`

### Test Steps

```bash
# 1. Create session
python3 -m cli.main session new "Test Debate Workflow"

# Expected:
# ✅ Session created: sessions/2025-12-21_test_debate_workflow/
# ✅ THINK/ folders created
# ✅ SANDBOX/gemini|claude|codex/ created
# ✅ DO/snapshot|dev|prod/ created
# ✅ CONTROL/ created
# ✅ .state/ created with sentinel JSON

# Verify:
ls sessions/2025-12-21_test_debate_workflow/
# Should show: THINK/ SANDBOX/ DO/ CONTROL/ .state/

# 2. Create test proposals
cd sessions/2025-12-21_test_debate_workflow/SANDBOX

cat > gemini/proposal.md << 'EOF'
# Gemini's Proposal
Test proposal from Gemini (research-based approach)
EOF

cat > claude/proposal.md << 'EOF'
# Claude's Proposal
Test proposal from Claude (safety-first approach)
EOF

cat > codex/proposal.md << 'EOF'
# Codex's Proposal
Test proposal from Codex (implementation-focused)
EOF

# 3. Compile debate
cd ../../../.ai
python3 -m cli.main debate compile --mode fast

# Expected:
# ✅ Created round_1.md (3 proposals)
# ✅ Created verdict.md (template)
# ✅ Updated debate_state.json

# Verify:
ls sessions/2025-12-21_test_debate_workflow/SANDBOX/DEBATE/
# Should show: round_1.md verdict.md

cat sessions/2025-12-21_test_debate_workflow/.state/debate_state.json
# Should be valid JSON with status="awaiting_verdict"

# 4. Try publish (should fail - placeholders)
python3 -m cli.main debate publish

# Expected:
# ❌ Error: verdict.md still has [HUMAN: ] placeholders

# 5. Fill verdict
vim sessions/2025-12-21_test_debate_workflow/SANDBOX/DEBATE/verdict.md

# Replace all [HUMAN: ...] with:
# Decision: Combine all three approaches
# Rationale: Each has merit
# Implementation Notes: Follow hybrid approach
# Verdict By: Tester / QA Lead

# 6. Publish (should succeed)
python3 -m cli.main debate publish

# Expected:
# ✅ Validated verdict
# ✅ Published to THINK/CONSENSUS.md
# ✅ Updated debate_state.json → complete

# Verify:
cat sessions/2025-12-21_test_debate_workflow/THINK/CONSENSUS.md
# Should contain filled verdict (no placeholders)

# 7. Verify dev (prepare for promote)
python3 -m cli.main verify dev

# Expected:
# ✅ Gates check DO/dev/
# ✅ Created .state/verify_dev.json

# 8. Try promote without verification
# (Reset verify_dev.json for testing)
rm sessions/2025-12-21_test_debate_workflow/.state/verify_dev.json
python3 -m cli.main promote

# Expected:
# ❌ Error: Dev verification not found

# 9. Verify dev again
python3 -m cli.main verify dev
# ✅ PASS

# 10. Promote (should succeed - has consensus + verification)
python3 -m cli.main promote

# Expected:
# ✅ Dev verified: PASS
# ✅ Consensus: exists
# ✅ DO/dev → DO/prod

# Verify:
ls sessions/2025-12-21_test_debate_workflow/DO/prod/
# Should have files from dev

# 11. Try promote without consensus
# (Test --force flag)
cd sessions/2025-12-21_test_debate_workflow
rm THINK/CONSENSUS.md
cd ../../.ai

python3 -m cli.main promote

# Expected:
# ❌ Error: CONSENSUS.md required

python3 -m cli.main promote --force

# Expected:
# ⚠️  WARNING: Promoting without CONSENSUS.md
# ✅ Promotion successful (logged)

# Verify audit log:
grep "promote_forced" sessions/2025-12-21_test_debate_workflow/.state/events.ndjson
# Should show override event

# 12. Verify prod
python3 -m cli.main verify prod
# ✅ PASS

# 13. Try close without prod verification
# (Test gate)
rm sessions/2025-12-21_test_debate_workflow/.state/verify_prod.json
python3 -m cli.main close run

# Expected:
# ❌ Error: Prod verification required (if WP6 implemented)

# 14. Verify prod again
python3 -m cli.main verify prod
# ✅ PASS

# 15. Close session
python3 -m cli.main close run

# Expected:
# ✅ Session closed
# ✅ State updated to DONE
```

---

## Test Scenario 2: Error Handling

### Test 2.1: Invalid Patch Format

```bash
# Create session
ai session new "Test Invalid Patch"

# Create invalid patch.diff
cd sessions/2025-12-21_test_invalid_patch/SANDBOX/codex/
cat > patch.diff << 'EOF'
This is not a valid unified diff format
Just random text
EOF

# Try apply
cd ../../../../.ai
ai sandbox apply codex

# Expected:
# ❌ Error: Invalid patch format
```

### Test 2.2: Patch Outside Scope

```bash
# Create patch that touches THINK/
cat > sessions/.../SANDBOX/codex/patch.diff << 'EOF'
--- a/THINK/CONSENSUS.md
+++ b/THINK/CONSENSUS.md
@@ -1 +1 @@
-Old
+New
EOF

ai sandbox apply codex

# Expected:
# ❌ Error: Patch escapes DO/dev scope
```

### Test 2.3: Binary File in Patch

```bash
# Create patch with binary content
# (Contains null bytes)

ai sandbox apply codex

# Expected:
# ❌ Error: Binary files not allowed
```

---

## Test Scenario 3: State Machine

### Test States Transition

```bash
# Check initial state
cat sessions/.../state/session_state.json
# Should show: "state": "INIT"

# Apply patch
ai sandbox apply codex
# State → EDITING

# Verify dev
ai verify dev
# State → VERIFIED (if PASS)

# Close
ai close run
# State → DONE (if verify_prod PASS)
```

---

## Regression Test Checklist

### WP0 (Spec Lock):
- [ ] SESSION_CONTRACT.md exists and complete
- [ ] All 4 design decisions documented
- [ ] PRIMER.md references contract
- [ ] MASTER_BLUEPRINT.md references contract

### WP1 (Scaffold):
- [ ] `ai session new` creates SANDBOX/
- [ ] WORKSPACE_PROMPT.md files created
- [ ] .state/*.json files are valid JSON (not 0-byte)
- [ ] Backward compatible (old sessions still work)

### WP2 (State):
- [ ] atomic_write_json never creates 0-byte files
- [ ] State machine enforces transitions
- [ ] `ai status` shows correct phase
- [ ] Crash recovery works (kill test)

### WP3 (Debate):
- [ ] `ai debate compile` collects proposals
- [ ] FAST mode creates 1 round
- [ ] STANDARD mode creates 2 rounds (if critiques exist)
- [ ] verdict.md template has placeholders
- [ ] `ai debate publish` validates (rejects if placeholders)
- [ ] Publishes to THINK/CONSENSUS.md

### WP4 (Single Ingress):
- [ ] `ai sandbox apply` applies patch.diff
- [ ] Scope guard rejects out-of-scope paths
- [ ] Binary files rejected
- [ ] Size limit enforced (>10MB rejected)
- [ ] Atomic apply (no partial changes)
- [ ] --dry-run works (preview only)

### WP5 (Verify & Promote):
- [ ] `ai verify dev` → verify_dev.json
- [ ] `ai verify prod` → verify_prod.json
- [ ] `ai promote` blocked without verify_dev PASS
- [ ] `ai promote` blocked without CONSENSUS.md (default)
- [ ] `ai promote --force` works (logged)
- [ ] Override logged to events.ndjson

### WP6 (Close):
- [ ] `ai close` blocked without verify_prod PASS
- [ ] `ai close` updates state → DONE
- [ ] `ai sandbox clean` archives SANDBOX/ (optional)

---

## Performance Benchmarks

**Expected Performance:**

| Command | Expected Duration |
|---------|------------------|
| `ai session new` | < 1 second |
| `ai snapshot run` | < 5 seconds (small projects) |
| `ai debate compile` | < 2 seconds |
| `ai debate publish` | < 1 second |
| `ai sandbox apply` | < 3 seconds |
| `ai verify dev` | < 5 seconds |
| `ai promote` | < 10 seconds |
| `ai verify prod` | < 5 seconds |
| `ai close run` | < 2 seconds |

**Full workflow:** < 2 minutes (excluding human decision time)

---

## Success Metrics

### Functional:
- [ ] All commands execute without errors
- [ ] All gates enforce correctly
- [ ] All state transitions valid
- [ ] All audit events logged

### Security:
- [ ] No secrets leak through gates
- [ ] No unauthorized file access
- [ ] No state corruption
- [ ] Audit trail complete

### Usability:
- [ ] Error messages clear and actionable
- [ ] Next steps always shown
- [ ] Documentation complete
- [ ] Examples work

---

**E2E Testing Complete when all scenarios pass. 🧪**
