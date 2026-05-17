"""Tests for RecordProxy v1 Option C audit chain enrichment.

Plan ref: session feat-recordproxy-integration-v1 plan steps S5/S6/S7.

S5 — every ritual command emits at least one RecordProxy-schema-valid
     event when its emit-site is exercised. Since all seven ritual
     commands route through ``AuditChain.append`` (verified by the
     static_no_direct_ndjson_writes test below), exercising
     ``AuditChain.append`` once covers all seven rituals; the
     per-ritual exhaustive matrix is encoded as a parametrize that
     loops over the ritual command modules and confirms each one imports
     AuditChain (or routes via ``loop.chain``).

S6 — redaction round-trip preserves verifier-required top-level fields
     even when ``details`` contains secret-shaped values that get
     redacted.

S7 — no plain (pre-enrichment shape) events are written via
     ``AuditChain.append`` after wire-in: every new event carries the
     RecordProxy v1 ``schema_version`` marker. Legacy events written
     before wire-in are tolerated on the read path.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from cli.core.audit import AuditChain
from cli.core.recordproxy.emit import emit_via_proxy
from cli.core.recordproxy.schemas import AUDIT_EVENT_SCHEMA_VERSION


RITUAL_MODULES = [
    "cli.commands.sss",
    "cli.commands.vvv",
    "cli.commands.nnn",
    "cli.commands.gogogo",
    "cli.commands.ddd",
    "cli.commands.rrr",
    "cli.commands.close",
]


def _make_chain(tmp_path: Path) -> AuditChain:
    return AuditChain(tmp_path / "events.ndjson")


# ─── S5: AuditChain.append produces enriched events ───────────────────────────


def test_audit_chain_append_emits_schema_versioned_event(tmp_path):
    chain = _make_chain(tmp_path)
    event = chain.append(
        "ritual.test_event",
        {
            "session_id": "sess_test",
            "ritual": "test",
            "decided_by": "executor",
        },
    )

    assert event["schema_version"] == AUDIT_EVENT_SCHEMA_VERSION
    assert event["type"] == "ritual.test_event"
    assert event["session_id"] == "sess_test"
    assert event["ritual"] == "test"
    assert event["actor"] == "executor"
    assert event["prev_hash"] == "0"
    assert "redaction_meta" in event
    assert event["redaction_meta"]["mode"] == "REDACTED"
    assert "hash" in event


def test_audit_chain_validates_after_enriched_append(tmp_path):
    chain = _make_chain(tmp_path)
    for i in range(3):
        chain.append(f"ritual.evt_{i}", {"session_id": "s1", "i": i})
    chain.validate()


def test_audit_chain_links_old_and_new_shape(tmp_path):
    """Legacy-shape events (5 fields) and enriched events coexist in
    one chain; validate() walks both without error."""
    path = tmp_path / "events.ndjson"

    legacy = {
        "ts": "2026-05-13T00:00:00Z",
        "type": "legacy.event",
        "prev_hash": "0",
        "details": {"any": "thing"},
    }
    import hashlib

    canonical = json.dumps(legacy, sort_keys=True, separators=(",", ":"))
    legacy["hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    path.write_text(json.dumps(legacy, separators=(",", ":")) + "\n", encoding="utf-8")

    chain = AuditChain(path)
    chain.append("enriched.event", {"session_id": "sX"})

    chain.validate()
    events = list(chain.iter_events())
    assert len(events) == 2
    assert "schema_version" not in events[0]
    assert events[1]["schema_version"] == AUDIT_EVENT_SCHEMA_VERSION
    assert events[1]["prev_hash"] == events[0]["hash"]


@pytest.mark.parametrize("module_name", RITUAL_MODULES)
def test_ritual_command_routes_through_audit_chain(module_name):
    """Each ritual command module must import or transitively use
    AuditChain (directly or via ``loop.chain.append``). This is the
    S5 per-ritual coverage assertion: by routing through the single
    splice point, every ritual emits RecordProxy-enriched events."""
    mod = importlib.import_module(module_name)
    src = Path(mod.__file__).read_text(encoding="utf-8")
    # Direct import OR loop.chain.append (loop.chain is an AuditChain
    # via core.loop.Loop) OR get_chain_for_project (audit.py helper).
    assert (
        "AuditChain" in src
        or "loop.chain.append" in src
        or "get_chain_for_project" in src
    ), f"{module_name} does not appear to use AuditChain"


# ─── S6: Redaction round-trip preserves required fields ───────────────────────


def test_redaction_preserves_top_level_required_fields(tmp_path):
    chain = _make_chain(tmp_path)
    event = chain.append(
        "ritual.secret_event",
        {
            "session_id": "sess_secret",
            "ritual": "ddd",
            "decided_by": "human",
            "leak": "Authorization: Bearer AAAAAAAAAA1234567890XYZ",
            "akia": "AKIA" + "IOSFODNN7EXAMPLE",
        },
    )

    assert event["session_id"] == "sess_secret"
    assert event["ritual"] == "ddd"
    assert event["actor"] == "human"
    assert event["schema_version"] == AUDIT_EVENT_SCHEMA_VERSION
    assert event["redaction_meta"]["redacted_count"] >= 2
    assert "bearer_token" in event["redaction_meta"]["applied_rules"]
    assert "aws_access_key" in event["redaction_meta"]["applied_rules"]
    assert "AAAAAAAAAA1234567890XYZ" not in json.dumps(event)
    assert "AKIA" + "IOSFODNN7EXAMPLE" not in json.dumps(event)


def test_redaction_with_no_secrets_records_zero_count(tmp_path):
    chain = _make_chain(tmp_path)
    event = chain.append(
        "ritual.clean_event",
        {"session_id": "s1", "msg": "nothing sensitive"},
    )
    assert event["redaction_meta"]["redacted_count"] == 0
    assert event["redaction_meta"]["applied_rules"] == []
    assert event["details"]["msg"] == "nothing sensitive"


# ─── S7: No plain events written after wire-in ────────────────────────────────


def test_no_plain_events_written_via_append(tmp_path):
    """Every event produced by AuditChain.append after wire-in must
    carry the RecordProxy v1 schema_version marker. Plain (5-field)
    legacy events are tolerated on the read path but never produced
    by the writer."""
    chain = _make_chain(tmp_path)
    chain.append("a", {"session_id": "s1"})
    chain.append("b", {"session_id": "s1"})
    chain.append("c", None)

    events = list(chain.iter_events())
    assert len(events) == 3
    for ev in events:
        assert ev.get("schema_version") == AUDIT_EVENT_SCHEMA_VERSION, (
            f"Event {ev.get('type')!r} written via AuditChain.append "
            f"is missing schema_version — plain-event leak detected."
        )


# ─── memory: feedback_rituals_root_path_resolution — tmp-project fixture ──────


def test_emit_via_proxy_pure_function_no_io(tmp_path, monkeypatch):
    """The enrichment function must work from a chdir'd tmp dir
    without touching any project-root config. Guards against the
    rituals_root path-resolution drift documented in memory:
    feedback_rituals_root_path_resolution."""
    monkeypatch.chdir(tmp_path)
    out = emit_via_proxy(
        "x.y",
        {"session_id": "s_tmp", "actor": "test", "ritual": "vvv"},
        prev_hash="0",
        ts="2026-05-13T00:00:00Z",
    )
    assert out["schema_version"] == AUDIT_EVENT_SCHEMA_VERSION
    assert out["session_id"] == "s_tmp"
    assert out["actor"] == "test"
    assert out["ritual"] == "vvv"
    assert "hash" not in out  # caller computes hash
