"""Session folder naming.

Reads rules from SSOT (`session_naming` block) and produces canonical
session IDs of the form:

    {seq:04d}_{date}_{HH}_{MM}_{ampm}_{type}-{slug}

All fields are configurable via SSOT. If the block is absent, a safe
default matching the documented format is used. An older callsite that
passes only `name` keeps working (falls back to `default_type`).
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_DEFAULTS: Dict[str, Any] = {
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


class SessionNamingError(ValueError):
    """Raised for invalid type, mode, or unresolvable format."""


def load_rules(raw_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge SSOT `session_naming` block over defaults."""
    rules = dict(_DEFAULTS)
    block = (raw_config or {}).get("session_naming") or {}
    if not isinstance(block, dict):
        raise SessionNamingError("session_naming must be a mapping")
    rules.update(block)
    return rules


def slugify(text: str, max_length: int, separator: str) -> str:
    """Lowercase, collapse whitespace, strip forbidden chars, truncate."""
    s = text.strip().lower()
    # Keep ASCII letters/digits + common intra-word chars; turn everything
    # else (incl. spaces, underscores, punctuation) into the separator so we
    # never leak the block separator ("_") into slug territory.
    s = re.sub(r"[^a-z0-9\u0e00-\u0e7f]+", separator, s)
    s = re.sub(rf"{re.escape(separator)}+", separator, s).strip(separator)
    return s[:max_length].rstrip(separator)


def parse_type_and_slug(name: str, rules: Dict[str, Any]) -> Tuple[str, str]:
    """Accept "feat: do thing", "feat do thing", or plain "do thing".

    Only the first token is treated as a type. Anything else falls back
    to `default_type`.
    """
    allowed = set(rules["allowed_types"])
    default_type = rules["default_type"]

    head, _, rest = name.strip().partition(":")
    head_token = head.strip().split(" ", 1)[0].lower() if head.strip() else ""

    if rest.strip() and head_token in allowed:
        return head_token, rest.strip()

    # No colon form: maybe the first word is a type marker.
    first, _, tail = name.strip().partition(" ")
    if first.lower() in allowed and tail.strip():
        return first.lower(), tail.strip()

    if default_type not in allowed:
        raise SessionNamingError(
            f"default_type '{default_type}' not in allowed_types {sorted(allowed)}"
        )
    return default_type, name.strip()


def next_seq(sessions_dir: Path, rules: Dict[str, Any], now: datetime.datetime) -> int:
    mode = rules["seq_mode"]
    if mode == "none":
        return 0
    if not sessions_dir.exists():
        return 1

    pad = int(rules["seq_padding"])
    seq_re = re.compile(rf"^(\d{{{pad},}})_")
    date_tag = now.strftime(rules["date_format"])

    hits: list[int] = []
    for child in sessions_dir.iterdir():
        if not child.is_dir():
            continue
        m = seq_re.match(child.name)
        if not m:
            continue
        if mode == "per_day" and date_tag not in child.name:
            continue
        hits.append(int(m.group(1)))
    return (max(hits) + 1) if hits else 1


def _now(tz_mode: str) -> datetime.datetime:
    if tz_mode == "utc":
        return datetime.datetime.now(datetime.timezone.utc)
    return datetime.datetime.now()


def build_session_id(
    name: str,
    sessions_dir: Path,
    raw_config: Dict[str, Any],
    *,
    explicit_type: Optional[str] = None,
    now: Optional[datetime.datetime] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Return (session_id, components) for a new session.

    `explicit_type` (from a future --type CLI flag) overrides type parsed
    from `name`. `now` is injectable for deterministic tests.
    """
    rules = load_rules(raw_config)
    current = now or _now(rules["timezone"])

    if explicit_type is not None:
        if explicit_type not in set(rules["allowed_types"]):
            raise SessionNamingError(
                f"type '{explicit_type}' not in allowed_types {sorted(rules['allowed_types'])}"
            )
        type_tag, slug_source = explicit_type, name.strip()
    else:
        type_tag, slug_source = parse_type_and_slug(name, rules)

    slug = slugify(slug_source, rules["slug_max_length"], rules["slug_separator"])
    if not slug:
        raise SessionNamingError("session name produced an empty slug")

    components = {
        "seq": next_seq(sessions_dir, rules, current),
        "date": current.strftime(rules["date_format"]),
        "hour": current.strftime(rules["hour_format"]),
        "minute": current.strftime(rules["minute_format"]),
        "ampm": "pm" if current.hour >= 12 else "am",
        "type": type_tag,
        "slug": slug,
    }
    if not rules["ampm_lowercase"]:
        components["ampm"] = components["ampm"].upper()

    try:
        session_id = rules["format"].format(**components)
    except KeyError as exc:
        raise SessionNamingError(
            f"unknown placeholder {exc} in session_naming.format"
        ) from exc
    return session_id, components
