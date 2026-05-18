---
title: "Related Projects, Inspirations & Attributions"
subtitle: "Where Trinity OS came from · what we learned from · what we don't use (and why)"
version: 1.0.0
status: reference
last-updated: 2026-04-28
---

# Related Projects, Inspirations & Attributions

> **เอกสารนี้บันทึกทุกโปรเจคที่ influence Trinity OS** — inspiration, dependencies, alternatives considered, licenses, attribution
>
> ถ้า specs อื่น reference ภายนอก — มาดูที่นี่เพื่อเข้าใจ context

---

## 0. Status

- **Audit date:** 2026-04-28
- **Coverage:** All projects mentioned across 13 spec docs + brainstorming sessions
- **Categories:** 7 types (inspiration, direct dep, reference impl, alternative, vendor host, future, research)

---

## 1. Project Family (Internal — workspace-root/)

### 1.1 TRINITY_LEGACY (this project)

```
Path:     <workspace-root>/TRINITY_LEGACY/
Status:   Production v0.5.1 → Evolution v2 (this spec pack)
Role:     Source of truth for kernel + specs
Contains: .ai/ runtime, sessions, archive, references, TRINITY_EVOLUTION/
```

**Internal relationships:**
- `TRINITY_LEGACY/.ai/cli/` = **legacy v1 kernel (deprecated 2026-05-01 per R21)** — see directory README; active kernel is the trinity_v2 sibling
- `TRINITY_LEGACY/TRINITY_EVOLUTION/` = v2 specs (this folder)
- `TRINITY_LEGACY/archive/` = legacy AI docs, old sessions
- `TRINITY_LEGACY/references/github_example/` = external AI harness study (see §3)

---

### 1.2 ai-docs (the original methodology)

```
Path:     <workspace-root>/ai-docs/
Version:  v3.0 (2025-11-27)
Status:   Reference framework
Role:     Methodology source — workflow ritual, anti-patterns, real lessons
License:  MIT
```

**Key features:**
- 5-step workflow (lll → vvv → nnn → gogogo → rrr)
- 22 retrospectives + 25+ incidents informed v3
- Multi-tool routing (Claude/Codex/Gemini/Antigravity)
- 12 real lessons with ROI metrics
- SYSTEM_STATUS.md pattern (session context)

**Influence on Trinity OS v2:**
- Short codes preserved verbatim
- Workflow ritual = foundation of Trinity loop
- Real lessons = first batch for memory-cli index
- Templates = Bootstrap Pack templates

**Differences:**
- ai-docs = static markdown methodology
- Trinity OS = runtime kernel + tools + memory + audit

---

### 1.3 <upstream-project> (production project)

```
Path:     <workspace-root>/<upstream-project>/
Type:     E-commerce (PHP+Smarty+MySQL)
Status:   Production (renamed to member-vbth3.com on 2026-04-25)
Role:     Largest user of Trinity v1 → migration target for v2
```

