# Trinity Session Template (PRD v0.4)

This is the **canonical session structure** used by `ai session new` command.

---

## 📂 Structure Overview (updated)

```
session/                        Template root
├── THINK/                     Human fills (6 files)
│   ├── 00_CONTEXT.md          Objectives, scope, constraints
│   ├── 01_PROMPT.md           Problem statement, goals
│   ├── 02_SCOPE.md            Files to change, impact zones
│   ├── 03_ACCEPTANCE.md       Success criteria, verification
│   ├── CLAUDE_GOVERNANCE_DECISION.md  Major decisions
│   └── NOTES.md               Free-form working notes
│
├── SANDBOX/                    Sequential workspace (numbered by step)
│   ├── 00_BRAINSTORM/         Step 1: Divergent ideation
│   │   ├── 00_SEED.md         Topic + scope + forbidden zones
│   │   ├── 01_DIVERGE.md      Free-form idea dump (no judging)
│   │   ├── 02_CLUSTER.md      Group similar ideas into themes
│   │   ├── 03_EVALUATE.md     Pro/con/risk/cost per cluster
│   │   ├── 04_SHORTLIST.md    Top 3-5 candidates → feed DEBATE
│   │   └── archive/           Past brainstorms
│   │
│   ├── 01_DEBATE/             Step 2: Convergent decision
│   │   ├── round_1.md         Motion + seats file proposals
│   │   ├── round_2.md         Rebuttals
│   │   ├── round_3.md         Verdict prep
│   │   ├── verdict.md         Final binding ruling
│   │   └── archive/           Past debates
│   │
│   ├── 02_gemini/             Step 3: Gemini seat workspace (research)
│   ├── 03_claude/             Step 3: Claude seat workspace (governance)
│   └── 04_codex/              Step 3: Codex seat workspace (implementation)
│
├── DO/                        User works here
│   ├── snapshot/              Immutable backup (DO NOT EDIT)
│   ├── dev/                   Working copy (EDIT HERE)
│   └── prod/                  Release candidate (from promote)
│
├── CONTROL/                   Human reads, system updates
│   ├── META.json              Session metadata
│   ├── VERIFY.md              Verification log
│   └── LIVE_MONITOR.md        Real-time status
│
└── .state/                    System-only (NEVER EDIT)
    ├── session_state.json     Session-local state machine
    ├── debate_state.json      Debate state (rounds, mode)
    ├── verify_dev.json        DEV verification report
    ├── verify_prod.json       PROD verification report
    └── events.ndjson          Event log
```

---

## 🎯 When You Run

```bash
ai session new "fix: Login Bug"
```

Trinity creates:
```
sessions/0001_2026-04-20_14_30_pm_fix-login-bug/
├── THINK/               ← copied from this template
├── DO/                  ← empty folders created
├── CONTROL/             ← copied + variable substitution
└── .state/              ← initialized with sentinel schemas
```

The folder name follows the canonical format
`{seq}_{date}_{hour}_{minute}_{ampm}_{type}-{slug}` — see
[`docs/SESSION_NAMING.md`](../../docs/SESSION_NAMING.md) for the full
naming spec.

---

## 📝 Trust Boundaries (PRD v0.5)

| Folder | Who Edits | Purpose |
|--------|-----------|---------|
| **THINK/** | Human | Planning and reasoning |
| **SANDBOX/00_BRAINSTORM/** | Human + any agent | Diverge → cluster → shortlist (before DEBATE) |
| **SANDBOX/01_DEBATE/** | 3 seats + chair | Converge via rounds + verdict |
| **SANDBOX/02_gemini/** | Gemini | Research + drafts (merge to DO/dev) |
| **SANDBOX/03_claude/** | Claude | Plans + reviews (merge to DO/dev) |
| **SANDBOX/04_codex/** | Codex | Implementation + tests (merge to DO/dev) |
| **DO/dev/** | Human | Working on code |
| **DO/snapshot/** | System | Immutable backup (DO NOT EDIT) |
| **DO/prod/** | System | Promoted from dev (via `ai promote`) |
| **CONTROL/** | System (Human reads) | Metadata and logs |
| **.state/** | System ONLY | Canonical state (NEVER EDIT) |

---

## 🚦 Workflow (with Sandboxes)

1. **Plan** → Fill out THINK/ files
2. **Brainstorm** (if new problem) → SANDBOX/00_BRAINSTORM/ diverge → shortlist
3. **Debate** → SANDBOX/01_DEBATE/ rounds → verdict (binding)
4. **Work (Isolated)** → Use SANDBOX/{02_gemini,03_claude,04_codex}/ workspaces per verdict
5. **Apply** → Merge SANDBOX → DO/dev (single ingress; WP4)
6. **Verify** → `ai verify dev`
7. **Promote** → `ai promote` (dev → prod; requires consensus by default)
8. **Deploy** → `ai deploy prod`
9. **Verify** → `ai verify prod`
10. **Close** → `ai close` (requires prod verify PASS)

### Brainstorm ↔ Debate cycle (multiple per session)

When next decision needed within same session:

```
00_BRAINSTORM/04_SHORTLIST.md → 01_DEBATE/round_1.md → verdict.md
                                                            ↓
                                               (verdict signed)
                                                            ↓
                                  00_BRAINSTORM → archive/<topic>/
                                  01_DEBATE     → archive/<topic>/
                                                            ↓
                          00_BRAINSTORM/00_SEED.md (next topic) ← fresh
```

---

## 🔒 Immutability Rules

1. **DO/snapshot/** = Read-only after creation
2. **.state/** = System-only, atomic writes
3. **DO/prod/** = Only written by `ai promote`

---

## 🧪 Example Session

See `tests/verify_fixtures/` for example sessions used in testing.

---

**This structure is the Single Source of Truth for all Trinity sessions.**
