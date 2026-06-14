from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .project_slug import collision_safe_slug, slugify_project_name, stable_project_suffix


REGISTRY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    project_slug: str
    project_name: str
    root_path: Path
    binding_path: Path
    memory_home: Path
    memory_db_path: Path
    trinity_version: str
    status: str
    created_at: str
    last_used_at: str


def default_trinity_home(env: Optional[Dict[str, str]] = None) -> Path:
    e = os.environ if env is None else env
    raw = e.get("TRINITY_HOME")
    if raw:
        return Path(raw).expanduser().resolve()
    # Runtime State Convention: honour an operator-declared runtime root
    # (.ai/runtime.yaml) before falling back to the checkout location.
    runtime_root = _declared_runtime_root(e)
    if runtime_root is not None:
        return runtime_root / ".trinity"
    return _default_workspace_root() / ".trinity"


def default_memory_home(env: Optional[Dict[str, str]] = None) -> Path:
    e = os.environ if env is None else env
    raw = e.get("MEMORY_HOME") or e.get("TRINITY_MEMORY_HOME")
    if raw:
        return Path(raw).expanduser().resolve()
    runtime_root = _declared_runtime_root(e)
    if runtime_root is not None:
        return runtime_root / ".memory"
    return _default_workspace_root() / ".memory"


def _declared_runtime_root(env: Dict[str, str]) -> Optional[Path]:
    """Operator-declared runtime root via .ai/runtime.yaml (non-strict).

    Returns None when nothing is declared so the legacy workspace fallback
    still applies (keeps existing behaviour unbroken). TRINITY_HOME env is
    intentionally NOT consulted here — the callers above already handle their
    own env keys with legacy semantics.
    """
    from .runtime_home import resolve_runtime_home

    env_without_trinity_home = {k: v for k, v in env.items() if k != "TRINITY_HOME"}
    return resolve_runtime_home(env=env_without_trinity_home, strict=False)


def _default_workspace_root() -> Path:
    """Default central home root: the Trinity checkout itself.

    In this repo layout:
      <user-home>/Downloads/yai_project/trinity_v2/.ai/cli/core/project_registry.py

    the default central homes should live in:
      <user-home>/Downloads/yai_project/trinity_v2/.trinity
      <user-home>/Downloads/yai_project/trinity_v2/.memory

    Environment variables still override this for installed/global setups.
    """
    here = Path(__file__).resolve()
    try:
        return here.parents[3]
    except IndexError:
        return Path.cwd().resolve()


def registry_path_for(trinity_home: Path) -> Path:
    return Path(trinity_home).expanduser().resolve() / "registry.sqlite"


def touch_memory_db(path: Path) -> None:
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA user_version=1")
        con.commit()
    finally:
        con.close()


