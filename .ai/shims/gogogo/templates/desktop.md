---
ritual: gogogo
channel: desktop
purpose: "Render `ai gogogo` step-walk verdicts for a desktop terminal"
last-updated: 2026-05-10
---

# `gogogo` — Desktop rendering template

## Channel signals
1. `--channel=desktop`. 2. `TRINITY_RENDER_CHANNEL=desktop`. 3. Default.

## Format rules
- ✅ Per-step verdict line: `step N [rule_set/mode] -> VERDICT (reason)`
- ✅ Box-drawing OK in summary panel
- ✅ Show iteration count + budget summary at end
- ✅ NEEDS_HUMAN escalation: full breach detail panel
- ✅ Streaming OK — emit each step verdict as it arrives, then summary

## Layout (success)
```
  step 1 [step_complete/production_phase4] -> PASS (all pass_when predicates satisfied)
  step 2 [step_complete/production_phase4] -> PASS (all pass_when predicates satisfied)
  ...

╭────── ✅ gogogo ──────╮
│ gogogo complete.
│   steps: N
│   graph_state: VERIFIED
╰───────────────────────╯
🟡 next (human): ai ddd --target=dev --reason='...'
```

## Layout (NEEDS_HUMAN budget breach mid-run)
```
  step N [...] -> RETRY/NEEDS_HUMAN (...)
╭────── 🟡 gogogo — NEEDS_HUMAN ──────╮
│ NEEDS_HUMAN — budget breach at step N.
│   breaches: [{cap, limit, estimate, ratio}, ...]
╰─────────────────────────────────────╯
```

## Anti-patterns
- ❌ Hiding step verdict reason on desktop — operators want the why.
- ❌ Suppressing rule_set/mode prefix; reviewers cross-reference verifier-rules.yaml.
