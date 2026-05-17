# Trinity Organ Refactor PRD & Task Specification v1.0

**Status:** Ready for Team Handoff  
**Date:** 2026-05-12  
**Owner:** Founder / Trinity Architect  
**Target:** Trinity v2 ecosystem, ritual workflow, sibling CLIs, governance runtime  
**Primary Goal:** Refactor Trinity from a collection of CLI scripts into a ritual-driven, organ-based AI governance control plane.

---

## 1. Executive Summary

Trinity must be refactored around a strict organ model. Each organ must have a narrow role, explicit authority, clear inputs and outputs, required artifacts, failure behavior, audit behavior, and a security boundary. Ritual commands such as `sss`, `vvv`, `nnn`, `gogogo`, `ddd`, `rrr`, and `close` must become thin ritual gates that route work to the proper organs rather than doing all work themselves.

The key implementation principle is:

```text
Kernel governs.
Planner plans.
Executor acts.
Verifier validates.
Memory retrieves evidence.
Retro reflects.
Transport delivers.
Human decides.
Audit remembers.
```

The first concrete implementation target is `rrr`, because it currently reveals a constitutional role-collapse bug: `rrr` closes a session but also feeds retros into Memory through a legacy semantic command (`memory-cli learn`). This must become mechanical evidence indexing (`memory-cli index`) with visible failure behavior.

This PRD consolidates the full refactor plan across all organs, phases, deliverables, acceptance criteria, PR sequence, and team task specs.

---

## 2. Product / Architecture Vision

Trinity is not an autonomous agent system. Trinity is a deterministic AI governance control plane for artifact-governed operations.

The desired architecture:

```text
HUMAN / FOUNDER
  ↓
DDD / Human Gate
  ↓
KERNEL
  ├─ State Graph
  ├─ Policy Engine
  ├─ Authority Check
  └─ Ritual Router
       ↓
       ├─ Planner   → PLAN.md + verification_contract.json
       ├─ Executor  → diff/log/artifacts via Sandbox
       ├─ Verifier  → verifier_report.json
       ├─ Memory    → index/search/pack exact evidence
       ├─ Retro     → RETRO.md and lessons artifact
       ├─ Audit     → append-only events
       └─ Transport → delivery only
```

Final ritual flow:

```text
sss → vvv → nnn → gogogo → ddd → rrr → close
```

Interpretation:

```text
sss starts.
vvv clarifies.
nnn plans.
gogogo executes.
ddd decides.
rrr closes by delegation.
close seals.
```

---

## 3. Background and Current Diagnosis

The current ecosystem already maps reasonably well to the constitutional roles, but it has role-collapse and ownership gaps that must be resolved before Trinity can operate reliably as a control plane.

### 3.1 Current Organ Status

| Constitutional Role | Current Implementer | Status |
|---|---|---|
| Kernel | `trinity_v2/.ai/cli/` commands | Mostly clean |
| Planner | model + `nnn` ritual + plan envelope | Mostly clean |
| Executor | shell/Edit/Write + sibling CLIs | Scattered; no central contract |
| Verifier | verifier rules + judge-cli + test-cli + contract tests | Split ownership |
| Memory | memory-cli v0.1 | Clean after exact-memory refactor |
| Audit | `.ai/audit/events.ndjson` | Clean but needs formal replay proof |
| Retro | `rrr.py` | Role collapse: calls memory learn |
| Transport | Telegram bot + notify-cli | Needs transport-only boundary audit |

### 3.2 Known Role Collapses / Risks

1. `kernel.rrr` calls `memory-cli learn`, creating semantic memory behavior inside terminal closure.
2. Legacy memory-cli v0.9 included learn/promote/verify/trace, mixing Memory, Planner, and Verifier roles.
3. Telegram transport may escalate into authority if HMAC/DDD pipeline bypasses Kernel.
4. Verifier responsibilities are split across policy rules, judge-cli, test-cli, and contract tests without clear verdict ownership.
5. Executor capability declarations are scattered across sibling tools and not centrally validated.
6. Hidden authority risk exists in legacy env toggles such as `MEMORY_CLI_LEGACY=1` and vendor skill systems.

