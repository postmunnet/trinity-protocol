# Command Contract

**Version**: v0.1 | **Status**: Binding | **Last Updated**: 2026-04-24
**Parent**: [`ARCHITECTURE.md`](ARCHITECTURE.md)

Binding contract for all browser-cli commands — input grammar, output schema, tiers, error codes.

---

## 1. Purpose

สัญญาของ command surface:
- Complete inventory of supported verbs
- Input grammar (parsing rules)
- Output schema (v1/v2)
- Tier classification (safe/medium/high)
- Error codes

Any command not in this contract = not supported.

---

## 2. Input Grammar

### 2.1 Basic verb form
```
<verb> [arg1] [arg2] ... [--option1=value1] [--option2]
```

### 2.2 Chain (sequential execution)
```
<verb1> [args1] ; <verb2> [args2] ; <verb3> [args3]
```
- Separator: ` ; ` (semicolon with surrounding spaces)
- Execution: strictly sequential, stop on first error (default)

### 2.3 Comments
```
# this is a comment
   # also works with leading space
```
- Lines starting with `#` (after trim) → skipped

### 2.4 Options
```
<verb> [args] --timeout_ms=5000 --retry=3
```
- Parsed as `options.timeout_ms = 5000`, `options.retry = 3`
- Underscores preserved in option names

### 2.5 Quoted args
```
fill #name "John Doe"
eval 'document.title'
```
- Double quotes: preserves spaces
- Single quotes: same
- Escapes: `\"` inside double, `\'` inside single

---

## 3. Response Schema

### 3.1 v1 (flat, backward-compatible)
```json
{
  "ok": true,
  "verb": "goto",
  "url": "https://example.com/x",
  "duration_ms": 150
}
```
Or error:
```json
{
  "ok": false,
  "verb": "click",
  "error": "Element not found: .missing",
  "error_code": "ELEMENT_NOT_FOUND"
}
```

### 3.2 v2 (structured envelope)
```json
{
  "ok": true,
  "verb": "goto",
  "args": ["/x"],
  "options": {},
  "data": {
    "url": "https://example.com/x",
    "title": "X Page"
  },
  "meta": {
    "session": {"profile": "backend", "user": "admin"},
    "policy_tier": "safe",
    "policy_mode": "normal",
    "duration_ms": 150,
    "attempt": 0,
    "run_id": "abc123",
    "artifacts": []
  }
}
```

See: [`RESPONSE_SCHEMA.md`](RESPONSE_SCHEMA.md)

---

## 4. Command Inventory (categorized)

### 4.1 Navigate
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `goto <url>` | url (relative or absolute) | safe | Navigate |
| `back` | — | safe | History back |
| `forward` | — | safe | History forward |
| `reload` | — | safe | Refresh page |

### 4.2 Read (no mutation)
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `text <sel>` | CSS selector | safe | `textContent` |
| `html <sel>` | CSS selector | safe | `innerHTML` |
| `attrs <sel>` | CSS selector | safe | All attributes |
| `exists <sel>` | CSS selector | safe | `{exists, count}` |
| `value <sel>` | CSS selector | safe | Input value |
| `eval <js>` | JavaScript expr | **high** | Run arbitrary JS |
| `outline` | — | safe | Page summary |
| `buttons` | — | safe | All buttons + state |
| `forms` | — | safe | Form fields |
| `table <sel>` | CSS selector | safe | Table as 2D array |
| `snapshot` | — | safe | Full page dump |
| `cookies` | — | safe | List cookies |

### 4.3 Action (mutation, reversible)
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `click <sel>` | CSS selector | medium | Click element |
| `dblclick <sel>` | CSS selector | medium | Double-click |
| `fill <sel> <val>` | sel + value | medium | Type in input |
| `type <sel> <text>` | sel + text | medium | Simulate keystrokes |
| `press <key>` | key name | medium | Keyboard press |
| `select <sel> <val>` | sel + option | medium | Select dropdown |
| `check <sel>` | CSS selector | medium | Check checkbox |
| `uncheck <sel>` | CSS selector | medium | Uncheck checkbox |
| `upload <sel> <file>` | sel + path | medium | File input |
| `hover <sel>` | CSS selector | safe | Hover |
| `focus <sel>` | CSS selector | safe | Focus element |
| `blur <sel>` | CSS selector | safe | Blur element |
| `screenshot [name]` | optional name | safe | Take screenshot |

### 4.4 Force (dangerous — tier high)
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `force-click <sel>` | sel | **high** | Click even if disabled |
| `force-fill <sel> <val>` | sel + val | **high** | Fill readonly |
| `force-submit <sel>` | form sel | **high** | Submit form directly |
| `force-enable <sel>` | sel | **high** | Remove `disabled` attr |
| `force-show <sel>` | sel | **high** | Remove `display:none` |

