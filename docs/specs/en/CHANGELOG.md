---
title: "Trinity Evolution Spec Pack — Changelog (English)"
purpose: "Version history of all docs in TRINITY_EVOLUTION/"
language: English
last-updated: 2026-04-28
note: "Translation of ../CHANGELOG.md"
---

# Changelog — Trinity OS Spec Pack (English)

> Version history of every document in `TRINITY_EVOLUTION/`.
>
> Follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

---

## Format

```text
## [version] - YYYY-MM-DD

### Added       — New features/docs
### Changed     — Changes to existing
### Deprecated  — Will be removed
### Removed     — Removed
### Fixed       — Bug fixes
### Security    — Vulnerabilities
```

---

## [Unreleased]

### Planned
- Phase 0.5 (P0) implementation: actual `install.sh` + templates from Bootstrap Pack spec
- Phase 1 (P1) implementation: `trinity-contract-test` CLI
- Phase 2 (P2) implementation: `memory-cli` v0.1
- Cross-reference back-fill in remaining specs (per audit in 11_RELATED_PROJECTS §12)
- Trinity OS license decision (recommend MIT or Apache-2.0)

---

## [1.0.0] - 2026-04-28

### Added — Initial Spec Pack (14 documents)

#### Foundation Documents
- `INDEX.md` — Master overview & navigation entry point
  - 18 sections, 951 lines
  - Vocabulary glossary basics, reading paths, FAQ
- `00_BLUEPRINT.md` v2.0 — Master technical spec
  - 10 committed decisions
  - 5 critical fixes integrated
  - 11-phase roadmap
  - 693 lines
- `00b_BOOTSTRAP_PACK.md` v1.0 — Phase 0.5 portability solution
  - CLAUDE.md/AGENTS.md/GEMINI.md templates
  - Minimal ai-docs + .ai/ structure
  - install.sh + verify-install.sh scripts
  - 1,071 lines
  - **Solves the original pain:** "AI doesn't know short codes after copy"
- `01_TOOL_CONTRACT.md` v1.1 — Universal CLI tool contract
  - 20 sections + 2 appendix
  - Action namespace (v1.1+)
  - Contract Compliance Test
  - 4 execution modes mandatory
  - 1,298 lines
  - **POSIX of Trinity tools**

#### Component Specs
- `02_VERIFIER_SPEC.md` v1.0 — Judge with file-based rules
  - 4 verdict types (PASS/RETRY/NEEDS_HUMAN/DEAD)
  - 5 built-in rule sets
  - Pyramid of Judgment (Verifier → Policy → LLM Judge → Human)
  - 710 lines
- `03_GOAL_LOOP_SPEC.md` v1.0 — Goal tree + loop state
  - Goal schema with type/status/decomposition
  - loop_state.json with checkpoint/resume
  - Budget management (tokens/duration/retry)
  - 644 lines
- `04_GRAPH_SPEC.md` v1.0 — Workflow + transition authority
  - Two-layer graph (kernel runtime + domain workflow)
  - Required `decided_by` field (verifier/policy/human/kernel)
  - 4 example graphs (standard/deploy/seo)
  - 710 lines
- `05_MEMORY_CLI_SPEC.md` v1.0 — Knowledge Brain (FTS5)
  - SQLite + FTS5 schema (5 tables)
  - 12 commands
  - Markdown frontmatter parsing
  - Phase 9 hybrid (vector) future plan
  - 830 lines
- `06_RETRO_CLI_SPEC.md` v1.0 — Structured retro writer
  - Additive frontmatter schema (legacy compatible)
  - 7 commands (validate/create/commit/migrate/lint/link/update)
  - Auto-call memory-cli index pipeline
  - 537 lines
- `07_SHIM_SPEC.md` v1.0 — Vendor harness extension
  - Universal trinity-shell + 5 vendor adapters
  - Skills, hooks, AGENTS.md, .cursor/rules/, GEMINI.md patterns
  - Vendor capability matrix
  - 693 lines

#### Reference Documents
- `08_DIAGRAMS.md` v1.0 — Visual reference
  - 20 Mermaid + ASCII diagrams
  - Architecture, flows, state machines
  - 877 lines