---

## 4. Goals

### 4.1 Primary Goals

- Make each Trinity organ narrow, explicit, testable, and auditable.
- Make ritual commands delegate rather than absorb roles.
- Enforce ritual flow through Kernel state transitions.
- Remove semantic learning from Memory core and terminal gates.
- Make Verifier ownership explicit and structured.
- Make Transport delivery-only.
- Make Executor tools declare capabilities before use.
- Make Audit replayable and formally checkable.
- Make DDD/Human gates artifact-based, not prompt-based.
- Preserve productivity through Decision Velocity Tiers.

### 4.2 Non-Goals

- Do not build a fully autonomous agent swarm.
- Do not re-expand memory-cli into semantic memory.
- Do not implement full crypto ratification in Phase 1.
- Do not require full Trinity rigor for all hot-path daily work.
- Do not let any organ become a god object.

---

## 5. Constitutional Constraints

The refactor must obey the following non-negotiable constraints:

```text
No artifact = No trust.
No verification = No completion.
No audit = No history.
No governance = No Trinity.
```

```text
Ritual command = gate.
Organ = bounded capability.
Kernel = governance.
Audit = history.
Human = irreversible authority.
```

No organ may silently absorb another organ’s role.

---

## 6. Decision Velocity Tiers

Trinity rigor must be proportional to durability and blast radius of failure.

| Tier | Use Cases | Required Rigor |
|---|---|---|
| HOT PATH | daily coding, experiments, reversible changes, low blast radius | no full Trinity required; lightweight logs/checks |
| WARM PATH | feature work, integrations, meaningful but reversible changes | light verification contract; deterministic checks |
| COLD PATH | governance, security, production deploy, irreversible/durable mistakes | full Trinity: contract, verifier, DDD, audit, possibly presentation/ratification |

Principle:

```text
Trinity rigor is reserved for durable mistakes.
```

---

## 7. Organ Model Requirements

Every organ must answer these eight questions before entering Trinity core:

```text
1. What is its role?
2. What authority does it have?
3. What are its inputs?
4. What are its outputs?
5. What artifacts does it produce?
6. What workflow states may it touch?
7. What is its failure behavior?
8. What is its audit behavior?
```

A component that cannot answer these is not yet a Trinity organ; it is only a script.

---

## 8. Organ Contracts

### 8.1 Kernel

**Role:** Governance, state, gates, authority.  
**Owns:** workflow state, legal transitions, policy checks, authority checks, ritual routing.  
**Must not own:** reasoning, execution, verification, memory interpretation, retro meaning.

Deliverables:

- `TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md`
- machine-readable transition table
- transition validator
- authority validator
- decision velocity tier integration

Acceptance:

- Unknown state is unsafe.
- Illegal transition fails.
- State transition emits audit.
- DONE requires required artifacts.

---

### 8.2 State Graph

**Role:** Finite workflow state machine.  
**Canonical states:**

```text
READY
THINK
PLAN
SANDBOX
EXECUTE
VERIFY
PROMOTE
DEPLOY
RETRO
DONE
FAILED
ABORTED
REOPENED
```

Deliverables:

- `.ai/graphs/standard.yaml`
- `TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md`
- illegal transition tests

Acceptance:

- `EXECUTE → DEPLOY` without VERIFY fails.
- `DONE → EXECUTE` without REOPENED fails.
- `FAILED → DEPLOY` without re-verification fails.

---

### 8.3 Policy Engine

**Role:** Enforce allowed/forbidden actions independent of state.  
**Owns:** forbidden paths, critical gate policy, secret policy, capability rules, risk escalation.

Deliverables:

- `.ai/policies/trinity_policy.yaml`
- `TRINITY_POLICY_ENGINE_SPEC_V1.md`
- rule categories for filesystem, network, secrets, authority, critical gates, memory boundaries

Acceptance:

