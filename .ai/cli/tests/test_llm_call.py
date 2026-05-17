"""Tests for the LLM-call foundation (`.ai/cli/core/llm_call.py`).

Coverage map (per session feat-llm-call-helper-foundation, gogogo step S9):
  T1   — module imports
  T2   — substitute plain_text
  T3   — substitute markdown_escaped
  T4   — substitute json_string
  T5   — substitute path
  T6   — substitute enum (valid + invalid)
  T7   — substitute code_block
  T8   — substitute evidence_ref
  T9   — MissingPlaceholderError on required-missing
  T10  — TypeMismatchError on enum out-of-range
  T11  — UntypedPlaceholderError on raw {{user_input}}
  T12  — load_ritual_pack on real .ai/rituals/vvv/
  T13  — discover_backends smoke (host CLIs)
  T14  — ClaudeCLIBackend.invoke via monkeypatched subprocess.run
  T15  — GeminiCLIBackend / CodexCLIBackend via monkeypatch
  T16  — BackendTimeout
  T17  — AnthropicAPIBackend graceful unavailability
  T18  — MockBackend roundtrip
  T19  — select_backend strategy (request / env / preference / default / not-found)
  T20  — _redact regex patterns
  T21  — _redact env-value
  T22  — audit emission on success
  T23  — audit emission on failure
  T24  — integration: load vvv pack + substitute + MockBackend
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest

from cli.core.audit import AuditChain
from cli.core.llm_call import (
    AnthropicAPIBackend,
    Backend,
    BackendError,
    BackendTimeout,
    BackendUnavailable,
    ClaudeCLIBackend,
    CodexCLIBackend,
    GeminiCLIBackend,
    LLMError,
    LLMRequest,
    LLMResponse,
    MissingPlaceholderError,
    MockBackend,
    NoBackendAvailable,
    TypeMismatchError,
    UntypedPlaceholderError,
    _redact,
    call_llm,
    discover_backends,
    load_ritual_pack,
    select_backend,
    substitute,
)


REPO_ROOT = Path.cwd()
RITUALS_DIR = REPO_ROOT / ".ai" / "rituals"


# ───────────────────────── T1 — imports ─────────────────────────


def test_imports_module_surface():
    """T1 — public API loadable."""
    assert callable(call_llm)
    assert callable(load_ritual_pack)
    assert callable(substitute)
    assert callable(discover_backends)
    assert callable(select_backend)


# ───────────────────────── substitution ─────────────────────────


def _schema(*specs: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "context_schema_version": "1.0",
        "ritual": "test",
        "placeholders": list(specs),
    }


def test_substitute_plain_text():
    """T2 — plain_text is pass-through string conversion."""
    out = substitute(
        "Hello {{plain_text:name}}",
        {"name": "World"},
        _schema({"identifier": "name", "type": "plain_text", "required": True, "description": "x"}),
    )
    assert out == "Hello World"


def test_substitute_markdown_escaped():
    """T3 — markdown_escaped html-escapes brackets."""
    out = substitute(
        "Body: {{markdown_escaped:body}}",
        {"body": "<script>alert(1)</script> & friends"},
        _schema({"identifier": "body", "type": "markdown_escaped", "required": True, "description": "x"}),
    )
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "&amp;" in out


def test_substitute_json_string():
    """T4 — json_string is canonical JSON encoding."""
    out = substitute(
        "Data: {{json_string:payload}}",
        {"payload": {"a": 1, "b": [2, 3]}},
        _schema({"identifier": "payload", "type": "json_string", "required": True, "description": "x"}),
    )
    assert '{"a":1,"b":[2,3]}' in out


def test_substitute_path():
    """T5 — path is rendered via pathlib (normalised)."""
    out = substitute(
        "File: {{path:loc}}",
        {"loc": "/tmp/foo/../bar"},
        _schema({"identifier": "loc", "type": "path", "required": True, "description": "x"}),
    )
    # Path doesn't auto-resolve '..' (that would need .resolve()), but it does
    # normalise the string. Just assert it round-trips through Path().
    assert "bar" in out


def test_substitute_enum_valid():
    """T6a — enum accepts in-range value."""
    out = substitute(
        "Tier: {{enum:tier}}",
        {"tier": "WARM"},
        _schema({
            "identifier": "tier", "type": "enum", "required": True,
            "description": "x", "enum_values": ["HOT", "WARM", "COLD"],
        }),
    )
    assert "Tier: WARM" == out


def test_substitute_enum_invalid_raises():
    """T6b — enum rejects out-of-range value."""
    with pytest.raises(TypeMismatchError):
        substitute(
            "Tier: {{enum:tier}}",
            {"tier": "WARMISH"},
            _schema({
                "identifier": "tier", "type": "enum", "required": True,
                "description": "x", "enum_values": ["HOT", "WARM", "COLD"],
            }),
        )


def test_substitute_code_block():
    """T7 — code_block wraps in triple-backtick fence."""
    out = substitute(
        "Code: {{code_block:src}}",
        {"src": "def f():\n    return 1"},
        _schema({"identifier": "src", "type": "code_block", "required": True, "description": "x"}),
    )
    assert out.startswith("Code: ```\n")
    assert "def f():" in out
    assert out.endswith("```")


def test_substitute_evidence_ref_dict():
    """T8 — evidence_ref serialises dict to compact JSON."""
    out = substitute(
        "Cite: {{evidence_ref:ref}}",
        {"ref": {"path": "foo.txt", "sha256": "abc"}},
        _schema({"identifier": "ref", "type": "evidence_ref", "required": True, "description": "x"}),
    )
    assert '{"path":"foo.txt","sha256":"abc"}' in out


# ───────────────────────── substitution errors ─────────────────────────


def test_substitute_raises_on_missing_required():
    """T9 — MissingPlaceholderError on required-missing identifier."""
    with pytest.raises(MissingPlaceholderError):
        substitute(
            "Hello {{plain_text:name}}",
            {},
            _schema({"identifier": "name", "type": "plain_text", "required": True, "description": "x"}),
        )


def test_substitute_optional_missing_becomes_empty():
    """Optional placeholder missing -> empty string substitution (no raise)."""
    out = substitute(
        "Hi {{plain_text:nick}}",
        {},
        _schema({"identifier": "nick", "type": "plain_text", "required": False, "description": "x"}),
    )
    assert out == "Hi "


def test_substitute_mismatch_enum_already_covered_in_T6b():
    """T10 — TypeMismatchError on enum already covered in T6b above (sanity dup)."""
    # Just re-assert the same path through a different identifier to be explicit.
    with pytest.raises(TypeMismatchError):
        substitute(
            "{{enum:x}}",
            {"x": "Z"},
            _schema({
                "identifier": "x", "type": "enum", "required": True,
                "description": "x", "enum_values": ["A", "B"],
            }),
        )


def test_substitute_rejects_raw_user_input_canary():
    """T11a — UntypedPlaceholderError on raw {{user_input}} (Article XVI canary)."""
    with pytest.raises(UntypedPlaceholderError):
        substitute("Hello {{user_input}}", {}, _schema())


def test_substitute_rejects_undeclared_typed_placeholder():
    """T11b — typed placeholder whose identifier is not in context_schema is rejected."""
    with pytest.raises(UntypedPlaceholderError):
        substitute(
            "Hi {{plain_text:not_declared}}",
            {"not_declared": "x"},
            _schema(),  # empty placeholders list
        )


def test_substitute_rejects_spaces_inside_braces():
    """T11c — `{{ name }}` (with spaces) is not a typed placeholder and is rejected."""
    with pytest.raises(UntypedPlaceholderError):
        substitute("Hi {{ name }}", {"name": "X"}, _schema())


# ───────────────────────── load_ritual_pack ─────────────────────────


def test_load_ritual_pack_vvv():
    """T12 — load_ritual_pack on the real .ai/rituals/vvv/ pack."""
    pack = load_ritual_pack("vvv", rituals_root=RITUALS_DIR)
    assert pack.ritual == "vvv"
    assert pack.contract["ritual"] == "vvv"
    assert pack.context_schema["ritual"] == "vvv"
    assert pack.check_template["check_template_version"] == "1.0"
    assert pack.write_template  # non-empty


def test_load_ritual_pack_missing_raises():
    """Bonus — load_ritual_pack on a missing ritual raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_ritual_pack("nonexistent_xyz", rituals_root=RITUALS_DIR)


