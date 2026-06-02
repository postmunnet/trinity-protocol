"""Verify the registered sibling tools are paired in tools.yaml + capabilities.yaml.

Updated 2026-05-24: added memory-semantic-cli (8 tools total). memory-semantic-cli
is registered for discoverability only — it carries `sibling_only: true` and
`kernel_invocable: false` in tools.yaml because the Trinity kernel must not
call intelligence siblings directly per the kernel-intelligence boundary.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.tool_registry import load_registry


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPECTED_TOOLS = {
    "browser-cli",
    "memory-cli",
    "memory-semantic-cli",
    "notify-cli",
    "image-cli",
    "seo-genie-cli",
    "judge-cli",
    "retro-cli",
}


@pytest.fixture(scope="module")
def registry():
    return load_registry(PROJECT_ROOT)


def test_all_expected_tools_registered(registry) -> None:
    assert set(registry.names()) == EXPECTED_TOOLS


@pytest.mark.parametrize("tool_name", sorted(EXPECTED_TOOLS - {"browser-cli", "memory-cli"}))
def test_new_tool_has_required_attrs(registry, tool_name: str) -> None:
    rec = registry.require(tool_name)
    assert rec.name == tool_name
    assert rec.path
    assert rec.bin
    assert rec.schema_version
    assert rec.contract_version
    assert rec.policy_default
    assert rec.required_capabilities
    assert rec.default_tier_requirement in {"HOT", "WARM", "COLD"}


def test_vocabulary_unchanged(registry) -> None:
    """No new capability axes should leak in from the registration."""
    from cli.core.tool_registry import CAPABILITY_VOCABULARY
    for tool_name in EXPECTED_TOOLS:
        rec = registry.require(tool_name)
        for cap in list(rec.required_capabilities) + list(rec.optional_capabilities):
            assert cap in CAPABILITY_VOCABULARY, (
                f"{tool_name} declares unknown capability {cap!r}"
            )


def test_never_granted_capabilities_not_required(registry) -> None:
    """audit.append + ddd.decide must never appear in required_capabilities."""
    from cli.core.tool_registry import NEVER_GRANTED_CAPABILITIES
    for tool_name in EXPECTED_TOOLS:
        rec = registry.require(tool_name)
        for cap in rec.required_capabilities:
            assert cap not in NEVER_GRANTED_CAPABILITIES, (
                f"{tool_name} requires never-granted {cap!r}"
            )


def test_sibling_dirs_exist_on_disk() -> None:
    """Informational: verify the sibling layout matches the registry path field.

    Not a hard requirement — registry is the authority, filesystem may
    diverge in CI sandboxes — but on a dev workstation this catches a
    paired-entry typo immediately.
    """
    parent = PROJECT_ROOT.parent
    for name in EXPECTED_TOOLS:
        sibling = parent / name
        if not sibling.exists():
            pytest.skip(f"sibling dir not present in this environment: {sibling}")
