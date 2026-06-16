---
title: "Context & Locked Decisions"
status: locked
last-updated: 2026-05-17
audience: "Anyone executing or auditing the trinity_v2 migration"
---

# 1. Context & Locked Decisions

## 1.1 ทำไมต้องสร้าง trinity_v2

**ปัญหา:** TRINITY_LEGACY เป็น kernel development ปนกับ:
- legacy artifacts (archive/, sessions เก่า, *_advice.md)
- uncommitted v2 work (artifacts.py, session_naming.py)
- runtime kernel components (loop.py, state.py, graph.py, audit.py)
- legacy FSM reference (kernel.py — kept only for smoke tests)
- spec pack ใหม่ (TRINITY_EVOLUTION/) ที่ยัง drift จาก code

**ทางแก้:** trinity_v2 = **clean canonical bootstrap/runtime repo** ที่:
1. ใช้ TRINITY_EVOLUTION เป็น source of truth ของ spec
2. ใช้ TRINITY_LEGACY/.ai/ HEAD + uncommitted v2 work เป็น runtime base
3. ใช้ <upstream-project>, browser-cli, ai-docs เป็น **reference เท่านั้น** (ไม่ใช่ active code)
4. ตรงกับ Per-project Trinity instance layout ใน `INDEX.md §5.3`

## 1.2 Source Projects (4 แหล่ง)

| Source | Path | Role | Use as |
|--------|------|------|--------|
| TRINITY_LEGACY | `<workspace-root>/TRINITY_LEGACY/` | Trinity kernel development | **Core base** (HEAD + uncommitted v2 work) |
| <upstream-project> | `<workspace-root>/<upstream-project>/` | Production user (PHP/Smarty) | **Behavior reference** (sanitized only) |
| browser-cli | `<workspace-root>/browser-cli/` | Reference DNA tool | **Tool contract reference** (docs + schema only) |
| ai-docs | `<workspace-root>/ai-docs/` | Methodology Framework v3.0 | **Knowledge Brain canonical** (generic) |

## 1.3 Locked Decisions (15)

### D1 — Core source = TRINITY_LEGACY (ไม่ใช่ <upstream-project>)
**Why:** TRINITY_LEGACY มี v2 work ที่ใหม่กว่า (numbered SANDBOX, session_naming, loop/artifacts/state modules) และไม่ปน hardcoded paths/credentials เหมือน <upstream-project>
**How to apply:** ทุกครั้งที่ต้องเลือกระหว่าง 2 source สำหรับ kernel runtime → ใช้ TRINITY_LEGACY (Loop + Graph + State + Audit)
**Source:** Star's analysis §5.1, Claude's refined plan, INDEX.md §3

### D2 — <upstream-project> = behavior reference, ไม่ใช่ canonical code
**Why:** <upstream-project> มี FTP creds, prod paths (`<user-home>/.../<upstream-project>/`), Smarty templates, deploy scripts ที่ project-specific. Clone = security + portability disaster
**How to apply:** Copy จาก <upstream-project> ต้องผ่าน sanitization ก่อน. Default = ไป `references/` ไม่ใช่ active code path
**Source:** Star's analysis §6, Claude's flag, Gemini's "Sanitization Protocol"

### D3 — Init git ที่ trinity_v2 (standalone repo)
**Why:** trinity_v2 ต้องเป็น canonical bootstrap repo อิสระจาก TRINITY_LEGACY
**How to apply:** `git init -b main`, ไม่ link กับ TRINITY_LEGACY/.ai/ git history
**Source:** User decision (turn 4)

### D4 — Uncommitted v2 work ที่ TRINITY_LEGACY เอามาด้วย
**Why:** session_naming.py, loop.py (runtime kernel), artifacts.py + numbered SANDBOX templates คือ source of truth จริงตาม spec — HEAD เก่ากว่า ไม่ตรง spec; kernel.py is kept only as legacy FSM reference for smoke tests.
**How to apply:** Commit 3 = direct file copy จาก working tree (ไม่ต้อง commit ที่ TRINITY_LEGACY ก่อน)
**Source:** User decision (after Star/Gemini brainstorm)
**Files:** ดู `02_EVIDENCE_TRIAGE.md §4`

