from __future__ import annotations

from pathlib import Path
from typing import List

from .project_binding import ProjectBinding


START_MARKER = "<!-- TRINITY_PROJECT_BINDING_START -->"
END_MARKER = "<!-- TRINITY_PROJECT_BINDING_END -->"


class AgentShimError(RuntimeError):
    pass


def render_agents_md_block(binding: ProjectBinding) -> str:
    cli = binding.trinity_home.parent / ".ai" / "cli" / "ai"
    return f"""\
{START_MARKER}
# Trinity Project Binding

This project is bound to Trinity.

Set this shell variable in examples:

```bash
TRINITY={cli}
```

Read first:
- `.trinity/project.yaml`

## Invocation Contract

When the user types `trinity <args>` or a Trinity short code, run the central
Trinity CLI exactly. Do not replace Trinity commands with handmade shell probes
or legacy project scripts.

For a user message that begins with `trinity `, the next tool call MUST execute
the matching Trinity CLI command. Do not summarize from memory first.
For exact Trinity command requests, the Trinity CLI call must be the first and
only shell command unless it fails. Relay the CLI output directly; do not add
extra git/session probes or a synthesized action menu unless the user asks for
analysis.

Prefer the project-local wrapper when present:
- `trinity lll` means `./trinity lll`
- `trinity status` means `./trinity status`
- `trinity project doctor` means `./trinity project doctor`

Fallback if `./trinity` is missing:
- `trinity lll` means `$TRINITY lll`
- `trinity status` means `$TRINITY status`
- `trinity project doctor` means `$TRINITY project doctor`

Known wrong behavior:
- running `ls .ai/sessions`, `git status`, or `git log` by hand for `trinity lll`
- piping `./trinity lll` through `head`, `tail`, or other truncation commands
- synthesizing a example_project status report instead of executing the Trinity CLI
- running git/session probes before the Trinity CLI command

## Trinity Commands

Always run from the project root.

### Orientation
- `$TRINITY project current` — show current project identity
- `$TRINITY project doctor` — verify binding, registry, and memory DB
- `$TRINITY status` — show current workflow/session status
- `$TRINITY lll` — snapshot git/session/audit/open work

### Workflow
- `$TRINITY sss "<task>"` — start a new Trinity session
- `$TRINITY vvv` — verify understanding
- `$TRINITY nnn --plan-envelope <path>` — approve a numbered plan
- `$TRINITY gogogo` — execute/verify the approved plan
- `$TRINITY ddd --target=dev --reason="<why>"` — human promote/deploy gate
- `$TRINITY rrr` — retrospective
- `$TRINITY close` — archive the completed session

### Project Management
- `$TRINITY project add <path> --name <name>` — register a project
- `$TRINITY project list` — list registered projects
- `$TRINITY project current` — resolve the current project
- `$TRINITY project doctor` — check binding health

### Command Rule
Do not guess Trinity commands. If unsure, run:

```bash
$TRINITY doctor commands
```

Project identity:
- project: `{binding.project_slug}`
- root: `{binding.root_path}`
- memory DB: `{binding.memory_db_path}`

Before work:
1. Run Trinity project doctor.
2. Check status.
3. Do not edit Trinity registry or memory DB manually.

{END_MARKER}
"""


def install_instruction_shim(
    root_path: Path, binding: ProjectBinding, filename: str
) -> Path:
    """Create or update the Trinity-managed block in an instruction file.

    The block is kept at the top so agent harnesses see the
    executable Trinity command contract before older project-local shorthand.
    Existing user content is preserved below the managed block.
    """
    path = Path(root_path) / filename
    block = render_agents_md_block(binding).rstrip() + "\n\n"
    if not path.exists():
        path.write_text(block, encoding="utf-8")
        return path

    text = path.read_text(encoding="utf-8")
    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    if (start == -1) != (end == -1):
        raise AgentShimError(
            f"broken Trinity AGENTS.md managed block markers in {path}; "
            "expected both START and END markers"
        )
    if start != -1 and end != -1 and end >= start:
        end += len(END_MARKER)
        existing = (text[:start].rstrip() + "\n\n" + text[end:].lstrip()).strip()
    elif start != -1 and end != -1:
        raise AgentShimError(
            f"broken Trinity AGENTS.md managed block markers in {path}; "
            "END marker appears before START marker"
        )
    else:
        existing = text.strip()
    updated = block + (existing + "\n" if existing else "")
    path.write_text(updated, encoding="utf-8")
    return path


def install_agents_md_shim(root_path: Path, binding: ProjectBinding) -> Path:
    return install_instruction_shim(root_path, binding, "AGENTS.md")


def install_project_agent_shims(root_path: Path, binding: ProjectBinding) -> List[Path]:
    """Install generic AGENTS.md plus existing vendor-specific entrypoints.

    AGENTS.md is always present for Codex/generic harnesses. Vendor files are
    updated only when the project already has them, preserving existing content.
    """
    root = Path(root_path)
    paths = [install_instruction_shim(root, binding, "AGENTS.md")]
    for filename in ("CLAUDE.md", "GEMINI.md", "WARP.md"):
        if (root / filename).exists():
            paths.append(install_instruction_shim(root, binding, filename))
    return paths


def install_project_trinity_wrapper(root_path: Path, binding: ProjectBinding) -> Path:
    """Install a project-local executable wrapper: ./trinity."""
    path = Path(root_path) / "trinity"
    cli = binding.trinity_home.parent / ".ai" / "cli" / "ai"
    content = f"""#!/usr/bin/env bash
set -euo pipefail
exec {cli} "$@"
"""
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path
