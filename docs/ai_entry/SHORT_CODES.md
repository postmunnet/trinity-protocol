---
title: "Short Codes — Canonical Reference"
status: locked
last-updated: 2026-04-28
authority: "This document is the single source of truth for short code semantics. Vendor adapters MUST conform."
---

# Short Codes — Canonical Reference

> Trinity workflow ritual. **7 short codes**, lowercase. ใช้แทนการอธิบายขั้นตอนยาวๆ. ห้าม invent ใหม่.

## The 7 Codes

| Code | Name | What AI does | When to use |
|------|------|--------------|-------------|
| `lll` | Look/List | Show current status: git, sessions, recent changes, memory hints | Start of session, anytime to check state |
| `sss: <task>` | Start Session | Create session capsule under `.ai/sessions/active/<id>/`, snapshot state, init THINK/ folder | Beginning a new task |
| `nnn` | New Plan | Task breakdown with estimates, identify risks, sub-goals if needed | After `sss` (locks scope first) |
| `vvv` | Verify | Confirm understanding — list files to change, ask 5 questions, wait for user | After `nnn` pass (post-plan confirm) |
| `gogogo` | Execute | Implement plan incrementally, run tests, output to `DO/dev/` | After `vvv` approved |
| `ddd` | Done/Deploy | Run deployment checklist, deploy dev/prod, requires `decided_by: human` | After `gogogo` + verification |
| `rrr` | Retrospective | Review what worked/didn't, document lessons, update memory | End of session |

## Standard Sequence (DO NOT SKIP)

```text
[task arrives]
   │
   ▼
sss: <task>          <- session created
   │
   ▼
   THINK             <- read context, scope
   │
   ▼
nnn                  <- plan with estimates
   │  (decided_by: kernel -- nnn_pass verdict)
   ▼
   SANDBOX           <- brainstorm, debate, propose
   │
   ▼
vvv                  <- gate: verify understanding (post-plan confirm)
   │  (decided_by: verifier -- vvv_pass verdict)
   ▼
gogogo               <- execute, output to DO/dev/
   │  (decided_by: verifier — gogogo_complete)
   ▼
   VERIFIED          ← verifier verdict
   │
   ▼  (human gate)
ddd                  ← deploy
   │  (decided_by: human)
   ▼
   DEPLOYED
   │
   ▼
rrr                  ← retro, update memory
   │
   ▼
   DONE
```

Note: graph order is `nnn_pass` (planning passes first, locks scope) -> `vvv_pass` (verification confirms post-plan) -> `gogogo`. The ritual short-codes can be invoked in either typed order; the kernel enforces the graph sequence per `.ai/graphs/standard.yaml` (transitions THINK -> SANDBOX on `nnn_pass`, SANDBOX -> DO on `vvv_pass`).

## Behavior Contract (every short code)

When a user types a short code, the AI agent MUST:

1. **Acknowledge the code** — explicitly say which code is being executed
2. **Check sequence** — if predecessor not done, prompt user (don't silently skip)
3. **Produce artifact** — every code produces files (see "Artifacts per code" below). Chat-only response = wrong
4. **Log to audit** — append event to `.ai/audit/events.ndjson` (hash chain)
5. **Check authority** — if a graph transition is implied with `decided_by: human`, ASK user before transitioning
6. **Stop on uncertainty** — return `NEEDS_HUMAN` rather than guess

## Artifacts per Code

| Code | Required artifacts |
|------|-------------------|
| `lll` | (read-only — no required write, but report MUST cite git/session/memory state) |
| `sss` | `.ai/sessions/active/<id>/THINK/{00_CONTEXT,01_PROMPT,02_SCOPE,03_ACCEPTANCE}.md` + `.state/session_state.json` |
| `vvv` | `<session>/CONTROL/VERIFY.md` (5 mandatory questions answered) |
| `nnn` | `<session>/THINK/CONSENSUS.md` or plan in agreed location |
| `gogogo` | `<session>/DO/dev/<changes>` + test logs + `<session>/CONTROL/META.json` updated |
| `ddd` | `deploy.log` in session + state transition to DEPLOYED |
| `rrr` | `<session>/99_SUMMARY.md` retro + memory entries (Phase 2: `.ai/memory/index.jsonl` updated) |

## Where Implementation Lives

| Layer | Location | Status |
|-------|----------|--------|
| **Spec / contract** | `docs/specs/INDEX.md §7` + this file | ✅ here |
| **Canonical shim (vendor-agnostic)** | `.ai/shims/{lll,vvv,nnn,gogogo,rrr}/SHIM.md` | 📋 Commit 6 |
| **Vendor adapter (auto-generated from canonical)** | `.claude/skills/`, `.cursor/rules/`, `.gemini/...` | 📋 Phase 8 |
| **Reference (<upstream-project>'s actual usage — DO NOT copy directly)** | `references/shims/upstream-skills/` | 📋 Commit 6 |

## Anti-Patterns (NEVER DO)

- ❌ Skip `vvv` and go straight to `gogogo` because "the task is simple"
- ❌ Auto-promote / auto-deploy (must be `decided_by: human`)
- ❌ Hardcode short code logic per vendor — must reference canonical `.ai/shims/`
- ❌ Treat short codes as suggestions — they are workflow gates
- ❌ Run multiple codes in parallel — sequence is strict
- ❌ Output only to chat without producing artifacts

## On Edge Cases

| Situation | Right action |
|-----------|--------------|
| User asks question, no task | Answer factually. No `sss` needed. |
| User says "just fix the typo" | Still go through `sss -> nnn -> vvv -> gogogo` (gates exist for a reason; graph order is nnn_pass then vvv_pass) |
| User says "skip vvv this time" | Politely refuse. Cite this doc. Suggest `lll` if they need quick info. |
| User invokes unknown code | Ask which of the 7 they meant. Do not invent. |
| Session already active | Use existing session. Do not create another (one active per agent). |
| Verifier returns RETRY | Re-do `gogogo` with adjustments — do NOT re-do whole sequence |
| Verifier returns NEEDS_HUMAN | Stop. Surface to user. Wait. |
| Verifier returns DEAD | Stop session. Do not retry. Run `rrr`. |
