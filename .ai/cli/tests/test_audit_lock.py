"""T3.1 — AuditChain.append concurrency lock.

The append critical section (read last_hash -> compute -> write) is guarded by a
POSIX fcntl exclusive lock, so concurrent appenders cannot read the same
prev_hash and fork the hash chain. Without the lock the contention test below
forks the chain and AuditChain.validate() raises.
"""
from __future__ import annotations

import threading
from pathlib import Path

from cli.core.audit import AuditChain


def _chain_path(tmp_path: Path) -> Path:
    p = tmp_path / ".ai" / "audit" / "events.ndjson"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def test_single_append_basic_regression(tmp_path: Path):
    c = AuditChain(_chain_path(tmp_path))
    c.append("test.one", {"x": 1})
    c.append("test.two", {"x": 2})
    c.validate()  # raises AuditChainError if the chain is broken
    assert sum(1 for _ in c.iter_events()) == 2


def test_concurrent_appends_produce_valid_contention_free_chain(tmp_path: Path):
    p = _chain_path(tmp_path)
    n_threads, n_each = 8, 25
    barrier = threading.Barrier(n_threads)
    errors: list = []

    def worker(i: int) -> None:
        chain = AuditChain(p)  # a separate instance per thread (own lock fd)
        try:
            barrier.wait()  # maximise contention on the first append
            for j in range(n_each):
                chain.append("test.event", {"thread": i, "j": j})
        except Exception as e:  # pragma: no cover - surfaced via errors
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, errors
    # The lock guarantees a single, unforked hash chain.
    AuditChain(p).validate()
    # Every append landed exactly once — no loss, no duplicate.
    assert sum(1 for _ in AuditChain(p).iter_events()) == n_threads * n_each
