---
title: "retro-cli Specification v1.0 (English)"
subtitle: "Structured retrospective writer with schema enforcement"
language: English
version: 1.0.0-draft
status: draft
last-updated: 2026-04-28
phase: 7
note: "Translation of ../06_RETRO_CLI_SPEC.md"
implements: TOOL_CONTRACT v1.1
---

# retro-cli Specification v1.0 (English)

> **retro-cli = Structured Memory Writer.**
>
> Forces retros to follow a searchable schema + auto-indexes into memory-cli.
> Additive — old retros still work, new ones must follow the schema.

---

## 0. Status

- **Phase:** 7
- **Depends on:** Phase 1 (Tool Contract), Phase 2 (memory-cli)
- **Action namespace:** `retro.*`
- **Memory boundary:** For Trinity v0.1 ritual paths, `rrr` / `retro-cli`
  delegates only to `memory-cli index <retro-path>`. `memory-cli learn`
  is a legacy/non-v0.1 semantic surface for non-ritual callers and must
  not be used by `rrr`.

---

## 1. Goal

### Pain
- 240 retros = free-form markdown
- AI doesn't always follow templates
- Search finds them, but quality is inconsistent
- Evidence links are not structured

### Solution
- **Additive frontmatter schema** — old retros don't break
- Validate before save
- Auto-call `memory-cli index` after save
- Evidence checker (artifacts must exist)

---

## 2. Frontmatter Schema

### 2.1 Required Fields (MUST)

```yaml
---
title: "Modal z-index black screen fix"
date: 2026-04-28
type: retro
session_id: sess_2026-04-28_modal
goal: "Fix modal causing black screen on z-index conflict"
status: success | partial | blocked | dead
---
```

### 2.2 Recommended Fields (SHOULD)

```yaml
---
# ... required ...
duration_min: 45
confidence: 0.85           # 0.0 - 1.0 (self-assessment)
tags: [bugfix, ui, modal, css]
evidence:
  - { type: screenshot, ref: artifacts/before.png, sha256: "..." }
  - { type: log, ref: artifacts/console.log, sha256: "..." }
  - { type: diff, ref: artifacts/fix.patch, sha256: "..." }
context_refs:
  - "memory:r_2025-11-25_username-display-fix"   # link to past retro
parent_session: null
supersedes: []             # IDs of retros this replaces
---
```

### 2.3 Optional Fields (MAY)

```yaml
---
# ... required + recommended ...
risk_level: low | medium | high
files_changed: [path/to/file.css, path/to/script.js]
lines_changed: { added: 12, removed: 3 }
test_coverage_delta: +2.3
verifier_verdict: PASS
verifier_run_id: run_xyz
participants: [yai, claude, codex]
external_refs:
  - { type: github_issue, ref: "https://..." }
---
```

### 2.4 Body Sections (Recommended)

```markdown
# Retro: Modal z-index black screen fix

## Goal
Fix modal causing black screen on z-index conflict

## What happened
[Brief narrative — what was the bug, how was it discovered]

## Root cause
[Technical root cause analysis]

## Fix
[What was changed, file by file]

## Evidence
[Reference artifacts in frontmatter]

## What went well
- ...

## What could improve
- ...

## Mistakes made
- ... (with prevention)

## Lessons learned
1. ...
2. ...

## Action items
- [ ] ...
- [ ] ...
```

---

## 3. Commands

| Verb | Action | Tier | Purpose |
|------|--------|------|---------|
| `validate` | `retro.validate` | safe | Check schema + evidence |
| `create` | `retro.create` | normal | Create new retro from template |
| `update` | `retro.update` | normal | Update existing retro |
| `commit` | `retro.commit` | normal | Save + index to memory-cli |
| `migrate` | `retro.migrate` | normal | Add frontmatter to legacy retro |
| `lint` | `retro.lint` | safe | Check style/completeness |
| `link` | `retro.link` | normal | Add context_refs / evidence |

### 3.1 `validate`

```bash
retro-cli --cmd "validate <path>"
```

