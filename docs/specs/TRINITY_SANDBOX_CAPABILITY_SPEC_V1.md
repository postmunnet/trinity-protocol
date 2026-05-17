# TRINITY_SANDBOX_CAPABILITY_SPEC_V1

**Status:** DRAFT v2 (S3 of recordproxy alignment patch — pending verifier review + ddd)
**Phase:** 7 — Sandbox Capability
**Organ:** #7 (Sandbox)
**Constitutional rank:** 5 — Workflow Contract (per Article XXV)
**Anchor commit:** main @ 4a6fd80 (RecordProxy v1 foundation)
**Predecessor anchor:** 17e74fa (Constitution v1.0 + Ritual Constitution v1.1; superseded 2026-05-13)
**Date:** 2026-05-13

## §0 — Rank-5 Authority Disclaimer (Article XXV)

This document is a **Workflow Contract** under Article XXV of the Trinity Constitution v1.0. It ranks **fifth** in the constitutional priority order:

```
Constitution → Ritual Constitution → Canonical Policies → Kernel State Rules → Workflow Contracts → Tool Contracts → Runtime Requests → Model Suggestions
```

Any clause in this document that conflicts with a higher-ranked instrument (Constitution, Ritual Constitution, Canonical Policies, Kernel State Rules) is void in the conflict and the higher-ranked instrument governs. Amendments to this spec follow Article XXIX (explicit proposal + rationale + impact analysis + human approval + version bump + audit entry). This spec does **not** amend the constitution corpus and does **not** self-enforce — runtime enforcement is deferred per S1 scope.

## §1 — Purpose

