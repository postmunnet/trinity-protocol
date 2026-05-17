# 13 — `notify-cli` Sibling Tool Spec

> **Status:** Draft v0.2.0-beta (2026-05-01) · Phase 0 review closed; split-duty contract for `events.ndjson` ownership baked in (§6.0, Decision C)
> **Tier:** 6-A (Clear sibling — closes real operational gap)
> **Decision rules check:** D13 ✓ (calls external networks/APIs), D14 ✓ (called per audit-event, NOT per kernel-step → bounded subprocess cost)
> **Depends on:** TOOL_CONTRACT v1 (`docs/specs/01_TOOL_CONTRACT.md`)
> **Used by:** `trinity-tg-bot` (spec 14, share `events.ndjson` via §6.0 split-duty contract), future `trinity-console`

## 0. Status

| Item | State |
|------|-------|
| Spec | Draft v0.2.0-beta |
| Implementation | Not started |
| Tests | Not started |
| Registered in `.ai/tools.yaml` | No |
| Contract test tier | Target: Platinum |

## 1. Why notify-cli

### Problem

Trinity kernel emits operationally-significant audit events that today have **no escalation channel**:

- `gogogo.step.failed` — verifier returned RETRY/DEAD, loop stuck
- `loop.budget.breach` — gogogo blew its budget, NEEDS_HUMAN escalation
- `nnn` budget breach → NEEDS_HUMAN
- `ddd` requested → human-decided promote/deploy gate awaits
- `vvv` written → next session ready for review
- `rrr.completed` / `rrr.retroactive` — closure events worth knowing

Operator currently must:
1. SSH into the host
2. `ai lll` to see state
3. Tail `events.ndjson` manually

This breaks remote workflows (mobile/away-from-desk) and forces synchronous attention.

### Solution

`notify-cli` is a **sibling tool** that bridges audit-chain events to external channels (Telegram, Discord, email, webhook, Slack, …) via a plug-in pattern.

It is **not** a notification service — it is a thin adapter that:
- subscribes to `events.ndjson` (tail mode) OR receives one-shot events (push mode)
- filters by event type / severity
- formats per-channel
- forwards to the channel's API
- emits its own `tool.invoked` + `tool.completed` audit events

### Not in scope

