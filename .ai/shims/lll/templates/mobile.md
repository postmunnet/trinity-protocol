---
ritual: lll
channel: mobile
purpose: "Render `ai lll` output for a narrow / mobile screen (Telegram, phone)"
last-updated: 2026-05-10
---

# `lll` — Mobile rendering template

> The AI rendering `ai lll` output to a **mobile / narrow screen**
> (trinity-tg-bot reply, terminal in 40-col mode, phone SSH session)
> should follow these rules. The bot's `sanitizeKernelOutput` already
> strips box-drawing chars at transport time; this template tells the AI
> how to RE-FORMAT the data above and beyond that.

## Channel signals (priority order)

1. Adapter sets `--channel=mobile` explicitly (e.g. trinity-tg-bot).
2. `TRINITY_RENDER_CHANNEL=mobile` in env.
3. User message arrived via Telegram `/lll` — bot context.

## Format rules

### Required
- ❌ **NO box-drawing characters** (no `╭ ╮ ┃ ─` or any `─-▟` block)
- ❌ **NO ASCII tables** with `|---|`-style horizontal rules
- ❌ **NO horizontal alignment** (column padding wraps unreadably on phone)
- ✅ One fact per line; emoji prefix instead of column header
- ✅ Compact timestamps (`HH:MM` only, drop full ISO)
- ✅ Truncate session ids to last 16 chars (or up to first segment after seq#)
- ✅ Max 4 audit rows (drop oldest); add `…+N more` if there are more
- ✅ Hard cap reply at 4000 chars (Telegram limit); truncate with `… [truncated]`

### Encouraged
- 📂 git: `branch X @ <short hash> · <N> dirty`
- 🟢 / ⚪ session: 🟢 + name when active, ⚪ + "no active session" otherwise
- 📋 audit (last 4): `HH:MM <type> · <decided_by>`
- 👉 next: 1-line action

### Avoid
- ❌ Restating sections the kernel already labeled — operator scans on phone
- ❌ Multi-paragraph narrative
- ❌ Code blocks longer than 10 lines

## Layout (compact)

```
🔍 lll
📂 main @ 4fdd44b · 94 dirty
🟢 0001_..._feat-ddd-hmac   (or)   ⚪ no active session
📋 last 4 events:
  16:55 lll.invoked · human
  16:46 session.closed · kernel
  16:46 rrr.completed · kernel
  16:46 graph.transition · kernel
👉 ai session new <slug>
```

## When to deviate

- Operator explicitly asks "show full output" → fall back to desktop template.
- Output references files only on desktop (e.g. open windows) → call out the
  pointer text but skip the file-list dump.
