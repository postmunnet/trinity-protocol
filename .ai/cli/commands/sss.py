"""sss ritual — library module for pack-honoring session initialization.

The sss ritual is physically split across two existing kernel code paths:

1. ``cli.commands.session.new`` (`ai session new <task>`) — creates the
   session directory tree and emits the pack-declared ``session.created``
   audit event.
2. ``cli.commands.vvv._run`` (line ~91, the READY auto-advance branch) —
   fires the READY → THINK transition via ``loop.fire("sss", ...)``.

Per RC v1.1-rc Article XII.5, both sites must honor the same template pack
at ``.ai/rituals/sss/``. To avoid duplicating pack loading + guard +
audit-emission logic at two sites, this module exposes two small library
functions that both call sites delegate to:

- :func:`emit_session_created` — for the dir-creation half (session.py)
- :func:`fire_sss_transition`  — for the transition-fire half (vvv.py)

Together they emit *exactly* the audit event set the sss pack declares
(``sss.invoked``, ``session.created``).

Authority:
  - Constitution v1.0 Article IV (Separation: single pack-honoring site)
  - Constitution v1.0 Article XX (Passive Core: guard before mutation)
  - Constitution v1.0 Article XXIX (Amendment: arrives via plan.amended)
  - Ritual Constitution v1.1-rc Article XII.5 (empirical ratification)

This module is *library only* — it deliberately does NOT register a typer
app, so the user-facing CLI surface (``ai session new``) is unchanged.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ..core.audit import AuditChain
from ..core.loop import Loop
from ..core.ritual_pack_loader import (
    assert_transition_allowed,
    load_pack,
    required_audit_events,
)


SSS_RITUAL = "sss"
SSS_NEXT_STATE = "THINK"
SSS_EVENT_INVOKED = "sss.invoked"
SSS_EVENT_SESSION_CREATED = "session.created"


class PackEventDriftError(RuntimeError):
    """Raised when the sss pack does not declare an event the code emits."""


def _rituals_root_from_chain(chain: AuditChain):
    """Resolve <project_root>/.ai/rituals from a chain whose path is
    ``<project_root>/.ai/audit/events.ndjson``. Avoids relying on cwd so
    tests that chdir to a tmp project still find the rituals tree.
    """
    return chain.path.parent.parent / "rituals"


def emit_session_created(
    chain: AuditChain,
    *,
    session_id: str,
    name: str,
    session_path_relative: str,
) -> Dict[str, Any]:
    """Emit the pack-declared ``session.created`` event.

    Loads the sss pack first to validate the event is declared (drift guard:
    if pack and code disagree, raise rather than silently emit). Returns the
    appended audit event dict (with ``hash`` and ``prev_hash`` populated).

    Used by :func:`cli.commands.session.new` at dir-creation time.
    """
    pack = load_pack(SSS_RITUAL, rituals_root=_rituals_root_from_chain(chain))
    declared = required_audit_events(pack)
    if SSS_EVENT_SESSION_CREATED not in declared:
        raise PackEventDriftError(
            f"sss pack does not declare {SSS_EVENT_SESSION_CREATED!r}; "
            f"declared events: {declared!r}"
        )
    return chain.append(
        SSS_EVENT_SESSION_CREATED,
        {
            "session_id": session_id,
            "name": name,
            "session_path": session_path_relative,
        },
    )


def fire_sss_transition(
    loop: Loop,
    *,
    session_id: str,
    decided_by: str = "kernel",
    evidence: Optional[Dict[str, Any]] = None,
) -> str:
    """Fire the READY → THINK transition per the sss pack contract.

    Sequence (Article XX — guard before any state mutation):

      1. ``load_pack("sss")``
      2. ``assert_transition_allowed(pack, current, "THINK")``  ← guard
      3. ``chain.append("sss.invoked", ...)``                   ← pack event
      4. ``loop.fire("sss", ...)``                              ← state mutation
                                                                  (Loop appends
                                                                  its own
                                                                  ``graph.transition``
                                                                  event)

    Returns the new graph state (always ``"THINK"`` for the happy path).

    Raises :class:`cli.core.ritual_pack_loader.StateTransitionError` if the
    current state is not in the pack's ``allowed_current_states``. The raise
    happens *before* any audit append or state mutation, satisfying the
    passive-core invariant.

    Used by :func:`cli.commands.vvv._run` in its READY auto-advance branch.
    """
    pack = load_pack(
        SSS_RITUAL,
        rituals_root=loop.project_root / ".ai" / "rituals",
    )
    declared = required_audit_events(pack)
    if SSS_EVENT_INVOKED not in declared:
        raise PackEventDriftError(
            f"sss pack does not declare {SSS_EVENT_INVOKED!r}; "
            f"declared events: {declared!r}"
        )

    current = loop.current()
    # Article XX guard — must run BEFORE any state-mutating call.
    assert_transition_allowed(pack, current, SSS_NEXT_STATE)

    loop.chain.append(
        SSS_EVENT_INVOKED,
        {
            "session_id": session_id,
            "graph_state": current,
            "decided_by": decided_by,
            "evidence": evidence or {},
        },
    )
    return loop.fire(SSS_RITUAL, decided_by=decided_by, evidence=evidence)


__all__ = [
    "SSS_RITUAL",
    "SSS_NEXT_STATE",
    "SSS_EVENT_INVOKED",
    "SSS_EVENT_SESSION_CREATED",
    "PackEventDriftError",
    "emit_session_created",
    "fire_sss_transition",
    "app",
]


# ---------------------------------------------------------------------------
# CLI surface (added 2026-05-14 to close command-contract drift)
#
# The library half above stays the canonical implementation. The Typer app
# below is a thin alias so `ai sss "<task>"` works as the ritual language
# expects, instead of forcing users (and AI agents) to translate to
# `ai session new "<task>"`.
#
# The alias delegates to session.new — no session-creation logic is
# duplicated here.
# ---------------------------------------------------------------------------
import typer  # noqa: E402

app = typer.Typer(
    help="Start a Trinity session via the sss ritual (alias of `ai session new`).",
    invoke_without_command=True,
)


def _git_pull_preflight() -> None:
    """Auto-sync with origin/main before sss scaffolds a new session.

    Per the SSOT doctrine (Q4 = pull on sss only), session start is the
    canonical sync boundary between Mac and VPS working copies. All error
    paths are fail-soft so sss continues to work offline, in non-git
    workspaces, and when conflicts exist.

    Guards (in order):
      1. TRINITY_SKIP_PULL=1 env → silent skip (operator opt-out)
      2. No `.git/` in cwd or ancestors → silent skip (not a git clone)
      3. git binary missing → one-line note · skip
      4. fetch fails (network / timeout) → warning · skip pull
      5. pull --ff-only fails (conflict) → warning · proceed to scaffold

    Output goes to stderr (matches the existing typer.echo pattern in
    this file) so it does not pollute structured stdout. Timeout 5s.
    """
    import os
    import subprocess

    if os.environ.get("TRINITY_SKIP_PULL") == "1":
        return

    cwd = Path.cwd()
    if not any((p / ".git").exists() for p in [cwd, *cwd.parents]):
        return

    try:
        fetch = subprocess.run(
            ["git", "fetch", "origin", "main"],
            capture_output=True, text=True, timeout=5,
        )
        if fetch.returncode != 0:
            typer.echo(
                f"[sss] git fetch skipped (offline?): "
                f"{fetch.stderr.strip()[:200]}",
                err=True,
            )
            return

        pull = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            capture_output=True, text=True, timeout=5,
        )
        if pull.returncode == 0:
            out = pull.stdout.strip()
            if "Already up to date" in out:
                typer.echo("[sss] origin/main: already up to date", err=True)
            else:
                last = out.splitlines()[-1] if out else "fast-forwarded"
                typer.echo(f"[sss] pulled origin/main: {last[:200]}", err=True)
        else:
            typer.echo(
                f"[sss] git pull --ff-only failed (conflict? "
                f"proceeding): {pull.stderr.strip()[:200]}",
                err=True,
            )
    except subprocess.TimeoutExpired:
        typer.echo("[sss] git preflight timeout (5s) · proceeding", err=True)
    except FileNotFoundError:
        typer.echo("[sss] git binary missing · skipped", err=True)
    except Exception as e:
        typer.echo(
            f"[sss] git preflight error ({type(e).__name__}) · proceeding",
            err=True,
        )


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    task: str = typer.Argument(
        None,
        help="Task / session name. Required unless invoking a subcommand.",
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport. When present, kernel "
        "verifies HMAC before opening the session; on failure emits "
        "sss.hmac_rejected and exits 79.",
    ),
):
    """Alias for `ai session new <task>`.

    `sss` is the ritual name; the canonical Typer command lives at
    `cli.commands.session.new`. This callback forwards to it so the
    ritual language and the executable CLI agree.
    """
    if ctx.invoked_subcommand is not None:
        return
    if task is None:
        typer.echo(
            "Usage: ai sss '<task name>'\n\n"
            "Alias for: ai session new '<task name>'",
            err=True,
        )
        raise typer.Exit(code=2)
    if hmac_envelope_file is not None:
        # Project-level HMAC enforcement before sss opens a new session.
        # sss has no pre-existing session_id; use the task slug as the
        # claimed_actor evidence key.
        from ..core.audit import get_chain_for_project
        from ..core.hmac_gate import enforce_hmac_or_exit
        from ..core.ssot import SSOTLoader
        config = SSOTLoader(Path.cwd()).load()
        chain = get_chain_for_project(config.project_root)
        enforce_hmac_or_exit(
            hmac_envelope_file=hmac_envelope_file,
            chain=chain,
            ritual="sss",
            session_id=f"pending:{task}",
        )
    # SSOT preflight (Q4 doctrine) — sync with origin/main before
    # scaffolding. All git error paths are fail-soft; sss must keep
    # working offline / in non-git workspaces / under conflicts.
    _git_pull_preflight()

    # Lazy-import to avoid any import-time cycle with session.py
    from . import session as session_cmd

    session_cmd.new(task)
