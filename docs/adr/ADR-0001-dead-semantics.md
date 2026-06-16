# ADR-0001 — DEAD Semantics and Failure-State Entry Policy

> **Status:** Accepted (operator rulings D1-D5 locked 2026-06-16)
> **Tier:** B — Design decision · **Depends on:** Batch 1 / T0.3 (commit `063ff91`)
> **Evidence base:** [`docs/audits/dead-semantics-precheck.md`](../audits/dead-semantics-precheck.md)
> **Principle:** *DONE proves completion. DEAD proves termination. Neither can be self-declared by AI.*

## Accepted definition (operator-locked)

```text
DEAD is a terminal failure state of a session graph.

A session enters DEAD only when it can no longer produce a trusted completion,
or when a human explicitly aborts the session.

DEAD is not a generic task failure.
Recoverable task failures must route to RETRY, NEEDS_HUMAN, amend, or audit paths.

Verifier-driven DEAD must transition the graph, not merely exit the process.
However, verifier DEAD may fire DO→DEAD only when the matched rule declares
dead_is_terminal=true.

Human operator_abort may fire DEAD from non-terminal active states, but must be
explicit, reasoned, and audited.

Policy fatal is deferred until policy/sandbox vocabulary exists. Current policy
deny does not imply DEAD.
```

A DEAD session is distinguished from peer outcomes by **metadata, not new states**:
`decided_by: verifier | human | kernel` · `reason: …` · `source: …` — so the failure
vocabulary does not fragment into multiple states (no `ABANDONED` added now).

## Context

After Batch 1, `DEAD` is a declared terminal state with `terminal_states: [DONE, DEAD]`, a terminal
guard (cannot fire out of DEAD), and DEAD-ready close infrastructure — but **no graph transition
reaches DEAD**. Meanwhile the verifier already emits a `DEAD` verdict and gogogo terminates the loop
on it **without firing a graph transition**, leaving a DEAD session stranded in `DO`
(the *orphaned-DEAD* gap — see precheck §3). This ADR decides the entry semantics for DEAD before
any `to: DEAD` transition is implemented.

---

## 1. DEAD is defined

**Recommended:** DEAD = **terminal session failure** — the session can no longer produce a
trustworthy completion. (The state graph is a *session* graph; DONE is terminal success, so DEAD is
terminal failure of the same session.) · *Operator ruling: see Decision Log **D1**.*

## 2. DONE vs DEAD

**Recommended distinction:**
- **DONE** = session reached accepted completion *with required evidence*.
- **DEAD** = session can no longer produce trustworthy completion.

Consequence: DONE may promote memory as *success* evidence; DEAD may promote memory only as
*failure / lesson / debt* evidence. · *Operator ruling: see **D5**.*

## 3. Authorities for DEAD entry

**Recommended rule:** only **human**, **verifier**, or **policy** may send a session to DEAD. The
**kernel may route** the transition but **must not invent** the failure.

| Cause | Authority |
|-------|-----------|
| Operator abort | human |
| Hard verifier failure (`dead_when`) | verifier |
| Policy fatal violation | policy *(deferred — see D4)* |
| Audit integrity failure | verifier / kernel-routed |

*Operator rulings: **D2** (verifier), **D3** (human abort), **D4** (policy).*

## 4. operator_abort semantics

**Recommended:** a human may abort from any non-terminal working state
(`THINK/SANDBOX/DO/VERIFIED`) via an `operator_abort` trigger, `decided_by: human`, landing in DEAD.
operator_abort is an explicit human act, never auto-fired. · *Operator ruling: see **D3**.*

## 5. Verifier DEAD mapping

**Recommended:** a verifier `DEAD` verdict maps to a graph `DO → DEAD` transition
(`trigger: verify_dead`, `decided_by: verifier`) **only when** the rule-set marks the failure as
terminal (`verdict.dead_is_terminal == true` or tier=terminal). This closes the orphaned-DEAD gap:
gogogo must fire the transition instead of bare `Exit(1)`. · *Operator ruling: see **D2**.*

## 6. Policy fatal

**Recommended:** **DEFER.** Today policy vocabulary is `ALLOW/DENY/CONDITIONAL/NEEDS_HUMAN` with no
`fatal` concept (precheck §6). A `policy_fatal → DEAD` path requires new policy vocabulary and must
wait for a dedicated Policy/Sandbox audit. Until then: `policy_deny` = stay in current state + audit
`policy.denied`; no policy→DEAD path ships. · *Operator ruling: see **D4**.*

## 7. Close behavior for DEAD

**Recommended:** close treats DEAD as a sealed *failure* archive — DEAD stays DEAD, never re-marked
success; retro from a DEAD session is a failure retro only. (close infra is already DEAD-ready —
precheck §5.) · *Operator ruling: derived from **D1**.*

## 8. Memory promotion from DEAD

**Recommended:** a DEAD session promotes memory **only** as failure / lesson / debt — never as
success evidence. · *Operator ruling: see **D5**.*

---

## Proposed minimal transition set (do NOT implement until this ADR is accepted)

```yaml
# Option A — minimal & safe (gated by D1-D3; excludes policy_fatal which is D4-deferred)
- {from: DO,       to: DEAD, trigger: verify_dead,            decided_by: verifier}
- {from: THINK,    to: DEAD, trigger: operator_abort,         decided_by: human}
- {from: SANDBOX,  to: DEAD, trigger: operator_abort,         decided_by: human}
- {from: DO,       to: DEAD, trigger: operator_abort,         decided_by: human}
- {from: VERIFIED, to: DEAD, trigger: operator_abort,         decided_by: human}
- {from: RETRO,    to: DEAD, trigger: retro_integrity_failed, decided_by: verifier}
```

Implementation tasks after acceptance (later batch): **T0.4.1** add transitions · **T0.4.2** wire
verifier DEAD → graph transition (fix the orphan) · **T0.4.3** close-DEAD behavior tests.

---

## Decision Log (operator-owned — ruled 2026-06-16)

| ID | Question | Decision (operator-ruled) | Status |
|----|----------|---------------------------|--------|
| D1 | DEAD = terminal session failure? | **Terminal session failure** — not a generic task fail; recoverable failures route to RETRY/NEEDS_HUMAN/amend/audit | Ruled (human) |
| D2 | Verifier verdict DEAD → graph DEAD? | **Yes, gated by `dead_is_terminal`** — gogogo must fire DO→DEAD (not bare `Exit(1)`) only when the matched rule declares it terminal; else stay/retry/needs_human | Ruled (human) |
| D3 | Human `operator_abort` → DEAD from non-terminal states? | **Yes, human-only explicit** — from THINK/SANDBOX/DO/VERIFIED, `decided_by: human`, reason required, audited; no new `ABANDONED` state | Ruled (human) |
| D4 | Policy `fatal` → DEAD? | **EXPLICITLY DEFERRED BY HUMAN** — no `policy_fatal` vocabulary exists yet; `policy_deny` stays + audits, never implies DEAD; revisit after policy/sandbox audit | Ruled (human, deferred) |
| D5 | Memory promotion from DEAD = failure/lesson only? | **Yes — failure/lesson/debt only, never success** | Ruled (human) |
