"""Verify project-root pyproject.toml carries pytest config for cwd-agnostic discovery."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT = REPO_ROOT / "pyproject.toml"


def test_pyproject_exists_at_repo_root() -> None:
    assert PYPROJECT.is_file()


def test_pytest_ini_options_section_present() -> None:
    # tomllib is 3.11+; for 3.9/3.10 fall back to a plain text check that
    # avoids adding a tomli dependency.
    body = PYPROJECT.read_text(encoding="utf-8")
    assert "[tool.pytest.ini_options]" in body
    assert "testpaths" in body


def test_pytest_finds_tests_from_arbitrary_cwd(tmp_path: Path) -> None:
    """The whole point of pyproject's rootdir anchor: pytest must find the
    project's tests no matter where you invoke it from.
    """
    proc = subprocess.run(
        ["python3", "-m", "pytest",
         str(REPO_ROOT / "tools" / "trinity-bootstrap-pack" / "tests"),
         "-q", "--collect-only"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "no tests ran" not in proc.stdout.lower()
