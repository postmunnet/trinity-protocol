---
title: "Trinity RRR Delegation Contract v1.0"
version: "1.0"
status: "locked"
last-updated: "2026-05-12"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
parent: "TRINITY_CONSTITUTION_V1.md"
related:
  - "TRINITY_RITUAL_CONTRACT_V1.md §rrr (gate semantics)"
  - "TRINITY_ORGAN_MAP_V1.md §12 RRR Terminal Gate, §9 Memory CLI, §11 Retro"
  - "TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md §B (Decision Velocity Tiers)"
  - "trinity_organ_refactor_prd.md §8.12 (RRR Terminal Gate); Phase 1 PR"
  - "BREAK_GLASS.yaml of Phase 0 (post_mortem_resolution = this contract)"
---

# Trinity RRR Delegation Contract v1.0

> The terminal-gate organ (`ai rrr`) is a **router**, not a memory
> writer. It closes the workflow, runs acceptance + forbidden-diff +
> metrics, fires the RETRO → DONE transition — and delegates the
> retro artifact to the Memory organ via **mechanical evidence
> indexing**.
>
> `memory-cli learn` was the v0.9 semantic-feed path. It is forbidden
> under Trinity Constitution v1.0 (Article IX — Memory Discipline).
> This contract codifies the replacement.

## Role

`rrr` is the terminal governance gate (Organ Map §12). Its
responsibilities:

```text
- collect acceptance results
- run forbidden-path diff
- compute session metrics
- write the retro artifact (deterministic envelope)
- fire RETRO → DONE
- delegate retro indexing to memory-cli (Article IX)
- emit delegation audit (Article X / XIX)
- (optionally) suggest pin (Article V / closing principle 2)
- print next-step hint
```

`rrr` is **not** authorised to:

```text
- run memory-cli learn / promote / verify / trace / embed / similar
- synthesise semantic lessons (root cause / insight / future doctrine)
- auto-pin retros
- silence delegation failures
- mutate state without going through Kernel
```

## Constitutional Anchoring

- **Article III** — AI Cannot Govern Itself. `rrr` does not declare meaning; the operator does.
- **Article IV** — Separation of Responsibilities. `rrr` is the Retro/Closure gate; semantic meaning is the Retro organ's or the Human's role.
- **Article V** — Kernel Authority. `rrr` invokes the gate; it does not act as Verifier or Planner.
- **Article IX** — Memory Discipline. Memory retrieves evidence; it does not derive truth. `memory-cli index` is mechanical; `memory-cli learn` is not.
- **Article X** — Audit Discipline. Every delegated call is auditable. Article XIX makes this concrete: hidden orchestration is forbidden.
- **Article XIV** — Critical Gates. Failure visibility (Article XXIII) is mandatory regardless of tier.
- **Article XX** — Passive Core. `rrr` runs only on explicit invocation.
- **Article XXIII** — Failure Visibility. Best-effort failure is NEVER silenced; severity is reported per Decision Velocity Tier.
- **Addendum §B** — Decision Velocity Tiers (HOT / WARM / COLD) drive the severity of a memory-index failure.

## Delegation Pipeline

```text
rrr (Kernel + Ritual Controller)
  ↓
  writes:  .ai/memory/retros/NNNN_<timestamp>_<slug>.md  (retro artifact)
  ↓
  delegates:  memory-cli index <retro-path>     ← Article IX compliant
  ↓
  records:  audit event 'rrr.delegated_call'   ← T4
  ↓
  records:  audit event 'rrr.completed' with memory_index summary
  ↓
  optionally:  prints suggest-pin hint           ← T1 + closing principle 2
  ↓
  fires:  RETRO → DONE
```

## Forbidden Patterns (lint at the source level)

The following substrings MUST NOT appear in `.ai/cli/commands/rrr.py`:

```text
memory-cli learn
learn --file=
"memory_learn"
'memory_learn'
```

The following call shapes are forbidden in the rrr code path:

```text
call_tool(..., "memory-cli", "pin ...")    ← rrr never auto-pins
call_tool(..., "memory-cli", "promote ...")
call_tool(..., "memory-cli", "verify ...")
call_tool(..., "memory-cli", "trace ...")
call_tool(..., "memory-cli", "embed ...")
call_tool(..., "memory-cli", "similar ...")
```

