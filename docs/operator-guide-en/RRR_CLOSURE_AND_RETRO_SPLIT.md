---
title: "rrr Closure and the Retro Split"
audience: "Operator (human + AI agent)"
last-updated: "2026-05-24"
---

# rrr Closure and the Retro Split

`rrr` is the **terminal closure organ** of a Trinity session. It is not a
"reflection step". It does not write lessons. It does not pin doctrine.
What it does is mechanical and bounded.

The semantic reflection — "what worked / what failed / what we learned" —
is a **separate organ**. This chapter explains the split, the four
artifacts it produces (three mandatory + one optional), and the operator
playbook around them.

Canonical spec (read this if anything below feels ambiguous):
[`docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md`](../specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md).

## What `rrr` Actually Does

When you run `bash .ai/cli/ai rrr`, the kernel runs three deterministic
checks against the active session and writes one canonical artifact.

```text
1. Acceptance evidence
   - Read THINK/03_ACCEPTANCE.yaml
   - Run each A* command in /bin/sh
   - Record actual_exit vs expect_exit per criterion

2. Forbidden-diff
   - Compare working tree against baseline_untracked (snapshotted at sss)
   - Reject writes outside the plan's allowed_paths
   - Reject writes to .ai/policies/** and .ai/audit/** (mutation)

3. Transition + chain accounting
   - Count graph.transition events for the session
   - Sum gogogo verdicts (pass / fail / unverified / retry / needs_human)
   - Anchor the per-session audit chain head + last_seq
```

The output of those three checks lands as a single closure record. No
prose. No opinions. No "the session went well".

## Why the Split Exists

Two constitutional articles force the split.

**Article IX — Memory Discipline** says, verbatim:

```text
Memory retrieves evidence.
It does not govern meaning.
```

If `rrr` wrote lessons, `rrr` would be governing meaning. That is the
Article IX violation that the legacy `rrr.py` carried for months. Phase 12
fixed it by removing semantic synthesis from the closure path entirely.

**Article IV — Separation of Responsibilities** assigns post-work
reflection to the `Retro` organ, not the `Kernel`. `rrr` is a kernel
command. A kernel command that also authored reflection would be a
textbook role-collapse violation.

The boundary contract (spec §2.3) is four lines long:

```text
rrr writes facts.
retro writes meaning.
human pins authority.
audit records all three.
```

If any of those four lines stops being true, you have a constitutional
amendment on your hands, not a refactor.

## The Four Artifacts

Three are written on every `rrr` invocation. The fourth — `RETRO_LESSONS.md`
— is **optional** and only appears when the operator passes `--with-lessons`.

| # | Artifact | Schema | Author | Trigger | Mechanical / Semantic | Where it lives |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `retro_envelope.md` | `trinity.retro_envelope.v1` (13 fields, frozen) | `rrr` (kernel) | every `rrr` | Mechanical | `<session>/THINK/retro_envelope.md` |
| 2 | `RETRO.md` | `trinity.retro_md.v1` | `rrr` (kernel) | every `rrr` | Mechanical (header rendered from envelope data) | `<session>/THINK/RETRO.md` |
| 3 | **`RETRO_LESSONS.md`** | none (free-form markdown) | kernel writes file from `retro_writer` agent stdout | **OPTIONAL — only with `bash .ai/cli/ai rrr --with-lessons`** | Semantic (proposal-only) | `<session>/THINK/RETRO_LESSONS.md` |
| 4 | Indexed retro copy | mirror of `RETRO.md` | `rrr` copies + `memory-cli index` reads | every `rrr` | Mechanical | `.ai/memory/retros/NNNN_<ts>_<slug>.md` |

### 1. `retro_envelope.md` — the deterministic record

This is the closure record. Its frontmatter is closed at exactly thirteen
fields per `RRR_OUTPUT_FIELDS` in `.ai/cli/core/retro_rrr_contract.py`:

```text
session_id            ts_started        ts_closed
duration_seconds      acceptance_results
forbidden_diff_status baseline_untracked
audit_chain_status    transition_count  gogogo_verdicts
tier                  memory_index_result
artifact_paths
```

Downstream consumers — `presentation_renderer`, `close`, the DDD packet
builder — read this file as the source of truth for "what mechanically
happened in this session". They do not parse `RETRO.md`. Adding a field
to the envelope is an Article XXIX amendment.

### 2. `RETRO.md` — kernel mechanical record (human-readable mirror of the envelope)

`rrr` always writes `RETRO.md` from the kernel side. Its content is
**mechanical only**: the same acceptance / forbidden-diff / transition
data as `retro_envelope.md`, rendered as prose so a human can scan it
without parsing the frontmatter. `rrr` itself does not write any
"Lessons" / "What worked" prose into this file — that semantic surface
lives in `RETRO_LESSONS.md` (artifact #3, optional).

### 3. `RETRO_LESSONS.md` — optional semantic proposal from `retro_writer`

This file exists **only** when the operator opts in by passing
`--with-lessons` on the `rrr` invocation. When the flag is present, the
kernel shells out to the in-house `retro_writer` agent and writes the
agent's stdout verbatim to `<session>/THINK/RETRO_LESSONS.md`. The agent
NEVER mutates `RETRO.md` (its own contract forbids it); `RETRO_LESSONS.md`
is a side-file that lives next to it.

```bash
# Mechanical-only retro (default — RETRO_LESSONS.md is NOT created)
bash .ai/cli/ai rrr

# Mechanical retro + semantic side-file from retro_writer
bash .ai/cli/ai rrr --with-lessons
```

`retro_writer` is **proposal-only**. The operator reviews
`RETRO_LESSONS.md` before treating it as the session's reflection of
record. If the proposal is wrong, edit it by hand — the agent has no
authority. If the agent times out or returns empty stdout, the kernel
prints a yellow warning and skips the file (the rest of the `rrr` run
still completes cleanly).

### 4. `.ai/memory/retros/NNNN_*.md` — indexed for cross-session recall

After writing `RETRO.md`, `rrr` copies the file under
`.ai/memory/retros/` with the next sequential `NNNN_<ts>_<slug>.md` name
and delegates to `memory-cli index` to make it discoverable from future
sessions. The delegation envelope is captured verbatim into
`retro_envelope.md` under `memory_index_result` — `rrr` does not
interpret, summarise, or filter it.

The indexed copy is evidence preservation, not doctrine. It is
retrievable through `memory-cli search`. It is **not** canonical until a
human pins it (see playbook below).

## Operator Playbook

### When `rrr` fails on acceptance

Read `RETRO.md`. The "Acceptance evidence" section lists each A* command
with its expected vs actual exit code. Three frequent fixes:

```text
1. The command uses bash syntax in /bin/sh
   Symptom: A* fails with "syntax error" or "[[: not found"
   Fix: rewrite using POSIX sh; arrays / [[ ]] / <(...) are not portable
   (see memory feedback_acceptance_command_sh_vs_bash)

2. grep -F pattern uses curly quotes / em-dash / nbsp from a copy-paste
   Symptom: A* fails silently with exit 1 even though the substring "is in"
   the file when you eyeball it
   Fix: copy the substring directly from the target file, then update BOTH
   THINK/03_ACCEPTANCE.yaml AND .state/plan.json
   (see memory feedback_acceptance_grep_char_mismatch)

3. Plan listed the child file but not the parent file in allowed_paths
   Symptom: A* tries to verify an edit that forbidden-diff rejected
   Fix: amend plan to include the parent (e.g. audit.py when adding an
   audit_<sub>.py subcommand)
   (see memory feedback_typer_subcommand_needs_parent_in_allowed_paths)
```

After fixing, re-run `bash .ai/cli/ai rrr`. It is idempotent on identical
inputs.

### When you want the semantic side-file (`--with-lessons`)

By default `rrr` writes only the mechanical artifacts (#1, #2, #4). To
also generate `RETRO_LESSONS.md` (#3 — the semantic proposal from
`retro_writer`), invoke the flag explicitly:

```bash
bash .ai/cli/ai rrr --with-lessons
```

The kernel will shell out to the in-house agent at
`.ai/cli/agents/retro_writer/`, capture its stdout, and write the file at
`<session>/THINK/RETRO_LESSONS.md`. Expect:

```text
- Agent runs with a 120s timeout.
- On non-zero exit OR empty stdout: kernel prints a yellow warning and
  skips the file. The rrr run still completes successfully.
- The agent NEVER edits RETRO.md — RETRO_LESSONS.md is always a separate
  file.
- The file is proposal-only. Review it. Edit it. Don't treat agent prose
  as authority.
```

If you re-run `rrr --with-lessons` on the same session, the file is
overwritten with the latest agent stdout — there is no append mode.

### When `close` gate-locks after a successful `rrr`

`close` requires **both** verification streams to be green before it will
archive the session:

```bash
bash .ai/cli/ai verify dev
bash .ai/cli/ai verify prod
```

The error message historically only mentioned `prod`; dev is also
required. If either is missing or red, `close` refuses with a gate-lock.
Run both, confirm both PASS, then retry `close`.

### Pinning a retro as canonical doctrine (human-only)

If a retro captures a pattern you want future sessions to cite, **you**
pin it. Not `rrr`. Not `retro_writer`. Not any agent.

```bash
memory-cli pin .ai/memory/retros/0123_2026-05-24_my-task.md \
              --as=retro-my-task \
              --reason='canonical pattern for X'
```

`--reason` is required. An empty reason is a constitutional failure
(Article XIII reserves irreversible actions to explicit human authority).
The pin event audits as `decided_by: human`.

`rrr` MAY print a stdout suggestion to pin when the session contains a
`decided_by: human` transition. That is courtesy text, not a decision.
Auto-pinning, auto-promoting, or any kernel-side pin emission is
forbidden.

## What `rrr` MUST NOT Do (Forbidden Patterns)

Per spec §3.2, `rrr.py` source MUST NOT contain any of these substrings:

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

A source-level lint enforces this. The only `memory-cli` verb that `rrr`
may invoke is `index`, because indexing is mechanical evidence
preservation. Every other verb is either semantic (`learn`, `verify`,
`embed`, `similar`) or authority-laden (`pin`, `promote`) and therefore
out of `rrr`'s authority surface (Article XVI — Least Authority).

`rrr` also MUST NOT write any of the following into `retro_envelope.md`:

```text
- "What worked" / "What failed" prose paragraphs
- "Lessons learned" / "Root cause" / "Future recommendation" sections
- Value judgments
- Doctrine candidates
- Comparative quality assessments vs prior sessions
- Predictions about future sessions
- Suggestions for policy changes
- Embeddings / vectors / similarity scores
- Auto-pin / auto-promote actions
```

That list is the operational expansion of Article IX. If you see any of
those phrases inside `retro_envelope.md`, the closure path has drifted
and the spec has been violated.

## Cross-References

- Canonical spec: [`docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md`](../specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md)
- Python contract: `.ai/cli/core/retro_rrr_contract.py`
- RRR Delegation Contract v1.0: [`docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md`](../constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md)
- Constitution Article IX (Memory Discipline) + Article IV (Separation): [`docs/constitution/TRINITY_CONSTITUTION_V1.md`](../constitution/TRINITY_CONSTITUTION_V1.md)
- Ritual loop overview: [`03_RITUAL_LOOP.md`](03_RITUAL_LOOP.md)

```text
rrr writes facts.
retro writes meaning.
human pins authority.
audit records all three.
```
