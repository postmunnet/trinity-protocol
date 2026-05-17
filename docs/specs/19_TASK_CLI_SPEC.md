# 19. task-cli — Task State Machine + Time Tracking + Resume Context

> **Status:** v0.1.0-beta (2026-05-10) — MVP shipped.
> **Sibling path:** `<workspace-root>/task-cli/`
> **Composition:** state machine + time tracking layer that calls
> memory-cli over subprocess for recall (best-effort, graceful).

## 1. Why this exists

Operator's three ADHD pains, each mapped to a verb:

| Pain | Verb |
|------|------|
| ลืมงานค้าง (forgotten pending work) | `stale` |
| จมงานเดียว (single-task tunnel-vision) | `current` + UNIQUE-active invariant |
| กลับมาทำต่อไม่ถูก (lost re-entry context) | `resume_context` |

Existing siblings did not cover these — `memory-cli` is recall-shaped
(documents/notes/retros), `notify-cli` is event-shaped, neither
exposes a state machine that distinguishes "what am I working on
right now" from "what's queued" from "what fell through the cracks".

## 2. Composition

```
+-------------+   subprocess  +-------------+
|  task-cli   | ────────────► |  memory-cli |
|  (state)    | ◄──────────── |  (recall)   |
+-------------+   envelope    +-------------+
       │
       │  (Phase 3, future)
       ▼
+-------------+      +-----------------+
|  notify-cli | ───► |  trinity-tg-bot |
+-------------+      +-----------------+
```

Compose contract — task-cli calls memory-cli on three triggers:

| task-cli verb | memory-cli call | Purpose |
|---------------|-----------------|---------|
| `done` | `note <summary> --source=task-cli` | Auto-summary of the finished task lands in inbox |
| `reflect` | `note <weekly-aggregate> --source=task-cli` | Weekly digest material |
| `resume_context` | `search <title+desc> --hybrid --limit=3` | Surface related past retros/notes |

All compose calls are SUBPROCESS only (`spawnSync`). task-cli never
imports memory-cli. Failures (binary missing, timeout, parse error,
non-zero exit) degrade silently — the parent verb still succeeds and
includes `memory_id: null` + `memory_error: <reason>` in its envelope.

Test override: `TASK_MEMORY_CLI_BIN=false` disables compose entirely.

## 3. Schema

### 3.1 `tasks`

```sql
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,                        -- t_<base36 ms>_<rand6>
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'open'
    CHECK(status IN ('open','active','paused','done')),
  project TEXT,
  priority TEXT NOT NULL DEFAULT 'med'
    CHECK(priority IN ('low','med','high')),
  due_at TEXT,
  created_at TEXT NOT NULL,
  started_at TEXT,
  paused_at TEXT,
  finished_at TEXT,
  time_spent_sec INTEGER NOT NULL DEFAULT 0,
  last_action TEXT,
  last_file TEXT,
  last_touched TEXT NOT NULL,
  metadata_json TEXT
);
```

### 3.2 `task_events`

```sql
CREATE TABLE task_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  event TEXT NOT NULL,        -- add|start|pause|resume|done|switch
  payload_json TEXT,
  ts TEXT NOT NULL,
  FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

### 3.3 Invariants

- `idx_tasks_status`, `idx_tasks_project`, `idx_tasks_priority`,
  `idx_tasks_last_touched` for filter/sort efficiency.
- **UNIQUE PARTIAL INDEX** `uniq_active_task ON tasks(status) WHERE
  status='active'` — at most one active task at any time. All
  promote-to-active verbs auto-pause any existing active task in the
  SAME transaction.
- WAL mode + `PRAGMA foreign_keys = ON`.
- Storage: `$TRINITY_TASKS_DB` env > `~/.trinity/tasks.db`. Separate
  from `memory-cli`'s `memory.db`.

## 4. State machine

```
   open ──start──► active ──pause──► paused
                    │     ◄─resume──┘
                    └────done────►  done
   open ─────────────done────────►  done
   paused ──────────done────────►  done
   done    (terminal)