Response:
```json
{
  "ok": true,
  "command": "validate",
  "data": {
    "path": "RETRO.md",
    "schema_valid": true,
    "required_fields": { "ok": true, "missing": [] },
    "evidence_check": {
      "ok": false,
      "missing_files": ["artifacts/console.log"],
      "sha256_mismatch": []
    },
    "lint": {
      "warnings": [
        "Body section 'Lessons learned' has only 1 item (recommend 3+)"
      ]
    },
    "verdict": "RETRY",
    "verdict_reason": "Evidence file missing"
  }
}
```

### 3.2 `create`

```bash
retro-cli --cmd "create --session=<id> [--template=<name>]"
```

Generates retro from template + auto-fills:
- `session_id` from CLI flag
- `date` = today
- `type` = `retro`
- Pulls goal from `loop_state.json`
- Lists artifacts from session

### 3.3 `commit` (the important one)

```bash
retro-cli --cmd "commit <path>"
```

Pipeline:
```
1. validate(path)
   ↓ if fail → return RETRY
2. lint(path)
   ↓ warnings logged but not blocking
3. evidence check
   ↓ if files missing → RETRY
4. memory-cli index <path>
   ↓ index artifact into Knowledge Brain
5. audit event
   ↓ write to events.ndjson
```

Response:
```json
{
  "ok": true,
  "command": "commit",
  "data": {
    "path": "RETRO.md",
    "validated": true,
    "memory_id": "r_2026-04-28_modal-fix",
    "indexed": true,
    "audit_event": "events.ndjson:line:1234"
  }
}
```

### 3.4 `migrate`

```bash
retro-cli --cmd "migrate <path>"
```

For legacy retros without frontmatter:
- Detect filename pattern → derive date, slug, type
- Extract title from H1
- Suggest tags from content
- Insert frontmatter (preserve existing body)
- Mark `confidence=draft` (manual upgrade later)

```bash
# Bulk migrate
find .claude/retrospectives -name "*.md" \
  | xargs -I {} retro-cli --cmd "migrate {}"
```

### 3.5 `lint`

```bash
retro-cli --cmd "lint <path>"
```

Checks (warnings only, non-blocking):
- Title not just filename
- Body has all recommended sections
- Lessons learned has 3+ items
- Evidence section non-empty
- Tags >= 1
- Confidence set
- Date in ISO 8601

---

## 4. Templates

### 4.1 Default Template

`templates/retro_default.md`:
```markdown
---
title: "{{TITLE}}"
date: {{DATE}}
type: retro
session_id: {{SESSION_ID}}
goal: "{{GOAL}}"
status: pending
duration_min: {{DURATION_MIN}}
confidence: 0.0
tags: []
evidence: []
---

# {{TITLE}}

## Goal
{{GOAL}}

## What happened


## Root cause


## Fix


## Evidence


## What went well
- 

## What could improve
- 

## Mistakes made
- 

## Lessons learned
1. 

## Action items
- [ ] 
```

### 4.2 Specialized Templates

- `templates/retro_bugfix.md` — bug-focused
- `templates/retro_feature.md` — feature-focused
- `templates/retro_deploy.md` — deployment-focused
- `templates/retro_research.md` — research/exploration

---

## 5. Evidence Checker

### 5.1 Validate Evidence Links

For each `evidence` entry in frontmatter:
- File exists at `ref` path
- If `sha256` provided, recompute and compare
- File size > 0
- (Optional) MIME type matches expected

### 5.2 Auto-collect Evidence

```bash
retro-cli --cmd "link <retro> --auto-collect=<session>"
```

Scans session artifact directory:
- Add screenshots
- Add logs
- Add diffs
- Compute sha256

---

## 6. Auto-update Memory

### 6.1 Pipeline

```
retro-cli commit RETRO.md
  ↓
validate
  ↓
lint
  ↓
evidence check
  ↓
memory-cli index RETRO.md
  ↓
audit event: retro_committed
```

### 6.2 Confidence Upgrade

Confidence stays `draft` until human review:
```bash
# Later, after review
memory-cli --cmd "tag r_xyz +reviewed_2026_04_28"
```

