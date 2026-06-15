"""Doc-coupling drift guard (v1).

Declarative coupling manifest (`.ai/policies/doc_coupling.yaml`) maps "if code X
changes -> doc Y must be updated in the same session". Checked at rrr (gate) and
by `ai doc-drift` (read-only).

Detection is content-hash snapshot first (the monorepo root is not a git repo, so
`git diff` is inert here) with git as a bonus on git-tracked instances. Hashes of
every manifest-referenced file are stamped at sss into
`.state/doc_coupling_hashes.json`; a file is "changed" when its live hash differs
from the stamp (or it is newly created / deleted).

Severity: block (high-confidence doctrine) | warn (narrative) | info. No manifest
=> clean report (gate skipped, opt-in). All reads fail-soft; never raises into the
ritual flow.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

HASHES_REL = "doc_coupling_hashes.json"
_ISO_OFFSET_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[.\d]+)?[+-]\d{2}:\d{2}")


# ── data ────────────────────────────────────────────────────────────────
@dataclass
class Coupling:
    id: str
    severity: str
    when_changed: List[str]
    require_update: List[str]
    reason: str


@dataclass
class Manifest:
    version: int
    changelog_required: bool
    timestamp_format: str
    timezone: str
    couplings: List[Coupling]


@dataclass
class Finding:
    coupling_id: str
    severity: str
    kind: str  # missing_update | missing_changelog
    missing: List[str]
    reason: str
    route: str


@dataclass
class DocCouplingReport:
    verdict: str = "clean"  # clean | warn | block
    findings: List[Finding] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    skipped: bool = False  # no manifest present

    @property
    def blocking(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "block"]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "warn"]


class DocCouplingManifestError(Exception):
    """Raised when the manifest exists but is malformed (fail-loud)."""


# ── manifest load ───────────────────────────────────────────────────────
def load_manifest(project_root: Path) -> Optional[Manifest]:
    """Resolve + parse the manifest (project-local first, kernel-source fallback).
    Returns None when no manifest exists anywhere (opt-in: gate skipped)."""
    import yaml

    from .kernel_resource import resolve_ai_resource

    path, _src = resolve_ai_resource(
        project_root, "policies/doc_coupling.yaml", label="doc_coupling", quiet=True
    )
    if path is None or not Path(path).is_file():
        return None
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise DocCouplingManifestError(f"doc_coupling.yaml invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise DocCouplingManifestError("doc_coupling.yaml must be a mapping")
    defaults = raw.get("defaults") or {}
    couplings: List[Coupling] = []
    for entry in raw.get("couplings") or []:
        if not isinstance(entry, dict) or "id" not in entry:
            raise DocCouplingManifestError(f"coupling missing id: {entry!r}")
        sev = entry.get("severity", "warn")
        if sev not in ("block", "warn", "info"):
            raise DocCouplingManifestError(
                f"coupling {entry['id']}: bad severity {sev!r}"
            )
        couplings.append(
            Coupling(
                id=entry["id"],
                severity=sev,
                when_changed=list(entry.get("when_changed") or []),
                require_update=list(entry.get("require_update") or []),
                reason=entry.get("reason", ""),
            )
        )
    return Manifest(
        version=int(raw.get("version", 1)),
        changelog_required=bool(defaults.get("changelog_required", True)),
        timestamp_format=str(defaults.get("timestamp_format", "iso8601_with_offset")),
        timezone=str(defaults.get("timezone", "UTC")),
        couplings=couplings,
    )


# ── glob matching ───────────────────────────────────────────────────────
def _glob_to_re(pat: str) -> "re.Pattern[str]":
    out, i, n = [], 0, len(pat)
    while i < n:
        c = pat[i]
        if pat.startswith("**", i):
            out.append(".*")
            i += 2
            if i < n and pat[i] == "/":
                i += 1
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def _match_any(rel: str, patterns: Sequence[str]) -> bool:
    return any(_glob_to_re(p).match(rel) for p in patterns)


def _all_patterns(manifest: Manifest) -> List[str]:
    pats: List[str] = []
    for c in manifest.couplings:
        pats.extend(c.when_changed)
        pats.extend(c.require_update)
    return pats


def _referenced_files(project_root: Path, manifest: Manifest) -> List[str]:
    """Every existing file under project_root matching any manifest pattern.
    Literal (non-glob) paths are included directly so missing docs are tracked too."""
    pats = _all_patterns(manifest)
    seen: Set[str] = set()
    # literal paths (may not 'exist' as glob walk targets but should be hashed)
    for p in pats:
        if not any(ch in p for ch in "*?[]"):
            seen.add(p)
    # globbed walk
    for f in project_root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(project_root).as_posix()
        if "/.git/" in f"/{rel}" or "/node_modules/" in f"/{rel}" or "/.ai/sessions/" in f"/{rel}":
            continue
        if _match_any(rel, pats):
            seen.add(rel)
    return sorted(seen)


def _sha256(path: Path) -> Optional[str]:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


# ── snapshot (sss) ──────────────────────────────────────────────────────
def record_coupling_hashes(state_dir: Path, project_root: Path) -> None:
    """Stamp sha256 of every manifest-referenced file at session start. Fail-soft:
    no manifest / unreadable => write nothing (gate stays opt-in / behaves clean)."""
    try:
        manifest = load_manifest(project_root)
        if manifest is None:
            return
        stamp: Dict[str, Optional[str]] = {}
        for rel in _referenced_files(project_root, manifest):
            stamp[rel] = _sha256(project_root / rel)
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / HASHES_REL).write_text(
            json.dumps(stamp, indent=2, sort_keys=True), encoding="utf-8"
        )
    except (OSError, DocCouplingManifestError):
        return


# ── changed-set ─────────────────────────────────────────────────────────
def _git_changed(project_root: Path, baseline: str) -> Set[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", baseline],
            cwd=str(project_root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return {ln.strip() for ln in out.splitlines() if ln.strip()}
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return set()


def compute_changed_set(
    project_root: Path,
    state_dir: Path,
    manifest: Manifest,
    *,
    baseline: str = "HEAD",
) -> Set[str]:
    """Files (relative posix) changed since sss: content-hash compare (primary) +
    git diff (bonus where tracked)."""
    changed: Set[str] = set()
    stamp_path = state_dir / HASHES_REL
    # Backward compat: sessions created before the sss snapshot hook have no
    # stamp file. Without a baseline we MUST NOT treat every referenced file as
    # changed (that would false-trigger every coupling). Fall back to git-only
    # (which is itself empty on a non-git root) — i.e. clean. Mirrors
    # forbidden_diff's baseline_untracked=[] backward-compat.
    if stamp_path.is_file():
        try:
            loaded = json.loads(stamp_path.read_text(encoding="utf-8"))
            stamp: Dict[str, Optional[str]] = loaded if isinstance(loaded, dict) else {}
        except (json.JSONDecodeError, OSError):
            stamp = {}
        # union of stamped keys + currently-referenced files (catches new files)
        candidates = set(stamp.keys()) | set(_referenced_files(project_root, manifest))
        for rel in candidates:
            live = _sha256(project_root / rel)
            if stamp.get(rel) != live:
                changed.add(rel)
    changed |= _git_changed(project_root, baseline)
    return changed


# ── changelog freshness ─────────────────────────────────────────────────
def _changelog_fresh(project_root: Path, doc: str, session_id: str) -> bool:
    """A touched doc must carry a changelog entry that references THIS session id
    and an ISO8601-with-offset timestamp (HTML data-attr block or MD markers)."""
    try:
        text = (project_root / doc).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return (session_id in text) and bool(_ISO_OFFSET_RE.search(text))


# ── check ───────────────────────────────────────────────────────────────
def check(
    project_root: Path,
    state_dir: Path,
    session_id: str,
    *,
    manifest: Optional[Manifest] = None,
    baseline: str = "HEAD",
) -> DocCouplingReport:
    """Run the doc-coupling check. Never raises on a missing/malformed-but-loaded
    manifest used via load_manifest (that raises earlier, at load)."""
    if manifest is None:
        try:
            manifest = load_manifest(project_root)
        except DocCouplingManifestError:
            # treat malformed manifest as a hard finding rather than crash rrr
            return DocCouplingReport(
                verdict="block",
                findings=[
                    Finding(
                        coupling_id="_manifest",
                        severity="block",
                        kind="manifest_invalid",
                        missing=["policies/doc_coupling.yaml"],
                        reason="doc_coupling.yaml is malformed",
                        route="fix the manifest YAML",
                    )
                ],
            )
    if manifest is None:
        return DocCouplingReport(skipped=True)

    changed = compute_changed_set(project_root, state_dir, manifest, baseline=baseline)
    report = DocCouplingReport(changed=sorted(changed))

    for c in manifest.couplings:
        triggered = any(_match_any(rel, c.when_changed) for rel in changed)
        if not triggered:
            continue
        # which required docs were NOT updated this session
        missing = [
            d for d in c.require_update if not any(_match_any(rel, [d]) for rel in changed)
        ]
        if missing:
            report.findings.append(
                Finding(
                    coupling_id=c.id,
                    severity=c.severity,
                    kind="missing_update",
                    missing=missing,
                    reason=c.reason,
                    route="update the doc(s) or `ai rrr --accept-doc-debt --reason ...`",
                )
            )
        # changelog freshness on docs that WERE updated
        if manifest.changelog_required:
            updated = [d for d in c.require_update if d not in missing]
            stale = [d for d in updated if not _changelog_fresh(project_root, d, session_id)]
            if stale:
                report.findings.append(
                    Finding(
                        coupling_id=c.id,
                        severity=c.severity,
                        kind="missing_changelog",
                        missing=stale,
                        reason="updated doc lacks an ISO8601+offset + session-id changelog entry",
                        route="add a changelog entry (ts with offset + session id) to the doc",
                    )
                )

    if report.blocking:
        report.verdict = "block"
    elif report.warnings:
        report.verdict = "warn"
    return report
