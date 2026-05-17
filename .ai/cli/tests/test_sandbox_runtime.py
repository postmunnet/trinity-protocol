"""Phase 7 Session H2 — sandbox-exec runtime hook unit + integration tests.

Layer 1 — pure unit tests that run on every host:
  - `is_sandbox_exec_available()` returns a bool
  - `build_fs_sandbox_profile` renders deny/allow lines from SandboxProfile
  - `wrap_argv_with_sandbox_exec` prepends sandbox-exec correctly
  - `write_profile_to_tmp` writes a 0600 .sb file
  - `should_wrap_fs` decision matrix
  - `dispatch_tool` honours `argv_transform` (back-compat: None = unchanged)

Layer 2 — Darwin-only integration test:
  - Dispatch a tool whose binary writes to a path outside write_roots →
    the sandbox should block the write, even though dispatch_tool itself
    returns exit 0 from /bin/sh.
"""
from __future__ import annotations

import os
import platform
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from cli.core.audit import AuditChain
from cli.core.executor import ExecutionLease
from cli.core.sandbox_contract import (
    AuthorityCapability,
    FsCapability,
    NetCapability,
    ProcCapability,
    SandboxProfile,
    ToolsCapability,
)
from cli.core.sandbox_runtime import (
    NET_OUTBOUND_ALLOWLIST,
    NET_OUTBOUND_DENIED,
    NET_OUTBOUND_OPEN,
    SANDBOX_EXEC_PATH,
    build_fs_sandbox_profile,
    build_net_sandbox_profile_lines,
    build_sandbox_profile_text,
    is_sandbox_exec_available,
    runtime_enforcement_axes,
    should_wrap,
    should_wrap_fs,
    should_wrap_net,
    wrap_argv_with_sandbox_exec,
    write_profile_to_tmp,
)
from cli.core.tool_dispatcher import dispatch_tool
from cli.core.tool_registry import ToolCapabilityRecord


# ─── fixtures ────────────────────────────────────────────────────────


def _empty_profile() -> SandboxProfile:
    return SandboxProfile(
        id="test-empty",
        version="1.0",
        fs=FsCapability(
            read_roots=[],
            write_roots=[],
            forbidden_paths=[],
            delete_roots=[],
            max_bytes_per_file=0,
            max_total_bytes=0,
        ),
        net=NetCapability(outbound="denied", allowlist=[], protocols=[]),
        proc=ProcCapability(
            allowed_binaries=[],
            forbidden_binaries=[],
            spawn_allowed=False,
            max_wallclock_seconds=0,
        ),
        tools=ToolsCapability(allowed=[], forbidden=[]),
        authority=AuthorityCapability(
            may_promote=False,
            may_deploy=False,
            may_modify_policies=False,
        ),
    )


def _profile_with_write_roots(write_roots: List[str]) -> SandboxProfile:
    p = _empty_profile()
    return SandboxProfile(
        id=p.id,
        version=p.version,
        fs=FsCapability(
            read_roots=[],
            write_roots=write_roots,
            forbidden_paths=[],
            delete_roots=[],
            max_bytes_per_file=0,
            max_total_bytes=0,
        ),
        net=p.net,
        proc=p.proc,
        tools=p.tools,
        authority=p.authority,
    )


def _profile_with_net_outbound(mode: str) -> SandboxProfile:
    p = _empty_profile()
    return SandboxProfile(
        id=p.id,
        version=p.version,
        fs=p.fs,
        net=NetCapability(outbound=mode, allowlist=[], protocols=[]),
        proc=p.proc,
        tools=p.tools,
        authority=p.authority,
    )


def _profile_with_forbidden(forbidden: List[str]) -> SandboxProfile:
    p = _empty_profile()
    return SandboxProfile(
        id=p.id,
        version=p.version,
        fs=FsCapability(
            read_roots=[],
            write_roots=[],
            forbidden_paths=forbidden,
            delete_roots=[],
            max_bytes_per_file=0,
            max_total_bytes=0,
        ),
        net=p.net,
        proc=p.proc,
        tools=p.tools,
        authority=p.authority,
    )


