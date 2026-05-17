---
ritual: rrr
channel: mobile
purpose: "Render `ai rrr` retro summary for a narrow / mobile screen"
last-updated: 2026-05-10
---

# `rrr` — Mobile rendering template

## Channel signals
1. `--channel=mobile`. 2. `TRINITY_RENDER_CHANNEL=mobile`. 3. TG bot.

## Format rules
- ❌ **NO box-drawing characters**
- ❌ **NO ASCII tables** (metrics table wraps unreadably)
- ✅ Two key lines: PASS/FAIL gate + 1-line metrics digest
- ✅ Retro path → basename only
- ✅ memory_learn outcome → 1-line note (especially if -6 was the
  issue R37 closed; bot can flag if it sees -6 returncode again)
- ✅ Hard cap 4000 chars

## Layout
```
🏁 rrr · graph: DONE
RRR contract: PASS · acceptance: PASS · forbidden-diff: 0
metrics: events=N · transitions=M · iters=K · verdicts={"PASS":K} · dur=X.Xm
retro: <basename>.md
memory: ok · id=<retro-id>
next: ai close
```

## Layout (any FAIL)
```
🏁 rrr · graph: <state>
🔴 RRR contract: FAIL · acceptance: FAIL · forbidden-diff: <N violations>
metrics: events=N · ...
violations:
- <path 1>
- <path 2>
…
ACTION: review violations + ai rrr again
```

## Anti-patterns
- ❌ Suppressing `forbidden_diff_violations` count — even 0 needs to
  show as the green confirmation.
- ❌ Hiding memory_learn diagnostic when ok=false (operators need to
  know if the central DB ingest skipped — even though R37/R38 fixed
  most cases, the diagnostic stays useful).
- ❌ Multi-paragraph narrative (operator scans on phone).
