---
ritual: nnn
channel: desktop
purpose: "Render `ai nnn` plan-envelope summary for a desktop terminal"
last-updated: 2026-05-10
---

# `nnn` — Desktop rendering template

## Channel signals
1. `--channel=desktop`. 2. `TRINITY_RENDER_CHANNEL=desktop`. 3. Default.

## Format rules
- ✅ Full plan envelope summary table — columns: `step n`, `title`,
  `est_min`, `risk`, `spec_ref`
- ✅ Box-drawing OK (terminal renders cleanly)
- ✅ Budget breach panel: every cap that exceeded with `cap`, `limit`,
  `estimate`, `ratio` columns + the human-readable revise hint
- ✅ NEEDS_HUMAN escalation surfaced verbatim

## Layout (success)
```
╭───── ✅ nnn ─────╮
│ scope:      THINK/02_SCOPE.md
│ acceptance: THINK/03_ACCEPTANCE.md
│ plan:       .state/plan.json
│ marker:     .state/nnn_pass
│ graph_state: DO
╰──────────────────╯

┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━┓
┃ # ┃ title                 ┃ min ┃ risk ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━┩
│ 1 │ <title>               │ 15  │ low  │
│ 2 │ ...                                │
└───┴───────────────────────┴─────┴──────┘
👉 next: ai gogogo
```

## Layout (NEEDS_HUMAN budget breach)
```
╭───── 🟡 nnn — NEEDS_HUMAN ─────╮
│ NEEDS_HUMAN — budget breach.
│   scope: THINK/02_SCOPE.md
│   breaches: [{cap, limit, estimate, ratio}, ...]
│
│ Revise estimates or add a budget_override
│ (decided_by: human, reason: ...) to plan envelope.
╰────────────────────────────────╯
```

## Anti-patterns
- ❌ Hiding spec_ref column — operators trace plans back to specs.
- ❌ Truncating step titles below 60 chars (operators read the title to
  understand the step purpose).
