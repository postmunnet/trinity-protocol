---
title: "Trinity Ritual Constitution v1.1"
version: "1.1"
status: FINAL
ratified_from: "v1.1-rc"
ratified_at: "2026-05-13"
last-updated: "2026-05-13"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
parent: "TRINITY_CONSTITUTION_V1.md"
child_layers:
  - "TRINITY_RITUAL_CONTRACT_V1.md (operational per-ritual table for the 7 canonical rituals)"
related:
  - "TRINITY_CONSTITUTION_V1.md (Article XXV priority chain; Article XXIX amendment process)"
  - "TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md §B (Decision Velocity Tiers)"
  - "TRINITY_ORGAN_MAP_V1.md (organ definitions)"
genesis:
  trust_status: "GENESIS_TRUST_ASSUMED"
  founder_declaration: |
    This document is a Genesis artifact under Article XIII of Trinity Ritual
    Constitution v1.1-rc. It was authored by the Founder/Operator before a
    fully ratified Trinity Ritual Constitution process existed; therefore its
    initial authority is declared, not derived from prior ratification.
  author_identity: "Operator (Founder / Trinity Architect)"
  creation_timestamp_utc: "2026-05-12T17:01:50Z"
  body_sha256: "fbb0cabc55127843e12c9b87626dee2e8af287e9b59a2758ff96a1b770b89f65"
  body_sha256_extraction: "sha256 of everything after the closing YAML frontmatter delimiter ('^---$' line #2), including the conventional blank line that follows it. Reproduce with: awk 'BEGIN{skip=1;cnt=0} /^---$/ && skip {cnt++; if(cnt==2){skip=0;next}} !skip {print}' <file> | shasum -a 256"
  body_bytes: 34383
  body_lines: 1929
  scope: "Ritual runtime, delegated cognition, templates, Kernel checks, and state transitions across the canonical Trinity ritual set (sss, vvv, nnn, gogogo, ddd, rrr, close)."
  version: "1.1-rc"
  reason_for_genesis_status: |
    Trinity has no prior Ritual Constitution to ratify this one against.
    Constitution v1.0 (governance) and Ritual Contract v1.0 (operational
    per-ritual table) exist, but no higher-level rule layer defining the
    three-template (Context / Write / Check) model has been locked. This
    document supplies that layer; until at least one real workflow runs
    end-to-end under these rules (Article XII.5), the status remains
    RC_PENDING_EMPIRICAL_RATIFICATION and must not be marked OFFICIAL.
  initial_audit_event_ref:
    session_id: "0001_2026-05-12_23_46_pm_feat-feat-ritual-constitution-v1"
    most_recent_audit_hash_at_creation: "ddddf39df04a7c94c243a5d91010d01b081599a862c482ab74c22db5ec779a6c"
    most_recent_audit_type_at_creation: "graph.transition"
    most_recent_audit_ts_at_creation: "2026-05-12T17:01:06Z"
ratification:
  status: "RATIFIED"
  ratified_as: "v1.1"
  ratified_at: "2026-05-13"
  superseded_status: "RC_PENDING_EMPIRICAL_RATIFICATION (v1.1-rc, 2026-05-12)"
  empirical_test_workflow_evidence:
    - "commit 04bb74f (per-ritual loader integration — sss/vvv/nnn/gogogo/ddd/rrr code paths consume their packs; 768 pytest green)"
    - "commit 5ce7b88 (close.py wired + gogogo event-name alignment + executor_helper prompt unblocked; 776 pytest green)"
    - "live smoke-test session 0001_2026-05-13_14_56_pm_feat-smoke-test-full-loop-integration (full ritual chain ran with all 7 .invoked events landing in the audit chain without bypass)"
  unlock_conditions_satisfied:
    - "All required rituals for the test workflow executed (sss/vvv/nnn/gogogo/ddd/rrr/close)"
    - "Required artifacts produced (RETRO.md, retro index in memory-cli, 03_ACCEPTANCE.yaml, plan.json, etc.)"
    - "Check templates used (loader honored .ai/rituals/<r>/ packs at runtime)"
    - "Failures visible (vvv.failed / nnn.failed / gogogo.step_failed branches present and tested)"
    - "Retry/escalation tested (audit chain shows no NEEDS_HUMAN escalations in the smoke test workflow; mechanism present)"
    - "Final audit exists (.ai/audit/events.ndjson hash-chained, append-only, genesis intact)"
    - "Operator confirmed workflow was not bypassed due to excessive friction (2026-05-13, 'ทำหมดตามลำดับ' directive)"
  amendment_record: "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md"
---

# TRINITY RITUAL CONSTITUTION v1.1

## Ratified — Article XII.5 Empirical Gate Satisfied

**Status:** `RATIFIED`
**Canonical Scope:** Ritual runtime, delegated cognition, templates, Kernel checks, and state transitions
**Ratified from:** `v1.1-rc` (2026-05-12) → `v1.1` (2026-05-13)
**Amendment record:** [`addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md`](addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md)

This document incorporates the panel convergence: approve v1.1-rc with patches XIII-XVIII and approve Article XII.5. The empirical gate (Article XII.5) was satisfied by the per-ritual loader integration work landed in commits `04bb74f` + `5ce7b88` and the live smoke-test session referenced in the frontmatter `empirical_test_workflow_evidence` block. The historical `RC_PENDING_EMPIRICAL_RATIFICATION` status is preserved in the frontmatter for audit-trail continuity.

