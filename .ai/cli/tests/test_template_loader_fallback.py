"""Thin-client fallback for TemplateLoader (retro: sss broken on thin projects).

A thin-linked project strips its vendored `.ai/templates`. Before the fix,
`from_ssot` resolved only the project-local templates dir; when absent,
`copy_structure`'s `rglob` silently yielded nothing, THINK/ was never created,
and the session scaffolder crashed writing THINK/CONSENSUS.md. The fix adds a
kernel-source fallback + a fail-loud guard. Same pattern as retro-0055.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

from cli.core.template_loader import TemplateLoader

KERNEL_TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


def _fake_ssot(ai_root: Path, project_root: Path):
    """Minimal stand-in matching the attributes from_ssot reads."""
    return SimpleNamespace(
        raw_config={"paths": {"templates": "${ai_root}/templates"}},
        ai_root=ai_root,
        project_root=project_root,
    )


def test_from_ssot_falls_back_to_kernel_templates_when_project_local_missing(tmp_path):
    # Simulate a thin client: ai_root exists but has NO templates/ dir.
    thin_ai_root = tmp_path / "thinproj" / ".ai"
    thin_ai_root.mkdir(parents=True)
    assert not (thin_ai_root / "templates").exists()

    loader = TemplateLoader.from_ssot(_fake_ssot(thin_ai_root, thin_ai_root.parent))

    assert loader.templates_root == KERNEL_TEMPLATES
    assert loader.templates_root.is_dir()


def test_from_ssot_uses_project_local_when_present(tmp_path):
    # A fat/dev project with its own templates/ keeps using it (no fallback).
    ai_root = tmp_path / "fatproj" / ".ai"
    (ai_root / "templates").mkdir(parents=True)

    loader = TemplateLoader.from_ssot(_fake_ssot(ai_root, ai_root.parent))

    assert loader.templates_root == ai_root / "templates"


def test_copy_structure_raises_loud_on_missing_src(tmp_path):
    # Both project-local AND a bogus templates_root -> fail loud, not silent.
    loader = TemplateLoader(tmp_path / "does_not_exist")
    with pytest.raises(FileNotFoundError):
        loader.copy_structure("session", tmp_path / "dst")


def test_kernel_has_session_template():
    # Guards the fallback target: the kernel must ship a session template.
    assert (KERNEL_TEMPLATES / "session").is_dir()
