---
ritual: gogogo
channel: mobile
purpose: "Render `ai gogogo` verdicts for a narrow / mobile screen"
last-updated: 2026-05-10
---

# `gogogo` — Mobile rendering template

## Channel signals
1. `--channel=mobile`. 2. `TRINITY_RENDER_CHANNEL=mobile`. 3. TG bot.

## Format rules
- ❌ **NO box-drawing characters**
- ❌ **NO ASCII tables**
- ✅ One step per line: `step N -> PASS` (or `RETRY`/`FAIL` with 1-line reason)
- ✅ Drop `(reason)` text on PASS — only show on retry/fail/dead
- ✅ 1-line summary at end: `▶️ steps: N · graph: VERIFIED`
- ✅ Streaming-friendly — bot can edit a single message every 2s with
  the latest line appended (per `gogogo_stream.js` pattern)
- ✅ Hard cap 4000 chars

## Layout (success, streaming end-state)
```
▶️ gogogo
step 1 -> PASS
step 2 -> PASS
step 3 -> PASS
…
step N -> PASS

✅ steps: N · graph: VERIFIED
next: ai ddd
```

## Layout (NEEDS_HUMAN — full reason mandatory)
```
🟡 NEEDS_HUMAN at step N
cap=max_iterations limit=8 est=12 ratio=1.5
revise: edit plan envelope or budget_override
```

## Anti-patterns
- ❌ Hiding NEEDS_HUMAN breach detail — even on mobile, this is
  ALWAYS load-bearing. Operator must see the cap name + ratio.
- ❌ Showing PASS reasons (visual noise; operator only cares about non-PASS).
- ❌ Box-drawing or ASCII tables.
