"""Phase 1.5 — detect writes to D1-forbidden paths since a baseline.

Spec ref: docs/migration/01_CONTEXT_AND_DECISIONS.md D1 (forbidden writes)
          .ai/shims/rrr/SHIM.md (rrr verifies boundary respect)
          docs/specs/TRINITY_RITUAL_CONTRACT_V1.md §rrr (gate semantics)
          .ai/sessions/<phase-0-5-session>/CONTROL/BREAK_GLASS.yaml
            post_mortem_resolution (allowlist carve-out mandate)

D1 forbids in-tree edits to:

  .ai/policies/**, .ai/schemas/**, docs/specs/**, docs/constitution/**, references/**

`docs/constitution/**` was added 2026-05-13 (Addendum v1.0.2) when the
six canonical Trinity constitutional documents were relocated from
`docs/specs/` to a dedicated `docs/constitution/` directory. Both
paths remain protected so the relocation is not an authority
downgrade.

`.ai/audit/**` is forbidden for *modify* but `events.ndjson` is the
hash-chained append log that grows every session. Rather than parse
git diff to distinguish append-only changes, we explicitly exclude
`events.ndjson` from this checker — its integrity is verified by
`AuditChain.validate()` instead. Other files under `.ai/audit/` (if
they exist) are still flagged.

Phase 0.5 addition — `allowed_paths` carve-outs:

A session's plan envelope may declare `allowed_paths` (typically when
the operator has explicitly authorised writes to a D1 zone via PRD,
e.g. spec-lock work in docs/specs/). When `check()` is called with
`allowed_paths`, a candidate path that matches a forbidden pattern
AND any allowed_paths glob is recorded as a CARVE-OUT instead of a
violation. Carve-outs remain visible in the report (Article XXIII —
failure visibility) but do not fail the gate.

Backward compat: `allowed_paths=None` or empty list → identical to
prior behaviour. Default is close-fail: malformed allowed_paths from
plan envelope is treated as `None`, not as "everything allowed".
"""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence


FORBIDDEN_PATTERNS = [
    re.compile(r"^\.ai/policies/"),
    re.compile(r"^\.ai/schemas/"),
    re.compile(r"^docs/specs/"),
    re.compile(r"^docs/constitution/"),
    re.compile(r"^references/"),
    # .ai/audit/ except events.ndjson (chain is append-only by design)
    re.compile(r"^\.ai/audit/(?!events\.ndjson$)"),
]


@dataclass
class ForbiddenDiffReport:
    baseline: str
    violations: List[str] = field(default_factory=list)
    carve_outs: List[str] = field(default_factory=list)
    skipped_audit_chain: bool = False  # purely informational

    @property
    def ok(self) -> bool:
        return not self.violations


def _normalise_allowed(
    allowed_paths: Optional[Sequence[str]],
) -> List[str]:
    """Coerce a caller-supplied allowed_paths into a clean glob list.

    A malformed value (None, non-list, bare string, non-strings inside)
    yields `[]`, i.e. no carve-out — close-fail by design. A bare string
    is explicitly rejected because iterating a string yields characters,
    and a `*` character would otherwise become a wildcard that matches
    every forbidden path.
    """
    if not allowed_paths:
        return []
    if not isinstance(allowed_paths, (list, tuple)):
        return []
    out: List[str] = []
    for item in allowed_paths:
        if not isinstance(item, str):
            continue
        # removeprefix strips only the literal "./" prefix; lstrip("./") would
        # treat "./" as a char-set and also strip leading "." from ".ai/..."
        # paths, breaking carve-outs for kernel-internal paths.
        cleaned = item.strip().removeprefix("./")
        if cleaned:
            out.append(cleaned)
    return out


