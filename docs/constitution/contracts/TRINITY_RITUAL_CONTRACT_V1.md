---
title: "Trinity Ritual Contract v1.0"
version: "1.0"
status: "locked"
last-updated: "2026-05-12"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
parent: "TRINITY_CONSTITUTION_V1.md"
parent_rule_layer: "TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md (Ritual Constitution v1.1-rc — RC_PENDING_EMPIRICAL_RATIFICATION; this contract's per-ritual table is the operational instance of the three-template model defined there)"
related:
  - "TRINITY_ORGAN_MAP_V1.md (organ definitions)"
  - "TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md §B (Decision Velocity Tiers)"
  - "trinity_organ_refactor_prd.md §8.4 (Ritual Controller)"
---

# Trinity Ritual Contract v1.0

> Ritual commands are **gates**, not work.
>
> A ritual command's job is to (a) validate preconditions, (b) emit
> audit, (c) fire a state transition, and (d) delegate the real work
> to the organ that owns that role (Organ Map V1).
>
> When a ritual command does the work itself — like `rrr` calling
> `memory-cli learn` — that is **role collapse** and violates
> Article IV. This contract is how we prevent that recurrence.

## Constitutional Anchoring

- **Article IV** — Separation of Responsibilities. Each ritual is a gate; organ work belongs to organs.
- **Article V** — Kernel Authority. Rituals invoke Kernel checks; they don't become Kernel themselves.
- **Article XI** — Explicit State Governance. Every ritual fires a declared transition.
- **Article XII** — Illegal Transitions. Wrong-order ritual = blocked transition.
- **Article XXIII** — Failure Visibility. Ritual failures must be visible, never silently swallowed.

## Ritual Flow

```text
sss → vvv → nnn → gogogo → ddd → rrr → close
```

Reading:

```text
sss      starts the session
vvv      clarifies the understanding
nnn      records the plan
gogogo   executes against the plan
ddd      requires the human decision
rrr      seals the session with audit + retro hand-off
close    archives the session capsule
```

## Universal Ritual Contract

Every ritual command MUST:

1. **Validate preconditions** — current graph state allows this ritual.
2. **Emit pre-event** — `<ritual>.invoked` or `<ritual>.proposed` to audit.
3. **Delegate work to the organ** that owns that role.
4. **Consume the organ's verdict** — never override it.
5. **Fire the state transition** through Kernel.
6. **Emit post-event** — `<ritual>.passed` or `<ritual>.completed`.
7. **Print the next-step hint** — what ritual comes next.

Every ritual command MUST NOT:

1. **Execute organ work itself** (no semantic derivation in rrr; no policy decisions in nnn; no verification in gogogo beyond invoking Verifier).
2. **Skip preconditions** (no "good enough" auto-pass on a missing field).
3. **Mutate state without going through Kernel.**
4. **Silently swallow organ failures.**

---

## Per-Ritual Contract

### sss — Start Session

