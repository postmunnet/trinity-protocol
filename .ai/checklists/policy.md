# Policy Checklist

Use this before changing `.ai/policies/**` or policy behavior.

Sources:
- `docs/specs/TRINITY_POLICY_ENGINE_SPEC_V1.md`
- `docs/ai_entry/BOUNDARIES.md`
- `AGENTS.md`

## Gate

- [ ] Human has explicitly approved policy work.
- [ ] The amendment tier is declared: editorial, operational, or constitutional.
- [ ] Operational/constitutional changes include a trace-to-failure reference.
- [ ] The diff is reviewable text; no binary policy blobs.
- [ ] Impact analysis lists every kernel call site that reads the affected rule.

## Boundary

- [ ] The change does not encode a verifier decision.
- [ ] The change does not encode a state-machine transition.
- [ ] The change preserves default-deny semantics.
- [ ] The change does not grant policy write authority to tools or agents.
- [ ] The change does not weaken forbidden path or secret handling.

## Artifact And Audit

- [ ] The affected policy version/frontmatter is bumped when applicable.
- [ ] The decided_by/human rationale is prepared.
- [ ] Expected audit event format is named.
- [ ] Rollback path is documented.
- [ ] Policy amendment is referenced from the session plan.

## Verification

- [ ] YAML parses cleanly.
- [ ] Policy-specific tests pass.
- [ ] Kernel startup still loads policy files.
- [ ] Negative test exists for the forbidden action being controlled.
- [ ] `bash .ai/cli/ai audit verify-chain` passes.

## Return Conditions

Return to proposer if any item is true:

- [ ] No trace-to-failure exists for operational/constitutional change.
- [ ] The policy encodes verifier judgment.
- [ ] The policy encodes graph transition authority.
- [ ] The policy creates broad allow-by-default behavior.
- [ ] The amendment cannot be reviewed from git diff.
