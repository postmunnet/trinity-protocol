---
title: "Trinity Constitution Addendum v1.0.2 — Canonical-Home Relocation"
version: "1.0.2"
status: "official"
last-updated: "2026-05-13"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
parent: "TRINITY_CONSTITUTION_V1.md"
supersedes: "Path tokens to docs/specs/TRINITY_*.md in CLAUDE.md, AGENTS.md, GEMINI.md, WARP.md, CONSTITUTION.md (root), docs/specs/INDEX.md, trinity_organ_refactor_prd.md (Appendix A), docs/ai_entry/BOUNDARIES.md, TRINITY_RRR_DELEGATION_CONTRACT_V1.md (line 218), TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md (Section A layer_0_artifacts paths)."
amendment-policy: "Article XXIX of the parent Constitution. Article-XXIX compliance is demonstrated below in §Proposal / §Rationale / §Impact / §Human Approval / §Version Bump / §Audit Entry."
audit-session: "0001_2026-05-13_00_41_am_feat-feat-constitution-home-docs-relocation"
---

# Trinity Constitution Addendum v1.0.2

> This Addendum amends the **canonical filesystem location** of every Trinity constitutional document. It does not amend any Article of the parent Constitution. The verbatim text of every relocated document remains byte-identical except for self-references that now point at the new home.
>
> If this Addendum conflicts with the parent Constitution, the parent wins (Article XXV).

---

## Article XXIX Compliance

### §1 Proposal

Relocate the six canonical Trinity constitutional documents from `docs/specs/` to a dedicated `docs/constitution/` directory (peer to `docs/specs/`), update every path reference across the repo, expand the D1 forbidden-write protection to cover the new location, **and organise the new directory into a three-tier hierarchy that visually distinguishes the two core Constitutions from extending Addendums and implementing Contracts** (added 2026-05-13 per operator amendment A1 of the plan envelope; see §1.1).

#### §1.1 Three-Tier Hierarchy (operator amendment A1)

The operator (Founder) directed that the two **core** constitutional documents — the Constitution v1.0 and the Ritual Constitution v1.1-rc — must be visually separated from the five dependent documents so anyone listing `docs/constitution/` immediately sees the supreme law. The chosen layout:

```text
docs/constitution/
├── INDEX.md                                  ← entry point
├── TRINITY_CONSTITUTION_V1.md                ⭐ CORE — the Constitution itself
├── TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md    ⭐ CORE — the Ritual Constitution
├── addendums/                                ← extensions under Article XXIX
│   ├── TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md
│   └── TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md (this file)
└── contracts/                                ← implementation contracts
    ├── TRINITY_ORGAN_MAP_V1.md
    ├── TRINITY_RITUAL_CONTRACT_V1.md
    └── TRINITY_RRR_DELEGATION_CONTRACT_V1.md
```

The six original relocations (from `docs/specs/` to `docs/constitution/`):

```text
docs/specs/TRINITY_CONSTITUTION_V1.md            → docs/constitution/TRINITY_CONSTITUTION_V1.md
docs/specs/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md → docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md
docs/specs/TRINITY_ORGAN_MAP_V1.md               → docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md
docs/specs/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md → docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md
docs/specs/TRINITY_RITUAL_CONTRACT_V1.md         → docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md
docs/specs/TRINITY_RRR_DELEGATION_CONTRACT_V1.md → docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md
```

New artifacts created in `docs/constitution/`:

```text
docs/constitution/INDEX.md                                         (canonical entry)
docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md (this file)
```

### §2 Rationale

Prior to this Addendum, constitutional documents were stored in `docs/specs/` alongside numbered technical specs (00–19) and ancillary files (CHANGELOG / CONTRIBUTING / LICENSE_DECISION). Mixing authority layers in one directory had four costs:

