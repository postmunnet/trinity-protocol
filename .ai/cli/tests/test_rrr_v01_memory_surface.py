"""Phase 1 — rrr Article-IX compliance regression suite.

Locks the four T1..T4 tightening mandates from Phase 0 BREAK_GLASS:
  T1  rrr MUST NOT autonomously generate semantic lessons
  T2  memory-cli index determinism (covered by memory-cli's own tests)
  T3  Severity-by-tier on best-effort failure
  T4  Delegation audit event shape

Plus the two closing principles:
  rrr may terminate workflows. rrr may not synthesize institutional memory.
  Memory indexing preserves history. Memory pinning confers authority.
"""
from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from cli.commands.rrr import (
    _index_memory_cli,
    _index_severity_for_tier,
    _load_plan_envelope_tier,
    _memory_index_blocks_completion,
    _memory_index_ok,
    _print_memory_index,
    _sha256_of_file,
    _summarize_memory_index,
)
from cli.core.tools_registry import ToolInvocation


RRR_SOURCE = (
    Path(__file__).resolve().parent.parent / "commands" / "rrr.py"
).read_text()


# ─────────────── Article IX compliance (source-level lint) ───────────────


def test_rrr_does_not_invoke_memory_cli_learn():
    """Article IX: rrr MUST NOT call the deprecated semantic verb."""
    assert "memory-cli learn" not in RRR_SOURCE
    assert "learn --file=" not in RRR_SOURCE


def test_rrr_invokes_memory_cli_index():
    """Article IX: rrr delegates to mechanical evidence retrieval."""
    assert "_index_memory_cli" in RRR_SOURCE
    assert "f\"index {memory_retro_path}\"" in RRR_SOURCE


def test_audit_field_is_memory_index_not_memory_learn():
    """Article X: audit field shape obeys the new contract."""
    assert "memory_index" in RRR_SOURCE
    # The legacy field name must not appear anywhere in the active code
    # path. (Comment references inside _summarize_memory_index docstrings
    # explicitly use the substring 'legacy _summarize_memory_learn' so
    # we check the audit-payload literal context instead.)
    assert "\"memory_learn\"" not in RRR_SOURCE
    assert "'memory_learn'" not in RRR_SOURCE


def test_rrr_emits_delegated_call_audit_event():
    """T4: every rrr→organ delegation MUST be auditable."""
    assert "rrr.delegated_call" in RRR_SOURCE
    # The payload includes the canonical fields from BREAK_GLASS T4.
    for field in (
        "tool",
        "action",
        "target",
        "result",
        "artifact_sha256",
        "workflow_id",
    ):
        assert f"\"{field}\"" in RRR_SOURCE, f"missing audit field: {field}"


def test_rrr_does_not_auto_pin():
    """T1 + closing principle 2: rrr MUST NOT call pin itself."""
    # Allow comments / docstrings that *say* 'pin'; forbid actual call_tool
    # invocations of memory-cli pin.
    assert "f\"pin " not in RRR_SOURCE
    assert 'memory-cli", "pin"' not in RRR_SOURCE


# ─────────────── _summarize_memory_index ───────────────


def _inv(ok, returncode, envelope, error=None):
    return ToolInvocation(
        ok=ok,
        returncode=returncode,
        envelope=envelope,
        stdout="",
        stderr="",
        error=error,
    )


def test_summarize_success_extracts_v01_fields():
    env = {
        "ok": True,
        "tool_version": "0.9.7-beta",
        "data": {
            "indexed_new": 2,
            "indexed_updated": 0,
            "artifacts_total": 12,
            "chunks_total": 47,
            "schema": "memory-cli-v01-evidence",
        },
    }
    inv = _inv(ok=True, returncode=0, envelope=env)
    out = _summarize_memory_index(inv)
    assert out["ok"] is True
    assert out["indexed_new"] == 2
    assert out["chunks_total"] == 47
    assert out["schema"] == "memory-cli-v01-evidence"


def test_summarize_failure_surfaces_error():
    env = {"ok": False, "error": {"code": "db_not_found", "message": "no db"}}
    inv = _inv(ok=False, returncode=1, envelope=env)
    out = _summarize_memory_index(inv)
    assert out["ok"] is False
    assert out["error"] == "no db"


# ─────────────── T3 severity by tier ───────────────


def test_severity_pass_when_ok():
    for tier in ("HOT", "WARM", "COLD", None, "junk"):
        assert _index_severity_for_tier(tier, ok=True) == "pass"


def test_severity_hot_is_warning_on_failure():
    assert _index_severity_for_tier("HOT", ok=False) == "warning"


def test_severity_warm_is_degraded_on_failure():
    assert _index_severity_for_tier("WARM", ok=False) == "degraded"


def test_severity_cold_is_block_on_failure():
    assert _index_severity_for_tier("COLD", ok=False) == "block"


def test_severity_unknown_tier_defaults_to_warm():
    """Closed-conservative: unknown/missing tier → WARM (degraded on fail)."""
    assert _index_severity_for_tier(None, ok=False) == "degraded"
    assert _index_severity_for_tier("", ok=False) == "degraded"
    assert _index_severity_for_tier("junk", ok=False) == "degraded"


def test_severity_is_case_insensitive():
    assert _index_severity_for_tier("hot", ok=False) == "warning"
    assert _index_severity_for_tier("cold", ok=False) == "block"


