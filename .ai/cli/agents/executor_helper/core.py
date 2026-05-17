"""Executor Helper — fourth in-house Trinity agent.

Drafts structured implementation proposal for a single plan_envelope step.
Output JSON shape:
  {step_id, files_to_create:[{path,content}], files_to_edit:[{path,old,new}],
   commands_to_run:[{cmd,cwd,expect_exit}], notes}

Authority:
  - Constitution v1.0 Articles III, IV (separation; Planner ≠ Executor),
    IX (exact-evidence), XVI (least authority), XVII (secret handling),
    XX (passive core).
  - RC v1.1-rc Articles XVI (template injection), XVIII (Executor Agent row).

Proposer-only design: agent NEVER writes files, runs commands, or invokes
the kernel. Operator (or future applier organ) is the gate.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

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

_REQUIRED_TOP_KEYS = (
    "step_id",
    "files_to_create",
    "files_to_edit",
    "commands_to_run",
    "notes",
)
_CREATE_KEYS = ("path", "content")
_EDIT_KEYS = ("path", "old", "new")
_COMMAND_KEYS = ("cmd", "cwd", "expect_exit")


class ValidationError(Exception):
    """LLM-returned proposal failed schema validation."""


class StepNotFoundError(Exception):
    """The requested step_id is not present in the session's plan_envelope."""


@dataclass
class ExecutionProposal:
    proposal: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.proposal)

    def to_json(self) -> str:
        return json.dumps(self.proposal, indent=2, ensure_ascii=False)


def _read_session_inputs(session_path: Path) -> Dict[str, Any]:
    """Read THINK/00_CONTEXT.md and .state/plan.json (kernel's canonical home)."""
    if not session_path.is_dir():
        raise FileNotFoundError(f"session path not found: {session_path}")
    context_path = session_path / "THINK" / "00_CONTEXT.md"
    plan_path = session_path / ".state" / "plan.json"
    if not context_path.is_file():
        raise FileNotFoundError(f"context not found: {context_path}")
    if not plan_path.is_file():
        raise FileNotFoundError(
            f".state/plan.json not found at {plan_path} — run `ai nnn` first"
        )
    ctx_md = context_path.read_text(encoding="utf-8")
    envelope = json.loads(plan_path.read_text(encoding="utf-8"))
    return {"context_md": ctx_md, "plan_envelope": envelope}


def _find_step(envelope: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    steps = envelope.get("steps", [])
    for step in steps:
        if step.get("id") == step_id:
            return step
    available = [s.get("id", "?") for s in steps]
    raise StepNotFoundError(
        f"step_id {step_id!r} not found; available: {available}"
    )


def _session_slug_from_path(session_path: Path) -> str:
    name = session_path.name
    m = re.match(
        r"^\d+_\d{4}-\d{2}-\d{2}_\d{1,2}_\d{2}_(?:am|pm)_(.+)$",
        name,
    )
    return m.group(1) if m else name


def _summarize_other_steps(
    envelope: Dict[str, Any],
    target_step_id: str,
    max_chars: int = 4000,
) -> str:
    """Build a bullet summary of other steps for dependency/dedup context.

    Cap at max_chars to avoid token blow-up on large plans (Risk #4 mitigation).
    """
    lines: List[str] = []
    for step in envelope.get("steps", []):
        sid = step.get("id", "?")
        if sid == target_step_id:
            continue
        action = step.get("action", "")[:200]
        lines.append(f"- {sid}: {action}")
    body = "\n".join(lines)
    if len(body) > max_chars:
        body = body[:max_chars] + "\n... (truncated)"
    return body or "(no other steps)"


def _validate_proposal(d: Any) -> None:
    """Strict schema check. Raises ValidationError on any deviation."""
    if not isinstance(d, dict):
        raise ValidationError(f"proposal must be a dict; got {type(d).__name__}")
    missing = [k for k in _REQUIRED_TOP_KEYS if k not in d]
    if missing:
        raise ValidationError(f"missing top-level keys: {missing}")
    if not isinstance(d["step_id"], str) or not d["step_id"]:
        raise ValidationError("step_id must be a non-empty string")
    if not isinstance(d["files_to_create"], list):
        raise ValidationError("files_to_create must be a list")
    for i, item in enumerate(d["files_to_create"]):
        if not isinstance(item, dict):
            raise ValidationError(f"files_to_create[{i}] must be a dict")
        missing_keys = [k for k in _CREATE_KEYS if k not in item]
        if missing_keys:
            raise ValidationError(
                f"files_to_create[{i}] missing keys {missing_keys} "
                f"(expected {_CREATE_KEYS})"
            )
        if not isinstance(item["path"], str) or not item["path"]:
            raise ValidationError(
                f"files_to_create[{i}].path must be a non-empty string"
            )
        if not isinstance(item["content"], str):
            raise ValidationError(
                f"files_to_create[{i}].content must be a string"
            )
    if not isinstance(d["files_to_edit"], list):
        raise ValidationError("files_to_edit must be a list")
    for i, item in enumerate(d["files_to_edit"]):
        if not isinstance(item, dict):
            raise ValidationError(f"files_to_edit[{i}] must be a dict")
        missing_keys = [k for k in _EDIT_KEYS if k not in item]
        if missing_keys:
            raise ValidationError(
                f"files_to_edit[{i}] missing keys {missing_keys} "
                f"(expected {_EDIT_KEYS})"
            )
        for key in _EDIT_KEYS:
            if not isinstance(item[key], str):
                raise ValidationError(
                    f"files_to_edit[{i}].{key} must be a string"
                )
        if not item["path"] or not item["old"]:
            raise ValidationError(
                f"files_to_edit[{i}]: path and old must be non-empty"
            )
    if not isinstance(d["commands_to_run"], list):
        raise ValidationError("commands_to_run must be a list")
    for i, item in enumerate(d["commands_to_run"]):
        if not isinstance(item, dict):
            raise ValidationError(
                f"commands_to_run[{i}] must be a dict, not a plain string"
            )
        missing_keys = [k for k in _COMMAND_KEYS if k not in item]
        if missing_keys:
            raise ValidationError(
                f"commands_to_run[{i}] missing keys {missing_keys}"
            )
        if not isinstance(item["cmd"], str) or not item["cmd"]:
            raise ValidationError(
                f"commands_to_run[{i}].cmd must be a non-empty string"
            )
        if not isinstance(item["cwd"], str):
            raise ValidationError(
                f"commands_to_run[{i}].cwd must be a string"
            )
        if not isinstance(item["expect_exit"], int):
            raise ValidationError(
                f"commands_to_run[{i}].expect_exit must be an integer"
            )
    if not isinstance(d["notes"], str) or not d["notes"].strip():
        raise ValidationError("notes must be a non-empty string")


def _parse_llm_json(text: str) -> Dict[str, Any]:
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
            f"LLM response must start with '{{'; got: {stripped[:80]!r}"
        )
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"LLM response is not valid JSON: {e.msg} at pos {e.pos}"
        ) from e


