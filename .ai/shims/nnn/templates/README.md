---
ritual: nnn
purpose: "Per-channel rendering templates for `ai nnn`"
last-updated: 2026-05-10
phase: "R30 Phase 2"
---

# `nnn` — Per-channel templates

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
- ❌ **Hiding spec_ref / step risk on mobile.** Operators on phone need
  to know whether to commit to gogogo before pulling out the laptop.
- ❌ **NEEDS_HUMAN with no actionable hint.** Always include the cap
  name and the revise instruction.
- ❌ **Box-drawing on mobile.** Use plain text.
- ❌ **Truncating step titles below ~50 chars.** Step titles ARE the
  operator's mental index of the plan.

## Cross-references
- `SHIM.md` — vendor-agnostic nnn definition (budget gates, scope/acceptance).
- `lll/templates/README.md` — pattern reference (R30 Phase 1).
