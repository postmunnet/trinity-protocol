---
ritual: rrr
purpose: "Per-channel rendering templates for `ai rrr`"
last-updated: 2026-05-10
phase: "R30 Phase 2"
---

# `rrr` — Per-channel templates

| File | Channel | Use case |
|------|---------|----------|
| `desktop.md` | desktop | Claude Code terminal, Warp |
| `mobile.md`  | mobile  | trinity-tg-bot, phone SSH |
| `README.md`  | (this)  | selection rules + anti-patterns |

## Selection rules (priority)
1. Explicit `--channel=desktop|mobile`.
2. `TRINITY_RENDER_CHANNEL=desktop|mobile`.
3. Heuristic: TG bot context → mobile.
4. Default: **desktop**.

## Anti-patterns
- ❌ **Hiding forbidden_diff_violations.** Even 0 is a load-bearing
  green confirmation; the operator wants to see it.
- ❌ **Truncating retro file paths on desktop.** The two retro files
  (`THINK/RETRO.md` + `.ai/memory/retros/<seq>_*.md`) are the canonical
  artifacts of the session.
- ❌ **Suppressing memory_learn diagnostic.** R37 closed the SIGABRT/-6
  issue, but operators still want to see the outcome stamped — especially
  if a regression sneaks back in.
- ❌ **Box-drawing on mobile.**

## Cross-references
- `SHIM.md` — vendor-agnostic rrr definition.
- `lll/templates/README.md` — pattern reference (R30 Phase 1).
- `feedback_native_destructor_exit.md` memory — why memory_learn outcome
  is worth surfacing.