- Policy can reject a transition or tool call before execution.
- Policy is separate from state graph.
- Secret and forbidden path rules are testable.

---

### 8.4 Ritual Controller

**Role:** Map ritual commands to organs.  
**Owns:** command-to-organ routing and audit event wrappers.  
**Must not own:** execution logic or semantic interpretation.

Deliverables:

- `TRINITY_RITUAL_CONTRACT_V1.md`
- command boundary tests for `sss/vvv/nnn/gogogo/ddd/rrr/close`

Acceptance:

- Each command has declared role and forbidden behaviors.
- Commands remain thin gates.

---

### 8.5 Planner

**Role:** Reasoning and planning.  
**Owns:** `PLAN.md`, scope declaration, risk assessment, verification contract.  
**Must not own:** execution, approval, verification result, state transition.

Deliverables:

- `PLAN.md` template
- `verification_contract.json` template
- `scope.json`
- `risk_assessment.md`

Acceptance:

- Non-trivial execution requires plan + verification contract.
- Plan declares allowed mutation surface and expected artifacts.

---

### 8.6 Executor

**Role:** Bounded action.  
**Owns:** file edits, shell/tool calls, execution logs, diffs.  
**Must not own:** approval, verification, final completion, state transition.

Deliverables:

- `execution_lease.json`
- `artifact_manifest.json`
- command execution wrapper
- tool capability enforcement

Acceptance:

- Executor cannot call undeclared tools.
- Executor cannot mutate outside declared scope.
- Executor produces diff/log/artifacts.

---

### 8.7 Sandbox

**Role:** Enforce blast radius below the model layer.  
**Owns:** filesystem boundary, network egress boundary, command allowlist, env restrictions, temporary credentials.

Deliverables:

- `TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md`
- `sandbox_profile.json`
- deny-by-default network model
- writable artifact directory model

Acceptance:

- Executor writes only allowed paths.
- Network is default-deny.
- Secret paths are blocked.
- Escape attempts produce visible failure and audit.

---

### 8.8 Verifier

**Role:** Independent validation.  
**Owns:** deterministic checks, policy checks, test/lint/typecheck results, `verifier_report.json`.  
**Must not own:** deployment, mutation, silent fixes, final authority.

Deliverables:

- `TRINITY_VERIFIER_CONTRACT_V1.md`
- `schemas/verifier_report.schema.json`
- tiered verifier harness

Verifier pyramid:

```text
Tier 0: artifact existence, hash, schema, command exit
Tier 1: tests, lint, typecheck, contract tests
Tier 2: policy-as-code
Tier 3: AI advisory review only
Tier 4: human gate
```

Acceptance:

- Every verdict declares tier.
- Every verdict cites artifact evidence.
- AI advisory is never sole pass condition for critical transitions.

---

### 8.9 Memory CLI

**Role:** Exact artifact evidence retrieval.  
**Owns:** indexing, search, show, pack, pins, clean/purge.  
**Must not own:** semantic learning, summarization, canonical truth decisions, execution.

Final command surface:

```text
memory health
memory index <path>
memory search <query>
memory show <path|id>
memory pin <path> --as <name>
memory unpin <name>
memory list --pins
memory pack <query>
memory clean
memory purge
```

Deliverables:

- `TRINITY_MEMORY_EXACT_SURFACE_V1.md`
- exact index output envelope
- retro indexing support
- evidence-only context pack

Acceptance:

- Search returns path + line range + sha256.
- Pack contains traceable evidence only.
- Pin requires explicit human/operator command.
- No core `learn`, `promote`, `verify`, `trace`, embeddings, semantic ranking.

---

### 8.10 Audit

**Role:** Immutable history.  
**Owns:** event log, hash chain, transition history, artifact references.  
**Must not own:** semantic truth or approval authority.

Deliverables:

- `TRINITY_AUDIT_EVENT_SPEC_V1.md`
- `audit replay`
- `audit verify-chain`
- `audit verify-artifact-refs`

Acceptance:

