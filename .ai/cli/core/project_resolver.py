from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .project_binding import ProjectBinding, find_binding_path, read_project_binding
from .project_registry import (
    ProjectRecord,
    ProjectRegistry,
    default_memory_home,
    default_trinity_home,
)
from .project_slug import slugify_project_name


class ProjectResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedProject:
    project_id: str
    project_slug: str
    project_name: str
    root_path: Path
    memory_home: Path
    memory_db_path: Path
    trinity_home: Path
    source: str
    registered: bool
    binding_path: Optional[Path] = None
    registry_path: Optional[Path] = None


def resolve_current_project(
    *,
    start_path: Optional[Path] = None,
    project_ref: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    registry: Optional[ProjectRegistry] = None,
    allow_fallback: bool = True,
) -> ResolvedProject:
    """Resolve the active project identity and memory DB path.

    Priority:
      1. explicit project_ref
      2. TRINITY_PROJECT / MEMORY_PROJECT
      3. cwd/.trinity/project.yaml
      4. registry root_path match
      5. git root basename
      6. cwd basename
    """
    e = os.environ if env is None else env
    cwd = Path(start_path or Path.cwd()).expanduser().resolve()
    reg = registry if registry is not None else ProjectRegistry.existing_default(e)

    if project_ref:
        if reg is None:
            raise ProjectResolutionError(
                f"No project registry found. Run: trinity project add . or pass a registered --project."
            )
        return _resolve_ref(reg, project_ref, "explicit")

    env_ref = e.get("TRINITY_PROJECT") or e.get("MEMORY_PROJECT")
    if env_ref:
        if reg is None:
            raise ProjectResolutionError(
                f"{'TRINITY_PROJECT' if e.get('TRINITY_PROJECT') else 'MEMORY_PROJECT'} is set to "
                f"{env_ref!r}, but no project registry exists."
            )
        return _resolve_ref(reg, env_ref, "environment")

    binding_path = find_binding_path(cwd)
    if binding_path:
        binding = read_project_binding(binding_path)
        registered = False
        registry_path = None
        if reg is not None:
            record = reg.get_by_slug(binding.project_slug)
            registered = record is not None
            registry_path = reg.path
            if record:
                _mark_used_best_effort(reg, record.project_slug)
        return _from_binding(
            binding,
            source="binding",
            registered=registered,
            registry_path=registry_path,
        )

    if reg is not None:
        matches = reg.match_root(cwd)
        if len(matches) == 1:
            _mark_used_best_effort(reg, matches[0].project_slug)
            return _from_record(matches[0], "registry", reg.path)
        if len(matches) > 1:
            slugs = ", ".join(r.project_slug for r in matches)
            raise ProjectResolutionError(
                f"Ambiguous registered project for {cwd}: {slugs}"
            )

    if not allow_fallback:
        raise ProjectResolutionError(
            "No registered project found. Run: trinity project add . or pass: --project <name>"
        )

    git_root = _git_root(cwd)
    if git_root:
        return _fallback_project(git_root, "git", e)

    return _fallback_project(cwd, "cwd", e)


def _resolve_ref(
    registry: ProjectRegistry,
    ref: str,
    source: str,
) -> ResolvedProject:
    matches = registry.lookup(ref)
    if not matches:
        raise ProjectResolutionError(
            f"No registered project found for {ref!r}. Run: trinity project list"
        )
    if len(matches) > 1:
        slugs = ", ".join(r.project_slug for r in matches)
        raise ProjectResolutionError(
            f"Ambiguous project reference {ref!r}; matches: {slugs}"
        )
    _mark_used_best_effort(registry, matches[0].project_slug)
    return _from_record(matches[0], source, registry.path)


def _from_record(
    record: ProjectRecord,
    source: str,
    registry_path: Path,
) -> ResolvedProject:
    return ResolvedProject(
        project_id=record.project_id,
        project_slug=record.project_slug,
        project_name=record.project_name,
        root_path=record.root_path,
        memory_home=record.memory_home,
        memory_db_path=record.memory_db_path,
        trinity_home=registry_path.parent,
        source=source,
        registered=True,
        binding_path=record.binding_path,
        registry_path=registry_path,
    )


def _from_binding(
    binding: ProjectBinding,
    *,
    source: str,
    registered: bool,
    registry_path: Optional[Path],
) -> ResolvedProject:
    return ResolvedProject(
        project_id=binding.project_id,
        project_slug=binding.project_slug,
        project_name=binding.project_name,
        root_path=binding.root_path,
        memory_home=binding.memory_home,
        memory_db_path=binding.memory_db_path,
        trinity_home=binding.trinity_home,
        source=source,
        registered=registered,
        binding_path=binding.binding_path,
        registry_path=registry_path,
    )


def _fallback_project(
    root_path: Path, source: str, env: Optional[Dict[str, str]] = None
) -> ResolvedProject:
    root = Path(root_path).expanduser().resolve()
    slug = slugify_project_name(root.name)
    memory_home = default_memory_home(env)
    return ResolvedProject(
        project_id=slug,
        project_slug=slug,
        project_name=root.name,
        root_path=root,
        memory_home=memory_home,
        # Doctrine (retro-0060): evidence DB is project-local (matches
        # tools_registry._tool_env). memory_home stays central for the
        # federation registry only.
        memory_db_path=root / ".ai" / ".memory" / "memory.sqlite",
        trinity_home=default_trinity_home(env),
        source=source,
        registered=False,
        binding_path=None,
        registry_path=None,
    )


def _git_root(cwd: Path) -> Optional[Path]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    return Path(out).resolve() if out else None


def _mark_used_best_effort(registry: ProjectRegistry, project_slug: str) -> None:
    try:
        registry.mark_used(project_slug)
    except Exception:
        pass
