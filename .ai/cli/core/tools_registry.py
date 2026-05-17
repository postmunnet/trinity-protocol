"""Tool registry resolver — load `.ai/tools.yaml` and invoke external
tools via their declared bin command.

Spec: docs/specs/01_TOOL_CONTRACT.md §16 (Tool Registry)
Decision: D13 (Plugin tool architecture).

This is the kernel side of the plugin contract. Tools live outside
the kernel (sibling repos under `${project_root}/../<tool>/`); this
module finds them and runs them, parsing the TOOL_CONTRACT v1 JSON
envelope from stdout.

Phase 2.2+'s first user is `ai rrr` — after writing the canonical
retro file, it pipes the path through `memory-cli index ...` so the
Knowledge Brain can retrieve the evidence later. Phase 2.3 wires
`lll`, `vvv`, and `nnn` against memory-cli `search` / `list`.

Design principles:

- Best-effort by default: a tool failure does not break a kernel
  ritual unless the caller explicitly opts in (`required=True`).
- Path resolution: `${project_root}` token in `tools.yaml` is
  expanded to the resolved Trinity repo root. Absolute paths and
  paths into `.ai/` are forbidden by `test_tools_registry.py`, so we
  trust the registry to be sanitary.
- Subprocess shape: `bin` is split on whitespace and treated as
  `argv` (no shell), then we append `--cmd "<verb> [args]"` (or any
  extra argv supplied by the caller). The kernel never executes a
  shell so verb arguments cannot leak into the host shell.
"""
from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import yaml

logger = logging.getLogger(__name__)

# A1 sibling-discovery — refinement E: schema_version forward-lock.
# Only manifest schema versions starting with "1" are accepted; "2" or
# higher must wait for an explicit breaking-change migration.
_SUPPORTED_MANIFEST_MAJOR = "1"

# A1 — runtime support gate. Only `node` ships in A1; additional runtimes
# (python, rust, shell, binary) reject with a clear NotImplementedError-style
# validation reason so future migrations notice.
_SUPPORTED_RUNTIMES = frozenset({"node"})


@dataclass
class ToolEntry:
    name: str
    bin_argv: List[str]            # already split + ${project_root} expanded
    path: Path                     # tool root directory
    contract_version: str
    schema_version: str
    policy_default: str
    health_check: Optional[str]    # CLI flag like "--health"
    engines_node: Optional[str]    # R15 — minimum Node version (e.g. ">=22.5.0")
    raw: Dict[str, Any]
    # A1 sibling-discovery — refinement B: provenance fields.
    # `source` is "legacy" for tools.yaml entries, "manifest" for entries
    # discovered from per-sibling trinity.yaml manifests. `manifest_path`
    # points at the originating manifest file when source="manifest".
    source: str = "legacy"
    manifest_path: Optional[Path] = None


class SiblingDuplicateError(Exception):
    """Raised when two manifests under TRINITY_SIBLINGS_ROOT claim the same
    tool name. Per refinement D, this is a hard failure: manifest-vs-manifest
    duplicates are misconfiguration, not a legitimate override scenario.
    """
    def __init__(self, name: str, path_a: Path, path_b: Path) -> None:
        super().__init__(
            f"duplicate sibling manifest name {name!r}: "
            f"{path_a} and {path_b}"
        )
        self.name = name
        self.path_a = path_a
        self.path_b = path_b


@dataclass
class ToolInvocation:
    ok: bool                       # True if process exited 0 AND envelope ok
    returncode: int
    envelope: Optional[Dict[str, Any]]
    stdout: str
    stderr: str
    error: Optional[str]           # python-side failure (e.g. ToolNotFound,
                                   # JSONDecode, timeout)


class ToolNotFound(Exception):
    pass


def _expand(token: str, project_root: Path) -> str:
    return token.replace("${project_root}", str(project_root))


