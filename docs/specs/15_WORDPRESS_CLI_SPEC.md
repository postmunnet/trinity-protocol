# Spec 15 — `wordpress-cli` sibling

**Status:** Draft v0.5 (SEO verbs addendum — supersedes v0.4)
**Owner:** yai
**Created:** 2026-05-02 (v0.1) · revised 2026-05-04 (v0.5 SEO verbs)
**Decision-rule class:** Tier 6-A clear sibling

## v0.5 Changelog (current)
- §5.6 NEW `seo` verb group: audit / get / set / bulk-set / detect
- §5.5 NEW bulk verb: `bulk seo-audit-deep`
- Auto-detect Yoast vs RankMath vs none via custom_fields probe (cached in sites.yaml as `seo_plugin`)
- `seo set` writes Yoast (`_yoast_wpseo_*`) or RankMath (`rank_math_*`) meta keys via XML-RPC custom_fields or REST settings
- §7.2 prod hardening: `seo set` + `seo bulk-set` require `--decided-by=human` on production-tagged sites
- §14 capability matrix: `seo.audit: [rest, xmlrpc]` · `seo.get: [rest, xmlrpc]` · `seo.set: [rest, xmlrpc]`
- Composition with `seo-genie-cli` (spec 17): audit.json → genie batch-meta-desc → fixes.json → wp-cli seo bulk-set
- Bumps to **v0.4.0-beta**

## v0.4 Changelog
- §5.2 `media`: add `upload <file>` and `bulk-upload --dir=<path>` sub-verbs
- §6 envelope: `result.attachment_id` / `result.url` populated on upload
- §7.2 prod hardening: `media upload` + `bulk-upload` require `--decided-by=human` on production-tagged sites
- §13 deps: `media upload` REST = handcrafted multipart/form-data (no extra npm dep); XML-RPC = base64 via `wp.uploadFile`
- §14 capability matrix: `media.upload: [rest, xmlrpc]` (REST primary, XML-RPC fallback)
- Composition with `image-cli` (spec 16) — operator pre-converts to WebP, then bulk-upload
- Bumps to **v0.3.0-beta**

## §5.6 SEO verb group (v0.5)

```
seo audit <site> [--post-type=post|page|all] [--out=report.md|json] [--tag=...]
   - Rubric-based scan: meta-desc length, h1 count, alt presence,
     keyword in title/url, content word count, image count, schema markup
   - Output: per-page score 0-10 + issues[] + recommendations
   - JSON shape ready for piping to seo-genie-cli

seo get <site> <post_id>
   - Auto-detect plugin (cached in sites.yaml::seo_plugin)
   - Read all SEO meta fields:
     Yoast: _yoast_wpseo_title, _yoast_wpseo_metadesc, _yoast_wpseo_focuskw,
            _yoast_wpseo_canonical, _yoast_wpseo_meta-robots-noindex, ...
     RankMath: rank_math_title, rank_math_description, rank_math_focus_keyword,
               rank_math_canonical_url, rank_math_robots, ...
   - Returns structured JSON with detected plugin name + values

seo set <site> <post_id> [options] --decided-by=human
   - Auto-pick correct meta keys per plugin
   - Options: --meta-desc=... --title=... --focus-kw=... --canonical=...
   - Writes via XML-RPC wp.editPost custom_fields OR REST /wp/v2/posts/<id>?meta=...
   - History line auto-appended to sites/<alias>.md

seo bulk-set <site> --json=fixes.json --decided-by=human
                    [--csv=fixes.csv] [--dry-run] [--include-production]
   - Apply N fixes from JSON/CSV
   - Format: [{id, meta_desc, title, focus_kw, ...}]
   - Per-page audit → write → log to History
   - Prod-tag site requires --include-production

seo detect <site>
   - Probe XML-RPC wp.getPost custom_fields of recent posts
   - Find Yoast or RankMath keys → cache in sites.yaml::seo_plugin
   - Return: yoast | rankmath | both | none
```

## §5.5 Bulk verb (v0.5 addition)

```
bulk seo-audit-deep [--tag=...] [--all] [--out=fleet-seo.md]
   - Fleet-wide audit: every site × every published post
   - Matrix output: site/page/score/issues
   - Markdown summary + per-site detail
```

## 1. Purpose

