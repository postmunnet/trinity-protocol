---
title: "Trinity Tool Contract v1.1 (English)"
subtitle: "Universal CLI tool contract — POSIX of Trinity"
language: English
version: 1.1.0
last-updated: 2026-04-28
note: "Translation of ../01_TOOL_CONTRACT.md (essential parts)"
---

# Trinity Tool Contract v1.1 (English)

> **Universal contract for CLI tools in Trinity OS ecosystem**
>
> Tool not following this → Trinity kernel won't orchestrate.
> Tool following this fully → plug-and-play with Trinity.

---

## Public Freeze Status

Public ecosystem messaging should treat the Tool Contract as:

```text
Tool Contract v1.0 = freeze candidate
Current working spec = v1.1.0-draft
```

Before declaring a stable external tool interface, Trinity must freeze at
least these 10 surfaces:

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

Until that checklist is complete, public docs should say **v1.0 freeze
candidate** or **v1.1 draft working spec**, not stable interface.

---

## 0. Compliance Levels

| Level | Description |
|-------|-------------|
| **MUST** | Required — kernel rejects tool if missing |
| **SHOULD** | Recommended — works but not best practice |
| **MAY** | Optional |

---

## 1. Scope

### In Scope
- Binary entry point conventions
- Stdin/stdout JSON protocol
- Response envelope schema
- Universal CLI flags
- Logging format (NDJSON)
- Policy tiers (safe/normal/aggressive)
- Error codes
- Schema versioning
- Discovery (`--list-commands`, `--describe`, `--health`)
- Helpers (YAML composition)
- Documentation requirements
- Test harness pattern
- Tool registry format

### Out of Scope
- ❌ Tool internal architecture
- ❌ Programming language (any works)
- ❌ External libraries
- ❌ Database choice
- ❌ **MCP protocol as default core path** — Trinity is CLI-first by default.
  MCP-only capabilities may be wrapped by an adapter, but they must enter
  Trinity through the Tool Contract envelope before they reach the audit chain.

---

## 2. Terminology

| Term | Definition |
|------|-----------|
| **Tool** | CLI binary implementing this contract |
| **Verb / Command** | Action a tool exposes (e.g., `search`, `goto`) |
| **Run** | One invocation of a tool |
| **Run ID** | Unique identifier for a run |
| **Envelope** | Response JSON wrapper |
| **Artifact** | File/data created — kept as truth |
| **Policy** | Tier limiting which verbs allowed |
| **Schema version** | Version of response format |
| **Helper** | YAML composition of commands |

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
```

### 3.2 Execution Modes (MUST support all 4)

#### Mode A: Single Command
```bash
memory-cli --cmd "search 'auth bug'"
```

#### Mode B: REPL (interactive)
```bash
memory-cli
> search auth
> get r123
> exit
```

#### Mode C: Pipe (stdin)
```bash
echo "search auth
get r123
exit" | memory-cli
```

#### Mode D: Run File
```bash
memory-cli --run-file batch.txt
```

### 3.3 Exit Codes (MUST)

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Generic error |
| `2` | Invalid usage |
| `3` | Policy violation |
| `4` | Configuration error |
| `5` | Permission denied |
| `10` | Timeout |
| `100+` | Tool-specific |

### 3.4 Stream Discipline (MUST)

| Stream | Purpose | Format |
|--------|---------|--------|
| **stdin** | Commands input | Plain text (1 command per line) |
| **stdout** | Responses | JSON (NDJSON) |
| **stderr** | Diagnostics | Free-form |

> **CRITICAL:** stdout must be **machine-parseable JSON only** — no banners, no debug

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
    "tool": "memory-cli@0.1.0",
    "schema_version": "1",
    "run_id": "run_2026-04-28_xyz",
    "duration_ms": 42,
    "timestamp": "2026-04-28T12:34:56Z"
  }
}
```

### 4.2 Error Envelope (MUST)

```json
{
  "ok": false,
  "command": "search",
  "action": "memory.search",
  "data": null,
  "artifacts": [],
  "error": {
    "code": "INDEX_NOT_FOUND",
    "message": "Memory index not initialized",
    "details": { "expected_path": "./.memory/index.db" },
    "recoverable": true
  },
  "meta": { "...": "..." }
}
```