Define the **capability model** for the Sandbox organ (#7) so that any Executor / Tool / Ritual that runs work inside a Trinity session can be constrained to a declared profile and **denied** at the kernel boundary when its requested actions exceed that profile.

Goals:

1. Express what an action *needs* (capabilities) and what a session *grants* (profile) in a single comparable shape.
2. Make denial **deterministic** — the kernel decides allow/deny without an LLM consult (Pyramid of Judgment layer 1).
3. Make the allowed surface **enumerable** — an operator can read a profile and know exactly what is permitted.
4. Stay **specification-only** in this phase — runtime hook drafting for `.ai/cli/core/sandbox.py` is deferred to a later gogogo.

Non-goals (this version):

- Implementing `.ai/cli/core/sandbox.py` runtime hook (deferred).
- Replacing `.ai/policies/safety.yaml` or `.ai/policies/forbidden_paths.yaml` — those remain authoritative until Phase 5 consolidation (Step S5) lands.
- Cryptographic attestation of profile assignment — that is Phase 14 (Genesis Trust deferral per audit verdict §3).

## §2 — Capability Axes

A sandbox **profile** is a finite set of capability declarations across the following axes. Each axis MUST be evaluable to allow / deny **without consulting an LLM**.

### §2.1 Filesystem axis

| Field | Type | Meaning |
|---|---|---|
| `fs.read_roots` | `string[]` | Repo-relative directory roots the actor MAY read. `[]` = no FS read. |
| `fs.write_roots` | `string[]` | Repo-relative directory roots the actor MAY write. `[]` = read-only. |
| `fs.delete_roots` | `string[]` | Repo-relative directory roots the actor MAY delete files in. `[]` = no FS delete (default). Subset of `fs.write_roots` enforced. |
| `fs.forbidden_paths` | `string[]` | Glob patterns the actor MUST NOT touch, **even if covered by a read/write/delete root**. Forbidden trumps allowed. |
| `fs.max_bytes_per_file` | `integer` | Reject writes larger than this; `0` = no per-file limit. |
| `fs.max_total_bytes` | `integer` | Reject the session if cumulative writes exceed; `0` = no total limit. |

### §2.2 Network axis

| Field | Type | Meaning |
|---|---|---|
| `net.outbound` | `enum("denied", "allowlist", "open")` | `denied` is the default for COLD-tier rituals. |
| `net.allowlist` | `string[]` | Required iff `net.outbound == "allowlist"`. Hostname patterns; no wildcards inside a single label. |
| `net.protocols` | `string[]` | E.g. `["https"]`. Other protocols denied. |

### §2.3 Process axis

| Field | Type | Meaning |
|---|---|---|
| `proc.allowed_binaries` | `string[]` | Whitelist of binaries the actor MAY exec (`python3`, `bash`, …). `[]` = no exec. |
| `proc.spawn_allowed` | `boolean` | If `false`, actor MUST NOT spawn detached/background subprocesses (only synchronous `exec`). Default `false`. Maps to Tool capability `proc.spawn`. |
| `proc.forbidden_binaries` | `string[]` | Hard-denied even if otherwise allowed. |
| `proc.max_wallclock_seconds` | `integer` | Reject any single command beyond this limit; `0` = no limit. |

### §2.4 Tool axis

A **tool** here is any contract under `.ai/tools.yaml` / `.ai/tools.capabilities.yaml` (Phase 6 — see Step S6). Each tool declares its required capabilities; the sandbox profile declares which tools it grants.

| Field | Type | Meaning |
|---|---|---|
| `tools.allowed` | `string[]` | Tool contract IDs the actor MAY invoke. `[]` = no tool invocation. |
| `tools.forbidden` | `string[]` | Tool contract IDs that are hard-denied. |

When Phase 6 ships, the kernel MUST compare `tools.allowed` to each tool's declared capability requirements (filesystem / network / process / authority subsets) and refuse to allow a tool whose declared needs exceed the granted profile. Cross-reference Step S6 deliverable `.ai/tools.capabilities.yaml`.

### §2.5 Authority axis

| Field | Type | Meaning |
|---|---|---|
| `authority.may_promote` | `boolean` | If `false`, actor MUST NOT issue a ddd-promote (Article XIII). Default `false`. |
| `authority.may_deploy` | `boolean` | If `false`, actor MUST NOT trigger deploy (Article XIII). Default `false`. |
| `authority.may_modify_policies` | `boolean` | If `false`, actor MUST NOT write to `.ai/policies/**`. Per Article III this is `false` for **all** AI actors; only a human-decided gate may flip it. Default `false`. |
| `authority.ddd_propose_allowed` | `boolean` | If `false`, actor MUST NOT emit a `ddd.packet_emitted` event. Default `false`. Maps to Tool capability `ddd.propose`. Note: `ddd.decide` is human-only and not representable as a sandbox grant. |

### §2.6 Audit / Policy read axes

| Field | Type | Meaning |
|---|---|---|
| `audit.read_allowed` | `boolean` | If `true`, actor MAY read `.ai/audit/events.ndjson` and per-session `<session>/CAPTURE/capture.sqlite` audit_events table. Default `false`. Maps to Tool capability `audit.read`. Writes are kernel-only (`audit.append` is never tool-granted; see Tool Capability Model §2.1). |
| `policy.read_allowed` | `boolean` | If `true`, actor MAY read `.ai/policies/**`. Default `false`. Maps to Tool capability `policy.read`. Writes to `.ai/policies/**` are governed by `authority.may_modify_policies` (Article III). |

## §3 — Denial Semantics

Denial is **deterministic** and follows this priority order:

1. **Forbidden trumps allowed.** If a path matches any `fs.forbidden_paths` glob, the action is denied even if otherwise covered by `fs.write_roots`. Same rule for `proc.forbidden_binaries` and `tools.forbidden`.
2. **Allowlist must be explicit.** If an action references a resource not listed in the corresponding allow surface, it is denied (no default-allow).
3. **Authority is closed by default.** Any `authority.*` boolean defaulting to `false` MUST be explicitly `true` in the profile to grant the corresponding power. Implicit grants are forbidden.
4. **Quota overflow is a denial.** Hitting `fs.max_bytes_per_file`, `fs.max_total_bytes`, or `proc.max_wallclock_seconds` results in a hard denial.
5. **Unknown axis fields are a denial.** Per the schema, `additionalProperties: false` — an unrecognized profile field rejects the profile at validation time, not at action time.

The kernel MUST emit a single `sandbox.deny` event per denial with shape `{ profile_id, axis, resource, reason, capture_id (optional) }` via the **per-session AuditWriter** (TRINITY_AUDIT_EVENT_SPEC_V1 §2 — 13-field shape; per-session SQLite at `<session>/CAPTURE/capture.sqlite` audit_events table; NOT direct write to legacy `.ai/audit/events.ndjson`). The kernel MUST NOT consult an LLM to decide allow/deny (Article XX — Passive Core; deterministic decisions stay at Pyramid layer 1).

### §3.1 ORPHANED_INVOCATION integration

Per RecordProxy v1 (DESIGN.md §10), any kernel-mediated mutation MUST be wrapped in a `RecordProxy.capture()` transaction so that the audit row carries a non-null `capture_id`. If a write/exec/tool-invocation completes outside a capture transaction (no `capture_id` on the audit row, or no matching `captures.capture_id` row), the verifier treats it as `ORPHANED_INVOCATION` and routes per tier (TRINITY_VERIFIER_CONTRACT_V1 §2.1):

- HOT → `RETRY` with degraded warning
- WARM → `NEEDS_HUMAN`
- COLD → `DEAD` / `TERMINAL_FAILED`

Sandbox profile bindings therefore MUST require that every mutation path runs under a capture transaction; profiles MAY surface this as an axis assertion (`fs.write_requires_capture: true` etc.) but the default invariant is enforced at the verifier level.

## §4 — Profile Lifecycle

1. **Declaration.** A session declares its sandbox profile at `sss` time via `plan_envelope.sandbox_profile` (referencing a profile ID; the profile body lives at `.ai/sandbox/profiles/<id>.yaml` once Phase 7 runtime ships).
2. **Validation.** The kernel validates the declared profile against `.ai/schemas/sandbox_profile.schema.json` (runtime validator deferred to gogogo).
3. **Binding.** The profile is bound at `vvv` and frozen for the session. The kernel MUST emit `sandbox.profile.bound` via per-session AuditWriter (TRINITY_AUDIT_EVENT_SPEC_V1 §3 registry) with payload `{ profile_id, tier, capability_grants }`. Mid-session mutation requires a `plan.amended` event + new audit record (per the amend-don't-fork pattern recorded in memory).
4. **Enforcement.** Every kernel-mediated action (write, exec, tool invocation) MUST be evaluated against the bound profile before execution.
5. **Close.** On `close`, the session's per-session audit chain (NOT the legacy global ndjson) MUST contain at least one `sandbox.profile.bound` event; absence is a verifier failure under TRINITY_VERIFIER_CONTRACT_V1 §4 rule `sandbox_profile_missing`. The bound profile's tier feeds TRINITY_SESSION_CLOSE_SPEC_V1 §4 tier-routing.

## §5 — Schema

The companion schema lives at `.ai/schemas/sandbox_profile.schema.json` and is pinned to **JSON Schema draft-07**. It is the authoritative shape; this prose is descriptive.

Required top-level fields: `id`, `version`, `fs`, `net`, `proc`, `tools`, `authority`. Unknown fields are rejected (`additionalProperties: false`) at every level.

## §6 — Cross-references

- **TRINITY_VERIFIER_CONTRACT_V1** — sandbox denial events feed verifier reports and must be tier-tagged HOT/WARM/COLD; ORPHANED_INVOCATION × tier verdict mapping in §2.1 of that spec governs §3.1 of this spec.
- **TRINITY_TOOL_CAPABILITY_MODEL_V1 §2.1** — explicit 1:1 mapping table between Tool `required_capabilities` vocabulary and the axes in §2 above. Rule: `requirement ⊆ grant` enforced by kernel comparator (Tool spec §4).
- **TRINITY_AUDIT_EVENT_SPEC_V1 §3** — `sandbox.deny` / `sandbox.profile.bound` registered in canonical event registry; §2 13-field shape applies; per-session AuditWriter is the write target (NOT legacy ndjson).
- **TRINITY_SESSION_CLOSE_SPEC_V1 §4** — sandbox-profile-bound tier is the highest-priority tier source for close-time routing.
- **trinity_policy.yaml `capture_policy`** (proposed; TRINITY_TRINITY_POLICY §capture_policy) — retention-class HOT/WARM/COLD and orphaned_invocation routing.
- **.ai/policies/forbidden_paths.yaml** — `fs.forbidden_paths` overlaps with this file; future policy consolidation must preserve the forbidden-trumps-allowed precedence.

## §7 — Open Questions (resolved at ddd / out-of-band)

- Tiering (HOT/WARM/COLD) of stock profiles — pending Phase 8 verifier tier-tag work (Step S2).
- Cross-reference IDs between sandbox profiles and policy gates (`.ai/policies/gates.yaml`) — pending Phase 5 consolidation (Step S5).
- Cryptographic profile-assignment attestation — deferred to Phase 14 under Genesis Trust.
- Stock profile catalog (`readonly`, `spec_author`, `ritual_executor`, `verifier`, …) — drafted in a follow-up after S1+S6 land, since stock profiles must reference real tool capability IDs.

## §8 — Out of Scope

- Runtime enforcement code (`.ai/cli/core/sandbox.py`) — deferred to a subsequent gogogo.
- Constitutional amendments — this document is rank 5; amendments would require an Article XXIX addendum.
- Tool capability declarations — drafted separately under Step S6 (Phase 6 Tool Capability Registry).
- Telegram / transport-side gating — Article XV (Transport is not Authority); transports MUST NOT decide sandbox.

---

**Authors:** Trinity Executor (proposal); pending Verifier + Human review per Articles III, XIII.
**Verifier:** to be evaluated under `.ai/policies/verifier-rules.yaml` at the S8 sweep step.
**Audit anchor:** introduction of this document to the repo is logged on apply as `spec.created` in `.ai/audit/events.ndjson`.
