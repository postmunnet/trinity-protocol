"""Gate-wait metric derivation from the kernel audit chain.

Pure-read building blocks for `ai audit metrics`. This module never writes
to the audit chain or any other file; it only parses NDJSON, joins
`bot_command.fired` events to terminal-transition events within the same
session, and exposes windowing + summary primitives. The CLI surface that
calls these primitives lives in `.ai/cli/commands/audit_metrics.py` (S3).

Joining contract
----------------

Within a single `session_id`, events are ordered by (timestamp, sequence).
A queue of unmatched `bot_command.fired` events is maintained; each
terminal-transition event consumes the oldest pending fired event in that
session. Cross-session pairing never happens.

Schema assumptions
------------------

Each NDJSON line is a JSON object with at least:
  - `ts`            ISO-8601 UTC timestamp (may use trailing 'Z')
  - `event`         event name string
  - `session_id`    string or null  (events with null session_id are skipped)
  - `sequence`      integer monotonic sequence (optional; ts-only fallback)

The `hash` / `prev_hash` chain fields are ignored here; chain integrity is
verified elsewhere.
"""

from __future__ import annotations

import bisect
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

BOT_FIRED = "bot_command.fired"

TERMINAL_TRANSITIONS: frozenset[str] = frozenset({
    "ddd.completed",
    "ddd.passed",
    "vvv.completed",
    "nnn.completed",
    "gogogo.completed",
    "rrr.completed",
    "close.completed",
})

DEFAULT_BUCKETS_SECONDS: tuple[float, ...] = (
    0.0, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 900.0, 3600.0,
)

_WINDOW_UNITS = {
    "s": timedelta(seconds=1),
    "m": timedelta(minutes=1),
    "h": timedelta(hours=1),
    "d": timedelta(days=1),
    "w": timedelta(weeks=1),
}


@dataclass(frozen=True)
class AuditEvent:
    ts: datetime
    event: str
    session_id: str | None
    sequence: int | None
    raw: dict


@dataclass(frozen=True)
class GateWaitSample:
    session_id: str
    fired_ts: datetime
    completed_ts: datetime
    completed_event: str
    duration_seconds: float


def load_events(path: Path) -> list[AuditEvent]:
    """Parse the audit NDJSON file at `path`.

    Skips blank lines. Raises `ValueError` on malformed JSON or on an event
    that lacks a timestamp; raises `FileNotFoundError` if the file is absent.
    """
    events: list[AuditEvent] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"audit_metrics: malformed JSON at line {line_no}: {exc}"
                ) from exc
            ts = _parse_ts(rec.get("ts") or rec.get("timestamp"))
            event = rec.get("event") or rec.get("type") or ""
            session_id = rec.get("session_id")
            raw_seq = rec.get("sequence", rec.get("seq"))
            sequence = raw_seq if isinstance(raw_seq, int) else None
            events.append(AuditEvent(
                ts=ts,
                event=event,
                session_id=session_id,
                sequence=sequence,
                raw=rec,
            ))
    return events


def _parse_ts(raw) -> datetime:
    if raw is None:
        raise ValueError("audit_metrics: event missing timestamp field")
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), tz=timezone.utc)
    if isinstance(raw, str):
        text = raw.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    raise TypeError(
        f"audit_metrics: unsupported timestamp type {type(raw).__name__}"
    )


