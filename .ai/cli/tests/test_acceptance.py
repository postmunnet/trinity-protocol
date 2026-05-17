"""R24 — verifier exit-code leniency tests.

Pre-fix: case (b) FAILS — `grep -c` style commands that exit 1 on no match
trigger false-negative gate failures even when stdout is correct.

Post-fix: case (b) PASSES — when expect_exit is implicit AND a stdout-check
is present, the verifier should not enforce exit_code == 0.

Covers all 4 combinations to lock backwards-compat:
  (a) explicit expect_exit, no stdout-check
  (b) implicit expect_exit, stdout-check present (BUG case)
  (c) explicit expect_exit, stdout-check present
  (d) implicit expect_exit, no stdout-check (default-strict still enforced)
"""
from __future__ import annotations

from pathlib import Path

import yaml

from cli.core.acceptance import (
    AcceptanceItem,
    load_acceptance,
    run_acceptance,
)


def _make_item(tmp_path: Path, **fields) -> AcceptanceItem:
    """Round-trip through load_acceptance so explicit-vs-default is preserved."""
    base = {"id": "T1", "description": "test", "command": "true"}
    base.update(fields)
    yaml_file = tmp_path / "acceptance.yaml"
    yaml_file.write_text(yaml.safe_dump({"acceptance": [base]}))
    return load_acceptance(yaml_file)[0]


def test_case_a_explicit_exit_no_stdout_check(tmp_path: Path) -> None:
    """Explicit expect_exit + no stdout-check — strict exit check."""
    item = _make_item(tmp_path, command="true", expect_exit=0)
    result = run_acceptance(item, tmp_path)
    assert result.passed, f"expected PASS, got {result.failure_reasons}"

    item_fail = _make_item(tmp_path, command="false", expect_exit=0)
    result_fail = run_acceptance(item_fail, tmp_path)
    assert not result_fail.passed
    assert any("exit_code" in r for r in result_fail.failure_reasons)


def test_case_b_implicit_exit_with_stdout_check(tmp_path: Path) -> None:
    """BUG case (R24): grep -c style — implicit exit + stdout-check.

    `grep -c "X" empty.txt` exits 1 but stdout is correct "0".
    Pre-fix: FAILS (exit_code 1 != expected 0).
    Post-fix: PASSES (exit check skipped because stdout-check is sufficient).
    """
    item = _make_item(
        tmp_path,
        command="bash -c 'echo 0; exit 1'",
        expect_stdout_strip="0",
    )
    result = run_acceptance(item, tmp_path)
    assert result.passed, (
        f"R24 regression — implicit-exit + stdout-check should PASS, "
        f"got failures: {result.failure_reasons}"
    )


def test_case_c_explicit_exit_with_stdout_check(tmp_path: Path) -> None:
    """Explicit expect_exit honored even when stdout-check is present."""
    item = _make_item(
        tmp_path,
        command="bash -c 'echo 0; exit 1'",
        expect_exit=1,
        expect_stdout_strip="0",
    )
    result = run_acceptance(item, tmp_path)
    assert result.passed, f"explicit exit=1 should PASS, got {result.failure_reasons}"

    item_mismatch = _make_item(
        tmp_path,
        command="bash -c 'echo 0; exit 2'",
        expect_exit=1,
        expect_stdout_strip="0",
    )
    result_mismatch = run_acceptance(item_mismatch, tmp_path)
    assert not result_mismatch.passed, "explicit exit mismatch must FAIL"
    assert any("exit_code" in r for r in result_mismatch.failure_reasons)


def test_case_d_implicit_exit_no_stdout_check_default_strict(tmp_path: Path) -> None:
    """Implicit expect_exit + no stdout-check → default-strict (exit must be 0).

    This locks backwards-compat: bare commands without stdout-check
    must still default to exit==0 (the historical behavior).
    """
    item_pass = _make_item(tmp_path, command="true")
    result_pass = run_acceptance(item_pass, tmp_path)
    assert result_pass.passed

    item_fail = _make_item(tmp_path, command="false")
    result_fail = run_acceptance(item_fail, tmp_path)
    assert not result_fail.passed, (
        "implicit exit + no stdout-check must still enforce exit==0"
    )
    assert any("exit_code" in r for r in result_fail.failure_reasons)


def test_load_acceptance_preserves_explicit_vs_default(tmp_path: Path) -> None:
    """Loader must distinguish 'expect_exit specified' from 'omitted'."""
    yaml_file = tmp_path / "acceptance.yaml"
    yaml_file.write_text(yaml.safe_dump({
        "acceptance": [
            {"id": "explicit", "description": "x", "command": "true", "expect_exit": 0},
            {"id": "implicit", "description": "x", "command": "true"},
        ]
    }))
    items = load_acceptance(yaml_file)
    assert len(items) == 2
    explicit, implicit = items
    assert explicit.expect_exit == 0
    assert implicit.expect_exit is None, (
        "omitted expect_exit must remain None to preserve "
        "explicit-vs-default distinction"
    )
