# memory-cli — Command Contract (frozen baseline)

**Version:** v0.9.2-beta · **Status:** Binding for v0.9.2 (Operational Brain capture + destructor-race workaround) · **Last Updated:** 2026-05-11
**Spec:** [`trinity_v2/docs/specs/05_MEMORY_CLI_SPEC.md`](../../specs/05_MEMORY_CLI_SPEC.md)
**Decision:** D13 — frozen contract baseline per tool

This file is the contract the Trinity kernel speaks against. Tool
implementation may evolve freely; the kernel only checks
`schema_version` + `contract_version` from `.ai/tools.yaml` against
this baseline.

**19 verbs wired:**

- **v0.5 baseline (Phase 2.1–2.3):** `stats`, `index`, `search`, `get`,
  `list`, `learn`, `tag`, `supersede`, `reflect`, `delete`, `reindex`,
  `health` (as a verb, distinct from the `--health` CLI flag).
- **v0.7 vector layer:** `embed` (per-doc sqlite-vec generation),
  `similar` (KNN over `vec_records`). Plus `search --hybrid` flag
  (FTS5 + vector RRF fusion) and the 7-phase action chain on every
  `learn`.
- **v0.8 visualization + threading:** `map` (PCA 2D/3D knowledge
  map), `thread` / `thread-of` / `unthread` (parent-child relations
  with DFS cycle detection).
- **v0.9 project tagging:** no new verbs — adds `project` column +
  auto-detect chain + `TRINITY_CENTRAL_DB` env + `--project` /
  `--project-not` search filters + `by_project` stats breakdown.
- **v0.9.1 capture surface:** `note` (quick-capture wrapper over
  `learn`; `type=note`, `confidence=draft`, `status='inbox'`,
  `skip_chain=true` by default).
- **v0.9.2:** no verb / schema changes — destructor-race workaround
  only (`closeAllOpenHandles()` + library-mode guard); eliminates the
  false-negative `memory_learn ok=false returncode=-6` on macOS.

`ai rrr` writes deterministic retro artifacts and delegates artifact
ingestion via `index`; it does not call `learn`, `promote`, `verify`,
`trace`, `embed`, or `similar` directly. `lll`/`vvv`/`nnn` query the
Brain via `search` / `list` / `reflect` for past-incident hints. The
action chain (when non-ritual callers invoke `learn` without
`skip_chain`) runs:
INSERT → auto-tag → FTS5 → embed → cross-link → audit → stats
(+ v0.8 phase 8: auto-thread from metadata).

---

## 1. Input Grammar

```
node index.js --cmd "<verb> [args...]"
node index.js --health
```

- `--cmd` — single string of verb + args, parsed by whitespace split
  inside the tool. The kernel passes the inner string verbatim.
- `--health` — boolean flag; returns a fixed health envelope. Used by
  the kernel's tool registry health check (`tools.yaml.health_check`).

---

## 2. Verbs

### 2.1 `stats`

**Action:** `memory.stats`
**Tier:** safe
**Purpose:** Return a snapshot of database health and content
distribution.

**Phase 2.1a behavior:** if no DB exists yet, returns the same shape
with zero values and a `note` flagging "run index first". After at
least one `index` call, returns real counts from the DB.

```bash
node index.js --cmd "stats"
```

**Response data shape:**

```json
{
  "total_docs": 3,
  "by_type": { "retro": 3 },
  "by_confidence": { "verified": 1, "draft": 2 },
  "total_words": 234,
  "db_size_bytes": 32768,
  "oldest": "2026-04-15",
  "newest": "2026-04-20T00:00:00Z",
  "top_tags": [
    { "tag": "bugfix", "count": 1 },
    { "tag": "ui", "count": 1 }
  ],
  "indexed_at": "2026-04-30T15:29:11.332Z"
}
```

### 2.2 `index`

**Action:** `memory.index`
**Tier:** normal
**Purpose:** Walk a markdown directory (or a single `.md` file),
parse frontmatter, deduplicate by `body_sha256`, and insert into
`documents` + `tags` + `documents_fts`. Idempotent: re-running with
the same content reports `skipped_existing` and writes nothing.

```bash
node index.js --cmd "index <path>"
node index.js --cmd "index <path> --force"   # re-index even if unchanged
node index.js --cmd "index <path> --db=/custom/path/memory.db"
```

**Behavior contract:**

- Walks recursively; skips `node_modules/`, `.git/`, `.memory/`
- Tolerates broken frontmatter (per-file error captured in
  `error_details`; overall `errors` count) — does NOT abort the
  whole batch
- Derives missing `id` / `title` / `type` / `created_at` per spec
  §5.2
- Atomic per file: each file's documents + tags + FTS rows go in
  one transaction (rollback on error)

**Response data shape:**

```json
{
  "path": "/abs/path/to/dir",
  "scanned": 3,
  "indexed_new": 3,
  "skipped_existing": 0,
  "errors": 0,
  "total_docs_after": 3,
  "db_path": "/abs/path/to/.memory/memory.db",
  "db_size_bytes": 4096
}
```

If any files failed (e.g. parse_error), `error_details` is included
as an array of `{file, error}` objects.

### 2.3 `search`

**Action:** `memory.search`
**Tier:** safe
**Purpose:** FTS5 BM25 query against title + body + tags.

```bash
node index.js --cmd "search <query> [--limit=N] [--type=T] [--confidence=C] [--tag=X] [--include-superseded]"
```

