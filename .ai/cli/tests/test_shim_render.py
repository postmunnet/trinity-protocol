"""Phase 8 — shim adapter renderer tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.shim_render import (
    SHORT_CODES,
    VENDORS,
    ShimSpec,
    _extract_claude_operational,
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


# ─── R30 layered-rendering doctrine (supersedes pre-R30 "no commentary") ───
# Operator decision 2026-06-12: kernel artifacts shown verbatim, but the agent
# MAY add surrounding orientation per the channel template. The renderer text
# must not re-emit the absolutist pre-R30 framing on `ai shim render`.

_PRE_R30_BANNED = (
    "must not add commentary",
    "do not narrate",
    "return its output verbatim",
    "return the kernel response verbatim",
    "return the output verbatim",
    "render the kernel output as-is",
)


@pytest.mark.parametrize("vendor", ["claude-code", "cursor", "agents"])
def test_renderers_are_r30_layered_not_absolutist(vendor):
    out = render_one(vendor, _spec("vvv")).lower()
    # pre-R30 absolutist phrasing must be gone
    for banned in _PRE_R30_BANNED:
        assert banned not in out, f"{vendor} still emits pre-R30 phrase: {banned!r}"
    # R30 doctrine must be present: artifacts verbatim, orientation allowed,
    # verdict never reinterpreted
    assert "verbatim" in out          # artifacts still shown verbatim
    assert "orientation" in out       # surrounding orientation now allowed
    assert "verdict" in out           # must never alter/reinterpret a verdict


def test_claude_adapter_points_at_channel_template():
    # R30: the claude adapter should hint at the per-channel template path so
    # the agent knows where the surrounding-text rules live.
    out = render_one("claude-code", _spec("gogogo"))
    assert "templates/" in out


def test_claude_adapter_is_rich_r30_two_layer():
    # B-lite: the generator (not a hand-edited surface file) is the source of
    # truth for the richer Claude two-layer R30 block. Re-rendering Claude must
    # be non-regressive vs the previously hand-authored .claude/commands/*.md.
    out = render_one("claude-code", _spec("lll"))
    low = out.lower()
    assert "render in two layers" in low
    assert "operator decision 2026-06-12" in low
    assert "kernel artifacts are verbatim" in low
    assert "around the artifact" in low
    # template path is parametrised per code (improves on the generic <ritual>)
    assert ".ai/shims/lll/templates/<channel>.md" in out


# ─── P3 SHIPPED (Fork A, 2026-06-18) — structured per-ritual Claude content ───
# P3 closed the B-lite deferral: vvv/nnn/gogogo now generate their per-ritual
# operational content from a delimited `trinity:claude-section:operational`
# region in each SHIM.md body. The pending set is now EMPTY (7/7 generated).
# Ownership manifest: docs/dev/shim-surface-ownership.md.
CLAUDE_MANUAL_PENDING_P3 = set()


def test_pending_p3_set_is_empty_p3_shipped():
    # 7/7 Claude surfaces are generated; no ritual remains hand-maintained.
    assert CLAUDE_MANUAL_PENDING_P3 == set()


def test_pending_p3_ownership_doc_reflects_completion():
    doc = REPO_ROOT / "docs" / "dev" / "shim-surface-ownership.md"
    assert doc.exists(), "ownership manifest missing — surface ownership must stay documented"
    text = doc.read_text(encoding="utf-8").lower()
    assert "7/7" in text  # all Claude surfaces generated


def test_p3_per_ritual_operational_now_generated():
    """The flipped tripwire: the generator now DOES emit each ritual's per-ritual
    operational content (the inverse of the B-lite tripwire that asserted absence)."""
    vvv = render_one("claude-code", _spec("vvv")).lower()
    assert "--show" in vvv
    assert "pre-flight" in vvv
    assert "why not bare" in vvv
    nnn = render_one("claude-code", _spec("nnn")).lower()
    assert "plan-envelope" in nnn
    gogogo = render_one("claude-code", _spec("gogogo")).lower()
    assert "plan.json" in gogogo


# ─── P3 extractor contract: present / missing / duplicate / unrelated-body ───

_START = "<!-- trinity:claude-section:operational:start -->"
_END = "<!-- trinity:claude-section:operational:end -->"


def test_extract_present_returns_inner_only():
    body = f"intro\n\n{_START}\nOPERATIONAL HERE\n{_END}\n\noutro"
    assert _extract_claude_operational(body) == "OPERATIONAL HERE"


def test_extract_missing_returns_none():
    assert _extract_claude_operational("just a normal SHIM.md body, no section") is None


def test_extract_duplicate_section_raises():
    body = f"{_START}\nA\n{_END}\n{_START}\nB\n{_END}"
    with pytest.raises(ValueError):
        _extract_claude_operational(body)


def test_extract_end_before_start_raises():
    body = f"{_END}\nbroken\n{_START}"
    with pytest.raises(ValueError):
        _extract_claude_operational(body)


def test_unrelated_body_text_is_not_rendered():
    # Proves this is structured extraction, NOT raw body injection: text in the
    # SHIM.md body OUTSIDE the delimited section never reaches the adapter.
    spec = ShimSpec(
        code="vvv", purpose="Verify", status="", last_updated="",
        body=(
            f"SENTINEL_OUTSIDE_BODY should never render\n\n"
            f"{_START}\nthe operational content\n{_END}\n\n"
            f"ANOTHER_SENTINEL also outside"
        ),
        claude_operational=_extract_claude_operational(
            f"SENTINEL_OUTSIDE_BODY should never render\n\n"
            f"{_START}\nthe operational content\n{_END}\n\n"
            f"ANOTHER_SENTINEL also outside"
        ),
    )
    out = render_one("claude-code", spec)
    assert "the operational content" in out
    assert "SENTINEL_OUTSIDE_BODY" not in out
    assert "ANOTHER_SENTINEL" not in out
