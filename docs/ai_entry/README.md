---
title: "AI Entry — Shared Reference"
status: locked
last-updated: 2026-04-28
audience: "AI agents (Claude / Codex / Cursor / Gemini / Warp / Aider)"
purpose: "Canonical content linked from every root entry file. Single source of truth for short codes, workflow, and boundaries."
---

# AI Entry — Shared Reference

> Root entry files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `WARP.md`) are vendor-tailored thin layers. The **canonical content** lives here. If your entry file conflicts with a doc in this folder, **this folder wins**.

## Documents

| Doc | Read when |
|-----|-----------|
| [`QUICK_START.md`](QUICK_START.md) | First session in this repo |
| [`SHORT_CODES.md`](SHORT_CODES.md) | Always — 7 short codes definitions |
| [`WORKFLOW.md`](WORKFLOW.md) | Before `sss/vvv/nnn/gogogo` (sequence) |
| [`BOUNDARIES.md`](BOUNDARIES.md) | Before any write/exec/transition action |

## Reading order on first visit

```
QUICK_START.md → SHORT_CODES.md → BOUNDARIES.md → WORKFLOW.md
```

## Why this folder exists

Without a shared canonical reference, each vendor entry file would drift, and short code behavior would diverge. Trinity is **vendor-agnostic** (Decision #4 — CLI-first only) so all AI agents must work from the same definitions.

## Cross-references

- Spec pack: [`../specs/INDEX.md`](../specs/INDEX.md)
- Migration plan: [`../migration/README.md`](../migration/README.md)
- Canonical shim definitions: `.ai/shims/` (added Commit 6)
- Reference (<upstream-project>'s actual usage): `references/shims/upstream-skills/` (added Commit 6)
