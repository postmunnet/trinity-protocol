# Session Context

> Written by the Session Initializer during the `sss` ritual.
> Authority: Trinity Ritual Constitution v1.1-rc Article I (Core Ritual Model), Article XVI (Template Injection Protection), Article XVIII (Role Matrix).
> This artifact is **mechanical bootstrap evidence** — it does not decide workflow meaning. Semantic clarification belongs to the `vvv` ritual.

## 1. Session Identity

- Session ID: {{plain_text:session.id}}
- Session Slug: {{plain_text:session.slug}}
- Session Directory: {{path:session.dir}}
- Created At (UTC): {{plain_text:created_at_utc}}
- Operator: {{plain_text:operator.name}}

## 2. Declared Goal

{{plain_text:session.goal}}

## 3. Velocity Tier

{{enum:session.risk_tier}}

(Tier governs which downstream rituals are required per Article XIV. Escalation HOT to WARM to COLD is auditable per Article XIV.1.)

## 4. Workflow Type

{{plain_text:session.workflow_type}}

## 5. Capsule Layout

The Session Initializer created the following directories under {{path:session.dir}}:

- `THINK/` (this file lives here)
- `SANDBOX/` (per-agent scratch)
- `DO/dev/` (executor mutation surface)
- `DO/prod/` (human-promoted-only)
- `DO/snapshot/` (deterministic snapshots)
- `CONTROL/` (session manifest + control state)
- `.ai/state/` (machine-readable kernel state)

## 6. Kernel Provenance

- Project Root: {{path:project_root}}
- Predecessor Audit Hash: {{plain_text:kernel.previous_audit_hash}}
- Author Role: Session Initializer
- Advisory Only: true
- Decision Authority: none (semantic decisions belong to `vvv` / `nnn` / human gates)

## 7. Next Step

The kernel will transition this session from `READY` to `THINK`. The next ritual is `vvv` (clarification). Until `vvv` records explicit operator intent, no downstream ritual may run.
