# Trinity Templates - PRD v0.4 Structure

**Purpose:** Template scaffold for Trinity v0.4 session creation
**Based on:** PRD v0.4 - Session-Based Dev→Prod Workflow

---

## 📂 Directory Structure

```
templates/
├── session/                  PRD v0.4 Canonical Structure
│   ├── THINK/               Human fills (reasoning/planning)
│   │   ├── 00_CONTEXT.md
│   │   ├── 01_PROMPT.md
│   │   ├── 02_SCOPE.md
│   │   ├── 03_ACCEPTANCE.md
│   │   ├── CLAUDE_GOVERNANCE_DECISION.md
│   │   └── NOTES.md (optional)
│   │
│   ├── CONTROL/             Human reads (system updates)
│   │   ├── META.json
│   │   ├── VERIFY.md
│   │   └── LIVE_MONITOR.md
│   │
│   └── state/               System-only (canonical state)
│       ├── status.json      (PRD sentinel schema)
│       ├── verify_report.json (PRD sentinel schema)
│       └── events.ndjson
│
└── agents/                   Agent-specific (optional)
    ├── claude/
    ├── gemini/
    ├── codex/
    └── antigravity/
```

---

## 🎯 How It Works

When you run:
```bash
ai session new "fix: Login Bug"
```

Trinity creates (see [`docs/SESSION_NAMING.md`](../docs/SESSION_NAMING.md)
for the folder-naming spec):
```
sessions/0001_2026-04-20_14_30_pm_fix-login-bug/
├── THINK/               ← copied from templates/session/THINK/
│   ├── 00_CONTEXT.md
│   ├── 01_PROMPT.md
│   ├── 02_SCOPE.md
│   ├── 03_ACCEPTANCE.md
│   ├── CLAUDE_GOVERNANCE_DECISION.md
│   └── NOTES.md
│
├── DO/                  ← created empty (user works here)
│   ├── snapshot/
│   ├── dev/
│   └── prod/
│
├── CONTROL/             ← copied from templates/session/CONTROL/
│   ├── META.json
│   ├── VERIFY.md
│   └── LIVE_MONITOR.md
│
└── .state/              ← initialized with sentinel schemas
    ├── status.json
    ├── verify_report.json
    └── events.ndjson
```

---

## 📝 Template Roles (Trust Boundaries)

### THINK/ (Human Editable)
User fills these out manually:

- **00_CONTEXT.md** - Session objectives, scope, constraints
- **01_PROMPT.md** - Problem statement, goals, success criteria
- **02_SCOPE.md** - Files to change, impact zones
- **03_ACCEPTANCE.md** - Success criteria, verification steps
- **CLAUDE_GOVERNANCE_DECISION.md** - Major decisions requiring approval
- **NOTES.md** - Free-form working notes (optional)

### CONTROL/ (Human Readable, System Updates)
User reads, system updates:

- **META.json** - Session metadata, workflow state
- **VERIFY.md** - Verification log (auto-updated by `ai verify`)
- **LIVE_MONITOR.md** - Real-time status (auto-updated)

### .state/ (System-Only, Canonical)
**Never hand-edited:**

- **status.json** - Global system state (PRD sentinel schema)
- **verify_report.json** - Latest verification results (PRD sentinel schema)
- **events.ndjson** - Append-only event log

---

## 🔧 Sentinel Schemas (PRD v0.4 Required)

### status.json (Never empty, always valid JSON)
```json
{
  "schema_version": 1,
  "updated_at": null,
  "phase": "INIT",
  "status": "IDLE",
  "active_session_id": null,
  "stop_requested": false,
  "last_verify": null,
  "pending": []
}
```

### verify_report.json (Never empty, always valid JSON)
```json
{
  "schema_version": 1,
  "run_id": null,
  "session_id": null,
  "status": "NOT_RUN",
  "passed": null,
  "checks": {
    "forbidden_files": { "status": "NOT_RUN" },
    "secrets": { "status": "NOT_RUN" },
    "smoke": { "status": "NOT_RUN" }
  },
  "blocks": [],
  "warnings": [],
  "errors": [],
  "started_at": null,
  "finished_at": null
}
```

**Critical Requirement:** All `.state/*` writes must be atomic (temp + rename).

---

## 🧪 Verification Fixtures

Located at `tests/verify_fixtures/` (NOT in `.ai/`):

```
tests/verify_fixtures/
├── pass_clean/
│   └── DO/prod/app.py       (clean code, should PASS)
├── fail_secret/
│   └── DO/prod/config.py    (has api_key, should FAIL)
└── fail_forbidden/
    └── DO/prod/.env         (forbidden file, should FAIL)
```

Test with:
```bash
ai selftest verify
```

Expected:
- `pass_clean` → exit 0 (PASS)
- `fail_secret` → exit 1 (FAIL on secret detection)
- `fail_forbidden` → exit 1 (FAIL on forbidden file)

---

## 🚀 Usage by CLI

Templates are loaded and variable-substituted by CLI:

```python
def create_session(name: str):
    template_dir = config.templates_path / "session"
    session_dir = config.sessions_path / session_id

    # Copy THINK/ templates
    for file in (template_dir / "THINK").glob("*.md"):
        content = file.read_text()
        content = content.replace("{{SESSION_NAME}}", name)
        content = content.replace("{{SESSION_ID}}", session_id)
        content = content.replace("{{TIMESTAMP}}", iso_timestamp)
        # ... write to session_dir/THINK/

    # Copy CONTROL/ templates (similar)
    # ...

    # Initialize .state/ with sentinel schemas
    # ...
```

---

## 📚 PRD v0.4 References

From PRD Section 5 (Canonical Session Structure):
> All sessions created under `sessions/` with one canonical layout.

From PRD Section 8 (State & Report Schema):
> Must exist and always be valid JSON (sentinel schemas).
> All writes to `.state/*` must be atomic (temp + rename).

From PRD Section 9 (Test the Tester):
> Fixtures structure with `DO/prod/` paths.
> `ai selftest verify` must be deterministic.

---

**End of Templates README**
