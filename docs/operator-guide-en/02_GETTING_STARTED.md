# Getting Started

Run from the repository root:

```bash
bash .ai/cli/ai status
bash .ai/cli/ai lll
```

Start a session:

```bash
bash .ai/cli/ai sss "Try Trinity with a small documentation task"
```

Answer `vvv`:

```bash
bash .ai/cli/ai vvv \
  --answer 1="Success means a clear plan exists" \
  --answer 2="Only docs are in scope" \
  --answer 3="Do not modify source code" \
  --answer 4="A plan file and acceptance criteria exist" \
  --answer 5="The scope may be too broad"
```

Check status:

```bash
bash .ai/cli/ai status
```

## Read The Session Capsule

After `sss`, Trinity creates:

```text
.ai/sessions/<session-id>/
  THINK/
  SANDBOX/
  DO/
  CONTROL/
  CAPTURE/
  .state/
```

If you are lost:

- read `CONTROL/` for work status
- read `THINK/` for goal, scope, and plan
- read `CAPTURE/` for evidence
- read `.state/session_state.json` for `graph_state`
- read `.ai/audit/events.ndjson` for the truth log
