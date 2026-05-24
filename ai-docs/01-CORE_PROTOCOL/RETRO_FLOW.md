---
title: "Retro / RRR Flow — the 4-Artifact Split"
status: stable
last-updated: 2026-05-24
source: "docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md"
audience: "AI agents recalling protocol knowledge during session work; future memory-cli indexer"
constitutional-anchor: ["Article III", "Article IV", "Article IX", "Article XVI", "Article XVII", "Article XX", "Article XXIX"]
---

# Retro / RRR Flow — the 4-Artifact Split

> **Core invariant** (spec §2.3):
> ```text
> rrr writes facts.
> retro writes meaning.
> human pins authority.
> audit records all three.
> ```

In Trinity, "retro" is not a single artifact. The terminal closure of a
session splits into **two organs and four artifacts**: a deterministic
closure record produced by the kernel (`rrr.py`), a mechanical RETRO.md
stub, an **optional** semantic reflection sourced from the advisory
`retro_writer` agent but file-written by the kernel, and an indexed
retro artifact written by `memory-cli index` for downstream evidence
retrieval. Article IV forbids any single component from owning both
"what mechanically happened" and "what it means" — so reading any one
of these artifacts in isolation is reading half the story.

For the workflow sequence that gets you to this boundary
(`sss → vvv → nnn → gogogo → ddd → rrr → close`), see
[WORKFLOW.md](./WORKFLOW.md). This file describes what AI agents
encounter **at and after `rrr`**.

---

## The 4 artifacts

