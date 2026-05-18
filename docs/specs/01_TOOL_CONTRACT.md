---
title: "Trinity Tool Contract"
subtitle: "Universal CLI tool contract — POSIX of Trinity"
version: 1.1.0-draft
status: revised
last-updated: 2026-04-28
applies-to: All CLI tools in Trinity OS userland
reference-implementation: browser-cli
revision-notes: "v1.1 — added Action Namespace, Contract Compliance Test, MCP stance clarified as CLI-first default with optional bridge"
---

# Trinity Tool Contract v1.1

> **Universal contract for CLI tools in Trinity OS ecosystem**
>
> ถ้า tool ไม่ตามสัญญานี้ — Trinity kernel จะไม่ orchestrate ได้
> ถ้า tool ตามสัญญานี้ครบ — เสียบกับ Trinity ได้ทันทีโดยไม่ต้องแก้ kernel

---

## Public Freeze Status

Public ecosystem messaging should treat the Tool Contract as:

```text
Tool Contract v1.0 = freeze candidate
Current working spec = v1.1.0-draft
```

ก่อนประกาศ stable interface ต้อง freeze อย่างน้อย 10 เรื่องนี้:

1. Input envelope
2. Output envelope
3. Exit code meaning
4. Verdict schema
5. Artifact declaration
6. Error taxonomy
7. Retry semantics
8. Idempotency expectation
9. Audit log requirements
10. Security boundary

จนกว่า checklist นี้จะปิดครบ ห้ามสื่อสารว่า external tool interface เป็น
stable แล้ว ให้ใช้คำว่า **v1.0 freeze candidate** หรือ **v1.1 draft working
spec** แทน

---

## 0. Status & Compliance Levels

| Level | Description |
|-------|-------------|
| **MUST** | บังคับ — ขาดไม่ได้, kernel จะปฏิเสธ tool |
| **SHOULD** | ควรทำ — ขาดได้แต่ไม่แนะนำ |
| **MAY** | ทำเพิ่มก็ได้ — ตามความเหมาะสม |

Tool compliance assessment ทำผ่าน `trinity tool verify <tool-name>` (Phase 5+)

---

## 1. Scope

### 1.1 In Scope
- Binary entry point conventions
- Stdin/stdout JSON protocol
- Response envelope schema
- Universal CLI flags (`--config`, `--run-id`, `--log-file`, ...)
- Logging format (NDJSON)
- Policy tiers (safe / normal / aggressive)
- Error code conventions
- Schema versioning rules
- Discovery (`--list-commands`, `--describe`, `--health`)
- Helpers (YAML composition)
- Documentation requirements
- Test harness pattern
- Tool registry format

### 1.2 Out of Scope
- ❌ Tool internal architecture (each tool decides)
- ❌ Programming language (Node/Python/Rust/Go ทั้งหมดได้)
- ❌ External library choices
- ❌ Database choice (FTS5, ChromaDB, etc.)
- ❌ **MCP protocol as default core path** — Trinity is CLI-first by default.
  - Vendor harness's built-in tools (Read/Write/Edit/Bash) = ใช้ตามปกติ (ไม่กระทบ)
  - External MCP servers = optional bridge only, not the default control path
  - MCP-only capability ต้องถูก wrap ผ่าน Tool Contract envelope ก่อนเข้า audit chain
  - Default replacement: capability สำคัญควรมี CLI tool ตาม contract นี้

### 1.3 Non-goals
- ไม่ใช่ AI logic specification
- ไม่ใช่ workflow graph definition
- ไม่ใช่ kernel orchestration logic

---

## 2. Terminology

| Term | Definition |
|------|------------|
| **Tool** | CLI binary ที่ implement contract นี้ |
| **Verb / Command** | คำสั่งใน tool (e.g. `search`, `index`, `goto`) |
| **Run** | 1 invocation ของ tool (single command, REPL session, pipe batch) |
| **Run ID** | Unique identifier ของ run — สำหรับ trace correlation |
| **Envelope** | Response JSON wrapper (`ok`, `data`, `error`, `meta`) |
| **Artifact** | File/data ที่ tool สร้าง — เก็บไว้เป็น truth |
| **Policy** | Tier ที่จำกัดว่า command ไหนรันได้ (safe/normal/aggressive) |
| **Schema version** | Version ของ response format (`v1`, `v2`, ...) |
| **Helper** | YAML composition ของ commands ที่ใช้ซ้ำ |

---

## 3. Binary Interface

### 3.1 Entry Point (MUST)

```bash
<tool-name> [universal-flags] [tool-flags] [-- <command-args>]
```

**Examples:**
```bash
memory-cli --config configs/<upstream-project>.json --cmd "search 'auth bug'"
browser-cli --config configs/<upstream-project>.json --login backend
wordpress-cli --config configs/site.json --policy=safe
```

### 3.2 Execution Modes (MUST support all 4)

#### Mode A: Single Command (`--cmd`)
```bash
memory-cli --cmd "search 'auth bug'"
```
- รัน 1 command, exit
- Response เดียวออก stdout

#### Mode B: REPL (interactive)
```bash
memory-cli
> search auth
> get r123
> exit
```
- Read-Eval-Print loop
- Prompt `> `
- Each command = 1 response line
- `exit` ออก

