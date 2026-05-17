---
title: "browser-cli — Frozen Contract Baseline v1.0"
status: frozen-baseline
contract_version: "1.0"
last-updated: 2026-04-30
audience: "Trinity kernel + tool authors targeting browser-cli compatibility"
source: "<workspace-root>/browser-cli @ v1.0.0 (snapshot)"
registered-as: "browser-cli (active)"
registry-entry: ".ai/tools.yaml → tools[name=browser-cli]"
---

# browser-cli — Frozen Contract Baseline v1.0

> ✅ **REGISTERED & ACTIVE** — see `.ai/tools.yaml`
> 🧊 **FROZEN BASELINE** — this folder is the version-pinned contract. Don't
> edit it after mint; bump `contract_version` and create a new folder if a
> real breaking change is needed.
>
> Trinity kernel uses this baseline to verify that whatever browser-cli build
> is on disk speaks the same handshake. The implementation can evolve freely
> (v1.0 → v1.1 → v1.2 …); the kernel only re-reads this folder when
> `contract_version` itself changes.

## Why this baseline exists

Trinity is **CLI-native** — every tool talks to the kernel through:
1. **stdin** → JSON command envelope (see `COMMAND_CONTRACT.md`)
2. **stdout** → JSON response envelope (see `RESPONSE_SCHEMA.md`)
3. **policy tier** → declared in tool registry (see `POLICY_TIERS.md`)

browser-cli is the **first plug** in Trinity's plugin tool architecture
(Decision **D13**). This frozen baseline is what the kernel checks against,
so the actual browser-cli source repo can iterate quickly without forcing
a Trinity kernel update on every change.

If you're building a new tool, model its CLI surface and response shape
after these files — they document a known-good handshake.

## Files in this folder

| File | What it covers |
|------|----------------|
| `COMMAND_CONTRACT.md` | Command envelope schema, required/optional fields, validation rules |
| `RESPONSE_SCHEMA.md` | Response envelope (success + error shapes), correlation IDs |
| `POLICY_TIERS.md` | Tier 1 (read-only) → Tier 2 (write-local) → Tier 3 (external) — what permissions each tier needs |
| `ARCHITECTURE.md` | Internal layout (process model, lifecycle, recorder hooks) — useful as a structural template |
| `AI_AGENT_GUIDE.md` | How an AI agent should invoke a Trinity tool from a sandbox |

## Companion schemas

See `../../schemas/browser-cli/` for the JSON Schema definitions that the
markdown contracts above describe formally:
- `config.schema.json` — config file shape
- `response-v2.schema.json` — response envelope (current version)

## Boundaries

- ❌ Do NOT install browser-cli into trinity_v2 as a runtime dependency
- ❌ Do NOT copy implementation code from this reference into `.ai/cli/`
- ✅ DO use these contracts as the design template for `.ai/tools.yaml` entries
- ✅ DO link to specific sections when writing your tool's contract doc

## When this becomes outdated

These docs are a **point-in-time snapshot**. If browser-cli evolves materially
(v2 contract, new policy tiers), refresh this folder via:

```bash
cp <workspace-root>/browser-cli/docs/{COMMAND_CONTRACT,RESPONSE_SCHEMA,POLICY_TIERS,ARCHITECTURE,AI_AGENT_GUIDE}.md \
   trinity_v2/docs/contracts/browser-cli/
cp <workspace-root>/browser-cli/schema/{config,response-v2}.schema.json \
   trinity_v2/docs/schemas/browser-cli/
```

Then bump `last-updated` + `source` in the frontmatter above.
