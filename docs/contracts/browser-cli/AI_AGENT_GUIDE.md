# AI Agent Guide — คู่มือสำหรับ AI Agents

**Version**: v0.1 | **Last Updated**: 2026-04-24
**Parent**: [`ARCHITECTURE.md`](ARCHITECTURE.md)

คู่มือสำหรับ **AI agents** (Claude, Codex, Gemini) ที่ต้องการใช้ browser-cli

---

## 1. Invocation Patterns

AI agents มี 3 วิธีเรียกใช้ browser-cli:

### Pattern 1: Direct pipe (CI-style)
```bash
echo 'goto /order/123' | node /path/to/browser-cli/index.js --cdp http://localhost:9222 --config /path/to/configs/<project>.json --agent-name claude
```
- ใช้เมื่อ AI ทำงานคนเดียว ไม่มี tmux
- Per-command new connection

### Pattern 2: `bcmd` via tmux (god team mode)
```bash
bcmd "goto /order/123"
```
- ใช้เมื่ออยู่ใน tmux god team (pane 0, 1, 2 → ส่งไป pane 3)
- Persistent CDP connection ใน pane 3
- ดู [`TMUX_INTEGRATION.md`](TMUX_INTEGRATION.md)

### Pattern 3: `--cmd` one-shot inline
```bash
node /path/to/index.js --cdp http://localhost:9222 --config /path/to/x.json --agent-name claude --cmd "buttons"
```
- เร็วที่สุดถ้าไม่ต้อง REPL
- AI ต้อง parse JSON stdout

---

## 2. Agent Name Tagging (สำคัญ)

ทุก AI invocation ต้องระบุ `--agent-name`:
```bash
--agent-name claude    # หรือ codex, gemini, ai-anonymous
```

Event log จะมี `source: "ai:claude"` → ช่วย trace ว่า agent ไหนทำอะไร

**เมื่อไม่ระบุ**: default = "ai:unknown" → WARN level

---

## 3. Response Parsing (v2 schema)

AI ต้อง parse JSON stdout:
```javascript
// Sample parse logic
const output = execSync('echo "buttons" | bc --response-schema=v2');
const response = JSON.parse(output);

if (response.ok) {
  const buttons = response.data.buttons;
  // process ...
} else {
  const errorCode = response.error_code;
  // handle ...
}
```

### Must-check fields
| Field | Required |
|:---|:---:|
| `ok` | ✅ |
| `verb` | ✅ |
| `error_code` (if !ok) | ✅ |
| `data` (if ok) | ✅ |
| `meta.policy_tier` | ✅ |
| `meta.duration_ms` | ✅ |

ดู [`RESPONSE_SCHEMA.md`](RESPONSE_SCHEMA.md) ละเอียด

---

## 4. Integration with Short-Code Skills

### VVV (Verify)
เมื่อ AI ทำ `vvv` report ส่วน §3 Evidence Gathered — ควรใช้ browser-cli rank 1 evidence:

**Rank 1 (live-curl) → ใช้ browser-cli แทน curl**:
```
§3 Evidence Gathered:
- Live evidence: `bcmd "goto /order/123 ; snapshot"` → {"slipData": null, ...}
```

**Rank 4 (grep-found)**:
ไม่ต้องใช้ browser-cli — ใช้ Grep tool แทน

### NNN (Plan)
เมื่อ AI ทำ `nnn` plan ส่วน §8 Test Plan — ระบุ browser-cli commands:
```
§8 Test Plan:
| # | Scenario | Expected | Method |
|---|----------|----------|--------|
| 1 | Customer slip | Button visible | `bcmd "goto /order/123 ; exists button.retry"` |
```

### GOGOGO (Execute)
เมื่อ AI ทำ `gogogo` ส่วน §4 Dev Deploy — ใช้ browser-cli verify หลัง deploy:
```
§4 Dev Deploy + MD5:
- trinity_deploy.sh dev ...  → MD5 ✅
- Live verify: `bcmd "goto /test-url ; assert-exists .new-feature"` → ✅
```

### RRR (Retro)
Action log ของ browser-cli feed §4 AI Diary + §24 User Communication:
```bash
# หลัง session:
cat /tmp/browser-cli-actions.ndjson | jq -c 'select(.source=="user")'
# → AI อ่าน user actions → ใส่ใน §24
```

