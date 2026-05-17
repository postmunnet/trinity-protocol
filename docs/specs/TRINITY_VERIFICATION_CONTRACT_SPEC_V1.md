---
title: "Trinity Verification Contract Spec v1.0"
version: "1.0"
status: "draft"
phase: "3"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes:
  - "(none -- first canonical version)"
constitutional-anchor: ["Article III", "Article IV", "Article XVI", "Article XX", "Article XXIX"]
amendment-policy: "Article XXIX -- explicit proposal + rationale + impact analysis + human approval + version bump + audit entry."
---

# TRINITY_VERIFICATION_CONTRACT_SPEC_V1

**Status:** DRAFT v1 (first canonical version -- pending verifier review + ddd)
**Phase:** 3 -- Verification Contract
**Organ:** Verifier (Article VIII), in coordination with Planner (Article VI), Executor (Article VII), and Audit (Article X)
**Constitutional rank:** 5 -- Workflow Contract (per Article XXV)
**Date:** 2026-05-15

## Section 0 -- Rank-5 Authority Disclaimer (Article XXV)

This document is a **Workflow Contract**. It ranks fifth in the constitutional priority order:

```text
Constitution
-> Ritual Constitution
-> Canonical Policies        (.ai/policies/**)
-> Kernel State Rules        (.ai/cli/**, graph transitions)
-> Workflow Contracts        (THIS DOCUMENT)
-> Tool Contracts
-> Runtime Requests
-> Model Suggestions
```

This Spec is **void where it conflicts with any higher-ranked instrument**. Amendments follow Article XXIX (operationalised by Addendum v1.0.4 -- editorial / operational / constitutional tier classification, trace-to-failure, pinned audit format).

This Spec does NOT amend `.ai/policies/verifier-rules.yaml`. That file is the authoritative rule corpus and is governed by Canonical Policies (rank 2). This Spec describes the **shape of the contract** that `nnn` produces, that `gogogo` consumes as a precondition, and that `verify`, `ddd`, `rrr`, and `close` reference downstream.

---

## Section 1 -- Purpose & Constitutional Anchor

**[normative-description]**

The Trinity Verification Contract is the artifact that operationalises the constitutional rule that **AI cannot govern itself**. It is the inspectable, machine-checkable promise -- written before execution -- that defines what success means, what failure means, what evidence will be produced, and where the human-decision boundary lies.

Every non-trivial workflow MUST produce a Verification Contract during `nnn` (planning). Every `gogogo` invocation MUST refuse non-trivial execution unless a contract is present, well-formed, and matches the plan envelope it gates.

### 1.1 Why a Verification Contract exists

Article III states (verbatim):

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

A model that proposes a plan AND verifies its own success is in violation of "verify its own correctness" and "bypass verifier approval". The Verification Contract closes that loophole by **fixing the verification surface BEFORE execution begins**, so the verifier is not asking the executor "did you succeed?" but asking the artifact "do you satisfy the pre-declared criteria?"

The contract is the answer to: *what would prove this work is done?* -- written by the planner, validated by deterministic rules + policy + (last resort) gated LLM judge + (final) human, with every verdict hash-chained into per-session audit (TRINITY_AUDIT_EVENT_SPEC_V1).

### 1.2 Article IV -- Separation of Responsibilities

Article IV states (verbatim):

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

The Verification Contract enforces this separation by **physically isolating the verification criteria from the executor that will be checked against them**. The contract is authored at PLAN time by Planner, frozen into the session state at PASS-of-`nnn`, and read (never re-authored) by Verifier at `gogogo` step boundaries and at `verify`. Executor MAY produce evidence that satisfies the contract; Executor MUST NOT mutate the contract itself. Kernel enforces this asymmetry.

### 1.3 Article XX -- Passive Core Principle

Article XX states (verbatim):

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

The Verifier is a Passive Core system. It evaluates only when invoked at a kernel-defined boundary (step completion in `gogogo`, the dedicated `verify` command, the final-manifest check at `close`, or the retro acceptance check at `rrr`). It MUST NOT:

- Trigger its own re-evaluation when bored
- Quietly upgrade a RETRY into a PASS over time
- Rewrite verifier-rules.yaml in response to repeated failures
- Generate new acceptance criteria that the planner did not declare

The Verification Contract is the **explicit invocation surface** for Verifier. Without a contract, the Verifier has nothing to evaluate against and MUST refuse to emit a verdict (the result of an invocation with no contract is a kernel-level error, not a Verifier verdict).

### 1.4 Article XXIX -- Amendment Discipline

Article XXIX states (verbatim):

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

