from __future__ import annotations

from pathlib import Path

from cli.core.project_binding import binding_path_for
from cli.core import project_registry as registry_mod
from cli.core.project_registry import (
    ProjectRegistry,
    default_memory_home,
    default_trinity_home,
    touch_memory_db,
)
from cli.core.project_slug import slugify_project_name


def test_slugify_project_name_is_deterministic() -> None:
    assert slugify_project_name("TRINITY_LEGACY") == "trinity_legacy"
    assert slugify_project_name("Project A") == "project_a"
    assert slugify_project_name("example_project-prod") == "example_project_prod"


def test_registry_allocates_collision_safe_project_slugs(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite")
    memory_home = tmp_path / "memory"
    root_a = tmp_path / "Project A"
    root_b = tmp_path / "project-a"
    root_a.mkdir()
    root_b.mkdir()

    rec_a = registry.register_project(
        project_name="Project A",
        root_path=root_a,
        binding_path=binding_path_for(root_a),
        memory_home=memory_home,
    )
    rec_b = registry.register_project(
        project_name="Project A",
        root_path=root_b,
        binding_path=binding_path_for(root_b),
        memory_home=memory_home,
    )

    assert rec_a.project_slug == "project_a"
    assert rec_b.project_slug.startswith("project_a__")
    assert rec_a.memory_db_path == memory_home / "db" / "project_a.db"
    assert rec_b.memory_db_path == memory_home / "db" / f"{rec_b.project_slug}.db"
    assert registry.lookup("Project A") == [rec_a, rec_b]


def test_touch_memory_db_creates_sqlite_file(tmp_path: Path) -> None:
    db_path = tmp_path / "memory" / "db" / "example_project.db"

    touch_memory_db(db_path)

    assert db_path.exists()


def test_default_homes_live_inside_trinity_checkout(tmp_path: Path, monkeypatch) -> None:
    fake_file = (
        tmp_path
        / "workspace-root"
        / "trinity_v2"
        / ".ai"
        / "cli"
        / "core"
        / "project_registry.py"
    )
    monkeypatch.setattr(registry_mod, "__file__", str(fake_file))

    trinity_root = tmp_path / "workspace-root" / "trinity_v2"
    assert default_trinity_home(env={}) == trinity_root / ".trinity"
    assert default_memory_home(env={}) == trinity_root / ".memory"


def test_default_homes_still_honor_env_overrides(tmp_path: Path) -> None:
    env = {
        "TRINITY_HOME": str(tmp_path / "custom-trinity"),
        "MEMORY_HOME": str(tmp_path / "custom-memory"),
    }

    assert default_trinity_home(env=env) == tmp_path / "custom-trinity"
    assert default_memory_home(env=env) == tmp_path / "custom-memory"