The user's query is sanitized (FTS5 special chars `^"():*` stripped)
before being passed to `documents_fts MATCH ?`. Filters compose with
AND semantics. By default, documents with `confidence == 'superseded'`
are excluded; pass `--include-superseded` to include them.

**Response data shape:**

```json
{
  "query": "bugfix",
  "sanitized_query": "bugfix",
  "total_matches": 1,
  "returned": 1,
  "results": [
    {
      "id": "r_2026-04-15_modal-fix",
      "title": "Modal z-index black screen fix",
      "type": "retro",
      "confidence": "verified",
      "created_at": "2026-04-15",
      "source_path": "/abs/path/to/with-frontmatter.md",
      "score": -1.234,
      "snippet": "…the **bugfix** for the modal z-index issue…",
      "tags": ["bugfix", "css", "modal", "ui"]
    }
  ]
}
```

**Score** is the BM25 score (lower = more relevant per FTS5
convention).

### 2.4 `get`

**Action:** `memory.get`
**Tier:** safe
**Purpose:** Fetch a single document by id with full body, tags, and
supersession info.

```bash
node index.js --cmd "get <id> [--include-body=false]"
```

**Response data shape:**

```json
{
  "id": "r_2026-04-15_modal-fix",
  "title": "Modal z-index black screen fix",
  "type": "retro",
  "confidence": "verified",
  "created_at": "2026-04-15",
  "indexed_at": "2026-04-30T15:29:11.332Z",
  "word_count": 61,
  "source_path": "/abs/path/to/with-frontmatter.md",
  "tags": ["bugfix", "css", "modal", "ui"],
  "metadata": { "id": "r_2026-04-15_modal-fix", "title": "...", "...": "..." },
  "body": "# Modal z-index black screen fix\n\n## What happened\n...",
  "supersession": {
    "superseded_by": null,
    "supersedes": []
  }
}
```

If `--include-body=false`, the `body` field is omitted (useful for
large bodies). Returns `error.code: not_found` for unknown ids.

### 2.5 `list`

**Action:** `memory.list`
**Tier:** safe
**Purpose:** Browse documents with filters + sort + pagination.

```bash
node index.js --cmd "list [--type=T] [--confidence=C] [--tag=X] [--since=ISODATE] [--sort=FIELD[:asc|:desc]] [--limit=N] [--offset=N] [--include-superseded]"
```

`sort` field ∈ `{created_at, indexed_at, title}`; default
`created_at:desc`. `since` is compared lexically against
`documents.created_at` (ISO 8601 strings sort correctly as text).

**Response data shape:**

```json
{
  "total": 3,
  "returned": 3,
  "limit": 20,
  "offset": 0,
  "sort": "created_at:desc",
  "items": [
    {
      "id": "r_2026-04-20_no-frontmatter",
      "title": "Auth bug — session token exposed in error log",
      "type": "retro",
      "confidence": "draft",
      "created_at": "2026-04-20T00:00:00Z",
      "indexed_at": "2026-04-30T15:29:11.332Z",
      "word_count": 65,
      "source_path": "/abs/path/.../2026-04-20_no-frontmatter.md",
      "tags": []
    }
  ]
}
```

### 2.6 `learn`

**Action:** `memory.learn`
**Tier:** normal
**Purpose:** Add or update a single document. Two input modes —
`--file=<path>` (re-parse markdown via the indexer pathway, with
optional type / confidence overrides) or `--json=<inline>` (pass a
structured payload directly).

```bash
node index.js --cmd "learn --file=<path> [--type=<type>] [--confidence=<level>] [--force]"
node index.js --cmd "learn --json='<inline-json>'"
```

The `--json` payload must include `title` and `body` (required); `id`
is derived from `source_path` (if supplied) or a sha256 prefix when
absent. Default `type=retro`, `confidence=draft`, `created_at` =
current UTC. This verb remains available for direct memory writes and
legacy integrations. The Trinity `ai rrr` ritual must not call this
verb; it writes a canonical retro artifact and delegates ingestion via
`index <canonical retro path>`.

**Response data shape:**

```json
{
  "id": "r_2026-04-30_session-xyz",
  "indexed": true,
  "is_new": true,
  "source": "file",
  "source_path": "/abs/path/.ai/memory/retros/0009_…md",
  "type": "retro",
  "confidence": "draft"
}
```

When the same content is learned twice, `indexed: false`,
`is_new: false`, `reason: "unchanged"` (idempotent — sha256 dedupe
matches the indexer behavior).

### 2.7 `tag`

**Action:** `memory.tag`
**Tier:** normal
**Purpose:** Mutate the tag set for an existing document. Three
mutually exclusive modes:

```bash
node index.js --cmd "tag <id> +<tag>"            # add (idempotent)
node index.js --cmd "tag <id> -<tag>"            # remove (no-op if absent)
node index.js --cmd "tag <id> --set=<csv>"       # replace whole set
```

The denormalized `documents_fts.tags` column is resynced on every
mutation, so `search --tag=<x>` keeps working post-update.

**Response data shape:**

```json
{
  "id": "r_2026-04-15_modal-fix",
  "tags": ["bugfix", "css", "modal", "ui", "critical"],
  "added": ["critical"],
  "removed": []
}
```

### 2.8 `supersede`