- Chain replay produces zero mismatches.
- Missing artifact refs are visible.
- Corrections create new events; no silent rewrite.

---

### 8.11 Retro CLI

**Role:** Post-work reflection artifact generation.  
**Owns:** lessons draft, bottleneck notes, improvement suggestions.  
**Must not own:** memory indexing, canonical pin, state transition, verification.

Deliverables:

- `retro_envelope.md`
- `RETRO.md`
- semantic retro draft optional

Acceptance:

- `rrr` may generate deterministic closure envelope.
- Semantic reflection is delegated to Retro/Human/AI drafter.
- Retro does not auto-pin or mutate memory.

---

### 8.12 RRR Terminal Gate

**Role:** Terminal governance gate and closure delegator.  
**Owns:** closure, acceptance collection, forbidden diff checks, metrics, graph transition, audit.  
**Must not own:** memory learning, semantic retro meaning, canonical pinning, verification truth.

Required change:

```text
memory-cli learn --file=<retro>
→
memory-cli index <retro-path>
```

Deliverables:

- `TRINITY_RRR_DELEGATION_CONTRACT_V1.md`
- `memory_index` audit field
- visible failure behavior
- pin suggestion only

Acceptance:

- `rrr` does not call `memory-cli learn`.
- `rrr` calls `memory-cli index`.
- Failure is visible.
- No `confidence=`, `embedding`, `auto-tag`, `auto-pin`.

---

### 8.13 DDD / Human Gate

**Role:** Human or governance decision gate.  
**Owns:** approve, reject, hold, approve-with-conditions.  
**Must not own:** execution, silent approval, unverified promotion.

Deliverables:

- `TRINITY_DDD_HUMAN_GATE_SPEC_V1.md`
- `decision_packet.json`
- `approval.json`
- `rejection.json`
- `hold.json`

Acceptance:

- Critical gate pauses.
- Human approval artifact exists.
- DDD cannot approve without verifier report where required.

---

### 8.14 Transport Gateway

**Role:** Delivery only.  
**Owns:** Telegram/Slack/webhook/API input and response delivery.  
**Must not own:** authority, approval, workflow state mutation.

Deliverables:

- `TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md`
- HMAC envelope tests
- kernel routing enforcement

Acceptance:

- Transport cannot approve DDD directly.
- Transport-originated action must pass Kernel.
- Gate approval without Kernel fails.

---

### 8.15 Tool Capability Registry

**Role:** Declare tool authority before use.  
**Owns:** tool identity, allowed operations, inputs/outputs, artifacts, security boundary.

Deliverables:

- `TRINITY_TOOL_CAPABILITY_MODEL_V1.md`
- `.ai/tools.capabilities.yaml`
- per-tool `trinity.yaml` or `contract.json`

Acceptance:

- Every tool has role/authority/input/output/artifact declarations.
- Unknown tools are denied by default.
- Kernel validates contract on registration.

---

### 8.16 Presentation Protocol

**Role:** Protect human judgment.  
**Owns:** convergence compression, dissent expansion, founder questions, raw artifact links.  
**Must not own:** authority, truth, ratification.

Deliverables:

- `TRINITY_PRESENTATION_PROTOCOL_V1.md`
- `ratification_packet.json`
- `presentation_synthesis.json`
- `ratification_decision.json`
- presentation verifier

Acceptance:

- Compressed view never replaces raw truth.
- Dissent is preserved.
- Full artifacts remain accessible.

---

### 8.17 Root of Trust / Ratification

**Role:** Make human authority machine-verifiable.  
**Owns:** genesis trust, signed canonical artifacts, versioning, revocation, threshold rules later.

Deliverables:

- `TRINITY_ROOT_OF_TRUST_SPEC_V1.md`
- `GENESIS_TRUST_ASSUMED` manifest
- root ratification artifact

Acceptance:

- Genesis trust is declared, not hidden.
- Layer 0 artifacts are hash-pinned.
- Crypto can be deferred until after MVP, but schema is ready.

---

### 8.18 Close / Session Finalizer