Single sibling for managing the operator's WordPress fleet via **REST API +
XML-RPC hybrid transport**, with per-site registry that doubles as living
documentation. Scope = **content management + plugin/theme admin** (NOT code
editing, NOT DB raw ops, NOT core WP updates). No SSH required — works against
any host with REST or XML-RPC enabled (i.e., 99% of WP installs).

## 2. Architecture invariant

> Sibling = transport router (REST or XML-RPC) selecting per (verb, site)
> via capability matrix. Kernel + verifier = authority for destructive ops.
> Every WP write lands in audit chain; destructive ops require
> `decided_by: human` envelope OR 2-step CONFIRM token.
>
> Transports operate over HTTPS only — no SSH, no wp-cli subprocess.

## 3. Layout

```
~/.config/wordpress-cli/
├── sites.yaml            # source of truth, human-editable, git-able (no secrets)
├── sites.db              # SQLite cache, auto-rebuilt from yaml + sync
├── sites/
│   └── <alias>.md        # per-site doc (frontmatter + auto Stack + auto History)
├── secrets/
│   └── <alias>.env       # xmlrpc_pass + (optional) app_password; chmod 600
└── audit/
    └── ops.ndjson        # every WP op (hash-chained)
```

Binary path: `<workspace-root>/wordpress-cli/index.js` (Node 20+).

```
wordpress-cli/
├── index.js              # entry, --cmd dispatcher
├── package.json          # Node 20+, deps: js-yaml (xmlrpc/rest via stdlib http)
├── README.md
├── TOOL_CONTRACT.json
├── lib/
│   ├── registry.js       # sites.yaml load/save + sites.db cache
│   ├── envelope.js       # TOOL_CONTRACT v1 envelope
│   ├── audit.js          # hash-chained ops.ndjson + redact
│   ├── gate.js           # --decided-by=human + 60s CONFIRM token
│   ├── secrets.js        # chmod 600 enforcement
│   ├── doc.js            # per-site .md autogen + marker block sync
│   ├── router.js         # capability matrix dispatcher
│   ├── capability.yaml   # verb → required transports list
│   ├── transports/
│   │   ├── rest.js       # WP REST API (HTTPS + Basic auth via app password)
│   │   └── xmlrpc.js     # XML-RPC (HTTPS POST + XML payload, user/pass auth)
│   ├── sync.js           # site metadata refresh (uses preferred transport)
│   └── verbs/
│       ├── sites.js      # add/list/show/sync/doc/remove
│       ├── post.js       # list/create/update/delete/publish/unpublish/schedule
│       ├── page.js       # alias of post --post-type=page
│       ├── media.js      # upload/list/delete
│       ├── term.js       # list/create/update/delete (cat+tag)
│       ├── menu.js       # list/create/add-item/remove-item/reorder
│       ├── comment.js    # list/approve/spam/trash/reply
│       ├── user.js       # list/create/update/reset-password
│       ├── option.js     # get/update (whitelist)
│       ├── plugin.js     # install/activate/deactivate/update/list (REST only)
│       ├── theme.js      # install/activate/update/list (REST only)
│       └── bulk.js       # post-import/media-cleanup/seo-check/publish-schedule/plugin-update/theme-update/comment-pending/audit
└── tests/
    ├── test_registry.js
    ├── test_envelope.js
    ├── test_router.js          # capability matrix dispatch
    ├── test_transport_rest.js  # mock HTTP responses
    ├── test_transport_xmlrpc.js
    ├── test_gate.js
    ├── test_doc.js
    └── test_secrets.js
```

## 4. Registry schema (sites.yaml v2)

```yaml
version: 2
sites:
  <alias>:
    url: <https://...>                       # required (was: path:)
    tags: [production|staging|local|...]
    transports:
      xmlrpc:                                # if present, this transport is available
        user: <wp-login username>            # password via secrets/<alias>.env::xmlrpc_pass
      rest:                                  # if present, REST is available
        app_password_user: <wp-login username>  # password via secrets/<alias>.env::app_password
    preferred: rest | xmlrpc                 # fallback chain: try preferred first, then other
    php: "8.2"                               # auto-synced (best-effort; some hosts hide)
    wp_version: "6.5.2"                     # auto-synced
    multisite: false                         # auto-synced (if discoverable)
    doc: sites/<alias>.md
    last_synced: <ISO 8601 UTC>
```

