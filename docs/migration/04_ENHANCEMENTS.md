---
title: "Star's Final Enhancements"
status: locked
last-updated: 2026-04-28
audience: "Executor (during Commit 1 + 2)"
purpose: "Two safety nets caught after refined plan was drafted. Apply during Commit 1 and Commit 2."
---

# 4. Star's 2 Final Enhancements

> Approved 2026-04-28 — apply during Commit 1 (relative paths) + Commit 2 (YAML validation)

## 4.1 YAML Validation Hook (Commit 2)

### Problem prevented
ใน Commit 2 เราสร้าง YAML ที่ซับซ้อน 4 ไฟล์:
- `.ai/policies/verifier-rules.yaml` (Pyramid 4 layers)
- `.ai/policies/loop-budget.yaml` (escalation rules)
- `.ai/graphs/standard.yaml` (8+ transitions)
- `.ai/graphs/deploy.yaml` (deploy subgraph)

ถ้า indentation ผิด หรือ field name typo → kernel CLI โหลดไม่ได้ตอน runtime → silent failure ที่จะเจอตอน Phase 4-6 (verify-cli, loop, graph runtime)

### Solution

ไฟล์: `trinity_v2/.ai/cli/tests/test_yaml_valid.py`

```python
"""YAML structural validation — Star Enhancement §3.1.

Catches:
- Indentation errors (yaml.safe_load fails)
- Missing decided_by in graph transitions (D10)
- Invalid decided_by values
- Pyramid layer naming typos
- Loop budget missing required fields
"""
import glob, os
import pytest
import yaml


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _path(rel):
    return os.path.join(REPO_ROOT, rel)


@pytest.mark.parametrize("path", sorted(
    glob.glob(_path(".ai/policies/*.yaml")) +
    glob.glob(_path(".ai/graphs/*.yaml"))
))
def test_yaml_loadable(path):
    """Every YAML in policies/ and graphs/ must parse cleanly."""
    with open(path) as f:
        yaml.safe_load(f)


def test_graphs_have_decided_by():
    """D10: every transition must declare decided_by."""
    valid_authorities = {"verifier", "policy", "human", "kernel"}
    for path in sorted(glob.glob(_path(".ai/graphs/*.yaml"))):
        with open(path) as f:
            graph = yaml.safe_load(f) or {}
        for i, t in enumerate(graph.get("transitions", [])):
            assert "decided_by" in t, \
                f"{path}: transition #{i} missing decided_by: {t}"
            assert t["decided_by"] in valid_authorities, \
                f"{path}: invalid decided_by '{t['decided_by']}' in {t}"


def test_verifier_rules_pyramid_structure():
    """D8: verifier-rules.yaml must define Pyramid 4 layers."""
    with open(_path(".ai/policies/verifier-rules.yaml")) as f:
        rules = yaml.safe_load(f)
    pyramid = rules.get("pyramid", {})
    required_layers = {
        "layer_1_deterministic",
        "layer_2_policy",
        "layer_3_llm_judge",
        "layer_4_human",
    }
    assert set(pyramid.keys()) >= required_layers, \
        f"Pyramid missing layers: {required_layers - set(pyramid.keys())}"
    assert pyramid["layer_3_llm_judge"]["enabled"] is False, \
        "layer_3_llm_judge must be disabled by default (gated)"


def test_loop_budget_has_real_values():
    """D11: loop-budget.yaml must have real numeric values, not zero."""
    with open(_path(".ai/policies/loop-budget.yaml")) as f:
        budget = yaml.safe_load(f)
    db = budget.get("default_budget", {})
    for field in ("max_iterations", "max_duration_minutes", "max_tool_calls"):
        assert field in db, f"loop-budget missing {field}"
        assert isinstance(db[field], int) and db[field] > 0, \
            f"loop-budget.{field} must be positive int, got {db[field]}"
```

### Acceptance
`pytest cli/tests/test_yaml_valid.py -v` → all 4 test functions pass (parametrized count varies with file count)

### Why this hook is non-negotiable
- Catches "stub vs real values" mismatch (D11)
- Catches missing `decided_by` (D10)
- Catches wrong layer names in Pyramid (D8)
- Cheap to run on every `pytest`

---

## 4.2 Relative-Path ssot.yaml (Commit 1)

### Problem prevented
TRINITY_LEGACY/.ai/ssot.yaml อาจมี absolute paths (`<user-home>/...`) จากการ debug เก่า. ถ้า copy ตรงๆ → kernel CLI ของ trinity_v2 จะหลุดไปอ่าน/เขียน path นอก project = sandbox escape

### Solution

หลัง copy ssot.yaml จาก TRINITY_LEGACY/.ai HEAD → **บังคับ verify**:

```bash
# In Commit 1, after copy:
SSOT="trinity_v2/.ai/ssot.yaml"

# Step 1: ensure project_root is "."
grep -E '^\s*project_root:\s*"\."' "$SSOT" || {
    echo "FAIL: project_root must be \".\" (relative)"
    exit 1
}

# Step 2: no absolute /Users/ paths
if grep -E '<user-home>/home/|/root/' "$SSOT"; then
    echo "FAIL: ssot.yaml contains absolute paths"
    exit 1
fi

# Step 3: every path uses ${project_root} interpolation
grep -E 'path|root|dir' "$SSOT" | grep -v -E '\$\{project_root\}|"\."|^\s*#' && {
    echo "WARN: paths not using \${project_root}; review manually"
}
```

### What "correct" ssot.yaml looks like

```yaml
version: "1.0"

paths:
  project_root: "."                              # ← runtime detect
  ai_root: "${project_root}/.ai"
  policies: "${ai_root}/policies"
  schemas: "${ai_root}/schemas"
  templates: "${ai_root}/templates"
  memory: "${ai_root}/memory"
  sessions: "${ai_root}/sessions"
  active_session: "${sessions}/active"
  audit: "${ai_root}/audit"
  state: "${ai_root}/state"
  cli: "${ai_root}/cli"

# ← NO absolute paths anywhere
# ← project_root is auto-detected by Trinity CLI at startup
#    (typically: directory containing .ai/ folder)
```

### Acceptance (Commit 1 sub-task 4 must include this)

- ✅ `grep "/Users/" .ai/ssot.yaml` → 0 matches
- ✅ `grep '^\s*project_root:\s*"\."' .ai/ssot.yaml` → 1 match
- ✅ All path values use `${project_root}` or `${ai_root}` etc.

### Why
- **Portability:** Anyone clone trinity_v2 anywhere → just works
- **Sandbox safety:** Kernel CLI confined to project directory
- **Spec compliance:** `00b_BOOTSTRAP_PACK.md` template uses placeholders

---

## 4.3 Wiring into Commit Plan

| Enhancement | Applied in | Sub-task # | Verified by |
|-------------|------------|-----------|-------------|
| 4.1 YAML validation hook | Commit 2 | sub-task 12 | `pytest cli/tests/test_yaml_valid.py` |
| 4.2 Relative-path ssot.yaml | Commit 1 | sub-task 2 + 4 | grep checks above |

Both already integrated in [`03_COMMIT_PLAN.md`](03_COMMIT_PLAN.md). This document is the rationale + reference implementation.