**Role:** Seal and archive session.  
**Owns:** final manifest verification, temp cleanup, next-step hint, optional external audit.

Deliverables:

- `final_manifest.json`
- `session_close_report.md`
- cleanup confirmation

Acceptance:

- Close only works on DONE/FAILED/ABORTED.
- Close does not rewrite audit or retro.
- Final manifest hashes validate.

---

## 9. Phase Roadmap

### Phase 0 — Lock Specs and Scope

**Objective:** Stop constitutional churn and create a stable handoff baseline.

Deliverables:

- `TRINITY_CONSTITUTION_V1.md`
- `TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md`
- `TRINITY_ORGAN_MAP_V1.md`
- `TRINITY_RITUAL_CONTRACT_V1.md`

Acceptance:

- Constitution is locked.
- Addendum defines Genesis, Decision Velocity Tiers, Break-Glass, External Audit, Cognitive Presentation.
- Organ map accepted by team.
- Ritual commands mapped to organs.

---

### Phase 1 — RRR Constitutional Bug Fix

**Objective:** Fix first real role-collapse bug.

PR name:

```text
feat-kernel-rrr-v01-memory-surface
```

Scope:

- Replace `memory-cli learn --file=<retro>` with `memory-cli index <retro-path>`.
- Rename `memory_learn` to `memory_index`.
- Rename helper functions.
- Update audit payload fields.
- Make index failure visible.
- Suggest pin only; never auto-pin.
- Add `TRINITY_RRR_DELEGATION_CONTRACT_V1.md`.

Acceptance:

```text
- grep finds no memory-cli learn in rrr path
- rrr calls memory-cli index
- audit event contains memory_index
- memory index failure is visible
- tests updated
- no confidence/embedding/auto-tag/auto-pin
```

---

### Phase 2 — Memory CLI Exact Surface

**Objective:** Finalize memory-cli v0.1 as exact artifact memory.

Deliverables:

- `memory index`
- `memory search`
- `memory show`
- `memory pack`
- `memory pin/unpin/list --pins`
- `memory clean/purge`

Acceptance:

- Retro file can be indexed.
- Search returns path/line/sha256.
- Pack is evidence-only.
- Pin is explicit human/operator action.
- Legacy verbs require explicit legacy env and are audited if used.

---

### Phase 3 — Verification Contract

**Objective:** Prevent execution without predefined checks.

Deliverables:

- `TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md`
- `schemas/verification_contract.schema.json`
- `verification_contract.json` template

Acceptance:

- `nnn` produces verification contract for WARM/COLD workflows.
- `gogogo` refuses non-trivial execution without contract.
- Contract includes scope, artifacts, checks, failure behavior, and human gate policy.

---

### Phase 4 — Kernel State Machine Formalization

**Objective:** Make ritual enforceable.

Deliverables:

- `TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md`
- `.ai/graphs/standard.yaml`
- transition validator
- illegal transition tests

Acceptance:

- All transitions declared.
- Illegal transitions fail.
- Unknown state is unsafe.
- Transition emits audit.

---

### Phase 5 — Policy Engine Extraction

**Objective:** Separate policy from state.

Deliverables:

- `.ai/policies/trinity_policy.yaml`
- policy validator
- critical gate rules
- forbidden path and secret rules

Acceptance:

- Kernel queries policy before transition/tool call.
- Policy can block tool use.
- Policy rules are testable independent of state graph.

---

### Phase 6 — Executor Tool Capability Declarations

**Objective:** Define authority for all sibling tools.

Deliverables:

- `TRINITY_TOOL_CAPABILITY_MODEL_V1.md`
- `.ai/tools.capabilities.yaml`
- per-tool contract files

Acceptance:

- Every tool declares role/authority/inputs/outputs/artifacts/state/failure/audit/security.
- Unknown tools rejected.
- Executor can only call declared tools.

---

### Phase 7 — Sandbox Capability

**Objective:** Enforce blast radius below prompt layer.

Deliverables:

