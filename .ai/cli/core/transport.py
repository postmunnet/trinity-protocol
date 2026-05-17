"""Transport organ — Article XV boundary (Spec 9, TRINITY_TRANSPORT_BOUNDARY_SPEC_V1).

This module is the kernel-side envelope-verification boundary. Transports
(trinity-tg-bot, notify-cli, future Slack/webhook/IDE bridges) deliver bytes;
this module decides whether the kernel accepts them as an Authority signal.

Article XV anchor: "Transport is not Authority." The transport carries the
envelope; the kernel decides. The 7-step pipeline below is the
operationalisation of that line.

Per spec §13 Out-of-scope: this module owns envelope-shape + replay +
overscope; the HMAC-SHA256 primitive lives in `core.auth` (imported, not
reimplemented). Key registry resolution is delegated to a caller-supplied
`key_loader` callable so that the actual registry can live behind Phase 14
Root of Trust without coupling this module to that schema.

Refusal codes (spec §5.1) and audit event names (spec §5.7 + §6.5) are
constants exported here so callers route them consistently into the audit
chain. Article XX: no self-trigger — emitting audit events is the caller's
job; this module only computes verdicts.
"""
from __future__ import annotations

import hmac as _hmac
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Protocol, Tuple

from .auth import compute_sig

# ─────────── Refusal codes (spec §5.1) ───────────

REFUSAL_UNSIGNED = "TRANSPORT_REFUSED_UNSIGNED"
REFUSAL_BADKEY = "TRANSPORT_REFUSED_BADKEY"
REFUSAL_REPLAY = "TRANSPORT_REFUSED_REPLAY"
REFUSAL_OVERSCOPE = "TRANSPORT_REFUSED_OVERSCOPE"

REFUSAL_CODES = frozenset(
    {REFUSAL_UNSIGNED, REFUSAL_BADKEY, REFUSAL_REPLAY, REFUSAL_OVERSCOPE}
)

# ─────────── Audit event names (spec §5.7 + §6.5) ───────────

EVENT_ACCEPTED = "transport.envelope_accepted"
EVENT_REFUSED_UNSIGNED = "transport.envelope_refused.unsigned"
EVENT_REFUSED_BADKEY = "transport.envelope_refused.badkey"
EVENT_REFUSED_REPLAY = "transport.envelope_refused.replay"
EVENT_REFUSED_OVERSCOPE = "transport.envelope_refused.overscope"

_REFUSAL_TO_EVENT = {
    REFUSAL_UNSIGNED: EVENT_REFUSED_UNSIGNED,
    REFUSAL_BADKEY: EVENT_REFUSED_BADKEY,
    REFUSAL_REPLAY: EVENT_REFUSED_REPLAY,
    REFUSAL_OVERSCOPE: EVENT_REFUSED_OVERSCOPE,
}

# ─────────── Pinned constants ───────────

HMAC_ALG_PIN = "HMAC-SHA256"
DEFAULT_EXPIRY_SKEW_SECONDS = 300
FORBIDDEN_ACTOR_CLASSES = frozenset({"kernel", "policy", "verifier"})
ALLOWED_ACTOR_CLASSES = frozenset({"human", "agent"})

_REQUIRED_FIELDS = (
    "envelope_id",
    "ts",
    "source_transport",
    "claimed_actor",
    "payload",
)


# ─────────── Caller-supplied protocols ───────────


class ReplayStore(Protocol):
    """Replay-window store interface; caller provides the implementation.

    Section 5.5: replay detection conflates envelope_id-seen and
    expires_ts-past into a single refusal code. The store is consulted in
    step 6 of verify_envelope.
    """

    def seen(self, envelope_id: str, issuer: str) -> bool: ...

    def mark(self, envelope_id: str, issuer: str) -> None: ...


