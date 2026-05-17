---
title: "Quick Start — First Session in trinity_v2"
status: locked
last-updated: 2026-04-28
audience: "AI agent picking up trinity_v2 for the first time"
read-time: "3 minutes"
---

# Quick Start — First Session in trinity_v2

> Read this if you're a new AI agent. Skim it. Then run `lll`.

## What is this repo?

**trinity_v2** = canonical bootstrap/runtime for **Trinity OS** — a CLI-native AI microkernel that makes vendor AI work safely under deterministic rules.

It is **NOT**:
- ❌ A clone of <upstream-project> (<upstream-project> is a separate production project that uses Trinity)
- ❌ A Claude Code clone (Trinity sits BENEATH Claude Code, not replacing it)
- ❌ An autonomous agent framework (you are the agent; Trinity is the kernel)

It IS:
- ✅ A coordinator + judge that orchestrates vendor AI workflow
- ✅ A reference implementation per `docs/specs/` (TRINITY_EVOLUTION v2.0)
- ✅ A test bed for Phase 0.5 (Bootstrap Pack) and Phase 1+ tools

## The 60-Second Mental Model

```
You (vendor AI: Claude/Codex/Gemini/Cursor/Warp)
   │  thinking, planning, generating code
   ▼
Trinity Shim (this repo's CLAUDE.md / AGENTS.md / etc. + .ai/shims/)
   │  inject context, route short codes, enforce ritual
   ▼
Trinity Kernel (.ai/cli/) — Coordinator + Judge
   │  state, loop, graph, policy, audit (events.ndjson hash chain)
   ▼
CLI Tools (browser-cli, memory-cli, verify-cli) — Organs
   │  do actual work via stdin/stdout JSON
   ▼
Artifacts (files, verdicts, audit log) — Truth
```

**You = brain. Kernel = executive function. Tools = hands. Artifacts = truth.**

## First-Time Checklist

1. ✅ Read this file (you're doing it)
2. Read [`SHORT_CODES.md`](SHORT_CODES.md) — memorize the 7 codes
3. Read [`BOUNDARIES.md`](BOUNDARIES.md) — know what you can/can't do
4. Skim [`WORKFLOW.md`](WORKFLOW.md) — sequence overview
5. Decide what kind of work you're doing:
   - **Setup work (Commit 0–7):** Read `../migration/README.md` next
   - **Phase 1+ implementation:** Read `../specs/INDEX.md` next
   - **Just answering a question:** Skip to commands below

## Common First Commands

| User says | You should |
|-----------|------------|
| `lll` | Run `bash .ai/cli/ai status`, parse output, present concisely |
| `sss: <task>` | Create new session via kernel, init THINK/, prompt for clarifications |
| Just a task description | Ask: "Should I `sss:` this task?" or run `lll` first |
| Question about how X works | Read relevant files, answer factually with citations (`file:line`) |
| Request to change code | NEVER write directly. Always go through `sss → vvv → nnn → gogogo` |
| `vvv` | List 5 questions, list files to change, wait for user approval |
| `nnn` | Produce task breakdown with estimates and risks |
| `gogogo` | Implement plan incrementally, run tests, output to DO/dev/ |
| `ddd` | Run deploy checklist; STOP at `decided_by: human` gate |
| `rrr` | Document lessons, update memory |

## Common Mistakes to Avoid

- ❌ Writing code on first response — must `vvv` first
- ❌ Editing `.ai/policies/**` — human-only write
- ❌ Auto-deploying — `ddd` requires human approval (`decided_by: human`)
- ❌ Skipping audit log — every state transition logs to `events.ndjson`
- ❌ Treating yourself as the judge — you propose, verifier decides
- ❌ Inventing new short codes — only 7 exist
- ❌ Reading `references/chatgpt_specs/` as authoritative — it's superseded
- ❌ Copying from `references/shims/upstream-skills/` directly — reference only, must genericize

## When You Need More Info

| Problem | Read |
|---------|------|
| Don't know which spec to read | `../specs/INDEX.md` (entry point, links to everything) |
| Don't know what was decided | `../migration/01_CONTEXT_AND_DECISIONS.md` |
| Don't know how to run kernel | `bash .ai/cli/ai status` (run from repo root) |
| Tests fail | `cd .ai && python3 -m pytest cli/tests` — see specific failure |
| YAML config invalid | `pytest .ai/cli/tests/test_yaml_valid.py` (added Commit 2) |
| Confused about boundaries | Re-read `BOUNDARIES.md` |
| Want history of a decision | `../migration/05_REVIEW_LOG.md` |
| Glossary lookup | `../specs/12_GLOSSARY.md` |

## What You Should NOT Do as Your First Action

- ❌ Suggest copy-paste from <upstream-project> (sanitize first; default = reject)
- ❌ Add a new spec doc (use existing in `docs/specs/`)
- ❌ Bypass `vvv` because "the task is simple"
- ❌ Generate skills for `.claude/skills/` (Phase 8 work; canonical lives in `.ai/shims/`)
- ❌ Run `git push --force` on any branch
- ❌ Modify `.ai/policies/` even "just a small fix"

## You're Ready

If user gave you a clear task: run `vvv` first.
If user is exploring or asking questions: run `lll` to orient yourself.
If unsure: ask.

> **Trinity rule #1: AI proposes; Verifier/Policy/Human decides.**
> **Trinity rule #2: Artifacts are truth, not chat.**
> **Trinity rule #3: When in doubt → NEEDS_HUMAN.**
