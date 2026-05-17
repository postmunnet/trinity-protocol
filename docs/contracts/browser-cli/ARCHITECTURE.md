# Browser CLI Architecture

**Version**: v0.1 | **Status**: Design-locked | **Last Updated**: 2026-04-24

Authoritative architecture overview for browser-cli. Contracts and implementations must conform to this document.

---

## 1. Purpose

Browser CLI is a **Playwright REPL for AI agents and humans** — portable browser automation via stdin/stdout (JSON responses).

**Primary goals**:
1. AI agents send commands, get structured JSON responses
2. Human users control the same browser instance in parallel
3. Real-time visibility of browser actions (AI + user)
4. Persistent Chrome session (login stays logged in across invocations)
5. tmux-based God Team integration (4-agent cohabitation)

---

## 2. Scope & Non-goals

### In scope (v0.1)
- ✅ Playwright-based browser automation
- ✅ CDP (Chrome DevTools Protocol) connection to external Chrome
- ✅ Command dispatch → handlers → structured response
- ✅ Policy tiers (safe/normal/aggressive)
- ✅ User action recorder (bidirectional log)
- ✅ tmux integration (shared Chrome, shared log)
- ✅ Claude Code skill integration
- ✅ Multi-tab management

### Out of scope (v0.1)
- ❌ WebDriver support (Playwright only)
- ❌ Firefox / Safari automation
- ❌ Distributed mode (network-exposed daemon)
- ❌ Authentication protocol beyond config-based fields
- ❌ Cloud hosting / SaaS

---

## 3. Architecture Layers

```
┌─────────────────────────────────────────────┐
│  INPUT LAYER                                 │
│  - stdin (REPL / pipe / run-file)           │
│  - --cmd <string> (one-shot)                 │
│  - tmux send-keys (agent injection)         │
│  - Unix socket (future daemon mode)          │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  PARSER (lib/parser.js)                      │
│  - verb + args + options                     │
│  - chain support (cmd1 ; cmd2)               │
│  - helper expansion                          │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  POLICY LAYER (lib/policy.js)                │
│  - tier classification (safe/medium/high)    │
│  - policy mode enforcement                   │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  DISPATCHER (index.js)                       │
│  - handler lookup                            │
│  - timeout + retry                           │
│  - artifact collection                       │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  COMMAND HANDLERS (lib/commands/)            │
│  - navigate / read / action / assert ...     │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  BROWSER LAYER (Playwright)                  │
│  - Launched: chromium.launch (local mode)    │
│  - Connected: chromium.connectOverCDP (CDP) │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  OUTPUT + LOGGING                            │
│  - stdout (JSON response per line)           │
│  - action log (ndjson, user + ai merged)    │
│  - policy log (ndjson)                       │
└─────────────────────────────────────────────┘
```

---

## 4. Execution Modes

### 4.1 Local mode (default, v2 compatible)
Launches new Chromium per invocation.
```bash
node index.js --config configs/<project>.json --login backend
```
- Chrome starts fresh, login each time
- Chrome closes on `exit` / stdin EOF
- ✅ Good for CI, one-shot tests

### 4.2 CDP mode (NEW in v0.1)
Connects to external Chrome with `--remote-debugging-port`.
```bash
# Start Chrome once:
./scripts/start-chrome-debug.sh

# Connect from CLI (multiple times, Chrome stays open):
node index.js --cdp http://localhost:9222 --config configs/<project>.json
```
- Chrome persistent (user controls lifecycle)
- Login stays logged in
- Multiple AI agents + user share same Chrome
- ✅ Primary mode for interactive / god-team work

### 4.3 One-shot command mode (NEW)
```bash
node index.js --cdp http://localhost:9222 --cmd "goto /order/123"
```
- Connect, execute single command, disconnect
- Chrome stays open
- ✅ Shell aliases rely on this

---

## 5. State Model