**Action:** `memory.supersede`
**Tier:** aggressive
**Purpose:** Mark a document obsolete in favor of a newer one. The
old document's `confidence` is set to `superseded` and a row is
written to the `supersession` table. "Nothing is Deleted" — the
old doc remains queryable via `--include-superseded`.

```bash
node index.js --cmd "supersede <old_id> --by=<new_id> [--reason='...']"
```

**Validation:**
- both ids must exist (else `not_found`)
- self-supersede rejected (`supersede_invalid`)
- a doc that's already superseded cannot be re-superseded
  (`already_superseded`); chain forward instead
  (`supersede <new_id> --by=<newer_id>`)

**Response data shape:**

```json
{
  "superseded_id": "r_with-broken-yaml",
  "superseded_by_id": "r_2026-04-15_modal-fix",
  "reason": "broken FM replaced",
  "superseded_at": "2026-04-30T16:00:00.000Z"
}
```

### 2.9 `reflect`

**Action:** `memory.reflect`
**Tier:** safe
**Purpose:** Surface a single random document — "lesson of the day"
or surprise-pull from the Brain. Optionally narrowed by topic
(FTS5) and/or type. Excludes superseded by default.

```bash
node index.js --cmd "reflect [--topic=<keyword>] [--type=<type>] [--include-superseded] [--include-body=false]"
```

**Response data shape:**

```json
{
  "topic": "auth",
  "type": null,
  "candidate_count": 1,
  "document": {
    "id": "r_2026-04-20_no-frontmatter",
    "title": "Auth bug — session token exposed in error log",
    "tags": [],
    "body": "…",
    "supersession": { "superseded_by": null, "supersedes": [] }
  }
}
```

When the filter set produces zero candidates, `candidate_count: 0`
and `document: null` — never an error, callers can branch on the
count.

### 2.10 `delete`

**Action:** `memory.delete`
**Tier:** aggressive
**Purpose:** Permanently remove a document. Default Trinity
philosophy is "Nothing is Deleted" (use `supersede`); this verb is
the explicit escape hatch for sensitive content / wrongly-ingested
data.

```bash
node index.js --cmd "delete <id> [--force]"
```

**Validation:**
- `not_found` if the id does not exist
- `delete_blocked` if the doc is part of a supersession chain
  (either side); pass `--force` to break the chain on delete

**Cascade:** removes from `documents` + `tags` + `documents_fts` +
`evidence_links`; with `--force` also removes related
`supersession` rows.

**Response data shape:**

```json
{
  "id": "r_bad_data",
  "deleted": true,
  "forced": false,
  "removed": {
    "supersession": 0,
    "tags": 4,
    "evidence_links": 0,
    "documents_fts": 1,
    "documents": 1
  }
}
```

### 2.11 `reindex`

**Action:** `memory.reindex`
**Tier:** aggressive
**Purpose:** Rebuild the FTS5 index. Default mode regenerates
`documents_fts` from existing `documents` rows (cheap; useful after a
tokenizer change). With `--from-source`, re-walks every distinct
`source_path` on disk and re-runs the indexer (force=true).

```bash
node index.js --cmd "reindex [--from-source]"
```

**Behavior:**
- default mode runs in a single transaction; FTS is empty during
  the rebuild window — search returns no hits transiently
- `--from-source` does NOT use an outer transaction (the per-file
  indexer uses its own); a mid-rebuild crash leaves earlier files
  committed and later ones unindexed — re-run is idempotent
- missing source files are recorded in `missing_files` and the
  doc's prior FTS row is regenerated from the documents copy
  (the doc remains queryable; deletion is opt-in via `delete`)

**Response data shape:**

```json
{
  "mode": "from-source",
  "total_docs": 254,
  "rebuilt": 252,
  "missing_files": ["/abs/path/that/disappeared.md"],
  "missing_count": 1
}
```

### 2.12 `health` (verb)

**Action:** `memory.health`
**Tier:** safe
**Purpose:** DB integrity + cross-table consistency check. **Distinct
from the `--health` CLI flag**, which is a tool-level liveness probe
("can the binary parse args?"). The verb opens the DB and runs
structural checks.

```bash
node index.js --cmd "health"
node index.js --health           # different — liveness probe only
```

**Checks (in order):**
1. `PRAGMA integrity_check`        — SQLite page-level structure
2. `PRAGMA foreign_key_check`      — broken FK rows
3. FTS row-count parity            — `documents.count == documents_fts.count`
4. Tag orphans                     — `tags.document_id` not in `documents`
5. Supersession references         — both ids exist in `documents`
6. Schema version pin              — `_meta.schema_version` matches code

**Status verdict:**
- `pass` — all checks clean
- `warn` — non-blocking inconsistency (e.g. FTS drift, fixable by
  `reindex`)
- `fail` — SQLite reports corruption or FK is broken

**Response data shape:**

```json
{
  "status": "warn",
  "checks": [
    { "name": "integrity_check",   "status": "pass" },
    { "name": "foreign_key_check", "status": "pass" },
    { "name": "fts_row_parity",    "status": "warn",
      "docs": 254, "fts": 247,
      "detail": "documents and documents_fts row counts differ — run `reindex`" },
    { "name": "tag_orphans",       "status": "pass" },
    { "name": "supersession_refs", "status": "pass" },
    { "name": "schema_version",    "status": "pass", "version": "1" }
  ],
  "summary": { "pass": 5, "warn": 1, "fail": 0 }
}
```

