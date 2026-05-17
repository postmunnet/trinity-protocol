---
title: "Trinity Tool Contracts — Index"
status: stable
last-updated: 2026-04-30
audience: "Anyone building or registering a tool for Trinity"
---

# Trinity Tool Contracts

> Frozen contract baselines for every tool that plugs into Trinity.
> Trinity kernel uses these to verify version compatibility — tools may
> evolve, but the **contract** here is the stable handshake.

## What lives here

Each subdirectory is a **frozen contract baseline** for one tool:

| Tool | Contract version | Status | Used by |
|------|------------------|--------|---------|
| [`browser-cli/`](browser-cli/) | v1.0 | ✅ Active | Web automation organ — the "eyes & hands" |
| `memory-cli/` | — | 🟡 Planned (Phase 2) | Search/index/recall over Knowledge Brain |
| `verify-cli/` | — | 🟡 Planned (Phase 4) | Runtime verifier rules engine |
| `retro-cli/` | — | 🟡 Planned (Phase 6) | Retrospective intake / `rrr` automation |

## What "contract baseline" means

When a tool ships v2, v3, ..., its **implementation** changes — new flags,
new internal schemas, refactored code. Trinity kernel doesn't care about any
of that, as long as the **handshake** stays the same:

1. **Binary interface** — entry point convention, exit codes, stdin/stdout JSON
2. **Universal flags** — `--config`, `--run-id`, `--log-file`, `--policy`
3. **Response envelope** — `{ ok, data, error, meta }` shape
4. **Discovery** — `--list-commands`, `--describe`, `--health`
5. **Policy tier** — `safe` / `normal` / `aggressive`

The frozen markdown here documents **exactly what that handshake is** at the
moment the contract was minted. If a tool wants to update the contract (real
breaking change), it bumps `contract_version` in `.ai/tools.yaml` and a new
folder appears here (e.g. `browser-cli-v2/`).

## How a tool gets registered

1. Tool author writes implementation that conforms to a contract version listed
   in [`docs/specs/01_TOOL_CONTRACT.md`](../specs/01_TOOL_CONTRACT.md).
2. Tool author copies (or links) docs to `docs/contracts/<tool-name>/` here.
3. Add an entry to [`.ai/tools.yaml`](../../.ai/tools.yaml) with:
   - `name`, `path`, `bin`
   - `schema_version`, `contract_version`
   - `contract_baseline: docs/contracts/<tool-name>/`
   - `capabilities`, `policy_default`, `health_check`
4. Pass `trinity-contract-test <tool-name>` (Phase 5+).
5. Commit. Kernel can now invoke the tool.

See [`01_TOOL_CONTRACT.md §16`](../specs/01_TOOL_CONTRACT.md) for the full
registry format and [`16a` Contract Compliance Test] for verification rules.

## Per-tool contract docs

Each tool's folder typically contains:

| File | Purpose |
|------|---------|
| `README.md` | "Frozen baseline" notice + index of files in this folder |
| `COMMAND_CONTRACT.md` | Command envelope schema + validation rules |
| `RESPONSE_SCHEMA.md` | Response envelope shapes (success + error) |
| `POLICY_TIERS.md` | Which actions belong to which tier |
| `ARCHITECTURE.md` | Internal layout (template — not implementation requirement) |
| `AI_AGENT_GUIDE.md` | How an AI agent invokes the tool from a sandbox |

JSON Schemas live one folder up at [`docs/schemas/<tool-name>/`](../schemas/).

## Boundaries

- ❌ These are docs only — no runtime dep, no implementation copied here
- ❌ Don't edit a contract baseline post-mint; bump `contract_version` instead
- ✅ Reference these baselines from `.ai/tools.yaml` for verifiability
- ✅ Use them as the authoritative spec when refactoring a tool's CLI surface
