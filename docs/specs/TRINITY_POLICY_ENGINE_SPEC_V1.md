---
title: "Trinity Policy Engine Spec v1.0"
version: "1.0"
status: "draft"
phase: "5"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes:
  - "(none -- first canonical version)"
constitutional-anchor: ["Article III", "Article IV", "Article XIII", "Article XVI", "Article XX", "Article XXIX"]
amendment-policy: "Article XXIX -- explicit proposal + rationale + impact analysis + human approval + version bump + audit entry."
---

# TRINITY_POLICY_ENGINE_SPEC_V1

**Phase:** 5 -- Policy Engine Extraction
**Organ:** #5 (Policy Engine)
**Constitutional rank:** 3 -- Canonical Policies (per Article XXV)
**Co-authored bundle:** Phase 3 (`TRINITY_VERIFICATION_CONTRACT_SPEC_V1`) + Phase 4 (`TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1`) + this document
**Date:** 2026-05-15

## Section 0 -- Rank-3 Authority Disclaimer (Article XXV)

**normative-description.** This document is a **Canonical Policies** instrument under Article XXV of the Trinity Constitution v1.0. It ranks third in the constitutional priority order:

```
Constitution
-> Ritual Constitution
-> Canonical Policies        (this spec lives here)
-> Kernel State Rules
-> Workflow Contracts
-> Tool Contracts
-> Runtime Requests
-> Model Suggestions
```

Any clause that conflicts with the Constitution, Ritual Constitution, or any other higher-ranked instrument is void in the conflict and the higher-ranked instrument governs. Amendments to this spec follow Article XXIX (explicit proposal + rationale + impact analysis + human approval + version bump + audit entry). This spec does **not** itself enforce policy at runtime; it defines the contract that the kernel and downstream policy validators MUST honour.

---

## 1. Purpose & Constitutional Anchor

**normative-description.** The Policy Engine is the deterministic decision surface that the kernel queries before every state transition, every tool invocation, and every filesystem mutation. Its existence is mandated by the Constitution. The reason it must be a **separate** organ -- not folded into the verifier (Phase 3) and not folded into the kernel state machine (Phase 4) -- is rooted in six articles of the Trinity Constitution v1.0.

### 1.1 Article III -- AI Cannot Govern Itself (verbatim)

> AI may:
>
> ```text
> - think
> - reason
> - propose
> - execute through authorized tools
> ```
>
> AI MUST NOT:
>
> ```text
> - declare final completion
> - approve its own work
> - verify its own correctness
> - bypass verifier approval
> - bypass governance gates
> - forge authority
> - redefine workflow state
> - rewrite constitutional policy
> ```

**normative-description.** Article III draws a hard line between proposing and governing. The Policy Engine is the kernel-side governor of "may this action proceed?" -- and because AI may not rewrite constitutional policy, the policy files (`.ai/policies/**`) are write-locked to AI actors. Policy edits are decided by humans (Article XIII below), executed as commits, and recorded as audit events (Section 6).

### 1.2 Article IV -- Separation of Responsibilities (verbatim)

> Trinity MUST enforce strict role separation.
>
> Canonical roles:
>
> ```text
> Kernel    = governance, state, gates, authority
> Planner   = reasoning, plans, risk analysis
> Executor  = bounded action, mutation, execution artifacts
> Verifier  = independent validation
> Memory    = evidence retrieval
> Audit     = immutable history
> Retro     = post-work reflection
> Transport = message delivery only
> ```
>
> No component may silently absorb another component's role.
>
> Role collapse is a constitutional violation.

**normative-description.** Article IV is the structural reason the Policy Engine is a distinct organ. Three anti-collapse rules follow:

1. The Verifier (Phase 3) decides "did the artifact match the declared criteria?" -- it does **not** decide "is this action permitted?" That second question is the Policy Engine's.
2. The kernel state machine (Phase 4) decides "is the requested transition legal in the graph?" -- it does **not** decide "is the actor permitted to request it?" That second question is the Policy Engine's.
3. The Policy Engine MUST NOT decide whether a step's evidence satisfies acceptance criteria. That is the Verifier. Policy and verification are orthogonal axes; collapsing them would silently merge "is allowed" with "is correct."

### 1.3 Article XIII -- Human Authority (verbatim)

> Humans remain the highest authority.
>
> AI may recommend irreversible actions.
>
> AI MUST NOT silently authorize irreversible actions.
>
> Critical actions SHOULD require explicit human approval.
>
> Critical actions include:
>
> ```text
> production deploy
> destructive operations
> credential changes
> privilege escalation
> irreversible mutations
> external publication
> legal/financial/customer-impacting actions
> ```
>
> Human approval MUST exist as an artifact.

**normative-description.** Article XIII is the source authority for the `decided_by: human` audit envelope and for the `NEEDS_HUMAN` policy verdict (Section 2). Every Critical Gate Rule (Section 6) terminates in a human-approval artifact; the Policy Engine never substitutes for human judgement on any item in the enumerated list.

### 1.4 Article XVI -- Least Authority (verbatim)

> Every component MUST operate with minimum required authority.
>
> Examples:
>
> ```text
> memory-cli must not own execution authority
> verifier must not own production mutation authority
> browser-cli must not own deployment authority
> transport must not own governance authority
> ```
>
> Unknown authority MUST be treated as denied authority.

**normative-description.** "Unknown authority MUST be treated as denied authority" is the literal source of the **default-deny** stance the Policy Engine adopts (Section 2.3). When the kernel queries for an action whose policy disposition is unknown, the verdict is `deny` with reason `unknown_authority`, never `allow`.

### 1.5 Article XX -- Passive Core Principle (verbatim)

> Core Trinity systems act only through explicit invocation.
>
> Core systems MUST NOT:
>
> ```text
> self-trigger
> self-expand authority
> silently mutate policy
> rewrite themselves recursively
> generate new goals autonomously
> ```
>
> Automation is allowed only when:
>
> ```text
> bounded
> observable
> interruptible
> auditable
> ```

**normative-description.** Article XX makes the Policy Engine a **passive** evaluator. It does not crawl, does not subscribe, does not auto-suggest, and does not silently amend its own rules. Every query must be explicit, originate from a named caller, and produce an audit-referenceable verdict (Section 4). This same principle is why Section 8 (Independence from State Graph) requires the policy rules to be testable in isolation: a passive component cannot grow a hidden side-channel into the kernel.

### 1.6 Article XXIX -- Constitutional Amendment (verbatim)

> The Constitution MUST NOT be silently rewritten.
>
> Amendments require:
>
> ```text
> explicit proposal
> rationale
> impact analysis
> human approval
> version bump
> audit entry
> ```
>
> Prior versions MUST remain inspectable.

**normative-description.** Article XXIX governs how policy itself evolves. The same six-step procedure applies to any change in `.ai/policies/**` because policy files are Canonical Policies (rank 3 in Article XXV). Section 9 details the amendment protocol per Addendum v1.0.4's three tier classification (editorial / operational / constitutional).

### 1.7 Why policy is not the verifier and not the state machine

**normative-description.** A simple thought experiment demonstrates the necessity of separation:

- The Verifier asks: "Does this artifact's measured shape match what was declared?"
- The State Machine asks: "Is this transition (from-state, to-state, evidence-shape) declared legal in the graph?"
- The Policy Engine asks: "Is this actor permitted to attempt that transition / tool call / mutation **at all**, given the target, the context, and the human-authored rules?"

