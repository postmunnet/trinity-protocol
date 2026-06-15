"""Fact-drift checker (doc-drift v2).

Compares a *fact's canonical value* (extracted from the source of truth) against
what docs *assert* that fact to be — catching semantic drift directly, even when
no file changed this session (e.g. the atlas says "88 retros" while the real
count is 119).

Each Fact has a `truth` extractor (reads the canonical source) and per-doc `claim`
extractors (read what a doc asserts). Both are fail-soft: any read/parse failure
yields None ("unknown"), never a false "drift". Extractors are code, not config,
so brittle HTML/MD regexes stay reviewable. READ-ONLY / advisory — not a gate.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

ATLAS = "dev/trinity_structure_workflow.html"
CLAUDE = "CLAUDE.md"


# ── helpers (fail-soft) ──────────────────────────────────────────────────
def _read(project_root: Path, rel: str) -> Optional[str]:
    try:
        return (project_root / rel).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _first(pattern: str, text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _distinct(pattern: str, text: Optional[str]) -> Optional[str]:
    """Distinct captured values, sorted+joined — flags docs that assert a fact
    inconsistently (e.g. '88' here, '101' there)."""
    if not text:
        return None
    vals = sorted({m.group(1) for m in re.finditer(pattern, text)})
    return ",".join(vals) if vals else None


# ── truth extractors ─────────────────────────────────────────────────────
def _truth_sibling_dirs(root: Path) -> Optional[str]:
    try:
        return str(sum(1 for p in (root / "siblings").iterdir() if p.is_dir()))
    except OSError:
        return None


def _truth_registry_active(root: Path) -> Optional[str]:
    return _first(r"(\d+)\s+registered", _read(root, "siblings/REGISTRY.md"))


def _truth_terminal_states(root: Path) -> Optional[str]:
    text = _read(root, ".ai/graphs/standard.yaml")
    if not text:
        return None
    m = re.search(r"terminal_states:\s*\[([^\]]*)\]", text)
    if not m:
        return None
    toks = sorted(t.strip() for t in m.group(1).split(",") if t.strip())
    return ",".join(toks) or None


def _truth_project_count(root: Path) -> Optional[str]:
    for cand in (
        root / "registry" / "projects.json",
        Path.home() / ".trinity-central" / "registry" / "projects.json",
    ):
        try:
            d = json.loads(cand.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        projs = d.get("projects") if isinstance(d, dict) else d
        if isinstance(projs, (list, dict)):
            return str(len(projs))
    return None


def _truth_retro_count(root: Path) -> Optional[str]:
    d = root / ".ai" / "memory" / "retros"
    if not d.is_dir():
        return None  # missing dir => unknown (not "0")
    try:
        return str(sum(1 for _ in d.glob("*.md")))
    except OSError:
        return None


# ── claim extractors (per doc) ───────────────────────────────────────────
def _claim_source_dirs(t: Optional[str]) -> Optional[str]:
    return _first(r"(\d+)\s+source dir", t)


def _claim_registry_active(t: Optional[str]) -> Optional[str]:
    return _distinct(r"(\d+)\s+registry-active", t)


def _claim_terminal_states(t: Optional[str]) -> Optional[str]:
    if not t:
        return None
    found = sorted({w for w in ("DONE", "DEAD") if w in t})
    return ",".join(found) or None


def _claim_projects(t: Optional[str]) -> Optional[str]:
    return _first(r"thin ×(\d+)", t)


def _claim_retros(t: Optional[str]) -> Optional[str]:
    return _distinct(r"(\d+)\s+retros\b", t)


# ── registry ─────────────────────────────────────────────────────────────
@dataclass
class Fact:
    id: str
    description: str
    truth_fn: Callable[[Path], Optional[str]]
    claim_fns: Dict[str, Callable[[Optional[str]], Optional[str]]]


FACTS: List[Fact] = [
    Fact("sibling_source_dirs", "sibling source directories (ls siblings/*/)",
         _truth_sibling_dirs, {ATLAS: _claim_source_dirs}),
    Fact("registry_active_tools", "registry-active tools (REGISTRY.md 'N registered')",
         _truth_registry_active, {ATLAS: _claim_registry_active}),
    Fact("graph_terminal_states", "graph terminal states (standard.yaml)",
         _truth_terminal_states, {ATLAS: _claim_terminal_states}),
    Fact("linked_project_count", "linked projects (registry/projects.json)",
         _truth_project_count, {ATLAS: _claim_projects}),
    Fact("memory_retro_count", "memory retros (.ai/memory/retros/*.md)",
         _truth_retro_count, {ATLAS: _claim_retros}),
]


@dataclass
class FactResult:
    fact_id: str
    description: str
    truth: Optional[str]
    claims: Dict[str, Optional[str]] = field(default_factory=dict)
    status: Dict[str, str] = field(default_factory=dict)  # doc -> match|drift|unknown

    @property
    def drifted(self) -> bool:
        return any(s == "drift" for s in self.status.values())


@dataclass
class FactDriftReport:
    results: List[FactResult] = field(default_factory=list)

    @property
    def drift_count(self) -> int:
        return sum(1 for r in self.results if r.drifted)

    @property
    def verdict(self) -> str:
        return "drift" if self.drift_count else "clean"


def _status(truth: Optional[str], claim: Optional[str]) -> str:
    if truth is None or claim is None:
        return "unknown"
    # numeric drift: a claim string may be a set like "88,101"; match only when the
    # claim is exactly the single true value.
    return "match" if claim.strip() == truth.strip() else "drift"


def compare(project_root: Path, facts: Optional[List[Fact]] = None) -> FactDriftReport:
    facts = facts if facts is not None else FACTS
    report = FactDriftReport()
    for f in facts:
        truth = f.truth_fn(project_root)
        res = FactResult(fact_id=f.id, description=f.description, truth=truth)
        for doc, fn in f.claim_fns.items():
            claim = fn(_read(project_root, doc))
            res.claims[doc] = claim
            res.status[doc] = _status(truth, claim)
        report.results.append(res)
    return report
