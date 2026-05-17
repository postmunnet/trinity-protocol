# Ritual Loop

Trinity ใช้ ritual เป็น gate ที่ executable ได้ ไม่ใช่คำสั่งพิธีกรรมลอย ๆ

| Ritual | Purpose | Output หลัก | Next state โดยทั่วไป |
| --- | --- | --- | --- |
| `lll` | ดู snapshot/status | console snapshot | ไม่เปลี่ยน state |
| `sss` | เปิด session และ intent | session capsule | `READY` |
| `vvv` | verify understanding | `THINK/01_PROMPT.md`, marker | `THINK` |
| `nnn` | normalize plan + budget | plan, scope, acceptance | `DO` |
| `gogogo` | execute approved plan | step verdicts | `VERIFIED` |
| `ddd` | human deploy/promote gate | decision packet | `PROMOTED`/`DEPLOYED` |
| `rrr` | retro + memory index | retro/evidence | `DONE` |
| `close` | close/archive safely | final manifest | closed |

## Rule สำคัญ

```text
อย่าข้าม vvv
อย่าให้ executor declare done เอง
อย่า deploy โดยไม่มี human gate
อย่า tag release จาก dirty worktree
```

## CLI Manifest

อย่าเดา command จาก ritual name เอง ให้ใช้ manifest-backed CLI:

```bash
bash .ai/cli/ai doctor commands
```

หรือเรียกโดยตรง:

```bash
bash .ai/cli/ai sss "task"
bash .ai/cli/ai vvv ...
bash .ai/cli/ai nnn --plan-envelope path/to/plan.json
```
