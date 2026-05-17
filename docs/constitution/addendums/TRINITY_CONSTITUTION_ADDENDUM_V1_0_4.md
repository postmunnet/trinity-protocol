---
title: "Trinity Constitution Addendum v1.0.4 - Article XXIX Amendment Process (3-Tier + Trace-to-Failure)"
version: "1.0.4"
status: "PROPOSED"
proposed_at: "2026-05-14"
parent: "TRINITY_CONSTITUTION_V1.md"
authority: "Article XXIX (amendment procedure)"
canonical: true
related:
  - "TRINITY_CONSTITUTION_V1.md (parent - Article XXIX, the procedure this addendum operationalises)"
  - "TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md (Decision Velocity Tiers - precedent for tiered classification)"
  - "TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md (canonical-home relocation)"
  - "TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md (Ritual Constitution v1.1 ratification)"
amendment-policy: "This Addendum operationalises Article XXIX of the parent Constitution. It may be revised independently of the Constitution provided the amendment policy is honoured."
---

## Version

Trinity Constitution Addendum v1.0.4 (against Constitution v1.0)

This Addendum is numbered independently of the Constitution. The Constitution itself remains at v1.0. The version bump applies to the Addendum, not to the parent.

---

# Trinity Constitution Addendum v1.0.4

## Article XXIX Amendment Process - 3-Tier Classification with Trace-to-Failure

This Addendum is a Section under the Trinity Constitution v1.0. It does
not contradict any Article; it operationalises Article XXIX's amendment
procedure with three concrete additions that the parent Constitution
names but does not detail:

1. A tiered classification (editorial / operational / constitutional)
2. A trace-to-failure rule differentiated by tier
3. A pinned audit-entry format consistent with the existing hash-chain at `.ai/audit/events.ndjson`

If this Addendum conflicts with the parent Constitution, the parent
wins (Article XXV - Constitutional Priority Order).

---

## 1. Proposal

Operationalise Article XXIX of Trinity Constitution v1.0 by:

- Defining three amendment tiers (XXIX.1 Editorial, XXIX.2 Operational, XXIX.3 Constitutional) with explicit scope-of-change and approval surface per tier.
- Adding XXIX.4 Trace-to-Failure with tier-differentiated obligation strength (not uniform SHOULD).
- Adding XXIX.5 Audit Entry Format that pins event names and required fields to the existing `.ai/audit/events.ndjson` hash chain.
- Adding XXIX.6 Classification Rule as the single-operator tiebreaker against downward drift.

The existing six-step amendment procedure (proposal / rationale / impact / approval / version / audit) is retained verbatim; the tiered classification governs HOW each step is satisfied per tier.

## 2. Rationale

Three blind spots were observed in the current Article XXIX:

1. **Unbounded "short rationale."** The phrase appears in current practice but has no upper bound. Without one, a 30-line "short rationale" silently becomes the norm and tier discipline collapses.
2. **Uniform SHOULD on trace.** A SHOULD-everywhere rule is skipped quietly. Different tiers carry different stakes; the wording must reflect that.
3. **No tiebreaker for ambiguous classification.** In a single-operator system, self-discipline needs an explicit rule against sliding amendments from operational into editorial to avoid friction.

This Addendum closes those three blind spots without expanding the surface of the procedure itself.

## 3. Impact analysis

**Behavior change.** Forward-looking only. No retroactive reclassification of v1.0.1, v1.0.2, or v1.0.3 is performed. All three remain at their declared status.

**Surface area.**

- `docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md` (this file; new)
- `CLAUDE.md` (one row added to the Constitutional Authority table)
- `docs/constitution/INDEX.md` (one row added to the Addendums table)
- `.ai/audit/events.ndjson` (one session-close event chain for THIS amendment, plus the FUTURE-facing event types defined in XXIX.5)

**Risk.** Low. The change is documentation-only and does not alter
kernel behavior, ritual semantics, schema, or any downstream consumer
contract. The new audit event types in XXIX.5 are declared but their
emitters are deferred to a future runtime-wiring session - declaring a
taxonomy does not register emitters (Article XX - Passive Core).

