# TRINITY_AUDIT_EVENT_SPEC_V1

**Status:** DRAFT v2 (S1 of recordproxy alignment patch + 2026-05-15 transport namespace addition per Article XXIX OPERATIONAL — pending verifier review + ddd)
**Phase:** 10 — Audit Replay / Verify-chain
**Organ:** (cross-cutting; Audit is Article X)
**Constitutional rank:** 5 — Workflow Contract (per Article XXV)
**Anchor commit:** main @ 4a6fd80 (RecordProxy v1 foundation)
**Predecessor anchor:** 17e74fa (pre-RecordProxy; superseded 2026-05-13)
**Date:** 2026-05-13

## §0 — Rank-5 Authority Disclaimer (Article XXV)

Workflow Contract. Void where it conflicts with higher-ranked instruments. Amendments via Article XXIX. This spec describes the **per-session audit chain shape**, the **event-type registry**, and the **replay/verify-chain subcommand design**. RecordProxy v1 at `.ai/cli/core/recordproxy/**` is the **immutable ground truth** for the event shape; this spec describes it for downstream consumers (Close, DDD, Verifier, Sandbox, Tool, Retro). The legacy `.ai/schemas/events.schema.json` is preserved as a compatibility shape for the global `.ai/audit/events.ndjson` export only (see §2.3).

## §1 — Purpose

RecordProxy v1 (committed `4a6fd80`, 2026-05-13) establishes **per-session SQLite audit chains** as the authoritative evidence layer (DESIGN.md §7). Each session owns one `<session>/CAPTURE/capture.sqlite` with an `audit_events` table; events are appended by `AuditWriter` under `BEGIN IMMEDIATE` (audit_writer.py:57). The global file `.ai/audit/events.ndjson` survives as a legacy/export compatibility surface — it is no longer the v1 source of truth.

This spec:

1. Pins the **per-session event shape** that AuditWriter writes (13 fields; §2).
2. Pins the **canonical event-type registry** unifying the kernel namespace (sss/vvv/nnn/gogogo/ddd/rrr/close, verify.*, graph.*) with the RecordProxy namespace from DESIGN.md §17 (ritual.*, capture.*, tool.*, sandbox.*, state.*, policy.*, break_glass.*); §3.
3. Specifies `ai audit replay` — re-emit chain events forward to a target state for debugging (§4).
4. Specifies `ai audit verify-chain` — cryptographically validate the per-session hash chain (§5).

## §2 — Event Shape (Authoritative — RecordProxy v1)

The canonical event row written by `AuditWriter.append()` and persisted in the per-session SQLite `audit_events` table has the following 13 fields (audit_writer.py:71-86; capture_store.py:56-71):

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | string | yes | const `"trinity.audit_event.v1"` (DESIGN.md §16 invariant: "No schema_version = invalid system artifact") |
| `event_id` | string | yes | `evt_<uuid4-hex>` |
| `session_id` | string | yes | the owning session ID |
| `seq` | integer | yes | monotonic per-session sequence; claimed under `BEGIN IMMEDIATE`; `UNIQUE(session_id, seq)` |
| `event_type` | string | yes | canonical name from §3 registry (closed namespace) |
| `ritual` | string\|null | optional | originating ritual (`sss`/`vvv`/`nnn`/`gogogo`/`ddd`/`rrr`/`close`) |
| `capture_id` | string\|null | optional | ULID linking back to a `captures` row when the event was produced inside a capture transaction |
| `actor` | string | yes | `kernel`/`agent:<name>`/`tool:<name>`/`human` |
| `ts_utc` | string | yes | RFC3339 UTC timestamp |
| `payload_json` | string | yes | canonicalised JSON body (sort_keys, separators `(",",":")`) |
| `payload_hash` | string | yes | `sha256(payload_json)` |
| `prev_hash` | string | yes | previous event's `hash`; genesis = `"0"` |
| `hash` | string | yes | `sha256(canonical_json(event_for_hash))` — see §2.1 |

### §2.1 Hash Chain Rule (per-session)

```
event_for_hash = {
  event_id, schema_version, session_id, seq, event_type, ritual,
  capture_id, actor, ts_utc, payload_hash, prev_hash
}
hash = sha256(canonical_json(event_for_hash))
canonical_json: sort_keys=True, separators=(",", ":")
```

