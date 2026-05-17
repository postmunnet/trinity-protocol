# 14 — `trinity-tg-bot` Sibling Tool Spec

> **Status:** Draft v0.3.0-beta (2026-05-10) · v0.3 adds Operational Brain quick-capture (`/note`) — composes with memory-cli v0.9.1 `note` verb. v0.2 baseline preserved (Phase 0 review closed; decisions C + Y baked in; in-bot voice transcription dropped)

## v0.3 Changelog (2026-05-10) — Operational Brain Session 1

- **`/note` intent (NEW)** — `lib/intent.js` extends `parseIntent()` with a
  dedicated `/note <free-form text>` regex (`NOTE_RE = /^\/note(?:\s+([\s\S]+))?$/i`)
  that runs BEFORE the generic whitespace-tokenize slash path so newlines,
  punctuation, and inline quotes survive into `args.text`.
- **Secret refusal (NEW)** — heuristic regex
  `SECRET_RE = /(password|api[_-]?key|secret|token|=\s*["'][^"']{6,}["'])/i`
  rejects accidental credential capture at intent time (returns
  `{action: 'reject', reason: "looks like secret/credential — please don't send via TG"}`).
  Operator sees the warning instead of the credential being persisted to
  the central DB or shipped to the memory-cli subprocess.
- **Length cap (NEW)** — `NOTE_MAX_LEN = 1900` chars; longer text is
  truncated with a `… [truncated]` suffix (TG message limit is 4096 but
  we leave headroom for the `✅ saved as <id>\n` reply).
- **`lib/flow/note.js` (NEW)** — spawns memory-cli as a subprocess via
  `node:child_process.spawnSync` with `{timeout: 10_000}`. Resolution
  order for the binary: `TEST_MEMORY_CLI_BIN` (test mock) >
  `MEMORY_CLI_BIN` (operator override) > sibling layout
  (`<repo>/../memory-cli/index.js`). JSON-stringifies the text token so
  quotes/newlines survive the shell boundary; passes `--source=tg-bot`
  so memory-cli tags the row's metadata.source for downstream digest
  filtering. Reply format: `✅ saved as <id>\n<preview>` (preview is
  the first 100 chars of the captured text).
- **Dispatcher wiring (`index.js`)** — new branch `if (intent.verb === 'note')`
  before the existing `vvv` branch; honours `intent.action === 'reject'`
  with a friendly TG warning, otherwise delegates to `noteFlow.handle()`.
- **Tests:** +10 cases (6 intent + 4 flow). Total: 49 (39 baseline + 10
  v0.3) green via `node --test tests/*.test.js tests/flow/*.test.js`.
- **Composes with:** memory-cli ≥0.9.1 (`note` verb + `documents.status`
  inbox column).

Bumps to **v0.3.0-beta**.

> **v0.2 baseline preserved:** Phase 0 review closed; decisions C (split-duty event tail) + Y (kernel HMAC verify at `core/auth.py`) baked in; in-bot voice transcription dropped (operator uses phone keyboard dictation)
> **Tier:** 6-A++ (Highest priority — direct user pain reduction)
> **Decision rules check:** D13 ✓ (calls Telegram external API), D14 ✓ (bot subprocess + kernel HMAC module both pass — see §2)
> **Depends on:** `notify-cli` (spec 13), TOOL_CONTRACT v1 (spec 01)
> **Goal:** Enable remote-first Trinity development — operate `lll/vvv/nnn/gogogo/rrr/ddd` from mobile via Telegram, using phone-keyboard text/dictation as the input surface, while traveling

## 0. Status

| Item | State |
|------|-------|
| Spec | Draft v0.2.0-beta |
| Implementation | Not started |
| Tests | Not started |
| Registered in `.ai/tools.yaml` | No |
| Contract test tier | Target: Platinum |

## 1. Why trinity-tg-bot

### Operator pain (measured)

