from __future__ import annotations
import os
import shutil
import fnmatch
from pathlib import Path
from typing import Iterable, Optional


def _should_exclude(name: str, exclude_patterns: set) -> bool:
    """Check if name matches any exclude pattern (supports wildcards via fnmatch)."""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def safe_copy_tree(src: Path, dst: Path, exclude: Optional[Iterable[str]] = None) -> None:
    """
    Safely copy a directory tree with exclude patterns.
    
    Args:
        src: Source directory path
        dst: Destination directory path  
        exclude: Patterns to exclude (supports wildcards like *.log, *.pyc)
    """
    exclude_patterns = set(exclude or [])
    dst.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        # skip excluded directories by name or pattern
        dirs[:] = [d for d in dirs if not _should_exclude(d, exclude_patterns)]
        # ensure directory exists at dest
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        # copy files (skip if matches exclude pattern)
        for name in files:
            if _should_exclude(name, exclude_patterns):
                continue
            s = Path(root) / name
            d = target_dir / name
            shutil.copy2(s, d)


def atomic_replace(src: Path, dst: Path) -> None:
    """Atomically replace directory or file at dst with src on the same filesystem.

    Strategy (cross-platform safe for dirs):
    - If dst exists, first rename it to a backup sibling
    - Rename src -> dst
    - Remove backup
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    backup = dst.with_suffix(dst.suffix + ".bak")
    if backup.exists():
        if backup.is_dir():
            shutil.rmtree(backup)
        else:
            backup.unlink()
    if dst.exists():
        os.replace(dst, backup)
    os.replace(src, dst)
    if backup.exists():
        if backup.is_dir():
            shutil.rmtree(backup)
        else:
            backup.unlink()


def set_read_only(target: Path) -> None:
    if target.is_dir():
        for p in target.rglob("*"):
            _chmod_ro(p)
        _chmod_ro(target)
    else:
        _chmod_ro(target)


def _chmod_ro(p: Path) -> None:
    try:
        mode = p.stat().st_mode
        # remove write bits for user/group/others
        mode &= ~0o222
        os.chmod(p, mode)
    except Exception:
        pass
