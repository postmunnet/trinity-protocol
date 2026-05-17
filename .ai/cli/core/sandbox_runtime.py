"""Phase 7 Sessions H2/H3/H4 — macOS sandbox-exec runtime hook (fs+net+proc).

Translates `SandboxProfile.{fs,net,proc}` into an Apple Sandbox TinyScheme
`.sb` policy and provides `wrap_argv_with_sandbox_exec` so callers can
prepend `sandbox-exec -f <policy>` to the subprocess argv BEFORE exec,
giving us OS-level mid-action interception for the fs + net + proc axes.

Scope (POC):
- fs axis (H2): read_roots is unrestricted (read* always allowed); write_roots
  produce `(allow file-write* (subpath ...))`; forbidden_paths produce
  `(deny file-write*/file-read* ...)`.
- net axis (H3): outbound={'denied','open'} → `(deny|allow network*)`.
  'allowlist' mode degrades to deny + emits a warning — Apple sandbox-exec
  lacks native hostname allowlist support (IP-only rules without DNS).
- proc axis (H4): forbidden_binaries → per-entry
  `(deny process-exec (literal "..."))`; spawn_allowed=False →
  `(deny process-fork*)`. allowed_binaries (non-empty) is OUT OF POC
  scope — supporting it requires injecting the wrapped tool's bin into
  the allowlist or the wrap itself would fail. We log a warning and
  skip allowlist emission.
- Linux seccomp deferred (no Linux dev host today). Callers MUST fail
  closed when a profile declares fs/net/proc axes and sandbox-exec is
  unavailable; tool-only profiles may still use the deterministic
  sandbox_gate checks without OS wrapping.
- Pure functions + tiny I/O helper. No audit emission here — the
  dispatcher still emits the existing started/completed/failed/timeout
  rows, and they will reflect any sandbox-denied write/connect because
  the binary's exit code or stderr will signal it.

Caveats (documented in module-level docstring intentionally — these are
not obvious from reading the code):

- macOS resolves /tmp → /private/tmp; we MUST `Path.resolve()` every
  path before injecting it into the .sb profile or subpath matching
  silently misses (cf. feedback_sqlite_gotchas — same /tmp drift bites
  here too).
- `sandbox-exec` is labelled deprecated by Apple since 10.15 but still
  ships and works as of Darwin 23.x. Absence is not a silent bypass for
  declared fs/net/proc profiles; callers gate via
  `runtime_enforcement_axes`.
- The .sb dialect (`version 1`) is undocumented post-10.15; the syntax
  used here is grounded on `/System/Library/Sandbox/Profiles/*.sb`
  shipped by macOS itself.

Spec anchors:
- docs/specs/TRINITY_SANDBOX_CAPABILITY_SPEC_V1.md §2.1 (fs axis)
- docs/specs/TRINITY_TOOL_CAPABILITY_MODEL_V1.md §3 (mid-action hook
  surface — until now empty for fs axis)
"""
from __future__ import annotations

import platform
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from cli.core.sandbox_contract import SandboxProfile


SANDBOX_EXEC_PATH = "/usr/bin/sandbox-exec"

# Mirror of sandbox_contract.NET_OUTBOUND_MODES (kept as plain str constants
# so callers can match without importing the frozenset).
NET_OUTBOUND_DENIED = "denied"
NET_OUTBOUND_OPEN = "open"
NET_OUTBOUND_ALLOWLIST = "allowlist"


