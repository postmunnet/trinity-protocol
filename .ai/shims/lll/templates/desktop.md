---
ritual: lll
channel: desktop
purpose: "Render `ai lll` output for a desktop terminal (Claude Code, plain shell)"
last-updated: 2026-05-10
---

# `lll` — Desktop rendering template

> The AI rendering `ai lll` output to a **desktop terminal** (Claude Code,
> Warp, iTerm, etc.) should follow these rules. The kernel CLI itself
> still emits its own panel-style output via `rich`; this template guides
> the AI when it summarizes / paraphrases / streams that output back to
> the operator.

## Channel signals (priority order)

1. Adapter sets `--channel=desktop` explicitly.
2. `TRINITY_RENDER_CHANNEL=desktop` in env.
3. Default fallback when no mobile signal is present.

## Format rules

### OK to use
- ✅ ASCII tables with horizontal rules (`├──┼──┤`)
- ✅ Box-drawing characters (`╭ ╮ ╯ ╰ ┃ ─ ━`) — terminal renders cleanly
- ✅ Multi-line audit rows with full timestamps + `decided_by` + full session_id
- ✅ Up to 5 audit events, untruncated
- ✅ Footer next-action line (`👉 next: ai <verb>`)
- ✅ Color/markup hints from kernel (rich panels)

### Avoid
- ❌ Stripping the panel borders that the kernel emits
- ❌ Truncating session ids past the visible column width
- ❌ Re-formatting into bullets when the kernel output is already a table
  (the table is the value — bullets lose horizontal correlation)

## Layout (5 sections)

```
╭───── 🔍 lll — snapshot ─────╮
│ git      branch <X> @ <hash> · dirty: <N> file(s)
│ session  <session-id> | (none — `ai session new <task>`)
│ open     <THINK / SANDBOX / DO/dev pointers>
╰─────────────────────────────╯

┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ts                   ┃ type             ┃ decided_by ┃ session               ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ <iso-ts>             │ <event-type>     │ <decider>  │ <session-id>          │
│ ...                                                                          │
└──────────────────────┴──────────────────┴────────────┴───────────────────────┘
👉 next: <next-action>
```

## When to deviate

- Operator screen is < 80 cols → fall back to mobile template.
- Output is being captured for a log/CI artifact → preserve plain-text only;
  drop emoji + box-drawing if the consumer is a non-Unicode parser.