`sites.db` (SQLite) cache: `sites`, `posts_summary`, `users`, `terms`,
`media_summary`, `confirm_tokens`, `audit_offset`. Rebuilt by `sites sync`.

## 5. Verbs

### 5.1 Registry
| verb | args | notes |
|------|------|-------|
| `sites add` | `<alias> --url=... [--xmlrpc-user=... --rest-user=... --tags=... --preferred=rest\|xmlrpc]` | initial sync via preferred transport + create doc |
| `sites list` | `[--tag=...] [--json]` | table or JSON |
| `sites show` | `<alias> [--posts\|--users\|--terms\|--all]` | sync + display |
| `sites sync` | `<alias>\|--all` | refresh sites.db + auto-update doc Stack block |
| `sites doc` | `<alias>` | open doc in `$EDITOR` |
| `sites remove` | `<alias>` | delete from yaml; does NOT touch WP |
| `sites probe` | `<alias>` | re-detect available transports + caps (e.g., XML-RPC blocked, REST plugin endpoint disabled) |

### 5.2 Content management
| verb | sub-verbs | destructive |
|------|-----------|-------------|
| `post` | list / create / update / delete / publish / unpublish / schedule | delete = ✅ |
| `page` | (alias of `post --post-type=page`) | delete = ✅ |
| `media` | upload / list / delete | delete = ✅ |
| `term` | list / create / update / delete | delete = ✅ |
| `menu` | list / create / add-item / remove-item / reorder | remove + delete = ✅ |
| `comment` | list / approve / spam / trash / reply | trash = ✅ |
| `user` | list / create / update / reset-password | reset-password = ✅ on prod |
| `option` | get / update (whitelist: site-title, tagline, timezone, posts_per_page) | update = ✅ on prod |

### 5.3 Plugin / Theme admin (REST only)
| verb | sub-verbs | destructive |
|------|-----------|-------------|
| `plugin` | install / activate / deactivate / update / list | activate+deactivate = ✅ on prod |
| `theme` | install / activate / update / list | activate = ✅ |

If site has only XML-RPC configured → these verbs exit `78 verb_unavailable`
with hint "configure REST app_password for plugin/theme ops".

### 5.4 Bulk ops
| verb | args | notes |
|------|------|-------|
| `bulk post-import` | `--csv=... --tag=... [--dry-run]` | CSV → batch create |
| `bulk media-cleanup` | `--tag=... [--orphans-only]` | report only, no auto-delete |
| `bulk seo-check` | `[--tag=...] [--out=report.md]` | posts missing title/description |
| `bulk publish-schedule` | `--csv=... --tag=...` | queue scheduled posts |
| `bulk plugin-update` | `[--tag=...] [--all] [--dry-run]` | REST-required sites only; skip XML-RPC-only with warning |
| `bulk theme-update` | `[--tag=...] [--all] [--dry-run]` | same |
| `bulk comment-pending` | `[--tag=...] [--all]` | fleet pending |
| `bulk audit` | `[--all] [--out=report.md]` | matrix: WP/PHP/transport caps/posts/comments |

## 6. TOOL_CONTRACT v1 envelope

```json
{
  "tool": "wordpress-cli",
  "version": "0.2.0-beta",
  "schema_version": "1.0",
  "verb": "post.create",
  "args": {"site": "amprohealth", "title": "..."},
  "transport": "rest" | "xmlrpc",
  "result": {"ok": true, "exit": 0, "duration_ms": 234, "wp_id": 35419},
  "evidence": {"wp_op_result": {...}, "transport_used": "rest"},
  "decided_by": "human" | "ai" | "tg:<user_id>",
  "audit_event_id": "ulid",
  "ts": "<ISO 8601 UTC>"
}
```

Audit emit: `tool.invoked` + `tool.completed` per call, with `transport_used`
field for traceability.

## 7. Security model

### 7.1 Destructive op gating
Same as v0.2: `--decided-by=human` flag OR 60s single-use CONFIRM token OR
envelope `decided_by: human`. Without any → exit 78.

### 7.2 Prod target hardening
If `tags` includes `production`:
- ALL writes (incl. activate/deactivate/update) require `--decided-by=human`
- Bulk on prod tag requires `--include-production` flag