Folding any pair of these collapses a role under Article IV. A Verifier that also enforces forbidden_paths would silently make policy mutable by adjusting verifier rules. A State Machine that also enforces secret-leakage would silently make policy depend on graph topology. The three organs MUST remain orthogonal.

---

## 2. Policy Surface Vocabulary

**normative-description.** The Policy Engine speaks a closed vocabulary of four verdicts, evaluated in a fixed precedence order, with default-deny as the terminal fallback.

### 2.1 Verdict set (closed)

```
allow         -- the requested action is permitted; kernel proceeds.
deny          -- the requested action is refused; kernel emits refusal audit.
conditional   -- the action is permitted only if all listed conditions hold;
                 each condition is a re-query that itself returns allow/deny.
NEEDS_HUMAN   -- the action requires explicit human approval per Article XIII;
                 kernel pauses and emits a human-gate artifact.
```

The verdict set is closed. The Policy Engine MUST NOT return any verdict outside this four-element set. An attempt to compute a fifth verdict is itself a constitutional violation under Article XVIII (Determinism Over Emergence).

### 2.2 Precedence order (when multiple rules match)

```
1. deny           (any matching deny rule terminates evaluation immediately)
2. NEEDS_HUMAN    (any matching needs-human rule overrides allow / conditional)
3. conditional    (each condition must resolve to allow before proceeding)
4. allow          (only if no deny / NEEDS_HUMAN / unresolved conditional matches)
```

**normative-description.** Precedence is **deny-wins**, then human-gates-win, then conditions, then allow. The same query MUST always produce the same verdict given the same policy file content; nondeterminism in the engine itself is forbidden (Article XVIII).

### 2.3 Default-deny stance

**normative-description.** When no policy rule matches the query, the verdict is `deny` with reason `unknown_authority`. This implements Article XVI's "Unknown authority MUST be treated as denied authority" verbatim. There is no implicit-allow fallback. The engine MUST NOT infer permission from the absence of a deny rule; absence is denial.

### 2.4 Reason codes (structured, append-only)

**normative-description.** Every non-`allow` verdict carries a structured `reason` field drawn from a closed enumeration. Adding a new reason code is an operational-tier amendment under Article XXIX (Section 9). Initial enumeration:

```
unknown_authority           -- default-deny (Article XVI)
forbidden_path              -- target matches forbidden_paths glob (Section 7)
secret_pattern_detected     -- payload matches secret regex / entropy threshold (Section 7)
human_gate_required         -- Critical Gate Rule triggered (Section 6)
illegal_actor               -- actor lacks declared authority (Article IV / XVI)
illegal_target              -- target outside actor's allowed surface (Article XVI)
schema_invalid              -- query envelope failed schema validation (Section 4)
quota_exceeded              -- actor exceeded a declared quota (e.g. retry budget)
amendment_required          -- rule exists but is marked stale; human must refresh
```

The kernel surfaces this reason verbatim in the refusal audit event (Section 5.3) and in the user-visible refusal message (Section 5.5).

### 2.5 non-normative-example -- precedence walk-through

```
Query: actor=executor_helper, action=fs.write, target=.ai/policies/safety.yaml
Matching rules:
  - rule_pol_001 (deny: target prefix .ai/policies/**)
  - rule_pol_007 (allow: actor=executor_helper, action=fs.write, target=.ai/sessions/**)
Precedence: deny wins -> verdict=deny, reason=forbidden_path, evidence_ref=rule_pol_001
```

```
Query: actor=human_operator, action=transition, from=VERIFY, to=DEPLOY
Matching rules:
  - rule_pol_042 (NEEDS_HUMAN: any to=DEPLOY)
Verdict: NEEDS_HUMAN, reason=human_gate_required, evidence_ref=rule_pol_042
Kernel pauses; emits ddd-gate artifact; awaits decided_by: human envelope.
```

---

## 3. Policy File Catalog

**normative-description.** The Policy Engine is fed by four canonical files under `.ai/policies/`. Each file has a single, declared role. This spec **describes** them; it does **not** author the missing one.

### 3.1 The canonical four

| File | Role | Owner | Phase |
|---|---|---|---|
| `.ai/policies/safety.yaml` | Risk-scoring factors, secret-scan gates, hard-block patterns. The deterministic safety surface. | Human (Article XIII) | Pre-existing; consumed by this engine |
| `.ai/policies/gates.yaml` | Guardrail definitions: per-language syntax checks, secret-scan provider, test-runner commands. | Human (Article XIII) | Pre-existing; consumed by this engine |
| `.ai/policies/verifier-rules.yaml` | The Pyramid of Judgment configuration: verdict set, layer ordering, per-rule-set predicates (`pass_when`, `retry_when`, `needs_human_when`, `dead_when`). | Human (Article XIII) | Pre-existing; **owned by Phase 3 verifier**, **read** by this engine for boundary verification only (Section 8) |
| `.ai/policies/trinity_policy.yaml` | The Phase 5 deliverable proper: actor-action-target rules, forbidden_paths, secret patterns, critical gate declarations, NEEDS_HUMAN triggers. | Human (Article XIII) | **Phase 5 deliverable -- NOT authored by this spec**; authored separately under Article XIII |

**normative-description.** This spec is the **contract** for `trinity_policy.yaml`. The file itself is a separate human-authored artifact and lands in a separate session under the `decided_by: human` envelope. Per Article III, no AI actor (including this author) may write the policy content.

### 3.2 Ownership boundary (write authority)

```
.ai/policies/safety.yaml         -- write: human only
.ai/policies/gates.yaml          -- write: human only
.ai/policies/verifier-rules.yaml -- write: human only
.ai/policies/trinity_policy.yaml -- write: human only
```

**normative-description.** All four files are write-locked against AI actors. The Policy Engine treats `.ai/policies/**` as `forbidden_path` for every actor whose `authority.may_modify_policies` is `false` -- which, per Article III, is **all AI actors unconditionally** (cross-ref `TRINITY_SANDBOX_CAPABILITY_SPEC_V1` Section 2.5).

### 3.3 Read authority

**normative-description.** The Policy Engine itself MUST be able to read `.ai/policies/**`. Tool actors that need to inspect policy (e.g. for proposing an amendment) MUST request the `policy.read` capability declared in `TRINITY_TOOL_CAPABILITY_MODEL_V1` Section 2.1, granted via `policy.read_allowed: true` in the bound sandbox profile (`TRINITY_SANDBOX_CAPABILITY_SPEC_V1` Section 2.6). Read access is **never** implicit.

### 3.4 Cross-spec consumption matrix

| File | Read by Phase 3 Verifier | Read by Phase 4 State Machine | Read by Phase 5 Policy Engine | Read by Phase 6 Tool Registry | Read by Phase 7 Sandbox |
|---|---|---|---|---|---|
| `safety.yaml` | yes (risk score for evidence) | no | yes (hard_blocks, secret patterns) | no | indirect (via policy query) |
| `gates.yaml` | yes (test-runner commands) | no | yes (gate definitions) | no | no |
| `verifier-rules.yaml` | yes (rule sets, layer config) | no | read-only (boundary check) | no | no |
| `trinity_policy.yaml` | no | no | yes (primary feed) | yes (per-tool rule lookup) | yes (profile derivation) |

**normative-description.** The matrix is not aspirational; the kernel MUST refuse to start if any file in the canonical four is unreadable, malformed, or missing the `version` frontmatter field.

### 3.5 RBAC file -- forward-looking deliverable (not yet authored)

