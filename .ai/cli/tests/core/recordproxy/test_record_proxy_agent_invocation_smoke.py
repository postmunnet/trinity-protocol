"""Smoke integration test for full RecordProxy capture lifecycle.

Asserts (design §3, §11):
    - prompt/context/template/stdout/stderr/validation captured
    - secret in prompt is redacted before hitting blob
    - capture status = COMPLETED after happy with-block
    - audit seq is contiguous across 2 captures
    - ULID monotonic ordering for two captures created in the same millisecond
"""

import json
import time

from cli.core.recordproxy import capture, new_capture_id
from cli.core.recordproxy.audit_writer import AuditWriter
from cli.core.recordproxy.capture_store import CaptureStore


def test_full_agent_invocation_lifecycle_smoke(tmp_path, monkeypatch):
    monkeypatch.delenv("TRINITY_RECORDPROXY_RAW", raising=False)

    sid = "sess_smoke"

    # ── Capture 1: simulate clarification_helper agent ──
    secret_prompt = "review this. Authorization: Bearer real_token_abc123def456"
    with capture(session_dir=tmp_path, ritual="vvv", role="CLARIFICATION_AGENT",
                 kind="agent_invocation", session_id=sid,
                 model_provider="anthropic", model_name="claude-sonnet") as cap:
        cap.input("prompt.md", secret_prompt)
        cap.input("context.json", {"task": "first vvv question"})
        cap.input("template.md", "# vvv template v1\n...")
        cap.output("stdout.md", "draft answer 1")
        cap.output("stderr.md", "")
        cap.output("raw_output.md", "{ \"1\": \"draft answer 1\" }")
        cap.validation("validation.json", {"ok": True, "questions_answered": 1})
        cid_1 = cap.capture_id

    # ── Capture 2: simulate executor_helper ──
    with capture(session_dir=tmp_path, ritual="gogogo", role="EXECUTOR_AGENT",
                 kind="agent_invocation", session_id=sid) as cap:
        cap.input("prompt.md", "implement step S1")
        cap.output("stdout.md", "files written: 2")
        cap.validation("validation.json", {"ok": True})
        cid_2 = cap.capture_id

    # ── Assertions ──
    store = CaptureStore(tmp_path)

    # 1. both captures finalized COMPLETED
    assert store.get_capture(cid_1)["status"] == "COMPLETED"
    assert store.get_capture(cid_2)["status"] == "COMPLETED"

    # 2. capture items recorded
    n1 = store.conn.execute(
        "SELECT COUNT(*) FROM capture_items WHERE capture_id=?", (cid_1,)
    ).fetchone()[0]
    assert n1 == 7  # prompt + context + template + stdout + stderr + raw + validation

    # 3. secret redacted on disk (search all blobs)
    blobs_root = tmp_path / "CAPTURE" / "blobs" / "sha256"
    leaked = False
    for blob in blobs_root.rglob("*"):
        if blob.is_file() and "real_token_abc123def456" in blob.read_text(
            encoding="utf-8", errors="ignore"
        ):
            leaked = True
            break
    assert not leaked, "Secret leaked into a blob — redaction failed before write"

    # 4. audit seq contiguous across 2 captures (start+complete × 2 = 4 events)
    audit = AuditWriter(store)
    chain = audit.read_chain(sid)
    seqs = [e["seq"] for e in chain]
    assert seqs == sorted(seqs)
    assert seqs == list(range(1, len(seqs) + 1))
    assert len(chain) >= 4

    # 5. chain verify
    ok, errs = audit.verify_chain(sid)
    assert ok, f"chain verify failed: {errs}"

    store.close()


def test_ulid_monotonic_same_process_same_millisecond():
    """Design §11: same-process ULID monotonic; cross-process NOT guaranteed."""
    # Generate 50 ids tight together — many will land in the same ms.
    ids = [new_capture_id() for _ in range(50)]
    assert ids == sorted(ids), "ULID not monotonic in same process"
    assert len(set(ids)) == 50, "ULID collision in same process"
    # ULID format: 26 chars Crockford base32
    for i in ids:
        assert len(i) == 26
        assert all(c in "0123456789ABCDEFGHJKMNPQRSTVWXYZ" for c in i)


def test_kernel_self_capture_via_optional_hook(tmp_path):
    """S6 acceptance: kernel.emit_context_built_capture is callable and creates a row."""
    from cli.core.kernel import Kernel
    k = Kernel(run_dir=tmp_path / "kernel_run")
    cid = k.emit_context_built_capture(
        session_dir=tmp_path,
        ritual="sss",
        context_sources=["operator.raw_intent", "session_manifest"],
    )
    assert cid is not None
    store = CaptureStore(tmp_path)
    row = store.get_capture(cid)
    assert row is not None
    assert row["role"] == "KERNEL"
    assert row["kind"] == "kernel_self_capture"
    assert row["status"] == "COMPLETED"
    store.close()


def test_kernel_self_capture_inert_default(tmp_path):
    """Hook MUST be no-op when session_dir=None."""
    from cli.core.kernel import Kernel
    k = Kernel(run_dir=tmp_path / "kernel_run")
    result = k.emit_context_built_capture(
        session_dir=None, ritual="sss", context_sources=[]
    )
    assert result is None
