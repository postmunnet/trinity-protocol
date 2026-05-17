---
title: "Trinity OS — License Decision (English)"
status: recommendation
language: English
last-updated: 2026-04-28
current: MIT (TRINITY_LEGACY/LICENSE)
recommendation: Keep MIT or upgrade to Apache-2.0
note: "Translation of ../LICENSE_DECISION.md"
---

# Trinity OS — License Decision (English)

> Analysis & recommendation for the Trinity OS v2 spec pack + future implementation.

---

## 0. Current Status

```
File:     <workspace-root>/TRINITY_LEGACY/LICENSE
License:  MIT
Holder:   Trinity Protocol Contributors
Year:     2025
```

✅ Trinity already uses **MIT License** — this decision is whether to **keep MIT** or **upgrade to Apache-2.0**.

---

## 1. License Comparison Matrix

| Aspect | MIT | Apache-2.0 | AGPL-3.0 | BUSL-1.1 |
|--------|-----|------------|----------|----------|
| **Permissive** | ✅ very | ✅ yes | ❌ copyleft | ⚠️ time-limited |
| **Commercial use** | ✅ | ✅ | ⚠️ must opensource | ❌ 4-year delay |
| **Patent grant** | ❌ implicit | ✅ explicit | ✅ explicit | ⚠️ |
| **Contributor agreement** | ❌ | ⚠️ recommended | ❌ | ❌ |
| **Modification redistribute** | ✅ | ✅ | ⚠️ same license | ⚠️ |
| **NOTICE file required** | ❌ | ✅ | ❌ | ❌ |
| **OSS-compatible** | ✅ all | ✅ most | ⚠️ limited | ❌ none |
| **Adoption barrier (enterprise)** | 🟢 lowest | 🟢 low | 🔴 high | 🔴 high |
| **Industry standard for tools** | ✅ | ✅ | ❌ | ❌ |
| **Examples** | wp-cli, jQuery | Apache, Kubernetes, Playwright | Plausible, Mastodon | arra-oracle-v3, Sentry |

---

## 2. Trinity-Specific Considerations

### 2.1 What Trinity Is

Trinity OS = **infrastructure tooling** (kernel + CLI tools) for AI workflow.

- Like Kubernetes (Apache-2.0)
- Like Playwright (Apache-2.0)
- Like wp-cli (MIT)
- Like browser-cli (currently internal/MIT)

**NOT like:**
- A SaaS product (would consider AGPL)
- A book or content (would use CC)
- A model/dataset (would use OpenRAIL or similar)

### 2.2 Dependencies' Licenses

| Dep | License | Compatibility |
|-----|---------|---------------|
| Playwright | Apache-2.0 | ✅ compat with both MIT and Apache |
| SQLite | Public domain | ✅ compat with anything |
| ChromaDB | Apache-2.0 | ✅ compat |
| Bun | MIT | ✅ compat |
| Hono | MIT | ✅ compat |
| wp-cli | MIT | ✅ compat |

→ **Both MIT and Apache-2.0 work** for Trinity.

### 2.3 Inspirations' Licenses (study only — no code copied)

| Inspiration | License | Trinity stance |
|-------------|---------|---------------|
| Oracle Framework | (check repo) | Inspiration only — no derivative |
| arra-oracle-v3 | BUSL-1.1 | Inspiration only — independent impl |
| Anthropic 1.6%/98.4% | (insight, not code) | Public statement |

---

## 3. Recommendation Analysis

### 3.1 Option A: Keep MIT ✅ (Status quo)

**Pros:**
- ✅ Already in place
- ✅ Simplest license
- ✅ Most permissive
- ✅ No NOTICE file overhead
- ✅ Compatible with all deps
- ✅ Industry common for tools

**Cons:**
- ❌ No explicit patent grant
- ❌ No standardized notice for contributions

**Best when:** Minimum overhead, maximum freedom, tool/library

---

### 3.2 Option B: Upgrade to Apache-2.0 ⭐ (Recommended for v2)

**Pros:**
- ✅ Explicit patent grant (architectural innovations protected)
- ✅ Industry standard for infrastructure (K8s, Playwright, Apache projects)
- ✅ Better enterprise adoption signal
- ✅ Compatible with all current deps
- ✅ Standardized notice via NOTICE file
- ✅ Defense against patent trolls

**Cons:**
- ⚠️ Migration overhead (notify contributors)
- ⚠️ Need NOTICE file maintenance
- ⚠️ Slightly longer license header

**Best when:** Production infrastructure, multi-contributor, enterprise-targeted

---

### 3.3 Option C: AGPL-3.0 ❌ (Not recommended)

**Why not:**
- ❌ Strong copyleft scares off contributors
- ❌ Commercial users avoid
- ❌ Trinity is tooling not SaaS
- ❌ Not industry-standard for this use case

---

### 3.4 Option D: BUSL-1.1 ❌ (Not recommended)

