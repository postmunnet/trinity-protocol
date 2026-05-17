"""Kernel HMAC primitive — Decision Y of spec 14 §6.1 Layer 3.

Provides the HMAC-SHA256 primitive (`compute_sig`, `verify_hmac`) and the
legacy 5-field envelope loader (`load_hmac_envelope`) used by trinity-tg-bot
v0.3.x. The shim:

- reads kernel-side secret from `TRINITY_KERNEL_HMAC_SECRET` env
- uses constant-time comparison (`hmac.compare_digest`)
- enforces an ISO-8601 timestamp skew window (default ±300s) to
  block replay
- returns `(ok: bool, reason: str)` — never raises on invalid input

This module is intentionally minimal and stdlib-only. It does NOT
wire itself into ddd / rrr / promote — that is a separate gating
decision; this shim just provides the verifier function.

## Boundary delegation (Article XV — Spec 9)

The full 7-step transport envelope boundary (envelope-shape, key resolution,
replay window, overscope, expiry) lives in `cli.core.transport`
(TRINITY_TRANSPORT_BOUNDARY_SPEC_V1 §4.5). This module remains as the
HMAC-SHA256 primitive used by `transport.compute_envelope_hmac()` and as the
backward-compat path for the legacy 5-field bot envelope (sig/ts/nonce/...)
emitted by tg-bot v0.3.x. New transports MUST use the 10-field envelope
shape and call `cli.core.transport.verify_envelope()` instead.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ENV_NAME = "TRINITY_KERNEL_HMAC_SECRET"
DEFAULT_MAX_SKEW_SECONDS = 300


def _load_secret(secret_env: str = ENV_NAME) -> Optional[str]:
    return os.environ.get(secret_env)


def _parse_ts(ts_iso: str) -> Optional[datetime]:
    if not ts_iso or not isinstance(ts_iso, str):
        return None
    try:
        # Accept "2026-05-02T01:00:00Z" or with timezone offset
        normalized = ts_iso.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, TypeError):
        return None


def compute_sig(payload_bytes: bytes, secret: str) -> str:
    """Compute hex-digest HMAC-SHA256 over payload_bytes."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def verify_hmac(
    payload_bytes: bytes,
    sig: str,
    ts_iso: str,
    *,
    secret_env: str = ENV_NAME,
    max_skew_seconds: int = DEFAULT_MAX_SKEW_SECONDS,
    now: Optional[datetime] = None,
) -> Tuple[bool, str]:
    """Verify HMAC sig + timestamp freshness.

    Returns (True, "ok") on success.
    Returns (False, reason) on failure where reason is one of:
      "no_secret"     — kernel env var missing/empty
      "bad_input"     — payload, sig, or ts missing or wrong type
      "malformed_ts"  — ts_iso not parseable as ISO-8601
      "ts_skew"       — abs(now - ts) > max_skew_seconds
      "sig_mismatch"  — HMAC verify failed (constant-time compare)
    Never raises on bad input.
    """
    secret = _load_secret(secret_env)
    if not secret:
        return False, "no_secret"

    if not isinstance(payload_bytes, (bytes, bytearray)):
        return False, "bad_input"
    if not isinstance(sig, str) or not sig:
        return False, "bad_input"
    if not isinstance(ts_iso, str) or not ts_iso:
        return False, "bad_input"

    parsed = _parse_ts(ts_iso)
    if parsed is None:
        return False, "malformed_ts"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    skew = abs((current - parsed).total_seconds())
    if skew > max_skew_seconds:
        return False, "ts_skew"

    expected = compute_sig(bytes(payload_bytes), secret)
    if not hmac.compare_digest(expected, sig):
        return False, "sig_mismatch"

    return True, "ok"


def load_hmac_envelope(
    path: Path,
) -> Tuple[Dict[str, Any], bytes, str, str]:
    """Parse envelope file → (envelope, canonical_payload_bytes, sig, ts_iso).

    Canonical payload bytes = JSON of envelope minus the `sig` field, serialized
    with `separators=(',', ':')`. Python 3.7+ preserves insertion order from the
    JSON parser, matching the bot's `JSON.stringify({session,command,args,ts,nonce[,user_id]})`
    byte-for-byte when the envelope on disk keeps the signing-side key order.

    Shared by ai ddd / ai gogogo / ai rrr. Raises ValueError on missing fields,
    json.JSONDecodeError on parse fail, OSError on read fail — callers are
    expected to translate those to a single `bad_envelope` reject reason.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("envelope must be a JSON object")
    sig = raw.get("sig")
    ts_iso = raw.get("ts")
    if not isinstance(sig, str) or not sig:
        raise ValueError("envelope missing 'sig' field")
    if not isinstance(ts_iso, str) or not ts_iso:
        raise ValueError("envelope missing 'ts' field")
    payload_dict = {k: v for k, v in raw.items() if k != "sig"}
    payload_bytes = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
    return raw, payload_bytes, sig, ts_iso


__all__ = [
    "ENV_NAME",
    "DEFAULT_MAX_SKEW_SECONDS",
    "compute_sig",
    "verify_hmac",
    "load_hmac_envelope",
]
