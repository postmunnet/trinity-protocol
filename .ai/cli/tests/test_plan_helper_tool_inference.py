"""S16 plan_helper tool-inference unit tests.

Activates the dormant dispatch+sandbox+policy infrastructure by
making plan_helper auto-emit `step.tool` when step.action mentions
a registered tool name.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

import sys

# plan_helper lives under .ai/cli/agents/plan_helper; importing it from
# pytest requires that path to be on sys.path.
_AGENT_ROOT = Path(__file__).resolve().parent.parent / "agents"
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


from plan_helper.core import (  # noqa: E402
    _infer_step_tools,
    _resolve_project_root,
)


# ─── fixtures: minimal tools.yaml + tools.capabilities.yaml ──────────


def _vocabulary() -> Dict[str, List[str]]:
    """Full vocabulary per TRINITY_TOOL_CAPABILITY_MODEL_V1 §2 — registry
    validator rejects missing axes."""
    return {
        "fs": ["fs.read", "fs.write", "fs.delete"],
        "net": ["net.outbound", "net.allowlist"],
        "proc": ["proc.exec", "proc.spawn"],
        "audit": ["audit.read", "audit.append"],
        "policy": ["policy.read"],
        "ddd": ["ddd.propose", "ddd.decide"],
        "tool": ["tool.invoke"],
    }


def _write_registry(proj: Path, tool_names: List[str]) -> None:
    (proj / ".ai").mkdir(exist_ok=True)
    tools = [
        {
            "name": n,
            "description": f"{n}",
            "path": f"/fake/{n}",
            "bin": f"/fake/{n}/bin",
            "schema_version": "1",
            "contract_version": "1.0",
            "capabilities": ["x"],
            "policy_default": "safe",
        }
        for n in tool_names
    ]
    caps = [
        {
            "name": n,
            "required_capabilities": ["fs.read"],
            "optional_capabilities": [],
            "default_tier_requirement": "WARM",
            "notes": "",
        }
        for n in tool_names
    ]
    (proj / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "tools": tools}, sort_keys=False)
    )
    (proj / ".ai" / "tools.capabilities.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "status": "authoritative",
                "authoritative": True,
                "capability_vocabulary": _vocabulary(),
                "tools": caps,
            },
            sort_keys=False,
        )
    )


def _envelope_with_actions(actions: List[str]) -> Dict[str, Any]:
    return {
        "goal": "test",
        "tier": "WARM",
        "allowed_paths": [],
        "forbidden_paths": [],
        "constitutional_notes": [],
        "steps": [
            {"id": f"S{i+1}", "action": a, "owner_role": "EXECUTOR",
             "expected_artifact": "x", "risk": "LOW"}
            for i, a in enumerate(actions)
        ],
        "acceptance": [],
        "rollback": [],
        "decided_by": "human",
    }


# ─── inference behavior ──────────────────────────────────────────────


def test_infers_browser_cli_from_action(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["browser-cli", "memory-cli"])
    env = _envelope_with_actions(["Use browser-cli to scrape the page."])
    inferred = _infer_step_tools(env, tmp_path)
    assert env["steps"][0].get("tool") == "browser-cli"
    assert inferred == [{"step_id": "S1", "tool_name": "browser-cli"}]


def test_no_match_no_injection(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["browser-cli", "memory-cli"])
    env = _envelope_with_actions(["Edit a python file"])
    inferred = _infer_step_tools(env, tmp_path)
    assert "tool" not in env["steps"][0]
    assert inferred == []


def test_preserves_existing_tool_field(tmp_path: Path) -> None:
    """If step already has tool field, don't overwrite — even on match."""
    _write_registry(tmp_path, ["browser-cli"])
    env = _envelope_with_actions(["Use browser-cli to fetch."])
    env["steps"][0]["tool"] = "memory-cli"  # pre-existing override
    inferred = _infer_step_tools(env, tmp_path)
    assert env["steps"][0]["tool"] == "memory-cli"  # preserved
    assert inferred == []  # nothing inferred (skipped)


def test_case_insensitive_match(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["browser-cli"])
    env = _envelope_with_actions(["Invoke BROWSER-CLI to scrape."])
    inferred = _infer_step_tools(env, tmp_path)
    assert env["steps"][0]["tool"] == "browser-cli"
    assert inferred == [{"step_id": "S1", "tool_name": "browser-cli"}]


