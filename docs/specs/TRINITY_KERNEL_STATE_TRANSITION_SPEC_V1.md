---
title: "Trinity Kernel State Transition Spec v1.0"
version: "1.0"
status: "draft"
phase: "4"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes:
  - "(none -- first canonical version)"
constitutional-anchor: ["Article III", "Article IV", "Article XVI", "Article XX", "Article XXIX"]
amendment-policy: "Article XXIX -- explicit proposal + rationale + impact analysis + human approval + version bump + audit entry."
---

# TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1

> **Constitutional rank:** 4 -- Kernel State Rules (Article XXV).
> **Phase:** 4 -- Kernel State Machine Formalization.
> **Sibling specs:** TRINITY_AUDIT_EVENT_SPEC_V1 (audit shape), TRINITY_DDD_HUMAN_GATE_SPEC_V1 (ddd shape), TRINITY_SESSION_CLOSE_SPEC_V1 (close shape), TRINITY_VERIFIER_CONTRACT_V1 (verifier surface).
> **Authoritative graph file (referenced, not authored here):** `.ai/graphs/standard.yaml`.

This spec normatively pins the Trinity kernel state machine -- the set of legal session lifecycle states, the legal transitions between them, who is allowed to *decide* each transition, what pre-conditions and post-conditions must hold, and what the kernel must emit on the audit chain when a transition fires. It is the layer between Constitution v1.0 (governance principles) and the implementation file `.ai/graphs/standard.yaml` (declarative graph). It does not author the YAML; it constrains its shape and semantics.

The single normative invariant is:

```text
Every kernel state mutation MUST be:
  - explicitly invoked        (Article XX -- Passive Core)
  - declared in the graph     (Article XII -- Illegal Transitions)
  - decided by the right authority (Article III, IV)
  - audit-logged              (Article X)
  - artifact-referenced       (Article II)
```

If a proposed transition fails any one of those, the kernel MUST refuse it and MUST emit an audit event recording the refusal.

---

## Section 1 -- Purpose & Constitutional Anchor

### 1.1 Purpose (normative-description)

This spec exists because, prior to Phase 4, the Trinity ritual sequence (`sss -> vvv -> nnn -> gogogo -> ddd -> rrr -> close`) was enforceable only by convention. Agents could narrate state changes without a backing transition; the kernel could not refuse an out-of-order ritual without bespoke per-command logic; and the audit chain carried no uniform record of *why* a state changed.

This spec closes those gaps by:

1. Enumerating the canonical state vocabulary (Section 2).
2. Pinning the legal transition catalog (Section 3) -- one row per legal `(from, trigger) -> to` move.
3. Pinning the pre-condition guards each transition must satisfy (Section 4).
4. Pinning the rejection semantics for illegal transitions (Section 5).
5. Pinning the `decided_by` attribution rules (Section 6).
6. Pinning the audit-event emission contract per transition (Section 7).
7. Pinning the Article XX passive-core invariant for state machine code (Section 8).
8. Pinning the Article XXIX amendment protocol for adding states or transitions without breaking existing chains (Section 9).
9. Cross-referencing the glossary so future agents resolve terms canonically (Section 10).

### 1.2 Why the kernel state machine MUST be enforceable AND passive (normative-description)

The constitutional anchor is the conjunction of Articles III, IV, XX, XVI, and XXIX. These five clauses are *both* the warrant for the spec and the constraint on how the spec is implemented.

