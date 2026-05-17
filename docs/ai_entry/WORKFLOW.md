---
title: "Workflow — Standard Sequence"
status: locked
last-updated: 2026-05-14
authority: "Defines session lifecycle, state transitions, and per-state actions. Conforms to .ai/graphs/standard.yaml (added Commit 2). Visual Reference section appended 2026-05-14 reflecting Ritual Constitution v1.1 (ratified 2026-05-13) + Addendum v1.0.4 + transcript-at-close."
---

# Workflow — Standard Sequence

> How short codes connect into a session lifecycle. **All transitions have explicit `decided_by` authority** (Decision #10).

## Session Lifecycle (overview)

```
[start]
   │
   ▼
  sss: <task>     ─── creates .ai/sessions/active/<id>/
   │              ─── decided_by: kernel (mechanical)
   ▼
   THINK          ─── 00_CONTEXT, 01_PROMPT, 02_SCOPE, 03_ACCEPTANCE
   │
   ▼
  nnn             ─── plan: task breakdown, estimates, risks
   │              ─── decided_by: kernel (nnn_pass)
   ▼
   SANDBOX        ─── 00_BRAINSTORM → 01_DEBATE → 02_gemini/03_claude/04_codex
   │
   ▼
  vvv             ─── verify understanding, list files, ask 5 questions
   │              ─── decided_by: verifier (vvv_pass; post-plan confirm)
   ▼
  gogogo          ─── execute plan; output → DO/dev/
   │              ─── decided_by: verifier (gogogo_complete)
   ▼
   VERIFIED       ─── verifier checks artifacts via .ai/policies/verifier-rules.yaml
   │
   ▼ (human gate)
  ddd (promote)   ─── code moves to DO/prod/ (ready for deploy)
   │              ─── decided_by: human, require_human_approval: true
   ▼
   PROMOTED
   │
   ▼ (human gate)
  ddd (deploy)    ─── deploy to production
   │              ─── decided_by: human, require_human_approval: true
   ▼
   DEPLOYED
   │
   ▼
  rrr             ─── retro, lessons learned, memory update
   │              ─── decided_by: kernel
   ▼
   DONE
```

## State Definitions

| State | What it means | Allowed writes |
|-------|---------------|----------------|
| `READY` | Kernel ready, no active session | (none) |
| `THINK` | Reading context, scoping work | `THINK/*.md` only |
| `SANDBOX` | Multi-AI brainstorm/debate | `SANDBOX/*` only |
| `DO` | Implementing | `DO/dev/` only (NOT prod) |
| `VERIFIED` | Verifier passed | (no write — gate) |
| `PROMOTED` | Code in prod-ready folder | `DO/prod/` (after human approval) |
| `DEPLOYED` | Live in production | deploy log only |
| `RETRO` | Documenting lessons | `99_SUMMARY.md`, memory |
| `DONE` | Session closed, archived | (no write — terminal) |

## Per-State Actions

### THINK
- AI reads existing code, asks questions
- Scopes work (what's in, what's out)
- Defines acceptance criteria
- **Output:** `00_CONTEXT.md`, `01_PROMPT.md`, `02_SCOPE.md`, `03_ACCEPTANCE.md`

### SANDBOX (numbered v2 layout — added Commit 3)
- `00_BRAINSTORM/` — initial idea space, no commitment
- `01_DEBATE/` — agents critique each other's proposals (round_1, round_2, round_3, verdict)
- `02_gemini/` — Gemini's analysis/proposal/research
- `03_claude/` — Claude's analysis/proposal/critique
- `04_codex/` — Codex's implementation/patch.diff/proposal

Each agent writes ONLY in its own folder. Cross-pollination happens in `01_DEBATE/`.

### DO/dev
- Implementation in dev sandbox
- Tests run incrementally
- Each iteration logged to `events.ndjson`
- **No prod writes here**

### VERIFIED
- Verifier reads artifacts (DO/dev/*, test logs)
- Applies rules from `.ai/policies/verifier-rules.yaml`
- Returns: PASS / RETRY / NEEDS_HUMAN / DEAD
- Pyramid: deterministic → policy → LLM gated (last) → human

### PROMOTED → DEPLOYED
- Both transitions are `decided_by: human`
- Human inspects DO/dev/ → approves promotion
- Human approves deploy → kernel runs deploy command
- Deploy log appended to session + audit

### RETRO
- Document: what worked, what didn't, lessons
- Update memory (current RRR contract: `memory-cli index`)
- Archive session (move active/ → archive/)

## Authority Hierarchy (per `decided_by`)

```
verifier   → 80% of automated transitions (deterministic rules)
policy     → safety/budget enforcement (allow/deny)
human      → sensitive ops (PROMOTED, DEPLOYED, destructive)
kernel     → mechanical entry/exit, retry, cleanup
```

**AI is NOT in this hierarchy.** AI proposes; the hierarchy decides.

## Budget per Session

ดู `.ai/policies/loop-budget.yaml` (added Commit 2):

```yaml
default_budget:
  max_iterations: 20
  max_duration_minutes: 30
  max_tool_calls: 100
  checkpoint_every: 5
escalation:
  on_iterations_exceeded: NEEDS_HUMAN
  on_duration_exceeded: NEEDS_HUMAN
  on_tool_calls_exceeded: NEEDS_HUMAN
```

When budget hit → escalate to human, do NOT silently continue.

## Multi-Session Rules

- **One active session per agent** (multiple agents can run parallel sessions if isolated)
- Active session under `.ai/sessions/active/<id>/`
- Closed session moves to `.ai/sessions/archive/<YYYY-MM>/<id>/`
- Session id format: defined in `docs/SESSION_NAMING.md` (added Commit 3)

## On Failure / Retry

| Verdict | What to do |
|---------|-----------|
| `PASS` | Continue to next state |
| `RETRY` | Re-do current step (max retries per loop-budget). Do NOT re-do whole sequence |
| `NEEDS_HUMAN` | Stop. Surface to user with full context. Wait |
| `DEAD` | Stop session. Run `rrr`. Do NOT retry |

## Spec References

- `docs/specs/04_GRAPH_SPEC.md` — graph definition format
- `docs/specs/03_GOAL_LOOP_SPEC.md` — loop + budget
- `docs/specs/02_VERIFIER_SPEC.md` — verdict types + Pyramid
- `.ai/graphs/standard.yaml` — actual graph (added Commit 2)

---

# Visual Reference (v1.1 + Addendum v1.0.4)

> Appended 2026-05-14. Reflects Ritual Constitution v1.1 (RATIFIED 2026-05-13 per Addendum v1.0.3), Article XXIX operationalisation (Addendum v1.0.4), and transcript-at-close integration (close.py snapshots Claude / Codex / Gemini conversation transcripts at archive time).

## Full Pipeline

```
    STATE              RITUAL                 DECIDED BY    EMITS
    ─────              ──────                 ──────────    ─────

   (no session)
        │
        │  ai sss "<task-slug>"                kernel       • session.created
        ▼  scaffold THINK/DO/CTRL/SANDBOX                   • sss.invoked
   ┌──────────┐
   │  READY   │
   └──────────┘
        │
        │  ai vvv --answer 1=… --answer 5=…    kernel       • vvv.invoked
        ▼  (5 questions: Goal / Scope /                     • vvv.proposed
        │   Constraint / Acceptance / Risk)                 • vvv.passed
        │                                                   • THINK/01_PROMPT.md
   ┌──────────┐
   │  THINK   │
   └──────────┘
        │
        │  ai nnn --plan-envelope <path>       kernel       • nnn.invoked
        ▼  (budget check + scope render)                    • plan.budget_checked
        │                                                   • nnn.passed
        │                                                   • THINK/02_SCOPE.md
   ┌──────────┐                                             • THINK/03_ACCEPTANCE.{md,yaml}
   │   DO     │                                             • .state/plan.json
   └──────────┘
        │
        │  ai gogogo                           kernel +     • gogogo.invoked
        ▼  walks plan.json step-by-step;       verifier     • step_started/step_passed (×N)
        │  verifier checkpoint per step                     • graph.transition (×N)
        │                                                   • gogogo.completed
   ┌──────────┐
   │ VERIFIED │  ◄── code/docs landed; gate before promote
   └──────────┘
        │
        │  ai ddd --target=dev                 ★ HUMAN ★    • ddd.invoked
        ▼  --reason='<why>'                    Article      • decided_by: human
        │  (promote+deploy gate)               XIII         • ddd_pass marker
   ┌──────────┐
   │ DEPLOYED │  ◄── human-authorized commitment
   └──────────┘
        │
        │  ai rrr                              kernel +     • rrr.invoked
        ▼  ① acceptance gate (run all A*)      verifier     • acceptance.{passed,failed}
        │  ② forbidden-path diff                            • forbidden_diff.checked
        │  ③ write RETRO.md + index to                      • RETRO.md
        │     memory-cli                                    • .ai/memory/retros/NNNN_*.md
        │                                                   • rrr_pass marker
   ┌──────────┐
   │   DONE   │  ◄── retro durable, evidence indexed
   └──────────┘
        │
        │  ai verify dev                       kernel       Lock 2 gates:
        │  ai verify prod                                     forbidden files / secrets / smoke
        │
        │  ai close run                        kernel       • close.invoked
        ▼  ① pre-archive: build final_manifest Article XX   • close.manifest_built
        │     emit external audit (COLD tier)               • close.external_audit_emitted (COLD)
        │  ② capture transcripts → CAS                      • capture_items (kind=runtime):
        │     - claude_code_transcript.jsonl                  claude / codex / gemini
        │     - codex_cli_transcript.jsonl                  • session.closed
        │     - gemini_cli_transcript.json                  • close.completed
        │  ③ archive_session(): move dir
   ┌──────────┐
   │ ARCHIVED │  ◄── session capsule sealed
   └──────────┘
```

One-liner reference:

```
sss -> nnn -> vvv -> gogogo -> *ddd* -> rrr -> verify dev -> verify prod -> close
READY  THINK   DO    VERIFIED   DEPLOYED  DONE                          ARCHIVED
                                * human only
```

Note: graph order is `nnn_pass` (planning passes first, locks scope) -> `vvv_pass` (verification confirms post-plan) -> `gogogo`. The ritual short-codes can be invoked in either typed order; the kernel enforces the graph sequence per `.ai/graphs/standard.yaml` (transitions THINK -> SANDBOX on `nnn_pass`, SANDBOX -> DO on `vvv_pass`).

---

## Project Folder Diagram

```
trinity_v2/
│
├── CLAUDE.md                ← Claude Code entry (precedence pointer)
├── AGENTS.md                ← Codex / Aider / generic agent entry
├── GEMINI.md                ← Gemini CLI entry
├── WARP.md                  ← Warp terminal entry
├── CONSTITUTION.md          ← root pointer → docs/constitution/
├── README.md
├── trinity_organ_refactor_prd.md
│
├── docs/                    ★ rule-of-law + specs + workflow docs
│   ├── constitution/        ★ ⭐ supreme law (D1 forbidden writes)
│   │   ├── TRINITY_CONSTITUTION_V1.md        ← Articles I–XXX
│   │   ├── TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md  (v1.1 RATIFIED)
│   │   ├── INDEX.md
│   │   ├── addendums/
│   │   │   ├── ADDENDUM_V1_0_1.md  (Genesis Trust, Velocity Tiers)
│   │   │   ├── ADDENDUM_V1_0_2.md  (canonical-home relocation)
│   │   │   ├── ADDENDUM_V1_0_3.md  (v1.1 ratification)
│   │   │   └── ADDENDUM_V1_0_4.md  (Article XXIX operationalised)
│   │   └── contracts/       (Organ Map, Ritual Contract, RRR Delegation)
│   ├── specs/               ★ technical spec corpus (D1 forbidden writes)
│   ├── ai_entry/            ← human/AI onboarding (this doc lives here)
│   ├── architecture/
│   ├── contracts/
│   ├── schemas/
│   └── migration/
│
├── .ai/                     ★ kernel — where the OS lives
│   ├── ssot.yaml            ← single source of truth (markers up-walks)
│   ├── cli/
│   │   ├── ai                 ← bash wrapper: cd .ai && python -m cli.main
│   │   ├── main.py            ← Typer entry; registers ritual subcommands
│   │   ├── COMMAND_MANIFEST.yaml  ← canonical ritual↔command map
│   │   ├── commands/          ← one .py per ritual (sss/vvv/nnn/gogogo/
│   │   │                         ddd/rrr/lll/close/audit/doctor/...)
│   │   ├── core/              ← state, audit, recordproxy/, ritual_pack_loader
│   │   ├── agents/            ← in-house Python helpers
│   │   │                         (plan_helper, executor_helper, retro_writer,
│   │   │                          session_bootstrap, clarification_helper,
│   │   │                          presentation_synthesizer)
│   │   └── tests/             ← pytest (962+ tests)
│   ├── rituals/             ← per-ritual template packs (pack contract v1.1)
│   ├── graphs/              ← state-machine definitions (standard.yaml)
│   ├── policies/            ✗ AI MAY NOT WRITE
│   │                          (safety, gates, verifier-rules, forbidden_paths,
│   │                           escalation, llm-budget, trinity_policy)
│   ├── schemas/             ✗ AI MAY NOT WRITE (JSON Schema draft-07)
│   ├── audit/               ✗ AI MAY NOT MODIFY (kernel appends only)
│   │   └── events.ndjson      ← global hash-chain (Layer 1 audit)
│   ├── memory/              ← retros (auto-indexed to memory-cli)
│   │   └── retros/            NNNN_<timestamp>_<slug>.md
│   ├── sessions/
│   │   ├── active/            (symlink/alias for current session)
│   │   ├── <session-id>/      ← live session capsule
│   │   └── archive/<session-id>.archive/  ← sealed past sessions
│   ├── shims/               ← canonical shim definitions (Phase 8)
│   ├── templates/           ← session scaffold templates
│   ├── state/               ← kernel runtime state (status.json, etc.)
│   ├── logs/
│   └── testing/canaries/    ← intentionally-failing fixtures
│
├── ai-docs/                 ← Knowledge Brain (Commit 5)
├── audit/external/          ← COLD-tier external audit emissions
│                              (audit/external/YYYY-MM-DD/<sid>.audit.json)
└── references/              ← read-only reference material (DO NOT copy)
```

Legend:

```
★ = rule-of-law authority (Article XXV ranks 1–4)
✗ = AI forbidden to write (CLAUDE.md boundary)
← = arrow points to description
```

---

## Session Anatomy

Every session created by `ai sss` (or `ai session new`) scaffolds this:

```
.ai/sessions/<session-id>/
│
├── THINK/                   ★ pre-execution reasoning
│   ├── 00_CONTEXT.md          (operator-facing context: prior memory,
│   │                           related sessions, references)
│   ├── 01_PROMPT.md           (rendered Q1–Q5 from vvv answers)
│   ├── 02_SCOPE.md            (rendered from nnn plan envelope)
│   ├── 03_ACCEPTANCE.md       (human-readable acceptance criteria)
│   ├── 03_ACCEPTANCE.yaml     (machine-readable; rrr reads from here)
│   ├── plan_envelope.json     (AI-authored plan input to nnn)
│   ├── NOTES.md
│   ├── CONSENSUS.md
│   ├── CLAUDE_GOVERNANCE_DECISION.md
│   └── RETRO.md               (written by rrr at end)
│
├── SANDBOX/                 ★ multi-agent staging area
│   ├── 00_BRAINSTORM/         (ideation; ends in archive/)
│   ├── 01_DEBATE/             (cross-agent debate; ends in archive/)
│   ├── 02_gemini/             (per-agent isolated workspace)
│   ├── 03_claude/
│   ├── 04_codex/
│   └── README.md
│
├── DO/                      ★ filesystem truth
│   ├── snapshot/              (immutable backup at session start)
│   ├── dev/                   (working copy; verifier targets dev)
│   └── prod/                  (promoted via ai promote; verifier targets prod)
│
├── CONTROL/                 ★ human-readable control plane
│   ├── META.json              ({id, name, created_at, status, workflow{...}})
│   ├── VERIFY.md
│   ├── LIVE_MONITOR.md
│   └── final_manifest.yaml    (built by ai close run)
│
├── CAPTURE/                 ★ per-session SQLite + CAS (Layer 2 audit)
│   ├── capture.sqlite         (audit_events, captures, capture_items, blobs)
│   └── blobs/sha256/<2>/<full-hash>
│                              (CAS — dedupe by SHA-256; one blob, many refs)
│
└── .state/                  ✗ kernel-only (never edit by hand)
    ├── session_state.json     (graph_state: READY → THINK → ... → ARCHIVED)
    ├── plan.json              (canonical plan written by nnn)
    ├── plan.json.bak          (if amended)
    ├── vvv_pass / nnn_pass / rrr_pass / ddd_pass  (markers)
    ├── verify_dev.json
    ├── verify_prod.json
    └── debate_state.json
```

On `ai close run`, the entire dir is **moved** (not copied) to
`.ai/sessions/archive/<session-id>.archive/`. The archive is the durable
record; `.state/` becomes read-only.

---

## Three Layers of Audit Recording

```
┌──────────────────────────────────────────────────────────────────┐
│ Layer 1: GLOBAL HASH-CHAIN          (lightweight, repo-wide)     │
│   .ai/audit/events.ndjson                                        │
│   NDJSON · prev_hash linked · SHA-256 per event                  │
│   Verify: ai audit verify-chain     Inspect: ai audit replay     │
│   Examples: session.created, vvv.invoked, plan.amended,          │
│             gogogo.completed, ddd.invoked, close.completed, ...  │
└──────────────────────────────────────────────────────────────────┘
                            │  capture_id reference
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ Layer 2: PER-SESSION CAPTURE        (heavy artifacts + CAS)      │
│   <session>/CAPTURE/capture.sqlite                               │
│     ├ captures           (one row per ritual invocation)         │
│     ├ capture_items      (input/output/validation/runtime/model) │
│     ├ audit_events       (capture.started / capture.completed)   │
│     └ blobs              (CAS-deduped storage references)        │
│   <session>/CAPTURE/blobs/sha256/<2>/<full-hash>                 │
│   Records: vvv answer_flags.json, nnn plan_envelope.json,        │
│            gogogo result, close final_manifest, ...              │
└──────────────────────────────────────────────────────────────────┘
                            │  close ritual snapshots transcripts
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│ Layer 3: VENDOR CONVERSATION TRANSCRIPTS  (bidirectional chat)   │
│   Sources (vendor-specific paths):                               │
│     ~/.claude/projects/<slug>/<uuid>.jsonl                       │
│     ~/.codex/sessions/<Y>/<M>/<D>/rollout-<ts>-<uuid>.jsonl      │
│     ~/.gemini/tmp/<sha256(project)>/chats/session-<ts>.json      │
│   Records: user messages + assistant replies + tool_use blocks   │
│            + thinking blocks + system reminders                  │
│   Snapshotted into Layer 2 CAS by close.py at archive time       │
│   CAS dedupes — same conversation across N sessions = 1 blob     │
└──────────────────────────────────────────────────────────────────┘
```

Discovery rules per vendor (see `cli.commands.close._snapshot_*_transcript`):

| Vendor | Lookup method | Verification |
|---|---|---|
| Claude Code | slug match `re.sub('[^A-Za-z0-9]+','-', path)` + sep-aware | cwd field per record |
| Codex CLI | `~/.codex/sessions/**/rollout-*.jsonl`, sort by mtime | first `session_meta.cwd` |
| Gemini CLI | `~/.gemini/tmp/<sha256(project_root)>/chats/session-*.json` | deterministic hash (exact) |

---

## Authority Matrix (Article III + XIII)

```
  Ritual         | kernel auto | verifier | human gate | NEEDS_HUMAN
  ───────────────|─────────────|──────────|────────────|─────────────
  sss            |      ✓      |          |            |
  vvv            |      ✓      |    ✓     |            |  (Q×5 fail)
  nnn            |      ✓      |    ✓     |            |  (budget over)
  gogogo         |      ✓      |    ✓     |            |  (step fail)
  ddd            |             |          |    ★★★     |  (always)
  rrr            |      ✓      |    ✓     |            |  (gate fail)
  verify         |      ✓      |    ✓     |            |  (secrets etc.)
  close          |      ✓      |          |            |  (COLD emit fail)
```

★★★ = `decided_by: human` REQUIRED. AI may NOT auto-fire ddd (Article XIII).

---

## Pyramid of Judgment

```
   AI (Claude / Codex / Gemini)        Verifier   (deterministic rules)
        │                                  ↓ unsure
        │   proposes                   Policy      (yaml gates)
        │   - plan envelope               ↓ unsure
        │   - vvv answers              Gated LLM judge (last resort)
        │   - code edits                  ↓ unsure
        │   - retro draft              Human       (NEEDS_HUMAN)
        ▼
   plan_envelope.allowed_paths
```

Forbidden writes by AI (CLAUDE.md, extendable by `plan_envelope.forbidden_paths`):

```
.ai/policies/**       .ai/audit/** (modify)
.ai/schemas/**        docs/specs/**
docs/constitution/**
```

---

## Amendment Flow (Article XXIX — operationalised by Addendum v1.0.4)

```
   Mid-session change of plan?
        │
        ▼
   ┌─── tier classification (XXIX.6 "When in doubt, classify upward") ──┐
   │                                                                    │
   │  Editorial         Operational         Constitutional              │
   │  ─────────         ───────────         ──────────────              │
   │  XXIX.1            XXIX.2              XXIX.3                      │
   │  wording only      proc/threshold      Article add/rm/mod          │
   │  rationale:        rationale: full     rationale: full +           │
   │   1-3 sent          proposal/impact    strategic                   │
   │   (commit body)                                                    │
   │  trace: optional   trace: MUST trace   trace: MUST trace +         │
   │                     observed failure   strategic rationale         │
   │                     / friction /                                   │
   │                     measurable risk                                │
   │  audit event:      audit event:        audit event:                │
   │   constitution.     constitution.       constitution.              │
   │   amended.editorial amended.operational amended.constitutional     │
   │                                                                    │
   │  Each event MUST include: actor, diff_sha256, tier, rationale_ref  │
   └────────────────────────────────────────────────────────────────────┘

   In a running session: emit "plan.amended" + extend .state/plan.json +
   THINK/plan_envelope.json + THINK/03_ACCEPTANCE.yaml. Don't force-close
   to open a sub-session unless architecturally required.
   (Memory: feedback_plan_amendment_vs_subsession)
```

---

## Cross-references

- Constitutional core: [`/docs/constitution/INDEX.md`](../constitution/INDEX.md)
- Ritual Constitution v1.1 (RATIFIED): [`/docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md`](../constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md)
- Article XXIX operationalised: [`/docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md`](../constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md)
- Short codes table: [`SHORT_CODES.md`](SHORT_CODES.md)
- Forbidden writes: [`BOUNDARIES.md`](BOUNDARIES.md)
- Kernel CLI manifest: [`/.ai/cli/COMMAND_MANIFEST.yaml`](../../.ai/cli/COMMAND_MANIFEST.yaml)
- Doctor (runtime contract check): `bash .ai/cli/ai doctor commands`