User self-reported (Session K wrap interview):
- **Q: How often does `gogogo` block waiting for your approval?**
  → **"Many times per session"**
- **Q: How often do you review old audit chains from mobile?**
  → "Rarely" (observability is NOT the bottleneck)
- **Q: Which workflows need human approval?**
  → **"Every workflow with plan/goal/vvv/gogogo"**

**Diagnosis:** The bottleneck is **gate approval frequency × physical proximity to laptop**. Multiple gates per session × inability to approve while traveling = days lost waiting on humans-for-machine.

### Solution

A Telegram bot sibling that:
1. Listens for `notify-cli` events (the alert side)
2. Accepts text/voice commands from the operator's mobile (the control side)
3. Translates commands → kernel CLI invocations
4. Streams kernel output back as TG messages (with edits for live updates)

**Architecture invariant** (from CLAUDE.md + D2 + D10):
> Bot ≠ authority. Bot is a transport layer. Kernel + verifier remain the authority. Every `decided_by:human` action via TG is signed and lands in audit chain with `tg:<user_id>` attribution.

### Not in scope

- Coding env replacement (use `claude --teleport` for that)
- Web UI / dashboard rendering (`trinity-extension-platform` already does that read-only)
- Multi-tenant team support (single operator only in v0.1)
- Approval policy beyond allowlist (no roles/RBAC in v0.1)

## 2. Decision Rules Check (D13 + D14)

| Rule | Verdict | Reason |
|------|---------|--------|
| **D13 capability** | Sibling | Calls Telegram Bot API (external network) |
| **D14 cost (bot)** | Sibling | Per-user-action invocation (~10–50/day, NOT per kernel-step) — subprocess spawn cost negligible |
| **D14 cost (kernel HMAC verify)** | Kernel module (NOT sibling) | Decision Y, v0.2: HMAC verify lands in `core/auth.py` shim, not as a subprocess. Called once per aggressive op (~1–5/day), pure stdlib `hmac` — deterministic, zero deps. Per the secondary D14 rule, kernel-internal hot-path bypasses subprocess boundary even when capability is sibling-shaped. Bot-side-verify alternative rejected — see §6.1 Layer 3 |
| **Tier** | A++ | Highest user-impact item identified to date |
| **Approval gate** | Phase 0 review closed v0.2 (decisions C + Y baked in); Phase 1 build pending operator setup (BotFather + kernel HMAC secret) |

## 3. Capability surface

### 3.1 Bot commands (TG-side)

| Command | Maps to | State req | Notes |
|---------|---------|-----------|-------|
| `/start` | hello + show pending gates | none | Onboarding |
| `/lll` | `ai lll` | none | Snapshot |
| `/status` | session selector + state | none | "what's running" |
| `/pending` | list NEEDS_HUMAN gates across sessions | none | Bird's-eye |
| `/sessions` | list active + recent archived | none | Selector |
| `/select <id>` | bind chat to a session | sets `active_session` | All subsequent commands target this |
| `/new <slug>` | `ai session new <slug>` | none | Creates session, auto-selects |
| `/vvv` | start vvv Q&A flow | needs `active_session` | Multi-turn Q1..Q5 |
| `/nnn` | request plan envelope | needs vvv pass | (Phase 4: pair with plan-cli auto-gen) |
| `/gogogo` | `ai gogogo` (streaming) | needs nnn pass | Live message edit |
| `/stop` | kill running gogogo | mid-gogogo | Sends SIGTERM |
| `/rrr` | `ai rrr` | post-gogogo | One-shot |
| `/ddd <target> <reason>` | `ai ddd ...` | needs VERIFIED state | **Double-confirm** |
| `/audit <n>` | last n audit events | none | Default n=20 |
| `/recall <query>` | `memory-cli search` | none | Past retros search |
| `/cancel` | abort current Q&A or stream | any | Reset to IDLE |
| `/help` | command list | none | |

### 3.2 Inline keyboard buttons

Generated by `notify-cli` events forwarded through bot:

