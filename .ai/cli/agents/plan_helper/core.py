"""Plan Helper — third in-house Trinity agent.

Drafts plan_envelope.json from active session's 00_CONTEXT.md + 01_PROMPT.md
(post-vvv). Output JSON is shape-compatible with `ai nnn --plan-envelope -`.

Authority:
  - Constitution v1.0 Articles III, IV, IX, XVI, XVII, XX, XXII (rollback).
  - RC v1.1-rc Articles XVI (template injection), XVIII (Planning Agent row).

⚠️ CANONICAL ACCEPTANCE SCHEMA enforcement: every acceptance row MUST have
keys {id, description, command, expect_exit, required}. The criterion+check
shape is rejected (documented foot-gun: feedback_nnn_rrr_acceptance_schema_mismatch).
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
    "goal",
    "tier",
    "allowed_paths",
    "forbidden_paths",
    "constitutional_notes",
    "steps",
    "acceptance",
    "rollback",
    "decided_by",
)
_VALID_TIERS = frozenset({"HOT", "WARM", "COLD"})
_VALID_OWNER_ROLES = frozenset({"EXECUTOR", "VERIFIER", "PLANNER"})
_VALID_RISKS = frozenset({"LOW", "MEDIUM", "HIGH"})
_ACCEPTANCE_REQUIRED_KEYS = ("id", "description", "command", "expect_exit", "required")
_STEP_REQUIRED_KEYS = ("id", "action", "owner_role", "expected_artifact", "risk")
_MIN_ROLLBACK_ENTRIES = 3

# Drift-detection patterns documented in feedback_plan_helper_drift_corrections.md.
# These reject acceptance.command values that exhibit known LLM drift patterns
# without auto-rewriting (Article III: agent proposes; operator decides).
_DRIFT_TEST_PATH_RE = re.compile(r"cli/agents/[A-Za-z_]+/tests")
_DRIFT_AUDIT_DIFF_RE = re.compile(r"git\s+diff[^\n]*\.ai/audit/?")
_DRIFT_BACKEND_FLAG_RE = re.compile(r"--backend[=\s]+\S+")


class ValidationError(Exception):
    """The LLM-returned envelope failed schema or content validation."""


@dataclass
class PlanDraft:
    envelope: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.envelope)

    def to_nnn_input(self) -> str:
        return json.dumps(self.envelope, indent=2, ensure_ascii=False)


def _read_session_inputs(session_path: Path) -> Dict[str, str]:
    """Read THINK/00_CONTEXT.md and THINK/01_PROMPT.md from the session.

    Raises FileNotFoundError on either missing — hard error per the design
    decision (no stub fallback). Empty file (whitespace only) is also a hard
    error.
    """
    if not session_path.is_dir():
        raise FileNotFoundError(f"session path not found: {session_path}")
    context_path = session_path / "THINK" / "00_CONTEXT.md"
    prompt_path = session_path / "THINK" / "01_PROMPT.md"
    if not context_path.is_file():
        raise FileNotFoundError(f"session context not found: {context_path}")
    if not prompt_path.is_file():
        raise FileNotFoundError(
            f"vvv prompt not found: {prompt_path} — run `ai vvv` first"
        )
    ctx_md = context_path.read_text(encoding="utf-8")
    prompt_md = prompt_path.read_text(encoding="utf-8")
    if not ctx_md.strip():
        raise FileNotFoundError(f"session context is empty: {context_path}")
    if not prompt_md.strip():
        raise FileNotFoundError(
            f"vvv prompt is empty: {prompt_path} — run `ai vvv` first"
        )
    return {"context_md": ctx_md, "vvv_prompt_md": prompt_md}


def _session_slug_from_path(session_path: Path) -> str:
    name = session_path.name
    m = re.match(
        r"^\d+_\d{4}-\d{2}-\d{2}_\d{1,2}_\d{2}_(?:am|pm)_(.+)$",
        name,
    )
    return m.group(1) if m else name


def _validate_envelope(d: Any) -> None:
    """Full plan_envelope schema check. Raises ValidationError on any deviation."""
    if not isinstance(d, dict):
        raise ValidationError(f"envelope must be a dict; got {type(d).__name__}")

    missing = [k for k in _REQUIRED_TOP_KEYS if k not in d]
    if missing:
        raise ValidationError(f"missing top-level keys: {missing}")

    if not isinstance(d["goal"], str) or not d["goal"].strip():
        raise ValidationError("goal must be a non-empty string")
    if d["tier"] not in _VALID_TIERS:
        raise ValidationError(
            f"tier must be one of {sorted(_VALID_TIERS)}; got {d['tier']!r}"
        )
    if not isinstance(d["allowed_paths"], list) or not d["allowed_paths"]:
        raise ValidationError("allowed_paths must be a non-empty list")
    if not all(isinstance(p, str) for p in d["allowed_paths"]):
        raise ValidationError("allowed_paths entries must all be strings")
    if not isinstance(d["forbidden_paths"], list):
        raise ValidationError("forbidden_paths must be a list")
    if not all(isinstance(p, str) for p in d["forbidden_paths"]):
        raise ValidationError("forbidden_paths entries must all be strings")
    if not isinstance(d["constitutional_notes"], list):
        raise ValidationError("constitutional_notes must be a list")
    if not all(isinstance(n, str) for n in d["constitutional_notes"]):
        raise ValidationError("constitutional_notes entries must all be strings")

    if not isinstance(d["steps"], list) or not d["steps"]:
        raise ValidationError("steps must be a non-empty list")
    for i, step in enumerate(d["steps"]):
        if not isinstance(step, dict):
            raise ValidationError(f"steps[{i}] must be a dict")
        missing_step = [k for k in _STEP_REQUIRED_KEYS if k not in step]
        if missing_step:
            raise ValidationError(
                f"steps[{i}] missing keys: {missing_step}"
            )
        if step["owner_role"] not in _VALID_OWNER_ROLES:
            raise ValidationError(
                f"steps[{i}].owner_role must be one of "
                f"{sorted(_VALID_OWNER_ROLES)}; got {step['owner_role']!r}"
            )
        if step["risk"] not in _VALID_RISKS:
            raise ValidationError(
                f"steps[{i}].risk must be one of {sorted(_VALID_RISKS)}; "
                f"got {step['risk']!r}"
            )

    if not isinstance(d["acceptance"], list) or not d["acceptance"]:
        raise ValidationError("acceptance must be a non-empty list")
    for i, row in enumerate(d["acceptance"]):
        if not isinstance(row, dict):
            raise ValidationError(f"acceptance[{i}] must be a dict")
        missing_row = [k for k in _ACCEPTANCE_REQUIRED_KEYS if k not in row]
        if missing_row:
            raise ValidationError(
                f"acceptance[{i}] missing required keys {missing_row} — "
                f"canonical schema is {_ACCEPTANCE_REQUIRED_KEYS} "
                f"(NOT criterion/check; see feedback_nnn_rrr_acceptance_schema_mismatch)"
            )
        # Reject the documented foot-gun explicitly with a clear message.
        wrong_keys = [k for k in ("criterion", "check") if k in row]
        if wrong_keys:
            raise ValidationError(
                f"acceptance[{i}] contains forbidden keys {wrong_keys} — "
                f"use {_ACCEPTANCE_REQUIRED_KEYS} instead; "
                f"this is the documented foot-gun "
                f"(feedback_nnn_rrr_acceptance_schema_mismatch)"
            )
        if not isinstance(row["id"], str) or not row["id"]:
            raise ValidationError(f"acceptance[{i}].id must be a non-empty string")
        if not isinstance(row["description"], str) or not row["description"].strip():
            raise ValidationError(
                f"acceptance[{i}].description must be a non-empty string"
            )
        if not isinstance(row["command"], str) or not row["command"].strip():
            raise ValidationError(
                f"acceptance[{i}].command must be a non-empty string"
            )
        if not isinstance(row["expect_exit"], int):
            raise ValidationError(
                f"acceptance[{i}].expect_exit must be an integer"
            )
        if not isinstance(row["required"], bool):
            raise ValidationError(
                f"acceptance[{i}].required must be a boolean"
            )
        # Drift-pattern detection (fail-fast on first match) — see
        # feedback_plan_helper_drift_corrections.md.
        cmd = row["command"]
        if _DRIFT_TEST_PATH_RE.search(cmd):
            raise ValidationError(
                f"acceptance[{i}] drift pattern (test path): command uses "
                f"`cli/agents/<name>/tests` — Trinity convention is "
                f"`.ai/cli/tests/test_<name>_agent.py`. Offending row id="
                f"{row['id']!r}, command={cmd[:200]!r}"
            )
        if _DRIFT_AUDIT_DIFF_RE.search(cmd):
            raise ValidationError(
                f"acceptance[{i}] drift pattern (audit-events not exempt): "
                f"command runs `git diff` against `.ai/audit/` — that "
                f"directory is kernel-mechanical append-only and every "
                f"session appends events. Use the canonical hash-chain "
                f"genesis check instead. Offending row id={row['id']!r}, "
                f"command={cmd[:200]!r}"
            )
        if _DRIFT_BACKEND_FLAG_RE.search(cmd):
            raise ValidationError(
                f"acceptance[{i}] drift pattern (fake --backend flag): "
                f"no Trinity agent has a `--backend` CLI flag. Backend "
                f"selection uses the LLM_BACKEND env var. Offending row "
                f"id={row['id']!r}, command={cmd[:200]!r}"
            )

    if not isinstance(d["rollback"], list):
        raise ValidationError("rollback must be a list")
    if len(d["rollback"]) < _MIN_ROLLBACK_ENTRIES:
        raise ValidationError(
            f"rollback must have at least {_MIN_ROLLBACK_ENTRIES} entries "
            f"(Article XXII); got {len(d['rollback'])}"
        )
    if not all(isinstance(r, str) and r.strip() for r in d["rollback"]):
        raise ValidationError("rollback entries must all be non-empty strings")

    if d["decided_by"] != "human":
        raise ValidationError(
            f"decided_by must be 'human' (Article XIII); got {d['decided_by']!r}"
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


def _resolve_project_root(session_path: Path) -> Path:
    """Walk up from session_path until we find a .ai directory.

    plan_helper runs as a subprocess so the cwd may differ; resolving
    via session_path is more reliable than cwd-based heuristics.
    Returns the parent that contains .ai/, or session_path.parent as
    fallback (rare).
    """
    cur = session_path.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".ai").is_dir():
            return parent
    return session_path.parent


def _infer_step_tools(
    envelope: Dict[str, Any], project_root: Path
) -> List[Dict[str, str]]:
    """S16 — scan each step.action for registered tool-registry names.

    When a registered tool name appears as a whole word in step.action
    AND the step does NOT already declare a `tool:` field, inject it.

    Whole-word detection is hyphen-aware: tool names like `browser-cli`
    contain `-` which is NOT a `\\w` character; standard `\\b` boundary
    treats `browser-cli` as two tokens. The pattern uses
    `(?<![\\w-])<name>(?![\\w-])` to extend word boundaries across `-`.

    Case-insensitive: operators writing 'Browser-CLI' still match.

    Returns a list of {step_id, tool_name} dicts for audit logging.
    Fail-soft: registry-load failures swallow the exception and return
    an empty list (Article XX — plan inference must not abort).
    """
    inferred: List[Dict[str, str]] = []
    try:
        from cli.core.tool_registry import load_registry
        registry = load_registry(project_root)
        names = list(registry.names())
    except Exception:
        return inferred

    if not names:
        return inferred

    # Sort longest-first to bias toward more specific matches
    names_sorted = sorted(names, key=lambda n: -len(n))
    patterns = [
        (n, re.compile(rf"(?<![\w-]){re.escape(n)}(?![\w-])", re.IGNORECASE))
        for n in names_sorted
    ]

    steps = envelope.get("steps") or []
    for step in steps:
        if not isinstance(step, dict):
            continue
        if "tool" in step and step["tool"]:
            continue  # operator (or LLM) already set it; preserve
        action_text = str(step.get("action", "") or "")
        if not action_text:
            continue
        for name, pat in patterns:
            if pat.search(action_text):
                step["tool"] = name
                inferred.append({
                    "step_id": str(step.get("id", "?")),
                    "tool_name": name,
                })
                break  # first-match-wins per step
    return inferred


def draft_plan_envelope(
    session_path: Path,
    backend: Optional[Backend] = None,
    audit_chain: Optional[AuditChain] = None,
) -> PlanDraft:
    """Top-level entrypoint: draft a plan_envelope for the given session.

    Audit events:
      - plan_helper.invoked (before LLM call)
      - plan_helper.proposed (on validated success)
      - plan_helper.failed (on ValidationError / backend error / IO error)
    """
    inputs = _read_session_inputs(session_path)
    slug = _session_slug_from_path(session_path)

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    context_schema = {
        "context_schema_version": "1.0",
        "ritual": "plan_helper",
        "placeholders": [
            {
                "identifier": "session.slug",
                "type": "plain_text",
                "required": True,
                "description": "Active session slug (data only).",
            },
            {
                "identifier": "session.context_md",
                "type": "markdown_escaped",
                "required": True,
                "description": "Active session THINK/00_CONTEXT.md body.",
            },
            {
                "identifier": "session.vvv_prompt_md",
                "type": "markdown_escaped",
                "required": True,
                "description": "Active session THINK/01_PROMPT.md (post-vvv).",
            },
        ],
    }
    ctx = {
        "session": {
            "slug": slug,
            "context_md": inputs["context_md"],
            "vvv_prompt_md": inputs["vvv_prompt_md"],
        },
    }
    prompt = substitute(template, ctx, context_schema)

    if audit_chain is not None:
        audit_chain.append("plan_helper.invoked", {
            "session_slug": slug,
            "context_chars": len(inputs["context_md"]),
            "prompt_chars": len(inputs["vvv_prompt_md"]),
        })

    backend = backend if backend is not None else select_backend()
    request = LLMRequest(prompt=prompt, timeout=180.0)

    try:
        response = call_llm(
            request,
            backend=backend,
            audit_chain=audit_chain,
            ritual_context={
                "ritual": "plan_helper",
                "session_slug": slug,
            },
        )
        envelope = _parse_llm_json(response.text)
        _validate_envelope(envelope)
    except Exception as e:
        if audit_chain is not None:
            audit_chain.append("plan_helper.failed", {
                "error_class": e.__class__.__name__,
                "error_message": str(e)[:500],
                "session_slug": slug,
            })
        raise

    # S16 — auto-infer step.tool from action text. This activates the
    # downstream dispatch + sandbox + policy infrastructure that was
    # otherwise dormant (no plan declared `tool:` field before).
    project_root = _resolve_project_root(session_path)
    inferred = _infer_step_tools(envelope, project_root)
    if audit_chain is not None and inferred:
        audit_chain.append("plan_helper.tool_inferred", {
            "session_slug": slug,
            "inferred": inferred[:50],   # cap for audit row size
            "inferred_count": len(inferred),
        })

    if audit_chain is not None:
        audit_chain.append("plan_helper.proposed", {
            "session_slug": slug,
            "tier": envelope["tier"],
            "step_count": len(envelope["steps"]),
            "acceptance_count": len(envelope["acceptance"]),
            "allowed_paths_count": len(envelope["allowed_paths"]),
            "tool_inferred_count": len(inferred),
        })

    return PlanDraft(envelope=envelope)


__all__ = [
    "draft_plan_envelope",
    "PlanDraft",
    "ValidationError",
    "_read_session_inputs",
    "_validate_envelope",
    "_parse_llm_json",
    "_session_slug_from_path",
    "_infer_step_tools",
    "_resolve_project_root",
]
