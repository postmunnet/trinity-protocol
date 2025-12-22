# Trinity Protocol: Session Contract

**Version:** v0.5 / Phase 6.1
**Date:** 2025-12-21
**Status:** 🔒 **LOCKED** - Canonical Specification
**Scope:** Hybrid Session Model (Phase-Based + Agent Sandboxes)

---

## 📜 Purpose

This document is the **canonical contract** for all Trinity Protocol sessions. Every Work Package (WP0-WP7) and all agents MUST follow this specification. This contract ensures:

- **Single Source of Truth** (Lock 1): One structure, no ambiguity
- **Predictable Safety** (Lock 2): Gates enforce this contract
- **Audit Trail** (Lock 3): All sessions follow same schema

**If in doubt, refer to this document.**

---

## 1. 🏗️ Canonical Session Structure

### 1.1 Folder Hierarchy (Contract)

```
sessions/YYYY-MM-DD_task_name/
├── THINK/                      # Human Planning (Human-Only Write)
│   ├── 00_CONTEXT.md           # Background, objectives, constraints
│   ├── 01_PROMPT.md            # Problem statement, goals
│   ├── 02_SCOPE.md             # Files to change, impact zones
│   ├── 03_ACCEPTANCE.md        # Success criteria, verification
│   ├── CLAUDE_GOVERNANCE_DECISION.md  # Major decisions
│   ├── NOTES.md                # Free-form working notes
│   └── CONSENSUS.md            # 🆕 Published debate verdict (required for promote)
│
├── SANDBOX/                    # 🆕 Agent Working Areas (Disposable)
│   ├── gemini/                 # Gemini's research & analysis
│   │   ├── WORKSPACE_PROMPT.md # Agent instructions
│   │   ├── research.md         # Research findings
│   │   ├── analysis.md         # Impact analysis
│   │   └── proposal.md         # Proposal for debate
│   ├── claude/                 # Claude's planning & safety
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── review.md           # Safety review
│   │   ├── critique.md         # Critique of proposals
│   │   ├── proposal.md         # Proposal for debate
│   │   └── governance.md       # Governance decisions
│   ├── codex/                  # Codex's implementation
│   │   ├── WORKSPACE_PROMPT.md
│   │   ├── implementation.md   # Implementation notes
│   │   ├── proposal.md         # Proposal for debate
│   │   └── patch.diff          # ⭐ CRITICAL: Unified diff output (ONLY ingress to DO/dev)
│   └── DEBATE/                 # 🆕 Debate Artifacts (Optional)
│       ├── round_1.md          # All proposals
│       ├── round_2.md          # All critiques (STANDARD/DEEP mode)
│       ├── round_3.md          # All rebuttals (DEEP mode only)
│       └── verdict.md          # Final decision (Human writes)
│
├── DO/                         # Execution Workspace (Deploy-Ready)
│   ├── snapshot/               # Immutable backup (System-Only Write)
│   ├── dev/                    # Working copy (Single Ingress via patch.diff)
│   └── prod/                   # Release candidate (Only `ai promote` writes here)
│
├── CONTROL/                    # Status & Metadata (System Updates, Human Reads)
│   ├── META.json               # Session metadata
│   ├── VERIFY.md               # Verification log
│   └── LIVE_MONITOR.md         # Real-time status
│
└── .state/                     # 🆕 Session-Local State (System-Only, Never Edit)
    ├── session_state.json      # Current phase (INIT/EDITING/VERIFIED/DONE)
    ├── debate_state.json       # Debate progress (mode, rounds)
    ├── verify_dev.json         # Dev verification results
    ├── verify_prod.json        # Prod verification results
    └── events.ndjson           # Event log (append-only)
```

---

## 2. 🔒 Non-Negotiable Rules

These rules MUST be enforced by all commands and respected by all agents:

