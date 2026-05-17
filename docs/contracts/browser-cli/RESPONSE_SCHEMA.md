# Response Schema

Browser CLI responses are line-delimited JSON on stdout (one response per line per command).

Two schemas coexist: `v1` (passthrough, legacy) and `v2` (locked contract). Select with `--response-schema=v1|v2`.

## v1 schema (default)

Per-command payload, no wrapping.

```json
{"ok": true, "url": "...", "title": "..."}
{"ok": true, "text": "..."}
{"ok": true, "exists": true, "count": 3}
{"ok": false, "error": "Not found: .x"}
```

Shape varies by command — consult `lib/commands/*.js` for exact fields.

## v2 schema (locked, validated)

Every response has this shape (validated by `schema/response-v2.schema.json`):

```json
{
  "ok": true,
  "command": {
    "verb": "goto",
    "args": ["/url"],
    "options": {"timeout_ms": 5000}
  },
  "input": "goto /url @timeout=5000",
  "data": { "url": "...", "title": "..." },
  "error": null,
  "error_code": null,
  "artifacts": [],
  "meta": {
    "ts": "2026-04-22T14:43:05.533Z",
    "schema": "v2",
    "profile": "backend",
    "session": {
      "authenticated": true,
      "profile": "backend",
      "user": "yai",
      "since": "2026-04-22T14:42:00.000Z"
    },
    "duration_ms": 314,
    "policy_tier": "safe",
    "run_id": null
  }
}
```

### Top-level fields

| Field | Type | Description |
|---|---|---|
| `ok` | boolean | Success flag |
| `command` | object | Canonical AST of the command that ran |
| `input` | string \| null | Original line/JSON before parsing |
| `data` | object \| array \| null | Command-specific payload (null on error) |
| `error` | string \| null | Human-readable error message |
| `error_code` | enum \| null | See `lib/errors.js` |
| `artifacts` | array | Persistent outputs (screenshots, downloads, logs) |
| `meta` | object | Runtime metadata |

### command

```json
{"verb": "goto", "args": ["/url"], "options": {"timeout_ms": 5000, "retry": 2}}
```

### artifacts

```json
[
  {"type": "screenshot", "path": "downloads/after.png"},
  {"type": "download", "path": "downloads/file.pdf", "size": 12345}
]
```

Allowed types: `screenshot`, `download`, `ajax-log`, `console-log`, `snapshot`.

### meta

| Field | Type | Description |
|---|---|---|
| `ts` | ISO 8601 string | Time the response was built |
| `schema` | `"v2"` | Constant |
| `profile` | string \| null | Active auth profile |
| `session` | object \| null | Session snapshot (authenticated, profile, user, since) |
| `duration_ms` | number | Handler + wrapper execution time |
| `policy_tier` | enum \| null | `safe`/`medium`/`high` |
| `run_id` | string \| null | Optional `--run-id` value |

## Error codes

See `lib/errors.js`:

```
UNKNOWN_COMMAND
PARSE_ERROR
ELEMENT_NOT_FOUND
TIMEOUT
NAVIGATION_FAILED
FILE_NOT_FOUND
AUTH_FAILED
POLICY_DENIED
HELPER_NOT_FOUND
CONFIG_INVALID
RUNTIME_ERROR
```

## Chain responses

```
goto /a ; buttons ; exists .x
```

Returns a single line:
```json
{"ok": true, "chain": [ <v2 response>, <v2 response>, <v2 response> ]}
```

Each inner element follows the v2 schema independently.

## Helper responses

```
my-helper arg1 arg2
```

Returns:
```json
{
  "ok": true,
  "command": {"verb": "my-helper", "args": ["arg1", "arg2"]},
  "data": {"helper": "my-helper", "results": [ <response>, ... ]},
  "meta": {"policy_tier": "<derived>", ...}
}
```

`meta.policy_tier` is the max tier of the expanded steps.

## Validation

```bash
node -e "
  const schema = require('./schema/response-v2.schema.json');
  const resp = JSON.parse(process.argv[1]);
  // ... validate with AJV or equivalent
" '{"ok":true,"command":...}'
```

The shipped `lib/config-loader.js` contains a minimal validator; for full JSON Schema validation, install `ajv` separately.
