"""`ai lll` — richer memory hint via Q1 Goal extraction (R30 followup).

Verifies _extract_prompt_query() in commands/lll.py — tolerant parsing
of THINK/01_PROMPT.md to enrich memory-cli search beyond slug.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.commands.lll import _extract_prompt_query


def _write_prompt(tmp_path: Path, body: str) -> Path:
    """Build a fake session path with THINK/01_PROMPT.md and return it."""
    sess = tmp_path / "sess"
    (sess / "THINK").mkdir(parents=True)
    (sess / "THINK" / "01_PROMPT.md").write_text(body, encoding="utf-8")
    return sess


def test_prompt_present_extracts_goal_answer(tmp_path):
    """A_PROMPT_PRESENT_USES_GOAL — extracted query equals the answer paragraph."""
    body = """---
ritual: vvv
---

## Q1 — Goal

**Question:** What does success look like?

**Answer:** Wire HMAC verify into `ai ddd` end-to-end so promotions
land in the audit chain with verified signatures.

## Q2 — Scope

**Answer:** ...
"""
    sess = _write_prompt(tmp_path, body)
    out = _extract_prompt_query(sess)
    assert out is not None
    assert "Wire HMAC verify" in out
    assert "audit chain" in out


def test_prompt_missing_returns_none(tmp_path):
    """A_PROMPT_MISSING_FALLBACK_SLUG — no PROMPT.md → None (caller falls back to slug)."""
    sess = tmp_path / "sess"
    (sess / "THINK").mkdir(parents=True)
    out = _extract_prompt_query(sess)
    assert out is None


def test_long_answer_truncated_at_200(tmp_path):
    """A_QUERY_TRUNCATED_AT_200 — answer over 200 chars trimmed."""
    long_text = "x" * 500
    body = f"""## Q1 — Goal

**Answer:** {long_text}
"""
    sess = _write_prompt(tmp_path, body)
    out = _extract_prompt_query(sess)
    assert out is not None
    assert len(out) <= 200


def test_no_answer_marker_falls_back_to_first_paragraph(tmp_path):
    """A_TOLERANT_PARSE_NO_ANSWER_MARKER — first non-empty paragraph used."""
    body = """## Q1 — Goal

This is the goal text without an explicit Answer marker.

Second paragraph after blank line.
"""
    sess = _write_prompt(tmp_path, body)
    out = _extract_prompt_query(sess)
    assert out is not None
    assert "goal text without an explicit" in out
    # Second paragraph should NOT be included (we take only the first).
    assert "Second paragraph" not in out


def test_no_q1_header_returns_none(tmp_path):
    """A_TOLERANT_PARSE_NO_Q1_HEADER — PROMPT.md without Q1 → None."""
    body = """## Some Other Section

Random content.

## Q5 — Risk

**Answer:** something
"""
    sess = _write_prompt(tmp_path, body)
    out = _extract_prompt_query(sess)
    assert out is None