- Persisting message history (channels do this)
- Two-way interaction (channel → kernel) — that's `trinity-tg-bot`'s job (spec 14)
- Scheduling / batching (cron-cli's job)
- Templating beyond simple `${field}` interpolation

## 2. Decision Rules Check (D13 + D14)

| Rule | Verdict | Reason |
|------|---------|--------|
| **D13 capability** | Sibling | calls external network APIs (Telegram, Slack, SMTP) |
| **D14 cost** | Sibling | called once per audit event matching filter, NOT per gogogo-step. Subprocess overhead acceptable (~50ms × N events) vs benefit (provider SDK isolation, lifecycle decoupling) |
| **Tier** | A | closes real gap (no escalation channel today) |
| **Approval gate** | Pending user buy-in (this spec) |

## 3. Capability

### 3.1 Verbs

| Verb | Action namespace | Tier | Purpose |
|------|------------------|------|---------|
| `send` | `notify.send` | normal | Send one-shot notification to a channel |
| `watch` | `notify.watch` | normal | Long-running tail of audit events; forward matches to configured channels |
| `list-channels` | `notify.list_channels` | safe | List configured channels |
| `test-channel` | `notify.test_channel` | normal | Send a smoke message to verify a channel works |
| `list-rules` | `notify.list_rules` | safe | List configured forward rules |
| `add-rule` / `remove-rule` | `notify.{add,remove}_rule` | normal | CRUD for forward rules |

### 3.2 Binary interface

```bash
notify-cli [--cmd "<verb> [args]"] [universal-flags]
```

Universal flags (TOOL_CONTRACT v1 §3):
- `--health` — return `{ok, schema_version, tool, action: "health"}` and exit 0
- `--config <path>` — override config file location

### 3.3 Usage examples

```bash
# Send a one-shot
notify-cli --cmd 'send --channel=telegram --severity=high \
  --title="NEEDS_HUMAN" --body="nnn budget breach @ tier1-sprint"'

# Start audit watcher (long-running)
notify-cli --cmd 'watch --project-root=<workspace-root>/trinity_v2'

# Verify channel config
notify-cli --cmd 'test-channel --channel=telegram'

# List rules
notify-cli --cmd 'list-rules'
```

### 3.4 Response envelopes (TOOL_CONTRACT v1 §4)

**`send` ok:**
```json
{
  "ok": true,
  "schema_version": "1.0",
  "tool": "notify-cli",
  "tool_version": "0.1.0-beta",
  "command": "send",
  "action": "notify.send",
  "data": {
    "channel": "telegram",
    "channel_msg_id": "123456",
    "delivered_at": "2026-05-01T10:23:45Z"
  },
  "artifacts": [],
  "error": null,
  "meta": {"ts": "2026-05-01T10:23:45.612Z"}
}
```

**`send` error (channel down):**
```json
{
  "ok": false,
  "command": "send",
  "action": null,
  "data": null,
  "error": {
    "code": "channel_unavailable",
    "message": "telegram bot API returned 502",
    "channel": "telegram",
    "retry_after_seconds": 30
  }
}
```

## 4. Configuration

### 4.1 Location

```
~/.config/notify-cli/channels.json
~/.config/notify-cli/rules.json
~/.config/notify-cli/state.db          # SQLite — last-seen audit offset
```

Per LLM-tool key-management invariant (TODO Tier 6 design pattern):
> **LLM-using tools manage their own API keys (`~/.config/<tool>/keys.json` or `.env`); never via Trinity vault**

### 4.2 channels.json (example)

```json
{
  "telegram": {
    "kind": "telegram",
    "bot_token": "1234567890:AAA...",
    "chat_id": "@your_dm_or_channel"
  },
  "telegram_alerts": {
    "kind": "telegram",
    "bot_token": "1234567890:AAA...",
    "chat_id": "-100xxx"
  },
  "discord_dev": {
    "kind": "discord",
    "webhook_url": "https://discord.com/api/webhooks/..."
  },
  "email_oncall": {
    "kind": "smtp",
    "host": "smtp.fastmail.com",
    "port": 587,
    "username": "ops@example.com",
    "password_env": "SMTP_PASSWORD",
    "to": "oncall@example.com",
    "from": "trinity@example.com"
  },
  "webhook_pipeline": {
    "kind": "webhook",
    "url": "https://example.com/trinity-events",
    "method": "POST",
    "headers": {"X-Auth-Token": "..."},
    "hmac_secret_env": "WEBHOOK_HMAC_SECRET"
  }
}
```

### 4.3 rules.json (example)

```json
[
  {
    "id": "needs-human-to-tg",
    "match": {"type_in": ["loop.budget.breach", "gogogo.step.failed"]},
    "channels": ["telegram"],
    "template": "🟡 NEEDS_HUMAN\n${session_id}\n${reason}",
    "throttle_seconds": 30
  },
  {
    "id": "deploy-events-to-discord",
    "match": {"type_glob": "ddd.*", "severity_min": "info"},
    "channels": ["discord_dev"],
    "template": "🚀 ${type}\n${session_id} → ${target}\nby ${decided_by}"
  },
  {
    "id": "rrr-summary-to-email",
    "match": {"type": "rrr.completed"},
    "channels": ["email_oncall"],
    "template_file": "${HOME}/.config/notify-cli/templates/rrr-summary.md.j2"
  }
]
```

## 5. Channel plug-in pattern

Each channel is a JS/Python module exposing:

```python
class Channel:
    name: str          # "telegram", "discord", "smtp", ...

    def validate_config(self, cfg: dict) -> list[str]:
        """Return list of error strings, empty if valid."""

    def health(self) -> dict:
        """Return {ok, latency_ms, last_check_ts}"""

    def send(self, payload: NotifyPayload) -> SendResult:
        """Deliver payload. Return {ok, channel_msg_id, error?}"""
```

### 5.1 Built-in channels (v0.1)

| Kind | Library | Auth |
|------|---------|------|
| `telegram` | python-telegram-bot OR raw HTTPS | bot_token + chat_id |
| `discord` | requests (webhook is just HTTPS POST) | webhook_url |
| `smtp` | stdlib smtplib | host/port/user/pass |
| `webhook` | requests | optional HMAC sign |

### 5.2 Future channels (out of v0.1)

- `slack` (incoming-webhook same as Discord)
- `signal` (signald socket)
- `matrix` (matrix-nio)
- `pagerduty` (events API)

## 6. Watch mode (audit tail)

`notify-cli --cmd 'watch --project-root=...'` — long-running daemon:

1. Read `state.db.last_offset` (default 0)
2. `tail -F .ai/audit/events.ndjson` from offset
3. For each new event:
   - Parse JSON line
   - For each rule in `rules.json`:
     - If `rule.match` matches event → resolve channels → send
     - Apply `throttle_seconds` per rule_id (dedupe burst)
   - Update `state.last_offset`
4. On crash: resume from `state.last_offset`

### 6.0 Ownership of `events.ndjson` — Decision C (split duties, v0.2)

Spec 14 (`trinity-tg-bot`) also tails `events.ndjson` for streaming `/gogogo` updates. To avoid race / coordination over a single offset cursor, **the two daemons split duties and each maintain an independent offset**:

| Consumer | Reads | Filters to | Offset file | Failure domain |
|----------|-------|-----------|-------------|----------------|
| `notify-cli` watch | full file via `tail -F` | rules.json matchers (ALERT-class events: `*.failed`, `*.breach`, `ddd.requested`, `loop.budget.breach`, etc.) | `~/.config/notify-cli/state.db::last_offset` | independent — TG bot crash does not affect channel forwarding |
| `trinity-tg-bot` stream | full file via `tail -F` | session_id-scoped events for the *current* user-attached session only (during `/gogogo`) | `~/.config/trinity-tg-bot/audit_offset` | independent — notify-cli crash does not affect live streaming |

**Trade-offs of split:**
- ✅ Independent failure domains — either daemon can crash without dropping the other's events
- ✅ Zero IPC, zero shared lock — each daemon owns its own state
- ✅ No coupling between sibling versions
- ❌ The file is `tail -F`'d twice — kernel-side I/O cost is `2 × N events/sec` (negligible at Trinity event rates: <10/sec peak)
- ❌ Two offset files to back up / monitor

**Rejected alternatives:**
- *(A) Bot imports notify-cli as a library* — couples bot lifetime to notify-cli; bot crash kills channel forwarding too
- *(B) notify-cli pipes events to bot via Unix socket* — adds an extra failure surface (socket reconnect logic) without removing the underlying need for offset state

**Cross-spec contract:** consumers MUST NOT write to each other's offset file. Each daemon writes only to its own state location listed above.

---

### 6.1 Rule matching DSL

```yaml
match:
  type: "ddd.requested"          # exact match
  type_in: ["a", "b"]            # OR-list
  type_glob: "gogogo.*"          # glob (fnmatch)
  severity_min: info             # info|warn|error|critical
  decided_by: "human"            # filter on event field
  session_id_glob: "0001*"       # filter on event field
```

### 6.2 Severity inference

Inferred from event type if `severity` field absent:

| Pattern | Severity |
|---------|----------|
| `*.failed`, `*.breach`, `*.error` | `error` |
| `*.retroactive`, `gogogo.step.failed` | `warn` |
| `rrr.completed`, `*.passed` | `info` |
| `lll.invoked` | `debug` (skip by default) |

## 7. Audit hooks

Per TOOL_CONTRACT v1 §6 (Tool composition), every `notify-cli` invocation lands as:

```json
{"type":"tool.invoked", "details":{"tool":"notify-cli","command":"send","decided_by":"kernel"}}
{"type":"tool.completed", "details":{"tool":"notify-cli","command":"send","ok":true,"channel":"telegram","msg_id":"..."}}
```

This makes notify-cli observable from `lll` / dashboard / chain replay.

**Self-loop guard:** notify-cli MUST NOT match its own `tool.invoked`/`tool.completed` events in watch mode (would cause infinite loop). Built-in skip-list:
```
SELF_TYPES = {"tool.invoked", "tool.completed"}  # when tool == "notify-cli"
```

## 8. Security & privacy

### 8.1 Whitelist payload fields

The `${var}` template DSL only resolves whitelisted fields:

```python
ALLOWED_FIELDS = {
    "type", "ts", "session_id", "graph_state", "decided_by",
    "from_state", "to_state", "trigger", "step_n", "title",
    "verifier_verdict", "verifier_reason", "rule_set",
    "target", "reason", "breaches"
}
```

Anything else (e.g. `vault_content`, raw `stdout`, file paths inside artifacts) — silently masked as `[redacted]`.

### 8.2 Channel secrets

- API tokens stored in `~/.config/notify-cli/channels.json` mode `0600`
- OR resolved from env via `password_env: "SMTP_PASSWORD"` pattern
- `notify-cli list-channels` redacts secrets in output (shows `bot_token: "12345...redacted..."`)

### 8.3 Webhook HMAC

When `hmac_secret_env` configured, `webhook` channel signs payload:
```
X-Trinity-Signature: sha256=<hex(hmac(secret, body))>
X-Trinity-Timestamp: <iso8601>
```

Receiver must verify within ±5 min window to prevent replay.

## 9. Implementation sketch

```
notify-cli/
├── package.json                # Node 22.5+ engines pin
├── index.js                    # CLI entrypoint
├── lib/
│   ├── envelope.js             # TOOL_CONTRACT v1 envelope builder
│   ├── config.js               # load channels.json + rules.json
│   ├── matcher.js              # rule matching DSL
│   ├── template.js             # ${var} interpolation + whitelist
│   ├── watcher.js              # tail-F events.ndjson
│   ├── state.js                # SQLite last_offset
│   ├── audit_emit.js           # write tool.invoked/completed back to kernel
│   └── channels/
│       ├── telegram.js
│       ├── discord.js
│       ├── smtp.js
│       └── webhook.js
└── tests/
    ├── matcher.test.js
    ├── template.test.js
    ├── watcher.test.js
    └── channels/*.test.js      # mock HTTP for each
```

Language: Node (matches memory-cli / retro-cli / extension-platform). Zero runtime deps beyond stdlib + `node-fetch` if pre-22.

## 10. Testing

### 10.1 Unit (Node `node:test`)

- matcher: 20+ rule shape × event shape combos
- template: whitelist enforcement + `${missing}` → `[unknown]`
- watcher: synthetic events.ndjson, verify offset persistence after crash
- channels: mock HTTP server per channel, verify request shape

### 10.2 Contract (trinity-contract-test)

```
trinity-contract-test --bin "node <workspace-root>/notify-cli/index.js" --tier=platinum
```

Must pass:
- Bronze: envelope shape on `--health`
- Silver: error envelope on bad input
- Gold: schema_version + tool_version present
- Platinum: `npm test` exits 0

### 10.3 Integration (manual smoke)

```bash
# 1. Configure a TG bot via @BotFather, drop creds in channels.json
# 2. Run test-channel
notify-cli --cmd 'test-channel --channel=telegram'
# Expect: TG dm shows "🧪 notify-cli smoke test from trinity_v2"

# 3. Start watcher, trigger an event
notify-cli --cmd 'watch --project-root=<workspace-root>/trinity_v2' &
ai lll  # writes lll.invoked event
# Expect: nothing on TG (lll filtered out by severity:debug)

cd <workspace-root>/trinity_v2/.ai
python3 -m cli.main session new test-notify
python3 -m cli.main vvv --answer "1=test" --answer "2=test" \
  --answer "3=test" --answer "4=test" --answer "5=test"
# Expect: TG shows "✅ vvv.passed @ test-notify"
```

## 11. Acceptance criteria

| ID | Description | Command |
|----|-------------|---------|
| A1 | `--health` envelope ok | `node index.js --health \| jq -e '.ok==true and .tool=="notify-cli"'` |
| A2 | `npm test` passes | `cd notify-cli && npm test` |
| A3 | Platinum contract test passes | `trinity-contract-test --bin "node /…/notify-cli/index.js" --tier=platinum` |
| A4 | Telegram smoke message delivered | manual: `test-channel --channel=telegram` → check phone |
| A5 | Watch mode picks up new event | inject synthetic event line → verify TG within 5s |
| A6 | Throttle dedupes burst | inject same event 10× in 1s → exactly 1 message sent |
| A7 | Sensitive field masked | inject event with `vault_content` → message shows `[redacted]` |
| A8 | Crash recovery resumes from last offset | kill -9 watcher → restart → no duplicate sends |
| A9 | Tool emits its own audit hooks | grep `tool.invoked.*notify-cli` in `events.ndjson` |
| A10 | `engines.node` pinned ≥18 | `package.json::engines.node` present |

## 12. Open questions

- **Q1:** Should `watch` mode run as launchd/systemd service or as a Trinity sidecar fired by `ai session new`?
  - **Tentative:** standalone launchd service — same lifecycle as the operator's machine, not per-session.
- **Q2:** Should rules.json be hot-reloaded or require restart?
  - **Tentative:** SIGHUP triggers reload; restart unnecessary.
- **Q3:** Per-channel rate limit vs per-rule throttle — pick one or both?
  - **Tentative:** both. Per-rule = dedupe; per-channel = respect Telegram's 30msg/sec.
- **Q4:** Mute hours / DnD?
  - **Tentative:** v0.2 feature; add `quiet_hours: [start_local, end_local]` per channel.

## 13. Cross-references

- TOOL_CONTRACT v1: `01_TOOL_CONTRACT.md`
- D13 (plugin tool architecture): `docs/migration/01_CONTEXT_AND_DECISIONS.md§D13`
- D14 (cost rule): `docs/migration/01_CONTEXT_AND_DECISIONS.md§D14`
- TG bot consumer (split-duty `events.ndjson` contract): `14_TRINITY_TG_BOT_SPEC.md` §5 + §6
- TODO entry: `TRINITY_LEGACY/TODO.md` Tier 0 + Tier 6-A

## 14. Versioning

- v0.1.0-beta — initial draft (Session K wrap, 2026-05-01)
- v0.2.0-beta — Phase 0 review closed (this revision, 2026-05-01):
  - §6.0 added — Decision C: split-duty `events.ndjson` ownership (notify-cli + tg-bot each maintain own offset, independent failure domains)
  - Cross-refs aligned with spec 14 v0.2.0-beta
- v0.3.0-beta (planned) — add quiet hours, slack channel
- v1.0.0 — freeze contract; pre-1.0 markers added in `tools-policy.yaml::supported_contract_versions` per R8

## 15. Estimate

| Work | Effort |
|------|--------|
| `lib/` modules (config, matcher, template, watcher, state) | ~3 hr |
| Channel modules (telegram + webhook + smtp + discord) | ~3 hr |
| Tests (unit + contract) | ~2 hr |
| Manual integration smoke + docs | ~1 hr |
| **Total** | **~9 hr (~1.5 day)** |