def _lease(session_id: str = "s1", step_id: str = "1") -> ExecutionLease:
    return ExecutionLease(
        lease_id="01KRQFAKELEASEIDFORTESTIN",
        session_id=session_id,
        step_id=step_id,
        granted_at="2026-05-16T00:00:00Z",
        expires_at="2026-05-16T00:10:00Z",
    )


def _record(name: str, bin_path: str) -> ToolCapabilityRecord:
    return ToolCapabilityRecord(
        name=name,
        required_capabilities=("fs.read",),
        optional_capabilities=(),
        default_tier_requirement="WARM",
        notes="",
        description=f"{name} description",
        path=f"/fake/{name}",
        bin=bin_path,
        schema_version="1",
        contract_version="1.0",
        declared_capabilities=("x",),
        policy_default="safe",
    )


# ─── Layer 1 unit tests ──────────────────────────────────────────────


def test_is_sandbox_exec_available_returns_bool() -> None:
    assert isinstance(is_sandbox_exec_available(), bool)
    if platform.system() != "Darwin":
        assert is_sandbox_exec_available() is False


def test_is_sandbox_exec_available_probes_sandbox_apply_success(monkeypatch) -> None:
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("cli.core.sandbox_runtime.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        "cli.core.sandbox_runtime.shutil.which",
        lambda name: "/usr/bin/sandbox-exec",
    )
    monkeypatch.setattr("cli.core.sandbox_runtime.subprocess.run", fake_run)

    assert is_sandbox_exec_available() is True
    assert calls
    argv, kwargs = calls[0]
    assert argv[:2] == ["/usr/bin/sandbox-exec", "-p"]
    assert "(version 1)" in argv[2]
    assert "(allow default)" in argv[2]
    assert kwargs["timeout"] == 2


def test_is_sandbox_exec_available_false_when_sandbox_apply_denied(monkeypatch) -> None:
    def fake_run(argv, **kwargs):
        return SimpleNamespace(
            returncode=71,
            stdout="",
            stderr="sandbox-exec: sandbox_apply: Operation not permitted",
        )

    monkeypatch.setattr("cli.core.sandbox_runtime.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        "cli.core.sandbox_runtime.shutil.which",
        lambda name: "/usr/bin/sandbox-exec",
    )
    monkeypatch.setattr("cli.core.sandbox_runtime.subprocess.run", fake_run)

    assert is_sandbox_exec_available() is False


def test_build_fs_profile_has_deny_default(tmp_path: Path) -> None:
    text = build_fs_sandbox_profile(_empty_profile(), tmp_path)
    assert "(version 1)" in text
    assert "(deny default)" in text
    assert "(deny file-write*)" in text
    # No write_roots → no allow lines
    assert "(allow file-write*" not in text


def test_build_fs_profile_emits_write_root_allow(tmp_path: Path) -> None:
    workdir = tmp_path / "DO" / "dev"
    workdir.mkdir(parents=True)
    profile = _profile_with_write_roots([str(workdir)])
    text = build_fs_sandbox_profile(profile, tmp_path)
    # Path.resolve() is applied — on macOS /tmp → /private/tmp folding
    # means the line must contain the realpath of workdir.
    resolved = workdir.resolve()
    assert f'(allow file-write* (subpath "{resolved}"))' in text


def test_build_fs_profile_emits_forbidden_deny(tmp_path: Path) -> None:
    secret = tmp_path / "secrets"
    secret.mkdir()
    profile = _profile_with_forbidden([str(secret)])
    text = build_fs_sandbox_profile(profile, tmp_path)
    resolved = secret.resolve()
    assert f'(deny file-write* (subpath "{resolved}"))' in text
    assert f'(deny file-read*  (subpath "{resolved}"))' in text


def test_build_fs_profile_resolves_relative_to_project_root(tmp_path: Path) -> None:
    (tmp_path / ".ai").mkdir()
    profile = _profile_with_write_roots([".ai"])
    text = build_fs_sandbox_profile(profile, tmp_path)
    resolved = (tmp_path / ".ai").resolve()
    assert f'(allow file-write* (subpath "{resolved}"))' in text


