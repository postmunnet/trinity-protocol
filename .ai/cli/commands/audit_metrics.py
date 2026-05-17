"""`ai audit metrics` — derive gate-wait latency from the audit chain.

Read-only over `.ai/audit/events.ndjson` (Article XX Passive Core).
Closes the Spec 14 §11 quantitative-ROI gap (Cognitive Bottleneck #1).
The join + percentile primitives live in `cli.core.audit_metrics`; this
module is the CLI surface only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..core import audit_metrics as core
from ..core.ssot import SSOTLoader

console = Console()


def _project_root(start: Path) -> Path:
    """Same walk-up as `audit.py` — avoids double-`.ai/` path doubling."""
    return SSOTLoader(start).project_root


def metrics(
    window: str = typer.Option("24h", "--window", help="Lookback window (e.g. 24h, 7d, 30m)"),
    chain_path: Optional[Path] = typer.Option(
        None,
        "--chain-path",
        help="Override the audit NDJSON path (default: <repo>/.ai/audit/events.ndjson).",
    ),
) -> None:
    """Compute gate-wait latency p50/p95/histogram over the given window.

    Output is a single JSON object on stdout with stable keys: `window`,
    `sample_count`, `p50`, `p95`, `histogram`. Percentiles are explicit
    `null` when zero samples (matches A3 acceptance contract).
    """
    repo_root = _project_root(Path.cwd())
    path = chain_path if chain_path is not None else repo_root / ".ai" / "audit" / "events.ndjson"

    try:
        start, end = core.parse_window(window)
    except ValueError as exc:
        typer.echo(f"audit metrics: {exc}", err=True)
        raise typer.Exit(2)

    if not path.exists():
        payload = {
            "window": {"spec": window, "start": start.isoformat(), "end": end.isoformat()},
            "sample_count": 0,
            "p50": None,
            "p95": None,
            "histogram": [],
            "note": f"audit chain not found at {path}",
        }
        typer.echo(json.dumps(payload, indent=2, default=str))
        return

    try:
        events = core.load_events(path)
    except ValueError as exc:
        typer.echo(f"audit metrics: failed to parse {path}: {exc}", err=True)
        raise typer.Exit(3)

    all_samples = core.pair_gate_waits(events)
    windowed = core.filter_window(all_samples, start=start, end=end)
    durations = [s.duration_seconds for s in windowed]

    payload = {
        "window": {
            "spec": window,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "sample_count": len(durations),
        "p50": core.percentile(durations, 50.0),
        "p95": core.percentile(durations, 95.0),
        "histogram": core.histogram(durations),
    }
    typer.echo(json.dumps(payload, indent=2, default=str))


__all__ = ["metrics"]
