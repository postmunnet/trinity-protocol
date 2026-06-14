"""Phase 8 — shim adapter renderer tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.shim_render import (
    SHORT_CODES,
    VENDORS,
    load_all_shims,
    load_shim,
    render_all,
    render_one,
)


REPO_ROOT = Path.cwd()


def test_short_codes_canonical_set():
    # Full ritual surface since 2026-06-10 (sss 05-11, ddd 06-10 shims).
    assert SHORT_CODES == ["lll", "sss", "vvv", "nnn", "gogogo", "ddd", "rrr"]


def test_vendors_canonical_set():
    assert set(VENDORS) == {"claude-code", "cursor", "agents", "warp"}


def test_load_shim_reads_frontmatter():
    spec = load_shim(REPO_ROOT / ".ai" / "shims", "lll")
    assert spec.code == "lll"
    assert "snapshot" in spec.purpose.lower() or spec.purpose
    assert spec.body  # non-empty body


def test_load_all_shims_returns_full_surface():
    specs = load_all_shims(REPO_ROOT / ".ai" / "shims")
    assert len(specs) == 7
    assert {s.code for s in specs} == set(SHORT_CODES)


def test_load_shim_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_shim(tmp_path, "lll")


# ─── per-vendor renderers ───


def _spec(code="lll"):
    return load_shim(REPO_ROOT / ".ai" / "shims", code)


def test_claude_code_renders_invoke_block():
    out = render_one("claude-code", _spec("vvv"))
    assert "ai vvv" in out
    assert "# `vvv`" in out


def test_cursor_renders_mdc_frontmatter():
    out = render_one("cursor", _spec("rrr"))
    # Cursor rules need YAML frontmatter at top
    assert out.startswith("---\n")
    assert "description:" in out
    assert "ai rrr" in out


def test_agents_renders_fragment_with_invoke():
    out = render_one("agents", _spec("gogogo"))
    assert "`gogogo`" in out
    assert "ai gogogo" in out


def test_warp_renders_yaml_workflow():
    out = render_one("warp", _spec("nnn"))
    assert out.startswith("---\n")
    assert "command:" in out
    assert "\"ai nnn\"" in out


def test_render_unknown_vendor_raises():
    with pytest.raises(ValueError):
        render_one("foo", _spec())


# ─── render_all (dry-run + write) ───


def test_render_all_dry_run_returns_paths(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / ".ai" / "shims").mkdir(parents=True)
    # Copy real shim folders for the test
    import shutil
    for code in SHORT_CODES:
        src = REPO_ROOT / ".ai" / "shims" / code
        dst = proj / ".ai" / "shims" / code
        shutil.copytree(src, dst)

    out = render_all(proj, "claude-code", dry_run=True)
    assert len(out) == 7
    for code in SHORT_CODES:
        assert f".claude/commands/{code}.md" in out
    # Dry-run: nothing written
    assert not (proj / ".claude").exists()


def test_render_all_writes_files(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / ".ai" / "shims").mkdir(parents=True)
    import shutil
    for code in SHORT_CODES:
        src = REPO_ROOT / ".ai" / "shims" / code
        dst = proj / ".ai" / "shims" / code
        shutil.copytree(src, dst)
    out = render_all(proj, "cursor", dry_run=False)
    assert len(out) == 7
    for code in SHORT_CODES:
        p = proj / ".cursor" / "rules" / f"{code}.mdc"
        assert p.exists()
        body = p.read_text(encoding="utf-8")
        assert f"ai {code}" in body


def test_agents_render_produces_single_fragment_file(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / ".ai" / "shims").mkdir(parents=True)
    import shutil
    for code in SHORT_CODES:
        src = REPO_ROOT / ".ai" / "shims" / code
        dst = proj / ".ai" / "shims" / code
        shutil.copytree(src, dst)
    out = render_all(proj, "agents", dry_run=False)
    # AGENTS_FRAGMENT.md is a single concatenated file (not per-code)
    assert len(out) == 1
    rel = list(out.keys())[0]
    assert rel.endswith("AGENTS_FRAGMENT.md")
    body = (proj / rel).read_text(encoding="utf-8")
    for code in SHORT_CODES:
        assert f"`{code}`" in body