def _validate_manifest(
    manifest: Dict[str, Any],
    manifest_path: Path,
) -> Tuple[bool, str]:
    """Validate a per-sibling `trinity.yaml` manifest.

    Returns ``(True, "ok")`` when the manifest is structurally sound and
    safe for the kernel registry. Returns ``(False, reason)`` otherwise.

    Validation rules (A1 refinements C+E):
    - Required fields: schema_version, name, bin, runtime.
    - schema_version forward-lock: only "1" or "1.x" accepted (refinement E).
    - runtime must be in `_SUPPORTED_RUNTIMES` (A1 ships node only).
    - `bin` must be a relative path (refinement C; absolute reject by default).
    - Resolved bin path must stay within the manifest's parent directory
      (path-traversal guard against `bin: "../escape.js"`).
    """
    if not isinstance(manifest, dict):
        return False, "manifest is not a YAML mapping"

    required = ("schema_version", "name", "bin", "runtime")
    missing = [k for k in required if not manifest.get(k)]
    if missing:
        return False, f"missing required fields: {', '.join(missing)}"

    schema_version = str(manifest["schema_version"])
    major = schema_version.split(".", 1)[0].strip()
    if major != _SUPPORTED_MANIFEST_MAJOR:
        return False, (
            f"schema_version forward-lock: only "
            f"{_SUPPORTED_MANIFEST_MAJOR}.x accepted, got {schema_version!r}"
        )

    runtime = str(manifest["runtime"]).strip()
    if runtime not in _SUPPORTED_RUNTIMES:
        return False, (
            f"runtime {runtime!r} not yet supported in A1 "
            f"(supported: {sorted(_SUPPORTED_RUNTIMES)})"
        )

    bin_str = str(manifest["bin"]).strip()
    bin_parts = shlex.split(bin_str)
    if not bin_parts:
        return False, "bin is empty after shlex.split"

    # For runtime=node, bin shape is typically `node ./entry.js` or just
    # `./entry.js`. The script-path token is the last non-flag argv item;
    # it MUST be relative. Absolute paths are rejected by default
    # (refinement C — defer absolute-allow flag to a later phase).
    script_token = bin_parts[-1]
    if script_token.startswith("/"):
        return False, (
            f"absolute bin rejected; bin must be relative to manifest_dir "
            f"(got {script_token!r})"
        )

    manifest_dir = manifest_path.parent.resolve()
    resolved = (manifest_dir / script_token).resolve()
    try:
        resolved.relative_to(manifest_dir)
    except ValueError:
        return False, (
            f"bin path traversal rejected: {script_token!r} resolves outside "
            f"manifest_dir {manifest_dir}"
        )

    return True, "ok"


def _build_manifest_entry(
    manifest: Dict[str, Any],
    manifest_path: Path,
) -> ToolEntry:
    """Construct a ToolEntry from a validated manifest. Caller MUST validate
    first via `_validate_manifest`; this function trusts its input.
    """
    manifest_dir = manifest_path.parent.resolve()
    runtime = str(manifest["runtime"]).strip()
    bin_str = str(manifest["bin"]).strip()
    bin_parts = shlex.split(bin_str)

    # Resolve script token (last argv element) against manifest_dir so the
    # final argv is `[interpreter, <abs script path>, ...]` regardless of
    # which directory invokes the kernel.
    script_token = bin_parts[-1]
    resolved_script = str((manifest_dir / script_token).resolve())
    bin_argv: List[str]
    if runtime == "node":
        # If the manifest already prefixed `node`, replace its script arg
        # with the resolved absolute path. Otherwise prepend `node`.
        if bin_parts[0] == "node":
            bin_argv = ["node", resolved_script] + bin_parts[1:-1]
        else:
            bin_argv = ["node", resolved_script] + bin_parts[:-1]
    else:
        # _validate_manifest already rejected non-node runtimes in A1, but
        # be defensive in case of future extension.
        bin_argv = [resolved_script] + bin_parts[:-1]

    engines = manifest.get("engines") or {}
    engines_node = engines.get("node") if isinstance(engines, dict) else None
    policy = manifest.get("policy") or {}
    policy_default = (
        policy.get("tier") if isinstance(policy, dict) else "normal"
    ) or "normal"
    health = manifest.get("health") or {}
    health_check = (
        health.get("command") if isinstance(health, dict) else None
    )

    return ToolEntry(
        name=str(manifest["name"]),
        bin_argv=bin_argv,
        path=manifest_dir,
        contract_version=str(manifest.get("contract_version", "")),
        schema_version=str(manifest["schema_version"]),
        policy_default=str(policy_default),
        health_check=health_check,
        engines_node=engines_node,
        raw=manifest,
        source="manifest",
        manifest_path=manifest_path.resolve(),
    )


