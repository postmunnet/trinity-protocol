---
title: "Trinity Knowledge Brain"
status: stable
last-updated: 2026-04-30
audience: "AI agents recalling protocol knowledge; future memory-cli indexer (Phase 2)"
source: "<upstream-project>/ai-docs/0[1-4]-*/ (Decision D6) — scrubbed of project-specific terms"
---

# Trinity Knowledge Brain

> **What lives here**: the canonical knowledge base for Trinity OS protocols,
> standards, and procedures. Generic — meant to be **read by any project**, not
> just the one it was extracted from.

This is the **passive recall layer**. It does NOT plan. It does NOT decide.
The Knowledge Brain is queried by the verifier (Pyramid layer 1), the kernel
(during `lll`/`vvv`), and (in Phase 2) by `memory-cli` for relevance search.

## Layout

```
ai-docs/
├── 01-CORE_PROTOCOL/        Protocol contracts (workflow, safety, multi-AI)
├── 02-STANDARDS/            Cross-cutting standards (env, naming, UX rules)
├── 03-PROCESS/              Operational procedures (rollback, recovery)
└── 04-MEMORY/               (empty — placeholder for Phase 2 memory-cli index)
```

## File index (11 files)

| Folder | File | Status |
|--------|------|--------|
| 01-CORE_PROTOCOL | `WORKFLOW.md` | scrubbed |
| 01-CORE_PROTOCOL | `SAFETY_GATES.md` | scrubbed |
| 01-CORE_PROTOCOL | `TOOL_USAGE.md` | clean (original placeholders) |
| 01-CORE_PROTOCOL | `GOD_TEAM_INTERACTION.md` | clean |
| 01-CORE_PROTOCOL | `HUMAN_AGENT_INTERACTION.md` | clean |
| 01-CORE_PROTOCOL | `MULTI_AI_COLLABORATION.md` | scrubbed |
| 02-STANDARDS | `UNIVERSAL_RULES.md` | scrubbed |
| 02-STANDARDS | `ENV_VARS.md` | scrubbed |
| 02-STANDARDS | `HUMAN_INTERFACE.md` | clean |
| 02-STANDARDS | `QUICK_REF.md` | clean |
| 03-PROCESS | `ROLLBACK_PROCEDURES.md` | scrubbed |

`04-MEMORY/` is intentionally empty until Phase 2 (memory-cli) lands.

## Sourcing & sanitization (Decision D6)

These docs were imported from `<upstream-project>/ai-docs/0[1-4]-*/` and **scrubbed** of
project-specific terms before commit. Per the contamination report in
`docs/migration/02_EVIDENCE_TRIAGE.md`, 7 of 11 files contained the upstream
project name, Smarty, CodeIgniter, FTPS, or upstream domain references.

The scrub replaced all such terms with `{{PLACEHOLDER}}` tokens. Any project
adopting this brain replaces the placeholders with its own values.

### Placeholders used

| Placeholder | Replaces (originally) | Example |
|-------------|----------------------|---------|
| `{{PROJECT_NAME}}` | `<upstream-project-name>` | The project's identifier |
| `{{PROJECT_DOMAIN}}` | `<upstream-domain>` | Production domain |
| `{{TEMPLATE_ENGINE}}` | `Smarty` | View layer engine |
| `{{FRAMEWORK}}` | `CodeIgniter 3` | Web framework |
| `{{TRANSFER_PROTOCOL}}` | `FTPS` | File transfer mechanism |
| `{{DEPLOY_SCRIPT}}` | `deploy_ftps.sh` | Deploy invocation |
| `{{DEPLOY_SCRIPT_DEV}}` | `deploy_dev_order_detail.sh` | Dev-tier deploy |
| `{{DEPLOY_SCRIPT_PROD}}` | `deploy_prod_slip_verification.sh` | Prod-tier deploy |
| `{{APP_DIR}}` | `<user-home>/.../<upstream-project>` | Project root path |
| `{{APP_ROOT}}` | `application/` | Framework's source root |
| `{{CONTROLLER_DIR}}` | `application/controllers/` | MVC controllers |
| `{{CONFIG_DIR}}` | `application/config/` | Config files |
| `{{MODEL_DIR}}` | `application/models/` | MVC models |
| `{{VIEW_DIR}}` | `application/views/` | MVC views |
| `{{PUBLIC_DIR}}` | `/public_html/` | Web-server document root |
| `{{PUBLIC_BACKUP}}` | `/public_html.backup` | Pre-deploy backup |
| `{{APP_ENTRY}}` | `application/file.php` | Generic source file |
| `{{ENTRY_POINT}}` | `backend.php` | Admin/backend dispatcher |
| `{{FTP_CREDENTIALS_REF}}` | `FTP_CRED*` env names | Credential env-var name |

## How to adopt this brain in a downstream project

1. Copy `ai-docs/` into your project root.
2. Search-and-replace `{{PLACEHOLDER}}` tokens with your project's values.
3. Wire `memory-cli` (Phase 2) to index this folder — your verifier will be
   able to recall by topic.
4. Append project-specific knowledge in a new `05-PROJECT/` folder (don't
   modify 01–04 — those are canonical Trinity protocol).

## Verification commands

```bash
# Confirm no original project leakage:
# (substitute `<upstream-project>`, `<upstream-domain>`, and `<user-home>` with the actual originals before running)
grep -irlE "<upstream-project>|smarty|codeigniter|<upstream-domain>|deploy_ftps|FTPS|FTP_CRED|<user-home>|/var/www" ai-docs/
# expected: 0 matches

# Confirm placeholders only appear where scrubs happened:
grep -rl "{{PROJECT_NAME}}\|{{TEMPLATE_ENGINE}}\|{{APP_DIR}}" ai-docs/ | wc -l
# expected: 7  (the scrubbed files)

# Count canonical files:
find ai-docs -type f -name "*.md" | wc -l
# expected: 11
```

## Boundaries

- ❌ Don't add project-specific knowledge to `01-04` folders (use `05-PROJECT/`)
- ❌ Don't remove placeholders without replacement — Trinity verifier checks
- ❌ Don't reference this brain as authoritative for *your* project's runbooks
  until you've replaced placeholders
- ✅ Do read end-to-end before invoking — context matters
- ✅ Do append project decisions in `04-MEMORY/decisions.md` (Phase 2)
