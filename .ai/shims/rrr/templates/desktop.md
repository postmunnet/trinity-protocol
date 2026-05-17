---
ritual: rrr
channel: desktop
purpose: "Render `ai rrr` retro / metrics output for a desktop terminal"
last-updated: 2026-05-10
---

# `rrr` — Desktop rendering template

## Channel signals
1. `--channel=desktop`. 2. `TRINITY_RENDER_CHANNEL=desktop`. 3. Default.

## Format rules
- ✅ Full session metrics table (event_count, transition_count, iterations,
  gogogo_verdicts, needs_human_count, final_graph_state, duration_min)
- ✅ Acceptance gate result (PASS / FAIL / SKIPPED) + count details
- ✅ Forbidden-diff verdict + violation list (or `✅ none`)
- ✅ memory-cli learn outcome (ok/skipped) + reason
- ✅ Both retro file paths (THINK/RETRO.md + .ai/memory/retros/<seq>_*.md)
- ✅ Box-drawing OK
- ✅ RRR contract: PASS / Acceptance evidence: PASS panel at end

## Layout
```
No THINK/03_ACCEPTANCE.yaml — acceptance gate SKIPPED (R11 not yet authored).
forbidden-path diff: ✅ none (baseline: HEAD)

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ session_id        ┃ <full session id>                                        ┃
┃ event_count       ┃ N                                                        ┃
┃ transition_count  ┃ M                                                        ┃
┃ iterations        ┃ K                                                        ┃
┃ gogogo_verdicts   ┃ {"PASS": K}                                              ┃
┃ needs_human_count ┃ 0                                                        ┃
┃ final_graph_state ┃ DEPLOYED / DONE                                          ┃
┃ duration_min      ┃ X.X                                                      ┃
└───────────────────┴──────────────────────────────────────────────────────────┘

wrote
  .ai/sessions/<id>/THINK/RETRO.md
  .ai/memory/retros/<seq>_<date>_<slug>.md
memory-cli learn: <ok / skipped reason>

╭───── 🏁 ai rrr ─────╮
│ rrr complete
│   graph_state: DONE
│   RRR contract: PASS
│   Acceptance evidence: PASS
╰─────────────────────╯
🏁 done: ai close
```

## Anti-patterns
- ❌ Hiding `forbidden_diff_violations` even when 0 (operator wants the
  green-check confirmation).
- ❌ Truncating retro file paths — they're the canonical artifacts.
- ❌ Hiding memory_learn outcome — false-negative -6 was a known issue,
  operators may need the diagnostic.