#### Mode C: Pipe (stdin)
```bash
echo "search auth
get r123
exit" | memory-cli
```
- อ่านบรรทัดจาก stdin
- Run sequentially
- Each command = 1 response line stdout

#### Mode D: Run File
```bash
memory-cli --run-file batch.txt
```
- อ่านไฟล์ — ทุกบรรทัด = 1 command
- Run sequentially
- Skip `#` comments

### 3.3 Exit Codes (MUST)

| Code | Meaning |
|------|---------|
| `0` | Success (all commands ok) |
| `1` | Generic error (1+ command failed) |
| `2` | Invalid usage (bad flags, missing config) |
| `3` | Policy violation (command blocked by tier) |
| `4` | Configuration error (config file invalid) |
| `5` | Permission denied (filesystem, network) |
| `10` | Timeout |
| `20` | External dependency failure (e.g. SQLite locked) |
| `64-78` | Reserved (sysexits.h compatibility) |
| `100+` | Tool-specific |

### 3.4 stdin/stdout/stderr Discipline (MUST)

| Stream | Purpose | Format |
|--------|---------|--------|
| **stdin** | Commands input | Plain text (1 command per line) |
| **stdout** | Responses | JSON (1 envelope per line, NDJSON) |
| **stderr** | Human-readable diagnostics | Free-form |

**Critical:** stdout ต้องเป็น **machine-parseable JSON เท่านั้น** ห้ามมี log/debug/banner

---

## 4. Response Envelope

### 4.1 Success Envelope (MUST)

```json
{
  "ok": true,
  "command": "search",
  "action": "memory.search",
  "data": { "...": "tool-specific" },
  "artifacts": [
    { "type": "file", "path": "./out/result.json", "sha256": "..." }
  ],
  "error": null,
  "meta": {
    "tool": "memory-cli",
    "schema_version": "1",
    "run_id": "run_2026-04-28_xyz",
    "duration_ms": 42,
    "timestamp": "2026-04-28T12:34:56.789Z"
  }
}
```

> ⚠️ **`action` field (v1.1+)** — canonical namespaced verb (e.g. `memory.search`, `browser.screenshot`) — ดู §4a Action Namespace

### 4.2 Error Envelope (MUST)

```json
{
  "ok": false,
  "command": "search",
  "data": null,
  "artifacts": [],
  "error": {
    "code": "INDEX_NOT_FOUND",
    "message": "Memory index not initialized",
    "details": {
      "expected_path": "./.memory/index.db",
      "hint": "Run 'memory-cli index ./.claude/retrospectives/' first"
    },
    "recoverable": true
  },
  "meta": {
    "tool": "memory-cli",
    "schema_version": "1",
    "run_id": "run_2026-04-28_xyz",
    "duration_ms": 5,
    "timestamp": "2026-04-28T12:34:56.789Z"
  }
}
```

### 4.3 Field Reference

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `ok` | MUST | boolean | `true`=success, `false`=error |
| `command` | MUST | string | verb ที่ถูกเรียก (local name) |
| `action` | MUST (v1.1+) | string | canonical namespaced verb (`tool.verb`) |
| `data` | MUST | object\|null | tool-specific payload (null on error) |
| `artifacts` | MUST | array | files/data created (เก็บเป็น truth) |
| `error` | MUST | object\|null | null on success |
| `error.code` | MUST | string | UPPER_SNAKE_CASE |
| `error.message` | MUST | string | human-readable (Thai+English ok) |
| `error.details` | SHOULD | object | structured context |
| `error.recoverable` | SHOULD | boolean | retry หาย vs need human |
| `meta` | MUST | object | run metadata |
| `meta.tool` | MUST | string | tool name + version (`memory-cli@0.1.0`) |
| `meta.schema_version` | MUST | string | response schema version |
| `meta.run_id` | MUST | string | run correlation ID |
| `meta.duration_ms` | MUST | number | exec time |
| `meta.timestamp` | MUST | string | ISO 8601 UTC |

### 4.4 Artifact Object Schema

```json
{
  "type": "file" | "url" | "ref",
  "path": "./out/screenshot.png",
  "sha256": "abc123...",
  "size_bytes": 4096,
  "mime": "image/png",
  "metadata": {}
}
```

---

## 4a. Action Namespace (v1.1+)

### 4a.1 Why
- `screenshot` มีทั้งใน browser-cli, future wordpress-cli — **conflict!**
- `search` มีใน memory-cli, future grep-cli — **conflict!**
- Audit log ต้องระบุ canonical action สำหรับ correlation

### 4a.2 Format (MUST)

```text
<tool-namespace>.<verb>
```

- `<tool-namespace>` = lowercase, kebab-case (`browser`, `memory`, `wordpress`, `ftp`, `seo`)
- `<verb>` = lowercase, snake_case (`search`, `screenshot`, `fill_form`)

### 4a.3 Reserved Namespaces

| Namespace | Tool |
|-----------|------|
| `browser` | browser-cli |
| `memory` | memory-cli |
| `retro` | retro-cli |
| `verify` | verify-cli |
| `wordpress` | wordpress-cli |
| `ftp` | ftp-cli |
| `seo` | seo-cli |
| `code` | grep-cli (code search) |
| `deploy` | deploy-cli |
| `god` | god-team-cli |

