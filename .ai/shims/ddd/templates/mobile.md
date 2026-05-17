---
ritual: ddd
channel: mobile
purpose: "Render `ai ddd` deploy decision for a narrow / mobile screen"
last-updated: 2026-05-10
---

# `ddd` — Mobile rendering template

## Channel signals
1. `--channel=mobile`. 2. `TRINITY_RENDER_CHANNEL=mobile`. 3. TG bot context.

## Format rules
- ❌ **NO box-drawing characters**
- ❌ **NO ASCII tables**
- ✅ One fact per line: target, reason, decided_by, verifier verdict
- ✅ Truncate reason to 100 chars (operator typed it; they know the rest)
- ✅ HMAC reject path: ALWAYS show `reason` field verbatim — the
  operator must see whether it was sig_mismatch (key drift) vs ts_skew
  (clock issue) vs bad_envelope (mangled file)
- ✅ Hard cap 4000 chars (Telegram)

## Layout (success)
```
✅ ddd · target: dev | prod · graph: DEPLOYED
decided_by: human:tg:<user_id> | human
reason: <100-char summary>
verifier: PASS | skipped
next: ai rrr
```

## Layout (HMAC reject — R39 path)
```
🔴 ddd.hmac_rejected
reason: sig_mismatch | ts_skew | bad_envelope
ts_iso: <envelope ts>
exit 79 — graph stays VERIFIED
```

## Anti-patterns
- ❌ **Dropping `decided_by` on mobile.** Operator working remotely
  REALLY needs to confirm the right HMAC user_id stamped (was it from
  their TG account, or someone else's?).
- ❌ **Hiding HMAC reject reason.** Always load-bearing — operator
  needs to know whether to fix bot config (sig drift), retry (clock
  skew), or check envelope file (bad envelope).
- ❌ **Box-drawing chars.** TG bot strips them but the AI's narration
  must not re-introduce them.
