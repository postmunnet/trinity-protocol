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
├── SANDBOX/                  Agent working areas (isolated)
│   ├── gemini/               Gemini workspace
│   ├── claude/               Claude workspace
│   ├── codex/                Codex workspace
│   └── DEBATE/               Debate rounds & verdict template
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
ai session new "Fix Login Bug"
```

Trinity creates:
```
sessions/2025-12-21_fix_login_bug/
├── THINK/               ← copied from this template
├── DO/                  ← empty folders created
├── CONTROL/             ← copied + variable substitution
└── .state/              ← initialized with sentinel schemas
```

---

## 📝 Trust Boundaries (PRD v0.5)

| Folder | Who Edits | Purpose |
|--------|-----------|---------|
| **THINK/** | Human | Planning and reasoning |
| **SANDBOX/gemini** | Gemini | Research + drafts (merge to DO/dev) |
| **SANDBOX/claude** | Claude | Plans + reviews (merge to DO/dev) |
| **SANDBOX/codex** | Codex | Implementation + tests (merge to DO/dev) |
| **DO/dev/** | Human | Working on code |
| **DO/snapshot/** | System | Immutable backup (DO NOT EDIT) |
| **DO/prod/** | System | Promoted from dev (via `ai promote`) |
| **CONTROL/** | System (Human reads) | Metadata and logs |
| **.state/** | System ONLY | Canonical state (NEVER EDIT) |

---

## 🚦 Workflow (with Sandboxes)

1. **Plan** → Fill out THINK/ files
2. **Work (Isolated)** → Use SANDBOX/<agent>/ workspaces
3. **Apply** → Merge SANDBOX → DO/dev (single ingress; WP4)
4. **Verify** → `ai verify dev`
5. **Promote** → `ai promote` (dev → prod; requires consensus by default)
6. **Deploy** → `ai deploy prod`
7. **Verify** → `ai verify prod`
8. **Close** → `ai close` (requires prod verify PASS)

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
