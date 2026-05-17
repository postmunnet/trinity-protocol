"""R30 Phase 1 + Phase 2 + R33 — per-channel rendering templates.

Phase 1 shipped `lll` templates + adapter wire (R33).
Phase 2 extends to vvv/nnn/gogogo/rrr.

Verifies all 5 rituals × 2 channels (desktop, mobile) have the canonical
template files + content invariants + the adapters reference them.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# test_shim_templates.py -> tests/ -> cli/ -> .ai/ -> trinity_v2/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SHIMS_DIR = Path(__file__).resolve().parent.parent.parent / "shims"
ADAPTERS = [
    PROJECT_ROOT / "CLAUDE.md",
    PROJECT_ROOT / "AGENTS.md",
]

ALL_RITUALS = ["lll", "vvv", "nnn", "gogogo", "rrr", "ddd"]


def _template_dir(ritual: str) -> Path:
    return SHIMS_DIR / ritual / "templates"


@pytest.mark.parametrize("ritual", ALL_RITUALS)
def test_templates_present(ritual):
    """A_TEMPLATES_PRESENT (per ritual) — desktop + mobile + README exist & non-empty."""
    template_dir = _template_dir(ritual)
    for name in ("desktop.md", "mobile.md", "README.md"):
        path = template_dir / name
        assert path.exists(), f"missing template: {path}"
        body = path.read_text(encoding="utf-8")
        assert len(body) > 200, f"{ritual}/{name} suspiciously short ({len(body)} chars)"


@pytest.mark.parametrize("ritual", ALL_RITUALS)
def test_template_content_invariants(ritual):
    """A_TEMPLATE_CONTENT_INVARIANTS (per ritual) — mobile forbids box-drawing + ASCII tables."""
    mobile = (_template_dir(ritual) / "mobile.md").read_text(encoding="utf-8").lower()
    assert ("no box-drawing" in mobile) or ("no box drawing" in mobile), (
        f"{ritual}/mobile.md must explicitly forbid box-drawing chars"
    )
    assert "no ascii tables" in mobile, (
        f"{ritual}/mobile.md must explicitly forbid ASCII tables"
    )


def test_lll_desktop_endorses_tables():
    """Sanity for the original Phase 1 contract — desktop endorses tables + box-drawing."""
    desktop = (_template_dir("lll") / "desktop.md").read_text(encoding="utf-8").lower()
    assert "table" in desktop, "lll/desktop.md must mention 'table'"
    assert ("box-drawing" in desktop) or ("box drawing" in desktop), (
        "lll/desktop.md must mention box-drawing chars"
    )


def test_adapter_references_templates():
    """A_ADAPTER_REFERENCES_TEMPLATES — repo-local entrypoint adapters
    reference the template directory + the R30/R33 marker block."""
    for path in ADAPTERS:
        assert path.exists(), f"missing adapter: {path}"
        body = path.read_text(encoding="utf-8")
        assert "Per-channel ritual rendering" in body, (
            f"{path.name} missing R30/R33 section header"
        )
        assert ".ai/shims/<ritual>/templates/<channel>.md" in body, (
            f"{path.name} missing canonical template path reference"
        )
        assert "BEGIN R30/R33 per-channel rendering" in body, (
            f"{path.name} missing R30/R33 marker"
        )
