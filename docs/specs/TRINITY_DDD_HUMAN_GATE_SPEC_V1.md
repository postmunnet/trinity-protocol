# TRINITY_DDD_HUMAN_GATE_SPEC_V1

**Status:** DRAFT v2 (S6 of recordproxy alignment patch — pending verifier review + ddd)
**Phase:** 11 — Done / Deploy / Decision (DDD)
**Organ:** #13 (DDD / Human Gate)
**Constitutional rank:** 5 — Workflow Contract (per Article XXV)
**Anchor commit:** main @ 4a6fd80 (RecordProxy v1 foundation)
**Predecessor anchor:** 17e74fa (pre-RecordProxy; superseded 2026-05-13)
**Date:** 2026-05-13

## §0 — Rank-5 Authority Disclaimer (Article XXV)

Workflow Contract; void where it conflicts with the Constitution, Ritual Constitution, Canonical Policies, or Kernel State Rules. Amendments via Article XXIX. Article XIII (Human Authority) is the controlling clause for every decision artefact described here — this spec pins shape only, never authority.

## §1 — Purpose

Fix the JSON shape of the four DDD artefacts so the human gate is **machine-validatable** and **audit-anchored**:

- **decision_packet.json** — bundle the verifier evidence + presentation + escalation context that the operator reviews.
- **approval.json** — operator says PROMOTE / DEPLOY.
- **rejection.json** — operator says NO with a reason.
- **hold.json** — operator says WAIT with a deadline.

Article XIII requires the deciding artefact to carry `decided_by: human`. This spec codifies the rest.

## §2 — Lifecycle

```
verifier produces verdict
   ↓
presentation_synthesizer drafts presentation packet
   ↓
kernel writes decision_packet.json (proposal)
   ↓
operator reads packet → emits ONE of:
   - approval.json   (decided_by: human, action: promote|deploy)
   - rejection.json  (decided_by: human, action: reject, reason: …)
   - hold.json       (decided_by: human, action: hold, until: <ts>)
   ↓
kernel verifies signature/HMAC (if transport-mediated) → audit event
   ↓
graph transitions
```

## §3 — decision_packet.json

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | unique packet id |
| `session` | string | session id |
| `created_ts` | RFC3339 | when kernel emitted the packet |
| `proposing_role` | enum(planner/executor/verifier) | who is asking for the decision |
| `requested_action` | enum(promote/deploy/abort/amend) | the action being asked of the operator |
| `verifier_reports` | array of `{path, hash, capture_refs}` | references to verifier_report.json files; `capture_refs` propagated from each report (TRINITY_VERIFIER_CONTRACT_V1 §5) |
| `presentation` | object | 3-layer packet from `presentation_synthesizer`; SHAPE pinned in §3.1 below per Addendum v1.0.1 §E Cognitive Presentation Protocol |
| `expires_ts` | RFC3339 | deadline by which an absent decision becomes a TIMEOUT (rejection) |

### §3.1 presentation object — required sub-fields (Addendum v1.0.1 §E)

Per Addendum v1.0.1 §E (Cognitive Presentation Protocol), the `presentation` object MUST carry these fields. Absence of any required field is a schema-violation that the kernel MUST refuse at packet-emit time:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `cognitive_protocol_version` | string | yes | const `"v1.0.2"` (pins to Addendum v1.0.1 §E + cross-spec amendment 2026-05-15 expanding §3.1 from 9 fields to 13 fields per Phase 13 §5 alignment); future versions require Addendum |
| `summary` | string | yes | 1-3 sentence human-readable précis of what is being decided |
| `convergence` | string[] | yes | bulleted facts the verifier/planner/executor agreed on (may be empty if no agreement existed) |
| `dissent_flags` | string[] | yes | bulleted points of disagreement / unresolved tension; empty array = explicitly "no dissent flagged" |
| `founder_decisions_required` | string[] | yes | the specific decisions the operator MUST make; each entry is one decision phrased as a question |
| `raw_artifacts_available` | boolean | yes | `true` if the operator can drill into raw evidence (capture blobs, verifier reports, audit chain slice); `false` MUST be paired with an explanation in `summary` |
| `panel_diversity` | object | yes | shape: `{ roles: string[], distinct_models: integer, distinct_layers: integer }` — describes which roles/models/pyramid-layers contributed to the convergence/dissent; minimum `distinct_layers >= 2` on COLD tier |
| `synthesizer_not_in_opinion_panel` | boolean | yes | `true` asserts the presentation_synthesizer agent did NOT vote in the convergence/dissent; required-true on COLD tier (per Addendum v1.0.1 §E "the messenger is not a juror") |
| `capture_refs` | string[] | yes | ULID list of `captures.capture_id` rows backing the verifier reports; subset of the union of `verifier_reports[*].capture_refs`; the operator can navigate to per-session CAPTURE/refs/<capture_id>.json to inspect raw evidence |
| `compression_ratio` | float | yes (cognitive v1.0.2+) | ratio of synthesised summary length to total raw artifact bytes; bounded [0.0, 1.0]; lower = more compression |
| `transport_capability` | object | yes (v1.0.2+) | shape: `{channel: string, max_payload_bytes: integer, supports_attachments: boolean}` — declares the delivery channel constraints the synthesis was sized for (e.g. Telegram 4096-char limit) |
| `dissent_preserved` | string[] | optional (v1.0.2+) | alias of `dissent_flags` for Phase 13 conformance; if both present, `dissent_flags` is canonical and `dissent_preserved` MUST be byte-identical or schema violation |
| `raw_artifact_links` | string[] | optional (v1.0.2+) | URL/path-resolved form of `capture_refs` for human-clickable navigation; canonical IDs remain in `capture_refs` |