---

## 5. Error Handling (AI agent perspective)

### เมื่อเจอ error
| Error Code | AI Action |
|:---|:---|
| `ELEMENT_NOT_FOUND` | ใช้ `outline` / `exists` รีเช็ค selector |
| `TIMEOUT` | เพิ่ม `--timeout_ms` หรือ check network issue |
| `POLICY_DENIED` | ไม่ควร escalate policy mode โดยไม่มี user approval |
| `CDP_CONNECT_REFUSED` | แจ้ง user ว่า Chrome ไม่รัน → ขอให้ start |
| `CDP_DISCONNECTED` | Chrome ปิด → แจ้ง user รอ |
| `AUTH_FAILED` | แจ้ง user ให้ login manually |

### อย่า
- ❌ Auto-retry ด้วย policy เลวร้ายกว่าเดิม (escalation)
- ❌ ทำ `force-*` commands โดยไม่มี user approval
- ❌ Silent ignore error — always report to user

---

## 6. Concurrency Awareness

**Multiple agents on same Chrome**: เป็นได้ แต่ต้อง aware:

### Check ก่อนทำ action
```bash
# Read current URL ก่อนคลิก
bcmd "eval window.location.pathname"
# → ถ้า URL ไม่ใช่ที่คิดว่าอยู่ → อาจมี agent อื่น navigate ไปแล้ว
```

### Read before write pattern
```bash
# Before fill form field:
bcmd "value #amount"        # อ่านค่าปัจจุบัน
bcmd "fill #amount 500"      # ถึงจะ fill
```

### Action log ให้ trace
```bash
tail -n 20 /tmp/browser-cli-actions.ndjson | jq -c 'select(.source!="ai:claude")'
# → ดูว่า user / agent อื่นทำอะไรไปล่าสุด
```

---

## 7. User Action Awareness (อ่าน log)

### เมื่อ AI ควรอ่าน action log
- ก่อนทำ sensitive action → check user ทำอะไรไปก่อนหน้า
- เมื่อสงสัยว่า page state เปลี่ยน
- ระหว่าง long session → ติดตาม context

### Query patterns
```bash
# User actions ใน 5 นาทีล่าสุด
tail -n 100 /tmp/browser-cli-actions.ndjson | \
  jq -c 'select(.source=="user" and .ts > (now - 300 | todateiso8601))'

# เจอว่า user เปิด DevTools?
grep '"type":"devtools-open"' /tmp/browser-cli-actions.ndjson | tail -1

# URL ล่าสุดที่ user เข้า?
tail -n 50 /tmp/browser-cli-actions.ndjson | \
  jq -r 'select(.source=="user" and .type=="navigation") | .to' | tail -1
```

### AI response when user is debugging
```
AI: "เห็น user เปิด DevTools ใน /order/123 เมื่อสักครู่
     เดา: user กำลัง debug network issue
     ขอเสนอ: ให้ผม monitor-ajax + click save → user ดูใน DevTools"
```

---

## 8. Patterns สำหรับ Common AI Tasks

### Pattern: VVV ด้วย browser-cli
```bash
# Grep alone ไม่พอ → ต้อง verify state จริง
bcmd "goto /order/123"
bcmd "outline"                        # page structure
bcmd "exists .retry-button"           # check hypothesis
bcmd "eval window.slipData"           # runtime state
bcmd "monitor-ajax"
bcmd "click .test-btn"
bcmd "ajax-log"                       # network evidence
```

### Pattern: Fill form programmatically
```bash
bcmd "goto /order/new"
bcmd "fill #customer_name 'John Doe'"
bcmd "fill #amount 500"
bcmd "select #bank 2"
bcmd "screenshot pre-submit"
# รอ user approve ก่อน submit
bcmd "click button[type=submit]"
bcmd "wait-ajax"
bcmd "exists .success-message"
```

### Pattern: Bulk test scenarios
```bash
# ใน nnn plan §8 มี 8 scenarios
for i in 1 2 3 4 5 6 7 8; do
  bcmd "goto /test-case-$i"
  bcmd "screenshot case-$i"
  bcmd "exists .expected-element"
done
```

