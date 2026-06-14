---
short-code: lll
purpose: "Look / List — situational awareness snapshot"
status: stub
spec: docs/specs/07_SHIM_SPEC.md §3.2
last-updated: 2026-04-30
---

# `lll` — Canonical Shim

> Vendor-agnostic definition. Adapters render this into a slash command,
> Cursor rule, AGENTS.md directive, or Warp workflow.

## Purpose

Give the agent (and the human) a **fast, factual snapshot** of the current
state before any other action: git, sessions, audit, recent decisions.

`lll` makes **no domain writes** — it NEVER mutates project state, opens
sessions, or proposes plans. The one deliberate exception: it appends a
single `lll.invoked` event to the audit chain, because *looking at state
is itself an auditable act* (who checked what, when — e.g. a remote
`/lll` from Telegram before approving a gate). Its only job is to
surface what is *currently true* so the next short code (`sss`/`vvv`/
`nnn`) starts from a correct baseline.
(Wording locked by operator decision 2026-06-12 — resolves the
"read-only vs audit append" drift recorded in the atlas K18 register.)

## When to invoke

- Start of every session
- After a context switch (long pause, returning from another task)
- Whenever the agent feels uncertain about state ("am I in a session?")
- Before `sss:` to see whether work is already in flight

## Inputs

| Field | Required | Source |
|-------|----------|--------|
| current cwd | yes | shell |
| repo root | yes | auto-detected via SSOT |
| optional `--vendor=<name>` | no | adapter |

No user-supplied args.

## What the kernel returns

A structured snapshot containing:

1. **Git state** — branch, dirty files (count, not contents), unpushed commits
2. **Trinity session state** — active session id, current state node (per
   `graphs/standard.yaml`), last transition timestamp
3. **Recent audit events** — last 3–5 entries from `.ai/audit/events.ndjson`
4. **Open work** — anything in `THINK/`, `SANDBOX/<seat>/`, or `DO/dev/` of
   the active session
5. **Memory hint** — top 1–3 relevant Knowledge Brain hits if `--vendor`
   suggests one (Phase 2 — currently no-op)

Output format defaults to human-readable Markdown; `--json` returns the
structured envelope per `01_TOOL_CONTRACT.md`.

## Behavior contract

**MUST**
- No domain writes: nothing under `.ai/state/`, session folders, or any
  project file may change. The audit chain is the single exception below.
- Resolve all paths via SSOT (`${project_root}/...`); never hard-code.
- Append a `lll.invoked` event to the audit chain — observation is an
  auditable act; the trail of "who looked, when" has real incident value
  (operator decision 2026-06-12; the earlier citation to D9 here was
  wrong — D9 is the genesis-event spec, unrelated to read-event appends).
- Exit 0 on success regardless of how much state exists (empty repo is OK).

**MUST NOT**
- Open a new session
- Suggest a plan ("you should now ...")
- Modify any file
- Make external calls (no network, no LLM judge)

## Adapter rendering hints

| Adapter | Surface | Notes |
|---------|---------|-------|
| Claude Code skill | `lll/instructions.md` invokes `trinity-shell lll --vendor=claude-code` | Render Markdown panel, no extra commentary |
| Codex CLI | AGENTS.md `On the keyword "lll"` directive | Show output as block, no narration |
| Cursor rule | `lll.mdc` triggers on user message `lll` | Inline render |
| Warp workflow | `.warp/workflows/lll.yaml` | `command: trinity-shell lll` |
| Gemini CLI | invocation directive in GEMINI.md | Same — render Markdown |

## Anti-patterns

- ❌ Adapter that wraps `lll` with extra LLM analysis (defeats the
  "factual snapshot" purpose)
- ❌ Adapter that hides parts of the output ("user doesn't need to see audit")
- ❌ Embedding project-specific status checks (<upstream-project> deploy state, etc.)
  → those belong in a project-specific extension, not the canonical `lll`

## Canonical user-facing text

See `docs/ai_entry/SHORT_CODES.md §lll` for the wording adapters should
match in their on-screen prompts and help text.