### 4a.4 Examples

| Local verb | Action namespace |
|-----------|------------------|
| `goto` (browser-cli) | `browser.goto` |
| `screenshot` (browser-cli) | `browser.screenshot` |
| `search` (memory-cli) | `memory.search` |
| `learn` (memory-cli) | `memory.learn` |
| `validate` (retro-cli) | `retro.validate` |
| `assert_browser` (verify-cli) | `verify.assert_browser` |
| `put` (ftp-cli) | `ftp.put` |

### 4a.5 Rules

- Tool ต้อง emit `action` field ใน envelope ทุก response
- Tool ต้อง register namespace ใน `.ai/tools.yaml`
- Trinity kernel ต้อง dedupe by action — log canonical name
- `--list-commands` MUST return action namespace per verb

---

## 5. Stdin/Stdout Protocol

### 5.1 Line Discipline (MUST)
- Each input command = 1 line, terminated by `\n`
- Each output envelope = 1 line, terminated by `\n` (NDJSON)
- No multi-line JSON output — everything single-line

### 5.2 Encoding (MUST)
- UTF-8
- ASCII subset acceptable
- No BOM

### 5.3 Buffering (SHOULD)
- Stdout: line-buffered (flush after each envelope)
- Stderr: unbuffered (immediate diagnostic)
- Stdin: line-buffered (read complete commands)

### 5.4 Backpressure (MAY)
- Tools MAY honor `SIGPIPE` to halt cleanly
- Long-running commands SHOULD send heartbeat to stderr (not stdout)

---

## 6. Universal CLI Flags

### 6.1 Required Flags (MUST support)

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config <path>` | path | `./<tool-name>.config.json` | Config file |
| `--run-id <string>` | string | auto-generated | Run correlation |
| `--log-file <path>` | path | none | NDJSON log output |
| `--policy <tier>` | enum | `normal` | `safe` \| `normal` \| `aggressive` |
| `--response-schema <ver>` | string | `1` | Response schema version |
| `--cmd "<command>"` | string | none | Single command mode |
| `--run-file <path>` | path | none | Batch from file |

### 6.2 Standard Flags (SHOULD support)

| Flag | Description |
|------|-------------|
| `--help, -h` | Print help |
| `--version, -v` | Print version |
| `--list-commands` | Print available verbs (JSON) |
| `--describe <cmd>` | Print verb spec (JSON) |
| `--health` | Print health check (JSON) |
| `--quiet, -q` | Suppress stderr diagnostics |
| `--verbose` | Extra stderr diagnostics |
| `--dry-run` | Validate without side effects |

### 6.3 Reserved Flags (MAY use, but conventions apply)

| Flag | Convention |
|------|-----------|
| `--show` | Visual mode (e.g. headed browser) |
| `--cdp <url>` | CDP/external connection (browser-cli) |
| `--reuse` | Reuse existing resource |
| `--force` | Bypass safety checks (require aggressive policy) |
| `--watch` | Long-running watch mode |

### 6.4 Tool-specific Flags (MAY use any unprefixed name not above)

ห้ามชนกับ universal/standard/reserved

---

## 7. Configuration

### 7.1 Config File Format (MUST)
- JSON (preferred)
- YAML (acceptable if tool dependencies allow)

### 7.2 Standard Config Fields

```json
{
  "$schema": "https://trinity.local/schemas/tool-config-v1.json",
  "version": "1.0",
  "tool": "memory-cli",
  "run": {
    "default_policy": "normal",
    "default_log_file": "./logs/memory-cli.ndjson",
    "max_duration_ms": 60000
  },
  "paths": {
    "data_dir": "./.memory",
    "artifact_dir": "./out"
  },
  "tool_specific": {
    "...": "tool-defined"
  }
}
```

### 7.3 Config Resolution Order (MUST)

1. CLI flag explicit (`--config foo.json`)
2. ENV `<TOOL_NAME>_CONFIG`
3. CWD `./<tool-name>.config.json`
4. CWD `./configs/<tool-name>.json`
5. Built-in default

### 7.4 Config Schema Validation (SHOULD)

Tool ต้อง validate config ก่อน execute และ exit code `4` ถ้าไม่ผ่าน

---

## 8. Logging (NDJSON)

### 8.1 Log Format (MUST when `--log-file` given)

Each log line = JSON object on one line:

```json
{"ts":"2026-04-28T12:34:56.789Z","level":"INFO","tool":"memory-cli","run_id":"run_xyz","event":"command_start","command":"search","args":["auth bug"]}
{"ts":"2026-04-28T12:34:56.823Z","level":"DEBUG","tool":"memory-cli","run_id":"run_xyz","event":"db_query","sql":"SELECT ..."}
{"ts":"2026-04-28T12:34:56.831Z","level":"INFO","tool":"memory-cli","run_id":"run_xyz","event":"command_end","command":"search","duration_ms":42,"ok":true}
```

### 8.2 Required Fields per Log Line

| Field | Type | Description |
|-------|------|-------------|
| `ts` | string | ISO 8601 UTC |
| `level` | enum | `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `tool` | string | tool name |
| `run_id` | string | run correlation |
| `event` | string | event type (snake_case) |