### Pattern: Iterate with user feedback
```bash
# AI ลอง hypothesis 1
bcmd "click .btn-option-1"
bcmd "screenshot after-click"

# User: "ไม่ใช่ ลองอีกปุ่ม"
# AI ทราบจาก log + user message

bcmd "click .btn-option-2"
bcmd "screenshot after-click-2"
```

---

## 9. Privacy Considerations

AI actions are logged — be aware:

### Don't log sensitive commands explicitly
```bash
# ❌ Don't print credentials to logs
bcmd "fill #password 'replace-me'"   # logged to actions.ndjson

# ✅ Use config-based auth
# Config file has creds → AI uses --login backend
# Recorder privacy filter skips password fields anyway
```

### When user asks AI to perform action
- AI shows planned command in chat BEFORE execute
- Gives user chance to review
- Explicit confirm ก่อนค่อย `gogogo`

---

## 10. Performance Notes

### Connection overhead
- **Pattern 1 (pipe)**: new connection ทุกครั้ง — ~500ms overhead
- **Pattern 2 (bcmd via tmux)**: persistent — ~50ms per command
- **Pattern 3 (--cmd)**: new connection — ~500ms

**Recommend**: ใช้ Pattern 2 (tmux) สำหรับ long sessions

### Rate limiting
- No built-in rate limit
- Multiple rapid commands OK
- Warning: flooding AJAX can slow page

### Screenshot size
- Default: full page PNG
- Size: ~100-500 KB typical
- Stored: `browser-cli/downloads/`

---

## 11. Integration with VVV/NNN/GOGOGO/RRR Skills

### Skill invocation workflow
```
User: /vvv ขอ debug order/123
↓
Claude Skill (SKILL.md) loaded
↓
Claude reads skill → produces VVV Report
  - §3 Evidence: uses `bcmd "goto /order/123 ; outline"`
  - §4 ASCII if flow
  - §9 Confidence
↓
User: /nnn
↓
Claude reads nnn skill → produces NNN Plan
  - §2 Tasks reference browser-cli commands
  - §8 Test Plan = browser-cli commands
↓
User: /gogogo
↓
Claude reads gogogo skill → executes
  - §2 Execution via bcmd
  - §4 Dev deploy + MD5
  - §5 Prod approval wait
↓
User: /rrr
↓
Claude reads rrr skill → produces retro
  - §4 AI Diary (references actions log)
  - §20 Time metrics from action log timestamps
```

---

## 12. Reference Sheet

### Quick verb reference
```
# Navigate
goto / back / forward / reload

# Read
text / html / attrs / exists / value / eval / outline / buttons / forms / table / snapshot / cookies

# Action
click / fill / type / press / select / check / upload / hover / focus / screenshot

# Force (high tier)
force-click / force-fill / force-submit / force-enable / force-show

# Download
download-click / downloads

# Monitor
monitor-ajax / ajax-log / monitor-console / console-log / wait-ajax / wait / wait-selector

# Assert
assert-text / assert-exists / assert-visible / assert-enabled / assert-value

# Session
login / logout / exit

# Tab
tabs / switch-tab / new-tab / close-tab

# Recorder
start-recording / stop-recording / recording-status / tail-actions

# Chain
cmd1 ; cmd2

# Helper
run-file <path> / helper <name>
```

ละเอียด: [`COMMAND_CONTRACT.md`](COMMAND_CONTRACT.md)

---

## 13. Links

- Parent: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Contracts: [`CDP_CONTRACT.md`](CDP_CONTRACT.md), [`COMMAND_CONTRACT.md`](COMMAND_CONTRACT.md), [`RECORDER_CONTRACT.md`](RECORDER_CONTRACT.md), [`TMUX_INTEGRATION.md`](TMUX_INTEGRATION.md)
- User: [`USER_GUIDE.md`](USER_GUIDE.md) (human-focused)
- Shell: [`SHELL_ALIASES.md`](SHELL_ALIASES.md)
- Troubleshooting: [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- project skill SKILLs: `<project>/.claude/skills/*/SKILL.md`

---

**Created**: 2026-04-24
**Version**: v0.1
