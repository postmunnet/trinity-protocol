---
title: "Trinity Bootstrap Pack v1.0 (English)"
subtitle: "Minimal pack to scaffold Trinity into a new project"
language: English
version: 1.0.0-draft
status: draft
last-updated: 2026-04-28
phase: 0.5
note: "Translation of ../00b_BOOTSTRAP_PACK.md"
solves: "Copy ai-docs/Trinity to a new project → AI doesn't know short codes"
---

# Trinity Bootstrap Pack v1.0 (English)

> **Solves:** *"Copy 2 folders to a new project, AI doesn't know the standard short codes immediately (vvv)."*

---

## 0. Goal

After running `install.sh` in a new project — **every AI agent must immediately know:**
- What short codes are (`lll/vvv/nnn/gogogo/rrr`)
- The workflow to follow
- Available tools
- Policies that must not be violated
- Where the memory layer (ai-docs) lives

**Without telling the AI first** — open a session, work right away.

---

## 1. Why This Exists

### Today's reality
- AI tools (Claude Code/Codex/Gemini/Cursor) only read **entrypoint files** at the project root
- Short codes are buried deep in `ai-docs/core/SHORT_CODES.md`
- Without an entrypoint pointing to short codes → AI doesn't know

### What the Bootstrap Pack solves
- Inline short codes in entrypoint (CLAUDE.md/AGENTS.md/GEMINI.md)
- Set up minimal `.ai/` + `ai-docs/` that AI sees immediately
- Customize per-project (project name, tech stack, paths)

---

## 2. Pack Contents

```
trinity-bootstrap-pack/
├── README.md                       ← Pack docs
├── install.sh                      ← Main install script
├── verify-install.sh               ← Sanity check
├── templates/
│   ├── CLAUDE.md.template          ← Claude Code entrypoint (inline short codes)
│   ├── AGENTS.md.template          ← Codex CLI entrypoint
│   ├── GEMINI.md.template          ← Gemini CLI entrypoint
│   └── WARP.md.symlink             ← Symlinks to CLAUDE.md
├── ai-docs/                        ← Minimal ai-docs
│   ├── QUICK_START.md
│   ├── SHORT_CODES.md              ← Authoritative short codes spec
│   ├── CORE_RULES.md               ← Mandatory blockers
│   └── WORKFLOW.md                 ← 5-step workflow
└── .ai/                            ← Minimal Trinity kernel
    ├── ssot.yaml                   ← Single Source of Truth
    ├── tools.yaml                  ← Tool registry (empty)
    ├── policies/
    │   ├── safety.yaml
    │   └── verifier-rules.yaml
    ├── graphs/
    │   └── standard.yaml
    └── schemas/
        └── (placeholder)
```

---

## 3. Entrypoint Templates

### 3.1 `CLAUDE.md.template`