The Verification Contract Spec itself is an amendment-bearing artifact. Bumping V1 -> V1.1 -> V2 follows Article XXIX (further operationalised by Addendum v1.0.4's editorial / operational / constitutional tiering). Section 9 of this Spec details the per-tier amendment requirements for changes to the contract surface.

The contract **schema** (`.ai/schemas/verification_contract.schema.json`, deferred to Phase 3 implementation gogogo) is similarly amendment-bearing: schema field additions are operational; schema field removals or semantic changes are constitutional.

### 1.5 Article XVI -- Least Authority

Article XVI states (verbatim):

```text
Every component MUST operate with minimum required authority.

Examples:

memory-cli must not own execution authority
verifier must not own production mutation authority
browser-cli must not own deployment authority
transport must not own governance authority

Unknown authority MUST be treated as denied authority.
```

The Verifier holds **read** authority over plan envelopes, contracts, and evidence; it holds **write** authority only to its own report file and to the audit chain (via `verify.completed` events through AuditWriter). The Verifier MUST NOT mutate plan state, MUST NOT mutate contract state, MUST NOT mutate executor artifacts. Any contract field that requests Verifier-side mutation is a contract violation and MUST be rejected at contract validation (Section 4).

**[non-normative-example]** -- if a plan author writes a contract requiring `verifier_action: "auto-fix lint failures"`, the contract validator MUST reject this at `nnn`, because granting the Verifier executor-equivalent authority collapses the role boundary required by Article IV and exceeds the least-authority bound of Article XVI.

---

## Section 2 -- Verdict Vocabulary

**[normative-description]**

The verdict set is **closed**. Every verifier evaluation -- regardless of layer (Section 3) -- terminates in exactly one of four verdicts. The vocabulary is fixed by `.ai/policies/verifier-rules.yaml` (`verdicts:` block) and is restated here as load-bearing for the contract surface.

```text
PASS, RETRY, NEEDS_HUMAN, DEAD
```

Adding a verdict is a **constitutional** amendment under Addendum v1.0.4 XXIX.3 -- it changes how every downstream organ (Kernel, Audit, DDD, Retro, Close) reads verifier output.

### 2.1 PASS

**Semantics.** The contract's pre-declared acceptance criteria are satisfied by the supplied evidence. The workflow MAY advance to the next state.

**Lifetime.** A PASS verdict is **scoped to the contract revision and evidence snapshot** it was emitted against. If either the contract is amended (`plan.amended` event) or the evidence is mutated after PASS, the PASS is invalidated and re-evaluation is required.

**Who can emit.**

- Layer 1 (deterministic) -- when ALL `pass_when` predicates evaluate true and no higher-priority predicate (`dead_when`, `needs_human_when`, `retry_when`) fired.
- Layer 2 (policy) -- when no policy gate denies and all required gates report `allow`.
- Layer 3 (gated LLM judge) -- only when the contract explicitly authorises layer-3 PASS authority for the rule_set in question. By default, layer 3 may downgrade (PASS -> RETRY / NEEDS_HUMAN) but MAY NOT upgrade an indeterminate evidence set into PASS.
- Layer 4 (human) -- always; the human verdict is final and supersedes lower-layer outputs (subject to audit).

**Constitutional anchor.** Article XXIV ("A successful state transition without required evidence is invalid"). PASS without contract-named evidence is a constitutional violation.

### 2.2 RETRY

**Semantics.** The contract's criteria are not met, but the failure mode is recoverable within the current session. The workflow MAY re-execute the failed step within its retry budget. The retry budget is contract-declared (Section 4) and enforced by Kernel.

**Lifetime.** A RETRY verdict is consumed by exactly one re-execution attempt. The retry counter (`retry_count`) is incremented in the per-session state. When `retry_count >= retry_budget`, the next failure auto-promotes to DEAD via the `retry_budget_exhausted` predicate.

**Who can emit.**

- Layer 1 -- when any `retry_when` predicate fires (e.g. `test_failed`, `missing_test_artifact`, `transient_compile_error`).
- Layer 2 -- when a policy gate is in soft-deny state pending evidence resubmission.
- Layer 3 -- as the default downgrade verdict for inconclusive LLM judgement.
- Layer 4 -- humans may emit RETRY when they want the executor to re-run with adjusted parameters.

### 2.3 NEEDS_HUMAN

**Semantics.** The verdict is indeterminate at the current layer and the situation requires human authority to resolve. The workflow is paused; no further automated progression is permitted until a human emits a definitive verdict (PASS / RETRY / DEAD) or amends the contract.

**Lifetime.** A NEEDS_HUMAN verdict persists until a human action (recorded as an audit event with `decided_by: human`) supersedes it. NEEDS_HUMAN does NOT auto-expire; transport-layer reminders are permitted (Article XV) but transports MAY NOT auto-resolve.

**Who can emit.**

- Layer 1 -- when a `needs_human_when` predicate fires (e.g. `unclear_intent`, `production_write`, `schema_change`, `api_breaking_change`).
- Layer 2 -- when policy denies an action whose only override path is human approval (e.g. critical-gate enforcement per Article XIV).
- Layer 3 -- as the default fallback when LLM judge budget is exhausted (`fallback_verdict: NEEDS_HUMAN`).
- Layer 4 -- humans MAY also emit NEEDS_HUMAN to defer a decision and request additional information; this remains a NEEDS_HUMAN verdict (it does not transmute into RETRY).

**Constitutional anchor.** Article XIII ("Human approval MUST exist as an artifact"). The NEEDS_HUMAN verdict is the **trigger** that obliges that artifact to exist before progression.

### 2.4 DEAD

**Semantics.** The contract cannot be satisfied within the current session. The workflow is terminated. No retry is permitted; no auto-escalation to NEEDS_HUMAN is permitted (DEAD is its own terminal state). Recovery requires an explicit new session, not a continuation.

**Lifetime.** Terminal. A DEAD verdict cannot be downgraded to RETRY or upgraded to PASS within the same session. A new session MAY pick up the workflow with a fresh contract; the DEAD audit entry remains immutable as required history (Article X).

**Who can emit.**

- Layer 1 -- when a `dead_when` predicate fires (e.g. `forbidden_pattern_found`, `sandbox_violation`, `retry_budget_exhausted`).
- Layer 2 -- when a hard-block policy fires (e.g. `hardcoded_secrets` in `safety.yaml`).
- Layer 3 -- generally MAY NOT emit DEAD on its own authority; the LLM judge MAY recommend DEAD but the kernel SHOULD route this to NEEDS_HUMAN unless a deterministic predicate corroborates it. (This rule is contract-overridable per rule_set.)
- Layer 4 -- humans MAY emit DEAD to abort a workflow they judge unrecoverable.

**Constitutional anchor.** Article XXIII ("Failure MUST be visible"). DEAD is the explicit, audited counterpart to silent abandonment, which is forbidden.

### 2.5 Verdict precedence

When multiple predicates fire in a single evaluation pass on layer 1 (per `verifier-rules.yaml` evaluation order), precedence is fixed:

```text
step.force_verdict (fixture override)  >  dead_when  >  needs_human_when  >  retry_when  >  pass_when (all-of)  >  fallback_verdict
```

This precedence is enforced by `.ai/cli/core/verifier.py` and is **NOT** contract-overridable. A contract MAY add or restrict the predicate set its rule_set evaluates against; it MAY NOT reorder verdict precedence.

**[non-normative-example]** -- a step that produces a passing test result AND a `forbidden_pattern_found` predicate hit emits DEAD, not PASS. The contract is satisfied in part (tests pass) but violated in part (forbidden pattern present), and the harder verdict wins.

---

## Section 3 -- Pyramid of Judgment Surface

**[normative-description]**

The Pyramid of Judgment is the four-layer escalation ladder that produces every verdict. The Verification Contract MUST declare which layers it authorises, what budget each layer has, and what the layer-emit authorities are.

The pyramid is operational law from `.ai/policies/verifier-rules.yaml` (`pyramid:` block). This Spec restates the layer authorities as load-bearing for the contract surface.

### 3.1 Layer matrix

| Layer | Source | Latency | Authority | Default budget |
|---|---|---|---|---|
| 1 -- deterministic | `.ai/policies/verifier-rules.yaml` rule sets | sub-ms | predicate evaluation against evidence dict | unlimited (cheap) |
| 2 -- policy | `.ai/policies/gates.yaml`, `.ai/policies/safety.yaml`, `.ai/policies/rbac.yaml` | ms | policy gate evaluation; allow / deny | unlimited (declarative) |
| 3 -- gated LLM judge | foundation at `.ai/cli/core/llm_call.py` (sibling-only; not kernel) | seconds | advisory verdict; bounded authority per Section 6 | max 3 calls / session (default), opt-in per session |
| 4 -- human | escalation surface (NEEDS_HUMAN -> human resolution artifact) | minutes -- hours | final authority within the session | unlimited (but slow) |

### 3.2 Resolution order

```text
layer_1_deterministic  ->  layer_2_policy  ->  layer_3_llm_judge  ->  layer_4_human
```

Resolution stops at the first **decisive** verdict, where decisive = `{PASS, RETRY, DEAD}`. NEEDS_HUMAN at layer 1 or layer 2 escalates upward; NEEDS_HUMAN at layer 3 falls through to layer 4; NEEDS_HUMAN at layer 4 is the terminal state until the human acts.

Per `verifier-rules.yaml` `resolution.on_unresolved: NEEDS_HUMAN` -- if all four layers complete without producing a decisive verdict, the synthesised verdict is NEEDS_HUMAN. This rule is **NOT** contract-overridable.

### 3.3 Per-layer authority bounds

**Layer 1 -- deterministic.** Evaluates predicate names against the supplied evidence dict. Predicates are NOT executed code; the engine looks up named predicates in evidence and treats them as truthy / falsy. Layer 1 MAY emit any verdict in the closed set. Layer 1 has no rate limit and no budget consumption.

**Layer 2 -- policy.** Evaluates declarative policy files. Layer 2 outputs a `policy_decision` of `allow` / `deny` / `defer`; the verifier translates this into the verdict set per the rule_set's `pass_when` / `needs_human_when` / `dead_when` mapping. Layer 2 has no rate limit; budget consumption is policy-evaluation cost (effectively zero).

**Layer 3 -- gated LLM judge.** Evaluates by invoking an LLM through `.ai/cli/core/llm_call.py`. Layer 3 is **opt-in per session** (default off in `verifier-rules.yaml: layer_3_llm_judge.enabled: false`). When opted in, the contract MUST declare:

- Maximum calls allowed in this session for this contract (default 3, hard ceiling 5).
- Timeout per call (default 60s).
- Fallback verdict when budget exhausted (`NEEDS_HUMAN` mandatory; this is NOT contract-overridable).
- Whether layer 3 may emit PASS on its own authority for this rule_set (default false; opt-in is operational-tier amendment).

Per Trinity D8 / D13, the kernel MUST NOT itself call layer-3 LLM judge primitives. Layer 3 invocations are made by sibling CLIs that the kernel coordinates. Audit captures the invocation as `llm.invoked` / `llm.completed` events (TRINITY_AUDIT_EVENT_SPEC_V1 Section 3 -- LLM event types).

**Layer 4 -- human.** Evaluates by reading a human-decision artifact (typically a DDD decision packet, a session note, or an out-of-band approval recorded into audit as `operator.approval.recorded` / `operator.rejection.recorded`). Layer 4 has unlimited authority within the session boundary; it MAY upgrade DEAD -> any other verdict, downgrade PASS -> any other verdict, override layer-3 outputs unconditionally. Layer 4 MUST emit through an audited surface (`decided_by: human` in the verdict report).

### 3.4 Per-layer audit obligation

Every layer's verdict MUST be hash-chained into the per-session audit chain via AuditWriter as a `verify.completed` event. The event payload MUST distinguish layer in the `layer:` field (Section 7). Layer 3 invocations additionally produce `llm.invoked` + `llm.completed` event pairs. Layer 4 invocations additionally produce `operator.approval.recorded` / `operator.rejection.recorded` / `operator.amendment.recorded` events.

**[non-normative-example]** -- a code-change step that passes layer-1 deterministic checks emits a single `verify.completed` event with `layer: 1, verdict: PASS`. A code-change step that escalates through all four layers emits one `verify.completed` per attempted layer, each with the layer's verdict; the kernel records the chain so audit replay (TRINITY_AUDIT_EVENT_SPEC_V1 Section 4) can reconstruct the escalation path.

### 3.5 Pyramid layer skipping

A contract MAY restrict which layers are consulted (e.g. "this rule_set is layer-1-only; never escalate to LLM judge"). A contract MAY NOT add layers beyond layer 4, and MAY NOT add custom layers between the four.

Skipping layer 4 (human) is **forbidden** for any rule_set tagged COLD-tier (per TRINITY_VERIFIER_CONTRACT_V1 Section 3 tier model). HOT-tier rule_sets MAY restrict to layer 1 only. WARM-tier rule_sets MAY restrict to layers 1+2. COLD-tier rule_sets MUST permit at minimum layers 1, 2, and 4; layer 3 remains opt-in.

---

## Section 4 -- Verifier-Rules YAML Schema Reference

**[normative-description]**

This Section describes the **shape** of `.ai/policies/verifier-rules.yaml` as it currently exists. This Spec does NOT amend that file; the file is governed by Canonical Policies (rank 2). This Section exists so that contract authors and contract validators have a single canonical reference for the rule_set fields a Verification Contract may bind to.

### 4.1 Top-level shape

```text
version:        string  (currently "1.0")
verdicts:       string[] (closed set: PASS, RETRY, NEEDS_HUMAN, DEAD)
pyramid:        object  (4 layers; per Section 3 of this Spec)
resolution:     object  (order + on_unresolved)
verifier_rules: map<rule_set_id, rule_set_definition>
```

A Verification Contract MUST reference `verifier_rules.<rule_set_id>` by name. Unknown rule_set_id is a contract validation error.

### 4.2 rule_set_definition shape

Each rule_set has the following fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `description` | string | yes | one-line human description of the rule_set's intent |
| `pass_when` | string[] | yes | predicate names; ALL must evaluate true for PASS |
| `retry_when` | string[] | yes | predicate names; first hit emits RETRY |
| `needs_human_when` | string[] | yes | predicate names; first hit emits NEEDS_HUMAN |
| `dead_when` | string[] | yes | predicate names; first hit emits DEAD |
| `fallback_verdict` | enum(PASS/RETRY/NEEDS_HUMAN/DEAD) | yes | verdict when no predicate fires |
| `defaults` | object | optional | default predicate values injected by callers (e.g. `step_done: true`); the engine does not evaluate this -- callers do |

The five rule_sets currently shipping in `verifier-rules.yaml` are:

| rule_set_id | Tier (per TRINITY_VERIFIER_CONTRACT_V1 Section 3) | Surface |
|---|---|---|
| `step_complete` | WARM | generic step-done check; default for ungated steps |
| `code_change` | WARM | code modification verification (test + diff scope + sandbox) |
| `browser_check` | HOT | browser-driven UI assertion verification |
| `deploy_check` | COLD | deployment outcome verification |
| `memory_promote` | WARM | retro -> memory promotion verification |

The Verification Contract for a non-trivial workflow MUST declare which rule_set its acceptance steps bind to. The default mapping (when not declared) is `step_complete`.

### 4.3 Evaluation order (within a single rule_set)

Per the comment block at the top of `verifier-rules.yaml`:

```text
1. step.force_verdict        (fixture override)  -- wins outright
2. dead_when                  (first hit wins)
3. needs_human_when           (first hit wins)
4. retry_when                 (first hit wins)
5. pass_when                  (ALL must be truthy)
6. fallback_verdict           (default: RETRY for most rule_sets)
```

This order is **NOT** contract-overridable. A contract MAY restrict which predicate names are evaluated (sub-setting `pass_when` for a specific contract instance) but MAY NOT reorder the verdict-precedence evaluation.

### 4.4 Predicate semantics

Predicates are **named references**, not executable expressions. The verifier engine looks up each name in the evidence dict supplied by the caller and treats the value as truthy / falsy. The engine NEVER evaluates arbitrary code. This is a hard rule from `verifier-rules.yaml`'s top comment block:

```text
A "predicate" is a string name. The engine looks it up against the
evidence dict supplied by the caller. The engine never executes
arbitrary expressions.
```

Verification Contracts MUST adhere to the same discipline: contract acceptance criteria reference predicate names; they do NOT inline expressions or code.

**[non-normative-example]** -- a contract acceptance entry like `predicate: "tests_pass AND coverage > 80"` is a contract validation error. The right shape is two predicates (`tests_pass` and `coverage_ge_80`), each declared as a separate name and evaluated independently.

### 4.5 Conflict resolution (rule_set selection)

If a step is evaluable by more than one rule_set, the contract MUST pick one explicitly. Multiple rule_set evaluations on a single step are **not** automatically merged. A contract author who wants two rule_sets to apply MUST sequence them (step S1 -> rule_set A; step S1' -> rule_set B) so each verdict is independently recorded.

If the contract leaves a step's rule_set unspecified, the kernel uses `step_complete` as the default. This is permissive on purpose (per the `step_complete.defaults: step_done: true` mechanic) and is **not** suitable for COLD-tier work; COLD-tier work MUST explicitly bind to `deploy_check` or another COLD-tier rule_set.

### 4.6 Contract binding to rule_sets

The Verification Contract envelope (the `verification_contract.json` file produced at `nnn`) carries, per acceptance step, a binding of the form:

```text
acceptance:
  - id: A1
    description: "Tests pass"
    rule_set: "code_change"            # MUST be one of verifier_rules.* or a tagged-new ID
    predicates:                          # subset of rule_set's predicate names
      - tests_pass
      - diff_scope_allowed
    evidence_keys:                       # what evidence the executor MUST supply
      - test_result.json
      - git.diff
    command: "pytest -q"                 # how to run the check
    expect_exit: 0
    required: true
```

The exact field set is fixed by `.ai/schemas/verification_contract.schema.json` (deferred to Phase 3 implementation gogogo). This Spec describes the field set; the schema authoritatively closes additionalProperties.

#### 4.6.1 Precedence-validator clause (enforcement of Section 2.5)

The contract validator (the runtime checker that gates `nnn` PASS, deferred to Phase 3 implementation gogogo per Section 11) MUST enforce the verdict precedence pinned by Section 2.5 (`force_verdict > dead_when > needs_human_when > retry_when > pass_when > fallback_verdict`). Specifically, the validator MUST reject a candidate contract when ANY of the following holds:

- An acceptance entry declares a `predicates:` list whose evaluation would require reordering the precedence chain (e.g. an entry that names both a `dead_when`-class predicate and a `pass_when`-class predicate from the bound rule_set with a per-entry override field intended to flip the verdict to PASS).
- An acceptance entry carries an `on_fire_verdict` mapping that contradicts the rule_set's predicate-class membership (e.g. mapping a `dead_when` predicate to `PASS`, or a `pass_when` predicate to `DEAD`).
- An acceptance entry attempts to declare a custom `precedence_override:` field; this field is forbidden at the schema level (`additionalProperties: false` in `verification_contract.schema.json`).
- An acceptance entry binds to a rule_set whose `fallback_verdict` differs from the contract's declared `expected_terminal_verdict` AND no rationale is provided in `rationale_for_fallback_divergence`.

Validator outcomes:

- Detected violation -> reject contract at `nnn` with a structured error referencing this clause and Section 2.5.
- The `nnn.proposed` audit event MUST record the rejection reason in its payload (`rejection_reason: "precedence_violation"` plus the offending acceptance ID).
- Rejection is non-recoverable within the same `nnn` attempt; the planner MUST resubmit a corrected contract (which produces a fresh `nnn.proposed` event).

This clause closes the gap that Section 2.5 declared verdict precedence non-overridable but did not pin enforcement. The schema field-level enforcement (`additionalProperties: false`) and the validator-level enforcement (this clause) together make the rule operationally inspectable.

---

## Section 5 -- Policy Boundary Contract

**[normative-description]**

The Verification Contract is consumed by the Verifier; the Verifier in turn **queries** the Policy Engine (Phase 5, layer 2 of the Pyramid). This Section defines the contract surface between Verifier and Policy.

### 5.1 Policy is queried, never authored

The Verifier MAY:

- Read `.ai/policies/safety.yaml` (risk scoring + secret patterns + hard blocks)
- Read `.ai/policies/gates.yaml` (gate definitions + commands)
- Read `.ai/policies/rbac.yaml` (when present; role-based access control)
- Submit a policy-evaluation request to the Policy Engine and receive `allow` / `deny` / `defer`

The Verifier MUST NOT:

- Write to any file under `.ai/policies/**`
- Mutate the in-memory policy cache
- Synthesise its own gate definitions
- Override a policy `deny` into a verifier `PASS` (the precedence is enforced by Kernel: layer 2 `deny` -> verifier `NEEDS_HUMAN` minimum, often `DEAD`)

This boundary mirrors Article IV's role separation. The Verifier validates artifacts; the Policy Engine declares allow / deny rules. Conflating the two collapses the role and is forbidden.

### 5.2 Policy-evaluation request shape

The request from Verifier to Policy is a structured envelope (deferred schema; described informally here):

| Field | Type | Meaning |
|---|---|---|
| `gate_name` | string | which gate to evaluate (e.g. `secrets`, `tests`, `scope`) |
| `evidence` | object | the same evidence dict the Verifier received |
| `tier` | enum(HOT/WARM/COLD) | risk tier from the contract |
| `actor` | string | which kernel actor is requesting evaluation |
| `session_id` | string | per-session correlation |

The response is a structured decision:

| Field | Type | Meaning |
|---|---|---|
| `decision` | enum(allow/deny/defer) | policy verdict |
| `reason` | string | human-readable |
| `gate_name` | string | echoed back |
| `audit_event_ref` | object | reference to the `policy.violation.detected` event when decision != allow |

### 5.3 Translation table -- policy decision to verifier verdict

Per Verifier Pyramid layer 2:

| Policy decision | Verifier verdict (default) | When NEEDS_HUMAN instead | When DEAD instead |
|---|---|---|---|
| `allow` | continue layer 1 / pass layer 2 | n/a | n/a |
| `deny` | NEEDS_HUMAN (most cases) | always when policy reason is overridable by human | when policy reason matches `safety.yaml: hard_blocks` |
| `defer` | RETRY | when defer reason explicitly says "needs human input" | n/a |

The contract MAY tighten this table (e.g. "treat all `deny` as DEAD") but MAY NOT loosen it (e.g. "treat `deny` as PASS" is a constitutional violation per Article XIV).

### 5.4 Policy versioning and contract binding

The Verification Contract MUST record, at the time it is sealed (`nnn` PASS), a snapshot reference to BOTH the policy versions AND the verifier-rules version it was validated against:

```text
policy_snapshot:
  safety_yaml_sha256:         "...."
  gates_yaml_sha256:          "...."
  rbac_yaml_sha256:           "...."   # when present
  verifier_rules_yaml_sha256: "...."   # MANDATORY (V1.1)
```

The `verifier_rules_yaml_sha256` field is mandatory because the rule_set definitions, predicate names, and verdict precedence semantics that the contract binds to (Sections 2-4) are sourced from `.ai/policies/verifier-rules.yaml`. A drift in that file silently changes the meaning of every contract acceptance entry that names one of its rule_sets; treating the file as out-of-snapshot would break the same "no silent drift" property that the policy_snapshot was introduced to guarantee.

If the policy files OR the verifier-rules file are mutated mid-session (e.g. by a human directly editing `safety.yaml` or adding a new predicate to `verifier-rules.yaml`), the recorded snapshot still governs the contract; re-evaluation against the new files requires a contract amendment (`plan.amended` event) plus re-`nnn`. This applies symmetrically to all four files in the snapshot.

This rule prevents **silent policy drift** AND **silent rule-set drift**: an executor cannot quietly benefit from either a policy relaxation or a rule-set redefinition that occurred after the contract was sealed.

### 5.5 Policy hard-blocks override the contract

The `hard_blocks` section of `safety.yaml` (currently: `hardcoded_secrets`, `private_key`) is a **non-overridable** safety floor. The contract MUST NOT declare that any hard-block predicate may be downgraded; an attempt to do so is a contract validation error.

**[non-normative-example]** -- a contract acceptance entry with `predicate: forbidden_pattern_found, on_fire_verdict: PASS` is rejected at `nnn`: the verdict precedence (Section 2.5) and the policy hard-block rule (this section) jointly forbid PASS in the presence of a forbidden-pattern hit.

---

## Section 6 -- Gated LLM Judge Envelope

**[normative-description]**

Layer 3 (gated LLM judge) is the **last automated resort** before human escalation. Its use is heavily restricted by audit, budget, and authority bounds. This Section details the envelope an LLM-judge invocation MUST be wrapped in.

### 6.1 When layer 3 is allowed

Layer 3 is permitted only when ALL of:

1. The session has explicitly opted in to layer 3 (default off per `verifier-rules.yaml: layer_3_llm_judge.enabled: false`).
2. The contract for the relevant step authorises layer 3 escalation for the rule_set in question.
3. The session's layer-3 budget is not exhausted (default 3 calls per session, hard ceiling 5).
4. The rule_set is NOT tagged COLD-tier with `layer_3_authority: deny` (the default for COLD).
5. The kernel is the invocation initiator. (Per D8 / D13, the kernel does NOT itself call llm_call.py; it coordinates a sibling CLI to do so. The "initiator" here means the kernel marked the call as `decided_by: layer_3_llm_judge` in the audit event ahead of the sibling invocation.)

Failing any of (1)-(5) MUST result in immediate escalation to layer 4 (NEEDS_HUMAN) without invoking the LLM.

### 6.2 Per-call budget

Per `verifier-rules.yaml: layer_3_llm_judge`:

```text
max_calls_per_session: 3      (default; hard ceiling 5)
timeout_seconds:       60     (default)
fallback_verdict:      NEEDS_HUMAN
```

The contract MAY tighten any of these (lower max, shorter timeout). The contract MAY NOT raise `max_calls_per_session` above 5; that is a constitutional ceiling. The contract MAY NOT change `fallback_verdict` away from NEEDS_HUMAN; that is a non-overridable safety floor.

### 6.3 Required audit fields

A layer-3 invocation MUST emit BOTH of the following events to the per-session AuditWriter chain:

**Event: `llm.invoked`** -- payload required fields:

| Field | Type | Meaning |
|---|---|---|
| `verdict_attempt_id` | string | UUID4 hex; correlates the invocation to its `verify.completed` event |
| `rule_set` | string | which verifier rule_set this invocation is judging |
| `session_layer3_call_index` | integer | 1-indexed; consumed budget pre-call |
| `session_layer3_budget_remaining` | integer | post-decrement remaining budget |
| `model_identity` | string | model + version actually invoked (e.g. `claude-opus-4-7`) |
| `prompt_sha256` | string | SHA-256 of the canonical prompt sent to the model |
| `actor` | string | sibling CLI name (e.g. `agent:executor_helper`) |

**Event: `llm.completed`** -- payload required fields:

| Field | Type | Meaning |
|---|---|---|
| `verdict_attempt_id` | string | matches the `llm.invoked` field |
| `latency_ms` | integer | wallclock invocation latency |
| `proposed_verdict` | enum(PASS/RETRY/NEEDS_HUMAN/DEAD) | what the LLM proposed |
| `accepted_verdict` | enum(PASS/RETRY/NEEDS_HUMAN/DEAD) | what the kernel accepted (may differ when layer-3 PASS authority is denied) |
| `confidence` | float | 0.0 -- 1.0; advisory only |
| `response_sha256` | string | SHA-256 of the canonical response body |
| `notes` | string | free-text rationale; required when `proposed_verdict != accepted_verdict` |

The full prompt and response bodies live in the per-session capture transaction (TRINITY_VERIFIER_CONTRACT_V1 Section 5 -- `capture_refs`). Audit carries the hashes; capture carries the bodies.

### 6.4 Refusal behaviour when budget is exhausted

When `session_layer3_call_index > max_calls_per_session`, the kernel MUST:

1. NOT invoke the LLM.
2. Emit a single `verify.completed` event with `verdict: NEEDS_HUMAN, layer: 3, notes: "layer_3_budget_exhausted"`.
3. Pause the workflow at the layer-4 boundary.
4. Surface a NEEDS_HUMAN signal to the operator via the configured transport (per Article XV; transport delivers, does not approve).

The kernel MUST NOT silently fall back to PASS; MUST NOT silently succeed; MUST NOT silently retry layer 3 from a different code path. Budget exhaustion is a hard stop for this layer.

### 6.5 Refusal behaviour when the LLM call fails

When the LLM call errors (timeout, network failure, malformed response):

1. The `llm.completed` event is still emitted, with `accepted_verdict: NEEDS_HUMAN, notes: "<error_class>: <error_message>"`.
2. The budget IS consumed (the failed call counts against `max_calls_per_session`).
3. The verdict resolves to NEEDS_HUMAN per the `fallback_verdict` rule.

This rule prevents a contract author from designing a "free retry" by counting only successful calls.

### 6.6 Layer-3 PASS authority

By default, layer 3 MAY downgrade verdicts but MAY NOT upgrade an indeterminate evidence set into PASS on its own authority. To grant layer-3 PASS authority for a specific rule_set, the contract MUST declare:

```text
acceptance:
  - id: A3
    rule_set: "browser_check"
    layer_3_authority: "may_emit_pass"   # requires operational-tier amendment justification
```

The default value when unspecified is `layer_3_authority: "downgrade_only"`. Granting `may_emit_pass` requires:

- Rule_set is HOT-tier (no persisted side-effect)
- Contract acceptance entry includes `rationale_for_llm_pass_authority` field with non-empty justification
- Audit event for the `nnn` PASS records the elevation as `layer_3_authority_elevation`

The `rationale_for_llm_pass_authority` field is load-bearing in the contract envelope (the `verification_contract.json` produced at `nnn`) and MUST be persisted at the same nesting level as the `layer_3_authority` field of the acceptance entry. The contract validator MUST reject any acceptance entry that declares `layer_3_authority: may_emit_pass` without a co-located non-empty `rationale_for_llm_pass_authority`. The `verification_contract.schema.json` (deferred to Phase 3 implementation gogogo per Section 11) MUST encode this co-occurrence as a JSON Schema `dependentRequired` rule (or equivalent), so the dependency is enforced at schema-validation time AND at contract-validator time.

For COLD-tier rule_sets, layer-3 PASS authority is **forbidden** -- contracts attempting to grant it are rejected at validation.

**[non-normative-example]** -- a contract for a deployment workflow that says `rule_set: deploy_check, layer_3_authority: may_emit_pass` is rejected at `nnn` with reason "COLD-tier rule_set may not grant LLM PASS authority (Article XIII, Article XVI)".

---

## Section 7 -- Audit Emission Requirements

**[normative-description]**

Every Verification Contract event flows through the per-session AuditWriter into the SQLite chain at `<session>/CAPTURE/capture.sqlite` (per TRINITY_AUDIT_EVENT_SPEC_V1). This Section pins the event types, required fields, and hash-chain integration discipline for verification-contract-related events.

### 7.1 Event types touched by the Verification Contract

| Event type | When emitted | Emitter |
|---|---|---|
| `nnn.proposed` | contract drafted at `nnn` | kernel |
| `nnn.passed` | contract sealed at `nnn` PASS | kernel |
| `plan.amended` | contract amended mid-session | kernel |
| `verify.invoked` | a verification round begins (per step or per gate) | kernel |
| `verify.completed` | verdict emitted | kernel (layers 1-2-3) or human-action-recorder (layer 4) |
| `policy.violation.detected` | layer-2 deny | kernel (proxy for Policy Engine) |
| `llm.invoked` | layer-3 LLM call begins | sibling CLI |
| `llm.completed` | layer-3 LLM call ends | sibling CLI |
| `operator.approval.recorded` | layer-4 human approval | kernel (recording the operator's signal) |
| `operator.rejection.recorded` | layer-4 human rejection | kernel |
| `operator.amendment.recorded` | layer-4 human amendment to contract | kernel |

All event types above are members of the canonical event-type registry in TRINITY_AUDIT_EVENT_SPEC_V1 Section 3. Adding a new event type touching the contract surface is an **operational-tier** amendment under Addendum v1.0.4 XXIX.2.

### 7.2 Required `verify.completed` payload fields

The `verify.completed` event is the canonical carrier of a Verifier verdict. Its `payload_json` MUST include at minimum:

| Field | Type | Meaning |
|---|---|---|
| `verdict` | enum(PASS/RETRY/NEEDS_HUMAN/DEAD) | the verdict (Section 2) |
| `decided_by` | enum(layer_1/layer_2/layer_3_llm_judge/human/kernel/sibling) | who decided; `kernel` when layer 1+2 are merged in a single decision; `human` for layer 4 |
| `layer` | integer (1/2/3/4) | which pyramid layer was decisive |
| `evidence_path` | string | relative path to the evidence file or directory (under `<session>/`) |
| `contract_id` | string | the verification_contract envelope ID this verdict gates |
| `contract_revision` | integer | revision counter; bumped at every `plan.amended` |
| `acceptance_id` | string | which acceptance entry (e.g. `A1`, `A3`) this verdict resolves; nullable for session-level verdicts |
| `rule_set` | string | which rule_set ID was bound to this acceptance entry |
| `report_path` | string | relative path to the `verifier_report.json` file |
| `report_hash` | string | SHA-256 of the report file (hex) |
| `capture_refs` | string[] | ULIDs of `captures.capture_id` rows that supplied evidence (per TRINITY_VERIFIER_CONTRACT_V1 Section 5) |

The `decided_by` field is load-bearing for downstream organs: DDD uses it to refuse promotion of COLD steps on layer-3 verdicts alone (TRINITY_VERIFIER_CONTRACT_V1 Section 6).

**Layer-2 propagation note (V1.1).** When the decisive layer is layer 2 (policy) AND the `policy_decision` was `deny` or `defer`, the `verify.completed` payload MUST additionally carry a `policy_violation_ref` field whose value is the `event_id` (or equivalent canonical reference) of the corresponding `policy.violation.detected` event emitted earlier in the chain (per Section 5.2's `audit_event_ref`). This makes the propagation explicit and audit-replayable: a downstream consumer reading `verify.completed` MUST be able to walk back to the originating policy violation without scanning the chain. Where no policy violation occurred (layer-1 or layer-3 paths, or layer-2 `allow`), the field is absent (NOT null). The reverse pointer (`policy.violation.detected.payload.verify_completed_ref`) is OPTIONAL and informational; the forward pointer on `verify.completed` is the load-bearing one.

### 7.3 Hash chain integration

Per TRINITY_AUDIT_EVENT_SPEC_V1 Section 2.1, every event row is hashed into the per-session chain:

```text
event_for_hash = {
  event_id, schema_version, session_id, seq, event_type, ritual,
  capture_id, actor, ts_utc, payload_hash, prev_hash
}
hash = sha256(canonical_json(event_for_hash))
```

The Verification Contract events inherit this discipline without modification. Specifically:

- `verify.completed` events MUST be appended under `BEGIN IMMEDIATE` so `seq` is claimed atomically.
- The `payload_hash` is `sha256(payload_json)` where `payload_json` is canonicalised (`sort_keys=True, separators=(",",":")`).
- The chain MUST be replayable via `ai audit verify-chain --session <sid>` (per TRINITY_AUDIT_EVENT_SPEC_V1 Section 5) without modification.

A `verify.completed` event whose `report_hash` does not match the on-disk report file is a chain-integrity violation; `verify-chain` returns exit 2 with reason `verifier_report_hash_mismatch`.

### 7.4 Legacy ndjson mirroring

The legacy global `.ai/audit/events.ndjson` (5-field shape per TRINITY_AUDIT_EVENT_SPEC_V1 Section 2.2) MAY receive a mirrored row for backward compatibility:

```text
timestamp:  <ts_utc>
type:       <event_type>          # e.g. "verify.completed"
prev_hash:  <legacy chain prev>
details:    <payload_json>        # lossy: object, not canonical string
hash:       <legacy chain hash>
```

The legacy mirror is **NOT** the source of truth; consumers MUST read the per-session chain first. Mirror writes are kernel-side and do not impose contract obligations on the Verifier.

### 7.5 Audit emission for contract amendments

When a contract is amended mid-session (e.g. plan extended to add a new acceptance entry), the kernel MUST emit:

1. `plan.amended` event with payload describing the diff (before/after acceptance arrays, contract_revision bump).
2. Any verdict already emitted against the old contract revision is **NOT** invalidated; it remains in the chain with its original `contract_revision`. The new revision starts a fresh evaluation cycle for affected acceptance entries.

This rule preserves Article X ("Audit history MUST NOT be silently rewritten. Corrections MUST create new audit entries.").

**[non-normative-example]** -- session S has contract revision 1 with acceptance entries A1, A2 both PASSed; operator amends to add A3. Audit chain shows: verify.completed(A1, rev=1, PASS) -> verify.completed(A2, rev=1, PASS) -> plan.amended(rev 1 -> 2, added A3) -> verify.completed(A3, rev=2, PASS). The original A1 / A2 verdicts are NOT re-emitted; they continue to gate the workflow at their original revision.

---

## Section 8 -- Conformance Test Matrix

**[normative-description]**

This Section enumerates the test surface that any Verification Contract implementation MUST satisfy. The matrix crosses each verdict against each layer and pins the expected behaviour. Tests are pseudocode-described here; concrete Python test patterns live under `.ai/cli/tests/test_verification_contract*.py` (deferred to Phase 3 implementation gogogo).

### 8.1 Verdict x layer matrix

| Verdict | Layer 1 (deterministic) | Layer 2 (policy) | Layer 3 (LLM judge) | Layer 4 (human) |
|---|---|---|---|---|
| PASS | ALL `pass_when` predicates true; no higher-priority predicate fires | policy `allow` and no defer | only when contract grants `may_emit_pass` AND budget remains AND rule_set permits | always permitted; supersedes lower layers |
| RETRY | any `retry_when` predicate fires AND no higher-priority predicate fires | policy `defer` for non-human reason | default LLM downgrade; consumes 1 budget unit | always permitted; resets retry counter at human option |
| NEEDS_HUMAN | any `needs_human_when` predicate fires | policy `deny` with `human_overridable: true` | budget-exhausted fallback; always when contract denies layer-3 PASS | terminal until human acts |
| DEAD | any `dead_when` predicate fires | policy `deny` matching `hard_blocks` | RECOMMEND only; kernel routes to NEEDS_HUMAN unless layer 1 corroborates | always permitted (terminates session) |

### 8.2 Required test cases per cell

For each cell in 8.1, conformance tests MUST cover at minimum:

**Cell PASS x layer 1.** Test that a step with all `pass_when` predicates true and no other predicate fires emits `verdict: PASS, layer: 1, decided_by: kernel`. Test that the `verify.completed` event records `report_hash` matching the on-disk file. Test that the audit chain replay succeeds.

**Cell RETRY x layer 1.** Test that `test_failed: true` triggers RETRY. Test that the retry counter increments. Test that `retry_count == retry_budget` causes the next failure to escalate to DEAD via `retry_budget_exhausted`. Test that the contract revision is preserved across retries.

**Cell NEEDS_HUMAN x layer 1.** Test that `production_write: true` triggers NEEDS_HUMAN. Test that the workflow pauses. Test that no automated action progresses until a human-decision artifact lands. Test that the audit chain shows `decided_by: layer_1, layer: 1, verdict: NEEDS_HUMAN`.

**Cell DEAD x layer 1.** Test that `forbidden_pattern_found: true` triggers DEAD. Test that subsequent retry attempts are refused. Test that the audit chain shows DEAD as terminal. Test that re-opening the workflow requires a new session ID.

**Cell PASS x layer 2.** Test that a policy `allow` with no layer-1 escalation passes through. Test that the `policy_snapshot` recorded at `nnn` matches the policy version at evaluation time.

**Cell RETRY x layer 2.** Test that policy `defer: "evidence resubmission required"` translates to RETRY. Test that the retry budget consumption rule applies.

**Cell NEEDS_HUMAN x layer 2.** Test that policy `deny` with `human_overridable: true` translates to NEEDS_HUMAN. Test that the `policy.violation.detected` event is emitted with the gate name and reason.

**Cell DEAD x layer 2.** Test that `safety.yaml: hard_blocks: hardcoded_secrets` regex match translates to DEAD. Test that the contract CANNOT downgrade this to PASS (validation error at `nnn`).

**Cell PASS x layer 3.** Test that an LLM judge call returns PASS AND the contract grants `may_emit_pass` AND budget remains -> verdict accepted as PASS. Test that the `llm.invoked` and `llm.completed` events are both emitted with matching `verdict_attempt_id`.

**Cell RETRY x layer 3.** Test that an LLM judge call returns RETRY -> verdict accepted; budget decremented by 1. Test that the kernel records `accepted_verdict == proposed_verdict` in this case.

**Cell NEEDS_HUMAN x layer 3.** Test that budget exhaustion (`session_layer3_call_index > max_calls_per_session`) triggers NEEDS_HUMAN WITHOUT invoking the LLM. Test that the `verify.completed` event records `notes: "layer_3_budget_exhausted"`.

**Cell DEAD x layer 3.** Test that an LLM judge call recommending DEAD without layer-1 corroboration is rerouted to NEEDS_HUMAN. Test that the `accepted_verdict` differs from `proposed_verdict` and `notes` field carries the rerouting rationale.

**Cell PASS x layer 4.** Test that a human-recorded approval (`operator.approval.recorded` event) translates to PASS. Test that the `verify.completed` event carries `decided_by: human`.

**Cell RETRY x layer 4.** Test that a human-recorded retry signal translates to RETRY and resets the retry counter (human discretion).

**Cell NEEDS_HUMAN x layer 4.** Test that a human deferral remains NEEDS_HUMAN; subsequent automated layers are not re-invoked until the human emits a definitive verdict.

**Cell DEAD x layer 4.** Test that a human-recorded abort translates to DEAD. Test that this DEAD is terminal and a new session is required for any continuation.

### 8.3 Cross-cutting tests

**Contract validation at `nnn`.** Test that:

- A contract referencing an unknown `rule_set` is rejected.
- A contract granting layer-3 PASS authority on a COLD-tier rule_set is rejected.
- A contract attempting to downgrade a `safety.yaml: hard_blocks` predicate is rejected.
- A contract with no `policy_snapshot` is rejected.
- A contract with malformed acceptance entries (missing `id`, `description`, `rule_set`, `evidence_keys`) is rejected.

**Contract precondition for `gogogo`.** Test that:

- `gogogo` refuses to run when no `verification_contract.json` is present in session state.
- `gogogo` refuses to run when the contract's `contract_revision` mismatches the plan envelope.
- `gogogo` refuses to run when the `policy_snapshot` SHAs do not match current `.ai/policies/` files (unless `--accept-policy-drift` flag is set, which itself requires human approval).

**Snapshot drift detection (V1.1).** Test that the snapshot drift check covers ALL four snapshot fields defined in Section 5.4 -- `safety_yaml_sha256`, `gates_yaml_sha256`, `rbac_yaml_sha256` (when present), AND `verifier_rules_yaml_sha256`. Specifically:

- A test MUST exercise drift on each of the four files independently (mutate one file post-`nnn`, run `gogogo`, assert refusal with `policy_snapshot_drift` reason naming the drifted file).
- A test MUST cover the `verifier-rules.yaml` drift case end-to-end: add a new predicate to a bound rule_set after `nnn` PASS, then assert that `gogogo` refuses with `verifier_rules_drift_detected` and surfaces the file's old vs new SHA-256.
- A test MUST cover the `--accept-policy-drift` flag path: assert that the flag does NOT bypass `verifier_rules_yaml_sha256` drift unless explicitly extended to `--accept-rule-set-drift` (a separate human-approved flag); this prevents conflating policy-text drift with rule-semantic drift.
- A test MUST assert that drift detection emits a structured audit entry (`gogogo.refused` event with `reason: snapshot_drift, drifted_files: [...]`) before the kernel exits non-zero, so audit-replay can reconstruct the refusal.

**Audit chain integrity.** Test that:

- Every `verify.completed` event has a corresponding `verifier_report.json` whose `sha256` matches `report_hash`.
- Every layer-3 verdict has a paired `llm.invoked` + `llm.completed` event with matching `verdict_attempt_id`.
- Every layer-4 verdict has a corresponding `operator.*.recorded` event in the chain with matching timestamp.
- `ai audit verify-chain --session <sid> --strict` returns exit 0 across the test suite.

**Contract amendment.** Test that:

- `plan.amended` events bump `contract_revision` monotonically.
- Old verdicts at lower revisions are NOT mutated.
- New acceptance entries added at higher revisions are independently evaluated.

### 8.4 Test fixture conventions

Test fixtures supply the evidence dict directly to the verifier engine; they MUST NOT depend on real executor runs. The `step.force_verdict` mechanism (per `verifier-rules.yaml` evaluation order) is a fixture-only override and MUST NOT be used in production session runs.

The conformance test runner is `pytest`, invoked via `cd .ai && python3 -m pytest cli/tests -q` (per CLAUDE.md Quick Run Commands).

**[non-normative-example]** -- a fixture for cell `RETRY x layer 1` supplies `evidence = {"step_done": false, "test_failed": true}` and expects the verifier to emit `verdict: RETRY, layer: 1, decided_by: kernel`. The fixture asserts that `report_path` exists, `report_hash` matches, and the audit event is appended with `seq = previous + 1`.

---

## Section 9 -- Versioning & Article XXIX Amendment Protocol

**[normative-description]**

The Verification Contract Spec is itself amendment-bearing. This Section pins the per-tier rules for amending V1 -> V1.1 -> V2 under Article XXIX (operationalised by Addendum v1.0.4).

### 9.1 What constitutes a breaking change

A change to this Spec is **breaking** (constitutional-tier per Addendum v1.0.4 XXIX.3) when ANY of:

- Adding, removing, or renaming a member of the verdict set (Section 2)
- Reordering the four pyramid layers (Section 3)
- Removing a required field from `verify.completed` payload (Section 7.2)
- Loosening any "MUST NOT" rule into "SHOULD NOT" or weaker
- Removing a non-overridable safety floor (e.g. `fallback_verdict: NEEDS_HUMAN` for layer 3)
- Changing the precedence of verdict evaluation (Section 2.5)
- Removing the requirement that contracts bind to a `rule_set` from `.ai/policies/verifier-rules.yaml`
- Changing how `decided_by` is computed in a way that affects DDD's gate-promotion logic

A change is **operational-tier** (Addendum v1.0.4 XXIX.2) when:

- Adding a new optional field to `verify.completed` payload
- Adding a new event type to Section 7.1 (with full proposal / rationale / impact analysis sections)
- Tightening a "SHOULD" into a "MUST" (which strictly narrows behaviour)
- Adding new required test cases to the conformance matrix
- Adjusting the layer-3 default budget (between the documented floor of 1 and the constitutional ceiling of 5)
- Renaming a non-load-bearing field (with migration shim documented)

A change is **editorial-tier** (Addendum v1.0.4 XXIX.1) when:

- ASCII normalisation
- Typo fix
- Link-target update to the same canonical document
- Formatting that does not alter the rule

### 9.2 Required artifacts per amendment

Per Article XXIX (verbatim):

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

This Spec inherits the discipline. The per-tier translation is:

| Tier | Proposal | Rationale | Impact analysis | Human approval | Version bump | Audit entry |
|---|---|---|---|---|---|---|
| Editorial (XXIX.1) | inline in commit body | inline in commit body (1-3 sentences max) | not required | operator commit suffices | patch (V1.0 -> V1.0.1) | `constitution.amended.editorial` event |
| Operational (XXIX.2) | dedicated section in addendum file or in this Spec body | full prose section | full prose section (surface area, risk, rollback) | DDD gate with `decided_by: human` audit event | minor (V1 -> V1.1) | `constitution.amended.operational` event |
| Constitutional (XXIX.3) | dedicated addendum file | full prose section | full prose section + strategic rationale (named principle preserved) | DDD gate with `decided_by: human` AND linked session id | major (V1 -> V2) | `constitution.amended.constitutional` event |

The audit event format is pinned by Addendum v1.0.4 XXIX.5; required fields are `actor`, `diff_sha256`, `tier`, `rationale_ref`.

### 9.3 Version-bump procedure

The Spec frontmatter `version:` field MUST be bumped per the table in 9.2. Examples:

- V1.0 -> V1.0.1 -- typo fix in Section 3 example sentence; editorial tier; commit message rationale.
- V1.0 -> V1.1 -- adds a new optional `confidence_floor` field to `verify.completed` payload; operational tier; new prose section in this Spec body documenting the field.
- V1.0 -> V2.0 -- removes `RETRY` from the verdict set; constitutional tier; new addendum `TRINITY_VERIFICATION_CONTRACT_ADDENDUM_V1_0_X.md`; this Spec is superseded; the `supersedes:` frontmatter of V2.0 references V1.0.

Prior versions remain inspectable in git history; the on-disk file is the most recent ratified version. A V1.0 reader who needs to inspect a V0.9 draft consults `git show <sha>:docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md`.

### 9.4 Trace-to-failure obligation

Per Addendum v1.0.4 XXIX.4:

```text
Editorial: trace is not required.
Operational: MUST trace to observed failure / recurring friction /
             measurable risk / autopilot safety requirement.
Constitutional: MUST trace to the above AND carry strategic rationale
                naming the constitutional principle being preserved or extended.
```

Operational and constitutional amendments to this Spec MUST cite a concrete trace -- a session id, an audit event id, a memory-anchor reference, or a named safety requirement. "It seemed like a good idea" is NOT a trace.

**[non-normative-example]** -- "Operational amendment V1.1: add `confidence_floor` field to layer-3 verdicts. Trace: session sss-2026-05-22-llm-overconfidence-incident, audit event evt_a1b2c3d4, where a layer-3 LLM emitted PASS with reported confidence 0.41 and the verdict was accepted because no floor existed. Strategic rationale: preserves Article III (AI cannot govern itself) by preventing low-confidence LLM PASS from substituting for verifier judgement."

### 9.5 Classification rule (tiebreaker)

Per Addendum v1.0.4 XXIX.6:

```text
When in doubt, classify upward.
Misclassification toward higher tier (e.g. editorial -> operational)
is acceptable. Misclassification toward lower tier is a
constitutional violation requiring retroactive reclassification.
```

A Spec amendment that touches verdict semantics, layer authority, or audit-event payload is **always at least operational**. When unclear whether a change is operational or constitutional, classify as constitutional and revisit downward only via explicit Addendum.

### 9.6 Forbidden amendment patterns

The following amendments to this Spec are FORBIDDEN -- they cannot be ratified at any tier without first amending the parent Constitution (which itself requires Article XXIX procedure on the Constitution):

- Allowing AI to self-certify completion (Article III)
- Allowing the Verifier to mutate executor artifacts (Article IV, Article XVI)
- Allowing the Verifier to operate without explicit invocation (Article XX)
- Allowing the Pyramid layers to be bypassed by transport-layer overrides (Article XV)
- Allowing audit history to be silently rewritten (Article X)
- Allowing successful state transition without required artifact (Article XXIV)

A proposed Spec amendment matching any of the above is a constitutional violation independent of the Spec; it is rejected at proposal time.

---

## Section 10 -- Glossary Cross-Refs

**[normative-description]**

This Section cross-references terms used in this Spec to the canonical glossary at `docs/specs/12_GLOSSARY.md`, and defines new terms introduced here that MUST be added to the glossary in a sibling editorial amendment.

### 10.1 Existing glossary terms (canonical -- consult `12_GLOSSARY.md`)

| Term | Used in Sections | Glossary entry |
|---|---|---|
| Artifact | 1, 2, 5, 7, 9 | Article 0 Section 1; `12_GLOSSARY.md` Artifact |
| Verification | 1, all | Article 0 Section 2; `12_GLOSSARY.md` Verification |
| Completion | 1, 2 | Article 0 Section 3; `12_GLOSSARY.md` Completion |
| Authority | 1, 3, 5, 6 | Article 0 Section 4; `12_GLOSSARY.md` Authority |
| Canonical | 0, 4, 5 | Article 0 Section 5; `12_GLOSSARY.md` Canonical |
| Verdict | 2, all | this Spec Section 2 (authoritative for the verdict set); `12_GLOSSARY.md` Verdict |
| Pyramid of Judgment | 3, 6 | `verifier-rules.yaml: pyramid:`; `12_GLOSSARY.md` Pyramid |
| Tier (HOT / WARM / COLD) | 3, 5, 6 | TRINITY_VERIFIER_CONTRACT_V1 Section 3; `12_GLOSSARY.md` Tier |
| Per-session audit chain | 7 | TRINITY_AUDIT_EVENT_SPEC_V1 Section 2; `12_GLOSSARY.md` Audit chain |
| Capture (RecordProxy) | 6, 7 | TRINITY_AUDIT_EVENT_SPEC_V1 Section 3; `12_GLOSSARY.md` Capture |
| Plan envelope | 4, 5, 7 | `02_VERIFIER_SPEC.md`; `12_GLOSSARY.md` Plan envelope |
| Acceptance entry | 4, 7, 8 | `02_VERIFIER_SPEC.md`; `12_GLOSSARY.md` Acceptance |
| `decided_by` | 5, 6, 7, 8 | TRINITY_VERIFIER_CONTRACT_V1 Section 5; `12_GLOSSARY.md` decided_by |
| Hash chain | 7 | Article X; TRINITY_AUDIT_EVENT_SPEC_V1 Section 2.1; `12_GLOSSARY.md` Hash chain |

### 10.2 New terms introduced by this Spec

The following terms are introduced in V1.0 of this Spec and MUST be added to `12_GLOSSARY.md` via a sibling editorial amendment (Addendum v1.0.4 XXIX.1):

**Verification Contract.** The artifact produced at `nnn` declaring scope, acceptance entries, evidence requirements, rule_set bindings, retry budget, layer-3 authority, policy snapshot, and human-gate policy. Frozen at `nnn` PASS; consulted by `gogogo`, `verify`, `ddd`, `rrr`, `close`. The Verification Contract is the operational instantiation of Article III's "verification" requirement.

**Contract revision.** Monotonic counter on the Verification Contract envelope. Bumped on every `plan.amended` event. Verdicts are tagged with the revision they were emitted against; old-revision verdicts are NOT invalidated by amendments at higher revisions.

**Policy snapshot.** SHA-256 hashes of `.ai/policies/safety.yaml`, `gates.yaml`, and `rbac.yaml` (when present) at the moment the contract was sealed. Stored in the contract envelope. Mismatch with current policy files at `gogogo` time blocks execution unless explicit policy-drift acceptance is recorded.

**Layer-3 PASS authority.** Per-rule_set, per-contract grant that permits layer-3 LLM judge to emit PASS on its own authority. Default `downgrade_only`; explicit opt-in `may_emit_pass` requires operational-tier amendment justification and is forbidden for COLD-tier rule_sets.

**Verdict precedence.** The fixed evaluation order within a single rule_set (Section 2.5): `force_verdict > dead_when > needs_human_when > retry_when > pass_when > fallback_verdict`. NOT contract-overridable.

**Decisive verdict.** A verdict in `{PASS, RETRY, DEAD}`; a decisive verdict halts pyramid escalation. NEEDS_HUMAN is the explicit non-decisive verdict at layers 1-3 (and is terminal at layer 4 until a human acts).

**Trace-to-failure.** The Article-XXIX-operationalised obligation that operational and constitutional amendments cite a concrete trace (session id, audit event, memory anchor, named safety requirement). Editorial amendments are exempt.

**Forbidden amendment pattern.** A class of amendment that cannot be ratified at any tier without first amending the parent Constitution. Enumerated in Section 9.6 of this Spec.

### 10.3 Cross-references to other Trinity v2 specs

| Spec | Relationship to this Spec |
|---|---|
| `TRINITY_VERIFIER_CONTRACT_V1.md` (Phase 8) | Pins the verifier *report shape*; this Spec pins the *contract shape* that the report is against. Read both together. |
| `TRINITY_AUDIT_EVENT_SPEC_V1.md` (Phase 10) | Pins the audit event shape and registry; Section 7 of this Spec depends on it. |
| `TRINITY_DDD_HUMAN_GATE_SPEC_V1.md` (Phase 11) | Consumes `decided_by` from `verify.completed`; refuses COLD-tier promotion on layer-3-only verdicts. |
| `TRINITY_SESSION_CLOSE_SPEC_V1.md` (Phase 12) | Final-manifest hash MUST cover every verifier report file produced during the session; `verifier_report.capture_refs` MUST be a subset of the manifest's `captures.capture_ids`. |
| `TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md` | `sandbox.deny` events surface as `sandbox_violation` predicate hits at layer 1; ORPHANED_INVOCATION translates per `TRINITY_VERIFIER_CONTRACT_V1` Section 2.1. |
| `TRINITY_TOOL_CAPABILITY_MODEL_V1.md` | `tool.invocation_denied` events surface as policy-layer predicates; routing per `TRINITY_VERIFIER_CONTRACT_V1` Section 2.1. |
| `docs/specs/02_VERIFIER_SPEC.md` (legacy spec pack) | Original verifier specification; this Spec is the contract counterpart. Conflicts resolved in favour of this Spec for contract-shape questions. |
| `04_GRAPH_SPEC.md` | Graph transitions consume verdict outputs; PASS is the precondition for `EXECUTE -> VERIFIED`, `VERIFIED -> PROMOTED` (with human gate per Article XIII), etc. |
| `12_GLOSSARY.md` | Canonical glossary; new terms from Section 10.2 require sibling editorial amendment. |

### 10.4 Cross-references to constitutional documents

| Document | Relationship |
|---|---|
| `TRINITY_CONSTITUTION_V1.md` Article III | "AI cannot govern itself" -- root justification for the contract surface |
| `TRINITY_CONSTITUTION_V1.md` Article IV | Role separation -- Verifier vs Executor vs Planner asymmetry pinned by the contract |
| `TRINITY_CONSTITUTION_V1.md` Article VIII | Verifier discipline -- Section 5 (policy boundary) and Section 6 (LLM judge) extend Article VIII's MUSTs |
| `TRINITY_CONSTITUTION_V1.md` Article X | Audit discipline -- Section 7 obligations |
| `TRINITY_CONSTITUTION_V1.md` Article XIII | Human authority -- Section 2.3 (NEEDS_HUMAN) and Section 6.6 (layer-3 PASS authority denial for COLD) |
| `TRINITY_CONSTITUTION_V1.md` Article XIV | Critical gates -- COLD-tier work MUST permit layer 4 |
| `TRINITY_CONSTITUTION_V1.md` Article XVI | Least authority -- Verifier write authority bounded to its own report file + audit chain |
| `TRINITY_CONSTITUTION_V1.md` Article XX | Passive Core -- Verifier evaluates only on explicit invocation |
| `TRINITY_CONSTITUTION_V1.md` Article XXII | Recovery and reversibility -- contract MUST declare retry budget + DEAD pathway |
| `TRINITY_CONSTITUTION_V1.md` Article XXIII | Failure visibility -- DEAD is the explicit, audited counterpart to silent abandonment |
| `TRINITY_CONSTITUTION_V1.md` Article XXIV | No silent success -- contract requires evidence_keys per acceptance entry |
| `TRINITY_CONSTITUTION_V1.md` Article XXV | Constitutional priority order -- this Spec is rank 5 (Workflow Contract) |
| `TRINITY_CONSTITUTION_V1.md` Article XXIX | Amendment procedure -- Section 9 of this Spec |
| `TRINITY_CONSTITUTION_V1.md` Article XXX | Completion rule -- Verification Contract is the artifact that operationalises "verification passed or approved exceptions exist" |
| `TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md` | Meta-rule layer above the Ritual Contract; Article XII.5 empirical gate referenced by `rrr` consumers of verdicts |
| `TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md` | Article XXIX operationalisation -- editorial / operational / constitutional tiers consumed by Section 9 |

### 10.5 Open questions (to resolve before V1.1)

- Should the Verification Contract envelope itself carry a `schema_version` field that is independent of this Spec's `version`? Proposed: yes, `contract_schema_version: "trinity.verification_contract.v1"`. Resolution at first amendment.
- Should layer-3 PASS authority elevations expire automatically (per-session vs persistent)? Proposed: per-session only; persistent elevation requires constitutional-tier amendment. Resolution at first operational amendment.
- Should `policy_snapshot` cover `verifier-rules.yaml` itself (not currently listed)? Proposed: yes, add `verifier_rules_yaml_sha256`. Resolution at next operational amendment.
- Should there be a `contract_quorum` mechanism for multi-human approvals on COLD-tier work? Out of scope for V1; track for V2 alongside multi-operator concerns.

---

## Section 11 -- Out of Scope (V1.0)

**[normative-description]**

The following are explicitly out of scope for V1.0 of this Spec:

- The `verification_contract.json` schema file itself (`.ai/schemas/verification_contract.schema.json`) -- deferred to Phase 3 implementation gogogo. This Spec describes the field set; the schema authoritatively closes additionalProperties.
- The runtime contract validator implementation (Python module) -- deferred to Phase 3 implementation gogogo.
- The `nnn` -> contract emission wiring -- deferred; current `nnn` emits a plan envelope without the dedicated contract envelope. Phase 3 lands the envelope as a sibling artifact.
- Multi-operator quorum (multiple humans must approve) -- deferred to V2.
- Cryptographic attestation of contract content (signed contracts) -- deferred to Phase 14 Root of Trust.
- Cross-session contract reuse (template contracts) -- out of scope; contracts are per-session by design (memory anchor: `feedback_plan_amendment_vs_subsession`).
- Layer-3 LLM judge implementation specifics (which model, which prompt, which sibling CLI carries the call) -- delegated to sibling-CLI implementation; this Spec only constrains the audit envelope (Section 6).
- Editing `.ai/policies/verifier-rules.yaml` -- governed by Canonical Policies (rank 2); this Spec only references the file's existing shape.

---

**Authors:** Trinity Architect (operator direct-draft, executor authoring sibling spec).
**Review status:** pending verifier review + ddd gate per Articles III, XIII.
**Audit reference:** the session-close audit chain emitted when this Spec lands constitutes the canonical record per Addendum v1.0.4 XXIX.5; tier classification `operational` (introduces a new contract artifact and a new validation precondition for `gogogo` without mutating any parent Constitution Article).
