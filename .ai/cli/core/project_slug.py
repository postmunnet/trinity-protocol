from __future__ import annotations

import hashlib
import re
from pathlib import Path


_NON_SLUG_RE = re.compile(r"[^0-9a-z]+")
_MULTI_UNDERSCORE_RE = re.compile(r"_+")


def slugify_project_name(name: str) -> str:
    """Return Trinity's deterministic project slug form.

    Examples:
      - TRINITY_LEGACY -> trinity_legacy
      - Project A -> project_a
      - example_project-prod -> example_project_prod
    """
    slug = _NON_SLUG_RE.sub("_", name.lower())
    slug = _MULTI_UNDERSCORE_RE.sub("_", slug).strip("_")
    return slug or "project"


def stable_project_suffix(root_path: Path) -> str:
    """Return a stable short suffix for collision-safe DB filenames."""
    resolved = str(Path(root_path).expanduser().resolve())
    return hashlib.sha1(resolved.encode("utf-8")).hexdigest()[:6]


def collision_safe_slug(base_slug: str, root_path: Path) -> str:
    """Return the deterministic collision form for an already-used slug."""
    return f"{base_slug}__{stable_project_suffix(root_path)}"