def test_wrap_argv_prepends_sandbox_exec(tmp_path: Path) -> None:
    profile_path = tmp_path / "p.sb"
    profile_path.write_text("(version 1)\n(allow default)\n", encoding="utf-8")
    wrapped = wrap_argv_with_sandbox_exec(["/bin/echo", "hello"], profile_path)
    assert wrapped[0] == SANDBOX_EXEC_PATH
    assert wrapped[1] == "-f"
    assert wrapped[2] == str(profile_path)
    assert wrapped[3:] == ["/bin/echo", "hello"]


def test_write_profile_to_tmp_creates_0600_file() -> None:
    path = write_profile_to_tmp("(version 1)\n(allow default)\n")
    try:
        assert path.is_file()
        mode = path.stat().st_mode & 0o777
        assert mode == 0o600, f"expected 0600, got {oct(mode)}"
        content = path.read_text(encoding="utf-8")
        assert "(version 1)" in content
    finally:
        path.unlink(missing_ok=True)


def test_should_wrap_fs_none_profile_returns_false() -> None:
    assert should_wrap_fs(None) is False


def test_should_wrap_fs_empty_fs_returns_false() -> None:
    # Empty fs axis → don't wrap (operator hasn't declared a boundary).
    assert should_wrap_fs(_empty_profile()) is False


def test_should_wrap_fs_with_write_roots_matches_availability() -> None:
    profile = _profile_with_write_roots(["/tmp"])
    expected = is_sandbox_exec_available()
    assert should_wrap_fs(profile) is expected


def test_dispatch_tool_argv_transform_default_unchanged(tmp_path: Path) -> None:
    """Back-compat: argv_transform=None preserves byte-identical exec."""
    chain = AuditChain(tmp_path / "events.ndjson")
    chain.append("genesis", {"v": 1})
    record = _record("echo", "/bin/echo")
    result = dispatch_tool(
        lease=_lease(),
        record=record,
        args=["hi"],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
    )
    assert result.exit_code == 0
    assert "hi" in result.stdout


def test_dispatch_tool_argv_transform_applied(tmp_path: Path) -> None:
    """argv_transform mutates the argv before exec."""
    chain = AuditChain(tmp_path / "events.ndjson")
    chain.append("genesis", {"v": 1})
    record = _record("true", "/usr/bin/false")
    # Transform "/usr/bin/false hi" → "/usr/bin/true hi" so exit=0.
    def _swap(argv: List[str]) -> List[str]:
        return ["/usr/bin/true"] + argv[1:]

    result = dispatch_tool(
        lease=_lease(),
        record=record,
        args=["hi"],
        chain=chain,
        project_root=tmp_path,
        timeout_seconds=5,
        argv_transform=_swap,
    )
    # Without the transform, /usr/bin/false would exit 1.
    assert result.exit_code == 0


# ─── Layer 2 Darwin-only integration ─────────────────────────────────


@pytest.mark.skipif(
    not is_sandbox_exec_available(),
    reason="sandbox-exec only on Darwin/macOS",
)
def test_sandbox_blocks_write_outside_write_roots(tmp_path: Path) -> None:
    """End-to-end: a tool that writes outside write_roots is OS-blocked.

    We dispatch /bin/sh -c "echo hi > <outside_path>" wrapped under a
    sandbox profile whose write_roots = [<allowed_dir>]. After the
    subprocess exits, <outside_path> must NOT exist.
    """
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.txt"

    profile = _profile_with_write_roots([str(allowed)])
    profile_text = build_fs_sandbox_profile(profile, tmp_path)
    profile_path = write_profile_to_tmp(profile_text)

    try:
        chain = AuditChain(tmp_path / "events.ndjson")
        chain.append("genesis", {"v": 1})
        record = _record("sh", "/bin/sh")
        result = dispatch_tool(
            lease=_lease(),
            record=record,
            args=["-c", f"echo hi > {outside}"],
            chain=chain,
            project_root=tmp_path,
            timeout_seconds=5,
            argv_transform=lambda argv: wrap_argv_with_sandbox_exec(
                argv, profile_path
            ),
        )
    finally:
        profile_path.unlink(missing_ok=True)

    # The sandbox blocks the write; the file MUST NOT exist.
    assert not outside.exists(), (
        "sandbox-exec failed to block file-write outside allowed root "
        f"(stdout={result.stdout!r}, stderr={result.stderr!r})"
    )
    # The redirect failure surfaces on stderr.
    assert "Operation not permitted" in result.stderr or "denied" in result.stderr.lower()


