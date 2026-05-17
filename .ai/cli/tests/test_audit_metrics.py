"""Tests for `cli.core.audit_metrics` + the `ai audit metrics` CLI surface.

Covers the join + windowing + percentile contracts called out in the plan
envelope acceptance criteria:
  (a) join correctness with interleaved concurrent sessions
  (b) zero-sample window → p50/p95 null sentinels (no crash)
  (c) single-sample window → p50 == p95 == that lone latency
  (d) N-sample window matches a hand-computed reference
  (e) malformed / orphan bot_command.fired rows are skipped not crashed
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.core import audit_metrics as core
from cli.commands.audit import app as audit_app


def _event(*, ts: str, event: str, session_id: str | None, sequence: int | None = None, **extra) -> dict:
    rec = {"ts": ts, "event": event, "session_id": session_id}
    if sequence is not None:
        rec["sequence"] = sequence
    rec.update(extra)
    return rec


def _write_chain(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for ev in events:
            fh.write(json.dumps(ev) + "\n")


# ---------------------------------------------------------------------------
# parse_window
# ---------------------------------------------------------------------------

class TestParseWindow:
    def test_24h(self):
        anchor = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        start, end = core.parse_window("24h", now=anchor)
        assert end == anchor
        assert end - start == timedelta(hours=24)

    def test_7d(self):
        anchor = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        start, end = core.parse_window("7d", now=anchor)
        assert end - start == timedelta(days=7)

    def test_30m(self):
        anchor = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)
        start, end = core.parse_window("30m", now=anchor)
        assert end - start == timedelta(minutes=30)

    @pytest.mark.parametrize("bad", ["", "abc", "12", "0h", "-1h", "10x"])
    def test_invalid_spec_raises(self, bad):
        with pytest.raises(ValueError):
            core.parse_window(bad)


# ---------------------------------------------------------------------------
# percentile
# ---------------------------------------------------------------------------

class TestPercentile:
    def test_empty_returns_none(self):
        assert core.percentile([], 50.0) is None
        assert core.percentile([], 95.0) is None

    def test_single_sample(self):
        assert core.percentile([3.0], 50.0) == 3.0
        assert core.percentile([3.0], 95.0) == 3.0

    def test_two_samples_p50(self):
        # linear interpolation between 1.0 and 3.0 at rank 0.5 → 2.0
        assert core.percentile([1.0, 3.0], 50.0) == 2.0

    def test_known_p50_p95(self):
        # Sorted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]; len=10, indices 0..9
        # p50: rank = 0.5 * 9 = 4.5 → interpolate values[4]=5 and values[5]=6 → 5.5
        # p95: rank = 0.95 * 9 = 8.55 → interpolate values[8]=9 and values[9]=10 → 9.55
        vals = list(range(1, 11))
        assert core.percentile(vals, 50.0) == pytest.approx(5.5)
        assert core.percentile(vals, 95.0) == pytest.approx(9.55)

    @pytest.mark.parametrize("pct", [-0.1, 100.1, 200.0])
    def test_out_of_range_raises(self, pct):
        with pytest.raises(ValueError):
            core.percentile([1.0, 2.0], pct)


# ---------------------------------------------------------------------------
# histogram
# ---------------------------------------------------------------------------

class TestHistogram:
    def test_empty_values_yields_zero_counts(self):
        out = core.histogram([])
        assert all(b["count"] == 0 for b in out)
        assert len(out) == len(core.DEFAULT_BUCKETS_SECONDS)

    def test_final_bucket_is_open_upper(self):
        out = core.histogram([10000.0])
        assert out[-1]["max"] is None
        assert out[-1]["count"] == 1

    def test_below_first_edge_is_dropped(self):
        # negative values fall below the 0.0 edge and are dropped
        out = core.histogram([-1.0, 0.5])
        total = sum(b["count"] for b in out)
        assert total == 1

    def test_custom_buckets(self):
        out = core.histogram([0.5, 1.5, 2.5], buckets=(0.0, 1.0, 2.0))
        # bin 0 [0,1): 0.5 → count 1; bin 1 [1,2): 1.5 → count 1; bin 2 [2,inf): 2.5 → count 1
        assert [b["count"] for b in out] == [1, 1, 1]


# ---------------------------------------------------------------------------
# load_events
# ---------------------------------------------------------------------------

class TestLoadEvents:
    def test_blank_lines_skipped(self, tmp_path):
        path = tmp_path / "chain.ndjson"
        events = [
            _event(ts="2026-05-14T10:00:00Z", event="bot_command.fired", session_id="s1"),
        ]
        _write_chain(path, events)
        # add a blank line
        with path.open("a") as fh:
            fh.write("\n\n")
        loaded = core.load_events(path)
        assert len(loaded) == 1
        assert loaded[0].event == "bot_command.fired"

    def test_type_field_fallback(self, tmp_path):
        # earlier audit emissions used `type` instead of `event`
        path = tmp_path / "chain.ndjson"
        path.write_text(json.dumps({
            "ts": "2026-05-14T10:00:00Z",
            "type": "ddd.completed",
            "session_id": "s1",
        }) + "\n", encoding="utf-8")
        loaded = core.load_events(path)
        assert loaded[0].event == "ddd.completed"

    def test_timestamp_alias(self, tmp_path):
        # accept `timestamp` as a synonym for `ts`
        path = tmp_path / "chain.ndjson"
        path.write_text(json.dumps({
            "timestamp": "2026-05-14T10:00:00Z",
            "event": "bot_command.fired",
            "session_id": "s1",
        }) + "\n", encoding="utf-8")
        loaded = core.load_events(path)
        assert loaded[0].ts == datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc)

    def test_malformed_json_raises(self, tmp_path):
        path = tmp_path / "chain.ndjson"
        path.write_text("not json\n", encoding="utf-8")
        with pytest.raises(ValueError):
            core.load_events(path)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            core.load_events(tmp_path / "missing.ndjson")


# ---------------------------------------------------------------------------
# pair_gate_waits — the core join contract
# ---------------------------------------------------------------------------

class TestPairGateWaits:
    def test_single_pair(self, tmp_path):
        events = core.load_events(self._write([
            _event(ts="2026-05-14T10:00:00Z", event="bot_command.fired", session_id="s1", sequence=1),
            _event(ts="2026-05-14T10:00:05Z", event="ddd.completed", session_id="s1", sequence=2),
        ], tmp_path))
        samples = core.pair_gate_waits(events)
        assert len(samples) == 1
        assert samples[0].duration_seconds == 5.0
        assert samples[0].completed_event == "ddd.completed"

    def test_interleaved_concurrent_sessions(self, tmp_path):
        # Two sessions firing nearly simultaneously; events MUST NOT cross sessions.
        events = core.load_events(self._write([
            _event(ts="2026-05-14T10:00:00Z", event="bot_command.fired", session_id="s1", sequence=1),
            _event(ts="2026-05-14T10:00:01Z", event="bot_command.fired", session_id="s2", sequence=1),
            _event(ts="2026-05-14T10:00:10Z", event="ddd.completed", session_id="s2", sequence=2),
            _event(ts="2026-05-14T10:00:30Z", event="ddd.completed", session_id="s1", sequence=2),
        ], tmp_path))
        samples = core.pair_gate_waits(events)
        by_session = {s.session_id: s.duration_seconds for s in samples}
        assert by_session == {"s1": 30.0, "s2": 9.0}

    def test_orphan_fired_is_unmatched(self, tmp_path):
        events = core.load_events(self._write([
            _event(ts="2026-05-14T10:00:00Z", event="bot_command.fired", session_id="s1"),
            _event(ts="2026-05-14T10:00:05Z", event="bot_command.fired", session_id="s1"),
            _event(ts="2026-05-14T10:00:10Z", event="ddd.completed", session_id="s1"),
        ], tmp_path))
        samples = core.pair_gate_waits(events)
        # FIFO: the first fired (10:00:00) is paired with the terminal (10:00:10);
        # the second fired (10:00:05) stays unmatched and is silently dropped
        assert len(samples) == 1
        assert samples[0].duration_seconds == 10.0

    def test_null_session_dropped(self, tmp_path):
        events = core.load_events(self._write([
            _event(ts="2026-05-14T10:00:00Z", event="bot_command.fired", session_id=None),
            _event(ts="2026-05-14T10:00:05Z", event="ddd.completed", session_id=None),
        ], tmp_path))
        samples = core.pair_gate_waits(events)
        assert samples == []

    def test_negative_duration_skipped(self, tmp_path):
        # Clock skew: terminal stamped BEFORE its fired event in the same session.
        events = core.load_events(self._write([
            _event(ts="2026-05-14T10:00:10Z", event="bot_command.fired", session_id="s1", sequence=1),
            _event(ts="2026-05-14T10:00:00Z", event="ddd.completed", session_id="s1", sequence=2),
        ], tmp_path))
        samples = core.pair_gate_waits(events)
        # Sorted by (ts, sequence) → terminal first (10:00:00) but no pending fired yet → unmatched.
        assert samples == []

    @staticmethod
    def _write(events: list[dict], tmp_path: Path) -> Path:
        path = tmp_path / "chain.ndjson"
        _write_chain(path, events)
        return path


# ---------------------------------------------------------------------------
# filter_window
# ---------------------------------------------------------------------------

class TestFilterWindow:
    def test_half_open_interval(self):
        s1 = core.GateWaitSample(
            session_id="s1",
            fired_ts=datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc),
            completed_ts=datetime(2026, 5, 14, 10, 0, 5, tzinfo=timezone.utc),
            completed_event="ddd.completed",
            duration_seconds=5.0,
        )
        start = datetime(2026, 5, 14, 9, 0, tzinfo=timezone.utc)
        end = datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc)
        # end is exclusive; sample at 10:00:00 falls on `end` → excluded
        assert core.filter_window([s1], start=start, end=end) == []
        # extend end past 10:00 → included
        end2 = datetime(2026, 5, 14, 10, 0, 1, tzinfo=timezone.utc)
        assert core.filter_window([s1], start=start, end=end2) == [s1]


# ---------------------------------------------------------------------------
# CLI surface — `ai audit metrics`
# ---------------------------------------------------------------------------

class TestCliSurface:
    runner = CliRunner()

    def test_empty_chain_returns_null_sentinels(self, tmp_path):
        chain = tmp_path / "empty.ndjson"
        chain.write_text("", encoding="utf-8")
        result = self.runner.invoke(
            audit_app, ["metrics", "--window", "24h", "--chain-path", str(chain)]
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["sample_count"] == 0
        assert payload["p50"] is None
        assert payload["p95"] is None
        assert payload["window"]["spec"] == "24h"

    def test_with_samples(self, tmp_path):
        chain = tmp_path / "chain.ndjson"
        now = datetime.now(tz=timezone.utc)
        recent_fired = (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        recent_done = (now - timedelta(minutes=9)).isoformat().replace("+00:00", "Z")
        _write_chain(chain, [
            _event(ts=recent_fired, event="bot_command.fired", session_id="s1", sequence=1),
            _event(ts=recent_done, event="ddd.completed", session_id="s1", sequence=2),
        ])
        result = self.runner.invoke(
            audit_app, ["metrics", "--window", "1h", "--chain-path", str(chain)]
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["sample_count"] == 1
        # 1 minute = 60s gate-wait
        assert payload["p50"] == pytest.approx(60.0, rel=0.05)
        assert payload["p95"] == pytest.approx(60.0, rel=0.05)

    def test_missing_chain_path_is_graceful(self, tmp_path):
        result = self.runner.invoke(
            audit_app, ["metrics", "--window", "24h", "--chain-path", str(tmp_path / "missing.ndjson")]
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["sample_count"] == 0
        assert payload["p50"] is None
        assert payload["p95"] is None

    def test_bad_window_exits_2(self, tmp_path):
        chain = tmp_path / "empty.ndjson"
        chain.write_text("", encoding="utf-8")
        result = self.runner.invoke(
            audit_app, ["metrics", "--window", "abc", "--chain-path", str(chain)]
        )
        assert result.exit_code == 2