def discover_siblings(
    siblings_root: Optional[Path],
) -> Dict[str, ToolEntry]:
    """Scan `<siblings_root>/*/trinity.yaml` and return manifest entries.

    Direct-child scan only (no rglob) — refinement note "predictable +
    cold-start safe". Returns empty dict when `siblings_root` is None or
    does not exist.

    Raises `SiblingDuplicateError` when two manifests under the same root
    declare the same tool name (refinement D — hard fail, not warn).

    Invalid manifests (failed `_validate_manifest`) are logged at WARNING
    and skipped; they never crash the discovery pass.
    """
    out: Dict[str, ToolEntry] = {}
    if siblings_root is None:
        return out
    root = Path(siblings_root)
    if not root.exists() or not root.is_dir():
        return out

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        manifest_path = child / "trinity.yaml"
        if not manifest_path.exists():
            continue
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as e:
            logger.warning(
                "tools_registry: skipping invalid manifest %s: %s",
                manifest_path, e,
            )
            continue

        ok, reason = _validate_manifest(manifest, manifest_path)
        if not ok:
            logger.warning(
                "tools_registry: skipping invalid manifest %s: %s",
                manifest_path, reason,
            )
            continue

        entry = _build_manifest_entry(manifest, manifest_path)
        if entry.name in out:
            raise SiblingDuplicateError(
                entry.name,
                out[entry.name].manifest_path or Path(""),
                manifest_path.resolve(),
            )
        out[entry.name] = entry

    return out


def load_registry(project_root: Path) -> Dict[str, ToolEntry]:
    """Parse `.ai/tools.yaml` (legacy) and merge with manifest discoveries.

    Discovery is opt-in via the `TRINITY_SIBLINGS_ROOT` environment
    variable: unset → behavior identical to legacy-only path (backward
    compat, zero regression). When set, `<root>/*/trinity.yaml` files
    are discovered and merged; manifest entries WIN by name collision
    with a warning naming both source paths (refinement D).
    """
    out: Dict[str, ToolEntry] = {}

    # Legacy layer — parse .ai/tools.yaml as before; tag entries source=legacy.
    tools_yaml = project_root / ".ai" / "tools.yaml"
    if tools_yaml.exists():
        with tools_yaml.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for entry in data.get("tools") or []:
            name = entry.get("name")
            if not name:
                continue
            bin_str = _expand(entry.get("bin", ""), project_root)
            path_str = _expand(entry.get("path", ""), project_root)
            engines = entry.get("engines") or {}
            engines_node = (
                engines.get("node") if isinstance(engines, dict) else None
            )
            out[name] = ToolEntry(
                name=name,
                bin_argv=shlex.split(bin_str),
                path=Path(path_str),
                contract_version=str(entry.get("contract_version", "")),
                schema_version=str(entry.get("schema_version", "")),
                policy_default=str(entry.get("policy_default", "normal")),
                health_check=entry.get("health_check"),
                engines_node=engines_node,
                raw=entry,
                source="legacy",
                manifest_path=None,
            )

    # Manifest layer — opt-in via TRINITY_SIBLINGS_ROOT.
    siblings_root_env = os.environ.get("TRINITY_SIBLINGS_ROOT", "").strip()
    if siblings_root_env:
        siblings_root = Path(siblings_root_env)
        discovered = discover_siblings(siblings_root)
        for name, entry in discovered.items():
            if name in out:
                legacy_ref = (
                    str(tools_yaml) if out[name].source == "legacy"
                    else str(out[name].manifest_path)
                )
                logger.warning(
                    "tools_registry: manifest override — tool %r from %s "
                    "supersedes legacy entry at %s",
                    name, entry.manifest_path, legacy_ref,
                )
            out[name] = entry

    return out


def find_tool(project_root: Path, name: str) -> ToolEntry:
    reg = load_registry(project_root)
    if name not in reg:
        raise ToolNotFound(
            f"tool {name!r} not registered in .ai/tools.yaml; "
            f"known: {sorted(reg)}"
        )
    return reg[name]


