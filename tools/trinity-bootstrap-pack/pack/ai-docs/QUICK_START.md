# Quick Start — {{PROJECT_NAME}}

## First time (run once)

```bash
pip install -r .ai/requirements.txt
bash .ai/cli/ai lll
```

## Per task

1. Open a session: `bash .ai/cli/ai sss "<task-slug>"`
2. Verify intent: `bash .ai/cli/ai vvv --answers-file <json-or-yaml>`
3. Plan: `bash .ai/cli/ai nnn --plan-envelope <path>`
4. Execute: `bash .ai/cli/ai gogogo`
5. Human gate: `bash .ai/cli/ai ddd --target=dev --reason='...'`
6. Retro: `bash .ai/cli/ai rrr`
7. Close: `bash .ai/cli/ai close`

See `SHORT_CODES.md` for the canonical spec.
