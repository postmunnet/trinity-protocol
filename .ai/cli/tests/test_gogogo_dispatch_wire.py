"""Phase 6 Session H — gogogo dispatch-wire integration tests.

Covers the four cases declared in the wire's vvv answer:

  (a) step.tool absent           → no dispatch, no invocation rows
  (b) tool ALLOW + exit 0        → proposed → started → completed (ordered)
  (c) tool ALLOW + exit !=0      → proposed → started → failed, Exit(1)
  (d) sandbox-deny short-circuit → sandbox.deny only (no started)

Reuses the `_seed_at_do` fixture pattern from `test_gogogo_step_tool_binding.py`
and uses /bin/true (exit 0) and /bin/false (exit 1) as portable real binaries.
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

TRUE_BIN = shutil.which("true") or "/bin/true"
FALSE_BIN = shutil.which("false") or "/bin/false"


def _tool_entry(name: str, bin_path: str) -> Dict[str, Any]:
    return {
        "name": name,
        "description": f"{name} description",
        "path": f"/fake/{name}",
        "bin": bin_path,
        "schema_version": "1",
        "contract_version": "1.0",
        "capabilities": ["x"],
        "policy_default": "safe",
    }


def _cap_entry(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "required_capabilities": ["fs.read"],
        "optional_capabilities": [],
        "default_tier_requirement": "WARM",
        "notes": "",
    }


def _vocabulary() -> Dict[str, List[str]]:
    return {
        "fs": ["fs.read", "fs.write", "fs.delete"],
        "net": ["net.outbound", "net.allowlist"],
        "proc": ["proc.exec", "proc.spawn"],
        "audit": ["audit.read", "audit.append"],
        "policy": ["policy.read"],
        "ddd": ["ddd.propose", "ddd.decide"],
        "tool": ["tool.invoke"],
    }


def _write_registry(
    proj: Path, tools: List[Dict[str, Any]], caps: List[Dict[str, Any]]
) -> None:
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
                "capability_vocabulary": _vocabulary(),
                "tools": caps,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _seed_at_do(tmp_path: Path) -> Tuple[Path, Path]:
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


def _write_sandbox_profile(proj: Path, profile_id: str, profile: Dict[str, Any]) -> None:
    profile_dir = proj / ".ai" / "policies" / "sandbox_profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / f"{profile_id}.yaml").write_text(
        yaml.safe_dump(profile, sort_keys=False), encoding="utf-8"
    )


def _chain_events(proj: Path) -> List[Dict[str, Any]]:
    chain = AuditChain(proj / ".ai" / "audit" / "events.ndjson")
    return list(chain.iter_events())


# ─── A1 source-level wiring ──────────────────────────────────────────


def test_gogogo_imports_dispatch_tool() -> None:
    """A1 — module sources `dispatch_tool` from tool_dispatcher."""
    source = inspect.getsource(gogogo_mod)
    assert "from ..core.tool_dispatcher import dispatch_tool" in source
    assert "dispatch_tool(" in source


# ─── (a) no-tool bypass: no dispatch rows ────────────────────────────


def test_no_tool_field_no_dispatch_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_plan(sess, [{"n": 1, "title": "no-tool step"}])
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "gogogo.step_started" in types
    assert "tool.invocation_proposed" not in types
    assert "tool.invocation.started" not in types
    assert "tool.invocation.completed" not in types
    assert "tool.invocation.failed" not in types


# ─── (b) ALLOW + exit 0: proposed → started → completed ordered ──────


def test_dispatch_success_ordered_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("alpha", TRUE_BIN)], [_cap_entry("alpha")])
    _write_plan(sess, [{"n": 1, "title": "smoke", "tool": "alpha"}])
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    # Three tool rows in correct order
    assert "tool.invocation_proposed" in types
    assert "tool.invocation.started" in types
    assert "tool.invocation.completed" in types
    proposed_idx = types.index("tool.invocation_proposed")
    started_idx = types.index("tool.invocation.started")
    completed_idx = types.index("tool.invocation.completed")
    assert proposed_idx < started_idx < completed_idx

    # Completed row carries exit_code 0 and the right lease_id
    completed = [e for e in events if e["type"] == "tool.invocation.completed"]
    assert len(completed) == 1
    details = completed[0]["details"]
    assert details["exit_code"] == 0
    assert details["tool_name"] == "alpha"
    assert "lease_id" in details
    # And the lease_id matches the proposed row
    proposed = [e for e in events if e["type"] == "tool.invocation_proposed"]
    assert proposed[0]["details"]["lease_id"] == details["lease_id"]


# ─── (c) ALLOW + exit != 0: failed row + Exit(1) ─────────────────────


def test_dispatch_failure_emits_failed_and_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("beta", FALSE_BIN)], [_cap_entry("beta")])
    _write_plan(sess, [{"n": 1, "title": "smoke-fail", "tool": "beta"}])
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "tool.invocation_proposed" in types
    assert "tool.invocation.started" in types
    assert "tool.invocation.failed" in types
    # No completed row on failure
    assert "tool.invocation.completed" not in types

    failed = [e for e in events if e["type"] == "tool.invocation.failed"]
    assert len(failed) == 1
    assert failed[0]["details"]["exit_code"] == 1
    assert failed[0]["details"]["tool_name"] == "beta"

    # gogogo.step_failed appended after dispatch
    step_failed = [e for e in events if e["type"] == "gogogo.step_failed"]
    assert len(step_failed) == 1
    reason = step_failed[0]["details"]["verifier_reason"]
    assert "tool dispatch failed" in reason
    assert "exit=1" in reason


# ─── (d) sandbox-deny: short-circuit before started ──────────────────


def test_sandbox_deny_skips_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("gamma", TRUE_BIN)], [_cap_entry("gamma")])
    # Profile that explicitly forbids `gamma` via tools.forbidden.
    _write_sandbox_profile(
        proj,
        "deny-gamma",
        {
            "id": "deny-gamma",
            "version": "1.0",
            "fs": {"read_roots": [], "write_roots": [], "forbidden_paths": []},
            "net": {"outbound": "denied"},
            "proc": {"allowed_binaries": [], "forbidden_binaries": []},
            "tools": {"allowed": [], "forbidden": ["gamma"]},
            "authority": {
                "may_promote": False,
                "may_deploy": False,
                "may_modify_policies": False,
            },
        },
    )
    _write_plan(
        sess,
        [{"n": 1, "title": "blocked", "tool": "gamma", "sandbox_profile": "deny-gamma"}],
    )
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    # sandbox.deny present, no dispatcher activity
    assert "sandbox.deny" in types
    assert "tool.invocation.started" not in types
    assert "tool.invocation.completed" not in types
    assert "tool.invocation.failed" not in types


def test_sandbox_runtime_unavailable_skips_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("gamma", TRUE_BIN)], [_cap_entry("gamma")])
    _write_sandbox_profile(
        proj,
        "net-denied",
        {
            "id": "net-denied",
            "version": "1.0",
            "fs": {"read_roots": [], "write_roots": [], "forbidden_paths": []},
            "net": {"outbound": "denied"},
            "proc": {"allowed_binaries": [], "forbidden_binaries": []},
            "tools": {"allowed": ["gamma"], "forbidden": []},
            "authority": {
                "may_promote": False,
                "may_deploy": False,
                "may_modify_policies": False,
            },
        },
    )
    _write_plan(
        sess,
        [{"n": 1, "title": "needs-os-sandbox", "tool": "gamma", "sandbox_profile": "net-denied"}],
    )
    monkeypatch.setattr(gogogo_mod, "is_sandbox_exec_available", lambda: False)
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "sandbox.runtime_unavailable" in types
    assert "tool.invocation.started" not in types
    assert "tool.invocation.completed" not in types
    runtime = [e for e in events if e["type"] == "sandbox.runtime_unavailable"][-1]
    assert runtime["details"]["required_axes"] == ["net"]


def test_sandbox_runtime_disabled_allows_dispatch_with_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    (proj / ".ai" / "ssot.yaml").write_text(
        yaml.safe_dump({
            "version": "1.0",
            "paths": {"state": "${ai_root}/state"},
            "sandbox": {"runtime_enforcement_enabled": False},
        })
    )
    _write_registry(proj, [_tool_entry("gamma", TRUE_BIN)], [_cap_entry("gamma")])
    _write_sandbox_profile(
        proj,
        "net-denied",
        {
            "id": "net-denied",
            "version": "1.0",
            "fs": {"read_roots": [], "write_roots": [], "forbidden_paths": []},
            "net": {"outbound": "denied"},
            "proc": {"allowed_binaries": [], "forbidden_binaries": []},
            "tools": {"allowed": ["gamma"], "forbidden": []},
            "authority": {
                "may_promote": False,
                "may_deploy": False,
                "may_modify_policies": False,
            },
        },
    )
    _write_plan(
        sess,
        [{"n": 1, "title": "agent-hosted", "tool": "gamma", "sandbox_profile": "net-denied"}],
    )
    monkeypatch.setattr(gogogo_mod, "is_sandbox_exec_available", lambda: False)
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "sandbox.runtime_disabled" in types
    assert "sandbox.runtime_unavailable" not in types
    assert "tool.invocation.started" in types
    disabled = [e for e in events if e["type"] == "sandbox.runtime_disabled"][-1]
    assert disabled["details"]["required_axes"] == ["net"]


def test_missing_sandbox_profile_skips_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("gamma", TRUE_BIN)], [_cap_entry("gamma")])
    _write_plan(
        sess,
        [{"n": 1, "title": "missing-profile", "tool": "gamma", "sandbox_profile": "missing"}],
    )
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "sandbox.profile_missing" in types
    assert "tool.invocation.started" not in types


# ─── (e) tool_args + tool_timeout schema honored ─────────────────────


def test_tool_args_and_timeout_forwarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanity: tool_args is forwarded to the subprocess argv."""
    proj, sess = _seed_at_do(tmp_path)
    # /bin/sh -c "exit 0" — but we use /bin/true for simplicity and pass an
    # unused arg. dispatch_tool joins record.bin + args; /bin/true accepts
    # and ignores args.
    _write_registry(proj, [_tool_entry("delta", TRUE_BIN)], [_cap_entry("delta")])
    _write_plan(
        sess,
        [
            {
                "n": 1,
                "title": "with-args",
                "tool": "delta",
                "tool_args": ["--noop", "ignored"],
                "tool_timeout": 5,
            }
        ],
    )
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    started = [e for e in events if e["type"] == "tool.invocation.started"]
    assert len(started) == 1
    argv = started[0]["details"]["argv"]
    # argv = bin tokens + args
    assert "--noop" in argv
    assert "ignored" in argv