---

# Preamble

Trinity rituals are not commands.

A Trinity ritual is:

```text
A constitutional workflow stage
where Kernel prepares context,
delegates semantic work to an agent,
receives artifacts,
validates them against a template,
emits audit,
and controls state transition.
```

Kernel does not create meaning.
Kernel does not write lessons.
Kernel does not decide semantic truth.
Kernel does not act as Planner, Executor, Verifier, Memory, Retro Writer, or Human Approver.

Kernel enforces:

```text
template
checklist
state
authority
audit
gate
```

Agents produce meaning-bearing artifacts.
Humans ratify irreversible consequence.
Artifacts preserve operational truth.
Audit preserves history.

---

# Article I — Core Ritual Model

Every ritual MUST have three canonical template layers:

```text
1. Context Template
2. Write Template
3. Check Template
```

## 1. Context Template

Generated by Kernel.

Purpose:

```text
Provide deterministic evidence and session data
to the delegated agent.
```

Examples:

```text
audit events
graph state
acceptance result
diff result
test output
session metadata
known blockers
allowed paths
risk tier
```

The delegated agent MUST NOT invent missing context.

---

## 2. Write Template

Used by the delegated agent.

Purpose:

```text
Tell the agent what artifact to write,
what sections to fill,
what evidence to cite,
and what claims are forbidden.
```

A write template MAY contain placeholders such as:

```text
{{session.id}}
{{session.goal}}
{{artifacts}}
{{acceptance.results}}
{{known_blockers}}
```

---

## 3. Check Template

Used by Kernel.

Purpose:

```text
Validate the artifact structurally and constitutionally.
```

Kernel checks:

```text
- required files exist
- required sections exist
- required fields exist
- evidence references exist
- forbidden phrases/actions are absent
- authority boundaries are respected
- state transition is legal
- audit was emitted
```

Kernel does not judge whether the agent's prose is brilliant.
Kernel judges whether the ritual was constitutionally completed.

---

# Article II — Template Authority

All ritual templates are canonical artifacts.

Templates MUST be:

```text
- versioned
- hashed
- auditable
- signed or ratified when used in governance-critical paths
```

Agents MUST NOT modify ritual templates during runtime.

Runtime-generated templates have no authority unless explicitly ratified.

---

# Article III — Ritual Execution Algorithm

Every ritual follows this runtime algorithm:

```text
1. Kernel loads ritual contract.
2. Kernel validates template version/hash.
3. Kernel builds deterministic context.
4. Kernel delegates semantic work to the assigned role.
5. Agent fills write template.
6. Agent returns artifact.
7. Kernel validates artifact against check template.
8. Kernel emits audit.
9. Kernel transitions state if valid.
10. Kernel blocks, degrades, retries, or escalates if invalid.
```

---

# Article IV — Shared Template Pack Format

Every ritual SHOULD use this structure:

```text
.ai/rituals/<ritual>/
  ritual.contract.json
  context.schema.json
  write.template.md
  check.template.json
```

Example:

```text
.ai/rituals/rrr/
  ritual.contract.json
  retro_context.schema.json
  retro_write.template.md
  retro_check.template.json
```

---

# Article V — Shared Ritual Contract Schema

```json
{
  "ritual": "string",
  "version": "1.0",
  "purpose": "string",
  "delegated_role": "string | null",
  "input_context": "string",
  "write_template": "string | null",
  "check_template": "string",
  "output_artifacts": ["string"],
  "required_checks": ["string"],
  "forbidden_actions": ["string"],
  "allowed_current_states": ["string"],
  "allowed_next_states": ["string"],
  "audit_events": ["string"],
  "retry_policy": {
    "max_retries": 3,
    "retry_owner": "same_delegated_role",
    "escalate_to": "NEEDS_HUMAN",
    "preserve_failed_attempts": true,
    "audit_each_attempt": true
  }
}
```

---

# Article VI — Shared Check Template Schema

```json
{
  "check_template_version": "1.0",
  "required_artifacts": [],
  "required_headings": [],
  "required_fields": {},
  "required_evidence_refs": {},
  "required_structural_predicates": [],
  "required_phrases": [],
  "forbidden_phrases": [],
  "forbidden_actions": [],
  "allowed_roles": [],
  "forbidden_roles": [],
  "state_transition": {
    "from": [],
    "to": []
  },
  "failure_behavior": {
    "on_missing_artifact": "BLOCK",
    "on_missing_evidence": "BLOCK",
    "on_forbidden_phrase": "BLOCK",
    "on_optional_failure": "WARN"
  }
}
```

`required_structural_predicates` SHOULD be preferred over brittle phrase matching when possible.

Example:

```json
{
  "predicate": "memory_handling.mode == index",
  "required": true
}
```

---

# Article VII — Ritual Registry

Canonical rituals:

```text
sss      = session initialization
vvv      = clarification / understanding
nnn      = planning / verification contract
gogogo   = bounded execution
ddd      = decision / deploy gate
rrr      = retrospective / closure
close    = seal session
```

Each ritual MUST define:

```text
- who writes
- what is written
- what Kernel checks
- what transition is allowed
```

---

# Article VIII — Kernel Validation Boundaries

Kernel MAY validate:

```text
- artifact existence
- schema validity
- heading presence
- field presence
- evidence reference existence
- forbidden phrase/action absence
- state legality
- role legality
- authority legality
- audit emission
```

Kernel MUST NOT validate:

```text
- philosophical correctness
- semantic genius
- emotional quality
- final meaning of lessons
- business wisdom
```

Semantic content may be advisory.
Authority requires human or canonical ratification.

---

# Article IX — Evidence Reference Rule

Any meaning-bearing claim in an agent-written artifact SHOULD include evidence reference.

Evidence references MAY be:

```text
- artifact path
- line range
- byte range
- sha256
- audit event id
- verifier report id
```

A claim without evidence may remain in the artifact only if tagged:

```text
ADVISORY
UNSUPPORTED
HYPOTHESIS
```

---

# Article X — Ritual Failure Rule

If a ritual output fails its check template:

```text
Kernel MUST NOT silently transition state.
```

Allowed responses:

```text
BLOCK
WARN
DEGRADED
NEEDS_HUMAN
FAILED
TERMINAL_FAILED
```

Failure is acceptable.
Invisible failure is unconstitutional.

---

# Article XI — Memory Boundary Rule

Memory-related ritual output MUST use exact artifact handling.

Allowed:

```text
memory-cli index <artifact>
memory-cli search <query>
memory-cli pack <query>
memory-cli pin <artifact> --as <name> only by human decision
```

Forbidden in core rituals:

```text
memory-cli learn
auto-tag
auto-embed
auto-confidence
auto-pin
semantic memory mutation
```

Memory indexing preserves history.
Memory pinning confers authority.

---

# Article XII — Ritual Template Integrity

No ritual is valid without:

```text
context template
write template
check template
output artifact
audit event
state transition rule
```

If any of these are missing:

```text
ritual != constitutionally complete
```

---

# Article XII.5 — Empirical Ratification Principle

No ritual constitution version may be marked `OFFICIAL` until it has been successfully executed end-to-end on at least one real workflow.

A ritual constitution that has not passed real execution MUST be tagged:

```text
UNTESTED_THEORETICAL_DRAFT
```

A release candidate MAY be tagged:

```text
RC_PENDING_EMPIRICAL_RATIFICATION
```

A ritual constitution may be marked `OFFICIAL` only after:

```text
- all required rituals for the selected workflow have executed
- required artifacts were produced
- check templates were used
- failures were visible
- retry/escalation behavior was tested or explicitly not applicable
- final audit exists
- operator confirms that the workflow was not bypassed due to excessive friction
```

This principle applies recursively.

Amendments to an official ritual constitution MUST survive at least one real ritual cycle before being marked official.

```text
A ritual constitution that has never passed a ritual
must not be treated as final truth.
```

---

# Article XIII — Genesis Protocol

Initial ritual templates, root policies, and constitutional artifacts created before a ratified Trinity process exists MUST be marked:

```text
GENESIS_TRUST_ASSUMED
```

Genesis artifacts MUST include:

```text
- founder declaration
- creation timestamp
- sha256 hash
- author identity
- scope
- version
- initial audit entry
- reason for genesis status
```

Genesis artifacts MUST NOT pretend to have been ratified by a process that did not yet exist.

Genesis trust is declared, not hidden.

---

# Article XIV — Ritual Velocity Tiers

Trinity rigor MUST be proportional to risk, reversibility, and blast radius.

## HOT PATH

Low-risk, reversible, exploratory work.

Required rituals:

```text
sss-minimal
gogogo
close
```

Optional:

```text
vvv
nnn
ddd
rrr
```

`rrr` is required only if failure, policy learning, governance concern, or user request occurs.

---

## WARM PATH

Meaningful but reversible work.

Required rituals:

```text
sss
nnn
gogogo
ddd-light
rrr
close
```

`vvv` is required if ambiguity exists.

---

## COLD PATH

Governance, security, production, irreversible, or high-consequence work.

Required rituals:

```text
sss
vvv
nnn
gogogo
ddd
rrr
close
```

No ritual may be skipped unless break-glass is invoked.

Principle:

```text
Trinity rigor is reserved for durable mistakes.
```

---

# Article XIV.1 — Tier Escalation Rule

A workflow MAY escalate:

```text
HOT → WARM → COLD
```

when new evidence reveals:

```text
- higher risk
- broader blast radius
- security implication
- production impact
- governance impact
- irreversible consequence
```

Escalation may be proposed by:

```text
Kernel
Verifier
Planner
Human Operator
```

Only Kernel may record tier transition.

Downgrade from `COLD → WARM` or `WARM → HOT` requires explicit human approval.

Escalation MUST be auditable.

---

# Article XV — Retry and Revision Policy

A failed ritual check MUST produce a visible failure result.

Each ritual template MUST define:

```text
- max_retries
- retry_owner
- escalation_state
- failed_attempt_preservation
- audit behavior
```

Default retry policy:

```json
{
  "max_retries": 3,
  "retry_owner": "same_delegated_role",
  "escalate_to": "NEEDS_HUMAN",
  "preserve_failed_attempts": true,
  "audit_each_attempt": true
}
```