### 4.3 Field Reference

| Field | Required | Type |
|-------|----------|------|
| `ok` | MUST | boolean |
| `command` | MUST | string (local verb) |
| `action` | MUST (v1.1+) | string (canonical `tool.verb`) |
| `data` | MUST | object\|null |
| `artifacts` | MUST | array |
| `error` | MUST | object\|null |
| `meta` | MUST | object |
| `meta.tool` | MUST | string |
| `meta.schema_version` | MUST | string |
| `meta.run_id` | MUST | string |
| `meta.duration_ms` | MUST | number |
| `meta.timestamp` | MUST | ISO 8601 |

---

## 4a. Action Namespace (v1.1+)

### Why
- `screenshot` exists in browser-cli AND wordpress-cli — conflict
- `search` exists in memory-cli AND grep-cli — conflict
- Audit needs canonical name

### Format (MUST)

```
<tool-namespace>.<verb>
```

### Reserved Namespaces

| Namespace | Tool |
|-----------|------|
| `browser` | browser-cli |
| `memory` | memory-cli |
| `retro` | retro-cli |
| `verify` | verify-cli |
| `wordpress` | wordpress-cli |
| `ftp` | ftp-cli |
| `seo` | seo-cli |
| `code` | grep-cli |
| `deploy` | deploy-cli |
| `god` | god-team-cli |

### Examples

| Local verb | Action namespace |
|-----------|------------------|
| `goto` (browser-cli) | `browser.goto` |
| `screenshot` (browser-cli) | `browser.screenshot` |
| `search` (memory-cli) | `memory.search` |
| `validate` (retro-cli) | `retro.validate` |
| `put` (ftp-cli) | `ftp.put` |

---

## 5. Stdin/Stdout Protocol

- Each input command = 1 line, terminated by `\n`
- Each output envelope = 1 line, terminated by `\n` (NDJSON)
- No multi-line JSON — single-line only
- UTF-8 encoding
- stdout: line-buffered (flush after each envelope)
- stderr: unbuffered

---

## 6. Universal CLI Flags

### Required (MUST support)

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--config <path>` | path | `./<tool>.config.json` | Config file |
| `--run-id <string>` | string | auto | Run correlation |
| `--log-file <path>` | path | none | NDJSON log output |
| `--policy <tier>` | enum | `normal` | safe/normal/aggressive |
| `--response-schema <ver>` | string | `1` | Schema version |
| `--cmd "<command>"` | string | none | Single command mode |
| `--run-file <path>` | path | none | Batch from file |

### Standard (SHOULD support)

| Flag | Description |
|------|-------------|
| `--help, -h` | Print help |
| `--version, -v` | Print version |
| `--list-commands` | List verbs (JSON) |
| `--describe <cmd>` | Verb spec (JSON) |
| `--health` | Health check (JSON) |
| `--quiet, -q` | Suppress stderr |
| `--verbose` | Extra diagnostics |
| `--dry-run` | Validate without effects |

---

## 7. Configuration

### 7.1 Format (MUST)
- JSON (preferred)
- YAML (acceptable)

### 7.2 Standard Fields

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
  "tool_specific": { "...": "tool-defined" }
}
```

### 7.3 Resolution Order (MUST)

1. `--config` flag
2. ENV `<TOOL>_CONFIG`
3. CWD `./<tool>.config.json`
4. CWD `./configs/<tool>.json`
5. Built-in default

---

## 8. Logging (NDJSON)

### Format (MUST when `--log-file`)

```json
{"ts":"2026-04-28T12:34:56Z","level":"INFO","tool":"memory-cli","run_id":"run_xyz","event":"command_start","command":"search","args":["auth bug"]}
{"ts":"2026-04-28T12:34:56Z","level":"DEBUG","tool":"memory-cli","run_id":"run_xyz","event":"db_query","sql":"SELECT ..."}
{"ts":"2026-04-28T12:34:56Z","level":"INFO","tool":"memory-cli","run_id":"run_xyz","event":"command_end","duration_ms":42,"ok":true}
```