### D5 — B1-B4 = MYTH, ไม่ port จาก <upstream-project> policies
**Why:** evidence จาก Commit 0 ยืนยัน `<upstream-project>/.ai/policies/safety.yaml` IDENTICAL กับ TRINITY_LEGACY/.ai/policies/safety.yaml. B1-B4 references มีแค่ใน `archive/legacy_docs/` + 3rd-party PHPExcel libraries
**How to apply:** ใช้ TRINITY_LEGACY/.ai/policies/safety.yaml ตรงๆ ไม่ต้อง patch <upstream-project> rules
**Source:** Commit 0 evidence (`diff` shows IDENTICAL)

### D6 — ai-docs source = <upstream-project>/ai-docs/ (Option B) พร้อม scrub
**Why:** <upstream-project>/ai-docs/ มี structure ที่ดี (`01-CORE_PROTOCOL/`, `02-STANDARDS/`, `03-PROCESS/`, `04-MEMORY/`) — battle-tested มากกว่า generic /yai_project/ai-docs/
**How to apply:** Copy 11 ไฟล์ + scrub 3 ไฟล์ที่มี <upstream-project>-specific keywords (`SAFETY_GATES.md`, `ENV_VARS.md`, `ROLLBACK_PROCEDURES.md`)
**Risk acknowledged:** Star + Gemini + Claude เตือนว่าเสี่ยง <upstream-project> contamination — ผู้ใช้ยืนยันยังเลือก B (override)
**Mitigation:** Sanitization บังคับ — replace `<upstream-project>/smarty/deploy_dev_order/FTP_CRED` ด้วย placeholders
**Source:** User decision (turn ที่ Star/Gemini brainstorm จบ)

### D7 — `.claude/skills` ห้าม install เป็น active ทันที
**Why:** <upstream-project> skills hardcode project context (Smarty, deploy, FTP). Trinity ต้อง vendor-agnostic ตาม Decision #4 (CLI-first) + 07_SHIM_SPEC §4.2
**How to apply:** Copy ไป `references/shims/upstream-skills/` เป็น reference. สร้าง `.ai/shims/{lll,vvv,nnn,gogogo,rrr}/` เป็น canonical (vendor-agnostic) แยกต่างหาก
**Source:** Star's analysis §2.1, Claude's flag, 07_SHIM_SPEC

### D8 — Pyramid of Judgment 4 ชั้น (ใส่ใน verifier-rules.yaml)
**Why:** หัวใจของ `02_VERIFIER_SPEC.md` — AI ห้ามเป็น sole judge. Layer 3 (LLM judge) ต้อง gated + audit log
**How to apply:** Commit 2 — `verifier-rules.yaml` ต้องมี structure 4 layers (deterministic → policy → LLM gated → human)
**Source:** Star caught this miss, 02_VERIFIER_SPEC.md §10

### D9 — Hash Chain Genesis Event (events.ndjson เริ่มต้นถูกต้อง)
**Why:** Trinity audit = tamper-evident hash chain. ถ้า genesis ผิด → chain ไร้ค่า
**How to apply:** Commit 1 — `audit/events.ndjson` ต้องมี genesis event แรกที่:
- `prev_hash: "0"`
- `hash: <sha256 of canonical event JSON>`
- `type: "genesis"`
- `details.trinity_version`, `details.spec_pack`
**Source:** Star's analysis §4.2, 00_BLUEPRINT.md §4

### D10 — `decided_by` ทุก transition ใน graphs/*.yaml
**Why:** Decision #10 ของ 10 Committed Decisions. AI may PROPOSE, ห้าม DECIDE transitions
**How to apply:** Commit 2 — `graphs/standard.yaml` + `graphs/deploy.yaml` ทุก transition ระบุ `decided_by: {verifier|policy|human|kernel}`
**Source:** 04_GRAPH_SPEC.md §3, Star's miss-list

