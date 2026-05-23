"""Detector unit tests."""

from pathlib import Path

import pytest

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent.parent))

from lib.detector import detect


def test_greenfield_when_empty(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    target.mkdir()
    fake_source = tmp_path / "src"
    fake_source.mkdir()
    res = detect(target, fake_source)
    assert res.mode == "greenfield"


def test_upgrade_v1_when_ai_docs_only(tmp_path: Path) -> None:
    target = tmp_path / "v1proj"
    (target / "ai-docs").mkdir(parents=True)
    (target / "CLAUDE.md").write_text("legacy", encoding="utf-8")
    fake_source = tmp_path / "src"
    fake_source.mkdir()
    res = detect(target, fake_source)
    assert res.mode == "upgrade-v1"


def test_upgrade_v2_when_ai_cli_present(tmp_path: Path) -> None:
    target = tmp_path / "v2proj"
    (target / ".ai" / "cli").mkdir(parents=True)
    fake_source = tmp_path / "src"
    fake_source.mkdir()
    res = detect(target, fake_source)
    assert res.mode == "upgrade-v2"


def test_self_install_when_target_equals_source(tmp_path: Path) -> None:
    root = tmp_path / "trinity_v2"
    root.mkdir()
    res = detect(root, root)
    assert res.mode == "self"


def test_self_install_when_markers_match(tmp_path: Path) -> None:
    target = tmp_path / "looks_like_v2"
    cli = target / ".ai" / "cli"
    cli.mkdir(parents=True)
    (cli / "ai").write_text("#!/bin/sh\n", encoding="utf-8")
    (target / ".ai" / "ssot.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    fake_source = tmp_path / "src"
    fake_source.mkdir()
    res = detect(target, fake_source)
    assert res.mode == "self"
