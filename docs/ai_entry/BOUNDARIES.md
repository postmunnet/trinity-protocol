---
title: "Boundaries — What AI Can and Cannot Do"
status: locked
last-updated: 2026-05-12
authority: "Trinity Constitution v1.0 (root CONSTITUTION.md) + Trinity Decision #1. Non-negotiable."
---

# Boundaries — What AI Can and Cannot Do

> ถ้า doubt — ถาม. NEEDS_HUMAN > confident wrong answer.

## Constitutional Authority

This document operationalises Trinity Constitution v1.0 — canonical at [`docs/constitution/TRINITY_CONSTITUTION_V1.md`](../constitution/TRINITY_CONSTITUTION_V1.md), with the root [`CONSTITUTION.md`](../../CONSTITUTION.md) as a short pointer. When the table in this file disagrees with the Constitution, the Constitution wins (Article XXV — Constitutional Priority Order). The full canonical home is [`docs/constitution/`](../constitution/INDEX.md).

Related canonical specs (Phase 0 corpus, relocated 2026-05-13 per Addendum v1.0.2):

- [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md`](../constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md) — Genesis Trust, Decision Velocity Tiers, Break-Glass, External Audit, Cognitive Presentation
- [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md`](../constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md) — Canonical-Home Relocation + three-tier internal structure
- [`docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md`](../constitution/contracts/TRINITY_ORGAN_MAP_V1.md) — 18 organs with charter
- [`docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md`](../constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md) — sss/vvv/nnn/gogogo/ddd/rrr/close as thin gates

The articles that govern this file directly:

- **Article III — AI Cannot Govern Itself.** AI may think, reason, propose, and act through authorized tools. AI MUST NOT declare final completion, approve its own work, bypass verifier approval, or rewrite policy.
- **Article IV — Separation of Responsibilities.** Kernel, Planner, Executor, Verifier, Memory, Audit, Retro, and Transport are distinct roles. No silent role collapse.
- **Article V — Kernel Authority.** The Kernel owns workflow state, transitions, policy enforcement, authority checks. It MUST NOT reason as Planner or execute as Executor.
- **Article XIII — Human Authority.** Production deploy, destructive operations, credential changes, and external publication require explicit human approval — recorded as an artifact.
- **Article XIV — Critical Gates.** Hard boundaries. MUST NOT be bypassed by model confidence, transport convenience, or hidden overrides.
- **Article XV — Transport Is Not Authority.** Telegram, Slack, webhooks, etc. deliver messages; they MUST NOT approve gates or mutate state.
- **Article XVI — Least Authority.** Every component runs with minimum required authority. Unknown authority is denied authority.
- **Article XX — Passive Core Principle.** Core systems act only through explicit invocation. No self-trigger, no self-expand authority, no silent policy mutation.
- **Article XXIX — Constitutional Amendment.** Even this document can be amended only with explicit proposal + rationale + impact analysis + human approval + version bump + audit entry. Prior versions remain inspectable.

## Core Rule

> **AI may PROPOSE. AI may NOT DECIDE.** (Articles III + XIII)
>
> Authority ∈ {verifier, policy, human, kernel} — never AI.

## What AI CAN Do (✅)

### Read

- ✅ Read any file in the repo
- ✅ Read `.ai/sessions/`, `.ai/audit/events.ndjson`, `.ai/memory/`
- ✅ Read `docs/specs/`, `docs/migration/`, `docs/ai_entry/`
- ✅ Query Knowledge Brain (`ai-docs/`, memory-cli when ready)

### Propose

- ✅ Propose plans, decompositions, architectures
- ✅ Propose code (in DO/dev/ within session sandbox)
- ✅ Propose verdict reasoning (LLM judge layer 3 — gated, audited)
- ✅ Propose retro lessons

### Execute (sandboxed)

- ✅ Run read-only commands (`ls`, `git status`, `grep`, `find`, `cat`)
- ✅ Run tests (`pytest`, `npm test`)
- ✅ Run linters / type checkers
- ✅ Write to current session SANDBOX (`SANDBOX/0X_<role>/*`)
- ✅ Write to current session DO/dev/ (after `vvv_pass`)

### Audit

- ✅ Append to `.ai/audit/events.ndjson` (hash chain — never edit existing entries)
- ✅ Update session state via kernel-provided commands

## What AI CANNOT Do (❌)

### Forbidden Writes (system-protected)

- ❌ Modify `.ai/policies/**` — **human-only write**
- ❌ Modify existing entries in `.ai/audit/**` — append-only (hash chain integrity)
- ❌ Modify `.ai/state/**` directly — system-only (use kernel commands)
- ❌ Modify `.ai/schemas/**` — schema changes are human decisions
- ❌ Modify `docs/specs/**` directly — spec updates need human review
- ❌ Modify `docs/migration/01_CONTEXT_AND_DECISIONS.md` without appending to `05_REVIEW_LOG.md`

### Forbidden Decisions

