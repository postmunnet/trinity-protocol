"""Retro Writer — sixth and FINAL in-house Trinity agent.

Composes the SEMANTIC retro layer (Lessons Learned / Patterns Observed /
Doctrine Claims / Anti-Patterns) distinct from rrr's MECHANICAL T1 retro
(RETRO.md). Output is markdown body to stdout; operator saves as
RETRO_LESSONS.md (sibling file). Agent NEVER modifies RETRO.md.

Authority:
  - RRR Delegation Contract T1 split: mechanical (rrr) vs semantic (this).
  - Constitution v1.0 Articles III, IV, IX, XVI, XVII, XX.
  - RC v1.1-rc Article XVIII (Retro Writer row).

Completes the in-house agent chain for all 6 ritual seats:
  sss → session_bootstrap
  vvv → clarification_helper
  nnn → plan_helper
  gogogo → executor_helper
  ddd → presentation_synthesizer
  rrr → retro_writer (this) ← FINAL
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

REQUIRED_HEADINGS_ORDER = (
    "## Lessons Learned",
    "## Patterns Observed",
    "## Doctrine Claims",
    "## Anti-Patterns",
)
_MIN_WORDS = 200


class ValidationError(Exception):
    pass


@dataclass
class RetroLessons:
    body: str

    def to_str(self) -> str:
        return self.body


def _session_slug_from_path(session_path: Path) -> str:
    name = session_path.name
    m = re.match(
        r"^\d+_\d{4}-\d{2}-\d{2}_\d{1,2}_\d{2}_(?:am|pm)_(.+)$",
        name,
    )
    return m.group(1) if m else name


def _read_session_inputs(session_path: Path) -> Dict[str, Any]:
    if not session_path.is_dir():
        raise FileNotFoundError(f"session path not found: {session_path}")
    retro_path = session_path / "THINK" / "RETRO.md"
    envelope_path = session_path / "THINK" / "plan_envelope.json"
    if not retro_path.is_file():
        raise FileNotFoundError(
            f"RETRO.md not found: {retro_path} — run `ai rrr` first"
        )
    if not envelope_path.is_file():
        raise FileNotFoundError(f"plan_envelope not found: {envelope_path}")
    retro_md = retro_path.read_text(encoding="utf-8")
    if not retro_md.strip():
        raise FileNotFoundError(f"RETRO.md is empty: {retro_path}")
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    return {"retro_md": retro_md, "plan_envelope": envelope}


def _summarize_session_audit(repo_root: Path, slug_substring: str) -> Dict[str, Any]:
    """Reuse pattern from presentation_synthesizer."""
    events_path = repo_root / ".ai" / "audit" / "events.ndjson"
    out = {
        "event_count": 0,
        "final_graph_state": "unknown",
        "gogogo_verdicts": {"PASS": 0, "FAIL": 0},
        "needs_human_count": 0,
    }
    if not events_path.is_file():
        return out
    for line in events_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        details_str = json.dumps(ev.get("details", {}))
        if slug_substring not in details_str:
            continue
        out["event_count"] += 1
        if ev.get("type") == "graph.transition":
            to_state = ev.get("details", {}).get("to")
            if to_state:
                out["final_graph_state"] = to_state
        if ev.get("type") == "gogogo.step_passed":
            out["gogogo_verdicts"]["PASS"] += 1
        if ev.get("type") == "gogogo.step_failed":
            out["gogogo_verdicts"]["FAIL"] += 1
        if "NEEDS_HUMAN" in details_str:
            out["needs_human_count"] += 1
    return out


def _validate_lessons(body: str) -> None:
    """Enforce: 4 required H2 headings in exact order; ≥200 words total;
    no H1 at top; starts with the first required heading.
    """
    if not isinstance(body, str) or not body.strip():
        raise ValidationError("lessons body must be a non-empty string")
    stripped = body.strip()
    # No H1 at top.
    if stripped.startswith("# "):
        raise ValidationError("body must NOT start with an H1 heading")
    # Must start with the first required heading (allow optional leading
    # whitespace already handled by strip).
    if not stripped.startswith(REQUIRED_HEADINGS_ORDER[0]):
        raise ValidationError(
            f"body must start with {REQUIRED_HEADINGS_ORDER[0]!r}; "
            f"got: {stripped[:60]!r}"
        )
    # Find each required heading at start of a line; ensure they appear in order.
    last_pos = -1
    for heading in REQUIRED_HEADINGS_ORDER:
        # heading must appear at start of a line — use regex with multiline.
        pattern = re.compile(r"(?m)^" + re.escape(heading) + r"\s*$")
        m = pattern.search(body)
        if m is None:
            raise ValidationError(f"missing required heading: {heading!r}")
        if m.start() <= last_pos:
            raise ValidationError(
                f"heading {heading!r} appears before previous required heading "
                f"(must be in declared order)"
            )
        last_pos = m.start()
    # Word count.
    word_count = len(body.split())
    if word_count < _MIN_WORDS:
        raise ValidationError(
            f"body too short: {word_count} words (minimum {_MIN_WORDS})"
        )


def compose_retro_lessons(
    session_path: Path,
    repo_root: Path,
    backend: Optional[Backend] = None,
    audit_chain: Optional[AuditChain] = None,
) -> RetroLessons:
    """Top-level entry. Audit events: retro_writer.invoked/.proposed/.failed."""
    inputs = _read_session_inputs(session_path)
    slug = _session_slug_from_path(session_path)
    audit_summary = _summarize_session_audit(repo_root, slug)

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    context_schema = {
        "context_schema_version": "1.0",
        "ritual": "retro_writer",
        "placeholders": [
            {"identifier": "session.slug", "type": "plain_text", "required": True, "description": "slug"},
            {"identifier": "session.retro_md", "type": "markdown_escaped", "required": True, "description": "mechanical retro"},
            {"identifier": "session.plan_envelope", "type": "json_string", "required": True, "description": "envelope"},
            {"identifier": "session.audit_summary", "type": "markdown_escaped", "required": True, "description": "audit summary"},
        ],
    }
    ctx = {
        "session": {
            "slug": slug,
            "retro_md": inputs["retro_md"],
            "plan_envelope": inputs["plan_envelope"],
            "audit_summary": json.dumps(audit_summary, indent=2),
        },
    }
    prompt = substitute(template, ctx, context_schema)

    if audit_chain is not None:
        audit_chain.append("retro_writer.invoked", {
            "session_slug": slug,
            "retro_chars": len(inputs["retro_md"]),
        })

    backend = backend if backend is not None else select_backend()
    request = LLMRequest(prompt=prompt, timeout=180.0)

    try:
        response = call_llm(
            request, backend=backend, audit_chain=audit_chain,
            ritual_context={"ritual": "retro_writer", "session_slug": slug},
        )
        body = response.text.strip()
        _validate_lessons(body)
    except Exception as e:
        if audit_chain is not None:
            audit_chain.append("retro_writer.failed", {
                "error_class": e.__class__.__name__,
                "error_message": str(e)[:500],
                "session_slug": slug,
            })
        raise

    if audit_chain is not None:
        audit_chain.append("retro_writer.proposed", {
            "session_slug": slug,
            "body_word_count": len(body.split()),
        })

    return RetroLessons(body=body)


__all__ = [
    "compose_retro_lessons",
    "RetroLessons",
    "ValidationError",
    "REQUIRED_HEADINGS_ORDER",
    "_read_session_inputs",
    "_summarize_session_audit",
    "_validate_lessons",
    "_session_slug_from_path",
]
