# `.ai/rituals/` — Ritual Template Pack root

**Authority:** [Trinity Ritual Constitution v1.1-rc](../../docs/constitution/TRINITY_RITUAL_CONSTITUTION_V1_1_RC.md) Articles I, IV, V, VI, XVI.

**Status:** Template-pack filesystem layout (bootstrapped 2026-05-13 under session `feat-ritual-template-packs-bootstrap`). Kernel runtime does not yet load from this tree — that wiring is a separate session and is the empirical-ratification path for Article XII.5.

## Layout (Article IV — non-negotiable)

```
.ai/rituals/
├── sss/
│   ├── ritual.contract.json    # RC Article V — declaratory contract
│   ├── context.schema.json     # RC Article XVI — typed-placeholder catalog
│   ├── write.template.md       # RC Article XVI — write-phase template
│   └── check.template.json     # RC Article VI — verifier predicates
├── vvv/    (same 4 files)
├── nnn/    (same 4 files)
├── gogogo/ (same 4 files)
├── ddd/    (same 4 files)
├── rrr/    (same 4 files)  ← also cites TRINITY_RRR_DELEGATION_CONTRACT_V1.md T1–T4
└── close/  (same 4 files)
```

## What each file is

| File | Authority | Purpose |
|---|---|---|
| `ritual.contract.json` | RC Article V | Declares `ritual_name`, `purpose`, `owner_role`, `required_inputs[]`, `required_artifacts[]`, `audit_events[]`, `state_transitions[]`, `failure_behavior`. Validated by `.ai/schemas/ritual_contract.schema.json`. |
| `context.schema.json` | RC Article XVI | Per-ritual typed-placeholder catalog. Defines which `{{type:identifier}}` tokens the write template may consume. Validated by `.ai/schemas/ritual_context.schema.json`. |
| `write.template.md` | RC Article XVI | The text body the ritual writes (e.g. `01_PROMPT.md`, `RETRO.md`). Uses typed placeholders only — no raw `{{user_input}}` (template-injection protection). |
| `check.template.json` | RC Article VI | Declarative verification spec: `required_artifacts[]`, `structural_predicates[]`, `content_predicates[]`, `failure_behavior` (BLOCK/WARN/DEGRADED/NEEDS_HUMAN/FAILED/TERMINAL_FAILED), `evidence_collection`. Validated by `.ai/schemas/ritual_check_template.schema.json`. |

## Discipline

- Files in this tree are **static template artifacts**. No executable code lives here.
- Edits to any pack are amendments to ritual contracts; they should be discussed against the Ritual Constitution before merging.
- Schemas in `.ai/schemas/ritual_*.schema.json` are the load-bearing authority — when pack contents drift from schemas, the pack is wrong, not the schema.
- `_REVIEW.md` (if present) is the cross-check artifact from the bootstrap session and may be removed once incorporated into a real verifier loop.

## Out of scope for the bootstrap session

- Kernel runtime that loads from `.ai/rituals/<r>/*` at ritual invocation time (separate session).
- Article XVIII role-permission matrix enforcement (separate session).
- Article XVII full 16-state graph (separate session).
- Article XII.5 empirical ratification (separate session — runs an end-to-end workflow under v1.1-rc rules using these packs).
