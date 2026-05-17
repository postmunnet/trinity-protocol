---
title: "Trinity Retro / RRR Split Spec v1.0"
version: "1.0"
status: "draft"
phase: "12"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes: ["(none — first canonical version)"]
constitutional-anchor: ["Article IX", "Article IV", "Article III", "Article XIII", "Article XVI", "Article XX", "Article XXIX"]
amendment-policy: "Article XXIX — explicit proposal + rationale + impact analysis + human approval + version bump + audit entry."
---

# TRINITY_RETRO_RRR_SPLIT_SPEC_V1

> Phase 12 deliverable per `trinity_organ_refactor_prd.md` §9.
>
> Separates the **terminal closure organ** (`rrr`) from the **semantic
> reflection organ** (Retro / `retro_writer` / human author). The two share
> a session boundary; they do **not** share decision rights, output formats,
> or audit footprints.

---

## §1 — Purpose & Constitutional Anchor

[normative-description]

This specification fixes the operational boundary between two organs that
the legacy `rrr.py` collapsed into one execution path:

```text
rrr     = deterministic terminal closure  (Kernel + Memory delegation)
retro   = semantic reflection             (Retro organ / human author)
```

The split exists because the Constitution forbids any single component
from owning both "what mechanically happened" and "what it means". The
former is artifact accounting; the latter is judgment. Trinity refuses to
let an AI organ author both at once.

### §1.1 Article IX — Memory Discipline (verbatim, primary anchor)

> **Article IX — Memory Discipline**
>
> Memory retrieves evidence.
>
> Memory MUST:
>
> ```text
> - preserve artifact references
> - preserve canonical references
> - return traceable evidence
> - avoid semantic overreach
> ```
>
> Memory MUST NOT:
>
> ```text
> - decide semantic truth
> - become AI brain
> - approve evidence
> - mutate workflow state
> - execute commands
> ```
>
> Memory retrieves evidence.
> It does not govern meaning.

Article IX is the load-bearing clause for this spec. `rrr` delegates
indexing to `memory-cli index` because indexing is mechanical evidence
preservation. `rrr` does **not** delegate "what should we learn from this
session?" because that is meaning-making and Memory cannot govern meaning.

### §1.2 Article IV — Separation of Responsibilities (verbatim, primary anchor)

> **Article IV — Separation of Responsibilities**
>
> Trinity MUST enforce strict role separation.
>
> Canonical roles:
>
> ```text
> Kernel    = governance, state, gates, authority
> Planner   = reasoning, plans, risk analysis
> Executor  = bounded action, mutation, execution artifacts
> Verifier  = independent validation
> Memory    = evidence retrieval
> Audit     = immutable history
> Retro     = post-work reflection
> Transport = message delivery only
> ```
>
> No component may silently absorb another component's role.
>
> Role collapse is a constitutional violation.

Article IV is why `rrr` (a Kernel/Closure organ) and Retro (a reflection
organ) MUST be separate processes, separate artifacts, and separate audit
event types. The legacy `rrr.py` that synthesised semantic lessons inside
the closure routine was a textbook role-collapse violation.

### §1.3 Secondary Anchors

[normative-description]

| Article | Operational Relevance |
|---|---|
| **III — AI Cannot Govern Itself** | `rrr` MUST NOT declare meaning, MUST NOT auto-pin its own retro, MUST NOT self-certify a session as "well-executed". Final completion requires `artifact + verification + governance approval + audit`. |
| **XIII — Human Authority** | Pinning a retro as canonical doctrine is a critical action. It MUST exist as an explicit human-authored artifact (`memory-cli pin --reason=...`), never as an automatic side-effect of `rrr.completed`. |
| **XVI — Least Authority** | `rrr` runs with closure authority only. It MUST NOT carry pin authority, supersede authority, or memory-mutation authority beyond mechanical `index`. Unknown authority is denied authority. |
| **XX — Passive Core** | `rrr` runs only on explicit invocation. It MUST NOT trigger a retro draft, an embedding pass, or a doctrine update on its own. The Retro organ likewise runs only when a human or kernel-coordinated agent invokes it. |
| **XXIX — Constitutional Amendment** | Adding a field to the closure record schema, deprecating an event type, or expanding `rrr`'s authority surface MUST follow the amendment protocol: explicit proposal + rationale + impact analysis + human approval + version bump + audit entry. |

---

## §2 — The Split: Deterministic Closure vs Semantic Reflection

[normative-description]

### §2.1 Taxonomy

```text
                   SESSION END BOUNDARY
                            |
                            |
          +-----------------+-----------------+
          |                                   |
    (deterministic)                      (semantic)
          |                                   |
        rrr                              retro_writer
          |                              (or human author)
          |                                   |
   retro_envelope.md                     RETRO.md
   rrr.completed event                   pin/no-pin decision
   memory-cli index                      (human-only via pin)
          |                                   |
   audit chain advances             audit only on pin event
```

