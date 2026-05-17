---
ritual: vvv
channel: mobile
purpose: "Render `ai vvv` answer set for a narrow / mobile screen"
last-updated: 2026-05-10
---

# `vvv` — Mobile rendering template

> Tight rendering for trinity-tg-bot, phone SSH, narrow term.
> Operator scans on phone — every line costs.

## Channel signals
1. `--channel=mobile`.
2. `TRINITY_RENDER_CHANNEL=mobile`.
3. Heuristic: bot context (TG `/vvv`).

## Format rules

### Required
- ❌ **NO box-drawing characters**
- ❌ **NO ASCII tables**
- ✅ One Q per line, `[Goal]:`, `[Scope]:`, etc. emoji-free
- ✅ Truncate each answer to ~80 chars, append `…` if over
- ✅ Hard cap 4000 chars (Telegram); truncate with `… [truncated]`

### Encouraged
- ✅ Short marker line at end: `✅ vvv passed · graph: THINK`
- ✅ 1-line next-action: `next: ai nnn --plan-envelope`
- ✅ Drop drill-down notes (cite memory hints separately if needed)

### Avoid
- ❌ Reordering Q1..Q5 — operator memorizes that order
- ❌ Paraphrasing IN/OUT scope clauses (load-bearing for nnn)
- ❌ Multi-paragraph drill-down

## Layout (compact)

```
📝 vvv
[Goal]: <80-char summary>
[Scope IN]: <80 chars>
[Scope OUT]: <80 chars>
[Constraint]: <80 chars>
[Acceptance]: N gates
[Risk]: <80 chars>

✅ vvv passed · graph: THINK
next: ai nnn --plan-envelope
```

## When to deviate
- Operator typed `/vvv full` → fall back desktop layout in TG (long
  message OK if explicitly asked).
- vvv NEEDS_HUMAN (missing answer) → show ALL of operator's partial
  text untruncated so they can fix the gap.
