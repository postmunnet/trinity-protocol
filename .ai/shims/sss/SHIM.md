---
short-code: sss
purpose: "Session Start — open a Trinity session capsule before any ritual that mutates state"
status: stub
spec: docs/specs/07_SHIM_SPEC.md §3.2
last-updated: 2026-05-11
---

# `sss` — Canonical Shim

> Vendor-agnostic definition. Adapters render this into a slash command,
> Cursor rule, AGENTS.md directive, or Warp workflow.

## Purpose

Open a **Trinity session capsule** so subsequent rituals (`vvv` / `nnn` /
`gogogo` / `rrr`) have a place to write artifacts and an audit thread to
attach events to.

`sss` is the **gate between observation and work**. `lll` is observation
(read-only); `vvv` onward is work. Every ritual after `lll` requires an
active session — `sss` is how you get one.

## When to invoke

- After `lll` confirms there is **no active session**
- At the start of any new task, before drafting questions or plans
- When `lll` shows a stale or wrong session and you want a fresh one
- **Always** before `vvv` — the `vvv` shim refuses without `sss`

## Inputs

| Field | Required | Source |
|-------|----------|--------|
| `<task-slug>` | yes | operator — kebab-case task name |
| optional `--vendor=<name>` | no | adapter |

The slug is a stable kebab-case identifier (e.g. `lock-sss-before-vvv`,
`fix-auth-modal`). It becomes part of the session directory name and is
quoted in every audit event for the life of the session.

## What the kernel does

The shim maps to the kernel command:

```
ai session new <task-slug>
```

The kernel then:

1. Allocates the next session id (`0001_…`, `0002_…`, etc.)
2. Creates `.ai/sessions/<id>_<date>_<task-slug>/` with the standard
   subtree (`THINK/`, `DO/`, `CONTROL/`, `SANDBOX/`, `.state/`)
3. Writes `META.json` with task slug, slug source, created_at
4. Records `session.created` to the audit chain
5. Sets the graph state to `THINK` (ready for `vvv`)

## Behavior contract

**MUST**
- Be invoked **before** `vvv` whenever no active session exists
- Carry a non-empty kebab-case `<task-slug>`
- Refuse silently if a session is already active (or surface a hint to
  close the existing one with `rrr` first)
- Append `session.created` to the audit chain
- Set graph state to `THINK`

**MUST NOT**
- Mutate any file outside the new session directory
- Open a session without a task slug
- Open more than one active session at a time
- Auto-fire `vvv` after creating the session (that is the operator's
  signal, not the shim's)

## Output shape

```
.ai/sessions/<id>_<date>_<slug>/
├── THINK/              ← context, vvv answers (01_PROMPT.md), scope, acceptance
├── DO/
│   ├── snapshot/       ← immutable backup of starting state
│   ├── dev/            ← working copy
│   └── prod/           ← release candidate (touched only at ddd)
├── CONTROL/
│   ├── META.json       ← session metadata
│   ├── VERIFY.md       ← verifier output log
│   └── LIVE_MONITOR.md ← step-by-step gogogo trace
├── SANDBOX/            ← parallel-seat scratch (gemini/claude/codex)
└── .state/             ← markers (vvv_pass, nnn_pass, …) — never edit
```

## Adapter rendering hints

Adapters should:
- Accept `sss <task-slug>` (positional) or `sss --task=<slug>`
- Validate the slug (kebab-case, no spaces) before firing
- After success, surface the new session path **and** the literal next
  command (`ai vvv` or `vvv` short code) so the operator never has to
  remember the order
- If the operator types `vvv` / `nnn` / `gogogo` / `rrr` while no
  session is active, **refuse and recommend `sss`** rather than
  silently failing or auto-creating one

## Anti-patterns

- ❌ Adapter auto-creates a session on `vvv` invocation (hides the
  session boundary; loses the operator's signal of intent)
- ❌ Operator runs `vvv` without `sss` and the adapter proceeds with a
  prior session that doesn't match the new task
- ❌ `sss` fires twice without a `rrr` in between (two open sessions
  is a Trinity boundary violation)
- ❌ Adapter accepts a `<task-slug>` with spaces or path separators
  (breaks session directory naming)

## Canonical user-facing text

Trinity workflow:

```
lll → sss <slug> → vvv → nnn → gogogo → rrr
```

`sss` is mandatory between `lll` and `vvv`. The audit chain enforces
the rest of the order; `sss` is enforced at the adapter level by the
`vvv` shim's pre-flight section (see `.ai/shims/vvv/SHIM.md`).
