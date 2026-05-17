# Architecture

Trinity is an executable control plane for AI-assisted work.

```text
Human Owner
    |
    v
Trinity Kernel
    |
    +-- Planner        (turn intent into scoped plan artifacts)
    +-- Executor       (run bounded work in approved scope)
    +-- Verifier       (check evidence and decide PASS/RETRY/NEEDS_HUMAN/DEAD)
    +-- Audit Chain    (append-only truth log)
    +-- Capture Store  (inputs, outputs, and evidence)
    +-- Memory Index   (retrieval over accepted artifacts)
```

## Core Principle

Trinity does not trust claims. Trinity trusts artifacts.

An AI agent can propose, edit, and produce evidence. It cannot self-approve
completion, bypass policy gates, or turn memory into truth.

## Runtime Layers

- **CLI kernel:** deterministic commands in `.ai/cli/`.
- **Session capsule:** per-task working area under `.ai/sessions/<id>/`.
- **State pointer:** `.state/session_state.json`, with canonical
  `graph_state` and compatibility-only `legacy_state`.
- **Audit chain:** `.ai/audit/events.ndjson`, append-only and hash-linked.
- **Verifier:** rule-driven checks that consume artifacts.
- **Memory:** retrieval index over accepted artifacts; `rrr` uses
  `memory-cli index`.

## Canonical Specs

Detailed contracts live under [`docs/specs/`](specs/). Operator docs are
practical entry points; the specs remain canonical for implementation
details.
