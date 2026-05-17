# Session Naming (Canonical Spec)

**Status:** Active (Trinity v0.5+)
**Owner:** core CLI (`cli/core/session_naming.py`)
**Configured by:** `.ai/ssot.yaml` → `session_naming:` block

This document is the single source of truth for how Trinity generates
session folder names. Any example in USER_MANUAL / USER_GUIDE / template
READMEs must match the rules described here.

---

## 1. Canonical Format

```
{seq:04d}_{date}_{hour}_{minute}_{ampm}_{type}-{slug}
```

**Example** (V2 Plan Implementation, created at 22:21 local time):

```
0001_2026-04-20_22_21_pm_feat-v2-plan-implementation
```

### Block breakdown

```
┌────┬────────────┬────┬────┬────┬──────┬─────────────────────────────┐
│0001│ 2026-04-20 │ 22 │ 21 │ pm │ feat │ v2-plan-implementation      │
└─┬──┴─────┬──────┴─┬──┴─┬──┴─┬──┴──┬───┴──────────┬──────────────────┘
  │        │        │    │    │     │              │
  │        │        │    │    │     │              └── slug    (free text, slugified)
  │        │        │    │    │     └──────────────── type    (feat|fix|...)
  │        │        │    │    └──────────────────── am/pm    (lowercase; derived from hour)
  │        │        │    └──────────────────────── minute   (00-59)
  │        │        └──────────────────────────── hour     (24-hour: 00-23)
  │        └──────────────────────────────────── date     (ISO 8601)
  └─────────────────────────────────────────── seq      (global, 4-digit zero-padded)
```

**Separators:** `_` between blocks, `-` inside the `type-slug` tail.

---

## 2. Variables

| Block  | Source        | Format     | Range     | Notes                              |
| :----- | :------------ | :--------- | :-------- | :--------------------------------- |
| seq    | folder scan   | `%04d`     | 0001–9999 | Global counter, `max(existing)+1`  |
| date   | `datetime.now`| `%Y-%m-%d` | ISO 8601  | Uses local timezone by default     |
| hour   | `datetime.now`| `%H`       | 00–23     | 24-hour clock                      |
| minute | `datetime.now`| `%M`       | 00–59     | Zero-padded                        |
| ampm   | derived       | `am`/`pm`  | enum      | `hour < 12 → am`, else `pm`        |
| type   | user or default | enum     | 7 values  | See §4 for the list                |
| slug   | user input    | slugified  | ≤40 chars | Lowercase, strip/collapse, truncate|

---

## 3. Configuration (`.ai/ssot.yaml`)

```yaml
session_naming:
  format: "{seq:04d}_{date}_{hour}_{minute}_{ampm}_{type}-{slug}"
  seq_mode: global                # global | per_day | none
  seq_padding: 4                  # 4 digits -> 0001..9999
  date_format: "%Y-%m-%d"
  hour_format: "%H"               # 24-hour (00..23)
  minute_format: "%M"             # 00..59
  ampm_lowercase: true            # am/pm (lowercase)
  timezone: local                 # local | utc
  slug_max_length: 40
  slug_separator: "-"             # inside type-slug and slug body
  block_separator: "_"            # between blocks
  default_type: feat
  allowed_types:
    - feat        # new feature
    - fix         # bug fix
    - refactor    # code cleanup / restructure
    - docs        # documentation
    - chore       # misc / maintenance
    - spike       # prototype / research
    - ops         # deploy / infra / release
```

If the `session_naming:` block is absent, the CLI falls back to the
defaults shown above so older projects keep working without a config
change.

---

## 4. Allowed Types

| Type       | When to use                                          |
| :--------- | :--------------------------------------------------- |
| `feat`     | New feature or capability                            |
| `fix`      | Bug fix for existing behavior                        |
| `refactor` | Code cleanup / restructure, no behavior change       |
| `docs`     | Docs-only changes (README, guides, migrations)       |
| `chore`    | Misc maintenance (dependency bump, cleanup)          |
| `spike`    | Prototype / proof-of-concept / research              |
| `ops`      | Deploy / infra / CI / release engineering            |

**Default:** `feat` (used when no type is detected from the name).

---

## 5. Type Parsing (accepted input forms)

| You type                           | Parsed type | Slug source      |
| :--------------------------------- | :---------- | :--------------- |
| `"fix: login 500"`                 | `fix`       | `login 500`      |
| `"fix login 500"`                  | `fix`       | `login 500`      |
| `"login 500 error"`                | `feat`      | `login 500 error`|
| `--type chore "cleanup archive"`   | `chore`     | `cleanup archive`|

