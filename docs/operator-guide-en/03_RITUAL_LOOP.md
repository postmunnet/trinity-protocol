# Ritual Loop

Trinity rituals are executable gates. They are not decorative command names.

| Ritual | Purpose | Main Output | Typical Next State |
| --- | --- | --- | --- |
| `lll` | Snapshot/status | console snapshot | unchanged |
| `sss` | Open session and intent | session capsule | `READY` |
| `vvv` | Verify understanding | `THINK/01_PROMPT.md`, marker | `THINK` |
| `nnn` | Normalize plan and budget | plan, scope, acceptance | `DO` |
| `gogogo` | Execute approved plan | step verdicts | `VERIFIED` |
| `ddd` | Human deploy/promote gate | decision packet | `PROMOTED`/`DEPLOYED` |
| `rrr` | Retro and memory index | retro/evidence | `DONE` |
| `close` | Close/archive safely | final manifest | closed |

## Important Rules

```text
Do not skip vvv
Do not let the executor declare done by itself
Do not deploy without a human gate
Do not tag a release from a dirty worktree
```

## CLI Manifest

Do not guess commands from ritual names. Use the manifest-backed CLI:

```bash
bash .ai/cli/ai doctor commands
```

Or call rituals directly:

```bash
bash .ai/cli/ai sss "task"
bash .ai/cli/ai vvv ...
bash .ai/cli/ai nnn --plan-envelope path/to/plan.json
```
