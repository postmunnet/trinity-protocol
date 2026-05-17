"""Tests for recordproxy.redaction — v1 pattern set + break-glass.

Acceptance A12 (amended 2026-05-13): default mode redacts; TRINITY_RECORDPROXY_RAW=1
preserves raw; break-glass path identifiable via redact_with_metadata mode
'RAW_BREAK_GLASS' or via this file containing the literal 'break_glass'.
"""

import os
import pytest

from cli.core.recordproxy.redaction import (
    redact,
    redact_with_metadata,
    RAW_BREAK_GLASS_ENV,
)
from cli.core.recordproxy.schemas import (
    REDACTION_MODE_DEFAULT,
    REDACTION_MODE_BREAK_GLASS,
)

FAKE_GITHUB_TOKEN = "ghp_" + "1234567890abcdefghijklmnopqrstuvwxyz"
FAKE_SLACK_TOKEN = "xoxb-" + "1111111111" + "-2222222222-" + "AbCdEfGhIjKl"


# ─── v1 pattern set (pinned) ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,must_not_contain",
    [
        ("Authorization: Bearer abc.def.ghi.long.token", "abc.def.ghi.long.token"),
        ("Authorization:  Bearer  eyJhbGciOiJIUzI1NiJ9.x.y", "eyJhbGciOiJIUzI1NiJ9.x.y"),
        ("AKIA" + "ABCDEFGHIJKLMNOP", "AKIA" + "ABCDEFGHIJKLMNOP"),
        (FAKE_GITHUB_TOKEN, FAKE_GITHUB_TOKEN),
        (FAKE_SLACK_TOKEN, FAKE_SLACK_TOKEN),
        ('api_key = "supersecretvalue1234"', "supersecretvalue1234"),
        ("DATABASE_SECRET=verysecret123\n", "verysecret123"),
        ("postgres://user:p@ssw0rd@host:5432/db", "p@ssw0rd"),
        ("Cookie: session=abcd1234efgh5678", "abcd1234efgh5678"),
    ],
)
def test_default_mode_redacts_v1_patterns(raw, must_not_contain, monkeypatch):
    monkeypatch.delenv(RAW_BREAK_GLASS_ENV, raising=False)
    out = redact(raw)
    assert must_not_contain not in out, f"Secret leaked through redaction: {out!r}"


def test_pem_private_key_redacted(monkeypatch):
    monkeypatch.delenv(RAW_BREAK_GLASS_ENV, raising=False)
    raw = (
        "-----BEGIN RSA " + "PRIVATE KEY-----\n"
        "MIIEpAIBAAKCAQEAabcd1234secret\n"
        "-----END RSA " + "PRIVATE KEY-----\n"
    )
    out = redact(raw)
    assert "MIIEpAIBAAKCAQEAabcd1234secret" not in out


def test_default_metadata_shape(monkeypatch):
    monkeypatch.delenv(RAW_BREAK_GLASS_ENV, raising=False)
    text, meta = redact_with_metadata("Authorization: Bearer abc.def.ghi.token")
    assert meta["mode"] == REDACTION_MODE_DEFAULT
    assert meta["redacted_count"] >= 1
    assert "bearer_token" in meta["applied_rules"]


# ─── break_glass behavior (A12 acceptance literal) ────────────────────────────


def test_break_glass_preserves_raw_when_explicit_env_set(monkeypatch):
    monkeypatch.setenv(RAW_BREAK_GLASS_ENV, "1")
    raw = "Authorization: Bearer the_actual_secret_value"
    out = redact(raw)
    assert "the_actual_secret_value" in out


def test_break_glass_metadata_identifies_RAW_BREAK_GLASS_mode(monkeypatch):
    monkeypatch.setenv(RAW_BREAK_GLASS_ENV, "1")
    text, meta = redact_with_metadata("Authorization: Bearer abc.def.ghi")
    assert meta["mode"] == REDACTION_MODE_BREAK_GLASS
    assert meta["applied_rules"] == []
    assert meta["redacted_count"] == 0


def test_break_glass_default_off_when_env_unset(monkeypatch):
    monkeypatch.delenv(RAW_BREAK_GLASS_ENV, raising=False)
    text, meta = redact_with_metadata("Authorization: Bearer abc.def.ghi")
    assert meta["mode"] == REDACTION_MODE_DEFAULT
    assert "abc.def.ghi" not in text


def test_break_glass_value_must_be_exactly_one(monkeypatch):
    """break-glass must require explicit '1'; truthy-ish '0'/'true'/'yes' do not flip."""
    for bad in ["0", "true", "yes", "TRUE", "", "false"]:
        monkeypatch.setenv(RAW_BREAK_GLASS_ENV, bad)
        text, meta = redact_with_metadata("Authorization: Bearer secret_abc_def_ghi")
        assert meta["mode"] == REDACTION_MODE_DEFAULT, f"break-glass leaked with env={bad!r}"
        assert "secret_abc_def_ghi" not in text


def test_redact_no_op_on_clean_text(monkeypatch):
    monkeypatch.delenv(RAW_BREAK_GLASS_ENV, raising=False)
    raw = "Just a normal log line with no secrets."
    assert redact(raw) == raw