### 8.3 Standard Events (SHOULD use)

| Event | When |
|-------|------|
| `run_start` | Tool process starts |
| `run_end` | Tool process exits |
| `command_start` | Verb begins execution |
| `command_end` | Verb finishes |
| `policy_violation` | Command blocked by tier |
| `artifact_created` | File written |
| `external_call` | DB/HTTP/exec invoked |
| `error_caught` | Exception handled |

### 8.4 Append-only (MUST)
- Log file = append-only NDJSON
- ห้ามแก้บรรทัดเก่า
- Rotation = สร้างไฟล์ใหม่ (ไม่ rewrite)

---

## 9. Policy Tiers

### 9.1 Tier Definitions (MUST honor)

| Tier | Allows | Use case |
|------|--------|----------|
| **safe** | Read-only verbs | Audit, status, search, get, list, describe |
| **normal** | + Write verbs | Standard work — index, learn, create, update |
| **aggressive** | + Destructive verbs | Migrations — delete, supersede, force, reset |

### 9.2 Verb Classification (MUST in `--describe`)

```json
{
  "verb": "delete",
  "tier_required": "aggressive",
  "destructive": true,
  "writes": true
}
```

### 9.3 Policy Enforcement (MUST)
- ก่อนรันทุก verb — check tier
- Block ด้วย exit code `3` + error envelope
- Log `policy_violation` event

```json
{
  "ok": false,
  "command": "delete",
  "error": {
    "code": "POLICY_VIOLATION",
    "message": "Verb 'delete' requires tier=aggressive, current=normal",
    "recoverable": false
  }
}
```

### 9.4 Policy Override (MAY)
- `--policy aggressive` flag = explicit ack
- ห้าม default = `aggressive`
- Tool MAY require additional confirmation (e.g. ENV `I_KNOW_WHAT_IM_DOING=1`)

---

## 10. Error Codes

### 10.1 Standard Codes (MUST use เหล่านี้สำหรับสถานการณ์ตรงกัน)

| Code | Meaning | Recoverable |
|------|---------|-------------|
| `INVALID_ARGS` | Bad command arguments | true |
| `INVALID_CONFIG` | Config file malformed | false |
| `MISSING_DEPENDENCY` | External tool not found | false |
| `POLICY_VIOLATION` | Tier insufficient | false |
| `PERMISSION_DENIED` | Filesystem/network forbidden | false |
| `RESOURCE_NOT_FOUND` | File/record missing | true |
| `RESOURCE_LOCKED` | Can't acquire lock | true |
| `RESOURCE_EXHAUSTED` | Disk/memory/quota | true |
| `EXTERNAL_FAILURE` | DB/HTTP/exec failed | true |
| `TIMEOUT` | Operation took too long | true |
| `SCHEMA_MISMATCH` | Response schema version wrong | false |
| `INTERNAL_ERROR` | Bug ใน tool | false |

### 10.2 Tool-specific Codes (MAY add)

- ใช้ prefix tool name: `MEMORY_INDEX_CORRUPT`, `BROWSER_PAGE_CRASH`
- UPPER_SNAKE_CASE
- Document ใน COMMAND_CONTRACT.md ของ tool

---

## 11. Schema Versioning

### 11.1 Versioning Rules (MUST)

- Schema version = string (e.g. `"1"`, `"2"`, `"1.1"`)
- Backward compat: `v2` tool MUST support `--response-schema=v1`
- Tool MUST embed `schema_version` ใน envelope `meta`

### 11.2 Breaking Changes Trigger (MUST bump major)

- ลบ field
- เปลี่ยน type ของ field
- เปลี่ยน semantic ของ field
- เพิ่ม required field

### 11.3 Non-breaking Changes (MAY bump minor)

- เพิ่ม optional field
- เพิ่ม enum value (clients SHOULD ignore unknown)

### 11.4 Deprecation (SHOULD)

- ประกาศ deprecation 1 major version ก่อนลบ
- Log `WARN` เมื่อ client ใช้ field ที่ deprecated

---

## 12. Discovery

### 12.1 `--list-commands` (MUST)

```bash
$ memory-cli --list-commands
```

```json
{
  "ok": true,
  "command": "list-commands",
  "data": {
    "tool": "memory-cli@0.1.0",
    "commands": [
      { "verb": "search", "tier": "safe", "description": "Hybrid search" },
      { "verb": "learn", "tier": "normal", "description": "Add document" },
      { "verb": "supersede", "tier": "aggressive", "description": "Mark obsolete" }
    ]
  },
  "error": null,
  "meta": { "...": "..." }
}
```

### 12.2 `--describe <verb>` (MUST)

```bash
$ memory-cli --describe search
```

```json
{
  "ok": true,
  "command": "describe",
  "data": {
    "verb": "search",
    "tier_required": "safe",
    "destructive": false,
    "writes": false,
    "args": [
      { "name": "query", "type": "string", "required": true, "description": "Search query" }
    ],
    "options": [
      { "name": "--limit", "type": "int", "default": 10 }
    ],
    "returns": {
      "type": "object",
      "schema": { "$ref": "schemas/search-response-v1.json" }
    },
    "examples": [
      "search 'auth bug'",
      "search 'login error' --limit=20"
    ]
  }
}
```

