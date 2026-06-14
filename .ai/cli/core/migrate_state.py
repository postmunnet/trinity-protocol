"""Phase D / R12 — migrate legacy sibling state out of $HOME into central_root.

Pure, idempotent logic (no I/O side effects until apply/cleanup are called).
Every sibling in MIGRATIONS is a DURABLE-state sibling whose code now resolves
central_root (central-paths, R12), so state lands under
<central_root>/state/<sibling>/ — the one durable home that survives runtime
channel switches. (Older runs left data in $HOME; this moves it.)

Flow: plan (dry-run) -> apply (copy, keeps legacy) -> cleanup (remove legacy,
only where the target already exists).
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .runtime_home import resolve_central_home

# Legacy home path (relative to $HOME) -> target (relative to central_root).
# memory-cli is intentionally absent: it is cwd-relative (.memory), not home.
MIGRATIONS = [
    {"sibling": "task-cli", "legacy": ".trinity/tasks.db", "target": "state/task-cli/tasks.db", "kind": "file"},
    {"sibling": "task-cli", "legacy": ".trinity/tasks.db-wal", "target": "state/task-cli/tasks.db-wal", "kind": "file"},
    {"sibling": "task-cli", "legacy": ".trinity/tasks.db-shm", "target": "state/task-cli/tasks.db-shm", "kind": "file"},
    {"sibling": "task-cli", "legacy": ".trinity-task-notes", "target": "state/task-cli/notes", "kind": "dir"},
    {"sibling": "brain-cli", "legacy": ".trinity-brain", "target": "state/brain-cli", "kind": "dir"},
    {"sibling": "notify-cli", "legacy": ".config/notify-cli/channels.json", "target": "state/notify-cli/channels.json", "kind": "file"},
    {"sibling": "notify-cli", "legacy": ".config/notify-cli/state.db", "target": "state/notify-cli/state.db", "kind": "file"},
    {"sibling": "notify-cli", "legacy": ".config/notify-cli/rules.json", "target": "state/notify-cli/rules.json", "kind": "file"},
    {"sibling": "tg-bot", "legacy": ".trinity-tg-notes", "target": "state/tg-bot/notes", "kind": "dir"},
    # R2 (2026-06-08): remaining home pollution — tg-bot config/db + judge/seo-genie/image/wordpress.
    {"sibling": "tg-bot", "legacy": ".config/trinity-tg-bot/config.json", "target": "state/tg-bot/config.json", "kind": "file"},
    {"sibling": "tg-bot", "legacy": ".config/trinity-tg-bot/state.db", "target": "state/tg-bot/state.db", "kind": "file"},
    {"sibling": "tg-bot", "legacy": ".config/trinity-tg-bot/state.db-wal", "target": "state/tg-bot/state.db-wal", "kind": "file"},
    {"sibling": "tg-bot", "legacy": ".config/trinity-tg-bot/state.db-shm", "target": "state/tg-bot/state.db-shm", "kind": "file"},
    {"sibling": "judge-cli", "legacy": ".config/judge-cli", "target": "state/judge-cli", "kind": "dir"},
    {"sibling": "seo-genie-cli", "legacy": ".config/seo-genie-cli", "target": "state/seo-genie-cli", "kind": "dir"},
    {"sibling": "seo-genie-cli", "legacy": ".seo-genie-feed", "target": "state/seo-genie-cli/feed", "kind": "dir"},
    {"sibling": "image-cli", "legacy": ".config/image-cli", "target": "state/image-cli", "kind": "dir"},
    {"sibling": "wordpress-cli", "legacy": ".config/wordpress-cli", "target": "state/wordpress-cli", "kind": "dir"},
]


@dataclass
class MigrationItem:
    sibling: str
    kind: str
    legacy: Path
    target: Path
    legacy_exists: bool
    target_exists: bool
    status: str = "pending"  # pending|copied|skipped_exists|skipped_missing|cleaned|kept

    def as_dict(self) -> dict:
        return {
            "sibling": self.sibling,
            "kind": self.kind,
            "legacy": str(self.legacy),
            "target": str(self.target),
            "legacy_exists": self.legacy_exists,
            "target_exists": self.target_exists,
            "status": self.status,
        }


@dataclass
class MigrationReport:
    central_root: Path
    items: List[MigrationItem] = field(default_factory=list)
    mode: str = "dry-run"

    def as_dict(self) -> dict:
        return {
            "central_root": str(self.central_root),
            "mode": self.mode,
            "items": [i.as_dict() for i in self.items],
            "summary": self.summary(),
        }

    def summary(self) -> dict:
        out: dict = {}
        for i in self.items:
            out[i.status] = out.get(i.status, 0) + 1
        return out


def build_plan(home: Optional[Path] = None, central: Optional[Path] = None, env=None) -> MigrationReport:
    """Resolve concrete legacy/target paths. Pure — touches nothing on disk.

    Targets land under central_root (R12): unlike runtime_root, resolve_central_home
    has a default (~/.trinity-central) and never raises.
    """
    home_dir = Path(home) if home is not None else Path.home()
    central_root = Path(central) if central is not None else resolve_central_home(env=env)
    items: List[MigrationItem] = []
    for m in MIGRATIONS:
        legacy = home_dir / m["legacy"]
        target = central_root / m["target"]
        items.append(
            MigrationItem(
                sibling=m["sibling"],
                kind=m["kind"],
                legacy=legacy,
                target=target,
                legacy_exists=legacy.exists(),
                target_exists=target.exists(),
            )
        )
    return MigrationReport(central_root=central_root, items=items, mode="dry-run")


def _copy(item: MigrationItem) -> None:
    if item.kind == "dir":
        item.target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(item.legacy, item.target, dirs_exist_ok=True)
    else:
        item.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.legacy, item.target)


def apply_plan(report: MigrationReport) -> MigrationReport:
    """Copy legacy -> target. Never deletes legacy. Idempotent."""
    for item in report.items:
        if not item.legacy_exists:
            item.status = "skipped_missing"
        elif item.target_exists:
            item.status = "skipped_exists"  # already migrated
        else:
            _copy(item)
            item.target_exists = True
            item.status = "copied"
    report.mode = "apply"
    return report


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def cleanup_plan(report: MigrationReport) -> MigrationReport:
    """Remove legacy ONLY where the target exists (i.e. it was copied)."""
    for item in report.items:
        if not item.legacy_exists:
            item.status = "skipped_missing"
        elif item.target_exists:
            _remove(item.legacy)
            item.legacy_exists = False
            item.status = "cleaned"
        else:
            item.status = "kept"  # not copied yet — refuse to delete
    report.mode = "cleanup"
    return report
