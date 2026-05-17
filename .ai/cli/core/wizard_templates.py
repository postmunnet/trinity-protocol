"""Built-in templates for `ai wizard new <slug> --type=<type>`.

Each template is a multi-line markdown skeleton for THINK/01_PROMPT.md
with the 5 vvv questions and type-specific Answer hint paragraphs.
Placeholders `{{slug}}`, `{{date}}`, `{{type}}` are substituted via
`render()`.

The hints are NOT real answers — they're guideposts that the operator
edits before submitting `ai vvv --answers-file=<path>`. Wizard's job
is to reduce blank-page friction, not to pretend it knows the work.
"""
from __future__ import annotations

from typing import Set

VALID_TYPES: Set[str] = {"feat", "fix", "ops", "docs", "refactor"}


_FRONTMATTER = """---
session: {{slug}}
ritual: vvv
status: draft
type: {{type}}
last-updated: {{date}}
---

"""


_QUESTIONS_PREFIX = """# `vvv` — 5 Questions

> Skeleton scaffolded by `ai wizard new {{slug}} --type={{type}}` on {{date}}.
> Replace each **Answer** placeholder with the real answer, then run:
>
>     ai vvv --answers-file=THINK/01_PROMPT.md
"""


def _section(qnum: int, title: str, question: str, hint: str) -> str:
    return (
        f"\n\n## Q{qnum} — {title}\n\n"
        f"**Question:** {question}\n\n"
        f"**Answer:** {hint}\n"
    )


# Type-specific hint paragraphs (Q1 Goal — most variation).
_HINTS_GOAL = {
    "feat": (
        "Ship a new capability X that solves Y for the operator. "
        "Replace with: one-sentence description of what success looks like."
    ),
    "fix": (
        "Restore behavior Z to its pre-regression baseline. Replace with: "
        "specific bug + observable symptom + expected baseline."
    ),
    "ops": (
        "Execute operational task X (deploy, migration, audit, cleanup). "
        "Replace with: action + target system + success criteria."
    ),
    "docs": (
        "Document Y so a future operator can pick up the work without you. "
        "Replace with: doc target + audience + key insight to land."
    ),
    "refactor": (
        "Extract / rename / move Z without changing observable behavior. "
        "Replace with: refactor target + invariant to preserve."
    ),
}

# Q2-Q5 hints reused across all types (less variation).
_HINTS_SCOPE = (
    "IN: list of paths/files/components in scope. "
    "OUT: explicit non-goals to prevent scope creep."
)
_HINTS_CONSTRAINT = (
    "What cannot be touched? (forbidden_paths, no new deps, baseline test "
    "count, locked APIs, schema invariants, operator-only files)."
)
_HINTS_ACCEPTANCE = (
    "Measurable signals: list of N gates (A_FOO, A_BAR) — each with a "
    "concrete check (file exists / test passes / behavior observed)."
)
_HINTS_RISK = (
    "Most likely failure mode + mitigation. Be specific — what could go "
    "wrong, and what's the safety net (back-compat path, test fixture, "
    "manual verify smoke)?"
)


def render(template_key: str, slug: str, date: str) -> str:
    """Build a 01_PROMPT.md skeleton for `template_key` (one of VALID_TYPES).

    Substitutes {{slug}}, {{date}}, {{type}} placeholders.
    Raises ValueError if `template_key` is not in VALID_TYPES.
    """
    if template_key not in VALID_TYPES:
        raise ValueError(
            f"unknown template type: {template_key!r}. "
            f"Valid types: {sorted(VALID_TYPES)}"
        )
    body = _FRONTMATTER + _QUESTIONS_PREFIX
    body += _section(
        1, "Goal",
        "What does success look like? (one sentence)",
        _HINTS_GOAL[template_key],
    )
    body += _section(2, "Scope", "What is explicitly in scope? What is out?", _HINTS_SCOPE)
    body += _section(3, "Constraint", "What cannot be touched? (policies, boundary docs)", _HINTS_CONSTRAINT)
    body += _section(4, "Acceptance", "What measurable signal proves 'done'?", _HINTS_ACCEPTANCE)
    body += _section(5, "Risk", "What is the most likely failure mode?", _HINTS_RISK)

    return (
        body.replace("{{slug}}", slug)
            .replace("{{date}}", date)
            .replace("{{type}}", template_key)
    )


__all__ = ["VALID_TYPES", "render"]