**Anchor coverage note (per NP-4-1):** all five anchor articles listed in the frontmatter (Article III, Article IV, Article XVI, Article XX, Article XXIX) are quoted verbatim in this section below. Article XXIX in particular is quoted in full at the end of Section 1.2; readers seeking the amendment-protocol obligation that derives from it should also consult Section 9 (this spec's own amendment procedure) which operationalises the Article XXIX clauses.

#### Article III -- AI Cannot Govern Itself (verbatim quote)

```text
AI may:

- think
- reason
- propose
- execute through authorized tools

AI MUST NOT:

- declare final completion
- approve its own work
- verify its own correctness
- bypass verifier approval
- bypass governance gates
- forge authority
- redefine workflow state
- rewrite constitutional policy

Final completion requires:

artifact + verification + governance approval + audit
```

Article III is what forbids any agent (Claude, Codex, Gemini, an in-house executor agent, a transport bot) from *unilaterally* recording a state mutation. The kernel state machine is the structural enforcement of Article III: an agent may *propose* a transition (e.g. by invoking `ai gogogo`), but the kernel itself decides whether the transition is legal, whether the right authority is asserting it, and whether the audit event is well-formed.

#### Article IV -- Separation of Responsibilities (verbatim quote)

```text
Trinity MUST enforce strict role separation.

Canonical roles:

Kernel    = governance, state, gates, authority
Planner   = reasoning, plans, risk analysis
Executor  = bounded action, mutation, execution artifacts
Verifier  = independent validation
Memory    = evidence retrieval
Audit     = immutable history
Retro     = post-work reflection
Transport = message delivery only

No component may silently absorb another component's role.

Role collapse is a constitutional violation.
```

Article IV is what forces the `decided_by` field on every transition. A transition with `decided_by: kernel` MUST be one that follows mechanically from a satisfied predicate; a transition with `decided_by: verifier` MUST be one whose predicate was evaluated by the deterministic verifier; `decided_by: human` MUST be one whose predicate was satisfied by a human-authored artifact (Section 6). The state machine is the structural encoding of the role separation matrix (Ritual Constitution v1.1 Article XVIII).

#### Article XVI -- Least Authority (verbatim quote)

```text
Every component MUST operate with minimum required authority.

Examples:

memory-cli must not own execution authority
verifier must not own production mutation authority
browser-cli must not own deployment authority
transport must not own governance authority

Unknown authority MUST be treated as denied authority.
```

Article XVI is what forces the kernel to refuse any transition whose `decided_by` is unrecognised. The set of valid authorities is closed (Section 6.1); a transition asserting `decided_by: trinity-tg-bot` is denied because Transport is not Authority (Article XV); a transition asserting `decided_by: claude` is denied because models do not vote in the role table.

#### Article XX -- Passive Core Principle (verbatim quote)

```text
Core Trinity systems act only through explicit invocation.

Core systems MUST NOT:

self-trigger
self-expand authority
silently mutate policy
rewrite themselves recursively
generate new goals autonomously

Automation is allowed only when:

bounded
observable
interruptible
auditable
```

Article XX is the load-bearing constraint on *how* the state machine is implemented. The kernel does not poll. The kernel does not background-crawl sessions. The kernel does not auto-promote a session that has been idle past a deadline. Every transition is fired by an explicit caller (a CLI subcommand, a programmatic `Loop.fire(...)` call, an audit-replay tool, or a human-authored artifact write). Section 8 is a deep dive on this invariant and the conformance tests that prove it.

#### Article XXIX -- Constitutional Amendment (verbatim quote)

```text
The Constitution MUST NOT be silently rewritten.

Amendments require:

explicit proposal
rationale
impact analysis
human approval
version bump
audit entry

Prior versions MUST remain inspectable.
```

Article XXIX is what forces this spec to declare its own amendment protocol (Section 9). Adding a new state or a new transition is not an editorial edit -- it is an Operational-tier (or, if it touches an Article, Constitutional-tier) amendment per Addendum v1.0.4 XXIX.2 / XXIX.3. The procedure includes a version bump, a trace-to-failure entry, an audit event, and -- critically -- a back-compatibility plan so that historical audit chains remain replayable against the new graph.

### 1.3 What this spec does NOT do (normative-description)

- It does **not** author `.ai/graphs/standard.yaml`. The YAML file is the implementation artifact; this spec constrains its shape (Section 3, 4, 6) and amendment process (Section 9).
- It does **not** author the validator code. Section 4 includes pseudocode in fenced blocks; an actual implementation lives in `.ai/cli/core/loop.py` (`Loop.fire`, `Loop._validate_graph`, `Loop._build_index`) and is governed by the existing test suite.
- It does **not** author test fixtures. The illegal-transition tests required by PRD Phase 4 acceptance are an implementation concern; this spec pins what they MUST cover (Section 5.4).
- It does **not** override or restate the Ritual Constitution v1.1 state vocabulary. Where the two diverge in practice, Section 2.6 documents the divergence and pins the canonical resolution.

---

## Section 2 -- State Vocabulary

### 2.1 Canonical states (normative-description)

The canonical kernel session lifecycle states are exactly the set declared in `.ai/graphs/standard.yaml` plus the Ritual Constitution v1.1 Article XVII extensions for failure / abort / revival. The following table is normative.

**Count clarification (per N-4-1):** the table below enumerates **17 canonical states**. Earlier draft prose referred to "16 states" by excluding `DEGRADED` from the lifecycle count on the grounds that `DEGRADED` is a non-blocking marker rather than a progression milestone. This spec pins `DEGRADED` as a first-class non-terminal lifecycle state (T19 / T20 / T21 transitions reference it normatively); the canonical count is therefore **17**, of which **5 are terminal** (`{DONE, SEALED, DEAD, ABORTED, TERMINAL_FAILED}` -- see Section 2.3). `DEGRADED` is **not** terminal: a `DEGRADED` session may transition to `NEEDS_HUMAN` (T20) or to `FAILED` (T21).

| State | Definition | Invariants |
|---|---|---|
| `READY` | Session created; no ritual has fired yet. Initial state. | `session_state.json:graph_state` is unset OR equals `READY`. No `vvv_pass`, `nnn_pass`, `verifier_report.*`, DDD artefact, or `RETRO.md` exists. |
| `THINK` | `sss` has fired; the session has a manifest, a goal, an initial scope, an assumed risk tier. Pre-`vvv`. | `session_init.md` and `session_manifest.json` exist. `vvv_pass` does not exist yet. |
| `SANDBOX` | `nnn` has fired; the plan envelope (`PLAN.md` + `verification_contract.json` + `risk_assessment.json` + `rollback.md`) exists; bounded execution may begin. | `nnn_pass` marker exists. `.state/plan.json` exists and validates against `verification_contract.schema.json`. `gogogo` has not yet completed any step. |
| `DO` | `vvv` has fired (or has been waived per workflow tier); per-step `gogogo` execution is in flight. | `vvv_pass` exists OR risk tier permits `vvv` skip per Ritual Constitution Article XIV. At least one step of `gogogo` has started. |
| `VERIFIED` | `gogogo` finished AND verifier returned PASS for all required checks. Pre-DDD. | `verifier_report.json` exists with `status: PASS`; `gogogo.completed` event is on the per-session audit chain. |
| `PROMOTED` | Operator (`decided_by: human`) approved promotion of `DO/dev/` artefacts to `DO/snapshot/` or onward. | `approval.json` exists with `action: promote` AND `decided_by: human`. |
| `DEPLOYED` | Operator (`decided_by: human`) approved deployment to the target environment. | `approval.json` exists with `action: deploy` AND `decided_by: human`; deploy verifier passed. |
| `RETRO` | `rrr` has fired; the `retro_writer` agent is producing `RETRO.md`. | `retro_context.json` exists; `RETRO.md` may be in flight or complete. |
| `DONE` | `rrr` is complete (`rrr.completed` event on chain); session is sealed pending final close. | `RETRO.md` validated against `rrr_check.template.json`; `metrics.json` and `memory_index_result.json` exist. |
| `SEALED` | `close` has fired; final manifest is hashed; session is read-only. | `final_manifest.yaml` (or `final_manifest.json`) exists; `close.completed` event on chain. Terminal. |
| `DEAD` | Terminal failure recorded by verifier or operator; session may not advance. | `terminal.freeze` artefact exists; no further transitions accepted. Terminal. |
| `FAILED` | A ritual check returned a non-recoverable failure but revival is still possible. | At least one `*.failed` event on chain; revival count below `max_revivals`. |
| `ABORTED` | Operator-initiated abort; session is closed without completion. | `decided_by: human` artefact recording the abort exists. Terminal unless explicitly reopened. |
| `REOPENED` | A previously `DONE` session was reopened by operator decision. | `decided_by: human` artefact recording the reopen exists; the prior `DONE` event remains on the chain unmutated. |
| `TERMINAL_FAILED` | Revival exhausted; session is permanently failed. | `max_revivals` count reached; no further `FAILED -> ...` transition allowed. Terminal. |
| `NEEDS_HUMAN` | Verifier or policy escalated; awaiting human decision artefact. | `verifier_report.json:status == NEEDS_HUMAN` OR a policy escalation event exists. |
| `DEGRADED` | A non-blocking ritual check warned but did not block; session proceeds with a degraded marker. | At least one `*.degraded` event on chain. |

### 2.2 Initial state (normative-description)

```text
initial_state = READY
```

A session begins in `READY` immediately upon creation by `ai sss "<task>"` / `ai session new "<task>"`. The kernel MUST refuse to fire any non-`sss` ritual against a session whose recorded `graph_state` is missing or `READY` (Section 4.2).

### 2.3 Terminal states (normative-description)

```text
terminal_states = {DONE, SEALED, DEAD, ABORTED, TERMINAL_FAILED}
```

A terminal state has *no* outgoing transitions in the canonical graph except via the explicit `REOPENED` route (which itself requires `decided_by: human`). The kernel MUST refuse any `Loop.fire(...)` against a session in a terminal state and MUST emit `ritual.transition.blocked` on the audit chain (Section 7.4).

**The DONE -> SEALED exception (per NP-4-2; load-bearing -- read carefully):**

`DONE` appears in the `terminal_states` set above, but it has **exactly one** legal outbound transition: T9 (`DONE -> SEALED` via the `close` trigger). No other trigger may fire from `DONE`. This is a deliberate two-step finalisation pattern, not an inconsistency:

1. `rrr_complete` (T8) lands the session at `DONE` -- the retro is written, metrics indexed, memory updated. Ritual progression is finished.
2. `close` (T9) is a separate, kernel-decided seal step -- it computes the final manifest, re-validates verify dev/prod, and (for COLD tier) emits the external audit. Only `close` may exit `DONE`.

In short: `DONE` is **terminal with respect to all rituals except `close`**. Every other terminal state in the set (`SEALED`, `DEAD`, `ABORTED`, `TERMINAL_FAILED`) is fully terminal -- no outbound transitions whatsoever (the `REOPENED` route via T17 reopens `DONE`, not the strictly-terminal four).

### 2.4 State invariants the kernel MUST enforce (normative-description)

For every state above, the kernel MUST hold the following invariants at all times:

1. **Single-source-of-truth.** The canonical `graph_state` lives in `<session>/.state/session_state.json` under the `graph_state` field. Any consumer (ritual command, verifier, audit replay) reads from this field, never from inferred state.
2. **Audit reconciliation.** On `Loop` initialization, the kernel reconciles the in-file `graph_state` against the most recent `graph.transition` event for that `session_id` on the audit chain. If they differ, the audit chain wins (D9 -- audit is append-only and is the source of truth). See `Loop._reconcile_from_audit` in `.ai/cli/core/loop.py`.
3. **Atomic write.** Mutations to `session_state.json` MUST use `atomic_write_json` (write-temp + fsync + replace). A crash mid-write MUST NOT leave a 0-byte state file (memory `feedback_sqlite_gotchas.md` / state.py:89-100).
4. **Merge-safe write.** A `set_graph_state(...)` call MUST preserve unrelated fields in `session_state.json` (e.g. `created_at`, `subgraph_stack`, `active_graph`). See state.py:225-235.

### 2.5 Sub-graph composition (informational)

The kernel supports sub-graph composition via `subgraph_stack` (state.py:244-287). When a sub-graph is pushed, the active graph name shifts (e.g. `standard -> deploy`); the outer state is preserved on the stack and restored on pop. This spec does NOT enumerate sub-graph transitions individually -- each sub-graph is a separately-versioned YAML under `.ai/graphs/<name>.yaml` and obeys the same shape rules pinned in Sections 3-7. Sub-graph composition is a Phase 6+ extension; the canonical session lifecycle uses only the `standard` graph.

**T6 placement note (per N-4-2):** despite the eventual existence of a `deploy` sub-graph (Phase 6+), the canonical T6 (`PROMOTED -> DEPLOYED` via `deploy_request`) **remains in `.ai/graphs/standard.yaml`** -- it is part of the standard lifecycle, not a sub-graph transition. Future sub-graph YAMLs (e.g. `.ai/graphs/deploy.yaml`, `.ai/graphs/migrate.yaml`) MUST be marked explicitly via the sub-graph naming convention and pushed via `subgraph_stack`; their transition rows MUST NOT shadow or replace any canonical T-row in this spec without going through the Section 9 amendment protocol.

### 2.6 Vocabulary divergence vs Ritual Constitution v1.1 Article XVII (normative-description)

Ritual Constitution v1.1 Article XVII enumerates a broader state vocabulary including `PLAN`, `EXECUTE`, `VERIFY`, `PROMOTE`, `DEPLOY`. The standard graph in `.ai/graphs/standard.yaml` uses the runtime-shorter equivalents `THINK`, `SANDBOX`, `DO`, `VERIFIED`, `PROMOTED`, `DEPLOYED`. The mapping is:

| Ritual Constitution name | Canonical kernel state (this spec + standard.yaml) |
|---|---|
| `READY` | `READY` |
| `THINK` | `THINK` |
| `PLAN` | `SANDBOX` (post-`nnn` is the sandbox-bound planning surface) |
| `SANDBOX` | `SANDBOX` |
| `EXECUTE` | `DO` (per-step executor work) |
| `VERIFY` | (transient -- verifier writes `verifier_report.json`; state remains `DO` until `gogogo.completed` flips to `VERIFIED`) |
| `PROMOTE` | `PROMOTED` |
| `DEPLOY` | `DEPLOYED` |
| `RETRO` | `RETRO` |
| `DONE` | `DONE` |
| `SEALED` | `SEALED` |
| `FAILED` / `DEGRADED` / `ABORTED` / `REOPENED` / `TERMINAL_FAILED` / `NEEDS_HUMAN` | identical |

The canonical names in this spec and in `.ai/graphs/standard.yaml` win at runtime (Article XXV: Kernel State Rules outrank Ritual Constitution where the runtime is concerned). The Ritual Constitution names remain valid in normative ritual prose. Adding a state to either vocabulary requires the Section 9 amendment protocol.

---

## Section 3 -- Transition Catalog

### 3.1 Catalog table (normative-description)

The table below is the closed set of transitions in the canonical `standard` graph. The kernel MUST NOT accept any `Loop.fire(...)` that does not correspond to a row in this table (or, for sub-graphs, a row in the sub-graph YAML). Adding a row is governed by Section 9.

Columns:

- **From** -- the required current `graph_state`. `ANY` means the transition matches from any non-terminal state.
- **Trigger** -- the string passed as the first argument to `Loop.fire(trigger, decided_by, evidence)`. Closed namespace.
- **To** -- the resulting `graph_state`.
- **Decided-by** -- the role authorised to fire this transition. Closed set: `kernel`, `verifier`, `policy`, `human`. See Section 6.
- **Pre-conditions** -- predicates that MUST hold before the kernel accepts the trigger. See Section 4.
- **Post-conditions** -- artefacts that MUST exist on disk after the kernel accepts the trigger. The kernel writes the audit event AFTER post-conditions are confirmed.
- **Audit event** -- the canonical event_type emitted on the per-session AuditWriter chain. See Section 7 and TRINITY_AUDIT_EVENT_SPEC_V1 §3.

| # | From | Trigger | To | Decided-by | Pre-conditions | Post-conditions | Audit event |
|---|---|---|---|---|---|---|---|
| T1 | `READY` | `sss` | `THINK` | `kernel` | A non-empty `<task>` string was supplied to `ai sss`. Session directory created. | `session_init.md`, `session_manifest.json`, baseline_untracked snapshot at `.state/baseline_untracked.json` (per memory `feedback_rrr_cross_session_forbidden_diff`). | `graph.transition` (+ `session.created`) |
| T2 | `THINK` | `nnn_pass` | `SANDBOX` | `kernel` | Explicit disjunct (per Ritual Constitution v1.1 Article XIV): (`vvv_pass` exists) OR (`risk_tier == HOT` AND vvv skipped). `plan_envelope` validated against `verification_contract.schema.json`. Forbidden-action and forbidden-phrase checks (`nnn_check.template.json`) pass. | `PLAN.md`, `verification_contract.json`, `risk_assessment.json`, `rollback.md`, `.state/plan.json`, `nnn_pass` marker. | `graph.transition` (+ `nnn.passed`) |
| T3 | `SANDBOX` | `vvv_pass` | `DO` | `verifier` | `vvv_check.template.json` passes (all required headings, `Clarifying Questions` >= 1, `assumptions.json` valid). No `blocking_unknown_unanswered`. | `VVV.md`, `assumptions.json`, `scope.md`, `vvv_pass` marker. | `graph.transition` (+ `vvv.passed`) |
| T4 | `DO` | `gogogo_complete` | `VERIFIED` | `verifier` | All steps in `.state/plan.json` reached `gogogo.step_completed`. Per-step `verifier_report` exists with `status: PASS`. `forbidden_diff` check (per Article XII -- Illegal Transitions; per `gogogo_check.template.json:on_forbidden_diff: BLOCK`) passes. Diff paths within `allowed_paths`. Acceptance grep checks pass exact-character (memory `feedback_acceptance_grep_char_mismatch`). | `EXECUTION_REPORT.md`, `diff.patch`, `execution.log`, `artifact_manifest.json`. | `graph.transition` (+ `gogogo.completed`) |
| T5 | `VERIFIED` | `promote_request` | `PROMOTED` | `human` | `decision_packet.json` emitted by kernel; `presentation` object conforms to TRINITY_DDD_HUMAN_GATE_SPEC_V1 §3.1. Operator wrote `approval.json` with `action: promote`, `decided_by: human`, signature (HMAC) where transport-mediated. `verify dev` passed (memory `feedback_close_requires_verify_dev_and_prod`). | `approval.json`, snapshot of `DO/dev/` -> `DO/snapshot/`. | `graph.transition` (+ `ddd.approved`) |
| T6 | `PROMOTED` | `deploy_request` | `DEPLOYED` | `human` | Operator wrote `approval.json` with `action: deploy`, `decided_by: human`. Deploy verifier passed (`verify prod`). Critical-gate sandbox check passed (TRINITY_SANDBOX_CAPABILITY_SPEC_V1). | Deploy artefacts under `DO/prod/`; `verify_prod.json` with `passed: true`. | `graph.transition` (+ `ddd.approved` for deploy) |
| T7 | `DEPLOYED` | `rrr` | `RETRO` | `kernel` | Operator (or kernel-on-DEPLOYED) invoked `ai rrr`. `retro_context.json` synthesised. **Canonicality (per N-4-4 / Ritual Constitution v1.1 Article XIV):** T7 is the canonical rrr path for **COLD** tier (full ddd -> promote -> deploy chain executed; rrr fires AFTER `DEPLOYED`). | `retro_context.json`. | `graph.transition` (+ `rrr.proposed`) |
| T7b | `VERIFIED` | `rrr` | `RETRO` | `kernel` | (HOT/WARM path -- session reaches retro without a DEPLOYED step.) Same as T7. **Canonicality (per N-4-4 / Ritual Constitution v1.1 Article XIV):** T7b is the canonical rrr path for **HOT** tier (vvv/ddd waived) and for **WARM** tier sessions whose plan envelope did not request promotion/deploy; rrr fires directly AFTER `VERIFIED`. T7 vs T7b is selected by tier, not by operator preference -- mixing them within a single session is a guard-failed refusal. | `retro_context.json`. | `graph.transition` (+ `rrr.proposed`) |
| T8 | `RETRO` | `rrr_complete` | `DONE` | `kernel` | `RETRO.md` validates against `rrr_check.template.json` (all required headings present, evidence refs valid, `memory_handling.mode == index`, no forbidden phrases). `metrics.json` and `memory_index_result.json` exist. Acceptance source-of-truth `THINK/03_ACCEPTANCE.yaml` re-checked (memory `feedback_rrr_acceptance_yaml_source`). | `RETRO.md`, `metrics.json`, `memory_index_result.json`. | `graph.transition` (+ `rrr.completed`) |
| T9 | `DONE` | `close` | `SEALED` | `kernel` | `verify dev` AND `verify prod` both passed (memory `feedback_close_requires_verify_dev_and_prod`). Final manifest computed per TRINITY_SESSION_CLOSE_SPEC_V1 Section 2; CAPTURE chain consistent. For COLD tier: external audit emitted per TRINITY_SESSION_CLOSE_SPEC_V1 Section 3. **Note (per C-4-3 reconciliation with TRINITY_SESSION_CLOSE_SPEC_V1 Section 2.2):** these pre-conditions are evaluated at *close-invocation* time (the moment the operator fires `ai close`), not at *close-completion* time. Mid-close validation steps (manifest hashing, capture-chain consistency re-check, archive) are part of the T9 transition body itself; their failure raises a guard-failed refusal rather than a separate transition. | `final_manifest.yaml` (or `final_manifest.json`); for COLD: `audit/external/<UTC-date>/<session-id>.audit.json`. | `graph.transition` (+ `close.completed`, `session.closed`) |
| T10 | `ANY` (non-terminal) | `verify_fail_hard` | `DEAD` | `verifier` | Verifier returned `FAIL_HARD` per TRINITY_VERIFIER_CONTRACT_V1. | `terminal.freeze` artefact recording outcome / code / by. | `graph.transition` (+ `verify.completed` with status FAIL_HARD) |
| T11 | `ANY` (non-terminal) | `policy_violation` | `DEAD` | `policy` | A canonical policy in `.ai/policies/**` returned a hard deny against the proposed action (e.g. forbidden-path mutation, secret leak). | `terminal.freeze` recording the policy match. | `graph.transition` (+ `policy.violation.detected`) |
| T12 | `VERIFIED` | `needs_human` | `NEEDS_HUMAN` | `verifier` | Verifier returned `NEEDS_HUMAN` (Ritual Constitution v1.1 §`ddd_check.failure_behavior.on_unverified_high_risk`). | `verifier_report.json:status == NEEDS_HUMAN`. | `graph.transition` (+ `verify.completed` with status NEEDS_HUMAN) |
| T13 | `NEEDS_HUMAN` | `human_resolution` | `PROMOTED` or `FAILED` | `human` | Operator wrote `approval.json` (-> `PROMOTED`) or `rejection.json` (-> `FAILED`). | The corresponding decision artefact. | `graph.transition` (+ `ddd.approved` / `ddd.rejected`) |
| T14 | `FAILED` | `revive` | `SANDBOX` | `human` | Revival count is below `max_revivals` (default 3, Ritual Constitution Article XV.2). Operator authored `decided_by: human` revival artefact. | `revival_log.json` increment. | `graph.transition` (+ `ritual.transition.requested`) |
| T15 | `FAILED` | `terminal_fail` | `TERMINAL_FAILED` | `kernel` | Revival count reached `max_revivals`. | `terminal.freeze`. | `graph.transition` |
| T16 | `FAILED` | `abort` | `ABORTED` | `human` | Operator authored `decided_by: human` abort artefact. | `abort.json`. | `graph.transition` (+ `session.abandoned`) |
| T17 | `DONE` | `reopen` | `REOPENED` | `human` | Operator authored `decided_by: human` reopen artefact. The prior `DONE` event remains on the chain unmutated; the reopen is a new event (Article X -- Audit Discipline). | `reopen.json`. | `graph.transition` |
| T18 | `REOPENED` | `replan` | `SANDBOX` | `kernel` | A fresh `nnn` envelope was prepared for the reopened scope. | `PLAN.md` (new revision), updated `.state/plan.json`. | `graph.transition` (+ `plan.amended`) |
| T19 | `ANY` (non-terminal) | `degrade` | `DEGRADED` | `verifier` | A non-blocking ritual check warned (e.g. `on_optional_failure: WARN`). | `*.degraded` marker. | `graph.transition` (+ `state.changed` payload `from -> DEGRADED`) |
| T20 | `DEGRADED` | `needs_human` | `NEEDS_HUMAN` | `verifier` | Degraded state requires operator review. | (no new artefact required.) | `graph.transition` |
| T21 | `DEGRADED` | `verify_fail_hard` | `FAILED` | `verifier` | Degraded check escalated to a hard failure on retry. | (no new artefact required.) | `graph.transition` |

**Audit-event registry cross-reference (per N-4-3):** the "Audit event" column above lists, alongside the mandatory `graph.transition` event, secondary ritual-namespace events (e.g. `nnn.passed`, `gogogo.completed`, `rrr.completed`, `close.completed`, `policy.violation.detected`, `plan.amended`). Each such secondary event MUST be registered in **TRINITY_AUDIT_EVENT_SPEC_V1 Section 3** (the canonical Phase 10 audit-event registry). Any new secondary event added to a row in this catalog MUST receive a matching Section 3 registry entry in the same amendment commit (Section 9.4 amendment rule); kernel-emitted secondary events absent from Section 3 are a constitutional violation per Article X -- Audit Discipline.

### 3.2 Trigger namespace closure (normative-description)

The trigger namespace above is **closed**. The kernel MUST refuse a `Loop.fire(trigger=...)` whose `trigger` is not in the union of:

- the `trigger` column above, AND
- the per-sub-graph triggers declared in any active sub-graph YAML.

The refusal MUST emit `ritual.transition.blocked` with payload `{reason: "unknown_trigger", trigger, current_state}`. See Section 5.2.

### 3.3 Non-normative example -- a HOT-path transition sequence

```text
sss "fix-typo"
  -> READY -> THINK            (T1, decided_by: kernel)
nnn --plan-envelope hot.json
  -> THINK -> SANDBOX           (T2, decided_by: kernel; vvv waived per HOT)
gogogo
  -> per-step audit; final flip:
  -> SANDBOX or DO -> VERIFIED  (T4, decided_by: verifier)
rrr
  -> VERIFIED -> RETRO          (T7b, decided_by: kernel)
rrr_complete
  -> RETRO -> DONE              (T8, decided_by: kernel)
close
  -> DONE -> SEALED             (T9, decided_by: kernel)
```

Note: HOT path skips `vvv`, `ddd`, the `PROMOTED`/`DEPLOYED` branch entirely. The kernel still requires `nnn_pass` because every non-trivial workflow MUST declare scope (Article VI).

### 3.4 Non-normative example -- a COLD-path transition sequence

```text
sss "deploy-prod-migration"
  -> READY -> THINK             (T1)
vvv
  -> (writes VVV.md; vvv_pass marker fires verifier check)
  -> SANDBOX -> DO              (T3, decided_by: verifier)
nnn --plan-envelope cold.json
  -> THINK -> SANDBOX           (T2)
gogogo (multi-step)
  -> per-step audit
  -> SANDBOX -> VERIFIED        (T4)
ddd --target=dev --reason=...
  -> kernel emits decision_packet.json
  -> operator writes approval.json
  -> VERIFIED -> PROMOTED       (T5, decided_by: human)
ddd --target=prod --reason=...
  -> operator writes approval.json
  -> PROMOTED -> DEPLOYED       (T6, decided_by: human)
rrr
  -> DEPLOYED -> RETRO          (T7)
rrr_complete
  -> RETRO -> DONE              (T8)
close run
  -> verify dev + verify prod re-checked
  -> external audit emitted
  -> DONE -> SEALED             (T9)
```

---

## Section 4 -- Transition Guards

### 4.1 What a guard is (normative-description)

A **transition guard** is a deterministic predicate evaluated by the kernel at the moment a transition is proposed. The guard is the structural enforcement of pre-conditions in Section 3. A transition that satisfies its trigger and `decided_by` but fails its guard MUST be refused; the refusal MUST be auditable; the refusal MUST NOT silently retry.

A guard is **deterministic** -- given the same session state, the same on-disk artefacts, the same audit chain, and the same trigger, the guard MUST return the same boolean. Guards MUST NOT call out to LLMs, MUST NOT depend on wallclock time except for explicit deadline checks (e.g. `decision_packet.expires_ts` comparison), and MUST NOT depend on network state.

### 4.2 Per-transition guard predicates (normative-description)

The list below pairs each transition row from Section 3 with the predicate(s) the guard MUST evaluate. These are reference predicates; the implementation in `.ai/cli/core/loop.py` and the per-ritual command modules MUST satisfy them.

```text
T1 (READY -> THINK via sss):
  GUARD g1.1: session_dir exists and is empty of ritual artefacts
  GUARD g1.2: <task> argument is non-empty after strip()
  GUARD g1.3: graph_state is unset OR == "READY"

T2 (THINK -> SANDBOX via nnn_pass):
  GUARD g2.1: graph_state == "THINK"
  GUARD g2.2: plan_envelope JSON validates against schemas/verification_contract.schema.json
  GUARD g2.3: plan_envelope.allowed_paths is a non-empty list
  GUARD g2.4: plan_envelope.acceptance[] uses canonical schema id+description+command+expect_exit+required (memory feedback_nnn_rrr_acceptance_schema_mismatch)
  GUARD g2.5: each acceptance.command grep -F pattern matches its target file char-for-char (memory feedback_acceptance_grep_char_mismatch)
  GUARD g2.6: forbidden_phrases per nnn_check.template.json absent
  GUARD g2.7: rollback.md present for WARM/COLD tier

T3 (SANDBOX -> DO via vvv_pass):
  GUARD g3.1: graph_state == "SANDBOX"
  GUARD g3.2: vvv_check.template.json predicates satisfied
  GUARD g3.3: assumptions.json:blocking_unknowns is empty (or all answered)

T4 (DO -> VERIFIED via gogogo_complete):
  GUARD g4.1: graph_state == "DO"
  GUARD g4.2: every step in .state/plan.json carries a gogogo.step_completed event
  GUARD g4.3: per-step verifier_report.json:status == "PASS"
  GUARD g4.4: diff_paths_within_allowed_scope == true
  GUARD g4.5: forbidden_paths_untouched == true
  GUARD g4.6: acceptance grep -F runs all return exit 0 with exact-character match

T5 (VERIFIED -> PROMOTED via promote_request):
  GUARD g5.1: graph_state == "VERIFIED"
  GUARD g5.2: decision_packet.json exists and conforms to DDD spec §3
  GUARD g5.3: presentation object conforms to DDD spec §3.1 (cognitive_protocol_version v1.0.1)
  GUARD g5.4: approval.json exists with action=="promote", decided_by=="human"
  GUARD g5.5: HMAC signature valid OR transport not used
  GUARD g5.6: verify_dev.json:passed == true

T6 (PROMOTED -> DEPLOYED via deploy_request):
  GUARD g6.1: graph_state == "PROMOTED"
  GUARD g6.2: approval.json with action=="deploy", decided_by=="human"
  GUARD g6.3: verify_prod.json:passed == true
  GUARD g6.4: sandbox.profile.tier validated for prod target

T7/T7b (DEPLOYED|VERIFIED -> RETRO via rrr):
  GUARD g7.1: graph_state in {"DEPLOYED","VERIFIED"}
  GUARD g7.2: retro_context.json synthesised from session state

T8 (RETRO -> DONE via rrr_complete):
  GUARD g8.1: graph_state == "RETRO"
  GUARD g8.2: RETRO.md required headings present (Session Summary ... Retro Provenance)
  GUARD g8.3: RETRO.md required_structural_predicates pass (memory_handling.mode == index, etc.)
  GUARD g8.4: forbidden_phrases absent
  GUARD g8.5: acceptance source-of-truth THINK/03_ACCEPTANCE.yaml re-runs cleanly
  GUARD g8.6: forbidden_diff against .state/baseline_untracked.json passes

T9 (DONE -> SEALED via close):
  GUARD g9.1: graph_state == "DONE"
  GUARD g9.2: verify_dev.json:passed AND verify_prod.json:passed
  GUARD g9.3: final_manifest computed per close spec §2
  GUARD g9.4: capture_chain_consistent OR tier == HOT
  GUARD g9.5: COLD tier -> external audit file created and referenced

T10 (* -> DEAD via verify_fail_hard):
  GUARD g10.1: verifier_report.json:status == "FAIL_HARD"
  GUARD g10.2: source ritual is recorded as the originating event

T11 (* -> DEAD via policy_violation):
  GUARD g11.1: a canonical .ai/policies/** rule matched the proposed action
  GUARD g11.2: rule id and matched action recorded in evidence

T13 (NEEDS_HUMAN -> PROMOTED|FAILED via human_resolution):
  GUARD g13.1: approval.json OR rejection.json present
  GUARD g13.2: decided_by == "human"

T14 (FAILED -> SANDBOX via revive):
  GUARD g14.1: revival_count < max_revivals (default 3)
  GUARD g14.2: human revival artefact present

T15 (FAILED -> TERMINAL_FAILED via terminal_fail):
  GUARD g15.1: revival_count >= max_revivals

T17 (DONE -> REOPENED via reopen):
  GUARD g17.1: human reopen artefact present
  GUARD g17.2: prior DONE event remains on chain unmutated
```

### 4.3 Pseudocode -- the canonical guard envelope (non-normative-example)

```python
def fire(trigger: str, decided_by: str, evidence: dict | None = None) -> str:
    cur = self.current()
    transition = self._index.get((cur, trigger)) or self._index.get(("ANY", trigger))
    if transition is None:
        self._emit("ritual.transition.blocked",
                   {"reason": "unknown_trigger", "trigger": trigger, "current_state": cur})
        raise TransitionNotFound(...)
    if decided_by != transition["decided_by"]:
        self._emit("ritual.transition.blocked",
                   {"reason": "decided_by_mismatch",
                    "expected": transition["decided_by"], "got": decided_by})
        raise DecidedByMismatch(...)
    for guard_id, predicate in self._guards_for(trigger):
        if not predicate(self.session_path, evidence):
            self._emit("ritual.transition.blocked",
                       {"reason": "guard_failed", "guard_id": guard_id,
                        "trigger": trigger, "current_state": cur})
            raise GuardFailed(guard_id)
    self._set_graph_state(transition["to"])
    self._emit("graph.transition",
               {"session_id": ..., "graph": ..., "from_state": cur,
                "to_state": transition["to"], "trigger": trigger,
                "decided_by": decided_by, "evidence": evidence or {}})
    return transition["to"]
```

The actual implementation in `.ai/cli/core/loop.py` does not yet thread `_guards_for(trigger)` -- guard predicates are currently scattered across the per-ritual command modules (`.ai/cli/commands/sss.py`, `vvv.py`, `nnn.py`, `gogogo.py`, `ddd.py`, `rrr.py`, `close.py`). Centralising guards is a Phase 4 follow-up implementation concern; this spec pins the contract.

### 4.4 Guard-failure audit event (normative-description)

When a guard fails the kernel MUST emit exactly one event:

```text
event_type: ritual.transition.blocked
payload_json:
  reason: "guard_failed"
  guard_id: <string from Section 4.2>
  trigger: <string>
  current_state: <state>
  evidence_ref: <optional path/sha256 of the failing predicate's evidence>
```

See Section 7 for the full 13-field event shape. The blocked event MUST land on the per-session AuditWriter chain BEFORE the calling Python exception is raised, so that even a crashing kernel leaves a record of refusal. This is the structural enforcement of Article XXIII -- Failure Visibility.

### 4.5 Guard composition rules (normative-description)

- Guards are evaluated **left-to-right** in the order listed in Section 4.2. The first failing guard wins; subsequent guards are not evaluated.
- A guard MUST NOT mutate session state. Guards are read-only predicates.
- A guard MUST be implementable in pure Python given (`session_path`, `evidence_dict`); it MUST NOT require shell-out except to deterministic local commands (e.g. `grep -F` for acceptance checks, `git diff --name-only` for forbidden-diff).
- A guard that wraps a shell-out MUST capture exit code, stdout, and stderr in the audit `evidence` field on failure (so post-mortem replay can see why the predicate failed).

---

## Section 5 -- Illegal Transitions

### 5.1 Definition (normative-description)

An **illegal transition** is any `Loop.fire(trigger, decided_by, evidence)` invocation that satisfies one or more of:

1. The `(current_state, trigger)` pair has no row in the canonical catalog (Section 3.1) and no `(ANY, trigger)` fallback row applies.
2. The trigger is unknown (not in the closed namespace per Section 3.2).
3. The `decided_by` value does not match the `decided_by` column for the matched row (Section 6.2).
4. A guard predicate (Section 4.2) returned false.
5. The session is in a terminal state (Section 2.3) and the trigger is not the explicit reopen (T17) for `DONE -> REOPENED`.

### 5.2 The kernel response to an illegal transition (normative-description)

For each of the five illegal-transition cases, the kernel MUST:

1. Refuse the state mutation (do not write to `session_state.json`).
2. Emit exactly one `ritual.transition.blocked` audit event with `reason` set to one of:
   - `unknown_trigger`
   - `unknown_state`
   - `no_matching_transition`
   - `decided_by_mismatch`
   - `guard_failed`
   - `terminal_state_locked`
3. Raise the corresponding Python exception class to the caller (`TransitionNotFound`, `DecidedByMismatch`, `GuardFailed`, `LoopError`) so command modules surface a non-zero exit code.
4. NOT retry. Retry is a caller-side concern, not a kernel one. The kernel MUST NOT loop.

### 5.3 The "unknown state is unsafe" rule (normative-description)

Per Article XI -- Explicit State Governance: "Unknown state is unsafe state." If a session's `session_state.json:graph_state` is set to a string not in the canonical state vocabulary (Section 2.1) AND not declared in the active sub-graph YAML, the kernel MUST treat the session as locked and MUST refuse every trigger except `abort` (T16) until an operator-authored artefact reconciles state.

```text
On Loop.__init__:
  state = session_state.json:graph_state
  if state is None: state = graph.initial_state ("READY")
  elif state not in graph.states and state not in subgraph.states:
    log "ritual.transition.blocked" {reason: "unknown_state", recorded_state: state}
    raise LoopError("session in unknown state; operator action required")
```

This rule prevents a corrupt or hand-edited `session_state.json` from being silently re-projected onto a default. The kernel does not guess. The kernel halts.

### 5.4 Illegal-transition tests (normative-description)

PRD Phase 4 acceptance requires "illegal transitions fail." The implementation MUST carry tests covering at minimum:

- `READY -> SANDBOX` with trigger `vvv_pass` -- no row, refuse with `no_matching_transition`.
- `THINK -> DEPLOYED` with trigger `deploy_request` -- no row, refuse.
- `READY -> THINK` with `decided_by: human` instead of `kernel` -- `decided_by_mismatch`.
- `VERIFIED -> PROMOTED` with `decided_by: kernel` -- `decided_by_mismatch` (this transition requires `human`).
- A trigger string `"sss-extended"` not in the namespace -- `unknown_trigger`.
- A `session_state.json` hand-edited to `graph_state: "FROBNICATED"` -- `unknown_state`.
- `DONE -> THINK` with trigger `sss` -- `terminal_state_locked` (must use `reopen` trigger first).
- A `gogogo_complete` fired with one step still in `gogogo.step_started` (no `step_completed`) -- `guard_failed g4.2`.
- A `nnn_pass` fired against a plan envelope missing `acceptance[]` -- `guard_failed g2.4`.
- A `close` fired with `verify_dev.json:passed = false` -- `guard_failed g9.2`.

Each test MUST verify the corresponding `ritual.transition.blocked` event landed on the chain with the documented `reason`.

### 5.5 Example -- illegal trigger refusal (non-normative-example)

```text
$ bash .ai/cli/ai gogogo                       # in a session whose graph_state == "READY"

ERROR: TransitionNotFound:
  no transition for state='READY' trigger='gogogo_complete' in graph 'standard'

Audit event written:
  type:        ritual.transition.blocked
  reason:      no_matching_transition
  trigger:     gogogo_complete
  current_state: READY
```

The operator's recovery is to fire `sss`, then `vvv` (or HOT-path skip), then `nnn`, then `gogogo` -- the canonical sequence.

### 5.6 Example -- terminal-state lock (non-normative-example)

```text
$ bash .ai/cli/ai sss "patch-it"               # in a session whose graph_state == "SEALED"

ERROR: LoopError:
  session in terminal state SEALED; refuse trigger 'sss'

Audit event written:
  type:        ritual.transition.blocked
  reason:      terminal_state_locked
  trigger:     sss
  current_state: SEALED
```

The session is read-only. The operator must create a NEW session (`ai sss "patch-it"` from a fresh session id) or invoke `reopen` if the session is `DONE` (not `SEALED`; SEALED has no exit).

---

## Section 6 -- Decided-By Attribution

### 6.1 The closed authority set (normative-description)

The `decided_by` field on every transition is a member of exactly:

```text
{ kernel, verifier, policy, human }
```

The kernel MUST refuse a transition whose `decided_by` is not in this set. The validator at `.ai/cli/core/loop.py:51` (`VALID_AUTHORITIES = {"verifier", "policy", "human", "kernel"}`) is the implementation reference.

Authority semantics:

- **`kernel`** -- the kernel itself decides, deterministically, given that all guards are satisfied. Examples: `READY -> THINK` (T1), `THINK -> SANDBOX` (T2), `RETRO -> DONE` (T8), `DONE -> SEALED` (T9). Kernel-decided transitions are mechanical: no semantic judgment is exercised.
- **`verifier`** -- the deterministic verifier (`.ai/policies/verifier-rules.yaml` + `.ai/cli/core/verifier.py`) decided. Examples: `SANDBOX -> DO` (T3), `DO -> VERIFIED` (T4), any `* -> DEAD` via `verify_fail_hard` (T10). The verifier writes `verifier_report.json` and the transition is fired with `decided_by: verifier` plus the report path as evidence.
- **`policy`** -- a canonical policy in `.ai/policies/**` matched and asserted authority. Example: `* -> DEAD` via `policy_violation` (T11). Policy authority is narrower than verifier authority -- policies emit only deny verdicts; pass is implicit (Article XVI -- Least Authority).
- **`human`** -- a human operator wrote a decision artefact. Examples: `VERIFIED -> PROMOTED` (T5), `PROMOTED -> DEPLOYED` (T6), `DONE -> REOPENED` (T17), `FAILED -> ABORTED` (T16). The artefact MUST carry `decided_by: human` per Article XIII and TRINITY_DDD_HUMAN_GATE_SPEC_V1 §4-6.

### 6.2 Per-transition decided-by enforcement (normative-description)

The decided_by column in Section 3.1 is normative. The kernel:

1. Reads the matched transition row.
2. Compares `transition.decided_by` against the caller-supplied `decided_by` argument.
3. Refuses if they differ; emits `ritual.transition.blocked` with `reason: decided_by_mismatch`.

This is the structural enforcement of Article IV -- Separation of Responsibilities. A planner-agent CLI command cannot fire a `human`-authority transition by supplying `decided_by: human` -- the transition still requires the human-authored artefact (via the guard, Section 4.2 GUARD g5.4). And a `human`-authority transition cannot be smuggled in as `decided_by: kernel` to bypass the artefact check, because the kernel refuses the assertion.

### 6.3 Spoofing prevention (normative-description)

`decided_by` is a self-asserted string from the caller. The kernel cannot, by inspecting only the function call, prove the caller is who they claim. Spoofing is structurally prevented by:

1. **Artefact requirement.** Every `decided_by: human` transition has a guard requiring an on-disk artefact whose schema asserts `decided_by: human`. A caller asserting `decided_by: human` without the artefact fails GUARD g5.4 / g6.2 / g13.2 / g16.x / g17.1 and is refused.
2. **HMAC signature for transport.** When the artefact arrived via transport (`trinity-tg-bot`), the artefact MUST carry an HMAC signature that the kernel verifies against the operator key (per `.ai/cli/core/auth.py` and TRINITY_DDD_HUMAN_GATE_SPEC_V1 §4 `signature` field). Article XV -- Transport is Not Authority -- means the transport itself cannot vouch; the HMAC binds the artefact to the operator's key.
3. **Verifier independence.** A `decided_by: verifier` transition requires `verifier_report.json` whose presence and shape the kernel re-validates. The kernel does not trust the caller's assertion; it re-reads the report.
4. **Policy lookup.** A `decided_by: policy` transition requires the policy id and matched rule to be recorded in the evidence; the kernel re-loads the policy file and re-evaluates the predicate before accepting.

In all four cases the guard re-derives the authority from the on-disk evidence; the `decided_by` argument is a routing hint, not a trust signal.

### 6.4 Mapping to the role permission matrix (informational)

Ritual Constitution v1.1 Article XVIII pins the role-to-ritual write permission matrix. The mapping to the kernel transition catalog is:

| Ritual | Writing role | decided_by on the corresponding transition |
|---|---|---|
| `sss` | Session Initializer | `kernel` (for T1) |
| `vvv` | Clarification Agent | `verifier` (for T3 -- the agent writes the artefact, the kernel verifies it) |
| `nnn` | Planning Agent | `kernel` (for T2 -- the kernel verifies the plan envelope schema) |
| `gogogo` | Executor Agent | `verifier` (for T4 -- step verifier returns PASS/FAIL) |
| `ddd` | Verifier Agent + Presentation Synthesizer + Human Approver | `human` (for T5 / T6) |
| `rrr` | Retro Writer | `kernel` (for T7/T7b/T8) |
| `close` | Kernel | `kernel` (for T9) |

The agent is the *writer* of the artefact; the *decider* of the state mutation is determined by which on-disk evidence the guard requires. Article IV is satisfied because no role is collapsed -- the writer is independent of the decider, and the decider is independent of the role that benefits.

---

## Section 7 -- Audit Emission per Transition

### 7.1 Required event (normative-description)

Every successful transition MUST emit exactly one `graph.transition` event on the per-session AuditWriter chain. The event obeys the 13-field shape pinned in TRINITY_AUDIT_EVENT_SPEC_V1 §2.

```text
schema_version:  "trinity.audit_event.v1"
event_id:        "evt_<uuid4-hex>"
session_id:      "<session id>"
seq:             <monotonic per-session integer; UNIQUE(session_id, seq)>
event_type:      "graph.transition"
ritual:          "<sss|vvv|nnn|gogogo|ddd|rrr|close|null>"   # null for ANY-fired transitions
capture_id:      <ULID linking back to a captures row, when wrapped in a capture transaction; else null>
actor:           "kernel"
ts_utc:          "<RFC3339 UTC>"
payload_json:    <canonicalised JSON; see §7.2>
payload_hash:    sha256(payload_json)
prev_hash:       <previous event's hash; "0" for genesis>
hash:            sha256(canonical_json(event_for_hash))   # see audit spec §2.1
```

The kernel MUST claim `seq` under `BEGIN IMMEDIATE` against the per-session SQLite at `<session>/CAPTURE/capture.sqlite` (TRINITY_AUDIT_EVENT_SPEC_V1 §2 / capture_store.py). The legacy `.ai/audit/events.ndjson` file MAY receive a mirrored 5-field row for backward compatibility (TRINITY_AUDIT_EVENT_SPEC_V1 §2.2); it is not authoritative.

### 7.2 Required payload fields for `graph.transition` (normative-description)

```json
{
  "graph": "<graph name; e.g. standard>",
  "from_state": "<previous state>",
  "to_state": "<new state>",
  "trigger": "<trigger string>",
  "decided_by": "<kernel|verifier|policy|human>",
  "evidence": { "<artefact path or short identifier>": "<sha256 or short value>", ... }
}
```

The `evidence` map SHOULD reference the on-disk artefact(s) the guard consumed. Examples:

- For T2 (`nnn_pass`): `evidence: {"plan_envelope_path": ".state/plan.json", "plan_envelope_sha256": "<hash>"}`
- For T4 (`gogogo_complete`): `evidence: {"verifier_report": "DO/dev/verifier_report.json", "verifier_report_sha256": "<hash>"}`
- For T5 (`promote_request`): `evidence: {"approval": "DO/control/approval.json", "approval_sha256": "<hash>", "decision_packet_id": "pkt_..."}`

### 7.3 Companion ritual event (normative-description)

Most transitions MUST also emit a companion ritual-namespace event from TRINITY_AUDIT_EVENT_SPEC_V1 §3. The pairing is fixed by the catalog table (Section 3.1, "Audit event" column):

| Transition | Companion event(s) |
|---|---|
| T1 | `sss.invoked`, `session.created` |
| T2 | `nnn.passed` |
| T3 | `vvv.passed` |
| T4 | `gogogo.completed` |
| T5 | `ddd.packet_emitted`, `ddd.approved` (for promote) |
| T6 | `ddd.approved` (for deploy) |
| T7/T7b | `rrr.proposed` |
| T8 | `rrr.completed` |
| T9 | `close.invoked`, `close.manifest_built`, `close.completed`, `session.closed` (and `close.external_audit_emitted` on COLD) |
| T10 | `verify.completed` (status FAIL_HARD) |
| T11 | `policy.violation.detected` |
| T12 | `verify.completed` (status NEEDS_HUMAN) |
| T13 | `ddd.approved` or `ddd.rejected` |
| T16 | `session.abandoned` |
| T18 | `plan.amended` |
| T19 | `state.changed` |

The companion events MAY be emitted before, after, or wrapped around the `graph.transition` event but MUST be on the same per-session chain with monotonic `seq`.

### 7.4 Refusal event for blocked transitions (normative-description)

When the kernel refuses a transition (Section 5), it MUST emit:

```text
event_type:  "ritual.transition.blocked"
actor:       "kernel"
payload_json:
  reason:        "<unknown_trigger|unknown_state|no_matching_transition|decided_by_mismatch|guard_failed|terminal_state_locked>"
  trigger:       "<the trigger string>"
  current_state: "<the state at refusal time>"
  ...
```

Optional payload fields by reason:

- `decided_by_mismatch`: `expected`, `got`
- `guard_failed`: `guard_id`, `evidence_ref`
- `unknown_trigger`: `triggers_known` (a small list of nearby valid triggers, for caller diagnosis)
- `terminal_state_locked`: `terminal_states` (the closed terminal set)

The blocked event MUST land on chain BEFORE the Python exception is raised; if the kernel crashes between the refusal decision and the chain append, the next `Loop.__init__` MUST detect the missing audit row and re-emit on `_reconcile_from_audit`.

### 7.5 Hash-chain integrity (normative-description)

Per TRINITY_AUDIT_EVENT_SPEC_V1 §2.1, the chain for a session is rooted at `prev_hash = "0"` at `seq = 1` and every subsequent event has `prev_hash = previous.hash` and `seq = previous.seq + 1`. The kernel MUST validate hash integrity on `Loop.__init__` (existing `audit verify-chain` infrastructure handles long-chain validation; per-session quick validation is a startup smoke test). A broken chain is a Article X -- Audit Discipline violation; the kernel MUST refuse all triggers and surface `NEEDS_HUMAN` until operator reconciliation.

### 7.6 Cross-reference -- legacy events.ndjson (informational)

The implementation in `.ai/cli/core/loop.py:177-189` currently appends `graph.transition` to the legacy global `.ai/audit/events.ndjson` (5-field shape, AuditChain class). This is the pre-RecordProxy path. Per TRINITY_AUDIT_EVENT_SPEC_V1 §2.2 the legacy file is kept for backward compatibility but is no longer the source of truth. Migration to per-session AuditWriter is the implementation concern of a separate Phase 10/15 session; this spec pins the contract a Phase-4-conformant implementation MUST satisfy.

---

## Section 8 -- Passive Core Invariant

### 8.1 The invariant (normative-description)

Per Article XX -- Passive Core Principle (verbatim quote in Section 1.2):

```text
Core Trinity systems act only through explicit invocation.

Core systems MUST NOT:

self-trigger
self-expand authority
silently mutate policy
rewrite themselves recursively
generate new goals autonomously
```

Applied to the kernel state machine, this means:

1. **No background timers.** The kernel does not run a daemon that polls sessions for stale `graph_state` and forces transitions. There is no `kernelctl auto-promote` cron.
2. **No self-trigger from inside fire().** A successful `Loop.fire(...)` MUST NOT recursively invoke another `Loop.fire(...)` on its own. The caller (a CLI command, a test, a sibling tool) is the sole authority for the next trigger.
3. **No silent state repair.** If `Loop._reconcile_from_audit` detects drift between `session_state.json` and the audit chain, it MUST update `session_state.json` to match the chain (audit wins, D9), but MUST NOT fire a new transition. Reconciliation is a read; not a write of new history.
4. **No automatic verifier re-run.** The kernel does not re-invoke the verifier after a `verify_fail_hard` to give it a "second chance." The caller invokes the verifier; the kernel only consumes the report.
5. **No automatic ritual chaining.** `ai vvv` does NOT auto-fire `ai nnn` on success. Each ritual is a separate explicit invocation. The CLI may print "next: nnn" as a hint, but the kernel does not run it.
6. **No background memory crawl.** Memory-CLI (Article IX) is invoked explicitly during `rrr`; it does not auto-index new files appearing in a session directory.

### 8.2 Why the invariant matters (normative-description)

The state machine is the Trinity layer that, if it were active, could most easily become an autonomous agent. A poll loop that "auto-completes" stale sessions; an auto-promote rule that fires on a successful verify; an auto-reopen on a downstream test failure -- each of these is a slippery-slope toward "AI governs itself" (Article III). Article XX is the structural prohibition against that drift.

The kernel state machine is a *referee*: it tells you whether a move is legal. It does not play moves. The caller plays the moves; the human plays the high-stakes moves; the kernel only records and refuses.

### 8.3 Conformance tests for the passive-core invariant (normative-description)

A Phase-4-conformant implementation MUST carry tests that prove:

1. **No background thread.** `import .ai.cli.core.loop` MUST NOT spawn a thread, MUST NOT register an `atexit` handler that mutates state, MUST NOT open a network socket, MUST NOT touch a session directory other than the one passed to `Loop.__init__`.
2. **fire() is one-shot.** A single `Loop.fire(...)` call results in exactly one `graph.transition` event on the chain. (Companion ritual events from Section 7.3 are emitted by the *caller* command module, not by `fire()` itself.)
3. **No self-fire recursion.** A guard predicate MUST NOT call `Loop.fire(...)`. Centralised guards (Section 4.3) are read-only.
4. **No daemonisation in CLI commands.** `bash .ai/cli/ai <ritual>` exits cleanly with a non-zero code on refusal and zero on acceptance; it does not background, does not hold a long-lived lock, does not auto-retry on EBUSY beyond the session-state lock acquisition timeout (state.py:120-142).
5. **`ai status` is read-only.** A `bash .ai/cli/ai status` invocation MUST NOT write to `session_state.json`, MUST NOT append to the audit chain, MUST NOT mutate the SQLite store. Status is a snapshot.
6. **Reconcile is read-then-write-once.** `Loop._reconcile_from_audit` may write `session_state.json` once (to align with the chain), but MUST NOT append a new audit event on reconciliation.

The conformance tests MUST run on every CI pass; a failure halts the merge.

### 8.4 Where automation IS allowed (informational)

Article XX permits automation when "bounded, observable, interruptible, auditable." The state machine's permitted automation surface is:

- **CLI loop within a single command.** `ai gogogo` walks the plan steps in a single subprocess, emitting one `gogogo.step_started` / `step_completed` per step. This is a bounded loop (length = number of plan steps); it is observable (each step audits); it is interruptible (Ctrl-C aborts); it is auditable (chain entry per step).
- **`ai loop run` budget loop.** The next-action loop (`.ai/cli/core/loop_state.py`) iterates within an explicit budget (count, wallclock); each iteration is one step; the budget itself is the bound; the operator sets the budget.
- **`ai close run` final manifest computation.** Close walks the session tree and hashes artefacts; the bound is the file count; the operation is auditable via `close.manifest_built`.

None of these write a `graph.transition` event without an explicit ritual command. The state machine never auto-advances.

---

## Section 9 -- Versioning & Article XXIX Amendment Protocol

### 9.1 Why amendments are constrained (normative-description)

Adding a new state, a new transition, or changing a `decided_by` is an Operational-tier amendment per Addendum v1.0.4 §XXIX.2 (changes how the system MUST behave at runtime), or a Constitutional-tier amendment per §XXIX.3 if it touches an Article (e.g. adding a new authority alongside `kernel|verifier|policy|human` would touch Article IV).

A naive amendment that adds a new state breaks two things:

1. **Audit replay.** Existing audit chains contain `graph.transition` events whose `to_state` is from the old state set. A new graph YAML that omits the old states fails replay against historical chains. (Memory `feedback_recordproxy_option_c_misleading.md` is a specific instance of this drift class -- schema enrichment without capture transaction breakage.)
2. **Sub-graph composition.** A sub-graph YAML that pushes onto the standard graph relies on the standard's state vocabulary; a removed state breaks the inner -> outer return path.

This section pins the procedure that prevents both classes of breakage.

### 9.2 The amendment procedure (normative-description)

Adding or removing a state, transition, or decided_by:

1. **Proposal.** A new addendum file at `docs/constitution/addendums/TRINITY_KERNEL_STATE_TRANSITION_ADDENDUM_<ver>.md` (or, if the change is small enough to be Operational, an in-spec section update with full §1-§3 of Addendum v1.0.4 form). Editorial typo fixes use the §XXIX.1 commit-message-only path; semantic changes do not.
2. **Rationale.** Trace-to-failure per §XXIX.4 -- a session id, an audit event id, an observed friction event, a measurable risk artefact, or a named safety requirement. "It seemed like a good idea" is not a trace.
3. **Impact analysis.** MUST list:
   - Every existing audit chain's compatibility (replayable / partially / requires migration).
   - Every sub-graph YAML's compatibility.
   - Every consumer (verifier, ddd command, close command, retro_writer, presentation_synthesizer, sibling CLIs).
   - Rollback path -- how to revert if the amendment proves harmful.
4. **Human approval.** A `decided_by: human` ddd artefact in the landing session.
5. **Version bump.** Bump the spec version (`v1.0` -> `v1.1` for Operational; `v1.0` -> `v2.0` for Constitutional). Update the `version:` frontmatter and the `last-updated:` date.
6. **Audit entry.** Per §XXIX.5, append to `.ai/audit/events.ndjson`:

   ```text
   event_type: constitution.amended.operational | constitution.amended.constitutional
   payload:
     actor:         <operator id or kernel session id>
     diff_sha256:   <sha256 of the unified diff>
     tier:          operational | constitutional
     rationale_ref: <addendum file path + section anchor>
   ```

### 9.3 Adding a new state -- specific rules (normative-description)

When adding a state `<X>`:

- The amendment MUST declare whether `<X>` is terminal.
- The amendment MUST list at least one inbound transition (otherwise `<X>` is unreachable and the amendment fails impact analysis).
- The amendment MUST list at least one outbound transition OR mark `<X>` terminal (otherwise the amendment introduces a state from which the session cannot exit).
- The amendment MUST update the canonical state vocabulary table (Section 2.1) AND the `.ai/graphs/standard.yaml` YAML in the SAME commit. Drift between spec and YAML is itself a constitutional violation (Article XXVII -- Scope Discipline).

### 9.4 Adding a new transition -- specific rules (normative-description)

When adding a transition row:

- The amendment MUST declare `from`, `to`, `trigger`, `decided_by` -- all four; partial declarations are refused at YAML validation (loop.py:118-128 `_validate_graph`).
- The amendment MUST declare the guard predicates (Section 4.2 entry).
- The amendment MUST declare the audit companion event (Section 7.3).
- The amendment MUST NOT introduce a `(from, trigger)` collision with an existing row (loop.py:142-146 `_build_index` enforces).
- If the amendment uses `from: ANY`, the rationale MUST justify why every state legitimately responds to this trigger -- ANY is reserved for cross-cutting failure paths (e.g. `verify_fail_hard`, `policy_violation`).

### 9.5 Removing a state or transition -- deprecation procedure (normative-description)

A state or transition MAY NOT be removed in one step. The procedure is:

1. **Mark deprecated.** Add a `deprecated: true` flag on the row in `.ai/graphs/standard.yaml`, AND a deprecation note in this spec, AND a deprecation event-type in TRINITY_AUDIT_EVENT_SPEC_V1 §3.1 ("Legacy aliases" extended to "Deprecated transitions").
2. **Emit deprecation warnings.** Every time the deprecated transition fires, the kernel MUST emit `state.changed` with `payload.deprecation_warning: "<row id> is deprecated; use <replacement> instead"`. The warning is observable by audit replay.
3. **Wait one full release cycle.** A release cycle is at minimum a Constitutional addendum + 30 calendar days OR a successful empirical test session per Article XII.5 of Ritual Constitution v1.1, whichever is longer.
4. **Removal.** A second amendment removes the row from `.ai/graphs/standard.yaml` and the catalog table (Section 3.1). Audit replay against historical chains uses the §3.1 legacy-alias mapping in TRINITY_AUDIT_EVENT_SPEC_V1.

### 9.6 Audit chain back-compatibility (normative-description)

A historical audit chain whose `graph.transition` events reference a removed state MUST remain replayable. This is achieved by:

- Keeping `to_state` and `from_state` as free-form strings in the audit row (§7.2). The replay tool (`ai audit replay`) does NOT validate that historical states are in the *current* graph's state set -- it validates against the *graph version recorded at session-start time* (a future field, deferred).
- Until the per-session graph-version field is added, audit replay against pre-amendment chains MUST surface a `state.changed` warning rather than a hard failure for unknown historical states. This preserves Article X -- Audit Discipline (history is not silently rewritten) and Article XXIII -- Failure Visibility.

### 9.7 Versioning strategy (normative-description)

Version field semantics:

- **`v1.0` -> `v1.1` (Operational)**: state vocabulary unchanged; one or more new transitions OR one new guard predicate OR one new companion event added. Existing chains replayable without migration.
- **`v1.0` -> `v2.0` (Constitutional)**: state vocabulary changed (state added or removed) OR `decided_by` set extended OR Article-touching change. Existing chains replayable with the legacy-alias mapping (Section 9.6).
- **Pre-1.0**: not used; this is the first canonical version.

The current version is `v1.0`; the spec is `status: draft` until the Phase 4 ddd gate accepts it.

---

## Section 10 -- Glossary Cross-Refs

### 10.1 Terms defined in `docs/specs/12_GLOSSARY.md` (informational)

The following glossary entries are load-bearing for this spec; readers are referred to `docs/specs/12_GLOSSARY.md` for the canonical definitions:

- **`decided_by`** -- §`12_GLOSSARY.md#decided_by`
- **Audit (events.ndjson)** -- §`12_GLOSSARY.md#audit-eventsndjson`
- **Authority** -- §`12_GLOSSARY.md#authority`
- **Artifact** -- §`12_GLOSSARY.md#artifact`
- **DEAD (verdict)** -- §`12_GLOSSARY.md#dead-verdict`
- **DO (state)** -- §`12_GLOSSARY.md#do-state`
- **Graph** -- §`12_GLOSSARY.md#graph`
- **Hash chain** -- §`12_GLOSSARY.md#hash-chain`
- **events.ndjson** -- §`12_GLOSSARY.md#eventsndjson`
- **Coordinator** -- §`12_GLOSSARY.md#coordinator`

### 10.2 New terms defined in this spec (normative-description)

The following terms are introduced or pinned by this spec; future glossary updates SHOULD link back here.

- **Transition guard.** A deterministic, read-only predicate evaluated by the kernel between trigger acceptance and state mutation. A guard's failure MUST refuse the transition AND emit `ritual.transition.blocked` with `reason: guard_failed`. See Section 4.
- **Illegal transition.** Any `Loop.fire(...)` invocation that fails one or more of: trigger-namespace check, `(from, trigger)` row lookup, `decided_by` match, guard predicate, terminal-state lock. Illegal transitions are refused, audited, and surface as exceptions to the caller. See Section 5.
- **Decided-by chain.** The end-to-end chain of authority for a session, read from the sequence of `graph.transition` events on the per-session audit chain. Each event's `decided_by` field is one of `kernel | verifier | policy | human`. The chain is the audit-replayable proof of who decided what, when. See Section 6 and Section 7.
- **Companion ritual event.** The ritual-namespace event (e.g. `nnn.passed`, `gogogo.completed`, `rrr.completed`) that pairs with the `graph.transition` event for a given trigger. See Section 7.3.
- **Terminal state lock.** The kernel's refusal to fire any trigger (other than the explicit reopen for `DONE`) once a session reaches a state in the closed terminal set `{DONE, SEALED, DEAD, ABORTED, TERMINAL_FAILED}`. See Section 5.3 and the `terminal_state_locked` blocked-reason in Section 7.4.
- **Passive core conformance test.** A kernel test asserting one of the six conditions in Section 8.3 (no background thread, fire() is one-shot, no self-fire recursion, no daemonisation, status is read-only, reconcile is read-then-write-once).

### 10.3 Cross-spec references (informational)

- **TRINITY_AUDIT_EVENT_SPEC_V1** -- 13-field event shape (§2), event-type registry (§3), `ai audit replay` and `verify-chain` commands (§4-5). This spec inherits all event-shape rules from there.
- **TRINITY_DDD_HUMAN_GATE_SPEC_V1** -- decision_packet / approval / rejection / hold artefact shapes; the source of GUARD g5.2-g5.4, g6.2, g13.1-g13.2.
- **TRINITY_SESSION_CLOSE_SPEC_V1** -- final manifest shape; the source of GUARD g9.3-g9.5.
- **TRINITY_VERIFIER_CONTRACT_V1** -- verifier_report shape; the source of GUARD g4.3, g10.1, g12.1.
- **TRINITY_SANDBOX_CAPABILITY_SPEC_V1** -- sandbox.profile.tier semantics; the source of GUARD g6.4 and Section 4.2 tier-routing.
- **Ritual Constitution v1.1 Article XVII** -- the broader state vocabulary; canonical mapping to this spec's vocabulary in Section 2.6.
- **Ritual Constitution v1.1 Article XVIII** -- the role permission matrix; mapping to `decided_by` in Section 6.4.
- **Ritual Constitution v1.1 Article XIV** -- HOT/WARM/COLD path requirements; the source of the `vvv` skip permission referenced in GUARD g2.1 and the catalog rows T2 / T3.
- **Ritual Constitution v1.1 Article XV.2** -- session revival rule; the source of GUARD g14.1 and g15.1 (max_revivals = 3).

### 10.4 Memory cross-refs (informational)

The following long-running memory entries informed specific guard predicates or transition rules; they are not normative but are worth flagging for future maintenance:

- `feedback_acceptance_grep_char_mismatch.md` -- GUARD g2.5, g4.6: ASCII-only patterns; em-dash / smart quotes / nbsp cause silent failure.
- `feedback_nnn_rrr_acceptance_schema_mismatch.md` -- GUARD g2.4: acceptance[] uses `id+description+command+expect_exit+required`.
- `feedback_close_requires_verify_dev_and_prod.md` -- GUARD g9.2: close requires BOTH verifies; error messages must say so.
- `feedback_rrr_cross_session_forbidden_diff.md` -- GUARD g8.6 and T1 post-condition: baseline_untracked snapshot at sss.
- `feedback_rrr_acceptance_yaml_source.md` -- GUARD g8.5: rrr re-runs acceptance from `THINK/03_ACCEPTANCE.yaml`.
- `feedback_executor_helper_forbidden_writes_drift.md` -- Section 6.3 spoofing prevention; in-house agents must not invert Article XXV priority.
- `feedback_plan_amendment_vs_subsession.md` -- T18 (REOPENED -> SANDBOX via replan) emits `plan.amended` rather than forcing a sub-session.
- `feedback_close_capture_before_archive.md` -- Section 8.3 conformance test #4: archive runs after capture exit.

---

## Final Invariants

```text
Every kernel state mutation MUST be:
  - explicitly invoked        (Article XX)
  - declared in the graph     (Article XII)
  - decided by closed authority (Article III, IV, XVI)
  - audit-logged              (Article X)
  - artifact-referenced       (Article II)
```

```text
Unknown trigger     -> refuse + audit ritual.transition.blocked
Unknown state       -> refuse + audit ritual.transition.blocked
No matching row     -> refuse + audit ritual.transition.blocked
decided_by mismatch -> refuse + audit ritual.transition.blocked
Guard failed        -> refuse + audit ritual.transition.blocked
Terminal locked     -> refuse + audit ritual.transition.blocked
```

```text
The kernel referees.
The kernel does not play.
The kernel does not poll.
The kernel does not auto-promote.
The kernel does not auto-deploy.
The kernel does not silently advance.
```

```text
AI proposes triggers.
Verifier and policy decide deterministic transitions.
Humans decide irreversible transitions.
Kernel records, refuses, and audits.
```

---

**Spec status:** DRAFT v1.0 (Phase 4 -- pending Phase 4 ddd gate per PRD §9).
**Implementation references:** `.ai/cli/core/loop.py`, `.ai/cli/core/state.py`, `.ai/graphs/standard.yaml`, `.ai/cli/COMMAND_MANIFEST.yaml`.
**Canonical authority:** Trinity Constitution v1.0 (Articles III, IV, X, XI, XII, XVI, XX, XXV, XXIX); Trinity Ritual Constitution v1.1 (Articles XIV, XVII, XVIII, XV.2); Trinity Constitution Addendum v1.0.4 (XXIX.1-XXIX.6).