@pytest.mark.skipif(
    not is_sandbox_exec_available(),
    reason="sandbox-exec only on Darwin/macOS",
)
def test_sandbox_allows_write_inside_write_roots(tmp_path: Path) -> None:
    """End-to-end: a tool that writes INSIDE write_roots succeeds."""
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    target = allowed / "ok.txt"

    profile = _profile_with_write_roots([str(allowed)])
    profile_text = build_fs_sandbox_profile(profile, tmp_path)
    profile_path = write_profile_to_tmp(profile_text)

    try:
        chain = AuditChain(tmp_path / "events.ndjson")
        chain.append("genesis", {"v": 1})
        record = _record("sh", "/bin/sh")
        dispatch_tool(
            lease=_lease(),
            record=record,
            args=["-c", f"echo hello > {target}"],
            chain=chain,
            project_root=tmp_path,
            timeout_seconds=5,
            argv_transform=lambda argv: wrap_argv_with_sandbox_exec(
                argv, profile_path
            ),
        )
    finally:
        profile_path.unlink(missing_ok=True)

    assert target.exists()
    assert "hello" in target.read_text()

# ─── Layer 1 net axis unit tests (H3) ────────────────────────────────


def test_build_net_lines_denied() -> None:
    profile = _profile_with_net_outbound(NET_OUTBOUND_DENIED)
    lines = build_net_sandbox_profile_lines(profile)
    assert lines == ["(deny network*)"]


def test_build_net_lines_open() -> None:
    profile = _profile_with_net_outbound(NET_OUTBOUND_OPEN)
    lines = build_net_sandbox_profile_lines(profile)
    assert lines == ["(allow network*)"]


def test_build_net_lines_allowlist_degrades_to_deny() -> None:
    profile = _profile_with_net_outbound(NET_OUTBOUND_ALLOWLIST)
    lines = build_net_sandbox_profile_lines(profile)
    # Must include (deny network*) — not (allow ...).
    assert "(deny network*)" in lines
    assert "(allow network*)" not in lines
    # And carry a warning comment so audit consumers see the degradation.
    assert any("allowlist" in ln for ln in lines)


def test_build_net_lines_unknown_mode_degrades_to_deny() -> None:
    """Article XVI default-deny applies to unknown net modes."""
    profile = _profile_with_net_outbound("zombie")
    lines = build_net_sandbox_profile_lines(profile)
    assert lines == ["(deny network*)"]


def test_build_sandbox_profile_text_combines_fs_and_net(tmp_path: Path) -> None:
    """Combined builder emits both fs + net directives in one text."""
    workdir = tmp_path / "DO" / "dev"
    workdir.mkdir(parents=True)
    profile = _empty_profile()
    profile = SandboxProfile(
        id=profile.id,
        version=profile.version,
        fs=FsCapability(
            read_roots=[],
            write_roots=[str(workdir)],
            forbidden_paths=[],
            delete_roots=[],
            max_bytes_per_file=0,
            max_total_bytes=0,
        ),
        net=NetCapability(outbound=NET_OUTBOUND_DENIED, allowlist=[], protocols=[]),
        proc=profile.proc,
        tools=profile.tools,
        authority=profile.authority,
    )
    text = build_sandbox_profile_text(profile, tmp_path)
    resolved = workdir.resolve()
    assert f'(allow file-write* (subpath "{resolved}"))' in text
    assert "(deny network*)" in text


def test_build_fs_sandbox_profile_back_compat_includes_net(tmp_path: Path) -> None:
    """Back-compat alias must produce identical output to build_sandbox_profile_text."""
    profile = _profile_with_net_outbound(NET_OUTBOUND_OPEN)
    fs_alias = build_fs_sandbox_profile(profile, tmp_path)
    new_combined = build_sandbox_profile_text(profile, tmp_path)
    assert fs_alias == new_combined


# ─── should_wrap predicate matrix ────────────────────────────────────


def test_should_wrap_none_profile_returns_false() -> None:
    assert should_wrap(None) is False


