---
title: "Contributing to Trinity OS"
audience: Contributors, developers, reviewers
last-updated: 2026-04-28
---

# Contributing to Trinity OS

> Thank you for considering a contribution! 🌌
>
> Trinity OS is built on disciplined collaboration — read this doc before opening PRs/issues.

---

## TL;DR

```
1. Read INDEX.md (15 min)
2. Read 00_BLUEPRINT.md (vocabulary + decisions)
3. Use Trinity workflow (lll → vvv → nnn → gogogo → rrr)
4. Follow Tool Contract for new tools
5. Write structured retro for every change
6. Submit PR with evidence (artifacts + tests)
```

---

## 0. Before You Start

### 0.1 Required Reading

| Document | Why |
|----------|-----|
| [`INDEX.md`](INDEX.md) | Master overview — vocabulary, components |
| [`00_BLUEPRINT.md`](00_BLUEPRINT.md) | Architecture decisions (the 10 commitments) |
| [`12_GLOSSARY.md`](12_GLOSSARY.md) | Look up terms when unsure |
| [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) | Inspirations + what we don't use (and why) |

### 0.2 Required Understanding

You should be able to answer:
- What is the difference between Knowledge Brain and Reasoning Engine?
- Why is MCP not core path?
- Why does AI propose but not decide transitions?
- What is the Pyramid of Judgment?
- What is the role of `events.ndjson`?

If unclear → read [`INDEX.md`](INDEX.md) §4 (Vocabulary)

---

## 1. Setup Development Environment

### 1.1 Prerequisites

```bash
# Required
bash 4+ or zsh
Python 3.10+
Node.js 18+
Git
SQLite 3.30+

# Recommended
jq           # NDJSON parsing
tmux         # Multi-pane workflow

# At least one AI vendor harness
Claude Code  # https://claude.com/claude-code (recommended)
# OR Codex CLI / Cursor / Gemini CLI
```

### 1.2 Clone & Setup

```bash
# Clone
git clone <trinity-ultimat-repo> ~/code/trinity
cd ~/code/trinity

# Read setup
less TRINITY_EVOLUTION/INDEX.md
```

### 1.3 Install Existing Tools (for testing)

```bash
# browser-cli (reference implementation)
git clone <browser-cli-repo> ~/code/browser-cli
cd ~/code/browser-cli && npm install
npx playwright install chromium

# Run tests
node tests/harness.js
node tests/golden.js
```

---

## 2. The Trinity Workflow (Eat Your Own Dogfood)

> 🍴 We use Trinity to build Trinity. All contributions follow the same workflow.

### 2.1 For Every Contribution

```bash
# In your AI tool (Claude Code recommended)
> lll                                 # Status check
> vvv "Add feature X"                  # Verify (5 questions, search past)
> nnn                                  # Plan
> gogogo                               # Execute (after plan approval)
> rrr                                  # Retrospective
```

### 2.2 vvv Discipline (mandatory)

Before any code change, answer 5 questions:
1. What is the actual file path?
2. Which files handle this?
3. Expected behavior?
4. Evidence?
5. User confirmed?

**Skipping vvv = invalid contribution** (per [`ai-docs/CORE_RULES.md`](../ai-docs/CORE_RULES.md))

### 2.3 Plan Format (`nnn` output)

Your `02_PLAN.md` should include:
- Goal + risk level
- Files to modify (with reasons)
- Implementation steps
- Testing strategy
- Rollback plan

---

## 3. Contribution Types

### 3.1 Spec Documentation Updates

**For typos/clarifications:**
```bash
# Quick fix
vim TRINITY_EVOLUTION/<doc>.md
git commit -m "docs: fix typo in <doc>"
```

**For substantive changes:**
- Open issue first (discuss intent)
- Reference spec section being changed
- Update CHANGELOG.md
- Bump doc version in frontmatter

### 3.2 New CLI Tool

**MUST follow [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md):**

#### Pre-flight Checklist
- [ ] Read TOOL_CONTRACT.md (1,298 lines)
- [ ] Choose action namespace (e.g., `mytool.*`)
- [ ] Define commands list (verbs + tier classification)
- [ ] Identify external deps (libraries, services)

#### Implementation Checklist
- [ ] Single binary entry point
- [ ] 4 execution modes (single-cmd, REPL, pipe, run-file)
- [ ] Universal CLI flags (`--config`, `--run-id`, `--log-file`, etc.)
- [ ] Response envelope (with `action` field per v1.1)
- [ ] NDJSON logging
- [ ] Policy tier enforcement
- [ ] `--list-commands` / `--describe` / `--health` discovery

#### Documentation Checklist
- [ ] README.md (user-facing intro)
- [ ] docs/ARCHITECTURE.md
- [ ] docs/COMMAND_CONTRACT.md
- [ ] docs/AI_AGENT_GUIDE.md
- [ ] docs/USER_GUIDE.md
- [ ] schema/config.schema.json
- [ ] schema/response-v1.schema.json

