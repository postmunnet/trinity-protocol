# Step {{plain_text:step.id}} — Execution Log

> Written by the Executor Agent during the `gogogo` ritual; verdict appended by the Verifier Agent.
> Authority: Trinity Ritual Constitution v1.1-rc Articles V (Ritual Contract), VIII (Kernel Validation Boundaries), XVI (Template Injection Protection), XVIII (Role Matrix); Trinity Constitution v1.0 Articles III (AI cannot self-govern), VIII (verification discipline), XX (Passive Core).
> This artifact is **mechanical execution evidence**, not a decision. The Verifier emits the verdict; the kernel records it; no agent self-certifies.

## 1. Session Identity

- Session ID: {{plain_text:session.id}}
- Session Slug: {{plain_text:session.slug}}
- Session Dir: {{path:session.dir}}
- Step ID: {{plain_text:step.id}}
- Owner Role (this step body): {{enum:step.owner_role}}

## 2. Action Summary

{{markdown_escaped:step.action_summary}}

## 3. Timing

- Started At (UTC): {{plain_text:step.started_at_utc}}
- Completed At (UTC): {{plain_text:step.completed_at_utc}}

## Verdict

{{enum:step.verdict}}

(Enum: PASS / FAIL / UNVERIFIED. Per Constitution Article VIII, PASS without evidence is forbidden — kernel rewrites such a verdict to UNVERIFIED.)

## Evidence

{{evidence_ref:step.evidence}}

(Artifact path + sha256, or audit event reference. Verifier-cited; required by Article VIII. Absence triggers BLOCK per `check.template.json.failure_behavior.on_missing_evidence`.)

## 4. Verifier Notes

{{markdown_escaped:step.notes}}

## 5. Authority Provenance

- Author Role: Executor Agent (step body); Verifier Agent (verdict + evidence)
- Decision Authority: none (gogogo executes; ddd decides promote/reject; human decides deploy)
- Advisory Only: false for the per-step verdict, true for any commentary in notes
- Self-Certification: forbidden (Article III) — `step.owner_role` MUST differ from the role that emits `step.verdict`
