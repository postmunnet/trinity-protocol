"""End-to-end smoke: invoke install.sh as a subprocess."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


PACK_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = PACK_ROOT / "install.sh"


def test_install_sh_exists_and_executable() -> None:
    assert INSTALL_SH.is_file()
    assert os.access(INSTALL_SH, os.X_OK)


def test_dry_run_greenfield_smoke(tmp_path: Path) -> None:
    target = tmp_path / "smoke"
    target.mkdir()
    proc = subprocess.run(
        ["bash", str(INSTALL_SH), "--dry-run", "--target", str(target),
         "--mode", "greenfield", "--project-name", "smoketest"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    receipt_file = target / ".trinity-install-receipt.json"
    assert receipt_file.exists()
    body = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert body["pack_version"] == "trinity-bootstrap-pack-v1"
    assert body["mode"] == "greenfield"
    assert body["dry_run"] is True


def test_self_install_refusal_smoke(tmp_path: Path) -> None:
    target = tmp_path / "fake_v2"
    cli = target / ".ai" / "cli"
    cli.mkdir(parents=True)
    (cli / "ai").write_text("#!/bin/sh\n", encoding="utf-8")
    (target / ".ai" / "ssot.yaml").write_text("version: '1.0'\n", encoding="utf-8")

    proc = subprocess.run(
        ["bash", str(INSTALL_SH), "--dry-run", "--target", str(target)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 20, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "self-install refused" in proc.stderr