# ─── P5 PolicyEngine gating wire (Phase 5 acceptance) ────────────────


def _write_trinity_policy_with_forbidden_tools(proj: Path, forbidden: List[str]) -> None:
    policy_dir = proj / ".ai" / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "trinity_policy.yaml").write_text(
        "policy_engine:\n"
        "  version: '1.0'\n"
        "  boundaries:\n"
        f"    forbidden_tools: {forbidden}\n",
        encoding="utf-8",
    )


def test_policy_deny_blocks_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase 5 acceptance: 'Policy can block tool use'.

    With forbidden_tools=['alpha'], dispatching tool=alpha must:
      - emit `policy.refused` audit row BEFORE dispatch
      - NOT emit `tool.invocation.started` (tool never runs)
      - raise typer.Exit(1)
    """
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("alpha", TRUE_BIN)], [_cap_entry("alpha")])
    _write_trinity_policy_with_forbidden_tools(proj, ["alpha"])
    _write_plan(sess, [{"n": 1, "title": "blocked", "tool": "alpha"}])
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    # policy.refused must be present
    assert "policy.refused" in types
    # tool.invocation.started / completed / failed MUST NOT appear — tool never ran
    assert "tool.invocation.started" not in types
    assert "tool.invocation.completed" not in types
    assert "tool.invocation.failed" not in types

    refused = [e for e in events if e["type"] == "policy.refused"]
    assert len(refused) == 1
    details = refused[0]["details"]
    # Spec §5.3 normative field shape
    assert details["verdict"] == "deny"
    assert details["reason"] == "illegal_target"
    assert details["rule_id"] == "boundaries.forbidden_tools"
    assert details["target"] == "alpha"
    assert details["actor"] == "executor"
    assert details["action_kind"] == "tool_invoke"
    assert "query_id" in details
    assert "engine_version" in details


def test_policy_allow_proceeds_to_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no forbidden rule, tool still runs and policy.refused is absent."""
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("alpha", TRUE_BIN)], [_cap_entry("alpha")])
    _write_trinity_policy_with_forbidden_tools(proj, ["bandit"])  # not alpha
    _write_plan(sess, [{"n": 1, "title": "allowed", "tool": "alpha"}])
    monkeypatch.chdir(proj)

    _run("step_complete", False)

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "policy.refused" not in types
    assert "tool.invocation.started" in types
    assert "tool.invocation.completed" in types