`rrr` and Retro **share** the session directory. They **do not share**:

| Dimension | rrr (closure) | retro (reflection) |
|---|---|---|
| Authority class | Kernel / Closure | Retro / Reflection |
| Decision rights | Mechanical: acceptance pass/fail, forbidden-diff, transition | Semantic: lessons, root cause, doctrine candidates |
| Decided-by | `kernel` | `agent:retro_writer` (draft) → `human` (pin) |
| Output format | YAML/MD with strict schema (§3, §4) | Free-form Markdown with section conventions (§5) |
| Audit event | `rrr.completed` (registered §6) | None on draft; `memory.promote` only on human pin |
| Triggered by | `bash .ai/cli/ai rrr` | Operator runs `bash .ai/cli/agent retro_writer draft ...` |
| Idempotent | Yes (re-run produces same hash on same inputs) | No (semantic content varies by reflection depth) |
| Article anchor | IV, IX, X, XX | IV, III, XIII, XX |

### §2.2 Why the split exists

[normative-description]

A single `rrr` that writes both a closure record and a "lessons learned"
section conflates four distinct decision rights:

1. **Did acceptance pass?** — deterministic, owned by Verifier.
2. **Did the diff stay inside allowed paths?** — deterministic, owned by Kernel.
3. **What is the root cause of the failures we hit?** — semantic, owned by Retro/Human.
4. **Should this become canonical doctrine?** — authority decision, owned by Human.

Decisions 1 and 2 are mechanically computable from session artifacts.
Decisions 3 and 4 require interpretation and, in the case of 4, explicit
human authority (Article XIII). Mixing them in one routine has historically
produced two failure modes:

- **Auto-pinning drift** — `rrr` quietly elevated its own draft retro to
  canonical doctrine, violating Article XIII and Article XVI.
- **Semantic overreach** — `rrr` wrote "the lesson here is X" with no
  human review, violating Article IX (Memory cannot govern meaning).

### §2.3 Boundary contract (one-line invariants)

[normative-description]

```text
rrr writes facts.
retro writes meaning.
human pins authority.
audit records all three.
```

If a candidate change to `rrr` makes any of those four lines untrue, the
change requires Article XXIX amendment review.

---

## §3 — rrr Output Contract: Deterministic Only

[normative-description]

`rrr` produces exactly **one canonical output file** per session in the
session directory:

```text
<session>/THINK/retro_envelope.md
```

(Memory delegation also writes a separate retro artifact for indexing —
see §4.4 and §7.)

### §3.1 What rrr MUST write

[normative-description]

`rrr` MUST populate `retro_envelope.md` with the following deterministic
fields (full schema in §4):

```text
- session_id            (mechanical: session directory name)
- ts_started            (mechanical: from sss audit event)
- ts_closed             (mechanical: now)
- duration_seconds      (mechanical: ts_closed - ts_started)
- acceptance_results[]  (mechanical: per-criterion pass/fail + command + exit code)
- forbidden_diff_status (mechanical: clean | violations[])
- baseline_untracked    (mechanical: snapshot taken at sss; cf. memory feedback_rrr_cross_session_forbidden_diff)
- audit_chain_status    (mechanical: session_chain_head + last_seq + verify-chain result)
- transition_count      (mechanical: graph.transition events count)
- gogogo_verdicts       (mechanical: PASS / FAIL counts per step)
- tier                  (mechanical: from sandbox.profile.bound -> verifier reports -> plan_envelope)
- memory_index_result   (mechanical: verbatim envelope from memory-cli index; see §7)
- artifact_paths[]      (mechanical: enumerate DO/dev, DO/prod, SANDBOX, THINK file paths + sha256)
```

### §3.2 What rrr MUST NOT write

[normative-description]

`rrr` MUST NOT write any of the following into `retro_envelope.md` or any
other artifact in the session:

```text
- "What worked"  / "What failed" prose paragraphs
- "Lessons learned" / "Root cause" / "Future recommendation" sections
- Value judgments ("the team executed well", "the design was elegant")
- Doctrine candidates ("this should become a canonical pattern")
- Comparative quality assessments vs prior sessions
- Predictions about future sessions
- Suggestions for policy changes
- Any field tagged confidence=verified by rrr itself
- Any embedding / vector / similarity score
- Any auto-pin / auto-promote action
```

This list is the operational expansion of the RRR Delegation Contract v1.0
T1 ("No semantic synthesis inside rrr") — which itself derives from
Article IX. The forbidden-substring lint at the source level remains as
specified in the delegation contract:

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

### §3.3 [non-normative-example] — Permissible vs forbidden phrases