```

Promotion rules:

- `open → active`: via `start`.
- `paused → active`: via `resume` (or `start` — same machinery).
- `active → paused`: via `pause` (accumulates time_spent_sec from
  started_at→now, clears started_at).
- any non-`done` → `done`: via `done` (active tasks accumulate
  in-flight time first).

Auto-pause: when `start`/`resume`/`switch` is called and another task
is `active`, that task is paused first inside the same transaction
with `event='pause', payload_json={reason:'auto-switch', triggered_by:<id>}`.

## 5. Verbs (12)

| Verb | Args | Status transitions |
|------|------|---------------------|
| `add` | `<title> [--project --prio --due --description]` | → `open` |
| `list` | `[--status --project --prio --limit]` | (read-only) |
| `get` | `<id>` | (read-only; +last 10 events) |
| `start` | `<id>` | open\|paused → active (auto-pauses other) |
| `pause` | `<id> [--reason]` | active → paused |
| `resume` | `<id>` | paused → active (auto-pauses other) |
| `done` | `<id> [--summary]` | any → done; **composes memory-cli** |
| `stale` | `[--days=7]` | (read-only) |
| `current` | (none) | (read-only) |
| `switch` | `<id>` | atomic pause-current + start-target |
| `reflect` | `[--days=7]` | (read-only; **composes memory-cli**) |
| `resume_context` | `<id>` | (read-only; **composes memory-cli**) |

## 6. Envelope

TOOL_CONTRACT v1.1 compatible. Every verb returns:

```json
{
  "ok": true,
  "schema_version": "1.0",
  "tool": "task-cli",
  "tool_version": "0.1.0-beta",
  "command": "<verb>",
  "action": "task.<verb>",
  "data": { /* verb-specific */ },
  "artifacts": [],
  "error": null,
  "meta": { "ts": "<ISO-8601>" }
}
```

## 7. Phase 3 hooks (future)

- **notify-cli**: rule-set on `task_events.event` —
  `pause` with reason='auto-switch' + `now-started_at > 90min` → focus warning.
  `stale` daily reminder via cron-style watch.
  `switch` events with project change → cross-project focus alert.
- **trinity-tg-bot**: `/task add|start|pause|done|current|stale`
  remote handlers, with HMAC-verified gate approvals (kernel core/auth
  shim already wired in Tier 0 sprint).

## 8. Acceptance gates (8) — all PASSED 2026-05-10

| ID | Description | Status |
|----|-------------|--------|
| A_REGRESSION_TASKCLI | All 27 unit tests pass | OK |
| A_DB_SCHEMA | tasks + task_events created with WAL | OK |
| A_STATE_MACHINE | start/pause/resume/done full cycle | OK |
| A_RESUME_CONTEXT | resume_context returns related_memory key | OK |
| A_PLATINUM | trinity-contract-test --tier=platinum 14/14 | OK |
| A_VERSION | package.json version 0.1.0-beta | OK |
| A_TOOLS_YAML | task-cli registered in tools.yaml | OK |
| A_INVENTORY_UPDATED | TOOLS_INVENTORY.md has task-cli row | OK |

## 9. Non-goals (v0.1)

- No notify-cli wiring (Phase 3).
- No trinity-tg-bot wiring (Phase 3).
- No web UI / dashboard (extension-platform sibling could surface
  later).
- No multi-user / collaborative tasks.
- No estimate-vs-actual tracking on tasks (could ship in v0.2).
- No automatic project detection (operator passes `--project=` for
  now; auto-detect from cwd is a v0.2 candidate).

## 10. Trinity-clean

- Zero npm dependencies.
- `package.json` lists no `dependencies` block.
- Pure Node ≥22.5.0 (`node:sqlite`, `node:child_process`,
  `node:test`).
