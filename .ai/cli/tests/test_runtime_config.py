"""Tests for the Runtime State Convention (Phase A).

Mirrors packages/runtime-paths/tests/resolve.test.js case-for-case, plus the
`ai config set-runtime/show` command and the project_registry alignment.
"""
from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cli.core.runtime_home import (
    RuntimeNotConfiguredError,
    memory_home,
    read_central_root,
    read_runtime_code,
    read_runtime_root,
    resolve_central_home,
    resolve_runtime_home,
    state_dir,
    write_runtime_yaml,
)
from cli.core import project_registry as registry_mod
from cli.commands.config import app as config_app


# --- resolution order (mirror of Node tests) --------------------------------

def test_env_trinity_home_wins(tmp_path):
    root = resolve_runtime_home(env={"TRINITY_HOME": str(tmp_path / "rt-env")})
    assert root == (tmp_path / "rt-env").resolve()


def test_runtime_yaml_fallback(tmp_path):
    inst = tmp_path / "inst"
    (inst / ".ai").mkdir(parents=True)
    write_runtime_yaml(inst, tmp_path / "declared")
    root = resolve_runtime_home(env={}, start_dir=inst)
    assert root == (tmp_path / "declared").resolve()


def test_runtime_yaml_discovered_walking_up(tmp_path):
    inst = tmp_path / "inst"
    (inst / ".ai").mkdir(parents=True)
    write_runtime_yaml(inst, tmp_path / "walkup")
    nested = inst / "a" / "b" / "c"
    nested.mkdir(parents=True)
    root = resolve_runtime_home(env={}, start_dir=nested)
    assert root == (tmp_path / "walkup").resolve()


def test_env_precedence_over_yaml(tmp_path):
    inst = tmp_path / "inst"
    (inst / ".ai").mkdir(parents=True)
    write_runtime_yaml(inst, tmp_path / "file")
    root = resolve_runtime_home(env={"TRINITY_HOME": str(tmp_path / "env")}, start_dir=inst)
    assert root == (tmp_path / "env").resolve()


def test_raises_when_unconfigured(tmp_path):
    with pytest.raises(RuntimeNotConfiguredError) as ei:
        resolve_runtime_home(env={}, start_dir=tmp_path)
    assert ei.value.code == "runtime_not_configured"


def test_error_names_the_fix(tmp_path):
    with pytest.raises(RuntimeNotConfiguredError, match=r"ai config set-runtime"):
        resolve_runtime_home(env={}, start_dir=tmp_path)


def test_non_strict_returns_none(tmp_path):
    assert resolve_runtime_home(env={}, start_dir=tmp_path, strict=False) is None


# --- layout helpers ----------------------------------------------------------

def test_state_dir_creates_under_root(tmp_path):
    d = state_dir("task-cli", env={"TRINITY_HOME": str(tmp_path)})
    assert d == (tmp_path / "state" / "task-cli").resolve()
    assert d.exists()


def test_memory_home_creates_under_root(tmp_path):
    d = memory_home(env={"TRINITY_HOME": str(tmp_path)})
    assert d == (tmp_path / "memory").resolve()
    assert d.exists()


def test_state_dir_rejects_bad_names(tmp_path):
    for bad in ["../evil", "a/b", "", "/abs", "."]:
        with pytest.raises(ValueError):
            state_dir(bad, env={"TRINITY_HOME": str(tmp_path)})


# --- project_registry alignment (does NOT break legacy fallback) ------------

def test_default_homes_respect_runtime_yaml(tmp_path, monkeypatch):
    inst = tmp_path / "inst"
    (inst / ".ai").mkdir(parents=True)
    write_runtime_yaml(inst, tmp_path / "rt")
    monkeypatch.chdir(inst)
    assert registry_mod.default_trinity_home(env={}) == (tmp_path / "rt").resolve() / ".trinity"
    assert registry_mod.default_memory_home(env={}) == (tmp_path / "rt").resolve() / ".memory"


def test_default_homes_legacy_fallback_unbroken(tmp_path, monkeypatch):
    # No runtime.yaml anywhere -> must NOT raise; legacy workspace fallback.
    monkeypatch.chdir(tmp_path)
    th = registry_mod.default_trinity_home(env={})
    mh = registry_mod.default_memory_home(env={})
    assert th.name == ".trinity"
    assert mh.name == ".memory"