The CLI checks, in order:
1. Explicit `--type <x>` flag (if supported by the command).
2. Leading `<type>:` prefix.
3. First word matching an allowed type.
4. Falls back to `default_type`.

---

## 6. Slugify Rules

Implemented in `cli/core/session_naming.py::slugify`:

1. Trim whitespace and lowercase.
2. Replace any run of non `[a-z0-9ก-๙]` characters with
   `slug_separator` (default `-`).
3. Collapse duplicate separators, strip leading/trailing separators.
4. Truncate to `slug_max_length` (default 40).

**Examples:**

| Input                      | Output                       |
| :------------------------- | :--------------------------- |
| `"V2 Plan Implementation"` | `v2-plan-implementation`     |
| `"fix/login_500 error!!"`  | `fix-login-500-error`        |
| `"แก้ bug login"`           | `แก้-bug-login` (Thai kept)  |
| `"   trim  me   "`         | `trim-me`                    |

Thai characters pass through untouched so Thai-speaking users can
describe tasks naturally.

---

## 7. Sequence Modes

| `seq_mode` | Behavior                                  | Collision handling            |
| :--------- | :---------------------------------------- | :---------------------------- |
| `global`   | Counts every session ever created         | `max(all seq prefixes) + 1`   |
| `per_day`  | Resets to `1` at the start of each `date` | `max(seq in same date) + 1`   |
| `none`     | No seq, always `0`                        | Use `time` for uniqueness     |

The scanner ignores folders that do not start with a numeric prefix,
so `archive/` and ad-hoc sibling folders do not break the counter.

---

## 8. Real Examples

| Command                                         | Generated session ID                                           |
| :---------------------------------------------- | :------------------------------------------------------------- |
| `session new "V2 Plan Implementation"` @22:21   | `0001_2026-04-20_22_21_pm_feat-v2-plan-implementation`         |
| `session new "fix: login 500"` @08:15           | `0002_2026-04-20_08_15_am_fix-login-500`                       |
| `session new "docs update readme"` @13:47       | `0003_2026-04-21_13_47_pm_docs-update-readme`                  |
| `session new "refactor: agent selector"` @18:03 | `0004_2026-04-21_18_03_pm_refactor-agent-selector`             |
| `session new "แก้ bug login"` @09:30            | `0005_2026-04-22_09_30_am_feat-แก้-bug-login`                   |

---

## 9. Before vs After

```
BEFORE (hardcoded, Trinity < v0.5)
  date_str = strftime("%Y-%m-%d")
  slug     = name.lower().replace(" ", "_").replace("/", "-")[:50]
  id       = f"{date_str}_{slug}"
  Example: 2025-12-21_fix_login_bug

  Problems: no seq, collides on 2nd session/day, no type, no time.

AFTER (SSOT-driven, Trinity v0.5+)
  id = build_session_id(name, sessions_dir, ssot)
  Example: 0001_2026-04-20_22_21_pm_feat-v2-plan-implementation

  Wins: unique (seq+time), sortable, filterable by type, configurable.
```

---

## 10. Migrating Existing Sessions

Old folders keep working — the CLI reads them by folder name, not by
pattern. When you want to rename, use:

```bash
# Pick a seq that doesn't collide with existing ones:
NEW_ID="0001_$(date +%Y-%m-%d_%H_%M)_pm_feat-<slug>"
git mv sessions/<old-id> sessions/${NEW_ID}
# Update internal refs in CONTROL/META.json, CONTROL/LIVE_MONITOR.md,
# CONTROL/VERIFY.md, and .state/status.json to match NEW_ID.
```

A helper command (`ai session rename <old> <new>`) is tracked as a
follow-up for a future session.

---

## 11. Implementation Pointers

| File                                        | Role                                       |
| :------------------------------------------ | :----------------------------------------- |
| `cli/core/session_naming.py`                | `build_session_id`, `slugify`, `next_seq`  |
| `cli/commands/session.py` (`new` command)   | Calls `build_session_id()`                 |
| `cli/tests/test_session_naming.py`          | 22 unit tests                              |
| `ssot.yaml` → `session_naming:`             | Per-project overrides                      |

Run the tests from the `.ai/` root:

```bash
cd .ai && python3 -m pytest cli/tests/test_session_naming.py -q
```
