# Trinity Protocol v0.5 - User Guide

**Version:** v0.5 / Phase 6.1 (Agent Sandbox)
**Last Updated:** 2025-12-21
**Status:** Complete Workflow Documentation

---

## Quick Start (5 minutes)

### Prerequisites
- Trinity Protocol installed in `.ai/`
- Python 3.8+ with venv activated
- Basic understanding of git and CLI

### Your First Session

```bash
cd .ai

# 1. Create session
python3 -m cli.main session new "My First Task"

# 2. Snapshot current state
python3 -m cli.main snapshot run

# 3. Make changes in DO/dev/ (or use SANDBOX/)
# Edit files in sessions/YYYY-MM-DD_my_first_task/DO/dev/

# 4. Verify changes
python3 -m cli.main verify dev

# 5. Promote to prod
python3 -m cli.main promote

# 6. Verify prod
python3 -m cli.main verify prod

# 7. Close session
python3 -m cli.main close run
```

---

## Complete Workflow Guide

### Workflow A: Simple Direct Edit (No Agents)

**Use when:** Simple bug fix, hotfix, solo work

```bash
# 1. Create session
cd .ai
python3 -m cli.main session new "Fix Typo in README"

# Created: sessions/2025-12-21_fix_typo_in_readme/

# 2. Backup current state
python3 -m cli.main snapshot run
# Copies project files → DO/snapshot/ → DO/dev/

# 3. Edit files directly
cd sessions/2025-12-21_fix_typo_in_readme/DO/dev/
vim README.md  # Fix typo

# 4. Verify dev
cd ../../../../.ai
python3 -m cli.main verify dev
# ✅ PASS → Creates .state/verify_dev.json

# 5. Promote to prod
python3 -m cli.main promote
# ❌ Error: CONSENSUS.md required

# Create simple consensus
cd sessions/2025-12-21_fix_typo_in_readme/THINK/
cat > CONSENSUS.md << 'EOF'
# Consensus: Fix README Typo

**Decision:** Fix spelling error in README.md line 42
**Rationale:** Improve documentation quality
EOF

# 6. Promote again
cd ../../../../.ai
python3 -m cli.main promote
# ✅ Success

# 7. Verify prod
python3 -m cli.main verify prod
# ✅ PASS → Creates .state/verify_prod.json

# 8. Deploy (if configured)
python3 -m cli.main deploy run --env prod

# 9. Close session
python3 -m cli.main close run
# ✅ Session closed
```

**Duration:** 10-15 minutes

---

### Workflow B: Multi-Agent Debate (Recommended)

**Use when:** Complex feature, multiple approaches, need consensus

```bash
# 1. Create session
cd .ai
python3 -m cli.main session new "Redesign Authentication System"

# Session created with SANDBOX/gemini|claude|codex/

# 2. Snapshot
python3 -m cli.main snapshot run

# 3. Agents work in parallel (human coordinates)
# Agent 1 (Gemini) - Research
cd sessions/2025-12-21_redesign_auth/SANDBOX/gemini/
cat > proposal.md << 'EOF'
# Gemini's Proposal: OAuth 2.0 + JWT

**Approach:** Use industry-standard OAuth 2.0

**Benefits:**
- Widely supported
- Secure by default
- Token-based (stateless)

**Implementation:**
- Use `authlib` library
- Add JWT middleware
- Migrate existing sessions
EOF

# Agent 2 (Claude) - Safety Analysis
cd ../claude/
cat > proposal.md << 'EOF'
# Claude's Proposal: Multi-Factor Auth + Rate Limiting

**Approach:** Enhance existing auth with MFA

**Benefits:**
- Backward compatible
- Security layer added
- Rate limiting prevents brute force

**Implementation:**
- Add TOTP support
- Add rate limiting middleware
- Keep existing password auth
EOF

# Agent 3 (Codex) - Implementation-First
cd ../codex/
cat > proposal.md << 'EOF'
# Codex's Proposal: Passkey (WebAuthn)

**Approach:** Modern passwordless authentication

**Benefits:**
- No passwords to leak
- Phishing resistant
- Better UX

**Implementation:**
- Use WebAuthn API
- Add passkey registration flow
- Fallback to password for legacy
EOF

# 4. Compile debate
cd ../../../../.ai
python3 -m cli.main debate compile --mode standard
# ✅ Created round_1.md (3 proposals)
# ✅ Created verdict.md (TEMPLATE)

# 5. Human decides
cd sessions/2025-12-21_redesign_auth/SANDBOX/DEBATE/
vim verdict.md

# Fill template:
# Decision: Use OAuth 2.0 (Gemini's proposal) with MFA (Claude's suggestion)
# Rationale: Industry standard + security enhancement
# Implementation Notes: Codex implements OAuth + MFA

# 6. Publish consensus
cd ../../../../.ai
python3 -m cli.main debate publish
# ✅ Validated verdict (no placeholders)
# ✅ Published to THINK/CONSENSUS.md

# 7. Codex implements (human coordinates)
cd sessions/2025-12-21_redesign_auth/SANDBOX/codex/
# Create patch.diff (or implement in full files)
cat > patch.diff << 'EOF'
--- a/auth.py
+++ b/auth.py
@@ -10,7 +10,12 @@ def login(username, password):
-    return create_session(user)
+    # Add OAuth flow
+    oauth_token = get_oauth_token(user)
+    return create_session(user, oauth_token)
EOF

# 8. Apply patch
cd ../../../../.ai
python3 -m cli.main sandbox apply codex
# ✅ Applied patch to DO/dev/

# 9. Verify dev
python3 -m cli.main verify dev
# ✅ PASS

# 10. Promote
python3 -m cli.main promote
# ✅ Gates: verify_dev PASS, CONSENSUS.md exists
# ✅ DO/dev → DO/prod

# 11. Verify prod
python3 -m cli.main verify prod
# ✅ PASS

# 12. Deploy
python3 -m cli.main deploy run --env prod

# 13. Close
python3 -m cli.main close run
# ✅ Session closed
```

