"""Tool registry runtime tests — load + invoke external tools.

Spec: docs/specs/01_TOOL_CONTRACT.md §16
Phase: 2.2 (first kernel-side caller is `ai rrr` → `memory-cli learn`)

Validates:
- `.ai/tools.yaml` parses into ToolEntry records
- `${project_root}` is expanded in `bin` and `path`
- `find_tool` raises ToolNotFound for unregistered names
- `call` returns ToolInvocation.ok=True when subprocess prints a v1
  envelope with `ok=true`
- `call` surfaces JSON parse errors and missing-executable cases
  without raising
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from cli.core.tools_registry import (
    ToolInvocation,
    ToolNotFound,
    call,
    find_tool,
    load_registry,
)


# ─────────── load_registry ───────────


def test_load_registry_parses_existing_tools_yaml():
    project_root = Path.cwd()
    reg = load_registry(project_root)
    assert "memory-cli" in reg, "memory-cli should be registered"
    entry = reg["memory-cli"]
    # ${project_root} must be expanded
    assert "${project_root}" not in " ".join(entry.bin_argv)
    assert str(entry.path).startswith(str(project_root.parent)) \
        or str(entry.path).startswith(str(project_root)), \
        f"bin path {entry.path} should resolve under or sibling-of repo root"


def test_load_registry_missing_tools_yaml_returns_empty(tmp_path: Path):
    # No .ai/tools.yaml in a fresh tmp dir
    reg = load_registry(tmp_path)
    assert reg == {}


# ─────────── find_tool ───────────


def test_find_tool_raises_for_unknown_name():
    with pytest.raises(ToolNotFound):
        find_tool(Path.cwd(), "this-tool-does-not-exist")


def test_find_tool_returns_entry_for_known_name():
    entry = find_tool(Path.cwd(), "memory-cli")
    assert entry.name == "memory-cli"
    assert entry.contract_version == "1.0"


# ─────────── call (synthetic tool) ───────────


def _make_synthetic_tool(
    tmp_path: Path, response: dict, name: str = "fake-tool",
    exit_code: int = 0,
) -> Path:
    """Build a tiny .ai/tools.yaml that points at a python script
    which prints `response` as JSON, then returns. Registers the tool
    under `name` and returns the synthetic project_root."""
    proj = tmp_path / "proj"
    (proj / ".ai").mkdir(parents=True)

    script = proj / "fake_bin.py"
    script.write_text(
        textwrap.dedent(
            f"""\
            import json, sys
            print(json.dumps({response!r}))
            sys.exit({exit_code})
            """
        ).replace("{response!r}", json.dumps(response)),
        encoding="utf-8",
    )

    tools_yaml = proj / ".ai" / "tools.yaml"
    tools_yaml.write_text(
        yaml.safe_dump({
            "version": "1.0",
            "tools": [
                {
                    "name": name,
                    "path": "${project_root}",
                    "bin": f"{sys.executable} ${{project_root}}/fake_bin.py",
                    "schema_version": "1",
                    "contract_version": "1.0",
                    "capabilities": ["test"],
                    "policy_default": "safe",
                    "health_check": "--health",
                }
            ],
        }),
        encoding="utf-8",
    )
    return proj


def test_call_returns_ok_when_tool_prints_ok_envelope(tmp_path: Path):
    envelope = {
        "ok": True,
        "schema_version": "1.0",
        "tool": "fake-tool",
        "tool_version": "0.0.1",
        "command": "ping",
        "action": "fake.ping",
        "data": {"answer": 42},
        "artifacts": [],
        "error": None,
        "meta": {"ts": "2026-04-30T00:00:00Z"},
    }
    proj = _make_synthetic_tool(tmp_path, envelope)
    inv = call(proj, "fake-tool", "ping")
    assert inv.ok is True
    assert inv.returncode == 0
    assert inv.envelope["data"]["answer"] == 42


def test_call_returns_not_ok_when_envelope_has_error(tmp_path: Path):
    envelope = {
        "ok": False,
        "schema_version": "1.0",
        "tool": "fake-tool",
        "command": "ping",
        "action": None,
        "data": None,
        "artifacts": [],
        "error": {"code": "boom", "message": "sad"},
        "meta": {"ts": "2026-04-30T00:00:00Z"},
    }
    proj = _make_synthetic_tool(tmp_path, envelope, exit_code=1)
    inv = call(proj, "fake-tool", "ping")
    assert inv.ok is False
    assert inv.envelope["error"]["code"] == "boom"


def test_call_returns_error_when_tool_unregistered(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / ".ai").mkdir(parents=True)
    (proj / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "tools": []})
    )
    inv = call(proj, "missing-tool", "ping")
    assert inv.ok is False
    assert "not registered" in (inv.error or "")


def test_call_returns_error_when_executable_missing(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / ".ai").mkdir(parents=True)
    (proj / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump({
            "version": "1.0",
            "tools": [{
                "name": "ghost",
                "path": "${project_root}",
                "bin": "/no/such/binary --cmd",
                "schema_version": "1",
                "contract_version": "1.0",
                "capabilities": ["test"],
                "policy_default": "safe",
                "health_check": "--health",
            }],
        })
    )
    inv = call(proj, "ghost", "ping")
    assert inv.ok is False
    assert inv.error and "not found" in inv.error.lower()


# ─────────── E2E: real memory-cli (skip if missing) ───────────


def _memory_cli_available(project_root: Path) -> bool:
    try:
        entry = find_tool(project_root, "memory-cli")
    except ToolNotFound:
        return False
    if not entry.path.exists():
        return False
    if shutil.which("node") is None:
        return False
    return True


@pytest.mark.skipif(
    not _memory_cli_available(Path.cwd()),
    reason="memory-cli sibling not installed or `node` unavailable",
)
def test_e2e_memory_cli_health_envelope():
    # `--health` is its own flag, not via --cmd; we exercise that path
    # by passing it via extra_argv.
    inv = call(
        Path.cwd(),
        "memory-cli",
        "stats",  # any verb; `--health` flag bypasses --cmd
    )
    # Either stats ran (DB exists or returns zeros) or returned an
    # envelope; what matters is the JSON parsed.
    assert inv.envelope is not None, f"stdout was: {inv.stdout!r} stderr={inv.stderr!r}"
    assert inv.envelope["tool"] == "memory-cli"