#### Testing Checklist
- [ ] tests/harness.js (unit, no deps, < 5s)
- [ ] tests/golden.js (integration, < 60s)
- [ ] Schema validation tests
- [ ] `trinity-contract-test <tool>` passes (Bronze+)

#### Registration
- [ ] Add to `.ai/tools.yaml`
- [ ] Update spec pack INDEX if architecturally significant

### 3.3 Trinity Kernel Changes

**Higher bar — these affect everyone:**

- [ ] Issue + design discussion FIRST
- [ ] Backward compatibility plan
- [ ] Migration script if breaking
- [ ] Update affected specs (00, 02-07)
- [ ] Update CHANGELOG.md
- [ ] Bump kernel version (semver)

### 3.4 Spec Architecture Changes

**Highest bar — affects all of Trinity:**

- [ ] RFC-style proposal in issue
- [ ] Discuss with all maintainers
- [ ] Document new decision in `11_RELATED_PROJECTS.md` (alternatives considered)
- [ ] Major version bump (e.g., v2 → v3 if breaking)
- [ ] Migration guide

---

## 4. Coding Standards

### 4.1 General

- **Match existing style** in the file/folder
- **Read code before writing** (vvv discipline)
- **Tests required** for tool/kernel changes
- **No silent failures** — exit code + error envelope

### 4.2 Per Language

#### Python (Trinity kernel)
- Python 3.10+
- Use `typer` for CLI (existing pattern)
- Type hints required
- Black formatter, isort
- pytest for tests

#### Node.js (CLI tools)
- Node 18+ (or Bun if performance critical)
- Plain JS or TypeScript
- No mandatory framework — match `browser-cli` pattern
- Prefer minimal deps
- `node tests/harness.js` for unit
- `node tests/golden.js` for integration

#### Markdown (Specs)
- GFM (GitHub Flavored Markdown)
- Frontmatter required (yaml — title/version/status)
- Cross-references via relative links
- Mermaid diagrams welcome (08_DIAGRAMS.md style)

### 4.3 Commit Messages

```
<type>: <short description>

<optional body>

<optional footer — references>
```

**Types:**
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `spec:` — spec pack change
- `tool:` — CLI tool change
- `kernel:` — Trinity kernel change
- `refactor:` — code refactor
- `test:` — test only
- `chore:` — tooling/build

**Examples:**
```
feat(memory-cli): add hybrid search

Implements ChromaDB integration for Phase 9.
Maintains backward compat with FTS5.

Closes #42
```

---

## 5. Pull Request Process

### 5.1 Before Opening PR

- [ ] Branch from `main` (or `develop` if applicable)
- [ ] Run `vvv` discipline (verify before changing)
- [ ] Implement following plan (`nnn` output)
- [ ] All tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md entry added
- [ ] Retro written (`rrr` output) — attach to PR

### 5.2 PR Description Template

```markdown
## Goal
[What problem does this solve?]

## Verify (vvv) Reference
[Link to verify-report.json or session ID]

## Plan (nnn) Reference  
[Link to 02_PLAN.md or session]

## Changes
- File X: reason
- File Y: reason

## Evidence
- [ ] Tests pass: [output]
- [ ] Manual verification: [steps]
- [ ] Screenshots (if UI): [link]
- [ ] Performance impact: [measurements]

## Risk Level
- [ ] Low — additive, reversible
- [ ] Medium — modifies existing behavior
- [ ] High — breaking change

## Rollback Plan
[How to revert if needed]

## Retro (rrr) Highlights
[Lessons learned, mistakes avoided]
```

### 5.3 Review Process

- **Minimum 1 reviewer** for tool/spec changes
- **Minimum 2 reviewers** for kernel changes
- **Minimum 3 reviewers** for spec architecture changes
- Reviewers must verify:
  - [ ] vvv was done
  - [ ] Tests cover the change
  - [ ] Docs updated
  - [ ] No skipped contract requirements

### 5.4 After Merge

- Squash merge for clean history (or rebase if preferred)
- Tag release if version bump
- Update `.ai/tools.yaml` if new tool registered
- Run `trinity audit verify-chain` (no corruption)

---

## 6. Issue Guidelines

### 6.1 Issue Types

#### Bug Report
```markdown
## Description
[What happened?]

## Expected
[What should have happened?]

## Reproduce
1. ...
2. ...

## Evidence
- Logs: [paste or link]
- Screenshots: [link]
- Environment: [OS, versions]

## Verifier Verdict (if applicable)
[PASS/RETRY/NEEDS_HUMAN/DEAD]
```

#### Feature Request
```markdown
## Problem
[What need does this address?]

## Proposed Solution
[Your idea]

## Alternatives Considered
[What else did you think about?]

## Impact
- Phase: [which phase does this affect]
- Components: [kernel / shim / tools / brain]
- Breaking: [yes/no]
```