- `TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md`
- `sandbox_profile.json`
- scoped execution lease
- network and filesystem restrictions

Acceptance:

- Allowed paths enforced.
- Default-deny egress enforced.
- Secret paths blocked.
- Sandbox violation becomes visible failure.

---

### Phase 8 — Verifier Harness Consolidation

**Objective:** Make verification independent and structured.

Deliverables:

- `TRINITY_VERIFIER_CONTRACT_V1.md`
- `schemas/verifier_report.schema.json`
- verifier CLI/harness
- tiered check mapping

Acceptance:

- Every verdict path maps to a tier.
- judge-cli declared as AI advisory verifier, not executor.
- AI verdict alone cannot promote/deploy.
- DDD consumes verifier report.

---

### Phase 9 — Transport Boundary Hardening

**Objective:** Ensure transport is never authority.

Deliverables:

- `TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md`
- Telegram HMAC audit tests
- remote command envelope validation

Acceptance:

- Telegram bot cannot approve DDD directly.
- Transport only relays signed/validated envelopes to Kernel.
- Gate approval without Kernel fails.

---

### Phase 10 — Audit Formal Proof

**Objective:** Make audit replayable and provable.

Deliverables:

- `TRINITY_AUDIT_EVENT_SPEC_V1.md`
- audit chain replay command
- artifact reference validation
- cross-session reference validation

Acceptance:

- Chain replay produces zero mismatches.
- Missing artifact refs detected.
- Audit correction creates new event.

---

### Phase 11 — DDD / Human Gate

**Objective:** Make human decisions explicit artifacts.

Deliverables:

- `TRINITY_DDD_HUMAN_GATE_SPEC_V1.md`
- `decision_packet.json`
- `approval.json`
- `rejection.json`
- `hold.json`

Acceptance:

- Critical gates pause progression.
- Decision artifact exists.
- Required verifier report exists before approve.

---

### Phase 12 — Retro / RRR Split Completion

**Objective:** Separate terminal closure from reflection.

Deliverables:

- deterministic `retro_envelope.md`
- semantic `RETRO.md` if needed
- `rrr.completed` event schema
- memory index result envelope

Acceptance:

- `rrr` writes deterministic closure records only.
- Retro component or human drafts semantic lessons.
- Memory indexes artifact mechanically.
- Human may pin; system does not auto-pin.

---

### Phase 13 — Presentation Protocol

**Objective:** Protect human judgment from cognitive overload.

Deliverables:

- `TRINITY_PRESENTATION_PROTOCOL_V1.md`
- `ratification_packet.json`
- `presentation_synthesis.json`
- `ratification_decision.json`
- presentation verifier

Acceptance:

- Dissent preserved.
- Convergence compressed.
- Full raw artifacts accessible.
- Compressed UI is never truth layer.

---

### Phase 14 — Root of Trust / Ratification

**Objective:** Make human authority machine-verifiable.

Deliverables:

- `TRINITY_ROOT_OF_TRUST_SPEC_V1.md`
- `GENESIS_TRUST_ASSUMED` manifest
- root ratification artifact
- signature support later

Acceptance:

- Genesis trust declared.
- Layer 0 artifacts hash-pinned.
- Crypto is optional until production, but schema is ready.

---

### Phase 15 — Close / Session Finalizer

**Objective:** Seal workflow without rewriting truth.

Deliverables:

- `final_manifest.json`
- `session_close_report.md`
- artifact hash verification
- optional external audit record for COLD path

Acceptance:

- Close only runs on DONE/FAILED/ABORTED.
- Close does not rewrite audit or retro.
- Final manifest validates.

---

### Phase 16 — End-to-End Ritual Integration

**Objective:** Run one full ritual end-to-end on a real WARM workflow.

Flow:

```text
sss → vvv → nnn → gogogo → ddd → rrr → close
```

Acceptance:

- Session starts and state is explicit.
- Plan and verification contract exist.
- Execution produces artifacts.
- Verifier report exists.
- DDD decision artifact exists.
- RRR indexes retro and emits audit.
- Close seals final manifest.

