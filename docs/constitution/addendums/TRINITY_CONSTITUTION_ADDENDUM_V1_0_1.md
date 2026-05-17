---
title: "Trinity Constitution Addendum v1.0.1"
version: "1.0.1"
status: "locked"
last-updated: "2026-05-12"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
parent: "TRINITY_CONSTITUTION_V1.md"
amendment-policy: "Article XXIX of the parent Constitution. This Addendum may be revised independently of the Constitution provided the amendment policy is honoured."
---

# Trinity Constitution Addendum v1.0.1

> This Addendum is a Section under the Trinity Constitution v1.0. It does
> not amend any Article; it operationalises five concepts that the
> Constitution names but does not detail:
>
> 1. Genesis Trust
> 2. Decision Velocity Tiers
> 3. Break-Glass Procedure
> 4. External Audit
> 5. Cognitive Presentation
>
> If this Addendum conflicts with the parent Constitution, the parent
> wins (Article XXV — Constitutional Priority Order).

---

## Section A — Genesis Trust

### Purpose

Trinity needs a declared starting point for authority. Without one, every
"signed approval" recurses into "who signed the signer?". The Constitution
requires explicit, scoped, auditable authority (Article 0 §4) — Genesis
Trust is that explicit floor.

### Declaration

Until cryptographic ratification is implemented (Phase 14 of the PRD),
Trinity operates under:

```text
GENESIS_TRUST_ASSUMED = true
genesis_authority     = "Operator / Founder"
genesis_artifact      = trinity_organ_refactor_prd.md (hash-pinned)
genesis_date          = 2026-05-12
```

This is **assumed trust**, not proven trust. It is honest about its
limits: every Layer 0 artifact (Constitution, Addendum, Organ Map,
Ritual Contract) is hash-pinned in `audit/genesis_manifest.json` once
that file is produced (Phase 14).

### Future Schema (deferred, not implemented in Phase 0)

```yaml
genesis_manifest:
  version: 1
  declared_at: "2026-05-12T00:00:00Z"
  trusted_actors:
    - id: "operator"
      role: "founder"
      authority_scope: ["constitutional_amendment", "human_gate_approve"]
  layer_0_artifacts:
    - path: "docs/constitution/TRINITY_CONSTITUTION_V1.md"
      sha256: "<computed at genesis>"
    - path: "docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md"
      sha256: "<computed at genesis>"
    - path: "docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md"
      sha256: "<computed at genesis>"
    - path: "docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md"
      sha256: "<computed at genesis>"
  signature: null   # filled in when Phase 14 ratification ships
  revocation_log: []
```

Until Phase 14 ships, the schema MUST exist in spec form so consumers
know where ratification will land. Hidden assumptions are forbidden by
Article XIX — Genesis Trust is the honest replacement.

### Revocation

When cryptographic ratification ships, the operator MAY revoke trust by
publishing a `revocation_artifact.json` referencing the prior genesis
manifest by hash. Revocation MUST itself be audited.

---

## Section B — Decision Velocity Tiers

### Purpose

Constitution Article XXX (Completion Rule) lists what is required for a
workflow to be complete. Applied uniformly, it would block every reversible
HOT-path change behind full ritual overhead. Trinity rigor MUST be
proportional to the **blast radius** and **durability** of failure.

### Tier Table

| Tier | Use Cases | Required Rigor | Required Artifacts |
|---|---|---|---|
| **HOT** | daily coding, experiments, reversible changes, local-only edits, exploratory branches | lightweight checks; logs; in-session memory | working tree change; (optional) lightweight log |
| **WARM** | feature work, integrations, meaningful but reversible changes, sibling-CLI edits, doc work | deterministic checks; plan envelope; audit entry; verifier (Tier 0–2) | `PLAN.md`; `verification_contract.json`; `verifier_report.json`; audit entries |
| **COLD** | governance, security, production deploy, irreversible/durable mistakes, external publication, credential changes, schema migrations | full Trinity: contract + verifier + DDD + audit + (Phase 14) ratification | every artifact in Appendix B of PRD; `decision_packet.json`; `approval.json` |

### Selection Rule

```text
If failure can be reverted in < 1 hour by the operator alone → HOT.
If failure requires team coordination or external rollback → WARM.
If failure persists in users / external systems / git history that ships → COLD.
```

When in doubt, escalate one tier upward.

### Constitutional Anchoring

- HOT path remains subject to Articles III, X, XVI, XX, XXIII (no
  self-governance, audit, least authority, passive core, failure
  visibility) — but skips Articles VI, VIII, XIV when not needed.
- WARM path adds Articles VI (Planning), VIII (Verification), XI/XII
  (state machine).
- COLD path adds Articles XIII (Human Authority), XIV (Critical Gates),
  XXII (Recovery), XXIX (Amendment where applicable), and the Genesis
  Trust + Presentation Protocol below.

The Kernel SHOULD record the declared tier in every session's `META.json`
or `plan_envelope.json` so the verifier can apply tier-appropriate rules.

---

## Section C — Break-Glass Procedure

### Purpose

Constitution Article XIV says critical gates MUST NOT be bypassed by
"hidden overrides". But Articles XXII (Recovery) and XXIII (Failure
Visibility) require an explicit, *visible* emergency path. Break-Glass
is that path.

### Procedure

When a verifier blocks progression and the operator judges the block to
be incorrect or non-applicable, the operator MAY override **once per
session** by producing a Break-Glass artifact:

```yaml
# .ai/sessions/<sid>/CONTROL/BREAK_GLASS.yaml
break_glass:
  session_id: "<sid>"
  declared_at: "<ISO-8601 UTC>"
  declared_by: "operator"
  reason: "<one-paragraph explanation, REQUIRED>"
  bypassed_check: "<name of the verifier rule being overridden>"
  artifact_evidence: "<path(s) to evidence supporting the override>"
  post_mortem_due: "<ISO-8601 deadline, MUST be set>"
```

### Constraints

- Break-Glass MUST emit an audit event `break_glass.invoked` with
  full payload.
- Break-Glass MUST NOT amend the Constitution, the Addendum, the
  Organ Map, or the Ritual Contract — those need Article XXIX
  (Constitutional Amendment).
- Break-Glass MUST NOT bypass Article XIII (Human Authority) — the
  operator IS the human authority; Break-Glass is not "AI bypasses
  human", it is "human bypasses verifier".
- Each Break-Glass invocation MUST be followed by a post-mortem retro
  in `.ai/memory/retros/` within the declared deadline.

### What it is NOT

- Not a way for AI to escalate authority.
- Not a way to skip audit.
- Not a way to silence a Verifier failure — the failure remains in
  the audit chain; Break-Glass overlays an explicit override on top.

---

## Section D — External Audit

### Purpose

For COLD-path workflows that publish externally or touch
customer/legal/financial state, in-session audit is necessary but not
sufficient. Article X requires audit; this Section operationalises
"external" audit for COLD path.

### Requirements

A COLD-path workflow SHOULD emit an external audit record to a
location separate from the session sandbox:

```text
audit/external/<UTC-date>/<session-id>.audit.json
```

Contents:

```yaml
session_id: "<sid>"
tier: "COLD"
final_state: "DEPLOYED|FAILED|ABORTED"
artifacts:
  - path: "<path>"
    sha256: "<hash>"
decision:
  approver: "<actor>"
  approval_artifact: "<path>"
  approval_artifact_sha256: "<hash>"
external_systems_touched:
  - name: "<system>"
    operation: "<verb>"
    target: "<resource>"
    reversible: false
audit_chain_anchor:
  events_ndjson_hash: "<sha256 of audit chain at this session's rrr.completed>"
```

### Anchoring

The `audit_chain_anchor` field MUST reference the canonical
`.ai/audit/events.ndjson` hash at the moment of rrr completion. This
allows future cross-verification: any future tampering of the audit
chain becomes detectable from the external record.

### Storage and Retention

External audit files MUST NOT be auto-deleted. They MAY be moved to
cold storage (file system, object storage, write-once media) once the
session is closed for ≥ 30 days, but the path index MUST remain
queryable.

---

## Section E — Cognitive Presentation

### Purpose

Article XVIII (Determinism Over Emergence) and Article XIX (Hidden State
Prohibition) protect Trinity from opaque AI behavior. They also imply a
duty to protect the operator from cognitive overload — a 200-page
verifier report is *technically* inspectable but practically not.
Cognitive Presentation defines how Trinity compresses for humans without
sacrificing truth.

### Three Layers of View

Every COLD-path decision presented to the human MUST offer:

1. **Compressed Synthesis** — a one-screen summary suitable for fast
   reading. Generated, never authoritative.
2. **Dissent Surface** — explicit list of disagreements, failed checks,
   and red flags. Even if 1 voice in 10 dissents, that voice surfaces.
3. **Raw Artifacts** — direct links to the inspectable evidence (plan,
   diff, verifier report, audit chain extract). Always present.

### Forbidden Patterns

- Hiding dissent inside a compressed summary.
- Replacing raw artifact links with chat-style narration.
- Showing only the synthesis to the human without the dissent surface.
- Presenting AI-generated confidence scores as truth.

### Artifact Shape

```yaml
presentation_packet:
  session_id: "<sid>"
  tier: "COLD"
  view:
    synthesis: "<<= one screen of markdown>"
    dissent:
      - source: "<verifier|judge-cli|test-cli|human reviewer>"
        finding: "<what disagrees>"
        severity: "BLOCK|WARN|NOTE"
        artifact_ref: "<path>"
    raw_artifacts:
      - "<path/to/PLAN.md>"
      - "<path/to/verifier_report.json>"
      - "<path/to/diff.patch>"
      - "<path/to/audit_extract.ndjson>"
  constitutional_check:
    article_xviii_determinism: "pass|warn|fail"
    article_xix_hidden_state: "pass|warn|fail"
```

### Constitutional Anchoring

The synthesis is **never** the truth layer. The truth is the linked
raw artifacts. The Compressed Synthesis is a courtesy view; if it
disagrees with the raw artifacts, the raw artifacts win.

---

## Cross-Section Invariants

These rules bind all five Sections together:

```text
1. Genesis Trust is declared, never hidden.
2. Decision Velocity Tier is declared at the start of every session.
3. Break-Glass is visible, audited, and produces a post-mortem.
4. External Audit anchors COLD work to the internal audit chain.
5. Cognitive Presentation never replaces raw artifacts.
```

If any Section's procedure conflicts with an Article of the parent
Constitution, the Article wins.

---

## Versioning

| Version | Date | Change |
|---|---|---|
| 1.0.1 | 2026-05-12 | Initial Addendum sections A–E |

Subsequent revisions MUST follow Article XXIX (explicit proposal +
rationale + impact analysis + human approval + version bump + audit
entry). Prior versions remain inspectable in git history.
