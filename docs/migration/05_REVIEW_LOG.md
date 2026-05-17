---
title: "Review Log — Decision History"
status: append-only
last-updated: 2026-05-17
audience: "Anyone asking 'why did we decide X?'"
purpose: "Chronological record of brainstorm + decisions. Append new entries; never edit history."
---

# 5. Review Log

> ทุก decision ใน [`01_CONTEXT_AND_DECISIONS.md`](01_CONTEXT_AND_DECISIONS.md) มีที่มาในเอกสารนี้

## 2026-04-28 — Setup Session

### Round 1: Initial Request
- **User:** "อ่าน TRINITY_LEGACY, สร้าง trinity_v2, copy + reorganize"
- **Claude:** Asked vvv (4 questions): location? scope? init git? handle uncommitted?
- **User answers:**
  - Location: `<workspace-root>/trinity_v2/` ✅
  - Scope: minimal (mini)
  - Init git: yes
  - Uncommitted: skip for now

### Round 2: Initial Migration (Init Commit)
- **Claude executed:** Created folder, copied TRINITY_EVOLUTION/ → docs/specs/ (35 files), copied .ai/cli/ from HEAD (27 files), wrote README.md/CLAUDE.md/AGENTS.md/.gitignore, `git init -b main`, initial commit `868017f`
- **Result:** 70 tracked files, clean tree

### Round 3: Task Summary
- **User:** "สรุป tasks"
- **Claude:** Summarized 14 spec docs (12,800 lines), 10 phases roadmap, 6 sprint plan (12 weeks), 10 locked decisions, critical path: 0.5 → 1 → 2 → 4 → 5

### Round 4: File Inventory + Source Survey
- **User:** "What files are in trinity_v2 + others needed?"
- **Claude:** Mapped 4 categories (🔴 must / 🟡 should / 🟢 missing per spec / ⚪ skip). Proposed 3 options A/B/C.
- **User asked about:** chatgpt_specs (368K), github_examples (229MB).
- **Claude:** Recommended Option C — chatgpt_specs full + github_examples docs only (~5MB)

### Round 5: Sibling Project Survey
- **User asked about:** ai-docs/, browser-cli/, <upstream-project>/. "I remember templates and contracts"
- **Claude surveyed 3 sources:**
  - `ai-docs/` (560K, methodology v3.0)
  - `browser-cli/` (36MB, but 200K of real value — docs/contracts + schemas)
  - `<upstream-project>/` (2.9GB, has .claude/skills/{lll,vvv,nnn,gogogo,rrr})
- **Claude proposed:** 3-tier copy plan with <upstream-project> as Tier 1 essential (this was wrong — see Round 6)

### Round 6: Friend Feedback (Codex tone)
- **User shared friend's analysis:** "Core Runnable + Selective Proven Assets + Sanitized References"
- **Key corrections from friend:**
  - DON'T clone <upstream-project> — security/portability disaster
  - USE TRINITY_LEGACY as core (newer, generic)
  - USE <upstream-project> only for sanitized behavior reference
  - SEPARATE `.ai/shims/` (canonical) from `.claude/skills/` (vendor-generated)
  - ONE source for ai-docs (no duplicate `docs/methodology/`)
- **Claude analyzed:** 85% agreement, flagged 4 unverified assumptions, 6 missing items (license, tests, version, evidence-gathering, retro sampling, Bootstrap Pack)

### Round 7: User Decisions (3 locks)
- **User locked:**
  1. Uncommitted TRINITY_LEGACY files: ✅ copy (override earlier "skip")
  2. B1-B4 <upstream-project> rules: verify first (later proven myth — see Commit 0)
  3. ai-docs canonical: B = `<upstream-project>/ai-docs/` (with structure 01-04 numbered)

### Round 8: Commit 0 Evidence Triage
- **Claude executed evidence collection:**
  - Test 1: `python3 .ai/cli/main.py status` → ImportError (need launcher)
  - Test 2: `pytest cli/tests` → 11/14 pass (3 fail = missing config files)
  - Diff: `<upstream-project>/.ai/policies/safety.yaml` vs `TRINITY_LEGACY/.ai/policies/safety.yaml` → **IDENTICAL** ⭐
  - Grep: B1-B4 references only in archives + 3rd-party PHPExcel libraries
  - Survey: <upstream-project>/ai-docs/ = 11 files, 3 contaminated with <upstream-project>-specific terms
  - Survey: TRINITY_LEGACY uncommitted = ~1700 lines (8 untracked + 2 modified + numbered SANDBOX)
- **Decision impact:** B1-B4 = MYTH → skip port. Refined Commit Plan.

### Round 9: Star's Deep Analysis
- **User shared "Star" (Senior Systems Engineer) deep analysis:**
  - Compared 3 AI proposals (Gemini 7/10, Claude 9/10, Codex 6/10)
  - **Caught what all 3 AIs missed:**
    1. Pyramid of Judgment (4 layers in 02_VERIFIER_SPEC.md)
    2. Hash Chain integrity (events.ndjson genesis)
    3. Loop Budget real values
    4. `decided_by` mandatory on every transition (D10)
    5. 17-week realistic timeline (vs 4-week)
    6. MCP cleanup must wait for browser-cli readiness (HIGH risk)
    7. Additive migration ("Don't break <upstream-project>")
    8. Bootstrap Pack proper usage (install.sh + verify-install.sh)
