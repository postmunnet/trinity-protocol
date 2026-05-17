"""Phase 6 Session F (FINAL) — gogogo step-tool binding integration tests.

Tests both:
  (a) source-level wiring of `tool_invocation_guard` / `lease_lifecycle`
      into `commands/gogogo.py`, and
  (b) runtime behavior when a plan step declares an optional `tool` field.

Reuses the `_seed_at_do` fixture shape from `test_gogogo_hmac.py` for the
session/graph state, then adds `.ai/tools.yaml` + `.ai/tools.capabilities.yaml`
and runs `_run` to verify the chain rows.
"""
from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
import typer
import yaml

# Phase 6 Session H — dispatcher now exec's the binary after ALLOW, so
# fixtures must point at a real exit-0 binary instead of a /fake/ path.
_TRUE_BIN = shutil.which("true") or "/bin/true"

from cli.commands import gogogo as gogogo_mod
from cli.commands.gogogo import _run
from cli.core.audit import AuditChain
from cli.core.loop import Loop

from test_goal_loop import _make_project

VERIFIER_RULES_YAML = (
    Path(__file__).resolve().parent.parent.parent
    / "policies"
    / "verifier-rules.yaml"
).read_text()


# ─── tool registry fixture builders ──────────────────────────────────


def _full_tool_entry(name: str, **overrides: Any) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        "name": name,
        "description": f"{name} description",
        "path": f"/fake/{name}",
        # Phase 6 Session H: dispatcher exec's the binary after ALLOW, so
        # the fixture must point at a real exit-0 binary. `/bin/true`
        # accepts and ignores any argv.
        "bin": _TRUE_BIN,
        "schema_version": "1",
        "contract_version": "1.0",
        "capabilities": ["x"],
        "policy_default": "safe",
    }
    e.update(overrides)
    return e


def _full_cap_entry(name: str, **overrides: Any) -> Dict[str, Any]:
    e: Dict[str, Any] = {
        "name": name,
        "required_capabilities": ["fs.read"],
        "optional_capabilities": [],
        "default_tier_requirement": "WARM",
        "notes": "",
    }
    e.update(overrides)
    return e


def _full_vocabulary() -> Dict[str, List[str]]:
    return {
        "fs": ["fs.read", "fs.write", "fs.delete"],
        "net": ["net.outbound", "net.allowlist"],
        "proc": ["proc.exec", "proc.spawn"],
        "audit": ["audit.read", "audit.append"],
        "policy": ["policy.read"],
        "ddd": ["ddd.propose", "ddd.decide"],
        "tool": ["tool.invoke"],
    }


def _write_registry(proj: Path, tools: List[Dict[str, Any]], caps: List[Dict[str, Any]]) -> None:
    (proj / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "tools": tools}, sort_keys=False),
        encoding="utf-8",
    )
    (proj / ".ai" / "tools.capabilities.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "status": "authoritative",
                "authoritative": True,
                "capability_vocabulary": _full_vocabulary(),
                "tools": caps,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _seed_at_do(tmp_path: Path) -> Tuple[Path, Path]:
    """Mirror of `test_gogogo_hmac._seed_at_do`. Returns (proj, sess)."""
    proj, sess = _make_project(tmp_path, with_budget=True)
    rituals_target = proj / ".ai" / "rituals"
    if not rituals_target.exists():
        rituals_target.symlink_to(
            Path(__file__).resolve().parent.parent.parent / "rituals"
        )
    (proj / ".ai" / "policies" / "verifier-rules.yaml").write_text(VERIFIER_RULES_YAML)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({"version": "1.0", "paths": {"state": "${ai_root}/state"}})
    )
    (proj / ".ai" / "state").mkdir(exist_ok=True, parents=True)
    (proj / ".ai" / "state" / "status.json").write_text(
        json.dumps({"version": "1.0", "current_session": str(sess)})
    )

    loop = Loop(sess, graph_name="standard", project_root=proj)
    loop.fire("sss", decided_by="kernel")
    loop.fire("nnn_pass", decided_by="kernel")
    loop.fire("vvv_pass", decided_by="verifier")
    assert loop.current() == "DO"

    (sess / ".state" / "vvv_pass").write_text("ok")
    (sess / ".state" / "nnn_pass").write_text("ok")
    return proj, sess


def _write_plan(sess: Path, steps: List[Dict[str, Any]]) -> None:
    (sess / ".state" / "plan.json").write_text(json.dumps({"steps": steps}))


def _chain_events(proj: Path) -> List[Dict[str, Any]]:
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    return list(chain.iter_events())