After max retries, Kernel MUST NOT silently continue.

---

# Article XV.1 — Retry Context Rule

On retry, the delegated agent MAY see:

```text
- failed check id
- failure reason
- required missing artifact/section
- relevant evidence refs
```

The delegated agent SHOULD NOT receive unlimited prior failed prose unless explicitly allowed.

This reduces minor-tweak gaming.

All failed attempts MUST be preserved as artifacts.

---

# Article XV.2 — Session Revival Rule

A workflow may transition:

```text
FAILED → PLAN
```

only a limited number of times.

Default:

```text
max_revivals = 3
```

After max revivals, Kernel MUST transition to:

```text
TERMINAL_FAILED
```

unless a human operator invokes break-glass or explicitly opens a new workflow.

---

# Article XVI — Template Injection Protection

All placeholder substitution MUST be escaped according to field type.

User-controlled values MUST NOT be injected into templates as executable instructions.

Fields MUST be typed:

```text
plain_text
markdown_escaped
json_string
path
enum
code_block
evidence_ref
```

Kernel MUST preserve user text as data, not instruction.

Example:

```text
{{session.goal}} is data.
It MUST NOT be interpreted as a new system instruction.
```

---

# Article XVII — Consolidated State Machine

Canonical states:

```text
READY
THINK
PLAN
SANDBOX
EXECUTE
VERIFY
NEEDS_HUMAN
PROMOTE
DEPLOY
RETRO
DONE
SEALED
FAILED
DEGRADED
ABORTED
REOPENED
TERMINAL_FAILED
```

Allowed baseline transitions:

```text
READY → THINK
THINK → PLAN
PLAN → SANDBOX
SANDBOX → EXECUTE
EXECUTE → VERIFY
VERIFY → PROMOTE
VERIFY → NEEDS_HUMAN
VERIFY → FAILED
NEEDS_HUMAN → PROMOTE
NEEDS_HUMAN → PLAN
PROMOTE → DEPLOY
DEPLOY → RETRO
RETRO → DONE
DONE → SEALED
FAILED → PLAN
FAILED → ABORTED
FAILED → TERMINAL_FAILED
DONE → REOPENED
REOPENED → PLAN
DEGRADED → NEEDS_HUMAN
DEGRADED → FAILED
```

Any transition not listed is illegal unless explicitly allowed by signed state policy.

---

# Article XVIII — Role-to-Ritual Permission Matrix

| Role                     | sss          | vvv          | nnn               | gogogo       | ddd            | rrr          | close        |
| ------------------------ | ------------ | ------------ | ----------------- | ------------ | -------------- | ------------ | ------------ |
| Human Operator           | request      | answer       | approve if needed | request      | approve/reject | request/pin  | request      |
| Kernel                   | execute      | execute      | execute           | execute      | execute        | execute      | execute      |
| Session Initializer      | write        | no           | no                | no           | no             | no           | no           |
| Clarification Agent      | no           | write        | no                | no           | no             | no           | no           |
| Planning Agent           | no           | assist       | write             | no           | no             | no           | no           |
| Executor Agent           | no           | no           | no                | write        | no             | no           | no           |
| Verifier Agent           | no           | no           | no                | no           | write          | no           | no           |
| Presentation Synthesizer | no           | no           | no                | no           | write          | no           | no           |
| Retro Writer             | no           | no           | no                | no           | no             | write        | no           |
| Memory CLI               | no           | no           | no                | no           | no             | index only   | no           |
| Transport                | request only | request only | request only      | request only | request only   | request only | request only |

Rules:

```text
Agents write artifacts.
Only Kernel transitions state.
Transport requests only.
Memory indexes; it does not learn.
```

For v1.1-rc, `Human Operator` is sufficient.

v1.2 MUST split human roles into:

```text
HUMAN_OPERATOR
HUMAN_APPROVER
ROOT_RATIFIER
DOMAIN_CURATOR
```

---

# Ritual Specifications

---

# 1. `sss` — Session Initialization Ritual

## Purpose

```text
Create constitutional workflow identity.
```

A workflow begins as a semantic proposal, not as a folder.

Kernel may create workflow identity.
Kernel may not invent workflow meaning.

## Delegated Role

```text
SESSION_INITIALIZER
```

## Context Template: `sss_context.json`

```json
{
  "user_intent": "{{raw_user_intent}}",
  "project_root": "{{project_root}}",
  "timestamp_utc": "{{timestamp}}",
  "caller": "{{actor}}",
  "available_policy_refs": [],
  "current_project_state": {}
}
```

## Write Template: `sss_write.template.md`

```md
# SESSION INITIALIZATION

## 1. Proposed Session Title

{{session_title}}

## 2. Initial Goal

{{goal}}

## 3. Workflow Type

{{workflow_type}}

## 4. Risk Tier

{{risk_tier}}

Allowed:
- HOT
- WARM
- COLD

## 5. Initial Scope

{{initial_scope}}

## 6. Assumptions

{{assumptions}}

## 7. Open Questions

{{open_questions}}

## 8. Suggested Tags

{{tags}}

## 9. Session Initializer Provenance

- Author Role: SESSION_INITIALIZER
- Advisory Only: true
- Context Ref: {{sss_context_sha256}}
```

