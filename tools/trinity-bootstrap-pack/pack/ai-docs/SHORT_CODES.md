# Trinity Short Codes — Canonical Spec

| Code | Maps to | Purpose |
|------|---------|---------|
| `lll` | `ai status` | Look / List status |
| `sss <task>` | `ai session new <task>` | Start session + snapshot |
| `nnn` | `ai nnn --plan-envelope <path>` | Plan + budget check |
| `vvv` | `ai vvv` | Verify intent (5 questions) |
| `gogogo` | `ai gogogo` | Execute plan incrementally |
| `ddd` | `ai ddd` | Done / human gate |
| `rrr` | `ai rrr` | Retrospective + memory update |

Graph order: `nnn_pass → vvv_pass → gogogo`.

The kernel enforces sequence per `.ai/graphs/standard.yaml`.

Source of truth (upstream): https://github.com/anthropics/trinity_v2 (or local kernel `.ai/cli/COMMAND_MANIFEST.yaml`).
