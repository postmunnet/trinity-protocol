# Trinity v2

> CLI-native AI microkernel — Coordinator + Judge for vendor AI harnesses.

**One-liner:** ai-docs is the knowledge brain, vendor AI is the reasoning engine, CLI tools are organs, verifier is the judge, artifacts are truth.

---

## Operator Guides

- **Operator Guide (English):** [`docs/operator-guide-en/00_README.md`](docs/operator-guide-en/00_README.md)
- **คู่มือใช้งานภาษาไทย:** [`docs/operator-guide-th/00_README.md`](docs/operator-guide-th/00_README.md)

English | Thai:
[`English`](docs/operator-guide-en/00_README.md) |
[`ไทย`](docs/operator-guide-th/00_README.md)

---

## Workflow

```text
Human Owner
    |
    v
sss -> vvv -> nnn -> gogogo -> ddd -> rrr -> close
 |      |      |        |       |      |       |
 |      |      |        |       |      |       +-- final manifest / archive
 |      |      |        |       |      +---------- retro + memory-cli index
 |      |      |        |       +----------------- Release Gate / human decision
 |      |      |        +------------------------- bounded execution + verifier
 |      |      +---------------------------------- plan + acceptance artifacts
 |      +----------------------------------------- scope / risk / acceptance
 +------------------------------------------------ session capsule

Artifact Truth
    |
    +-- THINK/plan + DO evidence + CAPTURE logs
    +-- Verifier verdicts
    +-- Audit Chain (.ai/audit/events.ndjson)
```

---

## Layout

```
trinity_v2/
├── CLAUDE.md            ← Claude Code entrypoint
├── AGENTS.md            ← Cursor / Codex entrypoint
├── .ai/                 ← Trinity runtime
│   ├── cli/             ← Python CLI (kernel commands)
│   ├── sessions/        ← session capsules
│   └── audit/           ← events.ndjson (hash-chain log)
└── docs/
    └── specs/           ← canonical implementation specs and contracts
```

## Start here

- **Getting started:** [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)
- **Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Storage taxonomy:** [`docs/STORAGE_TAXONOMY.md`](docs/STORAGE_TAXONOMY.md)
- **Version lineage:** [`docs/VERSION_LINEAGE.md`](docs/VERSION_LINEAGE.md)
- **Operator Guide (English):** [`docs/operator-guide-en/00_README.md`](docs/operator-guide-en/00_README.md)
- **Operator Guide (Thai):** [`docs/operator-guide-th/00_README.md`](docs/operator-guide-th/00_README.md)
- **Master overview:** [`docs/specs/INDEX.md`](docs/specs/INDEX.md)
- **Vision/blueprint:** [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md)
- **Tool contract:** [`docs/specs/01_TOOL_CONTRACT.md`](docs/specs/01_TOOL_CONTRACT.md)
- **Bootstrap a project:** [`docs/specs/00b_BOOTSTRAP_PACK.md`](docs/specs/00b_BOOTSTRAP_PACK.md)
- **GitHub-safe export:** [`docs/GITHUB_EXPORT.md`](docs/GITHUB_EXPORT.md)

## Status

- Trinity v2 runtime line: v0.1.0
- Kernel CLI: verified v0.1.0 runtime included in this repository
- Full CLI test suite: PASS (source checkout: 1862 passed, 6 skipped; clean export without optional sibling tools: 1860 passed, 8 skipped)
- Release evidence: [`docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md`](docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md)

## Version Lineage

This repository previously contained earlier experimental Trinity Protocol
materials. From `v0.1.0` onward, the root tree is the canonical Trinity v2
executable governance kernel. Legacy materials remain available through Git
history.

See [`docs/VERSION_LINEAGE.md`](docs/VERSION_LINEAGE.md).

## Memory CLI note

For the Trinity v0.1.0 ritual flow, `rrr` delegates to `memory-cli index`.
`memory-cli learn` appears in legacy/spec materials as a historical or
non-ritual memory surface and must not be used by `rrr`.
