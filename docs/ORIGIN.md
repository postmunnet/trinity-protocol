# Origin of Trinity

Language: English | [ไทย](ORIGIN_TH.md)

Before explaining what Trinity is, it helps to explain where it came from.

Trinity did not start as a clean framework designed on paper. It grew from
real production problems, one failure mode at a time, until those practices
became a system.

---

## September 2025 - AI in Production Was Hard to Control

I was building a full production e-commerce website. AI coding agents were
becoming useful enough to try on real implementation work, so I started using
them to help write code.

The problems showed up quickly:

- AI changed things I did not ask it to change.
- AI edited the wrong place.
- AI exceeded the requested scope.
- AI guessed what I wanted and acted on that guess.
- AI said work was done without evidence I could verify.

At that point, I was not thinking about governance or control planes. I only
wanted the AI not to damage customer production work.

---

## The First Documents - AGENTS.md / CLAUDE.md

The first solution was simple: write rules in a file and make agents read them
before starting.

Those files described things like:

- workflow expectations
- boundaries
- files that must not be touched
- commands that must not be run
- codebase conventions
- how to verify before claiming completion

That helped, but it was not enough.

A document is an instruction, not enforcement. AI can read it, forget it,
misinterpret it, or lose it when the context gets long.

---

## When Documentation Was Not Enough - Retro

The next problems were repetitive:

- The rules existed, but AI still violated them.
- Long sessions caused agents to forget early constraints.
- Old problems had to be taught again in new sessions.
- Fixes that had worked before were not retrieved systematically.

So I started writing retro documents.

Every time an AI made a mistake, hit an unusual bug, or found an important fix,
I saved the lesson:

- what happened
- why it happened
- how it was fixed
- what must not be repeated next time
- how to verify the fix

When the same type of issue returned, I could say:

> We have seen this before. Go read the retro.

The agent could then find the prior fix and move faster.

That was the first clear lesson:

> AI does not remember the way production work needs it to remember.
> We have to build the memory system around it.

---

## Rituals Started as Short Codes

As I worked with AI more often, I saw that most tasks had recurring phases.

Before starting, we need to know the current state. Before execution, we need
scope. Before making changes, we need a plan. After changing code, we need
verification. After finishing, we need lessons.

If every step happens inside one long conversation, the phases blur together.

Sometimes I only wanted status, but the agent proposed a plan. Sometimes I
wanted analysis, but it jumped into editing files. Sometimes it claimed the
work was done without tests, diffs, or evidence.

So I began using short codes to mark the phase of work.

Instead of explaining the whole protocol every time, a short word could mean:

- check status before starting
- define goal, scope, and constraints
- plan before execution
- wait for explicit approval
- inspect the diff after changes
- verify before summary
- write retro after the work

At first, these short codes were just a better way to talk to AI. They stopped
agents from jumping directly from a question to code edits. Work became more
rhythmic: phase, gate, artifact, next step.

But production use exposed the limits of short codes:

- A short code can signal intent, but it does not enforce state.
- A short code can organize phases, but it does not require artifacts.
- A short code can request verification, but it does not distinguish claims
  from evidence.
- A short code can ask for a summary, but it does not create an audit trail.
- A short code helps conversation, but it is not enough for rollback,
  production promotion, multi-agent work, or long-running sessions.

That is where short codes started becoming a ritual protocol.

---

## From Short Codes to Ritual Protocol

The important shift was this: rituals should not be only conversational
shortcuts. They should become operating rules.

Each ritual needed a contract:

- which phase it belongs to
- what input it accepts
- what output it must produce
- what artifact it must leave behind
- whether the step can be skipped
- where human approval is required
- how failure is recorded
- what counts as evidence that the step passed

At that point, the short codes changed meaning.

They stopped being:

> short commands for talking to AI

and became:

> a protocol for governing AI-assisted work

The protocol introduced:

- **state** - every ritual must know the current phase
- **scope** - the system must know what is allowed and what is out of scope
- **constraint** - some actions are forbidden even if technically possible
- **artifact** - claims must be backed by files, logs, diffs, tests, or reports
- **gate** - important transitions require explicit approval
- **verifier** - the executor should not be the final judge
- **retro** - completed work becomes a lesson instead of disappearing into chat
- **snapshot** - risky work needs a rollback point
- **audit** - important actions leave a trace
- **close** - a session ends with explicit state, not drift

The goal was no longer simply making AI faster. The goal was making AI work
bounded, reviewable, recoverable, and unable to skip important steps without
evidence.

In short:

> The original short codes helped me talk to AI in a more structured way.
> Trinity rituals make it harder for AI to bypass the structure without proof.

