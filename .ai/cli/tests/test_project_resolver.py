from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.project_binding import (
    ProjectBinding,
    binding_path_for,
    write_project_binding,
)
from cli.core.project_registry import ProjectRegistry
from cli.core.project_resolver import ProjectResolutionError, resolve_current_project


def _register(
    registry: ProjectRegistry,
    root: Path,
    name: str,
    memory_home: Path,
):
    root.mkdir(parents=True, exist_ok=True)
    return registry.register_project(
        project_name=name,
        root_path=root,
        binding_path=binding_path_for(root),
        memory_home=memory_home,
    )


def test_resolver_prefers_explicit_project_over_local_binding(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite")
    memory_home = tmp_path / "memory"
    root_a = tmp_path / "example_project"
    root_b = tmp_path / "trinity_v2"
    rec_a = _register(registry, root_a, "Example Project", memory_home)
    rec_b = _register(registry, root_b, "Trinity V2", memory_home)
    binding = ProjectBinding(
        project_id=rec_b.project_id,
        project_slug=rec_b.project_slug,
        project_name=rec_b.project_name,
        root_path=rec_b.root_path,
        trinity_home=tmp_path / "trinity",
        memory_home=rec_b.memory_home,
        memory_db_path=rec_b.memory_db_path,
        binding_path=rec_b.binding_path,
    )
    write_project_binding(binding)

    resolved = resolve_current_project(
        start_path=root_b,
        project_ref=rec_a.project_slug,
        registry=registry,
    )

    assert resolved.project_slug == rec_a.project_slug
    assert resolved.source == "explicit"
    assert resolved.memory_db_path == rec_a.memory_db_path


def test_resolver_uses_environment_before_binding(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite")
    memory_home = tmp_path / "memory"
    rec_a = _register(registry, tmp_path / "example_project", "Example Project", memory_home)
    rec_b = _register(registry, tmp_path / "other", "Other", memory_home)
    write_project_binding(ProjectBinding(
        project_id=rec_b.project_id,
        project_slug=rec_b.project_slug,
        project_name=rec_b.project_name,
        root_path=rec_b.root_path,
        trinity_home=tmp_path / "trinity",
        memory_home=rec_b.memory_home,
        memory_db_path=rec_b.memory_db_path,
        binding_path=rec_b.binding_path,
    ))

    resolved = resolve_current_project(
        start_path=rec_b.root_path,
        env={"TRINITY_PROJECT": rec_a.project_slug},
        registry=registry,
    )

    assert resolved.project_slug == rec_a.project_slug
    assert resolved.source == "environment"


def test_resolver_uses_project_yaml_binding_from_subdirectory(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite")
    rec = _register(registry, tmp_path / "example_project", "Example Project", tmp_path / "memory")
    write_project_binding(ProjectBinding(
        project_id=rec.project_id,
        project_slug=rec.project_slug,
        project_name=rec.project_name,
        root_path=rec.root_path,
        trinity_home=tmp_path / "trinity",
        memory_home=rec.memory_home,
        memory_db_path=rec.memory_db_path,
        binding_path=rec.binding_path,
    ))
    nested = rec.root_path / "wp-content" / "themes"
    nested.mkdir(parents=True)

    resolved = resolve_current_project(start_path=nested, registry=registry)

    assert resolved.project_slug == "example_project"
    assert resolved.source == "binding"
    assert resolved.registered is True


def test_resolver_matches_registry_root_without_binding(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite")
    rec = _register(registry, tmp_path / "example_project", "Example Project", tmp_path / "memory")
    nested = rec.root_path / "wp-content"
    nested.mkdir()

    resolved = resolve_current_project(start_path=nested, registry=registry)

    assert resolved.project_slug == rec.project_slug
    assert resolved.source == "registry"
    assert resolved.memory_db_path == rec.memory_db_path


def test_resolver_fails_clearly_when_reference_is_ambiguous(tmp_path: Path) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite")
    _register(registry, tmp_path / "one", "Project A", tmp_path / "memory")
    _register(registry, tmp_path / "two", "Project A", tmp_path / "memory")

    with pytest.raises(ProjectResolutionError, match="Ambiguous project reference"):
        resolve_current_project(
            start_path=tmp_path,
            env={"TRINITY_PROJECT": "Project A"},
            registry=registry,
        )


def test_resolver_fallback_uses_project_local_db_path(tmp_path: Path) -> None:
    project = tmp_path / "loose-project"
    project.mkdir()
    memory_home = tmp_path / "memory-home"

    resolved = resolve_current_project(
        start_path=project,
        env={"MEMORY_HOME": str(memory_home)},
        registry=None,
    )

    assert resolved.source == "cwd"
    assert resolved.registered is False
    # Doctrine (retro-0060): evidence DB is project-local even for
    # unregistered cwd-fallback projects; memory_home stays the
    # federation-registry home only.
    assert resolved.memory_db_path == project / ".ai" / ".memory" / "memory.sqlite"


def test_resolver_can_require_registered_project(tmp_path: Path) -> None:
    project = tmp_path / "loose-project"
    project.mkdir()

    with pytest.raises(ProjectResolutionError, match="No registered project found"):
        resolve_current_project(
            start_path=project,
            registry=None,
            allow_fallback=False,
        )


def test_resolver_does_not_fail_when_mark_used_is_readonly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = ProjectRegistry(tmp_path / "registry.sqlite")
    rec = _register(registry, tmp_path / "example_project", "Example Project", tmp_path / "memory")
    write_project_binding(ProjectBinding(
        project_id=rec.project_id,
        project_slug=rec.project_slug,
        project_name=rec.project_name,
        root_path=rec.root_path,
        trinity_home=tmp_path / "trinity",
        memory_home=rec.memory_home,
        memory_db_path=rec.memory_db_path,
        binding_path=rec.binding_path,
    ))

    def readonly_mark_used(project_slug: str) -> None:
        raise OSError("readonly database")

    monkeypatch.setattr(registry, "mark_used", readonly_mark_used)

    resolved = resolve_current_project(start_path=rec.root_path, registry=registry)

    assert resolved.project_slug == "example_project"
    assert resolved.source == "binding"