def test_should_wrap_empty_profile_returns_false() -> None:
    """Empty fs AND open net → no wrap needed."""
    p = _profile_with_net_outbound(NET_OUTBOUND_OPEN)
    assert should_wrap_net(p) is False
    assert should_wrap_fs(p) is False
    assert should_wrap(p) is False


def test_should_wrap_net_denied_triggers_wrap() -> None:
    p = _profile_with_net_outbound(NET_OUTBOUND_DENIED)
    expected = is_sandbox_exec_available()
    assert should_wrap_net(p) is expected
    assert should_wrap(p) is expected


def test_should_wrap_net_allowlist_triggers_wrap() -> None:
    """allowlist degrades to deny — still wants the wrapper."""
    p = _profile_with_net_outbound(NET_OUTBOUND_ALLOWLIST)
    expected = is_sandbox_exec_available()
    assert should_wrap_net(p) is expected


def test_runtime_enforcement_axes_open_tool_only_profile_is_empty() -> None:
    p = _profile_with_net_outbound(NET_OUTBOUND_OPEN)
    p.tools.allowed.append("alpha")
    assert runtime_enforcement_axes(p) == []


def test_runtime_enforcement_axes_reports_declared_os_axes(tmp_path: Path) -> None:
    p = _profile_with_write_roots([str(tmp_path)])
    assert runtime_enforcement_axes(p) == ["fs", "net"]


def test_runtime_enforcement_axes_reports_net_denied() -> None:
    p = _profile_with_net_outbound(NET_OUTBOUND_DENIED)
    assert runtime_enforcement_axes(p) == ["net"]


def test_runtime_enforcement_axes_reports_proc() -> None:
    p = _profile_with_proc(forbidden_binaries=["/bin/cat"])
    assert "proc" in runtime_enforcement_axes(p)


def test_should_wrap_combined_fs_only(tmp_path: Path) -> None:
    """fs declared + net open → wrap (for fs)."""
    p = _profile_with_write_roots([str(tmp_path)])
    expected = is_sandbox_exec_available()
    assert should_wrap_fs(p) is expected
    # net axis defaults to "denied" in _empty_profile builder which means
    # should_wrap_net is also True; the fs path is what matters here.
    assert should_wrap(p) is expected


# ─── Darwin-only net integration ─────────────────────────────────────


def _dns_resolves_example_com() -> bool:
    """Pre-check: only run the net integration if real DNS works."""
    import socket
    try:
        socket.setdefaulttimeout(3)
        socket.gethostbyname("example.com")
        return True
    except Exception:
        return False
    finally:
        socket.setdefaulttimeout(None)


@pytest.mark.skipif(
    not is_sandbox_exec_available() or not _dns_resolves_example_com(),
    reason="sandbox-exec only on Darwin AND network must be reachable for baseline",
)
def test_sandbox_blocks_dns_when_net_denied(tmp_path: Path) -> None:
    """End-to-end: with net.outbound=denied, DNS resolution is OS-blocked.

    Runs `python3 -c "import socket; socket.gethostbyname('example.com')"`
    under the sandbox; without the wrap this would succeed; with the wrap
    the syscall is denied at the kernel level → CalledProcessError exit !=0.
    """
    profile = _profile_with_net_outbound(NET_OUTBOUND_DENIED)
    profile_text = build_sandbox_profile_text(profile, tmp_path)
    profile_path = write_profile_to_tmp(profile_text)

    try:
        chain = AuditChain(tmp_path / "events.ndjson")
        chain.append("genesis", {"v": 1})
        record = _record("py3", "/usr/bin/python3")
        result = dispatch_tool(
            lease=_lease(),
            record=record,
            args=[
                "-c",
                "import socket,sys\ntry:\n    socket.gethostbyname('example.com')\n    sys.exit(0)\nexcept Exception:\n    sys.exit(7)",
            ],
            chain=chain,
            project_root=tmp_path,
            timeout_seconds=10,
            argv_transform=lambda argv: wrap_argv_with_sandbox_exec(
                argv, profile_path
            ),
        )
    finally:
        profile_path.unlink(missing_ok=True)

    # When sandbox denies network, the python script exits 7.
    assert result.exit_code == 7, (
        f"expected DNS resolution to be sandbox-denied "
        f"(stdout={result.stdout!r}, stderr={result.stderr!r}, exit={result.exit_code})"
    )


