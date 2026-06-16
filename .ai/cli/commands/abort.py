"""ai abort — fire operator_abort (active state -> DEAD, decided_by=human).

ADR-0001 D3: a human may explicitly abort an active session to DEAD. The
transition is reasoned (``--reason`` is required) and audited. DEAD is a
terminal, irreversible state — once aborted, the session can only be sealed
with ``ai close``.

Authority: operator_abort is locked to ``decided_by='human'`` in the graph.
Running this command at the CLI is the human's explicit, present approval.
For remote operators, ``--hmac-envelope-file`` carries a tg-bot-signed
envelope: it is verified via the canonical core.auth (shared with ddd / gogogo
/ rrr) and, on success, the ``human:tg:<user_id>`` transport tag is stamped
into the audit evidence — the graph transition still fires with
``decided_by='human'`` (the graph contract is never amended for transport).

Mirrors the ddd command's session-resolution + HMAC + fire pattern.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import typer
from rich.console import Console

from ..core.audit import get_chain_for_project
from ..core.auth import load_hmac_envelope, verify_hmac
from ..core.loop import Loop, TerminalStateLocked, TransitionNotFound
from ..core.session_resolver import resolve_current_session
from ..core.ssot import SSOTLoader
from ..core.transport import EVENT_REFUSED_BADKEY

app = typer.Typer()
console = Console()

# Reject exit code shared with ddd / gogogo / rrr (Decision Y).
HMAC_REJECT_EXIT = 79

# States that have an operator_abort edge in the standard graph (the graph is
# the source of truth; this list is only used for the friendly error message).
_ABORTABLE = ("THINK", "SANDBOX", "DO", "VERIFIED")


def _verify_transport(
    hmac_envelope_file: Path, session_id: str, chain
) -> Optional[Dict[str, Any]]:
    """Verify a tg-bot HMAC envelope (mirror ddd). On success return the audit
    ``evidence_extra`` (carrying the ``decided_by_attr`` transport tag + via /
    hmac_ts / hmac_nonce). On a bad envelope or a failed signature, emit the
    rejection audit events (dual-emit per Article XV) and return None — the
    caller exits HMAC_REJECT_EXIT. The transport tag is audit metadata only;
    the graph transition keeps decided_by='human'."""
    try:
        envelope, payload_bytes, sig, ts_iso = load_hmac_envelope(hmac_envelope_file)
    except (ValueError, json.JSONDecodeError, OSError) as e:
        chain.append(
            "abort.hmac_rejected",
            {"session_id": session_id, "reason": "bad_envelope", "ts_iso": None, "detail": str(e)},
        )
        chain.append(
            EVENT_REFUSED_BADKEY,
            {
                "session_id": session_id,
                "source_transport": "tg-bot:legacy-5field",
                "claimed_actor": "human:tg:unknown",
                "reason": "bad_envelope",
                "detail": str(e),
            },
        )
        console.print(f"[red]abort.hmac_rejected: bad_envelope ({e})[/red]")
        return None

    ok, hmac_reason = verify_hmac(payload_bytes, sig, ts_iso)
    if not ok:
        chain.append(
            "abort.hmac_rejected",
            {
                "session_id": session_id,
                "reason": hmac_reason,
                "ts_iso": ts_iso,
                "envelope_keys": sorted(list(envelope.keys())),
            },
        )
        chain.append(
            EVENT_REFUSED_BADKEY,
            {
                "session_id": session_id,
                "source_transport": "tg-bot:legacy-5field",
                "claimed_actor": f"human:tg:{envelope.get('user_id', 'bot')}",
                "reason": hmac_reason,
                "ts_iso": ts_iso,
            },
        )
        console.print(f"[red]abort.hmac_rejected: {hmac_reason}[/red]")
        return None

    user_id = envelope.get("user_id")
    decided_by_attr = f"human:tg:{user_id}" if user_id is not None else "human:tg:bot"
    return {
        "decided_by_attr": decided_by_attr,
        "via": "tg-bot:hmac",
        "hmac_ts": ts_iso,
        "hmac_nonce": envelope.get("nonce"),
    }


def _abort(
    session_path: Path,
    project_root: Path,
    reason: str,
    evidence_extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Fire operator_abort (active -> DEAD, decided_by=human). Returns the new
    graph state. Raises TransitionNotFound if the current state has no
    operator_abort edge, or TerminalStateLocked if the session is already in a
    terminal state (DONE/DEAD) — in both cases the session is not abortable."""
    loop = Loop(session_path, graph_name="standard", project_root=project_root)
    evidence = {"reason": reason, "source": "cli", **(evidence_extra or {})}
    return loop.fire("operator_abort", decided_by="human", evidence=evidence)


def _run(*, reason: str, hmac_envelope_file: Optional[Path] = None) -> int:
    config = SSOTLoader(Path.cwd()).load()
    session_path = resolve_current_session(config)

    evidence_extra: Optional[Dict[str, Any]] = None
    if hmac_envelope_file is not None:
        chain = get_chain_for_project(config.project_root)
        evidence_extra = _verify_transport(hmac_envelope_file, session_path.name, chain)
        if evidence_extra is None:
            return HMAC_REJECT_EXIT

    cur = Loop(
        session_path, graph_name="standard", project_root=config.project_root
    ).current()
    try:
        new_state = _abort(session_path, config.project_root, reason, evidence_extra)
    except (TransitionNotFound, TerminalStateLocked):
        console.print(
            f"[red]not abortable from {cur!r} — operator_abort is only valid "
            f"from active states ({'/'.join(_ABORTABLE)}); terminal states "
            f"(DONE/DEAD) cannot be aborted.[/red]"
        )
        return 2

    tag = (evidence_extra or {}).get("decided_by_attr", "human")
    console.print(
        f"[yellow]Session aborted: {cur} -> {new_state} "
        f"(operator_abort, decided_by={tag}). Reason: {reason}[/yellow]\n"
        f"[dim]DEAD is terminal — seal it with `ai close`.[/dim]"
    )
    return 0


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    reason: str = typer.Option(
        ...,
        "--reason",
        help="Why the session is being aborted (required; recorded in the audit chain).",
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from a remote transport (tg-bot). Verified via "
        "core.auth.verify_hmac; on success stamps decided_by=human:tg:<user_id> "
        "in the audit evidence; on failure emits abort.hmac_rejected and exits 79.",
    ),
) -> None:
    """Abort the current session: fire operator_abort -> DEAD (decided_by=human)."""
    if ctx.invoked_subcommand is not None:
        return
    raise typer.Exit(_run(reason=reason, hmac_envelope_file=hmac_envelope_file))
