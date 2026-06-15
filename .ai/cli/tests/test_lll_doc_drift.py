"""lll proactive doc-drift surface (discoverability layer)."""
from __future__ import annotations

from pathlib import Path

from cli.commands.lll import _doc_drift


def _project_with_sibling_drift(tmp: Path, *, real_dirs: int, atlas_claim: int) -> Path:
    sib = tmp / "siblings"
    sib.mkdir()
    for i in range(real_dirs):
        (sib / f"t{i}").mkdir()
    dev = tmp / "dev"
    dev.mkdir()
    # atlas asserts a different source-dir count -> drift
    (dev / "trinity_structure_workflow.html").write_text(f"siblings ×{atlas_claim} source dirs")
    return tmp


def test_doc_drift_none_when_no_sources(tmp_path):
    # empty tree: facts unknown, not drift -> None (no panel)
    assert _doc_drift(tmp_path) is None


def test_doc_drift_surfaces_drift(tmp_path):
    _project_with_sibling_drift(tmp_path, real_dirs=3, atlas_claim=9)
    d = _doc_drift(tmp_path)
    assert d is not None
    assert d["drift_count"] >= 1
    assert "sibling_source_dirs" in d["drifted"]


def test_doc_drift_none_when_aligned(tmp_path):
    _project_with_sibling_drift(tmp_path, real_dirs=4, atlas_claim=4)
    assert _doc_drift(tmp_path) is None  # claim matches truth -> clean -> None


def test_doc_drift_failsoft_bad_path(tmp_path):
    assert _doc_drift(tmp_path / "nope" / "missing") is None