### 4.5 Download
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `download-click <sel>` | sel | medium | Click + await download |
| `downloads` | — | safe | List downloaded files |

### 4.6 Monitor
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `monitor-ajax` | — | safe | Start AJAX logging |
| `ajax-log` | — | safe | Show AJAX log |
| `monitor-console` | — | safe | Start console logging |
| `console-log` | — | safe | Show console log |
| `wait-ajax` | — | safe | Wait network idle |
| `wait <ms>` | integer | safe | Fixed wait |
| `wait-selector <sel>` | sel | safe | Wait for element |

### 4.7 Assert
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `assert-text <sel> <exp>` | sel + expected | safe | Text contains |
| `assert-exists <sel>` | sel | safe | Element exists |
| `assert-visible <sel>` | sel | safe | Element visible |
| `assert-enabled <sel>` | sel | safe | Not disabled |
| `assert-value <sel> <exp>` | sel + value | safe | Input value match |

### 4.8 Session
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `login [profile]` | optional profile name | medium | Auto-login |
| `logout` | — | medium | Clear session |
| `exit` / `quit` | — | — | Close CLI (Chrome stays in CDP mode) |

### 4.9 Tab Management (NEW in v0.1)
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `tabs` | — | safe | List all tabs `[{index, title, url}, ...]` |
| `switch-tab <N>` | integer | safe | Make tab N active |
| `new-tab [url]` | optional url | medium | Open new tab |
| `close-tab [N]` | optional int | medium | Close tab N (default: current) |

### 4.10 Recorder Control (NEW in v0.1)
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `start-recording` | — | safe | Enable user action recording |
| `stop-recording` | — | safe | Disable recorder |
| `recording-status` | — | safe | Show recording state + log path |
| `tail-actions [N]` | optional N | safe | Show last N actions (default 20) |

### 4.11 Chain & Helpers
| Verb | Args | Tier | Description |
|:---|:---|:---:|:---|
| `cmd1 ; cmd2` | inline chain | (derived) | Multi-step |
| `run-file <path>` | file path | (derived) | Run commands from file |
| `helper <name> [args]` | helper name + args | (derived from steps) | Custom macro |

---

## 5. Input/Output Per Command (detailed spec)

### Example: `click`
**Input**:
```
click <css-selector> [--timeout_ms=N] [--force]
```

**Output (v2 success)**:
```json
{
  "ok": true,
  "verb": "click",
  "args": ["button.btn-primary"],
  "options": {},
  "data": {
    "clicked": true,
    "selector": "button.btn-primary"
  },
  "meta": {
    "duration_ms": 45,
    "policy_tier": "medium",
    ...
  }
}
```

**Errors**:
- `ELEMENT_NOT_FOUND` — selector matches 0
- `ELEMENT_DISABLED` — element is disabled (use `force-click`)
- `ELEMENT_NOT_VISIBLE` — hidden
- `TIMEOUT` — wait exceeded

### Example: `goto`
**Input**:
```
goto <url> [--waitUntil=domcontentloaded|load|networkidle] [--timeout_ms=N]
```

**Output**:
```json
{
  "ok": true,
  "verb": "goto",
  "args": ["/backend/order/123"],
  "data": {
    "url": "https://example.com/backend/order/123",
    "status": 200,
    "title": "Order #123"
  },
  "meta": {...}
}
```

### Example: `eval` (tier=high)
**Input**:
```
eval <js-expression>
```

**Output**:
```json
{
  "ok": true,
  "verb": "eval",
  "args": ["document.title"],
  "data": {
    "result": "Order #123",
    "type": "string"
  },
  "meta": {"policy_tier": "high", ...}
}
```

Policy check: rejected in `safe` mode.

---

## 6. Error Codes

### Standard codes
| Code | Meaning |
|:---|:---|
| `PARSE_ERROR` | Cannot parse input |
| `UNKNOWN_COMMAND` | Verb not in contract |
| `POLICY_DENIED` | Tier exceeds mode limit |
| `ELEMENT_NOT_FOUND` | CSS selector matches 0 |
| `ELEMENT_DISABLED` | Element has disabled attr |
| `ELEMENT_NOT_VISIBLE` | Display:none or hidden |
| `TIMEOUT` | Operation exceeded timeout |
| `NAVIGATION_FAILED` | Page load error |
| `AUTH_FAILED` | Login flow failed |
| `HELPER_NOT_FOUND` | Helper name not in config |
| `FILE_NOT_FOUND` | Upload/download file missing |
| `JS_EXCEPTION` | `eval` threw exception |
| `CDP_CONNECT_REFUSED` | CDP connection failed |
| `CDP_DISCONNECTED` | Lost CDP connection |
| `CDP_URL_INVALID` | Malformed CDP URL |
| `CDP_HOST_REJECTED` | Non-localhost CDP URL |

