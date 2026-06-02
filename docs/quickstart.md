# Quickstart — 60 seconds with Trinity

> Goal: install once, run one verified session, see the audit trail.
> Time: about a minute of typing, plus thinking time.

## Before you start

Make sure Trinity is installed and on your `PATH`. The full install
guide lives in [`docs/GETTING_STARTED.md`](GETTING_STARTED.md).

You can confirm everything is wired up with:

```bash
ai lll
```

`ai lll` is a read-only snapshot — git state, active session, recent
audit events. If you see a panel, you are good to go.

## Hello Trinity — a complete session

The task: rename every `foo` identifier in `src/` to `bar` without
breaking the tests. Five commands, one audit trail.

### 1. Open a session

```bash
ai sss "rename-foo-to-bar-everywhere"
```

This creates a session capsule on disk — a folder with `THINK/`,
`DO/`, `SANDBOX/`, and a hash-chained audit log.

### 2. Clarify the goal (five short questions)

```bash
ai vvv \
  --answer "1=All 'foo' references in src/ become 'bar' with tests still green" \
  --answer "2=src/**/*.py only — no config, no docs, no vendor" \
  --answer "3=Skip 'foo' in test fixtures and third-party modules" \
  --answer "4=All tests pass · zero 'foo' identifiers remain in src/" \
  --answer "5=Identifier collision if 'bar' already exists — grep first"
```

The five questions are Goal, Scope, Constraint, Acceptance, Risk.
Trinity refuses to plan until they are answered.

### 3. Lock in the plan

```bash
ai nnn --plan-envelope=plan.json
```

`plan.json` declares steps, budgets, allowed paths, and acceptance
checks. Trinity rejects the envelope on budget breach or missing
fields — no silent overruns.

### 4. Execute, checkpoint by checkpoint

```bash
ai gogogo
```

Each step runs its work, then a verifier evaluates pass-when
predicates. A failed predicate stops the chain — the agent cannot
declare itself done.

### 5. Close the loop

```bash
ai rrr
```

`rrr` runs the acceptance gates declared earlier, writes the
structured retro, and hands the lessons to `memory-cli` so the
next session can recall them.

## What just happened?

Five commands produced four artifacts you can audit at any time:

- A signed audit chain at `.ai/audit/events.ndjson`
- A frozen plan envelope at `.state/plan.json`
- A diff of every edited file under `DO/dev/`
- A retro under `.ai/memory/retros/` linked back to the audit chain

No step could be skipped, no claim could be self-certified.

## Today's commands & coming aliases

| Today    | Coming (alias) | Purpose                           |
|----------|----------------|-----------------------------------|
| `sss`    | `start`        | open a session capsule            |
| `vvv`    | `verify`       | answer the five clarifying Qs     |
| `nnn`    | `plan`         | lock in a budgeted plan envelope  |
| `gogogo` | `go`           | execute the plan with checkpoints |
| `ddd`    | `done`         | human-decided promote + deploy    |
| `rrr`    | `retro`        | acceptance gates + write retro    |
| `lll`    | `look`         | read-only state snapshot          |

The short codes are the canonical entrypoints today. The English
aliases ship in a later release; both will resolve to the same
underlying command.

## Where to go next

- [`../README.md`](../README.md) — the why and the architecture
- [`./GETTING_STARTED.md`](GETTING_STARTED.md) — install + first project
- [`./RITUALS.md`](RITUALS.md) — full command reference
- [`./STORAGE_TAXONOMY.md`](STORAGE_TAXONOMY.md) — where Trinity puts files
