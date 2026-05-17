# TRINITY_SESSION_CLOSE_SPEC_V1

**Status:** DRAFT v2 (S2 of recordproxy alignment patch — pending verifier review + ddd)
**Phase:** 15 — Close / Session Finalizer
**Organ:** #18 (Close)
**Constitutional rank:** 5 — Workflow Contract (per Article XXV)
**Anchor commit:** main @ 4a6fd80 (RecordProxy v1 foundation)
**Predecessor anchor:** 17e74fa (pre-RecordProxy; superseded 2026-05-13)
**Date:** 2026-05-13

## §0 — Rank-5 Authority Disclaimer (Article XXV)

Workflow Contract; void where it conflicts with higher-ranked instruments. Amendments via Article XXIX. This spec pins the **shape** of artefacts the existing `close.py` MUST produce; it does not re-author `close.py` itself. RecordProxy v1 at `.ai/cli/core/recordproxy/**` is the immutable evidence-layer ground truth; this spec defines how close seals it.

## §1 — Purpose

Close ships today as a kernel command but produces no **final manifest** and emits no **External Audit** record. Both are required by the predecessor audit verdict §3 for COLD-tier production-readiness. RecordProxy v1 (commit `4a6fd80`) introduces a per-session evidence layer at `<session>/CAPTURE/{capture.sqlite,blobs/,refs/}` and a per-session audit chain — close MUST seal **all of it**, not just the legacy `THINK/DO/SANDBOX/CONTROL` artefacts.

This spec defines:

1. The **final-manifest** hash structure that `close.py` MUST compute (including the CAPTURE/ layer; §2).
2. The **session-scoped audit anchor** that replaces the previous global `events.ndjson` hash (§3).
3. The **External Audit** emission contract — file location, fields, hash anchoring — per Addendum v1.0.1 §D (§3 + §4).

Invariant (DESIGN.md §22): **"No capture envelope = invalid ritual evidence."** A close that ignores CAPTURE is not a real close — it seals artefacts without sealing the evidence of how they were produced.

## §2 — Final Manifest

At `close` time, `close.py` MUST compute a single canonical manifest covering every artefact produced in the session, **including the CAPTURE/ evidence layer**:

```yaml
session_id: <sid>
closed_at: <RFC3339>
tier: HOT|WARM|COLD
graph_state_final: DEPLOYED|VERIFIED|ABORTED|FAILED|DONE|SEALED

artifacts:
  - path: <session-relative-path>          # files under DO/{dev,prod,snapshot}, SANDBOX, THINK, CONTROL
    sha256: <hash>
    size_bytes: <int>

captures:
  capture_store:
    path: CAPTURE/capture.sqlite           # SQLite manifest (capture_store.py:107)
    sha256: <hash>                         # checkpoint hash at close
    size_bytes: <int>
  blobs_root:
    path: CAPTURE/blobs/sha256             # CAS root (capture_store.py:105)
    blob_count: <int>
    total_bytes: <int>
  refs_root:
    path: CAPTURE/refs                     # capture-id reference files (DESIGN.md §4)
    ref_count: <int>
  capture_ids:                             # ULID list of every capture in this session
    - <cap_01...>
    - <cap_02...>
  capture_manifest_sha256: <hash>          # sha256 of canonicalised captures.* block above

audit:
  session_chain_head: <last_event.hash>    # see §3
  last_seq: <int>                          # last AuditWriter seq
  capture_chain_consistent: true|false     # verify_chain() result at close

manifest_sha256: <sha256 of canonicalised manifest body, excluding manifest_sha256 itself>
```

The manifest body MUST be sorted by `path` (and `capture_ids` by ULID lex order) to make `manifest_sha256` deterministic. The hash MUST cover:

- every file under `DO/dev/`, `DO/prod/`, `DO/snapshot/`, `SANDBOX/`, `THINK/`, `CONTROL/`
- every `verifier_report.*.json` and DDD artefact (decision_packet / approval / rejection / hold)
- **the `captures.*` block** (SQLite checkpoint hash + blobs/refs roots + capture_ids list)

The manifest file lands at `<session>/CONTROL/final_manifest.yaml`. `close.py` emits one `close.manifest_built` audit event via per-session AuditWriter (TRINITY_AUDIT_EVENT_SPEC_V1 §2) with payload `{path, sha256: manifest_sha256, capture_count, last_seq}`.

### §2.1 Why CAPTURE must be in the manifest

