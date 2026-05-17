---
ritual: ddd
purpose: "Per-channel rendering templates for `ai ddd` (deploy decision gate)"
last-updated: 2026-05-10
phase: "R30 Phase 3 — closes R30 in full across all 6 short-code rituals"
---

# `ddd` — Per-channel templates

| File | Channel | Use case |
|------|---------|----------|
| `desktop.md` | desktop | Claude Code terminal, Warp |
| `mobile.md`  | mobile  | trinity-tg-bot, phone SSH |
| `README.md`  | (this)  | selection rules + anti-patterns |

## Selection rules (priority)
1. Explicit `--channel=desktop|mobile`.
2. `TRINITY_RENDER_CHANNEL=desktop|mobile`.
3. Heuristic: TG bot context (`/ddd target=...`) → mobile.
4. Default: **desktop**.

## ddd-specific anti-patterns
- ❌ **Hiding `decided_by`.** Trinity's audit-chain identity model
  hinges on this: `human` = local CLI; `human:tg:<user_id>` = HMAC-
  verified TG bot. Operators audit by tracing this stamp.
- ❌ **Hiding HMAC reject reason.** R39 wired bot end-to-end with HMAC
  envelopes. When verify fails, the reason (`sig_mismatch`, `ts_skew`,
  `malformed_ts`, `no_secret`, `bad_envelope`) tells the operator
  exactly which lever to pull.
- ❌ **Hiding `target=dev|prod`.** Especially on mobile — operator must
  confirm the destination before re-running. Never abbreviate to
  just "deployed".
- ❌ **Compressing the reason field.** Operators audit reason text
  across sessions for retro patterns; preserve verbatim.
- ❌ **Box-drawing on mobile.**

## Cross-references
- `commands/ddd.py` — kernel implementation; reads `--hmac-envelope-file`
  and emits `ddd.completed` / `ddd.hmac_rejected` audit events.
- `core/auth.py::verify_hmac` — backing verifier (Decision Y).
- R34 / R35 / R39 in TRINITY_LEGACY/TODO.md — the HMAC wire-up history.
- `lll/templates/README.md` — pattern reference (R30 Phase 1).
