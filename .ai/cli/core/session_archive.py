"""Session archive helper.

Single source of truth for moving a session capsule from
`.ai/sessions/<name>/` to `.ai/sessions/archive/<name>.archive/`.

Used by:
  - `ai close run` (normal lifecycle terminator)
  - `ai rrr --retroactive` auto-archive (recovery path for ghost
    sessions stitched into the audit chain by retroactive rrr)

Resolves archive directory from ssot.yaml `paths.archive_sessions`
template (default `${sessions}/archive`), so callers don't reach
into `session_path.parent.parent` and get fooled by symlinked or
re-rooted layouts.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def archive_session(session_path: Path, config) -> Path:
    """Move session capsule into the configured archive dir.

    Returns the resolved archive path. Removes a pre-existing
    archive of the same name (idempotent overwrite — caller decides
    whether that is safe).
    """
    paths_cfg = (config.raw_config or {}).get("paths", {})
    archive_template = paths_cfg.get("archive_sessions", "${sessions}/archive")
    sessions_template = paths_cfg.get("sessions", "${ai_root}/sessions")
    sessions_resolved = (
        sessions_template
        .replace("${ai_root}", str(config.ai_root))
        .replace("${project_root}", str(config.project_root))
    )
    archive_resolved = (
        archive_template
        .replace("${sessions}", sessions_resolved)
        .replace("${ai_root}", str(config.ai_root))
        .replace("${project_root}", str(config.project_root))
    )
    archive_dir = Path(archive_resolved)
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_name = f"{session_path.name}.archive"
    archive_path = archive_dir / archive_name

    if archive_path.exists():
        shutil.rmtree(archive_path)

    shutil.move(str(session_path), str(archive_path))
    return archive_path
