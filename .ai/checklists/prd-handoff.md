# PRD Handoff Checklist

Use this before assigning a PRD-driven task or organ refactor PR.

Source:
- `trinity_organ_refactor_prd.md`

## Assignment Brief

- [ ] Organ being refactored is named.
- [ ] Role boundary is stated.
- [ ] Authority boundary is stated.
- [ ] Inputs are listed.
- [ ] Outputs are listed.
- [ ] Required artifacts are listed.
- [ ] Workflow states the organ may touch are listed.
- [ ] Failure behavior is listed.
- [ ] Audit behavior is listed.

## Scope Control

- [ ] Files allowed to mutate are listed.
- [ ] Forbidden paths are listed.
- [ ] Forbidden behaviors are listed.
- [ ] Non-goals are listed.
- [ ] Related organs that must not be absorbed are named.
- [ ] Human-gated actions are named.

## Acceptance Contract

- [ ] Acceptance criteria are measurable.
- [ ] Required checks are listed.
- [ ] Required tests are listed.
- [ ] Audit event expectations are listed.
- [ ] Rollback path is documented.
- [ ] Documentation/spec updates are listed.

## Reviewer Checklist

- [ ] Did this reduce role collapse?
- [ ] Did it avoid semantic overreach?
- [ ] Did it keep command code as a ritual gate?
- [ ] Did it preserve artifact visibility?
- [ ] Did it preserve audit visibility?
- [ ] Did it avoid changing unrelated organs?
- [ ] Did it avoid creating a new god object?

## Definition Of Done

- [ ] Tests pass.
- [ ] Smoke path demonstrates expected behavior.
- [ ] Failure mode is visible.
- [ ] No forbidden pattern remains.
- [ ] Spec or PRD reference is updated.
- [ ] Follow-up work is explicitly listed or ruled out.