```text
PERMITTED  in retro_envelope.md:
  acceptance_results:
    - id: A1
      command: "test -f docs/specs/FOO.md"
      expect_exit: 0
      actual_exit: 0
      pass: true

FORBIDDEN  in retro_envelope.md:
  reflection: "The session went smoothly. We learned that early
               clarification reduces churn."   <-- semantic; Article IX
```

### §3.4 Mechanical-vs-semantic decision rule

[normative-description]

When `rrr` (or any future agent that contributes to `rrr`) is uncertain
whether a candidate field is mechanical or semantic, apply this test:

```text
1. Can the field be derived deterministically from session artifacts
   (audit chain + capture store + filesystem) by a stateless function?

   YES -> mechanical -> belongs in retro_envelope.md
   NO  -> semantic   -> belongs in RETRO.md (human/agent-authored)
```

If the answer is YES but the function depends on a model call, the field
is **not** mechanical for the purposes of this spec. Model calls are not
deterministic; their outputs are semantic.

---

## §4 — `retro_envelope.md` Schema

[normative-description]

`retro_envelope.md` is a Markdown file with a single YAML frontmatter
block holding the deterministic closure record, optionally followed by a
machine-rendered summary table (no prose).

### §4.1 Frontmatter schema (canonical)

[normative-description]

```yaml
schema_version: "trinity.retro_envelope.v1"
session_id: <string>                  # required; e.g. "sess_2026-05-15_my-task"
slug: <string>                        # required; mirror of session slug
ts_started: <RFC3339-UTC>             # required; from session.created event
ts_closed: <RFC3339-UTC>              # required; rrr invocation moment
duration_seconds: <integer>           # required; ts_closed - ts_started
tier: HOT|WARM|COLD                   # required; resolved per Spec 15 §4
graph_state_final: DONE|FAILED|ABORTED  # required
decided_by: "kernel"                  # required; const "kernel" for rrr.completed
```

### §4.2 acceptance_results block

[normative-description]

```yaml
acceptance_results:
  - id: <string>                      # e.g. "A1"
    description: <string>             # verbatim from THINK/03_ACCEPTANCE.yaml
    command: <string>                 # exact shell invocation run
    expect_exit: <integer>            # declared expected exit code
    actual_exit: <integer>            # observed exit code
    pass: <bool>                      # actual_exit == expect_exit
    captured_stdout_sha256: <string|null>
    captured_stderr_sha256: <string|null>
acceptance_summary:
  total: <int>
  passed: <int>
  failed: <int>
  required_failed: <int>              # required acceptance criteria that failed
```

### §4.3 forbidden_diff + audit blocks

[normative-description]

```yaml
forbidden_diff_status: clean|violations
forbidden_diff_violations:            # empty list if status==clean
  - path: <string>
    rule: <string>                    # e.g. "policies/**"
    detected_at: <RFC3339-UTC>
baseline_untracked:                   # snapshot taken at sss [1]
  ts: <RFC3339-UTC>
  sha256: <string>
audit:
  session_chain_head: <hash>          # from per-session AuditWriter
  last_seq: <int>
  verify_chain_status: PASS|FAIL
  verify_chain_first_break: <string|null>  # "seq=N reason=..." if FAIL
transition_count: <int>
gogogo_verdicts:
  total_steps: <int>
  pass: <int>
  fail: <int>
  unverified: <int>
  retry: <int>
  needs_human: <int>
```

The `gogogo_verdicts` block has the explicit schema
`{total_steps: int, pass: int, fail: int, unverified: int, retry: int,
needs_human: int}`. The sum of all numeric fields other than
`total_steps` MUST equal `total_steps`; that is,
`pass + fail + unverified + retry + needs_human == total_steps`. A row
that fails this invariant is malformed and MUST be rejected by
downstream consumers (Close, DDD, sibling CLIs).

[1] `baseline_untracked` is captured at sss-time per memory
`feedback_rrr_cross_session_forbidden_diff` (resolved 2026-05-14,
Approach A): the untracked-file snapshot is taken when the session opens
so that the rrr-time forbidden-diff computation has a stable baseline
even when sibling sessions write into the working tree concurrently.
Concurrent sibling writes between sss and rrr that touch paths the
current session legitimately needs are reconciled via the carve-out
path mechanism described in memory
`feedback_plan_helper_drift_corrections` Pattern 4: the plan envelope's
allowed-path list explicitly carves out the sibling-owned path so the
forbidden-diff check skips it, preserving the cross-session invariant
without forcing serialisation of sibling sessions.

### §4.4 indexed retros block

[normative-description]

```yaml
indexed_retros:
  - path: .ai/memory/retros/<NNNN>_<ts>_<slug>.md
    sha256: <hash>
    indexed_chunks: <int>             # from memory-cli envelope
    project: <string>                 # auto-detected by memory-cli
artifact_paths:                       # full enumeration; sorted by path
  - path: <session-relative>
    sha256: <hash>
    size_bytes: <int>
```

### §4.5 Required vs optional summary