1. **Discoverability.** An operator or AI agent visiting `docs/specs/` saw constitutional documents at the same visual rank as `08_DIAGRAMS.md` or `13_NOTIFY_CLI_SPEC.md`.
2. **Reference ergonomics.** Frequent constitutional citations across CLAUDE.md / AGENTS.md / GEMINI.md / WARP.md / PRD pointed at `docs/specs/`, which is also the home of dozens of unrelated specs — readers could not infer authority from the path alone.
3. **Mental model.** New collaborators (human or AI) had no path-level signal that some documents in `docs/specs/` carry higher authority than others.
4. **Future growth.** As technical specs grow (Phases 3–15 add ~13 new files), the constitutional layer would have become increasingly buried.

The operator (Founder) declared on 2026-05-13 (Thai-language operator note): *"CONSTITUTION กระจัดกระจายอยู่ มันคือของใหญ่สุด สำคัญสุด ควรอยู่ในตำแหน่งที่ เข้าถึงง่าย จะได้อ้างอิงง่าย"* — i.e. constitutional documents must occupy a clearly distinguished, easy-to-reference home. This Addendum implements that operator decision.

### §3 Impact Analysis

#### §3.1 Path Reference Matrix

| File | Path tokens updated | Type |
|---|---|---|
| `CLAUDE.md` | 8 (core-row reorder + addendums/ contracts/ paths + Article XXV chain) | Documentation |
| `CONSTITUTION.md` (root) | 7 (core-row reorder + addendums/ contracts/ paths) | Documentation |
| `docs/specs/INDEX.md` | 1 (constitutional row → external pointer + relocation note) | Documentation |
| `trinity_organ_refactor_prd.md` | 8 (Appendix A three-tier list + §11 PR spec path) | Documentation |
| `docs/ai_entry/BOUNDARIES.md` | 4 (Constitutional Authority section, addendums/ + contracts/ paths) | Documentation |
| `docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md` | 1 (self-reference, line 218) | Self-reference |
| `docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md` | 4 (Section A layer_0_artifacts) | Self-reference |
| `docs/constitution/INDEX.md` | full rewrite into three-tier hierarchy table | Documentation |
| `.ai/cli/core/forbidden_diff.py` | 1 (FORBIDDEN_PATTERNS list) + docstring | Kernel code |
| `.ai/cli/tests/test_forbidden_diff_allowlist.py` | 2 new test functions | Tests |

`AGENTS.md`, `GEMINI.md`, `WARP.md` carried no `docs/specs/TRINITY_*` references and were left unchanged.

#### §3.2 D1 Boundary Delta

| Before | After |
|---|---|
| `^.ai/policies/` | `^.ai/policies/` |
| `^.ai/schemas/` | `^.ai/schemas/` |
| `^docs/specs/` | `^docs/specs/` |
| — (gap) | **`^docs/constitution/`** ← added |
| `^references/` | `^references/` |
| `^.ai/audit/(?!events\.ndjson$)` | `^.ai/audit/(?!events\.ndjson$)` |

Net effect: D1 protection coverage **expanded**, not relocated. `docs/specs/` remains protected so future technical-spec files there still require carve-outs. `docs/constitution/` is added at equal authority. No path is now less protected than before.

#### §3.3 Behaviour Preservation

- Article XXV priority chain text and ordering: **unchanged** (only the path token after "Ritual Constitution" updates).
- Verbatim Article body of every relocated document: **byte-identical** except where the document referenced sibling constitutional documents by path (those update to the new home).
- Audit chain: append-only by design; existing 1,840+ entries remain valid. The relocation does not require a chain rewrite.
- Ratification status of each relocated document: **preserved** (Constitution v1.0 stays OFFICIAL, Ritual Constitution v1.1-rc stays RC_PENDING_EMPIRICAL_RATIFICATION, etc.).

#### §3.4 Risks