def test_policy_query_emitted_before_dispatch_source_check() -> None:
    """Source-level: policy_query(...) call MUST appear before dispatch_tool(...)."""
    import inspect
    from cli.commands import gogogo as gogogo_mod
    source = inspect.getsource(gogogo_mod)
    pos_query = source.find("policy_query(")
    pos_dispatch = source.find("dispatch_tool(")
    assert pos_query > 0, "policy_query call missing"
    assert pos_dispatch > 0, "dispatch_tool call missing"
    assert pos_query < pos_dispatch, (
        f"policy_query at {pos_query} must precede dispatch_tool at {pos_dispatch}"
    )


def test_no_post_dispatch_policy_queried_emission() -> None:
    """The old advisory POST-dispatch `policy.queried` emission has been removed
    (gating is the new contract; advisory was the POC)."""
    import inspect
    from cli.commands import gogogo as gogogo_mod
    source = inspect.getsource(gogogo_mod)
    assert "policy.queried" not in source, (
        "policy.queried POST-dispatch emission should be removed (replaced by "
        "policy.refused PRE-dispatch gate)"
    )


# ─── §5.4 forbidden_path special form — forbidden_pattern surfaced ───


def _write_trinity_policy_with_forbidden_paths(
    proj: Path, pattern: str, gate_id: str = "gate.test"
) -> None:
    policy_dir = proj / ".ai" / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "trinity_policy.yaml").write_text(
        f"policy_engine:\n"
        f"  version: '1.0'\n"
        f"  boundaries:\n"
        f"    forbidden_mutation_paths:\n"
        f"      - pattern: '{pattern}'\n"
        f"        rationale: 'test'\n"
        f"        applies_to_actors: ['ai', 'tool', 'kernel']\n"
        f"        gate_id: '{gate_id}'\n",
        encoding="utf-8",
    )