class ProjectRegistry:
    def __init__(self, path: Path, create: bool = True):
        self.path = Path(path).expanduser().resolve()
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._init_schema()

    @classmethod
    def default(cls, env: Optional[Dict[str, str]] = None) -> "ProjectRegistry":
        return cls(registry_path_for(default_trinity_home(env)))

    @classmethod
    def existing_default(
        cls, env: Optional[Dict[str, str]] = None
    ) -> Optional["ProjectRegistry"]:
        path = registry_path_for(default_trinity_home(env))
        if not path.exists():
            return None
        return cls(path, create=False)

    def register_project(
        self,
        *,
        project_name: str,
        root_path: Path,
        binding_path: Path,
        memory_home: Path,
        trinity_version: str = "0.1.0",
    ) -> ProjectRecord:
        root = Path(root_path).expanduser().resolve()
        binding = Path(binding_path).expanduser().resolve()
        memory_home = Path(memory_home).expanduser().resolve()
        existing_root = self.find_by_root(root)
        if existing_root:
            slug = existing_root.project_slug
            project_id = existing_root.project_id
            created_at = existing_root.created_at
        else:
            base_slug = slugify_project_name(project_name)
            slug = self._allocate_slug(base_slug, root)
            project_id = slug
            created_at = _utc_now()

        # Doctrine (retro-0060): evidence DB is project-local (matches
        # tools_registry._tool_env); central memory keeps only the
        # federation registry, never per-project sqlite files.
        memory_db_path = root / ".ai" / ".memory" / "memory.sqlite"
        now = _utc_now()
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO projects (
                    project_id, project_slug, project_name, root_path,
                    binding_path, memory_home, memory_db_path,
                    trinity_version, status, created_at, last_used_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(root_path) DO UPDATE SET
                    project_name=excluded.project_name,
                    binding_path=excluded.binding_path,
                    memory_home=excluded.memory_home,
                    memory_db_path=excluded.memory_db_path,
                    trinity_version=excluded.trinity_version,
                    status='active',
                    last_used_at=excluded.last_used_at
                """,
                (
                    project_id,
                    slug,
                    project_name,
                    str(root),
                    str(binding),
                    str(memory_home),
                    str(memory_db_path),
                    trinity_version,
                    "active",
                    created_at,
                    now,
                ),
            )
            con.commit()
        return self.get_by_slug(slug)  # type: ignore[return-value]

    def list_projects(self) -> List[ProjectRecord]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT * FROM projects ORDER BY project_slug ASC"
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def find_by_root(self, root_path: Path) -> Optional[ProjectRecord]:
        root = str(Path(root_path).expanduser().resolve())
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM projects WHERE root_path = ?", (root,)
            ).fetchone()
        return _record_from_row(row) if row else None

    def get_by_slug(self, slug: str) -> Optional[ProjectRecord]:
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM projects WHERE project_slug = ? OR project_id = ?",
                (slug, slug),
            ).fetchone()
        return _record_from_row(row) if row else None

    def lookup(self, ref: str) -> List[ProjectRecord]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT * FROM projects
                WHERE project_slug = ?
                   OR project_id = ?
                   OR project_name = ?
                ORDER BY project_slug ASC
                """,
                (ref, ref, ref),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def match_root(self, cwd: Path) -> List[ProjectRecord]:
        cwd = Path(cwd).expanduser().resolve()
        candidates: List[ProjectRecord] = []
        for record in self.list_projects():
            if _is_relative_to(cwd, record.root_path):
                candidates.append(record)
        if not candidates:
            return []
        max_depth = max(len(r.root_path.parts) for r in candidates)
        return [r for r in candidates if len(r.root_path.parts) == max_depth]

    def mark_used(self, project_slug: str) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE projects SET last_used_at = ? WHERE project_slug = ?",
                (_utc_now(), project_slug),
            )
            con.commit()

    def _allocate_slug(self, base_slug: str, root_path: Path) -> str:
        existing = self.get_by_slug(base_slug)
        if not existing:
            return base_slug
        if existing.root_path == Path(root_path).expanduser().resolve():
            return base_slug
        candidate = collision_safe_slug(base_slug, root_path)
        if not self.get_by_slug(candidate):
            return candidate
        suffix = stable_project_suffix(root_path)
        for size in range(7, 41):
            candidate = f"{base_slug}__{suffix[:size]}"
            if not self.get_by_slug(candidate):
                return candidate
        raise RuntimeError(f"could not allocate collision-safe slug for {base_slug}")

    def _init_schema(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT NOT NULL,
                    project_slug TEXT NOT NULL UNIQUE,
                    project_name TEXT NOT NULL,
                    root_path TEXT NOT NULL UNIQUE,
                    binding_path TEXT NOT NULL,
                    memory_home TEXT NOT NULL,
                    memory_db_path TEXT NOT NULL,
                    trinity_version TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    last_used_at TEXT NOT NULL
                )
                """
            )
            con.execute(f"PRAGMA user_version={REGISTRY_SCHEMA_VERSION}")
            con.commit()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path))
        con.row_factory = sqlite3.Row
        return con


def _record_from_row(row: sqlite3.Row) -> ProjectRecord:
    return ProjectRecord(
        project_id=row["project_id"],
        project_slug=row["project_slug"],
        project_name=row["project_name"],
        root_path=Path(row["root_path"]),
        binding_path=Path(row["binding_path"]),
        memory_home=Path(row["memory_home"]),
        memory_db_path=Path(row["memory_db_path"]),
        trinity_version=row["trinity_version"],
        status=row["status"],
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
