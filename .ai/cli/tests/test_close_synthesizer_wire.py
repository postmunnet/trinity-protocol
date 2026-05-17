"""Wire — verify presentation_synthesizer is wired into close (--with-synthesis)."""
from __future__ import annotations

import inspect

from cli.commands import close as close_mod


def test_close_has_invoke_synthesizer_helper() -> None:
    assert hasattr(close_mod, "_invoke_presentation_synthesizer")
    assert callable(close_mod._invoke_presentation_synthesizer)


def test_run_has_with_synthesis_flag() -> None:
    src = inspect.getsource(close_mod.run)
    assert "--with-synthesis" in src
    assert "with_synthesis" in src


def test_helper_writes_to_presentation_synth_md() -> None:
    src = inspect.getsource(close_mod._invoke_presentation_synthesizer)
    assert "PRESENTATION_SYNTH.md" in src


def test_helper_invokes_agent_with_absolute_session_path() -> None:
    src = inspect.getsource(close_mod._invoke_presentation_synthesizer)
    assert "presentation_synthesizer" in src
    assert "--session-path" in src
    assert "str(session_path)" in src


def test_helper_is_fail_soft() -> None:
    src = inspect.getsource(close_mod._invoke_presentation_synthesizer)
    assert "try:" in src
    assert "except Exception" in src
    assert "return None" in src


def test_run_skips_synthesis_under_force() -> None:
    src = inspect.getsource(close_mod._run_impl)
    # Source must guard invocation with both with_synthesis AND not force.
    assert "with_synthesis and not force" in src
