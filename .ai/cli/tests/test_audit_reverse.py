"""T3.3 — AuditChain.iter_events_reversed lazy reverse-streaming reader.

The reverse iterator reads the file from the end in blocks instead of loading
the whole file; its yielded sequence must stay identical to the old
reversed(list(iter_events())), across block boundaries and long lines, and it
must be lazy (early-exit reads only the tail).
"""
from __future__ import annotations

from pathlib import Path

import cli.core.audit as audit_mod
from cli.core.audit import AuditChain


def _chain(tmp_path: Path) -> AuditChain:
    p = tmp_path / ".ai" / "audit" / "events.ndjson"
    p.parent.mkdir(parents=True, exist_ok=True)
    return AuditChain(p)


def _assert_equivalent(c: AuditChain) -> None:
    fwd = list(c.iter_events())
    assert list(c.iter_events_reversed()) == list(reversed(fwd))


def test_equivalence_empty(tmp_path):
    assert list(_chain(tmp_path).iter_events_reversed()) == []


def test_equivalence_single(tmp_path):
    c = _chain(tmp_path)
    c.append("e", {"i": 0})
    _assert_equivalent(c)


def test_equivalence_many(tmp_path):
    c = _chain(tmp_path)
    for i in range(50):
        c.append("e", {"i": i})
    _assert_equivalent(c)


def test_multiblock_boundary_tiny_block(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_mod, "_REVERSE_READ_BLOCK", 8)
    c = _chain(tmp_path)
    for i in range(30):
        c.append("e", {"i": i, "pad": "y" * 20})
    _assert_equivalent(c)


def test_long_line_spans_many_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_mod, "_REVERSE_READ_BLOCK", 16)
    c = _chain(tmp_path)
    c.append("big", {"blob": "z" * 500})  # one line far larger than a block
    c.append("small", {"i": 1})
    fwd = list(c.iter_events())
    rev = list(c.iter_events_reversed())
    assert rev == list(reversed(fwd))
    assert rev[-1] == fwd[0]  # the oldest (big) line reconstructed intact


def test_lazy_first_yield_is_most_recent(tmp_path):
    c = _chain(tmp_path)
    for i in range(10):
        c.append("e", {"i": i})
    fwd = list(c.iter_events())
    assert next(c.iter_events_reversed()) == fwd[-1]