def test_default_homes_explicit_env_still_wins(tmp_path):
    th = registry_mod.default_trinity_home(env={"TRINITY_HOME": str(tmp_path / "x")})
    assert th == (tmp_path / "x").resolve()


# --- `ai config` command -----------------------------------------------------

def test_config_set_runtime_and_show_roundtrip(tmp_path, monkeypatch):
    monkeypatch.delenv("TRINITY_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    res = runner.invoke(config_app, ["set-runtime", str(tmp_path / "rt"), "--json"])
    assert res.exit_code == 0, res.stdout
    assert "runtime_root" in res.stdout
    assert (tmp_path / ".ai" / "runtime.yaml").exists()

    res2 = runner.invoke(config_app, ["show", "--json"])
    assert res2.exit_code == 0, res2.stdout
    assert str((tmp_path / "rt").resolve()) in res2.stdout


def test_config_show_errors_when_unconfigured(tmp_path, monkeypatch):
    monkeypatch.delenv("TRINITY_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    res = runner.invoke(config_app, ["show", "--json"])
    assert res.exit_code == 1
    assert "runtime_not_configured" in res.stdout


def test_runtime_code_write_read_roundtrip(tmp_path):
    """R4: write_runtime_yaml(..., runtime_code) records both keys; readers
    parse each independently. runtime_root (state) stays resolvable."""
    inst = tmp_path / "proj"
    state = tmp_path / "state_root"
    code = tmp_path / "central_runtime"
    yaml_path = write_runtime_yaml(inst, state, runtime_code=code)
    assert read_runtime_root(yaml_path) == state.resolve()
    assert read_runtime_code(yaml_path) == code.resolve()
    # state resolution still works off runtime_root, independent of code
    assert resolve_runtime_home(env={}, start_dir=inst) == state.resolve()


def test_runtime_code_absent_when_not_given(tmp_path):
    """Back-compat: omitting runtime_code writes only runtime_root; reader -> None."""
    inst = tmp_path / "proj"
    state = tmp_path / "state_root"
    yaml_path = write_runtime_yaml(inst, state)
    assert read_runtime_root(yaml_path) == state.resolve()
    assert read_runtime_code(yaml_path) is None


def test_config_set_runtime_writes_code(tmp_path, monkeypatch):
    """`ai config set-runtime <state> --code <runtime>` records runtime_code."""
    monkeypatch.delenv("TRINITY_HOME", raising=False)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    res = runner.invoke(
        config_app,
        ["set-runtime", str(tmp_path / "rt"), "--code", str(tmp_path / "central"), "--json"],
    )
    assert res.exit_code == 0, res.stdout
    assert str((tmp_path / "central").resolve()) in res.stdout
    assert read_runtime_code(tmp_path / ".ai" / "runtime.yaml") == (tmp_path / "central").resolve()


# ── central_root (R12 Phase 1) ──────────────────────────────────────────────
def test_central_env_wins(tmp_path):
    c = resolve_central_home(env={"TRINITY_CENTRAL": str(tmp_path / "c")}, home=tmp_path / "h")
    assert c == (tmp_path / "c").resolve()


def test_central_yaml_when_no_env(tmp_path):
    inst = tmp_path / "inst"
    write_runtime_yaml(inst, tmp_path / "state")  # runtime_root only
    # append central_root by hand (R12: no writer yet in Phase 1)
    yp = inst / ".ai" / "runtime.yaml"
    yp.write_text(yp.read_text() + f"central_root: {tmp_path / 'cy'}\n")
    assert read_central_root(yp) == (tmp_path / "cy").resolve()
    c = resolve_central_home(env={}, start_dir=inst, home=tmp_path / "h")
    assert c == (tmp_path / "cy").resolve()


def test_central_default_when_unset(tmp_path):
    # no env, no yaml -> <home>/.trinity-central
    c = resolve_central_home(env={}, start_dir=tmp_path / "nowhere", home=tmp_path / "h")
    assert c == (tmp_path / "h" / ".trinity-central").resolve()


def test_central_env_precedence_over_yaml(tmp_path):
    inst = tmp_path / "inst"
    write_runtime_yaml(inst, tmp_path / "state")
    yp = inst / ".ai" / "runtime.yaml"
    yp.write_text(yp.read_text() + f"central_root: {tmp_path / 'cy'}\n")
    c = resolve_central_home(env={"TRINITY_CENTRAL": str(tmp_path / "cenv")}, start_dir=inst, home=tmp_path / "h")
    assert c == (tmp_path / "cenv").resolve()