## Check Template: `sss_check.template.json`

```json
{
  "required_artifacts": [
    "session_init.md",
    "session_manifest.json",
    "graph_state.json",
    "audit.ndjson"
  ],
  "required_headings": [
    "Proposed Session Title",
    "Initial Goal",
    "Workflow Type",
    "Risk Tier",
    "Initial Scope",
    "Assumptions",
    "Open Questions",
    "Suggested Tags",
    "Session Initializer Provenance"
  ],
  "required_fields": {
    "session_manifest.json": [
      "workflow_id",
      "session_title",
      "goal",
      "workflow_type",
      "risk_tier",
      "initial_scope",
      "created_at_utc"
    ]
  },
  "forbidden_phrases": [
    "approved",
    "verified",
    "deployed",
    "complete"
  ],
  "state_transition": {
    "from": ["READY"],
    "to": ["THINK"]
  },
  "failure_behavior": {
    "on_missing_goal": "BLOCK",
    "on_missing_scope": "BLOCK",
    "on_invalid_risk_tier": "BLOCK"
  }
}
```

---

# 2. `vvv` — Clarification Ritual

## Purpose

```text
Force explicit understanding before planning.
```

## Delegated Role

```text
CLARIFICATION_AGENT
```

## Context Template: `vvv_context.json`

```json
{
  "session_manifest": "{{session_manifest}}",
  "user_intent": "{{user_intent}}",
  "known_constraints": [],
  "previous_assumptions": [],
  "risk_tier": "{{risk_tier}}"
}
```

## Write Template: `vvv_write.template.md`

```md
# VVV — CLARIFICATION

## 1. Current Understanding

{{current_understanding}}

## 2. Clarifying Questions

{{questions}}

Each question must include:
- question
- why it matters
- blocking: true | false

## 3. Explicit Assumptions

{{assumptions}}

## 4. Scope Boundaries

### In Scope

{{in_scope}}

### Out of Scope

{{out_of_scope}}

## 5. Risk / Ambiguity Notes

{{risk_notes}}

## 6. Required Human Answers

{{required_human_answers}}

## 7. Clarification Provenance

- Author Role: CLARIFICATION_AGENT
- Context Ref: {{vvv_context_sha256}}
- Advisory Only: true
```

## Check Template: `vvv_check.template.json`

```json
{
  "required_artifacts": [
    "VVV.md",
    "assumptions.json",
    "scope.md"
  ],
  "required_headings": [
    "Current Understanding",
    "Clarifying Questions",
    "Explicit Assumptions",
    "Scope Boundaries",
    "Risk / Ambiguity Notes",
    "Required Human Answers",
    "Clarification Provenance"
  ],
  "minimum_counts": {
    "Clarifying Questions": 1
  },
  "required_fields": {
    "assumptions.json": [
      "assumptions",
      "blocking_unknowns",
      "answered_questions"
    ]
  },
  "state_transition": {
    "from": ["THINK"],
    "to": ["PLAN"]
  },
  "failure_behavior": {
    "on_blocking_unknown_unanswered": "BLOCK",
    "on_missing_scope": "BLOCK"
  }
}
```

---

# 3. `nnn` — Planning Ritual

## Purpose

```text
Create execution plan and verification contract.
```

## Delegated Role

```text
PLANNING_AGENT
```

## Context Template: `nnn_context.json`

```json
{
  "session_manifest": "{{session_manifest}}",
  "vvv_artifacts": [],
  "canonical_policies": [],
  "allowed_paths": [],
  "risk_tier": "{{risk_tier}}"
}
```

## Write Template: `nnn_write.template.md`

```md
# NNN — EXECUTION PLAN

## 1. Goal

{{goal}}

## 2. Scope

### Allowed Mutation Surface

{{allowed_mutation_surface}}

### Forbidden Mutation Surface

{{forbidden_mutation_surface}}

## 3. Execution Steps

{{execution_steps}}

Each step must include:
- action
- owner role
- expected artifact
- risk

## 4. Required Artifacts

{{required_artifacts}}

## 5. Verification Contract Summary

{{verification_contract_summary}}

## 6. Risk Assessment

{{risk_assessment}}

## 7. Rollback / Recovery Plan

{{rollback_plan}}

## 8. Human Gate Requirement

{{human_gate_requirement}}

## 9. Planner Provenance

- Author Role: PLANNING_AGENT
- Context Ref: {{nnn_context_sha256}}
- Advisory Only: true
```

## Check Template: `nnn_check.template.json`

```json
{
  "required_artifacts": [
    "PLAN.md",
    "verification_contract.json",
    "risk_assessment.json",
    "rollback.md"
  ],
  "required_headings": [
    "Goal",
    "Scope",
    "Execution Steps",
    "Required Artifacts",
    "Verification Contract Summary",
    "Risk Assessment",
    "Rollback / Recovery Plan",
    "Human Gate Requirement",
    "Planner Provenance"
  ],
  "required_fields": {
    "verification_contract.json": [
      "workflow_id",
      "scope",
      "required_artifacts",
      "checks",
      "failure_behavior",
      "allowed_next_states_on_pass",
      "allowed_next_states_on_fail"
    ],
    "risk_assessment.json": [
      "risk_tier",
      "blast_radius",
      "critical_gate_required"
    ]
  },
  "forbidden_phrases": [
    "skip verification",
    "auto approve",
    "trust model output"
  ],
  "forbidden_actions": [
    "weaken_canonical_policy",
    "expand_scope_without_kernel"
  ],
  "state_transition": {
    "from": ["PLAN"],
    "to": ["SANDBOX"]
  },
  "failure_behavior": {
    "on_missing_verification_contract": "BLOCK",
    "on_missing_rollback_for_warm_or_cold": "BLOCK",
    "on_scope_missing": "BLOCK"
  }
}
```