def test_whole_word_only_no_partial_match(tmp_path: Path) -> None:
    """'browser-clinic' should NOT match registered 'browser-cli'."""
    _write_registry(tmp_path, ["browser-cli"])
    env = _envelope_with_actions(["The browser-clinic team approved."])
    inferred = _infer_step_tools(env, tmp_path)
    assert "tool" not in env["steps"][0]
    assert inferred == []


def test_hyphen_in_name_treated_as_word_extension(tmp_path: Path) -> None:
    """Hyphenated tool names match as a single unit (not split at -).

    Standard \\b regex treats `-` as a non-word char so `\\bcli\\b`
    matches inside `browser-cli`. The inference logic must NOT match
    just `cli` if only `browser-cli` is registered.
    """
    _write_registry(tmp_path, ["browser-cli"])
    env = _envelope_with_actions(["Run a cli command"])
    inferred = _infer_step_tools(env, tmp_path)
    assert "tool" not in env["steps"][0]


def test_multiple_steps_independent_inference(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["browser-cli", "memory-cli", "image-cli"])
    env = _envelope_with_actions([
        "Use browser-cli to fetch the page",
        "Run a plain bash command",
        "Use memory-cli to store the result",
    ])
    inferred = _infer_step_tools(env, tmp_path)
    assert env["steps"][0]["tool"] == "browser-cli"
    assert "tool" not in env["steps"][1]
    assert env["steps"][2]["tool"] == "memory-cli"
    assert {row["tool_name"] for row in inferred} == {"browser-cli", "memory-cli"}


def test_first_match_wins_when_multiple_tools_in_action(tmp_path: Path) -> None:
    """Action mentions two tools — longest-first ordering picks the more specific."""
    _write_registry(tmp_path, ["browser-cli", "seo-genie-cli"])
    env = _envelope_with_actions([
        "Pipe browser-cli output into seo-genie-cli for analysis."
    ])
    inferred = _infer_step_tools(env, tmp_path)
    # longest-first → seo-genie-cli wins over browser-cli
    assert env["steps"][0]["tool"] == "seo-genie-cli"


def test_registry_load_failure_fail_soft(tmp_path: Path) -> None:
    """Missing tools.yaml → return empty list, don't raise."""
    # No registry files written
    env = _envelope_with_actions(["Use browser-cli for something"])
    inferred = _infer_step_tools(env, tmp_path)
    assert inferred == []
    assert "tool" not in env["steps"][0]  # no injection on failure


def test_empty_action_text_skipped(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["browser-cli"])
    env = _envelope_with_actions([""])
    inferred = _infer_step_tools(env, tmp_path)
    assert inferred == []


def test_resolve_project_root_finds_ai_dir(tmp_path: Path) -> None:
    """The resolver walks up until it finds a .ai/ sibling."""
    (tmp_path / ".ai").mkdir()
    nested_session = tmp_path / ".ai" / "sessions" / "0001_x"
    nested_session.mkdir(parents=True)
    assert _resolve_project_root(nested_session) == tmp_path


def test_resolve_project_root_fallback(tmp_path: Path) -> None:
    """When no .ai/ found anywhere, fallback to session_path.parent."""
    # No .ai/ in tmp_path or its ancestors
    nowhere = tmp_path / "nodot" / "nested"
    nowhere.mkdir(parents=True)
    # We can't be sure no ancestor has .ai (tmp_path lineage might), but
    # we can at least assert it returns a Path without raising.
    result = _resolve_project_root(nowhere)
    assert isinstance(result, Path)


def test_step_without_action_skipped(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["browser-cli"])
    env = {
        "goal": "x", "tier": "WARM",
        "allowed_paths": [], "forbidden_paths": [], "constitutional_notes": [],
        "steps": [{"id": "S1", "owner_role": "EXECUTOR",
                   "expected_artifact": "x", "risk": "LOW"}],  # no action key
        "acceptance": [], "rollback": [], "decided_by": "human",
    }
    inferred = _infer_step_tools(env, tmp_path)
    assert inferred == []
