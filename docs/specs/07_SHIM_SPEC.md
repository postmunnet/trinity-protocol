---
title: "Trinity Shim Specification"
subtitle: "Vendor harness extension layer (universal + adapters)"
version: 1.0.0-draft
status: draft
last-updated: 2026-04-28
phase: 8
purpose: "Bridge between vendor AI harness and Trinity kernel without rebuilding harness"
---

# Trinity Shim Specification v1.0

> **Trinity Shim = "เปลือก" บาง ๆ บน vendor harness (Claude Code/Codex/Cursor/Gemini)**
> 
> ทำให้ vendor harness behave เหมือน Trinity workflow ritual — โดยไม่ต้องเขียน harness ใหม่

---

## 0. Status

- **Phase:** 8 (last layer ก่อน extension platform)
- **Depends on:** Phase 1-7 (all foundations)
- **Action namespace:** N/A (เป็น integration layer ไม่ใช่ tool ปกติ)
- **Pattern inspiration:** [`oh-my-claudecode`](https://github.com/?/oh-my-claudecode), [`oh-my-codex`](https://github.com/yeachan-heo/oh-my-codex), [`openclaude`](https://github.com/?/openclaude) — extension framework patterns (study only, see [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §3)

---

## 1. Why Shim (ไม่ใช่ harness ใหม่)

### Vendor harness แต่ละตัวมี extension model ของตัวเอง

| Vendor | Extension model |
|--------|----------------|
| Claude Code | Skills (`.claude/skills/`) + Hooks + Slash commands |
| Codex CLI | `AGENTS.md` instruction file + tool config |
| Cursor | Rules (`.cursor/rules/*.mdc`) + commands |
| Gemini CLI | `GEMINI.md` + system instructions |
| Warp | `WARP.md` (symlink to CLAUDE.md) |

### Shim Strategy

```
ใช้ extension ของแต่ละ vendor เป็น "adapter"
ส่งข้อมูลผ่าน → Trinity kernel CLI
รับ response กลับ → vendor harness แสดง
```

ไม่ทำ:
- ❌ Replace vendor harness
- ❌ Build own conversation loop
- ❌ Build own LLM call layer

ทำ:
- ✅ Inject Trinity context (memory, policies, graph state)
- ✅ Bind slash commands → Trinity CLI
- ✅ Log every action to Trinity audit
- ✅ Enforce Trinity workflow ritual

---

## 2. Architecture

```
┌─────────────────────────────────────────┐
│ User                                    │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│ Vendor Harness (Claude Code / Codex /   │
│ Cursor / Gemini)                        │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │ Trinity Shim (vendor-specific)   │    │
│  │  • Slash commands (/lll /vvv ...) │    │
│  │  • Hooks (pre/post response)      │    │
│  │  • Skills/Rules (instructions)    │    │
│  │  • Context injection             │    │
│  └────────┬─────────────────────────┘    │
└───────────┼──────────────────────────────┘
            │ shells out
            ▼
┌─────────────────────────────────────────┐
│ Trinity Universal Shell (trinity-shell) │
│  • Common interface                     │
│  • Routes to kernel CLI                 │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│ Trinity Kernel (.ai/cli)                │
└─────────────────────────────────────────┘
```

### 2 Layers

1. **Universal Shell** (`trinity-shell`) — single CLI ที่ vendor adapters เรียก
2. **Vendor Adapters** — vendor-specific config (skills/rules/instructions)

---

## 3. Universal Shell (`trinity-shell`)

### 3.1 Binary Interface

```bash
trinity-shell <command> [args] [--vendor=<vendor>] [--session=<id>]
```

### 3.2 Commands

| Command | Purpose |
|---------|---------|
| `lll` | Status report — pulls memory + git + state |
| `vvv` | Verify ritual — 5-question + memory search |
| `nnn` | Plan ritual — context-injected planning |
| `gogogo` | Execute — opens Trinity loop |
| `rrr` | Retrospective — calls retro-cli |
| `ccc` | Checkpoint — save loop state |
| `consult` | Search memory inline |
| `verify` | Run verifier on artifacts |
| `status` | Current run/session state |
| `escalate` | Trigger human escalation |

### 3.3 Examples

```bash
# Standard
trinity-shell lll
trinity-shell vvv "ทำ SEO ทั้งเว็บ"
trinity-shell nnn
trinity-shell gogogo
trinity-shell rrr

# Vendor-aware
trinity-shell lll --vendor=claude-code
trinity-shell consult "auth bug" --limit=5

# Session ops
trinity-shell status --session=sess_xyz
trinity-shell escalate "needs review"
```

### 3.4 Output Format

Default: human-readable Markdown (for vendor harness rendering)
With `--json`: JSON envelope (for programmatic consumption)

```bash
trinity-shell lll --json
# → JSON envelope per TOOL_CONTRACT
```

---

## 4. Vendor Adapter: Claude Code

### 4.1 Layout

```
.claude/
├── settings.local.json              ← permissions
├── skills/                           ← Trinity slash commands
│   ├── lll/
│   │   └── instructions.md
│   ├── vvv/
│   │   └── instructions.md
│   ├── nnn/
│   │   └── instructions.md
│   ├── gogogo/
│   │   └── instructions.md
│   └── rrr/
│       └── instructions.md
└── hooks/                            ← lifecycle hooks
    ├── pre-response.sh
    ├── post-response.sh
    └── on-tool-call.sh
```

### 4.2 Skill Example: `.claude/skills/lll/instructions.md`

```markdown
---
name: lll
description: Trinity status report (project + git + memory + recent retros)
---

When user types `lll`, do this:

1. Run: `trinity-shell lll --vendor=claude-code --json`
2. Parse the JSON response
3. Render the data as Thai-language status report
4. Show:
   - Git status
   - Recent retros (last 5)
   - Active session (if any)
   - Critical reminders (vvv before nnn)
   - Available tools

Always respond in Thai.
End with: "พร้อมรับงาน — พิมพ์ vvv เพื่อเริ่มตรวจสอบ"
```

### 4.3 Hook Example: `.claude/hooks/pre-response.sh`

```bash
#!/usr/bin/env bash
# Runs before Claude generates response
# Inject Trinity context

# Check if there's an active session
if [ -f ".ai/sessions/active/.id" ]; then
  SESSION_ID=$(cat .ai/sessions/active/.id)
  
  # Get current loop state
  trinity-shell status --session=$SESSION_ID --json > .claude/.tmp/loop_state.json
  
  # Search memory for similar past work
  USER_INPUT="$1"
  trinity-shell consult "$USER_INPUT" --limit=3 --json > .claude/.tmp/memory_hint.json
  
  # Inject as context
  echo "## Trinity Context"
  echo "Session: $SESSION_ID"
  echo "Loop state: $(cat .claude/.tmp/loop_state.json | jq -r '.data.current_state')"
  echo ""
  echo "Relevant past:"
  cat .claude/.tmp/memory_hint.json | jq -r '.data.results[] | "- " + .title'
fi
```

### 4.4 Hook Example: `.claude/hooks/on-tool-call.sh`

```bash
#!/usr/bin/env bash
# Runs after every tool invocation
# Audit log to events.ndjson

TOOL_NAME="$1"
TOOL_ARGS="$2"
TOOL_RESULT="$3"

trinity-shell audit-log \
  --event=tool_call \
  --tool="$TOOL_NAME" \
  --args="$TOOL_ARGS" \
  --result-sha256=$(echo "$TOOL_RESULT" | sha256sum | cut -d' ' -f1)
```

---

## 5. Vendor Adapter: Codex CLI

### 5.1 Approach

Codex CLI ไม่มี skills/hooks เหมือน Claude Code — ใช้ **`AGENTS.md`** + tool config

### 5.2 `AGENTS.md` (Trinity-aware)

```markdown
# AGENTS.md — {{PROJECT_NAME}} (Codex + Trinity)

## Trinity Workflow

When user types short codes, run trinity-shell:

| User input | Action |
|-----------|--------|
| `lll` | `trinity-shell lll --vendor=codex` |
| `vvv ...` | `trinity-shell vvv "$ARGS" --vendor=codex` |
| `nnn` | `trinity-shell nnn --vendor=codex` |
| `gogogo` | `trinity-shell gogogo --vendor=codex` |
| `rrr` | `trinity-shell rrr --vendor=codex` |

## Always

- Before any code write: `trinity-shell consult "$task"`
- After complete: `trinity-shell rrr`
- On uncertainty: `trinity-shell escalate "..."`

## Never

- ❌ Skip vvv before nnn
- ❌ Auto-deploy
- ❌ Edit production folder
```

### 5.3 Limitations vs Claude Code

- No real-time hooks → audit log via post-action
- No skill discovery → must instruct in AGENTS.md
- Tool calls → wrap CLI tools, not native dispatch

---

## 6. Vendor Adapter: Cursor

### 6.1 Layout

```
.cursor/
├── rules/                          ← MDC files (instruction context)
│   ├── trinity-workflow.mdc
│   ├── trinity-shortcodes.mdc
│   ├── trinity-safety.mdc
│   └── trinity-tools.mdc
└── commands/                       ← Cursor commands (if supported)
    └── trinity-lll.md
```

### 6.2 `.cursor/rules/trinity-workflow.mdc`

```mdc
---
description: Trinity workflow ritual (lll/vvv/nnn/gogogo/rrr)
globs: ["**/*"]
alwaysApply: true
---

# Trinity Workflow

Before any task, run mental check:
1. Did user run `lll`? If not, suggest it.
2. Has `vvv` been done for this goal? If not, run it.
3. Did `nnn` produce a plan? If not, create one.

For execution, use Trinity tools:
- File ops: vendor's Edit/Read/Write
- Browser: `node /path/to/browser-cli/index.js --cmd "..."`
- Memory: `node /path/to/memory-cli/index.js --cmd "..."`

After complete: write retro via `node /path/to/retro-cli/index.js`

## Critical
- vvv MUST come before nnn
- No production write without approval
- All tool outputs are JSON (parse before using)
```

---

## 7. Vendor Adapter: Gemini CLI

### 7.1 `GEMINI.md`

(Similar to AGENTS.md — see Bootstrap Pack templates)

### 7.2 System Instructions

Gemini supports `--system` flag — bake Trinity ritual:

```bash
gemini --system "$(cat .ai/gemini-system.md)" "user prompt"
```

`.ai/gemini-system.md`:
```markdown
You are an AI assistant working under Trinity workflow.

Required behaviors:
- Run `trinity-shell lll` at session start
- Always `vvv` before `nnn`
- Use CLI tools (browser-cli, memory-cli) for capabilities
- Write retro via `retro-cli` after task

Tools available:
- browser-cli (browser ops)
- memory-cli (knowledge search)
- ...

Never:
- Skip verification
- Auto-deploy
- Edit prod/
```

---

## 8. Slash Command Implementations

### 8.1 `/lll` Implementation Logic

```python
def cmd_lll(vendor):
    # 1. Project status
    git_status = run("git status --short")
    branch = run("git rev-parse --abbrev-ref HEAD")
    
    # 2. Trinity state
    session_id = read_active_session()
    if session_id:
        loop_state = call_kernel(f"loop status --session={session_id}")
    else:
        loop_state = None
    
    # 3. Memory recall (recent + relevant)
    recent = call_tool("memory-cli", "list --since=7d --limit=5")
    
    # 4. Pending tasks (TODO list, etc.)
    pending = scan_todos()
    
    # 5. Format output (vendor-aware)
    if vendor == "claude-code":
        return format_markdown(...)
    elif vendor == "codex":
        return format_concise(...)
    else:
        return format_default(...)
```

### 8.2 `/vvv` Implementation Logic

```python
def cmd_vvv(question, vendor):
    # 1. Search memory for similar past
    similar = call_tool("memory-cli", f"search '{question}' --type=retro")
    
    # 2. Check policies for this question type
    policy_hits = check_policies(question)
    
    # 3. Generate 5 mandatory questions
    questions = generate_5_questions(question)
    
    # 4. Ask user (vendor-specific UX)
    answers = await_user_answers(questions, vendor)
    
    # 5. Build verify report
    report = build_verify_report(question, similar, policy_hits, answers)
    
    # 6. Save artifact
    save_artifact(".ai/sessions/active/verify-report.json", report)
    
    # 7. Call verify-cli
    verdict = call_tool("verify-cli", "verify --rule-set=default")
    
    return verdict
```

### 8.3 `/gogogo` Implementation Logic

```python
def cmd_gogogo(vendor):
    # 1. Verify plan exists
    plan = read_plan()
    if not plan:
        return error("No plan — run nnn first")
    
    # 2. Open Trinity loop
    loop_id = call_kernel(f"loop start --plan={plan.id}")
    
    # 3. Vendor harness handles execution
    # (Trinity loop calls back via tools)
    
    # 4. Stream loop progress
    stream_loop_status(loop_id, vendor)
```

---

## 9. Audit Log Integration

### 9.1 Every Vendor Interaction → events.ndjson

```json
{
  "ts": "2026-04-28T...",
  "event": "shim_invocation",
  "vendor": "claude-code",
  "command": "lll",
  "session_id": "sess_xyz",
  "user_input_sha256": "...",
  "response_sha256": "...",
  "tools_called": ["memory-cli", "browser-cli"],
  "duration_ms": 1234,
  "prev_hash": "...",
  "hash": "..."
}
```

### 9.2 Tool Calls Within Vendor

When vendor harness calls Trinity tool (via shell):
```json
{
  "ts": "...",
  "event": "tool_call",
  "vendor": "claude-code",
  "tool": "memory-cli",
  "command": "search 'auth bug'",
  "run_id": "run_xyz",
  "outcome": "success",
  "result_artifacts": [...]
}
```

---

## 10. Configuration

### 10.1 Shim Config

`.ai/shim-config.yaml`:
```yaml
version: 1
trinity_shell_bin: "node /path/to/trinity-shell/index.js"

vendors:
  claude-code:
    enabled: true
    skills_dir: ".claude/skills"
    hooks_dir: ".claude/hooks"
    audit_hook: pre-response.sh
  
  codex-cli:
    enabled: true
    agents_md: "AGENTS.md"
  
  cursor:
    enabled: true
    rules_dir: ".cursor/rules"
  
  gemini-cli:
    enabled: true
    gemini_md: "GEMINI.md"
  
  warp:
    enabled: true
    config: "WARP.md"  # symlink

audit:
  log_all_invocations: true
  log_tool_calls: true
  hash_chain: true
```

---

## 11. Capability Matrix (Vendor Comparison)

| Capability | Claude Code | Codex CLI | Cursor | Gemini CLI |
|------------|------------|-----------|--------|-----------|
| Slash commands | ✅ Skills | ⚠️ via prompt | ⚠️ Commands | ❌ |
| Pre-response hooks | ✅ | ❌ | ❌ | ❌ |
| Post-response hooks | ✅ | ❌ | ❌ | ❌ |
| Tool call hooks | ✅ | ⚠️ | ❌ | ❌ |
| Permission UX | ✅ Real-time | ⚠️ | ⚠️ | ❌ |
| Streaming | ✅ | ✅ | ✅ | ✅ |
| MCP support | ✅ | ❌ | ⚠️ | ❌ |
| Custom system prompt | ✅ via skills | ✅ AGENTS.md | ✅ rules | ✅ |

→ **Claude Code = best harness for Trinity shim** (richest extension)

---

## 12. Lifecycle

### 12.1 Session Start (User opens Claude Code)

```
1. Claude Code reads CLAUDE.md (entrypoint)
   → Trinity shim is referenced
2. User types `lll`
   → Skill `lll` triggered
   → Calls trinity-shell lll
   → Returns markdown status
   → Claude Code renders
3. User types `vvv ...`
   → Skill `vvv` triggered
   → Etc.
```

### 12.2 Session End (User closes)

```
- Hook: post-session.sh runs
- trinity-shell session close --session=<id>
- Loop checkpointed, memory updated
- Audit log finalized
```

---

## 13. Anti-patterns

| ❌ Anti-pattern | ✅ Correct |
|-----------------|-----------|
| Build full harness | Use vendor harness + shim |
| Hardcode for Claude Code | Universal shell + adapters |
| Skip audit on shim calls | Log every invocation |
| Direct LLM call in shim | Let vendor handle LLM |
| Bake commands in code | Skills/MDC/AGENTS.md (data) |

---

## 14. Open Questions

1. trinity-shell language — Node, Python, or Bash?
2. Claude Code skills format — stable enough?
3. Cursor MDC — sufficient extension?
4. Streaming through shim — possible?
5. Vendor capability detection — auto?
6. Multi-vendor session — switch mid-flow?
7. Skill versioning — migrate?
8. Hook permissions — security concerns?
9. Codex AGENTS.md = single source — sync per project?
10. Universal command names — `/lll` vs `/trinity-lll`?

---

## 15. Implementation Sketch

```
trinity-shell/
├── index.js                       ← entry
├── lib/
│   ├── command-router.js
│   ├── vendor-detector.js
│   ├── kernel-bridge.js           ← calls .ai/cli
│   ├── memory-bridge.js           ← calls memory-cli
│   ├── audit-emitter.js
│   └── formatters/
│       ├── claude-code.js
│       ├── codex.js
│       ├── cursor.js
│       └── default.js
├── commands/
│   ├── lll.js
│   ├── vvv.js
│   ├── nnn.js
│   ├── gogogo.js
│   ├── rrr.js
│   ├── ccc.js
│   ├── consult.js
│   ├── verify.js
│   ├── status.js
│   └── escalate.js
└── adapters/
    ├── claude-code/
    │   ├── skills/
    │   │   ├── lll/
    │   │   ├── vvv/
    │   │   └── ...
    │   └── hooks/
    ├── codex/
    │   └── AGENTS.md.template
    ├── cursor/
    │   └── rules/
    └── gemini/
        └── GEMINI.md.template
```

---

## 16. Quick Reference

### Setup new project
```bash
# Bootstrap Pack already installs adapters
bash trinity-bootstrap-pack/install.sh .

# Verify shim works
trinity-shell --health
```

### Daily use (Claude Code)
```
User types: lll
→ skill lll triggers
→ trinity-shell lll --vendor=claude-code
→ Claude renders status
```

### Multi-vendor
```bash
# Same project, different sessions
# Claude Code session
trinity-shell lll --vendor=claude-code

# Codex CLI session
trinity-shell lll --vendor=codex

# Both share same .ai/sessions/, same audit log
```

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §3 (Harness 3 levels)
- [`00b_BOOTSTRAP_PACK.md`](00b_BOOTSTRAP_PACK.md) — installs adapter scaffolding
- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) — trinity-shell follows tool contract
- All other specs (kernel calls)

## Changelog

- **v1.0.0-draft (2026-04-28)** — Initial draft (Phase 8 — final layer before Extension Platform)