### 12.3 `--health` (SHOULD)

```bash
$ memory-cli --health
```

```json
{
  "ok": true,
  "command": "health",
  "data": {
    "tool": "memory-cli@0.1.0",
    "status": "ready",
    "checks": [
      { "name": "config_loaded", "ok": true },
      { "name": "db_connection", "ok": true, "details": { "path": "./.memory/index.db" } },
      { "name": "external_deps", "ok": true, "deps": ["sqlite3"] }
    ]
  }
}
```

---

## 13. Helpers (YAML)

### 13.1 Helper File Format (SHOULD support)

```yaml
# memory-helpers.yml
helpers:
  fresh-search:
    args: [query]
    description: "Reindex then search"
    steps:
      - reindex
      - search {query}
  
  weekly-stats:
    description: "Stats + recent learnings"
    steps:
      - stats
      - list --since=7d --tag=lesson
```

### 13.2 Invocation

```bash
memory-cli --cmd "helper fresh-search 'auth bug'"
```

### 13.3 Variable Interpolation (MAY)
- `{arg_name}` = positional arg
- `{$ENV_VAR}` = environment variable
- `{ts}` = timestamp
- ห้าม shell injection — escape always

---

## 14. Documentation Requirements

### 14.1 Required Files (MUST in each tool repo)

```
<tool-name>/
├── README.md                      ← User-facing intro
├── docs/
│   ├── ARCHITECTURE.md            ← Design overview, state model, phases
│   ├── COMMAND_CONTRACT.md        ← All verbs + response schema
│   ├── CONFIG_SCHEMA.md           ← Config file schema
│   ├── AI_AGENT_GUIDE.md          ← How AI should use this tool
│   ├── USER_GUIDE.md              ← Human user guide
│   ├── POLICY_TIERS.md            ← Tier mapping per verb
│   └── TROUBLESHOOTING.md         ← Common errors + fixes
├── schema/
│   ├── config.schema.json         ← JSON Schema for config
│   └── response-v<N>.schema.json  ← JSON Schema for envelope
├── tests/
│   ├── harness.js (or .py)        ← Unit tests (no external deps)
│   └── golden.js (or .py)         ← Integration test
├── package.json (or pyproject.toml)
└── CHANGELOG.md
```

### 14.2 Recommended Files (SHOULD)

```
├── docs/
│   ├── examples/                  ← End-to-end examples
│   ├── SHELL_ALIASES.md           ← Quick aliases
│   └── TMUX_INTEGRATION.md        ← Pane patterns
└── configs/
    └── <project>.json             ← Example config
```

### 14.3 Documentation Requirements per File

#### README.md (MUST contain)
- Tool name + version
- 1-paragraph description
- Setup (install + first run)
- Usage examples (single-cmd, REPL, pipe)
- Link to docs/

#### COMMAND_CONTRACT.md (MUST contain)
- Every verb with full schema
- Tier classification
- Argument list
- Return schema
- Examples
- Error codes specific to verb

#### AI_AGENT_GUIDE.md (MUST contain)
- When to use (decision tree)
- When NOT to use
- Common patterns
- Anti-patterns
- Composition with other Trinity tools

---

## 15. Test Harness Pattern

### 15.1 Unit Test Harness (MUST have)

File: `tests/harness.js` (or `.py`)

```javascript
#!/usr/bin/env node
// Minimal unit test harness — no external deps
const assert = require('assert');
const parser = require('../lib/parser');

let passed = 0, failed = 0;

function test(name, fn) {
  try { fn(); console.log(`✓ ${name}`); passed++; }
  catch (e) { console.log(`✗ ${name}: ${e.message}`); failed++; }
}

// ─── Parser ───
test('basic verb + arg', () => {
  const r = parser.parse('search auth');
  assert.strictEqual(r.verb, 'search');
});

// ... more tests

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
```

**Invocation:** `node tests/harness.js` — no external services

### 15.2 Golden Test (MUST have)

File: `tests/golden.js`

- Integration test against real dependency (DB, browser, etc.)
- Idempotent (cleanup before/after)
- Must run < 60 seconds
- Exit code = 0 on full pass

### 15.3 Schema Validation Test (SHOULD have)

- Validate every example response against `schema/response-v<N>.schema.json`
- Fail if envelope doesn't match

---

## 16. Tool Registry

### 16.1 Registry Format

File: `.ai/tools.yaml` (in TRINITY kernel root)

```yaml
version: 1
tools:
  - name: browser-cli
    path: /<home>/<user>/Downloads/yai_project/browser-cli
    bin: node /<home>/<user>/Downloads/yai_project/browser-cli/index.js
    schema_version: "2"
    capabilities: [browser, navigation, dom, screenshot, assertion]
    policy_default: normal
    health_check: --health
    contract_version: "1.0"
  
  - name: memory-cli
    path: /<home>/<user>/Downloads/yai_project/memory-cli
    bin: node /<home>/<user>/Downloads/yai_project/memory-cli/index.js
    schema_version: "1"
    capabilities: [search, index, recall, learn]
    policy_default: normal
    health_check: --health
    contract_version: "1.0"
  
  # ... more tools
```

### 16.2 Registry Operations (Trinity kernel)

