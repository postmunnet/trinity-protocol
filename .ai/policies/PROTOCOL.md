# Trinity Protocol — SSOT (Policy-as-Code)

This file anchors the authoritative rules (SSOT) for Trinity Protocol in this repo.

Core principles:
- Artifact > Chat: work results are files (plan, diff, tests, reports).
- Policy-as-Code: safety rules live under `.ai/policies/` and are enforced by the CLI.
- Git-as-Truth: Git/PR/commits are the single source of truth for code.

Three Locks:
- Lock 1 — SSOT: policies and schemas in `.ai/policies/**` govern behavior.
- Lock 2 — Smart Gates: automated validation (syntax, secrets/PII, tests, scope) based on `safety.yaml`.
- Lock 3 — Tamper-Evident Audit: append-only, hash-chained logs in `.ai/audit/events.ndjson`.

Trust boundaries:
- Human-only write: `.ai/policies/**`, PRIMER/README specs.
- System-only write: `.ai/audit/**`, `.ai/state/**` (append-only, generated).
- AI-writable (guarded): capsule artifacts under `.ai/sessions/active/<capsule>/` per scope rules.

Refer to `codex_TRINITY_BLUEPRINT_v1.0.md` and `UNIFIED_TRINITY_STRATEGY.md` for detailed contracts.

