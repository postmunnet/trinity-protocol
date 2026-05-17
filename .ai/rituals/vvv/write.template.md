# vvv — Clarification Prompt

- **Session:** {{plain_text:session.slug}}
- **Operator:** {{plain_text:operator.name}}
- **Proposed at (UTC):** {{plain_text:vvv.proposed_at_utc}}
- **Ritual:** vvv (Clarification Gate)
- **Authority:** Trinity Ritual Constitution v1.1-rc, Article V / VI / XVIII; Ritual Contract v1.0 — vvv clauses.

> The five answers below are operator-provided data, not AI-synthesized.
> Per Trinity Constitution Article III, the AI may not self-certify
> understanding; per Article XX (Passive Core), this artifact exists only
> because the operator answered. Empty or AI-fabricated answers MUST be
> rejected by the kernel check (see check.template.json).

## Q1 Goal

> What does success look like? (one sentence)

{{markdown_escaped:answer.q1_goal}}

## Q2 Scope

> What is explicitly in scope? What is out?

{{markdown_escaped:answer.q2_scope}}

## Q3 Constraint

> What cannot be touched? (policies, boundary docs, forbidden paths)

{{markdown_escaped:answer.q3_constraint}}

## Q4 Acceptance

> What measurable signal proves 'done'?

{{markdown_escaped:answer.q4_acceptance}}

## Q5 Risk

> What is the most likely failure mode? How will we notice it?

{{markdown_escaped:answer.q5_risk}}

---

## Next Ritual

On `vvv.passed`, the kernel writes `.state/vvv_pass` and remains in state
`THINK`. The operator may then invoke `nnn` to transition `THINK → PLAN`
with a budgeted plan envelope.
