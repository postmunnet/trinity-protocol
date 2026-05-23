"""Tests for bootstrap.sh — curl|bash entrypoint.

Strategy: we don't actually clone over the network in tests. Instead we
seed a fake "remote" as a local bare repo, point TRINITY_REPO_URL at it,
and verify the bootstrap script clones / dispatches correctly.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


PACK_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_SH = PACK_ROOT / "bootstrap.sh"


def test_bootstrap_exists_and_executable() -> None:
    assert BOOTSTRAP_SH.is_file()
    assert os.access(BOOTSTRAP_SH, os.X_OK)


def test_help_mentions_cache_and_ref() -> None:
    proc = subprocess.run(
        ["bash", str(BOOTSTRAP_SH), "--help"], capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "TRINITY_KERNEL_CACHE" in proc.stdout
    assert "--ref" in proc.stdout


def test_help_no_args_shows_usage() -> None:
    proc = subprocess.run(
        ["bash", str(BOOTSTRAP_SH)], capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Usage" in proc.stdout


def test_cache_parent_not_writable_fails(tmp_path: Path) -> None:
    # Point cache at /nonexistent/never — parent not writable.
    proc = subprocess.run(
        ["bash", str(BOOTSTRAP_SH), str(tmp_path / "tgt"),
         "--kernel-cache", "/nonexistent/never/cache"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert proc.returncode == 60
    assert "cache parent not writable" in proc.stderr


def test_clone_dispatch_with_local_fake_remote(tmp_path: Path) -> None:
    """Set TRINITY_REPO_URL to a local bare repo and verify the wrapper:
    1. clones into the user-specified cache,
    2. dispatches to install.sh in that cache.
    """
    # Build a fake trinity_v2 source tree
    fake_source = tmp_path / "fake_trinity_v2"
    fake_source.mkdir()
    # Mirror the real install.sh shape: just a tiny script that prints OK
    install_sh = fake_source / "tools" / "trinity-bootstrap-pack" / "install.sh"
    install_sh.parent.mkdir(parents=True)
    install_sh.write_text(
        "#!/usr/bin/env bash\n"
        'echo "INSTALL_SH_CALLED args: $@"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    install_sh.chmod(0o755)

    # Init it as a git repo so bootstrap's git clone works
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=fake_source, check=True)
    subprocess.run(["git", "add", "."], cwd=fake_source, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"],
        cwd=fake_source,
        check=True,
    )

    cache = tmp_path / "kernel-cache"
    env = {
        **os.environ,
        "TRINITY_REPO_URL": str(fake_source),
        "TRINITY_KERNEL_CACHE": str(cache),
        "HOME": str(tmp_path),
    }
    proc = subprocess.run(
        ["bash", str(BOOTSTRAP_SH), str(tmp_path / "my-target"),
         "--project-name", "smoke"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "INSTALL_SH_CALLED" in proc.stdout
    assert (cache / ".git").is_dir()
    assert (cache / "tools" / "trinity-bootstrap-pack" / "install.sh").is_file()


def test_passthrough_args_reach_install_sh(tmp_path: Path) -> None:
    """Ensure --project-name and other install-time flags are passed through."""
    fake_source = tmp_path / "fake_v2"
    fake_source.mkdir()
    install_sh = fake_source / "tools" / "trinity-bootstrap-pack" / "install.sh"
    install_sh.parent.mkdir(parents=True)
    install_sh.write_text(
        "#!/usr/bin/env bash\n"
        'printf "ARGS:[%s]\\n" "$*"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    install_sh.chmod(0o755)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=fake_source, check=True)
    subprocess.run(["git", "add", "."], cwd=fake_source, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"],
        cwd=fake_source,
        check=True,
    )

    cache = tmp_path / "cache2"
    env = {
        **os.environ,
        "TRINITY_REPO_URL": str(fake_source),
        "TRINITY_KERNEL_CACHE": str(cache),
        "HOME": str(tmp_path),
    }
    proc = subprocess.run(
        ["bash", str(BOOTSTRAP_SH), str(tmp_path / "tgt"),
         "--project-name", "myproj", "--with-kernel", "none"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, f"stderr={proc.stderr}"
    assert "myproj" in proc.stdout
    assert "--project-name" in proc.stdout
    assert "--with-kernel none" in proc.stdout or "--with-kernel" in proc.stdout