```
🟡 NEEDS_HUMAN
Session: tier1-r-followup-sprint
Gate: nnn budget breach
Cap: max_tool_calls 140 > 100

[✅ Approve override]  [❌ Reject]  [📋 Detail]  [⏸ Pause session]
```

Tap → `callback_query` → bot processes → kernel command + audit entry.

### 3.3 Conversation states (state machine)

```
            ┌─────────────┐
            │    IDLE     │◀───── /cancel from anywhere
            └──────┬──────┘
                   │
       ┌───────────┼───────────────┬───────────────┬──────────┐
       │           │               │               │          │
   /lll, /rrr   /vvv           /gogogo         GATE         /ddd
   /status      /select        /stop           event        (destruct)
   /audit       /new
       │           │               │               │          │
       ▼           ▼               ▼               ▼          ▼
  ONESHOT      VVV_QA        GOGOGO_STREAM    GATE_PEND    DDD_CONFIRM
  exec→reply   idx 1..5      tail audit       inline kbd   2-step prompt
  →IDLE        accumulate    edit msg         await tap    "type CONFIRM"
               submit→IDLE   final→IDLE       resolve→IDLE  exec→IDLE
```

State stored in SQLite at `~/.config/trinity-tg-bot/state.db`:
```sql
CREATE TABLE conversation (
    tg_user_id INTEGER PRIMARY KEY,
    state TEXT NOT NULL,           -- IDLE | VVV_QA | GOGOGO_STREAM | GATE_PEND | DDD_CONFIRM
    active_session TEXT,
    project_root TEXT NOT NULL,
    qa_idx INTEGER,                 -- VVV_QA only
    qa_answers_json TEXT,           -- VVV_QA only
    streaming_msg_id INTEGER,       -- GOGOGO_STREAM only
    pending_gate_json TEXT,         -- GATE_PEND only
    pending_destructive_json TEXT,  -- DDD_CONFIRM only
    updated_at TEXT NOT NULL
);
```

### 3.4 Fuzzy ritual matching

The bot does not run its own speech-to-text (see §4 — in-bot voice transcription removed in v0.2). However, the operator typically composes messages on phone using the **OS keyboard's built-in dictation** (iOS / Android voice typing), which is not 100% accurate — short codes like `lll` / `ddd` / `rrr` are routinely mangled into `"hello"` / `"daddy"` / `"are"` etc. The matcher below absorbs that operator-side noise so the bot does not reject legitimate intent over a single transcription glitch.

Match logic:

```python
def parse_intent(text: str) -> str | None:
    norm = text.lower().strip().replace(" ", "").replace(".", "").replace("-", "")
    # Exact codes
    if norm in {"lll","vvv","nnn","gogogo","rrr","ddd"}: return norm
    # Common voice errors
    aliases = {
        "lll": ["triplel", "lll", "ell"],
        "vvv": ["triplev", "vivivi", "vvv", "vee"],
        "nnn": ["triplen", "nnn"],
        "gogogo": ["gogogogo","goinggo","googly","gogogo","gogo"],
        "rrr": ["tripler","rrr"],
        "ddd": ["tripled","ddd"],
    }
    for cmd, alist in aliases.items():
        for a in alist:
            if norm == a: return cmd
    # Levenshtein fallback (≤2)
    for cmd in {"lll","vvv","nnn","gogogo","rrr","ddd"}:
        if levenshtein(norm, cmd) <= 2: return cmd
    return None
```

## 4. Voice input — out of scope (v0.2)

Original v0.1 draft proposed in-bot speech-to-text for paragraph-level voice notes (vvv Q2/Q3 scope). Removed in v0.2 because the operator already uses **phone keyboard dictation** (iOS / Android built-in voice typing) to compose Telegram messages. Audio → text conversion happens in the OS keyboard before the message ever leaves the phone, so the bot only ever receives text.

