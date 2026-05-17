"""Clarification Helper — second in-house Trinity agent.

Drafts 5 vvv answers (Goal / Scope / Constraint / Acceptance / Risk) from an
active session's THINK/00_CONTEXT.md plus an operator task description. Output
shape matches what `ai vvv --answers-file` expects:

  {"1": "...", "2": "...", "3": "...", "4": "...", "5": "..."}

Authority:
  - Constitution v1.0 Articles III, IV, IX, XVI, XVII, XX (see plan envelope).
  - RC v1.1-rc Articles XVI (template injection), XVIII (Clarification Agent role).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from cli.core.audit import AuditChain
from cli.core.llm_call import (
    Backend,
    LLMRequest,
    call_llm,
    select_backend,
    substitute,
)


_HERE = Path(__file__).resolve().parent
_PROMPT_PATH = _HERE / "prompts" / "draft.md"

_REQUIRED_KEYS = ("1", "2", "3", "4", "5")
_MIN_ANSWER_CHARS = 40  # validation floor; prompt asks for >=80 but we keep
                       # the floor at 40 so a slightly-terse LLM response is
                       # still useful; tighter checks belong in the prompt itself.


class ValidationError(Exception):
    """The LLM-returned draft failed shape or content validation."""


@dataclass
class ClarificationDraft:
    answers: Dict[str, str]  # keys '1' through '5'

    def to_dict(self) -> Dict[str, str]:
        return dict(self.answers)

    def to_vvv_args_file(self) -> str:
        """Serialize as the JSON shape `ai vvv --answers-file` accepts."""
        return json.dumps(self.answers, indent=2, ensure_ascii=False)


def _read_session_context(session_path: Path) -> str:
    """Read THINK/00_CONTEXT.md from the active session directory.

    Returns the file body as text. Raises FileNotFoundError if the session
    directory or context file is missing.
    """
    if not session_path.is_dir():
        raise FileNotFoundError(f"session path not found: {session_path}")
    context_path = session_path / "THINK" / "00_CONTEXT.md"
    if not context_path.is_file():
        raise FileNotFoundError(f"session context not found: {context_path}")
    return context_path.read_text(encoding="utf-8")


def _validate_draft(d: Any) -> None:
    """Raise ValidationError if the draft dict is malformed."""
    if not isinstance(d, dict):
        raise ValidationError(f"expected dict, got {type(d).__name__}")
    missing = [k for k in _REQUIRED_KEYS if k not in d]
    if missing:
        raise ValidationError(f"missing required keys: {missing}")
    extras = [k for k in d.keys() if k not in _REQUIRED_KEYS]
    if extras:
        raise ValidationError(f"unexpected extra keys: {extras}")
    for k in _REQUIRED_KEYS:
        v = d[k]
        if not isinstance(v, str):
            raise ValidationError(
                f"answer '{k}' must be a string; got {type(v).__name__}"
            )
        stripped = v.strip()
        if not stripped:
            raise ValidationError(f"answer '{k}' is empty")
        if len(stripped) < _MIN_ANSWER_CHARS:
            raise ValidationError(
                f"answer '{k}' too short: {len(stripped)} chars "
                f"(minimum {_MIN_ANSWER_CHARS})"
            )


def _parse_llm_json(text: str) -> Dict[str, Any]:
    """Strict JSON parse with optional ```json fence stripping."""
    stripped = text.strip()
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        if first_nl == -1:
            raise ValidationError("LLM response had ``` but no newline")
        body = stripped[first_nl + 1 :]
        if body.endswith("```"):
            body = body[: -3].rstrip()
        stripped = body.strip()
    if not stripped.startswith("{"):
        raise ValidationError(
            f"LLM response must start with '{{' after stripping fences; "
            f"got: {stripped[:80]!r}"
        )
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"LLM response is not valid JSON: {e.msg} at pos {e.pos}"
        ) from e


def _session_slug_from_path(session_path: Path) -> str:
    """Derive a short slug from the session directory name.

    Format: 0001_<date>_<time>_<slug>; return everything after the time.
    Falls back to the basename if no match.
    """
    name = session_path.name
    m = re.match(
        r"^\d+_\d{4}-\d{2}-\d{2}_\d{1,2}_\d{2}_(?:am|pm)_(.+)$",
        name,
    )
    return m.group(1) if m else name


def draft_vvv_answers(
    description: str,
    session_path: Path,
    backend: Optional[Backend] = None,
    audit_chain: Optional[AuditChain] = None,
) -> ClarificationDraft:
    """Top-level entry point: draft 5 vvv answers for the given session.

    Audit events emitted (when audit_chain is provided):
      - clarification_helper.invoked (always, before LLM call)
      - clarification_helper.proposed (on validated success)
      - clarification_helper.failed (on ValidationError / backend error)
    """
    if not isinstance(description, str) or not description.strip():
        raise ValidationError("description must be a non-empty string")

    context_md = _read_session_context(session_path)
    slug = _session_slug_from_path(session_path)

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    context_schema = {
        "context_schema_version": "1.0",
        "ritual": "clarification_helper",
        "placeholders": [
            {
                "identifier": "session.slug",
                "type": "plain_text",
                "required": True,
                "description": "Active session slug (data only).",
            },
            {
                "identifier": "operator.task_description",
                "type": "markdown_escaped",
                "required": True,
                "description": "Operator's free-form task description.",
            },
            {
                "identifier": "session.context_md",
                "type": "markdown_escaped",
                "required": True,
                "description": "Active session THINK/00_CONTEXT.md body.",
            },
        ],
    }
    ctx = {
        "session": {"slug": slug, "context_md": context_md},
        "operator": {"task_description": description},
    }
    prompt = substitute(template, ctx, context_schema)

    if audit_chain is not None:
        audit_chain.append("clarification_helper.invoked", {
            "session_slug": slug,
            "description_chars": len(description),
            "context_chars": len(context_md),
        })

    backend = backend if backend is not None else select_backend()
    request = LLMRequest(prompt=prompt, timeout=120.0)

    try:
        response = call_llm(
            request,
            backend=backend,
            audit_chain=audit_chain,
            ritual_context={
                "ritual": "clarification_helper",
                "session_slug": slug,
            },
        )
        draft_dict = _parse_llm_json(response.text)
        _validate_draft(draft_dict)
    except Exception as e:
        if audit_chain is not None:
            audit_chain.append("clarification_helper.failed", {
                "error_class": e.__class__.__name__,
                "error_message": str(e)[:500],
                "session_slug": slug,
            })
        raise

    if audit_chain is not None:
        audit_chain.append("clarification_helper.proposed", {
            "session_slug": slug,
            "answer_chars_total": sum(len(draft_dict[k]) for k in _REQUIRED_KEYS),
        })

    return ClarificationDraft(answers={k: draft_dict[k] for k in _REQUIRED_KEYS})


__all__ = [
    "draft_vvv_answers",
    "ClarificationDraft",
    "ValidationError",
    "_read_session_context",
    "_validate_draft",
    "_parse_llm_json",
    "_session_slug_from_path",
]