- `09_DEPLOY_GUIDE.md` v1.0 — Operations runbook
  - Install (greenfield + migration)
  - 6 troubleshooting playbooks
  - 3 disaster recovery scenarios
  - 1,088 lines
- `10_UPSTREAM_AUDIT.md` v1.0 — Migration plan
  - 80% compliance verdict
  - 10-phase migration plan (17 weeks realistic)
  - Risk matrix + backward compatibility
  - 856 lines
- `11_RELATED_PROJECTS.md` v1.0 — Inspirations + attributions
  - 7 categories of projects
  - Oracle Framework, arra-oracle-v3, github_example/* studied
  - License summary
  - Watch list for future
  - 803 lines
- `12_GLOSSARY.md` v1.0 — Complete A-Z glossary
  - All terms with cross-references
  - Index by category + by spec doc
  - Quick lookup by first letter
  - ~1000 lines

### Decisions Committed (10)

1. Trinity = Coordinator/Judge, not full AI harness
2. ai-docs = Knowledge Brain, not autonomous planner
3. Vendor AI = Reasoning Engine
4. CLI-first only for core tools
5. MCP external servers ≠ core path
6. Tool Contract must exist before new tools
7. Bootstrap Pack mandatory for project portability
8. Verifier rules must be file-based
9. Loop must support goal tree + checkpoints
10. Graph transitions must declare `decided_by`

### Critical Fixes Integrated (5)

1. **Brain definition vague** → Vocabulary locked (Knowledge Brain ≠ Brain)
2. **Verifier no rules** → File-based YAML rules + Pyramid of Judgment
3. **Linear loop only** → Goal tree + sub-goals + checkpoint/resume
4. **Graph authority unclear** → `decided_by` required (4 authority types)
5. **Bootstrap missing** → Bootstrap Pack with templates + scripts

### Decision: NOT in v0.1

- Full AI harness (use vendor's)
- Full MCP server as core path
- Platform registry (Phase 10 future)
- Android-style extension SDK
- Big dashboard
- Multi-agent graphs (complex)
- ChromaDB before FTS5
- Auto deploy / auto PR
- Linear loop only
- Graph without `decided_by`
- Verifier without rules

### Stats

- **Total documents:** 14 (1 INDEX + 13 specs)
- **Total lines:** ~12,800
- **Total size:** ~390 KB
- **Read time:** ~4-5 hours full read

### Cross-references back-filled
- `00_BLUEPRINT.md` — added Inspirations Note section linking to 11_RELATED_PROJECTS
- `05_MEMORY_CLI_SPEC.md` — added arra-oracle-v3 + Oracle Framework attribution
- `07_SHIM_SPEC.md` — added oh-my-claudecode pattern attribution

---

## Synthesis Journey (Pre-Pack — Brainstorm)

### 2026-04-28 (this session)

#### Topics Explored
- TRINITY_LEGACY structure audit
- ai-docs framework v3.0 review
- Oracle Framework + arra-oracle-v3 study
- ChromaDB explanation
- <upstream-project> production audit
- browser-cli pattern analysis
- "Harness + Loop + Graph" iron triangle
- Anthropic 1.6%/98.4% insight
- WordPress-cli future tool design

#### Decisions Crystallized
- CLI-first vs MCP debate → CLI-first wins
- Brain definition refined → Knowledge Brain (not autonomous)
- Verifier needs rules → file-based YAML
- Loop needs goal tree → not linear
- Graph needs authority → decided_by mandatory
- Bootstrap Pack identified as critical → Phase 0.5

#### Friend Brainstorm Integration
- Received feedback document with 10 commitments
- 85-90% agreement
- 5 critical fixes incorporated

---

## Spec Pack Structure (as of v1.0.0)

```
TRINITY_EVOLUTION/
├── INDEX.md                    Entry point + master overview
├── 00_BLUEPRINT.md             Master technical spec (v2.0)
├── 00b_BOOTSTRAP_PACK.md       Phase 0.5 portability
├── 01_TOOL_CONTRACT.md         Tool Contract (v1.1)
├── 02_VERIFIER_SPEC.md         Phase 4: Judge
├── 03_GOAL_LOOP_SPEC.md        Phase 5: Loop
├── 04_GRAPH_SPEC.md            Phase 6: Graph
├── 05_MEMORY_CLI_SPEC.md       Phase 2: Brain
├── 06_RETRO_CLI_SPEC.md        Phase 7: Memory writer
├── 07_SHIM_SPEC.md             Phase 8: Vendor adapter
├── 08_DIAGRAMS.md              Visual reference
├── 09_DEPLOY_GUIDE.md          Operations
├── 10_UPSTREAM_AUDIT.md          Migration plan
├── 11_RELATED_PROJECTS.md      Attributions
├── 12_GLOSSARY.md              A-Z glossary
└── CHANGELOG.md                (this file)
```

---

## Versioning Policy

### Spec Pack Versioning

- **Major (X.0.0):** Breaking architectural changes (e.g., new layer, removing component)
- **Minor (1.X.0):** New phase added, new spec doc, significant additions
- **Patch (1.0.X):** Typo fixes, clarifications, cross-reference updates

### Per-Document Versioning

Each spec doc has its own version in frontmatter:
- `version: 1.0.0-draft` — initial draft
- `version: 1.0.0` — first stable
- `version: 1.1.0` — minor update (e.g., 01_TOOL_CONTRACT.md added Action Namespace)
- `version: 2.0.0` — breaking change (e.g., 00_BLUEPRINT.md v2 — vocabulary lock)

### Phase Implementation Versioning

When phases are implemented (CLI tools), they version independently:
- `browser-cli@0.1.2` (existing)
- `memory-cli@0.1.0` (when shipped)
- `verify-cli@0.1.0` (when shipped)
- `trinity-kernel@0.5.1` (current <upstream-project> version) → `@2.0.0` (after migration)

---

## Migration Notes

### From v1.0.0 (initial) → v1.x.x

Spec pack updates within v1.x.x are non-breaking:
- New docs added (12, 13, ...)
- Cross-references updated
- Examples added
- Open questions resolved

### From v1.0.0 → v2.0.0

Future v2 may:
- Re-organize phases
- Add new architectural layer
- Change schema versions

Migration plans will be in this changelog when v2.x.x ships.

---

## Document Lifecycle

### Status Levels

| Status | Meaning |
|--------|---------|
| `draft` | Initial — open questions, may change |
| `revised` | After feedback integration |
| `master-reference` | Stable, primary source |
| `reference` | Stable, supporting |
| `audit` | Point-in-time analysis |
| `deprecated` | Superseded, kept for history |

### Current Status (2026-04-28)

| Doc | Status |
|-----|--------|
| INDEX.md | master-reference |
| 00_BLUEPRINT.md | revised (v2.0) |
| 00b_BOOTSTRAP_PACK.md | draft |
| 01_TOOL_CONTRACT.md | revised (v1.1) |
| 02-07 specs | draft |
| 08_DIAGRAMS.md | reference |
| 09_DEPLOY_GUIDE.md | draft |
| 10_UPSTREAM_AUDIT.md | audit |
| 11_RELATED_PROJECTS.md | reference |
| 12_GLOSSARY.md | reference |
| CHANGELOG.md (this) | reference |

---

## Acknowledgments (for v1.0.0)

This spec pack synthesizes contributions from:

1. **yai** (project owner) — vision, decisions, <upstream-project> production data, browser-cli reference
2. **Friend brainstorm** — 10 decision commitments, 5 critical fixes feedback
3. **Anthropic Claude Code** — 1.6%/98.4% architecture insight (foundational)
4. **Soul-Brews-Studio** — Oracle Framework + arra-oracle-v3 inspirations
5. **Open source community** — browser-cli pattern, claw-code, oh-my-claudecode, openclaude reference architectures
6. **Cognition AI** — agent context fragility insights
7. **Unix/Plan 9 community** — composability + IPC + microkernel philosophy
8. **AI synthesis** (Claude Opus) — document drafting, cross-referencing, structure

---

## Contact / Updates

- **Repository:** TRINITY_LEGACY/TRINITY_EVOLUTION/
- **Updates:** Edit the relevant doc + add an entry to this CHANGELOG.md
- **Major changes:** Bump version in frontmatter

---

## See also

- [`INDEX.md`](INDEX.md) — Start here
- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master spec
- [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) — Attributions

---

*This changelog will be updated with every spec pack revision.*
