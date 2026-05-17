"""Presentation Synthesizer — fifth in-house Trinity agent (v2: DDD §3.1 fields).

Produces a `presentation` object for the ddd decision_packet per
TRINITY_DDD_HUMAN_GATE_SPEC_V1 §3.1 (Addendum v1.0.1 §E Cognitive Presentation
Protocol). Output validates against `.ai/schemas/decision_packet.schema.json`
properties.presentation.

Schema versioning:
  - cognitive_protocol_version "v1.0.1" — original 9 required fields (the
    .ai/schemas/decision_packet.schema.json const is "v1.0.1"; existing
    artefacts and downstream readers continue to work).
  - cognitive_protocol_version "v1.0.2" — adds 4 fields per Phase 13 §5
    cross-amendment (2026-05-15): compression_ratio (required),
    transport_capability (required), dissent_preserved (optional alias of
    dissent_flags), raw_artifact_links (optional URL/path form of capture_refs).
    Aliases MUST be byte-identical to canonical when both present
    (dissent_preserved == dissent_flags). raw_artifact_links carries
    URL/path strings and is only warned-on (not byte-equal-checked) since
    its semantics differ from capture_refs (IDs).

Authority:
  - Constitution v1.0 Articles III, IV, IX, XVI, XVII, XX.
  - Addendum v1.0.1 §E (Cognitive Presentation): synthesizer is the messenger,
    NEVER the juror. `synthesizer_not_in_opinion_panel` MUST be true.
  - RC v1.1 Article XVIII (Presentation Synthesizer role).
  - V1.1 Amendment Queue items C-13-1 + C-13-3 (RESOLVED 2026-05-15) for the
    v1.0.2 schema bump.

Pseudo-test (illustrative only; live tests at
.ai/cli/tests/test_presentation_synthesizer_agent.py):
  >>> p = _good_packet_v102()  # 9 base + 2 required + 2 optional
  >>> _validate_packet(p)      # passes
  >>> p["dissent_preserved"] = ["different"]
  >>> _validate_packet(p)      # raises: alias must be byte-identical
"""
from __future__ import annotations

import hashlib
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

# DDD §3.1 — required presentation sub-fields (decision_packet.schema.json).
_DDD_PRESENTATION_KEYS = (
    "cognitive_protocol_version",
    "summary",
    "convergence",
    "dissent_flags",
    "founder_decisions_required",
    "raw_artifacts_available",
    "panel_diversity",
    "synthesizer_not_in_opinion_panel",
    "capture_refs",
)
_PANEL_DIVERSITY_KEYS = ("roles", "distinct_models", "distinct_layers")

# v1.0.2 cross-amendment (2026-05-15) — Phase 13 §5 alignment.
# 2 newly canonical fields (required when version is v1.0.2):
_V102_REQUIRED_KEYS = ("compression_ratio", "transport_capability")
# 2 alias fields (optional under v1.0.2; consistency-checked when present):
_V102_OPTIONAL_ALIAS_KEYS = ("dissent_preserved", "raw_artifact_links")
_TRANSPORT_CAPABILITY_KEYS = ("channel", "max_payload_bytes", "supports_attachments")

# Canonical version constant (used by .proposed audit event + schema check).
# The .ai/schemas/decision_packet.schema.json file pins const "v1.0.1"; the
# in-process validator accepts both v1.0.1 and v1.0.2 so existing v1.0.1
# artefacts continue to validate against the JSON schema while new v1.0.2
# artefacts gain access to the 4 added fields.
_COGNITIVE_PROTOCOL_VERSION = "v1.0.2"
_ACCEPTED_PROTOCOL_VERSIONS = ("v1.0.1", "v1.0.2")
_STRING_LIST_FIELDS = (
    "convergence",
    "dissent_flags",
    "founder_decisions_required",
    "capture_refs",
)
_V102_STRING_LIST_FIELDS = (
    "dissent_preserved",
    "raw_artifact_links",
)


class ValidationError(Exception):
    pass


@dataclass
class PresentationPacket:
    packet: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.packet)

    def to_json(self) -> str:
        return json.dumps(self.packet, indent=2, ensure_ascii=False)


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
    envelope_path = session_path / "THINK" / "plan_envelope.json"
    retro_path = session_path / "THINK" / "RETRO.md"
    if not envelope_path.is_file():
        raise FileNotFoundError(f"plan_envelope not found: {envelope_path}")
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    retro_md = ""
    if retro_path.is_file():
        retro_md = retro_path.read_text(encoding="utf-8")
    return {
        "plan_envelope": envelope,
        "retro_md": retro_md,
        "retro_path": str(retro_path) if retro_path.is_file() else None,
    }


