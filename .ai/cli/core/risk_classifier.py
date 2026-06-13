"""Deterministic per-step risk classifier for gogogo (Q24.10 step 4).

Local-minimal classifier — NOT a policy framework (that is out of scope).
Risk is resolved deterministically; an LLM never judges risk here.

Priority (operator-locked 2026-06-13):
  1. explicit  — step.risk supplied by nnn in {low,medium,high}
  2. deterministic hotlist — path / command markers that touch the kernel,
     verifier surfaces, runtime/deploy, or destructive commands
  3. legacy unknown — no explicit risk and no hotlist hit → risk_level
     "unknown" / risk_source "legacy_missing_risk" (NOT silently "low";
     keeps step-5 KPI honest)
"""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple

_VALID_EXPLICIT = {"low", "medium", "high"}

# Path-like markers — matched as substrings (they contain '/' or '-' so they
# do not false-positive on ordinary prose).
_HOTLIST_PATH = (
    "core/trinity_v2",
    ".ai/cli",
    ".ai/policies",
    ".ai/schemas",
    ".ai/audit",
    "trinity-link",
    "trinity-patch",
)
# Bare-word markers — matched at WORD BOUNDARIES only, so "paragraph" does
# not trip "graph", "product" does not trip "prod", etc.
_HOTLIST_WORDS = (
    "verifier", "graph", "rrr", "gogogo", "vvv", "nnn", "runtime",
    "deploy", "prod", "migrate", "delete", "drop", "truncate",
)
_WORD_RE = re.compile(r"\b(" + "|".join(_HOTLIST_WORDS) + r")\b")
# Destructive command fragments — matched as substrings (space/dash anchored).
_HOTLIST_CMD = (
    "rm ",
    "rm -",
    "rsync --delete",
)


def _step_text(step: Dict[str, Any]) -> str:
    parts = [
        str(step.get("title", "")),
        str(step.get("command", "")),
    ]
    verify = step.get("verify")
    if isinstance(verify, dict):
        parts.append(str(verify.get("command", "")))
    # explicit path hints if the plan supplies them
    for key in ("path", "paths", "files", "spec_ref"):
        v = step.get(key)
        if v:
            parts.append(str(v))
    return " ".join(parts).lower()


def classify_risk(step: Dict[str, Any]) -> Tuple[str, str]:
    """Return (risk_level, risk_source) — deterministic, no inference.

    risk_level ∈ {low, medium, high, unknown}.
    risk_source ∈ {explicit, deterministic_hotlist, legacy_missing_risk}.
    """
    explicit = str(step.get("risk", "")).strip().lower()
    if explicit in _VALID_EXPLICIT:
        return explicit, "explicit"

    text = _step_text(step)
    if (
        any(m in text for m in _HOTLIST_PATH)
        or any(m in text for m in _HOTLIST_CMD)
        or _WORD_RE.search(text)
    ):
        return "high", "deterministic_hotlist"

    return "unknown", "legacy_missing_risk"


def evaluate_evidence_gate(step: Dict[str, Any]) -> Dict[str, Any]:
    """Decide gogogo's per-step evidence action (opt-A, risk-graduated).

    Pure decision (no subprocess) so it is unit-testable; gogogo runs the
    evidence command / appends audit based on `action`.

      action=evidence_run        step has verify.command → run it (existing
                                 evidence path: pass→PASS, fail→DEAD; never
                                 NEEDS_HUMAN on a clear evidence failure)
      action=needs_human         high-risk + no verify.command → stop; route
                                 back to `nnn --amend` (add verify) or human
      action=pass_with_warning   medium-risk + no verify.command → PASS, warn
      action=pass                low/unknown + no verify.command → PASS

    Always returns the machine-readable marking fields step-5 KPI needs:
    risk_level, risk_source, evidence_mode, structural_pass,
    evidence_command_present.
    """
    risk_level, risk_source = classify_risk(step)
    verify = step.get("verify") if isinstance(step.get("verify"), dict) else None
    has_verify = bool(verify and verify.get("command"))

    if has_verify:
        action = "evidence_run"
    elif risk_level == "high":
        action = "needs_human"
    elif risk_level == "medium":
        action = "pass_with_warning"
    else:  # low / unknown
        action = "pass"

    return {
        "risk_level": risk_level,
        "risk_source": risk_source,
        "evidence_mode": "evidence_command" if has_verify else "structural",
        "structural_pass": not has_verify,
        "evidence_command_present": has_verify,
        "action": action,
    }
