---
ritual: vvv
channel: desktop
purpose: "Render `ai vvv` 5-question Q&A output for a desktop terminal"
last-updated: 2026-05-10
---

# `vvv` — Desktop rendering template

> The AI rendering `ai vvv` answer-set output to a desktop terminal
> should follow these rules. The kernel writes `THINK/01_PROMPT.md`
> verbatim from the operator's answers; this template controls how the
> AI summarizes / cross-references / explains those answers back.

## Channel signals
1. `--channel=desktop` explicit.
2. `TRINITY_RENDER_CHANNEL=desktop`.
3. Default fallback.

## Format rules

### OK
- ✅ Bold Q1..Q5 headers (`Q1 (Goal)`, `Q2 (Scope)`, ...)
- ✅ Multi-line answers preserved verbatim — operator wrote it, AI shouldn't paraphrase
- ✅ Drill-down notes per Q (memory hints, prior session refs, link to relevant retro)
- ✅ Box-drawing panel framing if it adds clarity
- ✅ Trailing `vvv passed` confirmation + path to `THINK/01_PROMPT.md`

### Avoid
- ❌ Compressing operator's wording — Goal/Scope/Constraint phrases are load-bearing for nnn budget check
- ❌ Reordering questions
- ❌ Hiding the marker file path (operator may need to edit before nnn)

## Layout

```
╭────────── 📝 vvv answers ──────────╮
│ Q1 (Goal)
│   <verbatim answer>
│
│ Q2 (Scope)
│   IN: <verbatim>
│   OUT: <verbatim>
│
│ ... (Q3..Q5 same shape)
╰────────────────────────────────────╯
✅ vvv passed.
   prompt: .ai/sessions/<session>/THINK/01_PROMPT.md
   marker: .ai/sessions/<session>/.state/vvv_pass
   graph_state: THINK
👉 next: ai nnn --plan-envelope <path>
```

## When to deviate
- Operator screen narrow → fallback mobile.
- Q&A draft (pre-submit) → still show as desktop format; the verbose
  layout helps the operator catch missing answers.
