"""HMAC gate — shared ritual-entry transport verification.

Extracts the reject pattern duplicated in gogogo/ddd/rrr (Spec 14 §6.1
Layer 3 / Decision Y / R35) so the remaining ritual entries
(sss/vvv/nnn/close) can call a single helper instead of copying 30
lines per command.

The gate is a pure dispatcher: it does NOT decide policy, only enforces
the transport-layer envelope contract. Article XV — transport may carry
evidence; it may NOT approve the underlying gate.

Article XX: no I/O at import. The audit emission only happens when the
caller passes a non-None `hmac_envelope_file`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from rich.console import Console

from cli.core.audit import AuditChain
from cli.core.auth import load_hmac_envelope, verify_hmac


HMAC_REJECT_EXIT: int = 79

_console = Console()


def _append_reject(
    chain: AuditChain,
    *,
    ritual: str,
    session_id: str,
    reason: str,
    ts_iso: Optional[str],
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    details: Dict[str, Any] = {
        "session_id": session_id,
        "reason": reason,
        "ts_iso": ts_iso,
    }
    if extra:
        details.update(extra)
    chain.append(f"{ritual}.hmac_rejected", details)


def enforce_hmac_or_exit(
    *,
    hmac_envelope_file: Optional[Path],
    chain: AuditChain,
    ritual: str,
    session_id: str,
) -> Optional[Dict[str, Any]]:
    """Verify an HMAC envelope or exit 79 with an audit row.

    Args:
        hmac_envelope_file: path to an HMAC envelope JSON, or None to bypass.
        chain: audit chain for reject-row emission.
        ritual: ritual short-code ("sss"/"vvv"/"nnn"/"close"/...). Used
            in the audit event_type as `<ritual>.hmac_rejected`.
        session_id: parent session id (chain row detail).

    Returns:
        None when `hmac_envelope_file is None` (back-compat bypass).
        On success: a transport evidence dict (`via`, `hmac_ts`,
        `hmac_nonce`, `hmac_user_id`) for the caller to record.

    Raises:
        typer.Exit(HMAC_REJECT_EXIT) on bad envelope or signature mismatch.
    """
    if hmac_envelope_file is None:
        return None

    try:
        envelope, payload_bytes, sig, ts_iso = load_hmac_envelope(
            hmac_envelope_file
        )
    except (ValueError, json.JSONDecodeError, OSError) as e:
        _append_reject(
            chain,
            ritual=ritual,
            session_id=session_id,
            reason="bad_envelope",
            ts_iso=None,
            extra={"detail": str(e)},
        )
        _console.print(f"[red]{ritual}.hmac_rejected: bad_envelope ({e})[/red]")
        raise typer.Exit(HMAC_REJECT_EXIT)

    ok, reason = verify_hmac(payload_bytes, sig, ts_iso)
    if not ok:
        _append_reject(
            chain,
            ritual=ritual,
            session_id=session_id,
            reason=reason,
            ts_iso=ts_iso,
            extra={"envelope_keys": sorted(list(envelope.keys()))},
        )
        _console.print(f"[red]{ritual}.hmac_rejected: {reason}[/red]")
        raise typer.Exit(HMAC_REJECT_EXIT)

    return {
        "via": "tg-bot:hmac",
        "hmac_ts": ts_iso,
        "hmac_nonce": envelope.get("nonce"),
        "hmac_user_id": envelope.get("user_id"),
    }


__all__ = ["HMAC_REJECT_EXIT", "enforce_hmac_or_exit"]