### Required Fields

| Field | Type |
|-------|------|
| `ts` | ISO 8601 UTC |
| `level` | DEBUG/INFO/WARN/ERROR |
| `tool` | tool name |
| `run_id` | correlation |
| `event` | snake_case event |

### Standard Events

`run_start`, `run_end`, `command_start`, `command_end`, `policy_violation`, `artifact_created`, `external_call`, `error_caught`

### Append-only (MUST)

Log file is append-only. Rotation = new file (don't rewrite).

---

## 9. Policy Tiers

### Tiers (MUST honor)

| Tier | Allows |
|------|--------|
| **safe** | Read-only verbs |
| **normal** | + Write verbs |
| **aggressive** | + Destructive verbs |

### Verb Classification (MUST in `--describe`)

```json
{
  "verb": "delete",
  "tier_required": "aggressive",
  "destructive": true,
  "writes": true
}
```

### Enforcement (MUST)

Block with exit code `3` + error envelope:

```json
{
  "ok": false,
  "error": {
    "code": "POLICY_VIOLATION",
    "message": "Verb 'delete' requires tier=aggressive, current=normal"
  }
}
```

---

## 10. Standard Error Codes

| Code | Meaning | Recoverable |
|------|---------|-------------|
| `INVALID_ARGS` | Bad arguments | true |
| `INVALID_CONFIG` | Config malformed | false |
| `MISSING_DEPENDENCY` | External tool missing | false |
| `POLICY_VIOLATION` | Tier insufficient | false |
| `PERMISSION_DENIED` | FS/network forbidden | false |
| `RESOURCE_NOT_FOUND` | File/record missing | true |
| `RESOURCE_LOCKED` | Lock unavailable | true |
| `RESOURCE_EXHAUSTED` | Disk/memory/quota | true |
| `EXTERNAL_FAILURE` | DB/HTTP/exec failed | true |
| `TIMEOUT` | Operation too long | true |
| `SCHEMA_MISMATCH` | Schema version wrong | false |
| `INTERNAL_ERROR` | Tool bug | false |

Tool-specific: prefix with tool name (`MEMORY_INDEX_CORRUPT`)

---

## 11. Schema Versioning

### Rules (MUST)

- Schema version = string (`"1"`, `"2"`)
- Backward compat: v2 tool MUST support `--response-schema=v1`
- Embed `schema_version` in `meta`

### Breaking Changes (bump major)
- Remove field
- Change type
- Change semantic
- Add required field

### Non-breaking (bump minor)
- Add optional field
- Add enum value (clients ignore unknown)

---

## 12. Discovery

### `--list-commands` (MUST)

```json
{
  "ok": true,
  "command": "list-commands",
  "data": {
    "tool": "memory-cli@0.1.0",
    "commands": [
      { "verb": "search", "tier": "safe", "description": "Hybrid search" },
      { "verb": "learn", "tier": "normal", "description": "Add document" }
    ]
  }
}
```

### `--describe <verb>` (MUST)

```json
{
  "ok": true,
  "data": {
    "verb": "search",
    "tier_required": "safe",
    "destructive": false,
    "writes": false,
    "args": [
      { "name": "query", "type": "string", "required": true }
    ],
    "options": [
      { "name": "--limit", "type": "int", "default": 10 }
    ]
  }
}
```

### `--health` (SHOULD)

```json
{
  "ok": true,
  "data": {
    "tool": "memory-cli@0.1.0",
    "status": "ready",
    "checks": [
      { "name": "config_loaded", "ok": true },
      { "name": "db_connection", "ok": true }
    ]
  }
}
```

---

## 13. Helpers (YAML)

### File Format (SHOULD)

```yaml
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

### Invocation

```bash
memory-cli --cmd "helper fresh-search 'auth bug'"
```

---

## 14. Documentation Requirements

### Required Files (MUST)

```
<tool-name>/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── COMMAND_CONTRACT.md
│   ├── CONFIG_SCHEMA.md
│   ├── AI_AGENT_GUIDE.md
│   ├── USER_GUIDE.md
│   ├── POLICY_TIERS.md
│   └── TROUBLESHOOTING.md
├── schema/
│   ├── config.schema.json
│   └── response-v<N>.schema.json
├── tests/
│   ├── harness.js (unit, no deps)
│   └── golden.js (integration)
├── package.json (or pyproject.toml)
└── CHANGELOG.md
```

---

## 15. Test Harness Pattern

### Unit (MUST)

`tests/harness.js`:
- No external dependencies
- Run < 5 seconds
- Exit 0 on full pass

### Golden (MUST)

`tests/golden.js`:
- Integration test against real deps
- Run < 60 seconds
- Idempotent

---

## 16. Tool Registry

### Format

`.ai/tools.yaml`:

```yaml
version: 1
tools:
  - name: browser-cli
    path: /<home>/<user>/Downloads/yai_project/browser-cli
    bin: node /<home>/<user>/Downloads/yai_project/browser-cli/index.js
    schema_version: "2"
    capabilities: [browser, dom, screenshot]
    policy_default: normal
    health_check: --health
    contract_version: "1.1"
```

---

## 16a. Contract Compliance Test

### `trinity-contract-test <tool>`

Validates compliance:
- Binary interface (4 modes, exit codes, stdio)
- Universal flags
- Discovery (help/version/list/describe/health)
- Response envelope schema
- Logging (NDJSON format)
- Policy enforcement
- Schema versioning
- Action namespace (v1.1+)

### Compliance Levels

| Level | Definition |
|-------|------------|
| **Bronze** | Binary + envelope tests pass |
| **Silver** | + Discovery + logging |
| **Gold** | + Policy + schema + namespace |
| **Platinum** | + Golden integration tests |

Trinity kernel rejects below Bronze in production registry.

---

## 17. Compliance Checklist

Before registering a tool:

### Binary Interface
- [ ] 4 execution modes
- [ ] Exit codes per spec
- [ ] stdio discipline correct
- [ ] UTF-8 encoding

### Response Envelope
- [ ] All required fields
- [ ] `meta` complete (tool, schema_version, run_id, duration_ms, timestamp)
- [ ] `error.code` + `error.message` on errors
- [ ] Single-line NDJSON

### CLI Flags
- [ ] Universal flags (`--config`, `--run-id`, `--log-file`, `--policy`, `--response-schema`)
- [ ] Standard flags (`--help`, `--version`, `--list-commands`, `--describe`, `--health`)

### Configuration
- [ ] JSON or YAML config
- [ ] Resolution order correct
- [ ] Schema validation
- [ ] Exit `4` on invalid

### Logging
- [ ] NDJSON format with `--log-file`
- [ ] Required fields per line
- [ ] Standard events used

### Policy
- [ ] Verbs classified
- [ ] Tier enforcement before execute
- [ ] Exit `3` on violation

### Documentation
- [ ] README.md
- [ ] docs/ARCHITECTURE.md
- [ ] docs/COMMAND_CONTRACT.md
- [ ] docs/AI_AGENT_GUIDE.md
- [ ] schema/config.schema.json
- [ ] schema/response-v1.schema.json

### Tests
- [ ] tests/harness.js < 5s
- [ ] tests/golden.js < 60s
- [ ] Schema validation tests

### Registry
- [ ] Added to `.ai/tools.yaml`
- [ ] `trinity-contract-test <tool>` passes
- [ ] `trinity tool health <tool>` passes

---

## 18. Minimal Skeleton (Node.js)

```javascript
#!/usr/bin/env node
const fs = require('fs');
const readline = require('readline');

const TOOL_NAME = 'memory-cli';
const TOOL_VERSION = '0.1.0';
const SCHEMA_VERSION = '1';

const args = parseArgs(process.argv.slice(2));
const config = loadConfig(args.config);
const runId = args['run-id'] || generateRunId();
const policy = args.policy || 'normal';
const logFile = args['log-file'] ? fs.createWriteStream(args['log-file'], { flags: 'a' }) : null;

if (args.help) { printHelp(); process.exit(0); }
if (args.version) { console.log(`${TOOL_NAME}@${TOOL_VERSION}`); process.exit(0); }
if (args['list-commands']) { send(listCommands()); process.exit(0); }
if (args.describe) { send(describeVerb(args.describe)); process.exit(0); }
if (args.health) { send(healthCheck()); process.exit(0); }

if (args.cmd) {
  executeOne(args.cmd).then(env => { send(env); process.exit(env.ok ? 0 : 1); });
} else if (args['run-file']) {
  executeBatch(args['run-file']);
} else {
  startRepl();
}

async function executeOne(cmdLine) {
  const start = Date.now();
  log({ event: 'command_start', command: cmdLine });
  
  try {
    const { verb, args: verbArgs } = parseVerb(cmdLine);
    const verbSpec = getVerbSpec(verb);
    
    if (!isPolicyAllowed(verbSpec.tier_required, policy)) {
      return errorEnvelope(verb, 'POLICY_VIOLATION', 
        `Verb '${verb}' requires tier=${verbSpec.tier_required}, current=${policy}`);
    }
    
    const data = await runVerb(verb, verbArgs);
    const env = successEnvelope(verb, data, Date.now() - start);
    log({ event: 'command_end', command: verb, duration_ms: env.meta.duration_ms, ok: true });
    return env;
  } catch (e) {
    log({ event: 'command_end', command: cmdLine, ok: false, error: e.message });
    return errorEnvelope(cmdLine, e.code || 'INTERNAL_ERROR', e.message);
  }
}

function successEnvelope(command, data, duration_ms) {
  return {
    ok: true, command, action: `memory.${command}`,
    data: data || {}, artifacts: [], error: null,
    meta: {
      tool: `${TOOL_NAME}@${TOOL_VERSION}`,
      schema_version: SCHEMA_VERSION,
      run_id: runId, duration_ms,
      timestamp: new Date().toISOString()
    }
  };
}

function errorEnvelope(command, code, message, details = {}) {
  return {
    ok: false, command, action: `memory.${command}`,
    data: null, artifacts: [],
    error: { code, message, details, 
             recoverable: !['INVALID_CONFIG', 'POLICY_VIOLATION', 'INTERNAL_ERROR'].includes(code) },
    meta: { /* same as success */ }
  };
}

function send(envelope) {
  process.stdout.write(JSON.stringify(envelope) + '\n');
}

function log(entry) {
  if (!logFile) return;
  logFile.write(JSON.stringify({
    ts: new Date().toISOString(), level: 'INFO',
    tool: TOOL_NAME, run_id: runId, ...entry
  }) + '\n');
}
```

---

## 19. Migration Path: browser-cli to v1.1

| Item | Current | Target | Effort |
|------|---------|--------|--------|
| Response envelope v1 | partial | full | Med |
| `--list-commands` | ❌ | ✅ | Low |
| `--describe <verb>` | ❌ | ✅ | Low |
| `--health` | ❌ | ✅ | Low |
| `error.recoverable` | partial | full | Low |
| `meta.timestamp` | ⚠️ in v2 | required | Low |
| Action namespace `browser.*` | ❌ | ✅ | Low |

→ browser-cli should hit v2.1 to be fully contract-compliant

---

## 20. Open Questions

1. JSON vs YAML config — enforce JSON?
2. Run ID format — UUID v4 or timestamp-based?
3. Helper recursion — allow helper calling helper?
4. Streaming responses for long-running commands?
5. Multi-language tools — Python tool support same as Node?
6. Tool versioning vs schema versioning — link or separate?
7. Error code namespace — global unique or tool-scoped?
8. Capability taxonomy — central registry?
9. MCP bridge mapping — auto verb → MCP tool?

---

## See also

- [`README.md`](README.md)
- [`INDEX.md`](INDEX.md)
- [`00_BLUEPRINT.md`](00_BLUEPRINT.md)
- [`12_GLOSSARY.md`](12_GLOSSARY.md)
- [`../01_TOOL_CONTRACT.md`](../01_TOOL_CONTRACT.md) — Thai version (full detail)

---

## Changelog

- **v1.1.0 (2026-04-28)** — English translation, includes Action Namespace + Compliance Test
