---
ritual: ddd
channel: desktop
purpose: "Render `ai ddd` deploy decision output for a desktop terminal"
last-updated: 2026-05-10
---

# `ddd` — Desktop rendering template

## Channel signals
1. `--channel=desktop`. 2. `TRINITY_RENDER_CHANNEL=desktop`. 3. Default.

## Format rules
- ✅ Full deploy decision panel (target, reason, verifier verdict)
- ✅ Box-drawing OK; ASCII table fine for verifier evidence dict
- ✅ Show `decided_by` stamp verbatim — `human` for local CLI, or
  `human:tg:<user_id>` for HMAC-signed TG ddd (R34 user_id binding)
- ✅ When HMAC verify fails, show the rejected reason explicitly
  (`sig_mismatch`, `ts_skew`, `malformed_ts`, `no_secret`, `bad_envelope`)

## Layout (success)
```
╭──────── ✅ ai ddd ────────╮
│ deploy decision recorded.
│   graph_state: DEPLOYED
│   target: dev | prod
│   reason: <operator reason>
│   verifier: PASS / skipped
╰───────────────────────────╯
👉 next: ai rrr
```

## Layout (HMAC reject — R39 path)
```
╭──── 🔴 ddd.hmac_rejected ────╮
│ reason: sig_mismatch | ts_skew | bad_envelope
│ ts_iso: <envelope ts>
│ envelope_keys: [session, command, args, ts, nonce, user_id, sig]
╰──────────────────────────────╯
exit 79 — graph_state stays VERIFIED.
```

## Anti-patterns
- ❌ **Hiding `decided_by`.** This is the audit-chain truth — operator
  needs to see whether the action was kernel-decided, human-decided
  (local), or HMAC-verified human (TG bot).
- ❌ **Hiding `target`.** dev vs prod matters; the operator confirms
  before re-running.
- ❌ **Compressing the reason field.** Operators audit reasons across
  sessions; preserve the exact text the kernel emitted.