#### RFC (for spec changes)
```markdown
## Summary
[1-paragraph TL;DR]

## Motivation
[Why now?]

## Detailed Design
[Specific changes to which docs]

## Drawbacks
[Why might this be wrong?]

## Alternatives
[Other approaches considered]

## Migration Path
[How to transition]

## Unresolved Questions
[Open items]
```

---

## 7. Code of Conduct

### Be:
- ✅ Respectful and constructive
- ✅ Evidence-based in disagreements
- ✅ Patient with newcomers
- ✅ Clear in communication

### Don't:
- ❌ Skip vvv discipline
- ❌ Bypass policy gates
- ❌ Accept "AI says it works" without evidence
- ❌ Auto-merge sensitive changes
- ❌ Tamper with audit logs (events.ndjson)

---

## 8. Getting Help

### Where to Ask

| Question type | Where |
|--------------|-------|
| **How does X work?** | Read [`12_GLOSSARY.md`](12_GLOSSARY.md) → relevant spec |
| **Why this design?** | [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §6 (alternatives considered) |
| **Bug in existing code?** | Open issue with reproduction |
| **New idea?** | Open RFC issue |
| **Operational question?** | [`09_DEPLOY_GUIDE.md`](09_DEPLOY_GUIDE.md) §8 (troubleshooting) |
| **Migration question?** | [`10_UPSTREAM_AUDIT.md`](10_UPSTREAM_AUDIT.md) §3 |

---

## 9. Recognition

### Hall of Fame (contributors)

Listed in `NOTICE` file (if Apache-2.0 adopted) or:
- Spec pack acknowledgments ([`CHANGELOG.md`](CHANGELOG.md))
- Tool README credits

### Special Thanks

- **yai** — vision, <upstream-project> production data, browser-cli
- **Friend brainstorm** — 10 decision commitments
- **Anthropic** — Claude Code 1.6%/98.4% insight
- **Soul-Brews-Studio** — Oracle Framework + arra-oracle-v3
- All open source inspirations

---

## 10. Frequently Asked Questions

### Q: Do I need vendor AI to contribute?

**A:** Recommended (best for Trinity workflow), but not strictly required. You can contribute purely manually if needed.

### Q: Can I contribute without writing code?

**A:** Absolutely:
- Documentation improvements
- Real lessons (post-incident retros)
- Spec review and feedback
- Translation (e.g., to other languages)
- Use case examples

### Q: How long does PR review take?

**A:**
- Typo: 1 day
- Tool change: 3-7 days
- Kernel change: 7-14 days
- Spec architecture: 14-30 days (RFC process)

### Q: What if I disagree with a decision (e.g., MCP rejection)?

**A:** Open an RFC. Decisions can be revisited with evidence. See [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §6 for current alternatives considered.

### Q: Can I fork and create variants?

**A:** Yes (MIT license). Please:
- Credit Trinity OS in your fork
- Don't claim spec ownership
- Share back improvements if you can

### Q: How do I become a maintainer?

**A:** 
- Sustained quality contributions (3+ months)
- Show understanding of architecture
- Help review others' PRs
- Existing maintainers vote

---

## 11. Quick Reference

### First-time contributor checklist

- [ ] Read INDEX.md
- [ ] Read 00_BLUEPRINT.md
- [ ] Set up dev environment
- [ ] Pick a "good first issue" or small typo fix
- [ ] Run vvv discipline
- [ ] Submit PR with retro

### Returning contributor cheat sheet

```bash
# Daily flow
lll                  # status
vvv "task"           # verify (mandatory)
nnn                  # plan
gogogo               # execute
rrr                  # retro

# Tool dev
trinity-contract-test <tool>  # compliance check

# Verify Trinity itself
trinity audit verify-chain
trinity self-test
```

### Spec change shortcuts

```bash
# Find term
grep -r "term" TRINITY_EVOLUTION/

# Update CHANGELOG
vim TRINITY_EVOLUTION/CHANGELOG.md

# Bump version
vim <doc>.md   # update frontmatter version field
```

---

## 12. License

By contributing, you agree your contributions are licensed under the same license as the project (currently MIT — see [`LICENSE_DECISION.md`](LICENSE_DECISION.md)).

For substantial contributions, you may be asked to sign a Contributor License Agreement (CLA) if/when project switches to Apache-2.0.

---

## See also

- [`INDEX.md`](INDEX.md) — Master overview
- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Architecture
- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) — Tool development standards
- [`LICENSE_DECISION.md`](LICENSE_DECISION.md) — License rationale
- [`CHANGELOG.md`](CHANGELOG.md) — Version history

---

> 🌌 **Welcome to Trinity OS — let's build deterministic AI workflow together.**
