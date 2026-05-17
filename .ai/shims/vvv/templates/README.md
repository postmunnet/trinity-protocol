---
ritual: vvv
purpose: "Per-channel rendering templates for `ai vvv`"
last-updated: 2026-05-10
phase: "R30 Phase 2"
---

# `vvv` — Per-channel templates

| File | Channel | Use case |
|------|---------|----------|
| `desktop.md` | desktop | Claude Code terminal, Warp |
| `mobile.md`  | mobile  | trinity-tg-bot, phone SSH |
| `README.md`  | (this)  | selection rules + anti-patterns |

## Selection rules (priority)
1. `--channel=desktop|mobile` explicit.
2. `TRINITY_RENDER_CHANNEL=desktop|mobile`.
3. Heuristic: TG bot context → mobile.
4. Default: **desktop**.

## Anti-patterns
- ❌ **Paraphrasing operator answers.** Q1 (Goal), Q2 (Scope IN/OUT),
  Q3 (Constraint) are load-bearing for the next ritual — `ai nnn`
  reads `THINK/01_PROMPT.md` and the wording matters.
- ❌ **Reordering Q1..Q5.** The 5-question flow is a fixed contract
  per `docs/specs/06_PIPELINE_SPEC.md`.
- ❌ **Hiding the marker path.** Operator may need to edit
  `THINK/01_PROMPT.md` before submitting `ai nnn`.
- ❌ **Box-drawing on mobile.** Use plain text.

## Cross-references
- `SHIM.md` — vendor-agnostic vvv definition.
- `lll/templates/README.md` — pattern reference (R30 Phase 1).
