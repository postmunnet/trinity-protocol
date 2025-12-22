# 🌌 Trinity Protocol

<div align="center">

**AI-Native Operating System for Multi-Agent Development**

[![Version](https://img.shields.io/badge/version-0.5-blue.svg)](https://github.com/yourusername/trinity-protocol)
[![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*Stop Chatting. Start Orchestrating.*

[Quick Start](#-quick-start) •
[Features](#-features) •
[Installation](#-installation) •
[Documentation](#-documentation) •
[Contributing](#-contributing)

</div>

---

## 🤔 The Problem

Working with AI today means **chatting** — which leads to 3 critical problems:

| Problem | Description |
|---------|-------------|
| **🧠 Amnesia** | After 100 messages, AI loses context |
| **🎭 Hallucination** | No safety net for code generation |
| **👻 No Audit Trail** | Can't track who did what, when |

### Pain Points & Resolution Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      PAIN POINTS & RESOLUTION                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ╔═══════════════════════════════════════════════════════════════════════╗   │
│  ║                    😰 BEFORE: Chat-Based AI Work                       ║   │
│  ╠═══════════════════════════════════════════════════════════════════════╣   │
│  ║                                                                        ║   │
│  ║   👤 Human                          🤖 AI                              ║   │
│  ║      │                                 │                               ║   │
│  ║      │  "Fix the auth bug"             │                               ║   │
│  ║      │────────────────────────────────▶│                               ║   │
│  ║      │                                 │                               ║   │
│  ║      │  "Here's some code..."          │                               ║   │
│  ║      │◀────────────────────────────────│                               ║   │
│  ║      │                                 │                               ║   │
│  ║      │  "Actually, also add logging"   │                               ║   │
│  ║      │────────────────────────────────▶│                               ║   │
│  ║      │                                 │                               ║   │
│  ║      │  "What was the original task?"  │  ← 🧠 AMNESIA!               ║   │
│  ║      │◀────────────────────────────────│                               ║   │
│  ║      │                                 │                               ║   │
│  ║      │  (AI generates code with        │                               ║   │
│  ║      │   hardcoded API key)            │  ← 🎭 HALLUCINATION!         ║   │
│  ║      │◀────────────────────────────────│                               ║   │
│  ║      │                                 │                               ║   │
│  ║      │  "Who changed this file?"       │                               ║   │
│  ║      │  "When was this deployed?"      │  ← 👻 NO AUDIT!              ║   │
│  ║      │  "???"                          │                               ║   │
│  ║                                                                        ║   │
│  ║   RESULT: 😱 Chaos, Security Risks, Blame Game                        ║   │
│  ╚═══════════════════════════════════════════════════════════════════════╝   │
│                                                                               │
│                                    │                                          │
│                                    │  Trinity Protocol                        │
│                                    ▼                                          │
│                                                                               │
│  ╔═══════════════════════════════════════════════════════════════════════╗   │
│  ║                    😎 AFTER: Trinity Orchestration                     ║   │
│  ╠═══════════════════════════════════════════════════════════════════════╣   │
│  ║                                                                        ║   │
│  ║   ┌─────────────────────────────────────────────────────────────────┐ ║   │
│  ║   │                     SESSION: Fix Auth Bug                        │ ║   │
│  ║   │                                                                  │ ║   │
│  ║   │  THINK/                    SANDBOX/                  DO/         │ ║   │
│  ║   │  ┌──────────────┐         ┌──────────────┐         ┌─────────┐  │ ║   │
│  ║   │  │ CONSENSUS.md │         │ gemini/      │         │snapshot/│  │ ║   │
│  ║   │  │              │         │ claude/      │         │ dev/    │  │ ║   │
│  ║   │  │ ✅ Context   │         │ codex/       │         │ prod/   │  │ ║   │
│  ║   │  │    Preserved │         │   │          │         │         │  │ ║   │
│  ║   │  │              │         │   ▼          │         │         │  │ ║   │
│  ║   │  │ 🧠 SOLVED!   │         │ patch.diff───┼────────▶│ ✅      │  │ ║   │
│  ║   │  └──────────────┘         └──────────────┘         └─────────┘  │ ║   │
│  ║   │                                                                  │ ║   │
│  ║   │  .state/                                                         │ ║   │
│  ║   │  ┌──────────────────────────────────────────────────────────┐   │ ║   │
│  ║   │  │ • verify_dev.json   ← 🎭 SOLVED! Safety gates block      │   │ ║   │
│  ║   │  │ • verify_prod.json     secrets, syntax errors            │   │ ║   │
│  ║   │  │ • events.ndjson     ← 👻 SOLVED! Complete audit trail    │   │ ║   │
│  ║   │  └──────────────────────────────────────────────────────────┘   │ ║   │
│  ║   └─────────────────────────────────────────────────────────────────┘ ║   │
│  ║                                                                        ║   │
│  ║   RESULT: 🎉 Safe, Traceable, Reproducible                            ║   │
│  ╚═══════════════════════════════════════════════════════════════════════╝   │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Problem → Solution Mapping

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     PROBLEM → SOLUTION MAPPING                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────┐         ┌─────────────────────────────────────────┐ │
│  │ 🧠 AMNESIA          │         │ 📦 SESSION-BASED CONTEXT                │ │
│  │                     │         │                                          │ │
│  │ • Context lost      │ ──────▶ │ • THINK/CONSENSUS.md persists decisions │ │
│  │ • Repeat yourself   │         │ • .state/ tracks progress               │ │
│  │ • Start over        │         │ • Session = Complete unit of work       │ │
│  └─────────────────────┘         └─────────────────────────────────────────┘ │
│                                                                               │
│  ┌─────────────────────┐         ┌─────────────────────────────────────────┐ │
│  │ 🎭 HALLUCINATION    │         │ 🔒 SAFETY GATES (3 Locks)               │ │
│  │                     │         │                                          │ │
│  │ • Bad code          │ ──────▶ │ • Syntax check (php -l, eslint)         │ │
│  │ • Secrets leaked    │         │ • Secret scan (API keys, passwords)     │ │
│  │ • No validation     │         │ • Scope guard (path validation)         │ │
│  │                     │         │ • Single ingress (patch.diff only)      │ │
│  └─────────────────────┘         └─────────────────────────────────────────┘ │
│                                                                               │
│  ┌─────────────────────┐         ┌─────────────────────────────────────────┐ │
│  │ 👻 NO AUDIT TRAIL   │         │ ⛓️ TAMPER-EVIDENT LOGGING               │ │
│  │                     │         │                                          │ │
│  │ • Who did what?     │ ──────▶ │ • events.ndjson (immutable log)         │ │
│  │ • When?             │         │ • session_state.json (state machine)    │ │
│  │ • Can't rollback    │         │ • verify_*.json (gate results)          │ │
│  │                     │         │ • DO/snapshot/ (immutable backup)       │ │
│  └─────────────────────┘         └─────────────────────────────────────────┘ │
│                                                                               │
│  ┌─────────────────────┐         ┌─────────────────────────────────────────┐ │
│  │ 🤯 AGENT CHAOS      │         │ 🤖 SANDBOXED AGENTS                     │ │
│  │                     │         │                                          │ │
│  │ • Agents conflict   │ ──────▶ │ • SANDBOX/gemini/ (isolated)            │ │
│  │ • No coordination   │         │ • SANDBOX/claude/ (isolated)            │ │
│  │ • Overwrite work    │         │ • SANDBOX/codex/ (isolated)             │ │
│  │                     │         │ • DEBATE/ (structured consensus)        │ │
│  └─────────────────────┘         └─────────────────────────────────────────┘ │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Before/After Comparison

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        BEFORE vs AFTER                                        │
├───────────────────────────────────┬──────────────────────────────────────────┤
│          😰 BEFORE                │          😎 AFTER (Trinity)              │
├───────────────────────────────────┼──────────────────────────────────────────┤
│                                   │                                          │
│  Chat window = your workspace     │  Session folder = your workspace         │
│                                   │                                          │
│  Context in AI's memory (lost)    │  Context in THINK/*.md (persisted)       │
│                                   │                                          │
│  Code pasted in chat              │  Code in SANDBOX/agent/patch.diff        │
│                                   │                                          │
│  "Trust me, it works"             │  ai verify dev → PASS/FAIL               │
│                                   │                                          │
│  Copy-paste to production         │  ai promote (requires gates)             │
│                                   │                                          │
│  "Who broke prod?"                │  events.ndjson shows exactly who/when    │
│                                   │                                          │
│  Start over when AI forgets       │  ai status show → resume anytime         │
│                                   │                                          │
│  Multiple agents = chaos          │  Each agent in isolated sandbox          │
│                                   │                                          │
│  No review process                │  ai debate compile → human verdict       │
│                                   │                                          │
├───────────────────────────────────┼──────────────────────────────────────────┤
│  RISK: High 🔴                    │  RISK: Low 🟢                            │
│  TRACEABILITY: None               │  TRACEABILITY: 100%                      │
│  REPRODUCIBILITY: Impossible      │  REPRODUCIBILITY: Guaranteed             │
└───────────────────────────────────┴──────────────────────────────────────────┘
```

---

## 💡 The Solution

**Trinity Protocol** transforms AI collaboration from chat to **orchestration**:

- 📦 **Sessions** — Isolated workspaces for each task
- 🤖 **Agent Sandboxes** — Safe spaces for Gemini, Claude, Codex to work
- 🔒 **3 Locks** — SSOT, Smart Gates, Audit Trail
- ✅ **Safety Gates** — Verify before deploy

---

## ✨ Features

### 🆕 v0.5 Highlights

| Feature | Description |
|---------|-------------|
| **Agent Sandboxes** | Parallel workspaces for each AI agent |
| **Debate Workflow** | Agents propose → Human decides → Consensus |
| **Single Ingress** | Only `patch.diff` can modify code |
| **Session State** | Crash-resumable local state |
| **Safety Gates** | Syntax, secrets, risk verification |

### 🔒 Trinity "3 Locks"

```
┌─────────────────────────────────────────────────────┐
│                    TRINITY 3 LOCKS                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔒 SSOT          Single Source of Truth            │
│     └── SESSION_CONTRACT.md, CONSENSUS.md           │
│                                                      │
│  🚪 Smart Gates   Automated Verification            │
│     └── Syntax, Secrets, Risk Scoring               │
│                                                      │
│  ⛓️ Audit Trail   Tamper-Evident Logging            │
│     └── events.ndjson, state/*.json                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/trinity-protocol.git
cd trinity-protocol/.ai

# 2. Setup (creates venv, installs deps)
bash setup.sh
source .venv/bin/activate

# 3. Create your first session
python3 -m cli.main session new "My First Task"

# 4. Snapshot current state
python3 -m cli.main snapshot run

# 5. Make changes in DO/dev/ or use Agent Sandboxes

# 6. Verify & Promote
python3 -m cli.main verify dev
python3 -m cli.main promote
python3 -m cli.main verify prod
python3 -m cli.main close run

# Orchestrator (optional)
# Runs the full workflow programmatically (see docs/USER_GUIDE.md)
python .ai/examples/simple_orchestrator.py --task "Fix Auth Bug" \
  --patch sessions/examples/2025-12-22_sandbox_demo/SANDBOX/codex/patch.diff
```

---

## 📦 Installation

### Prerequisites

- **Python 3.8+**
- **Git**
- **macOS / Linux** (Windows WSL supported)

### Option 1: Fresh Install

```bash
# Clone repository
git clone https://github.com/yourusername/trinity-protocol.git
cd trinity-protocol/.ai

# Run setup
bash setup.sh
source .venv/bin/activate

# Verify installation
python3 -m cli.main --help
```

### Option 2: Add to Existing Project

```bash
# Copy .ai folder to your project
cp -r /path/to/trinity/.ai /path/to/your/project/

# Update configuration
cd /path/to/your/project/.ai
# Edit ssot.yaml: set project_root to your project path

# Run setup
bash setup.sh
source .venv/bin/activate
```

---

## 📂 Project Structure

```
.ai/                                    # 🌌 Trinity Control Plane (872 KB)
│
├── 📄 Core Specifications
│   ├── README.md                       # This file
│   ├── SESSION_CONTRACT.md             # v0.5 Canonical Spec (21 KB)
│   ├── MASTER_BLUEPRINT.md             # Architecture + 3 Locks (13 KB)
│   ├── PRIMER.md                       # 2-min Quick Reference
│   ├── ssot.yaml                       # Configuration (project_root, etc.)
│   ├── LICENSE                         # MIT License
│   └── CONTRIBUTING.md                 # Contribution Guidelines
│
├── 📂 cli/                             # 🔧 CLI Implementation (172 KB)
│   ├── main.py                         # Entry point + command registration
│   ├── commands/                       # 10 Active Commands
│   │   ├── session.py                  # Session management (new, list)
│   │   ├── snapshot.py                 # Backup project state
│   │   ├── debate.py                   # Multi-agent debate (compile, publish)
│   │   ├── sandbox.py                  # Single ingress (apply, clean)
│   │   ├── verify.py                   # Safety gates (dev, prod, selftest)
│   │   ├── promote.py                  # Dev → Prod promotion
│   │   ├── close.py                    # Close session (requires verify)
│   │   ├── deploy.py                   # Deploy to environment
│   │   ├── status.py                   # Show current state
│   │   └── unlock.py                   # Force-break session lock
│   ├── core/                           # Core Modules
│   │   ├── state.py                    # State machine (INIT→EDITING→VERIFIED→DONE)
│   │   ├── patch.py                    # Diff validation + scope guard
│   │   ├── fs.py                       # Atomic file operations
│   │   ├── ssot.py                     # Configuration loader
│   │   └── template_loader.py          # Session template engine
│   └── tests/                          # Unit Tests
│       ├── test_basic.py               # Basic CLI tests
│       ├── test_patch_apply.py         # Patch validation tests
│       ├── test_state_engine.py        # State machine tests
│       └── test_integration_smoke.py   # E2E integration tests
│
├── 📂 templates/                       # 📋 Session Templates (172 KB)
│   ├── session/                        # v0.5 Canonical Structure
│   │   ├── THINK/                      # 👤 Human Planning Zone
│   │   │   ├── 00_CONTEXT.md           # Project context
│   │   │   ├── 01_PROMPT.md            # Task description
│   │   │   ├── 02_SCOPE.md             # Work boundaries
│   │   │   ├── 03_ACCEPTANCE.md        # Success criteria
│   │   │   └── CONSENSUS.md            # Human decisions (required for promote)
│   │   │
│   │   ├── SANDBOX/                    # 🤖 Agent Workspaces (Disposable)
│   │   │   ├── gemini/                 # Gemini: Research & Analysis
│   │   │   │   ├── research.md
│   │   │   │   ├── analysis.md
│   │   │   │   └── proposal.md
│   │   │   ├── claude/                 # Claude: Planning & Safety
│   │   │   │   ├── review.md
│   │   │   │   ├── critique.md
│   │   │   │   └── proposal.md
│   │   │   ├── codex/                  # Codex: Implementation
│   │   │   │   ├── implementation.md
│   │   │   │   ├── proposal.md
│   │   │   │   └── patch.diff          # ⚡ Single ingress to DO/dev
│   │   │   └── DEBATE/                 # Compiled Debate Artifacts
│   │   │       ├── round_1.md
│   │   │       ├── round_2.md
│   │   │       ├── round_3.md
│   │   │       └── verdict.md          # Human final decision
│   │   │
│   │   ├── DO/                         # 🚀 Execution Zone
│   │   │   ├── snapshot/               # Immutable backup (created by ai snapshot)
│   │   │   ├── dev/                    # Development (← patch.diff applied here)
│   │   │   └── prod/                   # Production (← ai promote only)
│   │   │
│   │   ├── CONTROL/                    # 📊 Metadata
│   │   │   ├── META.json               # Session metadata
│   │   │   ├── VERIFY.md               # Verification results
│   │   │   └── LIVE_MONITOR.md         # Real-time status
│   │   │
│   │   └── .state/                     # ⚙️ Session-Local State (System-Only)
│   │       ├── session_state.json      # State machine (INIT/EDITING/VERIFIED/DONE)
│   │       ├── debate_state.json       # Debate progress
│   │       ├── verify_dev.json         # Dev verification result
│   │       ├── verify_prod.json        # Prod verification result
│   │       └── events.ndjson           # Audit trail
│   │
│   └── agents/                         # Agent-specific templates
│       ├── gemini/
│       ├── claude/
│       └── codex/
│
├── 📂 docs/                            # 📚 Documentation (284 KB)
│   ├── USER_GUIDE.md                   # Complete v0.5 workflow guide ⭐
│   ├── E2E_TEST_GUIDE.md               # Testing scenarios ⭐
│   ├── USER_MANUAL.md                  # Command reference
│   ├── AI_SETUP_GUIDE.md               # AI-assisted installation
│   ├── INSTALLATION_GUIDE.md           # Manual installation
│   ├── WHAT_YOU_GET.md                 # Benefits & ROI
│   ├── GITHUB_GUIDE.md                 # Publishing guide
│   ├── ARCHITECTURE_DIAGRAM.md         # 13 ASCII diagrams (64 KB)
│   ├── WEB_DASHBOARD_PLAN.md           # Future dashboard spec
│   ├── PRODUCTION_READINESS_CHECKLIST.md
│   └── README.md                       # Docs index
│
├── 📂 policies/                        # 🛡️ Safety Rules (20 KB)
│   ├── safety.yaml                     # Risk scoring matrix
│   ├── gates.yaml                      # Verification gate definitions
│   ├── rbac.yaml                       # Role-based access control
│   └── PROTOCOL.md                     # Protocol rules
│
├── 📂 schemas/                         # 📐 JSON Schemas (20 KB)
│   ├── session.schema.json
│   ├── verify_report.schema.json
│   └── ...
│
├── 📂 state/                           # ⚙️ Global State (24 KB)
│   ├── status.json                     # Current session status
│   ├── verify_report.json              # Last verification
│   └── events.ndjson                   # Global audit trail
│
├── 📂 memory/                          # 🧠 Knowledge Base (32 KB)
│   ├── INDEX.md                        # Knowledge index
│   ├── DECISIONS.md                    # Architecture decisions
│   └── TOPIC_MAP.md                    # Knowledge graph
│
├── 📂 audit/                           # 📜 Audit Logs (8 KB)
│   ├── events.ndjson                   # Immutable event log
│   └── locks.json                      # Lock registry
│
├── 📂 sessions/                        # 📦 Session Storage
│   ├── active/                         # Current sessions
│   └── archive/                        # Completed sessions
│
├── 📂 testing/                         # 🧪 Test Fixtures
│   └── canaries/                       # Test files for verification
│
├── 📂 archive/                         # 🗄️ Archived Files
│   └── legacy_docs/                    # Old documentation
│
├── setup.sh                            # 🚀 One-click installer
└── requirements.txt                    # Python dependencies
```

### Session Lifecycle

```
sessions/2025-12-22_my_task/
│
├── THINK/           👤 Human writes goals, scope, acceptance criteria
│   └── CONSENSUS.md    Required for promote
│
├── SANDBOX/         🤖 Agents work in isolation
│   ├── gemini/         Research
│   ├── claude/         Planning
│   └── codex/          Implementation → patch.diff
│
├── DO/              🚀 Execution (system-controlled)
│   ├── snapshot/       Backup (immutable)
│   ├── dev/            ← patch.diff applied here
│   └── prod/           ← ai promote only
│
├── CONTROL/         📊 Metadata (system-written)
│
└── .state/          ⚙️ State machine (system-only)
    └── session_state.json: INIT → EDITING → VERIFIED → DONE
```

---

## 🔧 CLI Commands

| Command | Description |
|---------|-------------|
| `ai session new "<name>"` | Create session with SANDBOX/ |
| `ai snapshot run` | Backup project state |
| `ai debate compile` | Compile agent proposals |
| `ai debate publish` | Publish verdict to consensus |
| `ai sandbox apply <agent>` | Apply patch.diff to DO/dev |
| `ai sandbox clean` | Archive/remove SANDBOX |
| `ai verify dev` | Verify DO/dev |
| `ai verify prod` | Verify DO/prod |
| `ai promote` | Promote dev → prod |
| `ai close run` | Close session |
| `ai status show` | Show current state |
| `ai unlock` | Force-break lock |

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [SESSION_CONTRACT.md](SESSION_CONTRACT.md) | 📜 Canonical Spec (v0.5) |
| [PRIMER.md](PRIMER.md) | ⚡ 2-min Quick Start |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 📚 Complete Guide |
| [docs/E2E_TEST_GUIDE.md](docs/E2E_TEST_GUIDE.md) | 🧪 Testing Scenarios |
| [MASTER_BLUEPRINT.md](MASTER_BLUEPRINT.md) | 🏗️ Architecture |
| [docs/ARCHITECTURE_DIAGRAM.md](docs/ARCHITECTURE_DIAGRAM.md) | 📊 13 Diagrams |

---

## 🔄 Workflow Diagrams

### Main Workflow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           TRINITY PROTOCOL WORKFLOW                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────┐   │
│  │ 1. SESSION  │───▶│ 2. SNAPSHOT │───▶│ 3. AGENTS WORK IN SANDBOX/      │   │
│  │    NEW      │    │             │    │    ┌─────────┐ ┌─────────┐      │   │
│  │             │    │ Project ──▶ │    │    │ Gemini  │ │ Claude  │      │   │
│  │ Creates:    │    │ DO/snapshot │    │    │Research │ │Planning │      │   │
│  │ • THINK/    │    │             │    │    └────┬────┘ └────┬────┘      │   │
│  │ • SANDBOX/  │    │             │    │         │           │           │   │
│  │ • DO/       │    │             │    │         ▼           ▼           │   │
│  │ • .state/   │    │             │    │    ┌─────────────────────┐      │   │
│  └─────────────┘    └─────────────┘    │    │      Codex          │      │   │
│                                         │    │   Implementation    │      │   │
│                                         │    │   ↓ patch.diff      │      │   │
│                                         │    └─────────────────────┘      │   │
│                                         └─────────────────────────────────┘   │
│                                                          │                    │
│                                                          ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────┐   │
│  │ 8. CLOSE    │◀───│ 7. VERIFY   │◀───│ 4. SANDBOX APPLY                │   │
│  │             │    │    PROD     │    │                                  │   │
│  │ Requires:   │    │             │    │ patch.diff ──▶ DO/dev/          │   │
│  │ verify_prod │    │ Gates:      │    │ (Single Ingress)                │   │
│  │ = PASS      │    │ • Syntax    │    │                                  │   │
│  │             │    │ • Secrets   │    │ Scope Guard:                     │   │
│  │ Sets state: │    │ • Risk      │    │ • Validates unified diff         │   │
│  │ DONE        │    │             │    │ • Checks path boundaries         │   │
│  └─────────────┘    └─────────────┘    └─────────────────────────────────┘   │
│        │                  ▲                           │                       │
│        │                  │                           ▼                       │
│        │            ┌─────────────┐    ┌─────────────────────────────────┐   │
│        │            │ 6. PROMOTE  │◀───│ 5. VERIFY DEV                   │   │
│        │            │             │    │                                  │   │
│        │            │ Requires:   │    │ Gates:                           │   │
│        │            │ • CONSENSUS │    │ • Syntax check                   │   │
│        │            │ • verify_dev│    │ • Secret scan                    │   │
│        │            │   = PASS    │    │ • Forbidden files                │   │
│        │            │             │    │                                  │   │
│        │            │ DO/dev ──▶  │    │ Output:                          │   │
│        │            │ DO/prod     │    │ .state/verify_dev.json           │   │
│        │            └─────────────┘    └─────────────────────────────────┘   │
│        ▼                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ✅ SESSION COMPLETE → Archived to sessions/archive/                    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW DIAGRAM                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                          INPUT SOURCES                                   │ │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │ │
│  │  │  Human   │    │  Gemini  │    │  Claude  │    │  Codex   │          │ │
│  │  │   👤     │    │   🔍     │    │   🛡️     │    │   ⚡     │          │ │
│  │  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘          │ │
│  │       │               │               │               │                 │ │
│  │       ▼               ▼               ▼               ▼                 │ │
│  │  ┌──────────┐    ┌──────────────────────────────────────────┐          │ │
│  │  │ THINK/   │    │              SANDBOX/                     │          │ │
│  │  │          │    │  ┌────────┐  ┌────────┐  ┌────────┐      │          │ │
│  │  │ CONSENSUS│    │  │gemini/ │  │claude/ │  │codex/  │      │          │ │
│  │  │   .md    │    │  │*.md    │  │*.md    │  │*.md    │      │          │ │
│  │  └────┬─────┘    │  └────────┘  └────────┘  │patch   │      │          │ │
│  │       │          │                          │.diff   │      │          │ │
│  │       │          │                          └───┬────┘      │          │ │
│  │       │          └──────────────────────────────┼───────────┘          │ │
│  └───────┼─────────────────────────────────────────┼──────────────────────┘ │
│          │                                         │                        │
│          │         ┌───────────────────────────────┘                        │
│          │         │                                                        │
│          ▼         ▼                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        PROCESSING PIPELINE                               ││
│  │                                                                          ││
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            ││
│  │  │ SANDBOX      │────▶│ VERIFY DEV   │────▶│ PROMOTE      │            ││
│  │  │ APPLY        │     │              │     │              │            ││
│  │  │              │     │ ┌──────────┐ │     │ Requires:    │            ││
│  │  │ patch.diff   │     │ │ Syntax   │ │     │ • CONSENSUS  │            ││
│  │  │    ↓         │     │ │ Secrets  │ │     │ • verify_dev │            ││
│  │  │ DO/dev/      │     │ │ Risk     │ │     │   PASS       │            ││
│  │  └──────────────┘     │ └──────────┘ │     └──────┬───────┘            ││
│  │                       └──────────────┘            │                     ││
│  │                                                   ▼                     ││
│  │                       ┌──────────────┐     ┌──────────────┐            ││
│  │                       │ VERIFY PROD  │◀────│ DO/dev ──▶   │            ││
│  │                       │              │     │ DO/prod      │            ││
│  │                       └──────┬───────┘     └──────────────┘            ││
│  │                              │                                          ││
│  └──────────────────────────────┼──────────────────────────────────────────┘│
│                                 │                                           │
│                                 ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                          OUTPUT / STATE                                  ││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────┐    ││
│  │  │                        .state/                                   │    ││
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │    ││
│  │  │  │session_state │  │ verify_dev   │  │ verify_prod  │           │    ││
│  │  │  │    .json     │  │   .json      │  │   .json      │           │    ││
│  │  │  │              │  │              │  │              │           │    ││
│  │  │  │ INIT→EDITING │  │ PASS/FAIL    │  │ PASS/FAIL    │           │    ││
│  │  │  │ →VERIFIED    │  │ + details    │  │ + details    │           │    ││
│  │  │  │ →DONE        │  │              │  │              │           │    ││
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘           │    ││
│  │  │                                                                  │    ││
│  │  │  ┌──────────────┐  ┌──────────────┐                             │    ││
│  │  │  │debate_state  │  │ events       │                             │    ││
│  │  │  │   .json      │  │  .ndjson     │                             │    ││
│  │  │  │              │  │              │                             │    ││
│  │  │  │ Debate       │  │ Audit Trail  │                             │    ││
│  │  │  │ Progress     │  │ (immutable)  │                             │    ││
│  │  │  └──────────────┘  └──────────────┘                             │    ││
│  │  └─────────────────────────────────────────────────────────────────┘    ││
│  │                                                                          ││
│  │  ┌───────────────────────────────────────┐                              ││
│  │  │            DO/ (Artifacts)            │                              ││
│  │  │  ┌───────────┐ ┌─────┐ ┌──────┐      │                              ││
│  │  │  │ snapshot/ │ │dev/ │ │prod/ │      │                              ││
│  │  │  │(immutable)│ │     │ │      │      │                              ││
│  │  │  └───────────┘ └─────┘ └──────┘      │                              ││
│  │  └───────────────────────────────────────┘                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### State Machine Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          SESSION STATE MACHINE                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                         ┌─────────────────┐                                   │
│                         │                 │                                   │
│                         │      INIT       │  ← ai session new                 │
│                         │                 │                                   │
│                         └────────┬────────┘                                   │
│                                  │                                            │
│                                  │ ai snapshot / ai sandbox apply             │
│                                  │                                            │
│                                  ▼                                            │
│                         ┌─────────────────┐                                   │
│                    ┌───▶│                 │◀───┐                              │
│                    │    │    EDITING      │    │                              │
│                    │    │                 │    │                              │
│                    │    └────────┬────────┘    │                              │
│                    │             │             │                              │
│    ai sandbox apply│             │ ai verify   │ verify FAIL                  │
│    (more changes)  │             │ (dev/prod)  │ (retry allowed)              │
│                    │             │             │                              │
│                    │             ▼             │                              │
│                    │    ┌─────────────────┐    │                              │
│                    │    │                 │    │                              │
│                    └────│    VERIFIED     │────┘                              │
│                         │                 │                                   │
│                         └────────┬────────┘                                   │
│                                  │                                            │
│                                  │ ai close (requires verify_prod PASS)       │
│                                  │                                            │
│                                  ▼                                            │
│                         ┌─────────────────┐                                   │
│                         │                 │                                   │
│                         │      DONE       │  → Session archived               │
│                         │                 │                                   │
│                         └─────────────────┘                                   │
│                                                                               │
│  ═══════════════════════════════════════════════════════════════════════════ │
│                                                                               │
│  State Transitions:                                                           │
│  ┌────────────┬─────────────────────┬─────────────────────────────────────┐  │
│  │ From       │ To                  │ Trigger                             │  │
│  ├────────────┼─────────────────────┼─────────────────────────────────────┤  │
│  │ (none)     │ INIT                │ ai session new                      │  │
│  │ INIT       │ EDITING             │ ai snapshot / ai sandbox apply      │  │
│  │ EDITING    │ EDITING             │ ai sandbox apply (more changes)     │  │
│  │ EDITING    │ VERIFIED            │ ai verify dev/prod (PASS)           │  │
│  │ VERIFIED   │ EDITING             │ ai verify (FAIL) / more changes     │  │
│  │ VERIFIED   │ DONE                │ ai close (requires verify_prod)     │  │
│  └────────────┴─────────────────────┴─────────────────────────────────────┘  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Trust Boundaries Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           TRUST BOUNDARIES                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ 👤 HUMAN-ONLY WRITE ZONE                                                 │ │
│  │    (Full Trust - Human Decision Required)                                │ │
│  │                                                                          │ │
│  │    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │ │
│  │    │ .ai/policies/    │  │ THINK/           │  │ SANDBOX/DEBATE/  │    │ │
│  │    │                  │  │                  │  │ verdict.md       │    │ │
│  │    │ • safety.yaml    │  │ • CONSENSUS.md   │  │                  │    │ │
│  │    │ • gates.yaml     │  │ • 00_CONTEXT.md  │  │ Human final      │    │ │
│  │    │ • rbac.yaml      │  │ • 01_PROMPT.md   │  │ decision         │    │ │
│  │    └──────────────────┘  └──────────────────┘  └──────────────────┘    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ 🤖 AGENT-SANDBOXED WRITE ZONE                                            │ │
│  │    (Isolated - Each Agent in Own Space)                                  │ │
│  │                                                                          │ │
│  │    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │ │
│  │    │ SANDBOX/       │  │ SANDBOX/       │  │ SANDBOX/       │          │ │
│  │    │ gemini/        │  │ claude/        │  │ codex/         │          │ │
│  │    │                │  │                │  │                │          │ │
│  │    │ 🔍 Gemini ONLY │  │ 🛡️ Claude ONLY │  │ ⚡ Codex ONLY  │          │ │
│  │    │                │  │                │  │                │          │ │
│  │    │ • research.md  │  │ • review.md    │  │ • impl.md      │          │ │
│  │    │ • analysis.md  │  │ • critique.md  │  │ • proposal.md  │          │ │
│  │    │ • proposal.md  │  │ • proposal.md  │  │ • patch.diff ★ │          │ │
│  │    └────────────────┘  └────────────────┘  └───────┬────────┘          │ │
│  │                                                     │                   │ │
│  │                          ★ Single Ingress ──────────┘                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                              │                                │
│                                              ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ ⚙️ SYSTEM-ONLY WRITE ZONE                                                │ │
│  │    (CLI Commands Only - No Direct Write)                                 │ │
│  │                                                                          │ │
│  │    ┌────────────────────┐  ┌────────────────────┐                       │ │
│  │    │ .state/            │  │ DO/                │                       │ │
│  │    │                    │  │                    │                       │ │
│  │    │ • session_state    │  │ • snapshot/        │ ← ai snapshot         │ │
│  │    │ • debate_state     │  │   (immutable)      │                       │ │
│  │    │ • verify_dev       │  │                    │                       │ │
│  │    │ • verify_prod      │  │ • dev/             │ ← ai sandbox apply    │ │
│  │    │ • events.ndjson    │  │   (single ingress) │                       │ │
│  │    │                    │  │                    │                       │ │
│  │    │ Written by:        │  │ • prod/            │ ← ai promote ONLY     │ │
│  │    │ CLI commands only  │  │   (promote only)   │                       │ │
│  │    └────────────────────┘  └────────────────────┘                       │ │
│  │                                                                          │ │
│  │    ┌────────────────────┐  ┌────────────────────┐                       │ │
│  │    │ CONTROL/           │  │ SANDBOX/DEBATE/    │                       │ │
│  │    │                    │  │ (except verdict)   │                       │ │
│  │    │ • META.json        │  │                    │                       │ │
│  │    │ • VERIFY.md        │  │ • round_*.md       │ ← ai debate compile   │ │
│  │    │ • LIVE_MONITOR.md  │  │   (compiled)       │                       │ │
│  │    └────────────────────┘  └────────────────────┘                       │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

### Development Setup

```bash
git clone https://github.com/yourusername/trinity-protocol.git
cd trinity-protocol/.ai
bash setup.sh
source .venv/bin/activate

# Run tests
pytest cli/tests/ -v
```

### Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- Follow PEP 8 for Python
- Add docstrings to functions
- Write tests for new features

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Gemini** - Research & Analysis
- **Claude** - Planning & Safety
- **Codex** - Implementation
- All contributors and early adopters

---

## 📊 Status

| Metric | Value |
|--------|-------|
| **Version** | v0.5 / Phase 6.1 |
| **Implementation** | 100% (7/7 Work Packages) |
| **Tests** | ✅ Passing |
| **Documentation** | ✅ Complete |
| **Production Ready** | ✅ Yes |

---

<div align="center">

**🌌 Trinity Protocol**

*Infrastructure for Multi-Agent Development*

[⬆ Back to Top](#-trinity-protocol)

</div>