**normative-description.** The Phase 3 verifier rule set (`.ai/policies/verifier-rules.yaml` line 46, illustrative) carries a cross-reference to a sibling file `rbac.yaml` that is **not** present in the canonical four enumerated in Section 3.1. This is an acknowledged forward-looking placeholder, not an active policy file. `rbac.yaml` will be authored in a future phase as the per-actor authority table; until that file exists and is committed, the Policy Engine MUST NOT load it and MUST NOT infer permissions from its absence. The cross-ref in `verifier-rules.yaml` is documentary; treating it as a load directive would violate Article XX (Passive Core) by silently reaching for an unauthored artifact. When `rbac.yaml` lands, this section will be amended (operational tier per Section 9) to add it to the catalog and the consumption matrix (Section 3.4).

### 3.6 non-normative-example -- catalog at engine boot

```
[policy.engine] boot at 2026-05-15T09:00:00Z
[policy.engine] loaded .ai/policies/safety.yaml             (sha256=ab12...)
[policy.engine] loaded .ai/policies/gates.yaml              (sha256=cd34...)
[policy.engine] loaded .ai/policies/verifier-rules.yaml     (sha256=ef56...; read-only)
[policy.engine] loaded .ai/policies/trinity_policy.yaml     (sha256=78ab...)
[policy.engine] precedence configured: deny > NEEDS_HUMAN > conditional > allow
[policy.engine] default-deny on unknown query: enabled
[policy.engine] ready
```

---

## 4. Query API Contract

**normative-description.** The kernel queries the Policy Engine through a single function: `policy.query(envelope) -> verdict_envelope`. The query is a structured envelope; the verdict is a structured envelope; both are schema-validated.

### 4.1 Query input schema (normative)

```yaml
# query envelope (input)
schema_version: "1"
query_id: <ulid>                  # caller-generated; reused in the verdict envelope
actor:
  id: <string>                    # e.g. "executor_helper", "human:operator", "kernel"
  authority_class:
    enum: [ai, human, kernel, tool, transport]
action:
  kind:
    enum: [transition, tool_invoke, fs_read, fs_write, fs_delete, net_outbound, proc_exec, policy_read, policy_write, ddd_propose, ddd_decide]
  detail:
    # action-specific payload; keys depend on kind
    # e.g. for transition: { from: "VERIFY", to: "DEPLOY" }
    # e.g. for fs_write:  { path: ".ai/sessions/<sid>/DO/dev/foo.py", bytes: 1024 }
target:
  type:
    enum: [path, host, binary, transition, tool_name, audit_event, policy_file, none]
  value: <string-or-null>
context:
  session_id: <ulid-or-null>
  ritual_phase:
    enum: [READY, THINK, PLAN, SANDBOX, EXECUTE, VERIFY, PROMOTE, DEPLOY, RETRO, DONE, FAILED, ABORTED, REOPENED, none]
  declared_authority: <string-or-null>   # what the actor claims; engine verifies
  evidence_refs: [<string>]              # artifact paths the caller offers as basis
```

**normative-description.** Every field above is required. A missing field MUST cause the engine to return `deny` with reason `schema_invalid`. The schema lives at `.ai/schemas/policy_query_envelope.v1.yaml` (write authority: human only; this spec defines the shape, the schema file is a separate human-authored deliverable per Article III).

### 4.2 Verdict response schema (normative)

```yaml
# verdict envelope (output)
schema_version: "1"
query_id: <ulid>                  # echoed from query
verdict:
  enum: [allow, deny, conditional, NEEDS_HUMAN]
reason: <string>                  # closed enumeration; see Section 2.4
evidence_ref:
  rule_id: <string>               # the matching policy rule's stable id
  rule_file: <string>             # e.g. ".ai/policies/trinity_policy.yaml"
  rule_anchor: <string>           # YAML anchor or line range
conditions:                       # only present when verdict == conditional
  - condition_id: <string>
    description: <string>
    re_query: <embedded-query-envelope>   # caller MUST resolve before proceeding
human_gate:                       # only present when verdict == NEEDS_HUMAN
  gate_id: <string>
  artifact_required: <string>     # e.g. ddd packet path
  rationale: <string>
emitted_at: <iso-8601-utc>
engine_version: "1.0"
```

**normative-description.** The verdict envelope is the **only** legitimate output of the Policy Engine. The kernel MUST persist every verdict envelope into the audit chain (Section 5.3). The kernel MUST NOT discard, summarise, or rewrite the envelope.

### 4.3 Caller contract (kernel-side)

**normative-description.** The kernel MUST query the Policy Engine **before**:

1. Any state transition (`from`, `to`, `actor`, evidence refs).
2. Any tool invocation (`tool_name`, declared capabilities, target).
3. Any filesystem mutation (`path`, action, byte count).
4. Any network outbound call (`host`, protocol).
5. Any process exec (`binary`, args summary).
6. Any read or write of `.ai/policies/**` (always denied for AI actors per Article III).
7. Any `ddd.propose` or `ddd.decide` event emission.

**normative-description.** The kernel MUST NOT proceed if `verdict != allow`. On `conditional`, the kernel MUST resolve every embedded condition (each as its own query) before proceeding. On `NEEDS_HUMAN`, the kernel MUST emit a `ddd` packet and pause. On `deny`, the kernel MUST emit a refusal audit event (Section 5.3) and abort the requested action.

### 4.4 Determinism guarantee

**normative-description.** Given identical policy file contents and identical query envelopes, the engine MUST return identical verdict envelopes (modulo `query_id` and `emitted_at`). This is testable via the conformance harness in Section 8.

### 4.5 non-normative-example -- end-to-end query/verdict pair

```yaml
# query
schema_version: "1"
query_id: "01J7K9M2X8N4P5Q6R7S8T9V0W1"
actor: { id: "executor_helper", authority_class: "ai" }
action:
  kind: "fs_write"
  detail: { path: ".ai/sessions/01J7.../DO/dev/build.py", bytes: 2048 }
target: { type: "path", value: ".ai/sessions/01J7.../DO/dev/build.py" }
context:
  session_id: "01J7K9M2X8N4P5Q6R7S8T9V0W1"
  ritual_phase: "EXECUTE"
  declared_authority: "plan_envelope.allowed_paths"
  evidence_refs: [".ai/sessions/01J7.../.state/plan.json"]
```

```yaml
# verdict
schema_version: "1"
query_id: "01J7K9M2X8N4P5Q6R7S8T9V0W1"
verdict: "allow"
reason: "actor_in_allowed_paths"
evidence_ref:
  rule_id: "rule_pol_022"
  rule_file: ".ai/policies/trinity_policy.yaml"
  rule_anchor: "rules.fs_write.allowed_under_session_dev"
emitted_at: "2026-05-15T09:00:01.123Z"
engine_version: "1.0"
```

---

## 5. Blocking Semantics

**normative-description.** When the Policy Engine returns `deny` or `NEEDS_HUMAN`, the kernel enters a **block** state for the requested action. Blocking has three observable surfaces: the audit chain, the user-visible message, and the session state file.

### 5.1 What policy can block