---

## 7. Tier Classification Rules

### Determining tier
1. **Explicit** in command spec (see §4 tables)
2. **Derived** for helpers:
   - Max of all nested command tiers
   - Helper cannot upgrade its own tier

### Policy modes
| Mode | Allows |
|:---:|:---|
| `safe` | tier=safe only |
| `normal` (default) | tier=safe OR medium |
| `aggressive` | all tiers including high |

### Override
- Policy never overridable at runtime (must be CLI flag / config)
- See: [`POLICY_TIERS.md`](POLICY_TIERS.md)

---

## 8. Validator Rules (YAML)

```yaml
command_validator:
  contract_version: "0.1"

  grammar:
    verb_required: true
    verb_pattern: "^[a-z][a-z0-9-]*$"
    chain_separator: " ; "
    option_prefix: "--"
    comment_prefix: "#"

  response:
    schema_v1_required_fields: ["ok", "verb"]
    schema_v2_required_fields: ["ok", "verb", "args", "options", "meta"]
    schema_v2_meta_fields: ["duration_ms", "policy_tier", "session"]

  tier_enforcement:
    modes: [safe, normal, aggressive]
    tier_hierarchy: [safe, medium, high]
    safe_mode_allows: [safe]
    normal_mode_allows: [safe, medium]
    aggressive_mode_allows: [safe, medium, high]

  anti_patterns:
    - id: unknown_verb
      severity: BLOCK
      message: "Verb must be in contract §4 inventory"

    - id: missing_required_args
      severity: BLOCK
      message: "Required args missing (see command spec)"

    - id: tier_escalation_in_helper
      severity: BLOCK
      message: "Helper cannot downgrade tier of nested commands"

    - id: non_json_response
      severity: BLOCK
      message: "Response must be valid JSON (one per line on stdout)"

    - id: missing_error_code_on_failure
      severity: WARN
      message: "Errors should include error_code from known list"
```

---

## 9. Anti-Patterns (BLOCK/WARN)

| Anti-pattern | Severity | Why |
|:---|:---:|:---|
| Unknown verb in chain | 🔴 BLOCK | Can't dispatch |
| Missing required args | 🔴 BLOCK | Command underspecified |
| Tier escalation via helper | 🔴 BLOCK | Bypass policy |
| Non-JSON on stdout | 🔴 BLOCK | Breaks AI agent parsing |
| Missing error_code on error | 🟡 WARN | Agents can't classify |
| `eval` with policy=safe | 🔴 BLOCK | Arbitrary JS = high tier |
| Chain with `exit` in middle | 🟡 WARN | Subsequent commands ignored |

---

## 10. Command Addition Process

To add a new verb:
1. Add row to §4 inventory (verb, args, tier, description)
2. Document I/O schema in §5
3. Add error codes if new ones needed (§6)
4. Update validator if grammar changes (§8)
5. Add tests
6. Bump `contract_version` in validator

---

## 11. Backwards Compatibility

### v1 → v2 response migration
- v1 callers receive flat response
- v2 callers get structured envelope
- No breaking changes to v1 within v0.1

### Deprecations
- `--response-schema=v1` supported through v0.x
- May be removed in v1.0

---

## 12. Examples

### Chain
```
goto /order/123 ; buttons ; screenshot order-123
```
**Output**: Array of 3 results in one chain response.

### Helper (from YAML)
```yaml
helpers:
  check-order:
    args: [id]
    steps:
      - goto /backend/order/{id}
      - outline
      - exists .alert-danger
```

Invocation:
```
helper check-order 123
```

### With options
```
click button.btn-primary --timeout_ms=10000 --retry=2
```

---

## 13. References

- Parent: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Response format: [`RESPONSE_SCHEMA.md`](RESPONSE_SCHEMA.md)
- Policy tiers: [`POLICY_TIERS.md`](POLICY_TIERS.md)
- CDP mode: [`CDP_CONTRACT.md`](CDP_CONTRACT.md)
- Recorder: [`RECORDER_CONTRACT.md`](RECORDER_CONTRACT.md)

---

**Contract Established**: 2026-04-24
**Version**: v0.1
**Authority**: Design approval required for verb additions/removals or tier changes
