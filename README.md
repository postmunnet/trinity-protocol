# Trinity Protocol

Language: English | [ไทย](#ภาษาไทย)

AI agents can claim work is done. Trinity makes them prove it.

Trinity is a CLI-first control layer for AI coding agents. It coordinates
vendor AI harnesses, verifies their work, and records decisions as auditable
artifacts.

Core rule:

```text
No artifact = no trust.
No verification = no completion.
No authority = no transition.
```

---

## Why Trinity?

AI coding agents are powerful, but their claims are not reliable evidence.

They may say:

- tests pass, but no test artifact exists
- a bug is fixed, but no reproduction was verified
- a deploy is safe, but no rollback path was recorded
- a file was changed correctly, but no diff was inspected

Trinity turns AI-assisted work into an evidence-driven workflow:

```text
Human intent
    |
    v
AI proposes / executes within scope
    |
    v
Trinity captures artifacts
    |
    v
Verifier checks evidence
    |
    v
Policy / Human decides promotion
```

Read the one-page explanation:

- [`WHY_TRINITY.md`](WHY_TRINITY.md)
- [`WHY_TRINITY_TH.md`](WHY_TRINITY_TH.md)

---

## 60-Second Example

Before Trinity:

```text
User: Fix the login bug.
Agent: Done. Tests pass.
```

Problem: there is no trustworthy evidence.

After Trinity:

```text
User: Fix the login bug.
Trinity requires:
1. a scoped plan
2. bounded execution
3. diff and test artifacts
4. verifier verdict
5. explicit promotion authority
```

If the agent cannot produce the artifact, the work cannot be promoted.

> **New here?** Start with [`docs/quickstart.md`](docs/quickstart.md) for
> the 60-second hands-on tour. The full command reference lives deeper
> in the docs tree.

---

## Current Status

- Architecture generation: Trinity v2
- Runtime release: v0.1.0
- Public Tool Contract: v1.0 freeze candidate; working spec is `v1.1.0-draft`
- Kernel CLI: verified v0.1.0 runtime included in this repository
- Release evidence: [`docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md`](docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md)

Behavioral proof, not just test count:

- State machine safety
- Gate enforcement
- Audit chain integrity
- Tool contract compliance
- Verifier verdict behavior
- Operator command sequence
- Human approval requirements for risky transitions

Latest verified test evidence:

```text
Source checkout: 1862 passed, 6 skipped
Clean export without optional sibling tools: 1860 passed, 8 skipped
```

---

## Architecture

```text
Human Owner
    |
    v
Trinity Control Layer
    |
    +-- Intent / Scope / Constraints
    +-- Session capsule + state machine
    +-- Bounded AI execution
    +-- Artifact capture
    +-- Verifier + policy gates
    +-- Audit chain
    |
    v
Promotion only with evidence
```

Worker layer:

```text
Claude Code / Codex / Cursor / Gemini
    |
    v
Vendor AI proposes and executes
```

Trinity does not replace the agent. Trinity governs the work.

---

## Quickstart

```bash
bash .ai/cli/ai status
bash .ai/cli/ai sss "Test Trinity with a small documentation task"
bash .ai/cli/ai vvv
bash .ai/cli/ai nnn
bash .ai/cli/ai gogogo
```

Run the CLI test suite:

```bash
python3 -m pytest .ai/cli/tests -q
```

---

## Ritual Commands

Rituals are the operator protocol. They are not the first thing to understand,
but they are how Trinity enforces the workflow once work begins.

```text
sss -> vvv -> nnn -> gogogo -> ddd -> rrr -> close
```

| Ritual | Purpose |
|---|---|
| `sss` | Start a session capsule and initial state |
| `vvv` | Define goal, scope, constraints, acceptance, risk |
| `nnn` | Normalize into plan, steps, and artifacts |
| `gogogo` | Explicit execution gate |
| `ddd` | Inspect diff, damage, and scope creep |
| `rrr` | Retro and memory handoff through `memory-cli index` |
| `close` | Close the session with explicit final state |

Reference:

- [`docs/RITUALS.md`](docs/RITUALS.md)
- [`docs/RITUALS_TH.md`](docs/RITUALS_TH.md)

---

## Documentation Map

Start here:

- **Why Trinity:** [`English`](WHY_TRINITY.md) | [`ไทย`](WHY_TRINITY_TH.md)
- **Origin story:** [`English`](docs/ORIGIN.md) | [`ไทย`](docs/ORIGIN_TH.md)
- **Ritual reference:** [`English`](docs/RITUALS.md) | [`ไทย`](docs/RITUALS_TH.md)
- **Getting started:** [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)
- **Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Storage taxonomy:** [`docs/STORAGE_TAXONOMY.md`](docs/STORAGE_TAXONOMY.md)
- **Version lineage:** [`English`](docs/VERSION_LINEAGE.md) | [`ไทย`](docs/VERSION_LINEAGE_TH.md)
- **GitHub-safe export:** [`docs/GITHUB_EXPORT.md`](docs/GITHUB_EXPORT.md)

Operator guides:

- [`docs/operator-guide-en/00_README.md`](docs/operator-guide-en/00_README.md)
- [`docs/operator-guide-th/00_README.md`](docs/operator-guide-th/00_README.md)

Specs:

- [`docs/specs/INDEX.md`](docs/specs/INDEX.md)
- [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md)
- [`docs/specs/01_TOOL_CONTRACT.md`](docs/specs/01_TOOL_CONTRACT.md)

---

## Layout

```text
trinity_v2/
├── AGENTS.md            # Generic agent entrypoint
├── CLAUDE.md            # Claude Code entrypoint
├── GEMINI.md            # Gemini CLI entrypoint
├── WARP.md              # Warp entrypoint
├── .ai/                 # Trinity runtime
│   ├── cli/             # Python CLI kernel commands
│   ├── sessions/        # Session capsules
│   └── audit/           # Hash-chain audit log
└── docs/
    ├── specs/           # Canonical implementation specs and contracts
    ├── operator-guide-en/
    └── operator-guide-th/
```

---

## Version Lineage

This repository previously contained earlier experimental Trinity Protocol
materials. From `v0.1.0` onward, the root tree is the canonical Trinity v2
executable governance kernel. Legacy materials remain available through Git
history.

Version story:

```text
Trinity Protocol v2  = architecture / constitution generation
Runtime v0.1.0       = first public executable runtime line
Tool Contract        = v1.0 freeze candidate, v1.1 draft working spec
```

See [`docs/VERSION_LINEAGE.md`](docs/VERSION_LINEAGE.md).

---

## Memory CLI Note

For the Trinity v0.1.0 ritual flow, `rrr` delegates to `memory-cli index`.
`memory-cli learn` appears in legacy/spec materials as a historical or
non-ritual memory surface and must not be used by `rrr`.

---

## ภาษาไทย

AI agent สามารถพูดได้ว่างานเสร็จแล้ว แต่ Trinity บังคับให้ต้องมีหลักฐาน

Trinity คือ control layer แบบ CLI-first สำหรับงานที่ใช้ AI coding agent
มันไม่ได้แทน Claude Code, Codex, Cursor หรือ Gemini แต่ทำหน้าที่คุม scope,
เก็บ artifact, ตรวจ verifier, และบันทึก decision ให้ audit ย้อนหลังได้

หลักการหลัก:

```text
ไม่มี artifact = ยังเชื่อไม่ได้
ไม่มี verification = ยังถือว่างานไม่เสร็จ
ไม่มี authority = ห้ามข้าม state
```

อ่านต่อ:

- [`WHY_TRINITY_TH.md`](WHY_TRINITY_TH.md) — ทำไมต้องมี Trinity
- [`docs/ORIGIN_TH.md`](docs/ORIGIN_TH.md) — ที่มาของ Trinity
- [`docs/RITUALS_TH.md`](docs/RITUALS_TH.md) — ritual reference
- [`docs/operator-guide-th/00_README.md`](docs/operator-guide-th/00_README.md) — คู่มือใช้งาน