def _summarize_session_audit(repo_root: Path, slug_substring: str) -> Dict[str, Any]:
    """Read `.ai/audit/events.ndjson`; filter to events matching slug_substring;
    return an aggregate dict with counts + panel-diversity inputs.

    Keys returned:
      - event_count, final_graph_state, gogogo_verdicts, needs_human_count,
        sample_event_types — backward-compatible scalars.
      - roles_seen (list[str]) — distinct emitters / actors observed
      - distinct_models (int) — distinct LLM model names from `llm.*` payloads
      - distinct_layers (int) — distinct verifier layer values from `verify.*`
    """
    events_path = repo_root / ".ai" / "audit" / "events.ndjson"
    out: Dict[str, Any] = {
        "event_count": 0,
        "final_graph_state": "unknown",
        "gogogo_verdicts": {"PASS": 0, "FAIL": 0, "UNVERIFIED": 0},
        "needs_human_count": 0,
        "sample_event_types": [],
        "roles_seen": [],
        "distinct_models": 0,
        "distinct_layers": 0,
    }
    if not events_path.is_file():
        return out
    seen_types: List[str] = []
    roles: set[str] = set()
    models: set[str] = set()
    layers: set[int] = set()
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
        ev_type = ev.get("type", "?")
        seen_types.append(ev_type)
        details = ev.get("details") or {}
        if isinstance(details, dict):
            actor = details.get("decided_by") or details.get("actor")
            if isinstance(actor, str) and actor:
                roles.add(actor)
            model = details.get("model") or details.get("model_name")
            if isinstance(model, str) and model:
                models.add(model)
            if ev_type.startswith("verify.") or ev_type.startswith("ritual.validation."):
                layer = details.get("layer")
                if isinstance(layer, int) and 1 <= layer <= 4:
                    layers.add(layer)
        if ev_type == "graph.transition":
            to_state = details.get("to") if isinstance(details, dict) else None
            if to_state:
                out["final_graph_state"] = to_state
        if ev_type == "gogogo.step_passed":
            out["gogogo_verdicts"]["PASS"] += 1
        if ev_type == "gogogo.step_failed":
            out["gogogo_verdicts"]["FAIL"] += 1
        if "NEEDS_HUMAN" in details_str:
            out["needs_human_count"] += 1
    out["sample_event_types"] = sorted(set(seen_types))[:20]
    out["roles_seen"] = sorted(roles)
    out["distinct_models"] = len(models)
    out["distinct_layers"] = len(layers) or (1 if out["event_count"] else 0)
    return out


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def _validate_packet(d: Any) -> None:
    """Validate a `presentation` packet against DDD §3.1 / decision_packet schema.

    Schema is authoritative (.ai/schemas/decision_packet.schema.json). This
    validator enforces the same constraints in-process so the agent can fail
    fast before emission.

    Versioning (cross-amendment 2026-05-15, V1.1 Amendment Queue C-13-1/3):
      - "v1.0.1" — original 9 required fields; no extras allowed.
      - "v1.0.2" — adds 2 required fields (compression_ratio,
        transport_capability) and 2 optional alias fields (dissent_preserved,
        raw_artifact_links). Aliases must be consistent with their canonical
        Phase 11 counterparts.
    """
    if not isinstance(d, dict):
        raise ValidationError(f"packet must be a dict; got {type(d).__name__}")

    # 1. All 9 base required keys present (regardless of version).
    for key in _DDD_PRESENTATION_KEYS:
        if key not in d:
            raise ValidationError(f"missing required key: {key!r}")

    # 2. cognitive_protocol_version must be one of the accepted versions.
    version = d["cognitive_protocol_version"]
    if version not in _ACCEPTED_PROTOCOL_VERSIONS:
        raise ValidationError(
            f"cognitive_protocol_version must be one of {list(_ACCEPTED_PROTOCOL_VERSIONS)!r}; "
            f"got {version!r}"
        )

    # 3. additionalProperties:false — known-key set depends on version.
    if version == "v1.0.1":
        allowed = set(_DDD_PRESENTATION_KEYS)
    else:  # v1.0.2
        allowed = set(_DDD_PRESENTATION_KEYS) | set(_V102_REQUIRED_KEYS) | set(_V102_OPTIONAL_ALIAS_KEYS)
    extras = set(d.keys()) - allowed
    if extras:
        raise ValidationError(f"unknown keys (additionalProperties:false): {sorted(extras)!r}")

    # 4. summary non-empty string.
    if not isinstance(d["summary"], str) or not d["summary"].strip():
        raise ValidationError("summary must be a non-empty string")

    # 5. String-list fields are flat string arrays (NOT objects).
    for field in _STRING_LIST_FIELDS:
        if not _is_string_list(d[field]):
            raise ValidationError(
                f"{field} must be a list of strings; got {type(d[field]).__name__}"
                + ("" if not isinstance(d[field], list) else " with non-string items")
            )

    # 6. raw_artifacts_available is boolean.
    if not isinstance(d["raw_artifacts_available"], bool):
        raise ValidationError("raw_artifacts_available must be a boolean")

    # 7. panel_diversity is dict with required 3 keys + correct types.
    pd = d["panel_diversity"]
    if not isinstance(pd, dict):
        raise ValidationError("panel_diversity must be a dict")
    for key in _PANEL_DIVERSITY_KEYS:
        if key not in pd:
            raise ValidationError(f"panel_diversity missing key: {key!r}")
    pd_extras = set(pd.keys()) - set(_PANEL_DIVERSITY_KEYS)
    if pd_extras:
        raise ValidationError(f"panel_diversity unknown keys: {sorted(pd_extras)!r}")
    if not _is_string_list(pd["roles"]):
        raise ValidationError("panel_diversity.roles must be a list of strings")
    if not isinstance(pd["distinct_models"], int) or isinstance(pd["distinct_models"], bool):
        raise ValidationError("panel_diversity.distinct_models must be an integer")
    if pd["distinct_models"] < 0:
        raise ValidationError("panel_diversity.distinct_models must be >= 0")
    if not isinstance(pd["distinct_layers"], int) or isinstance(pd["distinct_layers"], bool):
        raise ValidationError("panel_diversity.distinct_layers must be an integer")
    if not (1 <= pd["distinct_layers"] <= 4):
        raise ValidationError("panel_diversity.distinct_layers must be 1..4")

    # 8. synthesizer_not_in_opinion_panel MUST be true (Addendum §E messenger != juror).
    if d["synthesizer_not_in_opinion_panel"] is not True:
        raise ValidationError(
            "synthesizer_not_in_opinion_panel MUST be true (Addendum v1.0.1 §E: "
            "the messenger is not a juror)"
        )

    # 9. v1.0.2 cross-amendment fields.
    if version == "v1.0.2":
        # 9a. The 2 newly-canonical fields are REQUIRED in v1.0.2.
        for key in _V102_REQUIRED_KEYS:
            if key not in d:
                raise ValidationError(f"missing required key (v1.0.2): {key!r}")

        # 9b. compression_ratio: float in [0.0, 1.0].
        cr = d["compression_ratio"]
        # bool is subclass of int; reject explicitly.
        if isinstance(cr, bool) or not isinstance(cr, (int, float)):
            raise ValidationError("compression_ratio must be a number")
        if not (0.0 <= float(cr) <= 1.0):
            raise ValidationError("compression_ratio must be in [0.0, 1.0]")

        # 9c. transport_capability: object with channel/max_payload_bytes/supports_attachments.
        tc = d["transport_capability"]
        if not isinstance(tc, dict):
            raise ValidationError("transport_capability must be a dict")
        for key in _TRANSPORT_CAPABILITY_KEYS:
            if key not in tc:
                raise ValidationError(f"transport_capability missing key: {key!r}")
        tc_extras = set(tc.keys()) - set(_TRANSPORT_CAPABILITY_KEYS)
        if tc_extras:
            raise ValidationError(f"transport_capability unknown keys: {sorted(tc_extras)!r}")
        if not isinstance(tc["channel"], str) or not tc["channel"].strip():
            raise ValidationError("transport_capability.channel must be a non-empty string")
        if isinstance(tc["max_payload_bytes"], bool) or not isinstance(tc["max_payload_bytes"], int):
            raise ValidationError("transport_capability.max_payload_bytes must be an integer")
        if tc["max_payload_bytes"] < 0:
            raise ValidationError("transport_capability.max_payload_bytes must be >= 0")
        if not isinstance(tc["supports_attachments"], bool):
            raise ValidationError("transport_capability.supports_attachments must be a boolean")

        # 9d. Optional alias fields: when present, must be string lists.
        for field in _V102_STRING_LIST_FIELDS:
            if field in d and not _is_string_list(d[field]):
                raise ValidationError(
                    f"{field} must be a list of strings; got {type(d[field]).__name__}"
                    + ("" if not isinstance(d[field], list) else " with non-string items")
                )

        # 9e. dissent_preserved alias rule: if both present, MUST be byte-identical
        #     to canonical dissent_flags (Phase 11 §3.1.1 alias mapping).
        if "dissent_preserved" in d:
            if d["dissent_preserved"] != d["dissent_flags"]:
                raise ValidationError(
                    "dissent_preserved alias must be byte-identical to canonical "
                    "dissent_flags (Phase 11 §3.1.1 alias mapping)"
                )

        # 9f. raw_artifact_links: WARN-only (URL/path form differs from capture_refs IDs).
        #     We do not enforce equivalence; only enforce shape (string list, done above).


