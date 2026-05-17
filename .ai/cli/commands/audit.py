"""`ai audit` — replay + verify-chain commands.

Per TRINITY_AUDIT_EVENT_SPEC_V1 §4-§5. READ-ONLY (Article XX Passive Core).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.ssot import SSOTLoader

app = typer.Typer(help="Inspect audit chains (read-only).")
console = Console()


@app.callback()
def callback():
    """Audit chain inspection — replay + verify-chain."""
    pass


def _project_root(start: Path) -> Path:
    """Detect project root by walking upward to a folder containing .ai/ssot.yaml.

    Used instead of raw ``Path.cwd()`` because the kernel wrapper script
    (``.ai/cli/ai``) cd's into ``.ai/`` before invoking ``python -m cli.main``;
    a raw ``Path.cwd()`` would then prepend ``.ai/`` a second time, producing
    paths like ``<repo>/.ai/.ai/audit/events.ndjson``.

    ``SSOTLoader.__init__`` runs the walk-up at construction time and stashes
    the result on ``.project_root``; we deliberately do NOT call ``.load()``
    so test fixtures lacking a real ``ssot.yaml`` (e.g. CliRunner's
    isolated_filesystem) don't trip on a missing-SSOT exception.
    """
    return SSOTLoader(start).project_root


def _resolve_chain_source(
    session: Optional[str],
    legacy_ndjson: Optional[Path],
) -> tuple[str, Path]:
    """Return (chain_kind, path). 'session' or 'legacy'."""
    if legacy_ndjson is not None:
        return "legacy", legacy_ndjson
    repo_root = _project_root(Path.cwd())
    if session is None:
        # Default to legacy global ndjson.
        return "legacy", repo_root / ".ai" / "audit" / "events.ndjson"
    # Resolve session directory: look under .ai/sessions/<session>/CAPTURE/capture.sqlite
    sess_dir = repo_root / ".ai" / "sessions" / session
    if not sess_dir.is_dir():
        # Also look in archive.
        archive_dir = repo_root / ".ai" / "sessions" / "archive" / f"{session}.archive"
        if archive_dir.is_dir():
            sess_dir = archive_dir
    sqlite_path = sess_dir / "CAPTURE" / "capture.sqlite"
    return "session", sqlite_path


@app.command()
def replay(
    session: Optional[str] = typer.Option(None, "--session", help="Session ID (per-session SQLite mode)"),
    from_seq: Optional[int] = typer.Option(None, "--from", help="Start seq (per-session) / start line (legacy)"),
    to_seq: Optional[int] = typer.Option(None, "--to", help="End seq / end line"),
    event_type: Optional[str] = typer.Option(None, "--event-type", help="Filter to a single event_type"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Print events; do NOT mutate state (default)"),
    legacy_ndjson: Optional[Path] = typer.Option(None, "--legacy-ndjson", help="Use a specific ndjson file instead of per-session SQLite"),
    strict: bool = typer.Option(False, "--strict", help="Additionally validate event_type against canonical registry"),
):
    """Walk audit chain events and validate each one.

    Exits 0 (chain valid), 1 (schema violation or unknown event_type),
    or 2 (hash chain broken).
    """
    from ..core import audit_replay

    chain_kind, source_path = _resolve_chain_source(session, legacy_ndjson)
    if not source_path.is_file():
        console.print(f"[red]Source not found:[/red] {source_path}")
        raise typer.Exit(1)

    if chain_kind == "session":
        events = audit_replay.read_session_chain(source_path)
    else:
        events = audit_replay.read_legacy_ndjson(source_path)

    filtered = list(audit_replay.iter_events_filtered(
        events,
        from_seq=from_seq,
        to_seq=to_seq,
        event_type=event_type,
        session=session if chain_kind == "legacy" else None,
    ))

    table = Table(title=f"audit replay ({chain_kind})")
    table.add_column("seq/idx", justify="right")
    table.add_column("event_type")
    table.add_column("session_id")
    table.add_column("hash", style="dim")
    for idx, row in enumerate(filtered):
        seq = row.get("seq", idx)
        et = row.get("event_type") or row.get("type", "?")
        sid = (row.get("session_id")
               or (row.get("details") or {}).get("session_id", "")
               or "")
        h = (row.get("hash") or "")[:12]
        table.add_row(str(seq), et, sid[:48], h + ("…" if h else ""))
    console.print(table)

    ok, errors = audit_replay.verify_chain(filtered, strict=strict, chain_kind=chain_kind)
    if not ok:
        for e in errors:
            console.print(f"[red]✗[/red] {e}")
        exit_code = audit_replay.classify_verify_errors(errors)
        raise typer.Exit(exit_code)
    console.print(f"[green]✓ chain valid ({len(filtered)} events)[/green]")
    raise typer.Exit(audit_replay.EXIT_OK)


@app.command(name="verify-chain")
def verify_chain_cmd(
    session: Optional[str] = typer.Option(None, "--session", help="Session ID (per-session SQLite mode)"),
    strict: bool = typer.Option(False, "--strict", help="Validate event_type against canonical registry"),
    from_seq: Optional[int] = typer.Option(None, "--from", help="Start seq / start line"),
    legacy_ndjson: Optional[Path] = typer.Option(None, "--legacy-ndjson", help="Use specific ndjson file instead of per-session SQLite"),
):
    """Validate prev_hash linkage + SHA-256 recomputation across the chain.

    Read-only. Exits 0 (chain valid) or 2 (chain broken).
    """
    from ..core import audit_replay

    chain_kind, source_path = _resolve_chain_source(session, legacy_ndjson)
    if not source_path.is_file():
        console.print(f"[red]Source not found:[/red] {source_path}")
        raise typer.Exit(audit_replay.EXIT_CHAIN_BROKEN)

    if chain_kind == "session":
        events = audit_replay.read_session_chain(source_path)
    else:
        events = audit_replay.read_legacy_ndjson(source_path)

    if from_seq is not None:
        events = list(audit_replay.iter_events_filtered(events, from_seq=from_seq))

    ok, errors = audit_replay.verify_chain(events, strict=strict, chain_kind=chain_kind)
    if ok:
        console.print(
            f"[green]✓ chain valid ({len(events)} events, kind={chain_kind})[/green]"
        )
        raise typer.Exit(audit_replay.EXIT_OK)

    # Report first broken link + count
    first_err = errors[0] if errors else "unknown"
    console.print(f"[red]✗ chain broken:[/red] {first_err}")
    if len(errors) > 1:
        console.print(f"   ({len(errors) - 1} more issues)")
    raise typer.Exit(audit_replay.classify_verify_errors(errors))


from .audit_metrics import metrics as _metrics_cmd  # noqa: E402

app.command(name="metrics")(_metrics_cmd)


__all__ = ["app"]