| Action class | Block on `deny` | Block on `NEEDS_HUMAN` |
|---|---|---|
| State transition | yes -- transition refused, kernel stays in current state | yes -- kernel stays in current state and emits `ddd` packet |
| Tool invocation | yes -- tool not invoked, no side effects | yes -- tool not invoked, human gate emitted |
| Filesystem write | yes -- write rejected before bytes hit disk | yes -- write rejected; human-gate path emitted |
| Filesystem delete | yes -- delete rejected | yes -- almost always (Section 6) |
| Network outbound | yes -- connection not initiated | yes -- gate required |
| Process exec | yes -- process not spawned | yes -- gate required |
| Policy file write (AI actor) | yes -- always; per Article III | n/a -- never even reaches gate, denied unconditionally |
| ddd.propose | yes -- proposal not emitted | n/a -- propose itself does not need a human gate |
| ddd.decide (AI actor) | yes -- always; per Article XIII | n/a -- only humans may decide |

**normative-description.** The "block" is the engine's contract output; the kernel is the enforcer. A kernel that observes a `deny` verdict and proceeds anyway is in violation of Article V (Kernel Authority).

### 5.2 Refusal is not failure

**normative-description.** A `deny` verdict is **not** a `FAILED` workflow state. Refusal is a normal, expected outcome of the policy gate. The kernel records the refusal and continues to await the next legitimate request. Only repeated refusals against an explicit retry budget (out of scope for this spec; see verifier rule sets in `verifier-rules.yaml.code_change.dead_when.retry_budget_exhausted`) escalate to a workflow failure state.

### 5.3 Refusal audit event format (normative)

**normative-description.** Every `deny` and every `NEEDS_HUMAN` verdict MUST be appended to `.ai/audit/events.ndjson` as a single hash-chained event. Field shape:

```json
{
  "ts": "<iso-8601-utc>",
  "seq": <integer>,
  "event": "policy.refused",
  "session_id": "<ulid-or-null>",
  "actor": "<string>",
  "action_kind": "<string>",
  "target": "<string>",
  "verdict": "<deny|NEEDS_HUMAN>",
  "reason": "<reason-code>",
  "rule_id": "<string>",
  "rule_file": "<string>",
  "query_id": "<ulid>",
  "engine_version": "1.0",
  "prev_hash": "<sha256>",
  "hash": "<sha256>"
}
```

**normative-description.** The event uses the existing audit chain primitives defined in `TRINITY_AUDIT_EVENT_SPEC_V1` (no new chain, no parallel log). The `event` discriminator is `policy.refused` for `deny` and `policy.gate_required` for `NEEDS_HUMAN`. Both events are append-only; corrections (Section 9) emit new events, never mutate existing ones.

### 5.4 Forbidden-path refusal: special form

**normative-description.** When the deny is rooted in `forbidden_path`, the audit event MUST also carry `forbidden_pattern: "<glob>"` to make the rule diff inspectable in retro analysis (cross-ref memory anchor `feedback_executor_helper_forbidden_writes_drift`).

### 5.5 User-visible refusal message format

**normative-description.** The kernel surfaces refusals to the operator as a single deterministic line plus a pointer to the audit event:

```
policy.refused: <action_kind> on <target>
  actor:   <actor>
  reason:  <reason-code>
  rule:    <rule_id> (<rule_file>:<rule_anchor>)
  query:   <query_id>
  audit:   .ai/audit/events.ndjson seq=<seq>
```

For `NEEDS_HUMAN`:

```
policy.gate_required: <action_kind> on <target>
  actor:   <actor>
  gate:    <gate_id>
  artifact_required: <ddd-packet-path>
  rationale:         <one-line-rationale>
  audit:   .ai/audit/events.ndjson seq=<seq>
```

**normative-description.** ASCII only. No emojis, no smart quotes, no em-dash. Memory anchor `feedback_acceptance_grep_char_mismatch` makes this load-bearing: downstream tooling greps these messages and any non-ASCII rune silently breaks the match.

### 5.6 non-normative-example -- a forbidden_path refusal in flight

```
$ bash .ai/cli/ai gogogo
[execute] step S2: write .ai/policies/trinity_policy.yaml ... 
policy.refused: fs_write on .ai/policies/trinity_policy.yaml
  actor:   executor_helper
  reason:  forbidden_path
  rule:    rule_pol_001 (.ai/policies/trinity_policy.yaml:rules.policy_files.write_locked)
  query:   01J7K9M2X8N4P5Q6R7S8T9V0W1
  audit:   .ai/audit/events.ndjson seq=10428
[gogogo] step S2 blocked by policy. Halting plan.
```

---

## 6. Critical Gate Rules

**normative-description.** A **Critical Gate** is a class of action that always returns `NEEDS_HUMAN` -- never `allow` -- regardless of session state, actor authority, or sandbox profile. Critical Gates are the runtime expression of Article XIII (Human Authority) and Article XIV (Critical Gates).

### 6.1 Enumerated Critical Gates

| Gate id | Trigger | Required artifact | Constitutional anchor |
|---|---|---|---|
| `gate.production_deploy` | any transition with `to: DEPLOY` AND target environment != local sandbox | `decided_by: human` ddd-packet referencing the deploy plan | Article XIII |
| `gate.destructive_op` | any `fs_delete`, `fs_write` with overwrite of existing tracked file in `DO/prod/`, or `proc_exec` of binaries marked destructive | human-approved ddd-packet referencing the diff or command | Article XIII |
| `gate.external_publication` | any `net_outbound` to a host classified as "publication surface" (CMS, social, mailing-list, package registry) | human-approved ddd-packet with target URL + payload diff | Article XIII |
| `gate.credential_change` | any `fs_write` to declared credential paths or `proc_exec` of credential-rotation binaries | human-approved ddd-packet + out-of-band confirmation | Article XIII |
| `gate.privilege_escalation` | any query attempting to expand `authority.*` flags in the bound sandbox profile | human-approved ddd-packet referencing the new profile | Articles XIII, XVI |
| `gate.policy_amendment` | any `fs_write` to `.ai/policies/**` from a non-human actor | human commit + Article XXIX trace artifact | Articles III, XIII, XXIX |
| `gate.audit_truncation` | any attempt to mutate or truncate `.ai/audit/events.ndjson` | human commit + retroactive audit entry per Addendum v1.0.4 XXIX.6 | Articles X, XIII, XXIX |
| `gate.constitution_amendment` | any `fs_write` to `docs/constitution/**` from a non-human actor | full Article XXIX six-step procedure | Article XXIX |

**normative-description.** The list above is a normative starting set. Adding a gate is an **operational-tier** amendment under Addendum v1.0.4 XXIX.2 (Section 9). Removing a gate is a **constitutional-tier** amendment under XXIX.3 because each gate maps to an explicit Constitutional article.

### 6.2 Gate evidence shape (`decided_by: human`)

**normative-description.** The `decided_by: human` envelope is the canonical artifact that satisfies a Critical Gate. Required fields:

```yaml
decided_by: human
human_id: <operator-id>
gate_id: <string>                  # the gate from Section 6.1
query_id: <ulid>                   # the policy query that triggered the gate
decision:
  enum: [approve, deny]
rationale: <multiline-string>      # why the human is approving / denying
artifact_refs:
  - <path-to-diff-or-plan-or-command>
decided_at: <iso-8601-utc>
audit_seq: <integer>               # the policy.gate_required event being decided
```

**normative-description.** The envelope is itself an audit event (`event: ddd.decided`) and is hash-chained. Cross-ref `TRINITY_DDD_HUMAN_GATE_SPEC_V1` for the full ddd-packet contract.

### 6.3 Gate timeout behaviour

**normative-description.** A Critical Gate that has no `decided_by: human` envelope within the operator-configured gate timeout MUST emit a `policy.gate_expired` audit event and the kernel MUST treat the action as **denied** (not as auto-approved). Default timeout: 60 minutes (cross-ref `verifier-rules.yaml.layer_4_human.timeout_minutes`). Auto-approval on gate expiry is forbidden by Article XIII.

