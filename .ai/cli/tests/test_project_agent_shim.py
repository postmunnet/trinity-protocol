from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.project_agent_shim import (
    END_MARKER,
    START_MARKER,
    AgentShimError,
    install_agents_md_shim,
    install_project_agent_shims,
    install_project_trinity_wrapper,
)
from cli.core.project_binding import ProjectBinding, binding_path_for


def _binding(root: Path, slug: str = "example_project") -> ProjectBinding:
    return ProjectBinding(
        project_id=slug,
        project_slug=slug,
        project_name=slug,
        root_path=root,
        trinity_home=root.parent / "trinity_v2" / ".trinity",
        memory_home=root.parent / "trinity_v2" / ".memory",
        memory_db_path=root.parent / "trinity_v2" / ".memory" / "db" / f"{slug}.db",
        binding_path=binding_path_for(root),
    )


def test_install_agents_md_shim_creates_file(tmp_path: Path) -> None:
    root = tmp_path / "example_project"
    root.mkdir()

    path = install_agents_md_shim(root, _binding(root))

    text = path.read_text(encoding="utf-8")
    assert path == root / "AGENTS.md"
    assert START_MARKER in text
    assert END_MARKER in text
    assert "project: `example_project`" in text
    assert "TRINITY=" in text
    assert "$TRINITY doctor commands" in text
    assert "$TRINITY sss \"<task>\"" in text
    assert "$TRINITY project doctor" in text
    assert "trinity lll` means `$TRINITY lll" in text
    assert "Do not replace Trinity commands with handmade shell probes" in text
    assert "trinity lll` means `./trinity lll" in text
    assert "first and\nonly shell command" in text
    assert "Relay the CLI output directly" in text
    assert "running `ls .ai/sessions`, `git status`, or `git log` by hand" in text
    assert "piping `./trinity lll` through `head`" in text


def test_install_agents_md_shim_prepends_without_touching_existing_text(tmp_path: Path) -> None:
    root = tmp_path / "example_project"
    root.mkdir()
    agents = root / "AGENTS.md"
    agents.write_text("# Existing\n\n- Keep this.\n", encoding="utf-8")

    install_agents_md_shim(root, _binding(root))

    text = agents.read_text(encoding="utf-8")
    assert text.startswith(START_MARKER)
    assert "# Existing\n\n- Keep this." in text
    assert text.count(START_MARKER) == 1
    assert text.count(END_MARKER) == 1


def test_install_agents_md_shim_replaces_existing_managed_block(tmp_path: Path) -> None:
    root = tmp_path / "example_project"
    root.mkdir()
    agents = root / "AGENTS.md"
    agents.write_text(
        f"# Existing\n\n{START_MARKER}\nold block\n{END_MARKER}\n",
        encoding="utf-8",
    )

    install_agents_md_shim(root, _binding(root, slug="example_project_prod"))

    text = agents.read_text(encoding="utf-8")
    assert text.startswith(START_MARKER)
    assert "# Existing" in text
    assert "old block" not in text
    assert "project: `example_project_prod`" in text
    assert text.count(START_MARKER) == 1


def test_install_agents_md_shim_rejects_broken_marker(tmp_path: Path) -> None:
    root = tmp_path / "example_project"
    root.mkdir()
    (root / "AGENTS.md").write_text(
        f"# Existing\n\n{START_MARKER}\nmissing end\n",
        encoding="utf-8",
    )

    with pytest.raises(AgentShimError, match="broken Trinity AGENTS.md"):
        install_agents_md_shim(root, _binding(root))


def test_install_project_trinity_wrapper(tmp_path: Path) -> None:
    root = tmp_path / "example_project"
    root.mkdir()

    path = install_project_trinity_wrapper(root, _binding(root))

    text = path.read_text(encoding="utf-8")
    assert path == root / "trinity"
    assert "exec " in text
    assert "/trinity_v2/.ai/cli/ai" in text
    assert path.stat().st_mode & 0o111


def test_install_project_agent_shims_updates_existing_vendor_files(tmp_path: Path) -> None:
    root = tmp_path / "example_project"
    root.mkdir()
    (root / "CLAUDE.md").write_text("# Claude Existing\n", encoding="utf-8")

    paths = install_project_agent_shims(root, _binding(root))

    assert root / "AGENTS.md" in paths
    assert root / "CLAUDE.md" in paths
    assert not (root / "GEMINI.md").exists()

    claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude.startswith(START_MARKER)
    assert "# Claude Existing" in claude
    assert "trinity lll` means `./trinity lll" in claude