```bash
trinity tool list                  # ดู tools ทั้งหมด
trinity tool register <path>       # เพิ่ม tool
trinity tool verify <name>         # ตรวจ contract compliance
trinity tool health <name>         # ตรวจ health
trinity tool capabilities <q>      # ค้น tool ที่มี capability
```

### 16.3 Capability Naming Convention

- lowercase
- hyphen-separated
- noun (resource) or verb (action)
- examples: `browser`, `dom-query`, `screenshot`, `search`, `index`, `delete`

---

## 16a. Contract Compliance Test (v1.1+)

### 16a.1 Why (MUST)
ถ้ามี TOOL_CONTRACT แต่ไม่มี automated test — tool จะ drift จาก contract เสมอ

### 16a.2 `trinity-contract-test` CLI

```bash
trinity-contract-test <tool-name>
```

ตัวอย่าง output:
```
Testing: memory-cli@0.1.0
─────────────────────────
Binary Interface
  ✓ stdin/stdout JSON discipline
  ✓ Exit codes match spec
  ✓ Single-cmd mode works
  ✓ REPL mode works
  ✓ Pipe mode works
  ✓ Run-file mode works

Universal Flags
  ✓ --config supported
  ✓ --run-id supported
  ✓ --log-file supported
  ✓ --policy supported
  ✓ --response-schema supported
  ✓ --cmd / --run-file supported

Discovery
  ✓ --help works
  ✓ --version works
  ✓ --list-commands returns valid JSON
  ✓ --describe <verb> returns valid JSON
  ✗ --health endpoint missing       ← FAIL

Response Envelope
  ✓ Success envelope schema valid
  ✓ Error envelope schema valid
  ✓ action field present (v1.1+)
  ✓ All required meta fields present

Logging
  ✓ NDJSON format valid
  ✓ Required fields per log line
  ✓ Standard events used

Policy
  ✓ Verbs classified in --describe
  ✓ Tier enforcement blocks correctly
  ✓ POLICY_VIOLATION error code used

Schema
  ✓ Backward compat (v1 supported)
  ✓ schema_version embedded

─────────────────────────
RESULT: 22/23 PASSED, 1 FAILED
```

### 16a.3 Test Categories (MUST run)

| Category | Tests |
|----------|-------|
| Binary Interface | exec modes, exit codes, stdio discipline |
| Universal Flags | all required flags accepted |
| Discovery | help/version/list-commands/describe/health |
| Response Envelope | success/error schema validation |
| Logging | NDJSON format + required fields |
| Policy | tier classification + enforcement |
| Schema | versioning + backward compat |
| Action Namespace | format + registry consistency (v1.1+) |

### 16a.4 Implementation

`trinity-contract-test` itself = CLI tool that:
- Spawns target tool with various inputs
- Validates outputs against schemas (JSON Schema)
- Reports per-test result + overall verdict
- Exit code: `0` if all pass, `1` if any fail

### 16a.5 CI Integration (SHOULD)

ทุก tool ใน registry ต้องรัน `trinity-contract-test` ใน CI:
- Pre-commit hook
- GitHub Actions / GitLab CI
- Block merge if fail

### 16a.6 Compliance Levels

| Level | Definition |
|-------|------------|
| **Bronze** | Pass binary interface + envelope tests |
| **Silver** | + Pass discovery + logging tests |
| **Gold** | + Pass policy + schema + namespace tests |
| **Platinum** | + Pass golden integration tests |

Trinity kernel SHOULD reject tools below Bronze in production registry

---

## 17. Compliance Checklist

ก่อน register tool ใน Trinity registry — tool ต้องผ่านทุกข้อต่อไปนี้:

### Binary Interface
- [ ] รับ 4 execution modes (single-cmd, REPL, pipe, run-file)
- [ ] Exit codes ตาม spec
- [ ] stdin/stdout/stderr discipline ถูก
- [ ] UTF-8 encoding

### Response Envelope
- [ ] ทุก response มี fields ครบ (`ok`, `command`, `data`, `artifacts`, `error`, `meta`)
- [ ] `meta` มี tool, schema_version, run_id, duration_ms, timestamp
- [ ] Error envelope มี `error.code` + `error.message`
- [ ] Single-line NDJSON output

### CLI Flags
- [ ] รองรับ `--config`, `--run-id`, `--log-file`, `--policy`, `--response-schema`, `--cmd`, `--run-file`
- [ ] รองรับ `--help`, `--version`, `--list-commands`, `--describe`, `--health`

### Configuration
- [ ] Config file = JSON (or YAML)
- [ ] Config resolution order ถูก
- [ ] Config schema validation
- [ ] Exit `4` on invalid config

### Logging
- [ ] NDJSON format เมื่อ `--log-file` ระบุ
- [ ] Required fields per log line ครบ
- [ ] Standard events ใช้ตามที่ spec

### Policy
- [ ] Verbs classified ใน `--describe`
- [ ] Tier enforcement ก่อน execute
- [ ] Exit `3` + envelope on policy violation

### Error Codes
- [ ] ใช้ standard codes ที่ตรงสถานการณ์
- [ ] Tool-specific codes มี prefix
- [ ] `error.recoverable` set ถูกต้อง