### 6.4 Secret-leakage prevention as a Critical Gate

**normative-description.** Detected secret payloads (Section 7) are a **deny**, not a `NEEDS_HUMAN`. The reason: a leaked secret cannot be un-leaked by human approval; the only valid response is to refuse the write and surface the detection. A human MAY subsequently amend policy (Section 9) to whitelist a specific path, but the act of writing the secret is unconditionally refused at the engine boundary.

### 6.5 non-normative-example -- production_deploy gate flow

```
1. Kernel queries: action=transition, from=VERIFY, to=DEPLOY, target_env=production
2. Engine returns: verdict=NEEDS_HUMAN, gate_id=gate.production_deploy
3. Kernel emits audit event: policy.gate_required (seq=10500)
4. Kernel writes ddd-packet template to .ai/sessions/<sid>/GATE/deploy_packet.yaml
5. Kernel pauses; user-visible: policy.gate_required ... artifact_required=...
6. Operator inspects packet, fills in rationale, sets decision: approve.
7. Operator runs: bash .ai/cli/ai ddd approve --gate gate.production_deploy
8. Kernel emits: ddd.decided (seq=10501) with decided_by: human envelope
9. Kernel re-queries policy: same action, now with evidence_ref=audit:10501
10. Engine returns: verdict=allow, reason=human_gate_satisfied, evidence_ref=ddd:10501
11. Kernel proceeds with the transition.
```

---

## 7. Forbidden Path & Secret Rules

**normative-description.** Two of the most load-bearing rule families in the Policy Engine are the **forbidden_paths** list and the **secret detection** rules. This section describes their **shape and invocation**; it does **not** enumerate the actual path globs or the actual secret regex patterns, both of which live in human-authored policy files.

### 7.1 Forbidden paths -- pattern, not enumeration

**normative-description.** `trinity_policy.yaml` (the Phase 5 deliverable, authored separately) declares `forbidden_paths` as a list of glob patterns. The Policy Engine resolves each `fs_write`, `fs_delete`, and `fs_read` query against this list and returns `deny` (reason: `forbidden_path`) on any match. The match check is **literal glob** -- no regex, no semantic interpretation.

```yaml
# shape only; actual globs live in trinity_policy.yaml (human-authored)
forbidden_paths:
  - "<glob-pattern-1>"
  - "<glob-pattern-2>"
  - ...
```

**normative-description.** The CLAUDE.md root file enumerates the operator-known forbidden surfaces: `.ai/policies/**`, `.ai/audit/**` (modify), `.ai/schemas/**`, `docs/specs/**`. The authoritative source is `trinity_policy.yaml`. If the two diverge, the policy file wins (Article XXV: Canonical Policies > documentation).

### 7.2 Forbidden trumps allowed

**normative-description.** A path that appears in `forbidden_paths` MUST be denied even if the same path is covered by a sandbox `fs.write_roots` grant or by a session-specific `plan_envelope.allowed_paths` declaration. This is the kernel-side enforcement of Article XVI (Least Authority): the most-restrictive declaration wins. Cross-ref memory anchor `feedback_executor_helper_forbidden_writes_drift` -- the inverse mistake (allowed_paths overriding forbidden) is a constitutional violation.

### 7.3 Secret detection -- regex + entropy

**normative-description.** Secret detection runs on `fs_write` queries (and on outbound payload hashes). Two detection axes:

1. **Regex axis.** A list of pattern definitions in `safety.yaml.gates.secrets.patterns` and `safety.yaml.hard_blocks[].regex`. The Policy Engine MUST run each pattern against the proposed payload bytes.
2. **Entropy axis.** A configurable Shannon-entropy threshold over base64- and hex-shaped substrings. High-entropy substrings beyond a length threshold (illustrative placeholder: 32 chars at >= 4.5 bits/char) MUST trigger a `secret_pattern_detected` deny.

```yaml
# illustrative placeholders only; do not interpret as real patterns
secrets:
  regex_patterns:
    - id: "secret_pattern_001"
      pattern: "<placeholder-regex>"
      severity: deny
    - id: "secret_pattern_002"
      pattern: "<placeholder-regex>"
      severity: deny
  entropy:
    enabled: true
    min_substring_length: 32
    min_bits_per_char: 4.5
    severity: deny
```

**normative-description.** Real patterns are operator-authored and committed under Article XIII. This spec MUST NOT contain real patterns; doing so would itself constitute a leak surface.

### 7.4 Excluded paths

**normative-description.** The `safety.yaml.gates.secrets.exclude_paths` list (already populated; see file) declares paths where pattern matches are documentation, not credentials. The Policy Engine MUST honour these exclusions verbatim. Adding to the exclusion list is an operational-tier amendment.

### 7.5 Detection on read

**normative-description.** Secret detection runs primarily on `fs_write` and `net_outbound` (egress). On `fs_read`, the engine does **not** detect secrets in the file content (the file already exists; reading is not a leak). The engine MAY detect secrets in `evidence_refs` payloads when the query envelope embeds them.

### 7.6 Engine invocation order for fs_write

```
1. Schema validation of query envelope (deny on schema_invalid)
2. Forbidden-path check (deny on forbidden_path)
3. Secret regex check (deny on secret_pattern_detected)
4. Secret entropy check (deny on secret_pattern_detected)
5. Sandbox profile compatibility (deny on illegal_target / illegal_actor)
6. Critical Gate check (NEEDS_HUMAN on matching gate)
7. Allow/conditional rule lookup (allow / conditional / default-deny)
```

**normative-description.** The order is fixed and deterministic. Step 2 cannot be skipped on the basis of step 5, and step 3 cannot be skipped on the basis of any subsequent step. Each step is independently testable per Section 8.

### 7.7 non-normative-example -- secret detection on a write

```yaml
# query: actor wants to write a config file containing a high-entropy string
query:
  actor: { id: "executor_helper", authority_class: "ai" }
  action:
    kind: "fs_write"
    detail:
      path: ".ai/sessions/<sid>/DO/dev/config.yaml"
      bytes: 412
      payload_sha256: "<hash>"
      payload_excerpt: "api_key: <high-entropy-32-char-string>"
# verdict
verdict: deny
reason: secret_pattern_detected
evidence_ref:
  rule_id: "secret_pattern_001"
  rule_file: ".ai/policies/safety.yaml"
  rule_anchor: "gates.secrets.patterns[0]"
```

---

## 8. Independence from State Graph

**normative-description.** Article XX (Passive Core) requires that the Policy Engine be a passive evaluator. The structural test of passivity is **independence**: every policy rule MUST be queryable and verifiable **without** instantiating the kernel state machine. This section makes that independence concrete.

### 8.1 The independence invariant

**normative-description.** Given:

- A policy file (`trinity_policy.yaml`).
- A query envelope (Section 4.1).
- The Policy Engine binary.

A test harness MUST be able to compute the verdict envelope **without**:

- Loading any kernel state.
- Reading or writing any session directory under `.ai/sessions/`.
- Loading any graph definition from `.ai/graphs/`.
- Calling any LLM (Pyramid layer 3 is verifier-side, not policy-side).
- Touching the audit chain (the harness inspects the verdict, it does not append).

### 8.2 Conformance test pattern (normative)

