# WARP.md — Warp Terminal Entrypoint for trinity_v2

> For Warp's AI assistant in terminal sessions. Same canonical content; Warp-specific notes here.

## What is trinity_v2?

CLI-native AI microkernel — Coordinator + Judge for vendor AI. Spec pack v2.0 in `docs/specs/`.

> **CLI-native = perfect fit for Warp.** Trinity speaks via `bash .ai/cli/ai` launcher; Warp speaks shell.

## Read FIRST (priority order)

1. **For setup work (Commit 0–7):** [`docs/migration/README.md`](docs/migration/README.md)
2. **For Phase 1+ implementation:** [`docs/specs/INDEX.md`](docs/specs/INDEX.md) → [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md)
3. **First time here:** [`docs/ai_entry/QUICK_START.md`](docs/ai_entry/QUICK_START.md)
4. **Always:** [`docs/ai_entry/SHORT_CODES.md`](docs/ai_entry/SHORT_CODES.md) + [`BOUNDARIES.md`](docs/ai_entry/BOUNDARIES.md) + [`WORKFLOW.md`](docs/ai_entry/WORKFLOW.md)

## Short Codes

| Code | Action | When |
|------|--------|------|
| `lll` | Look/List status | Start of session, anytime |
| `sss: <task>` | Start session | New task |
| `vvv` | Verify understanding | Before code |
| `nnn` | New plan with estimates | After vvv pass |
| `gogogo` | Execute plan | After nnn approved |
| `ddd` | Deploy (human gate) | After gogogo + verify |
| `rrr` | Retrospective | End of session |

**Sequence:** `sss → vvv → nnn → gogogo → ddd → rrr`

Detail: [`docs/ai_entry/SHORT_CODES.md`](docs/ai_entry/SHORT_CODES.md)

## CLI Command Rule

Do not guess Trinity commands from ritual names. Ritual short-codes map to executable CLI via [`.ai/cli/COMMAND_MANIFEST.yaml`](.ai/cli/COMMAND_MANIFEST.yaml); from Warp you can `cat` it or run `bash .ai/cli/ai doctor commands` to see the live contract.

- `sss "<task>"` → `bash .ai/cli/ai sss "<task>"` (alias of `bash .ai/cli/ai session new "<task>"`)
- `status` → `bash .ai/cli/ai status` (alias of `bash .ai/cli/ai status show`)
- `vvv / nnn / gogogo / ddd / rrr / lll / close` → `bash .ai/cli/ai <code>`

If a command fails with `No such command` or `Missing command`, stop and run `bash .ai/cli/ai doctor commands` — do NOT retry random variants. The doctor walks the manifest and reports drift as structured PASS/FAIL.

## Per-channel ritual rendering

<!-- BEGIN R30/R33 per-channel rendering -->
Ritual output layout is template-driven. Before changing `lll`, `vvv`, `nnn`,
`gogogo`, `ddd`, or `rrr` presentation, read the canonical templates at
`.ai/shims/<ritual>/templates/<channel>.md`.

- `desktop.md` may use dense tables and box-drawing where appropriate.
- `mobile.md` must avoid box-drawing and ASCII tables.
- Adapter files only point agents at the templates; the templates own layout.
<!-- END R30/R33 per-channel rendering -->

## Boundaries

- ✅ AI **proposes** — Verifier/Policy/Human **decides**
- ✅ Every action logs to `.ai/audit/events.ndjson` (hash chain — `tail -f` it from Warp!)
- ❌ Forbidden: edit `.ai/policies/**`, auto-deploy, MCP as core, <upstream-project> direct copy

Detail: [`docs/ai_entry/BOUNDARIES.md`](docs/ai_entry/BOUNDARIES.md)

## Warp-Specific Notes

### Strengths to leverage
- **Terminal-first** — Trinity is CLI-native, every command works in Warp blocks
- **Workflow integration** — Warp Workflows can wrap Trinity short codes
- **AI in shell** — Warp AI sees command history; great for `lll` follow-up commands

### Suggested Warp Workflow stubs (Phase 8 will provide canonical)

```yaml
# .warp/workflows/trinity-lll.yaml (suggested, NOT active yet)
name: lll
command: bash .ai/cli/ai status
description: Trinity status report

# .warp/workflows/trinity-sss.yaml
name: sss
command: bash .ai/cli/ai session new "{{task}}"
description: Start Trinity session
arguments:
  - name: task
    description: Task description
    type: text
```

> ⚠️ Warp workflow files are **NOT** active in trinity_v2 yet. Phase 8 will provide canonical generators from `.ai/shims/`. Do not hand-write Warp configs that hardcode behavior — they will be **generated** from canonical shims.

### Audit log in terminal
Trinity's hash chain is `events.ndjson` (one JSON per line) — Warp's structured output handles it well:

```bash
# Live tail
tail -f .ai/audit/events.ndjson | jq

# Filter by type
grep '"type":"session.transition"' .ai/audit/events.ndjson | jq

# Validate genesis hash (run after Commit 1)
python3 -c "import json,hashlib;e=json.loads(open('.ai/audit/events.ndjson').readline());c=json.dumps({k:v for k,v in e.items() if k!='hash'},sort_keys=True,separators=(',',':'));print('genesis ok' if e['hash']==hashlib.sha256(c.encode()).hexdigest() else 'CHAIN BROKEN')"
```

### `.warp/` directory
Not yet populated. No workflow configs (Phase 8). Don't create them by hand.

### Reference (DO NOT copy directly)
`references/shims/upstream-skills/` (added Commit 6) — <upstream-project> used Claude Code skills format. Warp's format is Workflow YAML; not a 1:1 translation, must regenerate from canonical `.ai/shims/`.

## Session Sandbox Rules

If Warp AI is acting as primary agent (uncommon but valid):
- Pick a SANDBOX role folder (suggest `04_codex/` — closest to terminal-first style, or new with user approval)
- Write only in your role folder during SANDBOX phase

## Quick Run Commands

```bash
# Status
bash .ai/cli/ai status

# Tests
cd .ai && python3 -m pytest cli/tests -q

# YAML config validation (Phase 0.5)
cd .ai && python3 -m pytest cli/tests/test_yaml_valid.py -v

# Tail audit log
tail -f .ai/audit/events.ndjson | jq

# Active session
ls .ai/sessions/active/
```

## Quick Links

| What | Where |
|------|-------|
| Spec overview | [`docs/specs/INDEX.md`](docs/specs/INDEX.md) |
| Master vision | [`docs/specs/00_BLUEPRINT.md`](docs/specs/00_BLUEPRINT.md) |
| Migration plan | [`docs/migration/README.md`](docs/migration/README.md) |
| Decisions log | [`docs/migration/01_CONTEXT_AND_DECISIONS.md`](docs/migration/01_CONTEXT_AND_DECISIONS.md) |
| Glossary | [`docs/specs/12_GLOSSARY.md`](docs/specs/12_GLOSSARY.md) |

## Don't

- ❌ Run destructive commands without explicit user approval (`rm -rf`, `git push --force`, `git reset --hard`, `DROP TABLE`)
- ❌ Edit `.ai/policies/**`
- ❌ Auto-deploy via shell trickery (still requires `decided_by: human` gate)
- ❌ Hand-write `.warp/workflows/` (Phase 8 generates from canonical)
- ❌ Skip Trinity workflow even for "simple" terminal tasks

When unsure → ask. NEEDS_HUMAN > confident wrong answer.
