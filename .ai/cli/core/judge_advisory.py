"""S14 — judge-cli advisory enforcement helper.

Satisfies PRD Phase 8 acceptance lines 799+800:
  - "judge-cli declared as AI advisory verifier, not executor."
    (already encoded in .ai/tools.yaml#judge-cli.capabilities containing
    "advisory" and .ai/tools.capabilities.yaml notes; this module
    surfaces that declaration as a runtime predicate)
  - "AI verdict alone cannot promote/deploy."
    (this module supplies the predicate ddd uses to refuse prod
    promotion when the chain's only verdicts come from advisory
    sources)

Article anchors:
- Article IV — separation of roles; AI verifier is advisory, not
  authoritative
- Article XIII — human authority on promote/deploy
- Article XX — passive: pure functions, no I/O beyond explicit chain
  read

Advisory verdict sources (closed):
  - decided_by == "layer_3_llm_judge"   (Pyramid layer 3 — LLM judge)
  - decided_by == "advisory"            (explicit advisory marker)

Non-advisory (authoritative) sources include:
  - decided_by == "verifier"            (layer 1 deterministic)
  - decided_by == "policy"              (layer 2)
  - decided_by == "human"               (layer 4 — Article XIII)
  - decided_by == "kernel"              (kernel-level transitions)
"""
from __future__ import annotations

from typing import Set, TYPE_CHECKING

if TYPE_CHECKING:
    from cli.core.audit import AuditChain
    from cli.core.tool_registry import ToolCapabilityRecord


# Closed set of decided_by values that count as advisory-only.
# Any other decided_by counts as authoritative.
ADVISORY_DECIDED_BY: Set[str] = {
    "layer_3_llm_judge",
    "advisory",
}


# Audit event types that carry a verifier verdict (used to scope the
# chain scan in verdict_is_advisory_only).
VERDICT_EVENT_TYPES: Set[str] = {
    "verify.completed",
    "gogogo.step_passed",
    "gogogo.step_failed",
}


def is_tool_advisory(record: "ToolCapabilityRecord") -> bool:
    """True iff the tool's declared_capabilities contains 'advisory'.

    judge-cli is registered with capabilities=['judge', 'llm', 'advisory']
    in `.ai/tools.yaml`; ToolCapabilityRecord materialises that as the
    `declared_capabilities` tuple. The 'advisory' tag is the marker
    that tells the kernel this tool's verdict cannot promote/deploy
    on its own.
    """
    return "advisory" in record.declared_capabilities


def verdict_is_advisory_only(chain: "AuditChain", session_id: str) -> bool:
    """True iff the session's audit chain has verdicts AND every verdict
    is from an advisory source.

    Returns:
      - True  when at least one verdict event exists for `session_id`
              AND every such event's `details.decided_by` is in
              ADVISORY_DECIDED_BY
      - False when no verdict events exist for `session_id` (caller
              should not block — there's nothing to evaluate)
      - False when any verdict event has a non-advisory decided_by

    The caller (ddd) uses True to refuse prod promotion.
    """
    saw_verdict = False
    for event in chain.iter_events():
        if event.get("type") not in VERDICT_EVENT_TYPES:
            continue
        details = event.get("details") or {}
        if details.get("session_id") != session_id:
            continue
        saw_verdict = True
        decided_by = details.get("decided_by", "")
        if decided_by not in ADVISORY_DECIDED_BY:
            return False
    return saw_verdict


__all__ = [
    "ADVISORY_DECIDED_BY",
    "VERDICT_EVENT_TYPES",
    "is_tool_advisory",
    "verdict_is_advisory_only",
]
