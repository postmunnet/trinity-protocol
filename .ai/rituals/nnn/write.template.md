# Scope

> Written by the Planning Agent during the `nnn` ritual.
> Authority: Trinity Ritual Constitution v1.1-rc Articles V (Three-Template Model), VI (Check Templates), VII (Ritual Registry), XII (per-ritual specs), XIV (Velocity Tiers), XVI (Template Injection Protection), XVII (State Machine), XVIII (Role Matrix); Constitution v1.0 Article XXII (Recovery & Reversibility).
> This artifact is the human-readable scope summary. The canonical machine-readable plan lives at `THINK/plan_envelope.json` with its sibling contracts `THINK/verification_contract.json`, `THINK/risk_assessment.json`, and `THINK/rollback.md`.
> The Planning Agent proposes; the Kernel + Verifier decide. This ritual does NOT self-certify PASS.

Session: {{plain_text:session.slug}}
Operator: {{plain_text:operator.name}}
Proposed at (UTC): {{plain_text:nnn.proposed_at_utc}}
Velocity Tier: {{enum:plan.tier}}

## Goal

{{markdown_escaped:plan.goal}}

## In Scope

The executor (`gogogo`) MAY write only the following paths:

{{markdown_escaped:plan.allowed_paths_list}}

## Out of Scope

The executor MUST NOT touch the following paths (forbidden write surface):

{{markdown_escaped:plan.forbidden_paths_list}}

## Constraints

- Velocity Tier {{enum:plan.tier}} governs the required-rituals path per Article XIV.
- Verifier rules in `.ai/policies/verifier-rules.yaml` decide PASS / RETRY / NEEDS_HUMAN / DEAD; the Planning Agent does NOT decide verdict.
- Boundary documents (`.ai/policies/**`, `.ai/audit/**`, `.ai/schemas/**`, `docs/specs/**`, `docs/constitution/**`) are forbidden writes regardless of plan content.
- Rollback (Constitution v1.0 Article XXII) is declared below and mirrored in `THINK/rollback.md`; no execution may begin without it.

## Acceptance

The plan is considered "done" when ALL of the following measurable signals hold (mirrors `plan_envelope.json.acceptance` and `THINK/03_ACCEPTANCE.{md,yaml}`):

{{markdown_escaped:plan.acceptance_list}}

## Steps (Summary)

{{markdown_escaped:plan.steps_summary}}

## Rollback

{{markdown_escaped:plan.rollback_summary}}

## Provenance

- Author Role: Planning Agent (Article XVIII row 5)
- Advisory Only: true
- Decision Authority: none (verdict belongs to Verifier Agent during `gogogo` / `ddd`; promotion belongs to human)
- Companion artifacts:
  - `THINK/plan_envelope.json` (canonical structured plan)
  - `THINK/verification_contract.json` (predicates the Verifier will run)
  - `THINK/risk_assessment.json` (risk register feeding Article XIV / XXII)
  - `THINK/03_ACCEPTANCE.md` and `THINK/03_ACCEPTANCE.yaml` (acceptance criteria)
  - `THINK/rollback.md` (reversibility plan, Constitution v1.0 Article XXII)
  - `.state/nnn_pass` (kernel-written sentinel; never written by the Planning Agent itself)

## Next Step

On Kernel + Verifier approval of these artifacts, the session transitions `THINK -> PLAN` per Article XVII. The next ritual is `gogogo` (bounded execution). Until the Kernel records `.state/nnn_pass`, no executor mutation may begin.