Note: `payload_json` is **not** included in `event_for_hash` directly; `payload_hash` represents it. This matches audit_writer.py:71-86.

For session `S`, the chain root is `prev_hash = "0"` at `seq = 1`. Every subsequent event has `prev_hash = previous.hash` and `seq = previous.seq + 1`. Gap detection: `(seq, prev_hash, hash recompute)` must all line up (DESIGN.md §7 line 312-320).

### §2.2 Legacy / Export Compatibility

`.ai/audit/events.ndjson` (existing global file) remains writable by the kernel for backward-compatible export and out-of-band tooling. Its on-disk shape is the legacy `.ai/schemas/events.schema.json` 5-field row (`timestamp`, `type`, `prev_hash`, `details`, `hash`). Properties:

- **Not the v1 source of truth.** New code MUST read per-session SQLite first.
- **Append-only legacy export.** Kernel may continue writing here for tools that haven't migrated.
- **Field mapping**: `timestamp ↔ ts_utc`, `type ↔ event_type`, `details ↔ payload_json` (lossy: `details` typed as `object`; payload_json is canonicalised string).
- **Hash chain**: the legacy file maintains its own SHA-256 chain over its 5-field rows; this is **not** the per-session AuditWriter chain.

Once every downstream consumer (Close, DDD, Verifier, Sandbox, Tool, Retro, sibling CLIs) is on AuditWriter, the legacy file may be retired in a future Addendum. Until then it coexists.

### §2.3 SQLite Table Definition (informational)

Per capture_store.py:56-71:

```sql
CREATE TABLE audit_events (
  event_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL,
  session_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  ritual TEXT,
  capture_id TEXT,
  actor TEXT NOT NULL,
  ts_utc TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  prev_hash TEXT,
  hash TEXT NOT NULL,
  UNIQUE(session_id, seq)
);
```