KeyLoader = Callable[[str], Tuple[Optional[str], Optional[str]]]
"""Resolve a `key_id` to `(secret, issuer)`.

Spec §4.2: keys are issued by Authority organs, not by transports. The
loader returns `(None, None)` when the `key_id` is unknown — verify
maps that to REFUSAL_BADKEY.
"""


# ─────────── Pure helpers ───────────


def refusal_to_event(refusal_code: str) -> str:
    """Map a refusal-code constant to its audit event_type."""
    if refusal_code not in _REFUSAL_TO_EVENT:
        raise ValueError(f"unknown refusal code: {refusal_code!r}")
    return _REFUSAL_TO_EVENT[refusal_code]


def canonical_signed_bytes(envelope: Dict[str, Any]) -> bytes:
    """Canonical-JSON encoding of envelope minus the `hmac` field.

    Sort keys, no whitespace, utf-8 — matches spec §3.3 canonical encoding
    rule. The `hmac` field is excluded so verification can recompute the
    signature without circular dependency.
    """
    signed = {k: v for k, v in envelope.items() if k != "hmac"}
    return json.dumps(
        signed, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def compute_envelope_hmac(envelope: Dict[str, Any], secret: str) -> str:
    """Compute the HMAC-SHA256 hex digest for an envelope per spec §4.3."""
    return compute_sig(canonical_signed_bytes(envelope), secret)


def _parse_rfc3339(ts: str) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_mutating(envelope: Dict[str, Any]) -> bool:
    """A mutating envelope MUST carry hmac/hmac_alg/key_id (spec §3.1).

    Read-only envelopes may omit them. We infer mutation-ness from the
    presence of any of those fields — if any is present, all three are
    required.
    """
    return any(envelope.get(f) is not None for f in ("hmac", "hmac_alg", "key_id"))


# ─────────── 7-step verification pipeline (spec §4.5) ───────────


def verify_envelope(
    envelope: Dict[str, Any],
    *,
    key_loader: KeyLoader,
    replay_store: Optional[ReplayStore] = None,
    now: Optional[datetime] = None,
    expiry_skew_seconds: int = DEFAULT_EXPIRY_SKEW_SECONDS,
) -> Tuple[bool, Optional[str]]:
    """Verify a transport envelope per spec §4.5 seven-step pipeline.

    Returns (True, None) on success or (False, refusal_code) on failure
    where refusal_code is one of the REFUSAL_* constants. Caller is
    responsible for emitting the corresponding audit event (use
    refusal_to_event() on failure, or EVENT_ACCEPTED on success).

    Steps:
      1. Schema check  — required fields present, payload is a JSON object
      2. Algorithm     — hmac_alg == HMAC-SHA256
      3. Key resolve   — key_loader returns (secret, issuer)
      4. Class check   — claimed_actor.class allowed for issuer
      5. Signature     — HMAC over canonical-JSON minus hmac field
      6. Replay        — envelope_id not seen in issuer's window
      7. Expiry        — expires_ts (if present) not in past

    A read-only envelope (no hmac/hmac_alg/key_id) short-circuits at step 2
    after the schema check passes — replay/expiry still enforced if the
    fields are present.

    `now` injects a deterministic clock for testing; defaults to
    datetime.now(timezone.utc).
    """
    # Step 1 — Schema check
    if not isinstance(envelope, dict):
        return False, REFUSAL_UNSIGNED
    missing = [f for f in _REQUIRED_FIELDS if envelope.get(f) is None]
    if missing:
        return False, REFUSAL_UNSIGNED
    if not isinstance(envelope.get("payload"), dict):
        return False, REFUSAL_UNSIGNED

    actor = envelope["claimed_actor"]
    if not isinstance(actor, str) or actor.count(":") < 2:
        return False, REFUSAL_UNSIGNED
    actor_class = actor.split(":", 2)[0]

    # Spec §3.5 forbidden classes
    if actor_class in FORBIDDEN_ACTOR_CLASSES:
        return False, REFUSAL_OVERSCOPE
    if actor_class not in ALLOWED_ACTOR_CLASSES:
        return False, REFUSAL_OVERSCOPE

    mutating = _is_mutating(envelope)
    current = now or datetime.now(timezone.utc)

    # Read-only envelopes skip HMAC/key/sig but still respect replay+expiry
    if not mutating:
        # Step 6 — replay (read-only too — duplicate observation is a replay)
        if replay_store is not None and replay_store.seen(
            envelope["envelope_id"], "read-only"
        ):
            return False, REFUSAL_REPLAY
        # Step 7 — expiry
        expires_ts = envelope.get("expires_ts")
        if expires_ts is not None:
            expiry = _parse_rfc3339(expires_ts)
            if expiry is None:
                return False, REFUSAL_UNSIGNED
            if (current - expiry).total_seconds() > expiry_skew_seconds:
                return False, REFUSAL_REPLAY
        return True, None

    # Mutating envelope — must have hmac, hmac_alg, key_id all present
    for f in ("hmac", "hmac_alg", "key_id"):
        if not isinstance(envelope.get(f), str) or not envelope[f]:
            return False, REFUSAL_UNSIGNED
    hmac_value = envelope["hmac"]
    if not all(c in "0123456789abcdef" for c in hmac_value):
        return False, REFUSAL_UNSIGNED

    # Step 2 — Algorithm
    if envelope["hmac_alg"] != HMAC_ALG_PIN:
        return False, REFUSAL_BADKEY

    # Step 3 — Key resolution
    secret, issuer = key_loader(envelope["key_id"])
    if secret is None or issuer is None:
        return False, REFUSAL_BADKEY

    # Step 4 — Class consistency
    # The issuer is identified by Authority organ name. We don't hardcode
    # the issuer→class mapping here (key_loader is the authority); the
    # forbidden-class check at step 1 caught kernel/policy/verifier. The
    # remaining check: an `agent` envelope MUST resolve to a kernel-issued
    # key; a `human` envelope MUST resolve to a human-gate-issued key.
    # We delegate this validation to the key_loader by convention: it
    # returns issuer="" or None when the class doesn't match its scope.
    # For belt-and-suspenders, refuse if issuer is empty string.
    if not issuer:
        return False, REFUSAL_OVERSCOPE

    # Step 5 — Signature verify
    expected_hmac = compute_envelope_hmac(envelope, secret)
    if not _hmac.compare_digest(expected_hmac, hmac_value):
        return False, REFUSAL_BADKEY

    # Step 6 — Replay
    if replay_store is not None and replay_store.seen(
        envelope["envelope_id"], issuer
    ):
        return False, REFUSAL_REPLAY

    # Step 7 — Expiry
    expires_ts = envelope.get("expires_ts")
    if expires_ts is not None:
        expiry = _parse_rfc3339(expires_ts)
        if expiry is None:
            return False, REFUSAL_UNSIGNED
        if (current - expiry).total_seconds() > expiry_skew_seconds:
            return False, REFUSAL_REPLAY

    # All seven steps passed
    if replay_store is not None:
        replay_store.mark(envelope["envelope_id"], issuer)
    return True, None


__all__ = [
    "REFUSAL_UNSIGNED",
    "REFUSAL_BADKEY",
    "REFUSAL_REPLAY",
    "REFUSAL_OVERSCOPE",
    "REFUSAL_CODES",
    "EVENT_ACCEPTED",
    "EVENT_REFUSED_UNSIGNED",
    "EVENT_REFUSED_BADKEY",
    "EVENT_REFUSED_REPLAY",
    "EVENT_REFUSED_OVERSCOPE",
    "HMAC_ALG_PIN",
    "DEFAULT_EXPIRY_SKEW_SECONDS",
    "FORBIDDEN_ACTOR_CLASSES",
    "ALLOWED_ACTOR_CLASSES",
    "ReplayStore",
    "KeyLoader",
    "refusal_to_event",
    "canonical_signed_bytes",
    "compute_envelope_hmac",
    "verify_envelope",
]