# ───────────────────────── Backends ─────────────────────────


def test_discover_backends_returns_known_set():
    """T13 — discover_backends returns the 4 known backends."""
    backends = discover_backends()
    names = {b.name for b in backends}
    assert names == {"claude", "gemini", "codex", "anthropic-api"}


def _fake_completed_process(stdout: str = "OK", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(
        args=["fake"], returncode=returncode, stdout=stdout, stderr=stderr,
    )


def test_claude_cli_invoke_monkeypatched(monkeypatch):
    """T14 — ClaudeCLIBackend.invoke through a stubbed subprocess.run."""
    captured: Dict[str, Any] = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return _fake_completed_process(stdout="hello from claude\n")

    monkeypatch.setattr("cli.core.llm_call.subprocess.run", fake_run)
    monkeypatch.setattr("cli.core.llm_call.shutil.which", lambda b: "/fake/" + b)

    b = ClaudeCLIBackend()
    resp = b.invoke(LLMRequest(prompt="hi"))
    assert resp.text == "hello from claude"
    assert resp.backend == "claude"
    assert captured["argv"] == ["claude", "-p", "hi"]
    assert captured["kwargs"]["timeout"] == 120.0


def test_gemini_and_codex_cli_invoke_argv_shape(monkeypatch):
    """T15 — Gemini and Codex backends use correct argv shape."""
    monkeypatch.setattr("cli.core.llm_call.shutil.which", lambda b: "/fake/" + b)
    captured: List[List[str]] = []

    def fake_run(argv, **kwargs):
        captured.append(list(argv))
        return _fake_completed_process(stdout="x")

    monkeypatch.setattr("cli.core.llm_call.subprocess.run", fake_run)

    GeminiCLIBackend().invoke(LLMRequest(prompt="p"))
    CodexCLIBackend().invoke(LLMRequest(prompt="p"))

    assert captured[0] == ["gemini", "-p", "p"]
    assert captured[1] == ["codex", "exec", "p"]


def test_backend_unavailable_when_binary_missing(monkeypatch):
    """Bonus — invoking when binary missing -> BackendUnavailable."""
    monkeypatch.setattr("cli.core.llm_call.shutil.which", lambda b: None)
    with pytest.raises(BackendUnavailable):
        ClaudeCLIBackend().invoke(LLMRequest(prompt="x"))


def test_backend_timeout(monkeypatch):
    """T16 — subprocess.TimeoutExpired -> BackendTimeout."""
    monkeypatch.setattr("cli.core.llm_call.shutil.which", lambda b: "/fake/claude")

    def hanging(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs.get("timeout", 0))

    monkeypatch.setattr("cli.core.llm_call.subprocess.run", hanging)
    with pytest.raises(BackendTimeout):
        ClaudeCLIBackend().invoke(LLMRequest(prompt="slow", timeout=0.01))


def test_backend_non_zero_returncode_redacts_stderr(monkeypatch):
    """Bonus — non-zero returncode raises BackendError; stderr is redacted."""
    monkeypatch.setattr("cli.core.llm_call.shutil.which", lambda b: "/fake/claude")
    leak = "sk-ant-" + "AAAAAAAAAAAAAAAAAAAAAAAA"

    def err(argv, **kwargs):
        return _fake_completed_process(stdout="", stderr=f"boom {leak}", returncode=2)

    monkeypatch.setattr("cli.core.llm_call.subprocess.run", err)
    with pytest.raises(BackendError) as exc:
        ClaudeCLIBackend().invoke(LLMRequest(prompt="x"))
    assert leak not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


def test_anthropic_api_backend_graceful_unavailability(monkeypatch):
    """T17 — when SDK absent or key missing, .available is False and .invoke raises BackendUnavailable."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    b = AnthropicAPIBackend()
    # Force the "SDK absent" branch deterministically regardless of host env.
    b._sdk_available = False
    assert b.available is False
    with pytest.raises(BackendUnavailable):
        b.invoke(LLMRequest(prompt="x"))


def test_mock_backend_roundtrip():
    """T18 — MockBackend returns canned response."""
    b = MockBackend(canned="HELLO")
    resp = b.invoke(LLMRequest(prompt="ignored"))
    assert resp.text == "HELLO"
    assert resp.backend == "mock"
    assert resp.model == "mock-model"


# ───────────────────────── select_backend strategy ─────────────────────────


class _FakeBackend(Backend):
    def __init__(self, name: str, available: bool):
        self._name = name
        self._available = available

    @property
    def name(self) -> str:  # type: ignore[override]
        return self._name

    @property
    def available(self) -> bool:
        return self._available

    def invoke(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="x", model=self._name, backend=self._name, duration_ms=0)


def test_select_backend_request_override():
    """T19a — request.backend wins over env and preference."""
    pool = [_FakeBackend("claude", True), _FakeBackend("codex", True), _FakeBackend("gemini", True)]
    req = LLMRequest(prompt="x", backend="gemini")
    chosen = select_backend(request=req, backends=pool)
    assert chosen.name == "gemini"


def test_select_backend_env_override(monkeypatch):
    """T19b — LLM_BACKEND env wins when request.backend is unset."""
    pool = [_FakeBackend("claude", True), _FakeBackend("codex", True)]
    monkeypatch.setenv("LLM_BACKEND", "codex")
    chosen = select_backend(backends=pool)
    assert chosen.name == "codex"


def test_select_backend_preference_first_available():
    """T19c — preference list picks the first available."""
    pool = [_FakeBackend("claude", False), _FakeBackend("codex", True), _FakeBackend("gemini", True)]
    chosen = select_backend(preference=["claude", "codex", "gemini"], backends=pool)
    assert chosen.name == "codex"


def test_select_backend_default_preference(monkeypatch):
    """T19d — default preference order is claude > codex > gemini > anthropic-api."""
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    pool = [
        _FakeBackend("claude", True),
        _FakeBackend("codex", True),
        _FakeBackend("gemini", True),
        _FakeBackend("anthropic-api", True),
    ]
    chosen = select_backend(backends=pool)
    assert chosen.name == "claude"


def test_select_backend_no_backend_raises(monkeypatch):
    """T19e — when nothing matches, NoBackendAvailable is raised."""
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    pool = [_FakeBackend("claude", False), _FakeBackend("codex", False)]
    with pytest.raises(NoBackendAvailable):
        select_backend(backends=pool)


def test_select_backend_unknown_request_name():
    """Bonus — request.backend that names an unknown backend raises NoBackendAvailable."""
    pool = [_FakeBackend("claude", True)]
    with pytest.raises(NoBackendAvailable):
        select_backend(request=LLMRequest(prompt="x", backend="nonesuch"), backends=pool)


# ───────────────────────── _redact ─────────────────────────


def test_redact_strips_anthropic_key_pattern():
    """T20a — sk-ant-... is redacted."""
    text = "leaked: " + "sk-ant-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ_-1234567"
    out = _redact(text)
    assert "sk-ant-" not in out
    assert "[REDACTED]" in out


def test_redact_strips_openai_key_pattern():
    """T20b — sk-... (OpenAI-shape) is redacted."""
    text = "key: " + "sk-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"
    out = _redact(text)
    assert "[REDACTED]" in out
    assert "sk-AB" not in out


def test_redact_strips_google_key_pattern():
    """T20c — AIza... (Google-shape) is redacted."""
    text = "key: " + "AIza" + "SyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456"
    out = _redact(text)
    assert "[REDACTED]" in out
    assert "AIza" not in out


def test_redact_strips_bearer_token():
    """T20d — Bearer <token> is redacted (case-insensitive)."""
    text = "Authorization: Bearer xyz.123.abc"
    out = _redact(text)
    assert "[REDACTED]" in out
    assert "xyz.123.abc" not in out


def test_redact_strips_env_credential_value(monkeypatch):
    """T21 — when ANTHROPIC_API_KEY is set, its raw value is redacted from text."""
    secret = "VERY_SECRET_VALUE_1234"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    out = _redact(f"leaked: {secret} :end")
    assert secret not in out
    assert "[REDACTED]" in out


def test_redact_empty_string():
    """Bonus — _redact('') returns ''."""
    assert _redact("") == ""


# ───────────────────────── audit emission ─────────────────────────


@pytest.fixture
def isolated_chain(tmp_path: Path) -> AuditChain:
    """Fresh, isolated audit chain for tests; never touches the real one."""
    return AuditChain(tmp_path / "events.ndjson")


def test_audit_emission_on_success(isolated_chain: AuditChain):
    """T22 — successful call emits llm.call_started + llm.call_completed."""
    backend = MockBackend(canned="ok")
    resp = call_llm(
        LLMRequest(prompt="hi"),
        backend=backend,
        audit_chain=isolated_chain,
        ritual_context={"ritual": "vvv", "session_id": "s1"},
    )
    assert resp.text == "ok"
    events = list(isolated_chain.iter_events())
    types = [e["type"] for e in events]
    assert "llm.call_started" in types
    assert "llm.call_completed" in types
    started = next(e for e in events if e["type"] == "llm.call_started")
    assert started["details"]["ritual"] == "vvv"
    assert started["details"]["session_id"] == "s1"
    assert "prompt_sha256" in started["details"]
    completed = next(e for e in events if e["type"] == "llm.call_completed")
    assert completed["details"]["response_chars"] == 2  # "ok"


def test_audit_emission_on_failure(isolated_chain: AuditChain, monkeypatch):
    """T23 — failed call emits llm.call_failed with redacted error message."""

    class FailingBackend(Backend):
        name = "failing"

        @property
        def available(self) -> bool:
            return True

        def invoke(self, request: LLMRequest) -> LLMResponse:
            raise BackendError("boom " + "sk-ant-" + "LEAKEDKEY1234567890ABCDEFG")

    with pytest.raises(BackendError):
        call_llm(
            LLMRequest(prompt="x"),
            backend=FailingBackend(),
            audit_chain=isolated_chain,
        )

    events = list(isolated_chain.iter_events())
    types = [e["type"] for e in events]
    assert "llm.call_started" in types
    assert "llm.call_failed" in types
    failed = next(e for e in events if e["type"] == "llm.call_failed")
    assert failed["details"]["error_class"] == "BackendError"
    assert "sk-ant-" not in failed["details"]["error_message"]
    assert "[REDACTED]" in failed["details"]["error_message"]


def test_audit_chain_validates_after_calls(isolated_chain: AuditChain):
    """Bonus — chain hash-validates after llm.call_* events."""
    call_llm(LLMRequest(prompt="x"), backend=MockBackend(), audit_chain=isolated_chain)
    call_llm(LLMRequest(prompt="y"), backend=MockBackend(), audit_chain=isolated_chain)
    isolated_chain.validate()  # raises if broken


# ───────────────────────── integration ─────────────────────────


def test_integration_vvv_pack_substitute_and_mock_invoke(isolated_chain: AuditChain):
    """T24 — load vvv ritual pack, substitute mock context, MockBackend roundtrip."""
    pack = load_ritual_pack("vvv", rituals_root=RITUALS_DIR)

    # Build a context that satisfies every required placeholder in vvv's
    # context schema with synthetic values.
    context: Dict[str, Any] = {}
    for spec in pack.context_schema["placeholders"]:
        if not spec.get("required"):
            continue
        ident = spec["identifier"]
        t = spec["type"]
        if t == "enum":
            value: Any = spec["enum_values"][0]
        elif t == "json_string":
            value = {"k": "v"}
        elif t == "evidence_ref":
            value = {"path": "x", "sha256": "y"}
        elif t == "code_block":
            value = "x = 1"
        else:
            value = "sample"
        # Place value at the dotted path.
        cur = context
        parts = ident.split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = value

    prompt = substitute(pack.write_template, context, pack.context_schema)
    assert prompt  # non-empty
    # No leftover typed placeholders.
    from cli.core.llm_call import _TYPED_PLACEHOLDER_RE
    assert _TYPED_PLACEHOLDER_RE.search(prompt) is None

    resp = call_llm(
        LLMRequest(prompt=prompt),
        backend=MockBackend(canned="VVV_OK"),
        audit_chain=isolated_chain,
        ritual_context={"ritual": pack.ritual, "session_id": "integration"},
    )
    assert resp.text == "VVV_OK"
    events = [e["type"] for e in isolated_chain.iter_events()]
    assert events == ["llm.call_started", "llm.call_completed"]
