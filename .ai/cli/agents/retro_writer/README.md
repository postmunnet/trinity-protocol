# `retro_writer` agent

**Authority:** RRR Delegation Contract T1 (mechanical/semantic split) · RC Article XVIII (Retro Writer row) · Constitution v1.0 Articles III (proposal-only), IV (separation), IX (exact-evidence), XVI (least authority), XVII (secret handling), XX (passive core).

**SIXTH and FINAL in-house Trinity agent.** Composes the SEMANTIC retro layer (lessons / patterns / doctrine / anti-patterns) DISTINCT from rrr's MECHANICAL T1 retro (`RETRO.md`).

## T1 split

| Artifact | Owner | Content | Where it lives |
|---|---|---|---|
| `RETRO.md` | `ai rrr` (kernel, mechanical) | Verdict, metrics, transitions, acceptance evidence, forbidden-path diff | Written automatically at rrr time |
| `RETRO_LESSONS.md` | `retro_writer` agent (operator-saved) | Lessons Learned, Patterns Observed, Doctrine Claims, Anti-Patterns | Operator captures stdout and saves manually |

The agent NEVER modifies `RETRO.md`. The split is constitutional (RRR Delegation Contract T1).

## Output

Markdown body with EXACTLY 4 H2 sections in this order:

```markdown
## Lessons Learned
<paragraphs; ≥80 words>

## Patterns Observed
<paragraphs; ≥60 words>

## Doctrine Claims
<rule-form claims OR literal "(none)">

## Anti-Patterns
<entries OR literal "(none)">
```

Validator rejects:
- Missing or out-of-order headings (case-sensitive, exact)
- H1 at top
- Total word count < 200
- Prose before the first `## Lessons Learned` heading

## Usage

### Wrapper (recommended)

Run from **project root** — no `cd .ai &&` prefix needed.

```bash
# Compose semantic retro for an active session (after rrr completed)
bash .ai/cli/agent retro_writer draft --session-path .ai/sessions/0001_...

# Capture for review then save
bash .ai/cli/agent retro_writer draft --session-path .ai/sessions/0001_... \
    > .ai/sessions/0001_.../THINK/RETRO_LESSONS.md
# operator reviews/edits THINK/RETRO_LESSONS.md before commit
```

### Advanced (direct module invocation)

```bash
cd .ai && python3 -m cli.agents.retro_writer draft --session-path /abs/path/to/session
```

## Article XXVIII

| Field | Value |
|---|---|
| Role | Retro Writer (RC Article XVIII; RRR Delegation Contract T1 semantic half) |
| Authority | none — proposal only |
| Inputs | session path containing RETRO.md + plan_envelope.json (both required) |
| Outputs | Markdown body to stdout (4 H2 sections, ≥200 words) |
| Artifacts | none persisted (operator saves manually) |
| State | stateless |
| Failure | ValidationError / LLMError → non-zero exit + redacted stderr |
| Audit | emits retro_writer.invoked/.proposed/.failed + inherited llm.call_* |
| Security | RETRO.md + envelope + audit summary are markdown_escaped/json_string data (RC Article XVI); credential redaction (Article XVII) |

## 🏆 Completes the in-house agent chain

| Ritual | Agent | Status |
|---|---|---|
| sss | session_bootstrap | ✅ |
| vvv | clarification_helper | ✅ |
| nnn | plan_helper | ✅ |
| gogogo | executor_helper | ✅ |
| ddd | presentation_synthesizer | ✅ |
| **rrr** | **retro_writer (this)** | ✅ **FINAL** |
| close | (mechanical, no agent) | — |

After this agent lands, every ritual seat that needs LLM-driven proposing has a contracted, audited, in-house organ. Main-conversation Claude is fully a coordinator.
