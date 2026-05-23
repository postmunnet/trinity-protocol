"""Unit tests for kernel_wire."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.kernel_wire import KernelWireError, wire_kernel


def _fake_source(tmp_path: Path) -> Path:
    """Build a minimal trinity_v2-shaped source root."""
    src = tmp_path / "trinity_v2_src"
    (src / ".ai" / "cli").mkdir(parents=True)
    (src / ".ai" / "cli" / "ai").write_text("#!/bin/sh\n", encoding="utf-8")
    (src / ".ai" / "rituals").mkdir()
    (src / ".ai" / "rituals" / "marker.txt").write_text("rituals\n", encoding="utf-8")
    (src / ".ai" / "requirements.txt").write_text("typer\n", encoding="utf-8")
    return src


def test_none_mode_no_writes(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    tgt.mkdir()
    res = wire_kernel(mode="none", source_root=src, target=tgt, dry_run=False, force=False)
    assert res.mode == "none"
    assert res.bindings == []
    assert not (tgt / ".ai" / "cli").exists()


def test_symlink_default(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    tgt.mkdir()
    res = wire_kernel(mode="symlink", source_root=src, target=tgt, dry_run=False, force=False)
    assert res.mode == "symlink"
    cli = tgt / ".ai" / "cli"
    rituals = tgt / ".ai" / "rituals"
    assert cli.is_symlink()
    assert rituals.is_symlink()
    assert cli.resolve() == (src / ".ai" / "cli").resolve()
    # requirements.txt is always copied (not symlinked)
    req = tgt / ".ai" / "requirements.txt"
    assert req.is_file()
    assert not req.is_symlink()


def test_copy_mode_deep_copy(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    tgt.mkdir()
    res = wire_kernel(mode="copy", source_root=src, target=tgt, dry_run=False, force=False)
    assert res.mode == "copy"
    cli = tgt / ".ai" / "cli"
    assert cli.is_dir()
    assert not cli.is_symlink()
    assert (cli / "ai").is_file()


def test_dry_run_no_filesystem_writes(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    tgt.mkdir()
    res = wire_kernel(mode="symlink", source_root=src, target=tgt, dry_run=True, force=False)
    assert res.mode == "symlink"
    assert res.bindings  # plans recorded
    # but nothing on disk
    assert not (tgt / ".ai" / "cli").exists()


def test_submodule_mode_refused_in_v11(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    tgt.mkdir()
    with pytest.raises(KernelWireError) as exc_info:
        wire_kernel(mode="submodule", source_root=src, target=tgt, dry_run=False, force=False)
    assert exc_info.value.exit_code == 30


def test_unknown_mode_refused(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    tgt.mkdir()
    with pytest.raises(KernelWireError):
        wire_kernel(mode="bogus", source_root=src, target=tgt, dry_run=False, force=False)  # type: ignore[arg-type]


def test_existing_target_dir_skipped_without_force(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    (tgt / ".ai" / "cli").mkdir(parents=True)
    (tgt / ".ai" / "cli" / "preexisting").write_text("keep me", encoding="utf-8")
    res = wire_kernel(mode="symlink", source_root=src, target=tgt, dry_run=False, force=False)
    # Preexisting kept
    assert (tgt / ".ai" / "cli" / "preexisting").is_file()
    # Warning emitted
    assert any("skipped" in w for w in res.warnings)


def test_force_overwrites(tmp_path: Path) -> None:
    src = _fake_source(tmp_path)
    tgt = tmp_path / "tgt"
    (tgt / ".ai" / "cli").mkdir(parents=True)
    (tgt / ".ai" / "cli" / "preexisting").write_text("clobber", encoding="utf-8")
    res = wire_kernel(mode="symlink", source_root=src, target=tgt, dry_run=False, force=True)
    # After force, target is now a symlink to source
    assert (tgt / ".ai" / "cli").is_symlink()
    # Preexisting is gone (in target — source doesn't have it)
    assert not (tgt / ".ai" / "cli" / "preexisting").exists()


def test_source_missing_kernel_refused(tmp_path: Path) -> None:
    src = tmp_path / "empty_source"
    src.mkdir()
    tgt = tmp_path / "tgt"
    tgt.mkdir()
    with pytest.raises(KernelWireError) as exc_info:
        wire_kernel(mode="symlink", source_root=src, target=tgt, dry_run=False, force=False)
    assert exc_info.value.exit_code == 40
