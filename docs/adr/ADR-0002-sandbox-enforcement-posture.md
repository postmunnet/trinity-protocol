# ADR-0002 — Sandbox Enforcement Posture & Threat Model

> **Status:** Accepted (operator-locked 2026-06-17)
> **Tier:** B — Design decision · **Closes:** T4-AUDIT (items 3 + 4)
> **Evidence base:** [`docs/audits/policy-sandbox-classification.md`](../audits/policy-sandbox-classification.md)
> **Principle:** Defend the actual threat, not an imagined one — and record the
> gap between declared and enforced rather than hiding it.

## Context

The T4 classification audit found the policy + sandbox layer **largely
implemented and genuinely enforcing**, with a few axes that are *declared in a
profile but not actually enforced* (degraded fail-safe + audited). Two remain
after the cleanup batches (items 1/2/5):

- **Item 3 — `net.outbound: allowlist`** is not enforced. macOS `sandbox-exec`
  has no hostname rules (IP-only, no DNS), so an allowlist degrades to full
  `(deny network*)` and emits `sandbox.allowlist_unenforced`. Fail-safe (deny is
  stricter than the operator's intent) but "allow host X" silently becomes
  "allow nothing."
- **Item 4 — `proc.allowed_binaries` allow-side + `fs` reads.** The proc
  *deny-side* (`forbidden_binaries`, `spawn_allowed=False`), fs *writes*, and
  forbidden-path globs are OS-enforced; the proc *allow-list* is POC-skipped
  (comment-only) and fs *reads* are intentionally unrestricted.

The audit deemed both defer-worthy. This ADR locks **why** and **when to
revisit**, so the deferral is an explicit, reasoned posture rather than an
implicit gap.

## Decision — threat model (D1)

**Trinity's sandboxed tools are first-party and trusted.** They are the
vetted sibling tools in this monorepo, run by the operator. The sandbox's job
is therefore a **guardrail** — prevent *accidents* (a tool writing outside its
roots, clobbering a forbidden path, an unbounded fork-bomb, unintended network
chatter) — **not adversarial isolation** against a hostile tool deliberately
trying to escape.

Rationale: the accident/guardrail threat is already covered end-to-end —
- the **policy gate** blocks forbidden tools / mutation paths and pauses on
  human-gate triggers before any tool runs;
- the **sandbox tool-gate** blocks non-allowlisted tools;
- the **OS `sandbox-exec` hook** enforces fs-write + forbidden-path + net-deny
  (default) + proc-deny at exec, and **fails closed** when a profile declares
  those axes and sandbox-exec is unavailable;
- the **hash-chained audit** records every decision, including the
  declared-vs-enforced gap (`sandbox.allowlist_unenforced`).

Building adversarial-grade isolation (real per-host egress control, positive
binary allow-lists, read confinement) would add significant infrastructure and
platform-specific machinery for a threat (malicious first-party tool) that is
out of scope today.

## Decision — net.outbound allowlist (D2): DEFER

Keep the current fail-safe behaviour: a declared `allowlist` degrades to deny +
`sandbox.allowlist_unenforced` audit. Do **not** build per-host egress now.

**Revisit triggers** — implement real egress control (preferred approach: a
DNS-resolving egress proxy; IP-snapshot rules and pf/iptables are fragile or
root-heavy alternatives) when **either**:
1. a sandboxed first-party tool legitimately needs outbound access to *specific*
   hosts (not all-or-nothing), or
2. the threat model shifts to running **untrusted / third-party** tools.

## Decision — proc allow-list + fs reads (D3): DEFER

Keep deny-side proc + fs-write + forbidden-path enforced; leave the proc
allow-list and fs-read confinement as POC-open.

**Revisit trigger:** the threat model shifts to **adversarial tools** — then add
positive `proc.allowed_binaries` emission and fs-read root confinement (the
sandbox_runtime `.sb` generator is the natural home).

## Non-goals (now)

- No DNS-proxy / pf / iptables egress control.
- No Linux seccomp backend (already noted deferred in `sandbox_runtime.py`).
- No positive proc allow-list emission; no fs-read confinement.
- No change to the policy/sandbox code or schemas — this is a posture decision.

## Consequences

- T4-AUDIT is **closed**: the declared-only axes are an **accepted posture for
  the first-party threat model**, not bugs, and now carry a documented revisit
  contract.
- Operators reading a profile's `net.outbound: allowlist` should understand it
  currently means "deny" (the `sandbox.allowlist_unenforced` audit event makes
  this visible at runtime); honoring it is gated on D2's triggers.
- If Trinity ever runs untrusted tools, D1 is invalidated and D2 + D3 must be
  reopened before that deployment.
