# memory-cli — frozen contract baseline

This directory is the **frozen contract baseline** for the `memory-cli`
plugin tool. It pins the verb inventory, envelope schema, and policy
defaults that the Trinity kernel speaks against. The actual tool
implementation lives in `../../../../memory-cli/` (sibling of
trinity_v2).

## Why frozen?

Per Decision **D13** (Plugin tool architecture):

> Tools live OUTSIDE `.ai/`; the registry tells the kernel how to
> reach them and which contract version they speak. When a tool's
> implementation evolves (memory-cli v0.2 → v0.3) but the contract
> stays the same, only `tool_version` changes. When the *contract*
> changes (rare), bump `contract_version` and add a new versioned
> directory under `docs/contracts/memory-cli/`.

## Files

| File | What |
|------|------|
| [`COMMAND_CONTRACT.md`](COMMAND_CONTRACT.md) | Verb list + envelope schema + tier defaults |

Future docs (Phase 2.1+):

- `ARCHITECTURE.md` — internal layout (DB, indexer, search)
- `RESPONSE_SCHEMA.md` — JSON Schema for the envelope
- `POLICY_TIERS.md` — per-verb tier rationale
- `AI_AGENT_GUIDE.md` — how an agent should call memory-cli

## Status

**Phase 2.0 alpha** — only the `stats` verb is wired (returns a stub
envelope). The other 11 verbs (`index`, `learn`, `search`, `get`,
`list`, `tag`, `supersede`, `reflect`, `delete`, `reindex`, `health`)
land in Phase 2.1.

The kernel's `contract_version: "1.0"` reflects the **envelope shape**,
which is stable from day one. The alpha-ness of the implementation
is captured in `tool_version: "0.1.0-alpha"` and the `notes:` field of
the registry entry.

## Spec

Full Phase 2 specification:
[`trinity_v2/docs/specs/05_MEMORY_CLI_SPEC.md`](../../specs/05_MEMORY_CLI_SPEC.md)