DESIGN.md §22 invariant: "No capture envelope = invalid ritual evidence." If close manifests every output artefact but does not seal CAPTURE/, the artefacts are sealed but the *evidence of how they were produced* is unsealed and mutable post-close. This is incompatible with COLD-tier production-readiness (predecessor audit verdict §3). The `captures.*` block makes the evidence layer first-class and tamper-evident at the manifest level.

### §2.2 Capture status check at close

Before emitting `close.manifest_built`, `close.py` MUST verify:

- Every `captures` row in `CAPTURE/capture.sqlite` has `status ∈ {COMPLETED, RECONCILED, ARCHIVED}` (DESIGN.md §6).
- Any `FAILED_PARTIAL`, `ORPHANED_INVOCATION`, or stuck `CAPTURING` rows MUST escalate per the Verifier verdict mapping (TRINITY_VERIFIER_CONTRACT_V1 §2.1):
  - HOT → close proceeds with `audit.capture_chain_consistent: false` and a warning event
  - WARM → `NEEDS_HUMAN` (Article XIII); close blocks
  - COLD → close refuses (`TERMINAL_FAILED`); operator MUST resolve before re-attempting

## §3 — External Audit (Addendum v1.0.1 §D, RecordProxy-aligned)

For sessions with `tier: COLD`, `close.py` MUST additionally emit:

```text
audit/external/<UTC-date>/<session-id>.audit.json
```

The shape preserves Addendum v1.0.1 §D **except** for `audit_chain_anchor`, which is rebased on the per-session AuditWriter chain (RecordProxy v1):

```yaml
session_id: <sid>
tier: COLD
final_state: DEPLOYED|FAILED|ABORTED|SEALED
artifacts:
  - path: <path>
    sha256: <hash>
captures:                                # NEW vs Addendum v1.0.1 §D pre-RecordProxy
  capture_store_sha256: <hash>           # sha256 of CAPTURE/capture.sqlite at rrr.completed
  capture_ids: [<cap_01...>, ...]
  capture_manifest_sha256: <hash>
decision:
  approver: <actor>
  approval_artifact: <path>
  approval_artifact_sha256: <hash>
external_systems_touched:
  - name: <system>
    operation: <verb>
    target: <resource>
    reversible: false
audit_chain_anchor:
  session_id: <sid>                      # the anchor is scoped to THIS session
  session_chain_head: <last_event.hash>  # last hash from per-session audit_events SQLite
  last_seq: <int>                        # last seq number (UNIQUE per session)
  audit_export_ref:                      # OPTIONAL legacy export reference
    path: .ai/audit/events.ndjson        # legacy global file (§2.2 of Audit Event Spec)
    sha256: <sha256 of file at rrr.completed; recorded for cross-check only>
```

`session_chain_head` and `last_seq` MUST be read from the per-session SQLite at the moment `rrr.completed` fires (via `AuditWriter.read_chain(session_id)` — audit_writer.py:122). Recorded once; re-read at close to confirm no drift in the session chain. The legacy `audit_export_ref` block is OPTIONAL and provided only for tools that still consume the global ndjson; it is **not** a hash chain anchor.

External Audit files MUST NOT be auto-deleted (per Addendum v1.0.1 §D Storage and Retention).

### §3.1 Why global `events_ndjson_hash` was wrong

The previous version of this spec (anchored at `17e74fa`, before RecordProxy v1) hashed the **entire** `.ai/audit/events.ndjson` content at `rrr.completed`. This was broken in three ways:

1. **Cross-session noise.** `events.ndjson` is a global append-only file. Sessions A and B writing concurrently make the hash of A's anchor depend on B's writes — the anchor "drifts" with unrelated activity.
2. **Read-time race.** "Read once, hashed, recorded — read again at close to confirm no drift" assumed serialisation of writes; with parallel sessions this is unreliable.
3. **Demoted source of truth.** Per TRINITY_AUDIT_EVENT_SPEC_V1 §2.2, `events.ndjson` is now legacy/export-only. Hashing legacy file content as the cryptographic anchor of a COLD-tier production decision is incoherent.

Per-session `session_chain_head + last_seq` is invariant under sibling-session activity, is owned by the session's own AuditWriter, and reflects the v1 source of truth. The legacy ndjson hash is retained as `audit_export_ref` for backward-compatible tools only.

## §4 — Tier Routing

