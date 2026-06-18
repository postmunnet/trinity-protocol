"""Phase 8 — Trinity Shim adapter renderer.

Spec: docs/specs/07_SHIM_SPEC.md, .ai/shims/<code>/SHIM.md.

Reads canonical shim YAML-frontmatter from `.ai/shims/<code>/SHIM.md`
and emits vendor-specific adapter files so the short codes
(`lll`, `vvv`, `nnn`, `gogogo`, `rrr`) become first-class
prompts/commands in each AI tool.

Vendor targets (one per ritual × vendor):

  claude-code    .claude/commands/<code>.md       (Claude Code slash command)
  cursor         .cursor/rules/<code>.mdc          (Cursor rule)
  agents         AGENTS.md fragment                (concatenated by caller)
  warp           .warp/workflows/<code>.yaml       (Warp workflow)

Each adapter is generated from the shim's frontmatter — the canonical
purpose line, plus the `ai <code>` invocation line. Adapters do NOT
re-implement ritual semantics; they just point the vendor harness at
the kernel CLI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Full ritual surface — sss/ddd gained shims 2026-05-11 / 2026-06-10 (D2/D3).
SHORT_CODES = ["lll", "sss", "vvv", "nnn", "gogogo", "ddd", "rrr"]
VENDORS = ["claude-code", "cursor", "agents", "warp"]


@dataclass
class ShimSpec:
    code: str
    purpose: str
    status: str
    last_updated: str
    body: str
    # P3: per-ritual Claude operational content extracted from the SHIM.md body's
    # delimited `trinity:claude-section:operational` region. None = no section
    # (the Claude adapter falls back to the generic implementation block).
    claude_operational: Optional[str] = None


# P3 (Fork A) — structured body-section contract for per-ritual Claude adapter
# content. The renderer extracts ONLY the text between these exact markers; it
# never renders the rest of the SHIM.md body (proves this is structured
# extraction, not raw body injection).
_CLAUDE_OP_START = "<!-- trinity:claude-section:operational:start -->"
_CLAUDE_OP_END = "<!-- trinity:claude-section:operational:end -->"


def _extract_claude_operational(body: str) -> Optional[str]:
    """Return the inner text of the delimited Claude operational section.

    - present (exactly one start + one end, in order) -> inner text, stripped
    - missing (zero start + zero end)                 -> None (generic fallback)
    - malformed (count mismatch, or end-before-start) -> ValueError (never a
      silent drop)

    Content outside the delimiters is never returned.
    """
    starts = body.count(_CLAUDE_OP_START)
    ends = body.count(_CLAUDE_OP_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ValueError(
            "malformed claude-operational section: "
            f"{starts} start / {ends} end marker(s) (expected exactly 1 each)"
        )
    i = body.index(_CLAUDE_OP_START) + len(_CLAUDE_OP_START)
    j = body.index(_CLAUDE_OP_END)
    if j < i:
        raise ValueError(
            "malformed claude-operational section: end marker precedes start"
        )
    return body[i:j].strip()


def _parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Tiny YAML-frontmatter reader (scalar-only, no nested maps)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_raw = parts[1]
    body = parts[2].lstrip("\n")
    out: Dict[str, str] = {}
    for line in fm_raw.splitlines():
        line = line.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*)$", line)
        if not m:
            continue
        out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out, body


def load_shim(shims_dir: Path, code: str) -> ShimSpec:
    p = shims_dir / code / "SHIM.md"
    if not p.exists():
        raise FileNotFoundError(f"shim missing: {p}")
    text = p.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    return ShimSpec(
        code=fm.get("short-code") or code,
        purpose=fm.get("purpose", ""),
        status=fm.get("status", ""),
        last_updated=fm.get("last-updated", ""),
        body=body,
        claude_operational=_extract_claude_operational(body),
    )


def load_all_shims(shims_dir: Path) -> List[ShimSpec]:
    return [load_shim(shims_dir, c) for c in SHORT_CODES]


# ─────────── Claude Code (.claude/commands/<code>.md) ───────────


def render_claude_code(spec: ShimSpec) -> str:
    # Universal R30 head — every Claude adapter gets the two-layer rendering
    # contract regardless of ritual.
    head = (
        f"# `{spec.code}` — {spec.purpose}\n\n"
        f"Run the Trinity ritual `{spec.code}` via the kernel CLI.\n\n"
        f"## What this does\n\n"
        f"{spec.purpose}.\n"
        f"Invoke `ai {spec.code}`. Render in two layers "
        f"(operator decision 2026-06-12):\n\n"
        f"1. **Kernel artifacts are verbatim** — the kernel's panels, "
        f"verdicts, tables, and next-step footer MUST be shown "
        f"unmodified: never edited, truncated, re-worded, or replaced "
        f"by a summary. The next-step footer comes from the kernel, "
        f"not from the adapter.\n"
        f"2. **Around the artifact**, the agent MAY add "
        f"orientation/summary per the channel template "
        f"(`.ai/shims/{spec.code}/templates/<channel>.md`) — desktop "
        f"keeps additions minimal; mobile re-formats per its template "
        f"because the transport strips panels anyway. Commentary must "
        f"never contradict or reinterpret a kernel verdict.\n\n"
    )
    # P3: when the SHIM.md declares a structured operational section, it OWNS the
    # ritual-specific "how to invoke + caveats" (replaces the generic block).
    # Otherwise emit the generic single-command implementation (lll/rrr/ddd/sss).
    if spec.claude_operational:
        middle = spec.claude_operational.rstrip() + "\n\n"
    else:
        middle = (
            f"## Implementation\n\n"
            f"```bash\n"
            f"!ai {spec.code}\n"
            f"```\n\n"
        )
    return (
        head
        + middle
        + f"## Canonical spec\n\n`.ai/shims/{spec.code}/SHIM.md`\n"
    )


# ─────────── Cursor (.cursor/rules/<code>.mdc) ───────────


def render_cursor(spec: ShimSpec) -> str:
    return (
        f"---\n"
        f"description: \"`{spec.code}` — {spec.purpose}\"\n"
        f"globs: [\"**\"]\n"
        f"alwaysApply: false\n"
        f"---\n\n"
        f"# Trinity Ritual: {spec.code}\n\n"
        f"When the user types `{spec.code}` (or `/{spec.code}`) as a "
        f"message, treat it as a command, not chatter. Run the "
        f"Trinity kernel CLI:\n\n"
        f"```bash\n"
        f"ai {spec.code}\n"
        f"```\n\n"
        f"Show the kernel's artifacts (panels, verdicts, tables, "
        f"next-step footer) verbatim — never edit, truncate, or "
        f"replace them. You MAY add brief orientation around the "
        f"artifact per the channel template, but never contradict or "
        f"reinterpret a kernel verdict. The audit chain depends on the "
        f"ritual firing with its artifacts un-rephrased.\n\n"
        f"Spec: `.ai/shims/{spec.code}/SHIM.md`.\n"
    )


# ─────────── AGENTS.md fragment (concatenable) ───────────


def render_agents_fragment(spec: ShimSpec) -> str:
    return (
        f"### `{spec.code}` — {spec.purpose}\n\n"
        f"On the keyword `{spec.code}` (alone on a line, or as the "
        f"first token), invoke:\n\n"
        f"    ai {spec.code}\n\n"
        f"Show the kernel's artifacts verbatim; you may add brief "
        f"orientation around them but never alter or reinterpret a "
        f"verdict. Spec: "
        f"`.ai/shims/{spec.code}/SHIM.md`.\n"
    )


def render_agents_full(specs: List[ShimSpec]) -> str:
    head = (
        "# Trinity Short Codes — AGENTS.md fragment\n\n"
        "_Generated by `ai shim render --target=agents` — do not "
        "hand-edit; re-run instead._\n\n"
        "When the user types one of the short codes below as a "
        "message, treat it as a command, run the listed kernel CLI "
        "invocation, and show the kernel's artifacts verbatim — you "
        "may add brief orientation around them, but never alter or "
        "reinterpret a verdict.\n\n"
    )
    return head + "\n".join(render_agents_fragment(s) for s in specs)


# ─────────── Warp (.warp/workflows/<code>.yaml) ───────────


def render_warp(spec: ShimSpec) -> str:
    return (
        f"---\n"
        f"name: \"trinity:{spec.code}\"\n"
        f"description: \"{spec.purpose}\"\n"
        f"command: \"ai {spec.code}\"\n"
        f"tags: [trinity, {spec.code}]\n"
        f"shells: [bash, zsh, fish]\n"
        f"arguments: []\n"
        f"---\n"
    )


# ─────────── Renderer dispatch ───────────


VENDOR_PATHS: Dict[str, Tuple[str, str]] = {
    # vendor → (relative path template, file extension)
    "claude-code": (".claude/commands/{code}.md", "md"),
    "cursor":      (".cursor/rules/{code}.mdc",   "mdc"),
    "warp":        (".warp/workflows/{code}.yaml", "yaml"),
    # agents is special: concatenated single file
}


def render_one(vendor: str, spec: ShimSpec) -> str:
    if vendor == "claude-code":
        return render_claude_code(spec)
    if vendor == "cursor":
        return render_cursor(spec)
    if vendor == "agents":
        return render_agents_fragment(spec)
    if vendor == "warp":
        return render_warp(spec)
    raise ValueError(
        f"unknown vendor {vendor!r}; supported: {', '.join(VENDORS)}"
    )


def render_all(
    project_root: Path, vendor: str, *, dry_run: bool = False
) -> Dict[str, str]:
    """Render adapters for all 5 short codes for one vendor.

    Returns a dict mapping the *target relative path* → rendered text.
    When dry_run=False, writes each file and creates parent dirs.
    """
    if vendor not in VENDORS:
        raise ValueError(
            f"unknown vendor {vendor!r}; supported: {', '.join(VENDORS)}"
        )
    shims_dir = project_root / ".ai" / "shims"
    specs = load_all_shims(shims_dir)
    out: Dict[str, str] = {}

    if vendor == "agents":
        body = render_agents_full(specs)
        rel = ".ai/shims/AGENTS_FRAGMENT.md"
        out[rel] = body
    else:
        path_tpl, _ext = VENDOR_PATHS[vendor]
        for spec in specs:
            rel = path_tpl.format(code=spec.code)
            out[rel] = render_one(vendor, spec)

    if not dry_run:
        for rel, body in out.items():
            abs_p = project_root / rel
            abs_p.parent.mkdir(parents=True, exist_ok=True)
            abs_p.write_text(body, encoding="utf-8")
    return out