**Duration:** 2-4 hours (with debate)

---

## Command Reference

### Session Management

**ai session new "<name>"**
- Creates new session with THINK/, SANDBOX/, DO/, CONTROL/, .state/
- Initializes sentinel JSON files
- Creates WORKSPACE_PROMPT.md for each agent

**ai snapshot run**
- Backs up current project state
- Copies to DO/snapshot/ (immutable)
- Copies to DO/dev/ (working copy)

**ai status show**
- Shows current session status
- Shows next recommended action

---

### Debate Workflow

**ai debate compile --mode <fast|standard|deep>**
- Collects proposals from SANDBOX/<agent>/proposal.md
- Creates SANDBOX/DEBATE/round_*.md
- Creates verdict.md TEMPLATE for human
- Modes:
  - `fast`: 1 round (proposals only)
  - `standard`: 2 rounds (proposals + critiques)
  - `deep`: 3 rounds (proposals + critiques + rebuttals)

**ai debate publish**
- Validates verdict.md (no [HUMAN: ] placeholders)
- Copies to THINK/CONSENSUS.md
- Updates debate_state.json → complete

**ai debate status**
- Shows debate progress
- Shows verdict status
- Recommends next action

---

### Sandbox Management

**ai sandbox apply <agent>**
- Applies SANDBOX/<agent>/patch.diff to DO/dev/
- Validates scope (only touches DO/dev/)
- Atomic apply (rollback on failure)
- Requires: unified diff format, no binary, <10MB

**ai sandbox clean [--remove] [-y]**
- Archives `SANDBOX/` to `SANDBOX_archive_<timestamp>` by default
- `--remove -y` permanently deletes `SANDBOX/` (requires confirmation)
- Logs event to `.state/events.ndjson`

---

### Verification & Promotion

**ai verify dev**
- Runs gates on DO/dev/
- Gates: forbidden files, secrets, smoke hooks
- Creates .state/verify_dev.json

**ai verify prod**
- Runs gates on DO/prod/
- Creates .state/verify_prod.json

**ai promote**
- Requires: verify_dev PASS + CONSENSUS.md (default)
- Copies DO/dev/ → DO/prod/
- Excludes: .env, config.dev.json
- Override: --force (logged)

---

### Deployment & Closure

**ai deploy run --env <dev|prod>**
- Deploys to configured environment
- Supports: rsync, scp, local copy

**ai close run**
- Requires: verify_prod PASS
- Updates session_state.json → DONE
- Closes session

**ai sandbox clean**
- Archives or deletes SANDBOX/ (optional)
- Keeps DEBATE/verdict.md for audit

**ai unlock**
- Force-break `.state/LOCK` if a stale lock blocks operations
- Prefer using timeout/stale cleanup; use `unlock` only when necessary

---

## Session Structure Reference

```
sessions/YYYY-MM-DD_task_name/
├── THINK/                      # Human Planning
│   ├── 00_CONTEXT.md           # Background
│   ├── 01_PROMPT.md            # Problem
│   ├── 02_SCOPE.md             # Scope
│   ├── 03_ACCEPTANCE.md        # Success criteria
│   └── CONSENSUS.md            # ⭐ Published verdict (required for promote)
│
├── SANDBOX/                    # Agent Working Areas
│   ├── gemini/                 # Research & analysis
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── research.md
│   │   ├── proposal.md         # For debate
│   │   └── critique.md         # For STANDARD/DEEP modes
│   ├── claude/                 # Planning & safety
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── review.md
│   │   ├── proposal.md
│   │   └── critique.md
│   ├── codex/                  # Implementation
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── implementation.md
│   │   ├── proposal.md
│   │   └── patch.diff          # ⭐ Unified diff (ONLY ingress to DO/dev)
│   └── DEBATE/                 # Compiled debate
│       ├── round_1.md          # All proposals
│       ├── round_2.md          # All critiques (if mode=standard/deep)
│       └── verdict.md          # Human writes decision
│
├── DO/                         # Execution
│   ├── snapshot/               # Immutable backup
│   ├── dev/                    # Working copy (single ingress via patch.diff)
│   └── prod/                   # Release candidate (via ai promote)
│
├── CONTROL/                    # Status
│   ├── META.json
│   ├── VERIFY.md
│   └── LIVE_MONITOR.md
│
└── .state/                     # System State (Never Edit)
    ├── session_state.json      # INIT/EDITING/VERIFIED/DONE
    ├── debate_state.json       # Debate progress
    ├── verify_dev.json         # Dev verification result
    ├── verify_prod.json        # Prod verification result
    └── events.ndjson           # Audit log
```

