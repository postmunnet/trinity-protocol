# Philosophy — why Trinity demands evidence

> This document is not a tutorial. It explains the three rules
> Trinity enforces, the failure modes they prevent, and the
> tradeoffs we accepted along the way.

## The three rules

Trinity is structured around three rules. Each one is short. Each
one is non-negotiable inside a session.

### No artifact = no trust

An AI agent can claim anything. It can claim tests pass, claim a
bug is fixed, claim a deploy is safe. None of those claims are
evidence. Only the actual test output, the actual reproduction,
the actual deploy log are evidence.

Trinity refuses to advance a session on claims. Every state
transition is gated on an artifact: a written plan, a captured
diff, a verifier report, a signed approval. If the artifact does
not exist on disk, the work does not advance — full stop.

### No verification = no completion

Producing an artifact is not enough. The artifact has to satisfy
a predicate that was declared in advance.

The verifier reads the plan envelope, finds the acceptance gates
the operator declared during `nnn`, and runs each gate as an
executable command. If a gate exits non-zero, the session does
not reach `DONE`. The agent cannot self-certify; the verifier is
the only authority for "this met the criteria."

### No authority = no transition

Some transitions are too consequential for the kernel or the
verifier to decide alone. Promoting to production, deploying,
overriding a budget — these require a human decision recorded in
the audit chain with `decided_by: human`.

The kernel will not fire those transitions on its own. A human
must approve, and that approval is captured as a structured
artifact, not as ambient trust.

## Why this way?

We tried the alternative. Agents that self-report success drift
silently. Tests pass that were never run. Deploys "succeed" that
never rolled back cleanly. The cost of catching a fabricated
claim weeks later is much higher than the cost of demanding
evidence up front.

Evidence-driven workflow is heavier per session. It is
dramatically lighter per incident.

## How the rules map to commands

| Rule                              | Enforced by                                          |
|-----------------------------------|------------------------------------------------------|
| No artifact = no trust            | `sss` capsule + hash-chained audit log               |
| No verification = no completion   | `nnn` acceptance gates + `gogogo` verifier checks    |
| No authority = no transition      | `ddd` human gate + `decided_by` field in transitions |

Each ritual exists because one rule needed a checkpoint. The
chain is `sss → vvv → nnn → gogogo → ddd → rrr → close`; see
[`./RITUALS.md`](RITUALS.md) for the full reference.

## Common objections

**"This is too heavyweight for small tasks."** It is. For a
one-line config change, you should not open a Trinity session.
Trinity is for work where being wrong is expensive — schema
migrations, security-sensitive code paths, anything you would
want a paper trail for if the change later caused an incident.

**"What stops an agent from faking the artifact?"** Two things.
The verifier runs declared commands against real files, so a
fake artifact has to actually pass the test — at which point it
is not fake. And every artifact is anchored in the hash-chained
audit log, so post-hoc tampering breaks the chain visibly.

## Where to read more

- [`./RITUALS.md`](RITUALS.md) — canonical command reference
- [`./STORAGE_TAXONOMY.md`](STORAGE_TAXONOMY.md) — where evidence lives
- [`./constitution/`](constitution/) — full governance corpus (advanced)
- [`./ai_entry/SHORT_CODES.md`](ai_entry/SHORT_CODES.md) — short-code spec