def _parse_llm_json(text: str) -> Dict[str, Any]:
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
        raise ValidationError(f"LLM response must start with '{{'; got: {stripped[:80]!r}")
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ValidationError(f"LLM response is not valid JSON: {e.msg}") from e


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def synthesize_presentation(
    session_path: Path,
    repo_root: Path,
    backend: Optional[Backend] = None,
    audit_chain: Optional[AuditChain] = None,
) -> PresentationPacket:
    """Top-level entry. Audit events: presentation_synthesizer.invoked/.proposed/.failed."""
    inputs = _read_session_inputs(session_path)
    slug = _session_slug_from_path(session_path)
    audit_summary = _summarize_session_audit(repo_root, slug)

    template = _PROMPT_PATH.read_text(encoding="utf-8")
    context_schema = {
        "context_schema_version": "1.0",
        "ritual": "presentation_synthesizer",
        "placeholders": [
            {"identifier": "session.slug", "type": "plain_text", "required": True, "description": "slug"},
            {"identifier": "session.plan_envelope", "type": "json_string", "required": True, "description": "envelope"},
            {"identifier": "session.retro_md", "type": "markdown_escaped", "required": False, "description": "retro md"},
            {"identifier": "session.audit_summary", "type": "markdown_escaped", "required": True, "description": "audit"},
        ],
    }
    ctx = {
        "session": {
            "slug": slug,
            "plan_envelope": inputs["plan_envelope"],
            "retro_md": inputs["retro_md"] or "(no RETRO.md present yet)",
            "audit_summary": json.dumps(audit_summary, indent=2),
        },
    }
    prompt = substitute(template, ctx, context_schema)

    if audit_chain is not None:
        audit_chain.append("presentation_synthesizer.invoked", {
            "session_slug": slug,
            "has_retro": bool(inputs["retro_md"]),
            "audit_event_count": audit_summary["event_count"],
        })

    backend = backend if backend is not None else select_backend()
    request = LLMRequest(prompt=prompt, timeout=180.0)

    try:
        response = call_llm(
            request, backend=backend, audit_chain=audit_chain,
            ritual_context={"ritual": "presentation_synthesizer", "session_slug": slug},
        )
        packet = _parse_llm_json(response.text)
        _validate_packet(packet)
    except Exception as e:
        if audit_chain is not None:
            audit_chain.append("presentation_synthesizer.failed", {
                "error_class": e.__class__.__name__,
                "error_message": str(e)[:500],
                "session_slug": slug,
            })
        raise

    if audit_chain is not None:
        audit_chain.append("presentation_synthesizer.proposed", {
            "session_slug": slug,
            "dissent_flag_count": len(packet.get("dissent_flags", [])),
            "founder_decisions_required_count": len(packet.get("founder_decisions_required", [])),
            "capture_refs_count": len(packet.get("capture_refs", [])),
            "cognitive_protocol_version": packet.get("cognitive_protocol_version"),
        })

    return PresentationPacket(packet=packet)


__all__ = [
    "synthesize_presentation",
    "PresentationPacket",
    "ValidationError",
    "_DDD_PRESENTATION_KEYS",
    "_PANEL_DIVERSITY_KEYS",
    "_COGNITIVE_PROTOCOL_VERSION",
    "_ACCEPTED_PROTOCOL_VERSIONS",
    "_V102_REQUIRED_KEYS",
    "_V102_OPTIONAL_ALIAS_KEYS",
    "_TRANSPORT_CAPABILITY_KEYS",
    "_read_session_inputs",
    "_summarize_session_audit",
    "_validate_packet",
    "_parse_llm_json",
    "_session_slug_from_path",
    "_compute_sha256",
]