| Field | Value |
|---|---|
| Role | Session creation gate |
| Pre-state | `(no active session)` |
| Post-state | `READY` |
| Owning organ | Kernel (Organ #1) + Ritual Controller (Organ #4) |
| Required input | task name / slug |
| Required output artifacts | `META.json`, `CONTROL/META.json`, `THINK/00_CONTEXT.md`, `DO/snapshot/`, `DO/dev/`, `DO/prod/`, `.state/` |
| Audit events | `session.created` |
| Forbidden behavior | Creating a session while another is active (must close first) |
| Failure behavior | Returns ERROR with `next` hint |
| Implementation | `.ai/cli/commands/session.py:new()` |

**Today's pattern:**

```bash
ai session new "feat <slug>"
```

---

### vvv — Verify Understanding (5 questions)

| Field | Value |
|---|---|
| Role | Understanding gate — forces explicit goal/scope/constraint/acceptance/risk before planning |
| Pre-state | `READY` |
| Post-state | `THINK` |
| Owning organ | Planner (Organ #5) + Ritual Controller (Organ #4) |
| Required input | answers to the 5 questions |
| Required output artifacts | `THINK/01_PROMPT.md`, `.state/vvv_pass` |
| Audit events | `vvv.proposed`, `vvv.passed` (or `vvv.failed`) |
| Forbidden behavior | Auto-answering for the operator; skipping any of the 5 questions |
| Failure behavior | `vvv.failed` HALTs at `READY` |
| Implementation | `.ai/cli/commands/vvv.py` |

**The 5 questions:**

```text
Q1 (Goal)        What does success look like? (one sentence)
Q2 (Scope)       What is explicitly in scope? What is out?
Q3 (Constraint)  What cannot be touched? (policies, boundary docs)
Q4 (Acceptance)  What measurable signal proves 'done'?
Q5 (Risk)        What is the most likely failure mode?
```

---

### nnn — Plan + Budget

| Field | Value |
|---|---|
| Role | Plan gate — records `plan_envelope.json` with budget, allowed/forbidden paths, steps, acceptance |
| Pre-state | `THINK` |
| Post-state | `DO` (via SANDBOX) |
| Owning organ | Planner (Organ #5) — produces the artifacts. Ritual Controller routes. Policy Engine validates. |
| Required input | `THINK/plan_envelope.json` |
| Required output artifacts | `THINK/02_SCOPE.md`, `THINK/03_ACCEPTANCE.md` + `.yaml`, `.state/plan.json`, `.state/nnn_pass` |
| Audit events | `nnn.proposed`, `nnn.passed` |
| Forbidden behavior | Approving a plan whose budget exceeds the declared override; pulling work from later phases into the current plan |
| Failure behavior | `nnn.failed` HALTs at `THINK` |
| Implementation | `.ai/cli/commands/nnn.py` |

**Plan envelope MUST declare:** `goal`, `tier` (HOT/WARM/COLD per Addendum §B), `allowed_paths`, `forbidden_paths`, `steps[]`, `acceptance[]`, `budget_override` (when applicable, with `decided_by: human`).

---

### gogogo — Execute Plan

| Field | Value |
|---|---|
| Role | Execution gate — walks `.state/plan.json` step by step, invokes verifier checkpoint per step |
| Pre-state | `DO` |
| Post-state | `VERIFIED` |
| Owning organ | Executor (Organ #6) — performs the work. Sandbox (Organ #7) — bounds it. Verifier (Organ #8) — checks each step. Ritual Controller routes. |
| Required input | `.state/plan.json` + working tree state |
| Required output artifacts | `diff.patch`, `execution.log`, `tool_calls.jsonl`, `artifact_manifest.json`, `verifier_report.json` |
| Audit events | `gogogo.step.started`, `gogogo.step.completed` (or `gogogo.step.failed`), `gogogo.completed` |
| Forbidden behavior | Skipping verifier per step; mutating outside `allowed_paths`; auto-promoting after green |
| Failure behavior | Step failure HALTs at `DO` with `gogogo.step.failed` |
| Implementation | `.ai/cli/commands/gogogo.py` |

**Verifier per step** must produce a verdict (PASS / FAIL / UNVERIFIED) with cited evidence per Article VIII.

---

### ddd — Deploy Decision (Human Gate)

| Field | Value |
|---|---|
| Role | Human decision gate — collects the human approval as an artifact (Article XIII) |
| Pre-state | `VERIFIED` |
| Post-state | `DEPLOYED` (or `FAILED` / `ABORTED` on rejection) |
| Owning organ | DDD / Human Gate (Organ #13). Ritual Controller routes. Transport Gateway (Organ #14) may deliver the approval envelope under HMAC. |
| Required input | `--target=dev\|prod`, `--reason`, `--evidence <path-to-deploy_check-evidence.json>`, optional `--hmac-envelope-file` (Article XV) |
| Required output artifacts | `decision_packet.json`, one of `approval.json` / `rejection.json` / `hold.json` |
| Audit events | `ddd.proposed`, `ddd.completed` with `decided_by`, `target`, `reason`, `evidence_ref` |
| Forbidden behavior | Approving without a verifier report; bypassing HMAC verification for transport-delivered approvals (Article XV) |
| Failure behavior | Rejection produces `rejection.json` and HALTs deployment; `--skip-verify` is logged as a warning |
| Implementation | `.ai/cli/commands/ddd.py` |

**Critical:** for COLD-tier deploys, `--skip-verify` is forbidden by policy and rejected.

---

### rrr — Retro / Terminal Gate

| Field | Value |
|---|---|
| Role | Terminal governance gate — runs acceptance checks, forbidden-diff, metrics, fires DONE transition, delegates retro indexing to Memory |
| Pre-state | `DEPLOYED` (or `VERIFIED` for HOT-tier work) |
| Post-state | `DONE` |
| Owning organ | RRR Terminal Gate (Organ #12) — gate + closure. Retro (Organ #11) — semantic reflection draft. Memory (Organ #9) — indexes retro mechanically. Audit (Organ #10) — records the closure event. |
| Required input | session in `VERIFIED` / `DEPLOYED`; optional `--retroactive` |
| Required output artifacts | `THINK/RETRO.md` (deterministic closure envelope), `.ai/memory/retros/NNNN_<timestamp>_<slug>.md` (canonical retro artifact) |
| Audit events | `rrr.proposed`, `rrr.completed` (or `rrr.retroactive`) |
| Forbidden behavior | Calling `memory-cli learn` (Article IX — Memory must not derive semantic meaning); auto-pinning retros; rewriting prior retros |
| Required behavior | Calling `memory-cli index <retro-path>` (mechanical); suggesting `memory-cli pin` only when a `decided_by:human` transition exists in the session — human pins, system does not |
| Failure behavior | Acceptance/forbidden-diff failure produces `rrr.failed`; HOT-tier MAY complete with `FAILED_VISIBLE` flag; COLD-tier MUST block closure |
| Implementation | `.ai/cli/commands/rrr.py` (Phase 1 of PRD refactors this to obey Article IX) |

**Phase 1 PR (`feat-kernel-rrr-v01-memory-surface`) changes:**

```text
OLD: memory-cli learn --file=<retro>   (semantic, Article IX violation)
NEW: memory-cli index <retro-path>     (mechanical, evidence retrieval)
audit field memory_learn → memory_index
```

---

### close — Session Finalizer

| Field | Value |
|---|---|
| Role | Seal and archive the completed session |
| Pre-state | `DONE` / `FAILED` / `ABORTED` |
| Post-state | `(archived)` |
| Owning organ | Close / Session Finalizer (Organ #18). Audit emits the final event. |
| Required input | terminal session state; optional `--force` |
| Required output artifacts | `final_manifest.json` (planned, Phase 15), `session_close_report.md` (planned) |
| Audit events | `session.closed` with `final_manifest_sha256` (planned) |
| Forbidden behavior | Closing on a non-terminal state without `--force`; rewriting audit or retro |
| Failure behavior | Non-terminal state blocks; `--force` allowed but emits `session.closed.forced` audit |
| Implementation | `.ai/cli/commands/close.py` |

---

## Ritual → Organ Delegation Matrix

```text
sss     → Kernel (#1) + Ritual Controller (#4)
vvv     → Planner (#5) + Ritual Controller (#4)
nnn     → Planner (#5) + Policy Engine (#3) + Ritual Controller (#4)
gogogo  → Executor (#6) + Sandbox (#7) + Verifier (#8) + Ritual Controller (#4)
ddd     → DDD/Human Gate (#13) + Transport Gateway (#14, optional HMAC) + Ritual Controller (#4)
rrr     → RRR Terminal Gate (#12) + Retro (#11) + Memory CLI (#9) + Audit (#10) + Ritual Controller (#4)
close   → Close/Session Finalizer (#18) + Audit (#10)
```

Every ritual passes through the **Ritual Controller (#4)** as a routing pass-through. The Controller does NOT do work; it does routing and audit-wrap.

---

## Tier-Aware Ritual Strictness (Addendum §B)

| Tier | sss | vvv | nnn | gogogo | ddd | rrr | close |
|---|---|---|---|---|---|---|---|
| **HOT** | optional | optional | optional | invoked directly | not required | optional | not required |
| **WARM** | required | required | required | required | required (`--target=dev`) | required | recommended |
| **COLD** | required | required | required | required | required (`--target=prod` + verifier report + HMAC envelope where transport involved) | required | required (with final manifest) |

The Kernel SHOULD enforce tier-appropriate strictness at each ritual gate.

---

## Failure Visibility (Article XXIII)

Every ritual failure MUST produce:

1. A non-zero CLI exit code.
2. An audit event tagged `*.failed`.
3. A visible operator message with the cited rule, the proposed remediation, and the next-step hint.

A ritual MUST NOT pretend success when its delegated organ failed. The
`memory-cli learn skipped: verb 'learn' is outside memory-cli core v0.1`
warning observed during the 2026-05-12 retroactive `rrr` is an example
of the visibility this contract requires: the failure was reported, the
audit chain shows it, and the next PR (Phase 1) closes the gap.

---

## Versioning

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-12 | Initial Ritual Contract |

Future revisions: Article XXIX (Constitutional Amendment) applies.
