"""Phase 14 — root_of_trust_helper tests."""
from __future__ import annotations

import hashlib
import importlib
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cli.core.root_of_trust_helper import (
    append_ratification,
    compute_layer0_sha256,
    make_genesis_manifest,
    make_layer0_entry,
    verify_layer0_against_manifest,
)

_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def test_module_import_has_no_side_effects() -> None:
    mod = importlib.import_module("cli.core.root_of_trust_helper")
    assert hasattr(mod, "make_genesis_manifest")


# ─── A2 sha256 ──────────────────────────────────────────────────────


def test_compute_layer0_sha256_matches_hashlib(tmp_path: Path) -> None:
    f = tmp_path / "doc.md"
    payload = b"hello trinity\n"
    f.write_bytes(payload)
    assert compute_layer0_sha256(f) == hashlib.sha256(payload).hexdigest()


# ─── A3 make_layer0_entry ───────────────────────────────────────────


def test_make_layer0_entry_builds_dict(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    f = tmp_path / "docs" / "C.md"
    f.write_text("constitution\n")
    e = make_layer0_entry(
        path="docs/C.md",
        role="constitution",
        authority_class="founder",
        project_root=tmp_path,
    )
    assert e["path"] == "docs/C.md"
    assert e["role"] == "constitution"
    assert e["authority_class"] == "founder"
    assert e["sha256"] == hashlib.sha256(b"constitution\n").hexdigest()


def test_make_layer0_entry_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        make_layer0_entry(
            path="missing.md",
            role="x",
            authority_class="founder",
            project_root=tmp_path,
        )


# ─── A4 genesis manifest defaults ───────────────────────────────────


def test_make_genesis_manifest_defaults_tier_1_hmac() -> None:
    m = make_genesis_manifest(asserted_by="operator:test", layer_0_artifacts=[])
    cs = m["crypto_status"]
    assert cs["tier"] == "tier_1_hmac"
    assert cs["algorithm"] == "none"
    assert cs["key_id"] is None
    assert cs["verified_at"] is None
    assert m["ratification_chain"] == []
    assert m["asserted_at"].endswith("Z")


# ─── A5 verify happy path ───────────────────────────────────────────


def test_verify_layer0_against_manifest_all_match(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "A.md").write_text("alpha")
    (tmp_path / "docs" / "B.md").write_text("beta")
    m = make_genesis_manifest(
        asserted_by="op",
        layer_0_artifacts=[
            make_layer0_entry(path="docs/A.md", role="r1", authority_class="founder", project_root=tmp_path),
            make_layer0_entry(path="docs/B.md", role="r2", authority_class="founder", project_root=tmp_path),
        ],
    )
    results = verify_layer0_against_manifest(tmp_path, m)
    assert all(r["ok"] for r in results)
    assert len(results) == 2


# ─── A6 verify tamper ───────────────────────────────────────────────


def test_verify_flags_tampered_file(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    f = tmp_path / "docs" / "A.md"
    f.write_text("alpha")
    m = make_genesis_manifest(
        asserted_by="op",
        layer_0_artifacts=[
            make_layer0_entry(path="docs/A.md", role="r", authority_class="founder", project_root=tmp_path),
        ],
    )
    f.write_text("alpha tampered")
    results = verify_layer0_against_manifest(tmp_path, m)
    assert len(results) == 1
    assert results[0]["ok"] is False
    assert results[0]["expected"] != results[0]["actual"]


def test_verify_flags_missing_file(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    f = tmp_path / "docs" / "A.md"
    f.write_text("x")
    m = make_genesis_manifest(
        asserted_by="op",
        layer_0_artifacts=[
            make_layer0_entry(path="docs/A.md", role="r", authority_class="founder", project_root=tmp_path),
        ],
    )
    f.unlink()
    results = verify_layer0_against_manifest(tmp_path, m)
    assert results[0]["ok"] is False
    assert results[0]["actual"] is None


# ─── A7 append_ratification ─────────────────────────────────────────


def test_append_ratification_grows_chain() -> None:
    m = make_genesis_manifest(asserted_by="op", layer_0_artifacts=[])
    m2, art = append_ratification(
        m,
        ratified_by="operator:test",
        constitutional_articles_invoked=["XXIX"],
        evidence_refs=[".ai/audit/events.ndjson#L1"],
    )
    assert len(m2["ratification_chain"]) == 1
    rid = m2["ratification_chain"][0]
    assert rid.startswith("rat_")
    assert _ULID_RE.match(rid.replace("rat_", "").replace("genesis_", ""))
    # artifact mirrors
    assert art["ratification_id"] == rid
    assert art["ratified_by"] == "operator:test"
    assert art["constitutional_articles_invoked"] == ["XXIX"]


# ─── A8 genesis ratification id format ──────────────────────────────


def test_append_genesis_ratification_id_format() -> None:
    m = make_genesis_manifest(asserted_by="op", layer_0_artifacts=[])
    m2, art = append_ratification(
        m,
        ratified_by="op",
        constitutional_articles_invoked=["XXIX"],
        is_genesis=True,
    )
    assert art["ratification_id"].startswith("rat_genesis_")
    body = art["ratification_id"].replace("rat_genesis_", "")
    assert _ULID_RE.match(body)