### 7.3 Secret handling
- `secrets/<alias>.env` chmod 600 enforced
- Format:
  ```env
  XMLRPC_PASS=<wp-login password>          # required if transports.xmlrpc set
  APP_PASSWORD=<application password>      # required if transports.rest set
  ```
- Never logged; redacted via TOOL_CONTRACT `redact:` list before audit write
- HTTPS required (sibling refuses `http://` URLs unless `--allow-insecure` for local dev)

### 7.4 Transport-specific risks
- **XML-RPC:** brute-force target — recommend strong wp-login pass; warn user if `xmlrpc.php` returns weak rate-limit headers
- **REST:** Application Password is per-user — user must generate via wp-admin; sibling provides instructions in `sites add` error message

## 8. Doc auto-generation

`sites add` writes `sites/<alias>.md`:
```markdown
---
alias: <alias>
url: <url>
created: <date>
tags: [<tags>]
transports: [rest, xmlrpc]
preferred: rest
---

## Stack <!-- AUTO-GENERATED, DO NOT EDIT BELOW UNTIL "## Quirks" -->
- WP <ver> / PHP <ver> (best-effort detection)
- Transports available: rest, xmlrpc
- Preferred: rest
- Posts: <count> / Users: <count> / Categories: <count>
<!-- END AUTO -->

## Quirks
<!-- user-editable freeform -->

## History <!-- AUTO-APPENDED -->
- <ISO date>: bootstrap into wordpress-cli registry
```

`sites sync` regenerates **only** the Stack block. Quirks stays user-owned.

## 9. Acceptance criteria

| # | criterion |
|---|-----------|
| A1 | `sites add foo --url=https://wp.local --xmlrpc-user=admin --tags=local` writes yaml + creates doc + populates sites.db |
| A2 | `sites list --json` returns parseable JSON array |
| A3 | `sites/foo.md` autogen contains `<!-- AUTO-GENERATED -->` + `## Quirks` + `## History` markers |
| A4 | `post foo list` via mock REST transport returns envelope with `transport: "rest"` |
| A5 | `post foo list` falls back to XML-RPC when REST 404s; envelope shows `transport: "xmlrpc"` |
| A6 | `post foo delete 1` (no decided_by) → exit 78 |
| A7 | `post foo delete 1 --decided-by=human` → exit ≠ 78 (gate passed) |
| A8 | `plugin prod-test activate yoast` (production tag, no decided_by) → exit 78 |
| A9 | `plugin prod-test activate yoast --decided-by=human` → exit ≠ 78 |
| A10 | `plugin xmlrpc-only-site list` → exit 78 with hint "configure REST" |
| A11 | `bulk plugin-update --tag=staging --dry-run` enumerates without invoking |
| A12 | `bulk plugin-update --tag=production` rejected without `--include-production` |
| A13 | TOOL_CONTRACT v1 Platinum contract test → 14/14 |
| A14 | `secrets/foo.env` mode 0644 → exit 1 |
| A15 | Registered in `TRINITY_LEGACY/.ai/tools.yaml` |

## 10. Phased rollout

| Phase | Scope | Effort |
|-------|-------|--------|
| 0 | Spec review + buy-in | ~30 min |
| 1 | Registry verbs + sites.yaml v2 + sites.db + doc autogen | ~½ day |
| 2 | Transports: lib/transports/rest.js + xmlrpc.js + lib/router.js + capability.yaml + audit emit | ~1 day |
| 3 | Content verbs (post/page/media/term/menu/comment/user/option) routed via router | ~½ day |
| 4 | Plugin/theme admin (REST-only path) + bulk ops + prod hardening | ~½ day |
| 5 | Platinum contract + tools.yaml registration + smoke against amprohealth read-only | ~½ day |

**Total: ~2 days build** + smoke.

## 11. Out of scope (defer)

- **SSH + wp-cli transport** (L3 — for db/scaffold/core ops; defer until power-user need)
- **browser-cli wrap** (L4 — for page builders / customizer; needs browser-cli sibling first)
- **Theme/plugin code editing** (filesystem PHP/CSS/JS edits)
- **Theme/plugin delete** (manual via wp-admin)
- **DB raw ops** (export/import/search-replace/reset/drop)
- **Cron management**
- **WP core update**
- **GUI / web dashboard**
- **Multi-user team support**
- **CPT/WooCommerce/Elementor/i18n specialized verbs**

