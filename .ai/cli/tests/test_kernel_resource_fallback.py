"""Thin-client kernel-source fallback for project-local .ai resources (P0-3).

Linked client projects strip most of the vendored .ai tree; every
kernel-default resource loader must fall back loudly to the kernel's own
copy. Companion of retro-0055 (doctor), retro-0061 (templates),
retro-0063 (ritual packs).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.budget import Budget
from cli.core.kernel_resource import (
    FALLBACK_RESOURCES,
    kernel_ai_root,
    resolve_ai_resource,
)
from cli.core.policy_engine import load_policy_doc
from cli.core.verifier import load_rules


@pytest.fixture()
def thin_root(tmp_path: Path) -> Path:
    """A thin-client project root: .ai exists but no policies/graphs."""
    (tmp_path / ".ai").mkdir()
    return tmp_path


def test_resolver_prefers_project_local(thin_root: Path, capsys) -> None:
    rel = "policies/verifier-rules.yaml"
    local = thin_root / ".ai" / "policies"
    local.mkdir(parents=True)
    (local / "verifier-rules.yaml").write_text("verifier_rules: {}\n")
    path, source = resolve_ai_resource(thin_root, rel, label="verifier")
    assert source == "project"
    assert path == local / "verifier-rules.yaml"
    assert capsys.readouterr().err == ""  # no note when project-local wins


def test_resolver_falls_back_to_kernel_with_loud_note(thin_root: Path, capsys) -> None:
    path, source = resolve_ai_resource(
        thin_root, "policies/verifier-rules.yaml", label="verifier"
    )
    assert source == "kernel"
    assert path == kernel_ai_root() / "policies" / "verifier-rules.yaml"
    assert path.is_file()
    err = capsys.readouterr().err
    assert "using kernel default" in err


def test_resolver_missing_both(thin_root: Path) -> None:
    path, source = resolve_ai_resource(
        thin_root, "policies/does-not-exist.yaml", label="x"
    )
    assert path is None
    assert source == "missing"


def test_load_rules_thin_client_uses_kernel_rules(thin_root: Path) -> None:
    rules = load_rules(thin_root)
    assert "verifier_rules" in rules
    assert "step_complete" in rules["verifier_rules"]


def test_budget_thin_client_uses_kernel_budget(thin_root: Path) -> None:
    budget = Budget.for_project(thin_root)
    caps = budget.effective_caps("standard")
    assert caps.get("max_duration_minutes", 0) > 0


def test_graph_loader_thin_client_uses_kernel_graph(thin_root: Path) -> None:
    from cli.core.kernel_resource import resolve_ai_resource as r

    path, source = r(thin_root, "graphs/standard.yaml", label="graph:standard")
    assert source == "kernel"
    assert path.is_file()


def test_policy_doc_thin_client_uses_kernel_baseline(thin_root: Path, capsys) -> None:
    doc = load_policy_doc(thin_root)
    # kernel ships a baseline trinity_policy.yaml — thin client gets it
    assert isinstance(doc, dict)
    assert doc != {}
    assert "using kernel default" in capsys.readouterr().err


def test_policy_doc_corrupt_is_loud_default_deny(thin_root: Path, capsys) -> None:
    pol_dir = thin_root / ".ai" / "policies"
    pol_dir.mkdir(parents=True)
    (pol_dir / "trinity_policy.yaml").write_text("{: not yaml :::")
    doc = load_policy_doc(thin_root)
    assert doc == {}
    err = capsys.readouterr().err
    assert "DEFAULT-DENY" in err


def test_kernel_ships_every_declared_fallback_resource() -> None:
    """Guard: FALLBACK_RESOURCES must point at real kernel files/dirs —
    otherwise doctor resources reports nonsense and fallbacks silently die."""
    for label, rel in FALLBACK_RESOURCES:
        assert (kernel_ai_root() / rel).exists(), (label, rel)


def test_ssot_is_not_fallback_eligible() -> None:
    """retro-0056: ssot.yaml absence is a load-bearing signal. The fallback
    table must never include it."""
    rels = [rel for _label, rel in FALLBACK_RESOURCES]
    assert "ssot.yaml" not in rels