> **Note on the v0.7 vector layer.** Two embedding subsystems coexist
> in memory-cli at the time of this contract revision:
>
> 1. **Verb path** (`embed`, `similar`) uses `lib/embed.js` providers
>    — currently one built-in: `'fake'` (deterministic sha256-derived,
>    **64-dim**). Stored in `documents.embedding` BLOB +
>    `documents.embedding_provider` + `documents.embedding_dim`.
> 2. **Action-chain path** (run on every `learn` unless `skip_chain`)
>    uses `lib/embed_chain.js` — fastembed-js, **1024-dim** MLE5Large
>    (or the deterministic 1024-dim mock when `MEMORY_CLI_MOCK_EMBED=1`).
>    Stored in the `vec_records` sqlite-vec table.
>
> The two systems do not share storage. `similar` does not see docs
> that were only fastembed'd via the action chain; `map` (PCA) does
> not see docs that were only `embed`'d through the verb path. This
> is a real implementation artifact, not a contract specification —
> the spec calls for unification but it has not landed yet.

### 2.13 `embed`

**Action:** `memory.embed`
**Tier:** normal
**Purpose:** Batch-compute provider embeddings for documents in the
DB that don't have one yet. Iterates `documents` rows where
`embedding IS NULL OR embedding_provider != <provider>`, embeds
`title + "\n\n" + body` via the named provider, and writes the
result back to the `documents` row (`embedding`,
`embedding_provider`, `embedding_dim`, `embedded_at`).

```bash
node index.js --cmd "embed [--provider=fake] [--limit=N] [--force]"
```

**Behavior:**
- Default `--provider=fake` (currently the only built-in provider —
  deterministic 64-dim sha256-derived; not semantic). The provider
  interface (`name`, `dim ≥ 4`, `embed(text)`) is open; real providers
  register themselves via `embedMod.registerProvider()`.
- Default `--limit=100` per invocation; raise it for one-shot
  backfill of larger corpora.
- `--force` re-embeds even rows that already have a row for this
  provider; otherwise the WHERE clause skips them.
- Returns `embed_provider_unknown` if `--provider=<name>` is not in
  `PROVIDERS`. Returns `embed_failed` (with `last_id`) on per-row
  exception. Returns `db_not_found` if no DB exists yet.
- **Not connected to the action-chain embedder.** The 1024-dim
  fastembed pipeline used by `learn`'s action chain writes
  `vec_records`, not `documents.embedding` — see the note at the top
  of §2.13.

**Response data shape:**

```json
{
  "provider": "fake",
  "provider_dim": 64,
  "scanned": 12,
  "embedded": 12,
  "remaining": 0,
  "limit": 100,
  "force": false
}
```

### 2.14 `similar`

**Action:** `memory.similar`
**Tier:** safe
**Purpose:** Cosine-similarity search over `documents` rows that
already carry a `documents.embedding` BLOB for the named provider.
This is `similar <query>` — a free-text query that is embedded by
the provider on the fly and compared against stored embeddings —
**not** "neighbors of an existing doc id".

```bash
node index.js --cmd "similar <query> [--provider=fake] [--limit=N] [--type=...] [--confidence=...] [--include-superseded]"
```

**Behavior:**
- Requires a non-empty query token (else `missing_argument` at
  dispatch, or `similar_invalid_input` from the impl)
- Default `--provider=fake` (64-dim). Unknown provider →
  `embed_provider_unknown`
- Pure-JS scan over all rows where `embedding IS NOT NULL AND
  embedding_provider = <provider>`; OK for ≤10K docs. A dedicated
  vector store is roadmap.
- Excludes `confidence='superseded'` unless `--include-superseded`
- `--type` / `--confidence` add WHERE clauses (AND semantics)
- Results sorted by `score` DESC (cosine similarity — higher is
  more similar; range [-1, 1] for L2-normalized vectors)

**Response data shape:**

```json
{
  "query": "auth bug",
  "provider": "fake",
  "provider_dim": 64,
  "total_candidates": 12,
  "total_matches": 3,
  "returned": 3,
  "results": [
    {
      "id": "r_2026-04-20_no-frontmatter",
      "title": "Auth bug — session token exposed",
      "type": "retro",
      "confidence": "draft",
      "created_at": "2026-04-20T00:00:00Z",
      "source_path": "/abs/path/...",
      "score": 0.847
    }
  ]
}
```

### 2.15 `map`

**Action:** `memory.map`
**Tier:** safe
**Purpose:** PCA 2D/3D projection of all `vec_records` (the
1024-dim action-chain embeddings, NOT `documents.embedding`) for
visualization. Caches results in `vec_pca_2d` / `vec_pca_3d`;
recomputes when the cached row-count drifts more than 10%
(`STALE_THRESHOLD`) or on `--force`. SVD via `ml-pca` is run on 3
components and sliced for 2D / 3D.

```bash
node index.js --cmd "map [--dim=2|3] [--out=<path>] [--color-by=tag|project] [--force] [--no-labels] [--radius=N] [--width=N] [--height=N] [--format=svg|json]"
```

**Behavior:**
- Requires the sqlite-vec extension to be loaded (`db._vec_table_ready`)
  — else `pca_no_vec_backend`
- Requires ≥ 5 `vec_records` rows — else `pca_insufficient_records`
  (below this the projection is mostly noise)