@pytest.mark.skipif(
    not is_sandbox_exec_available() or not _dns_resolves_example_com(),
    reason="sandbox-exec only on Darwin AND network must be reachable",
)
def test_sandbox_allows_dns_when_net_open(tmp_path: Path) -> None:
    """End-to-end: with net.outbound=open, DNS resolution still works."""
    profile = _profile_with_net_outbound(NET_OUTBOUND_OPEN)
    profile_text = build_sandbox_profile_text(profile, tmp_path)
    profile_path = write_profile_to_tmp(profile_text)

    try:
        chain = AuditChain(tmp_path / "events.ndjson")
        chain.append("genesis", {"v": 1})
        record = _record("py3", "/usr/bin/python3")
        result = dispatch_tool(
            lease=_lease(),
            record=record,
            args=[
                "-c",
                "import socket,sys\ntry:\n    socket.gethostbyname('example.com')\n    sys.exit(0)\nexcept Exception:\n    sys.exit(7)",
            ],
            chain=chain,
            project_root=tmp_path,
            timeout_seconds=10,
            argv_transform=lambda argv: wrap_argv_with_sandbox_exec(
                argv, profile_path
            ),
        )
    finally:
        profile_path.unlink(missing_ok=True)

    assert result.exit_code == 0, (
        f"expected DNS resolution to succeed under net=open "
        f"(stdout={result.stdout!r}, stderr={result.stderr!r})"
    )


# ─── proc axis fixtures + unit tests (H4) ────────────────────────────


def _profile_with_proc(
    forbidden_binaries=None,
    allowed_binaries=None,
    spawn_allowed=True,
    max_wallclock_seconds=0,
) -> SandboxProfile:
    p = _empty_profile()
    return SandboxProfile(
        id=p.id,
        version=p.version,
        fs=p.fs,
        net=NetCapability(outbound="open", allowlist=[], protocols=[]),
        proc=ProcCapability(
            allowed_binaries=list(allowed_binaries or []),
            forbidden_binaries=list(forbidden_binaries or []),
            spawn_allowed=spawn_allowed,
            max_wallclock_seconds=max_wallclock_seconds,
        ),
        tools=p.tools,
        authority=p.authority,
    )


def test_build_proc_lines_forbidden_binaries() -> None:
    from cli.core.sandbox_runtime import build_proc_sandbox_profile_lines
    profile = _profile_with_proc(forbidden_binaries=["/bin/cat", "/usr/bin/curl"])
    lines = build_proc_sandbox_profile_lines(profile)
    assert '(deny process-exec (literal "/bin/cat"))' in lines
    assert '(deny process-exec (literal "/usr/bin/curl"))' in lines


def test_build_proc_lines_spawn_disallowed_emits_fork_deny() -> None:
    from cli.core.sandbox_runtime import build_proc_sandbox_profile_lines
    # Need to also declare a forbidden binary so the proc block counts as
    # "explicitly authored" (per _proc_axis_explicitly_declared).
    profile = _profile_with_proc(
        forbidden_binaries=["/usr/bin/curl"], spawn_allowed=False
    )
    lines = build_proc_sandbox_profile_lines(profile)
    assert "(deny process-fork*)" in lines


def test_build_proc_lines_default_no_emission() -> None:
    """Default proc (empty + spawn_allowed=True) → no lines."""
    from cli.core.sandbox_runtime import build_proc_sandbox_profile_lines
    profile = _profile_with_proc()  # all defaults
    lines = build_proc_sandbox_profile_lines(profile)
    assert lines == []


def test_build_proc_lines_allowed_binaries_logs_warning_no_emission() -> None:
    """POC limit: allowed_binaries non-empty → warning comment, no allow."""
    from cli.core.sandbox_runtime import build_proc_sandbox_profile_lines
    profile = _profile_with_proc(allowed_binaries=["/bin/sh"])
    lines = build_proc_sandbox_profile_lines(profile)
    # Warning comment present
    assert any("POC limit" in ln or "allowed_binaries" in ln for ln in lines)
    # No (allow process-exec ...) line
    assert not any("(allow process-exec" in ln for ln in lines)