def parse_window(spec: str, *, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Parse a `'24h'` / `'7d'` / `'30m'` spec into a `(start_utc, end_utc)` pair.

    `end_utc` defaults to the current UTC time. `start_utc = end_utc - delta`.
    Raises `ValueError` for any malformed or non-positive input.
    """
    if not isinstance(spec, str) or not spec.strip():
        raise ValueError("audit_metrics: --window requires a non-empty string")
    text = spec.strip().lower()
    if len(text) < 2 or not text[-1].isalpha():
        raise ValueError(
            f"audit_metrics: invalid window spec {spec!r}; expected e.g. '24h', '7d'"
        )
    unit = text[-1]
    if unit not in _WINDOW_UNITS:
        raise ValueError(
            f"audit_metrics: unknown window unit {unit!r}; valid: {sorted(_WINDOW_UNITS)}"
        )
    magnitude_text = text[:-1]
    try:
        magnitude = int(magnitude_text)
    except ValueError as exc:
        raise ValueError(
            f"audit_metrics: invalid window magnitude in {spec!r}"
        ) from exc
    if magnitude <= 0:
        raise ValueError(
            f"audit_metrics: window magnitude must be positive, got {magnitude}"
        )
    end = (now or datetime.now(tz=timezone.utc)).astimezone(timezone.utc)
    start = end - _WINDOW_UNITS[unit] * magnitude
    return start, end


def _sort_key(ev: AuditEvent) -> tuple:
    seq = ev.sequence if ev.sequence is not None else -1
    return (ev.ts, seq)


def pair_gate_waits(
    events: Sequence[AuditEvent],
    *,
    terminal_events: Iterable[str] = TERMINAL_TRANSITIONS,
) -> list[GateWaitSample]:
    """Pair each `bot_command.fired` to the next terminal transition in its session.

    Within each session, events are sorted by (ts, sequence) and FIFO-matched:
    every terminal-transition event consumes the oldest unmatched
    `bot_command.fired` in that same session. Events with `session_id is None`
    are skipped. Negative durations (clock skew) are dropped silently; callers
    that need the raw events can inspect them via `load_events` directly.
    """
    terminal_set = frozenset(terminal_events)
    by_session: dict[str | None, list[AuditEvent]] = {}
    for ev in events:
        by_session.setdefault(ev.session_id, []).append(ev)

    samples: list[GateWaitSample] = []
    for session_id, bucket in by_session.items():
        if session_id is None:
            continue
        ordered = sorted(bucket, key=_sort_key)
        pending: list[AuditEvent] = []
        for ev in ordered:
            if ev.event == BOT_FIRED:
                pending.append(ev)
                continue
            if ev.event in terminal_set and pending:
                fired = pending.pop(0)
                duration = (ev.ts - fired.ts).total_seconds()
                if duration < 0:
                    continue
                samples.append(GateWaitSample(
                    session_id=session_id,
                    fired_ts=fired.ts,
                    completed_ts=ev.ts,
                    completed_event=ev.event,
                    duration_seconds=duration,
                ))
    return samples


def filter_window(
    samples: Sequence[GateWaitSample],
    *,
    start: datetime,
    end: datetime,
) -> list[GateWaitSample]:
    """Return samples whose `fired_ts` falls in the half-open interval `[start, end)`."""
    return [s for s in samples if start <= s.fired_ts < end]


def percentile(values: Sequence[float], pct: float) -> float | None:
    """Linear-interpolated percentile of `values`.

    Returns `None` — the explicit zero-sample sentinel — when `values` is empty.
    `pct` must be in the closed interval `[0, 100]`.
    """
    if not 0.0 <= pct <= 100.0:
        raise ValueError(
            f"audit_metrics: percentile must be in [0, 100], got {pct}"
        )
    if not values:
        return None
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (pct / 100.0) * (len(ordered) - 1)
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return ordered[lo]
    frac = rank - lo
    return ordered[lo] + (ordered[hi] - ordered[lo]) * frac


def histogram(
    values: Sequence[float],
    buckets: Sequence[float] = DEFAULT_BUCKETS_SECONDS,
) -> list[dict]:
    """Right-open bucket histogram of `values` over `buckets`.

    `buckets` is a sequence of left edges; bin `i` covers `[buckets[i], buckets[i+1])`
    and the final bin covers `[buckets[-1], +inf)`. Values below `buckets[0]` are
    dropped (callers should pass a `0.0` first edge for non-negative metrics such
    as gate-wait durations). Returns one `{min, max, count}` dict per bin; the
    final bin's `max` is `None` to signal an open upper bound.
    """
    if not buckets:
        raise ValueError("audit_metrics: histogram requires at least one bucket edge")
    ordered_edges = sorted(float(b) for b in buckets)
    counts = [0] * len(ordered_edges)
    for raw in values:
        v = float(raw)
        idx = bisect.bisect_right(ordered_edges, v) - 1
        if idx < 0:
            continue
        counts[idx] += 1
    out: list[dict] = []
    for i, edge in enumerate(ordered_edges):
        upper = ordered_edges[i + 1] if i + 1 < len(ordered_edges) else None
        out.append({"min": edge, "max": upper, "count": counts[i]})
    return out


__all__ = [
    "AuditEvent",
    "GateWaitSample",
    "BOT_FIRED",
    "TERMINAL_TRANSITIONS",
    "DEFAULT_BUCKETS_SECONDS",
    "load_events",
    "parse_window",
    "pair_gate_waits",
    "filter_window",
    "percentile",
    "histogram",
]