def check_engines_compat(tool: ToolEntry) -> Optional[str]:
    """R15 — best-effort Node-version compat check.

    Returns None if compatible (or no constraint declared / Node missing).
    Returns a human-readable warning string when the running `node` is
    older than `engines.node` declares. The kernel never raises on this:
    sibling tools may still work, and Node version detection itself can
    fail in CI containers; surfacing a warning is cheaper than blocking.
    """
    spec = (tool.engines_node or "").strip()
    if not spec or not spec.startswith(">="):
        return None
    required = spec[2:].strip()
    try:
        proc = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    actual = proc.stdout.strip().lstrip("v")
    if _semver_lt(actual, required):
        return (
            f"tool {tool.name!r} requires node{spec} but found v{actual}; "
            f"may crash on `node:sqlite` (>=22.5) or other recent APIs"
        )
    return None


def _tool_env(project_root: Path, tool_name: str) -> Dict[str, str]:
    """Build subprocess env for a registered tool invocation.

    Memory v0.1 defaults to `<cwd>/.memory/memory.sqlite`, while Trinity's
    canonical evidence DB lives under `.ai/.memory`. Inject the Trinity DB
    path unless an operator already supplied an explicit memory DB override.
    """
    env = os.environ.copy()
    if (
        tool_name == "memory-cli"
        and not env.get("MEMORY_DB")
        and not env.get("TRINITY_MEMORY_DB")
    ):
        env["TRINITY_MEMORY_DB"] = str(
            (project_root / ".ai" / ".memory" / "memory.sqlite").resolve()
        )
    return env


def _semver_lt(a: str, b: str) -> bool:
    """Return True if version `a` is strictly less than `b`. Pre-release
    suffixes (e.g. -beta) are stripped before compare; this is enough
    for the engines.node use case (we only care about major.minor)."""
    def parts(v: str) -> List[int]:
        head = v.split("-", 1)[0]
        out = []
        for piece in head.split("."):
            try:
                out.append(int(piece))
            except ValueError:
                out.append(0)
        return out
    pa, pb = parts(a), parts(b)
    n = max(len(pa), len(pb))
    pa += [0] * (n - len(pa))
    pb += [0] * (n - len(pb))
    return pa < pb


def call(
    project_root: Path,
    tool_name: str,
    cmd: str,
    *,
    timeout_seconds: int = 30,
    extra_argv: Optional[Sequence[str]] = None,
) -> ToolInvocation:
    """Run a tool with `--cmd "<cmd>"` and return the parsed envelope.

    `cmd` is the verb-and-args string (e.g. `'index /abs/p.md'`).
    It is passed as a single argv element after `--cmd`, so internal
    spaces inside the verb string are preserved by the tool's own
    parser — no shell expansion happens.

    Returns a `ToolInvocation` whose `ok` is True only when:
      1. the subprocess exited 0,
      2. stdout parsed as JSON, and
      3. the envelope's `ok` field is True.
    A python-side failure (tool missing, timeout, malformed JSON) is
    surfaced via the `error` field; `envelope` is None in that case.
    """
    try:
        tool = find_tool(project_root, tool_name)
    except ToolNotFound as e:
        return ToolInvocation(
            ok=False, returncode=-1, envelope=None,
            stdout="", stderr="", error=str(e),
        )

    argv = list(tool.bin_argv) + ["--cmd", cmd]
    if extra_argv:
        argv.extend(extra_argv)

    try:
        proc = subprocess.run(
            argv,
            cwd=str(project_root),
            env=_tool_env(project_root, tool_name),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as e:
        return ToolInvocation(
            ok=False, returncode=-1, envelope=None,
            stdout="", stderr="",
            error=f"executable not found: {argv[0]} ({e})",
        )
    except subprocess.TimeoutExpired as e:
        return ToolInvocation(
            ok=False, returncode=-1, envelope=None,
            stdout=e.stdout or "", stderr=e.stderr or "",
            error=f"timeout after {timeout_seconds}s",
        )

    envelope: Optional[Dict[str, Any]] = None
    parse_error: Optional[str] = None
    if proc.stdout.strip():
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            parse_error = f"stdout was not JSON: {e}"

    ok_envelope = bool(envelope and envelope.get("ok") is True)
    ok = proc.returncode == 0 and ok_envelope

    return ToolInvocation(
        ok=ok,
        returncode=proc.returncode,
        envelope=envelope,
        stdout=proc.stdout,
        stderr=proc.stderr,
        error=parse_error,
    )
