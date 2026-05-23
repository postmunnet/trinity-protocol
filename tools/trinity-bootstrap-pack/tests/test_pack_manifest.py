"""Manifest unit tests."""

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.pack_manifest import PACK_VERSION, build_manifest, manifest_to_dict


PACK_DIR = Path(__file__).resolve().parent.parent / "pack"


def test_pack_dir_exists() -> None:
    assert PACK_DIR.is_dir()


def test_build_manifest_returns_nonempty() -> None:
    entries = build_manifest(PACK_DIR)
    assert len(entries) > 0
    for e in entries:
        assert len(e.sha256) == 64
        assert e.size >= 0
        assert "/" in e.relpath or e.relpath in {"ssot.yaml"}  # sanity


def test_manifest_to_dict_shape() -> None:
    entries = build_manifest(PACK_DIR)
    body = manifest_to_dict(entries)
    assert body["pack_version"] == PACK_VERSION
    assert body["file_count"] == len(entries)
    assert isinstance(body["files"], list)


def test_pack_contains_required_files() -> None:
    relpaths = {e.relpath for e in build_manifest(PACK_DIR)}
    # Project-customizable files that ship in pack
    assert "templates/CLAUDE.md.template" in relpaths
    assert "ai-docs/SHORT_CODES.md" in relpaths
    assert ".ai/ssot.yaml" in relpaths
    assert ".ai/tools.yaml" in relpaths
    assert ".ai/policies/safety.yaml" in relpaths
    assert ".ai/policies/verifier-rules.yaml" in relpaths


def test_pack_does_not_ship_kernel_canonical_files() -> None:
    """v1.2 — graphs/schemas/shims/templates/checklists come from kernel_wire,
    NOT from the pack. Shipping them in pack would create drift risk.
    """
    relpaths = {e.relpath for e in build_manifest(PACK_DIR)}
    forbidden = [
        ".ai/graphs/standard.yaml",
        ".ai/schemas/.keep",
        ".ai/shims/",
        ".ai/templates/",   # kernel-side templates; pack ships templates/ (CLAUDE.md etc.)
        ".ai/checklists/",
    ]
    for f in forbidden:
        matching = [r for r in relpaths if r.startswith(f.rstrip("/"))]
        assert not matching, f"pack should NOT ship kernel-canonical {f}; found {matching}"