| Risk | Mitigation |
|---|---|
| Stale path reference in a vendor file or PRD breaks Article XXV priority chain at runtime | Acceptance check A3: grep -rln 'docs/specs/TRINITY_' (excluding archives/retros) returns 0 hits |
| Addendum omits required Article XXIX fields | This document has §Proposal, §Rationale, §Impact, §Human Approval, §Version Bump, §Audit Entry — all six |
| FORBIDDEN_PATTERNS regex regression breaks existing tests | New parameterised tests cover docs/constitution/ violation and carve-out paths alongside legacy docs/specs/ tests |
| Future operator forgets the relocation and creates a constitutional file in docs/specs/ | docs/specs/INDEX.md carries an explicit redirect note pointing to docs/constitution/INDEX.md |

### §4 Human Approval

This Addendum is approved by the Operator (Founder / Trinity Architect) acting under Article XIII (Human Authority).

The approval is recorded in the audit chain as the `ddd` event of session `0001_2026-05-13_00_41_am_feat-feat-constitution-home-docs-relocation` with `decided_by=human`. Until that audit entry exists, this Addendum's `status` field is `pending` (not `official`).

The plan envelope at `.ai/sessions/<this-session>/THINK/plan_envelope.json` field `decided_by` set to `human`. The acceptance evidence at `.ai/sessions/<this-session>/CONTROL/deploy_check_evidence.json` will be inspected by the operator before `ddd` is issued.

### §5 Version Bump

| Document | Old version | New version |
|---|---|---|
| `TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md` | `1.0.1` | (unchanged — separate document) |
| `TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md` | (new) | `1.0.2` |

The parent `TRINITY_CONSTITUTION_V1.md` is **not** version-bumped — no Article body changes. This Addendum is the version bump for the relocation event.

### §6 Audit Entry

This Addendum corresponds to the session capsule:

```text
.ai/sessions/0001_2026-05-13_00_41_am_feat-feat-constitution-home-docs-relocation/
```

Required audit events (emitted by Trinity kernel):

```text
session.created  ← sss
vvv.completed    ← vvv
nnn.completed    ← nnn (plan envelope accepted)
gogogo.completed ← gogogo (12 steps walked)
ddd.completed    ← ddd (human approval — required for §4)
rrr.completed    ← rrr (memory-cli index of retro)
session.closed   ← archive
```

The audit chain remains validatable by:

```bash
python3 -c 'import json,hashlib;e=json.loads(open(".ai/audit/events.ndjson").readline());c=json.dumps({k:v for k,v in e.items() if k!="hash"},sort_keys=True,separators=(",",":"));print("genesis ok" if e["hash"]==hashlib.sha256(c.encode()).hexdigest() else "CHAIN BROKEN")'
```

---

## Article XXV Priority Chain — No Change

The Article XXV priority chain in CLAUDE.md remains:

```text
Constitution
→ Ritual Constitution       (docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md — RC, Article XII.5 pending)
→ Canonical Policies        (.ai/policies/**)
→ Kernel State Rules        (.ai/cli/**, graph transitions)
→ Workflow Contracts        (docs/contracts/**)
→ Tool Contracts            (.ai/tools.yaml, sibling tool contracts)
→ Runtime Requests
→ Model Suggestions
```

Only the path token after "Ritual Constitution" updates from `docs/specs/` to `docs/constitution/`. The chain itself — order, content, semantics — is identical.

---

## Future Work

Items intentionally **out of scope** for this Addendum:

1. Memory-cli `memory-cli index` of `docs/constitution/` — will be picked up automatically by the next `rrr` ritual that indexes session retros.
2. Renaming `.ai/sessions/archive/` snapshots that capture the old `docs/specs/TRINITY_*` paths — archives are frozen historical records by Article (immutable session evidence).
3. Memory retro files at `.ai/memory/retros/*.md` referencing the old paths — also frozen historical records.
4. The `TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md` status of `RC_PENDING_EMPIRICAL_RATIFICATION` — Article XII.5 ratification is a separate workflow.

---

## End of Addendum v1.0.2