- `--dim` ∈ {2, 3}; default 2
- `--format` ∈ {`svg`, `json`}; default inferred from `--out`
  extension, else `json`. SVG with `--dim=3` silently degrades to
  JSON because 3D-to-screen projection is the operator's choice
  (d3.js / three.js / plotly consume the JSON).
- `--out=<path>` writes the artifact to disk (creating parent dirs);
  without `--out` the body is returned inline (`svg` field for SVG,
  `points` array for JSON).
- `--color-by` ∈ {`tag`, `project`}; hashes the value into a
  12-color palette. Project requires the v0.9 `project` column.
- SVG: one `<circle>` per record; optional id labels suppressible
  via `--no-labels`. viewBox auto-fits with 10% padding. Font stack
  picks up system Thai/CJK fonts (Sukhumvit Set / Noto Sans Thai /
  Noto Sans CJK).

**Response data shape (JSON):**

```json
{
  "dim": 2,
  "format": "json",
  "record_count": 42,
  "cached": true,
  "computed_at": "2026-05-09T14:23:11.000Z",
  "color_by": "tag",
  "out": null,
  "points": [
    { "id": "r_x", "x": 0.123, "y": -0.456, "tags": ["bugfix"], "project": "trinity_v2" }
  ]
}
```

**Response data shape (SVG):**

```json
{
  "dim": 2,
  "format": "svg",
  "record_count": 42,
  "cached": true,
  "computed_at": "2026-05-09T14:23:11.000Z",
  "out": "/abs/path/map.svg",
  "svg": null
}
```

When `--out` is omitted, `out: null` and the inline body lives in
`svg` (SVG path) or `points` (JSON path). Top-level `artifacts: []`
is not populated by this verb.

### 2.16 `thread`

**Action:** `memory.thread`
**Tier:** normal
**Purpose:** Create a parent→child relation row in the `threads`
table. Used to model session continuation and document lineage.

```bash
node index.js --cmd "thread <child_id> --parent=<parent_id> [--relation-type=<type>] [--relation=<type>]"
```

**Behavior:**
- Both `<child_id>` (positional) and `--parent=<id>` are required
  (else `missing_argument` at dispatch)
- Self-thread (child == parent) rejected with `thread_self_cycle`
  before any DB write
- DFS up the parent's ancestor chain at INSERT — rejects with
  `thread_cycle_detected` if `<child_id>` is already an ancestor
- Idempotent: the underlying SQL is `INSERT OR IGNORE` keyed on
  (parent, child, relation_type); a duplicate call returns
  `inserted: false` instead of erroring
- **Default `relation_type` is `'session_continuation'`** (not
  `'manual'`). This matches the auto-thread path on `learn`
  (Phase 8 of the action chain reads
  `metadata.parent_session_id` and threads with the same default).
  Operators wanting a different label pass `--relation-type=manual`
  (or `--relation=manual`) explicitly.

**Response data shape:**

```json
{
  "ok": true,
  "inserted": true,
  "parent_id": "session_J",
  "child_id": "session_K",
  "relation_type": "session_continuation"
}
```

(The `ok: true` inside `data` is an artifact of the impl returning
its own success envelope; the outer envelope's `ok` is the
canonical one for kernel consumers.)

### 2.17 `thread-of`

**Action:** `memory.thread_of`  ← note the underscore, not a dash
**Tier:** safe
**Purpose:** Inspect a record's thread context — direct parents
and children plus recursive ancestors and descendants with the
longest ancestor path length.

```bash
node index.js --cmd "thread-of <id>"
```

**Behavior:**
- `<id>` is required (else `missing_argument`)
- DFS up (ancestors) and down (descendants); a `visited` set
  guards against any pre-existing cycle in the data
- `parents` / `children` are the **full row** objects with
  `relation_type` and `created_at`
- `ancestors` / `descendants` are flat lists of ids
- `depth` is the longest ancestor path length (number of edges up
  to the deepest reachable ancestor)
- Returns empty arrays (no error) when the doc has no relations

**Response data shape:**

```json
{
  "id": "session_K",
  "parents": [
    {
      "parent_id": "session_J",
      "relation_type": "session_continuation",
      "created_at": "2026-05-09T15:00:00.000Z"
    }
  ],
  "children": [],
  "ancestors": ["session_J", "session_I"],
  "descendants": [],
  "depth": 2
}
```

### 2.18 `unthread`

**Action:** `memory.unthread`
**Tier:** aggressive
**Purpose:** Remove a thread edge between a parent and a child.
Idempotent — removing a non-existent edge returns
`removed: false` without erroring.

```bash
node index.js --cmd "unthread <child_id> --parent=<parent_id> [--relation-type=<type>]"
```

**Behavior:**
- Both `<child_id>` (positional) and `--parent=<id>` are required
  (else `missing_argument`)
- If `--relation-type=<type>` is supplied, only that exact triple
  is removed
