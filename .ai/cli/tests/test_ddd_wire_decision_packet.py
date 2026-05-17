"""Wire #3 — verify ddd_artifacts is wired into commands/ddd.py."""
from __future__ import annotations

import inspect

from cli.commands import ddd as ddd_mod


def test_ddd_imports_decision_packet_helpers() -> None:
    src = inspect.getsource(ddd_mod)
    assert "from ..core.ddd_artifacts import" in src
    assert "make_decision_packet" in src
    assert "write_decision_packet" in src


def test_ddd_builds_and_writes_packet_inside_ddd_inner() -> None:
    src = inspect.getsource(ddd_mod)
    assert "make_decision_packet(" in src
    assert "write_decision_packet(session_path, packet)" in src
    inner_pos = src.find("def _ddd_inner")
    build_pos = src.find("make_decision_packet(")
    write_pos = src.find("write_decision_packet(")
    completed_pos = src.find('"ddd.completed"')
    # All inside _ddd_inner, ordering: build → write → ddd.completed.
    assert inner_pos < build_pos < write_pos < completed_pos


def test_packet_emission_is_fail_soft() -> None:
    src = inspect.getsource(ddd_mod)
    # Slice from "Wire #3" comment to "6. ddd.completed audit event" header.
    start = src.find("Wire #3 — produce schema-valid decision_packet")
    end = src.find("# 6. ddd.completed audit event")
    block = src[start:end]
    assert "try:" in block
    assert "except Exception" in block
    assert "decision packet emission failed" in block


def test_verifier_reports_built_from_verify_files() -> None:
    src = inspect.getsource(ddd_mod)
    assert "verify_dev.json" in src
    assert "verify_prod.json" in src
    assert "sha256" in src
