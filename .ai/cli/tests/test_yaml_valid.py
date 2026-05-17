"""YAML structural validation — Star Enhancement §4.1.

Catches:
- Indentation / syntax errors (yaml.safe_load fails)
- Missing decided_by in graph transitions (D10)
- Invalid decided_by authority values
- Pyramid layer naming typos (D8)
- Loop budget missing required fields or zero values (D11)

Repo-root-relative path resolution so test runs the same whether invoked
from repo root or from .ai/.
"""
import glob
import os

import pytest
import yaml


# test file is at <repo>/.ai/cli/tests/test_yaml_valid.py — climb 4 levels
REPO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)


def _path(rel):
    return os.path.join(REPO_ROOT, rel)


@pytest.mark.parametrize(
    "path",
    sorted(
        glob.glob(_path(".ai/policies/*.yaml"))
        + glob.glob(_path(".ai/graphs/*.yaml"))
        + [_path(".ai/ssot.yaml"), _path(".ai/tools.yaml")]
    ),
)
def test_yaml_loadable(path):
    """Every YAML in policies/, graphs/, plus ssot.yaml and tools.yaml must parse cleanly."""
    with open(path) as f:
        yaml.safe_load(f)


def test_graphs_have_decided_by():
    """D10: every transition must declare decided_by from a closed authority set."""
    valid_authorities = {"verifier", "policy", "human", "kernel"}
    graph_paths = sorted(glob.glob(_path(".ai/graphs/*.yaml")))
    assert graph_paths, "no graph files found in .ai/graphs/"

    for path in graph_paths:
        with open(path) as f:
            graph = yaml.safe_load(f) or {}
        transitions = graph.get("transitions", [])
        assert transitions, f"{path}: no transitions defined"

        for i, t in enumerate(transitions):
            assert "decided_by" in t, \
                f"{path}: transition #{i} missing decided_by: {t}"
            assert t["decided_by"] in valid_authorities, \
                f"{path}: invalid decided_by '{t['decided_by']}' in {t}"


def test_verifier_rules_pyramid_structure():
    """D8: verifier-rules.yaml must define all 4 Pyramid layers; LLM judge disabled by default."""
    with open(_path(".ai/policies/verifier-rules.yaml")) as f:
        rules = yaml.safe_load(f)

    pyramid = rules.get("pyramid", {})
    required_layers = {
        "layer_1_deterministic",
        "layer_2_policy",
        "layer_3_llm_judge",
        "layer_4_human",
    }
    missing = required_layers - set(pyramid.keys())
    assert not missing, f"Pyramid missing layers: {missing}"

    assert pyramid["layer_3_llm_judge"]["enabled"] is False, \
        "layer_3_llm_judge must be disabled by default (gated, opt-in)"

    verdicts = set(rules.get("verdicts", []))
    assert verdicts == {"PASS", "RETRY", "NEEDS_HUMAN", "DEAD"}, \
        f"verdicts must be exactly the closed set; got {verdicts}"


def test_loop_budget_has_real_values():
    """D11: loop-budget.yaml must define positive integer caps for all 3 dimensions."""
    with open(_path(".ai/policies/loop-budget.yaml")) as f:
        budget = yaml.safe_load(f)

    db = budget.get("default_budget", {})
    for field in ("max_iterations", "max_duration_minutes", "max_tool_calls"):
        assert field in db, f"loop-budget missing {field}"
        assert isinstance(db[field], int) and db[field] > 0, \
            f"loop-budget.{field} must be positive int, got {db[field]!r}"

    escalation = budget.get("escalation", {})
    for trigger in (
        "on_iterations_exceeded",
        "on_duration_exceeded",
        "on_tool_calls_exceeded",
    ):
        assert escalation.get(trigger) == "NEEDS_HUMAN", \
            f"escalation.{trigger} must escalate to NEEDS_HUMAN"