def _matches_allowed(path: str, allowed: Sequence[str]) -> bool:
    """fnmatch-based glob match. Translates gitignore-style ``**`` to
    fnmatch's ``*`` so callers can write paths like
    ``docs/specs/TRINITY_*.md`` or ``docs/specs/**``."""
    for pattern in allowed:
        # fnmatch.fnmatch with ** treated as cross-segment wildcard.
        normalised = pattern.replace("**", "*")
        if fnmatch.fnmatch(path, normalised):
            return True
        # Also try a leading-./ stripped variant for safety.
        if fnmatch.fnmatch(path, normalised.lstrip("./")):
            return True
    return False


def check(
    project_root: Path,
    baseline: str = "HEAD",
    allowed_paths: Optional[Sequence[str]] = None,
    *,
    baseline_untracked: Optional[Sequence[str]] = None,
) -> ForbiddenDiffReport:
    """Run `git diff --name-only <baseline>` from project_root, flag any
    paths that match a forbidden pattern. Untracked files are also
    considered (via `git status --porcelain`) so a new policies/ file
    is caught even before `git add`.

    Phase 0.5: if `allowed_paths` is provided, a forbidden hit that also
    matches any allowed_paths glob is recorded as a carve-out rather
    than a violation. The carve-out list is reported for audit (Article
    XXIII) but does not fail `report.ok`.

    Cross-session fix (2026-05-14, `feedback_rrr_cross_session_forbidden_diff`):
    `baseline_untracked` is an optional list of paths that were ALREADY
    untracked at this session's start (recorded by `record_baseline_untracked`
    at sss time). Those paths are excluded from the untracked candidate set
    here so a parallel HOLD session's deliverables do not surface as the
    current session's violations. Backward compat: `baseline_untracked=None`
    or empty → identical to prior behavior.
    """
    report = ForbiddenDiffReport(baseline=baseline)
    allowed = _normalise_allowed(allowed_paths)

    diffed = _git_files(project_root, baseline)
    untracked_all = _git_untracked(project_root)
    pre_existing = set(baseline_untracked or [])
    untracked = [p for p in untracked_all if p not in pre_existing]
    candidates = sorted(set(diffed) | set(untracked))

    for path in candidates:
        if path == ".ai/audit/events.ndjson":
            report.skipped_audit_chain = True
            continue
        forbidden = False
        for pat in FORBIDDEN_PATTERNS:
            if pat.search(path):
                forbidden = True
                break
        if not forbidden:
            continue
        if allowed and _matches_allowed(path, allowed):
            report.carve_outs.append(path)
            continue
        report.violations.append(path)
    return report


def _git_files(project_root: Path, baseline: str) -> List[str]:
    """Files changed since baseline (tracked + modifications)."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", baseline],
            cwd=str(project_root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def record_baseline_untracked(
    session_state_dir: Path,
    project_root: Path,
) -> List[str]:
    """Snapshot the working tree's pre-existing untracked files at session
    creation time, writing the list to `<session_state_dir>/baseline_untracked.json`.

    Called by `cli.commands.session.new` right after `.state/` is initialised
    so the file lands inside the session capsule. The list is consumed by
    `cli.commands.rrr` to filter another session's HOLD files out of this
    session's forbidden-diff scan
    (`feedback_rrr_cross_session_forbidden_diff`).

    Returns the recorded list. The file content is a JSON array of strings —
    paths relative to `project_root` exactly as `git status --porcelain
    --untracked-files=all` reports them.
    """
    session_state_dir.mkdir(parents=True, exist_ok=True)
    untracked = _git_untracked(project_root)
    target = session_state_dir / "baseline_untracked.json"
    target.write_text(
        json.dumps(untracked, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return untracked


def _git_untracked(project_root: Path) -> List[str]:
    """Untracked (new) files surfaced by `git status --porcelain
    --untracked-files=all`. The `=all` flag forces git to enumerate
    every file inside untracked directories rather than collapsing
    them to a single entry like `?? .ai/`."""
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=str(project_root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    untracked: List[str] = []
    for line in out.splitlines():
        if line.startswith("?? "):
            untracked.append(line[3:].strip())
    return untracked
