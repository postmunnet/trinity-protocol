"""D2 — close --force must carry an audited --reason (no silent skeleton key).

The reason gate runs at the very top of _run_impl, BEFORE any SSOT/session
load, so the negative tests are safe (they exit before touching a session).
The positive emission path is asserted at source level to avoid running a
real close against whatever the kernel's status.json points at.
"""
from __future__ import annotations

import inspect

from typer.testing import CliRunner

import cli.commands.close as close_mod
from cli.commands.close import app

runner = CliRunner()


# ─────────── G5 / G13 — force without reason is rejected ───────────


def test_force_without_reason_rejected() -> None:
    result = runner.invoke(app, ["--force"])
    assert result.exit_code != 0
    assert "reason" in result.output.lower()


def test_force_run_subcommand_without_reason_rejected() -> None:
    result = runner.invoke(app, ["run", "--force"])
    assert result.exit_code != 0
    assert "reason" in result.output.lower()


# ─────────── G6 / G14 — forced close emits audited close.forced ───────────


def test_close_forced_emission_wired() -> None:
    src = inspect.getsource(close_mod)
    assert '"close.forced"' in src, "close must emit a close.forced event"
    assert '"reason": reason' in src, "close.forced must carry the reason"
    assert '"decided_by": "operator"' in src
    assert '"source": "cli_flag"' in src


def test_force_gate_precedes_ssot_load() -> None:
    """The reason check must run before SSOT/session work (fail-fast, safe)."""
    src = inspect.getsource(close_mod)
    gate_idx = src.find("close --force requires --reason")
    ssot_idx = src.find("SSOTLoader(Path.cwd())")
    assert gate_idx >= 0 and ssot_idx >= 0
    assert gate_idx < ssot_idx, "reason gate must precede SSOT load"