| # | Artifact | Format | Trigger | Writer (file I/O) | Source of content | Audience an AI agent should assume |
|---|---|---|---|---|---|---|
| 1 | `<session>/THINK/retro_envelope.md` | YAML frontmatter + Markdown body, schema `trinity.retro_envelope.v1` | every `rrr` | `rrr.py` (kernel, deterministic) | kernel (mechanical closure facts) | Verifier + future memory-cli queries. **Read this for facts** — acceptance results, forbidden-diff status, audit-chain head, timing. Do NOT treat its body as interpretation; it summarises mechanical results only. |
| 2 | `<session>/THINK/RETRO.md` | Markdown stub with conventional H2 headings | every `rrr` | `rrr.py` (kernel, deterministic) | kernel scaffold (operators or future tooling may fill the body) | Operator + reviewers. The mechanical stub the kernel always emits so a downstream reader can rely on the file existing. Do not assume semantic content lives here by default — see #3. |
| 3 | `<session>/THINK/RETRO_LESSONS.md` | Free-form Markdown (the agent's full stdout) | **only when `--with-lessons` is passed to `ai rrr`** | `rrr.py` (kernel writes the file from agent stdout) | `retro_writer` agent (advisory, semantic) — kernel never edits the body | Operator + reviewers + future memory-cli queries. **Read this for meaning** — lessons, patterns, doctrine, what worked / what failed. An AI proposing a follow-up plan reads this; an AI making a gate decision does NOT rely on it. **Do not expect this file to exist** unless `--with-lessons` was used. |
| 4 | `.ai/memory/retros/NNNN_*.md` | Markdown chunks suitable for memory-cli indexing | every `rrr` | `rrr.py` + `memory-cli index` | copy of `retro_envelope.md` (and any companion artifacts) preserved for retrieval | The retrieval layer (Article IX evidence). AI agents do not author this — they may query it via `memory-cli` exact-only artifact evidence. |

What an AI agent **does** at each:

- **Encounters #1 (`retro_envelope.md`) while reading session state** → trust the frontmatter as the source of truth for closure facts; never amend its fields without an Article XXIX amendment.
- **Encounters #2 (`RETRO.md`) while proposing follow-up work** → treat as a stub scaffold the kernel guarantees; cite it as the canonical retro filename, but do not assume it carries the semantic body unless an operator (or `retro_writer` output explicitly merged in) has filled it.
- **Encounters #3 (`RETRO_LESSONS.md`) while looking for lessons, patterns, or doctrine** → read it; this is where `retro_writer`'s semantic content actually lands. If the file is missing, the operator did not run `ai rrr --with-lessons` and there is no advisory semantic retro for this session — do NOT fabricate one, and do NOT treat absence as failure. Pinning anything from this file is a separate human-only act (Article XIII).
- **Encounters #4 (`.ai/memory/retros/NNNN_*.md`) via memory-cli** → returns evidence chunks, never verdicts. Article IX: memory retrieves evidence, it does not govern meaning.

> **Authorship vs file-write boundary (Article IV).** For artifact #3 the
> `retro_writer` agent is the *source* of the semantic content but the
> *kernel* (`rrr.py`) performs the file write — the agent runs as a
> subprocess, the kernel captures its stdout, and the kernel persists it
> to `RETRO_LESSONS.md`. The agent never touches the filesystem of the
> session directly. This preserves the separation between advisory
> drafting (agent) and deterministic state mutation (kernel).

---

## Schema lock — `trinity.retro_envelope.v1`

The `RETRO_ENVELOPE_SCHEMA_VERSION` constant in
`.ai/cli/core/retro_rrr_contract.py` pins the frontmatter shape. Its
13 mechanical fields (`RRR_OUTPUT_FIELDS`, spec §3.1) are the **closed
contract** between rrr and any downstream consumer:

```text
session_id          ts_started           ts_closed
duration_seconds    acceptance_results   forbidden_diff_status
baseline_untracked  audit_chain_status   transition_count
gogogo_verdicts     tier                 memory_index_result
artifact_paths
```

This list is **FROZEN**. Adding, removing, or renaming a field requires:

1. An explicit Article XXIX amendment proposal in `docs/specs/`,
2. Human approval recorded as an artifact (`decided_by: human`),
3. A version bump of the schema constant,
4. An audit entry on the chain.

An AI agent that "improves" the envelope by adding a `confidence` or
`summary` field has just committed a constitutional violation. Don't.

---

## Boundaries — what `rrr.py` MUST NOT do

These are the source-level forbidden substrings encoded in
`RETRO_FORBIDDEN_PATTERNS` (spec §3.2). They derive from Article IX
(Memory cannot govern meaning) and Article XVI (Least Authority —
unknown authority is denied):

```text
memory-cli learn
learn --file=
"memory_learn"
'memory_learn'
call_tool(..., "memory-cli", "pin ...")
call_tool(..., "memory-cli", "promote ...")
call_tool(..., "memory-cli", "verify ...")
call_tool(..., "memory-cli", "trace ...")
call_tool(..., "memory-cli", "embed ...")
call_tool(..., "memory-cli", "similar ...")
```

In plain language: `rrr` may **invoke `memory-cli index`** (mechanical
preservation) and **nothing else against memory-cli**. It MUST NOT
learn, pin, promote, verify, trace, embed, or compute similarity. It
MUST NOT write "what worked / what failed / lessons / root cause /
recommendations" prose into `retro_envelope.md`. It MUST NOT
self-certify the session as successful — Article III: AI cannot govern
itself.

When an AI agent proposes changes to `rrr.py`, the diff is auto-rejected
if it introduces any of the substrings above. The agent should propose
the change against `retro_writer` (the advisory organ) instead, where
semantic content legitimately lives.

Article XX (Passive Core) closes the loop: `rrr` runs only on explicit
operator invocation (`bash .ai/cli/ai rrr`). It does not self-trigger,
self-heal, or background-crawl session state. Same for `retro_writer` —
it drafts only when invoked, never on its own initiative.

---

## Where to look

Quick reference table for AI agents resolving a retro-related question:

| Question | File / Source |
|---|---|
| What fields go in `retro_envelope.md`? | `.ai/cli/core/retro_rrr_contract.py` → `RRR_OUTPUT_FIELDS` (13 fields, frozen) |
| What sections does `retro_writer` add to `RETRO.md`? | `.ai/cli/core/retro_rrr_contract.py` → `RETRO_MD_SECTIONS` (advisory; agent MAY extend) |
| What rrr.py MUST NOT call / write? | `.ai/cli/core/retro_rrr_contract.py` → `RETRO_FORBIDDEN_PATTERNS` |
| What severity values can `memory_index_result` take? | `.ai/cli/core/retro_rrr_contract.py` → `MEMORY_INDEX_SEVERITY` (pass / warning / degraded / block) |
| How is a field classified mechanical vs semantic? | `.ai/cli/core/retro_rrr_contract.py` → `mechanical_vs_semantic(field_name)` |
| Operator playbook (EN / TH)? | `docs/operator-guide-en/RRR_CLOSURE_AND_RETRO_SPLIT.md` · `docs/operator-guide-th/RRR_CLOSURE_AND_RETRO_SPLIT.md` |
| Canonical spec (the only authoritative source)? | `docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md` |
| Where the workflow that leads here is defined? | `ai-docs/01-CORE_PROTOCOL/WORKFLOW.md` |

---

## Reading order for AI agents

1. **First read** — `docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md` is
   authoritative. Anything in this Knowledge Brain entry that contradicts
   the spec is wrong; the spec wins (Article XXV priority order).
2. **Code reference** — `.ai/cli/core/retro_rrr_contract.py` is the
   declarative Python mirror. The frozensets (`RRR_OUTPUT_FIELDS`,
   `RETRO_FORBIDDEN_PATTERNS`, `MEMORY_INDEX_SEVERITY`,
   `RETRO_MD_SECTIONS`) are the load-bearing invariants.
3. **Operator playbook** — the bilingual `RRR_CLOSURE_AND_RETRO_SPLIT.md`
   guides describe the human-facing procedure; the AI agent reads them
   to understand what the operator expects to see.

If any of those three disagree, escalate as `NEEDS_HUMAN` — do not
reconcile silently. Article XXIX requires every amendment to flow
through explicit human approval.