def test_build_sandbox_profile_text_includes_proc_lines(tmp_path: Path) -> None:
    """Combined builder emits proc directives alongside fs+net."""
    profile = _profile_with_proc(forbidden_binaries=["/bin/cat"])
    text = build_sandbox_profile_text(profile, tmp_path)
    assert '(deny process-exec (literal "/bin/cat"))' in text


# ─── should_wrap_proc decision matrix ────────────────────────────────


def test_should_wrap_proc_none_profile_returns_false() -> None:
    from cli.core.sandbox_runtime import should_wrap_proc
    assert should_wrap_proc(None) is False


def test_should_wrap_proc_default_profile_returns_false() -> None:
    """Default proc (no explicit declaration) → no wrap."""
    from cli.core.sandbox_runtime import should_wrap_proc
    profile = _profile_with_proc()
    assert should_wrap_proc(profile) is False


def test_should_wrap_proc_forbidden_triggers_wrap() -> None:
    from cli.core.sandbox_runtime import should_wrap_proc
    profile = _profile_with_proc(forbidden_binaries=["/usr/bin/curl"])
    expected = is_sandbox_exec_available()
    assert should_wrap_proc(profile) is expected


def test_should_wrap_proc_allowed_triggers_wrap() -> None:
    """Even though allowlist emission is skipped, the proc block IS
    authored, so the wrapper should activate (other axes still apply)."""
    from cli.core.sandbox_runtime import should_wrap_proc
    profile = _profile_with_proc(allowed_binaries=["/bin/sh"])
    expected = is_sandbox_exec_available()
    assert should_wrap_proc(profile) is expected


# ─── Darwin-only proc integration ────────────────────────────────────


@pytest.mark.skipif(
    not is_sandbox_exec_available(),
    reason="sandbox-exec only on Darwin/macOS",
)
def test_sandbox_blocks_forbidden_binary(tmp_path: Path) -> None:
    """End-to-end: a tool forbidden by proc.forbidden_binaries cannot exec."""
    profile = _profile_with_proc(forbidden_binaries=["/bin/cat"])
    profile_text = build_sandbox_profile_text(profile, tmp_path)
    profile_path = write_profile_to_tmp(profile_text)

    try:
        chain = AuditChain(tmp_path / "events.ndjson")
        chain.append("genesis", {"v": 1})
        # /bin/sh tries to spawn /bin/cat — should fail under the sandbox.
        record = _record("sh", "/bin/sh")
        result = dispatch_tool(
            lease=_lease(),
            record=record,
            args=["-c", "/bin/cat /etc/hostname >/dev/null 2>&1; echo exit:$?"],
            chain=chain,
            project_root=tmp_path,
            timeout_seconds=5,
            argv_transform=lambda argv: wrap_argv_with_sandbox_exec(
                argv, profile_path
            ),
        )
    finally:
        profile_path.unlink(missing_ok=True)

    # The wrapper itself runs /bin/sh fine; sh's `/bin/cat ...` call is
    # the operation that should be denied. exit:126 is the typical sh
    # exit code for "permission denied" + the stderr should show it.
    assert "exit:" in result.stdout
    # /bin/sh reports "Operation not permitted" when sandbox denies exec
    assert "Operation not permitted" in result.stderr or "not permitted" in result.stderr


@pytest.mark.skipif(
    not is_sandbox_exec_available(),
    reason="sandbox-exec only on Darwin/macOS",
)
def test_sandbox_allows_non_forbidden_binary(tmp_path: Path) -> None:
    """End-to-end: a binary NOT in forbidden_binaries still works under wrap."""
    profile = _profile_with_proc(forbidden_binaries=["/usr/bin/curl"])
    profile_text = build_sandbox_profile_text(profile, tmp_path)
    profile_path = write_profile_to_tmp(profile_text)

    try:
        chain = AuditChain(tmp_path / "events.ndjson")
        chain.append("genesis", {"v": 1})
        record = _record("sh", "/bin/sh")
        result = dispatch_tool(
            lease=_lease(),
            record=record,
            args=["-c", "/bin/echo hello"],
            chain=chain,
            project_root=tmp_path,
            timeout_seconds=5,
            argv_transform=lambda argv: wrap_argv_with_sandbox_exec(
                argv, profile_path
            ),
        )
    finally:
        profile_path.unlink(missing_ok=True)

    assert result.exit_code == 0
    assert "hello" in result.stdout


