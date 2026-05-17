"""Trinity policy validator stub (Phase 5, Step S5).

Read-only validator for the proposed `.ai/policies/trinity_policy.yaml`
consolidation file. This module:

  - parses trinity_policy.yaml
  - checks required top-level keys exist
  - returns a structured report (no side effects)

It MUST NOT mutate any state, write any file, or invoke any external
process. The acceptance test for this stub greps for write/exec
surfaces and fails if any are present.

Status: stub (S5 proposal). Runtime enforcement is deferred.
"""

from pathlib import Path
import yaml

REQUIRED_KEYS = (
    "version",
    "status",
    "authoritative",
    "references_authoritative_sources",
    "verifier_rule_tiers",
    "sandbox",
    "ddd",
    "close",
    "tools_capability",
    "audit_events",
)


def parse(path):
    """Read and YAML-parse the policy file. Read-only."""
    with open(Path(path)) as f:
        return yaml.safe_load(f)


def validate(path):
    """Return a structured validity report for a trinity_policy.yaml file.

    Report shape:
        {
            "ok": bool,
            "errors": list[str],
            "path": str,
            "version": str | None,
            "status": str | None,
            "authoritative": bool | None,
        }
    """
    errors = []
    data = None
    try:
        data = parse(path)
    except FileNotFoundError:
        return {
            "ok": False,
            "errors": [f"file not found: {path}"],
            "path": str(path),
            "version": None,
            "status": None,
            "authoritative": None,
        }
    except yaml.YAMLError as e:
        return {
            "ok": False,
            "errors": [f"yaml parse error: {e}"],
            "path": str(path),
            "version": None,
            "status": None,
            "authoritative": None,
        }

    if not isinstance(data, dict):
        errors.append("top-level YAML must be a mapping")
        data = {}

    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"missing required key: {key}")

    # Tier values are constrained to HOT/WARM/COLD.
    tiers = data.get("verifier_rule_tiers")
    if isinstance(tiers, dict):
        for rule_id, tier in tiers.items():
            if tier not in ("HOT", "WARM", "COLD"):
                errors.append(
                    f"verifier_rule_tiers.{rule_id}: invalid tier {tier!r}"
                )

    return {
        "ok": not errors,
        "errors": errors,
        "path": str(path),
        "version": data.get("version") if isinstance(data, dict) else None,
        "status": data.get("status") if isinstance(data, dict) else None,
        "authoritative": data.get("authoritative")
        if isinstance(data, dict)
        else None,
    }
