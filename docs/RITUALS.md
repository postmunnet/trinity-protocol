# Trinity Rituals - Operator Reference

Language: English | [ไทย](RITUALS_TH.md)

This document is the operator-facing reference for the seven Trinity rituals.

For the narrative origin story behind these rituals, read [`ORIGIN.md`](ORIGIN.md).

The technical contract for state machines, schemas, audit format, and runtime
behavior lives in
[`constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md`](constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md)
and the related specs under [`specs/`](specs/).

---

## Quick Reference

| Ritual | When to use it | Main purpose |
|---|---|---|
| `sss` | Before starting a session | Create the session capsule and initial state snapshot |
| `vvv` | Before planning or execution | Define goal, scope, constraints, acceptance, and risk |
| `nnn` | After `vvv` passes | Normalize the goal into a plan, steps, and expected artifacts |
| `gogogo` | After the plan is accepted | Explicit execution gate |
| `ddd` | After execution | Inspect diff, damage, and scope creep from real files |
| `rrr` | After completion or failure | Turn the session into retro and memory handoff |
| `close` | At session end | Close with explicit final state |

Standard sequence:

```text
sss -> vvv -> nnn -> gogogo -> ddd -> rrr -> close
```

---

## `sss` - Session Capsule / Snapshot / Starting State

Use `sss` before starting meaningful work.

Its job is to create a session capsule and preserve the initial state before
changes begin.

It answers:

- What was the state at the start?
- Which important files existed?
- What context must be carried into the task?
- Where can we roll back if the work breaks?
- What is this session trying to change?

`sss` prevents a session from starting as an immediate edit. It starts by
creating a reference point.

---

## `vvv` - Goal / Scope / Constraint / Acceptance / Risk

Use `vvv` as the gate before planning or execution.

It forces five questions to be answered:

1. **Goal** - What does success look like?
2. **Scope** - What is in scope and out of scope?
3. **Constraint** - What must not be touched, changed, or attempted?
4. **Acceptance** - How will we know the work is really complete?
5. **Risk** - What failure mode matters most?

This matters because AI agents often act before they fully understand the
boundary of the task.

`vvv` defines the field before work begins.

---

## `nnn` - Normalize / Plan / Next Action

Use `nnn` to turn the clarified goal into an executable plan.

After goal and scope are known, `nnn` produces:

- plan
- steps
- dependencies
- expected artifacts
- verification path
- next action

The goal is not to make the AI think longer for its own sake. The goal is to
produce a plan that can be inspected before execution.

---

## `gogogo` - Explicit Execution Gate

Use `gogogo` when the human operator explicitly approves execution.

Before this gate existed, AI agents often started editing while the human was
still asking a question or exploring options.

`gogogo` creates a clear line between:

- thinking
- planning
- approved execution

Principle:

> Without an explicit execution gate, do not perform actions that materially
> change state.

---

## `ddd` - Diff / Inspect / Damage Check

Use `ddd` after execution to inspect what actually changed.

AI explanations can differ from the real diff. `ddd` checks the files and
artifacts, not just the agent's description.

It asks:

- What is the diff?
- Which files changed?
- Did anything outside scope change?
- Did scope creep occur?
- Does the change match the plan?
- Is there damage that needs rollback?

`ddd` reinforces the rule:

> Do not trust the explanation before seeing the diff.

---

## `rrr` - Retro / Lesson / Memory

Use `rrr` after completion or after an important failure.

Its job is to turn experience into a lesson.

It is not only a completion summary. It answers:

- What happened?
- What made the work succeed?
- What nearly failed?
- What pattern should be remembered?
- What should be done differently next time?
- Should a rule or verifier be added?

`rrr` is the bridge from one session to the next. It prevents important context
from disappearing into chat history.

In Trinity v0.1.0 ritual flow, `rrr` delegates memory handoff through
`memory-cli index`, not `memory-cli learn`.

---

## Retro artifacts