| Tier | Final Manifest | CAPTURE in manifest | External Audit |
|---|---|---|---|
| HOT | YES | YES | NO |
| WARM | YES | YES | NO |
| COLD | YES | YES | YES (required) |

**Tier resolution priority**:

1. **Sandbox profile** (bound at `vvv` per TRINITY_SANDBOX_CAPABILITY_SPEC_V1 §4.3) — if `sandbox.profile.tier` is set, use it.
2. **Verifier report** — if step verifier reports carry a `tier` field (TRINITY_VERIFIER_CONTRACT_V1 §5), use the strictest (`COLD > WARM > HOT`).
3. **plan_envelope.tier** — fallback if neither of the above is set.

This priority matters because the sandbox-bound tier is the strongest invariant; verifier reports reflect step-level risk; plan_envelope is the operator's pre-execution declaration.

## §5 — Audit Events Emitted

In addition to the existing `close.invoked` / `session.closed` / `close.completed` events, `close.py` MUST emit via per-session AuditWriter (TRINITY_AUDIT_EVENT_SPEC_V1 §2 — NOT direct ndjson write):

- `close.manifest_built` — payload `{path: <manifest path>, sha256: <manifest_sha256>, capture_count, last_seq}`
- `close.external_audit_emitted` — payload `{path: <external audit path>, sha256: <its hash>}` (COLD only)

If the external audit emission fails on a COLD session, `close.py` MUST raise `NEEDS_HUMAN` (Article XIII) rather than silently completing.

Each close event row obeys the 13-field shape from TRINITY_AUDIT_EVENT_SPEC_V1 §2, including `schema_version=trinity.audit_event.v1` and `seq` claimed under `BEGIN IMMEDIATE`. The legacy `.ai/audit/events.ndjson` MAY receive a mirrored 5-field row for backward compatibility (TRINITY_AUDIT_EVENT_SPEC_V1 §2.2 — legacy/export only).

## §6 — Cross-references

- **TRINITY_VERIFIER_CONTRACT_V1 (S5)** — `verifier_report.tier` and `verifier_report.capture_refs[]` drive §4 routing and §2.2 capture status check.
- **TRINITY_AUDIT_EVENT_SPEC_V1 (S1)** — `close.manifest_built`, `close.external_audit_emitted`, `session.closed` registered in §3 canonical list; 13-field shape per §2; per-session chain per §2.1; legacy ndjson per §2.2.
- **TRINITY_SANDBOX_CAPABILITY_SPEC_V1 (S3)** — `sandbox.profile.bound` is required in the session chain before close.
- **Addendum v1.0.1 §D** — controlling clause for the external-audit shape; §3 of this spec patches `audit_chain_anchor` to be RecordProxy-aligned while preserving the rest of §D.
- **DESIGN.md §22** — "No capture envelope = invalid ritual evidence." Drives §2.1.
- **DESIGN.md §6** — capture status model; drives §2.2.
- **DESIGN.md §14** — retention classes (HOT 30d / WARM 90d / COLD indefinite); orthogonal to close but referenced by `.ai/policies/trinity_policy.yaml capture_policy`.
- `feedback_close_requires_verify_dev_and_prod.md` (memory) — known UX bug; out of scope for this spec but ties to the same `close.py` runtime.

## §7 — Open Questions

- Where to store the long-term archive of `audit/external/<date>/` — operator decision; spec leaves location pluggable.
- WARM tier opt-in to External Audit (e.g. for legally-sensitive but non-COLD changes) — proposed `plan_envelope.external_audit: true` override; not in V1.
- Should `capture_chain_consistent: false` block close on HOT tier as well? Currently HOT proceeds with a warning; revisit in V2.
- Should `audit_export_ref` be required on COLD or stay optional? Currently optional (legacy tools only); revisit when legacy ndjson is retired.

## §8 — Out of Scope

- Editing `close.py` (deferred to a later gogogo).
- Modifying `.ai/cli/core/recordproxy/**` — immutable ground truth.
- Compressing / signing manifests (Phase 14 Root of Trust territory).
- `audit_chain_anchor` cross-verification tooling — covered by TRINITY_AUDIT_EVENT_SPEC_V1 §4–5 (`ai audit replay` / `verify-chain`).

---

**Authors:** Trinity Executor (operator direct-draft; RecordProxy alignment patch).
**RecordProxy v1 reference**: `.ai/cli/core/recordproxy/{capture_store.py,audit_writer.py}` @ commit `4a6fd80`; DESIGN.md §4, §6, §7, §22.
