"""Tool registry validation — Decision D13.

Catches:
- Missing required fields in .ai/tools.yaml entries (per 01_TOOL_CONTRACT.md §16.1)
- Path-resolution rules violated by entries (per .ai/policies/tools-policy.yaml)
- Contract baseline folder missing for a registered tool
- Unsupported contract_version
- Forbidden absolute paths (D12 violation)
- Reference to disallowed root (kernel-internal path)
"""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from cli.core.tools_registry import call


# conftest.py pins cwd to repo root and adds .ai/ to sys.path,
# so direct path strings work the same from .ai/ or repo root.
TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent

TOOLS_YAML = REPO_ROOT / ".ai" / "tools.yaml"
TOOLS_POLICY = REPO_ROOT / ".ai" / "policies" / "tools-policy.yaml"
CONTRACTS_DIR = REPO_ROOT / "docs" / "contracts"


REQUIRED_FIELDS = {
    "name",
    "path",
    "bin",
    "schema_version",
    "contract_version",
    "capabilities",
    "policy_default",
    "health_check",
}


def _load(path: Path):
    with open(path) as f:
        return yaml.safe_load(f)


def _get_tools() -> list[dict]:
    return _load(TOOLS_YAML).get("tools") or []


def _write_minimal_tools_yaml(project_root: Path) -> None:
    ai_dir = project_root / ".ai"
    ai_dir.mkdir(parents=True)
    (ai_dir / "tools.yaml").write_text(
        yaml.safe_dump(
            {
                "tools": [
                    {
                        "name": "memory-cli",
                        "path": "${project_root}/../memory-cli",
                        "bin": "node ${project_root}/../memory-cli/index.js",
                        "schema_version": "1",
                        "contract_version": "1.0",
                        "capabilities": [],
                        "policy_default": "safe",
                        "health_check": "--health",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_tools_yaml_loads():
    """tools.yaml must parse and have a top-level `tools` list."""
    data = _load(TOOLS_YAML)
    assert isinstance(data, dict)
    assert "tools" in data, "tools.yaml missing top-level `tools` key"
    assert isinstance(data["tools"], list)


def test_tools_policy_loads():
    """tools-policy.yaml must parse and define tiers + path_resolution."""
    policy = _load(TOOLS_POLICY)
    assert "tiers" in policy
    assert "path_resolution" in policy
    assert "version_handshake" in policy
    assert set(policy["tiers"].keys()) >= {"safe", "normal", "aggressive"}


def test_call_sets_trinity_memory_db_for_memory_cli(
    tmp_path: Path,
    monkeypatch,
):
    _write_minimal_tools_yaml(tmp_path)
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout='{"ok": true, "data": {"status": "ok"}}',
            stderr="",
        )

    monkeypatch.delenv("MEMORY_DB", raising=False)
    monkeypatch.delenv("TRINITY_MEMORY_DB", raising=False)
    monkeypatch.setattr("cli.core.tools_registry.subprocess.run", fake_run)

    inv = call(tmp_path, "memory-cli", "health")

    assert inv.ok is True
    assert captured["kwargs"]["cwd"] == str(tmp_path)
    assert captured["kwargs"]["env"]["TRINITY_MEMORY_DB"] == str(
        (tmp_path / ".ai" / ".memory" / "memory.sqlite").resolve()
    )


def test_call_respects_operator_memory_db_override(
    tmp_path: Path,
    monkeypatch,
):
    _write_minimal_tools_yaml(tmp_path)
    captured = {}

    def fake_run(argv, **kwargs):
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout='{"ok": true, "data": {"status": "ok"}}',
            stderr="",
        )

    monkeypatch.setenv("MEMORY_DB", "/tmp/operator-memory.sqlite")
    monkeypatch.delenv("TRINITY_MEMORY_DB", raising=False)
    monkeypatch.setattr("cli.core.tools_registry.subprocess.run", fake_run)

    inv = call(tmp_path, "memory-cli", "health")

    assert inv.ok is True
    assert captured["kwargs"]["env"]["MEMORY_DB"] == "/tmp/operator-memory.sqlite"
    assert "TRINITY_MEMORY_DB" not in captured["kwargs"]["env"]


@pytest.mark.parametrize("idx", range(len(_get_tools()) or 1))
def test_each_tool_has_required_fields(idx):
    """Each entry must declare every field required by 01_TOOL_CONTRACT.md §16.1."""
    tools = _get_tools()
    if not tools:
        pytest.skip("no tools registered yet")

    tool = tools[idx]
    missing = REQUIRED_FIELDS - set(tool.keys())
    assert not missing, f"tool {tool.get('name', idx)!r} missing fields: {missing}"


@pytest.mark.parametrize("tool", _get_tools())
def test_tool_paths_are_not_absolute_user_paths(tool):
    """D12: no absolute <user-home> /var/* /etc/* paths in tools.yaml."""
    forbidden_prefixes = ("/Users/", "/var/", "/etc/", "/home/", "/root/")
    for field in ("path", "bin"):
        value = tool.get(field, "")
        for prefix in forbidden_prefixes:
            assert prefix not in value, \
                f"tool {tool['name']!r}: {field}={value!r} contains forbidden prefix {prefix!r}"


@pytest.mark.parametrize("tool", _get_tools())
def test_tool_paths_do_not_point_into_kernel(tool):
    """Tools must live outside .ai/ — kernel and tools are separate concerns (D13)."""
    for field in ("path", "bin"):
        value = tool.get(field, "")
        assert "${project_root}/.ai" not in value, \
            f"tool {tool['name']!r}: {field} points into kernel internals"


@pytest.mark.parametrize("tool", _get_tools())
def test_tool_policy_tier_is_valid(tool):
    """policy_default must be one of safe|normal|aggressive."""
    valid = {"safe", "normal", "aggressive"}
    assert tool.get("policy_default") in valid, \
        f"tool {tool['name']!r}: policy_default={tool.get('policy_default')!r} not in {valid}"


@pytest.mark.parametrize("tool", _get_tools())
def test_tool_contract_version_is_supported(tool):
    """contract_version must be in tools-policy.yaml::version_handshake.supported_contract_versions."""
    policy = _load(TOOLS_POLICY)
    supported = policy["version_handshake"]["supported_contract_versions"]
    cv = tool.get("contract_version")
    assert cv in supported, \
        f"tool {tool['name']!r}: contract_version={cv!r} not in supported {supported}"


@pytest.mark.parametrize("tool", _get_tools())
def test_contract_baseline_exists(tool):
    """If a tool declares contract_baseline, the folder must exist with a README."""
    baseline = tool.get("contract_baseline")
    if not baseline:
        return
    baseline_path = REPO_ROOT / baseline
    assert baseline_path.is_dir(), \
        f"tool {tool['name']!r}: contract_baseline {baseline_path} missing"
    assert (baseline_path / "README.md").is_file(), \
        f"tool {tool['name']!r}: contract_baseline missing README.md"