**Implications:**
- No external transcription API / on-device speech model dependency
- No in-bot speech module
- Three-cloud-hop privacy concern (TG → transcription cloud → TG) is eliminated by design — speech stays on-device
- Fuzzy intent matcher (§3.4) is **retained** to absorb residual typos from on-device dictation, which is not 100% accurate (esp. for short codes like "lll" / "ddd")

If a future operator demands in-bot voice ingestion, re-open this section in v0.3 with a fresh privacy threat model.

## 5. Streaming `gogogo`

### 5.1 Mechanism

```
Bot receives /gogogo
   ↓
Send initial msg "🚀 Starting <plan-step-count> steps..." → save msg_id
   ↓
Spawn `ai gogogo` as subprocess (background)
   ↓
Subscribe to events.ndjson tail (tail -F equivalent in JS/Python)
   ↓
For each new event matching session_id:
   ↓ buffer event in deque
   ↓
Every 2 seconds (or on completion):
   ↓ render summary string
   ↓ TG editMessageText(chat_id, msg_id, summary)
   ↓
On gogogo.completed:
   ↓ final edit with full report + [✅ rrr] [↩ Resume]
```

### 5.2 Render template

```
🚀 gogogo · 0001_2026-05-01_…tier1-sprint
plan: 16 steps · budget 240min/200tools

▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  13/16  (81%)

✅ R20 bulk-index
✅ R8 contract markers
✅ R15 engines.node
✅ R14 retroactive flag
✅ R16 stitch (deferred mark)
✅ R19 DRY tools-yaml
✅ R7 plan-envelope path
✅ R18 install non-clobber
✅ R13 baseline flag
✅ R17 verifier defaults doc
✅ R22 verify-cli wording
✅ R23 D14 promote
✅ R21 legacy stub
🔄 R5 test_basic accept idle|busy
⏸ test suite
⏸ rrr + TODO update

Last: PASS  ·  18.7 min elapsed
[⏹ Stop]  [📋 Audit tail]
```

### 5.3 Edit-rate respect

- TG limits: ~30 msg/sec per chat globally; ~1 edit/sec per message
- Buffer events 2 sec before edit → 0.5 edit/sec — well within limits
- On `gogogo.completed` → flush immediately (final state)

## 6. Security model

### 6.1 Layered controls (defense-in-depth)

```
Layer 1 — Telegram identity
   bot.allowed_user_ids = [<your_tg_user_id>]
   ALL inbound messages: reject if from.id not in allowlist

Layer 2 — Command tier
   Safe commands (lll, status, audit, recall) — no extra confirmation
   Normal commands (vvv, nnn, gogogo, rrr) — execute on receipt
   Aggressive commands (ddd target=prod, /stop, raw shell) — require:
     a) Type "CONFIRM" within 60s of issuing
     b) HMAC-signed payload to kernel

Layer 3 — Kernel HMAC verify (Decision Y, v0.2)
   For aggressive commands, bot computes:
     payload = {session, command, args, ts, nonce}
     sig = hmac_sha256(BOT_SECRET, payload)
   Kernel verifies sig at `core/auth.py` shim before firing transition.

   Why kernel-side verify (not bot-side):
   - Defense-in-depth: if bot host is compromised the attacker still
     cannot fire kernel transitions — kernel demands a sig that hashes
     under a secret the kernel reads itself, separate from bot env
   - The bot-side-verify alternative was rejected because it collapses
     to "trust the bot," which is the exact threat we are mitigating
   - `core/auth.py` lives at the shim layer (NOT inside the verifier
     engine), so it does not break the kernel-cleanliness invariant —
     no LLM, no network, called once per aggressive op, deterministic
     hmac stdlib only. Passes D14 cost rule (see §2)
   - Key material: kernel reads `TRINITY_KERNEL_HMAC_SECRET` env via
     standard env-loader; bot reads same value via
     `kernel_hmac_secret_env` config (§6.3). Operator provisions both
     to the same secret at setup time

Layer 4 — Audit trail
   Every TG-sourced action lands as audit event:
     {type, decided_by: "human:tg:<user_id>",
      evidence: {tg_msg_id, tg_chat_id, hmac_sig, ts}}
   Hash-chained → tamper-evident
```