Any field unrecognised by this list is a schema violation (`additionalProperties: false`). As of cognitive_protocol_version v1.0.2 the schema is 13 fields (9 original + 4 added via Phase 13 §5 alignment), not 9; the additionalProperties:false constraint applies to the expanded 13-field set.

### §3.1.1 v1.0.2 alias mapping

The 4 fields added in v1.0.2 originate from Phase 13 §5 (Presentation Protocol). Two are newly canonical in Phase 11; two are aliases of existing canonical Phase 11 fields. The mapping is normative:

| Phase 13 §5 field | Phase 11 §3.1 canonical | Mapping rule |
|---|---|---|
| `dissent_preserved` | `dissent_flags` | alias; canonical (`dissent_flags`) wins on conflict; if both present they MUST be byte-identical |
| `raw_artifact_links` | `capture_refs` | URL/path-resolved form; canonical IDs remain in `capture_refs`; `raw_artifact_links` carries clickable navigation strings |
| `compression_ratio` | `compression_ratio` | newly canonical in Phase 11 v1.0.2 |
| `transport_capability` | `transport_capability` | newly canonical in Phase 11 v1.0.2 |

Synthesizers conforming to Phase 13 §5 MAY emit either the alias name or the canonical name. Validators MUST accept both. The kernel-side validator collapses aliases to canonical before audit emission; conflict (both present, byte-different) is a schema violation.

### §3.2 Why these presentation fields are required

Per Addendum v1.0.1 §E, the cognitive failure mode at human gates is **not** "operator lacked information" — it is "operator was shown synthesised consensus without dissent surface, without diversity audit, and without a path to raw evidence." Each required field above is the operational guard against one specific failure mode:

- `dissent_flags` — surfaces disagreement (anti-groupthink)
- `panel_diversity` — proves the convergence wasn't 3 instances of the same model agreeing (anti-monoculture)
- `synthesizer_not_in_opinion_panel` — separates messenger from juror (anti-synthesis-collapse)
- `raw_artifacts_available` + `capture_refs` — guarantees a drill-down path (anti-summary-only)
- `founder_decisions_required` — surfaces *which* decisions the operator is on the hook for (anti-rubber-stamp)
- `cognitive_protocol_version` — pins the contract so DDD downstream can detect when a presentation was generated against an outdated version
- `compression_ratio` — surfaces synthesis discipline (anti-overload); a synthesis with ratio near 1.0 is a passthrough that defeats the purpose of compression; a ratio near 0.0 is suspect for over-compression (added v1.0.2)
- `transport_capability` — pins the delivery channel constraints (anti-truncation-surprise) so the operator can detect when the channel that delivered the synthesis cannot resolve raw evidence drill-down (added v1.0.2)
- `dissent_preserved` (alias) — Phase 13 v1.0 compatibility shim; canonical field is `dissent_flags`; both fields if present MUST be byte-identical (added v1.0.2)
- `raw_artifact_links` — operator-clickable evidence path (Phase 13 §3 truth-layer requirement); URL/path form of `capture_refs` for transports that surface clickable links (added v1.0.2)

## §4 — approval.json

