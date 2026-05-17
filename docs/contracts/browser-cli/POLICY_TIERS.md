# Policy Tiers

Browser CLI classifies every command into one of three risk tiers. Tier mode controls which commands are allowed to execute — denied commands return `error_code: "POLICY_DENIED"` without touching the page.

## Tiers

| Tier | Intent | Examples |
|---|---|---|
| **safe** | Read-only / observation | `goto`, `text`, `exists`, `outline`, `assert-*`, `screenshot`, `wait-*`, `cookies`, `monitor-*`, `*-log` |
| **medium** | Legitimate user interaction | `click`, `fill`, `select`, `download-click`, `download-url`, `login`, `run-file` |
| **high** | Bypass UI safety | `force-click`, `force-fill`, `force-select`, `force-submit`, `force-enable`, `force-show`, `force-hide`, `upload` |

Full mapping: `lib/policy.js` — `COMMAND_TIER`.

## Modes

| Mode | Allows |
|---|---|
| `safe` | SAFE only |
| `normal` (default) | SAFE + MEDIUM |
| `aggressive` | SAFE + MEDIUM + HIGH |

## Mode resolution precedence

```
CLI flag (--policy=X)  >  config.policy.mode  >  env BROWSER_CLI_POLICY  >  default "normal"
```

Example config snippet:
```json
{
  "baseUrl": "...",
  "policy": { "mode": "normal" }
}
```

## Helper macro tiers

Helpers (YAML macros) do not have a static tier. The effective tier is **derived at expand time** — the max tier across all expanded sub-commands.

```yaml
helpers:
  recover-stuck-form:
    args: [id]
    steps:
      - goto /backend/x/{id}    # safe
      - force-enable input      # high  ← whole helper becomes HIGH
      - click button.submit     # medium
```

Calling this helper in `--policy=normal` mode → `POLICY_DENIED` because derived tier = `high`.

## Why `high` exists

Force commands bypass element `disabled`, `readOnly`, and visibility checks. They are invaluable for debugging stuck forms but should be explicit, not accidental. By defaulting to `normal`, Trinity/CI/automation cannot accidentally force a submit that the UI intentionally blocks.

## Overriding per run

```bash
# one-shot aggressive run for a specific recovery session
node index.js --config ... --policy=aggressive < recovery.txt
```

## Logging

Every policy denial emits a `POLICY_DENIED` event to the structured log (if `--log-file` is set), with fields `{verb, tier, mode}`. Use this to audit which runs hit tier boundaries.