### 6.2 Threat model

| Threat | Mitigation |
|--------|-----------|
| TG account takeover | 2FA on TG account; allowlist IDs; rotate `BOT_TOKEN` on suspicion |
| Bot host (Mac/VPS) compromise | HMAC sig from bot — kernel rejects unsigned aggressive ops; SSH key for `ai` exec scoped to non-prod ops; `ddd target=prod` requires kernel-side `decided_by:human` confirmation that bot ALONE cannot satisfy (kernel demands both bot HMAC AND human-typed CONFIRM in TG) |
| Replay of stale TG message | Bot tracks last `update_id`; rejects out-of-order; kernel checks payload `ts` within ±5min |
| Voice transcription poisoning | Fuzzy intent matcher refuses unknown intents; user always sees parsed intent before exec ("Did you mean: gogogo? [Yes] [No]") |
| TG cloud sniffing message text | Don't include secrets in messages; treat TG cloud as semi-trusted; for true secrets use SSH directly |
| Bot crash mid-gate | Kernel state unaffected; bot resumes via state.db on next launch; pending gates still visible via `/pending` |

### 6.3 Allowlist config

```json
{
  "allowed_tg_user_ids": [123456789],
  "allowed_chat_ids": [123456789],   // typically same as user ID for DMs
  "bot_token_env": "TRINITY_TG_BOT_TOKEN",
  "kernel_hmac_secret_env": "TRINITY_KERNEL_HMAC_SECRET",
  "destructive_commands": ["ddd", "stop", "deploy", "promote"],
  "destructive_confirm_window_seconds": 60
}
```

## 7. Deployment

### 7.1 Where bot runs

**Tier 1 (start here): Mac launchd**

```xml
<!-- ~/Library/LaunchAgents/com.trinity.tg-bot.plist -->
<plist>
  <dict>
    <key>Label</key><string>com.trinity.tg-bot</string>
    <key>ProgramArguments</key>
    <array>
      <string><user-home>/.nvm/versions/node/v22.5.0/bin/node</string>
      <string><workspace-root>/trinity-tg-bot/index.js</string>
      <string>--cmd</string>
      <string>run</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
      <key>TRINITY_TG_BOT_TOKEN</key><string>...</string>
      <key>TRINITY_KERNEL_HMAC_SECRET</key><string>...</string>
    </dict>
    <key>KeepAlive</key><true/>
    <key>RunAtLoad</key><true/>
    <key>StandardOutPath</key><string>/tmp/trinity-tg-bot.out</string>
    <key>StandardErrorPath</key><string>/tmp/trinity-tg-bot.err</string>
  </dict>
</plist>
```

Caveat: Mac sleeps. Use `caffeinate -i` or `pmset` to keep awake during travel days, OR migrate to Tier 2.

**Tier 2 (later): VPS systemd**

```ini
# /etc/systemd/system/trinity-tg-bot.service
[Unit]
Description=Trinity Telegram Bot
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/node /opt/trinity-tg-bot/index.js --cmd run
Restart=always
RestartSec=10
EnvironmentFile=/etc/trinity-tg-bot.env
User=trinity
Group=trinity

[Install]
WantedBy=multi-user.target
```

VPS bot must SSH back into operator's Mac to run kernel commands — adds operational complexity. Defer to phase 4+.

### 7.2 Bot ↔ kernel transport

**Option A — Bot on same host as kernel** (Mac launchd)
- Direct `subprocess.run(["python3", "-m", "cli.main", ...])`
- No SSH, no network surface
- Simplest, most secure