---

# 4. `gogogo` — Execution Ritual

## Purpose

```text
Execute bounded work inside approved scope.
```

## Delegated Role

```text
EXECUTOR_AGENT
```

## Context Template: `gogogo_context.json`

```json
{
  "plan_ref": "{{PLAN.md}}",
  "verification_contract_ref": "{{verification_contract.json}}",
  "allowed_mutation_surface": [],
  "forbidden_mutation_surface": [],
  "sandbox_capabilities": {},
  "risk_tier": "{{risk_tier}}"
}
```

## Write Template: `gogogo_write.template.md`

```md
# GOGOGO — EXECUTION REPORT

## 1. Execution Summary

{{execution_summary}}

## 2. Steps Performed

{{steps_performed}}

Each step must include:
- planned step id
- action performed
- output artifact
- success/failure

## 3. Files Changed

{{files_changed}}

Each item must include:
- path
- change type
- reason

## 4. Commands Run

{{commands_run}}

Each item must include:
- command
- cwd
- exit code
- output artifact

## 5. Test / Validation Output

{{test_validation_output}}

## 6. Deviations From Plan

{{deviations}}

If none, write:
`No deviations from approved plan.`

## 7. Executor Provenance

- Author Role: EXECUTOR_AGENT
- Verification Contract Ref: {{verification_contract_sha256}}
- Advisory Only: false
```

## Check Template: `gogogo_check.template.json`

```json
{
  "required_artifacts": [
    "EXECUTION_REPORT.md",
    "diff.patch",
    "execution.log",
    "artifact_manifest.json"
  ],
  "required_headings": [
    "Execution Summary",
    "Steps Performed",
    "Files Changed",
    "Commands Run",
    "Test / Validation Output",
    "Deviations From Plan",
    "Executor Provenance"
  ],
  "required_checks": [
    "diff_paths_within_allowed_scope",
    "forbidden_paths_untouched",
    "required_artifacts_exist",
    "sandbox_policy_not_violated"
  ],
  "forbidden_actions": [
    "self_approve",
    "change_policy",
    "mutate_forbidden_path",
    "bypass_sandbox",
    "deploy_without_ddd"
  ],
  "state_transition": {
    "from": ["SANDBOX", "EXECUTE"],
    "to": ["VERIFY"]
  },
  "failure_behavior": {
    "on_forbidden_diff": "BLOCK",
    "on_missing_diff": "BLOCK",
    "on_sandbox_violation": "TERMINAL_FAILED",
    "on_test_failure": "ALLOW_VERIFY_FAIL"
  }
}
```

---

# 5. `ddd` — Decision / Deployment Gate Ritual

## Purpose

```text
Validate execution and approve irreversible consequence.
```

## Delegated Roles

```text
VERIFIER_AGENT
PRESENTATION_SYNTHESIZER
HUMAN_APPROVER when required
```

## Context Template: `ddd_context.json`

```json
{
  "execution_artifacts": [],
  "verification_contract": "{{verification_contract.json}}",
  "diff_ref": "{{diff.patch}}",
  "test_output_ref": "{{test_output.txt}}",
  "risk_tier": "{{risk_tier}}",
  "critical_gate_required": true
}
```

## Write Template: `verifier_write.template.md`

```md
# VERIFIER REPORT

## 1. Verification Status

{{status}}

Allowed:
- PASS
- FAIL
- UNVERIFIED
- NEEDS_HUMAN

## 2. Checks Performed

{{checks}}

Each check must include:
- check id
- method
- expected
- actual
- result
- evidence ref

## 3. Policy Findings

{{policy_findings}}

## 4. Evidence References

{{evidence_refs}}

## 5. Unresolved Risks

{{unresolved_risks}}

## 6. Recommended Next State

{{recommended_next_state}}

## 7. Verifier Provenance

- Author Role: VERIFIER_AGENT
- Independent From Executor: true
- Context Ref: {{ddd_context_sha256}}
```

## Write Template: `presentation_write.template.md`

```md
# DECISION PRESENTATION

## 1. One-Line Summary

{{summary}}

## 2. Convergence

{{convergence}}

## 3. Disagreement / Dissent

{{dissent}}

## 4. Founder Decisions Required

{{founder_questions}}

## 5. Blast Radius

{{blast_radius}}

## 6. Rollback / Recovery

{{rollback}}

## 7. Required Approval

{{approval_requirement}}

## 8. Raw Artifacts

{{raw_artifact_refs}}

## 9. Presentation Provenance

- Author Role: PRESENTATION_SYNTHESIZER
- Raw Packet Ref: {{ratification_packet_sha256}}
- Advisory Only: true
```

## Check Template: `ddd_check.template.json`

