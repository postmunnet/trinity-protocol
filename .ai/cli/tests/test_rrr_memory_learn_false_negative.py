"""R47 — rrr's _summarize_memory_index signal-exit recovery.

Originally written for the v0.9 `memory-cli learn` delegation. Phase 1
(2026-05-12) replaced `learn` with the Article-IX-compliant `index`
verb; this test file was renamed semantically (kept the filename to
preserve git history continuity, but the helpers now reference the
`_index` variants).

memory-cli MAY emit its TOOL_CONTRACT envelope to stdout BEFORE a
libc++ destructor abort (R37 caveat, only relevant when running under
MEMORY_CLI_LEGACY=1 since the v0.1 core path no longer loads
fastembed/sqlite-vec). If envelope.ok=true and the process exited via
signal (returncode<0), the SQLite WAL has already committed — trust
the envelope rather than report a false-negative.
"""
from __future__ import annotations

import io
from contextlib import redirect_stdout

from cli.commands.rrr import (
    _summarize_memory_index,
    _print_memory_index,
)
from cli.core.tools_registry import ToolInvocation


def _inv(ok, returncode, envelope, error=None, stdout="", stderr=""):
    return ToolInvocation(
        ok=ok,
        returncode=returncode,
        envelope=envelope,
        stdout=stdout,
        stderr=stderr,
        error=error,
    )


# A_SIGNAL_EXIT_WITH_OK_ENVELOPE --------------------------------------
def test_signal_exit_with_ok_envelope_recovers():
    """returncode=-6 + envelope.ok=true -> trust envelope; note records the signal exit."""
    env = {
        "ok": True,
        "tool_version": "0.9.7-beta",
        "data": {
            "indexed_new": 1,
            "indexed_updated": 0,
            "artifacts_total": 5,
            "chunks_total": 23,
            "schema": "memory-cli-v01-evidence",
        },
    }
    inv = _inv(ok=False, returncode=-6, envelope=env)

    out = _summarize_memory_index(inv)
    assert out["ok"] is True
    assert out["indexed_new"] == 1
    assert out["indexed_updated"] == 0
    assert out["artifacts_total"] == 5
    assert out["chunks_total"] == 23
    assert out["schema"] == "memory-cli-v01-evidence"
    assert out["tool_version"] == "0.9.7-beta"
    assert "note" in out
    assert "signal_exit returncode=-6" in out["note"]
    assert "envelope.ok=true" in out["note"]


# A_SIGNAL_EXIT_WITH_FAIL_ENVELOPE ------------------------------------
def test_signal_exit_with_fail_envelope_still_fails():
    """returncode=-6 but envelope.ok=false -> genuine failure, no recovery."""
    env = {"ok": False, "error": {"code": "internal_error", "message": "boom"}}
    inv = _inv(ok=False, returncode=-6, envelope=env)

    out = _summarize_memory_index(inv)
    assert out["ok"] is False
    assert out["error"] == "boom"


# A_POSITIVE_EXIT_FAIL ------------------------------------------------
def test_positive_exit_does_not_recover():
    """returncode=1 (not signal exit) -> no recovery even if envelope.ok=true."""
    env = {"ok": True, "data": {"indexed_new": 0}}
    inv = _inv(ok=False, returncode=1, envelope=env)

    out = _summarize_memory_index(inv)
    # Positive exit is treated as genuine failure. R47 only covers
    # signal-induced exits (returncode<0). This preserves the safety
    # invariant: "exit code 1 means the tool itself reported failure;
    # don't second-guess that."
    assert out["ok"] is False
    assert "returncode=1" in (out.get("error") or "")


# A_NO_ENVELOPE_FAIL --------------------------------------------------
def test_no_envelope_does_not_recover():
    """returncode=-6 with no envelope -> can't trust anything, fail."""
    inv = _inv(ok=False, returncode=-6, envelope=None)
    out = _summarize_memory_index(inv)
    assert out["ok"] is False
    assert "returncode=-6" in (out.get("error") or "")


# A_PRINT_HELPER_RECOVERED --------------------------------------------
def test_print_helper_emits_recovered_line():
    """_print_memory_index surfaces the recovery distinctly from skip path."""
    env = {
        "ok": True,
        "tool_version": "0.9.7-beta",
        "data": {
            "indexed_new": 1,
            "chunks_total": 7,
            "schema": "memory-cli-v01-evidence",
        },
    }
    inv = _inv(ok=False, returncode=-6, envelope=env)

    from cli.commands import rrr as rrr_mod
    buf = io.StringIO()
    with redirect_stdout(buf):
        from rich.console import Console
        orig = rrr_mod.console
        rrr_mod.console = Console(file=buf, force_terminal=False, color_system=None)
        try:
            _print_memory_index(inv)
        finally:
            rrr_mod.console = orig
    captured = buf.getvalue()
    assert "recovered" in captured
    assert "signal exit" in captured
    assert "indexed_new=1" in captured
    # Must NOT print the failure line.
    assert "FAIL" not in captured.upper().split("MEMORY-CLI INDEX")[0]