```markdown
---
title: "{{PROJECT_NAME}} — Trinity-enabled"
trinity-version: 2.0
last-updated: {{YYYY-MM-DD}}
---

# {{PROJECT_NAME}}

> 🤖 Trinity-enabled project. AI agents start by reading this file + running `lll`.

---

## ⛔ READ FIRST (Mandatory < 1 min)

1. **vvv before nnn** — Verify before planning (100% enforcement)
2. **Read actual code** — Evidence-based, no assumptions
3. **No production write without approval** — Always ask

📖 Full rules: [`ai-docs/CORE_RULES.md`](ai-docs/CORE_RULES.md)

---

## 🚀 Quick Start (Session Start)

```bash
type: lll        # see project status + session start
```

---

## 📋 Short Codes (Inline — AI must know immediately)

| Code | Action | When |
|------|--------|------|
| `lll` | Status report (project + git + memory) | Session start |
| `vvv` | Verify (5 mandatory questions, evidence-based) | Before any analysis |
| `nnn` | Plan (detailed, file-by-file) | After verify |
| `gogogo` | Execute plan | After plan approved |
| `rrr` | Retrospective (structured + memory update) | After task done |

**The Critical Rule:**
> `vvv` MUST come before `nnn`. Skipping = invalid session.

📖 Full spec: [`ai-docs/SHORT_CODES.md`](ai-docs/SHORT_CODES.md)

---

## 📊 Project Info

- **Name:** {{PROJECT_NAME}}
- **Tech Stack:** {{TECH_STACK}}
- **Type:** {{PROJECT_TYPE}}

---

## 🗂 Trinity Layout

```
{{PROJECT_NAME}}/
├── CLAUDE.md / AGENTS.md / GEMINI.md   ← AI entrypoints (you are here)
├── .ai/                                 ← Trinity kernel
│   ├── ssot.yaml
│   ├── tools.yaml
│   ├── policies/
│   ├── graphs/
│   └── sessions/
├── ai-docs/                             ← Knowledge Brain
│   ├── QUICK_START.md
│   ├── SHORT_CODES.md
│   ├── CORE_RULES.md
│   ├── WORKFLOW.md
│   ├── retrospectives/
│   └── real_lessons/
└── ... (your project code)
```

---

## ⚠️ Safety Rules

```text
✅ ALWAYS use vvv before nnn
✅ ALWAYS get approval before production
✅ ALWAYS check {{PROD_FOLDER}} is read-only
❌ NEVER skip verification
❌ NEVER deploy without approval
❌ NEVER edit {{PROD_FOLDER}}/ directly
```

---

## 🛠 Available Tools (CLI-first)

| Tool | Purpose |
|------|---------|
| `browser-cli` | Browser automation (DOM/screenshot/AJAX) |
| `ftp-cli` | FTP/SFTP file transfer (when installed; future standard organ) |
| (more from `.ai/tools.yaml`) | (see `trinity tool list`) |

---

## 🧠 Knowledge Brain (Memory)

- Past retrospectives: `ai-docs/retrospectives/`
- Lessons learned: `ai-docs/real_lessons/`
- Search: `memory-cli --cmd "search '<query>'"` (when memory-cli installed)

---

## 📚 Read When Needed

- [`ai-docs/QUICK_START.md`](ai-docs/QUICK_START.md) — 5 min onboarding
- [`ai-docs/WORKFLOW.md`](ai-docs/WORKFLOW.md) — full workflow
- [`ai-docs/CORE_RULES.md`](ai-docs/CORE_RULES.md) — mandatory rules
- [`.ai/ssot.yaml`](.ai/ssot.yaml) — project paths/config

---

**Trinity:** ai-docs = Knowledge Brain · vendor AI = Reasoning · CLI tools = Organs · Verifier = Judge · Artifacts = Truth
```

### 3.2 `AGENTS.md.template`

```markdown
# AGENTS.md — {{PROJECT_NAME}} (Codex CLI)

> 🤖 Codex CLI agent handbook. Read top-to-bottom before first action.

---

## ⛔ READ FIRST

1. `vvv before nnn` — Verify before plan
2. Read actual code — no assumptions
3. No production writes without approval

---

## 🚀 Quick Start

```bash
# Session start
ls -la .ai/sessions/active/    # current session

# Read mandatory docs
cat ai-docs/CORE_RULES.md
cat ai-docs/SHORT_CODES.md
```

---

## 📋 Short Codes (Inline — Codex must know)

| Code | Action |
|------|--------|
| `lll` | Status report (run before any task) |
| `vvv` | Verify (5 questions, evidence-based) — MANDATORY before nnn |
| `nnn` | Plan (detailed, file-by-file) |
| `gogogo` | Execute plan |
| `rrr` | Retrospective + memory update |

**Critical:** `vvv` MUST come before `nnn` — violations void session

---

## 🎯 Codex Specialty

Codex is best for: **Fast code generation, scaffolding, boilerplate**
Use Claude for: Deep analysis, planning, refactoring
Use Gemini for: Research, large context, web search

---

## 📊 Project

- **Name:** {{PROJECT_NAME}}
- **Tech:** {{TECH_STACK}}

---

## ⚠️ Safety

```text
❌ NEVER write to production without approval
❌ NEVER skip vvv
❌ NEVER use --no-verify on git
✅ ALWAYS check .ai/policies/ before risky ops
```

---

## 🛠 Tools

CLI-first ecosystem (tool-agnostic):
- `browser-cli` — browser ops
- `memory-cli` — search past retros (when installed)
- (see `.ai/tools.yaml`)

---

## 📚 Files to Read

- `ai-docs/SHORT_CODES.md` — full short code spec
- `ai-docs/WORKFLOW.md` — workflow detail
- `ai-docs/CORE_RULES.md` — mandatory blockers
- `.ai/ssot.yaml` — paths/config

---

**Trinity Brain Vocabulary:**
- ai-docs = Knowledge Brain
- vendor AI (Codex) = Reasoning Engine
- CLI tools = Organs
- Verifier = Judge
- Artifacts = Truth
```