## Tightening Mandates (T1–T4) from Phase 0 BREAK_GLASS

### T1 — No semantic synthesis inside `rrr`

```text
rrr MUST NOT autonomously generate semantic lessons
(root cause, insight, future recommendation, doctrine change).
```

If semantic content is needed, it MUST come from one of:

```text
- retro-cli (future organ — PRD §8.11)
- planner / advisory AI (an AI other than rrr itself)
- a human author
```

`rrr` merely attaches the artifact.

### T2 — Deterministic memory-cli index

Lives in `TRINITY_MEMORY_EXACT_SURFACE_V1.md` (Phase 2 deliverable):

```text
memory-cli index MUST NOT mutate source content.
Chunk boundaries MUST be reproducible:
  - line-based
  - byte-range-based
  - deterministic tokenizer
Same input bytes → same chunk hashes, always.
```

memory-cli v0.1 already enforces this in `lib/v01/chunks.js`
(fixed 200-line windows, line + byte ranges, sha256 per chunk).

### T3 — Severity-by-tier on best-effort failure

| Decision Velocity Tier (Addendum §B) | memory-cli index failure → |
|---|---|
| **HOT**  | warning printed; `rrr` completes; audit records `memory_index_severity: "warning"` |
| **WARM** | FAILED_VISIBLE printed; `rrr` completes; audit records `memory_index_severity: "degraded"` |
| **COLD** | red block printed; `rrr` records `memory_index_severity: "block"`; caller MUST treat as required-failure (gate consequence) |

Closed-conservative default: any unknown / missing tier → WARM.

```text
Invisible best-effort failure is unconstitutional regardless of tier.
```

### T4 — Delegation Audit Event

Every rrr → organ delegation emits:

```json
{
  "type": "rrr.delegated_call",
  "details": {
    "session_id": "<sid>",
    "tool": "memory-cli",
    "action": "index",
    "target": ".ai/memory/retros/NNNN_*.md",
    "result": "PASS|FAIL",
    "artifact_sha256": "<hex sha256 of the retro file>",
    "workflow_id": "<sid>"
  }
}
```

Plus the existing `rrr.completed` event carries:

```json
{
  "tier": "HOT|WARM|COLD",
  "memory_index": {"ok": true|false, "indexed_new": ..., ...},
  "memory_index_severity": "pass|warning|degraded|block"
}
```

```text
Delegation without audit = hidden orchestration.   (Article XIX)
```

## Pin Suggestion Protocol

After the delegation audit, if the session contains a transition with
`decided_by: "human"` (e.g. operator approved `ddd`), `rrr` prints:

```text
suggest: this session contains a human decision. To mark the retro
canonical, run
  memory-cli pin <retro-path> --as=retro-<slug> --reason='<your reason>'
(rrr will never auto-pin; pinning is authority decision.)
```

This is **stdout-only**, never recorded in the audit chain as a
decision. It is a courtesy notice; the human pins.

```text
Memory indexing preserves history.   (closing principle 2)
Memory pinning confers authority.
```

## Acceptance Contract

```yaml
workflow: feat-kernel-rrr-v01-memory-surface
allowed_mutation_paths:
  - .ai/cli/commands/rrr.py
  - .ai/cli/tests/test_rrr_memory_learn_false_negative.py
  - .ai/cli/tests/test_rrr_v01_memory_surface.py
  - docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md
required_checks:
  - rrr does not call memory-cli learn
  - rrr calls memory-cli index
  - audit field is memory_index (not memory_learn)
  - rrr emits rrr.delegated_call event with the T4 shape
  - severity-by-tier helper returns correct mapping
  - rrr never auto-pins
  - pin suggestion fires only on decided_by:human transition
  - tests updated
forbidden_patterns:
  - memory-cli learn
  - confidence=
  - embedding
  - auto-tag
  - auto-pin
```

## Versioning

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-12 | Initial contract — Phase 1 of the organ refactor. |

Future revisions: Article XXIX (Constitutional Amendment) applies.

## Closing

```text
rrr owns closure.
rrr does not own meaning.

rrr may terminate workflows.
rrr may not synthesize institutional memory.

Memory indexing preserves history.
Memory pinning confers authority.
```