- ❌ Decide a `decided_by: human` transition (e.g. PROMOTED, DEPLOYED)
- ❌ Skip `vvv` (workflow gate)
- ❌ Override verifier verdict
- ❌ Bypass `loop-budget.yaml` limits
- ❌ Auto-promote / auto-deploy / auto-merge

### Forbidden Patterns

- ❌ Use external MCP servers as core path (Decision #5 — CLI-first only)
- ❌ Issue destructive ops without explicit user approval:
  - `rm -rf`
  - `git reset --hard`
  - `git push --force` (especially to main/master)
  - `git checkout .` (destroys uncommitted work)
  - `DROP TABLE`, `TRUNCATE`
  - Mass file deletion
- ❌ Commit secrets / credentials (gates check, but don't rely on gates)
- ❌ Hardcode `<user-home>` or other absolute paths in config (use placeholders)
- ❌ Silent retry on failure (escalate per workflow)

### Forbidden Imports / Sources

- ❌ Copy <upstream-project> active code to trinity_v2 active path without sanitization (Decision D2)
- ❌ Install <upstream-project> skills directly to `.claude/skills/` (Decision D7)
- ❌ Use any chatgpt_specs/* as authoritative spec — they are SUPERSEDED references

## Authority Hierarchy

```
human         ← sensitive ops, prod transitions, escalation target
   │              (decided_by: human)
   ▼
verifier      ← deterministic rules
   │              (.ai/policies/verifier-rules.yaml)
   ▼
policy        ← safety/budget gates
   │              (.ai/policies/safety.yaml + gates.yaml)
   ▼
kernel        ← entry/exit, retry, mechanical
   │              (.ai/cli/ runtime)
```

**AI sits OUTSIDE this hierarchy.** AI is the proposer, not a decider.

## Pyramid of Judgment (verdict resolution)

When a verdict is needed, the system tries layers in this order:

```
1. Deterministic verifier rules            (.ai/policies/verifier-rules.yaml)
   ↓ unsure / no rule covers this
2. Policy engine                            (.ai/policies/safety.yaml + gates.yaml)
   ↓ unsure
3. Gated LLM judge                          (last resort, audit logged, max 3/session)
   ↓ unsure
4. Human escalation                         (verdict: NEEDS_HUMAN)
```

AI is **layer 3 ONLY** — gated, audited, last resort. Never layer 1, never the sole judge.

## Audit Requirement

Every action that:
- Writes to disk (outside session SANDBOX)
- Calls an external tool (browser-cli, ftp-cli, etc.)
- Crosses a state transition

...MUST produce an entry in `.ai/audit/events.ndjson`:

```json
{
  "ts": "2026-04-28T15:23:00Z",
  "type": "session.transition",
  "prev_hash": "<sha256 of previous event's hash>",
  "hash": "<sha256 of this event's canonical JSON, excluding hash field>",
  "details": {
    "session_id": "...",
    "from": "SANDBOX",
    "to": "DO",
    "decided_by": "verifier",
    "verdict": "PASS"
  }
}
```

Hash chain integrity is **non-negotiable**. Tampering = system compromise.

## Trust Boundaries (per `.ai/policies/PROTOCOL.md`)

| Path pattern | Who can write |
|--------------|---------------|
| `.ai/policies/**` | Human only |
| `.ai/audit/**` | System (append) |
| `.ai/state/**` | System (kernel commands) |
| `.ai/schemas/**` | Human (spec changes) |
| `.ai/sessions/active/<id>/SANDBOX/<agent>/` | That agent (AI-writable, guarded) |
| `.ai/sessions/active/<id>/DO/dev/` | AI (after vvv_pass) |
| `.ai/sessions/active/<id>/DO/prod/` | Human only (after PROMOTED) |
| `docs/specs/**` | Human (with review) |
| `docs/migration/**` | Append to REVIEW_LOG; Edit others with care |
| `docs/ai_entry/**` | Human (this is canonical AI contract) |
| `references/**` | Read-only after Commit 7 (historical archive) |
| `ai-docs/**` | Human (Knowledge Brain canonical) |
| `*.md` at root (CLAUDE.md, AGENTS.md, etc.) | Human (vendor entry contracts) |

## On Uncertainty

If unsure whether an action is allowed:

1. Check `.ai/policies/safety.yaml` and `gates.yaml`
2. Check this document (`BOUNDARIES.md`)
3. Check `docs/migration/01_CONTEXT_AND_DECISIONS.md` for related decision
4. If still unsure → **ask user** (verdict: NEEDS_HUMAN)
5. Never proceed under uncertainty

## Penalties for Violation

These are not just guidelines — they are **enforcement gates**:

- Pre-commit hook checks for hardcoded secrets, absolute paths, policy edits
- Hash chain validation runs on every audit append
- Verifier rules block forbidden patterns at `vvv_pass` gate
- Test suite (`pytest .ai/cli/tests`) catches structural violations

If you're an AI and you find yourself trying to bypass any of these — **stop and ask**.
