# Decision Packet

- **Session:** {{plain_text:session.slug}}
- **Tier:** {{enum:plan.tier}}
- **Requested at (UTC):** {{plain_text:requested_at_utc}}
- **Requested Action:** {{enum:requested_action}}
- **Ritual:** ddd (Human Decision Gate)
- **Authority:** Trinity Constitution Articles XIII (Human Authority) & XV (Transport is not Authority); Ritual Constitution v1.1-rc Articles V/VI/XII/XIV/XV/XVI/XVII/XVIII; Ritual Contract v1.0 — ddd clauses.

> This packet is rendered for human review only. Per Constitution Article III,
> the AI MUST NOT self-decide; per Article XV, transport (tg-bot, webhook,
> etc.) MAY deliver the operator's signed envelope but MUST NOT approve.
> Kernel verifies the HMAC envelope and records `decided_by: human` —
> any other decider value is rejected (exit 79 contract).

## Goal

{{markdown_escaped:plan.goal}}

## Verifier Report

{{markdown_escaped:verifier_report_summary}}

- **Evidence:** {{evidence_ref:verifier_report_ref}}
- **Audit chain anchor at proposal:** {{evidence_ref:audit_chain_anchor}}

## Risk

{{markdown_escaped:risk_summary}}

### Dissent (preserved per Article XIII)

{{markdown_escaped:dissent_summary}}

## Requested Action

The operator is asked to authorize the following action: **{{enum:requested_action}}**.

Possible outcomes:

- **Approve** → kernel writes `.state/ddd/approval.json`, emits `ddd.approved`, transitions `VERIFY → PROMOTE`.
- **Reject** → kernel writes `.state/ddd/rejection.json`, emits `ddd.rejected`, transitions `VERIFY → FAILED`.
- **Hold** → kernel writes `.state/ddd/hold.json`, emits `ddd.held`, transitions `VERIFY → NEEDS_HUMAN` (operator may re-issue decision later; max 3 retries per retry_policy).

---

## Next Ritual

On `ddd.approved`, the kernel transitions to `PROMOTE`; the operator may
then invoke `gogogo` for deploy/promote execution or proceed to `rrr` for
retrospective if the gated action was the terminal step. On `ddd.rejected`
the session enters `FAILED` and the operator must open a remediation
session. On `ddd.held` the session waits in `NEEDS_HUMAN` for a renewed
decision packet.
