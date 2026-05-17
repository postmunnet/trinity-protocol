---
title: "memory-cli Specification"
subtitle: "Knowledge Brain — FTS5 + sqlite-vec hybrid + action chain + central project tagging + Operational Brain capture"
version: 0.9.1-beta
status: draft
last-updated: 2026-05-10
phase: 2
implements: TOOL_CONTRACT v1.1
---

## v0.9.1 Changelog (2026-05-10) — Operational Brain Session 1

- **`note` verb (NEW)** — quick-capture wrapper over `learn`. Inserts
  `{type:'note', confidence:'draft', tags:['quick-capture', ...]}` with
  `metadata: {source, capture_mode, captured_at}`. Default `source='cli'`;
  trinity-tg-bot v0.3 passes `--source=tg-bot`. Skips the action chain by
  default (`skip_chain=true`) to keep capture latency low — the inbox
  digest reflector is the consumer that runs heavier passes later.
  ID format: `note_<epoch_ms>_<random_hex6>`. Implementation:
  `lib/verbs/note.js` (thin wrapper) + `noteAction()` in `index.js`
  dispatch.
- **`documents.status TEXT DEFAULT 'inbox'` (NEW column)** — additive
  schema migration via idempotent `ALTER TABLE documents ADD COLUMN
  status TEXT DEFAULT 'inbox'` + `CREATE INDEX IF NOT EXISTS
  idx_docs_status ON documents(status)`. New INSERTs that omit the
  column receive 'inbox'; legacy rows keep NULL until next learn.
  Foundation for the Operational Brain inbox/digest workflow (consumer
  ships in a follow-up session).
- **SCHEMA_VERSION 5 → 6.** WAL mode preserved.
- **No new npm deps.**
- **CLI form:** `--cmd 'note <text> [--source=<tag>] [--project=<name>]'`
  (text token is reassembled from positional args; `--text=` override
  also accepted to skip shell-quoting entirely).
- **Operator usage from TG:** `/note <free-form text>` →
  `trinity-tg-bot/lib/flow/note.js` spawns memory-cli `note` →
  envelope.data.id surfaced in TG reply.
- **Tests:** +7 unit tests (5 note-verb cases + 2 status-column cases).
  Total memory-cli unit tests: 186 (179 v0.9 + 7 v0.9.1) green via
  `MEMORY_CLI_MOCK_EMBED=1 node --test tests/*.test.js`.

Bumps to **v0.9.1-beta**.

## v0.9 Changelog (2026-05-10)
- **Central project tagging** — foundation for cross-project Trinity knowledge graph. `documents.project TEXT` column added via idempotent ALTER TABLE migration. Auto-detect at learn-time via chain: explicit `--project=<name>` flag > `TRINITY_PROJECT` env > `<cwd>/.ai/ssot.yaml` `name:` field (walk up 6 levels) > `path.basename(cwd)` > `'default'`. Process-level cache.
- **`TRINITY_CENTRAL_DB` env** — overrides `defaultDbPath()` so every project's `ai rrr` writes into a shared DB without kernel involvement (`export TRINITY_CENTRAL_DB=~/.trinity/memory.db`).
- **Search filters** — `--project=<name>` (filter to one project) and `--project-not=<name>` (exclude one; NULL preserved so legacy unprojected rows still surface).
- **Map color-by-project** — `map --color-by=project` builds a stable palette (sorted distinct projects → palette indices; 'unassigned' is grey). Returns `legend: [{project, color}]` at envelope level.
- **Stats breakdown** — `stats` envelope now includes `data.by_project = {<name>: <count>, unassigned: <count>}`.
- **`records` view alias** — `CREATE VIEW records AS SELECT * FROM documents` lets external callers reasoning about "records" see the same shape (incl. project column).
- **Schema version → 5.** WAL mode preserved.
- **No new npm deps.** SSOT name parsing is a single-line regex (js-yaml not pulled in).
- **Tests:** 179 unit (115 v0.6 + 33 v0.7 + 16 v0.8 + 15 v0.9), 21 acceptance gates (15 baseline + 6 new — `A_PROJECT_COL`, `A_AUTO_DETECT`, `A_PROJECT_FLAG`, `A_CENTRAL_ENV`, `A_SEARCH_FILTER`, `A_STATS_BREAKDOWN`).

Bumps to **v0.9.0-beta**.