```python
# pseudocode -- the actual harness lives in cli/tests/test_policy_engine.py
# (deliverable of a separate Phase 5 sub-session, NOT this spec)

def test_policy_rule_<rule_id>():
    engine = PolicyEngine.load_from_paths(
        safety=".ai/policies/safety.yaml",
        gates=".ai/policies/gates.yaml",
        verifier_rules=".ai/policies/verifier-rules.yaml",  # read-only boundary
        trinity_policy=".ai/policies/trinity_policy.yaml",
    )
    query = make_query(
        actor={"id": "<actor>", "authority_class": "<class>"},
        action={"kind": "<kind>", "detail": {...}},
        target={"type": "<type>", "value": "<value>"},
        context={"session_id": None, "ritual_phase": "none", ...},
    )
    verdict = engine.query(query)
    assert verdict.verdict == "<expected>"
    assert verdict.reason == "<expected-reason>"
    assert verdict.evidence_ref.rule_id == "<expected-rule-id>"
    # No kernel.transition() call. No session dir. No graph load.
```

**normative-description.** Every rule in `trinity_policy.yaml` MUST have at least one positive test (the rule fires) and at least one negative test (the rule does not fire on a near-miss query). Coverage gaps are themselves a constitutional defect under Article XX.

### 8.3 Negative-space test (normative)

**normative-description.** The harness MUST also include an "unknown query" test that asserts default-deny:

```python
def test_unknown_query_is_denied():
    engine = PolicyEngine.load_from_paths(...)
    query = make_query(
        actor={"id": "<unknown-actor>", "authority_class": "ai"},
        action={"kind": "tool_invoke", "detail": {"tool_name": "<unknown-tool>"}},
        target={"type": "tool_name", "value": "<unknown-tool>"},
        context={...},
    )
    verdict = engine.query(query)
    assert verdict.verdict == "deny"
    assert verdict.reason == "unknown_authority"
```

This test enforces Article XVI verbatim.

### 8.4 Phase 3 / Phase 4 boundary

**normative-description.** The Policy Engine reads `verifier-rules.yaml` **only** to confirm two boundary invariants:

1. The verifier's verdict set (`PASS`, `RETRY`, `NEEDS_HUMAN`, `DEAD`) does not collide with the policy verdict set (`allow`, `deny`, `conditional`, `NEEDS_HUMAN`). The shared `NEEDS_HUMAN` token is intentional and means the same thing on both sides: human escalation.
2. No verifier rule attempts to encode a policy decision (e.g. `forbidden_pattern_found` is a verifier rule that consumes a policy result; it does not author one).

The Policy Engine MUST NOT call into the verifier and the verifier MUST NOT call into the Policy Engine for verdict computation. They are siblings.

**normative-description.** Similarly, the Policy Engine MUST NOT load `.ai/graphs/standard.yaml`. The state machine asks the engine "may this transition proceed?" -- the engine answers without knowing what other transitions are legal in the graph.

### 8.5 Verdict-Source Boundary Check

**normative-description.** The `NEEDS_HUMAN` verdict token is intentionally shared between the Policy Engine and the Phase 3 Verifier (Section 8.4). At runtime, that shared token is a **role-collapse risk** under Article IV (Separation of Responsibilities) -- a `NEEDS_HUMAN` produced by a verifier evaluation MUST NOT be silently consumed by the Policy Engine as if the engine itself authored it, and vice versa. To enforce Article IV at the boundary, the Policy Engine MUST verify that any `NEEDS_HUMAN` it consumes from a verifier-side artifact carries `source: "verifier"` in its envelope metadata, and any `NEEDS_HUMAN` the engine itself emits MUST carry `source: "policy"` in the verdict envelope (Section 4.2 amendment for downstream consumers). When the engine is presented with a `NEEDS_HUMAN` lacking a declared `source` -- or carrying a `source` that does not match the artifact's origin -- the engine MUST refuse the input with `deny / schema_invalid` and MUST NOT promote it into a policy verdict. This boundary check is the runtime expression of Article IV; without it, a verifier verdict could be transposed into a policy decision (or the reverse) and the role separation would silently dissolve.

### 8.6 Cross-spec co-authorship note

**normative-description.** Phase 3 (`TRINITY_VERIFICATION_CONTRACT_SPEC_V1`) and Phase 4 (`TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1`) are co-authored alongside this spec in the same parallel session bundle. The three documents establish the orthogonal axes of Trinity governance:

- Phase 3: "Did the artifact match the criteria?" (verifier)
- Phase 4: "Is this transition declared in the graph?" (state machine)
- Phase 5: "Is this actor permitted to attempt it?" (this spec)

Conflicts between the three are resolved per Article XXV (higher rank wins) and via the Article XXIX amendment procedure. Cross-references between specs MUST be by stable spec id, not by line number.

### 8.7 non-normative-example -- a passing conformance run

```
$ cd .ai && python3 -m pytest cli/tests/test_policy_engine.py -q
.....................................                                       [100%]
37 passed in 0.41s
no kernel state instantiated
no session directory touched
no graph loaded
no LLM called
```

---

## 9. Versioning & Article XXIX Amendment Protocol

**normative-description.** Policy is a Canonical Policies instrument (Article XXV rank 3). Every change to `.ai/policies/**` is an amendment under Article XXIX, classified per Constitutional Addendum v1.0.4 into editorial / operational / constitutional tiers. This section is the operational protocol.

### 9.1 Tier classification for policy edits

| Edit class | Tier | Examples |
|---|---|---|
| Typo fix in a comment, ASCII normalisation, link target update with no semantic change | editorial (XXIX.1) | "Fix spelling in `safety.yaml` rationale comment" |
| Add a new rule, modify a threshold, add a forbidden_path glob, add a secret pattern, add a Critical Gate, change a reason code | operational (XXIX.2) | "Add `gate.external_publication` to Critical Gates list" |
| Remove a Critical Gate, remove a forbidden_path that maps to a Constitutional article, redefine the verdict set, redefine default-deny | constitutional (XXIX.3) | "Change default-deny stance" (would itself violate Article XVI) |

**normative-description.** When in doubt, classify upward (Addendum v1.0.4 XXIX.6). Misclassification toward a lower tier is a constitutional violation and triggers retroactive reclassification under XXIX.6.

### 9.2 The six-step amendment procedure (verbatim, restated)

**normative-description.** Article XXIX requires every amendment to satisfy:

```text
explicit proposal
rationale
impact analysis
human approval
version bump
audit entry
```

For policy files specifically:

1. **Explicit proposal.** A diff against the current policy file, reviewable in git.
2. **Rationale.** For editorial: 1-3 sentences in the commit body. For operational and constitutional: full sections in a sibling document.
3. **Impact analysis.** Identify every kernel call site that reads the affected rule. Identify every session in flight that may be affected.
4. **Human approval.** `decided_by: human` envelope. AI may propose; AI MUST NOT decide.
5. **Version bump.** Bump the `version` field in the affected policy file's frontmatter (`safety.yaml`, `gates.yaml`, `verifier-rules.yaml`, `trinity_policy.yaml`). Bump is independent per file.
6. **Audit entry.** Append `policy.amended` event (one per amendment) with tier discriminator: `policy.amended.editorial`, `policy.amended.operational`, `policy.amended.constitutional`.

### 9.3 Trace-to-failure (Addendum v1.0.4 XXIX.4)

**normative-description.** Operational and constitutional policy amendments MUST trace to a concrete signal: a session id where the missing rule caused friction, an audit event id, an observed leak, a measurable risk artifact, or a named safety requirement. The trace is part of the rationale; a missing trace returns the proposal to the proposer for amendment.