### 3.3 `GEMINI.md.template`

```markdown
# GEMINI.md — {{PROJECT_NAME}} (Gemini CLI)

> 🔍 Gemini CLI agent guide. Optimized for research + large context.

---

## ⛔ READ FIRST

1. `vvv before nnn` — Verify before plan (mandatory)
2. Evidence-based analysis only
3. No production writes without approval

---

## 🚀 Quick Start

```bash
# Session start
ls -la .ai/sessions/active/

# Read essentials
cat ai-docs/CORE_RULES.md
cat ai-docs/SHORT_CODES.md
```

---

## 📋 Short Codes (Inline — Gemini must know)

| Code | Action |
|------|--------|
| `lll` | Status report (project + git + memory) |
| `vvv` | Verify (5 mandatory questions) — REQUIRED before nnn |
| `nnn` | Plan (detailed) |
| `gogogo` | Execute |
| `rrr` | Retrospective + memory update |

**Critical:** vvv before nnn (always)

---

## 🎯 Gemini Specialty

Best for:
- **Large context analysis** (1M tokens — load whole codebase)
- **Web research** (Google Search integration)
- **Documentation lookup** (real-time, no knowledge cutoff)

Use Claude for: deep reasoning · planning · refactoring
Use Codex for: fast code generation

---

## 📊 Project

- **Name:** {{PROJECT_NAME}}
- **Tech:** {{TECH_STACK}}

---

## ⚠️ Safety

```text
❌ NEVER auto-deploy
❌ NEVER skip vvv
✅ ALWAYS cite sources (web search results)
✅ ALWAYS verify file existence before referencing
```

---

## 🛠 Tools

CLI-first (tool-agnostic):
- `browser-cli` — browser
- `memory-cli` — search past knowledge (when installed)
- (see `.ai/tools.yaml`)

---

## 📚 Read

- `ai-docs/SHORT_CODES.md` · `ai-docs/WORKFLOW.md` · `ai-docs/CORE_RULES.md`
- `.ai/ssot.yaml`

---

**Vocabulary:** Knowledge Brain (ai-docs) · Reasoning Engine (Gemini) · Organs (CLI tools) · Judge (verifier) · Truth (artifacts)
```

---

## 4. Minimal ai-docs

### 4.1 `ai-docs/QUICK_START.md`

```markdown
# {{PROJECT_NAME}} — Quick Start (5 min)

## Workflow

```text
lll → vvv → nnn → gogogo → rrr
status verify plan  execute  reflect
```

## First Time

1. Type `lll` → see project status
2. Read `ai-docs/CORE_RULES.md` (1 min)
3. Read `ai-docs/SHORT_CODES.md` (3 min)
4. Start working

## Daily

```bash
# Morning
lll                  # status

# New task
vvv                  # verify understanding
nnn                  # plan
gogogo               # execute
rrr                  # retrospective
```

## Tools

```bash
browser-cli ...     # browser ops
memory-cli ...      # search past knowledge (when installed)
```

## See

- WORKFLOW.md — full
- SHORT_CODES.md — commands
- CORE_RULES.md — mandatory
```

### 4.2 `ai-docs/SHORT_CODES.md` (authoritative)