def is_sandbox_exec_available() -> bool:
    """True iff macOS sandbox-exec exists and can apply a minimal policy.

    Some hosted/sandboxed macOS processes can see `/usr/bin/sandbox-exec`
    but fail `sandbox_apply` with "Operation not permitted". Treat that
    as unavailable so callers fail soft before wrapping subprocesses.
    """
    if platform.system() != "Darwin":
        return False
    sandbox_exec = shutil.which("sandbox-exec")
    if sandbox_exec is None and Path(SANDBOX_EXEC_PATH).is_file():
        sandbox_exec = SANDBOX_EXEC_PATH
    if sandbox_exec is None:
        return False

    true_bin = "/usr/bin/true" if Path("/usr/bin/true").is_file() else "/bin/true"
    try:
        proc = subprocess.run(
            [sandbox_exec, "-p", "(version 1)\n(allow default)\n", true_bin],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _resolve_root(root: str, project_root: Path) -> Path:
    """Resolve a profile-declared root to an absolute, real path.

    Profile roots may be repo-relative (e.g. ".ai/sessions/0001/DO/dev/")
    or already absolute. Path.resolve() collapses symlinks so /tmp is
    folded into /private/tmp on macOS — required for subpath matching.
    """
    p = Path(root)
    if not p.is_absolute():
        p = project_root / p
    return p.resolve()


def _build_fs_lines(profile: SandboxProfile, project_root: Path) -> List[str]:
    """fs axis emission (H2). See build_sandbox_profile_text docstring."""
    parts: List[str] = [
        "(allow file-read*)",
        "(deny file-write*)",
    ]
    for root in profile.fs.write_roots:
        resolved = _resolve_root(root, project_root)
        parts.append(f'(allow file-write* (subpath "{resolved}"))')
    for forbidden in profile.fs.forbidden_paths:
        resolved = _resolve_root(forbidden, project_root)
        parts.append(f'(deny file-write* (subpath "{resolved}"))')
        parts.append(f'(deny file-read*  (subpath "{resolved}"))')
    return parts


def resolve_allowlist_hostnames(
    hostnames: List[str], *, timeout_seconds: float = 2.0
) -> Dict[str, List[str]]:
    """S15 — best-effort DNS snapshot of allowlist hostnames.

    Returns a mapping hostname → list of resolved IPv4 addresses (empty
    list when resolution fails). The snapshot is ADVISORY: macOS
    sandbox-exec rejects literal-IP allowlists ('host must be * or
    localhost'), so this resolution can't be turned into per-IP allow
    rules. It is recorded in the .sb policy text as a comment + in the
    `sandbox.allowlist_unenforced` audit row so operators can see the
    intended targets even though enforcement degrades to deny.

    Network I/O: this function performs DNS lookups (one per hostname).
    It is the ONE public function in this module that does I/O; rest
    of the module remains pure (Article XX passive — I/O only on
    explicit invocation).
    """
    out: Dict[str, List[str]] = {}
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout_seconds)
        for h in hostnames:
            try:
                _, _, ips = socket.gethostbyname_ex(h)
                out[h] = list(ips)
            except (socket.gaierror, OSError):
                out[h] = []
    finally:
        socket.setdefaulttimeout(old_timeout)
    return out


def should_emit_unenforced_warning(
    profile: Optional[SandboxProfile],
) -> bool:
    """S15 — true iff the operator declared a hostname allowlist that
    we cannot enforce at the sandbox-exec layer.

    Triggers when:
      - a profile is bound
      - profile.net.outbound == 'allowlist' (operator intent)
      - profile.net.allowlist is non-empty
      - sandbox-exec is available (we WILL wrap; deny fallback active)

    The caller (gogogo) emits `sandbox.allowlist_unenforced` so retro
    analysis can see the gap between declared and actual enforcement.
    """
    if profile is None:
        return False
    mode = (profile.net.outbound or "").strip()
    if mode != NET_OUTBOUND_ALLOWLIST:
        return False
    if not profile.net.allowlist:
        return False
    return is_sandbox_exec_available()