### Rule 1: SANDBOX = Disposable
- **SANDBOX/** folders are for drafts and experimentation only
- NOT subject to verification gates (drafts don't need to pass tests)
- Can be deleted without affecting session validity
- **Purpose:** Parallel agent work, debate, prototyping

### Rule 2: DO/dev = Single Ingress (⭐ CRITICAL)
- **ONLY** way to write to `DO/dev/` is via `ai sandbox apply <agent>` command
- This command applies `SANDBOX/<agent>/patch.diff` (unified diff format)
- **NO** direct writes, manual copy-paste, or other entry points
- **Purpose:** Prevent race conditions, ensure atomic updates, enable audit trail

### Rule 3: DO/prod = Promote-Only
- **ONLY** way to write to `DO/prod/` is via `ai promote` command
- Humans and agents **CANNOT** write directly to `DO/prod/`
- **Purpose:** Enforce verification gates before production

### Rule 4: THINK/CONSENSUS.md = Published Output
- `CONSENSUS.md` contains the final, agreed-upon decision from debate
- Created by `ai debate publish` (copies from `SANDBOX/DEBATE/verdict.md`)
- **Required** by `ai promote` (default behavior, see Design Decision Q2)
- **Purpose:** Ensure all changes are based on documented reasoning

### Rule 5: .state/ = System-Only
- Humans and agents **CANNOT** write directly to `.state/` files
- All state updates happen via atomic operations by commands
- All `.state/*.json` files MUST be valid JSON (never 0 bytes)
- **Purpose:** Prevent state corruption, enable crash recovery

---

## 3. 🎯 Design Decisions (Locked)

### Decision 1: Verdict Authorship (Q1)

**Question:** Who writes `SANDBOX/DEBATE/verdict.md`?

**Answer:** **Human** (not AI)

**Workflow:**
1. `ai debate compile` → Creates `verdict.md` as **TEMPLATE** with placeholders
2. **Human** reads all proposals, makes decision, fills template:
   - Decision: What was decided
   - Rationale: Why this decision was made
   - Implementation Notes: Guidance for Codex
3. `ai debate publish` → Validates verdict (no placeholders), copies to `THINK/CONSENSUS.md`

**Rationale:**
- Prevents AI bias in decision-making
- Maintains human-in-the-loop safety (Trinity principle)
- Creates clear accountability

**Future:** AI-assisted verdict generation may be added (WP9), but always requires human approval.

---

### Decision 2: Consensus Requirement (Q2)

**Question:** Does `ai promote` require `THINK/CONSENSUS.md`?

**Answer:** **Yes (default)**

**Implementation:**
```bash
# Default behavior (strict)
ai promote
# → Checks THINK/CONSENSUS.md exists
# → Blocks if missing: "Error: CONSENSUS.md required (--force to override)"

# Emergency override (logged)
ai promote --force
# → Allows promote without consensus
# → Logs override event to .state/events.ndjson
# → Requires justification in log
```

**Rationale:**
- Enforces planning discipline (no cowboy deployments)
- Creates audit trail of why changes were made
- Prevents shortcuts that bypass debate/review

**Policy:** Can be configured via `.ai/policies/gates.yaml` (optional, defaults to required).

---

### Decision 3: State Transitions (Q3)

**Question:** Who controls state transitions? (System or Agent?)

**Answer:** **System only**

**Implementation:**
- Commands update state automatically (not agents)
- Agents **CANNOT** directly modify `.state/` files
- `.state/` directory permissions: read-only for agents (if enforced)

**State Machine (Minimal - WP2 MVP):**
```
INIT → EDITING → VERIFIED → DONE
```

**Transition Rules:**
- `INIT → EDITING`: Triggered by `ai sandbox apply` or direct edits to `DO/dev/`
- `EDITING → VERIFIED`: Triggered by `ai verify dev` (PASS)
- `VERIFIED → DONE`: Triggered by `ai close` (requires `verify_prod PASS`)

**Rationale:**
- **Security:** Agents cannot bypass gates by changing state
- **Predictability:** State transitions follow defined rules
- **Integrity:** State machine is enforced, not suggested

---

### Decision 4: Diff Format (Q4)

**Question:** What patch format? Binary files allowed?

**Answer:** **Unified diff, no binary, 10MB limit**

**Specification:**

**Format:** Unified diff only (`diff -u` format)
```diff
--- a/file.py
+++ b/file.py
@@ -10,7 +10,7 @@
 def foo():
-    return "old"
+    return "new"
```

**Constraints:**
- **NO binary files** (reject with error: "Binary files not allowed in patch.diff")
- **Max size: 10MB** (reject if larger: "Patch too large (>10MB)")
- **Format validation:** Must be parseable as unified diff

**Rationale:**
- **Reviewability:** Humans can read unified diffs easily
- **Security:** Text-only diffs prevent encoding attacks
- **Tool Support:** Standard format, widely supported

**Note (from Gemini):** LLMs may struggle to generate perfect unified diffs. Consider allowing agents to write full files, then system creates diff. Implementation choice for WP4.

---

## 4. 🗣️ Debate Modes

### 4.1 Mode Definitions

**FAST Mode (1 round):**
- Agents write `proposal.md` → Human reads → Human writes `verdict.md`
- Use when: Simple tasks, clear requirements, low controversy

**STANDARD Mode (2 rounds):**
- Round 1: Agents write `proposal.md`
- Round 2: Agents write `critique.md` (review other proposals)
- Human reads both → Human writes `verdict.md`
- Use when: Moderate complexity, multiple valid approaches

**DEEP Mode (3 rounds):**
- Round 1: Proposals
- Round 2: Critiques
- Round 3: Rebuttals (agents respond to critiques)
- Human reads all → Human writes `verdict.md`
- Use when: High complexity, significant disagreement, critical decisions

### 4.2 Debate Workflow

```bash
# 1. Agents write proposals
# (Each agent creates SANDBOX/<agent>/proposal.md)

# 2. Compile debate
ai debate compile --mode fast  # or standard, deep

# Output:
# - SANDBOX/DEBATE/round_1.md (all proposals)
# - SANDBOX/DEBATE/round_2.md (if mode=standard/deep)
# - SANDBOX/DEBATE/round_3.md (if mode=deep)
# - SANDBOX/DEBATE/verdict.md (TEMPLATE for human)

# 3. Human edits verdict.md
# (Read proposals, make decision, fill template)

# 4. Publish verdict
ai debate publish

# Output:
# - Validates verdict (no [HUMAN: ] placeholders)
# - Copies to THINK/CONSENSUS.md
# - Updates debate_state.json → complete
# - Updates session_state.json → next phase
```

---

## 5. 🛡️ Trust Boundaries

### 5.1 Who Can Write Where

| Zone | Human | Agents | System | Purpose |
|------|-------|--------|--------|---------|
| **THINK/** | ✅ Write | 👁️ Read | 👁️ Read | Planning, consensus |
| **SANDBOX/gemini/** | 👁️ Read | ✅ Write (Gemini only) | 👁️ Read | Gemini's workspace |
| **SANDBOX/claude/** | 👁️ Read | ✅ Write (Claude only) | 👁️ Read | Claude's workspace |
| **SANDBOX/codex/** | 👁️ Read | ✅ Write (Codex only) | 👁️ Read | Codex's workspace |
| **SANDBOX/DEBATE/** | 👁️ Read | ❌ No Write | ✅ Write (via commands) | Compiled debate artifacts |
| **DO/snapshot/** | ❌ No Write | ❌ No Write | ✅ Write (`ai snapshot`) | Immutable backup |
| **DO/dev/** | ✅ Write | ❌ No Write | ✅ Write (`ai sandbox apply`) | Working copy (single ingress) |
| **DO/prod/** | ❌ No Write | ❌ No Write | ✅ Write (`ai promote`) | Release candidate |
| **CONTROL/** | 👁️ Read | 👁️ Read | ✅ Write | Metadata, logs |
| **.state/** | 👁️ Read | ❌ No Write | ✅ Write | Canonical state |

### 5.2 Agent Isolation

**Key Principle:** Each agent has **exclusive write access** to their sandbox.

**Enforcement:**
- Agent A **CANNOT** write to `SANDBOX/B/`
- Agent A **CAN** read `SANDBOX/B/` (for collaboration)
- Enforcement via CLI validation (optional: file permissions)

**Rationale:**
- Prevents agents from tampering with each other's work
- Enables parallel work without conflicts
- Clear accountability (who wrote what)

---

## 6. ⚙️ State Machine

### 6.1 Minimal State Machine (WP2 MVP)

**States:**
- `INIT`: Session created, no work yet
- `EDITING`: Code changes in progress (`DO/dev/` has changes)
- `VERIFIED`: Dev changes verified (`verify_dev PASS`)
- `DONE`: Session closed (`verify_prod PASS` + `ai close`)

**Transitions:**
```
INIT
  │
  ├─→ (ai sandbox apply OR manual edit) → EDITING
  │
EDITING
  │
  ├─→ (ai verify dev PASS) → VERIFIED
  │
VERIFIED
  │
  ├─→ (ai close, requires verify_prod PASS) → DONE
```

**Future States (Deferred to WP3):**
- `RESEARCH`: Agent research phase
- `DEBATE`: Debate in progress
- `DEV_EDITING`: Separate editing phase after debate

**Rationale:** Start simple (4 states), add complexity later if needed.

---

## 7. 🚦 Verification Gates

### 7.1 Gate Hierarchy

**Level 1: Dev Verification** (`ai verify dev`)
- Scope: `DO/dev/` workspace
- Gates: Syntax, secrets, forbidden files, smoke tests
- Output: `.state/verify_dev.json`
- **Blocks:** `ai promote` if FAIL

**Level 2: Prod Verification** (`ai verify prod`)
- Scope: `DO/prod/` workspace
- Gates: Same as dev + additional prod-specific checks
- Output: `.state/verify_prod.json`
- **Blocks:** `ai close` if FAIL

**Level 3: Consensus Gate** (optional, default ON)
- Scope: `THINK/CONSENSUS.md` existence
- **Blocks:** `ai promote` if missing (unless `--force`)

### 7.2 Gate Outputs

**verify_dev.json:**
```json
{
  "timestamp": "2025-12-21T10:00:00Z",
  "result": "PASS",  // or "FAIL"
  "gates": {
    "secrets": {"passed": true, "findings": []},
    "forbidden": {"passed": true, "files": []},
    "syntax": {"passed": true, "errors": []}
  }
}
```

**verify_prod.json:** Same schema, different scope.

---

## 8. 📝 Patch.diff Specification

### 8.1 Format Requirements

**Valid Patch:**
```diff
--- a/src/auth.py
+++ b/src/auth.py
@@ -45,10 +45,12 @@ def login(username, password):
     if not user:
-        return None
+        raise ValueError("User not found")

     if not check_password(user, password):
-        return None
+        raise ValueError("Invalid password")

+    log_login_attempt(user)
     return create_session(user)
```

**Required:**
- ✅ Unified diff format (`diff -u`)
- ✅ All paths relative (no absolute paths)
- ✅ All paths within `DO/dev/` scope

**Forbidden:**
- ❌ Binary content (error: "Binary files not allowed")
- ❌ Paths outside `DO/dev/` (error: "Patch escapes scope")
- ❌ Size > 10MB (error: "Patch too large")
- ❌ Symlink creation (error: "Symlinks not allowed")

### 8.2 Validation Logic

**Before applying patch.diff, `ai sandbox apply` MUST:**

1. **Format Check:** Validate unified diff format
2. **Size Check:** Reject if > 10MB
3. **Binary Check:** Reject if contains binary content (`\x00` bytes)
4. **Scope Check:** All paths must be within `DO/dev/`
   - Extract paths from diff headers
   - Normalize paths (resolve `..`)
   - Validate all paths start with `DO/dev/`
   - Reject if any path is `THINK/`, `CONTROL/`, `.state/`, `SANDBOX/`
5. **Symlink Check:** Reject if creates symlinks
6. **Apply:** Only if all checks pass

**If any check fails:** Reject entire patch, leave `DO/dev/` unchanged.

---

## 9. 🔐 Trinity "3 Locks" Compliance

### 9.1 Lock 1: SSOT (Single Source of Truth)

**Enforcement in This Contract:**
- ✅ Single session structure (this document)
- ✅ Single ingress to `DO/dev/` (patch.diff only)
- ✅ Single consensus document (`THINK/CONSENSUS.md`)
- ✅ Policies in `.ai/policies/` (not scattered)

**Contract Status:** This document IS the SSOT for sessions.

---

### 9.2 Lock 2: Smart Gates (Automated Enforcement)

**Gates Defined:**
- ✅ Scope guard (WP4): Validates patch.diff paths
- ✅ Secret detection (existing): Scans for API keys
- ✅ Forbidden files (existing): Blocks `.env` in prod
- ✅ Verify gates (WP5): Enforces quality before promote
- ✅ Consensus gate (WP5): Enforces planning before deploy
- ✅ Close gate (WP6): Enforces prod verification before done

**All gates are automated, non-negotiable.**

---

### 9.3 Lock 3: Audit Trail (Tamper-Evident Logging)

**Event Logging:**
- ✅ All significant actions logged to `.state/events.ndjson`
- ✅ Append-only format (no edits to past events)
- ✅ Timestamped, includes actor (human/system/agent)

**Example Event:**
```json
{"timestamp": "2025-12-21T10:00:00Z", "action": "sandbox_apply", "agent": "codex", "files_changed": 3}
{"timestamp": "2025-12-21T10:05:00Z", "action": "verify_dev", "result": "PASS"}
{"timestamp": "2025-12-21T10:10:00Z", "action": "promote", "consensus": true}
```

---

## 10. 🎓 Usage Examples

### Example 1: Simple Task (FAST Mode, No Debate)

```bash
# 1. Create session
ai session new "Fix typo in README"

# 2. Codex writes fix directly to SANDBOX/codex/patch.diff
# (Human or agent creates patch.diff)

# 3. Apply patch
ai sandbox apply codex

# 4. Verify
ai verify dev

# 5. Promote
ai promote  # Blocked: needs CONSENSUS.md
ai promote --force  # Override (logged)

# 6. Deploy & Close
ai deploy prod
ai verify prod
ai close
```

---

### Example 2: Complex Task (STANDARD Mode, With Debate)

```bash
# 1. Create session
ai session new "Redesign Authentication System"

# 2. Agents write proposals
# - Gemini: SANDBOX/gemini/proposal.md (research-based approach)
# - Claude: SANDBOX/claude/proposal.md (safety-first approach)
# - Codex: SANDBOX/codex/proposal.md (implementation-focused approach)

# 3. Compile debate
ai debate compile --mode standard
# Creates: round_1.md (proposals), verdict.md (template)

# 4. (Optional) Agents write critiques
# - Gemini: SANDBOX/gemini/critique.md
# - Claude: SANDBOX/claude/critique.md

# 5. Compile round 2
ai debate compile --mode standard
# Updates: round_2.md (critiques)

# 6. Human reads all proposals + critiques
vim SANDBOX/DEBATE/round_1.md
vim SANDBOX/DEBATE/round_2.md

# 7. Human writes verdict
vim SANDBOX/DEBATE/verdict.md
# Fill template: Decision, Rationale, Implementation Notes

# 8. Publish verdict
ai debate publish
# Validates verdict → Copies to THINK/CONSENSUS.md

# 9. Codex implements decision
# Creates: SANDBOX/codex/patch.diff

# 10. Apply & Verify
ai sandbox apply codex
ai verify dev

# 11. Promote (consensus exists, no --force needed)
ai promote

# 12. Deploy & Close
ai deploy prod
ai verify prod
ai close
```

---

## 11. ✅ Compliance Checklist

### For Developers (Implementing WP1-WP7):

Before implementing any WP, verify:
- [ ] This SESSION_CONTRACT.md has been read
- [ ] Design Decisions (Q1-Q4) are understood
- [ ] Structure matches Section 1 (Canonical Session Structure)
- [ ] Rules match Section 2 (Non-Negotiable Rules)
- [ ] State machine matches Section 6
- [ ] Patch validation matches Section 8

### For Commands (CLI Implementation):

Every command MUST:
- [ ] Respect trust boundaries (Section 5)
- [ ] Update state via atomic operations (never direct writes to .state/)
- [ ] Log significant actions to events.ndjson
- [ ] Enforce gates (scope, verify, consensus)
- [ ] Validate inputs (patch format, file paths, JSON schemas)

### For Agents (Human or AI):

Agents MUST:
- [ ] Write only to their designated SANDBOX/<agent>/ folder
- [ ] NOT write directly to DO/dev/, DO/prod/, CONTROL/, .state/
- [ ] Use patch.diff format for code changes (unified, no binary)
- [ ] Follow debate workflow (proposal → verdict → publish)

---

## 12. 🚧 Future Enhancements (Out of Scope for WP0-WP7)

**Deferred to Phase 2:**
- **WP8:** Agent API Layer (programmatic agent invocation)
- **WP9:** Orchestrator (automated multi-agent workflows)
- **Advanced State Machine:** More states (RESEARCH, DEBATE phases)
- **Automated Verdict:** AI-assisted verdict generation (still requires human approval)
- **File Permissions:** OS-level enforcement of trust boundaries
- **Resource Limits:** Disk quotas for SANDBOX/

**These are NOT required for Phase 1 (WP0-WP7). Current scope is manual orchestration with clear safety boundaries.**

---

## 13. 📚 References

**Related Documents:**
- `.ai/PRIMER.md` - Quick start guide
- `.ai/MASTER_BLUEPRINT.md` - Architecture overview
- `sessions/00_2025-12-21_implement_agent_sandbox/THINK/07_DESIGN_DECISIONS.md` - Decision rationale
# (Note: Legacy TODO plans from early sessions have been archived and are no longer required for current workflows.)

**Work Packages:**
- **WP0:** This document (Spec Lock)
- **WP1:** Scaffold Generator (creates this structure)
- **WP2:** State Engine (enforces state machine)
- **WP3:** Debate Compiler (implements debate workflow)
- **WP4:** Single Ingress (enforces patch.diff validation)
- **WP5:** Verify & Promote (enforces gates)
- **WP6:** Close & Cleanup (enforces close gate)
- **WP7:** E2E Testing (validates entire contract)

---

## 14. 🔒 Contract Status

**Version:** v0.5 / Phase 6.1
**Status:** 🔒 **LOCKED** - This is the canonical specification
**Last Updated:** 2025-12-21
**Approved By:** Trinity Protocol Team (Gemini, Claude, Codex)

**Changes to this contract require:**
1. Team consensus
2. Version increment
3. Migration plan (if breaking changes)
4. Update to all referencing documents

---

**This contract is now in effect. All implementations MUST comply.**

**Questions?** Refer to this document first. If still unclear, consult team.

---

**🌌 Trinity Protocol - Session Contract v0.5**