**Option B — Bot on VPS, kernel on Mac**
- Bot SSHs into Mac via deploy-key (scoped non-prod ops only)
- Mac must be reachable (Tailscale, ngrok, or persistent SSH tunnel)
- More moving parts; defer

v0.1 = **Option A only**.

## 8. Configuration

```
~/.config/trinity-tg-bot/
├── config.json              # bot token, allowlist, project_root, hmac
├── state.db                 # SQLite — conversation states
├── audit_offset              # last events.ndjson offset processed
└── logs/
    └── bot.log              # rotated daily
```

### 8.1 config.json (minimal)

```json
{
  "bot_token_env": "TRINITY_TG_BOT_TOKEN",
  "allowed_tg_user_ids": [123456789],
  "default_project_root": "<workspace-root>/trinity_v2",
  "kernel_invocation": {
    "kind": "subprocess",
    "cwd": "<workspace-root>/trinity_v2/.ai",
    "argv_prefix": ["python3", "-m", "cli.main"]
  },
  "destructive_commands": ["ddd", "stop"],
  "destructive_confirm_window_seconds": 60,
  "edit_throttle_seconds": 2
}
```

## 9. Capability list (TOOL_CONTRACT v1)

### 9.1 Verbs

| Verb | Action | Tier | Purpose |
|------|--------|------|---------|
| `run` | `bot.run` | aggressive | Long-running event loop (TG poll/webhook) |
| `health` | `bot.health` | safe | Liveness ping |
| `inspect-state` | `bot.inspect_state` | safe | Show conversation state for a user |

### 9.2 Universal flags

- `--health` — TOOL_CONTRACT health check
- `--config <path>` — config file override

## 10. Phased rollout

### Phase 1 — single-shot commands + security baseline (~1.5 day)

Ships:
- /start, /lll, /status, /sessions, /select, /audit, /recall, /pending, /help, /cancel
- IDLE → ONESHOT → IDLE state machine
- Allowlist enforcement (§6.1 Layer 1)
- Subprocess kernel exec
- Markdown formatting + inline buttons
- **HMAC sign on aggressive ops** (bot computes sig; kernel verifies — see §6.1 Layer 3 + §6.3) — *moved up from former Phase 5 to close the window where voice/destructive intents could fire before crypto gate is in place*
- **Destructive 2-step CONFIRM** (`ddd`, `stop`, `deploy`, `promote`) with 60s expiry window
- launchd plist + setup script (so the security baseline runs as a service from day 1)

Acceptance: Operator can ssh-free run `lll` from phone, see state. `ddd target=prod` requires CONFIRM and is rejected outside the 60s window. HMAC sigs visible on aggressive-op audit events.

### Phase 2 — interactive vvv Q&A (~1 day)

Ships:
- /vvv flow with 5 sequential prompts
- Multi-message answer accumulation (text only)
- IDLE → VVV_QA → IDLE transition
- /cancel mid-flow
- Auto-suggest defaults from past memory hints

Acceptance: Operator can start a fresh session + author 01_PROMPT.md from phone in < 5 min (typing or phone-keyboard dictation).

### Phase 3 — streaming gogogo (~½ day)

Ships:
- /gogogo with live msg edit (2-sec throttle)
- Audit tail subscription (separate offset.db from notify-cli — see §5 + spec 13 §6 split-duty contract)
- /stop sends SIGTERM
- Final report with [rrr] button

Acceptance: Operator sees gogogo progress in real-time on phone; can abort.

### Phase 4 — quality of life (~½ day)

Ships:
- Output truncation + gist URL or `/tmp` file
- `/quiet` / `/noisy` notification modes
- Per-user state inspection
- Memory-hint enrichment in /pending replies

Acceptance: Long gogogo report does not exceed Telegram message size cap; quiet mode mutes non-critical notify-cli forwards.

> **Note:** former Phase 4 (in-bot voice notes) and former Phase 5 (HMAC + 2-step CONFIRM) merged elsewhere — in-bot transcription deleted (operator uses phone keyboard dictation, see §4); HMAC + CONFIRM promoted into Phase 1.

