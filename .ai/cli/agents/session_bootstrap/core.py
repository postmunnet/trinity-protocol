"""Session Bootstrap Agent — core logic.

In-house Trinity agent (RC Article XVIII Session-Initializer-support role).
Proposes {slug, tier, tier_reasoning, context_draft, related_sessions[]} for
the operator to review BEFORE running `ai session new <slug>`.

Authority hierarchy:
  - Constitution v1.0 Article III: AI proposes; operator decides.
  - Constitution v1.0 Article IX: related-sessions lookup is exact-evidence
    retrieval (slug-regex match against archive listing) — no semantic
    interpretation, no embedding, no meaning derivation.
  - Constitution v1.0 Article XVI: capability surface declared in README
    (Article XXVIII 8-field). This module READS archive listings, CALLS
    cli.core.llm_call, APPENDS audit events. Nothing else.
  - Constitution v1.0 Article XVII: credential redaction is inherited from
    cli.core.llm_call (the foundation). This module never logs raw prompts.
  - RC Article XVI: operator's task description is `markdown_escaped`, never
    instruction.
"""
from __future__ import annotations

import json
import os
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


# Path of this file: .ai/cli/agents/session_bootstrap/core.py
_HERE = Path(__file__).resolve().parent
_PROMPT_PATH = _HERE / "prompts" / "draft.md"

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_VALID_TIERS = frozenset({"HOT", "WARM", "COLD"})
_REQUIRED_KEYS = (
    "slug",
    "tier",
    "tier_reasoning",
    "context_draft",
    "related_sessions_brief",
)
_MAX_RELATED = 10
_ARCHIVE_DIRNAME = "archive"


class ValidationError(Exception):
    """The LLM-returned proposal failed shape or content validation."""


@dataclass
class Proposal:
    slug: str
    tier: str
    tier_reasoning: str
    context_draft: str
    related_sessions: List[Dict[str, str]]
    raw_brief: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "tier": self.tier,
            "tier_reasoning": self.tier_reasoning,
            "context_draft": self.context_draft,
            "related_sessions": self.related_sessions,
            "related_sessions_brief": self.raw_brief,
        }


def _list_recent_archive(
    repo_root: Path,
    limit: int = 20,
) -> List[Dict[str, str]]:
    """Return up to `limit` recent archive entries as [{slug, archive_path}].

    Reads only directory NAMES; never opens any session body. mtime-sorted
    descending. Empty list if archive dir is absent.
    """
    archive_dir = repo_root / ".ai" / "sessions" / _ARCHIVE_DIRNAME
    if not archive_dir.is_dir():
        return []
    entries: List[Dict[str, Any]] = []
    for child in archive_dir.iterdir():
        # Archive entries look like "0001_<date>_<slug>.archive".
        if not child.name.endswith(".archive"):
            continue
        # Extract the trailing slug after the second underscore-separated date.
        base = child.name[: -len(".archive")]
        # Form: "0001_2026-05-13_03_36_am_feat-foo"; slug = part after the time.
        # Conservative split: take everything after the first "_<digits>-..._<am|pm>_" pattern.
        m = re.match(
            r"^\d+_\d{4}-\d{2}-\d{2}_\d{1,2}_\d{2}_(?:am|pm)_(.+)$",
            base,
        )
        slug = m.group(1) if m else base
        try:
            mtime = child.stat().st_mtime
        except OSError:
            mtime = 0
        entries.append({
            "slug": slug,
            "archive_path": str(child),
            "mtime": mtime,
        })
    entries.sort(key=lambda e: e["mtime"], reverse=True)
    out: List[Dict[str, str]] = []
    for e in entries[:limit]:
        out.append({"slug": e["slug"], "archive_path": e["archive_path"]})
    return out


def _slug_collision_check(
    proposed: str,
    existing_slugs: List[str],
) -> str:
    """Return `proposed` if unique, else append -2 / -3 / ... until unique.

    Comparison is case-insensitive. existing_slugs are basename slugs already
    stripped of the date/time prefix.
    """
    existing_lower = {s.lower() for s in existing_slugs}
    if proposed.lower() not in existing_lower:
        return proposed
    for n in range(2, 100):
        candidate = f"{proposed}-{n}"
        if candidate.lower() not in existing_lower:
            return candidate
    # Should be unreachable in practice.
    raise ValidationError(
        f"unable to resolve slug collision for {proposed!r} after 100 attempts"
    )


