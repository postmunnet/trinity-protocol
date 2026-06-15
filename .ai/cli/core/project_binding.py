from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


PROJECT_BINDING_REL = Path(".trinity") / "project.yaml"


@dataclass(frozen=True)
class ProjectBinding:
    project_id: str
    project_slug: str
    project_name: str
    root_path: Path
    trinity_home: Path
    memory_home: Path
    memory_db_path: Path
    binding_path: Path
    trinity_version: str = "0.1.0"

    @property
    def root_str(self) -> str:
        return str(self.root_path)


def binding_path_for(root_path: Path) -> Path:
    return Path(root_path) / PROJECT_BINDING_REL


def find_binding_path(start: Path) -> Optional[Path]:
    """Walk upward from start to find .trinity/project.yaml."""
    cur = Path(start).expanduser().resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in [cur, *cur.parents]:
        path = binding_path_for(candidate)
        if path.exists():
            return path
    return None


def read_project_binding(path: Path) -> ProjectBinding:
    path = Path(path).expanduser().resolve()
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return _binding_from_dict(data, path)


def write_project_binding(binding: ProjectBinding, force: bool = False) -> None:
    path = binding.binding_path
    if path.exists() and not force:
        raise FileExistsError(f"project binding already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project_id": binding.project_id,
        "project_slug": binding.project_slug,
        "project_name": binding.project_name,
        "root_path": str(binding.root_path),
        "trinity": {
            "home": str(binding.trinity_home),
            "version": binding.trinity_version,
        },
        "memory": {
            "home": str(binding.memory_home),
            "db": str(binding.memory_db_path),
        },
        "paths": {
            "sessions": ".trinity/sessions",
            "artifacts": ".trinity/artifacts",
            "retros": ".trinity/retros",
            "overrides": ".trinity/local-overrides.yaml",
        },
    }
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)


def ensure_project_dirs(root_path: Path) -> None:
    base = Path(root_path) / ".trinity"
    for name in ("sessions", "artifacts", "retros"):
        (base / name).mkdir(parents=True, exist_ok=True)


def _binding_from_dict(data: Dict[str, Any], binding_path: Path) -> ProjectBinding:
    root_path = Path(
        data.get("root_path") or binding_path.parent.parent
    ).expanduser().resolve()
    trinity = data.get("trinity") or {}
    memory = data.get("memory") or {}
    trinity_home = Path(trinity.get("home") or "~/.trinity").expanduser()
    memory_home = Path(memory.get("home") or "~/.memory").expanduser()
    project_slug = data.get("project_slug") or data.get("project_id")
    if not project_slug:
        raise ValueError(f"project binding missing project_slug: {binding_path}")
    # Doctrine (retro-0060): the evidence DB is project-local; central memory
    # holds only the federation registry. Default must match what the kernel
    # actually injects via tools_registry._tool_env, or lll/status display a
    # path no tool ever writes (the example_client empty-central-DB incident).
    memory_db = Path(
        memory.get("db") or (root_path / ".ai" / ".memory" / "memory.sqlite")
    )
    return ProjectBinding(
        project_id=str(data.get("project_id") or project_slug),
        project_slug=str(project_slug),
        project_name=str(data.get("project_name") or data.get("name") or project_slug),
        root_path=root_path,
        trinity_home=trinity_home.expanduser(),
        memory_home=memory_home.expanduser(),
        memory_db_path=memory_db.expanduser(),
        binding_path=binding_path,
        trinity_version=str(trinity.get("version") or data.get("trinity_version") or "0.1.0"),
    )
