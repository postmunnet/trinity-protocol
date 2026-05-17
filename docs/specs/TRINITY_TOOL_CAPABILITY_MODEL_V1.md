# TRINITY_TOOL_CAPABILITY_MODEL_V1

**Status:** DRAFT v2 (S4 of recordproxy alignment patch — pending verifier review + ddd)
**Phase:** 6 — Tool Capability Registry
**Organ:** #15 (Tool Capability Registry)
**Constitutional rank:** 5 — Workflow Contract (per Article XXV)
**Anchor commit:** main @ 4a6fd80 (RecordProxy v1 foundation)
**Predecessor anchor:** 17e74fa (pre-RecordProxy; superseded 2026-05-13)
**Date:** 2026-05-13

## §0 — Rank-5 Authority Disclaimer (Article XXV)

Workflow Contract. Void where it conflicts with higher-ranked instruments. Amendments via Article XXIX. This spec defines the **capability** axis for tool plugins; the existing `.ai/tools.yaml` remains the authoritative tool registry until consolidation lands.

## §1 — Purpose

The kernel today reads `.ai/tools.yaml` to discover sibling tool plugins. Each tool declares a high-level `capabilities:` tag list (e.g. `[browser, navigation, dom]`). What's missing:

- A **required-capabilities** declaration mappable to sandbox profile axes (Step S1).
- A **deny-by-default** posture: if a sandbox profile does not explicitly grant the required capability, the kernel MUST deny invocation.

This spec defines the unified capability vocabulary, the per-tool declaration shape, and the kernel's compatibility check.

## §2 — Capability Vocabulary

Capabilities are short identifiers in a closed namespace:

| Family | Identifiers | Notes |
|---|---|---|
| `fs.*` | `fs.read`, `fs.write`, `fs.delete` | maps to sandbox `fs.*` axis |
| `net.*` | `net.outbound`, `net.allowlist` | maps to sandbox `net.*` axis |
| `proc.*` | `proc.exec`, `proc.spawn` | maps to sandbox `proc.*` axis |
| `audit.*` | `audit.read`, `audit.append` | append is kernel-only; tools never get this |
| `policy.*` | `policy.read` | tools may read policies; writing is forbidden by Article III |
| `ddd.*` | `ddd.propose`, `ddd.decide` | `ddd.decide` is human-only; tools may only propose |
| `tool.*` | `tool.invoke` | invoking another tool transitively |

Per-tool capability requirements are **declared**; the kernel intersects requirement ↔ grant and denies on shortfall.

### §2.1 Capability ↔ Sandbox Axis Mapping (1:1, authoritative)

This table is the kernel's compatibility check rule. Each tool capability identifier maps to a single sandbox profile axis assertion. A tool may be invoked iff every entry in its `required_capabilities` is satisfied by the bound sandbox profile.

| Tool capability | Sandbox profile assertion | Notes |
|---|---|---|
| `fs.read` | `fs.read_roots != []` AND `path ⊆ fs.read_roots \ fs.forbidden_paths` | per-path check at action time |
| `fs.write` | `fs.write_roots != []` AND `path ⊆ fs.write_roots \ fs.forbidden_paths` | per-path; also subject to `fs.max_bytes_per_file` / `fs.max_total_bytes` quotas |
| `fs.delete` | `fs.delete_roots != []` AND `path ⊆ fs.delete_roots \ fs.forbidden_paths` | new axis added in Sandbox v2 (§2.1); enforced as strict subset of `fs.write_roots` |
| `net.outbound` | `net.outbound != "denied"` | when `"allowlist"`, the requested host MUST be in `net.allowlist` and protocol in `net.protocols` |
| `net.allowlist` | `net.outbound == "allowlist"` AND `net.allowlist != []` | declares the tool relies on the allowlist mode, not `"open"` |
| `proc.exec` | `proc.allowed_binaries != []` AND `binary ∈ proc.allowed_binaries \ proc.forbidden_binaries` | subject to `proc.max_wallclock_seconds` |
| `proc.spawn` | `proc.spawn_allowed == true` AND `proc.exec` also satisfied | new axis added in Sandbox v2 (§2.3); for detached/background subprocesses |
| `audit.read` | `audit.read_allowed == true` | new axis added in Sandbox v2 (§2.6); read-only access to legacy ndjson and per-session SQLite audit_events |
| `audit.append` | **NEVER granted** (kernel-only) | reserved invariant: only kernel `AuditWriter` may append; per DESIGN.md §7 "Only AuditWriter may claim seq" |
| `policy.read` | `policy.read_allowed == true` | new axis added in Sandbox v2 (§2.6); read-only access to `.ai/policies/**` |
| `ddd.propose` | `authority.ddd_propose_allowed == true` | new axis added in Sandbox v2 (§2.5); allows emitting `ddd.packet_emitted` events |
| `ddd.decide` | **NEVER granted** (human-only) | reserved invariant per Article XIII (Human Authority); only `decided_by: human` envelopes carry this authority |
| `tool.invoke` | `tools.allowed` contains tool name AND tool name ∉ `tools.forbidden` | per-tool name check; transitively re-verifies the called tool's own `required_capabilities` |

### §2.2 Comparison rule (authoritative)

```
Tool capabilities are REQUIREMENTS.
Sandbox profile is the GRANT.
Kernel comparator decides: requirement ⊆ grant.
```

