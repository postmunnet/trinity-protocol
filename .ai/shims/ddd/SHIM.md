---
short-code: ddd
purpose: "Deploy decision — the human-decided promote + deploy gate"
status: stub
spec: docs/specs/07_SHIM_SPEC.md §3.2
last-updated: 2026-06-10
---

# `ddd` — Canonical Shim

## Purpose

The **human-decided** gate between a verified session and a deployed
artifact. `ddd` fires the `promote_request` (VERIFIED → PROMOTED) and
`deploy_request` (PROMOTED → DEPLOYED) transitions — both carry
`decided_by: human` + `require_human_approval: true` in the graph
(`.ai/graphs/standard.yaml`). The kernel never auto-promotes.

Only artifact-shipping sessions need `ddd`; doc/analysis sessions may
go straight from VERIFIED to `rrr` *(the graph still routes through
DEPLOYED — `ddd --target=dev` is the no-op-deploy convention for them)*.

## When to invoke

- After `gogogo` completes (graph_state = VERIFIED)
- Before `rrr` — the retro reads the deploy decision from the audit chain

## Inputs

| Field | Required | Source |
|-------|----------|--------|
| `--target dev\|prod` | yes | human decision |
| `--reason "<text>"` | yes | human decision, stamped into audit |
| evidence file (JSON/YAML) | optional | `--evidence` for deploy_check verifier |
| HMAC envelope | optional | remote transport (tg-bot) |

## What the kernel does

1. Verifies graph_state is VERIFIED (or PROMOTED for the second hop)
2. Appends `promote_request` / `deploy_request` with `decided_by: human`
3. Runs the `deploy_check` verifier rule_set **advisorily** — the verdict
   is recorded in the audit chain (`verifier.deploy_check`) but the
   transition remains a human decision
4. Optionally dispatches `ai deploy --target=<t>`
5. Appends `ddd.completed` + `graph.transition`

## Behavior contract

**MUST**
- Require an explicit `--reason`; refuse empty reasons
- Stamp `decided_by: human` (or `human:tg:<user_id>` via HMAC transport)
- Record the deploy_check verdict in the audit chain even when ignored
- Block `--target=prod` without a verified human authority chain

**MUST NOT**
- Auto-promote or auto-deploy on a verifier PASS
- Treat a transport message as approval (Article XV — transport ≠ authority)
- Skip the audit append on refusal paths

## Known gap (P1 backlog)

The deploy_check verdict is advisory: an operator can approve a deploy
whose check FAILED and the audit cannot distinguish "saw the failure and
accepted the risk" from "never looked". Planned fix: explicit
`--accept-failed-check "<reason>"` flag required when the verdict is not
PASS (see WORKFLOW_FULL_REVIEW_2026-06-10 §A2).

## Output shape

```
audit: promote_request → verifier.deploy_check → deploy_request → ddd.completed
graph: VERIFIED → PROMOTED → DEPLOYED   (or VERIFIED → DEPLOYED for dev)
optional: decision packet JSON (--packet)
```

## Adapter rendering hints

- Surface the deploy_check verdict prominently BEFORE asking the human
  to confirm — the gate is only meaningful if the human saw the evidence
- Render `--target=prod` requests with maximum friction (type-CONFIRM)
