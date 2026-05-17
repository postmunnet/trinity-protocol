# Session Close Report

- **Session:** {{plain_text:session.slug}}
- **Session ID:** {{plain_text:session.id}}
- **Tier:** {{enum:plan.tier}}
- **Requested at (UTC):** {{plain_text:close.requested_at_utc}}
- **Completed at (UTC):** {{plain_text:close.completed_at_utc}}
- **Ritual:** close (Session Finalizer)
- **Authority:** Trinity Constitution Articles X (Audit Discipline) & XXX (Completion Rule); Ritual Constitution v1.1-rc Articles V/VI/VII/XII/XIV/XV/XVI/XVII/XVIII; Ritual Contract v1.0 — close clauses (final manifest); Addendum v1.0.1 §D (COLD-tier external audit).

> This report is kernel-mechanical. Per Constitution Article X, the audit
> chain is append-only — close MUST NOT rewrite prior events; any
> correction is a NEW event. Per Article XX (Passive Core), close runs
> only on explicit invocation against a terminal session state. Per
> Ritual Constitution Article XV, transport MAY deliver the close
> command but MUST NOT decide closure; the kernel verifies terminal
> state and emits `close.completed`.

## Final State

- **Final state at close-invocation:** {{enum:session.final_state}}
- **Target state on success:** SEALED
- **Tier policy:** {{enum:plan.tier}} — COLD tier emits an external audit artifact per Addendum v1.0.1 §D; HOT/WARM omit it.

### Outcome Summary (carried forward from retro, not edited)

{{markdown_escaped:summary_notes}}

## Artifact Manifest

- **Final manifest:** {{evidence_ref:final_manifest.path}}
- **Artifact count (sha256 hashes captured):** {{json_string:final_manifest.artifact_count}}

The manifest enumerates every file under `DO/prod/` with its sha256
hash, the session metadata, and the audit chain anchor at completion
time. Per Ritual Contract v1.0, the manifest is the canonical
post-mortem evidence package — downstream auditors replay the chain
from the anchor and re-hash artifacts to confirm integrity.

## Audit Chain Anchor

- **Head event hash at close.completed (sha256):** {{evidence_ref:audit_chain_anchor}}

Per Constitution Article X, audit replay is the source of truth for
what happened in this session. close does NOT modify any prior event;
the anchor freezes the chain head as of close-completion. Subsequent
corrections (if any) MUST be emitted as new events in a separate
session — never appended to a SEALED session in place.

## External Audit (COLD tier only)

- **External audit artifact:** {{evidence_ref:external_audit.path}}

Present only when `plan.tier == COLD`. Emitted to
`audit/external/<UTC-date>/<sid>.audit.json` for off-host retention
per Addendum v1.0.1 §D. For HOT/WARM tiers this section is rendered
with the placeholder unresolved by design (kernel context omits the
key) and the check template treats the absence as PASS.

---

## Next Ritual

On `close.completed`, the kernel transitions the session
`DONE|FAILED|ABORTED → SEALED`. A SEALED session is read-only; any
follow-up work (re-open, remediation, amendment) MUST occur in a new
session that cites this manifest as evidence. Per Article XX the core
does not self-trigger re-open; the operator initiates with `sss` on a
new slug. Per Article XIII any destructive follow-up (archive purge,
external publication of audit) requires explicit human authority and
its own decision packet.
