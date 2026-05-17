"""Tests for cli.core.session_naming."""
from __future__ import annotations

import datetime
import re
from pathlib import Path

import pytest

from cli.core.session_naming import (
    SessionNamingError,
    build_session_id,
    load_rules,
    next_seq,
    parse_type_and_slug,
    slugify,
)

SSOT_WITH_BLOCK = {
    "session_naming": {
        "format": "{seq:04d}_{date}_{hour}_{minute}_{ampm}_{type}-{slug}",
        "seq_mode": "global",
        "seq_padding": 4,
        "date_format": "%Y-%m-%d",
        "hour_format": "%H",
        "minute_format": "%M",
        "ampm_lowercase": True,
        "timezone": "local",
        "slug_max_length": 40,
        "slug_separator": "-",
        "block_separator": "_",
        "default_type": "feat",
        "allowed_types": ["feat", "fix", "refactor", "docs", "chore", "spike", "ops"],
    }
}

# 2026-04-20 22:21 local — user-facing afternoon in TH.
FIXED_NOW = datetime.datetime(2026, 4, 20, 22, 21, 53)


def test_load_rules_defaults_when_block_missing():
    rules = load_rules({})
    assert rules["format"].startswith("{seq")
    assert "feat" in rules["allowed_types"]


def test_load_rules_merges_ssot_block():
    cfg = {"session_naming": {"default_type": "ops"}}
    rules = load_rules(cfg)
    assert rules["default_type"] == "ops"
    assert rules["seq_padding"] == 4  # default preserved


def test_load_rules_rejects_non_mapping():
    with pytest.raises(SessionNamingError):
        load_rules({"session_naming": ["not", "a", "mapping"]})


@pytest.mark.parametrize(
    "text, expected",
    [
        ("V2 Plan Implementation", "v2-plan-implementation"),
        ("fix/login_500 error!!", "fix-login-500-error"),
        ("  trim  me  ", "trim-me"),
    ],
)
def test_slugify_basic(text, expected):
    assert slugify(text, max_length=40, separator="-") == expected


def test_slugify_respects_max_length():
    out = slugify("a" * 80, max_length=10, separator="-")
    assert out == "a" * 10


def test_slugify_preserves_thai():
    # Thai block should pass through (important for yai's workflow).
    assert slugify("แก้ bug login", 40, "-") == "แก้-bug-login"


def test_parse_type_colon_form():
    assert parse_type_and_slug("fix: login 500", SSOT_WITH_BLOCK["session_naming"]) == (
        "fix",
        "login 500",
    )


def test_parse_type_first_word_form():
    assert parse_type_and_slug("docs update readme", SSOT_WITH_BLOCK["session_naming"]) == (
        "docs",
        "update readme",
    )


def test_parse_type_falls_back_to_default():
    rules = SSOT_WITH_BLOCK["session_naming"]
    t, s = parse_type_and_slug("implement agent sandbox", rules)
    assert t == rules["default_type"]
    assert s == "implement agent sandbox"


def test_parse_type_rejects_bad_default_type():
    rules = dict(SSOT_WITH_BLOCK["session_naming"], default_type="bogus")
    with pytest.raises(SessionNamingError):
        parse_type_and_slug("random name", rules)


def test_next_seq_empty_dir(tmp_path: Path):
    rules = load_rules(SSOT_WITH_BLOCK)
    assert next_seq(tmp_path, rules, FIXED_NOW) == 1


def test_next_seq_global_max_plus_one(tmp_path: Path):
    rules = load_rules(SSOT_WITH_BLOCK)
    (tmp_path / "0001_2026-04-20_10_00_am_feat-one").mkdir()
    (tmp_path / "0003_2026-04-20_11_00_am_fix-two").mkdir()
    (tmp_path / "archive").mkdir()  # should be ignored (no numeric prefix)
    assert next_seq(tmp_path, rules, FIXED_NOW) == 4


def test_next_seq_per_day_isolates_by_date(tmp_path: Path):
    cfg = {"session_naming": {**SSOT_WITH_BLOCK["session_naming"], "seq_mode": "per_day"}}
    rules = load_rules(cfg)
    (tmp_path / "0005_2026-04-19_09_00_am_feat-old").mkdir()
    (tmp_path / "0001_2026-04-20_08_00_am_feat-new").mkdir()
    assert next_seq(tmp_path, rules, FIXED_NOW) == 2


def test_build_session_id_canonical_format(tmp_path: Path):
    session_id, comps = build_session_id(
        "V2 Plan Implementation",
        tmp_path,
        SSOT_WITH_BLOCK,
        now=FIXED_NOW,
    )
    assert session_id == "0001_2026-04-20_22_21_pm_feat-v2-plan-implementation"
    assert comps["ampm"] == "pm"
    assert comps["type"] == "feat"


def test_build_session_id_24hour_am(tmp_path: Path):
    morning = FIXED_NOW.replace(hour=8, minute=15)
    session_id, _ = build_session_id(
        "fix: login 500", tmp_path, SSOT_WITH_BLOCK, now=morning
    )
    assert session_id == "0001_2026-04-20_08_15_am_fix-login-500"


def test_build_session_id_honors_explicit_type(tmp_path: Path):
    session_id, _ = build_session_id(
        "cleanup archive", tmp_path, SSOT_WITH_BLOCK, explicit_type="chore", now=FIXED_NOW
    )
    assert session_id.endswith("_chore-cleanup-archive")


def test_build_session_id_rejects_bad_explicit_type(tmp_path: Path):
    with pytest.raises(SessionNamingError):
        build_session_id(
            "anything", tmp_path, SSOT_WITH_BLOCK, explicit_type="wtf", now=FIXED_NOW
        )


def test_build_session_id_rejects_empty_slug(tmp_path: Path):
    with pytest.raises(SessionNamingError):
        build_session_id("   ", tmp_path, SSOT_WITH_BLOCK, now=FIXED_NOW)


def test_build_session_id_seq_increments_across_calls(tmp_path: Path):
    first, _ = build_session_id("task one", tmp_path, SSOT_WITH_BLOCK, now=FIXED_NOW)
    (tmp_path / first).mkdir()
    second, _ = build_session_id("task two", tmp_path, SSOT_WITH_BLOCK, now=FIXED_NOW)
    assert first.startswith("0001_")
    assert second.startswith("0002_")


def test_build_session_id_format_is_parseable(tmp_path: Path):
    session_id, _ = build_session_id(
        "V2 Plan Implementation", tmp_path, SSOT_WITH_BLOCK, now=FIXED_NOW
    )
    pattern = re.compile(r"^(\d{4})_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})_(am|pm)_([a-z]+)-(.+)$")
    m = pattern.match(session_id)
    assert m, f"Generated id does not match canonical regex: {session_id}"
    assert m.group(6) in {"feat", "fix", "refactor", "docs", "chore", "spike", "ops"}
