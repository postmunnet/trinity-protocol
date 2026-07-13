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

The task is deliberately tiny — create a one-line note file — so you can
watch the whole governed loop open, execute, verify, and close **green**
in about a minute. Real code sessions run through the exact same loop.

### 1. Open a session

```bash
ai sss "hello-trinity"
```

This creates a session capsule on disk — a folder with `THINK/`,
`DO/`, `SANDBOX/`, and a hash-chained audit log.

### 2. Clarify the goal (five short questions)

```bash
ai vvv \
  --answer "1=Create hello/trinity.md containing the line 'Trinity verified this.'" \
  --answer "2=Only the hello/ folder — nothing else" \
  --answer "3=Do not touch anything outside hello/" \
  --answer "4=hello/trinity.md exists and contains that exact line" \
  --answer "5=None — it is a trivial note"
```

The five questions are Goal, Scope, Constraint, Acceptance, Risk.
Trinity refuses to plan until they are answered.

### 3. Lock in the plan

A plan envelope is just a JSON file — steps, budgets, allowed paths,
and acceptance checks. Trinity rejects the envelope on budget breach
or missing fields, so nothing silently overruns. A ready-to-run
example for this exact task ships at
[`../examples/plan.json`](../examples/plan.json):

```json
{
  "goal": "Create a note at hello/trinity.md containing the line 'Trinity verified this.'",
  "estimated_duration_minutes": 5,
  "estimated_iterations": 1,
  "estimated_tool_calls": 3,
  "target": "hello/",
  "allowed_paths": [
    "hello/**"
  ],
  "steps": [
    {
      "n": 1,
      "title": "Create hello/trinity.md containing the line 'Trinity verified this.'",
      "estimate_min": 2,
      "risk": "low"
    }
  ],
  "forbidden_paths": [
    "docs/specs/**",
    ".ai/policies/**",
    ".ai/schemas/**",
    ".ai/audit/**"
  ],
  "acceptance": [
    {
      "id": "A1",
      "description": "the note file exists",
      "command": "test -f hello/trinity.md",
      "required": true,
      "expect_exit": 0
    },
    {
      "id": "A2",
      "description": "it contains the required line (the work actually happened)",
      "command": "grep -q 'Trinity verified this.' hello/trinity.md",
      "required": true,
      "expect_exit": 0
    }
  ]
}
```

Run it straight from the shipped example — no need to type it out:

```bash
ai nnn --plan-envelope=examples/plan.json
```

### 4. Do the work

The plan describes one step. Do it — in a real session this is the part
your coding agent performs for you:

```bash
mkdir -p hello && echo "Trinity verified this." > hello/trinity.md
```

### 5. Checkpoint the execution

```bash
ai gogogo
```

Each step runs its work, then a verifier evaluates pass-when
predicates. A failed predicate stops the chain — the agent cannot
declare itself done.

### 6. Confirm the goal is really yours

Trinity will not let an AI self-certify *the goal*. Mark the five
answers as human-confirmed before you close:

```bash
ai vvv --confirm 1,2,3,4,5
```

### 7. Close the loop

```bash
ai rrr
```

`rrr` runs the acceptance gates (the file exists **and** contains the
line), writes the structured retro, and hands the lessons to
`memory-cli`. Because the work is proven and the goal is confirmed, the
session closes **DONE**. Archive it with `ai close`.

## What just happened?

One governed loop produced four artifacts you can audit at any time:

- A signed audit chain at `.ai/audit/events.ndjson`
- A frozen plan envelope at `.state/plan.json`
- An acceptance + forbidden-path gate at `rrr`, checked against your git baseline
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