### Total

**~3.5 days implementation + 2 weeks dogfooding** before deciding on Phase 5 (full Console).

## 11. Acceptance criteria (full spec)

| ID | Description | How to verify |
|----|-------------|---------------|
| A1 | Health envelope ok | `node index.js --health \| jq -e '.ok==true'` |
| A2 | Bot runs as launchd service | `launchctl list \| grep trinity.tg-bot` shows running |
| A3 | Allowlist rejects unknown TG user | Send msg from non-allowlisted account → bot ignores |
| A4 | /lll returns state in <3s | manual: send `/lll`, time response |
| A5 | /vvv flow completes Q1..Q5 + writes 01_PROMPT.md | manual end-to-end |
| A6 | /gogogo edits msg ≥3 times during run | grep TG bot log for editMessageText calls |
| A7 | /stop sends SIGTERM and gogogo halts | manual: start gogogo, /stop, verify no further audit events |
| A8 | **Phase 1 ships HMAC sign + 2-step CONFIRM together** (no destructive op fires before crypto gate is in place) | grep Phase 1 acceptance text mentions both `HMAC` and `CONFIRM`; integration smoke covers both |
| A9 | Destructive cmd requires CONFIRM within 60s | manual: /ddd target=prod, wait 70s, verify rejection |
| A10 | All TG-sourced actions land in audit chain | grep `decided_by.*human:tg` in events.ndjson |
| A11 | HMAC verified for aggressive ops by kernel (`core/auth.py`) | inject bad sig → kernel rejects with `auth.hmac.fail` audit event |
| A12 | Crash recovery resumes pending state | kill -9 bot, restart, verify VVV_QA state restored |
| A13 | Platinum contract test passes | `trinity-contract-test --bin "node /…/trinity-tg-bot/index.js" --tier=platinum` |
| A14 | `engines.node` pinned ≥22.5 (raw HTTPS to TG Bot API; no STT subprocess) | `package.json::engines.node` present |
| A15 | Sensitive payload masked in TG output | Inject event with `vault_content` → message shows `[redacted]` |

## 12. Implementation sketch

```
trinity-tg-bot/
├── package.json                    # Node 22.5+ engines pin
├── index.js                        # CLI entrypoint
├── lib/
│   ├── envelope.js                 # TOOL_CONTRACT v1 builder
│   ├── config.js                   # config.json loader
│   ├── allowlist.js                # TG user ID gate
│   ├── intent.js                   # fuzzy ritual parser
│   ├── state.js                    # SQLite conversation state
│   ├── tg/
│   │   ├── client.js               # Telegram Bot API wrapper (no library, raw HTTPS)
│   │   ├── handler.js              # update dispatch
│   │   ├── keyboard.js             # inline button builder
│   │   └── render.js               # markdown formatting
│   ├── kernel.js                   # subprocess.run("ai <verb>")
│   ├── stream.js                   # gogogo audit-tail (own offset.db, see §5 + spec 13 §6)
│   ├── flow/
│   │   ├── oneshot.js
│   │   ├── vvv_qa.js
│   │   ├── gogogo_stream.js
│   │   ├── gate_pending.js
│   │   └── ddd_confirm.js
│   ├── hmac.js                     # bot-side sign (kernel verifies — see §6.1 Layer 3)
│   └── audit.js                    # write tool.invoked/completed
└── tests/
    ├── intent.test.js
    ├── state.test.js
    ├── allowlist.test.js
    ├── kernel.test.js              # mock subprocess
    ├── tg/handler.test.js          # mock TG API
    ├── stream.test.js              # mock audit tail
    └── flow/*.test.js              # per-flow unit tests
```

Language: Node (zero external dep mandate per Trinity sibling pattern). Raw HTTPS calls to TG Bot API instead of `python-telegram-bot` to keep deps minimal. SQLite via `node:sqlite` (Node 22.5+).