```json
{
  "required_artifacts": [
    "verifier_report.json",
    "VERIFIER_REPORT.md",
    "presentation_synthesis.json",
    "DECISION_PRESENTATION.md"
  ],
  "required_headings": {
    "VERIFIER_REPORT.md": [
      "Verification Status",
      "Checks Performed",
      "Policy Findings",
      "Evidence References",
      "Unresolved Risks",
      "Recommended Next State",
      "Verifier Provenance"
    ],
    "DECISION_PRESENTATION.md": [
      "One-Line Summary",
      "Convergence",
      "Disagreement / Dissent",
      "Founder Decisions Required",
      "Blast Radius",
      "Rollback / Recovery",
      "Required Approval",
      "Raw Artifacts",
      "Presentation Provenance"
    ]
  },
  "required_fields": {
    "verifier_report.json": [
      "status",
      "checks",
      "evidence_refs",
      "allowed_next_states"
    ],
    "presentation_synthesis.json": [
      "summary",
      "convergence",
      "dissent_flags",
      "founder_decisions_required",
      "raw_artifacts_available"
    ]
  },
  "forbidden_actions": [
    "verifier_deploy",
    "presentation_approve",
    "transport_approve",
    "synthesizer_role_overlap_with_opinion_agent",
    "verifier_role_overlap_with_executor"
  ],
  "state_transition": {
    "from": ["VERIFY"],
    "to": ["PROMOTE", "DEPLOY", "FAILED", "NEEDS_HUMAN"]
  },
  "failure_behavior": {
    "on_missing_verifier_report": "BLOCK",
    "on_unverified_high_risk": "NEEDS_HUMAN",
    "on_missing_human_approval_for_critical_gate": "BLOCK"
  }
}
```

---

# 6. `rrr` — Retrospective / Closure Ritual

## Purpose

```text
Close workflow and preserve historical reflection.
```

`rrr` does not write lessons.
`rrr` commissions a retro.

```text
rrr closes.
Retro Writer reflects.
Memory indexes.
Human may pin.
Kernel audits.
```

## Delegated Role

```text
RETRO_WRITER
```

## Context Template: `retro_context.json`

```json
{
  "session": {
    "id": "{{session_id}}",
    "slug": "{{session_slug}}",
    "goal": "{{goal}}",
    "risk_tier": "{{risk_tier}}",
    "started_at": "{{started_at}}",
    "ended_at": "{{ended_at}}",
    "final_state": "{{final_state}}"
  },
  "results": {
    "acceptance": {},
    "forbidden_diff": {},
    "gogogo": {},
    "ddd": {},
    "rrr": {}
  },
  "artifacts": [],
  "audit_summary": {
    "events": 0,
    "transitions": 0,
    "human_decisions": []
  },
  "metrics": {},
  "known_blockers": [],
  "memory_policy": {
    "retro_is_artifact": true,
    "index_not_learn": true,
    "pin_requires_human": true
  }
}
```

## Write Template: `retro_write.template.md`

```md
# RETRO: {{session.slug}}

## 1. Session Summary

- Session ID: {{session.id}}
- Goal: {{session.goal}}
- Final State: {{session.final_state}}
- Risk Tier: {{session.risk_tier}}

## 2. What Was Done

Describe what was completed.

Required:
- cite at least one artifact from `retro_context.artifacts`

## 3. Acceptance Results

Summarize:
- acceptance result
- gogogo result
- ddd result
- rrr result

## 4. Artifacts Produced

List important artifacts.

Each artifact must include:
- path
- purpose
- sha256 if available

## 5. Blockers / Failures

Describe visible failures.

Required if blockers exist:
- blocker id
- cause
- current impact
- recommended next action

## 6. Constitutional Notes

Explain whether the session exposed any governance or boundary issue.

Allowed:
- cite facts from context
- identify visible governance issues

Forbidden:
- declare policy changed
- claim canonical truth
- auto-ratify any lesson

## 7. Lessons Learned

Write advisory lessons only.

Each lesson must include:
- lesson
- evidence reference
- confidence: LOW | MEDIUM | HIGH
- requires_human_ratification: true | false

## 8. Follow-up Actions

Each action must include:
- action
- owner role
- priority
- required artifact

## 9. Memory / Indexing Notes

Required structured facts:
- memory_handling.mode: index
- memory_handling.learn_allowed: false
- memory_handling.pin_requires_human: true

## 10. Retro Provenance

- Retro Writer: {{retro_writer.identity}}
- Retro Writer Role: RETRO_WRITER
- Generated From Context: {{retro_context.sha256}}
- Template Version: {{template.version}}
- Advisory Only: true
```

## Check Template: `rrr_check.template.json`