### Schema Versioning
- [ ] Schema version embedded in meta
- [ ] Backward compat รองรับ
- [ ] Deprecation warnings

### Documentation
- [ ] README.md
- [ ] docs/ARCHITECTURE.md
- [ ] docs/COMMAND_CONTRACT.md
- [ ] docs/AI_AGENT_GUIDE.md
- [ ] docs/USER_GUIDE.md
- [ ] schema/config.schema.json
- [ ] schema/response-v1.schema.json
- [ ] CHANGELOG.md

### Tests
- [ ] tests/harness.js — unit, no deps, < 5s
- [ ] tests/golden.js — integration, < 60s
- [ ] Schema validation tests

### Registry
- [ ] เพิ่มใน `.ai/tools.yaml`
- [ ] `trinity tool verify <name>` ผ่าน
- [ ] `trinity tool health <name>` ผ่าน

---

## 18. Examples

### 18.1 Minimal Compliant Tool Skeleton (Node.js)

```javascript
#!/usr/bin/env node
// memory-cli — minimal contract-compliant skeleton

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// ─── Constants ───
const TOOL_NAME = 'memory-cli';
const TOOL_VERSION = '0.1.0';
const SCHEMA_VERSION = '1';

// ─── Args parsing ───
const args = parseArgs(process.argv.slice(2));
const config = loadConfig(args.config);
const runId = args['run-id'] || generateRunId();
const policy = args.policy || 'normal';
const logFile = args['log-file'] ? fs.createWriteStream(args['log-file'], { flags: 'a' }) : null;

// ─── Discovery flags ───
if (args.help) { printHelp(); process.exit(0); }
if (args.version) { console.log(`${TOOL_NAME}@${TOOL_VERSION}`); process.exit(0); }
if (args['list-commands']) { send(listCommands()); process.exit(0); }
if (args.describe) { send(describeVerb(args.describe)); process.exit(0); }
if (args.health) { send(healthCheck()); process.exit(0); }

// ─── Execution mode dispatch ───
if (args.cmd) {
  executeOne(args.cmd).then(env => { send(env); process.exit(env.ok ? 0 : 1); });
} else if (args['run-file']) {
  executeBatch(args['run-file']);
} else {
  startRepl();
}

// ─── Core ───
async function executeOne(cmdLine) {
  const start = Date.now();
  log({ event: 'command_start', command: cmdLine });
  
  try {
    const { verb, args: verbArgs } = parseVerb(cmdLine);
    
    // Policy check
    const verbSpec = getVerbSpec(verb);
    if (!isPolicyAllowed(verbSpec.tier_required, policy)) {
      return errorEnvelope(verb, 'POLICY_VIOLATION', 
        `Verb '${verb}' requires tier=${verbSpec.tier_required}, current=${policy}`);
    }
    
    // Execute
    const data = await runVerb(verb, verbArgs);
    const env = successEnvelope(verb, data, Date.now() - start);
    log({ event: 'command_end', command: verb, duration_ms: env.meta.duration_ms, ok: true });
    return env;
  } catch (e) {
    const env = errorEnvelope(cmdLine, e.code || 'INTERNAL_ERROR', e.message);
    log({ event: 'command_end', command: cmdLine, ok: false, error: e.message });
    return env;
  }
}

function successEnvelope(command, data, duration_ms) {
  return {
    ok: true,
    command,
    data: data || {},
    artifacts: [],
    error: null,
    meta: {
      tool: `${TOOL_NAME}@${TOOL_VERSION}`,
      schema_version: SCHEMA_VERSION,
      run_id: runId,
      duration_ms,
      timestamp: new Date().toISOString()
    }
  };
}

function errorEnvelope(command, code, message, details = {}) {
  return {
    ok: false,
    command,
    data: null,
    artifacts: [],
    error: { code, message, details, recoverable: !['INVALID_CONFIG', 'POLICY_VIOLATION', 'INTERNAL_ERROR'].includes(code) },
    meta: {
      tool: `${TOOL_NAME}@${TOOL_VERSION}`,
      schema_version: SCHEMA_VERSION,
      run_id: runId,
      duration_ms: 0,
      timestamp: new Date().toISOString()
    }
  };
}

function send(envelope) {
  process.stdout.write(JSON.stringify(envelope) + '\n');
}

function log(entry) {
  if (!logFile) return;
  logFile.write(JSON.stringify({
    ts: new Date().toISOString(),
    level: 'INFO',
    tool: TOOL_NAME,
    run_id: runId,
    ...entry
  }) + '\n');
}

function generateRunId() {
  return `run_${new Date().toISOString().replace(/[:.]/g, '-')}_${Math.random().toString(36).slice(2, 8)}`;
}

// ... rest of implementation (parseArgs, loadConfig, parseVerb, getVerbSpec, runVerb, etc.)
```

### 18.2 Real Use Case — Trinity Loop Calling Tools