def draft_step_implementation(
    session_path: Path,
    step_id: str,
    backend: Optional[Backend] = None,
    audit_chain: Optional[AuditChain] = None,
) -> ExecutionProposal:
    """Top-level entry. Audit events: executor_helper.invoked / .proposed / .failed."""
    inputs = _read_session_inputs(session_path)
    envelope = inputs["plan_envelope"]
    step = _find_step(envelope, step_id)
    slug = _session_slug_from_path(session_path)

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    context_schema = {
        "context_schema_version": "1.0",
        "ritual": "executor_helper",
        "placeholders": [
            {"identifier": "session.slug", "type": "plain_text", "required": True, "description": "slug"},
            {"identifier": "session.context_md", "type": "markdown_escaped", "required": True, "description": "context md"},
            {"identifier": "step.id", "type": "plain_text", "required": True, "description": "step id"},
            {"identifier": "step.action", "type": "markdown_escaped", "required": True, "description": "action"},
            {"identifier": "step.expected_artifact", "type": "markdown_escaped", "required": True, "description": "expected artifact"},
            {"identifier": "step.owner_role", "type": "plain_text", "required": True, "description": "owner role"},
            {"identifier": "plan.other_steps_summary", "type": "markdown_escaped", "required": True, "description": "summary"},
        ],
    }
    ctx = {
        "session": {"slug": slug, "context_md": inputs["context_md"]},
        "step": {
            "id": step.get("id", ""),
            "action": step.get("action", ""),
            "expected_artifact": step.get("expected_artifact", ""),
            "owner_role": step.get("owner_role", ""),
        },
        "plan": {
            "other_steps_summary": _summarize_other_steps(envelope, step_id),
        },
    }
    prompt = substitute(template, ctx, context_schema)

    if audit_chain is not None:
        audit_chain.append("executor_helper.invoked", {
            "session_slug": slug,
            "step_id": step_id,
            "context_chars": len(inputs["context_md"]),
        })

    backend = backend if backend is not None else select_backend()
    request = LLMRequest(prompt=prompt, timeout=180.0)

    try:
        response = call_llm(
            request,
            backend=backend,
            audit_chain=audit_chain,
            ritual_context={
                "ritual": "executor_helper",
                "session_slug": slug,
                "step_id": step_id,
            },
        )
        proposal = _parse_llm_json(response.text)
        _validate_proposal(proposal)
        if proposal.get("step_id") != step_id:
            raise ValidationError(
                f"proposal.step_id {proposal.get('step_id')!r} does not match "
                f"requested step_id {step_id!r}"
            )
    except Exception as e:
        if audit_chain is not None:
            audit_chain.append("executor_helper.failed", {
                "error_class": e.__class__.__name__,
                "error_message": str(e)[:500],
                "session_slug": slug,
                "step_id": step_id,
            })
        raise

    if audit_chain is not None:
        audit_chain.append("executor_helper.proposed", {
            "session_slug": slug,
            "step_id": step_id,
            "files_to_create_count": len(proposal["files_to_create"]),
            "files_to_edit_count": len(proposal["files_to_edit"]),
            "commands_to_run_count": len(proposal["commands_to_run"]),
        })

    return ExecutionProposal(proposal=proposal)


__all__ = [
    "draft_step_implementation",
    "ExecutionProposal",
    "ValidationError",
    "StepNotFoundError",
    "_read_session_inputs",
    "_find_step",
    "_validate_proposal",
    "_parse_llm_json",
    "_session_slug_from_path",
    "_summarize_other_steps",
]