**Rollback path.** Revert this commit. No prior addendum or Constitution
text is mutated; reverting removes the new addendum file and the two
index rows.

## 4. Human approval

Pending ddd gate in the session that lands this addendum. Recorded as
`decided_by: human` in the audit log.

## 5. Version bump

```text
Addendum v1.0.3 (ENACTED 2026-05-13 - Ritual Constitution v1.1 ratification)
  + Addendum v1.0.4 (PROPOSED 2026-05-14 - Article XXIX operationalisation)
Constitution v1.0 - unchanged
```

The Addendum number bumps from v1.0.3 to v1.0.4. The parent Constitution
remains at v1.0. No "Constitution v1.0.4" exists; that label would
indicate a Constitution-level amendment, which this is not.

## 6. Audit entry

The canonical record of THIS amendment is the session-close audit chain
emitted by the Trinity kernel when the landing session completes. The
audit entries DEFINED by this addendum (Section XXIX.5 below) are the
ones FUTURE amendments will emit; they do not retroactively apply to
prior addendums.

---

# Section XXIX - Operationalised

The following subsections operationalise the parent Constitution's Article XXIX. The existing six numbered steps (proposal, rationale, impact analysis, human approval, version bump, audit entry) remain in force unchanged; XXIX.1 through XXIX.6 below govern how each step is performed per tier.

## XXIX.1 - Editorial Tier

**Scope.** Wording clarification without semantic change. Typo fixes, ASCII normalisation, link-target updates that point to the same canonical document, or formatting that does not alter the rule being expressed.

**Required form of rationale.**

```
Editorial rationale MUST fit in the git commit message body
(1-3 sentences). If longer rationale is needed, the change is
not editorial - reclassify as operational.
```

**Trace obligation.** See XXIX.4. Editorial: trace is not required.

**Approval surface.** Operator commit suffices. No separate human-approval artifact required beyond the commit itself.

**Audit entry.** See XXIX.5; event type `constitution.amended.editorial`.

## XXIX.2 - Operational Tier

**Scope.** Adding, removing, or modifying a procedure, threshold, audit format, ritual rule, or any rule that changes how the system MUST behave at runtime - without altering a constitutional principle or article in the parent Constitution.

**Required form of rationale.** Full proposal / rationale / impact analysis sections in the addendum body (see Sections 1-3 of this file as the template). The commit-body 1-3-sentence form is INSUFFICIENT for operational changes.

**Trace obligation.** See XXIX.4. Operational: MUST trace.

**Approval surface.** Explicit human approval recorded in audit as `decided_by: human`. A linked session id is the canonical proof of approval.

**Audit entry.** See XXIX.5; event type `constitution.amended.operational`.

## XXIX.3 - Constitutional Tier

**Scope.** Adding, removing, or modifying an Article of the parent Constitution v1.0 (Article I through Article XXX), OR adding an Addendum that operationalises an Article. THIS addendum (v1.0.4) is itself a constitutional-tier amendment, because it operationalises Article XXIX.

**Required form of rationale.** Full proposal / rationale / impact analysis sections AND an explicit strategic rationale - the constitutional principle being preserved or extended, named by article.

**Trace obligation.** See XXIX.4. Constitutional: MUST trace AND strategic rationale required.

**Approval surface.** Explicit human approval recorded in audit as `decided_by: human`, with the addendum file itself serving as the durable artifact. Version bump applies to the addendum number, not to the parent Constitution.

**Audit entry.** See XXIX.5; event type `constitution.amended.constitutional`.

## XXIX.4 - Trace-to-Failure (Tier-Differentiated)

Every operational and constitutional amendment MUST be traceable to a concrete signal. The strength of the obligation differs by tier:

- Editorial: trace is not required.
- Operational: MUST trace to observed failure / recurring friction /
  measurable risk / autopilot safety requirement.
- Constitutional: MUST trace to the above AND carry strategic rationale
  naming the constitutional principle being preserved or extended.

The trace MUST be a concrete reference - a session id, an audit event id, an observed friction event, a measurable risk artifact, or a named safety requirement. "It seemed like a good idea" is not a trace.