## 12. Risks

| risk | mitigation |
|------|-----------|
| XML-RPC blocked by host security | `sites probe` detects + reports; user can add REST app password as alternate transport |
| REST API disabled / behind login wall | sites probe detects; falls back to XML-RPC if available |
| App Password compromised | rotate via wp-admin → update `secrets/<alias>.env` |
| XML-RPC creds reused across sites = brute force risk | per-site `secrets/<alias>.env` (no shared creds) |
| HTTPS cert invalid on target | reject by default; `--allow-insecure` flag for local dev only |
| Plugin activate WSODs prod | activate on prod requires decided_by:human; History line for rollback |
| Bulk update WSODs many sites | `--dry-run` default-on for production tag |
| Doc auto-Stack overwrites user notes | strict marker block; sync NEVER touches outside markers |
| Secret leak via stdout | redact list + chmod check + audit redact |

## 13. Dependencies

- Node 20+ runtime
- `node:sqlite` (stdlib)
- `node:http` / `node:https` (stdlib)
- `js-yaml` (single npm dep)
- **NO** `wp` binary required
- **NO** `ssh` required

## 14. Capability matrix (lib/capability.yaml)

```yaml
# verb → list of transports that can satisfy it (router tries in preferred order)
verb_capabilities:
  sites.add:           [rest, xmlrpc]    # uses preferred for sync
  sites.sync:          [rest, xmlrpc]
  post.list:           [rest, xmlrpc]
  post.create:         [rest, xmlrpc]
  post.update:         [rest, xmlrpc]
  post.delete:         [rest, xmlrpc]
  post.publish:        [rest, xmlrpc]
  post.unpublish:      [rest, xmlrpc]
  post.schedule:       [rest, xmlrpc]
  page.*:              [rest, xmlrpc]
  media.upload:        [rest, xmlrpc]
  media.list:          [rest, xmlrpc]
  media.delete:        [rest, xmlrpc]
  term.list:           [rest, xmlrpc]
  term.create:         [rest, xmlrpc]
  term.update:         [rest, xmlrpc]
  term.delete:         [rest, xmlrpc]
  menu.list:           [rest]            # XML-RPC has no native menu API
  menu.create:         [rest]
  menu.add-item:       [rest]
  menu.remove-item:    [rest]
  menu.reorder:        [rest]
  comment.list:        [rest, xmlrpc]
  comment.approve:     [rest, xmlrpc]
  comment.spam:        [rest, xmlrpc]
  comment.trash:       [rest, xmlrpc]
  comment.reply:       [rest, xmlrpc]
  user.list:           [rest, xmlrpc]
  user.create:         [rest]
  user.update:         [rest]
  user.reset-password: [rest]
  option.get:          [rest, xmlrpc]    # XML-RPC option whitelist is small
  option.update:       [rest]
  plugin.*:            [rest]            # XML-RPC cannot
  theme.*:             [rest]
  bulk.post-import:    [rest, xmlrpc]
  bulk.media-cleanup:  [rest, xmlrpc]
  bulk.seo-check:      [rest, xmlrpc]
  bulk.publish-schedule: [rest, xmlrpc]
  bulk.plugin-update:  [rest]            # skip XML-RPC-only sites with warning
  bulk.theme-update:   [rest]
  bulk.comment-pending: [rest, xmlrpc]
  bulk.audit:          [rest, xmlrpc]
```

Router algorithm (lib/router.js):
1. Look up `verb_capabilities[verb]` → ordered transport list
2. For each transport in order:
   - If site has it configured AND (transport == site.preferred OR no preferred) → try first
   - Else queue for fallback
3. Try transports in order: invoke `transports/<name>.js::<verb>(site, args)`
4. On success → return wrapped envelope with `transport: <name>`
5. On all-fail → exit 78 `verb_unavailable` with hint listing missing transports

---

*End of spec 15 v0.3*
*Supersedes v0.2 (SSH+wp-cli architecture). v0.1.0-beta archived to /tmp/wordpress-cli-v0.1.0-beta-backup-<ts>.*
