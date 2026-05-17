"""Trinity CLI command-contract tests.

Goal: catch ritual ↔ executable-command drift structurally so the
operator never sees `No such command 'sss'` or `Missing command` for
`ai status` again.

These tests use Typer's CliRunner to invoke the top-level app
(`cli.main.app`) directly — same import path the wrapper script
uses — so they exercise the exact dispatch surface real callers
hit.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from cli.main import app


runner = CliRunner()


# ---------------------------------------------------------------------------
# 1. `ai status` (no subcommand) ≡ `ai status show`
# ---------------------------------------------------------------------------


def test_status_bare_does_not_error_missing_command():
    """`ai status` MUST NOT exit with `Missing command`.

    Before this contract was fixed, Typer treated `status` as a group
    requiring a subcommand and exit code 2. After the fix it falls
    through to `status show` and exit 0.
    """
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0, (
        f"`ai status` should exit 0 (alias of `ai status show`); "
        f"got rc={result.exit_code}\nstdout={result.stdout!r}\nstderr={result.stderr!r}"
    )


def test_status_show_still_works():
    """Backward compat: `ai status show` MUST keep working."""
    result = runner.invoke(app, ["status", "show"])
    assert result.exit_code == 0, (
        f"`ai status show` regression: rc={result.exit_code}"
    )


def test_status_path_subcommand_still_exists():
    """Backward compat: `ai status path --help` MUST resolve."""
    result = runner.invoke(app, ["status", "path", "--help"])
    assert result.exit_code == 0, (
        f"`ai status path` --help regression: rc={result.exit_code}"
    )


def test_close_bare_does_not_error_missing_command(monkeypatch):
    """`ai close` MUST dispatch to the close runner, not Typer's
    group-level `Missing command` error. The runner is monkeypatched so
    this test never archives the real active session.
    """
    from cli.commands import close as close_mod

    called = {}

    def fake_run_impl(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(close_mod, "_run_impl", fake_run_impl)
    result = runner.invoke(app, ["close"])
    assert result.exit_code == 0, (
        f"`ai close` should dispatch to close runner; "
        f"got rc={result.exit_code}\noutput={result.output!r}"
    )
    assert called["force"] is False
    assert called["with_synthesis"] is False
    assert called["hmac_envelope_file"] is None


def test_close_bare_accepts_force_option(monkeypatch):
    from cli.commands import close as close_mod

    called = {}

    def fake_run_impl(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(close_mod, "_run_impl", fake_run_impl)
    result = runner.invoke(app, ["close", "--force"])
    assert result.exit_code == 0
    assert called["force"] is True


# ---------------------------------------------------------------------------
# 2. `ai sss` is a real executable command (alias of `ai session new`)
# ---------------------------------------------------------------------------


def test_sss_help_resolves():
    """`ai sss --help` MUST NOT error `No such command`."""
    result = runner.invoke(app, ["sss", "--help"])
    assert result.exit_code == 0, (
        f"`ai sss --help` should resolve; got rc={result.exit_code}"
    )
    # Help text should mention the alias relationship
    assert "session new" in result.stdout, (
        "sss help should reference the canonical `session new` command"
    )


def test_sss_no_arg_gives_usage_hint_not_crash():
    """`ai sss` with no task name should print a usage hint, not crash."""
    result = runner.invoke(app, ["sss"])
    assert result.exit_code != 0, (
        "sss with no task should exit non-zero (usage error)"
    )
    # CliRunner merges stderr into output by default
    out = result.output or ""
    assert "session new" in out or "Usage" in out, (
        f"sss no-arg output missing usage hint: {out!r}"
    )


def test_session_new_help_still_works():
    """Backward compat: `ai session new --help` MUST keep working."""
    result = runner.invoke(app, ["session", "new", "--help"])
    assert result.exit_code == 0, (
        f"`ai session new --help` regression: rc={result.exit_code}"
    )


# ---------------------------------------------------------------------------
# 3. All ritual commands resolve their --help (no silent removal)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cmd",
    ["vvv", "nnn", "gogogo", "ddd", "rrr", "lll", "close"],
)
def test_ritual_command_help_resolves(cmd: str):
    """Each ritual command --help MUST exit 0."""
    result = runner.invoke(app, [cmd, "--help"])
    assert result.exit_code == 0, (
        f"`ai {cmd} --help` regression: rc={result.exit_code}"
    )


# ---------------------------------------------------------------------------
# 4. COMMAND_MANIFEST.yaml is the canonical source of truth
# ---------------------------------------------------------------------------


# conftest.py pins cwd to repo root, so this relative path resolves
MANIFEST_PATH = Path(".ai/cli/COMMAND_MANIFEST.yaml")


def test_command_manifest_exists():
    assert MANIFEST_PATH.exists(), (
        f"COMMAND_MANIFEST.yaml not found at {MANIFEST_PATH} — "
        "the CLI contract has no source of truth"
    )


def test_command_manifest_parses_and_has_expected_keys():
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    assert isinstance(manifest, dict), "manifest root must be a mapping"
    assert "rituals" in manifest, "manifest MUST declare `rituals`"
    assert "doctor_survey" in manifest, "manifest MUST declare `doctor_survey`"
    # Every ritual short-code must appear under `rituals`
    for ritual in ("sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "lll", "close"):
        assert ritual in manifest["rituals"], (
            f"ritual {ritual!r} missing from manifest"
        )
        entry = manifest["rituals"][ritual]
        assert "canonical" in entry, (
            f"ritual {ritual!r} missing `canonical` field"
        )


def test_command_manifest_sss_points_at_session_new():
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    sss_entry = manifest["rituals"]["sss"]
    assert "session new" in (sss_entry.get("equivalent_to") or ""), (
        "manifest `sss.equivalent_to` should reference `session new`"
    )


def test_command_manifest_close_canonical_is_bare_ritual():
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    close_entry = manifest["rituals"]["close"]
    assert close_entry["canonical"] == "ai close"
    assert "close run" in (close_entry.get("equivalent_to") or "")


# ---------------------------------------------------------------------------
# 5. `ai doctor commands` is wired and runs cleanly
# ---------------------------------------------------------------------------


def test_doctor_commands_help_resolves():
    result = runner.invoke(app, ["doctor", "commands", "--help"])
    assert result.exit_code == 0, (
        f"`ai doctor commands --help` regression: rc={result.exit_code}"
    )


def test_doctor_top_level_help_resolves():
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0, (
        f"`ai doctor --help` regression: rc={result.exit_code}"
    )