## 13. Open questions

- **Q1:** Do we want a /sandbox command to simulate gate scenarios without affecting real audit chain? **Tentative:** v0.2.
- **Q2:** Multi-project switching — should `/cd <project>` change `default_project_root` permanently? **Tentative:** persistent per-user setting in state.db.
- **Q3:** Should bot post hourly heartbeat to confirm it's alive? **Tentative:** no — silence = good. /status pings explicitly.
- **Q4:** Image preview for diff/screenshot artifacts in TG? **Tentative:** v0.3 — generate inline with `sendPhoto`.
- **Q5:** Should we support Discord identically as a second channel from day one? **Tentative:** no — TG first; Discord via notify-cli channel only (read-only alerts; no command surface) until v0.2 if user demands.

## 14. Cross-references

- TOOL_CONTRACT v1: `01_TOOL_CONTRACT.md`
- D2 (decided_by:human invariant): `docs/migration/01_CONTEXT_AND_DECISIONS.md§D2`
- D10 (decided_by per transition): `01_CONTEXT_AND_DECISIONS.md§D10`
- D13 / D14 (sibling architecture + cost rule): `01_CONTEXT_AND_DECISIONS.md§D13/D14`
- notify-cli (split-duty `events.ndjson` ownership contract): `13_NOTIFY_CLI_SPEC.md` §6.0
- Kernel HMAC verify shim: `core/auth.py` (Decision Y, see §6.1 Layer 3 of this spec)
- TODO entry: `TRINITY_LEGACY/TODO.md` Tier 0

## 15. Versioning

- v0.1.0-beta — initial draft (Session K wrap, 2026-05-01)
- v0.2.0-beta — Phase 0 review closed (this revision, 2026-05-01):
  - Decision C: split-duty `events.ndjson` tail — notify-cli and tg-bot each maintain own offset (see §5 + spec 13 §6)
  - Decision Y: HMAC verify lands in kernel `core/auth.py` shim, NOT bot-side (see §6.1 Layer 3 + §2)
  - HMAC sign + 2-step destructive CONFIRM moved up from old Phase 5 into Phase 1 (security baseline ships day 1)
  - In-bot voice transcription dropped — operator uses phone keyboard dictation (see §4); fuzzy intent matcher §3.4 retained for typo absorption
  - Phase count 5 → 4; total estimate unchanged at 3.5 day
- v0.3.0-beta (planned) — Discord parity, image previews, sandbox mode
- v1.0.0 — freeze contract; pre-1.0 markers added in `tools-policy.yaml::supported_contract_versions` per R8

## 16. Estimate (rolled-up)

| Phase | Effort | Cumulative |
|-------|--------|-----------|
| 1 — single-shot + HMAC + CONFIRM (security baseline) | 1.5 day | 1.5 day |
| 2 — interactive vvv | 1 day | 2.5 day |
| 3 — streaming gogogo | 0.5 day | 3 day |
| 4 — quality of life | 0.5 day | **3.5 day** |
| Dogfood | 2 weeks | (parallel) |
| Phase 5 (full Console) | NOT scheduled | conditional on dogfood verdict |

> v0.2 reshuffle: HMAC + 2-step CONFIRM moved up from old Phase 5 into Phase 1 (security baseline); old Phase 4 (in-bot voice) deleted. Net total unchanged at 3.5 day.

## 17. ROI rationale

User pain × frequency:
- N gates/session × M sessions/week × P% awaiting human-at-laptop
- Bot collapses P → ~0% (operator can approve from anywhere with mobile signal)
- 3.5-day investment unlocks "remote-first dev" workflow
- Compared to full Console (6 weeks), bot delivers ~80% of value at ~10% of cost
- No new HTTP surface = security risk minimized
- Self-hostable = no subscription lock-in (vs `claude --teleport` which requires Anthropic subscription)

Decision gate (per D13 step 4): pending operator buy-in via TODO.md Tier 0 review.