- If `--relation-type` is omitted, **all edges** between the pair
  are removed regardless of `relation_type`. (This differs from
  `thread`'s default-of-session_continuation behavior.)
- Does not cascade — descendants of `<child_id>` keep their own
  edges intact

**Response data shape:**

```json
{
  "ok": true,
  "removed": true,
  "removed_count": 1,
  "parent_id": "session_J",
  "child_id": "session_K",
  "relation_type": "session_continuation"
}
```

`relation_type` is `null` in the response when the call omitted it
(i.e. the "remove all between pair" mode).

### 2.19 `note`

**Action:** `memory.note`
**Tier:** normal
**Purpose:** Quick-capture wrapper over `learn` for low-latency note
intake (v0.9.1 Operational Brain capture surface). Assembles a
`{type:'note', confidence:'draft'}` document, tags it
`quick-capture`, records metadata, and delegates the write to
`learnFromJson(db, json, { skip_chain: true })` — single ingress for
INSERT + FTS5 + project tagging, but **bypassing the 7-phase action
chain** (so no auto-tag / embed / cross-link fan-out at capture
time).

```bash
node index.js --cmd 'note <text> [--source=<src>] [--capture-mode=<mode>] [--project=<name>]'
node index.js --cmd 'note --text="<text>" [--source=<src>] ...'
```

**Behavior:**
- Text source: positional tokens joined by spaces (with a defensive
  unwrap of one outer quote pair), OR `--text=<...>` to bypass
  shell-quoting entirely. Empty / whitespace-only text returns
  `invalid_input`.
- Generated id: `note_<unix_ms>_<6 hex chars>` (e.g.
  `note_1715430000000_b3a91f`).
- Defaults: `source='cli'`, `capture_mode='quick'`, project from
  the standard v0.9 detection chain (flag > env > ssot.yaml > cwd).
- Document fields injected: `title = text.slice(0, 80)`,
  `body = text.trim()`, `tags = ['quick-capture']` (+ caller-supplied
  via the underlying impl `opts.tags`, though the CLI dispatcher
  does not currently expose `--tag`).
- Metadata recorded: `{ source, capture_mode, captured_at }`.
- New rows land with `status='inbox'` (default of the v0.9.1
  `documents.status` column) — operators surface via
  `list --status=inbox` for digest review. (The CLI does not yet
  ship a `--status` filter on `list`; that is roadmap.)
- **No `--with-chain` flag.** If you want the chain to run, use
  `learn` directly with a `{type:'note'}` payload.

**Response data shape** (inherited from `learn`):

```json
{
  "id": "note_1715430000000_b3a91f",
  "indexed": true,
  "is_new": true,
  "source": "json",
  "type": "note",
  "confidence": "draft"
}
```

---

## 3. Response Envelope (TOOL_CONTRACT v1)

Every command must return a JSON object on stdout matching:

```json
{
  "ok": true | false,
  "schema_version": "1.0",
  "tool": "memory-cli",
  "tool_version": "0.9.2-beta",
  "command": "stats" | null,
  "action": "memory.stats" | null,
  "data": { ... } | null,
  "artifacts": [],
  "error": null | { "code": "...", "message": "...", ... },
  "meta": { "ts": "<iso>" }
}
```

- **`ok`** mirrors `error == null`.
- Process exit code: `0` if `ok`, `1` otherwise.
- `meta.ts` must be an RFC 3339 / ISO-8601 UTC timestamp.

---

## 4. Error Codes

| Code | When | Recovery |
|------|------|----------|
| `no_command` | Neither `--cmd` nor `--health` provided | Pass `--cmd "<verb>"` |
| `unsupported_verb` | Verb not in §2 | Use a verb listed in `error.supported_verbs` |
| `missing_argument` | `index` called without a path argument | Provide `--cmd "index <path>"` |
| `path_not_found` | `index` path does not exist | Verify the path |
| `db_not_found` | search / get / list called before any `index` | Run `index <path>` first |
| `not_found` | `get` / `tag` / `supersede` for an unknown id | Check id; use `list` to find ids |
| `not_a_file` | `learn --file=` pointed to a directory | Pass a regular file |
| `learn_invalid_input` | `learn` called without input, with both inputs, or with malformed `--json` (missing title/body, bad JSON) | Pass exactly one of `--file=` or `--json=` with required fields |
| `learn_failed` | `learn --file=` produced a parse error in non-tolerant mode | Inspect file frontmatter |
| `tag_invalid_input` | `tag` called without a mutation token (`+x` / `-x` / `--set=`) or mixed modes | Use a single mutation per call |
| `supersede_invalid` | `supersede <id> --by=<id>` with the same id on both sides | Pick distinct ids |
| `already_superseded` | `<old_id>` already has a supersession row | Chain forward (`supersede <new_id> --by=<newer_id>`) |
| `reflect_invalid_input` | `reflect --topic=` sanitized to empty (only FTS5 special chars) | Pass real keywords |
| `delete_blocked` | `delete <id>` rejected because id is in a supersession chain | Re-run with `--force` (also removes chain rows) |
| `embed_provider_unknown` | `embed` / `similar` called with `--provider=<name>` not registered in `lib/embed.js` | Use `--provider=fake` (the only built-in) or register a provider |
| `embed_failed` | Per-row exception while embedding inside `embed` (see `error.last_id`) | Inspect that doc; rerun with `--force` after fix |
| `embed_disabled` | `MEMORY_CLI_NO_EMBED=1` is set while the action-chain embedder is called | Unset the env var or set `MEMORY_CLI_MOCK_EMBED=1` for tests |
| `similar_invalid_input` | `similar` called with whitespace-only query | Pass real text |
| `pca_insufficient_records` | `map` called with fewer than 5 `vec_records` rows | Learn / embed more docs (≥5) before mapping |
| `pca_no_vec_backend` | `map` cannot run — sqlite-vec extension not loaded or `vec_records` table absent | Install sqlite-vec + run at least one `learn` (so the action chain populates `vec_records`) |
| `pca_failed` | Other unhandled failure inside `pca.computePca()` | See `error.message` |
| `thread_self_cycle` | `thread <id> --parent=<id>` (self parent) | Pick distinct ids |
| `thread_cycle_detected` | `thread <child> --parent=<parent>` where child is already an ancestor of parent | Restructure the lineage; cycles are not permitted |
| `thread_missing_argument` | `thread.thread()` / `thread.unthread()` called without `childId` / `parentId` (impl-level — dispatcher returns `missing_argument` first) | Pass both ids |
| `thread_failed` / `thread_of_failed` / `unthread_failed` | Other unhandled failure in the thread verbs | See `error.message` |
| `invalid_input` | `note` called without text, or with empty/whitespace-only text (also returned when the impl is invoked without a `db` handle) | Pass a non-empty text token |
| `note_failed` | Other unhandled failure inside the `note` verb wrapper | See `error.message` |
| `internal_error` | Uncaught exception in dispatch | See `error.message`; set `MEMORY_CLI_DEBUG=1` for stack trace |

All 19 verbs are wired at v0.9.2. Future surface area on this
contract: inbox/digest workflow (no `digest` verb yet), forget /
decay criteria, recall instrumentation, **unification of the two
embedding paths** (verb-level `documents.embedding` vs action-chain
`vec_records`). Each will land a new error code rather than reusing
an existing one.

---

## 5. Tier Defaults

Per `.ai/tools.yaml`, memory-cli's `policy_default` is `safe` —
appropriate for read-mostly recall verbs. Per-verb tiers:

| Tier | Verbs |
|------|-------|
| `safe` | `stats`, `search`, `get`, `list`, `reflect`, `health`, `similar`, `map`, `thread-of` |
| `normal` | `index`, `learn`, `tag`, `embed`, `thread`, `note` |
| `aggressive` | `supersede`, `delete`, `reindex`, `unthread` |

---

## 6. Out of Scope (current, at v0.9.2)

Listed here so the next contract review can confirm what is
intentionally deferred:

- **Inbox / digest workflow** — `documents.status` column shipped
  in v0.9.1 (foundation), but no `digest` verb, no auto-promote
  from `inbox`, no scheduled summary.
- **Memory promotion policy** — no `confidence_score`, no
  `staleness`, no `learning → doctrine` auto-promotion, no
  contradiction detection. Only `supersede` (manual).
- **Forget criteria** — every doc is permanent until explicit
  `delete --force`. No decay, no archival, no TTL.
- **Recall instrumentation** — `v07_stats` counts verb
  invocations but does not track "search hit utility"
  (queries → action follow-through, top no-result queries, etc.).
- **Row-level project isolation** — `TRINITY_CENTRAL_DB` is a
  shared pool; any caller can read any project's docs. Not
  suitable for multi-tenant deployments.
- **BGE-M3 model** — spec target, but no Node.js binding ships
  it; v0.7 hardcodes MLE5Large instead. Tracked but blocked on
  upstream.
- **3D SVG rasterization** — `map --dim=3 --format=svg` degrades
  to JSON; operators consume via d3.js / three.js / plotly.
- **Native destructor race** — `closeAllOpenHandles()` mitigates
  locally but upstream sqlite-vec / fastembed destructor ordering
  is not fixed. See `memory-cli/docs/R48_DESTRUCTOR_RACE.md`.

Older "alpha out-of-scope" items (SQLite + FTS5, indexer,
the 11 v0.5 verbs) are all now shipped — they have moved into §2.

---

## 7. Versioning Rule

When Phase 2.1 lands real verbs, bump:

- `tool_version` in `index.js` and `package.json` (e.g. `0.2.0`)
- `contract_version` in `.ai/tools.yaml` (e.g. `0.2-beta`)
- This file's "Status" line and §2 verb table
- A new dated changelog entry at the bottom of this file

If a *breaking* change to envelope shape is needed (rare), bump
`schema_version` to `2.0` and create a new directory
`docs/contracts/memory-cli/v2/` rather than overwriting v1 here.

---

## Changelog

- **2026-05-10** — v0.9.2-beta — Destructor-race workaround. No
  verb / schema changes. `lib/db.js` exposes `closeAllOpenHandles()`
  invoked before process exit; `index.js` wraps the CLI dispatcher
  in `if (require.main === module)` for safe library-mode imports.
  Eliminates the false-negative `memory_learn ok=false
  returncode=-6` reported by `ai rrr` on macOS (caused by the
  sqlite-vec native destructor racing V8 teardown). See
  `memory-cli/docs/R48_DESTRUCTOR_RACE.md`. tool_version bumped to
  `0.9.2-beta`. 190 internal tests passing.
- **2026-05-10** — v0.9.1-beta — Operational Brain capture surface.
  New verb `note` — quick-capture wrapper over `learn` (type=note,
  confidence=draft, tag=quick-capture, hardcoded `skip_chain=true`
  in the wrapper). Schema 5→6: idempotent `ALTER TABLE documents
  ADD COLUMN status TEXT DEFAULT 'inbox'` + `idx_docs_status`
  foundation for the inbox/digest workflow. New error code:
  `invalid_input` (reused — note returns this, not a note-specific
  code). tool_version bumped to `0.9.1-beta`. 188 internal tests
  passing.
- **2026-05-10** — v0.9.0-beta — Central project tagging. Adds
  `documents.project` column (idempotent ALTER, schema 4→5) +
  `lib/project_detect.js` resolution chain (flag > `TRINITY_PROJECT`
  env > parent-dir `ssot.yaml` `name:` > cwd basename).
  `TRINITY_CENTRAL_DB` env redirects writes to a shared DB so
  multiple sibling projects can feed one brain. New `search`
  filters: `--project=<csv>` and `--project-not=<csv>`. `stats` now
  reports `by_project` breakdown. `map` accepts `--color-by=project`.
  No new verbs. tool_version bumped to `0.9.0-beta`. 180 internal
  tests passing.
- **2026-05-09** — v0.8.0-beta — PCA visualization + threading.
  New verbs: `map` (PCA 2D/3D via ml-pca; caches in `vec_pca_2d` /
  `vec_pca_3d` with 10% drift `STALE_THRESHOLD`; SVG output for
  2D, JSON for 3D), `thread` / `thread-of` / `unthread`
  (parent-child relations in `threads` table with DFS cycle
  detection at INSERT). Schema 3→4: 3 new tables (`vec_pca_2d`,
  `vec_pca_3d`, `threads`). Action chain extended to Phase 8 —
  auto-thread from `metadata.parent_session_id` on `learn`. New
  error codes: `pca_insufficient_records`, `pca_no_vec_backend`,
  `thread_self_cycle`, `thread_cycle_detected`. New dep:
  `ml-pca ^4.1.1` (pure JS, no native builds). tool_version bumped
  to `0.8.0-beta`. 164 internal tests passing.
- **2026-05-09** — v0.7.0-beta — Vector layer + action chain. New
  verbs: `embed` (per-doc sqlite-vec embedding via fastembed-js,
  default MLE5Large 1024-dim) and `similar` (KNN over
  `vec_records`). New flag: `search --hybrid` (FTS5 BM25 + vector
  RRF fusion). 7-phase action chain on every `learn`: INSERT →
  auto-tag (YAML rules) → FTS5 → embed → cross-link (KNN) → audit
  → stats. `chain.errors[]` + `partial: true` keep INSERT atomic
  when later phases fail. Schema 2→3: `vec_records`, `vec_id_map`,
  `v07_tags`, `v07_stats`, `evidence_links` tables added. New deps:
  `fastembed ^2.1.0` and `sqlite-vec ^0.1.9`. `MEMORY_CLI_MOCK_EMBED=1`
  hooks the embedder with a sha256-derived deterministic vector for
  CI. New error codes: `embed_provider_unknown`, `embed_failed`,
  `embed_disabled`, `similar_invalid_input`. tool_version bumped to
  `0.7.0-beta`. 148 internal tests passing. CAVEAT: this baseline
  shipped two embedding subsystems that do not share storage — the
  64-dim provider path (`embed` / `similar` verbs writing
  `documents.embedding`) and the 1024-dim action-chain path
  (`learn` writing `vec_records` via sqlite-vec). Unification is
  roadmap.
- **2026-05-09** — v0.6.0-beta — Phase 9 legacy slice. Added
  initial `embed` and `similar` verbs as scaffolding (later
  hardened in v0.7). Schema 1→2. tool_version bumped to `0.6.0-beta`.
- **2026-05-01** — v0.5-beta — Phase 2.3: `delete` + `reindex` +
  `health` (as a verb) wired. All 12 spec verbs now live. `delete`
  is aggressive with chain-protection (`--force` to break);
  `reindex` rebuilds FTS from documents (default) or re-walks source
  paths (`--from-source`); `health` (verb) runs PRAGMA
  integrity_check + foreign_key_check + cross-table consistency
  (vs the existing `--health` CLI flag which is a liveness probe).
  New error code: `delete_blocked`. Per-verb tier table updated.
  tool_version bumped to `0.5.0-beta`. 93 internal tests passing
  (was 76).
- **2026-04-30** — v0.4-beta — Phase 2.2: `learn` + `tag` + `supersede`
  + `reflect` verbs wired. `learn` accepts `--file=<path>` (re-parse
  via indexer) or `--json=<inline>` (structured payload). Historical
  retro ingestion used this verb; the current RRR Delegation Contract
  uses `index` for artifact ingestion.
  `tag` supports `+x` / `-x` / `--set=csv` with FTS5 resync.
  `supersede` records "Nothing is Deleted" chain (refuses self- and
  re-supersede). `reflect` returns a random doc, optionally narrowed
  by topic / type. New error codes: `learn_invalid_input`,
  `learn_failed`, `not_a_file`, `tag_invalid_input`,
  `supersede_invalid`, `already_superseded`,
  `reflect_invalid_input`. tool_version bumped to `0.4.0-beta`.
  Per-verb tier table added to §5. 76 internal tests passing
  (was 33).
- **2026-04-30** — v0.3-beta — Phase 2.1b: `search` + `get` + `list`
  verbs wired. FTS5 BM25 ranking + sanitization, supersession joins
  in `get`, filter/sort/paginate in `list`. New error codes:
  `db_not_found`, `not_found`. tool_version bumped to `0.3.0-beta`.
  33 internal tests passing.
- **2026-04-30** — v0.2-beta — Phase 2.1a: `index` verb wired
  (SQLite + FTS5 standalone via Node 22+ `node:sqlite`); `stats` now
  reads real DB counts. tool_version bumped to `0.2.0-beta`.
- **2026-04-30** — v0.1-alpha — initial baseline (1 verb: `stats`).
