"""Wire #1 — verify presentation_renderer is wired into close.py."""
from __future__ import annotations

import inspect

from cli.commands import close as close_mod


def test_close_imports_write_close_pack() -> None:
    src = inspect.getsource(close_mod)
    assert "from ..core.presentation_renderer import write_close_pack" in src


def test_close_calls_write_close_pack_in_pre_archive() -> None:
    src = inspect.getsource(close_mod)
    assert "write_close_pack(session_path)" in src
    # The call sits inside _close_pre_archive (i.e. before archive_session
    # in run()). We assert ordering by source-text position.
    pre_archive_pos = src.find("def _close_pre_archive")
    call_pos = src.find("write_close_pack(session_path)")
    archive_emit_pos = src.find("def _close_archive_and_emit")
    assert pre_archive_pos < call_pos < archive_emit_pos


def test_close_pack_render_is_fail_soft() -> None:
    """A render failure must NOT abort close (wrapped in try/except)."""
    src = inspect.getsource(close_mod)
    # Slice _close_pre_archive body.
    start = src.find("def _close_pre_archive")
    end = src.find("def _close_archive_and_emit")
    pre = src[start:end]
    assert "try:" in pre
    assert "write_close_pack(session_path)" in pre
    assert "except Exception" in pre
    assert "close pack render failed" in pre