**Why important:**
- Production-tested 6+ months
- 240 retrospectives in `.claude/retrospectives/` (Knowledge Brain seed data!)
- 14 real_lessons in `ai-docs/real_lessons/`
- Evolved ai-docs structure (01-CORE_PROTOCOL/, etc.)
- Per-command CONTRACTS (ai-docs/protocols/*_CONTRACT.md)

**Migration:** ดู [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md)

---

### 1.4 browser-cli (reference implementation)

```
Path:     <workspace-root>/browser-cli/
Version:  v0.1.2 (2026-04-25)
Status:   Production
License:  (project-internal)
Role:     Reference DNA for ALL Trinity CLI tools
```

**Key features (= Tool Contract reference):**
- stdin/stdout JSON contract (v1/v2)
- Schema-locked responses
- NDJSON structured logging
- Policy tiers (safe/normal/aggressive)
- Helpers YAML
- CDP mode (connect external Chrome)
- Tmux integration (5-pane God Team)
- Recorder (bidirectional action log)

**Influence on Trinity OS:**
- 9 design rules in TOOL_CONTRACT.md derived from browser-cli
- All future CLI tools clone its layout
- Wraps Playwright (replaces Playwright MCP per decision #5)

**Files imported into spec pack:**
- `docs/ARCHITECTURE.md` → influenced `01_TOOL_CONTRACT.md`
- `docs/COMMAND_CONTRACT.md` → format used by all tools
- `docs/RESPONSE_SCHEMA.md` → envelope schema
- `docs/POLICY_TIERS.md` → tier convention
- `docs/RECORDER_CONTRACT.md` → future tool feature

---

### 1.5 TRINITY_EVOLUTION (this spec pack)

```
Path:     TRINITY_LEGACY/TRINITY_EVOLUTION/
Status:   v1.0 (current)
Role:     v2 specs (Phase 0-10) + master overview
Contents: 13 documents, 10,956 lines, 336 KB
```

This is what you're reading now.

---

## 2. Direct Inspirations (Philosophical / Architectural)

### 2.1 Oracle Framework

```
Repo:        github.com/Soul-Brews-Studio/oracle-framework
Version:     2.0.0 (Jan 2026)
Type:        Philosophical framework + folder convention
License:     (check repo)
Status:      Public · Active
```

**Core concepts borrowed:**
- **"Nothing is Deleted"** → influenced supersession chain (memory-cli §5)
- **"Patterns Over Intentions"** → influenced verifier (deterministic vs intent)
- **"External Brain, Not Command"** → influenced Knowledge Brain definition
- **Trace → Distill → Awaken flow** → mirrored in Trinity loop

**ψ/ structure (their folder convention):**
```
ψ/
├── active/        (research, ephemeral)
├── memory/        (resonance, learnings, retrospectives, logs)
├── inbox/         (communication)
├── writing/       (drafts)
├── lab/           (experiments)
└── ...
```

**What Trinity adopted:**
- Append-only memory model
- Permanent retrospectives → memory-cli indexes
- Multi-model allocation pattern (different LLM per task)

**What Trinity didn't adopt:**
- Mystical/philosophical naming (we use technical: Knowledge Brain not "soul")
- "Mirror only — never auto-execute" → Trinity has hard gates instead
- Free-form retros → Trinity enforces schema

---

### 2.2 arra-oracle-v3 (production memory MCP)

```
Repo:        github.com/Soul-Brews-Studio/arra-oracle-v3
Version:     v26.4.19-alpha.7 (CalVer)
Type:        TypeScript MCP server (memory layer)
License:     BUSL-1.1
Status:      Public · Alpha · Active
```

**Tech stack inspirational:**
- Bun runtime
- SQLite + FTS5 (full-text)
- ChromaDB (vector embeddings)
- Drizzle ORM (type-safe)
- Hono (HTTP framework)
- Hybrid search (FTS5 + vector with 50/50 merge + 10% overlap boost)

**What Trinity adopted (memory-cli):**
- SQLite + FTS5 for Phase 2
- Document/FTS/tags/supersession schema
- Hybrid ranking algorithm (Phase 9 future)
- Indexer pattern (walk dirs, parse markdown, chunk)

**What Trinity didn't adopt:**
- ❌ MCP protocol (decision #5 — CLI-first only)
- ❌ HTTP API as core (Phase 10 future, not Phase 2)
- ❌ Federation (OracleNet) — too early
- ❌ 2D/3D vector visualization — nice-to-have

**License note:** BUSL-1.1 has commercial restriction (4 years) — Trinity's memory-cli is independent implementation, not derivative

---

## 3. Reference Implementations (External — Studied)

ที่ `TRINITY_LEGACY/references/github_example/`:

### 3.1 claw-code

```
Repo:    ultraworkers/claw-code
Type:    Claude Code clone
Studied: Architecture of Claude Code-style harness
```

### 3.2 oh-my-claudecode

```
Repo:    ?/oh-my-claudecode
Type:    Claude Code customization framework (skills + commands)
Studied: Extension pattern for Trinity Shim (Phase 8)
Influence: skills/ directory structure + slash command bindings
```

**Key learning:** Don't replicate Claude Code — extend it via skills/hooks (this is the Trinity Shim approach)

### 3.3 oh-my-codex (OMX)

```
Repo:    yeachan-heo/oh-my-codex
Type:    Codex CLI customization
Studied: AGENTS.md pattern + Codex-specific extensions
```

### 3.4 oh-my-openagent

```
Repo:    ?/oh-my-openagent
Type:    Generic agent framework (built on OpenClaw fork)
Studied: Tool-agnostic harness extension
```

### 3.5 openclaude

```
Repo:    ?/openclaude
Type:    Open-source coding-agent CLI (multi-provider)
Provider support: OpenAI, Gemini, GitHub Models, Codex OAuth, Codex, Ollama, Atomic Chat
Studied: Multi-vendor harness pattern
```

**Key learning:** Building full harness requires multi-provider abstraction — too much scope for v0.1, hence Trinity Shim approach

---

## 4. Vendor Hosts (Required for Trinity Shim)

### 4.1 Claude Code (Anthropic)

```
URL:        https://claude.com/claude-code
Type:       AI coding harness (CLI + IDE extensions)
Models:     Claude Sonnet 4.5, Opus 4.x, Haiku 4.x
Status:     Production · Vendor product
```

**Used by Trinity:**
- Primary vendor harness (recommended)
- Skills/hooks extension model = Trinity Shim Phase 8 target
- MCP support (we don't use external MCP per decision #5)
- Built-in Read/Write/Edit/Bash/Glob/Grep (replaces Morphllm MCP)

**Trinity-specific integrations:**
- `.claude/skills/` for slash commands
- `.claude/hooks/` for audit
- `.claude/settings.local.json` permissions

### 4.2 Codex CLI (OpenAI)

```
URL:        npm install -g @openai/codex-cli
Type:       AI coding CLI
Models:     GPT-4 / GPT-5 family
Status:     Production · Vendor product
```

**Used by Trinity:**
- Secondary vendor harness (fast generation)
- AGENTS.md instruction file = adapter point
- 3-mode approval workflow

### 4.3 Gemini CLI (Google)

```
URL:        npm install -g @google/gemini-cli
Type:       AI CLI with 1M context
Models:     Gemini 3 Pro (default), Claude Sonnet (alternative)
Status:     Production · Vendor product
```

**Used by Trinity:**
- Research-heavy tasks (1M context)
- Google Search integration
- GEMINI.md adapter point
- Free tier available

### 4.4 Cursor

```
URL:        https://cursor.com
Type:       IDE-based AI harness
Status:     Production · Vendor product
```

**Used by Trinity:**
- IDE-based workflow
- `.cursor/rules/` MDC files = adapter point

### 4.5 Warp

```
URL:        https://www.warp.dev
Type:       Terminal with AI integration
Status:     Production
```

**Used by Trinity:**
- WARP.md → CLAUDE.md symlink (lightweight adapter)

### 4.6 Antigravity (Google)

```
Type:       Browser automation + async agents (Google product)
Status:     Mentioned in ai-docs/tools/ANTIGRAVITY.md
```

**Trinity stance:** Not used directly — browser-cli replaces (per decision #5)

---

## 5. Direct Dependencies (Trinity Tools)

### 5.1 Playwright

```
Used by:    browser-cli
Version:    ^1.59.0
License:    Apache-2.0
URL:        https://playwright.dev
```

**Why:** Best-in-class browser automation; CDP support; cross-browser

### 5.2 SQLite (with FTS5)

```
Used by:    memory-cli (Phase 2)
Version:    3.30+ required (FTS5 included)
License:    Public domain
```

**Why:** Local-first, zero-config, FTS5 for full-text search

### 5.3 ChromaDB

```
Used by:    memory-cli (Phase 9 future)
URL:        https://www.trychroma.com
License:    Apache-2.0
```

**Why:** Local-first vector DB, easy Python/JS bindings, hybrid-search ready

**Status in Trinity:** Phase 9 — defer until FTS5 proves insufficient

### 5.4 Bun (consideration)

```
URL:        https://bun.sh
Type:       Fast JS runtime + package manager
Status:     Considered for memory-cli (vs Node)
```

**Status:** Open question — memory-cli might use Bun (fast, native TS) vs Node (browser-cli precedent)

### 5.5 Python (3.10+)

```
Used by:    Trinity kernel (.ai/cli/)
Library:    Typer (CLI framework)
```

**Why:** <upstream-project> production uses Python; preserve continuity

### 5.6 wp-cli (PHP, official)

```
Used by:    wordpress-cli (future)
URL:        https://wp-cli.org
License:    MIT
```

**Why:** Official WordPress CLI — wordpress-cli wraps it (not replaces)

---

## 6. Alternatives Considered (Not Chosen)

### 6.1 MCP (Model Context Protocol) — REJECTED for core

```
Status:     ❌ Not core path (decision #5)
Reason:     Vendor lock-in (Claude Code only)
Alternative: CLI-first stdin/stdout JSON
```

**External MCP servers REJECTED:**
- `mcp__playwright__*` → use browser-cli
- `mcp__morphllm-fast-apply__*` → use vendor's Read/Write/Edit
- `mcp__sequential-thinking__*` → use ai-docs ritual

**KEPT:** `mcp__ide__executeCode` (vendor IDE bridge — not external)

### 6.2 Full AI Harness (like openclaude) — DEFERRED

```
Status:     ❌ Not in v0.1
Reason:     Too much scope (Anthropic uses dozens of devs × 2 years)
Alternative: Use vendor harness + Trinity Shim (Phase 8)
```

### 6.3 LangGraph / AutoGen / Devin — DIFFERENT APPROACH

```
Type:       Python-native agent frameworks
Status:     Not used (different architecture)
```

**Why not:**
- LangGraph = in-process, Python-only — Trinity = CLI-native, multi-language
- AutoGen = group chat agents — Trinity = single-leader hierarchy
- Devin = closed-source SaaS — Trinity = open architecture

**What we learned from them:**
- Graph-based state machine pattern (LangGraph) → influenced Phase 6
- Multi-agent dispatch (AutoGen) → future (god-team-cli)
- Goal tree decomposition (Devin) → influenced Phase 5

### 6.4 xstate / pytransitions (graph engine choice)

```
Status:     Open question (Phase 6)
Candidates: xstate (TS), pytransitions (Python), custom (~200 LOC)
```

**Decision pending** — likely custom for Trinity simplicity

### 6.5 ChromaDB vs Pinecone vs Weaviate vs Qdrant

```
Chosen:     ChromaDB (Phase 9)
Reason:     Local-first, easy setup, sufficient scale (~1M docs)
```

**Rejected:**
- Pinecone — cloud-only, $$$
- Weaviate — feature-rich but complex
- Qdrant — Rust, learning curve
- pgvector — perf lower than dedicated VDB

### 6.6 Drizzle ORM (arra-oracle uses)

```
Status:     Considered for memory-cli — likely not used
Reason:     Trinity prefers raw SQL + simple schema (less abstraction)
```

### 6.7 Hono (arra-oracle uses)

```
Status:     Future option for HTTP bridge (Phase 10)
Reason:     Lightweight, edge-ready
```

---

## 7. Industry References (Research / Inspiration)

### 7.1 Anthropic's "Claude Code" Architecture Insight

**Key quote:**
> *"1.6% of the codebase is AI decision logic, 98.4% is deterministic harness"*

**Source:** Public comments from Anthropic (Boris Cherny, Cat Wu, etc.)

**Influence:** Foundational insight — Trinity OS positioned as 100% deterministic harness leveraging vendor AI for reasoning

### 7.2 Unix Philosophy (Eric S. Raymond, 1978)

**Influence:** 
- "Do one thing well" → CLI tools as organs
- "Pipes for composability" → stdin/stdout JSON
- "Programs as filters" → tool envelope pattern

**Reference:** "The Unix Philosophy" — Mike Gancarz / "The Cathedral and the Bazaar" — ESR

### 7.3 Microkernel Architecture (L4, QNX, Mach)

**Influence:**
- Small kernel + userspace services → Trinity kernel + CLI tools
- IPC = clear boundary → stdin/stdout JSON
- Trust nothing, validate every IPC → schema-locked envelope

### 7.4 Plan 9 from Bell Labs

**Influence:**
- Everything is a file → tools.yaml registry pattern
- Namespace flexibility → action namespace (`tool.verb`)

### 7.5 Emacs / Lisp Machines

**Influence:**
- Persistent state + extensions → ai-docs as substrate
- Live system → resumable sessions

### 7.6 Smalltalk Image / REPL-driven dev

**Influence:**
- Persistent runtime state → loop_state.json + checkpoints

### 7.7 Cognition AI (Devin team) — Public posts

**Key insight:**
- "Don't run multi-agent in parallel" — context fragility
- "Implicit decisions break agents" — must be explicit

**Influence:** Trinity → explicit `decided_by` in graph transitions

---

## 8. Cross-References Within Spec Pack

### 8.1 References Inside Specs

| Spec | References |
|------|-----------|
| `00_BLUEPRINT.md` | All other specs |
| `00b_BOOTSTRAP_PACK.md` | TOOL_CONTRACT, ai-docs templates |
| `01_TOOL_CONTRACT.md` | browser-cli reference (heavy) |
| `02_VERIFIER_SPEC.md` | LOOP_SPEC, GRAPH_SPEC |
| `03_GOAL_LOOP_SPEC.md` | VERIFIER, GRAPH, MEMORY_CLI |
| `04_GRAPH_SPEC.md` | VERIFIER, LOOP |
| `05_MEMORY_CLI_SPEC.md` | TOOL_CONTRACT, browser-cli, retro-cli |
| `06_RETRO_CLI_SPEC.md` | MEMORY_CLI, VERIFIER |
| `07_SHIM_SPEC.md` | All other specs (integration layer) |
| `08_DIAGRAMS.md` | Visual for all |
| `09_DEPLOY_GUIDE.md` | All operational |
| `10_UPSTREAM_AUDIT.md` | All for migration |
| `INDEX.md` | All (entry point) |

---

## 9. License Summary

| Project | License | Trinity Use |
|---------|---------|-------------|
| ai-docs (yai) | MIT | Direct (code/concepts) |
| browser-cli (yai) | (internal) | Direct (reference impl) |
| Oracle Framework | (check repo) | Inspiration only |
| arra-oracle-v3 | BUSL-1.1 | Inspiration only (independent impl) |
| Playwright | Apache-2.0 | Direct dep (browser-cli) |
| SQLite | Public domain | Direct dep (memory-cli) |
| ChromaDB | Apache-2.0 | Direct dep (Phase 9 future) |
| wp-cli | MIT | Direct dep (wordpress-cli future) |
| Hono | MIT | Optional dep (Phase 10) |
| Drizzle ORM | Apache-2.0 | Optional dep |
| xstate | MIT | Optional graph engine |
| Bun | MIT | Optional runtime |

**Trinity OS itself:** TBD (recommend MIT or Apache-2.0)

---

## 10. Attribution Statement (for spec pack)

```text
Trinity OS is informed by:

1. Anthropic Claude Code's architectural insights (1.6%/98.4% pattern)
2. Oracle Framework's append-only memory philosophy
3. arra-oracle-v3's hybrid search implementation
4. Unix philosophy and microkernel architecture (L4, Plan 9)
5. Cognition AI's lessons on agent context fragility
6. yai's own ai-docs methodology (v3.0)
7. browser-cli's CLI-native design DNA
8. <upstream-project> production lessons (240 retrospectives, 14 incidents)
9. 5 reference AI harness implementations 
   (claw-code, oh-my-claudecode, oh-my-codex, oh-my-openagent, openclaude)

Trinity OS does NOT directly use:
- Any external MCP server (CLI-first decision)
- LangGraph / AutoGen / Devin (different architecture)
- Cloud-managed vector DBs (local-first)

All vendor harnesses (Claude Code, Codex, Cursor, Gemini, Warp) are 
external products used as hosts via the Trinity Shim adapter pattern.
```

---

## 11. Future Integrations (Watch List)

Projects to watch for future integration:

### 11.1 oh-my-claudecode evolution

```
Status:     Active (Building in Public)
Watch for:  Stable skill/hook API → Trinity Shim Phase 8
```

### 11.2 Anthropic's Computer Use API

```
Status:     Beta (as of 2026-04)
Watch for:  Native browser automation alternative to browser-cli
Decision:   browser-cli still preferred (CLI-first, vendor-agnostic)
```

### 11.3 OpenAI Agents SDK / Swarm

```
Status:     OpenAI's agentic framework
Watch for:  Pattern for god-team-cli (multi-agent dispatch)
```

### 11.4 Continue.dev / Aider

```
Type:       Open-source AI coding tools
Watch for:  CLI-native patterns (validate Trinity approach)
```

### 11.5 ChromaDB Cloud

```
Status:     Hosted ChromaDB (paid)
Watch for:  Federation across Trinity instances (Phase 9+)
```

### 11.6 Anthropic MCP Spec Evolution

```
Status:     Spec evolving
Trinity stance: MCP not core, but optional bridge in Phase 10+
```

---

## 12. References by Document Mention Count

(Audit of how often each project is mentioned across 13 spec docs)

| Project | Mentions | Coverage |
|---------|----------|----------|
| Claude Code | 67+ | Heavy — primary vendor host |
| Codex CLI | 59+ | Heavy — secondary vendor |
| Gemini CLI | 64+ | Heavy — research vendor |
| Cursor | 41+ | Medium — IDE host |
| FTS5/SQLite | 56+ | Heavy — memory-cli |
| Playwright | 23+ | Medium — browser-cli backend |
| ChromaDB | 8 | Light — Phase 9 future |
| Warp | 10 | Light — terminal host |
| wp-cli | 3 | Light — wordpress-cli future |
| Oracle Framework | 0* | **GAP** — should add (this doc fixes) |
| arra-oracle-v3 | 0* | **GAP** — should add (this doc fixes) |
| openclaude | 2 | Light — reference study |
| claw-code | 1 | Very light — reference study |
| oh-my-claudecode | 0* | **GAP** — important for Phase 8 |
| Antigravity | 0 | Not used (decision) |

*Mentioned in this doc (`11_RELATED_PROJECTS.md`) for first time

---

## 13. Project Glossary (Acronyms)

| Acronym | Full | Where used |
|---------|------|-----------|
| OMX | oh-my-codex | Reference |
| MCP | Model Context Protocol | Anthropic / Claude Code |
| CLI | Command Line Interface | Trinity tools |
| FTS5 | Full-Text Search v5 | SQLite |
| BUSL | Business Source License | arra-oracle-v3 |
| SOC2 | Service Organization Control 2 | Compliance target |
| ISO27001 | ISO Information Security | Compliance target |
| CDP | Chrome DevTools Protocol | browser-cli |
| ABI | Application Binary Interface | Tool Contract |
| POSIX | Portable Operating System Interface | Inspiration for Tool Contract |
| TUI | Terminal User Interface | Future |
| NDJSON | Newline-Delimited JSON | Audit log |
| BM25 | Best Match 25 (ranking) | FTS5 |
| ROI | Return on Investment | Real lessons metric |
| SDK | Software Development Kit | Phase 10 |

---

## 14. Open Questions / Action Items

### 14.1 To Verify

- [ ] Confirm Oracle Framework license (commercial use ok?)
- [ ] Confirm BUSL-1.1 implications (4-year clock starts when?)
- [ ] Confirm browser-cli license (set if not set)
- [ ] Confirm Trinity OS license (recommend MIT/Apache-2.0)

### 14.2 To Add Cross-References

- [ ] Update `00_BLUEPRINT.md` to link this doc
- [ ] Update `01_TOOL_CONTRACT.md` to mention browser-cli explicitly
- [ ] Update `05_MEMORY_CLI_SPEC.md` to credit arra-oracle-v3 inspiration
- [ ] Update `07_SHIM_SPEC.md` to credit oh-my-claudecode pattern

### 14.3 To Document Further

- [ ] Detail comparison: Trinity vs LangGraph (architectural)
- [ ] Detail comparison: Trinity vs OpenAI Agents SDK
- [ ] Document upgrade path from arra-oracle (if user wants migrate)

### 14.4 To Engage

- [ ] Open issue/discussion on Oracle Framework repo (if relevant)
- [ ] Star/follow oh-my-claudecode for Phase 8 evolution
- [ ] Follow Anthropic blog for Claude Code architecture posts

---

## 15. Quick Reference

### Inspirations TL;DR

```text
Anthropic Claude Code   → "harness > model" insight
Oracle Framework        → append-only memory + supersession
arra-oracle-v3          → hybrid search (FTS5 + vector)
Unix / microkernel      → CLI + IPC + small kernel
Plan 9                  → uniform interface
Cognition AI            → no implicit decisions
ai-docs (yai)           → workflow ritual + retros
browser-cli (yai)       → CLI-native DNA
<upstream-project> (yai)            → 240 retros + production lessons
```

### Direct Dependencies TL;DR

```text
Required:   Python 3.10+, Node 18+, Git, SQLite 3.30+
Per-tool:   Playwright (browser-cli), FTS5 (memory-cli)
Future:     ChromaDB (Phase 9), Bun (maybe)
```

### Vendor Hosts TL;DR

```text
Primary:    Claude Code (best skills/hooks)
Secondary:  Codex CLI (fast generation)
Tertiary:   Gemini CLI (research, 1M context), Cursor (IDE)
Optional:   Warp (terminal)
```

### NOT used TL;DR

```text
❌ External MCP servers (CLI-first only)
❌ Full AI harness rebuild (use vendor's)
❌ Cloud vector DB (local-first)
❌ LangGraph/AutoGen (different architecture)
❌ Antigravity (browser-cli replaces)
```

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §9 — MCP stance details
- [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) §15 — arra-oracle pattern reference
- [`07_SHIM_SPEC.md`](07_SHIM_SPEC.md) — vendor harness extension (Phase 8)
- `TRINITY_LEGACY/references/github_example/` — actual repo clones for study

## Changelog

- **v1.0.0 (2026-04-28)** — Initial cross-reference + attribution document. Fills gap where Oracle Framework, arra-oracle-v3, github_example/* were inspirations but lacked formal reference in spec pack.