[normative-description]

| Field | Required | Notes |
|---|---|---|
| `schema_version` | yes | const "trinity.retro_envelope.v1" |
| `session_id` | yes | — |
| `slug` | yes | — |
| `ts_started` / `ts_closed` / `duration_seconds` | yes | — |
| `tier` / `graph_state_final` / `decided_by` | yes | — |
| `acceptance_results[]` | yes | empty list permitted on ABORTED |
| `acceptance_summary` | yes | derived from list |
| `forbidden_diff_status` | yes | — |
| `forbidden_diff_violations[]` | yes | empty if clean |
| `baseline_untracked` | yes | required to satisfy memory `feedback_rrr_cross_session_forbidden_diff` |
| `audit.*` | yes | from per-session AuditWriter (Spec 10 §2) |
| `transition_count` / `gogogo_verdicts` | yes | — |
| `indexed_retros[]` | conditional | required when memory-cli index ran (the typical case); empty list permitted only on COLD-tier index failure with severity=block |
| `artifact_paths[]` | yes | full enumeration |
| `memory_index_result` | yes | verbatim envelope; see §7 |

---

## §5 — `RETRO.md` (Semantic) Schema

[normative-description]

`RETRO.md` is the **semantic reflection** artifact. It is written by:

```text
- a human author, OR
- the retro_writer in-house agent (proposal-only; see CLAUDE.md)
```

`RETRO.md` is **never** written by `rrr` itself.

### §5.1 Authoring authority

[normative-description]

| Step | Actor | Authority |
|---|---|---|
| Draft `RETRO.md` | `retro_writer` agent OR human | Proposal only |
| Land in `<session>/THINK/RETRO.md` | Operator approval | Human gate |
| Pin as canonical doctrine | Human via `memory-cli pin` | Article XIII gate |

The `retro_writer` agent is a Trinity in-house agent (see project memory
`project_in_house_agents_pattern`) that proposes a draft. Proposal is not
authority. The human MUST explicitly accept or amend the draft before it
is treated as the session's reflection of record.

### §5.2 Recommended sections

[normative-description]

```markdown
---
schema_version: "trinity.retro_md.v1"
session_id: <string>
authored_by: "human" | "agent:retro_writer"
authored_at: <RFC3339-UTC>
companion_envelope: THINK/retro_envelope.md
companion_envelope_sha256: <hash>
---

# RETRO — <session slug>

## What worked
[free-form prose; specific moments / decisions that produced good outcomes]

## What failed
[free-form prose; specific moments / decisions that produced bad outcomes]

## Lessons
[1-N numbered lessons; each lesson MUST cite a specific artifact path]

## Followups
[bulleted list of concrete actions; each action SHOULD reference an
 owner (human handle) and a target session-id placeholder]
```

### §5.3 Pinning rule (Article XX + Article XIII)

[normative-description]

`RETRO.md` is **never auto-pinned**. Per Article XX (Passive Core), no
core system may automatically promote a draft to canonical status.

To make a `RETRO.md` canonical doctrine, a human MUST run:

```bash
memory-cli pin <retro-path> --as=<canonical-name> --reason='<text>'
```

The `--reason` flag is required; an empty reason is a constitutional
failure (Article XIII — irreversible action without recorded human
intent). `memory-cli pin` is the **only** authorised path; `rrr` MUST NOT
emit a pin command and the `retro_writer` agent MUST NOT emit one either.

### §5.4 Cross-link to envelope (deterministic anchor)

[normative-description]

When a `RETRO.md` is authored, its frontmatter MUST carry
`companion_envelope_sha256`, the SHA-256 of the corresponding
`retro_envelope.md` file at the moment of authorship. This pins the
semantic reflection to the deterministic record of the same session and
makes it possible to detect drift if either file is later mutated.

---

## §6 — `rrr.completed` Event Schema

[normative-description]

`rrr.completed` is the audit event that records terminal closure. It is
already registered in TRINITY_AUDIT_EVENT_SPEC_V1 §3 (Ritual gates
section). This spec pins its **payload** shape; the row shape itself
follows the 13-field event row from Audit Event Spec §2.

### §6.1 Row shape (per Audit Event Spec §2)

[normative-description]

`rrr.completed` is a normal AuditWriter row; the 13 outer fields are
fixed by Spec 10 §2. The fields specific to this event:

```yaml
event_type: "rrr.completed"           # const
ritual: "rrr"                         # const
actor: "kernel"                       # const; rrr is a kernel command
capture_id: <ULID|null>               # populated when rrr ran inside a capture transaction
schema_version: "trinity.audit_event.v1"
```

### §6.2 payload_json schema

[normative-description]

The `payload_json` field MUST canonicalise the following structure
(`sort_keys=True, separators=(",",":")` per Spec 10 §2.1):