```markdown
# Short Codes — Authoritative Spec

> 5 commands. Required workflow order: lll → vvv → nnn → gogogo → rrr

## Overview

| Code | Action | Frequency | Time |
|------|--------|-----------|------|
| `lll` | Status report | Every session start | 30s |
| `vvv` | Verify (5 questions) | Every task — MANDATORY | 2-5 min |
| `nnn` | Plan (detailed) | Before code | 5-10 min |
| `gogogo` | Execute | After plan | varies |
| `rrr` | Retrospective | After task done | 5-10 min |

## The Critical Rule

```text
vvv MUST come before nnn.
Skipping vvv = invalid session.
Real case: skipping vvv = 3+ days wasted.
Using vvv = 30 minutes, correct first time.
```

---

## 1. `lll` — Status Report

**When:** Session start, after break, before changes

**Show:**
- Git status (branch, commits, changes)
- Project paths (dev/prod folders)
- Recent memory (last 3 retros)
- Pending tasks
- Critical reminders (vvv before nnn)

---

## 2. `vvv` — Verify

**When:** **Before any analysis** (mandatory)

**5 Mandatory Questions:**
1. What is the actual URL/path? (not assumed)
2. Which files handle this? (verified, not guessed)
3. Expected behavior? (clearly defined)
4. Evidence? (logs/tests/screenshots)
5. User confirmed? (no assumptions left)

**Output:** verify-report (PASS/RETRY/NEEDS_HUMAN)

---

## 3. `nnn` — Plan

**When:** After vvv passed

**Output:**
- Goal + risk level
- Files to modify (with reasons)
- Implementation steps
- Testing strategy
- Rollback plan

---

## 4. `gogogo` — Execute

**When:** After plan approved

**Behavior:**
- Follow plan step-by-step
- Test as you go
- Stop on failure
- Report progress

---

## 5. `rrr` — Retrospective

**When:** After task done

**Output (structured!):**
```yaml
goal: "..."
duration: "..."
status: "success | partial | blocked"
what_went_well: [...]
what_could_improve: [...]
mistakes: [...]
lessons: [...]
evidence: [...]
confidence: 0.0-1.0
tags: [...]
```

→ memory-cli auto-indexes (when installed)

---

## Combinations

```text
Quick check:    lll → vvv
Full workflow:  lll → vvv → nnn → gogogo → rrr
Bug fix:        lll → vvv → nnn → gogogo → rrr
```

## Never Skip

- `vvv` — always required
- `rrr` — for non-trivial changes

## Can Skip

- `lll` — if just checked
- `nnn` — for trivial (< 5 min)
```

### 4.3 `ai-docs/CORE_RULES.md`

```markdown
# Core Rules — Mandatory Blockers

> Read before any action. Violations void session.

## 🔴 BLOCKER 1: vvv before nnn (100%)

```text
NEVER plan (nnn) without verifying first (vvv).
Reason: assumption-based planning fails 70% of the time.
Real case: 3+ days wasted skipping vvv.
```

## 🔴 BLOCKER 2: Read actual code

```text
NEVER assume code structure. ALWAYS:
- grep / find files
- read file contents
- check actual behavior
```

## 🔴 BLOCKER 3: No prod write without approval

```text
NEVER write to production folder without explicit user approval.
Always ask: "Should I deploy this to {{PROD_FOLDER}}?"
```

## 🔴 BLOCKER 4: Evidence required

```text
NEVER conclude without:
- file paths verified
- logs/output checked
- test results
- screenshots (for UI)
```

## 🔴 BLOCKER 5: Single ingress

```text
NEVER write to multiple folders simultaneously.
Single ingress = `.ai/sandbox/apply` (when Trinity kernel ready)
```

## ⚠️ Violation Consequences

```text
- Session marked invalid
- Restart required
- Audit log captures violation
```
```

### 4.4 `ai-docs/WORKFLOW.md`

```markdown
# Workflow — 5-Step Process

```
lll → vvv → nnn → gogogo → rrr
```

## Step 0 (Session Start): `lll`
- Status report
- Pull memory context
- Identify current state

## Step 1 (Mandatory): `vvv`
- 5 questions
- Evidence collection
- User confirmation

## Step 2: `nnn`
- Detailed plan
- File-by-file changes
- Testing strategy
- Rollback plan
- Risk assessment

## Step 3: `gogogo`
- Execute systematically
- Test after each step
- Report progress
- Halt on failure

## Step 4: `rrr`
- What went well
- Mistakes made
- Lessons learned
- Memory update (auto via memory-cli when installed)

## Recovery Paths

```text
vvv fail → ask user, gather more evidence
nnn rejected → revise plan
gogogo fail recoverable → retry with fix
gogogo fail unrecoverable → rollback + escalate
```
```

---

## 5. Minimal `.ai/`

### 5.1 `.ai/ssot.yaml`

```yaml
# Single Source of Truth — paths, config, identity
version: 1
project:
  name: "{{PROJECT_NAME}}"
  type: "{{PROJECT_TYPE}}"
  tech_stack: "{{TECH_STACK}}"

paths:
  app_dir: "{{APP_DIR}}"
  dev_dir: "{{DEV_DIR}}"
  prod_dir: "{{PROD_DIR}}"
  ai_docs: "ai-docs"
  sessions: ".ai/sessions"
  retrospectives: "ai-docs/retrospectives"

policies:
  default_tier: "normal"
  require_human_for: ["promote", "deploy", "delete"]

trinity:
  version: "2.0"
  bootstrap_pack: "1.0"
```