### Browser instance lifecycle
```
┌─────────────┐
│  UNLAUNCHED │
└──────┬──────┘
       │ launch OR connect-cdp
       ↓
┌─────────────┐        ┌──────────────┐
│   LOCAL     │ -exit→ │    CLOSED    │
└─────────────┘        └──────────────┘
       
┌─────────────┐        ┌──────────────┐
│ CDP-CONNECT │ -exit→ │  DETACHED    │ ← Chrome ยังเปิดอยู่
└──────┬──────┘        └──────────────┘
       │ Chrome user close
       ↓
┌─────────────┐
│  CDP-LOST   │
└─────────────┘
```

### Authentication state (per-profile)
```
NO_AUTH → AUTHENTICATING → AUTHED → EXPIRED
                ↓
           AUTH_FAILED
```

---

## 6. Phased Development Roadmap

| Phase | Focus | Deliverables | Status |
|:---:|:---|:---|:---:|
| **v0.1 Phase 1** | CDP foundation | `--cdp` flag, persistent Chrome, skip-login-if-cookies | 📋 Planned |
| **v0.1 Phase 2** | User UX | `--cmd`, tabs, new-tab, switch-tab, shell aliases | 📋 Planned |
| **v0.1 Phase 3** | Bidirectional recorder | `recorder.js` inject, event server, action log | 📋 Planned |
| **v0.1 Phase 4** | tmux integration | `ttt-browser.sh`, 5-pane layout, bcmd helper | 📋 Planned |

---

## 7. Component Inventory

### Existing (v2)
| Component | File | Role |
|:---|:---|:---|
| Parser | `lib/parser.js` | Parse verb + args |
| Policy | `lib/policy.js` | Tier classification |
| Commands | `lib/commands/*` | ~30 verb handlers |
| Wrapper | `lib/wrapper.js` | v1/v2 response format |
| Logger | `lib/logger.js` | Structured ndjson log |
| Session | `lib/session.js` | Auth state tracking |
| Config Loader | `lib/config-loader.js` | Profile config load |
| Artifacts | `lib/artifacts.js` | Screenshot/download refs |

### New in v0.1
| Component | File | Role |
|:---|:---|:---|
| CDP Connector | `lib/cdp.js` 🆕 | `connectOverCDP` + lifecycle |
| Chrome Launcher | `scripts/start-chrome-debug.sh` 🆕 | Start external Chrome |
| Action Recorder | `lib/recorder.js` 🆕 | Injected page script |
| Event Server | `lib/event-server.js` 🆕 | HTTP endpoint for user actions |
| Action Logger | `lib/action-logger.js` 🆕 | Unified user+AI log |
| tmux Setup | `scripts/ttt-browser.sh` 🆕 | 5-pane god team |
| Shell Aliases | `scripts/bashrc-snippet.sh` 🆕 | bcmd/bgoto/bclick |

---

## 8. Integration Points

### With Claude Code Skills
- Skills at `<project>/.claude/skills/vvv/` etc. can call `bcmd` helper
- Skills reference browser-cli command syntax
- No tight coupling (skills = prompts, CLI = tool)

### With project ai-docs
- `<project>/ai-docs/tools/BROWSER_CLI.md` → guide
- Config file: `<project>/.browser-cli/config.json` (or centralized)

### With Trinity V2 (future)
- Trinity kernel invokes browser-cli as executor
- Response JSON feeds verifier
- Artifacts reference browser screenshots/logs

### With tmux
- Pane 4 runs browser-cli CDP REPL
- Pane 5 tails action log
- Agents in panes 1-3 use `bcmd` helper

---

## 9. Response Schema Versions

### v1 (backward compatible, default)
```json
{"ok": true, "verb": "goto", "url": "/x", ...}
```

### v2 (structured envelope)
```json
{
  "ok": true,
  "verb": "goto",
  "args": ["/x"],
  "options": {},
  "data": {...},
  "meta": {
    "session": {...},
    "artifacts": [],
    "policy_tier": "safe",
    "duration_ms": 120,
    "run_id": "..."
  }
}
```