```yaml
session_id: <string>
ts: <RFC3339-UTC>                     # mirrors ts_utc on the row
tier: HOT|WARM|COLD
graph_state_final: DONE|FAILED|ABORTED
decided_by: "kernel"                  # const; rrr is mechanical closure
retro_envelope_path: "THINK/retro_envelope.md"
retro_envelope_sha256: <hash>         # required
retro_md_path: "THINK/RETRO.md"|null  # null when no semantic retro authored
retro_md_sha256: <hash>|null          # null iff retro_md_path is null
indexed_retro_path: <string|null>     # path under .ai/memory/retros/
indexed_retro_sha256: <hash|null>
indexed_chunks: <int>                 # 0 if index skipped or failed
memory_index:                         # verbatim from memory-cli; see §7
  ok: <bool>
  indexed_new: <int>
  indexed_updated: <int>
  chunks_total: <int>
  errors: [<string>, ...]
memory_index_severity: pass|warning|degraded|block
acceptance_summary: { total, passed, failed, required_failed }
forbidden_diff_status: clean|violations
audit_chain_anchor:
  session_chain_head: <hash>
  last_seq: <int>
```

### §6.3 Drift Resolution (cross-session anchor reconciliation)

[normative-description]

The `audit_chain_anchor` block in §6.2 is captured by `rrr` at
`rrr.completed` time. The same anchor is re-read later by Session Close
when it builds the close manifest (see §6.4 cross-reference to Spec 15).
If the close-time anchor differs from the rrr-time anchor (typically
because a concurrent sibling session advanced the global audit chain
between rrr and close) the close MUST emit a
`rrr.completed.drift_detected` audit event whose payload references both
seq numbers (the rrr-time `last_seq` and the close-time `last_seq`) and
both `session_chain_head` values. The workflow does **not** block on
drift: concurrent sibling sessions are the expected cause, and the
per-session chain is the source of truth for closure decisions. The
difference is informational, recorded so audit replay can reconcile the
two anchors without ambiguity.

### §6.4 Required fields on the registry row

[normative-description]

| Field | Required | Notes |
|---|---|---|
| `event_type` | yes | const "rrr.completed" |
| `session_id` | yes | — |
| `ts` (mirror of `ts_utc`) | yes | — |
| `decided_by` | yes | const "kernel" — rrr never sets this to "human" |
| `retro_envelope_sha256` | yes | the closure record hash |
| `retro_md_sha256` | conditional | nullable; non-null only when RETRO.md exists |
| `memory_index` envelope | yes | verbatim per §7 |
| `memory_index_severity` | yes | per RRR Delegation Contract T3 |
| `audit_chain_anchor` | yes | per Spec 15 §3 (RecordProxy-aligned) |

### §6.5 Cross-reference

[normative-description]

This event row registers in:

- **TRINITY_AUDIT_EVENT_SPEC_V1 §3** — Ritual gates section, already lists
  `rrr.completed` in the canonical registry.
- **TRINITY_SESSION_CLOSE_SPEC_V1 §3** — `audit_chain_anchor` is read at
  `rrr.completed` and re-checked at `close.manifest_built`. This spec
  fixes the producer side; Spec 15 fixes the consumer side.
- **TRINITY_RRR_DELEGATION_CONTRACT_V1 §T4** — `rrr.delegated_call` is
  emitted **before** `rrr.completed`. The completion event carries the
  `memory_index` summary; the delegated_call event carries the per-call
  detail.

---

## §7 — Memory Index Result Envelope

[normative-description]

When `rrr` delegates to `memory-cli index <retro-path>`, it MUST capture
the entire response envelope verbatim into `retro_envelope.md` and into
the `payload_json` of `rrr.completed`. `rrr` MUST NOT interpret,
summarise, or filter the envelope.

### §7.1 Envelope fields (read by rrr; produced by memory-cli)

[normative-description]

```yaml
ok: <bool>                            # required
indexed_new: <int>                    # required; count of newly inserted documents
indexed_updated: <int>                # required; count of updated documents (sha256 changed)
chunks_total: <int>                   # required; documents created or updated
scanned: <int>                        # required; total files scanned
skipped_existing: <int>               # required; count of unchanged
errors: [<string>, ...]               # required; empty list if no errors
db_path: <string>                     # required; absolute path to memory.db
indexed_at: <RFC3339-UTC>             # required; per memory-cli envelope spec
```

### §7.2 [non-normative-example] — Verbatim capture

```yaml
# Excerpt of retro_envelope.md showing the verbatim block:
memory_index_result:
  ok: true
  indexed_new: 1
  indexed_updated: 0
  chunks_total: 1
  scanned: 1
  skipped_existing: 0
  errors: []
  db_path: <user-home>/.trinity/memory.db
  indexed_at: "2026-05-15T12:34:56Z"
```

### §7.3 Severity mapping (RRR Delegation Contract T3)