### D11 — Loop Budget มีค่าจริง ไม่ใช่ stub เปล่า
**Why:** ป้องกัน Infinite Hallucination Loop. Phase 5 safety mechanism
**How to apply:** Commit 2 — `policies/loop-budget.yaml` ต้องมี `max_iterations`, `max_duration_minutes`, `max_tool_calls`, `checkpoint_every` พร้อม escalation rule
**Source:** Star's miss-list, 03_GOAL_LOOP_SPEC.md

### D12 — ssot.yaml ใช้ Relative Paths + Placeholders
**Why:** Sandbox safety + portability. ห้ามมี absolute path เช่น `<user-home>/...`
**How to apply:** Commit 1 — ssot.yaml มี `${project_root}` placeholder, runtime detect, ทุก path เป็น relative ภายใน trinity_v2
**Source:** Star's enhancement §3.2, 00b_BOOTSTRAP_PACK.md template

### D13 — Plugin Tool Architecture (Sibling + Registry)
**Why:** ผู้ใช้ตั้งใจให้ tools (browser-cli, memory-cli, ...) เป็น "plugin ที่เสียบเข้ามาตามงาน" + "วิธีเชื่อมต่อใช้งานไม่เปลี่ยนแปลง" แม้ tool version เปลี่ยน. การ vendor ทุก tool เข้า trinity_v2 ทำให้ canonical bootstrap บวมและ coupling แรงเกินไป. Linux philosophy — kernel ≠ tools; tools register & speak a stable contract.
**How to apply:**
- Tools live OUTSIDE `.ai/` (sibling directory or external path)
- `.ai/tools.yaml` = registry (Commit 4.5 — first entry: browser-cli)
- `.ai/policies/tools-policy.yaml` = path resolution + tier permissions (Commit 4.5)
- `docs/contracts/<tool>/` = **frozen contract baseline** per tool — version-pinned snapshot ที่ kernel ใช้ verify (Commit 4 = browser-cli baseline)
- Tool implementation evolves freely; kernel ตรวจ `contract_version` field, ไม่ใช่ tool version
- หาก contract มี breaking change → bump `contract_version`, สร้าง folder ใหม่ใน `docs/contracts/`
**Source:** vvv session 2026-04-30 (user answer: "เยอะเหมือน plugin" + "วิธีเชื่อมต่อไม่เปลี่ยน"); aligns with `01_TOOL_CONTRACT.md` §16, `00_BLUEPRINT.md` userland model, Decision #5 (CLI-first)

### D14 — Cost Rule: kernel-internal hot-path bypasses subprocess boundary even when capability is sibling-shaped
**Why:** D13 says "tools live outside the kernel". But a *deterministic, zero-deps* capability that the kernel calls **per-step / per-event** loses ~50–100ms × N to subprocess spawn for zero correctness benefit. The verifier rules engine is the prototype: 10–50 calls per session × ~50ms spawn = ~2.5s of pure overhead per session for a pure dict-lookup against YAML. Sibling extraction makes sense when the boundary buys SDK isolation, audit boundary, or lifecycle decoupling — not when it just adds spawn cost.
**How to apply:**
- A capability MUST satisfy BOTH rules to extract as a subprocess sibling:
  1. **Capability rule (D13):** needs network / LLM / external API → sibling
  2. **Cost rule (D14, this entry):** kernel calls it bounded times (not per-step / per-event) **OR** the subprocess boundary buys real isolation (deps, audit, lifecycle) → sibling
- If only D13 says "sibling" but D14 says "called too often to justify subprocess" → **keep in-kernel as a module + thin CLI subcommand wrapper**.
- Examples (see also `TODO.md` Tier 6 "Stays in kernel" table):
  - `verify-cli` — pure dict lookup, called 10–50× per session → kernel module + `ai verify` subcommand
  - `forbidden_diff` (basic) — git diff + path regex, called per-rrr → kernel module
  - `timeline-cli` (ASCII-only) — data already in `core/audit.py` → `ai timeline` subcommand
  - `debate-cli` / `plan-cli` / `judge-cli` — LLM-using, bounded calls → sibling (D13 + D14 both say sibling)
