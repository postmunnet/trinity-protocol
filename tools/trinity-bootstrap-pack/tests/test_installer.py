"""Installer integration tests (dry-run + full)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.installer import InstallError, run_install
from lib.pack_manifest import PACK_VERSION


INSTALLER_FILE = Path(__file__).resolve().parent.parent / "lib" / "installer.py"


def test_greenfield_dry_run_writes_receipt(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    target.mkdir()
    receipt = run_install(
        target=target,
        mode_override="greenfield",
        dry_run=True,
        force=False,
        allow_self_install=False,
        project_name="testproj",
        installer_file=INSTALLER_FILE,
    )
    assert receipt["pack_version"] == PACK_VERSION
    assert receipt["mode"] == "greenfield"
    assert receipt["dry_run"] is True
    receipt_file = target / ".trinity-install-receipt.json"
    assert receipt_file.exists()
    body = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert body["pack_version"] == PACK_VERSION


def test_greenfield_full_install_lays_down_files(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    target.mkdir()
    receipt = run_install(
        target=target,
        mode_override="greenfield",
        dry_run=False,
        force=False,
        allow_self_install=False,
        project_name="myproj",
        installer_file=INSTALLER_FILE,
    )
    assert receipt["dry_run"] is False
    assert receipt["file_count"] > 0
    # CLAUDE.md should land at root with project name substituted
    claude = target / "CLAUDE.md"
    assert claude.exists()
    assert "myproj" in claude.read_text(encoding="utf-8")
    # ssot.yaml under .ai/
    assert (target / ".ai" / "ssot.yaml").exists()


def test_refuses_non_empty_target_without_force(tmp_path: Path) -> None:
    target = tmp_path / "occupied"
    target.mkdir()
    (target / "existing.txt").write_text("hello", encoding="utf-8")
    with pytest.raises(InstallError) as excinfo:
        run_install(
            target=target,
            mode_override="greenfield",
            dry_run=False,
            force=False,
            allow_self_install=False,
            project_name=None,
            installer_file=INSTALLER_FILE,
        )
    assert excinfo.value.exit_code == 20


def test_refuses_self_install_without_flag(tmp_path: Path) -> None:
    # Build a directory shaped like trinity_v2 source root.
    target = tmp_path / "v2_clone"
    cli = target / ".ai" / "cli"
    cli.mkdir(parents=True)
    (cli / "ai").write_text("#!/bin/sh\n", encoding="utf-8")
    (target / ".ai" / "ssot.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    with pytest.raises(InstallError) as excinfo:
        run_install(
            target=target,
            mode_override=None,  # auto-detect → self
            dry_run=True,
            force=False,
            allow_self_install=False,
            project_name=None,
            installer_file=INSTALLER_FILE,
        )
    assert excinfo.value.exit_code == 20
    assert "self-install refused" in str(excinfo.value)


def test_upgrade_v1_keeps_existing_files(tmp_path: Path) -> None:
    target = tmp_path / "v1"
    target.mkdir()
    (target / "ai-docs").mkdir()
    existing = target / "CLAUDE.md"
    existing.write_text("PRESERVE-ME", encoding="utf-8")
    receipt = run_install(
        target=target,
        mode_override="upgrade-v1",
        dry_run=False,
        force=False,
        allow_self_install=False,
        project_name="legacy",
        installer_file=INSTALLER_FILE,
    )
    assert receipt["mode"] == "upgrade-v1"
    # CLAUDE.md preserved
    assert existing.read_text(encoding="utf-8") == "PRESERVE-ME"
    # New file laid down
    assert (target / ".ai" / "ssot.yaml").exists()
