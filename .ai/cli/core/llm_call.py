"""LLM-call foundation for Trinity sibling CLIs.

Authority hierarchy (highest first):
  - Constitution v1.0 Article IX (Memory Discipline): this module is NOT memory;
    it does not decide meaning. It is a transport between ritual templates and
    an external LLM. Semantic interpretation happens INSIDE the sibling CLI
    that wraps llm_call, never inside llm_call itself.
  - Constitution v1.0 Article XVI (Least Authority): every backend declares its
    capability surface (CLI subprocess vs network SDK); unknown backend = denied.
  - Constitution v1.0 Article XVII (Secret Handling): API keys and bearer tokens
    are redacted before any audit emission or error surface.
  - Constitution v1.0 Article XX (Passive Core): this module is invoked
    explicitly; it does not poll, retry beyond a configurable cap, or
    background-fetch.
  - Ritual Constitution v1.1-rc Article XVI (Template Injection Protection):
    placeholder substitution is typed; any non-typed double-brace token fails
    closed (UntypedPlaceholderError).

This module is the foundation that future sibling CLIs (judge-cli,
presentation-synthesizer-cli, plan-helper-cli, debate-cli, retro-writer-cli)
will reuse. Kernel rituals themselves (sss/nnn/gogogo/ddd/rrr/close) MUST NOT
call this module — they stay deterministic per Decisions D8/D13.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from cli.core.audit import AuditChain


# ───────────────────────── Errors ─────────────────────────


class LLMError(Exception):
    """Base class for every llm_call error."""


class MissingPlaceholderError(LLMError):
    """A required placeholder was not present in the substitution context."""


class TypeMismatchError(LLMError):
    """A placeholder value failed type-specific validation (e.g. enum)."""


class UntypedPlaceholderError(LLMError):
    """Template contains a double-brace token that is not a typed placeholder.

    Per RC Article XVI, every substitution must be typed. Raw `{{user_input}}`
    is the canonical attack surface and is rejected here.
    """


class BackendUnavailable(LLMError):
    """Backend cannot be used (SDK absent, CLI not in PATH, auth missing)."""


class BackendError(LLMError):
    """Backend invocation failed at runtime."""


class BackendTimeout(BackendError):
    """Backend exceeded the configured timeout."""


class NoBackendAvailable(LLMError):
    """No backend matched the selection criteria."""


# ───────────────────────── Dataclasses ─────────────────────────


@dataclass
class LLMRequest:
    prompt: str
    model: Optional[str] = None
    backend: Optional[str] = None
    timeout: float = 120.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    text: str
    model: str
    backend: str
    duration_ms: int
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RitualPack:
    ritual: str
    contract: Dict[str, Any]
    context_schema: Dict[str, Any]
    check_template: Dict[str, Any]
    write_template: str
    root: Path


# ───────────────────────── Ritual pack loader ─────────────────────────


def load_ritual_pack(
    ritual_name: str,
    rituals_root: Path = Path(".ai/rituals"),
) -> RitualPack:
    """Load the 4-file template pack for a given ritual."""
    pack_dir = Path(rituals_root) / ritual_name
    if not pack_dir.is_dir():
        raise FileNotFoundError(f"ritual pack dir not found: {pack_dir}")
    contract_path = pack_dir / "ritual.contract.json"
    context_path = pack_dir / "context.schema.json"
    check_path = pack_dir / "check.template.json"
    write_path = pack_dir / "write.template.md"
    for p in (contract_path, context_path, check_path, write_path):
        if not p.is_file():
            raise FileNotFoundError(f"missing pack file: {p}")
    return RitualPack(
        ritual=ritual_name,
        contract=json.loads(contract_path.read_text(encoding="utf-8")),
        context_schema=json.loads(context_path.read_text(encoding="utf-8")),
        check_template=json.loads(check_path.read_text(encoding="utf-8")),
        write_template=write_path.read_text(encoding="utf-8"),
        root=pack_dir,
    )


# ───────────────────────── Typed placeholder substitution ─────────────────────────

# Mirrors the regex in test_ritual_template_packs.py exactly.
_TYPED_PLACEHOLDER_RE = re.compile(
    r"\{\{([a-z_]+):([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)\}\}"
)
_ANY_DOUBLE_BRACE_RE = re.compile(r"\{\{([^}]+)\}\}")

# RC Article XVI typed-field enumeration.
_VALID_TYPES = frozenset({
    "plain_text",
    "markdown_escaped",
    "json_string",
    "path",
    "enum",
    "code_block",
    "evidence_ref",
})


def _escape_for_type(
    value: Any,
    type_name: str,
    enum_values: Optional[List[str]] = None,
) -> str:
    if type_name not in _VALID_TYPES:
        raise TypeMismatchError(f"unknown placeholder type: {type_name!r}")
    if type_name == "plain_text":
        return str(value)
    if type_name == "markdown_escaped":
        return html.escape(str(value), quote=False)
    if type_name == "json_string":
        return json.dumps(value, separators=(",", ":"), default=str)
    if type_name == "path":
        return str(Path(str(value)))
    if type_name == "enum":
        if enum_values is None:
            raise TypeMismatchError(
                "enum placeholder requires enum_values in context_schema"
            )
        if str(value) not in enum_values:
            raise TypeMismatchError(
                f"enum value {value!r} not in {list(enum_values)!r}"
            )
        return str(value)
    if type_name == "code_block":
        return f"```\n{str(value)}\n```"
    # evidence_ref
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"), default=str)
    return str(value)


def _get_dotted(obj: Any, dotted: str) -> Any:
    """Walk a dotted path through nested dicts. Raises KeyError if missing."""
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(dotted)
    return cur


def substitute(
    template: str,
    context: Dict[str, Any],
    context_schema: Dict[str, Any],
) -> str:
    """Substitute typed placeholders in template using context.

    context_schema is the body of a context.schema.json file (object with
    `placeholders[]` array per ritual_context.schema.json).

    Raises:
      MissingPlaceholderError — required placeholder missing from context.
      TypeMismatchError — value fails type-specific validation.
      UntypedPlaceholderError — template contains a non-typed double-brace
                                 token or a typed token whose identifier is
                                 not declared in context_schema.
    """
    placeholders = {
        p["identifier"]: p for p in context_schema.get("placeholders", [])
    }

    # Pre-pass: reject any double-brace token that is not a typed placeholder.
    for match in _ANY_DOUBLE_BRACE_RE.finditer(template):
        token = match.group(0)
        if not _TYPED_PLACEHOLDER_RE.fullmatch(token):
            raise UntypedPlaceholderError(
                f"non-typed placeholder rejected: {token!r}"
            )

    def _sub(match: "re.Match[str]") -> str:
        type_name = match.group(1)
        identifier = match.group(2)
        spec = placeholders.get(identifier)
        if spec is None:
            raise UntypedPlaceholderError(
                f"placeholder {identifier!r} not declared in context_schema"
            )
        try:
            value = _get_dotted(context, identifier)
        except KeyError:
            if spec.get("required"):
                raise MissingPlaceholderError(
                    f"required placeholder {identifier!r} missing from context"
                )
            value = ""
        return _escape_for_type(value, type_name, spec.get("enum_values"))

    return _TYPED_PLACEHOLDER_RE.sub(_sub, template)


# ───────────────────────── Redaction ─────────────────────────

_REDACTION_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.=]+", re.IGNORECASE),
)
_ENV_CREDENTIAL_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
)


def _redact(text: str) -> str:
    """Replace credential-shaped strings and env-credential values with [REDACTED].

    Constitution Article XVII — secret handling. Used before every audit
    emission and inside every BackendError message.
    """
    if not text:
        return text
    redacted = text
    for pat in _REDACTION_PATTERNS:
        redacted = pat.sub("[REDACTED]", redacted)
    for var in _ENV_CREDENTIAL_VARS:
        v = os.environ.get(var)
        if v and len(v) >= 8:
            redacted = redacted.replace(v, "[REDACTED]")
    return redacted


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ───────────────────────── Backends ─────────────────────────


class Backend(ABC):
    """Capability declaration (Article XXVIII):
      - role: external-LLM transport
      - authority: none (transport-only; never decides verdicts)
      - inputs: LLMRequest
      - outputs: LLMResponse
      - artifacts: none (caller decides what to persist)
      - state: stateless (backend instance has no mutable state across calls)
      - failure: raises BackendUnavailable / BackendError / BackendTimeout
      - audit: caller emits llm.call_* events via call_llm()
      - security: redacts credentials before raising
    """

    name: str = "abstract"

    @property
    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def invoke(self, request: LLMRequest) -> LLMResponse: ...


class _CLIBackendBase(Backend):
    """Common implementation for one-shot CLI subprocess backends."""

    binary: str = ""

    @property
    def available(self) -> bool:
        return bool(self.binary) and shutil.which(self.binary) is not None

    def build_argv(self, request: LLMRequest) -> List[str]:
        raise NotImplementedError

    def invoke(self, request: LLMRequest) -> LLMResponse:
        if not self.available:
            raise BackendUnavailable(
                f"{self.name} CLI not in PATH (binary={self.binary!r})"
            )
        argv = self.build_argv(request)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=request.timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise BackendTimeout(
                f"{self.name} exceeded timeout {request.timeout}s"
            ) from e
        duration_ms = int((time.monotonic() - started) * 1000)
        if proc.returncode != 0:
            raise BackendError(
                f"{self.name} returncode={proc.returncode}: "
                f"{_redact(proc.stderr)[:500]}"
            )
        return LLMResponse(
            text=proc.stdout.strip(),
            model=self.name,
            backend=self.name,
            duration_ms=duration_ms,
            raw={
                "stdout_chars": len(proc.stdout),
                "stderr_chars": len(proc.stderr),
                "returncode": proc.returncode,
                "argv0": argv[0] if argv else "",
            },
        )


class ClaudeCLIBackend(_CLIBackendBase):
    name = "claude"
    binary = "claude"

    def build_argv(self, request: LLMRequest) -> List[str]:
        return [self.binary, "-p", request.prompt]


class GeminiCLIBackend(_CLIBackendBase):
    name = "gemini"
    binary = "gemini"

    def build_argv(self, request: LLMRequest) -> List[str]:
        return [self.binary, "-p", request.prompt]


class CodexCLIBackend(_CLIBackendBase):
    name = "codex"
    binary = "codex"

    def build_argv(self, request: LLMRequest) -> List[str]:
        return [self.binary, "exec", request.prompt]


class AnthropicAPIBackend(Backend):
    """Optional API backend. Uses anthropic SDK if installed and ANTHROPIC_API_KEY set."""

    name = "anthropic-api"

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        self.model = model
        try:
            import anthropic  # noqa: F401
            self._sdk_available = True
        except ImportError:
            self._sdk_available = False

    @property
    def available(self) -> bool:
        return self._sdk_available and bool(os.environ.get("ANTHROPIC_API_KEY"))

    def invoke(self, request: LLMRequest) -> LLMResponse:
        if not self._sdk_available:
            raise BackendUnavailable("anthropic SDK not installed")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise BackendUnavailable("ANTHROPIC_API_KEY not set in env")
        from anthropic import Anthropic, APIError

        client = Anthropic()
        model = request.model or self.model
        started = time.monotonic()
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": request.prompt}],
            )
        except APIError as e:
            raise BackendError(
                f"anthropic API: {_redact(str(e))[:500]}"
            ) from e
        duration_ms = int((time.monotonic() - started) * 1000)
        text = ""
        if getattr(msg, "content", None):
            block = msg.content[0]
            text = getattr(block, "text", "") or ""
        return LLMResponse(
            text=text,
            model=getattr(msg, "model", model),
            backend=self.name,
            duration_ms=duration_ms,
            raw={
                "stop_reason": getattr(msg, "stop_reason", None),
            },
        )


@dataclass
class MockBackend(Backend):
    """Deterministic backend for tests; never reaches network or subprocess."""

    name: str = "mock"
    canned: str = "MOCK_RESPONSE"
    canned_model: str = "mock-model"

    @property
    def available(self) -> bool:
        return True

    def invoke(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text=self.canned,
            model=self.canned_model,
            backend=self.name,
            duration_ms=0,
            raw={"prompt_chars": len(request.prompt)},
        )


# ───────────────────────── Discovery and selection ─────────────────────────

_DEFAULT_PREFERENCE = ("claude", "codex", "gemini", "anthropic-api")


def discover_backends() -> List[Backend]:
    """Instantiate one of each known backend; consult .available to filter.

    Returned list is a fresh instance — callers may keep their own instances
    (e.g. with custom Anthropic models) and pass to select_backend(backends=).
    """
    return [
        ClaudeCLIBackend(),
        GeminiCLIBackend(),
        CodexCLIBackend(),
        AnthropicAPIBackend(),
    ]


def select_backend(
    request: Optional[LLMRequest] = None,
    preference: Optional[Sequence[str]] = None,
    env_override: Optional[str] = None,
    backends: Optional[Sequence[Backend]] = None,
) -> Backend:
    """Select a backend per the documented strategy:
      1) request.backend (explicit override)
      2) env_override / LLM_BACKEND env var
      3) preference list (default: claude, codex, gemini, anthropic-api)
    """
    pool = list(backends) if backends is not None else discover_backends()
    by_name = {b.name: b for b in pool}

    # 1) Request-level override.
    if request is not None and request.backend:
        b = by_name.get(request.backend)
        if b is None:
            raise NoBackendAvailable(
                f"unknown backend: {request.backend!r}"
            )
        if not b.available:
            raise BackendUnavailable(
                f"requested backend {request.backend!r} is not available"
            )
        return b

    # 2) Environment override.
    env_name = env_override
    if env_name is None:
        env_name = os.environ.get("LLM_BACKEND")
    if env_name:
        key = env_name.lower()
        b = by_name.get(key)
        if b is None:
            raise NoBackendAvailable(
                f"LLM_BACKEND={env_name!r} is not a known backend"
            )
        if not b.available:
            raise BackendUnavailable(
                f"LLM_BACKEND={env_name!r} is not available"
            )
        return b

    # 3) Preference list.
    pref = preference if preference is not None else _DEFAULT_PREFERENCE
    for name in pref:
        b = by_name.get(name)
        if b is not None and b.available:
            return b

    avail = sorted([b.name for b in pool if b.available])
    raise NoBackendAvailable(
        f"no backend in {list(pref)!r} is available; have {avail}"
    )


# ───────────────────────── call_llm — orchestrator ─────────────────────────


def call_llm(
    request: LLMRequest,
    backend: Optional[Backend] = None,
    audit_chain: Optional[AuditChain] = None,
    ritual_context: Optional[Dict[str, Any]] = None,
) -> LLMResponse:
    """Invoke an LLM with audit emission and credential redaction.

    Arguments:
      request — the LLMRequest to send.
      backend — explicit backend (overrides selection); when None, calls
                 select_backend(request=request).
      audit_chain — when provided, emits 'llm.call_started' (before invoke),
                    'llm.call_completed' (success), 'llm.call_failed' (error).
                    When None, audit is silent (useful for unit tests).
      ritual_context — optional metadata recorded on audit events (e.g.
                       {"ritual": "vvv", "session_id": "..."}).

    Returns LLMResponse on success.
    Raises BackendUnavailable / BackendError / BackendTimeout / NoBackendAvailable.
    """
    chosen = backend if backend is not None else select_backend(request=request)
    prompt_redacted = _redact(request.prompt)

    if audit_chain is not None:
        started_details: Dict[str, Any] = {
            "backend": chosen.name,
            "model": request.model or chosen.name,
            "prompt_sha256": _sha256(prompt_redacted),
            "prompt_chars": len(request.prompt),
        }
        if ritual_context:
            if "ritual" in ritual_context:
                started_details["ritual"] = ritual_context["ritual"]
            if "session_id" in ritual_context:
                started_details["session_id"] = ritual_context["session_id"]
        audit_chain.append("llm.call_started", started_details)

    try:
        response = chosen.invoke(request)
    except LLMError as e:
        if audit_chain is not None:
            audit_chain.append("llm.call_failed", {
                "backend": chosen.name,
                "error_class": e.__class__.__name__,
                "error_message": _redact(str(e))[:500],
            })
        raise

    if audit_chain is not None:
        audit_chain.append("llm.call_completed", {
            "backend": chosen.name,
            "model": response.model,
            "response_chars": len(response.text),
            "response_sha256": _sha256(_redact(response.text)),
            "duration_ms": response.duration_ms,
        })
    return response


__all__ = [
    # public API
    "call_llm",
    "load_ritual_pack",
    "substitute",
    "discover_backends",
    "select_backend",
    # dataclasses
    "LLMRequest",
    "LLMResponse",
    "RitualPack",
    # backends
    "Backend",
    "ClaudeCLIBackend",
    "GeminiCLIBackend",
    "CodexCLIBackend",
    "AnthropicAPIBackend",
    "MockBackend",
    # errors
    "LLMError",
    "MissingPlaceholderError",
    "TypeMismatchError",
    "UntypedPlaceholderError",
    "BackendUnavailable",
    "BackendError",
    "BackendTimeout",
    "NoBackendAvailable",
]