[normative-description]

When `ok: false` or `errors[]` is non-empty, `rrr` MUST set
`memory_index_severity` per the tier mapping fixed by the RRR Delegation
Contract:

```text
HOT  -> "warning"   (rrr completes; warning printed)
WARM -> "degraded"  (rrr completes; FAILED_VISIBLE printed)
COLD -> "block"     (rrr records block severity; gate consequence)
```

`rrr` MUST NOT silence the failure regardless of tier. Silence is an
Article XXIII violation (Failure Visibility) — fixed in writing.

The `tier` value used to drive the severity mapping above is resolved per
TRINITY_SESSION_CLOSE_SPEC_V1 §4 priority order: `sandbox.profile.bound`
first, then `verifier_report.tier`, then `plan_envelope.tier`, with a
default of WARM when none of the upstream sources fix the tier. `rrr`
MUST NOT recompute or override this resolution; it consumes the tier as
already bound by the session and applies the mapping verbatim.

### §7.4 What rrr MUST NOT do with the envelope

[normative-description]

```text
- Recompute or "correct" any field
- Flatten errors[] into a single string
- Drop the envelope when severity is HOT
- Embed the envelope under a different schema_version
- Re-emit it with rrr as the producer (memory-cli is the producer)
```

These prohibitions exist because Memory governs evidence retrieval per
Article IX; `rrr` is a delegate, not the source of truth for what was
indexed.

---

## §8 — Pinning Authority — Human Only

[normative-description]

This section is the constitutional deep dive on why `rrr` MUST NOT pin.

### §8.1 What pinning means

[normative-description]

In `memory-cli`, a "pin" elevates a document from indexed-evidence to
canonical-doctrine. The pinned document survives supersession sweeps,
appears in default `lll`/`vvv` context loads, and becomes a citable source
in future planner reasoning. Pinning is **authority**: the pinned record
governs how subsequent sessions will be evaluated.

### §8.2 Why rrr cannot pin (Article IX)

[normative-description]

Pinning is semantic canonicalisation: it asserts "this retro represents
how Trinity should think about this class of work going forward". That
assertion is meaning-making, and Article IX forbids Memory from governing
meaning. `rrr` is even more constrained — it is a closure organ, not the
Memory organ — so it can neither pin nor delegate pinning.

### §8.3 Why rrr cannot pin (Article XIII)

[normative-description]

Pinning has irreversible-by-default semantics: once a retro becomes
canonical doctrine, downstream sessions begin to cite it, and revoking
the pin produces audit-visible drift across every session that consumed
the pinned record. Article XIII reserves irreversible actions to explicit
human authority. An auto-pin by `rrr` would silently authorise
irreversible institutional change — a textbook Article XIII violation.

### §8.4 Why rrr cannot pin (Article XVI)

[normative-description]

Per Article XVI (Least Authority), `rrr` runs with minimum required
authority. It needs:

```text
- read session artifacts
- read audit chain
- write retro_envelope.md
- write a per-session retro file under .ai/memory/retros/
- invoke memory-cli index
- emit rrr.delegated_call + rrr.completed audit events
- fire RETRO -> DONE transition
```

It does **not** need pin authority, supersede authority, or any other
memory-mutation authority beyond `index`. Granting more would violate
"unknown authority is denied authority".

### §8.5 The only authorised pin path

[normative-description]

```bash
memory-cli pin <retro-path> --as=<canonical-name> --reason='<text>'
```

Constraints:

```text
- Invoked by a human, from a human shell session, never by an agent
- --reason is required; empty reason is rejected
- The pin event audits as decided_by: "human"
- rrr MAY print a stdout suggestion to pin (per RRR Delegation Contract
  Pin Suggestion Protocol) when the session contains a decided_by:human
  transition; the suggestion is NEVER recorded in the audit chain as a
  decision
```

### §8.6 [non-normative-example] — Suggestion vs decision

```text
ALLOWED stdout from rrr:
  suggest: this session contains a human decision. To mark the retro
  canonical, run:
    memory-cli pin .ai/memory/retros/0123_2026-05-15_my-task.md \
                  --as=retro-my-task \
                  --reason='canonical pattern for X'
  (rrr will never auto-pin; pinning is authority decision.)

FORBIDDEN: any rrr code path that calls memory-cli pin directly,
           OR that records a "decided_by: kernel" pin event,
           OR that flips memory.confidence to "verified" without a
           human-authored pin record.
```

---

## §9 — Conformance Test Matrix

[normative-description]

The following table enumerates `rrr` behaviours, classifies them as
deterministic or semantic, fixes the expected output surface, and pins
the audit event(s) that MUST be emitted. Conformance tests for the
`rrr.py` runtime SHOULD assert each row.

