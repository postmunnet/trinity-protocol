"""Phase 1.5 — ai rrr executable gate tests.

Covers:

  Acceptance executor (core/acceptance.py)
    - load YAML
    - exit-code matching
    - stdout substring/strip matching
    - timeout handling
    - required vs non-required pass/fail aggregation

  Forbidden diff (core/forbidden_diff.py)
    - flags policies/schemas/specs/references
    - skips .ai/audit/events.ndjson (append-only)
    - flags other audit/ files
    - tolerates non-git contexts (return empty report)

  Metrics (core/metrics.py)
    - filters by session_id
    - aggregates transitions, gogogo verdicts, needs_human
    - duration computed from first/last ts

  rrr render helpers (commands/rrr.py)
    - _memory_retro_path mints valid sequential filename
    - _render_retro produces frontmatter + sections
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from cli.core.acceptance import (
    AcceptanceItem,
    load_acceptance,
    run_acceptance,
    run_all,
)
from cli.core.audit import AuditChain
from cli.core.forbidden_diff import check as check_forbidden, FORBIDDEN_PATTERNS
from cli.core.metrics import metrics_for_session
from cli.commands.rrr import _memory_retro_path, _render_retro


# ─────────── core/acceptance.py ───────────


def test_acceptance_load_and_run_pass(tmp_path: Path):
    yaml_path = tmp_path / "03_ACCEPTANCE.yaml"
    yaml_path.write_text(
        """
session: t
ritual: rrr-input
acceptance:
  - id: A1
    description: "echo hello returns 0"
    command: "echo hello"
    expect_exit: 0
    expect_stdout_contains: "hello"
    required: true