The trace MUST be present in the addendum body before the human-approval step in Article XXIX runs; an amendment lacking a trace is RETURNED, not refused - the proposer reclassifies, attaches a trace, or withdraws.

## XXIX.5 - Audit Entry Format

```
Audit entries MUST be appended to .ai/audit/events.ndjson
with event types:
- constitution.amended.editorial
- constitution.amended.operational
- constitution.amended.constitutional
Each event MUST include: actor, diff_sha256, tier, rationale_ref.
```

Field semantics:

- `actor` - the entity authoring the amendment. For human-approved
  amendments this is the operator id; for kernel-derived editorial fixes
  it is the kernel session id that produced the diff.
- `diff_sha256` - SHA-256 of the patch as applied. Computed over the
  unified diff bytes (whitespace-significant) so the audit can verify
  the on-disk change matches the recorded amendment.
- `tier` - one of `editorial`, `operational`, `constitutional`. MUST
  match the event-type suffix. A mismatched tier is itself a
  reclassification trigger (see XXIX.6).
- `rationale_ref` - canonical reference to the rationale text. For
  editorial: the git commit hash. For operational and constitutional:
  the addendum file path (relative to repo root) and the section anchor
  within it.

Events are append-only and hash-chained; the existing genesis-hash and
chain-verify discipline (Article 0 + kernel `audit verify-chain`) apply
to these event types without modification.

The emitters for these event types are DEFINED here but not WIRED in
this addendum. Wiring is deferred to a future runtime session under
Article XX (Passive Core) - declaring a taxonomy does not register
emitters.

## XXIX.6 - Classification Rule (Tiebreaker)

```
XXIX.6 - Classification Rule
When in doubt, classify upward.
Misclassification toward higher tier (e.g. editorial -> operational)
is acceptable. Misclassification toward lower tier is a
constitutional violation requiring retroactive reclassification.
```

Retroactive reclassification means: the offending amendment is
re-recorded at the correct higher tier in a NEW addendum, with the
audit chain recording the downgrade discovery as `constitution.amended.constitutional`
(event type at the corrective tier, not at the offending tier). The
prior offending audit entry is NOT mutated - the chain remains
append-only - the new entry supersedes it.

The single-operator setup makes this rule load-bearing: without an
asymmetric cost on downward misclassification, every amendment slowly
drifts toward editorial because editorial has the lowest friction. The
rule embeds the friction back into downward miscalls.

---

## Canonical Paths

For reference and to reduce agent search overhead, the three confirmed
paths involved in any Article XXIX amendment to this Constitution corpus
are:

```text
Constitution:  docs/constitution/TRINITY_CONSTITUTION_V1.md
Addendum:      docs/constitution/addendums/TRINITY_CONSTITUTION_ADDENDUM_V1_0_4.md
Pointer:       CONSTITUTION.md
```

The Pointer (`CONSTITUTION.md` at repo root) is a redirect target only - it
is never the amendment surface; amendments land in the canonical document
or in a new addendum.

---

## References

- Parent: [`../TRINITY_CONSTITUTION_V1.md`](../TRINITY_CONSTITUTION_V1.md) - Article XXIX (amendment procedure)
- Prior: [`TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md`](TRINITY_CONSTITUTION_ADDENDUM_V1_0_1.md) - Decision Velocity Tiers (precedent for tiered classification under the Constitution)
- Prior: [`TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md`](TRINITY_CONSTITUTION_ADDENDUM_V1_0_2.md) - Canonical-home relocation
- Prior: [`TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md`](TRINITY_CONSTITUTION_ADDENDUM_V1_0_3.md) - Ritual Constitution v1.1 ratification
- Pointer: [`../../../CONSTITUTION.md`](../../../CONSTITUTION.md) - root redirect
- Article XXV: Constitutional Priority Order - this Addendum sits at constitutional tier under the parent Constitution v1.0
- Article XXIX: Amendment procedure - operationalised by this Addendum
- Article XX: Passive Core - the audit event taxonomy in XXIX.5 is declared, not wired