### 5.2 `.ai/tools.yaml`

```yaml
version: 1
tools: []
# Add tools as installed:
# - name: browser-cli
#   path: <workspace-root>/browser-cli
#   bin: node <workspace-root>/browser-cli/index.js
#   schema_version: "2"
#   capabilities: [browser, dom, screenshot]
#   contract_version: "1.1"
```

### 5.3 `.ai/policies/safety.yaml`

```yaml
version: 1
forbidden_patterns:
  - "git push --force"
  - "DROP TABLE"
  - "rm -rf /"

require_approval:
  - production_write
  - schema_change
  - destructive_op

audit:
  log_file: ".ai/audit/events.ndjson"
  hash_chain: true
```

### 5.4 `.ai/policies/verifier-rules.yaml`

```yaml
version: 1
verifier_rules:
  default:
    required_evidence: [user_confirmation]
    pass_when: [all_questions_answered]
    needs_human_when: [unclear_intent]
  
  code_change:
    required_evidence: [file_path_verified, test_pass]
    pass_when: [tests_pass, scope_allowed]
    retry_when: [test_failed]
    needs_human_when: [production_write]
```

### 5.5 `.ai/graphs/standard.yaml`

```yaml
version: 1
states:
  - { name: READY, terminal: false }
  - { name: VERIFYING, terminal: false }
  - { name: PLANNING, terminal: false }
  - { name: EXECUTING, terminal: false }
  - { name: VERIFIED, terminal: false }
  - { name: DONE, terminal: true }
  - { name: FAILED, terminal: true }
  - { name: ESCALATED, terminal: true }

initial_state: READY

transitions:
  - { from: READY, to: VERIFYING, trigger: lll_done, decided_by: kernel }
  - { from: VERIFYING, to: PLANNING, trigger: vvv_pass, decided_by: verifier }
  - { from: VERIFYING, to: ESCALATED, trigger: vvv_needs_human, decided_by: verifier }
  - { from: PLANNING, to: EXECUTING, trigger: nnn_approved, decided_by: human }
  - { from: EXECUTING, to: VERIFIED, trigger: gogogo_done, decided_by: kernel }
  - { from: VERIFIED, to: DONE, trigger: rrr_done, decided_by: kernel }
  - { from: ANY, to: FAILED, trigger: policy_violation, decided_by: policy }
```

---

## 6. `install.sh`