For the ritual-level operator reference, see [`RITUALS.md`](RITUALS.md).

---

## Snapshot Saved My Sanity

The biggest practical problem with AI agents in production code was recovery:

> If it breaks something, how do I get back?

So I added workflow concepts that made experimentation less dangerous:

- `sss` - create a session capsule and initial state snapshot
- sandbox - test ideas in an isolated area first
- `do/dev` - implement and test in a development path
- `do/snapshot` - capture a rollback point before risky work or promotion
- `do/prod` - promote only after verification

If development broke, I could roll back to the snapshot. If tests and
verification passed, I could promote deliberately.

This changed the psychology of the work.

Before:

> Every enter key felt risky.

After:

> We can try it. If it breaks, we can roll back.

That reduced stress and kept AI agents inside safer boundaries, because state,
snapshot, rollback, and gates were part of the workflow.

---

## Multi-Agent Work in tmux

As problems became more complex, one agent often saw the problem from one
angle and missed important blind spots.

So I started experimenting with multiple agents:

- debate - agents argue different views of the same issue
- tmux multi-agent team - separate panes for separate angles
- planner / executor / verifier roles
- the human operator makes the final decision

This produced better coverage. One agent could catch another agent's blind
spot, and I did not have to trust a single answer immediately.

That made the next principle clear:

> The problem is not only making AI smarter.
> The problem is making multiple AIs work under one shared protocol.

---

## Why Not Log Everything?

Once the workflow started working, new questions appeared:

- If an agent works for a long time, how do we know where it went wrong?
- If there are multiple projects, how do we track state?
- If multiple agents run together, who did what?
- If a bug appears later, can we reconstruct the event chain?
- Can past work become operational knowledge?

The answer became increasingly clear:

> Log the things that change truth.
> Turn those logs into artifacts that can be inspected later.

This is not logging only for debugging. It is logging as operational memory.

---

## Today - Trinity v2

Trinity v2 is the result of those lessons.

It is no longer only a personal prompt pack or ritual habit. It is a control
layer for AI-assisted work.

The current system includes:

- **Trinity Kernel** - orchestrates ritual workflow, state machine, and gates
- **memory-cli** - stores and retrieves accepted artifacts, logs, and retros
- **CLI tools as organs** - focused tools for verification, retro, browser,
  SEO, image, and task-specific operations
- **audit chain** - append-only event log with hash linking
- **artifact-as-truth** - agent claims are not final truth; files, verdicts,
  hashes, logs, and artifacts are the evidence
- **human gate** - important decisions still require human authority

Trinity does not replace AI agents.

Trinity provides the layer that helps AI agents work within boundaries, leave
evidence, recover from mistakes, and reuse lessons from prior work.

The closest phrase for Trinity today is:

> Control plane for AI-assisted work

Like a control plane in orchestration systems, Trinity does not do the worker's
job. It defines state, boundary, audit, recovery, and promotion paths so
workers can operate together more safely.

---

## Trinity Is Not an Agent Framework

Trinity is not trying to be a coding agent, executor, or workflow engine.

Those belong to the worker layer.

Trinity sits in a different layer. It cares about questions like:

- What did the AI do?
- What artifact proves it?
- What scope was allowed?
- What is the current state?
- If it breaks, how do we roll back?
- Who verified the result?
- What evidence shows the work is complete?
- Which decision requires human approval?

The core principles are:

> No artifact = no trust
> No verification = no completion
> AI can execute, but AI cannot be the final authority

---

## This Was Not Built to Sell a Story

Every current Trinity feature responds to a real problem I hit while doing
work. It was not designed because the feature sounded impressive.

I am still the primary user, and that is fine.

If someone else finds it useful, good. If not, that is also fine.

I mainly wanted to put it somewhere it can live:

- so someone facing the same problem can find it
- so I can understand my own thinking later
- so the pattern is available when the world is ready for it

---

## Tomorrow

Trinity is still evolving.

Human-in-the-loop is still the bottleneck. For now, I still gate major
decisions myself.

The next direction is to move more deterministic rules into the verifier layer
so humans are needed only for decisions that require judgment.

Trinity is not trying to make AI autonomous without boundaries.

It is trying to make AI work:

- controllable
- verifiable
- recoverable
- able to learn from past work
- safe enough for real production use

---

## Read Next

- [`RITUALS.md`](RITUALS.md) - ritual operator reference
- [`ORIGIN_TH.md`](ORIGIN_TH.md) - Thai version
- [`operator-guide-en/00_README.md`](operator-guide-en/00_README.md) - Operator guide in English
- [`operator-guide-th/00_README.md`](operator-guide-th/00_README.md) - Thai operator guide
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - architecture overview