| Field | Type | Meaning |
|---|---|---|
| `packet_id` | string | references decision_packet.id |
| `decided_by` | string | const "human" |
| `decided_at` | RFC3339 | operator timestamp |
| `action` | enum(promote/deploy/amend_approve) | matches packet.requested_action subset |
| `notes` | string | operator commentary; optional |
| `signature` | object | nullable; HMAC envelope per `.ai/cli/core/auth.py` when transport-mediated |

## §5 — rejection.json

| Field | Type | Meaning |
|---|---|---|
| `packet_id` | string | references decision_packet.id |
| `decided_by` | string | const "human" |
| `decided_at` | RFC3339 | operator timestamp |
| `action` | string | const "reject" |
| `reason` | string | required, ≥1 char — the *why* |
| `signature` | object | nullable; HMAC envelope |

## §6 — hold.json

| Field | Type | Meaning |
|---|---|---|
| `packet_id` | string | references decision_packet.id |
| `decided_by` | string | const "human" |
| `decided_at` | RFC3339 | operator timestamp |
| `action` | string | const "hold" |
| `until` | RFC3339 | required deadline after which kernel may re-prompt or escalate |
| `notes` | string | optional — what the operator is waiting on |
| `signature` | object | nullable; HMAC envelope |

## §7 — Audit Anchoring

Every emission MUST register an event via the **per-session AuditWriter** (TRINITY_AUDIT_EVENT_SPEC_V1 §2 — 13-field shape; per-session SQLite at `<session>/CAPTURE/capture.sqlite` audit_events table; NOT direct write to legacy `.ai/audit/events.ndjson`):

- `ddd.packet_emitted` for decision_packet.json
- `ddd.approved` / `ddd.rejected` / `ddd.held` for the corresponding decision file
- `ddd.timeout` if `decision_packet.expires_ts` passes without a decision file

Each event carries `payload_json = {path, sha256, capture_refs (optional)}` of the source JSON, plus `actor = "human"` for the decision events (`actor = "kernel"` for `ddd.packet_emitted` and `ddd.timeout`). The per-session hash chain integrity check (TRINITY_AUDIT_EVENT_SPEC_V1 §2.1) covers these as it covers everything else; legacy ndjson MAY receive a mirrored 5-field row for backward-compatible tools.

### §7.1 Cross-reference to canonical event registry

The `ddd.*` event types above are registered in TRINITY_AUDIT_EVENT_SPEC_V1 §3 under the "Ritual gates (kernel)" section. The event row shape is the 13-field shape (§2 of that spec); `schema_version=trinity.audit_event.v1`; `seq` claimed under `BEGIN IMMEDIATE`. The `capture_id` field is optional for DDD events (decision packets are not themselves capture transactions; the decision is made *about* upstream captures via `capture_refs` in the payload).

## §8 — Cross-references

- **TRINITY_VERIFIER_CONTRACT_V1 §5, §6** — source of `decision_packet.verifier_reports[].{path,hash,capture_refs}`; DDD MUST propagate `capture_refs` into `presentation.capture_refs[]`.
- **TRINITY_AUDIT_EVENT_SPEC_V1 §2, §3** — 13-field event shape; `ddd.*` events registered in §3 canonical registry; per-session AuditWriter is the write target (NOT legacy ndjson).
- **TRINITY_SESSION_CLOSE_SPEC_V1 §2** — DDD artefacts (decision_packet / approval / rejection / hold) covered by final-manifest hash.
- **Constitution Article XIII** — controlling authority clause for `decided_by: human`; this spec implements but does not extend.
- **Addendum v1.0.1 §E (Cognitive Presentation Protocol)** — controlling clause for §3.1 presentation required fields; this spec implements §E without re-deriving it.
- **`presentation_synthesizer` agent** at `.ai/cli/agents/presentation_synthesizer/` — drafts the `presentation` object conforming to §3.1.

## §9 — Open Questions

- HMAC signing on operator-side transport (`trinity-tg-bot`) — keying covered in Phase 14 (deferred); for Phase 11 the `signature` field is nullable.
- Multi-operator quorum (e.g. 2-of-N) — out of scope for V1; current contract is single-operator.

## §10 — Out of Scope

- Runtime ddd kernel command (already exists; this spec defines the shape it must read/write).
- Telegram transport contract — Article XV (Transport is not Authority).
- Phase 14 crypto attestation.

---

**Authors:** Trinity Executor (operator direct-draft).