```python
# .ai/cli/commands/loop.py — kernel loop calls tools
import subprocess, json

def call_tool(tool_bin, command, run_id, policy='normal'):
    result = subprocess.run(
        [*tool_bin.split(), '--cmd', command, '--run-id', run_id, '--policy', policy,
         '--log-file', f'.ai/audit/tool-{tool_bin.split()[-1]}.ndjson'],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout.strip().split('\n')[-1])

# Trinity loop
def trinity_loop(goal, max_iter=10):
    run_id = f"run_{goal[:20]}_{int(time.time())}"
    
    for i in range(max_iter):
        # Step 1: get memory context
        ctx = call_tool('node memory-cli/index.js', f"search '{goal}'", run_id, 'safe')
        if not ctx['ok']: break
        
        # Step 2: verify evidence
        evidence = call_tool('python verify-cli', f"check '{goal}'", run_id, 'safe')
        
        # ... etc
```

---

## 19. Migration Path for browser-cli

browser-cli ปัจจุบันใกล้ contract นี้แล้ว — ส่วนที่ต้องปรับ:

| Item | Current | Target | Effort |
|------|---------|--------|--------|
| Response envelope v1 | partial | full | 🟡 Med |
| `--list-commands` | ❌ | ✅ | 🟢 Low |
| `--describe <verb>` | ❌ | ✅ | 🟢 Low |
| `--health` | ❌ | ✅ | 🟢 Low |
| `error.recoverable` | partial | full | 🟢 Low |
| `meta.timestamp` | ⚠️ in v2 | required | 🟢 Low |
| Helpers YAML | ✅ | ✅ | - |
| Policy tiers | ✅ | ✅ | - |
| NDJSON log | ✅ | ✅ | - |

> browser-cli should hit **v2.1** to be fully contract-compliant — small additions, no breaking

---

## 20. Open Questions

1. **JSON vs YAML config** — บังคับ JSON หรือเปิดเลือก?
2. **Schema location** — ภายใน tool repo หรือ shared schema repo?
3. **Run ID format** — UUID v4 หรือ timestamp-based?
4. **Helper recursion** — helper เรียก helper อื่นได้ไหม?
5. **Streaming responses** — สำหรับ long-running commands ทำยังไง?
6. **Multi-language tools** — Python tool รองรับครบเหมือน Node ไหม?
7. **Tool versioning vs schema versioning** — ผูกกัน หรือแยก?
8. **Error code namespace** — globally unique หรือ tool-scoped?
9. **Capability taxonomy** — มี registry กลางไหม?
10. **MCP bridge mapping** — verb → MCP tool ทำอัตโนมัติ?

---

## Appendix A: browser-cli as Reference

`browser-cli` เป็น reference implementation:
- ✅ stdin/stdout JSON
- ✅ Schema-locked (v1/v2)
- ✅ NDJSON log
- ✅ Policy tiers (safe/normal/aggressive)
- ✅ Run ID
- ✅ JSON config + helpers YAML
- ✅ REPL + pipe + run-file modes
- ✅ Documentation suite (docs/)

ทุก tool ใหม่ — ดู browser-cli แล้ว clone pattern

## Appendix B: JSON Schemas (preview)

### B.1 Response Envelope v1
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["ok", "command", "data", "artifacts", "error", "meta"],
  "properties": {
    "ok": { "type": "boolean" },
    "command": { "type": "string" },
    "data": { "type": ["object", "null"] },
    "artifacts": { "type": "array", "items": { "$ref": "#/definitions/artifact" } },
    "error": { "oneOf": [{ "type": "null" }, { "$ref": "#/definitions/error" }] },
    "meta": { "$ref": "#/definitions/meta" }
  },
  "definitions": {
    "artifact": {
      "type": "object",
      "required": ["type", "path"],
      "properties": {
        "type": { "enum": ["file", "url", "ref"] },
        "path": { "type": "string" },
        "sha256": { "type": "string" },
        "size_bytes": { "type": "integer" },
        "mime": { "type": "string" }
      }
    },
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": { "type": "string", "pattern": "^[A-Z][A-Z0-9_]*$" },
        "message": { "type": "string" },
        "details": { "type": "object" },
        "recoverable": { "type": "boolean" }
      }
    },
    "meta": {
      "type": "object",
      "required": ["tool", "schema_version", "run_id", "duration_ms", "timestamp"],
      "properties": {
        "tool": { "type": "string" },
        "schema_version": { "type": "string" },
        "run_id": { "type": "string" },
        "duration_ms": { "type": "number", "minimum": 0 },
        "timestamp": { "type": "string", "format": "date-time" }
      }
    }
  }
}
```

### B.2 Tool Registry Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "tools"],
  "properties": {
    "version": { "const": 1 },
    "tools": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "bin", "schema_version", "capabilities", "contract_version"],
        "properties": {
          "name": { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
          "path": { "type": "string" },
          "bin": { "type": "string" },
          "schema_version": { "type": "string" },
          "capabilities": { "type": "array", "items": { "type": "string" } },
          "policy_default": { "enum": ["safe", "normal", "aggressive"] },
          "health_check": { "type": "string" },
          "contract_version": { "type": "string" }
        }
      }
    }
  }
}
```

---

## Changelog

- **v1.0.0-draft (2026-04-28)** — Initial draft based on browser-cli reference + blueprint synthesis

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Trinity Big Evolution Blueprint
- `browser-cli/docs/COMMAND_CONTRACT.md` — Reference implementation contract
- `browser-cli/docs/RESPONSE_SCHEMA.md` — Reference v1/v2 schemas
- `browser-cli/docs/POLICY_TIERS.md` — Reference tier mapping