## v0.8 Changelog (2026-05-09)
- **PCA knowledge map** — project 1024-dim vec_records → 2D/3D coords via `ml-pca` (pure JS npm, no native deps). Cached in `vec_pca_2d` / `vec_pca_3d` tables. New CLI verb `map` outputs JSON or SVG (system font for Thai).
- **Document threading** — parent-child relations between records via `threads(parent_id, child_id, relation_type, created_at)` table. New verbs: `thread`, `thread-of`, `unthread`. Cycle detection via DFS; auto-detect from `metadata.parent_session_id` at learn-time (non-blocking).
- All v0.7 foundation preserved (action chain, fastembed BGE-family, sqlite-vec, hybrid search).
- Bumps to **v0.8.0-beta**

## v0.7 Changelog (2026-05-09)

- **Action chain** — every `learn` triggers 7 phases auto: insert → auto-tag → reindex(FTS5) → embed → cross-link → audit → stats. Phases 2-7 best-effort; INSERT atomic.
- **Embedding via `fastembed-js`** (Qdrant team, embedded Rust). NO Ollama, NO Python service — pure npm. Default model `MLE5Large` (1024-dim multilingual; fastembed-js v2.1 enum lacks BGEM3 — MLE5Large is closest spirit). Operator override via `MEMORY_CLI_EMBED_MODEL=<key>`.
- **sqlite-vec extension** — semantic search in same SQLite file via `vec_records` virtual table. NO separate vector DB service. Bridge table `vec_id_map(doc_id TEXT, vec_id INTEGER)` because vec0 requires INTEGER PK. L2-normalized vectors → cosine = `1 - dist²/2`.
- **Auto-tag rules** — YAML at `~/.config/memory-cli/auto_tag_rules.yaml` (operator override) + bundled `rubrics_or_rules/auto_tag_rules_default.yaml`. Derives tags from metadata fields + body keyword regex.
- **Cross-link** — top-3 cosine KNN; link if similarity ≥ 0.85 (configurable).
- **Own audit chain** — `~/.config/memory-cli/audit/ops.ndjson` hash-chained (sibling pattern; mirrors judge-cli/wp-cli/seo-genie).
- **Stats** — durable `v07_stats` SQLite table + per-write flush + opt-in hourly. Tracks verb/tool counters.
- **Hybrid search** — `--hybrid` flag merges FTS5 BM25 + sqlite-vec cosine via RRF fusion (k=60).
- **Migration** — `reindex --re-embed` backfills v0.6 records lacking embeddings; `shouldAutoMigrate()` detects v0.6 → v0.7 transition.
- **Trinity philosophy preserved** — NO external services (no ChromaDB, no Ollama). Pure Node 20+ + SQLite + npm.

Bumps to **v0.7.0-beta**.


# memory-cli Specification v1.0

> **memory-cli = Knowledge Brain recall organ**
>
> Index 240+ retros + 14 lessons → semantic recall ผ่าน CLI
> FTS5 first (Phase 2), ChromaDB hybrid later (Phase 9)

---

## 0. Status