**Why not:**
- ❌ 4-year commercial restriction limits adoption
- ❌ Complex licensing transition
- ❌ Unusual for kernel/tooling
- ❌ Trinity benefits from network effect

---

## 4. Final Recommendation

### 🎯 **Keep MIT for now, plan Apache-2.0 upgrade for v2.0 production**

**Reasoning:**
1. **MIT is already in place** — no immediate action required
2. **Spec pack (v2 docs)** can stay MIT-licensed
3. **When CLI tools ship** (memory-cli, verify-cli, etc.) — consider Apache-2.0 for new tools
4. **Major version v2.0** of Trinity kernel — opportunity to upgrade license cleanly

### Migration Path (if/when upgrade)

```
1. Notify all Trinity Protocol Contributors
2. Get explicit OK (or assume implicit if no objection in 30 days)
3. Replace LICENSE file with Apache-2.0 text
4. Add NOTICE file with attributions
5. Update copyright headers in source files
6. Bump version to 2.0.0
7. Update README + spec docs
```

---

## 5. License-Per-Component Strategy

### 5.1 Trinity OS Spec Pack (this folder)
**License:** MIT (current) or Apache-2.0 (recommended for v2.0)

### 5.2 CLI Tools
**Recommendation per tool:**

| Tool | Suggested License | Reason |
|------|-------------------|--------|
| browser-cli | MIT or Apache-2.0 | Match Playwright (Apache) |
| memory-cli | Apache-2.0 | Patent considerations (search algorithms) |
| verify-cli | Apache-2.0 | Patent considerations |
| retro-cli | MIT | Simple |
| trinity-shell | Apache-2.0 | Multi-vendor adapter (patent risk) |
| wordpress-cli (wraps wp-cli) | MIT | Match wp-cli |

### 5.3 Documentation
**License:** Same as code (or CC-BY-4.0 for docs-only)

---

## 6. NOTICE File Template (if Apache-2.0)

```
Trinity OS
Copyright 2025-2026 Trinity Protocol Contributors

This product includes software developed at:
- Trinity Protocol Contributors (https://github.com/...)

Inspirations (no code derived):
- Anthropic Claude Code architecture insights (1.6%/98.4%)
- Oracle Framework by Soul-Brews-Studio
- arra-oracle-v3 by Soul-Brews-Studio
- Unix philosophy and microkernel architecture (L4, Plan 9)
- Cognition AI public posts on agent architecture

Major dependencies:
- Playwright (https://playwright.dev) — Apache-2.0
- SQLite (https://sqlite.org) — Public Domain
- ChromaDB (https://trychroma.com) — Apache-2.0 (Phase 9 future)

This software is released under the Apache License, Version 2.0.
See LICENSE file for full terms.
```

---

## 7. Decision Required (Action Items)

### Owner needs to decide:

- [ ] Keep MIT? (option A — status quo, no action)
- [ ] Plan Apache-2.0 upgrade? (option B — schedule for v2.0)
- [ ] Other? (consult contributors)

### If keeping MIT:
- [ ] No action needed
- [ ] Document decision in spec (this doc serves)

### If upgrading to Apache-2.0:
- [ ] Notify contributors
- [ ] Update LICENSE file
- [ ] Create NOTICE file
- [ ] Update spec pack metadata
- [ ] Update CHANGELOG.md

---

## 8. Quick Decision Tree

```
Do you have patent concerns or enterprise users?
  ├─ NO  → Stick with MIT (simpler, fine)
  └─ YES → Upgrade to Apache-2.0

Are you building infrastructure used by many?
  ├─ NO  → MIT is fine
  └─ YES → Apache-2.0 stronger

Do you want CLA (Contributor License Agreement)?
  ├─ NO  → MIT (or Apache without CLA)
  └─ YES → Apache + DCO or CLA

Will competitors run this as SaaS?
  ├─ DON'T CARE → MIT/Apache
  └─ CARE       → Consider AGPL (but barrier to adoption)
```

For Trinity OS as **AI workflow tooling**:
> **MIT or Apache-2.0 — both fine. Default: keep MIT for simplicity.**

---

## 9. Final Answer

> 🎯 **Recommendation: Keep MIT (current), revisit at v2.0 release**
>
> - Simpler
> - Already in place
> - Fits "tooling/library" pattern
> - All deps compatible
> - Can upgrade to Apache-2.0 later cleanly if needed
>
> If patent concerns emerge → upgrade to Apache-2.0 at v2.0.0 milestone.

---

## See also

- [`/TRINITY_LEGACY/LICENSE`](../../LICENSE) — Current MIT license
- [`11_RELATED_PROJECTS.md`](11_RELATED_PROJECTS.md) §9 — Dependency licenses
- [Choose a License](https://choosealicense.com/) — General guidance

## Changelog

- **v1.0 (2026-04-28)** — Initial license decision document