def build_net_sandbox_profile_lines(
    profile: SandboxProfile,
    *,
    resolved_hostnames: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    """net axis emission (H3+S15). Returns .sb lines for the net mode.

    Modes:
      - 'denied'    → (deny network*)
      - 'open'      → (allow network*)
      - 'allowlist' → (deny network*) + warning comment + (S15) resolved
                      hostname snapshot as comments
                      Apple sandbox-exec rejects literal-IP allowlists
                      ('host must be * or localhost'), so true hostname
                      enforcement is impossible at this layer. The safest
                      degradation is to treat allowlist as deny; the
                      operator's intent is recorded as comments in the
                      .sb file for audit replay.

    `resolved_hostnames` is the optional output of
    resolve_allowlist_hostnames(profile.net.allowlist) — when provided
    AND mode == 'allowlist', the .sb file gets a comment line per
    hostname showing the resolved IPs (advisory snapshot).

    Any unrecognised mode also degrades to deny — Article XVI default-deny
    applies at the runtime hook layer the same way it does at the policy
    organ (cf. policy_engine.query).
    """
    mode = (profile.net.outbound or "").strip()
    if mode == NET_OUTBOUND_OPEN:
        return ["(allow network*)"]
    if mode == NET_OUTBOUND_ALLOWLIST:
        lines = [
            "; net.outbound=allowlist degraded to deny",
            "; sandbox-exec has no native hostname allowlist (IP only).",
        ]
        # S15 — record the intended allowlist + resolved IPs as advisory
        # comments so operators inspecting the .sb file see what was
        # requested even though enforcement degrades to deny.
        for host in profile.net.allowlist:
            ips = (resolved_hostnames or {}).get(host, [])
            ips_text = ",".join(ips) if ips else "<unresolved>"
            lines.append(f"; allowlist intent: {host} -> {ips_text}")
        lines.append("(deny network*)")
        return lines
    # 'denied' or unknown → default-deny
    return ["(deny network*)"]


def build_proc_sandbox_profile_lines(profile: SandboxProfile) -> List[str]:
    """proc axis emission (H4). Returns .sb lines for the proc mode.

    Modes:
      - forbidden_binaries non-empty → per-entry
        `(deny process-exec (literal "<path>"))` lines
      - spawn_allowed=False          → `(deny process-fork*)` line
      - allowed_binaries non-empty   → warning comment + skip (POC limit)

    The wrapped tool binary is itself process-exec'd by the wrapper, so
    naive allowlist emission breaks the wrap. POC restricts to deny-side
    enforcement; allowlist support is deferred until the wrapper can
    inject the tool's bin into the allowlist automatically.
    """
    parts: List[str] = []
    for forbidden in profile.proc.forbidden_binaries:
        # Emit the literal as-given. sandbox-exec matches by literal
        # path; symlink resolution would defeat the operator's intent.
        parts.append(f'(deny process-exec (literal "{forbidden}"))')
    if not profile.proc.spawn_allowed:
        # Only emit when the operator explicitly disallowed spawn.
        # An empty default profile.proc (spawn_allowed defaults to False
        # in the dataclass) is treated as "operator hasn't declared" iff
        # forbidden_binaries is also empty — see should_wrap_proc.
        if profile.proc.forbidden_binaries or _proc_axis_explicitly_declared(profile):
            parts.append("(deny process-fork*)")
    if profile.proc.allowed_binaries:
        parts.insert(0, "; proc.allowed_binaries non-empty — POC limit, allowlist not emitted")
    return parts


def _proc_axis_explicitly_declared(profile: SandboxProfile) -> bool:
    """Heuristic: True iff operator authored a proc block (vs default).

    Used to disambiguate the default `spawn_allowed=False` (no proc
    block) from an explicit `spawn_allowed=False` (operator wrote it).
    For POC, we treat any of (forbidden_binaries, allowed_binaries,
    max_wallclock_seconds>0) as evidence of an authored block.
    """
    if profile.proc.forbidden_binaries:
        return True
    if profile.proc.allowed_binaries:
        return True
    if profile.proc.max_wallclock_seconds and profile.proc.max_wallclock_seconds > 0:
        return True
    return False


def build_sandbox_profile_text(
    profile: SandboxProfile, project_root: Path
) -> str:
    """Render a combined fs+net `.sb` TinyScheme policy text.

    Layout:
      (version 1)
      (deny default)                       ; default-deny everything
      (allow process-fork)                  ; wrapped binary must fork+exec
      (allow process-exec)
      (allow sysctl-read)                   ; dyld + libc need a few sysctls
      (allow signal (target self))          ; SIGCHLD etc.

      ; fs axis (H2)
      (allow file-read*)                    ; reads unrestricted in POC
      (deny file-write*)                    ; default-deny writes
      (allow file-write* (subpath ...))     ; per profile.fs.write_roots
      (deny file-write* (subpath ...))      ; per profile.fs.forbidden_paths
      (deny file-read*  (subpath ...))      ; per profile.fs.forbidden_paths

      ; net axis (H3)
      (deny network*) | (allow network*)    ; per profile.net.outbound

    Notes on fs.read: the POC keeps file-read* fully permissive because
    constraining reads safely requires also allowing the system
    framework dirs (/usr, /System, /Library, dyld cache) which expand
    the profile well beyond the POC's scope. The write axis is what
    actually protects the workspace; the net axis is what gates egress.
    """
    parts: List[str] = [
        "(version 1)",
        "(deny default)",
        "(allow process-fork)",
        "(allow process-exec)",
        "(allow sysctl-read)",
        "(allow signal (target self))",
    ]
    parts.extend(_build_fs_lines(profile, project_root))
    parts.extend(build_net_sandbox_profile_lines(profile))
    parts.extend(build_proc_sandbox_profile_lines(profile))
    return "\n".join(parts) + "\n"


def build_fs_sandbox_profile(profile: SandboxProfile, project_root: Path) -> str:
    """Back-compat alias for `build_sandbox_profile_text`.

    Phase 7 Session H2 named this function for the fs-only POC; H3 extended
    it to also emit net axis directives. The fs-only callers / tests from
    H2 keep working because the additional net lines are appended after
    the fs block, not in place of it.
    """
    return build_sandbox_profile_text(profile, project_root)


def write_profile_to_tmp(text: str, *, prefix: str = "trinity-sb-") -> Path:
    """Write a `.sb` profile to a tempfile and return its path.

    Caller is responsible for unlinking the file after use (or relying
    on tmp cleanup). The file is created with restrictive perms (600)
    so only the kernel + process owner can read it.
    """
    fd, path_str = tempfile.mkstemp(prefix=prefix, suffix=".sb")
    path = Path(path_str)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    path.chmod(0o600)
    return path


def wrap_argv_with_sandbox_exec(argv: List[str], profile_path: Path) -> List[str]:
    """Prepend `sandbox-exec -f <profile_path>` to the argv list.

    Returns a fresh list — does not mutate the input. Caller is
    responsible for ensuring `is_sandbox_exec_available()` returned True
    before calling this; on a non-Darwin host the wrapped argv would
    fail at subprocess.run with ENOENT, which is louder than silent
    bypass — that is intentional.
    """
    return [SANDBOX_EXEC_PATH, "-f", str(profile_path), *argv]


def should_wrap_fs(profile: Optional[SandboxProfile]) -> bool:
    """Decide whether the fs axis hook should activate for this profile.

    The hook activates only when:
      - a profile is bound to the call
      - profile.fs has at least one declared write_root or forbidden_path
        (an empty fs axis means the operator hasn't declared an fs
        boundary, so wrapping would over-constrain by default-denying
        all writes)
      - sandbox-exec is available on this host
    """
    if profile is None:
        return False
    if not (profile.fs.write_roots or profile.fs.forbidden_paths):
        return False
    return is_sandbox_exec_available()


def should_wrap_net(profile: Optional[SandboxProfile]) -> bool:
    """Decide whether the net axis hook should activate.

    Activates when profile.net.outbound is in NET_OUTBOUND_MODES other
    than 'open' (we wrap to enforce deny / allowlist-degraded-to-deny).
    'open' is functionally equivalent to no wrap so we skip — keeps the
    wrapped subprocess overhead off for the common no-net-restriction
    case.
    """
    if profile is None:
        return False
    mode = (profile.net.outbound or "").strip()
    if mode in ("", NET_OUTBOUND_OPEN):
        return False
    return is_sandbox_exec_available()


def should_wrap_proc(profile: Optional[SandboxProfile]) -> bool:
    """Decide whether the proc axis hook should activate.

    Activates when profile.proc has any of:
      - forbidden_binaries non-empty (per-binary deny)
      - allowed_binaries non-empty (warning + skip, but the operator
        DID author a proc block — so wrap to apply other axes too)
      - max_wallclock_seconds > 0 (evidence of authored proc block)

    spawn_allowed=False alone (the dataclass default) is NOT enough —
    that would over-wrap every default profile.
    """
    if profile is None:
        return False
    if not _proc_axis_explicitly_declared(profile):
        return False
    return is_sandbox_exec_available()


def runtime_enforcement_axes(profile: Optional[SandboxProfile]) -> List[str]:
    """Return declared axes that require OS-level runtime enforcement.

    Tool allow/deny is enforced deterministically by `sandbox_gate` and is
    not listed here. Any non-empty result means a caller must either wrap
    with sandbox-exec or fail closed when sandbox-exec is unavailable.
    """
    if profile is None:
        return []
    axes: List[str] = []
    if (
        profile.fs.read_roots
        or profile.fs.write_roots
        or profile.fs.delete_roots
        or profile.fs.forbidden_paths
        or profile.fs.max_bytes_per_file
        or profile.fs.max_total_bytes
    ):
        axes.append("fs")
    mode = (profile.net.outbound or "").strip()
    if mode and mode != NET_OUTBOUND_OPEN:
        axes.append("net")
    elif profile.net.allowlist or profile.net.protocols:
        axes.append("net")
    if _proc_axis_explicitly_declared(profile):
        axes.append("proc")
    return axes


def should_wrap(profile: Optional[SandboxProfile]) -> bool:
    """Decide whether ANY axis hook should activate.

    Combined predicate: returns True iff at least one declared axis
    (fs, net, or proc) is non-trivial AND sandbox-exec is available.
    This is the predicate gogogo's wire uses to gate the wrapper.
    """
    return (
        should_wrap_fs(profile)
        or should_wrap_net(profile)
        or should_wrap_proc(profile)
    )


__all__ = [
    "SANDBOX_EXEC_PATH",
    "NET_OUTBOUND_DENIED",
    "NET_OUTBOUND_OPEN",
    "NET_OUTBOUND_ALLOWLIST",
    "is_sandbox_exec_available",
    "build_fs_sandbox_profile",
    "build_net_sandbox_profile_lines",
    "build_proc_sandbox_profile_lines",
    "build_sandbox_profile_text",
    "resolve_allowlist_hostnames",
    "write_profile_to_tmp",
    "wrap_argv_with_sandbox_exec",
    "should_emit_unenforced_warning",
    "should_wrap_fs",
    "should_wrap_net",
    "should_wrap_proc",
    "runtime_enforcement_axes",
    "should_wrap",
]
