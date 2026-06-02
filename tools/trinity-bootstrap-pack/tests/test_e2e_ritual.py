"""End-to-end ritual smoke test.

The bug that motivated v1.2: pack v1.1 installed cleanly but `sss` crashed
with FileNotFoundError because `.ai/templates/session/` wasn't shipped or
symlinked. This test catches that class of bug — fresh install + actual
ritual cycle in the target.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALL_SH = REPO_ROOT / "tools" / "trinity-bootstrap-pack" / "install.sh"


@pytest.fixture
def fresh_install(tmp_path: Path) -> Path:
    """Install pack into a fresh target dir.

    On macOS, `tmp_path` is under /var/folders but pytest gives a /private
    prefix; resolving to the real path avoids cross-link comparison issues
    when the kernel compares cwd-relative vs absolute paths (matches the
    realpath quirk noted in feedback_sqlite_gotchas).
    """
    target = (tmp_path / "e2e_target").resolve()
    target.mkdir()
    # Resolve the symlink in the path so the kernel's path comparisons match.
    target = Path(os.path.realpath(target))
    proc = subprocess.run(
        ["bash", str(INSTALL_SH), str(target),
         "--project-name", "e2e-smoke", "--force"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"install failed:\n{proc.stdout}\n{proc.stderr}"
    return target


def test_install_lays_down_kernel_symlinks(fresh_install: Path) -> None:
    """v1.2: all 7 kernel dirs symlinked + 2 always-copied files present."""
    for sub in ("cli", "rituals", "graphs", "schemas", "shims", "templates", "checklists"):
        link = fresh_install / ".ai" / sub
        assert link.is_symlink() or link.is_dir(), f"{sub} missing"
    for f in ("requirements.txt", "tools.capabilities.yaml"):
        path = fresh_install / ".ai" / f
        assert path.is_file(), f"{f} missing"


def test_lll_runs_in_target(fresh_install: Path) -> None:
    """Sanity: `ai lll` must work in a freshly bootstrapped target."""
    proc = subprocess.run(
        ["bash", ".ai/cli/ai", "lll"],
        capture_output=True,
        text=True,
        cwd=str(fresh_install),
    )
    assert proc.returncode == 0, f"lll failed:\n{proc.stdout}\n{proc.stderr}"
    assert "snapshot" in proc.stdout.lower() or "session" in proc.stdout.lower()


def test_sss_scaffolds_session(fresh_install: Path) -> None:
    """The bug that motivated v1.2: sss must NOT crash with FileNotFoundError."""
    proc = subprocess.run(
        ["bash", ".ai/cli/ai", "sss", "smoke-test-task"],
        capture_output=True,
        text=True,
        cwd=str(fresh_install),
    )
    assert proc.returncode == 0, (
        f"sss failed — likely missing kernel binding:\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    # Verify session capsule scaffold succeeded
    sessions = list((fresh_install / ".ai" / "sessions").glob("[0-9]*"))
    assert sessions, "no session dir created"
    session = sessions[0]
    assert (session / "THINK").is_dir()
    assert (session / "THINK" / "CONSENSUS.md").is_file(), (
        "CONSENSUS.md missing — the v1.1 bug we set out to fix"
    )


def test_vvv_with_answers_succeeds(fresh_install: Path) -> None:
    """Full sss -> vvv cycle should work end-to-end."""
    proc_sss = subprocess.run(
        ["bash", ".ai/cli/ai", "sss", "smoke-vvv"],
        capture_output=True, text=True, cwd=str(fresh_install),
    )
    assert proc_sss.returncode == 0, f"sss step failed: {proc_sss.stderr}"

    proc_vvv = subprocess.run(
        ["bash", ".ai/cli/ai", "vvv",
         "--answer", "1=success means smoke test passes",
         "--answer", "2=in: smoke; out: anything else",
         "--answer", "3=forbidden: .ai/policies/, .ai/audit/",
         "--answer", "4=A1: this test exits 0",
         "--answer", "5=no major risk; isolated tmp"],
        capture_output=True, text=True, cwd=str(fresh_install),
    )
    assert proc_vvv.returncode == 0, (
        f"vvv failed — bindings issue?\n"
        f"stdout={proc_vvv.stdout}\nstderr={proc_vvv.stderr}"
    )
    # vvv_pass marker should exist
    sessions = list((fresh_install / ".ai" / "sessions").glob("[0-9]*"))
    session = sessions[0]
    assert (session / ".state" / "vvv_pass").exists()
