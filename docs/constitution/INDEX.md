---
title: "Trinity Constitution — Canonical Home"
status: locked
last-updated: 2026-05-13
purpose: "Single authoritative index for every Trinity constitutional document. Higher authority than docs/specs/INDEX.md."
---

# Trinity Constitution — Canonical Home

> This directory is the canonical home of every Trinity constitutional document.
> Authority precedence is governed by **Article XXV** of Trinity Constitution v1.0.
> Amendments require Article XXIX (proposal + rationale + impact + human approval + version bump + audit).

## Why this directory exists

Prior to Addendum v1.0.2 (2026-05-13), constitutional documents lived in `docs/specs/` alongside technical specs (00–19). Mixing authority layers made it hard for AI agents and humans to recognise constitutional authority at a glance. This directory separates the **rule-of-law** layer (here) from **how-the-machine-works** specs (`docs/specs/`).

`docs/constitution/` carries D1 forbidden-write protection equal to `docs/specs/` (enforced by `.ai/cli/core/forbidden_diff.py`).

## Authority Precedence (Article XXV)

```text
Constitution                                  ← TRINITY_CONSTITUTION_V1.md
↓
Ritual Constitution (meta-rule layer, RC)     ← TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md
↓
Canonical Policies                            ← .ai/policies/**
↓
Kernel State Rules                            ← .ai/cli/**, graph transitions
↓
Workflow Contracts                            ← docs/contracts/**
↓
Tool Contracts                                ← .ai/tools.yaml, sibling tool contracts
↓
Runtime Requests
↓
Model Suggestions                             ← AI's own opinion ranks LAST
```

If any document — in this directory or elsewhere — conflicts with `TRINITY_CONSTITUTION_V1.md`, the Constitution wins.

## Directory Layout — Three Tiers

```text
docs/constitution/
├── INDEX.md                              ← this file
├── TRINITY_CONSTITUTION_V1.md            ⭐ CORE — the Constitution itself
├── TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md ⭐ CORE — the Ritual Constitution
├── addendums/                            ← extensions to the Constitution
│   ├── TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md
│   ├── TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md
│   ├── TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md
│   └── TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md
└── contracts/                            ← implementation contracts under the Constitution
    ├── TRINITY_ORGAN_MAP_V1.md
    ├── TRINITY_RITUAL_CONTRACT_V1.md
    └── TRINITY_RRR_DELEGATION_CONTRACT_V1.md
```

Only two documents are constitutionally **core** — they sit flat at the root because the file path itself signals authority. Addendums extend the Constitution but cannot contradict it (Article XXV). Contracts implement specific organ behaviour under the Constitution.

## ⭐ Core Constitutional Documents (the two supreme laws)

| # | Document | Authority | Status | Path |
|---|---|---|---|---|
| 1 | **Trinity Constitution v1.0** (30 articles · Article I–XXX) | **Supreme law** — every other rule, policy, contract, kernel transition must conform | OFFICIAL · locked 2026-05-12 | [`TRINITY_CONSTITUTION_V1.md`](TRINITY_CONSTITUTION_V1.md) |
| 2 | **Trinity Ritual Constitution v1.1-rc** (18 articles + 7 ritual specs) | **Meta-rule layer** above Ritual Contract — defines ritual templates, role permission matrix, velocity tiers, execution algorithm | `RC_PENDING_EMPIRICAL_RATIFICATION` (Article XII.5) | [`TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md`](TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md) |

If any text — anywhere in this repo — conflicts with Constitution v1.0, **the Constitution wins**. Article XII.5 forbids treating the Ritual Constitution v1.1-rc as `OFFICIAL` until it has executed end-to-end on at least one real workflow under v1.1-rc rules.

## Addendums (extensions under Article XXIX)

| Document | Subject | Status | Path |
|---|---|---|---|
| **Addendum v1.0.1** | Genesis Trust · Decision Velocity Tiers · Break-Glass · External Audit · Cognitive Presentation | OFFICIAL · locked 2026-05-12 | [`addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md`](addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md) |
| **Addendum v1.0.2** | Canonical-Home Relocation (this directory) + three-tier internal structure | OFFICIAL · 2026-05-13 | [`addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md`](addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md) |
| **Addendum v1.0.3** | Ritual Constitution v1.1-rc → v1.1 ratification (Article XXIX amendment record; Article XII.5 empirical gate satisfied) | ENACTED · 2026-05-13 | [`addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md`](addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md) |
| **Addendum v1.0.4** | Article XXIX operationalised — 3-tier classification (editorial / operational / constitutional) + trace-to-failure + pinned audit-entry format | PROPOSED · 2026-05-14 | [`addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md`](addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md) |

## Contracts (implementation specs under the Constitution)

| Document | Scope | Status | Path |
|---|---|---|---|
| **Organ Map v1.0** | 18 organs with charter | OFFICIAL · locked 2026-05-12 | [`contracts/TRINITY_ORGAN_MAP_V1.md`](contracts/TRINITY_ORGAN_MAP_V1.md) |
| **Ritual Contract v1.0** | sss → vvv → nnn → gogogo → ddd → rrr → close ritual gates | OFFICIAL · locked 2026-05-12 | [`contracts/TRINITY_RITUAL_CONTRACT_V1.md`](contracts/TRINITY_RITUAL_CONTRACT_V1.md) |
| **RRR Delegation Contract v1.0** | rrr → memory-cli evidence surface | OFFICIAL · locked 2026-05-12 | [`contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md`](contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md) |

## Amendment Process (Article XXIX)

Every amendment to any document in this directory MUST carry, in order:

1. **Proposal** — explicit statement of the change (typically a session plan envelope)
2. **Rationale** — why this change is necessary
3. **Impact Analysis** — what other rules, code, or workflows are affected
4. **Human Approval** — recorded as `decided_by: human` in audit
5. **Version Bump** — visible in document frontmatter and filename
6. **Audit Entry** — automatic via Trinity kernel session events

Prior versions remain inspectable in git history. Silent rewrites are forbidden.

## Cross-References

- Root pointer: [`/CONSTITUTION.md`](../../CONSTITUTION.md) (this is the redirect target)
- Vendor entries: [`/CLAUDE.md`](../../CLAUDE.md) · [`/AGENTS.md`](../../AGENTS.md) · [`/GEMINI.md`](../../GEMINI.md) · [`/WARP.md`](../../WARP.md)
- Technical spec corpus: [`/docs/specs/INDEX.md`](../specs/INDEX.md)
- PRD (Phases 0–16): [`/trinity_organ_refactor_prd.md`](../../trinity_organ_refactor_prd.md)
- D1 boundary enforcement: [`/.ai/cli/core/forbidden_diff.py`](../../.ai/cli/core/forbidden_diff.py)