### 9.4 Audit entry shape for policy amendments

```json
{
  "ts": "<iso-8601-utc>",
  "seq": <integer>,
  "event": "policy.amended.<tier>",
  "actor": "<operator-id>",
  "policy_file": "<path>",
  "diff_sha256": "<sha256>",
  "tier": "<editorial|operational|constitutional>",
  "rationale_ref": "<commit-hash-or-doc-path>",
  "trace_ref": "<session-id-or-audit-seq-or-doc>",
  "version_before": "<string>",
  "version_after": "<string>",
  "prev_hash": "<sha256>",
  "hash": "<sha256>"
}
```

**normative-description.** The event format aligns with Addendum v1.0.4 XXIX.5 verbatim. The audit chain is append-only; mistakes are corrected by new entries, not by mutation.

### 9.5 Session-Context Carry

**normative-description.** Every policy query envelope MUST include the `session_id` field already declared in `context.session_id` (Section 4.1). The `query_id` (Section 4.1, 4.2) is an audit-grade ULID generated by the caller; the kernel MUST log the pair `(query_id, session_id)` in the refusal audit event (Section 5.3, the `session_id` field is already present in the event shape). This pairing is the audit-trace primitive that lets a downstream operator answer "which session originated this policy query?" by joining `policy.refused.query_id` to `session.created.query_id`-or-equivalent in the audit chain. Queries that arise outside any session (e.g. kernel boot self-checks) MUST set `session_id: null` explicitly; the field is required, the value MAY be null. A missing `session_id` field (as opposed to an explicit null) returns `deny / schema_invalid` per Section 4.1.

### 9.6 Stale-Rule Audit Query Pattern

**normative-description.** Detection of stale rules (Section 9.7) currently requires a manual operator audit query against the audit chain. The recommended pattern is:

```
bash .ai/cli/ai audit query --rule-id=<rule_id> --since=<window>
```

The query returns the count of `policy.refused` and `policy.gate_required` events that cite the supplied `rule_id` within the supplied window. A zero count, combined with a `last_reviewed` timestamp older than the staleness threshold, identifies a candidate stale rule for human review. This pattern is **manual** in v1.0; in v1.1 it is marked **automatable** -- a kernel-side `policy.engine.scan_stale` boot check MAY emit `policy.stale_rule_detected` events without operator invocation, provided the scan itself is bounded, observable, interruptible, and auditable (Article XX). Until v1.1 lands the automation, operators SHOULD run the manual query at amendment-review cadence (illustrative: weekly during active development, monthly during steady state).

### 9.7 Migration of stale rules

**normative-description.** A rule is **stale** when its `last_reviewed` field is older than the operator-configured staleness threshold (illustrative default: 365 days) **and** the rule has not fired in audit history during that window. Stale rules MUST NOT be silently deleted. They are flagged at engine boot:

```
[policy.engine] stale rules detected (threshold: 365 days, no fires in window):
  - rule_pol_055 (.ai/policies/trinity_policy.yaml:rules.legacy.foo) last_reviewed=2024-09-12
  - rule_pol_061 (.ai/policies/safety.yaml:hard_blocks[3]) last_reviewed=2024-08-30
  human review required (Article XXIX); see policy.amendment_required reason code.
```

**normative-description.** A query that matches a stale rule returns `deny` with reason `amendment_required` (Section 2.4). The kernel surfaces this to the operator, who either re-confirms the rule (operational amendment, refreshing `last_reviewed`) or removes it (operational or constitutional amendment per Section 9.1). Auto-deletion is forbidden by Article XX.

### 9.8 What the engine itself versions

**normative-description.** The Policy Engine binary carries an `engine_version` (currently `"1.0"`). A bump in engine version is a code change, not a policy amendment, and follows the Phase 4 / Phase 5 sibling code-change procedure (its own session, its own verifier pass, its own ddd gate). The engine version is emitted in every verdict envelope (Section 4.2) so amendments can correlate verdicts to engine releases.

### 9.9 non-normative-example -- an operational amendment

```
1. Operator drafts diff: add gate.external_publication to Critical Gates list.
2. Trace: session 01J7AB...; rationale: a sibling tool attempted an unaudited
   webhook POST that should have been gated.
3. Impact analysis: kernel re-checks every net_outbound query against the new
   gate; in-flight sessions inherit the new gate at next query.
4. Human approval: ddd-packet approved; decided_by: human envelope written.
5. Version bump: trinity_policy.yaml frontmatter version 1.4 -> 1.5.
6. Audit entry: policy.amended.operational seq=10712.
```

---

## 10. Glossary Cross-Refs

**normative-description.** Terms introduced or refined by this spec are listed below with cross-refs to `docs/specs/12_GLOSSARY.md`. Where a term is new, the definition is normative; where a term already exists in the glossary, this spec defers to that definition.

### 10.1 New terms (normative definitions)

| Term | Definition |
|---|---|
| **Policy verdict** | A member of the closed set `{allow, deny, conditional, NEEDS_HUMAN}` returned by the Policy Engine in response to a query envelope. The only legitimate output of the engine. (Section 2.1) |
| **Query envelope** | The schema-validated structured input to `policy.query(...)`. Carries actor, action, target, and context. (Section 4.1) |
| **Verdict envelope** | The schema-validated structured output of `policy.query(...)`. Carries verdict, reason, evidence_ref, and optionally conditions / human_gate. (Section 4.2) |
| **Default-deny** | The terminal fallback verdict when no policy rule matches the query envelope. Implements Article XVI verbatim. (Section 2.3) |
| **Least Authority binding** | The runtime instantiation of Article XVI: an actor's effective permissions are the intersection of (declared sandbox profile) and (matching policy rules), minus (forbidden_paths and Critical Gates). (Sections 5.1, 6.1, 7.1) |
| **Critical Gate** | An action class that always returns `NEEDS_HUMAN` regardless of actor, profile, or session state. Each gate maps to one or more Constitutional articles. (Section 6.1) |
| **Refusal audit event** | An append-only event in `.ai/audit/events.ndjson` of type `policy.refused` or `policy.gate_required`, carrying the verdict envelope's structured fields. (Section 5.3) |
| **Stale rule** | A policy rule whose `last_reviewed` is older than the staleness threshold and which has not fired in the audit window. Returns `deny` with reason `amendment_required`. (Section 9.7) |
| **Independence invariant** | The structural property that any policy rule is queryable and verifiable without loading the kernel state machine, the graph, the session directory, or any LLM. (Section 8.1) |

### 10.2 Existing glossary terms used in this spec (deferred to glossary)

| Term | Glossary anchor |
|---|---|
| Artifact | `12_GLOSSARY.md#artifact` (Article 0 §1) |
| Verification | `12_GLOSSARY.md#verification` (Article 0 §2) |
| Authority | `12_GLOSSARY.md#authority` (Article 0 §4) |
| Canonical | `12_GLOSSARY.md#canonical` (Article 0 §5) |
| `decided_by: human` envelope | `12_GLOSSARY.md#decided-by-human` (Article XIII) |
| Pyramid of Judgment | `12_GLOSSARY.md#pyramid-of-judgment` (verifier-rules.yaml) |
| Audit chain / hash chain | `12_GLOSSARY.md#audit-chain` (Article X, `TRINITY_AUDIT_EVENT_SPEC_V1`) |
| Sandbox profile | `12_GLOSSARY.md#sandbox-profile` (`TRINITY_SANDBOX_CAPABILITY_SPEC_V1`) |
| Tool capability | `12_GLOSSARY.md#tool-capability` (`TRINITY_TOOL_CAPABILITY_MODEL_V1`) |
| Ritual phase | `12_GLOSSARY.md#ritual-phase` (Article XI; Ritual Constitution v1.1) |