""",
        encoding="utf-8",
    )
    items = load_acceptance(yaml_path)
    assert len(items) == 1
    report = run_all(items, cwd=tmp_path)
    assert report.ok
    assert report.items[0].passed


def test_acceptance_exit_code_mismatch(tmp_path: Path):
    item = AcceptanceItem(
        id="A1", description="false", command="false", expect_exit=0
    )
    result = run_acceptance(item, cwd=tmp_path)
    assert not result.passed
    assert any("exit_code" in r for r in result.failure_reasons)


def test_acceptance_stdout_strip_match(tmp_path: Path):
    item = AcceptanceItem(
        id="A6",
        description="git diff count",
        command="echo '0'",
        expect_stdout_strip="0",
    )
    result = run_acceptance(item, cwd=tmp_path)
    assert result.passed


def test_acceptance_stdout_strip_mismatch(tmp_path: Path):
    item = AcceptanceItem(
        id="A6",
        description="echo wrong",
        command="echo '5'",
        expect_stdout_strip="0",
    )
    result = run_acceptance(item, cwd=tmp_path)
    assert not result.passed


def test_acceptance_timeout(tmp_path: Path):
    item = AcceptanceItem(
        id="slow",
        description="should time out",
        command="sleep 5",
        timeout_seconds=1,
    )
    result = run_acceptance(item, cwd=tmp_path)
    assert result.timed_out
    assert not result.passed


def test_acceptance_required_aggregation(tmp_path: Path):
    items = [
        AcceptanceItem(id="A", command="true", expect_exit=0, required=True, description=""),
        AcceptanceItem(id="B", command="false", expect_exit=0, required=False, description=""),
    ]
    report = run_all(items, cwd=tmp_path)
    # B failed but is not required → overall ok still True
    assert report.ok
    assert len(report.required_failures) == 0


def test_acceptance_required_failure_breaks_ok(tmp_path: Path):
    items = [
        AcceptanceItem(id="A", command="false", expect_exit=0, required=True, description=""),
    ]
    report = run_all(items, cwd=tmp_path)
    assert not report.ok
    assert len(report.required_failures) == 1


# ─────────── core/forbidden_diff.py ───────────


def _git_init_with_baseline(tmp: Path) -> None:
    """Create a tmp git repo with a baseline commit so HEAD diff works."""
    subprocess.run(["git", "init", "-b", "main"], cwd=str(tmp), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=str(tmp), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(tmp), check=True, capture_output=True)
    (tmp / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "seed.txt"], cwd=str(tmp), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=str(tmp), check=True, capture_output=True)


def test_forbidden_diff_clean(tmp_path: Path):
    _git_init_with_baseline(tmp_path)
    report = check_forbidden(tmp_path)
    assert report.ok
    assert report.violations == []


def test_forbidden_diff_flags_policy_write(tmp_path: Path):
    _git_init_with_baseline(tmp_path)
    (tmp_path / ".ai" / "policies").mkdir(parents=True)
    (tmp_path / ".ai" / "policies" / "loop-budget.yaml").write_text("v: 1")
    report = check_forbidden(tmp_path)
    assert not report.ok
    assert any(".ai/policies/" in v for v in report.violations)


def test_forbidden_diff_skips_audit_chain(tmp_path: Path):
    _git_init_with_baseline(tmp_path)
    (tmp_path / ".ai" / "audit").mkdir(parents=True)
    (tmp_path / ".ai" / "audit" / "events.ndjson").write_text(
        '{"ts":"x","type":"genesis","prev_hash":"0","details":{},"hash":"a"}\n'
    )
    report = check_forbidden(tmp_path)
    assert report.ok  # events.ndjson is excluded
    assert report.skipped_audit_chain


def test_forbidden_diff_flags_other_audit_file(tmp_path: Path):
    _git_init_with_baseline(tmp_path)
    (tmp_path / ".ai" / "audit").mkdir(parents=True)
    (tmp_path / ".ai" / "audit" / "secret.txt").write_text("oops")
    report = check_forbidden(tmp_path)
    assert not report.ok


def test_forbidden_diff_non_git_returns_empty(tmp_path: Path):
    # No git init → git diff returns empty; report should be ok
    report = check_forbidden(tmp_path)
    assert report.ok
    assert report.violations == []


def test_forbidden_pattern_coverage():
    """Hard-coded sanity check: the patterns cover all D1-listed roots."""
    samples = [
        ".ai/policies/safety.yaml",
        ".ai/schemas/x.schema.json",
        "docs/specs/05_FOO.md",
        "references/whatever",
        ".ai/audit/secret.txt",
    ]
    for s in samples:
        assert any(p.search(s) for p in FORBIDDEN_PATTERNS), s


# ─────────── core/metrics.py ───────────


def test_metrics_filters_by_session_id(tmp_path: Path):
    chain_path = tmp_path / "events.ndjson"
    chain = AuditChain(chain_path)
    chain.append("genesis", {})  # no session_id
    chain.append(
        "graph.transition",
        {"session_id": "S1", "from_state": "READY", "to_state": "THINK", "trigger": "sss", "decided_by": "kernel"},
    )
    chain.append(
        "graph.transition",
        {"session_id": "S2", "from_state": "READY", "to_state": "THINK", "trigger": "sss", "decided_by": "kernel"},
    )
    chain.append(
        "gogogo.step_passed",
        {"session_id": "S1", "verifier_verdict": "PASS"},
    )
    m = metrics_for_session(chain, "S1")
    assert m.event_count == 2
    assert m.transition_count == 1
    assert m.iterations == 1
    assert m.gogogo_verdict_counts == {"PASS": 1}


def test_metrics_aggregates_verdicts_and_needs_human(tmp_path: Path):
    chain = AuditChain(tmp_path / "events.ndjson")
    chain.append("genesis", {})
    for verdict in ["PASS", "PASS", "RETRY", "NEEDS_HUMAN"]:
        chain.append(
            "gogogo.step_passed",
            {"session_id": "S1", "verifier_verdict": verdict},
        )
    chain.append("loop.budget.breach", {"session_id": "S1"})
    m = metrics_for_session(chain, "S1")
    assert m.gogogo_verdict_counts["PASS"] == 2
    assert m.gogogo_verdict_counts["RETRY"] == 1
    # NEEDS_HUMAN counted via verdict + budget breach event
    assert m.needs_human_count == 2
    assert m.iterations == 4


def test_metrics_duration_computed(tmp_path: Path):
    chain = AuditChain(tmp_path / "events.ndjson")
    chain.append("a", {"session_id": "S1"}, ts="2026-04-30T10:00:00Z")
    chain.append("b", {"session_id": "S1"}, ts="2026-04-30T10:30:00Z")
    m = metrics_for_session(chain, "S1")
    assert m.duration_seconds == pytest.approx(1800.0, abs=1)


# ─────────── commands/rrr.py helpers ───────────


def test_memory_retro_path_sequence(tmp_path: Path):
    proj = tmp_path / "proj"
    (proj / ".ai" / "memory" / "retros").mkdir(parents=True)
    p1 = _memory_retro_path(
        proj, "feat", "0001_2026-04-30_21_53_pm_feat-phase1-5-rrr"
    )
    assert p1.parent == proj / ".ai" / "memory" / "retros"
    assert p1.name.startswith("0001_")
    assert "feat-phase1-5-rrr" in p1.name
    p1.write_text("placeholder")
    p2 = _memory_retro_path(
        proj, "feat", "0001_2026-04-30_21_55_pm_feat-other"
    )
    # second mint must be 0002 (sequence advances)
    assert p2.name.startswith("0002_")


def test_render_retro_includes_verdicts():
    from cli.core.acceptance import AcceptanceReport, AcceptanceResult, AcceptanceItem
    from cli.core.forbidden_diff import ForbiddenDiffReport
    from cli.core.metrics import SessionMetrics

    metrics = SessionMetrics(
        session_id="sess_test",
        event_count=10,
        transition_count=3,
        iterations=2,
        gogogo_verdict_counts={"PASS": 2},
        final_graph_state="DONE",
    )
    fd_report = ForbiddenDiffReport(baseline="HEAD", violations=[])
    item = AcceptanceItem(
        id="A1", description="echo", command="echo x", required=True
    )
    acc_report = AcceptanceReport(
        items=[
            AcceptanceResult(
                item=item,
                passed=True,
                exit_code=0,
                stdout="x\n",
                stderr="",
            )
        ]
    )
    md = _render_retro(metrics, acc_report, fd_report, "sess_test")
    assert "acceptance-evidence: PASS" in md
    assert "rrr-contract: PASS" in md
    assert "iterations (gogogo steps): 2" in md
    assert "✅ **A1**" in md


def test_render_retro_marks_failure():
    from cli.core.acceptance import AcceptanceReport, AcceptanceResult, AcceptanceItem
    from cli.core.forbidden_diff import ForbiddenDiffReport
    from cli.core.metrics import SessionMetrics

    metrics = SessionMetrics(session_id="sess_x")
    fd_report = ForbiddenDiffReport(baseline="HEAD", violations=[".ai/policies/bad.yaml"])
    item = AcceptanceItem(id="A1", description="d", command="false", required=True)
    acc_report = AcceptanceReport(
        items=[
            AcceptanceResult(
                item=item,
                passed=False,
                exit_code=1,
                stdout="",
                stderr="",
                failure_reasons=["exit_code 1 != expected 0"],
            )
        ]
    )
    md = _render_retro(metrics, acc_report, fd_report, "sess_x")
    assert "acceptance-evidence: FAIL" in md
    assert "rrr-contract: FAIL" in md
    assert "❌ **A1**" in md
    assert ".ai/policies/bad.yaml" in md
