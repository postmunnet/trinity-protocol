---
ritual: nnn
channel: mobile
purpose: "Render `ai nnn` plan summary for a narrow / mobile screen"
last-updated: 2026-05-10
---

# `nnn` — Mobile rendering template

## Channel signals
1. `--channel=mobile`. 2. `TRINITY_RENDER_CHANNEL=mobile`. 3. TG bot.

## Format rules
- ❌ **NO box-drawing characters**
- ❌ **NO ASCII tables** (mobile wraps unreadably)
- ✅ One step per line: `step N: <title 50ch>… · <Nm>· <risk>`
- ✅ Hard cap 4000 chars total
- ✅ NEEDS_HUMAN budget breach: 1-line summary `🟡 NEEDS_HUMAN — cap=<name> est=<X>m limit=<Y>m`
- ✅ Show total estimated_duration_minutes at top

## Layout (success)
```
✅ nnn · graph: DO · ~<total>m total
step 1: <50-char title>… · 15m · low
step 2: <50-char title>… · 25m · med
step 3: <50-char title>… · 30m · high
…+N more
next: ai gogogo
```

## Layout (NEEDS_HUMAN)
```
🟡 NEEDS_HUMAN — budget breach
cap=max_duration_minutes limit=30 est=90 ratio=3.0
fix: add budget_override (decided_by: human) to plan envelope
```

## Anti-patterns
- ❌ Dropping step risk — even on mobile, risk is what tells the
  operator whether to babysit the gogogo run.
- ❌ Hiding total estimated_duration — the operator's mobile decision
  is "do I have time for this now?".