# ─── S15 net.allowlist hostname snapshot + unenforced warning ────────


from cli.core.sandbox_runtime import (
    resolve_allowlist_hostnames,
    should_emit_unenforced_warning,
)


def _profile_with_allowlist(hostnames: List[str]) -> SandboxProfile:
    p = _empty_profile()
    return SandboxProfile(
        id=p.id,
        version=p.version,
        fs=p.fs,
        net=NetCapability(
            outbound=NET_OUTBOUND_ALLOWLIST,
            allowlist=hostnames,
            protocols=[],
        ),
        proc=p.proc,
        tools=p.tools,
        authority=p.authority,
    )


def test_resolve_allowlist_hostnames_localhost() -> None:
    """localhost always resolves to a known address."""
    out = resolve_allowlist_hostnames(["localhost"])
    assert "localhost" in out
    assert out["localhost"]  # non-empty list of IPs
    # localhost usually resolves to 127.0.0.1 or ::1
    assert any(ip.startswith("127.") or ip == "::1" for ip in out["localhost"])


def test_resolve_allowlist_hostnames_unresolvable_returns_empty_list() -> None:
    """Unresolvable hostnames map to empty list (best-effort)."""
    out = resolve_allowlist_hostnames(["totally.invalid.tld.example.test.notreal"])
    assert "totally.invalid.tld.example.test.notreal" in out
    assert out["totally.invalid.tld.example.test.notreal"] == []


def test_resolve_allowlist_hostnames_empty_input() -> None:
    assert resolve_allowlist_hostnames([]) == {}


def test_should_emit_unenforced_warning_none_profile_false() -> None:
    assert should_emit_unenforced_warning(None) is False


def test_should_emit_unenforced_warning_denied_mode_false() -> None:
    p = _profile_with_net_outbound(NET_OUTBOUND_DENIED)
    assert should_emit_unenforced_warning(p) is False


def test_should_emit_unenforced_warning_open_mode_false() -> None:
    p = _profile_with_net_outbound(NET_OUTBOUND_OPEN)
    assert should_emit_unenforced_warning(p) is False


def test_should_emit_unenforced_warning_allowlist_empty_false() -> None:
    """allowlist mode but empty list → schema validation would normally
    reject this, but the predicate must still return False (nothing to
    warn about)."""
    p = _profile_with_allowlist([])
    assert should_emit_unenforced_warning(p) is False


def test_should_emit_unenforced_warning_allowlist_nonempty_matches_availability() -> None:
    p = _profile_with_allowlist(["example.com"])
    assert should_emit_unenforced_warning(p) is is_sandbox_exec_available()


def test_build_net_lines_allowlist_includes_intent_comments(tmp_path: Path) -> None:
    """S15 — .sb output for allowlist mode includes a comment per hostname
    showing the resolved IPs (advisory snapshot for audit replay)."""
    p = _profile_with_allowlist(["host-a.example", "host-b.example"])
    resolved = {
        "host-a.example": ["1.2.3.4", "1.2.3.5"],
        "host-b.example": [],
    }
    lines = build_net_sandbox_profile_lines(p, resolved_hostnames=resolved)
    assert "(deny network*)" in lines
    assert any("allowlist intent: host-a.example -> 1.2.3.4,1.2.3.5" in ln for ln in lines)
    assert any("allowlist intent: host-b.example -> <unresolved>" in ln for ln in lines)


def test_build_net_lines_allowlist_back_compat_no_resolved(tmp_path: Path) -> None:
    """Old callers (no resolved_hostnames kwarg) still get a valid result."""
    p = _profile_with_allowlist(["host.example"])
    lines = build_net_sandbox_profile_lines(p)
    assert "(deny network*)" in lines
    # Intent line still emitted with <unresolved> marker
    assert any("allowlist intent: host.example -> <unresolved>" in ln for ln in lines)
