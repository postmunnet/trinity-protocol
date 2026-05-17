"""Wire — verify retro_writer agent is wired into rrr (--with-lessons)."""
from __future__ import annotations

import inspect

from cli.commands import rrr as rrr_mod


def test_rrr_has_invoke_retro_writer_helper() -> None:
    assert hasattr(rrr_mod, "_invoke_retro_writer")
    assert callable(rrr_mod._invoke_retro_writer)


def test_callback_has_with_lessons_flag() -> None:
    src = inspect.getsource(rrr_mod.callback)
    assert "--with-lessons" in src
    assert "with_lessons" in src


def test_helper_writes_to_retro_lessons_md_path() -> None:
    src = inspect.getsource(rrr_mod._invoke_retro_writer)
    assert "RETRO_LESSONS.md" in src
    assert "THINK" in src


def test_helper_invokes_agent_with_absolute_session_path() -> None:
    src = inspect.getsource(rrr_mod._invoke_retro_writer)
    assert "retro_writer" in src
    assert "--session-path" in src
    assert "str(session_path)" in src


def test_helper_is_fail_soft() -> None:
    src = inspect.getsource(rrr_mod._invoke_retro_writer)
    assert "try:" in src
    assert "except Exception" in src
    # Returns None on failure to signal skip rather than raise.
    assert "return None" in src


def test_inner_skips_lessons_under_dry_run_or_retroactive() -> None:
    src = inspect.getsource(rrr_mod._rrr_inner)
    assert "with_lessons" in src
    # Guard clause must include all three predicates.
    assert "not dry_run" in src
    assert "not retroactive" in src
