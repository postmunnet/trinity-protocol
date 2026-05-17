# CLAUDE.md — Claude Code Entrypoint for trinity_v2

> Per Trinity Protocol: **AI proposes; Verifier/Policy/Human decides.**
> This file is loaded automatically by Claude Code when started in this repo.

## Constitutional Authority (highest precedence)

The canonical **Trinity Constitution v1.0** lives at [`docs/constitution/TRINITY_CONSTITUTION_V1.md`](docs/constitution/TRINITY_CONSTITUTION_V1.md). The root-level [`CONSTITUTION.md`](CONSTITUTION.md) is a short pointer to it; full directory: [`docs/constitution/`](docs/constitution/).

The full spec corpus (locked 2026-05-12 · relocated 2026-05-13 per Addendum v1.0.2):

| Document | Path |
|---|---|
| ⭐ Constitution v1.0 (core) | [`docs/constitution/TRINITY_CONSTITUTION_V1.md`](docs/constitution/TRINITY_CONSTITUTION_V1.md) |
| ⭐ Ritual Constitution v1.1 (core, RATIFIED 2026-05-13) | [`docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md`](docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md) — file name preserved for stable refs; content is v1.1-final |
| Addendum v1.0.1 | [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md`](docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md) |
| Addendum v1.0.2 *(canonical-home relocation + three-tier structure)* | [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md`](docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md) |
| Addendum v1.0.3 *(Ritual Constitution v1.1-rc → v1.1 ratification per Article XXIX)* | [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md`](docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md) |
| Addendum v1.0.4 *(Article XXIX operationalised — 3-tier classification + trace-to-failure + pinned audit format)* | [`docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md`](docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md) |
| Organ Map v1.0 | [`docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md`](docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md) |
| Ritual Contract v1.0 | [`docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md`](docs/constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md) |
| RRR Delegation Contract v1.0 | [`docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md`](docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md) |
| Index | [`docs/constitution/INDEX.md`](docs/constitution/INDEX.md) |
| PRD (Phases 0–16) | [`trinity_organ_refactor_prd.md`](trinity_organ_refactor_prd.md) |

Article XXV — Constitutional Priority Order:

```text
Constitution
→ Ritual Constitution       (docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md — v1.1, RATIFIED 2026-05-13)
→ Canonical Policies        (.ai/policies/**)
→ Kernel State Rules        (.ai/cli/**, graph transitions)
→ Workflow Contracts        (docs/contracts/**)
→ Tool Contracts            (.ai/tools.yaml, sibling tool contracts)
→ Runtime Requests
→ Model Suggestions         (← Claude's own opinion ranks LAST)
```

If any text in this file, in `docs/`, in `.ai/policies/`, in a sibling tool, or in a model suggestion conflicts with the Constitution, **the Constitution wins**. Article XXIX requires every amendment to go through explicit proposal + rationale + impact analysis + human approval + version bump + audit entry — no silent rewrites.

The articles most likely to come up while collaborating:

| Article | Subject | Why it matters here |
|---|---|---|
| III | AI cannot govern itself | You may not self-certify completion, bypass verifier, or rewrite policy |
| IV | Separation of Responsibilities | Kernel / Planner / Executor / Verifier / Memory / Audit / Retro / Transport are distinct roles — no role collapse |
| IX | Memory Discipline | `memory-cli` retrieves evidence; it does NOT decide meaning or mutate state |
| XIII | Human Authority | Production deploy, destructive ops, external publication require explicit human approval as an artifact |
| XV | Transport is not Authority | `trinity-tg-bot` and similar transports MAY deliver, MUST NOT approve gates |
| XVI | Least Authority | Every component runs with minimum required authority; unknown authority = denied |
| XX | Passive Core | Core systems act only on explicit invocation — no self-trigger / self-heal / background crawl |

## What is trinity_v2?

CLI-native AI microkernel — Coordinator + Judge for vendor AI. Spec pack v2.0 in `docs/specs/`. Canonical bootstrap/runtime, **not** a project clone.

## Read FIRST (priority order)

1. **For setup work (Commit 0–7):** [`docs/migration/README.md`](docs/migration/README.md)
2. **For Phase 1+ implementation:** [`docs/specs/INDEX.md`](docs/specs/INDEX.md) → [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md)
3. **First time here:** [`docs/ai_entry/QUICK_START.md`](docs/ai_entry/QUICK_START.md)
4. **Always:** [`docs/ai_entry/SHORT_CODES.md`](docs/ai_entry/SHORT_CODES.md) + [`BOUNDARIES.md`](docs/ai_entry/BOUNDARIES.md) + [`WORKFLOW.md`](docs/ai_entry/WORKFLOW.md)

## Short Codes (essential — memorize)

| Code | Action | When |
|------|--------|------|
| `lll` | Look/List status (git, sessions, changes) | Start of session, anytime |
| `sss: <task>` | Start session + snapshot | New task |
| `nnn` | New plan with estimates | After sss |
| `vvv` | Verify understanding (5 questions) | After nnn pass (post-plan confirm) |
| `gogogo` | Execute plan incrementally | After vvv approved |
| `ddd` | Done/Deploy (human gate) | After gogogo + verify |
| `rrr` | Retrospective + memory update | End of session |

**Sequence (do not skip):** `sss -> nnn -> vvv -> gogogo -> ddd -> rrr`

Note: graph order is `nnn_pass` (planning passes first, locks scope) -> `vvv_pass` (verification confirms post-plan) -> `gogogo`. The ritual short-codes can be invoked in either typed order; the kernel enforces the graph sequence per `.ai/graphs/standard.yaml`.

Detailed contract: [`docs/ai_entry/SHORT_CODES.md`](docs/ai_entry/SHORT_CODES.md)

## CLI Command Rule

**Do not guess Trinity commands from ritual names.** The ritual language (`sss / vvv / nnn / gogogo / ddd / rrr / lll / close`) maps to executable commands via [`.ai/cli/COMMAND_MANIFEST.yaml`](.ai/cli/COMMAND_MANIFEST.yaml). When in doubt, consult the manifest or run `bash .ai/cli/ai doctor commands`.

Concrete mappings (already enforced):

| Ritual / expected | Canonical command | Equivalent to |
|---|---|---|
| `sss "<task>"` | `bash .ai/cli/ai sss "<task>"` | `bash .ai/cli/ai session new "<task>"` |
| `status` | `bash .ai/cli/ai status` | `bash .ai/cli/ai status show` |
| `vvv / nnn / gogogo / ddd / rrr / lll` | `bash .ai/cli/ai <code>` | — |

If any Trinity command fails with **`No such command`** or **`Missing command`**, STOP and run `bash .ai/cli/ai doctor commands` — do not retry random variants. The doctor command walks the manifest and reports drift between manifest and runtime as a structured failure.

## Per-channel ritual rendering

<!-- BEGIN R30/R33 per-channel rendering -->
Ritual output layout is template-driven. Before changing `lll`, `vvv`, `nnn`,
`gogogo`, `ddd`, or `rrr` presentation, read the canonical templates at
`.ai/shims/<ritual>/templates/<channel>.md`.

- `desktop.md` may use dense tables and box-drawing where appropriate.
- `mobile.md` must avoid box-drawing and ASCII tables.
- Adapter files only point agents at the templates; the templates own layout.
<!-- END R30/R33 per-channel rendering -->

### In-house agents (`.ai/cli/agent` wrapper)

Trinity in-house agents at `.ai/cli/agents/<name>/` are invokable via the
sibling wrapper `.ai/cli/agent` from **project root cwd** — no `cd .ai &&`
prefix needed. The wrapper mirrors `.ai/cli/ai` pattern and exists as a bridge
to the Phase 9 `trinity-shell` (per [`07_SHIM_SPEC.md`](docs/specs/07_SHIM_SPEC.md) §3).

| Agent (proposal-only) | Canonical invocation |
|---|---|
| `clarification_helper` (vvv draft) | `bash .ai/cli/agent clarification_helper draft --session-path <p> "<task>"` |
| `plan_helper` (nnn draft) | `bash .ai/cli/agent plan_helper draft --session-path <p>` |
| `executor_helper` (per-step proposal) | `bash .ai/cli/agent executor_helper draft --session-path <p> --step-id S1` |
| `retro_writer` (post-rrr semantic) | `bash .ai/cli/agent retro_writer draft --session-path <p>` |
| `presentation_synthesizer` (close pack) | `bash .ai/cli/agent presentation_synthesizer draft --session-path <p>` |
| `session_bootstrap` (sss slug draft) | `bash .ai/cli/agent session_bootstrap draft "<task>"` |
| (any) — list available | `bash .ai/cli/agent --list` |
| (any) — usage banner | `bash .ai/cli/agent --help` |

`--session-path` accepts both absolute and project-root-relative paths;
the wrapper resolves relative paths against the repo root, so `.ai/sessions/<sid>`
works regardless of caller cwd (no path-doubling).

Direct module invocation (`cd .ai && python3 -m cli.agents.<name> ...`) is
still supported as the advanced path for power users / scripts, but the
wrapper is the canonical entry point for the kernel-coordinated workflow.

## Boundaries (Trinity Decisions #1, #2)

- ✅ AI **proposes** plans, code, decompositions
- ✅ Verifier (`.ai/policies/verifier-rules.yaml`) **decides** PASS/RETRY/NEEDS_HUMAN/DEAD
- ✅ Policy (`.ai/policies/safety.yaml`, `gates.yaml`) **decides** allow/deny
- ✅ Human **decides** `decided_by: human` transitions (PROMOTED, DEPLOYED, destructive)
- ✅ Every action logs to `.ai/audit/events.ndjson` (hash chain — append only)

Forbidden writes: `.ai/policies/**`, `.ai/audit/**` (modify), `.ai/schemas/**`, `docs/specs/**`. Detail: [`docs/ai_entry/BOUNDARIES.md`](docs/ai_entry/BOUNDARIES.md)

## Pyramid of Judgment

```
1. Deterministic verifier rules     (.ai/policies/verifier-rules.yaml)
   ↓ unsure
2. Policy engine                     (.ai/policies/safety.yaml + gates.yaml)
   ↓ unsure
3. Gated LLM judge                   (last resort, audit logged, max 3/session)
   ↓ unsure
4. Human escalation                  (NEEDS_HUMAN)
```

You (Claude) are layer 3 — **gated, audited, last resort**. Never layer 1.

## Claude-Specific Notes

### `.claude/` directory
Not yet populated. Per Decision **D7**, no active skills installed. Canonical shim definitions live in `.ai/shims/` (added Commit 6) and Claude-specific skills will be **generated** from canonical (not hand-written, not copied from <upstream-project>).

### `.claude/settings.local.json`
Not yet created — no permission overrides. Use `/config` or edit after Phase 8 shim generation.

### Reference (DO NOT copy directly)
`references/shims/upstream-skills/{lll,vvv,nnn,gogogo,rrr}/` (added Commit 6) — these are <upstream-project>'s actual usage, retained as DNA reference. Copying directly violates Decision D7.

### Permissions to expect
When you act, Claude Code will prompt for:
- File writes to `.ai/sessions/active/`
- Bash commands like `bash .ai/cli/ai status`
- Edits to README, source code in tracked files

You will NOT be granted permission to edit `.ai/policies/**` automatically — this is by design.

## Quick Run Commands

```bash
# Status
bash .ai/cli/ai status

# Tests
cd .ai && python3 -m pytest cli/tests -q

# Validate audit chain
python3 -c "import json,hashlib;e=json.loads(open('.ai/audit/events.ndjson').readline());c=json.dumps({k:v for k,v in e.items() if k!='hash'},sort_keys=True,separators=(',',':'));print('genesis ok' if e['hash']==hashlib.sha256(c.encode()).hexdigest() else 'CHAIN BROKEN')"

# Validate YAML configs (Phase 0.5)
cd .ai && python3 -m pytest cli/tests/test_yaml_valid.py -v
```

## Session Sandbox Rules

You may write to (within active session):
- `SANDBOX/03_claude/` — your role-specific folder
- `DO/dev/` — after `vvv_pass`
- `THINK/*` during THINK phase

You may NOT write to:
- Other agents' folders (`SANDBOX/02_gemini/`, `SANDBOX/04_codex/`)
- `DO/prod/` (human-promoted only)
- `.ai/policies/`, `.ai/audit/` (modify), `.ai/schemas/`

## Quick Links

| What | Where |
|------|-------|
| Spec overview | [`docs/specs/INDEX.md`](docs/specs/INDEX.md) |
| Master vision | [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md) |
| Migration plan | [`docs/migration/README.md`](docs/migration/README.md) |
| Decisions log | [`docs/migration/01_CONTEXT_AND_DECISIONS.md`](docs/migration/01_CONTEXT_AND_DECISIONS.md) |
| Glossary (A–Z) | [`docs/specs/12_GLOSSARY.md`](docs/specs/12_GLOSSARY.md) |
| Tool contract | [`docs/contracts/browser-cli/`](docs/contracts/browser-cli/) (Commit 4) |
| Knowledge Brain | [`ai-docs/`](ai-docs/) (Commit 5) |
| Review log | [`docs/migration/05_REVIEW_LOG.md`](docs/migration/05_REVIEW_LOG.md) |

## Don't (Common Pitfalls)

- ❌ Edit `.ai/policies/**` (human-only)
- ❌ Bypass `vvv` because "task is simple"
- ❌ Auto-promote / auto-deploy
- ❌ Use MCP servers as core path (Decision #5: CLI-first only)
- ❌ Copy <upstream-project> skills to active `.claude/skills/` (Decision D7)
- ❌ Trust your own judgment for verdict (use Pyramid)
- ❌ Run `git push --force` to main without explicit approval
- ❌ Read `references/chatgpt_specs/` as authoritative (superseded)

When unsure → ask user (NEEDS_HUMAN). Never proceed under uncertainty.