- **Phase:** 2
- **Depends on:** Phase 1 (Tool Contract)
- **Reference DNA:** browser-cli pattern (CLI structure)
- **Memory architecture inspiration:** [arra-oracle-v3](https://github.com/Soul-Brews-Studio/arra-oracle-v3) — hybrid SQLite FTS5 + ChromaDB pattern (independent implementation, see [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §2.2)
- **Append-only philosophy inspiration:** [Oracle Framework](https://github.com/Soul-Brews-Studio/oracle-framework) — "Nothing is Deleted" (see [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §2.1)
- **Action namespace:** `memory.*`

---

## 1. Goals

### Core (Phase 2 — FTS5 only)
- Index existing markdown retros + lessons + summaries
- Full-text search (SQLite FTS5)
- Get document by ID
- List documents (filter by tag/date/confidence)
- Stats / health
- Add new document (from retro-cli)
- Mark superseded (chain tracking)

### Future (Phase 9 — Hybrid)
- Vector embeddings (ChromaDB or similar)
- Semantic similarity (`similar`)
- Hybrid ranking (FTS5 + vector merge)
- Visualization (`map` 2D/3D)

---

## 2. Architecture

```
┌─────────────────────────────────┐
│ memory-cli (Node.js)            │
│  • Stdin/stdout JSON contract   │
│  • Commands per TOOL_CONTRACT   │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│ Indexer (lib/indexer.js)        │
│  • Walk source directories      │
│  • Parse markdown frontmatter   │
│  • Chunk by headers             │
│  • Insert to SQLite + FTS5      │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│ SQLite + FTS5                   │
│  Tables:                        │
│  - documents (metadata)         │
│  - documents_fts (full-text)    │
│  - tags (many-to-many)          │
│  - supersession (chain)         │
└─────────────────────────────────┘
```

---

## 3. Database Schema

### 3.1 SQLite Tables

```sql
-- documents: metadata
CREATE TABLE documents (
    id TEXT PRIMARY KEY,                    -- e.g. r_2025-11-24_modal-fix
    source_path TEXT NOT NULL,
    title TEXT NOT NULL,
    type TEXT NOT NULL,                     -- retro | lesson | summary | decision
    confidence TEXT NOT NULL DEFAULT 'draft', -- verified | draft | superseded
    created_at TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    body TEXT NOT NULL,                     -- markdown body
    body_sha256 TEXT NOT NULL,              -- for change detection
    word_count INTEGER NOT NULL,
    metadata_json TEXT                      -- frontmatter as JSON
);
CREATE INDEX idx_docs_type ON documents(type);
CREATE INDEX idx_docs_confidence ON documents(confidence);
CREATE INDEX idx_docs_created ON documents(created_at);

-- documents_fts: full-text index
CREATE VIRTUAL TABLE documents_fts USING fts5(
    title,
    body,
    tags,                                    -- denormalized for search
    content=documents,
    content_rowid=rowid,
    tokenize='unicode61 remove_diacritics 1'
);

-- tags: many-to-many
CREATE TABLE tags (
    document_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (document_id, tag),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX idx_tags_tag ON tags(tag);

-- supersession: track which doc replaces which
CREATE TABLE supersession (
    superseded_id TEXT NOT NULL,
    superseded_by_id TEXT NOT NULL,
    reason TEXT,
    superseded_at TEXT NOT NULL,
    PRIMARY KEY (superseded_id),
    FOREIGN KEY (superseded_id) REFERENCES documents(id),
    FOREIGN KEY (superseded_by_id) REFERENCES documents(id)
);

-- evidence_links: each doc may link to evidence artifacts
CREATE TABLE evidence_links (
    document_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,            -- file | url | log | screenshot
    artifact_ref TEXT NOT NULL,
    sha256 TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
```

### 3.2 Database Location

`<config.data_dir>/memory.db` (default: `./.memory/memory.db`)

---

## 4. Commands

### 4.1 Verb List

| Verb | Action | Tier | Purpose |
|------|--------|------|---------|
| `index` | `memory.index` | normal | Bulk index a directory |
| `learn` | `memory.learn` | normal | Add/update single document |
| `search` | `memory.search` | safe | FTS5 search |
| `get` | `memory.get` | safe | Get document by ID |
| `list` | `memory.list` | safe | List with filter |
| `stats` | `memory.stats` | safe | DB stats |
| `tag` | `memory.tag` | normal | Add/remove tag |
| `supersede` | `memory.supersede` | aggressive | Mark obsolete |
| `reflect` | `memory.reflect` | safe | Random/topical retrieval |
| `delete` | `memory.delete` | aggressive | Permanent delete (rare) |
| `reindex` | `memory.reindex` | aggressive | Full rebuild |
| `health` | `memory.health` | safe | DB integrity check |

### 4.2 Command: `index`

```bash
memory-cli --cmd "index <path> [--type=<type>] [--confidence=<level>] [--dry-run]"
```

**Examples:**
```bash
memory-cli --cmd "index .claude/retrospectives/"
memory-cli --cmd "index ai-docs/real_lessons/ --type=lesson"
memory-cli --cmd "index .ai/sessions/sess_xyz/99_SUMMARY.md --type=summary"
```

**Behavior:**
- Walk directory recursively (or single file)
- Detect markdown files
- Parse frontmatter (if present)
- Auto-derive `id` from filename if no frontmatter
- Auto-derive `type` from path (retrospectives/ → retro, real_lessons/ → lesson)
- Skip already-indexed (by sha256) unless `--force`
- Default confidence: `draft` (until manually set `verified`)

**Response:**
```json
{
  "ok": true,
  "command": "index",
  "action": "memory.index",
  "data": {
    "path": ".claude/retrospectives/",
    "scanned": 240,
    "indexed_new": 240,
    "skipped_existing": 0,
    "errors": 0,
    "total_docs_after": 254
  }
}
```

### 4.3 Command: `search`

```bash
memory-cli --cmd "search '<query>' [--limit=<n>] [--type=<type>] [--confidence=<level>] [--tag=<tag>]"
```

**Examples:**
```bash
memory-cli --cmd "search 'auth bug' --limit=10"
memory-cli --cmd "search 'modal timing' --type=retro --confidence=verified"
memory-cli --cmd "search '*' --tag=critical --limit=20"
```

**Default behavior:**
- FTS5 with BM25 ranking
- Filter by `confidence != superseded` by default
- Limit 10 by default
- Returns snippets

**Response:**
```json
{
  "ok": true,
  "command": "search",
  "action": "memory.search",
  "data": {
    "query": "auth bug",
    "total_matches": 7,
    "returned": 7,
    "results": [
      {
        "id": "r_2025-11-25_username-display-fix",
        "score": 8.42,
        "title": "Username display fix with critical mistakes",
        "type": "retro",
        "confidence": "verified",
        "created_at": "2025-11-25T22:13:00Z",
        "snippet": "...the **auth** check failed because of...**bug** in session token...",
        "tags": ["bugfix", "auth", "session"],
        "source_path": ".claude/retrospectives/2025-11/2025-11-25_22-13_username-display-fix-with-critical-mistakes.md"
      },
      ...
    ]
  }
}
```

### 4.4 Command: `get`

```bash
memory-cli --cmd "get <id> [--include-body=true]"
```

**Response:**
```json
{
  "ok": true,
  "command": "get",
  "action": "memory.get",
  "data": {
    "id": "r_2025-11-25_username-display-fix",
    "title": "Username display fix with critical mistakes",
    "type": "retro",
    "confidence": "verified",
    "created_at": "2025-11-25T22:13:00Z",
    "tags": ["bugfix", "auth", "session"],
    "source_path": "...",
    "metadata": { /* frontmatter */ },
    "body": "# Username display fix\n\n...",
    "evidence_links": [
      { "type": "screenshot", "ref": "artifacts/before.png", "sha256": "..." }
    ],
    "supersession": {
      "superseded_by": null,
      "supersedes": ["r_2025-11-20_initial-fix"]
    }
  }
}
```

### 4.5 Command: `learn`

```bash
memory-cli --cmd "learn --file=<path> [--type=<type>] [--confidence=<level>]"
memory-cli --cmd "learn --json='<inline-json>'"
```

**Legacy direct-use path** to add one document:
```bash
memory-cli --cmd "learn --file=.ai/sessions/active/RETRO.md --type=retro --confidence=draft"
```

Current Trinity `rrr` writes a deterministic retro artifact and
delegates ingestion with `index <canonical retro path>`; `rrr` must not
call `learn` directly.

**Response:**
```json
{
  "ok": true,
  "command": "learn",
  "action": "memory.learn",
  "data": {
    "id": "r_2026-04-28_session-xyz",
    "indexed": true,
    "is_new": true
  }
}
```

### 4.6 Command: `list`

```bash
memory-cli --cmd "list [--type=<type>] [--confidence=<level>] [--tag=<tag>] [--since=<date>] [--limit=<n>] [--sort=<field>]"
```

**Examples:**
```bash
memory-cli --cmd "list --type=retro --since=2026-01-01 --sort=created_at"
memory-cli --cmd "list --confidence=draft --limit=50"
memory-cli --cmd "list --tag=critical"
```

### 4.7 Command: `stats`

```bash
memory-cli --cmd "stats"
```

**Response:**
```json
{
  "ok": true,
  "command": "stats",
  "action": "memory.stats",
  "data": {
    "total_docs": 254,
    "by_type": { "retro": 240, "lesson": 14, "summary": 0 },
    "by_confidence": { "verified": 12, "draft": 240, "superseded": 2 },
    "total_words": 1234567,
    "db_size_bytes": 5242880,
    "oldest": "2025-09-01T00:00:00Z",
    "newest": "2026-04-28T00:00:00Z",
    "top_tags": [
      { "tag": "bugfix", "count": 87 },
      { "tag": "deploy", "count": 42 },
      { "tag": "auth", "count": 23 }
    ],
    "indexed_at": "2026-04-28T11:00:00Z"
  }
}
```

### 4.8 Command: `supersede`

```bash
memory-cli --cmd "supersede <old_id> --by=<new_id> [--reason='...']"
```

**Tier:** aggressive (irreversible operation)

**Behavior:**
- Mark `<old_id>` as `confidence=superseded`
- Insert into `supersession` table
- New search results exclude superseded by default

### 4.9 Command: `reflect`

```bash
memory-cli --cmd "reflect [--topic=<keyword>] [--type=<type>]"
```

**Behavior:** Returns 1 random document — useful for "lesson of the day"

### 4.10 Command: `tag`

```bash
memory-cli --cmd "tag <id> +<tag>"            # add
memory-cli --cmd "tag <id> -<tag>"            # remove
memory-cli --cmd "tag <id> --set=tag1,tag2"   # replace all
```

---

## 5. Markdown Parsing

### 5.1 Frontmatter Detection

```markdown
---
title: "Modal z-index black screen fix"
date: 2025-11-24
type: retro
confidence: verified
tags: [bugfix, ui, modal, css]
evidence:
  - { type: screenshot, ref: artifacts/before.png }
  - { type: log, ref: artifacts/console-error.log }
session_id: sess_2025-11-24_modal
---

# Modal z-index black screen fix

## What happened
...
```

### 5.2 Without Frontmatter (legacy 240 retros)

Auto-derive:
- `id` = filename (slug) `r_2025-11-24_modal-fix`
- `title` = first H1
- `type` = inferred from path (`retrospectives/` → `retro`)
- `confidence` = `draft` (manual `verified` later)
- `created_at` = filename date prefix or file mtime
- `tags` = []

### 5.3 Body Chunking (future)

For large docs, split by H2/H3 — index chunks separately
For Phase 2 — index whole doc as one row (simple)

---

## 6. Configuration

### 6.1 Default Config

```json
{
  "$schema": "https://trinity.local/schemas/tool-config-v1.json",
  "version": "1.0",
  "tool": "memory-cli",
  "run": {
    "default_policy": "normal",
    "default_log_file": "./logs/memory-cli.ndjson"
  },
  "paths": {
    "data_dir": "./.memory",
    "default_index_paths": [
      ".claude/retrospectives",
      "ai-docs/real_lessons",
      ".ai/sessions/*/99_SUMMARY.md"
    ]
  },
  "tool_specific": {
    "fts_tokenize": "unicode61 remove_diacritics 1",
    "search_default_limit": 10,
    "search_filter_superseded": true,
    "indexer_skip_pattern": ["**/node_modules/**", "**/.git/**"],
    "snippet_length": 200,
    "snippet_around_match": true
  }
}
```

---

## 7. Indexer Logic

### 7.1 Walk Source

```javascript
async function indexPath(path, options) {
  const stats = fs.statSync(path);
  
  if (stats.isFile()) {
    return indexFile(path, options);
  }
  
  // Directory — walk recursively
  const files = await glob('**/*.md', { cwd: path });
  let indexed = 0;
  
  for (const file of files) {
    const fullPath = join(path, file);
    if (shouldSkip(fullPath, config.indexer_skip_pattern)) continue;
    
    const result = await indexFile(fullPath, options);
    if (result.indexed) indexed++;
  }
  
  return { scanned: files.length, indexed_new: indexed };
}
```

### 7.2 Index Single File

```javascript
async function indexFile(filePath, options) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const sha256 = crypto.createHash('sha256').update(content).digest('hex');
  
  // Check if already indexed
  const existing = db.prepare('SELECT body_sha256 FROM documents WHERE source_path = ?').get(filePath);
  if (existing && existing.body_sha256 === sha256 && !options.force) {
    return { indexed: false, reason: 'unchanged' };
  }
  
  // Parse
  const { frontmatter, body } = parseMarkdown(content);
  const id = frontmatter.id || deriveIdFromPath(filePath);
  const title = frontmatter.title || extractH1(body) || basename(filePath);
  const type = frontmatter.type || inferTypeFromPath(filePath);
  const tags = frontmatter.tags || [];
  
  // Insert/replace
  db.transaction(() => {
    db.prepare(`
      INSERT OR REPLACE INTO documents
      (id, source_path, title, type, confidence, created_at, indexed_at, body, body_sha256, word_count, metadata_json)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(id, filePath, title, type, frontmatter.confidence || 'draft',
           frontmatter.date || statTime(filePath), new Date().toISOString(),
           body, sha256, countWords(body), JSON.stringify(frontmatter));
    
    // Update tags
    db.prepare('DELETE FROM tags WHERE document_id = ?').run(id);
    for (const tag of tags) {
      db.prepare('INSERT INTO tags (document_id, tag) VALUES (?, ?)').run(id, tag);
    }
    
    // Update FTS
    db.prepare(`
      INSERT OR REPLACE INTO documents_fts (rowid, title, body, tags)
      VALUES ((SELECT rowid FROM documents WHERE id = ?), ?, ?, ?)
    `).run(id, title, body, tags.join(' '));
    
    // Evidence links
    if (frontmatter.evidence) {
      db.prepare('DELETE FROM evidence_links WHERE document_id = ?').run(id);
      for (const ev of frontmatter.evidence) {
        db.prepare(`
          INSERT INTO evidence_links (document_id, artifact_type, artifact_ref, sha256)
          VALUES (?, ?, ?, ?)
        `).run(id, ev.type, ev.ref, ev.sha256);
      }
    }
  })();
  
  return { indexed: true, id };
}
```

---

## 8. FTS5 Search Query

### 8.1 Query Sanitization

```javascript
function sanitizeFtsQuery(q) {
  // Strip FTS5 special chars
  return q.replace(/[\^"\(\)\*\:]/g, ' ').trim();
}
```

### 8.2 Search SQL

```sql
SELECT
  d.id, d.title, d.type, d.confidence, d.created_at, d.source_path,
  bm25(documents_fts) AS score,
  snippet(documents_fts, 1, '<mark>', '</mark>', '...', 30) AS snippet,
  GROUP_CONCAT(t.tag) AS tag_list
FROM documents_fts
JOIN documents d ON d.rowid = documents_fts.rowid
LEFT JOIN tags t ON t.document_id = d.id
WHERE documents_fts MATCH ?
  AND (? IS NULL OR d.type = ?)
  AND (? IS NULL OR d.confidence = ?)
  AND (? IS NULL OR EXISTS (SELECT 1 FROM tags t2 WHERE t2.document_id = d.id AND t2.tag = ?))
GROUP BY d.rowid
ORDER BY score
LIMIT ?;
```

### 8.3 Result Ranking

- BM25 (default FTS5) for now
- Future: boost recent docs · boost verified · penalize superseded

---

## 9. Existing 240 Retros — Migration

### 9.1 Initial Index

```bash
# First time setup
memory-cli --cmd "index .claude/retrospectives/"
# → indexes 240 retros as confidence=draft

memory-cli --cmd "index ai-docs/real_lessons/ --confidence=verified"
# → indexes 14 lessons as confidence=verified
```

### 9.2 Bulk Confidence Upgrade

After review, mark good retros:
```bash
# Manually verified
memory-cli --cmd "list --type=retro --confidence=draft" | jq '.data[] | .id' \
  | xargs -I {} echo "Review: {}"

# Mark specific ones verified (manual review)
memory-cli --cmd "tag r_2025-11-24_modal-fix +reviewed_2026_04_28"
# (no bulk verified flag for now — preserve auditability)
```

### 9.3 Auto-detect superseded

Future: detect when retros mention same bug/feature → propose supersession chain

---

## 10. Tests

### 10.1 Unit (`tests/harness.js`)

- Parse frontmatter (YAML frontmatter detection)
- Derive ID from path
- Sanitize FTS query
- Schema validation
- Tag operations

### 10.2 Golden (`tests/golden.js`)

- Setup test DB with fixtures
- Run index against `tests/fixtures/retros/` (5 sample files)
- Verify count = 5
- Search for known terms → expect specific results
- Get by ID
- Tag add/remove
- Supersede chain
- Stats correctness
- Cleanup

### 10.3 Contract Compliance

```bash
trinity-contract-test memory-cli
# Should pass all (Bronze → Silver → Gold)
```

---

## 11. Wire into lll/vvv/nnn (Phase 3)

### 11.1 `lll` integration

```python
def cmd_lll():
    # ... existing project status ...
    
    # NEW: pull recent context
    recent = call_tool('memory-cli', 
                       f"list --since=7d --limit=5 --confidence=verified")
    
    similar = call_tool('memory-cli',
                        f"search '{current_session.goal}' --limit=3")
    
    write_context_artifact({
        'recent_retros': recent.data,
        'similar_past': similar.data
    })
```

### 11.2 `vvv` integration

```python
def cmd_vvv(question):
    # NEW: search past incidents
    past = call_tool('memory-cli', f"search '{question}' --type=retro --tag=bugfix")
    
    if past.data.results:
        print("⚠️  Found similar past incidents:")
        for r in past.data.results:
            print(f"  - {r.title} ({r.created_at})")
            print(f"    {r.snippet}")
    
    # ... continue 5-question verification
```

### 11.3 `nnn` integration

```python
def cmd_nnn(plan_request):
    # NEW: get hints from memory
    hints = call_tool('memory-cli', f"search '{plan_request}' --limit=3")
    
    plan_context = {
        'request': plan_request,
        'memory_hints': hints.data.results
    }
    # → vendor AI plans with hints
```

---

## 12. Anti-patterns

| ❌ Anti-pattern | ✅ Correct |
|-----------------|-----------|
| Index everything always | Skip-by-sha256 for unchanged |
| Search returns superseded by default | Filter superseded unless explicit |
| All retros = verified | Default draft, manual upgrade |
| Delete docs | Supersede (Nothing is Deleted) |
| FTS query with raw user input | Sanitize first |
| Memory = source of truth | Memory = recall, source = files |

---

## 13. Open Questions

1. ID format — slug from filename, or UUID?
2. Chunking strategy — whole doc, by H2, or by paragraph?
3. Tag taxonomy — free-form or controlled vocabulary?
4. Markdown variants — GFM, MDX, plain?
5. Multi-language — Thai/English token? FTS5 unicode61 ok?
6. Backup strategy — git? snapshot DB?
7. Concurrent access — single-writer or multi?
8. Index update on file change — watch mode?
9. Vendor AI direct vs CLI — preference?
10. Privacy — exclude sensitive content (passwords, keys)?

---

## 14. Implementation Sketch

```
memory-cli/
├── index.js                       ← entry
├── package.json
├── lib/
│   ├── db.js                       ← SQLite + FTS5
│   ├── indexer.js                  ← walk + parse + insert
│   ├── search.js                   ← FTS5 query
│   ├── parser.js                   ← markdown + frontmatter
│   ├── id-generator.js
│   ├── tag-manager.js
│   ├── supersession.js
│   ├── stats.js
│   ├── policy.js                   ← tier check
│   ├── logger.js                   ← NDJSON
│   ├── envelope.js                 ← response wrapper
│   └── parser.js                   ← command parser
├── schema/
│   ├── config.schema.json
│   ├── response-v1.schema.json
│   └── document.schema.json
├── configs/
│   └── <upstream-project>-memory.json
├── tests/
│   ├── harness.js
│   ├── golden.js
│   └── fixtures/
└── docs/
    ├── ARCHITECTURE.md
    ├── COMMAND_CONTRACT.md
    ├── AI_AGENT_GUIDE.md
    └── USER_GUIDE.md
```

---

## 15. Phase 9 (Future) — Hybrid Search

When ready:

```sql
-- Add embedding column
ALTER TABLE documents ADD COLUMN embedding BLOB;
```

```javascript
// Add ChromaDB collection
const chroma = new ChromaClient();
await chroma.add({
  ids: [doc.id],
  embeddings: await embed(doc.body),
  metadatas: { type: doc.type, ... }
});

// Hybrid search
async function hybridSearch(query) {
  const [ftsResults, vectorResults] = await Promise.all([
    fts5Search(query),
    vectorSearch(await embed(query))
  ]);
  return mergeRanked(ftsResults, vectorResults, weight=0.5, overlap_boost=0.1);
}
```

---

## 16. Quick Reference

### Daily commands
```bash
memory-cli --cmd "search 'topic'"          # search
memory-cli --cmd "list --since=7d"          # recent
memory-cli --cmd "stats"                    # health
```

### Setup commands
```bash
memory-cli --cmd "index .claude/retrospectives/"
memory-cli --cmd "index ai-docs/real_lessons/ --confidence=verified"
```

### Maintenance
```bash
memory-cli --cmd "supersede <old> --by=<new>"
memory-cli --cmd "reindex"
memory-cli --health
```

---

## See also

- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) — implements this contract
- [`06_RETRO_CLI_SPEC.md`](06_RETRO_CLI_SPEC.md) — retro-cli writes to memory-cli
- [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) — loop calls memory-cli
- browser-cli reference for code structure

## Changelog

- **v1.0.0-draft (2026-04-28)** — Initial draft (Phase 2 — FTS5 only)
