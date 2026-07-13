# Getting Started

Trinity is a local-first AI governance kernel. It does not make an AI
agent smarter; it makes AI-assisted work more explicit, auditable, and
verifiable.

## Prerequisites

- Python 3.9+
- Install runtime dependencies: `pip install -r requirements.txt`
  (installs `rich`, `typer`, `PyYAML` — the packages the kernel imports)

## First Commands

Run from the repository root:

```bash
bash .ai/cli/ai status
bash .ai/cli/ai lll
```

Start a small session:

```bash
bash .ai/cli/ai sss "Test Trinity with a small documentation task"
```

Answer the five `vvv` questions:

```bash
bash .ai/cli/ai vvv \
  --answer 1="Success means a small plan exists" \
  --answer 2="Only docs are in scope" \
  --answer 3="Do not modify source code" \
  --answer 4="A plan file exists" \
  --answer 5="The plan may be too vague"
```

Then check state:

```bash
bash .ai/cli/ai status
```

## What To Expect

- `sss` creates a session capsule under `.ai/sessions/`.
- `vvv` records goal, scope, constraints, acceptance, and risk.
- `nnn` accepts a plan envelope and writes planning artifacts.
- `gogogo` executes the approved plan steps.
- `rrr` writes retrospective evidence and delegates memory ingestion via
  `memory-cli index`, not `memory-cli learn`.

## Read Next

- Thai Operator Guide: [`operator-guide-th/00_README.md`](operator-guide-th/00_README.md)
- Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Release workflow: [`operator-guide-th/05_RELEASE_GATE.md`](operator-guide-th/05_RELEASE_GATE.md)