```bash
#!/usr/bin/env bash
# Trinity Bootstrap Pack installer
# Usage: bash install.sh [target-dir]

set -euo pipefail

TARGET="${1:-.}"
PACK_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🌌 Trinity Bootstrap Pack Installer"
echo "===================================="
echo "Target: $TARGET"
echo ""

# ─── Prompt for project info ───
read -p "Project name: " PROJECT_NAME
read -p "Project type (web-app/api/cli/library): " PROJECT_TYPE
read -p "Tech stack (e.g. PHP+MySQL, Node+React): " TECH_STACK
read -p "App dir (default: ./): " APP_DIR
APP_DIR=${APP_DIR:-./}
read -p "Dev folder name (default: dev): " DEV_DIR
DEV_DIR=${DEV_DIR:-dev}
read -p "Prod folder name (default: prod): " PROD_DIR
PROD_DIR=${PROD_DIR:-prod}

# ─── Create folders ───
echo "📁 Creating folders..."
mkdir -p "$TARGET/.ai/policies"
mkdir -p "$TARGET/.ai/graphs"
mkdir -p "$TARGET/.ai/schemas"
mkdir -p "$TARGET/.ai/sessions"
mkdir -p "$TARGET/.ai/audit"
mkdir -p "$TARGET/ai-docs/retrospectives"
mkdir -p "$TARGET/ai-docs/real_lessons"

# ─── Render templates ───
echo "📝 Rendering templates..."

render() {
  local src="$1"
  local dst="$2"
  sed -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" \
      -e "s|{{PROJECT_TYPE}}|$PROJECT_TYPE|g" \
      -e "s|{{TECH_STACK}}|$TECH_STACK|g" \
      -e "s|{{APP_DIR}}|$APP_DIR|g" \
      -e "s|{{DEV_DIR}}|$DEV_DIR|g" \
      -e "s|{{PROD_DIR}}|$PROD_DIR|g" \
      -e "s|{{YYYY-MM-DD}}|$(date +%Y-%m-%d)|g" \
      -e "s|{{PROD_FOLDER}}|$PROD_DIR|g" \
      "$src" > "$dst"
}

render "$PACK_DIR/templates/CLAUDE.md.template" "$TARGET/CLAUDE.md"
render "$PACK_DIR/templates/AGENTS.md.template" "$TARGET/AGENTS.md"
render "$PACK_DIR/templates/GEMINI.md.template" "$TARGET/GEMINI.md"

# ─── Copy ai-docs ───
echo "📚 Installing ai-docs..."
for f in QUICK_START.md SHORT_CODES.md CORE_RULES.md WORKFLOW.md; do
  render "$PACK_DIR/ai-docs/$f" "$TARGET/ai-docs/$f"
done

# ─── Copy .ai/ ───
echo "⚙️  Installing Trinity kernel..."
render "$PACK_DIR/.ai/ssot.yaml" "$TARGET/.ai/ssot.yaml"
cp "$PACK_DIR/.ai/tools.yaml" "$TARGET/.ai/tools.yaml"
cp "$PACK_DIR/.ai/policies/safety.yaml" "$TARGET/.ai/policies/safety.yaml"
cp "$PACK_DIR/.ai/policies/verifier-rules.yaml" "$TARGET/.ai/policies/verifier-rules.yaml"
cp "$PACK_DIR/.ai/graphs/standard.yaml" "$TARGET/.ai/graphs/standard.yaml"

# ─── Symlink WARP.md → CLAUDE.md ───
echo "🔗 Creating WARP.md symlink..."
(cd "$TARGET" && ln -sf CLAUDE.md WARP.md)

# ─── Write README hint ───
cat > "$TARGET/.ai/INSTALLED" << EOF
Trinity Bootstrap Pack v1.0
Installed: $(date -Iseconds)
Project: $PROJECT_NAME
EOF

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Open AI tool (Claude Code/Codex/Cursor)"
echo "  2. Type 'lll' — should see project status"
echo "  3. Verify: bash $PACK_DIR/verify-install.sh $TARGET"
echo ""
echo "Read:"
echo "  - $TARGET/CLAUDE.md"
echo "  - $TARGET/ai-docs/QUICK_START.md"
echo ""
```

---

## 7. `verify-install.sh`

```bash
#!/usr/bin/env bash
# Verify Trinity Bootstrap Pack installation
# Usage: bash verify-install.sh [target-dir]

set -euo pipefail

TARGET="${1:-.}"
PASSED=0
FAILED=0

check() {
  local name="$1"
  local test_cmd="$2"
  if eval "$test_cmd" &>/dev/null; then
    echo "  ✓ $name"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ $name"
    FAILED=$((FAILED+1))
  fi
}

echo "🔍 Verifying Trinity installation at: $TARGET"
echo ""

echo "Entrypoints:"
check "CLAUDE.md exists" "[ -f '$TARGET/CLAUDE.md' ]"
check "AGENTS.md exists" "[ -f '$TARGET/AGENTS.md' ]"
check "GEMINI.md exists" "[ -f '$TARGET/GEMINI.md' ]"
check "WARP.md symlink" "[ -L '$TARGET/WARP.md' ]"

echo ""
echo "Inline short codes (CLAUDE.md):"
check "lll defined" "grep -q 'lll' '$TARGET/CLAUDE.md'"
check "vvv defined" "grep -q 'vvv' '$TARGET/CLAUDE.md'"
check "nnn defined" "grep -q 'nnn' '$TARGET/CLAUDE.md'"
check "gogogo defined" "grep -q 'gogogo' '$TARGET/CLAUDE.md'"
check "rrr defined" "grep -q 'rrr' '$TARGET/CLAUDE.md'"

echo ""
echo "ai-docs:"
check "QUICK_START.md" "[ -f '$TARGET/ai-docs/QUICK_START.md' ]"
check "SHORT_CODES.md" "[ -f '$TARGET/ai-docs/SHORT_CODES.md' ]"
check "CORE_RULES.md" "[ -f '$TARGET/ai-docs/CORE_RULES.md' ]"
check "WORKFLOW.md" "[ -f '$TARGET/ai-docs/WORKFLOW.md' ]"

echo ""
echo ".ai/ Trinity kernel:"
check "ssot.yaml" "[ -f '$TARGET/.ai/ssot.yaml' ]"
check "tools.yaml" "[ -f '$TARGET/.ai/tools.yaml' ]"
check "safety.yaml" "[ -f '$TARGET/.ai/policies/safety.yaml' ]"
check "verifier-rules.yaml" "[ -f '$TARGET/.ai/policies/verifier-rules.yaml' ]"
check "standard.yaml graph" "[ -f '$TARGET/.ai/graphs/standard.yaml' ]"

echo ""
echo "─────────────────────────"
echo "RESULT: $PASSED passed, $FAILED failed"

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
exit 0
```

