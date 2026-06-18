# Shim surface ownership — generated vs manual-pending-P3

> **Doctrine:** vendor surface files (`.claude/commands/*`, `.cursor/rules/*`,
> `.warp/workflows/*`, `AGENTS_FRAGMENT.md`) are **generated artifacts**.
> `core/trinity_v2/.ai/cli/core/shim_render.py` is the **source of truth for
> surface wording**; the kernel `commands/*.py` is the source of truth for
> ritual *semantics*. A vendor file must **never** become a semantic
> source-of-truth. If a surface needs better wording, encode it in
> `shim_render.py` and lock it with a test — do not hand-edit the generated file.

Last reconciled: 2026-06-18 (R30 layered-rendering wording + B-lite surface render).

## Ownership matrix

| vendor | surface | status |
|---|---|---|
| **cursor** | `.cursor/rules/*.mdc` (7/7) | ✅ generated |
| **warp** | `.warp/workflows/*.yaml` (7/7) | ✅ generated |
| **agents** | `.ai/shims/AGENTS_FRAGMENT.md` | ✅ generated |
| **claude** | `.claude/commands/{lll,rrr,ddd,sss}.md` (4/7) | ✅ generated |
| **claude** | `.claude/commands/{vvv,nnn,gogogo}.md` (3/7) | 🛑 **manual-pending-P3** |

## Why 3 Claude files are still manual (TEMPORARY, NOT a permanent exception)

`vvv`, `nnn`, `gogogo` Claude command files carry **per-ritual operational
content** that the frontmatter-only generator cannot emit:

- **vvv** — two-phase invocation (`ai vvv --show` → `ai vvv --answer`), the
  "why not bare `ai vvv`" audit-pollution warning, the pre-flight (session
  required) note, and show-before-submit / Q2 files-expected guidance.
- **nnn** — ritual-specific plan-envelope / budget operational guidance.
- **gogogo** — ritual-specific incremental-execution / evidence-gate guidance.

Re-rendering these today with the generic generator would **regress** that
content. They therefore stay hand-authored **until P3 lands**. This deferral is
**tracked and tripwired**, not silent: see
`core/trinity_v2/.ai/cli/tests/test_shim_render.py` →
`CLAUDE_MANUAL_PENDING_P3` + `test_pending_p3_*`. The tripwire test fails LOUD
if the generator ever starts emitting that per-ritual content, forcing this set
to be revisited (so the deferral can never rot into a forgotten exception).

## P3 — the contract that closes this gap (do NOT just inject the body)

P3 is **not** "dump `SHIM.md` body into the renderer" — that turns the markdown
body into an unmanaged token blob. P3 = **structured per-ritual adapter
content**:

```
Goal: generate ritual-specific Claude adapter sections WITHOUT making the
      vendor file a source-of-truth.

Input: structured fields the renderer consumes deterministically, e.g. in
       SHIM.md frontmatter —
  claude:
    two_phase: ...        # invocation shape
    usage: ...
    preflight: ...        # session-required etc.
    warnings: ...         # e.g. "why not bare ai vvv" audit pollution
    audit_notes: ...

Output: render_claude_code() emits the generic R30 two-layer block PLUS the
        ritual-specific operational sections from those fields.

Result: vvv / nnn / gogogo become safely generated → removed from
        CLAUDE_MANUAL_PENDING_P3 → re-rendered → 7/7 generated.
```

Until the section contract above exists, the 3 files remain manual-pending-P3.
