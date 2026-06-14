"""Trinity runtime-home resolver (kernel side).

Python mirror of `packages/runtime-paths/` (see that package's SPEC.md — the
single source of truth). Resolves WHERE runtime state lives, with a
**mandatory-config** rule: never guess, error instead.

Resolution order (must match the Node impl exactly):
    1. $TRINITY_HOME env
    2. <instance>/.ai/runtime.yaml   (runtime_root: key)
    3. raise RuntimeNotConfiguredError
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional

RUNTIME_YAML_REL = Path(".ai") / "runtime.yaml"
_RUNTIME_ROOT_RE = re.compile(r"^[ \t]*runtime_root[ \t]*:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
# runtime_code: = CODE root of the central runtime (where the kernel/siblings code
# lives). Separate from runtime_root (STATE). Read by the per-project .ai/ai shim
# (R4) to exec <code>/core/trinity_v2/.ai/cli/ai. State resolution never reads it.
_RUNTIME_CODE_RE = re.compile(r"^[ \t]*runtime_code[ \t]*:[ \t]*(.+?)[ \t]*$", re.MULTILINE)


class RuntimeNotConfiguredError(Exception):
    """Raised when no runtime root is configured (and strict resolution asked)."""

    code = "runtime_not_configured"

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(
            message
            or "Trinity runtime not configured — run `ai config set-runtime <path>`"
        )


def find_runtime_yaml(start: Path) -> Optional[Path]:
    """Walk up from `start` looking for `<dir>/.ai/runtime.yaml`."""
    d = Path(start).resolve()
    while True:
        candidate = d / RUNTIME_YAML_REL
        if candidate.exists():
            return candidate
        if d.parent == d:
            return None
        d = d.parent


def read_runtime_root(yaml_path: Path) -> Optional[Path]:
    """Extract the `runtime_root:` value from a runtime.yaml. Abs path or None."""
    try:
        text = Path(yaml_path).read_text(encoding="utf-8")
    except OSError:
        return None
    m = _RUNTIME_ROOT_RE.search(text)
    if not m:
        return None
    val = m.group(1).strip().strip('"').strip("'")
    if not val:
        return None
    return Path(val).expanduser().resolve()


def read_runtime_code(yaml_path: Path) -> Optional[Path]:
    """Extract the `runtime_code:` value (CODE root) from a runtime.yaml.

    Parallel to read_runtime_root but for the central-runtime CODE path used by
    the per-project shim. Returns an absolute Path or None when unset/unreadable.
    """
    try:
        text = Path(yaml_path).read_text(encoding="utf-8")
    except OSError:
        return None
    m = _RUNTIME_CODE_RE.search(text)
    if not m:
        return None
    val = m.group(1).strip().strip('"').strip("'")
    if not val:
        return None
    return Path(val).expanduser().resolve()


def read_engine_source_sha(start: Path) -> Optional[str]:
    """Read the running engine's provenance hash (.trinity-runtime.json source_sha).

    Resolves the engine CODE root via the instance's .ai/runtime.yaml runtime_code:
    pointer, then reads `<engine>/.trinity-runtime.json`'s `source_sha`. Returns None
    fail-soft when there is no runtime.yaml (source-mode — no pointer indirection,
    hence no in-flight drift to detect), no runtime_code:, or the provenance file is
    missing / unreadable / malformed. Never raises — this is a warn-only signal.
    """
    try:
        yaml_path = find_runtime_yaml(Path(start))
        if yaml_path is None:
            return None
        engine_root = read_runtime_code(yaml_path)
        if engine_root is None:
            return None
        data = json.loads(
            (engine_root / ".trinity-runtime.json").read_text(encoding="utf-8")
        )
        sha = data.get("source_sha")
        return str(sha) if sha else None
    except (OSError, ValueError, TypeError):
        return None


def resolve_runtime_home(
    env: Optional[Dict[str, str]] = None,
    start_dir: Optional[Path] = None,
    strict: bool = True,
) -> Optional[Path]:
    """Resolve the runtime root per SPEC. Raises if strict and unresolved."""
    e = os.environ if env is None else env

    raw = e.get("TRINITY_HOME")
    if raw and str(raw).strip():
        return Path(str(raw).strip()).expanduser().resolve()

    start = Path(start_dir) if start_dir else Path.cwd()
    yaml_path = find_runtime_yaml(start)
    if yaml_path:
        root = read_runtime_root(yaml_path)
        if root:
            return root

    if strict:
        raise RuntimeNotConfiguredError()
    return None


def write_runtime_yaml(
    instance_root: Path,
    runtime_root: Path,
    runtime_code: Optional[Path] = None,
) -> Path:
    """Declare the runtime at <instance>/.ai/runtime.yaml. Returns the path.

    `runtime_root` = STATE root (where <root>/state/<name> lives).
    `runtime_code` (optional) = CODE root of the central runtime, read by the
    per-project `.ai/ai` shim to exec the kernel. When omitted, only runtime_root
    is written (back-compat).
    """
    ai_dir = Path(instance_root).expanduser().resolve() / ".ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = ai_dir / "runtime.yaml"
    abs_root = Path(runtime_root).expanduser().resolve()
    lines = [
        "# Trinity runtime declaration (written by `ai config set-runtime`)",
        f"runtime_root: {abs_root}",
    ]
    if runtime_code is not None:
        abs_code = Path(runtime_code).expanduser().resolve()
        lines.append(f"runtime_code: {abs_code}")
    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return yaml_path


def state_dir(name: str, **kwargs) -> Path:
    """<runtime>/state/<name> (created). Mirrors Node siblingStateDir."""
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", name, re.IGNORECASE):
        raise ValueError(f"invalid sibling name: {name!r}")
    root = resolve_runtime_home(**kwargs)
    d = root / "state" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def memory_home(**kwargs) -> Path:
    """<runtime>/memory (created). Mirrors Node memoryHome."""
    root = resolve_runtime_home(**kwargs)
    d = root / "memory"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── central_root (R12) ──────────────────────────────────────────────────────
# Durable operator state that must survive runtime channel switches lives under
# central_root, NOT runtime_root (disposable) and NOT the monorepo (source).
# UNLIKE runtime_root, central_root intentionally DEFAULTS to ~/.trinity-central
# (it is the one durable home location, not scattered state). See design §12.
_CENTRAL_ROOT_RE = re.compile(r"^[ \t]*central_root[ \t]*:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
DEFAULT_CENTRAL_REL = ".trinity-central"


def read_central_root(yaml_path: Path) -> Optional[Path]:
    """Extract the `central_root:` value from a runtime.yaml. Abs path or None."""
    try:
        text = Path(yaml_path).read_text(encoding="utf-8")
    except OSError:
        return None
    m = _CENTRAL_ROOT_RE.search(text)
    if not m:
        return None
    val = m.group(1).strip().strip('"').strip("'")
    return Path(val).expanduser().resolve() if val else None


def resolve_central_home(
    env: Optional[Dict[str, str]] = None,
    start_dir: Optional[Path] = None,
    home: Optional[Path] = None,
) -> Path:
    """Resolve central_root. Order: env TRINITY_CENTRAL -> .ai/runtime.yaml
    central_root -> default <home>/.trinity-central. Never raises (always has a
    default), unlike resolve_runtime_home."""
    e = os.environ if env is None else env
    raw = e.get("TRINITY_CENTRAL")
    if raw and str(raw).strip():
        return Path(str(raw).strip()).expanduser().resolve()
    start = Path(start_dir) if start_dir else Path.cwd()
    yaml_path = find_runtime_yaml(start)
    if yaml_path:
        root = read_central_root(yaml_path)
        if root:
            return root
    base = Path(home) if home is not None else Path.home()
    return (base / DEFAULT_CENTRAL_REL).expanduser().resolve()


def central_memory_home(create: bool = True, **kwargs) -> Path:
    """<central>/memory."""
    d = resolve_central_home(**kwargs) / "memory"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def central_state_dir(name: str, create: bool = True, **kwargs) -> Path:
    """<central>/state/<name>."""
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", name, re.IGNORECASE):
        raise ValueError(f"invalid sibling name: {name!r}")
    d = resolve_central_home(**kwargs) / "state" / name
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def central_registry_home(create: bool = True, **kwargs) -> Path:
    """<central>/registry."""
    d = resolve_central_home(**kwargs) / "registry"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d