**Source:** Session J rrr (2026-05-01, sibling-vs-kernel classification turn). Implementation evidence: `cli/core/verifier.py` exists alongside `ai verify` subcommand; spec `02_VERIFIER_SPEC.md §4` carries an R22 implementation note explaining the divergence from the original "subprocess sibling" framing. The cost rule was previously documented only in `TRINITY_LEGACY/TODO.md` Tier 6; promoted here so it's citable from spec text and future retros.

### D15 — Multi-project runtime: copy-per-project now, central+binding later
**Why:** Immediate multi-project work needs isolated `current_session`, sessions, artifacts, audit, and command context per project. The current CLI still has paths that resolve through one active `current_session` pointer under the active Trinity runtime, and commands such as `ddd` / `close` do not yet accept a project-scoped session selector. Moving to a central runtime before state/session resolution is fully project-scoped creates collision risk when two projects are active at the same time.

**Current default (accepted temporary model):**
- Copy the Trinity runtime into each project that needs to run independently.
- Each project owns its own `.ai/` runtime state, sessions, audit, command manifest, and local agent entry files.
- This is explicitly a pragmatic default for usable isolation, not the final architecture.

**Future target (do not block current work):**
- Keep Trinity core in one central runtime, for example `<workspace-root>/trinity_v2/`.
- Keep only a thin project binding inside each project:
  - `AGENTS.md` / vendor entry managed block
  - optional `./trinity` wrapper
  - `.trinity/project.yaml`
- Store per-project runtime workspace centrally, not by copying the core:
  - `<trinity-root>/.trinity/projects/<project_slug>/state/status.json`
  - `<trinity-root>/.trinity/projects/<project_slug>/sessions/`
  - `<trinity-root>/.trinity/projects/<project_slug>/artifacts/`
  - `<trinity-root>/.trinity/projects/<project_slug>/retros/`
- Store memory as one SQLite file per project:
  - `<trinity-root>/.memory/db/<project_slug>.db`

**How to apply now:**
- If opening an AI agent inside any live project today, use that project's copied Trinity runtime so `current_session` cannot collide with other projects.
- Do not treat the central+binding experiment as required for day-to-day project work yet.
- When implementing the future target, first make state/session resolution project-scoped across `sss`, `lll`, `status`, `vvv`, `nnn`, `gogogo`, `ddd`, `rrr`, and `close`; no command should require manually switching a global pointer.

**Migration acceptance for future implementation:**
- Two projects can run `sss -> vvv -> nnn -> gogogo -> ddd -> rrr -> close` concurrently without sharing `current_session`.
- `trinity project current`, `trinity status`, `trinity lll`, `trinity ddd`, and `trinity close` resolve the same project from the current working directory or explicit binding.
- Project files contain only thin binding files; Trinity core code is not copied for the future central mode.
- Backward compatibility remains: existing copy-per-project installs keep working until an explicit migration command is run.

**Source:** User decision on 2026-05-17 after multi-project discussion: accept copy-per-project for now; record central core + project binding + per-project runtime workspace as Future Implement. See `05_REVIEW_LOG.md` 2026-05-17 entry.

## 1.4 Out-of-scope (ไม่ทำใน trinity_v2 setup นี้)

| Item | ทำไมไม่ทำตอนนี้ | ไปทำที่ phase ไหน |
|------|----------------|-------------------|
| MCP cleanup (Playwright/Morphllm/Sequential) | HIGH risk — รอ browser-cli พิสูจน์ครบ 13 tools ก่อน | <upstream-project> migration Phase 4 (สัปดาห์ 8-10) |
| memory-cli index 240 retros | memory-cli ยังไม่ implement | Phase 2 (สัปดาห์ 5-6) |
| verify-cli active runtime | verify-cli ยังไม่ implement | Phase 4 (สัปดาห์ 7-8) |
| Trinity loop runtime | Phase 5 spec | Phase 5 (สัปดาห์ 9-10) |
| install.sh from Bootstrap Pack | ยัง [Unreleased] ใน CHANGELOG | Phase 0.5 implementation |
| Backup branch ที่ trinity_v2 | trinity_v2 พึ่งสร้าง ไม่มีอะไร backup | สำหรับ <upstream-project> migration เท่านั้น |