def test_cold_memory_index_block_refuses_completion():
    assert _memory_index_blocks_completion("block") is True
    assert _memory_index_blocks_completion("block", retroactive=True) is False
    assert _memory_index_blocks_completion("degraded") is False
    assert _memory_index_blocks_completion("warning") is False
    assert _memory_index_blocks_completion("pass") is False


def test_rrr_checks_cold_memory_block_before_done_transition():
    block_pos = RRR_SOURCE.index("if _memory_index_blocks_completion(")
    done_pos = RRR_SOURCE.index('loop.fire(\n            "rrr_complete"')
    assert block_pos < done_pos


# ─────────────── Tier loader ───────────────


def test_load_plan_envelope_tier_default_warm_when_missing(tmp_path: Path):
    session = tmp_path / "session"
    (session / "THINK").mkdir(parents=True)
    assert _load_plan_envelope_tier(session) == "WARM"


def test_load_plan_envelope_tier_default_warm_when_malformed(tmp_path: Path):
    session = tmp_path / "session"
    (session / "THINK").mkdir(parents=True)
    (session / "THINK" / "plan_envelope.json").write_text("{ not json")
    assert _load_plan_envelope_tier(session) == "WARM"


def test_load_plan_envelope_tier_honours_declared_value(tmp_path: Path):
    session = tmp_path / "session"
    (session / "THINK").mkdir(parents=True)
    for declared, expected in (
        ("HOT", "HOT"),
        ("warm", "WARM"),
        ("Cold", "COLD"),
        ("INVALID", "WARM"),
        (None, "WARM"),
        (123, "WARM"),
    ):
        envelope = (
            "{}" if declared is None and False
            else __import__("json").dumps({"tier": declared})
        )
        (session / "THINK" / "plan_envelope.json").write_text(envelope)
        assert _load_plan_envelope_tier(session) == expected, declared


# ─────────────── _memory_index_ok / sha256 helpers ───────────────


def test_memory_index_ok_true_for_clean_success():
    env = {"ok": True, "data": {}}
    inv = _inv(ok=True, returncode=0, envelope=env)
    assert _memory_index_ok(inv) is True


def test_memory_index_ok_true_for_signal_exit_recovery():
    env = {"ok": True, "data": {}}
    inv = _inv(ok=False, returncode=-6, envelope=env)
    assert _memory_index_ok(inv) is True


def test_memory_index_ok_false_for_genuine_failure():
    env = {"ok": False, "error": {"message": "boom"}}
    inv = _inv(ok=False, returncode=1, envelope=env)
    assert _memory_index_ok(inv) is False


def test_sha256_of_file_returns_hex_digest(tmp_path: Path):
    p = tmp_path / "x.md"
    p.write_text("hello\n")
    digest = _sha256_of_file(p)
    # sha256("hello\n") known constant
    assert digest == (
        "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
    )


def test_sha256_of_file_empty_string_on_missing():
    assert _sha256_of_file(Path("/nonexistent/path/x.md")) == ""


# ─────────────── _index_memory_cli command shape ───────────────


def test_index_memory_cli_uses_v01_index_verb(monkeypatch):
    """Article IX compliance at call-time: the verb passed to call_tool
    MUST be 'index ...', never 'learn ...'."""
    captured = {}

    def fake_call_tool(project_root, tool_name, args, timeout_seconds=None):
        captured["tool"] = tool_name
        captured["args"] = args
        return ToolInvocation(
            ok=True,
            returncode=0,
            envelope={"ok": True, "data": {}},
            stdout="",
            stderr="",
            error=None,
        )

    monkeypatch.setattr("cli.commands.rrr.call_tool", fake_call_tool)
    _index_memory_cli(Path("/tmp"), Path("/tmp/retro.md"))
    assert captured["tool"] == "memory-cli"
    assert captured["args"].startswith("index ")
    assert "learn" not in captured["args"]


# ─────────────── _print_memory_index visibility ───────────────


def test_print_success_does_not_print_failure(monkeypatch):
    env = {
        "ok": True,
        "data": {
            "indexed_new": 1,
            "indexed_updated": 0,
            "chunks_total": 4,
            "schema": "memory-cli-v01-evidence",
        },
        "tool_version": "0.9.7-beta",
    }
    inv = _inv(ok=True, returncode=0, envelope=env)
    from cli.commands import rrr as rrr_mod
    buf = io.StringIO()
    from rich.console import Console
    orig = rrr_mod.console
    rrr_mod.console = Console(file=buf, force_terminal=False, color_system=None)
    try:
        _print_memory_index(inv)
    finally:
        rrr_mod.console = orig
    out = buf.getvalue()
    assert "memory-cli index:" in out
    assert "indexed_new=1" in out
    assert "FAIL" not in out
    assert "WARNING" not in out


def test_print_failure_surfaces_severity_per_tier():
    env = {"ok": False, "error": {"message": "db_not_found"}}
    inv = _inv(ok=False, returncode=1, envelope=env)
    for tier, expected_kw in (
        ("HOT", "WARNING"),
        ("WARM", "DEGRADED"),
        ("COLD", "BLOCK"),
    ):
        from cli.commands import rrr as rrr_mod
        buf = io.StringIO()
        from rich.console import Console
        orig = rrr_mod.console
        rrr_mod.console = Console(file=buf, force_terminal=False, color_system=None)
        try:
            _print_memory_index(inv, tier=tier)
        finally:
            rrr_mod.console = orig
        out = buf.getvalue()
        assert expected_kw in out, f"tier={tier} missing {expected_kw} in {out!r}"
        assert "db_not_found" in out
