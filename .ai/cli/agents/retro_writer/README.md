# `retro_writer` agent

**Authority:** RRR Delegation Contract T1 (mechanical/semantic split) · RC Article XVIII (Retro Writer row) · Constitution v1.0 Articles III (proposal-only), IV (separation), IX (exact-evidence), XVI (least authority), XVII (secret handling), XX (passive core).

**SIXTH and FINAL in-house Trinity agent.** Composes the SEMANTIC retro layer (Lessons Learned / Patterns Observed / Doctrine Claims / Anti-Patterns) DISTINCT from rrr's MECHANICAL T1 retro. The agent NEVER modifies rrr's mechanical output.

## T1 split (runtime artifacts)

Spec authority: [`docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md`](../../../../docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md).

| Artifact | Owner | Content | Where it lives |
|---|---|---|---|
| `retro_envelope.md` | `ai rrr` (kernel, mechanical) | YAML frontmatter + body for the 13 schema-locked fields in `RRR_OUTPUT_FIELDS` (acceptance results, forbidden diff, transitions, audit anchor, memory-index result, etc.) per spec §3.1/§4 | `<session>/THINK/retro_envelope.md` (kernel-written every rrr) |
| `RETRO.md` | `ai rrr` (kernel, mechanical block) | Verdict, metrics, transitions, acceptance evidence, forbidden-path diff — written from rrr's deterministic capsule | `<session>/THINK/RETRO.md` (kernel-written every rrr) |
| `RETRO_LESSONS.md` | `ai rrr --with-lessons` (kernel writes; **this agent proposes the body**) | The agent's stdout — exactly 4 H2 sections of semantic prose; kernel captures stdout and saves it; fail-soft if agent errors or times out | `<session>/THINK/RETRO_LESSONS.md` (only when `--with-lessons` is passed and the agent succeeds) |
| Indexed retro copy | `ai rrr` (kernel) | mirror of the mechanical retro for `memory-cli index` per spec §6 | `.ai/memory/retros/NNNN_*.md` |

The agent NEVER writes any of those files itself — it emits markdown to stdout. The kernel's `rrr` command (when invoked with `--with-lessons`) shells out to this agent, captures stdout, and saves it as `RETRO_LESSONS.md` alongside the mechanical artifacts. The agent NEVER modifies `retro_envelope.md`, `RETRO.md`, or the indexed retro copy — the split is constitutional (RRR Delegation Contract T1).

## Output

Markdown body to stdout with EXACTLY 4 H2 sections in this order:

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

### Kernel-driven (recommended)

The kernel invokes the agent automatically when you pass `--with-lessons` to `ai rrr`:

```bash
# Run rrr and have the kernel save the semantic layer to THINK/RETRO_LESSONS.md
bash .ai/cli/ai rrr --with-lessons
```

Fail-soft: if the agent errors or times out (120 s), rrr still completes normally — only the optional `RETRO_LESSONS.md` is skipped. Skipped under `--dry-run` and `--retroactive`.

### Direct wrapper invocation (advanced)

Run from **project root** — no `cd .ai &&` prefix needed.

```bash
# Compose semantic retro for an active session (RETRO.md + plan_envelope.json must already exist)
bash .ai/cli/agent retro_writer draft --session-path .ai/sessions/0001_...
```

### Direct module invocation (power users / scripts)

```bash
cd .ai && python3 -m cli.agents.retro_writer draft --session-path /abs/path/to/session
```

## Article XXVIII

| Field | Value |
|---|---|
| Role | Retro Writer (RC Article XVIII; RRR Delegation Contract T1 semantic half) |
| Authority | none — proposal only |
| Inputs | session path containing `THINK/RETRO.md` + `THINK/plan_envelope.json` (both required) |
| Outputs | Markdown body to stdout (4 H2 sections, ≥200 words) |
| Artifacts | none persisted by the agent. Kernel `rrr --with-lessons` captures stdout and writes `THINK/RETRO_LESSONS.md` |
| State | stateless |
| Failure | ValidationError / LLMError → non-zero exit + redacted stderr; kernel fail-soft (skips lessons file, rrr continues) |
| Audit | emits `retro_writer.invoked` / `retro_writer.proposed` / `retro_writer.failed` + inherited `llm.call_*` |
| Security | RETRO.md + envelope + audit summary are `markdown_escaped` / `json_string` data (RC Article XVI); credential redaction (Article XVII) |

## Completes the in-house agent chain

| Ritual | Agent | Status |
|---|---|---|
| sss | session_bootstrap | done |
| vvv | clarification_helper | done |
| nnn | plan_helper | done |
| gogogo | executor_helper | done |
| ddd | presentation_synthesizer | done |
| **rrr** | **retro_writer (this)** | done — **FINAL** |
| close | (mechanical, no agent) | — |

After this agent lands, every ritual seat that needs LLM-driven proposing has a contracted, audited, in-house organ. Main-conversation Claude is fully a coordinator.
