# DEAD Semantics — Pre-Implementation Audit (read-only)

> **Produced by:** ADR-0001 session `0001_2026-06-16_19_24_pm_feat-adr-dead-semantics-and-failure-state-ent`
> **Scope:** read-only evidence gathering for ADR-0001. No code changed.
> **Baseline:** commit `063ff91` (Batch 1 shipped: DEAD declared in states, terminal guard, validator).
> **Headline finding:** **DEAD is an orphaned verdict** — the verifier emits `DEAD` and gogogo
> terminates on it, but **no graph transition reaches the DEAD state**, so a DEAD session is
> left stranded in a non-terminal state.

---

## §6 checklist results

### 1. `grep 'to: DEAD'` across all graph YAML
```
$ grep -rn 'to: DEAD' .ai/graphs/
(no matches)
```
`.ai/graphs/standard.yaml` declares `DEAD` in `states` and `terminal_states: [DONE, DEAD]`
(post-T0.3), but **no transition has `to: DEAD`**. DEAD is declared-but-unreachable.

### 2. Verifier verdict DEAD — does it exist, who produces it
- `.ai/cli/core/verifier.py:68` — `VALID_VERDICTS = {"PASS","RETRY","NEEDS_HUMAN","DEAD"}`
- `.ai/cli/core/verifier.py:427-435` — a rule-set `dead_when` predicate match returns
  `VerifierVerdict(verdict="DEAD", reason="dead_when matched: …", tier=…)`.
- `.ai/cli/core/verifier_runtime.py:15,132` — closed precedence **`DEAD > NEEDS_HUMAN > RETRY > PASS`**.
**→ DEAD is a first-class, already-implemented verifier verdict. Rule-sets can already declare `dead_when`.**

### 3. gogogo hard-fail behavior (the orphan)
- `.ai/cli/commands/gogogo.py:968` — comment: *"D11 — a clear evidence failure is DEAD, NOT NEEDS_HUMAN."*
- `.ai/cli/commands/gogogo.py:1052-1056`:
  ```python
  if verdict.verdict == "DEAD":
      console.print(f"[red]Step {n} DEAD — terminating loop.[/red]")
      raise typer.Exit(1)
  ```
**→ gogogo consumes DEAD by terminating the process. It does NOT call `loop.fire(...)`, so the
session `graph_state` is never advanced to DEAD — it stays at `DO`.** This is the core gap the
ADR must resolve (see ADR D2 / §8 T0.4.2).

### 4. rrr behavior when current state is DEAD
- The standard graph reaches RETRO via `VERIFIED→RETRO` / `DEPLOYED→RETRO`. There is **no
  `DEAD→RETRO`** transition.
- Post-Batch-1, `Loop.fire()` raises `TerminalStateLocked` for any trigger fired from a terminal
  state (`loop.py`, T0.2). So firing `rrr` from `DEAD` would be **blocked** — which is correct:
  you do not retro *out of* DEAD, you close it.
**→ rrr is not a DEAD exit path; DEAD is closed directly. No change needed for rrr.**

### 5. close behavior when current state is DEAD
- `.ai/cli/core/terminal_states.py:28` — `_REQUIRED_CLOSE_TERMINALS = frozenset({"DONE","DEAD"})`;
  the close terminal set is derived from the graph and **requires DEAD**.
- `.ai/cli/commands/close.py:314,499` — comments confirm *"DEAD stays DEAD"*: close seals/archives
  a DEAD session as-is and never re-marks it as success.
**→ close infrastructure is already DEAD-ready. The only missing piece is a path that *enters* DEAD.**

### 6. policy deny / fatal distinction
- `.ai/cli/core/policy_contract.py:35,44` — policy verdict vocabulary today is
  **`ALLOW / DENY / CONDITIONAL / NEEDS_HUMAN`** with precedence `deny > NEEDS_HUMAN > conditional > allow`.
- There is **no `fatal` concept** and no policy→DEAD path.
**→ ADR D4 (policy_fatal → DEAD) would require NEW policy vocabulary. Confirms the canvas
recommendation to DEFER D4 until a dedicated Policy/Sandbox audit.**

### 7. audit events emitted on verifier DEAD
- gogogo appends a `verifier.verdict` / step-verdict audit event (with `verifier_verdict: "DEAD"`,
  `tier`, `decided_by: "verifier"`) **before** the `Exit(1)` — so the DEAD *verdict* is audited.
- But because no `graph.transition` to DEAD is fired, **there is no `graph.transition` audit event
  recording the session entering DEAD.** The audit shows "a step went DEAD" but not "the session
  is DEAD."

---

## Synthesis for the ADR

| Component | State today | Implication for ADR |
|-----------|-------------|---------------------|
| `DEAD` in graph states | ✅ declared (T0.3) | ready |
| `terminal_states: [DONE, DEAD]` | ✅ | ready |
| terminal guard | ✅ (T0.2) DEAD can't fire out | ready — DEAD is a true sink |
| verifier `DEAD` verdict | ✅ implemented + precedence | ready (D2 maps it) |
| gogogo on DEAD | ⚠️ exits, **no graph transition** | **the gap** (D2 / T0.4.2) |
| `to: DEAD` transitions | ❌ none | ADR must specify the minimal set (D1-D3) |
| close on DEAD | ✅ seals as failure | ready (informs D5 close behavior) |
| policy `fatal` | ❌ no such concept | **defer D4** until policy audit |

**Bottom line:** every piece needed to *hold* a DEAD session already exists; the only missing
piece is the *entry path*. The ADR's job is to decide which entries are allowed (D1-D5) — not to
build new terminal infrastructure.