This DDL is owned by RecordProxy v1 (immutable per Article XXIX + this session's forbidden_paths); changes require a separate Addendum.

## §3 — Event Type Registry (Canonical, Unified)

Closed namespace, grouped by emitter. This registry unifies the kernel namespace (sss/vvv/nnn/gogogo/ddd/rrr/close, verify.*, graph.*) with RecordProxy v1's invocation/capture namespace (DESIGN.md §17). Adding a type requires an Addendum (Article XXIX); the audit-replay subcommand SHOULD warn on any `event_type` outside this set.

### Chain root
- `genesis` — chain root; emitted at first AuditWriter.append() per session (`prev_hash = "0"`, `seq = 1`)

### Session lifecycle
- `session.created` — `ai session new`
- `session.closed` — `ai close run`
- `session.abandoned` — `ai close run --force` on incomplete work

### Operator (RecordProxy §17)
- `operator.input.captured` — operator input recorded as evidence
- `operator.approval.recorded` — operator approval signal
- `operator.rejection.recorded` — operator rejection signal
- `operator.amendment.recorded` — operator amendment signal

### Ritual gates (kernel)
- `vvv.proposed` — `ai vvv` invoked (questions presented)
- `vvv.passed` — answers landed; vvv_pass marker created
- `nnn.proposed` — plan envelope submitted
- `nnn.passed` — plan accepted; nnn_pass marker created
- `gogogo.step_started` — per step
- `gogogo.step_completed` — per step (carries verifier verdict)
- `gogogo.completed` — all steps finished
- `gogogo.hmac_rejected` — exit 79 per Spec 14 §6.1
- `ddd.packet_emitted` — decision packet drafted
- `ddd.approved` / `ddd.rejected` / `ddd.held` / `ddd.timeout` — operator decisions
- `rrr.proposed` — retro drafted
- `rrr.completed` — retro accepted; DONE state

### Ritual mechanics (RecordProxy §17)
- `ritual.started` — ritual execution begins
- `ritual.contract.loaded` — ritual pack contract resolved
- `ritual.context.built` — kernel self-capture event (kernel.py context.built hook)
- `ritual.agent.invocation.started` — agent invocation wrapped in capture transaction
- `ritual.agent.invocation.completed` — agent invocation finished with valid capture
- `ritual.agent.invocation.failed` — agent invocation errored before finalize
- `ritual.agent.invocation.timeout` — agent invocation hit wallclock limit
- `ritual.validation.started` — ritual gate validation begins
- `ritual.validation.completed` — ritual gate validation finished
- `ritual.transition.requested` — transition proposed
- `ritual.transition.completed` — transition accepted
- `ritual.transition.blocked` — transition denied

### Verifier
- `verify.invoked` — gate check started
- `verify.completed` — gate check finished (carries `verifier_report.json` reference + `capture_refs`)

### Graph
- `graph.transition` — `READY → THINK → SANDBOX → DO → VERIFIED → PROMOTED → DEPLOYED → DONE`

### Close
- `close.invoked` — `ai close run` started
- `close.manifest_built` — final manifest hashed (cf. TRINITY_SESSION_CLOSE_SPEC_V1 §2)
- `close.external_audit_emitted` — Addendum v1.0.1 §D record written (COLD only)
- `close.completed` — archive done

### Sandbox
- `sandbox.profile.bound` — profile resolved at vvv
- `sandbox.deny` — action denied at the kernel boundary

### Transport (Spec 9 — TRINITY_TRANSPORT_BOUNDARY_SPEC_V1 §5.1 + §6.5)
- `transport.envelope_accepted` — kernel-side envelope passed all 7 verification steps; payload includes `{envelope_id, source_transport, claimed_actor, key_id, payload_kind}`
- `transport.envelope_refused.unsigned` — required HMAC field absent on a mutating envelope, or schema violation (Section 5.3)
- `transport.envelope_refused.badkey` — `key_id` unknown, signature mismatch, or `hmac_alg` not pinned (Section 5.4)
- `transport.envelope_refused.replay` — `envelope_id` already seen in issuer's replay window, or `expires_ts` in the past (Section 5.5)
- `transport.envelope_refused.overscope` — `claimed_actor.class` not allowed by issuing Authority organ for this `key_id` (Section 5.6)

### Tool
- `tool.invocation_proposed`
- `tool.invocation_denied`
- `tool.invocation.started` (RecordProxy §17 alias of `tool.invocation_proposed` for capture-wrapped invocations)
- `tool.invocation.completed`
- `tool.invocation.failed`
- `tool.invocation.timeout`

### Capture (RecordProxy §17)
- `capture.started` — `RecordProxy.capture()` context entered
- `capture.completed` — capture finalised (`status = COMPLETED`)
- `capture.failed_partial` — capture aborted mid-transaction (`status = FAILED_PARTIAL`)
- `capture.reconciled` — orphan reconciled into a retroactive capture (`status = RECONCILED`)

### State / Policy / Break-glass (RecordProxy §17)
- `state.changed` — observable state mutation outside a ritual transition
- `policy.violation.detected` — verifier-rules predicate fired
- `break_glass.invoked` — `TRINITY_RECORDPROXY_RAW=1` or similar emergency override invoked (always escalates to NEEDS_HUMAN)

### Plan
- `plan.amended` — mid-session plan envelope mutation (per memory `feedback_plan_amendment_vs_subsession`)

### Memory
- `memory.write` — append to audit-anchored memory store
- `memory.promote` — memory_promote rule set verdict

### LLM (sibling siblings only; D8/D13 — kernel does not emit these)
- `llm.invoked` — `llm_call.py` foundation invocation from a sibling CLI
- `llm.completed` — response received

### §3.1 Legacy aliases

The following kernel-era names predate RecordProxy v1 and are accepted by readers as aliases. Writers SHOULD emit the canonical name above; readers MUST accept either:

| Legacy alias | Canonical (RecordProxy v1) |
|---|---|
| `tool.invocation_completed` | `tool.invocation.completed` |
| `tool.invocation_failed` | `tool.invocation.failed` |
| `verify.completed` | `ritual.validation.completed` *(both retained; verify.* is the kernel-Verifier name; ritual.validation.* is the RecordProxy-mechanics name; they MAY co-occur)* |

Adding a new alias requires an Addendum.

## §4 — `ai audit replay`

```
ai audit replay --session <sid> [--from <seq|hash>] [--to <seq|hash>]
                                [--event-type <type>] [--dry-run]
```

- Reads per-session SQLite at `<session>/CAPTURE/capture.sqlite`, table `audit_events`, ordered by `seq ASC` (audit_writer.py:122-134).
- Validates each row against the §2 13-field shape.
- Validates `event_type` against the §3 registry (legacy aliases per §3.1 accepted).
- Recomputes `hash` from `event_for_hash` (§2.1) and confirms `prev_hash` chain integrity.
- `--dry-run` (default): print events; do not mutate state.
- Without `--dry-run`: re-emit events to a target state file (for debugging, not for production replay).

Legacy export mode: `--legacy-ndjson <path>` walks `.ai/audit/events.ndjson` instead, using the §2.2 5-field shape. Exit codes are the same.

Exits:
- `0` — chain valid
- `1` — schema violation or unknown event_type
- `2` — hash chain broken (gap in `seq`, `prev_hash` mismatch, or hash recompute fails)

## §5 — `ai audit verify-chain`

```
ai audit verify-chain --session <sid> [--strict] [--from <seq|hash>]
ai audit verify-chain --legacy-ndjson [--strict] [--from <ts|hash>]
```

- Per-session mode (default): validates `prev_hash` linkage + SHA-256 recomputation across the per-session SQLite chain (audit_writer.py:136-167 is the reference implementation).
- Legacy-ndjson mode: same validation over the 5-field global file.
- `--strict`: additionally validates `event_type ∈ §3 registry` (legacy aliases accepted).
- Always read-only; never modifies the chain (Article XX — Passive Core).

Exits:
- `0` — chain valid
- `2` — chain broken (first broken link reported: `seq=N event_id=… reason=…`)

## §6 — Cross-references

- **TRINITY_SANDBOX_CAPABILITY_SPEC_V1 (S3)** — `sandbox.profile.bound`, `sandbox.deny` are emitted via per-session AuditWriter (not direct ndjson write).
- **TRINITY_VERIFIER_CONTRACT_V1 (S5)** — `verify.completed` carries `capture_refs[]` (link to per-session captures table); event row obeys §2 shape.
- **TRINITY_DDD_HUMAN_GATE_SPEC_V1 (S6)** — DDD events (`ddd.*`) registered here; emitted via AuditWriter; the `payload_json` carries the decision_packet/approval/rejection/hold envelope.
- **TRINITY_SESSION_CLOSE_SPEC_V1 (S2)** — close events (`close.manifest_built`, `close.external_audit_emitted`); the close-time `audit_chain_anchor` uses `session_chain_head + last_seq` rather than a hash over the legacy ndjson.
- **TRINITY_TOOL_CAPABILITY_MODEL_V1 (S4)** — tool events (`tool.invocation_*` + `tool.invocation.*`); §3.1 legacy aliases apply.
- **DESIGN.md §17** — RecordProxy v1 event-type taxonomy; merged into §3 above.
- **DESIGN.md §7** — `BEGIN IMMEDIATE` semantics for `seq` claim.
- **DESIGN.md §16** — `schema_version` invariant.
- **DESIGN.md §22** — "Audit captures the system."

## §7 — Open Questions

- Should `ai audit verify-chain` cache the last verified hash (per session) to avoid full re-scan on long chains? Proposed: yes, in `<session>/CAPTURE/.last_verified_hash`; not in V1.
- Multi-chain segmentation (per-session sub-chains anchored to a global root) — out of scope under Genesis Trust (Addendum v1.0.1 §A); revisit in Phase 14 Root of Trust.
- When the legacy ndjson is retired (post-migration), what is the deprecation signal? Proposed: `legacy_export_enabled: false` in `trinity_policy.yaml` flips kernel writers off; not in V1.

## §8 — Out of Scope

- Implementing the subcommands (`.ai/cli/commands/audit.py`) — deferred to a later gogogo. This session is spec-only.
- Modifying `events.schema.json` — preserved as legacy 5-field shape (§2.2).
- Modifying `.ai/cli/core/recordproxy/**` — RecordProxy v1 is ratified ground truth (Article XXIX would govern any future change).
- Phase 14 cryptographic anchoring beyond SHA-256 chain — Root of Trust spec is a separate Addendum.

---

**Authors:** Trinity Executor (operator direct-draft; RecordProxy alignment patch).
**RecordProxy v1 reference**: `.ai/cli/core/recordproxy/{audit_writer.py,capture_store.py,schemas.py}` @ commit `4a6fd80`.
