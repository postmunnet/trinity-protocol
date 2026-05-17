"""Wire #2 — verify sandbox_gate + sandbox profile loader wired into gogogo."""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

from cli.commands import gogogo as gogogo_mod
from cli.commands.gogogo import SandboxProfileLoadError, _load_sandbox_profile
from cli.core.sandbox_contract import SandboxProfile


def test_gogogo_imports_sandbox_gate_and_validator() -> None:
    src = inspect.getsource(gogogo_mod)
    assert "from ..core.sandbox_gate import run_sandbox_gated_lifecycle" in src
    assert "validate_profile_dict" in src


def test_gogogo_has_load_sandbox_profile_helper() -> None:
    assert callable(_load_sandbox_profile)


def test_step_loop_uses_run_sandbox_gated_lifecycle() -> None:
    src = inspect.getsource(gogogo_mod)
    assert "result = run_sandbox_gated_lifecycle(" in src
    # The old direct call to run_lease_lifecycle inside the step loop
    # should be replaced (still imported, but not called directly per-step).
    # Source should still reference the import line, just not call it per step.


def test_helper_reads_canonical_profile_path() -> None:
    src = inspect.getsource(_load_sandbox_profile)
    assert ".ai" in src
    assert "policies" in src
    assert "sandbox_profiles" in src
    assert ".yaml" in src


def test_helper_hydrates_sandbox_profile(tmp_path: Path) -> None:
    profiles_dir = tmp_path / ".ai" / "policies" / "sandbox_profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "demo.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "demo",
                "version": "1.0",
                "fs": {
                    "read_roots": ["/safe"],
                    "write_roots": ["/safe/out"],
                    "forbidden_paths": [],
                },
                "net": {"outbound": "denied", "allowlist": [], "protocols": []},
                "proc": {
                    "allowed_binaries": ["python3"],
                    "forbidden_binaries": [],
                    "spawn_allowed": False,
                    "max_wallclock_seconds": 60,
                },
                "tools": {"allowed": ["alpha"], "forbidden": []},
                "authority": {
                    "may_promote": False,
                    "may_deploy": False,
                    "may_modify_policies": False,
                    "ddd_propose_allowed": True,
                },
                "description": "demo sandbox",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    profile = _load_sandbox_profile(tmp_path, "demo")

    assert isinstance(profile, SandboxProfile)
    assert profile.id == "demo"
    assert profile.tools.allowed == ["alpha"]
    assert profile.net.outbound == "denied"
    assert profile.proc.allowed_binaries == ["python3"]


def test_helper_fail_closed_on_missing_profile(tmp_path: Path) -> None:
    with pytest.raises(SandboxProfileLoadError) as exc_info:
        _load_sandbox_profile(tmp_path, "nonexistent")
    assert exc_info.value.event_type == "sandbox.profile_missing"


def test_helper_fail_closed_on_invalid_yaml(tmp_path: Path) -> None:
    profiles_dir = tmp_path / ".ai" / "policies" / "sandbox_profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "bad.yaml").write_text("not: { valid: yaml\n", encoding="utf-8")
    with pytest.raises(SandboxProfileLoadError) as exc_info:
        _load_sandbox_profile(tmp_path, "bad")
    assert exc_info.value.event_type == "sandbox.profile_invalid"