---

## Trust Boundaries

| Zone | Human | Agents | System |
|------|-------|--------|--------|
| THINK/ | ✅ Write | 👁️ Read | 👁️ Read |
| SANDBOX/gemini/ | 👁️ Read | ✅ Gemini Write | 👁️ Read |
| SANDBOX/claude/ | 👁️ Read | ✅ Claude Write | 👁️ Read |
| SANDBOX/codex/ | 👁️ Read | ✅ Codex Write | 👁️ Read |
| SANDBOX/DEBATE/ | 👁️ Read | ❌ No Write | ✅ Write (via commands) |
| DO/snapshot/ | ❌ No Write | ❌ No Write | ✅ Write (ai snapshot) |
| DO/dev/ | ✅ Write | ❌ No Write | ✅ Write (ai sandbox apply) |
| DO/prod/ | ❌ No Write | ❌ No Write | ✅ Write (ai promote) |
| CONTROL/ | 👁️ Read | 👁️ Read | ✅ Write |
| .state/ | 👁️ Read | ❌ No Write | ✅ Write |

---

## Troubleshooting

### Error: "CONSENSUS.md required"

**Cause:** `ai promote` requires consensus by default

**Solutions:**
1. Run debate workflow: `ai debate compile` → edit verdict → `ai debate publish`
2. Create CONSENSUS.md manually with your decision
3. Use `--force` (not recommended): `ai promote --force`

---

### Error: "Dev verification not found"

**Cause:** Must run `ai verify dev` before promote

**Solution:**
```bash
ai verify dev
# Wait for PASS
ai promote
```

---

### Error: "Patch escapes DO/dev scope"

**Cause:** patch.diff tries to modify files outside DO/dev/

**Solution:**
- Review patch.diff
- Ensure all paths are within DO/dev/
- Remove any paths to THINK/, CONTROL/, .state/

---

### Error: "verdict.md still has [HUMAN: ] placeholders"

**Cause:** verdict.md template not filled

**Solution:**
```bash
vim SANDBOX/DEBATE/verdict.md
# Fill all [HUMAN: ...] sections
ai debate publish
```

---

## Best Practices

### DO:
- ✅ Run debate for complex decisions
- ✅ Fill THINK/CONSENSUS.md for all promotes
- ✅ Verify dev before promote
- ✅ Verify prod before close
- ✅ Use descriptive session names

### DON'T:
- ❌ Edit .state/ files directly
- ❌ Skip verification gates
- ❌ Use --force habitually
- ❌ Write to DO/prod/ directly

---

## Advanced Usage

### Emergency Hotfix (Skip Debate)

```bash
ai session new "Emergency Hotfix"
ai snapshot run
# Edit DO/dev/ directly
echo "# Hotfix" > sessions/.../THINK/CONSENSUS.md  # Simple consensus
ai verify dev
ai promote
ai verify prod
ai close run
```

### Multi-Round Debate

```bash
# Round 1: Proposals
ai debate compile --mode standard

# Agents write critiques
# (Create SANDBOX/<agent>/critique.md)

# Round 2: Compile critiques
ai debate compile --mode standard
# Now has round_1.md + round_2.md

# Human decides
vim SANDBOX/DEBATE/verdict.md
ai debate publish
```

---

## State Machine

```
INIT
  │
  └→ (ai sandbox apply OR edit DO/dev) → EDITING
       │
       └→ (ai verify dev PASS) → VERIFIED
            │
            └→ (ai close, requires verify_prod PASS) → DONE

Notes:
- State transitions are system-only (commands update state)
- `.state/*.json` is always written atomically; never edit manually
```

---

## Configuration

**SSOT:** `.ai/ssot.yaml`
**Policies:** `.ai/policies/*.yaml`
**Templates:** `.ai/templates/session/`

---

## Further Reading

- `SESSION_CONTRACT.md` - Complete specification
- `MASTER_BLUEPRINT.md` - Architecture overview
- `PRIMER.md` - Quick reference

---

**🌌 Trinity v0.5 - Multi-Agent Development Made Safe**
### Orchestrator (Reference)

For automation or CI-like runs, use the reference orchestrator to chain commands:

```
python .ai/examples/simple_orchestrator.py --task "Fix Auth Bug" \
  --patch sessions/examples/2025-12-22_sandbox_demo/SANDBOX/codex/patch.diff

# Quick path (no patch apply)
python .ai/examples/simple_orchestrator.py --quick "Small Fix"
```

The orchestrator executes:
- session new → snapshot → optional sandbox apply → verify dev → promote → verify prod → close
and prints a progress tree with success/failure per step.