---

## 10. PR Roadmap

### P0 PRs — Constitutional Role Collapse Fixes

1. `feat-kernel-rrr-v01-memory-surface`
2. `feat-transport-organ-article-xv-compliance`
3. `feat-verifier-organ-consolidation`

### P1 PRs — Ritual Enforceability

4. `feat-executor-organ-contract-declaration`
5. `feat-audit-organ-hash-chain-formal-proof`
6. `feat-kernel-organ-state-machine-formal`
7. `feat-policy-organ-extraction`

### P2 PRs — Production Hardening

8. `feat-sandbox-capability-enforcement`
9. `feat-verification-contract-v1`
10. `feat-ddd-human-gate-artifacts`
11. `feat-retro-rrr-split-completion`

### P3 PRs — Governance UX / Ratification

12. `feat-presentation-protocol-v1`
13. `feat-root-of-trust-genesis-v1`
14. `feat-close-finalizer-v1`
15. `feat-ritual-e2e-warm-path`

---

## 11. First PR Detailed Task Spec

### PR: `feat-kernel-rrr-v01-memory-surface`

**Objective:** Make `rrr` compliant with memory-cli v0.1 exact evidence surface.

### Files in Scope

```text
.ai/cli/commands/rrr.py
.ai/tests/**rrr**
docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md
```

### Required Code Changes

```text
OLD: memory-cli learn --file=<retro>
NEW: memory-cli index <retro-path>
```

Rename:

```text
_feed_memory_cli              → _index_memory_cli
_summarize_memory_learn       → _summarize_memory_index
memory_learn                  → memory_index
audit.memory_learn            → audit.memory_index
```

### Required Behavior

- If memory index succeeds, audit contains success envelope.
- If memory index fails in HOT/WARM path, `rrr` may complete but must show `FAILED_VISIBLE` and next hint.
- If memory index fails in COLD/governance path, `rrr` must produce `DONE_WITH_INDEX_FAILURE` or block closure according to policy.
- If human decision exists, `rrr` may suggest `memory pin`, but must not run it.

### Forbidden Patterns

```text
memory-cli learn
confidence=
embedding
auto-tag
auto-pin
```

### Acceptance Contract

```json
{
  "workflow": "feat-kernel-rrr-v01-memory-surface",
  "allowed_mutation_paths": [
    ".ai/cli/commands/rrr.py",
    ".ai/tests/**",
    "docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md"
  ],
  "required_checks": [
    "rrr does not call memory-cli learn",
    "rrr calls memory-cli index",
    "audit field is memory_index",
    "memory index failure is visible",
    "tests updated"
  ],
  "forbidden_patterns": [
    "memory-cli learn",
    "confidence=",
    "embedding",
    "auto-tag",
    "auto-pin"
  ]
}
```

### Definition of Done

- Tests pass.
- Smoke ritual produces `memory_index` in audit.
- `rrr` output shows visible index status.
- No legacy memory verb used.
- Spec added and referenced.

---

## 12. Testing Strategy

### Unit Tests

- command boundary tests
- transition validator tests
- policy engine tests
- verifier schema tests
- memory index/search/pack tests
- transport boundary tests

### Integration Tests

- ritual flow HOT path
- ritual flow WARM path
- ritual flow COLD path
- failed verifier blocks promotion
- memory index failure visible
- transport cannot approve gate

### Governance Tests

- role collapse detection
- unknown tool denied
- illegal transition denied
- artifact missing blocks completion
- audit replay zero mismatches

---

## 13. Release Criteria

A phase may be marked complete only when:

```text
- required artifacts exist
- acceptance criteria pass
- audit events are emitted
- failure behavior is visible
- no forbidden role absorption occurs
- documentation/spec files are updated
```

A ritual may be marked complete only when:

```text
- plan exists where required
- verification contract exists where required
- execution artifacts exist where required
- verifier report exists where required
- DDD decision exists where required
- RRR closure exists
- final audit exists
```

---

## 14. Team Handoff Checklist

