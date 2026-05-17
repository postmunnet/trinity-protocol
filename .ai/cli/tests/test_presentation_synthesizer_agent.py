"""Tests for the in-house `presentation_synthesizer` agent — v2 (DDD §3.1)."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from cli.agents.presentation_synthesizer.core import (
    PresentationPacket,
    ValidationError,
    _ACCEPTED_PROTOCOL_VERSIONS,
    _COGNITIVE_PROTOCOL_VERSION,
    _DDD_PRESENTATION_KEYS,
    _PANEL_DIVERSITY_KEYS,
    _TRANSPORT_CAPABILITY_KEYS,
    _V102_OPTIONAL_ALIAS_KEYS,
    _V102_REQUIRED_KEYS,
    _compute_sha256,
    _parse_llm_json,
    _read_session_inputs,
    _session_slug_from_path,
    _summarize_session_audit,
    _validate_packet,
    synthesize_presentation,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import MockBackend


def _seed_session(
    tmp_path: Path,
    slug: str = "feat-x",
    envelope: Dict[str, Any] = None,
    retro: str = "",
) -> Path:
    if envelope is None:
        envelope = {"goal": "build", "tier": "WARM", "steps": []}
    session_dir = tmp_path / f"0001_2026-05-13_11_13_am_{slug}"
    (session_dir / "THINK").mkdir(parents=True)
    (session_dir / "THINK" / "plan_envelope.json").write_text(json.dumps(envelope))
    if retro:
        (session_dir / "THINK" / "RETRO.md").write_text(retro)
    return session_dir


def _good_packet() -> Dict[str, Any]:
    """Sample packet conforming to DDD §3.1 (9 fields)."""
    return {
        "cognitive_protocol_version": "v1.0.1",
        "summary": "5 gogogo steps PASS; final state VERIFIED; no NEEDS_HUMAN.",
        "convergence": [
            "Plan envelope landed at THINK/plan_envelope.json",
            "All 5 gogogo steps returned PASS",
        ],
        "dissent_flags": [],
        "founder_decisions_required": [
            "Approve promote to dev?",
        ],
        "raw_artifacts_available": True,
        "panel_diversity": {
            "roles": ["planner", "executor", "verifier"],
            "distinct_models": 0,
            "distinct_layers": 1,
        },
        "synthesizer_not_in_opinion_panel": True,
        "capture_refs": [],
    }


# ─────────────── Imports + helpers ───────────────


def test_imports():
    assert callable(synthesize_presentation)


def test_ddd_presentation_keys_complete():
    """The 9 required keys from DDD §3.1 must all be present in the constant."""
    expected = {
        "cognitive_protocol_version",
        "summary",
        "convergence",
        "dissent_flags",
        "founder_decisions_required",
        "raw_artifacts_available",
        "panel_diversity",
        "synthesizer_not_in_opinion_panel",
        "capture_refs",
    }
    assert set(_DDD_PRESENTATION_KEYS) == expected


def test_panel_diversity_keys_complete():
    assert set(_PANEL_DIVERSITY_KEYS) == {"roles", "distinct_models", "distinct_layers"}


def test_cognitive_protocol_version_constant():
    """v1.0.2 cross-amendment (2026-05-15) bumped the canonical version
    while keeping v1.0.1 in the accepted set for backward compatibility."""
    assert _COGNITIVE_PROTOCOL_VERSION == "v1.0.2"
    assert set(_ACCEPTED_PROTOCOL_VERSIONS) == {"v1.0.1", "v1.0.2"}


def test_v102_constants_complete():
    """v1.0.2 introduces 2 newly-canonical fields + 2 alias fields."""
    assert set(_V102_REQUIRED_KEYS) == {"compression_ratio", "transport_capability"}
    assert set(_V102_OPTIONAL_ALIAS_KEYS) == {"dissent_preserved", "raw_artifact_links"}
    assert set(_TRANSPORT_CAPABILITY_KEYS) == {
        "channel", "max_payload_bytes", "supports_attachments",
    }


# ─────────────── _read_session_inputs ───────────────


def test_read_session_inputs_happy(tmp_path: Path):
    session = _seed_session(tmp_path)
    out = _read_session_inputs(session)
    assert out["plan_envelope"]["tier"] == "WARM"
    assert out["retro_md"] == ""
    assert out["retro_path"] is None


def test_read_session_inputs_with_retro(tmp_path: Path):
    session = _seed_session(tmp_path, retro="# Retro\n\nbody")
    out = _read_session_inputs(session)
    assert "Retro" in out["retro_md"]
    assert out["retro_path"] is not None


def test_read_session_inputs_missing_envelope(tmp_path: Path):
    d = tmp_path / "no-plan"
    (d / "THINK").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="plan_envelope"):
        _read_session_inputs(d)


def test_session_slug_extract():
    p = Path("/x/0001_2026-05-13_11_13_am_feat-foo")
    assert _session_slug_from_path(p) == "feat-foo"


# ─────────────── _summarize_session_audit ───────────────


def test_summarize_audit_no_chain(tmp_path: Path):
    out = _summarize_session_audit(tmp_path, "feat-test")
    assert out["event_count"] == 0
    assert out["final_graph_state"] == "unknown"
    assert out["distinct_models"] == 0
    assert out["distinct_layers"] == 0


def test_summarize_audit_with_events(tmp_path: Path):
    """Synthetic audit chain with session-matched events."""
    audit_dir = tmp_path / ".ai" / "audit"
    audit_dir.mkdir(parents=True)
    events = [
        {"type": "session.created", "details": {"session": "feat-foo", "actor": "kernel"}, "hash": "h1"},
        {"type": "graph.transition", "details": {"session": "feat-foo", "to": "DO"}, "hash": "h2"},
        {"type": "verify.completed", "details": {"session": "feat-foo", "layer": 1}, "hash": "h3"},
        {"type": "verify.completed", "details": {"session": "feat-foo", "layer": 2}, "hash": "h4"},
        {"type": "session.created", "details": {"session": "feat-other"}, "hash": "h5"},
    ]
    with (audit_dir / "events.ndjson").open("w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    out = _summarize_session_audit(tmp_path, "feat-foo")
    assert out["event_count"] == 4
    assert out["final_graph_state"] == "DO"
    assert out["distinct_layers"] == 2
    assert "kernel" in out["roles_seen"]


# ─────────────── _validate_packet — happy path ───────────────


def test_validate_packet_well_formed():
    _validate_packet(_good_packet())


def test_validate_packet_against_decision_packet_schema(tmp_path: Path, repo_root: Path = None):
    """The packet must also validate against the JSON schema (full contract check)."""
    repo = Path(__file__).resolve().parents[3]
    schema_path = repo / ".ai" / "schemas" / "decision_packet.schema.json"
    import jsonschema
    schema = json.loads(schema_path.read_text())
    presentation_schema = schema["properties"]["presentation"]
    jsonschema.Draft7Validator(presentation_schema).validate(_good_packet())


# ─────────────── _validate_packet — failures ───────────────


def test_validate_packet_missing_summary():
    p = _good_packet()
    del p["summary"]
    with pytest.raises(ValidationError, match="missing required key.*summary"):
        _validate_packet(p)


def test_validate_packet_empty_summary():
    p = _good_packet()
    p["summary"] = "   "
    with pytest.raises(ValidationError, match="summary.*non-empty"):
        _validate_packet(p)


def test_validate_packet_wrong_cognitive_protocol_version():
    p = _good_packet()
    p["cognitive_protocol_version"] = "v0.9"
    with pytest.raises(ValidationError, match="cognitive_protocol_version"):
        _validate_packet(p)


def test_validate_packet_dissent_flags_must_be_strings():
    p = _good_packet()
    p["dissent_flags"] = [{"topic": "x", "view": "y"}]  # old shape — now invalid
    with pytest.raises(ValidationError, match="dissent_flags.*list of strings"):
        _validate_packet(p)


def test_validate_packet_empty_dissent_flags_ok():
    """Empty dissent_flags IS valid (anti-groupthink signal)."""
    p = _good_packet()
    p["dissent_flags"] = []
    _validate_packet(p)


def test_validate_packet_panel_diversity_missing_field():
    p = _good_packet()
    del p["panel_diversity"]["distinct_layers"]
    with pytest.raises(ValidationError, match="panel_diversity missing.*distinct_layers"):
        _validate_packet(p)


def test_validate_packet_panel_diversity_unknown_field():
    p = _good_packet()
    p["panel_diversity"]["extra"] = "nope"
    with pytest.raises(ValidationError, match="panel_diversity unknown keys"):
        _validate_packet(p)


def test_validate_packet_distinct_layers_out_of_range():
    p = _good_packet()
    p["panel_diversity"]["distinct_layers"] = 5
    with pytest.raises(ValidationError, match="distinct_layers.*1..4"):
        _validate_packet(p)


def test_validate_packet_synthesizer_in_panel_rejected():
    p = _good_packet()
    p["synthesizer_not_in_opinion_panel"] = False
    with pytest.raises(ValidationError, match="messenger is not a juror"):
        _validate_packet(p)


def test_validate_packet_unknown_top_level_key():
    p = _good_packet()
    p["extra_field"] = "nope"
    with pytest.raises(ValidationError, match="unknown keys"):
        _validate_packet(p)


def test_validate_packet_raw_artifacts_available_must_be_bool():
    p = _good_packet()
    p["raw_artifacts_available"] = "true"  # string not bool
    with pytest.raises(ValidationError, match="raw_artifacts_available.*boolean"):
        _validate_packet(p)


def test_validate_packet_capture_refs_must_be_strings():
    p = _good_packet()
    p["capture_refs"] = ["valid_ulid", 123]
    with pytest.raises(ValidationError, match="capture_refs.*list of strings"):
        _validate_packet(p)


def test_validate_packet_founder_decisions_must_be_strings():
    p = _good_packet()
    p["founder_decisions_required"] = [{"q": "?"}]
    with pytest.raises(ValidationError, match="founder_decisions_required.*list of strings"):
        _validate_packet(p)


def test_validate_packet_convergence_must_be_strings():
    p = _good_packet()
    p["convergence"] = ["fact", 42]
    with pytest.raises(ValidationError, match="convergence.*list of strings"):
        _validate_packet(p)


# ─────────────── v1.0.2 cross-amendment (Phase 13 §5 alignment) ───────────────


def _good_packet_v102() -> Dict[str, Any]:
    """Sample packet conforming to DDD §3.1 v1.0.2 (9 base + 2 required + 2 alias)."""
    p = _good_packet()
    p["cognitive_protocol_version"] = "v1.0.2"
    p["compression_ratio"] = 0.18
    p["transport_capability"] = {
        "channel": "telegram",
        "max_payload_bytes": 4096,
        "supports_attachments": False,
    }
    # Optional aliases:
    p["dissent_preserved"] = list(p["dissent_flags"])  # byte-identical copy
    p["raw_artifact_links"] = ["https://kernel.local/artefacts/cap_x"]
    return p


def test_validate_packet_v102_well_formed():
    _validate_packet(_good_packet_v102())


def test_validate_packet_v102_without_optional_aliases():
    p = _good_packet_v102()
    del p["dissent_preserved"]
    del p["raw_artifact_links"]
    _validate_packet(p)


def test_validate_packet_v102_missing_compression_ratio():
    p = _good_packet_v102()
    del p["compression_ratio"]
    with pytest.raises(ValidationError, match="missing required key.*v1\\.0\\.2.*compression_ratio"):
        _validate_packet(p)


def test_validate_packet_v102_compression_ratio_out_of_range():
    p = _good_packet_v102()
    p["compression_ratio"] = 1.5
    with pytest.raises(ValidationError, match="compression_ratio must be in"):
        _validate_packet(p)


def test_validate_packet_v102_compression_ratio_must_be_number():
    p = _good_packet_v102()
    p["compression_ratio"] = "0.5"
    with pytest.raises(ValidationError, match="compression_ratio must be a number"):
        _validate_packet(p)


def test_validate_packet_v102_compression_ratio_bool_rejected():
    p = _good_packet_v102()
    p["compression_ratio"] = True
    with pytest.raises(ValidationError, match="compression_ratio must be a number"):
        _validate_packet(p)


def test_validate_packet_v102_missing_transport_capability():
    p = _good_packet_v102()
    del p["transport_capability"]
    with pytest.raises(ValidationError, match="missing required key.*v1\\.0\\.2.*transport_capability"):
        _validate_packet(p)


def test_validate_packet_v102_transport_capability_missing_field():
    p = _good_packet_v102()
    del p["transport_capability"]["channel"]
    with pytest.raises(ValidationError, match="transport_capability missing.*channel"):
        _validate_packet(p)


def test_validate_packet_v102_transport_capability_unknown_field():
    p = _good_packet_v102()
    p["transport_capability"]["extra"] = "nope"
    with pytest.raises(ValidationError, match="transport_capability unknown keys"):
        _validate_packet(p)


def test_validate_packet_v102_transport_capability_max_payload_negative():
    p = _good_packet_v102()
    p["transport_capability"]["max_payload_bytes"] = -1
    with pytest.raises(ValidationError, match="max_payload_bytes must be >= 0"):
        _validate_packet(p)


def test_validate_packet_v102_transport_capability_supports_attachments_must_be_bool():
    p = _good_packet_v102()
    p["transport_capability"]["supports_attachments"] = "no"
    with pytest.raises(ValidationError, match="supports_attachments must be a boolean"):
        _validate_packet(p)


def test_validate_packet_v102_dissent_preserved_alias_byte_identical():
    """Alias must equal canonical when both present (Phase 11 §3.1.1)."""
    p = _good_packet_v102()
    p["dissent_flags"] = ["A dissent point"]
    p["dissent_preserved"] = ["A different dissent point"]
    with pytest.raises(ValidationError, match="dissent_preserved alias must be byte-identical"):
        _validate_packet(p)


def test_validate_packet_v102_dissent_preserved_alias_matches_ok():
    p = _good_packet_v102()
    p["dissent_flags"] = ["A dissent point"]
    p["dissent_preserved"] = ["A dissent point"]
    _validate_packet(p)


def test_validate_packet_v102_dissent_preserved_must_be_strings():
    p = _good_packet_v102()
    p["dissent_preserved"] = [{"role": "verifier"}]
    with pytest.raises(ValidationError, match="dissent_preserved.*list of strings"):
        _validate_packet(p)


def test_validate_packet_v102_raw_artifact_links_must_be_strings():
    p = _good_packet_v102()
    p["raw_artifact_links"] = ["good_link", 42]
    with pytest.raises(ValidationError, match="raw_artifact_links.*list of strings"):
        _validate_packet(p)


def test_validate_packet_v102_raw_artifact_links_warn_only_no_id_match():
    """raw_artifact_links is URL/path form; not byte-checked against capture_refs."""
    p = _good_packet_v102()
    p["capture_refs"] = ["cap_01HZ..."]
    p["raw_artifact_links"] = ["https://kernel.local/totally/different/path"]
    # no error: links and IDs are intentionally different shapes
    _validate_packet(p)


def test_validate_packet_v101_rejects_v102_extra_fields():
    """A v1.0.1 packet MUST NOT carry v1.0.2 fields (additionalProperties:false)."""
    p = _good_packet()  # v1.0.1
    p["compression_ratio"] = 0.5
    with pytest.raises(ValidationError, match="unknown keys"):
        _validate_packet(p)


def test_validate_packet_unknown_version_rejected():
    p = _good_packet()
    p["cognitive_protocol_version"] = "v2.0"
    with pytest.raises(ValidationError, match="cognitive_protocol_version must be one of"):
        _validate_packet(p)


# ─────────────── _parse_llm_json ───────────────


def test_parse_llm_json_fence():
    assert _parse_llm_json('```json\n{"a":1}\n```') == {"a": 1}


def test_parse_llm_json_bare():
    assert _parse_llm_json('{"a":1}') == {"a": 1}


def test_parse_llm_json_garbage():
    with pytest.raises(ValidationError):
        _parse_llm_json("not JSON")


# ─────────────── synthesize_presentation ───────────────


def test_synthesize_via_mock_backend(tmp_path: Path):
    session = _seed_session(tmp_path)
    backend = MockBackend(canned=json.dumps(_good_packet()))
    packet = synthesize_presentation(
        session_path=session, repo_root=tmp_path, backend=backend
    )
    assert isinstance(packet, PresentationPacket)
    assert packet.packet["cognitive_protocol_version"] == "v1.0.1"
    assert packet.packet["synthesizer_not_in_opinion_panel"] is True
    assert packet.packet["dissent_flags"] == []


def test_synthesize_audit_emission(tmp_path: Path):
    session = _seed_session(tmp_path)
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned=json.dumps(_good_packet()))
    synthesize_presentation(
        session_path=session, repo_root=tmp_path, backend=backend, audit_chain=chain
    )
    types = [e["type"] for e in chain.iter_events()]
    assert types == [
        "presentation_synthesizer.invoked",
        "llm.call_started",
        "llm.call_completed",
        "presentation_synthesizer.proposed",
    ]


def test_synthesize_proposed_event_carries_new_fields(tmp_path: Path):
    """The .proposed audit event payload should carry v2 field counts."""
    session = _seed_session(tmp_path)
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned=json.dumps(_good_packet()))
    synthesize_presentation(
        session_path=session, repo_root=tmp_path, backend=backend, audit_chain=chain
    )
    proposed = [e for e in chain.iter_events() if e["type"] == "presentation_synthesizer.proposed"][0]
    details = proposed.get("details", {})
    assert details.get("cognitive_protocol_version") == "v1.0.1"
    assert "dissent_flag_count" in details
    assert "founder_decisions_required_count" in details
    assert "capture_refs_count" in details


def test_synthesize_failure_audit(tmp_path: Path):
    session = _seed_session(tmp_path)
    chain = AuditChain(tmp_path / "events.ndjson")
    backend = MockBackend(canned="not JSON")
    with pytest.raises(ValidationError):
        synthesize_presentation(
            session_path=session, repo_root=tmp_path, backend=backend, audit_chain=chain
        )
    types = [e["type"] for e in chain.iter_events()]
    assert "presentation_synthesizer.invoked" in types
    assert "presentation_synthesizer.failed" in types


def test_synthesize_rejects_old_shape(tmp_path: Path):
    """Old 4-key shape (synthesis/dissent/raw/notes) must fail validation."""
    session = _seed_session(tmp_path)
    old_shape = {
        "synthesis": {"one_line": "x", "what_landed": "y", "verdict_summary": "z", "risk_remaining": "w"},
        "dissent": [],
        "raw": {"plan_envelope_path": "p", "retro_path": None, "audit_event_count": 0,
                "gogogo_verdicts": {}, "needs_human_count": 0, "final_graph_state": "DONE"},
        "notes": "n",
    }
    backend = MockBackend(canned=json.dumps(old_shape))
    with pytest.raises(ValidationError, match="missing required key"):
        synthesize_presentation(
            session_path=session, repo_root=tmp_path, backend=backend
        )


# ─────────────── helpers ───────────────


def test_compute_sha256(tmp_path: Path):
    f = tmp_path / "x.txt"
    f.write_bytes(b"hello")
    h = _compute_sha256(f)
    assert h == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


# ─────────────── CLI ───────────────


def test_cli_happy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.presentation_synthesizer import cli as ps_cli

    def _fake(session_path, repo_root, backend=None, audit_chain=None):
        return PresentationPacket(packet=_good_packet())

    monkeypatch.setattr(ps_cli, "synthesize_presentation", _fake)
    session = _seed_session(tmp_path)
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = ps_cli.main(["draft", "--session-path", str(session), "--no-audit"])
    assert rc == 0
    parsed = json.loads(captured.getvalue())
    assert parsed["cognitive_protocol_version"] == "v1.0.1"
    assert parsed["synthesizer_not_in_opinion_panel"] is True


def test_cli_missing_session_exit_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from cli.agents.presentation_synthesizer import cli as ps_cli
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    rc = ps_cli.main([
        "draft", "--session-path", str(tmp_path / "noexist"), "--no-audit",
    ])
    assert rc == 2
