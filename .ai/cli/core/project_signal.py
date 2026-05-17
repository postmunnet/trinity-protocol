from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List


RETRO_GLOBS = (
    ".claude/retrospectives/**/*.md",
    ".ai/retrospectives/**/*.md",
    ".trinity/retros/**/*.md",
)

SECTION_PATTERNS = {
    "carryover": re.compile(r"(next session prep|next prep|carryover|one-sentence summary)", re.I),
    "pending": re.compile(r"(pending items|todo)", re.I),
    "regression_watch": re.compile(r"(regression watch|risk|watch)", re.I),
}
DEPLOY_RE = re.compile(r"\b(PROD|production)\b.*\b(bundle|deploy|pending|plan)\b|\bdeploy\b.*\b(PROD|production)\b", re.I)
E2E_RE = re.compile(r"\b(E2E|real-data|real data)\b", re.I)
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+\.|\[[ xX]\])\s*(.+?)\s*$")


@dataclass(frozen=True)
class SignalEntry:
    text: str
    source: str
    line: int

    def as_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "source": self.source, "line": self.line}


def collect_project_signal(project_root: Path, max_files: int = 8, max_entries: int = 5) -> Dict[str, Any]:
    """Collect sourced, deterministic project signals for `lll`.

    This intentionally does not summarize with an LLM. It scans bounded
    retrospective files for explicit sections and carries their own lines into
    the signal object with source references.
    """
    root = Path(project_root)
    files = _retro_files(root)[:max_files]
    buckets: Dict[str, List[SignalEntry]] = {
        "carryover": [],
        "pending": [],
        "regression_watch": [],
        "deploy_risk": [],
        "next_actions": [],
    }

    for path in files:
        _scan_file(root, path, buckets)

    _derive_next_actions(buckets)

    return {
        "available": any(buckets.values()),
        "sources": [str(p.relative_to(root)) for p in files],
        "carryover": _dedupe_entries(buckets["carryover"], max_entries),
        "pending": _dedupe_entries(buckets["pending"], max_entries),
        "regression_watch": _dedupe_entries(buckets["regression_watch"], max_entries),
        "deploy_risk": _dedupe_entries(buckets["deploy_risk"], max_entries),
        "next_actions": _dedupe_entries(buckets["next_actions"], max_entries),
    }


def _retro_files(root: Path) -> List[Path]:
    found: List[Path] = []
    for pattern in RETRO_GLOBS:
        found.extend(p for p in root.glob(pattern) if p.is_file())
    return sorted(set(found), key=lambda p: _retro_sort_key(root, p), reverse=True)


def _retro_sort_key(root: Path, path: Path) -> tuple:
    rel = str(path.relative_to(root))
    match = re.search(
        r"(\d{4}-\d{2}-\d{2})_(\d{1,2})_(\d{2})_([ap]m)",
        path.name,
        re.I,
    )
    if not match:
        return ("0000-00-00", 0, 0, rel)
    date, hour_raw, minute_raw, ampm = match.groups()
    hour = int(hour_raw)
    minute = int(minute_raw)
    ampm = ampm.lower()
    if ampm == "pm" and hour != 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    return (date, hour, minute, rel)


def _scan_file(root: Path, path: Path, buckets: Dict[str, List[SignalEntry]]) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    rel = str(path.relative_to(root))
    active_sections: List[str] = []
    for idx, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        heading = HEADING_RE.match(line)
        if heading:
            title = _clean_text(heading.group(2))
            active_sections = [
                key for key, pat in SECTION_PATTERNS.items() if pat.search(title)
            ]
            if "carryover" in active_sections and len(title) > 10:
                buckets["carryover"].append(SignalEntry(title, rel, idx))
            continue

        bullet = BULLET_RE.match(line)
        if not bullet:
            continue
        text = _clean_text(bullet.group(1))
        if not text:
            continue
        for section in active_sections:
            buckets[section].append(SignalEntry(text, rel, idx))
        if DEPLOY_RE.search(text):
            buckets["deploy_risk"].append(SignalEntry(text, rel, idx))
        if E2E_RE.search(text):
            buckets["pending"].append(SignalEntry(text, rel, idx))


def _derive_next_actions(buckets: Dict[str, List[SignalEntry]]) -> None:
    if buckets["deploy_risk"]:
        src = buckets["deploy_risk"][0]
        buckets["next_actions"].append(
            SignalEntry("Write a PROD deploy plan for the accumulated feature bundle.", src.source, src.line)
        )
    for entry in buckets["pending"]:
        if E2E_RE.search(entry.text):
            buckets["next_actions"].append(
                SignalEntry("Run the real-data E2E/smoke flow flagged by the latest retrospective.", entry.source, entry.line)
            )
            break


def _dedupe_entries(entries: Iterable[SignalEntry], limit: int) -> List[Dict[str, Any]]:
    out: List[SignalEntry] = []
    seen = set()
    for entry in entries:
        key = _clean_text(entry.text).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(entry)
        if len(out) >= limit:
            break
    return [entry.as_dict() for entry in out]


def _clean_text(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\[[ xX]\]\s*", "", text)
    return " ".join(text.strip(" -\t").split())