def test_policy_refused_carries_forbidden_pattern_top_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec §5.4 — forbidden_path deny → policy.refused.details.forbidden_pattern at top."""
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("alpha", TRUE_BIN)], [_cap_entry("alpha")])
    # Pattern matches tool_name=alpha (gogogo passes tool name as target.value)
    _write_trinity_policy_with_forbidden_paths(proj, "alpha", "gate.alpha_blocked")
    _write_plan(sess, [{"n": 1, "title": "blocked-by-path", "tool": "alpha"}])
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 1

    events = _chain_events(proj)
    refused = [e for e in events if e["type"] == "policy.refused"]
    assert len(refused) == 1
    details = refused[0]["details"]
    assert details["reason"] == "forbidden_path"
    assert details["forbidden_pattern"] == "alpha"
    assert details["gate_id"] == "gate.alpha_blocked"


# ─── §6.5 NEEDS_HUMAN flow — policy.gate_required + packet ───────────


def _write_trinity_policy_with_critical_gate(
    proj: Path, gate_id: str, action_kinds: list
) -> None:
    policy_dir = proj / ".ai" / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "trinity_policy.yaml").write_text(
        f"policy_engine:\n"
        f"  version: '1.0'\n"
        f"  boundaries:\n"
        f"    critical_gates:\n"
        f"      - gate_id: '{gate_id}'\n"
        f"        action_kinds: {action_kinds}\n",
        encoding="utf-8",
    )


def test_critical_gate_emits_policy_gate_required_and_writes_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec §6.5 NEEDS_HUMAN flow:
      - emit policy.gate_required (NOT policy.refused)
      - write packet template to <session>/GATE/<gate_id>_packet.yaml
      - no tool.invocation.started
      - Exit(0) — kernel pauses, not fails"""
    proj, sess = _seed_at_do(tmp_path)
    _write_registry(proj, [_tool_entry("alpha", TRUE_BIN)], [_cap_entry("alpha")])
    _write_trinity_policy_with_critical_gate(
        proj, "gate.alpha_review", ["tool_invoke"]
    )
    _write_plan(sess, [{"n": 1, "title": "gated", "tool": "alpha"}])
    monkeypatch.chdir(proj)

    with pytest.raises(typer.Exit) as exc_info:
        _run("step_complete", False)
    assert exc_info.value.exit_code == 0  # pause, not fail

    events = _chain_events(proj)
    types = [e["type"] for e in events]
    assert "policy.gate_required" in types
    assert "policy.refused" not in types  # distinct from deny path
    assert "tool.invocation.started" not in types

    gate_evt = [e for e in events if e["type"] == "policy.gate_required"][0]
    details = gate_evt["details"]
    assert details["verdict"] == "NEEDS_HUMAN"
    assert details["reason"] == "human_gate_required"
    assert details["gate_id"] == "gate.alpha_review"
    assert "ddd_packet_path" in details

    # Packet file exists with required spec §6.2 fields
    packet_path = sess / "GATE" / "gate.alpha_review_packet.yaml"
    assert packet_path.is_file()
    content = yaml.safe_load(packet_path.read_text())
    for required_key in ("decided_by", "human_id", "gate_id", "query_id", "decision", "rationale"):
        assert required_key in content
    assert content["gate_id"] == "gate.alpha_review"
