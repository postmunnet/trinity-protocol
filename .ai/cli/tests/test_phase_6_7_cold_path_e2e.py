"""Phase 16 — Phase 6+7 cold-path end-to-end integration tests.

Tests the composition of sandbox_gate + lease_lifecycle + presentation +
ddd_artifacts + root_of_trust against edge cases the warm-path tests skip.

No new production code — purely cross-module integration.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from cli.core.audit import AuditChain
from cli.core.ddd_artifacts import (
    make_decision_packet,
    write_decision_packet,
)
from cli.core.ddd_contract import validate_decision_packet
from cli.core.presentation_renderer import render_close_pack
from cli.core.root_of_trust_helper import (
    make_genesis_manifest,
    make_layer0_entry,
    verify_layer0_against_manifest,
)
from cli.core.sandbox_contract import (
    FsCapability,
    NetCapability,
    ProcCapability,
    SandboxProfile,
    ToolsCapability,
)
from cli.core.sandbox_gate import (
    SANDBOX_DENY_EVENT_TYPE,
    run_sandbox_gated_lifecycle,
)
from cli.core.tool_invocation_guard import (
    DENIED_EVENT_TYPE,
    PROPOSED_EVENT_TYPE,
)
from cli.core.tool_registry import load_registry


# ─── shared fixtures ────────────────────────────────────────────────


def _write_registry(root: Path, tools: List[str]) -> None:
    (root / ".ai").mkdir(parents=True, exist_ok=True)
    (root / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "tools": [
                    {
                        "name": n,
                        "description": f"{n} desc",
                        "path": f"/fake/{n}",
                        "bin": f"/fake/{n}/bin",
                        "schema_version": "1",
                        "contract_version": "1.0",
                        "capabilities": ["x"],
                        "policy_default": "safe",
                    }
                    for n in tools
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (root / ".ai" / "tools.capabilities.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "status": "authoritative",
                "authoritative": True,
                "capability_vocabulary": {
                    "fs": ["fs.read", "fs.write", "fs.delete"],
                    "net": ["net.outbound", "net.allowlist"],
                    "proc": ["proc.exec", "proc.spawn"],
                    "audit": ["audit.read", "audit.append"],
                    "policy": ["policy.read"],
                    "ddd": ["ddd.propose", "ddd.decide"],
                    "tool": ["tool.invoke"],
                },
                "tools": [
                    {
                        "name": n,
                        "required_capabilities": ["fs.read"],
                        "optional_capabilities": [],
                        "default_tier_requirement": "WARM",
                        "notes": "",
                    }
                    for n in tools
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _profile(allowed: List[str]) -> SandboxProfile:
    return SandboxProfile(
        id="p_e2e",
        version="1.0",
        fs=FsCapability(),
        net=NetCapability(),
        proc=ProcCapability(),
        tools=ToolsCapability(allowed=allowed),
    )


def _chain(tmp_path: Path) -> AuditChain:
    return AuditChain(tmp_path / ".ai" / "audit" / "events.ndjson")


# ─── A1 sandbox denies registry-declared tool ───────────────────────


def test_sandbox_denies_registry_declared_tool(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["alpha"])
    reg = load_registry(tmp_path)
    chain = _chain(tmp_path)
    profile = _profile(allowed=[])  # tools allowed=[] → sandbox denies any tool

    result = run_sandbox_gated_lifecycle(
        session_id="s", step_id="S1", tool_name="alpha",
        registry=reg, chain=chain, profile=profile,
    )
    assert result.success is False
    types = [e["type"] for e in chain.iter_events()]
    assert SANDBOX_DENY_EVENT_TYPE in types
    assert PROPOSED_EVENT_TYPE not in types
    assert DENIED_EVENT_TYPE not in types


# ─── A2 sandbox allows but registry rejects unknown ─────────────────


def test_sandbox_allows_but_registry_unknown_tool_denied(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["alpha"])
    reg = load_registry(tmp_path)
    chain = _chain(tmp_path)
    # Sandbox allows the requested name; registry doesn't have it.
    profile = _profile(allowed=["ghost"])

    result = run_sandbox_gated_lifecycle(
        session_id="s", step_id="S1", tool_name="ghost",
        registry=reg, chain=chain, profile=profile,
    )
    assert result.success is False
    types = [e["type"] for e in chain.iter_events()]
    assert DENIED_EVENT_TYPE in types
    assert SANDBOX_DENY_EVENT_TYPE not in types


# ─── A3 happy path lease_id propagation ─────────────────────────────


def test_lease_id_appears_in_proposed_envelope(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["alpha"])
    reg = load_registry(tmp_path)
    chain = _chain(tmp_path)
    profile = _profile(allowed=["alpha"])

    result = run_sandbox_gated_lifecycle(
        session_id="s", step_id="S1", tool_name="alpha",
        registry=reg, chain=chain, profile=profile,
    )
    assert result.success is True
    proposed = [e for e in chain.iter_events() if e["type"] == PROPOSED_EVENT_TYPE]
    assert proposed[0]["details"]["lease_id"] == result.lifecycle.lease.lease_id


# ─── A4 chain integrity over 12-step alternation ────────────────────


def test_chain_validates_over_long_alternation(tmp_path: Path) -> None:
    _write_registry(tmp_path, ["alpha", "beta"])
    reg = load_registry(tmp_path)
    chain = _chain(tmp_path)

    allow_ab = _profile(allowed=["alpha", "beta"])
    allow_with_ghost = _profile(allowed=["alpha", "beta", "ghost"])
    sand_deny = _profile(allowed=[])

    for i in range(12):
        if i % 3 == 0:
            tool, profile = "alpha", allow_ab          # propose
        elif i % 3 == 1:
            tool, profile = "alpha", sand_deny         # sandbox.deny
        else:
            # Sandbox permits ghost, but registry doesn't know it →
            # tool.invocation_denied with reason=unknown_tool.
            tool, profile = "ghost", allow_with_ghost
        run_sandbox_gated_lifecycle(
            session_id="s", step_id=f"S{i}", tool_name=tool,
            registry=reg, chain=chain, profile=profile,
        )

    chain.validate()
    events = list(chain.iter_events())
    assert len(events) == 12
    type_counts = {t: 0 for t in (PROPOSED_EVENT_TYPE, SANDBOX_DENY_EVENT_TYPE, DENIED_EVENT_TYPE)}
    for e in events:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
    assert type_counts[PROPOSED_EVENT_TYPE] == 4
    assert type_counts[SANDBOX_DENY_EVENT_TYPE] == 4
    assert type_counts[DENIED_EVENT_TYPE] == 4


# ─── A5 DDD round-trip ──────────────────────────────────────────────


def test_ddd_decision_packet_round_trip(tmp_path: Path) -> None:
    sess = tmp_path / "sess"
    sess.mkdir()
    packet = make_decision_packet(
        session_id="0001",
        proposing_role="planner",
        requested_action="promote",
        verifier_reports=[{"path": ".state/verify_dev.json", "hash": "a" * 64}],
        summary="Ship v1.0",
        convergence=["all gates green"],
    )
    out = write_decision_packet(sess, packet)
    reread = json.loads(out.read_text())
    validate_decision_packet(reread)
    assert reread["presentation"]["cognitive_protocol_version"] == "v1.0.1"


# ─── A6 presentation renderer end-to-end ────────────────────────────


def test_presentation_renderer_includes_all_sections(tmp_path: Path) -> None:
    sess = tmp_path / ".ai" / "sessions" / "0001_e2e"
    (sess / "THINK").mkdir(parents=True)
    (sess / "THINK" / "02_SCOPE.md").write_text("# Scope\n\nShip P16.")
    (sess / "THINK" / "03_ACCEPTANCE.md").write_text("A1 PASS\nA2 PASS")
    (sess / "THINK" / "RETRO.md").write_text("Smooth run.")

    audit_p = tmp_path / ".ai" / "audit" / "events.ndjson"
    audit_p.parent.mkdir(parents=True)
    audit_p.write_text(json.dumps({
        "ts": "2026-05-16T02:30:00Z",
        "type": "sss.opened",
        "details": {"session_id": "0001_e2e"},
    }) + "\n")

    md = render_close_pack(sess, audit_chain_path=audit_p)
    assert "# Close Pack" in md
    assert "Ship P16." in md
    assert "A1 PASS" in md
    assert "Smooth run." in md
    assert "sss.opened" in md


# ─── A7 root of trust verify happy + tamper ────────────────────────


def test_root_of_trust_verify_happy_and_tamper(tmp_path: Path) -> None:
    (tmp_path / "docs" / "constitution").mkdir(parents=True)
    c = tmp_path / "docs" / "constitution" / "TRINITY_CONSTITUTION_V1.md"
    c.write_text("Constitution v1 content.\n")
    entry = make_layer0_entry(
        path="docs/constitution/TRINITY_CONSTITUTION_V1.md",
        role="constitution",
        authority_class="founder",
        project_root=tmp_path,
    )
    m = make_genesis_manifest(asserted_by="operator:test", layer_0_artifacts=[entry])

    # Happy path
    results = verify_layer0_against_manifest(tmp_path, m)
    assert results[0]["ok"] is True
    assert results[0]["actual"] == hashlib.sha256(b"Constitution v1 content.\n").hexdigest()

    # Tamper path
    c.write_text("Constitution v1 TAMPERED.\n")
    results = verify_layer0_against_manifest(tmp_path, m)
    assert results[0]["ok"] is False
    assert results[0]["expected"] != results[0]["actual"]