---

## 8. Customization Guide

### 8.1 Per-project tuning

After install, edit:
- `.ai/ssot.yaml` — adjust paths
- `.ai/policies/safety.yaml` — add forbidden patterns
- `.ai/policies/verifier-rules.yaml` — domain-specific rules
- `ai-docs/CORE_RULES.md` — add project-specific blockers
- `CLAUDE.md` — fill `{{}}` placeholders not rendered by install.sh

### 8.2 Adding existing retros

```bash
# Copy existing retros (from previous Trinity project)
cp -r /path/to/old-retros/* ai-docs/retrospectives/

# Index (when memory-cli installed)
memory-cli --cmd "index ai-docs/retrospectives/"
```

### 8.3 Registering tools

Edit `.ai/tools.yaml`:

```yaml
tools:
  - name: browser-cli
    path: /path/to/browser-cli
    bin: node /path/to/browser-cli/index.js
    schema_version: "2"
    capabilities: [browser, dom, screenshot]
    contract_version: "1.1"
```

---

## 9. Examples

### 9.1 New Project (greenfield)

```bash
mkdir my-new-project
cd my-new-project
git init

bash /path/to/trinity-bootstrap-pack/install.sh .
# Answer prompts: name=my-new-project, type=web-app, ...

bash /path/to/trinity-bootstrap-pack/verify-install.sh .
# All checks ✓

# Open Claude Code in this dir
# Type: lll
# → Project status appears, AI knows short codes
```

### 9.2 Existing Project (migration)

```bash
cd existing-project

# Backup current AI configs
cp -r .claude .claude.backup
cp CLAUDE.md CLAUDE.md.backup 2>/dev/null || true

# Install
bash /path/to/trinity-bootstrap-pack/install.sh .

# Merge old configs (manual)
# - Move custom rules from CLAUDE.md.backup → ai-docs/CORE_RULES.md
# - Move retros to ai-docs/retrospectives/

# Verify
bash /path/to/trinity-bootstrap-pack/verify-install.sh .
```

### 9.3 Updating existing Trinity project to v2

```bash
cd <upstream-project>  # existing Trinity project

# Diff against pack
diff -r ai-docs/ /path/to/trinity-bootstrap-pack/ai-docs/

# Selective update
cp /path/to/trinity-bootstrap-pack/ai-docs/SHORT_CODES.md ai-docs/SHORT_CODES.md
# (review changes first)
```

---

## 10. Open Questions

1. install.sh — bash or Node script?
2. Templates use Handlebars/Mustache or sed?
3. Should there be a TUI installer?
4. How deep should verify script go — file existence only or schema validation?
5. Update path — how to do version migration?
6. Multi-language project — should install.sh auto-detect tech stack?
7. Bootstrap pack version vs Trinity version — sync?
8. Pack distribution — git submodule, npm, curl, brew?

---

## 11. Pain Point vs Solution

| Pain | Solution in Pack |
|------|------------------|
| "Copy ai-docs to new project, AI doesn't know short codes" | ✅ CLAUDE.md/AGENTS.md/GEMINI.md inline short codes |
| Every project needs manual setup | ✅ install.sh prompts + renders |
| Forget to sync rules between projects | ✅ Pack is single source — copy fresh |
| Codex/Gemini don't read CLAUDE.md | ✅ Separate AGENTS.md / GEMINI.md |
| Don't know if install is complete | ✅ verify-install.sh |
| Per-project custom paths | ✅ `{{APP_DIR}}` / `{{DEV_DIR}}` / `{{PROD_DIR}}` placeholders |

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master blueprint (Phase 0.5 referenced)
- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) — Tool ABI (used in `.ai/tools.yaml`)

---

## Changelog

- **v1.0.0-draft (2026-04-28)** — Initial draft as Phase 0.5 critical fix
