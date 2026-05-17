"""Validate the ritual template pack layout under .ai/rituals/.

Authority: Trinity Ritual Constitution v1.1-rc Articles I, IV, V, VI, XVI.
Authored under session feat-ritual-template-packs-bootstrap, gogogo step S5.

These tests enforce that the 7 ritual packs (sss/vvv/nnn/gogogo/ddd/rrr/close)
each contain the 4 required files (ritual.contract.json, context.schema.json,
write.template.md, check.template.json) and that every JSON file validates
against the corresponding base schema in .ai/schemas/ritual_*.schema.json.

The kernel runtime does not yet load from .ai/rituals/ — these tests guard
the static template artifacts so the future loader can trust their shape.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

# conftest pins cwd to repo root.
REPO_ROOT = Path.cwd()
RITUALS_DIR = REPO_ROOT / ".ai" / "rituals"
SCHEMAS_DIR = REPO_ROOT / ".ai" / "schemas"

RITUALS = ("sss", "vvv", "nnn", "gogogo", "ddd", "rrr", "close")
PACK_FILES = (
    "ritual.contract.json",
    "context.schema.json",
    "write.template.md",
    "check.template.json",
)

CONTRACT_SCHEMA = SCHEMAS_DIR / "ritual_contract.schema.json"
CHECK_SCHEMA = SCHEMAS_DIR / "ritual_check_template.schema.json"
CONTEXT_SCHEMA = SCHEMAS_DIR / "ritual_context.schema.json"

PLACEHOLDER_RE = re.compile(r"\{\{([a-z_]+):([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)\}\}")
ANY_DOUBLE_BRACE_RE = re.compile(r"\{\{([^}]+)\}\}")


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def jsonschema_validator():
    """Return jsonschema.validate or skip if library not present."""
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema library not installed; structural-parse tests still cover the basics")
    return jsonschema.validate


def test_rituals_dir_exists_and_has_seven_subdirs():
    """A1 — .ai/rituals/ has exactly 7 ritual subdirectories."""
    assert RITUALS_DIR.is_dir(), f"{RITUALS_DIR} not found"
    subdirs = sorted(p.name for p in RITUALS_DIR.iterdir() if p.is_dir())
    assert subdirs == sorted(RITUALS), f"Expected 7 ritual dirs {sorted(RITUALS)}, got {subdirs}"


@pytest.mark.parametrize("ritual", RITUALS)
@pytest.mark.parametrize("filename", PACK_FILES)
def test_pack_file_present(ritual, filename):
    """A2 — every ritual dir has all 4 required pack files."""
    path = RITUALS_DIR / ritual / filename
    assert path.is_file(), f"Missing pack file: {path}"


@pytest.mark.parametrize("ritual", RITUALS)
def test_contract_json_parses(ritual):
    """A3 — ritual.contract.json parses as JSON."""
    _load_json(RITUALS_DIR / ritual / "ritual.contract.json")


@pytest.mark.parametrize("ritual", RITUALS)
def test_context_schema_parses(ritual):
    """A3 — context.schema.json parses as JSON."""
    _load_json(RITUALS_DIR / ritual / "context.schema.json")


@pytest.mark.parametrize("ritual", RITUALS)
def test_check_template_parses(ritual):
    """A3 — check.template.json parses as JSON."""
    _load_json(RITUALS_DIR / ritual / "check.template.json")


@pytest.mark.parametrize("ritual", RITUALS)
def test_contract_schema_validates(ritual, jsonschema_validator):
    """A4 — ritual.contract.json validates against ritual_contract.schema.json (RC Article V)."""
    contract = _load_json(RITUALS_DIR / ritual / "ritual.contract.json")
    schema = _load_json(CONTRACT_SCHEMA)
    jsonschema_validator(contract, schema)


@pytest.mark.parametrize("ritual", RITUALS)
def test_check_schema_validates(ritual, jsonschema_validator):
    """A5 — check.template.json validates against ritual_check_template.schema.json (RC Article VI)."""
    check = _load_json(RITUALS_DIR / ritual / "check.template.json")
    schema = _load_json(CHECK_SCHEMA)
    jsonschema_validator(check, schema)


@pytest.mark.parametrize("ritual", RITUALS)
def test_context_schema_validates(ritual, jsonschema_validator):
    """context.schema.json validates against ritual_context.schema.json (RC Article XVI)."""
    context = _load_json(RITUALS_DIR / ritual / "context.schema.json")
    schema = _load_json(CONTEXT_SCHEMA)
    jsonschema_validator(context, schema)


@pytest.mark.parametrize("ritual", RITUALS)
def test_ritual_field_matches_directory(ritual):
    """ritual.contract.json.ritual and context.schema.json.ritual match the directory name."""
    contract = _load_json(RITUALS_DIR / ritual / "ritual.contract.json")
    context = _load_json(RITUALS_DIR / ritual / "context.schema.json")
    assert contract["ritual"] == ritual, f"contract.ritual={contract['ritual']!r} != dir={ritual!r}"
    assert context["ritual"] == ritual, f"context.ritual={context['ritual']!r} != dir={ritual!r}"


@pytest.mark.parametrize("ritual", RITUALS)
def test_audit_events_include_invoked(ritual):
    """RC Article V — every ritual MUST declare <ritual>.invoked in audit_events."""
    contract = _load_json(RITUALS_DIR / ritual / "ritual.contract.json")
    events = contract.get("audit_events", [])
    invoked_events = [e for e in events if e.endswith(".invoked")]
    assert invoked_events, (
        f"ritual {ritual!r} declares no *.invoked audit event; "
        f"required by RC Article V (audit_events contains pattern)."
    )


@pytest.mark.parametrize("ritual", RITUALS)
def test_write_template_uses_typed_placeholders_only(ritual):
    """RC Article XVI — write.template.md uses ONLY {{type:identifier}} form, never raw {{user_input}}."""
    write_template = (RITUALS_DIR / ritual / "write.template.md").read_text(encoding="utf-8")
    # Any double-brace token must be a typed placeholder.
    for match in ANY_DOUBLE_BRACE_RE.finditer(write_template):
        token = match.group(0)
        body = match.group(1)
        # Skip blockquote-style annotations that are not actual placeholders
        # (none expected in current templates; keep strict).
        assert PLACEHOLDER_RE.fullmatch(token), (
            f"ritual {ritual!r} write.template.md contains non-typed placeholder {token!r}; "
            f"RC Article XVI requires {{{{type:identifier}}}} form."
        )
        # Defense-in-depth: literal {{user_input}} as instruction is forbidden.
        assert body != "user_input", (
            f"ritual {ritual!r} write.template.md contains raw {{{{user_input}}}}; "
            f"RC Article XVI explicitly forbids it."
        )


@pytest.mark.parametrize("ritual", RITUALS)
def test_write_template_placeholders_match_context_schema(ritual):
    """Every required placeholder declared in context.schema.json MUST be consumed in write.template.md;
    every placeholder consumed in write.template.md MUST be declared in context.schema.json."""
    context = _load_json(RITUALS_DIR / ritual / "context.schema.json")
    declared = {p["identifier"]: p for p in context.get("placeholders", [])}

    write_template = (RITUALS_DIR / ritual / "write.template.md").read_text(encoding="utf-8")
    consumed = {m.group(2) for m in PLACEHOLDER_RE.finditer(write_template)}

    # Required-true placeholders must all be consumed.
    required_unconsumed = [
        ident for ident, spec in declared.items()
        if spec.get("required") and ident not in consumed
    ]
    assert not required_unconsumed, (
        f"ritual {ritual!r}: required placeholders declared in context.schema.json "
        f"but not consumed by write.template.md: {required_unconsumed}"
    )

    # Consumed placeholders must all be declared.
    consumed_undeclared = sorted(consumed - declared.keys())
    assert not consumed_undeclared, (
        f"ritual {ritual!r}: write.template.md consumes placeholders not declared "
        f"in context.schema.json: {consumed_undeclared}"
    )


@pytest.mark.parametrize("ritual", RITUALS)
def test_check_template_forbids_user_input_canary(ritual):
    """RC Article XVI — check.template.json MUST treat raw {{user_input}} as a forbidden phrase."""
    check = _load_json(RITUALS_DIR / ritual / "check.template.json")
    forbidden = check.get("forbidden_phrases", [])
    assert "{{user_input}}" in forbidden, (
        f"ritual {ritual!r} check.template.json missing canary phrase '{{{{user_input}}}}' "
        f"in forbidden_phrases (template-injection canary)."
    )


def test_rrr_pack_enforces_t1_t2_t4():
    """RRR Delegation Contract — T1 (no semantic synthesis), T2 (memory-cli index not learn), T4 (delegated_call audit)."""
    contract = _load_json(RITUALS_DIR / "rrr" / "ritual.contract.json")
    check = _load_json(RITUALS_DIR / "rrr" / "check.template.json")

    # T4 — rrr.delegated_call must be in audit_events
    assert "rrr.delegated_call" in contract.get("audit_events", []), (
        "rrr pack missing 'rrr.delegated_call' audit event (RRR Delegation Contract T4)."
    )

    # T2 — memory-cli learn must be forbidden
    assert "memory-cli learn" in check.get("forbidden_phrases", []), (
        "rrr pack missing 'memory-cli learn' in forbidden_phrases (RRR Delegation Contract T2)."
    )

    # T1 — predicate enforcing memory_handling.mode == index (Article VI canonical example)
    predicates = check.get("required_structural_predicates", [])
    predicate_texts = [p.get("predicate", "") for p in predicates]
    assert any("memory_handling.mode == index" in p for p in predicate_texts), (
        "rrr pack missing structural predicate 'memory_handling.mode == index' "
        "(RC Article VI canonical example + T1 enforcement)."
    )


def test_ddd_pack_enforces_human_authority():
    """Constitution Article XIII + Article XV — ddd decided_by must be human; transport cannot approve."""
    check = _load_json(RITUALS_DIR / "ddd" / "check.template.json")
    predicates = [p.get("predicate", "") for p in check.get("required_structural_predicates", [])]
    forbidden_roles = check.get("forbidden_roles", [])

    assert any("decided_by" in p and "human" in p for p in predicates), (
        "ddd pack missing predicate enforcing decided_by==human (Constitution Article XIII)."
    )
    assert "Transport" in forbidden_roles, (
        "ddd pack must list 'Transport' in forbidden_roles (Constitution Article XV — "
        "transport cannot approve gates)."
    )


def test_gogogo_pack_forbids_self_certification():
    """Constitution Article III — AI cannot self-certify; gogogo step.owner_role must differ from verdict decider."""
    check = _load_json(RITUALS_DIR / "gogogo" / "check.template.json")
    predicates = [p.get("predicate", "") for p in check.get("required_structural_predicates", [])]
    assert any(
        ("owner_role" in p and "decided_by" in p and "!=" in p) for p in predicates
    ), (
        "gogogo pack missing predicate enforcing step.owner_role != decided_by "
        "(Constitution Article III — no self-certification)."
    )


def test_nnn_pack_enforces_rollback():
    """Constitution Article XXII — plan MUST declare rollback."""
    check = _load_json(RITUALS_DIR / "nnn" / "check.template.json")
    predicates = [p.get("predicate", "") for p in check.get("required_structural_predicates", [])]
    assert any("rollback" in p.lower() for p in predicates), (
        "nnn pack missing predicate enforcing rollback declaration (Constitution Article XXII)."
    )


def test_close_pack_enforces_audit_append_only():
    """Constitution Article X — audit chain is append-only; close MUST NOT rewrite in place."""
    check = _load_json(RITUALS_DIR / "close" / "check.template.json")
    forbidden_actions = check.get("forbidden_actions", [])
    predicates = [p.get("predicate", "") for p in check.get("required_structural_predicates", [])]
    enforced = (
        any("rewrite_audit" in a or "audit_chain" in a for a in forbidden_actions)
        or any("in_place_modification" in p or "append_only" in p for p in predicates)
    )
    assert enforced, (
        "close pack missing enforcement of audit append-only (Constitution Article X). "
        "Add to forbidden_actions or required_structural_predicates."
    )


def test_sss_pack_is_idempotent():
    """sss should be idempotent — retry_policy.max_retries should be 0 (collision aborts, not retries)."""
    contract = _load_json(RITUALS_DIR / "sss" / "ritual.contract.json")
    max_retries = contract.get("retry_policy", {}).get("max_retries")
    assert max_retries == 0, (
        f"sss retry_policy.max_retries={max_retries}; should be 0 (sss is idempotent — "
        f"collision should abort with NEEDS_HUMAN, not retry)."
    )


def test_state_transitions_consistent_between_contract_and_check():
    """ritual.contract.json {allowed_current_states, allowed_next_states} must be a superset of
    check.template.json state_transition.{from, to}."""
    mismatches = []
    for ritual in RITUALS:
        contract = _load_json(RITUALS_DIR / ritual / "ritual.contract.json")
        check = _load_json(RITUALS_DIR / ritual / "check.template.json")
        c_from = set(contract.get("allowed_current_states", []))
        c_to = set(contract.get("allowed_next_states", []))
        chk_from = set(check.get("state_transition", {}).get("from", []))
        chk_to = set(check.get("state_transition", {}).get("to", []))
        if not chk_from.issubset(c_from):
            mismatches.append(f"{ritual}: check.state_transition.from {chk_from} not subset of contract.allowed_current_states {c_from}")
        if not chk_to.issubset(c_to):
            mismatches.append(f"{ritual}: check.state_transition.to {chk_to} not subset of contract.allowed_next_states {c_to}")
    assert not mismatches, "State-transition inconsistencies:\n  " + "\n  ".join(mismatches)