```json
{
  "required_artifacts": [
    "retro_context.json",
    "RETRO.md",
    "metrics.json",
    "memory_index_result.json"
  ],
  "required_headings": [
    "Session Summary",
    "What Was Done",
    "Acceptance Results",
    "Artifacts Produced",
    "Blockers / Failures",
    "Constitutional Notes",
    "Lessons Learned",
    "Follow-up Actions",
    "Memory / Indexing Notes",
    "Retro Provenance"
  ],
  "required_structural_predicates": [
    "memory_handling.mode == index",
    "memory_handling.learn_allowed == false",
    "memory_handling.pin_requires_human == true",
    "retro.provenance.advisory_only == true"
  ],
  "required_evidence_refs": {
    "What Was Done": 1,
    "Lessons Learned": 1
  },
  "forbidden_phrases": [
    "canonical truth",
    "policy is changed",
    "auto-pinned",
    "memory learned",
    "verified as final truth"
  ],
  "forbidden_actions": [
    "memory_learn",
    "auto_pin",
    "semantic_embedding",
    "promote_policy"
  ],
  "required_checks": [
    "acceptance_passed_or_visible_failure",
    "forbidden_diff_passed_or_visible_failure",
    "retro_required_sections_present",
    "retro_evidence_refs_valid",
    "memory_index_result_visible"
  ],
  "state_transition": {
    "from": ["RETRO", "DEPLOY", "VERIFY"],
    "to": ["DONE", "DEGRADED", "FAILED"]
  },
  "failure_behavior": {
    "on_missing_retro": "BLOCK",
    "on_missing_required_heading": "BLOCK",
    "on_missing_memory_index_hot": "WARN",
    "on_missing_memory_index_warm": "DEGRADED",
    "on_missing_memory_index_cold": "BLOCK"
  }
}
```

---

# 7. `close` — Session Seal Ritual

## Purpose

```text
Seal workflow lifecycle.
```

No semantic agent is required.

Kernel fills deterministic closure artifacts.

## Context Template: `close_context.json`

```json
{
  "session_manifest": "{{session_manifest}}",
  "graph_state": "{{graph_state}}",
  "audit_summary": "{{audit_summary}}",
  "final_artifacts": [],
  "unresolved_failures": []
}
```

## Write Template: `close_write.template.md`

```md
# SESSION CLOSURE

## 1. Session Identity

- Session ID: {{session.id}}
- Slug: {{session.slug}}
- Final State: {{graph.final_state}}

## 2. Rituals Completed

{{rituals_completed}}

## 3. Final Artifact Manifest

{{final_artifacts}}

## 4. Audit Summary

{{audit_summary}}

## 5. Unresolved Failures

{{unresolved_failures}}

## 6. Closure Status

{{closure_status}}

## 7. Closure Provenance

- Written By: Kernel
- Semantic Author: none
- Audit Finalized: {{audit_finalized}}
```

## Check Template: `close_check.template.json`

```json
{
  "required_artifacts": [
    "SESSION_CLOSURE.md",
    "final_manifest.json"
  ],
  "required_headings": [
    "Session Identity",
    "Rituals Completed",
    "Final Artifact Manifest",
    "Audit Summary",
    "Unresolved Failures",
    "Closure Status",
    "Closure Provenance"
  ],
  "required_fields": {
    "final_manifest.json": [
      "workflow_id",
      "final_state",
      "artifacts",
      "audit_finalized",
      "closed_at_utc"
    ]
  },
  "state_transition": {
    "from": ["DONE"],
    "to": ["SEALED"]
  },
  "failure_behavior": {
    "on_unresolved_critical_failure": "BLOCK",
    "on_audit_not_finalized": "BLOCK",
    "on_missing_final_manifest": "BLOCK"
  }
}
```

---

# Final Ritual Invariants

```text
Kernel enforces structure.
Agents generate semantics.
Artifacts preserve truth.
Verifier validates evidence.
Memory retrieves artifacts.
Audit preserves history.
Humans ratify authority.
```

```text
Context Template prevents invention.
Write Template guides the agent.
Check Template constrains the Kernel.
Audit Template preserves history.
```

```text
No template = no ritual.
No artifact = no trust.
No check = no transition.
No audit = no history.
```

---

# Implementation Lock

This ritual constitution locks Trinity Kernel as:

```text
a constitutional runtime validator
not an AI orchestrator
```

A valid ritual implementation MUST include:

```text
context template
write template
check template
output artifact
audit event
state transition rule
retry policy
role permission
```

Any ritual that allows an agent to:

```text
- define its own template
- bypass check template
- self-approve output
- transition state directly
- hide missing artifacts
- mutate memory semantically
```

is not Trinity.

---

# v1.1 Ratification Status

```text
RATIFIED AS: v1.1
RATIFIED AT: 2026-05-13
GATE:        Article XII.5 — empirical end-to-end ritual cycle
SUPERSEDES:  v1.1-rc (RC_PENDING_EMPIRICAL_RATIFICATION, 2026-05-12)
```

Empirical evidence (Article XII.5 gate satisfied):

```text
- commit 04bb74f — per-ritual loader integration (6 rituals)
- commit 5ce7b88 — close.py wired (ritual #7) + alignment + agent prompt
- smoke session 0001_2026-05-13_14_56_pm_feat-smoke-test-full-loop-integration
```

The smoke session ran a complete `sss → vvv → nnn → gogogo → ddd → rrr → close`
cycle without bypass, and all 7 pack-declared `.invoked` events landed in the
hash-chained audit log.

This document is therefore:

```text
RATIFIED — FINAL OFFICIAL TRUTH (v1.1)
```

Per Article XXIX the amendment record lives at
[`addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md`](addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md)
and the canonical ratification audit event is `ritual_constitution.ratified`
in `.ai/audit/events.ndjson` (Session B, 2026-05-13).