- If any `required_capability` lacks a satisfying sandbox assertion → DENY (no default-allow).
- If a capability is in the "NEVER granted" rows above (`audit.append`, `ddd.decide`) → DENY unconditionally; profiles MUST NOT grant these.
- `optional_capabilities` are not checked at this gate; they may be granted or absent without blocking invocation.
- Per-action capability scope (e.g. specific path within `fs.read_roots`) is re-checked at action time, not just at invocation gate.

## §3 — Per-Tool Declaration

The sibling registry file `.ai/tools.capabilities.yaml` carries one entry per tool name (matching `.ai/tools.yaml.tools[].name`):

```yaml
- name: browser-cli
  required_capabilities:
    - net.outbound
    - net.allowlist
    - fs.read
  optional_capabilities:
    - fs.write   # only when --screenshot-to-disk is used
  default_tier_requirement: WARM
  notes: "Browser organ; outbound HTTP/HTTPS; sandbox host allowlist required."
```

Fields:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | matches `.ai/tools.yaml.tools[].name` |
| `required_capabilities` | string[] | MUST be granted by sandbox profile to invoke |
| `optional_capabilities` | string[] | MAY be granted; absence does not block invocation |
| `default_tier_requirement` | enum(HOT/WARM/COLD) | lowest tier that may grant required_capabilities |
| `notes` | string | free-text rationale |

## §4 — Kernel Compatibility Check

Before invoking a tool, the kernel MUST (in order):

1. Look up the tool in `.ai/tools.capabilities.yaml`. If absent → DENY (unknown authority is denied per Article XVI).
2. Confirm session's sandbox profile `tools.allowed` includes the tool's `name` and `name ∉ tools.forbidden`.
3. Apply the §2.1 mapping table: for every entry in `required_capabilities`, confirm the corresponding sandbox assertion is satisfied. **Rule: `requirement ⊆ grant`** (§2.2). If any required capability lacks its assertion → DENY.
4. Confirm `audit.append` and `ddd.decide` are NOT in `required_capabilities` (kernel-only / human-only invariants per §2.1).
5. Confirm session tier ≥ `default_tier_requirement`. Tier ordering: HOT < WARM < COLD. Tier is resolved per TRINITY_SESSION_CLOSE_SPEC_V1 §4 priority (sandbox profile > verifier report > plan_envelope).
6. Confirm the invocation is wrapped in a `RecordProxy.capture()` transaction (carrying a valid `capture_id`). If not → emit `tool.invocation_denied` with `reason: ORPHANED_INVOCATION` (see §4.5).

Any check failure emits `tool.invocation_denied` via the **per-session AuditWriter** (TRINITY_AUDIT_EVENT_SPEC_V1 §2 — 13-field shape; per-session SQLite at `<session>/CAPTURE/capture.sqlite` audit_events table; NOT direct write to legacy `.ai/audit/events.ndjson`) and aborts the invocation. The denial event payload carries `{ tool_name, missing_capabilities, reason, capture_id (optional) }`.

### §4.5 ORPHANED_INVOCATION integration

Per RecordProxy v1 (DESIGN.md §10), a tool invocation that occurs **outside** a `RecordProxy.capture()` transaction is an `ORPHANED_INVOCATION`. The verifier verdict mapping (TRINITY_VERIFIER_CONTRACT_V1 §2.1) routes per tier:

- HOT → `RETRY` with degraded warning, capture-id back-filled via reconciliation (`status=RECONCILED`)
- WARM → `NEEDS_HUMAN` (Article XIII)
- COLD → `DEAD` / `TERMINAL_FAILED` — invocation refused, session may not proceed

Tools MUST be invoked via the kernel's capture-wrapping path (e.g. `trinity-agent-run` per DESIGN.md §20). Bare subprocess spawns or out-of-band tool calls fail this check.

## §5 — Cross-references

- **TRINITY_SANDBOX_CAPABILITY_SPEC_V1 §2.1–§2.6** — the grant side of the §2.1 mapping table; new axes `fs.delete_roots`, `proc.spawn_allowed`, `audit.read_allowed`, `policy.read_allowed`, `authority.ddd_propose_allowed` added there to support this mapping.
- **TRINITY_VERIFIER_CONTRACT_V1 §2.1** — `tool.invocation_denied` and `ORPHANED_INVOCATION` are inputs to the `dead_when` / `needs_human_when` predicates per tier; `capture_refs` field links denials back to per-session captures.
- **TRINITY_AUDIT_EVENT_SPEC_V1 §3** — `tool.invocation_*` and `tool.invocation.*` (RecordProxy alias) registered in canonical event registry; §3.1 legacy-aliases table applies.
- **TRINITY_SESSION_CLOSE_SPEC_V1 §4** — tier resolution priority used by §4 step 5 above.
- **`.ai/tools.yaml`** — existing registry; `name` field must match.
- **DESIGN.md §10** — ORPHANED_INVOCATION definition; drives §4.5.
- **DESIGN.md §20** — `trinity-agent-run` wrapper as the canonical capture-wrapping invocation path.

## §6 — Open Questions

- Should `optional_capabilities` carry a `gated_by:` clause naming the operator flag? Proposed: defer to V2.
- Tool versioning vs capability declarations — if `browser-cli` v2 needs more capabilities than v1, do we version the capability file? Proposed: yes, file gains a per-entry `contract_version` field; not added in V1 to keep the proposal small.

## §7 — Out of Scope

- Runtime check at `.ai/cli/core/tools_registry.py` — already exists; this spec describes the shape but does not edit it.
- Per-action capability scopes (finer-grained than per-tool) — V2 territory.
- Phase 14 cryptographic capability attestation.

---

**Authors:** Trinity Executor (operator direct-draft).