def _validate_proposal(d: Dict[str, Any]) -> None:
    """Raise ValidationError if the proposal dict is malformed."""
    if not isinstance(d, dict):
        raise ValidationError(
            f"expected dict, got {type(d).__name__}"
        )
    missing = [k for k in _REQUIRED_KEYS if k not in d]
    if missing:
        raise ValidationError(f"missing required keys: {missing}")
    if not isinstance(d["slug"], str) or not _SLUG_RE.fullmatch(d["slug"]):
        raise ValidationError(
            f"slug must match {_SLUG_RE.pattern}; got {d['slug']!r}"
        )
    if len(d["slug"]) > 64:
        raise ValidationError(
            f"slug exceeds 64 chars: {len(d['slug'])}"
        )
    if d["tier"] not in _VALID_TIERS:
        raise ValidationError(
            f"tier must be one of {sorted(_VALID_TIERS)}; got {d['tier']!r}"
        )
    for key in ("tier_reasoning", "context_draft", "related_sessions_brief"):
        if not isinstance(d[key], str) or not d[key].strip():
            raise ValidationError(
                f"{key} must be a non-empty string"
            )


def _parse_llm_json(text: str) -> Dict[str, Any]:
    """Strict JSON parse of LLM response. Strips surrounding whitespace; if
    the response is wrapped in a code fence (```json ... ```), peels that off.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        # Allow ```json\n{...}\n``` or ```\n{...}\n```
        first_newline = stripped.find("\n")
        if first_newline == -1:
            raise ValidationError("LLM response had ``` but no newline")
        body = stripped[first_newline + 1 :]
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


def propose_session(
    description: str,
    repo_root: Path,
    backend: Optional[Backend] = None,
    audit_chain: Optional[AuditChain] = None,
) -> Proposal:
    """Top-level entrypoint: turn an operator description into a Proposal.

    Audit emissions when audit_chain is provided:
      - session_bootstrap.invoked (always, before LLM call)
      - session_bootstrap.proposed (on validated success)
      - session_bootstrap.failed (on ValidationError or backend error)
    """
    if not isinstance(description, str) or not description.strip():
        raise ValidationError("description must be a non-empty string")

    archive_entries = _list_recent_archive(repo_root, limit=_MAX_RELATED)
    archive_slugs = [e["slug"] for e in archive_entries]
    recent_slugs_text = "\n".join(f"- {s}" for s in archive_slugs) or "(none)"

    # Load prompt template and context schema.
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    context_schema = {
        "context_schema_version": "1.0",
        "ritual": "session_bootstrap",
        "placeholders": [
            {
                "identifier": "operator.task_description",
                "type": "markdown_escaped",
                "required": True,
                "description": "Operator's free-form task description.",
            },
            {
                "identifier": "archive.recent_slugs",
                "type": "markdown_escaped",
                "required": True,
                "description": "Bulleted list of recent archive slugs.",
            },
        ],
    }
    ctx = {
        "operator": {"task_description": description},
        "archive": {"recent_slugs": recent_slugs_text},
    }
    prompt = substitute(template, ctx, context_schema)

    if audit_chain is not None:
        audit_chain.append("session_bootstrap.invoked", {
            "description_chars": len(description),
            "archive_count": len(archive_entries),
        })

    backend = backend if backend is not None else select_backend()
    request = LLMRequest(prompt=prompt, timeout=120.0)

    try:
        response = call_llm(
            request,
            backend=backend,
            audit_chain=audit_chain,
            ritual_context={"ritual": "session_bootstrap"},
        )
        proposal_dict = _parse_llm_json(response.text)
        _validate_proposal(proposal_dict)
    except Exception as e:
        if audit_chain is not None:
            audit_chain.append("session_bootstrap.failed", {
                "error_class": e.__class__.__name__,
                "error_message": str(e)[:500],
            })
        raise

    # Apply collision check (operator may have asked for a slug that exists).
    resolved_slug = _slug_collision_check(
        proposal_dict["slug"], archive_slugs
    )

    if audit_chain is not None:
        audit_chain.append("session_bootstrap.proposed", {
            "slug": resolved_slug,
            "slug_was_collision_adjusted": resolved_slug != proposal_dict["slug"],
            "tier": proposal_dict["tier"],
            "context_chars": len(proposal_dict["context_draft"]),
            "related_count": len(archive_entries),
        })

    return Proposal(
        slug=resolved_slug,
        tier=proposal_dict["tier"],
        tier_reasoning=proposal_dict["tier_reasoning"],
        context_draft=proposal_dict["context_draft"],
        related_sessions=archive_entries,
        raw_brief=proposal_dict["related_sessions_brief"],
    )


__all__ = [
    "propose_session",
    "Proposal",
    "ValidationError",
    "_list_recent_archive",
    "_slug_collision_check",
    "_validate_proposal",
    "_parse_llm_json",
]