Before assigning a PR, each task owner must know:

```text
- Organ being refactored
- Role boundary
- Forbidden behaviors
- Files allowed to mutate
- Required artifacts
- Required tests
- Audit event expectations
- Acceptance contract
```

Reviewers must check:

```text
- Did this PR reduce role collapse?
- Did it avoid adding semantic overreach?
- Did it keep command as a ritual gate?
- Did it preserve artifact/audit visibility?
- Did it avoid changing unrelated organs?
```

---

## 15. Final Implementation Principle

Do not make Trinity smarter by making commands bigger.

Make Trinity safer by making organs smaller.

```text
Everything is an organ.
Every organ has a boundary.
Every boundary has a contract.
Every contract has acceptance criteria.
Every state change has an artifact.
Every artifact has audit.
```

---

## Appendix A — Required Spec Files

> **Note:** As of 2026-05-13 (Addendum v1.0.2), constitutional documents live in `docs/constitution/`. Remaining technical-spec files in this list stay in `docs/specs/`.

Constitutional layer (locked under D1 protection · three-tier structure per Addendum v1.0.2):

```text
docs/constitution/INDEX.md
docs/constitution/TRINITY_CONSTITUTION_V1.md             ⭐ core
docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md ⭐ core
docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md
docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md
docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md
docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md
docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md
```

Technical-spec layer (still required, awaiting authorship — see Phases 2–15):

```text
docs/specs/TRINITY_MEMORY_EXACT_SURFACE_V1.md
docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md
docs/specs/TRINITY_KERNEL_STATE_TRANSITION_SPEC_V1.md
docs/specs/TRINITY_POLICY_ENGINE_SPEC_V1.md
docs/specs/TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md
docs/specs/TRINITY_VERIFIER_CONTRACT_V1.md
docs/specs/TRINITY_AUDIT_EVENT_SPEC_V1.md
docs/specs/TRINITY_DDD_HUMAN_GATE_SPEC_V1.md
docs/specs/TRINITY_TRANSPORT_BOUNDARY_SPEC_V1.md
docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md
docs/specs/TRINITY_PRESENTATION_PROTOCOL_V1.md
docs/specs/TRINITY_ROOT_OF_TRUST_SPEC_V1.md
docs/specs/TRINITY_CLOSE_FINALIZER_SPEC_V1.md
```

---

## Appendix B — Minimum Machine-Readable Artifacts

```text
SESSION.json
UNDERSTANDING.md
PLAN.md
scope.json
risk_assessment.md
verification_contract.json
execution_lease.json
sandbox_profile.json
diff.patch
execution.log
tool_calls.jsonl
artifact_manifest.json
verifier_report.json
decision_packet.json
approval.json / rejection.json / hold.json
retro_envelope.md
RETRO.md
memory_index_result.json
final_manifest.json
session_close_report.md
```

---

## Appendix C — Phase Ownership Suggestion

| Phase | Suggested Owner |
|---|---|
| Phase 0 | Architect / Tech Lead |
| Phase 1 | Kernel engineer |
| Phase 2 | Memory engineer |
| Phase 3 | Planner + Verifier engineer |
| Phase 4 | Kernel engineer |
| Phase 5 | Policy engineer |
| Phase 6 | Tooling/platform engineer |
| Phase 7 | Infra/security engineer |
| Phase 8 | QA/verifier engineer |
| Phase 9 | Transport engineer |
| Phase 10 | Audit/platform engineer |
| Phase 11 | Product/founder + kernel engineer |
| Phase 12 | Retro/kernel engineer |
| Phase 13 | UX/governance engineer |
| Phase 14 | Security/root-of-trust engineer |
| Phase 15 | Kernel/platform engineer |
| Phase 16 | Integration owner |

---

## Appendix D — Final Lock Statement

```text
Trinity organs must be small.
Ritual commands must delegate.
Kernel must govern.
No organ may absorb another organ’s role.
No semantic work may happen inside terminal gates.
No closure without visible artifacts.
```

