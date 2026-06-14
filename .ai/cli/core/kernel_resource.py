"""Kernel-source fallback resolution for project-local .ai resources.

Thin-client doctrine (retro-0055/0061/0063 → P0-3 batch, 2026-06-10):
linked client projects strip most of the vendored `.ai/` tree. Every
kernel codepath that reads a *kernel-default* resource from
`<project_root>/.ai/...` must therefore fall back to the kernel's own
shipped copy — loudly, never silently — when the project-local file is
absent.

Eligible resources are kernel defaults only (verifier rules, graphs,
loop-budget, trinity_policy, sandbox profiles, rituals, templates).
Project-identity files (`.ai/ssot.yaml`) are NEVER eligible: their
absence is a load-bearing signal (retro-0056) and must keep failing.

Every fallback prints exactly one stderr note so the operator (and
`ai doctor resources`) can always tell which source is live.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Tuple

# parents[2] of cli/core/kernel_resource.py is the kernel `.ai` dir
# (mirrors ritual_pack_loader / TemplateLoader fallbacks, retro-0061/0063).
_KERNEL_AI_ROOT = Path(__file__).resolve().parents[2]

# Resources `ai doctor resources` reports on. rel paths are under `.ai/`.
FALLBACK_RESOURCES = (
    ("verifier-rules", "policies/verifier-rules.yaml"),
    ("graph:standard", "graphs/standard.yaml"),
    ("graph:deploy", "graphs/deploy.yaml"),
    ("loop-budget", "policies/loop-budget.yaml"),
    ("trinity-policy", "policies/trinity_policy.yaml"),
    ("rituals", "rituals"),
    ("templates", "templates"),
)


def kernel_ai_root() -> Path:
    return _KERNEL_AI_ROOT


def resolve_ai_resource(
    project_root: Path,
    rel: str,
    *,
    label: str,
    quiet: bool = False,
) -> Tuple[Optional[Path], str]:
    """Resolve `.ai/<rel>` preferring the project, then the kernel source.

    Returns (path, source) where source is "project" | "kernel" | "missing"
    (path is None when missing). On kernel fallback a single loud stderr
    note is printed unless quiet=True (doctor uses quiet for reporting).
    """
    project_path = Path(project_root) / ".ai" / rel
    if project_path.exists():
        return project_path, "project"
    kernel_path = _KERNEL_AI_ROOT / rel
    if kernel_path.exists():
        if not quiet:
            print(
                f"[trinity] {label}: project-local .ai/{rel} missing — "
                f"using kernel default ({kernel_path})",
                file=sys.stderr,
            )
        return kernel_path, "kernel"
    return None, "missing"
