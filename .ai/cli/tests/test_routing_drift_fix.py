"""KI-2026-05-16-001 routing drift regression — parallel session test.

Simulates the failure mode documented in docs/KNOWN_ISSUES.md:
  1. session A created
  2. session B created (overwrites current_session pointer)
  3. operator invokes vvv with --session=A → MUST write to A, not B

Without the fix this test would fail because vvv reads current_session
(= B at the time) and would write A's prompt under B's THINK folder.
"""
from __future__ import annotations

import inspect

from cli.commands import vvv as vvv_mod
from cli.commands import nnn as nnn_mod
from cli.commands import gogogo as gogogo_mod


# ─── source-level wire presence ──────────────────────────────────────


def test_vvv_has_session_typer_option() -> None:
    source = inspect.getsource(vvv_mod)
    assert '"--session"' in source, "vvv must expose --session typer.Option"
    assert "session_override" in source, "vvv must thread session_override through _run"
    assert "_resolve_with_override" in source


def test_nnn_has_session_typer_option() -> None:
    source = inspect.getsource(nnn_mod)
    assert '"--session"' in source
    assert "session_override" in source
    assert "_resolve_with_override" in source


def test_gogogo_has_session_typer_option() -> None:
    source = inspect.getsource(gogogo_mod)
    assert '"--session"' in source
    assert "session_override" in source
    assert "_resolve_with_override" in source


def test_all_three_rituals_emit_kernel_session_override() -> None:
    """The drift-bypass audit event name is consistent across rituals."""
    for mod in (vvv_mod, nnn_mod, gogogo_mod):
        source = inspect.getsource(mod)
        assert "kernel.session_override" in source, (
            f"{mod.__name__} must emit kernel.session_override "
            f"on --session bypass"
        )


def test_all_three_rituals_import_session_resolver() -> None:
    """Each ritual imports the shared resolver, not re-implements it."""
    for mod in (vvv_mod, nnn_mod, gogogo_mod):
        source = inspect.getsource(mod)
        assert "from ..core.session_resolver import" in source, (
            f"{mod.__name__} must import shared session_resolver"
        )


# ─── behavior: explicit --session bypasses current_session ───────────


def test_resolve_with_override_bypasses_global_pointer(tmp_path, monkeypatch):
    """Direct unit test of vvv._resolve_with_override: with session_override set,
    current_session is bypassed."""
    from cli.commands.vvv import _resolve_with_override
    from cli.core.ssot import SSOTConfig

    # Build a minimal project: 2 sessions + status.json pointing at A
    proj = tmp_path
    (proj / ".ai" / "sessions").mkdir(parents=True)
    (proj / ".ai" / "state").mkdir(parents=True)
    (proj / ".ai" / "audit").mkdir(parents=True)
    sess_a = proj / ".ai" / "sessions" / "0001_session-a"
    sess_b = proj / ".ai" / "sessions" / "0002_session-b"
    sess_a.mkdir()
    sess_b.mkdir()
    import json as _json
    (proj / ".ai" / "state" / "status.json").write_text(_json.dumps({
        "version": "1.0",
        "current_session": str(sess_b),  # drift: pointer at B
        "system": {"status": "busy"},
    }))

    # Minimal config-like object — we just need .project_root for the helper
    class _Cfg:
        project_root = proj
        state_path = proj / ".ai" / "state"
        status_path = proj / ".ai" / "state" / "status.json"
        audit_path = proj / ".ai" / "audit" / "events.ndjson"

    cfg = _Cfg()

    # Without --session: returns B (current behaviour)
    no_override = _resolve_with_override(cfg, None)
    assert no_override == sess_b

    # With --session=A: explicitly resolves A despite current_session=B
    override = _resolve_with_override(cfg, "0001_session-a")
    assert override == sess_a