See: [`RESPONSE_SCHEMA.md`](RESPONSE_SCHEMA.md)

---

## 10. Policy & Safety

### Tier classification
- **safe**: read-only (outline, buttons, text, exists)
- **medium**: mutating but reversible (click, fill, select)
- **high**: destructive / irreversible (force-*, download-click, eval arbitrary)

### Policy modes
| Mode | Safe | Medium | High |
|:---:|:---:|:---:|:---:|
| `safe` | ✅ | ❌ | ❌ |
| `normal` | ✅ | ✅ | ❌ |
| `aggressive` | ✅ | ✅ | ✅ |

See: [`POLICY_TIERS.md`](POLICY_TIERS.md)

---

## 11. Multi-Client Coexistence (v0.1 key feature)

### Scenario: AI + User on same Chrome
```
Chrome (CDP port 9222)
   ↑                ↑                  ↑
   │                │                  │
User terminal     AI Claude         AI Codex
(types bcmd)      (writes via       (writes via
                   stdin pipe)        tmux send-keys)

All three → same Chrome instance
Shared: cookies, tabs, DOM state
```

### Conflict handling
- **Optimistic concurrency**: commands execute sequentially per connection
- **Action log**: all actors' actions logged with `source` field (user/ai:<agent>)
- **No locking**: race conditions possible; user/AI coordinate via chat

---

## 12. Privacy & Security

### Action recorder defaults
- ❌ Never log: `<input type="password">` values
- ❌ Never log: `[data-sensitive="true"]` fields
- ❌ Never log: `autocomplete="cc-*"` (credit card)
- ✅ Configurable: additional CSS selectors to skip

### Network binding
- Event server binds `127.0.0.1` only (never external)
- CDP endpoint assumed local

### Credential storage
- Config file (JSON) — user's responsibility to protect
- No credential caching in browser-cli code

---

## 13. Testing Strategy

| Level | Scope | Files |
|:---|:---|:---|
| Unit | parser, policy, wrapper | `tests/harness.js` |
| Integration | launch + commands (no CDP) | `tests/golden.js` |
| CDP mode | connect + commands | `tests/cdp.js` 🆕 |
| Recorder | event capture + privacy | `tests/recorder.js` 🆕 |
| tmux | end-to-end god team | `tests/tmux-integration.sh` 🆕 |

---

## 14. Versioning Policy

- **v0.1**: Initial contract-locked release (this document)
- **v0.2**: Bug fixes + minor additions (no schema break)
- **v1.0**: Production-stable (all contracts frozen)

Breaking changes to any contract → bump version + document migration in `MIGRATION_*.md`

---

## 15. References (เอกสารเชื่อมโยง)

### Binding Contracts
- [`CDP_CONTRACT.md`](CDP_CONTRACT.md) — CDP mode binding
- [`COMMAND_CONTRACT.md`](COMMAND_CONTRACT.md) — all verbs spec
- [`RECORDER_CONTRACT.md`](RECORDER_CONTRACT.md) — action recorder
- [`TMUX_INTEGRATION.md`](TMUX_INTEGRATION.md) — tmux layout

### Guides
- [`USER_GUIDE.md`](USER_GUIDE.md) — การใช้งานของ user
- [`AI_AGENT_GUIDE.md`](AI_AGENT_GUIDE.md) — การใช้งานของ AI
- [`SHELL_ALIASES.md`](SHELL_ALIASES.md) — bcmd templates

### Existing (v2)
- [`MIGRATION_V1_TO_V2.md`](MIGRATION_V1_TO_V2.md)
- [`RESPONSE_SCHEMA.md`](RESPONSE_SCHEMA.md)
- [`POLICY_TIERS.md`](POLICY_TIERS.md)

---

**Contract Established**: 2026-04-24
**Version**: v0.1
**Authority**: Design approval required for architecture changes
