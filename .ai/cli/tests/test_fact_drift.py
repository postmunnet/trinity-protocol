"""Fact-drift checker (doc-drift v2) — truth extractors, claims, compare."""
from __future__ import annotations

import json
from pathlib import Path

from cli.core import fact_drift as fd


def _project(tmp: Path, *, sib_dirs=3, registered=12, retros=5, projects=8,
             atlas_source="3", atlas_active="12", atlas_projects="8",
             atlas_retros="5", atlas_terminal="DONE, DEAD") -> Path:
    sib = tmp / "siblings"
    sib.mkdir()
    for i in range(sib_dirs):
        (sib / f"tool-{i}").mkdir()
    (sib / "REGISTRY.md").write_text(f"{sib_dirs + 5} workspace tools: {registered} registered + N staged.\n")
    g = tmp / ".ai" / "graphs"
    g.mkdir(parents=True)
    (g / "standard.yaml").write_text("terminal_states: [DONE, DEAD]\n")
    reg = tmp / "registry"
    reg.mkdir()
    (reg / "projects.json").write_text(json.dumps({"version": 1, "projects": [str(i) for i in range(projects)]}))
    rt = tmp / ".ai" / "memory" / "retros"
    rt.mkdir(parents=True)
    for i in range(retros):
        (rt / f"{i:04d}_x.md").write_text("retro")
    dev = tmp / "dev"
    dev.mkdir()
    (dev / "trinity_structure_workflow.html").write_text(
        f"siblings/ ×{atlas_source} source dirs · {atlas_active} registry-active · "
        f"thin ×{atlas_projects} · states {atlas_terminal} · {atlas_retros} retros indexed"
    )
    return tmp


# ── registry / truth ─────────────────────────────────────────────────────
def test_registry_has_five_facts():
    assert len(fd.FACTS) == 5
    assert {f.id for f in fd.FACTS} == {
        "sibling_source_dirs", "registry_active_tools",
        "graph_terminal_states", "linked_project_count", "memory_retro_count",
    }


def test_truth_extractors_on_real_tree(tmp_path):
    _project(tmp_path, sib_dirs=4, registered=11, retros=7, projects=6)
    assert fd._truth_sibling_dirs(tmp_path) == "4"
    assert fd._truth_registry_active(tmp_path) == "11"
    assert fd._truth_terminal_states(tmp_path) == "DEAD,DONE"
    assert fd._truth_project_count(tmp_path) == "6"
    assert fd._truth_retro_count(tmp_path) == "7"


def test_truth_failsoft_on_missing_sources(tmp_path):
    # empty tree: every truth extractor returns None, never raises
    assert fd._truth_sibling_dirs(tmp_path) is None
    assert fd._truth_registry_active(tmp_path) is None
    assert fd._truth_terminal_states(tmp_path) is None
    assert fd._truth_retro_count(tmp_path) is None


# ── claim extractors ─────────────────────────────────────────────────────
def test_claim_distinct_flags_inconsistent():
    # a doc asserting a fact two different ways -> sorted distinct set
    assert fd._claim_retros("88 retros indexed ... 101 retros later") == "101,88"


def test_claim_terminal_set():
    assert fd._claim_terminal_states("graph ... DONE, DEAD terminal") == "DEAD,DONE"
    assert fd._claim_terminal_states("nothing here") is None


# ── compare ──────────────────────────────────────────────────────────────
def _status_for(report, fact_id):
    r = next(r for r in report.results if r.fact_id == fact_id)
    return next(iter(r.status.values()))


def test_compare_all_match(tmp_path):
    _project(tmp_path)  # atlas defaults aligned to truth
    rep = fd.compare(tmp_path)
    assert rep.verdict == "clean" and rep.drift_count == 0


def test_compare_detects_drift(tmp_path):
    _project(tmp_path, retros=5, atlas_retros="88")  # atlas says 88, truth 5
    rep = fd.compare(tmp_path)
    assert rep.verdict == "drift"
    assert _status_for(rep, "memory_retro_count") == "drift"
    # the aligned ones stay match
    assert _status_for(rep, "sibling_source_dirs") == "match"


def test_compare_unknown_when_source_missing(tmp_path):
    # no siblings dir => truth None => unknown (not drift)
    (tmp_path / "dev").mkdir()
    (tmp_path / "dev" / "trinity_structure_workflow.html").write_text("21 source dirs")
    rep = fd.compare(tmp_path)
    assert _status_for(rep, "sibling_source_dirs") == "unknown"


# ── command serialization ────────────────────────────────────────────────
def test_facts_report_shape(tmp_path):
    _project(tmp_path, atlas_retros="88")
    rep = fd.compare(tmp_path)
    drifted = [r for r in rep.results if r.drifted]
    assert drifted and drifted[0].fact_id == "memory_retro_count"