### 10.3 Glossary maintenance

**normative-description.** New terms in Section 10.1 MUST be appended to `docs/specs/12_GLOSSARY.md` in a follow-up session. The append is an operational-tier amendment under Article XXIX (the glossary is rank 5: a Workflow Contract). This spec does **not** edit the glossary file; cross-spec edits are out of scope per the parallel-bundle constraints.

### 10.4 Cross-spec ID map

| This spec section | Cross-references |
|---|---|
| 1 (Constitutional anchor) | `TRINITY_CONSTITUTION_V1.md` Articles III, IV, XIII, XVI, XX, XXIX |
| 2 (Surface vocabulary) | `verifier-rules.yaml.verdicts` (boundary check only) |
| 3 (File catalog) | `safety.yaml`, `gates.yaml`, `verifier-rules.yaml`, `trinity_policy.yaml` (Phase 5 deliverable) |
| 4 (Query API) | `.ai/schemas/policy_query_envelope.v1.yaml` (separate human deliverable) |
| 5 (Blocking semantics) | `TRINITY_AUDIT_EVENT_SPEC_V1`, memory anchor `feedback_executor_helper_forbidden_writes_drift` |
| 6 (Critical Gates) | `TRINITY_DDD_HUMAN_GATE_SPEC_V1`, Articles XIII / XIV |
| 7 (Forbidden paths and secrets) | `safety.yaml.gates.secrets`, `safety.yaml.hard_blocks` |
| 8 (Independence) | `TRINITY_VERIFICATION_CONTRACT_SPEC_V1` (Phase 3 sibling), `TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1` (Phase 4 sibling), `.ai/graphs/standard.yaml` (NOT loaded) |
| 9 (Amendment) | `TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md` XXIX.1 through XXIX.6 |
| 10 (Glossary) | `docs/specs/12_GLOSSARY.md` |

---

## Appendix A -- Acceptance Criteria for Phase 5

**normative-description.** Per `trinity_organ_refactor_prd.md` §9 Phase 5, this spec satisfies the Phase 5 acceptance items as follows:

| PRD acceptance | Where addressed |
|---|---|
| Kernel queries policy before transition / tool call | Section 4.3 (caller contract) |
| Policy can block tool use | Section 5.1 (table row: tool invocation, both deny and NEEDS_HUMAN columns) |
| Policy rules are testable independent of state graph | Section 8 (independence invariant + conformance pattern) |

**normative-description.** The PRD also lists four deliverables for Phase 5:

1. `.ai/policies/trinity_policy.yaml` -- **NOT authored by this spec**; separate human-authored deliverable per Article III.
2. policy validator -- this spec defines the contract; the validator code is a separate Phase 5 sub-session deliverable.
3. critical gate rules -- defined normatively in Section 6.
4. forbidden path and secret rules -- shape and invocation defined normatively in Section 7.

This spec covers the deliverable contract for items 2, 3, and 4. Item 1 is intentionally outside scope per Article III and Article XIII.

---

## Appendix B -- Conformance Checklist (operator-facing)

**normative-description.** Before any session lands a change to `.ai/policies/**`, the operator MUST be able to answer "yes" to every item below:

```
[ ] The amendment is classified into a tier (editorial / operational / constitutional)
    per Addendum v1.0.4 XXIX.1-XXIX.3.
[ ] If operational or constitutional: a trace-to-failure reference is present
    (session id, audit seq, friction event, or named risk).
[ ] The diff is reviewable in git (no binary blobs in policy files).
[ ] Impact analysis identifies every kernel call site that reads the affected rule.
[ ] A decided_by: human envelope is prepared (or, for editorial, a commit body
    rationale of 1-3 sentences is prepared).
[ ] The version field in the affected policy file's frontmatter is bumped.
[ ] The corresponding policy.amended.<tier> audit event format is ready
    (engine wires the emit; operator writes the diff).
[ ] No new rule violates default-deny semantics (Section 2.3).
[ ] No new rule attempts to encode a verifier decision (Section 8.4).
[ ] No new rule attempts to encode a state-machine transition (Section 8.4).
```

**normative-description.** A failed checklist item returns the amendment to the proposer per Addendum v1.0.4 XXIX.4 ("an amendment lacking a trace is RETURNED, not refused").

---

## Appendix C -- Failure Modes & Remediation

**normative-description.** Documented failure modes for the Policy Engine, drawn from Trinity operational memory and from the constraints above.

| Failure mode | Symptom | Remediation |
|---|---|---|
| Engine boot with a missing canonical file | engine refuses to start; kernel cannot launch | Restore the file; verify sha256 against last known good audit event |
| Schema-invalid query envelope | engine returns `deny / schema_invalid` | Caller fixes the envelope; do not relax the schema |
| Default-deny on a routine action | engine returns `deny / unknown_authority` for a query the operator believes should be allowed | Author an explicit allow rule via operational amendment (Section 9); do not weaken default-deny |
| Stale rule firing as `amendment_required` | recurring deny on previously-allowed action | Re-confirm or amend the rule per Section 9.7 |
| Critical Gate misclassified as deny | Critical action returns `deny` instead of `NEEDS_HUMAN` | Operational amendment to add the action's matching gate to Section 6.1 enumeration |
| forbidden_path silently overridden by sandbox grant | write succeeds despite forbidden glob match | Constitutional violation under Article XVI; emit `policy.violation_detected`, halt session, audit retroactive reclassification per Addendum v1.0.4 XXIX.6 |
| Two policy files declare the same rule with different verdicts | nondeterministic verdict | Engine refuses to boot; operator resolves the conflict in a Section 9 amendment |
| Audit chain hash mismatch on `policy.refused` | chain corruption suspected | Halt the session; run `bash .ai/cli/ai audit verify-chain`; treat as `gate.audit_truncation` (Section 6.1) |

---

## Appendix D -- Quote-Cited Constitutional Anchors (consolidated)

**normative-description.** For the convenience of downstream readers, the six articles cited in Section 1 are listed here with verbatim text and the section in this spec where they are load-bearing:

```
Article III   -- AI Cannot Govern Itself
              -- Section 1.1, 3.2, 6.1 (gate.policy_amendment), 6.2, 9.2 step 4
Article IV    -- Separation of Responsibilities
              -- Section 1.2, 1.7, 8.4
Article XIII  -- Human Authority
              -- Section 1.3, 6 (entire), 9.2 step 4, Appendix B
Article XVI   -- Least Authority
              -- Section 1.4, 2.3, 7.2, 8.3, Glossary 10.1 (Least Authority binding)
Article XX    -- Passive Core Principle
              -- Section 1.5, 8 (entire), 9.5 (no auto-deletion)
Article XXIX  -- Constitutional Amendment
              -- Section 1.6, 9 (entire), Addendum v1.0.4 references
```

---

## Final Lock

```
The Policy Engine proposes verdicts.
The Kernel enforces them.
The Human decides Critical Gates.
The Audit chain remembers everything.
```

Any implementation that allows policy to:

```
- be silently amended
- be silently bypassed by a sandbox grant
- auto-approve a Critical Gate on timeout
- merge with the verifier or the state machine
- evaluate via LLM
- silently delete stale rules
```

is not Trinity policy.

---

**End of TRINITY_POLICY_ENGINE_SPEC_V1**