For now, no automated `verified` upgrade — preserve curation discipline.

---

## 7. Verifier Integration

### 7.1 retro-cli + verifier

retro-cli `commit` triggers `verify-cli` with rule set `memory_promote`:

```yaml
# .ai/policies/verifier-rules.yaml
verifier_rules:
  memory_promote:
    required_evidence:
      - frontmatter_valid
      - evidence_artifacts_listed
      - confidence_score
    pass_when:
      - schema_valid
      - has_evidence
    retry_when:
      - missing_frontmatter_field
    needs_human_when:
      - contradicts_existing_memory
```

### 7.2 Conflict Detection

Before indexing a retro artifact, check for similar existing memories:
```bash
memory-cli --cmd "search '{{goal}}' --limit=3"
```

If a high-similarity match exists → ask human:
- Supersede old?
- Add as parallel?
- Merge?

---

## 8. Configuration

```json
{
  "version": "1.0",
  "tool": "retro-cli",
  "tool_specific": {
    "templates_dir": "./templates/",
    "default_template": "retro_default",
    "memory_cli_bin": "node /path/to/memory-cli/index.js",
    "verify_cli_bin": "node /path/to/verify-cli/index.js",
    "lint_strictness": "warn",
    "auto_index": true,
    "evidence_required": true,
    "min_confidence": 0.0,
    "min_lessons_count": 1,
    "auto_collect_artifacts": [
      "*.png", "*.log", "*.patch", "*.diff"
    ]
  }
}
```

---

## 9. Anti-patterns

| ❌ Anti-pattern | ✅ Correct |
|-----------------|-----------|
| Free-form retro | Schema-enforced |
| AI fabricates evidence | File must exist + sha256 verify |
| Auto-mark verified | Default draft, manual upgrade |
| Skip migration | `retro-cli migrate` for legacy |
| Lessons section empty | Lint warns |
| No links to past | `context_refs` field |

---

## 10. Open Questions

1. Templates — file-based or programmatic?
2. Schema versioning — migrate when v2?
3. Body validation — required sections or recommended?
4. Multi-language retros (Thai/English) — handle?
5. Photo evidence — embedded or referenced?
6. Auto-tag suggestion — AI or keyword?
7. Conflict resolution UX — interactive prompt?
8. Bulk migration safety — dry-run by default?

---

## 11. Implementation Sketch

```
retro-cli/
├── index.js
├── lib/
│   ├── validator.js
│   ├── linter.js
│   ├── template-engine.js
│   ├── evidence-checker.js
│   ├── migrator.js              ← legacy retro upgrade
│   ├── memory-bridge.js         ← calls memory-cli
│   ├── verify-bridge.js         ← calls verify-cli
│   └── envelope.js
├── schema/
│   ├── retro-frontmatter.schema.json
│   ├── config.schema.json
│   └── response-v1.schema.json
├── templates/
│   ├── retro_default.md
│   ├── retro_bugfix.md
│   ├── retro_feature.md
│   ├── retro_deploy.md
│   └── retro_research.md
├── tests/
│   ├── harness.js
│   ├── golden.js
│   └── fixtures/
└── docs/
    ├── ARCHITECTURE.md
    ├── COMMAND_CONTRACT.md
    ├── AI_AGENT_GUIDE.md
    └── FRONTMATTER_SCHEMA.md
```

---

## 12. Quick Reference

### Daily flow (after task)
```bash
# rrr → triggers retro-cli internally
rrr

# Or manual
retro-cli --cmd "create --session=$(cat .ai/sessions/active/.id)"
# (edit RETRO.md)
retro-cli --cmd "commit RETRO.md"
```

### Migration
```bash
find .claude/retrospectives -name "*.md" \
  | xargs -I {} retro-cli --cmd "migrate {}"
```

### Validation
```bash
retro-cli --cmd "validate path/to/retro.md"
retro-cli --cmd "lint path/to/retro.md"
```

---

## See also

- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md)
- [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md) — receiver
- [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) — `memory_promote` rule

## Changelog

- **v1.0.0-draft (2026-04-28)** — Initial draft (Phase 7)