# ─── A1 source-level wiring ──────────────────────────────────────────


def test_gogogo_imports_lease_lifecycle_and_load_registry() -> None:
    """A1 — module sources the Session E/F symbols."""
    source = inspect.getsource(gogogo_mod)
    assert "from ..core.lease_lifecycle import run_lease_lifecycle" in source
    assert "from ..core.tool_registry import" in source
    assert "RegistryValidationError" in source
    assert "load_registry" in source


def test_gogogo_step_loop_guards_tool_field() -> None:
    """A1b — the wiring only activates when step.get('tool') is truthy."""
    source = inspect.getsource(gogogo_mod)
    assert "tool_name = step.get(\"tool\")" in source
    assert "if tool_name:" in source
    # Backward-compat: keep the original step_started + _verify_step flow.
    assert "_verify_step(step, rule_set, rules_doc)" in source


def test_gogogo_propagates_lifecycle_failure() -> None:
    """A1c — denied lifecycle raises typer.Exit(1).

    Wire #2 (sandbox bind) renamed `lifecycle` → `result` (GatedResult).
    Accept either variable name so the historical Session F assertion
    survives the rename.
    """
    source = inspect.getsource(gogogo_mod)
    assert ("if not lifecycle.success:" in source) or (
        "if not result.success:" in source
    )
    assert "typer.Exit(1)" in source


def test_gogogo_handles_registry_load_failure() -> None:
    """A1d — RegistryValidationError / OSError emit gogogo.step_failed and Exit(2)."""
    source = inspect.getsource(gogogo_mod)
    assert "tool registry load failed" in source
    assert "RegistryValidationError" in source
    assert "typer.Exit(2)" in source


# ─── A2 happy path: declared tool emits proposed ─────────────────────


def test_declared_tool_emits_invocation_proposed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    _write_plan(sess, [{"n": 1, "title": "smoke", "tool": "alpha"}])
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "gogogo.step_started" in types
    assert "tool.invocation_proposed" in types
    # The proposed row carries the tool name + a lease_id.
    proposed = [e for e in events if e["type"] == "tool.invocation_proposed"]
    assert len(proposed) == 1
    assert proposed[0]["details"]["tool_name"] == "alpha"
    assert "lease_id" in proposed[0]["details"]


# ─── A3 unknown tool denied ──────────────────────────────────────────


def test_unknown_tool_denied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    _write_plan(sess, [{"n": 1, "title": "smoke", "tool": "ghost"}])
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    denied = [e for e in events if e["type"] == "tool.invocation_denied"]
    assert len(denied) == 1
    assert denied[0]["details"]["tool_name"] == "ghost"
    assert denied[0]["details"]["reason"] == "unknown_tool"


# ─── A4 backward compat: no tool field, zero invocation events ───────


def test_no_tool_field_zero_invocation_events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proj, sess = _seed_at_do(tmp_path)
    # Intentionally do NOT write tools.yaml.
    _write_plan(sess, [{"n": 1, "title": "smoke step"}])
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "gogogo.step_started" in types
    # Zero invocation events when step has no tool field.
    assert "tool.invocation_proposed" not in types
    assert "tool.invocation_denied" not in types


# ─── A5 registry load failure exits 2 ────────────────────────────────


def test_registry_load_failure_exits_two(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proj, sess = _seed_at_do(tmp_path)
    # Plan declares a tool but the project has no tools.yaml — load_registry
    # raises RegistryValidationError (missing file).
    _write_plan(sess, [{"n": 1, "title": "smoke", "tool": "alpha"}])
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 2

    events = _chain_events(proj)
    failed = [
        e for e in events
        if e["type"] == "gogogo.step_failed"
        and "tool registry load failed" in str(e.get("details", {}).get("verifier_reason", ""))
    ]
    assert len(failed) == 1


# ─── A6 chain integrity after mixed plan ─────────────────────────────


def test_chain_validates_after_mixed_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_full_tool_entry("alpha")], [_full_cap_entry("alpha")])
    _write_plan(
        sess,
        [
            {"n": 1, "title": "no-tool step"},
            {"n": 2, "title": "declared tool", "tool": "alpha"},
            {"n": 3, "title": "another no-tool step"},
        ],
    )
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    chain.validate()  # raises if any link broken
    events = list(chain.iter_events())
    proposed = [e for e in events if e["type"] == "tool.invocation_proposed"]
    assert len(proposed) == 1  # only step 2 has a tool
    assert proposed[0]["details"]["tool_name"] == "alpha"
