from __future__ import annotations

from pathlib import Path

from cli.core.project_binding import (
    ProjectBinding,
    binding_path_for,
    find_binding_path,
    read_project_binding,
    write_project_binding,
)


def test_project_binding_round_trip_and_upward_discovery(tmp_path: Path) -> None:
    root = tmp_path / "example_project"
    root.mkdir()
    binding_path = binding_path_for(root)
    binding = ProjectBinding(
        project_id="example_project",
        project_slug="example_project",
        project_name="Example Project Production",
        root_path=root.resolve(),
        trinity_home=tmp_path / "trinity",
        memory_home=tmp_path / "memory",
        memory_db_path=tmp_path / "memory" / "db" / "example_project.db",
        binding_path=binding_path,
        trinity_version="0.1.0",
    )

    write_project_binding(binding)

    loaded = read_project_binding(binding_path)
    assert loaded.project_id == "example_project"
    assert loaded.project_slug == "example_project"
    assert loaded.project_name == "Example Project Production"
    assert loaded.memory_db_path == tmp_path / "memory" / "db" / "example_project.db"

    nested = root / "wp-content" / "plugins"
    nested.mkdir(parents=True)
    assert find_binding_path(nested) == binding_path.resolve()
