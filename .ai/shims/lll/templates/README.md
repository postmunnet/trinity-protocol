---
ritual: lll
purpose: "Per-channel rendering templates index for `ai lll`"
last-updated: 2026-05-10
phase: "R30 Phase 1 (lll only) + R33 (CLAUDE.md adapter wire)"
---

# `lll` — Per-channel templates

This directory holds rendering templates that adapter-side AI agents
read **before** rendering `ai lll` output back to the operator. The
kernel CLI emits its own panel-style output via `rich`; these templates
guide the AI when summarizing, paraphrasing, streaming, or
re-formatting that output for a specific channel.

| File | Channel | Use case |
|------|---------|----------|
| `desktop.md` | desktop | Claude Code in terminal, Warp, plain shell |
| `mobile.md`  | mobile  | trinity-tg-bot reply, phone SSH, narrow term |
| `README.md`  | (this)  | selection rules + anti-patterns |

## Selection rules (priority order)

1. Adapter passes explicit `--channel=desktop|mobile`.
2. Env var `TRINITY_RENDER_CHANNEL=desktop|mobile`.
3. Heuristic: bot context (TG, Slack, etc.) → mobile.
4. Default fallback: **desktop**.

The adapter (the AI's surface — Claude Code, Cursor, AGENTS.md, GEMINI,
Warp, tg-bot) is responsible for picking the channel and reading the
matching template before producing user-facing output.

## Anti-patterns

- ❌ **Mixing styles.** Don't render a partial mobile layout in desktop
  channel "to be safe". Pick one template and follow it.
- ❌ **Box-drawing on mobile.** Never. The bot's `sanitizeKernelOutput`
  strips them, but if the AI re-emits box-drawing chars in its narration
  the bot's strip pass may miss them and the operator sees garbage.
- ❌ **Truncating audit rows on desktop.** Operators want full
  timestamps + decided_by + full session_id; truncation defeats the
  factual-snapshot purpose.
- ❌ **Mixing emoji prefixes with table headers.** The two layouts are
  mutually exclusive.

## Phase 2 (deferred)

Templates for the other 4 rituals (`vvv`, `nnn`, `gogogo`, `rrr`)
follow the same `<ritual>/templates/{desktop,mobile}.md` layout.
Tracked as `R30 Phase 2` in `TRINITY_LEGACY/TODO.md`.

## Cross-references

- `SHIM.md` — canonical vendor-agnostic definition of `lll`.
- `docs/architecture/01_AI_HARNESS_RATIO.md` — design rationale (move
  formatting work from AI to template; 1.6%/98.4% AI/engineering ratio).
- `CLAUDE.md` adapter — operator-facing entry point that instructs the
  AI to read these templates (R33 wire).
