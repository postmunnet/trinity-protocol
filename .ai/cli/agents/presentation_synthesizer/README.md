# `presentation_synthesizer` agent

**Authority:** Constitution Addendum §E (Cognitive Presentation) · Organ Map #16 · RC Article XVIII (Presentation Synthesizer row) · Constitution v1.0 Articles III (proposal-only), IV (separation), XVI (least authority), XVII (secret handling), XX (passive core).

**Fifth in-house Trinity agent.** Produces a 3-layer `presentation_packet` for the `ddd` gate to read.

## Output

```json
{
  "synthesis": {
    "one_line": "...",
    "what_landed": "...",
    "verdict_summary": "...",
    "risk_remaining": "..."
  },
  "dissent": [
    {"topic": "...", "view": "...", "evidence_ref": "..."}
  ],
  "raw": {
    "plan_envelope_path": "THINK/plan_envelope.json",
    "retro_path": "THINK/RETRO.md" or null,
    "audit_event_count": <int>,
    "gogogo_verdicts": {"PASS": <int>, "FAIL": <int>, "UNVERIFIED": <int>},
    "needs_human_count": <int>,
    "final_graph_state": "...",
    "artifact_hashes": [{"path": "...", "sha256": "..."}]
  },
  "notes": "<methodology + caveats>"
}
```

## Discipline

- **Dissent preserved** (Addendum §E). Empty dissent IS valid; smoothed-away dissent is NOT.
- **Synthesis is friendly, never truth.** Truth layer is `raw`.
- **No interpretation in `raw`.** Just pointers + counts + hashes.

## Usage

### Wrapper (recommended)

Run from **project root** — no `cd .ai &&` prefix needed.

```bash
bash .ai/cli/agent presentation_synthesizer draft --session-path .ai/sessions/0001_...
```

### Advanced (direct module invocation)

```bash
cd .ai && python3 -m cli.agents.presentation_synthesizer draft --session-path /abs/path/to/session
```

## Article XXVIII

| Field | Value |
|---|---|
| Role | Presentation Synthesizer (Article XVIII row; Organ #16) |
| Authority | none — proposal only |
| Inputs | session path with plan_envelope.json (required) + optional RETRO.md + filtered audit events |
| Outputs | 3-layer JSON packet to stdout |
| Artifacts | none persisted (operator captures stdout) |
| State | stateless |
| Failure | ValidationError / LLMError → non-zero exit + redacted stderr |
| Audit | emits presentation_synthesizer.invoked/.proposed/.failed; inherits llm.call_* |
| Security | inputs are markdown_escaped/json_string data (RC Article XVI); credentials redacted (Article XVII) |

## Position

```
sss   → session_bootstrap (slug)
nnn   → plan_helper (plan_envelope)
vvv   → clarification_helper (5 answers)
gogogo → executor_helper (step proposals)
ddd   → presentation_synthesizer (this) ← cognitive packet for human review
rrr   → retro_writer (TBD, semantic lessons layer)
```