- **Star's recommended Roadmap:** Phase 0 (Backup) → 0.5 (Bootstrap) → 1 (Tool Contract) → 2 (Brain) → 3-4 (Wire+MCP) → 5-8 (Verifier/Loop/Graph/Shim)

### Round 10: Claude Counter-Response
- **Claude analyzed Star's feedback:**
  - **Accepted 9 catches** (all valid — Claude self-rated 6.5/10, not 9/10)
  - **Push-backed 3 overstatements:**
    1. `install.sh` from Bootstrap Pack — still [Unreleased] in CHANGELOG, not actually exist
    2. "Phase 0 backup at trinity_v2" — wrong context (target is empty, source is the one to backup)
    3. "memory-cli index 240 retros" — memory-cli not implemented yet (Phase 2)
- **Claude refined plan:** Scope reset from "7 commits in 60 min = full migration" to "Phase 0.5 setup runnable + scaffolds per spec — Phase 1-10 are weeks 3-17 of real migration"

### Round 11: Star's Counter-Approval + 2 Enhancements
- **Star acknowledged 3 overstatements** (corrected Claude's score 6.5/10 up to 8.5/10)
- **Star approved Refined Commit Plan**
- **Star added 2 final enhancements:**
  1. YAML Validation Hook (Commit 2) — pytest test for indentation/decided_by/Pyramid/Loop budget integrity
  2. Relative-Path ssot.yaml (Commit 1) — sandbox safety + portability

### Round 12: Plan Documentation (this folder)
- **User:** "บันทึกแผนใน trinity 2 อย่างละเอียดจะได้ไม่มีการเดา"
- **Claude:** Created `docs/migration/` with 5 documents (this is one of them)

## 2026-05-17 — Multi-project Trinity Runtime Decision

### Round 13: Copy-per-project now, central+binding later
- **User:** Asked how Trinity should work across many projects, including opening an AI agent inside a live project, and challenged that central project workspaces were starting to look like copying Trinity into every project.
- **Observed issue:** The current runtime still has commands that depend on one active session pointer. In particular, `ddd` and `close` operate on `current_session` and do not expose a direct `--session` / project selector, so simultaneous projects would collide unless each project has isolated runtime state.
- **Decision:** Lock D15 in [`01_CONTEXT_AND_DECISIONS.md`](01_CONTEXT_AND_DECISIONS.md): current default is copy-per-project for practical isolation; central Trinity core + thin project binding + per-project runtime workspace is Future Implement.
- **Current implementation posture:** A live project may carry its own copied `.ai/` runtime so `current_session`, sessions, artifacts, audit, and command context stay isolated.
- **Future target:** Central core at `<workspace-root>/trinity_v2/`, project-local binding only (`AGENTS.md` managed block, optional `./trinity`, `.trinity/project.yaml`), and central per-project runtime workspace under `<trinity-root>/.trinity/projects/<project_slug>/`.
- **Evidence:** During two-session close cleanup, `ddd` / `close` required changing the active session pointer because the commands were current-session based. This is acceptable inside one runtime, but it is not a safe multi-project concurrency model.
- **Side effects:** Future implementation must first make project-scoped state/session resolution consistent across `sss`, `lll`, `status`, `vvv`, `nnn`, `gogogo`, `ddd`, `rrr`, and `close`; until then, central+binding should not block active project work.

---

## Cross-Reference Map

| Decision | First proposed in | Locked in | Verified by |
|----------|------------------|-----------|-------------|
| D1 (TRINITY_LEGACY base) | Round 6 (friend) | Round 9 (Star) | Round 10 (Claude refined) |
| D2 (<upstream-project> = reference) | Round 6 (friend) | Round 9 (Star) | — |
| D3 (init git) | Round 1 (user) | Round 2 (executed) | — |
| D4 (uncommitted copy) | Round 7 (user) | Round 8 (evidence) | — |
| D5 (B1-B4 myth) | Round 7 (verify) | Round 8 (Commit 0 evidence) | `diff` IDENTICAL |
| D6 (ai-docs B + scrub) | Round 7 (user) | Round 8 (with scrub plan) | Round 11 |
| D7 (.claude/skills via reference) | Round 6 (friend) | Round 9 (Star) | 07_SHIM_SPEC §4 |
| D8 (Pyramid 4 layers) | Round 9 (Star caught) | Round 10 (Claude integrated) | 02_VERIFIER_SPEC §10 |
| D9 (Hash chain genesis) | Round 9 (Star caught) | Round 10 | 00_BLUEPRINT §4 |
| D10 (decided_by mandatory) | Round 9 (Star caught) | Round 10 | 04_GRAPH_SPEC §3 |
| D11 (Loop budget real values) | Round 9 (Star caught) | Round 10 | 03_GOAL_LOOP_SPEC |
| D12 (Relative paths) | Round 11 (Star enhancement) | — | grep checks |

---

## How to append future entries

```markdown
### YYYY-MM-DD — <Round N> — <Title>

- **Actor:** User / Claude / Star / Other AI
- **Input:** what was said/proposed
- **Decision:** what was locked (if any) — link to Decision ID in 01_CONTEXT_AND_DECISIONS.md
- **Evidence:** what verified it (if applicable)
- **Side effects:** which other docs need updating
```

**Rule:** This log is **append-only**. Never edit past entries. If a decision is reversed, append a new entry that supersedes the old (with link).
