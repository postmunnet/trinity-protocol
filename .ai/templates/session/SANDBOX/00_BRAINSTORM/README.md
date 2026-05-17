# BRAINSTORM — Divergent Ideation (before DEBATE)

**Purpose:** generate options openly before narrowing to a decision

## Flow

```
BRAINSTORM                    DEBATE                  DO
(diverge)         →           (converge)      →       (build)
── สร้างตัวเลือก              ── เลือก 1 ตัว           ── ลงมือทำ
── ไม่ judge                  ── judge ด้วย criteria   ── ตาม verdict
── ทุกคนเสนอได้               ── 3 seat + chair        ── single ingress
── output: shortlist          ── output: verdict       ── output: diff
```

BRAINSTORM's output (`04_SHORTLIST.md`) = DEBATE's input (proposal candidates)

## Files

| File | Role |
|---|---|
| `00_SEED.md` | Opening prompt — what are we brainstorming? scope, constraints, forbidden zones |
| `01_DIVERGE.md` | Free-form idea dump. Quantity > quality. No filtering, no judging yet |
| `02_CLUSTER.md` | Group similar ideas into themes. Still no evaluation |
| `03_EVALUATE.md` | Pro/con per cluster. Surface risks, costs, dependencies |
| `04_SHORTLIST.md` | Top 3-5 candidates that go to DEBATE as options (A/B/C/…) |
| `agents/{gemini,claude,codex}.md` | Optional per-agent freestyle contributions |
| `archive/` | Past brainstorms (moved here when debate for that topic closes) |

## Rules

1. **No kill criterion in brainstorm** — this is the "yes, and" phase
2. **Every participant can add** — unlike DEBATE (3 seats only), BRAINSTORM welcomes human + any agent + hooks
3. **Shortlist is democratic but not binding** — DEBATE can reject all options and push back to BRAINSTORM
4. **One BRAINSTORM per DEBATE** — don't mix topics; spawn new brainstorm for next decision

## When to skip BRAINSTORM

- Scope is already narrowed by human (e.g. "use exactly X")
- Re-running a known pattern (copy past debate's verdict pattern)
- Emergency fix (bug → direct to DO)

## When BRAINSTORM is mandatory

- New problem type (never done before)
- Multiple viable architectures in play
- Budget/scope high (≥ 1 week dev)
- Disagreement in prior verdict requires re-open
