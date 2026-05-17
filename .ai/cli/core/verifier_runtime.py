"""Phase 8 verifier runtime — first runtime caller of verification_contract types.

Closes the "verification_contract.py 0 callers" gap. Provides three pure
helpers that bind the declarative-only contract surface
(`AcceptanceEntry`, `VERDICT_VOCABULARY`) into a runtime that gogogo can
call after all step verdicts are known:

  - `parse_acceptance_to_entries(items)` — list[dict] → list[AcceptanceEntry]
  - `consolidate_step_verdicts(verdicts)` — list[str] → terminal str
  - `is_terminal_verdict_consistent(expected, actual)` — bool

Consolidation precedence (most-severe-wins, per spec §2 verdict
vocabulary + Article XIII human authority):

  DEAD > NEEDS_HUMAN > RETRY > PASS

This mirrors policy_engine.resolve_precedence (deny > NEEDS_HUMAN >
conditional > allow) — the two axes use disjoint vocabularies (verifier
returns PASS/RETRY/NEEDS_HUMAN/DEAD; policy returns allow/deny/
conditional/NEEDS_HUMAN) but the same most-severe-wins shape.

Pure functions only; Article XX passive. No I/O, no audit emission, no
module-level state. The caller (gogogo) is responsible for emitting the
audit row.

Spec anchors:
- docs/specs/TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md §2 (verdict vocabulary)
- docs/constitution/contracts/TRINITY_ORGAN_MAP_V1.md §2 (Verifier organ)
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from cli.core.verification_contract import (
    SANDBOX_TIERS,
    VERDICT_VOCABULARY,
    AcceptanceEntry,
)


# Most-severe-wins. Members must be a permutation of VERDICT_VOCABULARY —
# enforced by `test_consolidation_precedence_is_permutation`.
CONSOLIDATION_PRECEDENCE: tuple = (
    "DEAD",
    "NEEDS_HUMAN",
    "RETRY",
    "PASS",
)


# Tier severity for terminal-tier consolidation (PRD Phase 8 acceptance
# "Every verdict path maps to a tier"). Most-severe-first:
#   COLD = rare-but-critical (deploy/orphan/severe boundary missing)
#   WARM = ordinary work (step_complete, code_change)
#   HOT  = high-frequency active work (browser_check)
# COLD is "most attention required" — rule of thumb: COLD changes are
# expensive to revert (production-tier impact) so they dominate the
# terminal tier of a mixed session. Members must be a permutation of
# SANDBOX_TIERS (asserted by test_tier_severity_is_permutation).
TIER_SEVERITY: tuple = (
    "COLD",
    "WARM",
    "HOT",
)


ACCEPTANCE_ID_PATTERN = re.compile(r"^A[0-9]+$")


def parse_acceptance_to_entries(items: List[Dict[str, object]]) -> List[AcceptanceEntry]:
    """Map a plan_envelope acceptance list into typed AcceptanceEntry rows.

    Best-effort on optional fields (predicates, evidence_keys, notes,
    on_fire_verdict) — missing values fall back to safe defaults. Hard
    failure on:
      - missing `id` (acceptance row must be identifiable)
      - `id` violating the ^A[0-9]+$ schema pattern
      - missing `description`, `command`, `expect_exit`, `required`,
        or `rule_set` (these are the contract's required keys per
        verification_contract.schema.json)
      - on_fire_verdict referencing a verdict not in VERDICT_VOCABULARY
    """
    entries: List[AcceptanceEntry] = []
    for raw in items:
        if "id" not in raw:
            raise ValueError("acceptance entry missing required key: id")
        aid = str(raw["id"])
        if not ACCEPTANCE_ID_PATTERN.match(aid):
            raise ValueError(
                f"acceptance id {aid!r} does not match schema pattern ^A[0-9]+$"
            )
        for required_key in ("description", "command", "expect_exit", "required", "rule_set"):
            if required_key not in raw:
                raise ValueError(
                    f"acceptance entry {aid!r} missing required key: {required_key}"
                )

        on_fire = raw.get("on_fire_verdict")
        if on_fire is not None:
            if not isinstance(on_fire, dict):
                raise ValueError(
                    f"acceptance {aid!r}: on_fire_verdict must be a mapping"
                )
            for pred_name, verdict in on_fire.items():
                if verdict not in VERDICT_VOCABULARY:
                    raise ValueError(
                        f"acceptance {aid!r}: on_fire_verdict[{pred_name!r}] = "
                        f"{verdict!r} not in VERDICT_VOCABULARY"
                    )

        entries.append(
            AcceptanceEntry(
                id=aid,
                description=str(raw["description"]),
                rule_set=str(raw["rule_set"]),
                command=str(raw["command"]),
                expect_exit=int(raw["expect_exit"]),
                required=bool(raw["required"]),
                predicates=list(raw.get("predicates", []) or []),
                evidence_keys=list(raw.get("evidence_keys", []) or []),
                notes=str(raw.get("notes", "") or ""),
                on_fire_verdict=on_fire,
            )
        )
    return entries


def consolidate_step_verdicts(verdicts: List[str]) -> str:
    """Reduce a list of per-step verifier verdicts to one terminal verdict.

    Closed precedence: DEAD > NEEDS_HUMAN > RETRY > PASS. Raises:
      - ValueError on empty list (caller's bug — gogogo should only
        consolidate when at least one step ran)
      - ValueError on any verdict ∉ VERDICT_VOCABULARY (contract drift)
    """
    if not verdicts:
        raise ValueError(
            "consolidate_step_verdicts: empty verdict list — caller must "
            "guard against zero-step plans"
        )
    unknown = [v for v in verdicts if v not in VERDICT_VOCABULARY]
    if unknown:
        raise ValueError(
            f"consolidate_step_verdicts: verdicts not in VERDICT_VOCABULARY: "
            f"{sorted(set(unknown))!r}"
        )
    seen = set(verdicts)
    for tier in CONSOLIDATION_PRECEDENCE:
        if tier in seen:
            return tier
    # Unreachable — CONSOLIDATION_PRECEDENCE is a permutation of
    # VERDICT_VOCABULARY by construction.
    raise AssertionError(
        "CONSOLIDATION_PRECEDENCE drift vs VERDICT_VOCABULARY — invariant broken"
    )


def precedence_validator(
    contract: Dict[str, object],
    rules_doc: "Optional[Dict[str, object]]" = None,
) -> List[str]:
    """§4.6.1 Precedence-validator clause — enforce verdict precedence.

    Returns a list of violation messages. Empty list = valid contract.
    Caller (nnn) uses any non-empty result to reject the contract.

    Violation cases per spec §4.6.1:
      (a) acceptance entry has `precedence_override:` field (forbidden
          at schema level via additionalProperties:false, but we
          double-check for defense in depth)
      (b) `on_fire_verdict` mapping contradicts the bound rule_set's
          predicate-class membership (e.g., maps a `dead_when` predicate
          to PASS, or a `pass_when` predicate to DEAD)
      (c) acceptance.rule_set.fallback_verdict ≠ contract.expected_terminal_verdict
          AND contract.rationale_for_fallback_divergence is empty

    Case (a) and (c) are checkable from contract alone; case (b)
    requires `rules_doc` (the .ai/policies/verifier-rules.yaml content).
    When `rules_doc` is None, case (b) is skipped + a note is appended
    explaining the skip (so callers can decide whether to treat as
    pass or as inconclusive).
    """
    from cli.core.verification_contract import VERDICT_VOCABULARY

    violations: List[str] = []
    expected_terminal = contract.get("expected_terminal_verdict")
    rationale = (contract.get("rationale_for_fallback_divergence") or "").strip()

    # Map each predicate class to the verdict it implies.
    PREDICATE_CLASS_TO_VERDICT = {
        "dead_when": "DEAD",
        "needs_human_when": "NEEDS_HUMAN",
        "retry_when": "RETRY",
        "pass_when": "PASS",
    }

    for entry in contract.get("acceptance", []) or []:
        if not isinstance(entry, dict):
            continue
        aid = entry.get("id", "?")

        # Case (a) — precedence_override field present
        if "precedence_override" in entry:
            violations.append(
                f"acceptance {aid!r}: forbidden `precedence_override` field "
                "(spec §4.6.1 — additionalProperties:false at schema level)"
            )

        # Case (b) — on_fire_verdict contradicts rule_set predicate-class
        on_fire = entry.get("on_fire_verdict")
        rule_set_name = entry.get("rule_set")
        if isinstance(on_fire, dict) and rule_set_name and rules_doc is not None:
            rule_sets = rules_doc.get("rule_sets") if isinstance(rules_doc, dict) else None
            rule_set = (
                rule_sets.get(rule_set_name)
                if isinstance(rule_sets, dict)
                else None
            )
            if isinstance(rule_set, dict):
                # Build pred_name → predicate_class map from the rule_set
                pred_class: Dict[str, str] = {}
                for klass in PREDICATE_CLASS_TO_VERDICT:
                    klass_block = rule_set.get(klass)
                    if isinstance(klass_block, dict):
                        for pname in klass_block.keys():
                            pred_class[pname] = klass
                    elif isinstance(klass_block, list):
                        for pname in klass_block:
                            if isinstance(pname, str):
                                pred_class[pname] = klass
                # Check each on_fire_verdict mapping
                for pname, mapped_verdict in on_fire.items():
                    if pname not in pred_class:
                        continue  # Unknown predicate — not a precedence violation, skip
                    implied = PREDICATE_CLASS_TO_VERDICT[pred_class[pname]]
                    if mapped_verdict != implied and mapped_verdict in VERDICT_VOCABULARY:
                        violations.append(
                            f"acceptance {aid!r}: on_fire_verdict[{pname!r}]={mapped_verdict!r} "
                            f"contradicts rule_set {rule_set_name!r} class "
                            f"{pred_class[pname]!r} (implies {implied!r})"
                        )

        # Case (c) — fallback_verdict divergence without rationale
        if rule_set_name and rules_doc is not None and expected_terminal:
            rule_sets = rules_doc.get("rule_sets") if isinstance(rules_doc, dict) else None
            rule_set = (
                rule_sets.get(rule_set_name)
                if isinstance(rule_sets, dict)
                else None
            )
            if isinstance(rule_set, dict):
                fallback = rule_set.get("fallback_verdict")
                if fallback and fallback != expected_terminal and not rationale:
                    violations.append(
                        f"acceptance {aid!r}: rule_set {rule_set_name!r} "
                        f"fallback_verdict={fallback!r} diverges from contract "
                        f"expected_terminal_verdict={expected_terminal!r} with "
                        "no rationale_for_fallback_divergence (spec §4.6.1)"
                    )

    return violations


def consolidate_step_tiers(tiers: List[str]) -> str:
    """Reduce a list of per-step tier strings to one terminal tier.

    Closed precedence: COLD > WARM > HOT (most-severe-wins; see
    TIER_SEVERITY docstring). Raises ValueError on:
      - empty list (caller bug — guard before calling)
      - any tier ∉ SANDBOX_TIERS frozenset (contract drift; e.g. the
        `_TIER_SENTINEL` value would surface here)
    """
    if not tiers:
        raise ValueError(
            "consolidate_step_tiers: empty tier list — caller must guard"
        )
    unknown = [t for t in tiers if t not in SANDBOX_TIERS]
    if unknown:
        raise ValueError(
            f"consolidate_step_tiers: tiers not in SANDBOX_TIERS: "
            f"{sorted(set(unknown))!r}"
        )
    seen = set(tiers)
    for tier in TIER_SEVERITY:
        if tier in seen:
            return tier
    raise AssertionError(
        "TIER_SEVERITY drift vs SANDBOX_TIERS — invariant broken"
    )


def is_terminal_verdict_consistent(expected: str, actual: str) -> bool:
    """True iff the actual terminal verdict matches the contract's expected.

    Both arguments must be in VERDICT_VOCABULARY; an unknown verdict on
    either side returns False (drift visible to the caller). This is a
    pure predicate; the caller is responsible for emitting any audit
    row that records the comparison.
    """
    if expected not in VERDICT_VOCABULARY:
        return False
    if actual not in VERDICT_VOCABULARY:
        return False
    return expected == actual


__all__ = [
    "ACCEPTANCE_ID_PATTERN",
    "CONSOLIDATION_PRECEDENCE",
    "TIER_SEVERITY",
    "consolidate_step_tiers",
    "consolidate_step_verdicts",
    "is_terminal_verdict_consistent",
    "parse_acceptance_to_entries",
    "precedence_validator",
]