When `rrr` runs, Trinity produces **four distinct retro artifacts**. They are
intentionally separated so that mechanical closure (kernel-decided) and
semantic reflection (human or agent-authored) never collapse into one
write. The split is governed by
[`specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md`](specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md).

| # | Artifact | Path | Format | Writer | Trigger |
|---|---|---|---|---|---|
| 1 | Retro envelope | `<session>/THINK/retro_envelope.md` | YAML frontmatter, 13-field schema-locked (`trinity.retro_envelope.v1`) | kernel `rrr.py` | every `rrr` |
| 2 | Session retro report | `<session>/THINK/RETRO.md` | Markdown report (verdict, metrics, acceptance evidence) | kernel `rrr.py` | every `rrr` |
| 3 | **Semantic lessons** (optional) | `<session>/THINK/RETRO_LESSONS.md` | Markdown body ("What worked / What failed / Lessons / Followups") sourced from `retro_writer` agent stdout; kernel writes the file (the agent never touches disk directly) | kernel `rrr.py` (from `retro_writer` agent stdout) | **only with `--with-lessons` flag** |
| 4 | Memory retro | `.ai/memory/retros/NNNN_<date>_<slug>.md` | Markdown copy indexed by `memory-cli` (FTS5) | kernel `rrr.py` copies + indexes | every `rrr` |

Key invariants:

- The retro envelope schema is **FROZEN**. The 13 fields enumerated in
  `RRR_OUTPUT_FIELDS` (see `.ai/cli/core/retro_rrr_contract.py`) form a
  closed set. Adding, renaming, or removing a field requires an explicit
  **Article XXIX amendment** — proposal + rationale + impact analysis +
  human approval + version bump + audit entry. No silent edits.
- `retro_envelope.md` is the deterministic record. It carries no prose,
  no lessons, no value judgments — only mechanical fields derivable from
  session artifacts (acceptance results, forbidden-diff status, audit
  chain anchor, gogogo verdicts, artifact paths, memory index envelope).
- `RETRO.md` is the kernel-authored structural record (verdict, metrics,
  acceptance evidence). It is **always** written, never extended by the
  agent. Pinning a `RETRO.md` as canonical doctrine is human-only via
  `memory-cli pin`.
- `RETRO_LESSONS.md` is the **optional** semantic companion. Only fired
  when `rrr` is invoked with `--with-lessons`. The `retro_writer`
  in-house agent (proposal-only) emits the markdown body to stdout; the
  kernel `rrr.py` captures that stdout and writes it to disk as a
  separate file alongside `RETRO.md`. The agent never writes to the
  session directory itself.
- `retro_envelope.md` is read by `presentation_renderer.py` at `close`
  time to build the operator-facing `CLOSE_PACK.md`. Downstream
  consumers (Close, DDD, sibling CLIs) MUST reject any envelope whose
  `schema_version` is not `trinity.retro_envelope.v1`.

---

## `close` - Close Session / Final State

Use `close` to end a session with explicit state.

Without `close`, sessions tend to end ambiguously:

- Was the work really done?
- Did tests pass?
- Which artifacts matter?
- What remains pending?
- What risk remains?

`close` records:

- done or not done
- artifact locations
- verification result
- pending issues
- next step
- anything that should be carried into retro or memory

At that point, a session is not just a conversation. It becomes a unit of work
that can be closed.

---

## See Also

- [`ORIGIN.md`](ORIGIN.md) - origin story and rationale behind the rituals
- [`RITUALS_TH.md`](RITUALS_TH.md) - Thai version
- [`constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md`](constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md) - canonical contract
- [`operator-guide-en/03_RITUAL_LOOP.md`](operator-guide-en/03_RITUAL_LOOP.md) - ritual loop operator guide
- [`operator-guide-th/03_RITUAL_LOOP.md`](operator-guide-th/03_RITUAL_LOOP.md) - Thai ritual loop operator guide
- [`specs/INDEX.md`](specs/INDEX.md) - master spec index