| # | Behaviour | Class | Expected output surface | Audit event(s) |
|---|---|---|---|---|
| C1 | Compute acceptance pass/fail per criterion | Deterministic | `retro_envelope.acceptance_results[]` | `rrr.proposed` then `rrr.completed` (acceptance_summary in payload) |
| C2 | Run forbidden-path diff against `baseline_untracked` | Deterministic | `retro_envelope.forbidden_diff_status` + `forbidden_diff_violations[]` | `rrr.completed` (forbidden_diff_status in payload) |
| C3 | Snapshot session metrics (duration, transitions, gogogo verdicts) | Deterministic | `retro_envelope.duration_seconds` + `transition_count` + `gogogo_verdicts` | `rrr.completed` |
| C4 | Compute audit chain anchor (per-session SQLite) | Deterministic | `retro_envelope.audit.*` | `rrr.completed` (audit_chain_anchor in payload) |
| C5 | Write per-session retro file under `.ai/memory/retros/` | Deterministic | `.ai/memory/retros/<NNNN>_<ts>_<slug>.md` | none yet (file write only) |
| C6 | Invoke `memory-cli index <retro-path>` | Delegated | `retro_envelope.memory_index_result` (verbatim) | `rrr.delegated_call` (T4 shape) |
| C7 | Capture severity per Decision Velocity Tier | Deterministic | `retro_envelope.memory_index_severity` | `rrr.completed` (severity in payload) |
| C8 | Fire `RETRO -> DONE` graph transition | Kernel | `graph.transition` event row | `graph.transition` then `rrr.completed` |
| C9 | Print pin suggestion when session contains `decided_by:human` | Stdout courtesy | stdout text only | NONE (suggestion is not an audit decision) |
| C10 | Author "What worked / failed / lessons" prose | **FORBIDDEN — semantic** | n/a | n/a — this MUST NOT happen |
| C11 | Run `memory-cli pin` directly | **FORBIDDEN — authority** | n/a | n/a — this MUST NOT happen |
| C12 | Run `memory-cli learn / promote / verify / trace / embed / similar` | **FORBIDDEN — RRR Delegation Contract** | n/a | n/a — this MUST NOT happen |
| C13 | Silently swallow a memory-cli failure on HOT | **FORBIDDEN — Article XXIII** | n/a | n/a — failure MUST be visible |
| C14 | Mutate `.ai/policies/**` or `.ai/audit/**` (modify) | **FORBIDDEN — CLAUDE.md boundaries** | n/a | n/a — this MUST NOT happen |
| C15 | Idempotent re-run on identical inputs | Deterministic | byte-identical `retro_envelope.md` (modulo `ts_closed`) | second `rrr.completed` row OR explicit "already-closed" refusal |

### §9.1 Test fixture structure (normative)

[normative-description]

A conformance test fixture for row C1-C5 SHOULD:

```text
1. Create a synthetic session under tmp/<sid>/
2. Plant THINK/03_ACCEPTANCE.yaml with a known set of criteria
3. Plant deterministic acceptance commands (exit 0 / exit 1)
4. Pre-populate a per-session capture.sqlite with N audit rows
5. Run `bash .ai/cli/ai rrr` against the session
6. Assert: retro_envelope.md exists, schema_version=trinity.retro_envelope.v1
7. Assert: per-row deterministic fields match expected
8. Assert: rrr.completed row appears with the expected payload
```

### §9.2 Negative tests (normative)

[normative-description]

```text
N1. Plant a "what worked" string into a candidate rrr code path -> source
    lint MUST reject (forbidden-substring lint per RRR Delegation Contract)
N2. Plant a memory-cli pin call into rrr.py -> source lint MUST reject
N3. Force memory-cli index to fail -> rrr MUST set memory_index_severity
    correctly per tier and MUST NOT silently complete on COLD
N4. Mutate an acceptance criterion's grep -F to use em-dash chars -> A*
    MUST fail visibly (cf. memory feedback_acceptance_grep_char_mismatch)
N5. Concurrent sibling-session writes during rrr -> baseline_untracked
    snapshot from sss MUST be the source of truth for the diff (cf.
    memory feedback_rrr_cross_session_forbidden_diff)
```

---

## §10 — Versioning & Article XXIX Amendment Protocol

[normative-description]

### §10.1 Schema versioning

[normative-description]

This spec pins three schema versions:

```text
trinity.retro_envelope.v1     -- §4 schema for retro_envelope.md
trinity.retro_md.v1           -- §5 schema for RETRO.md frontmatter
trinity.audit_event.v1        -- §6 row shape (defined by Spec 10 §2)
```

Each schema_version is a closed namespace. Adding a field MUST bump the
minor portion of the schema_version (e.g. `v1` -> `v1.1`); breaking
changes MUST bump the major portion (e.g. `v1` -> `v2`).

### §10.2 Adding a field to the closure record

[normative-description]

To add a field to `retro_envelope.md` or to the `rrr.completed`
`payload_json`:

```text
1. Submit Article XXIX amendment proposal (explicit proposal + rationale)
2. Include impact analysis: which downstream consumers (Close, DDD,
   sibling CLIs) read the field; what their failure mode is on missing
   field; backward-compatibility plan
3. Obtain explicit human approval (operator signature on the proposal)
4. Bump schema_version per §10.1
5. Update the canonical event registry in TRINITY_AUDIT_EVENT_SPEC_V1 §3
6. Append an audit entry recording the amendment (decided_by: "human")
7. Bump this spec's version (this spec is rank 5 — Workflow Contract)
```

### §10.3 Deprecating a field

[normative-description]

Per Article XXI (Canonical Truth), deprecated fields MUST NOT be silently
deleted. They MAY be tagged DEPRECATED with a sunset date. The amendment
protocol from §10.2 applies in full; deprecation also requires a
deprecation window of at least one minor version cycle so downstream
consumers can migrate.

### §10.4 Aligning with Audit Event Spec changes

[normative-description]

The `rrr.completed` event lives in the canonical registry of Spec 10 §3.
If Spec 10 amends the row shape (e.g. adds a 14th field), this spec MUST
re-publish §6 to mirror the change. Conversely, if this spec adds a new
required payload field, the change MUST be reflected as a comment on the
canonical registry entry — the registry is the source of truth for which
event types exist; this spec is the source of truth for what their
payloads carry.

### §10.5 Cross-spec dependency map (informational)

[non-normative-example]

```text
TRINITY_RETRO_RRR_SPLIT_SPEC_V1 (this spec)
    consumes:
      Article IX, Article IV, Article III, Article XIII,
      Article XVI, Article XX, Article XXIX
    consumes:
      TRINITY_RRR_DELEGATION_CONTRACT_V1 (T1, T2, T3, T4)
      TRINITY_AUDIT_EVENT_SPEC_V1 §2 (row shape) + §3 (registry)
      TRINITY_SESSION_CLOSE_SPEC_V1 §3 (audit_chain_anchor)
      05_MEMORY_CLI_SPEC §4.2 (index command envelope)
    produces:
      retro_envelope.md schema (trinity.retro_envelope.v1)
      RETRO.md schema (trinity.retro_md.v1)
      rrr.completed payload contract
```

---

## §11 — Out of Scope

[normative-description]

This spec does **not** cover:

```text
- Implementing rrr.py changes -- deferred to a later gogogo
- Implementing the retro_writer agent -- deferred to a later session
- Implementing memory-cli pin authority checks -- 05_MEMORY_CLI_SPEC
  governs that surface
- Phase 14 Root of Trust cryptographic anchoring -- separate Addendum
- Presentation Protocol (Phase 13) -- separate spec
- Any change to the constitution itself -- Article XXIX governs that
```

---

## §12 — Cross-references

[normative-description]

| Reference | Why |
|---|---|
| Article IX (Memory Discipline) | Primary anchor; load-bearing for §8 (pinning) and §3 (no semantic synthesis) |
| Article IV (Separation) | Primary anchor; load-bearing for §2 (the split) |
| Article III (AI cannot govern itself) | rrr cannot self-certify completion or self-author meaning |
| Article XIII (Human Authority) | Pinning is irreversible action; human-only |
| Article XVI (Least Authority) | rrr's authority surface is bounded |
| Article XX (Passive Core) | rrr and retro_writer run only on explicit invocation; no auto-pin |
| Article XXIX (Amendment) | §10 amendment protocol |
| TRINITY_RRR_DELEGATION_CONTRACT_V1 | T1-T4 shape; forbidden patterns; severity tiers |
| TRINITY_AUDIT_EVENT_SPEC_V1 §2, §3 | rrr.completed row shape and registry membership |
| TRINITY_SESSION_CLOSE_SPEC_V1 §3 | audit_chain_anchor consumer of rrr.completed |
| 05_MEMORY_CLI_SPEC §4 | index command envelope shape |
| memory `feedback_rrr_cross_session_forbidden_diff` | baseline_untracked snapshot rationale |
| memory `feedback_rrr_acceptance_yaml_source` | THINK/03_ACCEPTANCE.yaml is the source of acceptance criteria |
| memory `feedback_close_capture_before_archive` | rrr's capture must close before close archives the session |

---

## §13 — Closing

[normative-description]

```text
rrr writes facts.
retro writes meaning.
human pins authority.
audit records all three.
```

```text
Memory retrieves evidence.
It does not govern meaning.   (Article IX)
```

```text
No silent semantic synthesis.
No auto-pin.
No role collapse between Closure and Reflection.   (Article IV)
```

---

**Author:** Trinity Architect (operator direct-draft).
**Status:** DRAFT v1.0 — pending verifier review and ddd.
**Constitutional rank:** 5 — Workflow Contract (Article XXV).
