---
ritual: gogogo
purpose: "Per-channel rendering templates for `ai gogogo`"
last-updated: 2026-05-10
phase: "R30 Phase 2"
---

# `gogogo` — Per-channel templates

| File | Channel | Use case |
|------|---------|----------|
| `desktop.md` | desktop | Claude Code terminal, Warp |
| `mobile.md`  | mobile  | trinity-tg-bot streaming, phone SSH |
| `README.md`  | (this)  | selection rules + anti-patterns |

## Selection rules (priority)
1. Explicit `--channel=desktop|mobile`.
2. `TRINITY_RENDER_CHANNEL=desktop|mobile`.
3. Heuristic: TG bot context → mobile.
4. Default: **desktop**.

## Streaming note
gogogo emits per-step output as it walks `.state/plan.json`. The
trinity-tg-bot streams these via `gogogo_stream.js` (live message edit
every 2s). The mobile template is optimized for that incremental edit
flow — keep each step line short so the running message doesn't
balloon past Telegram's edit limits.

## Anti-patterns
- ❌ **Hiding NEEDS_HUMAN breach detail.** Always load-bearing —
  operator must see cap + ratio + revise hint.
- ❌ **Suppressing rule_set/mode prefix on desktop.** Reviewers
  cross-reference `policies/verifier-rules.yaml` by rule_set name.
- ❌ **Box-drawing chars on mobile.** Bot's `sanitizeKernelOutput`
  strips them, but the AI's narration must not re-introduce them.

## Cross-references
- `SHIM.md` — vendor-agnostic gogogo definition.
- `lll/templates/README.md` — pattern reference (R30 Phase 1).
