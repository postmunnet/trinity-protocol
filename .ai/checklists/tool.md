# Tool Checklist

Use this before adding or registering a CLI organ in Trinity.

Sources:
- `docs/specs/01_TOOL_CONTRACT.md`
- `docs/specs/CONTRIBUTING.md`
- `.ai/tools.yaml`
- `.ai/tools.capabilities.yaml`

## Pre-Flight

- [ ] Read the tool contract.
- [ ] Choose an action namespace, for example `browser.*` or `memory.*`.
- [ ] Define verbs and classify each by policy tier.
- [ ] Identify external dependencies and install path.
- [ ] Decide whether this belongs inside `.ai/cli/agents/` or as a sibling tool.

## Binary Interface

- [ ] Single binary entry point exists.
- [ ] Single-command mode works.
- [ ] REPL mode works, if required by contract.
- [ ] Pipe mode works.
- [ ] Run-file mode works.
- [ ] Exit codes match the contract.
- [ ] stdin/stdout/stderr discipline is correct.
- [ ] UTF-8 encoding is used.

## Response Envelope

- [ ] Every response has `ok`, `command`, `data`, `artifacts`, `error`, `meta`.
- [ ] `meta` includes tool, schema_version, run_id, duration_ms, timestamp.
- [ ] Error envelopes include `error.code` and `error.message`.
- [ ] NDJSON output is single-line when required.

## Discovery And Flags

- [ ] Universal flags exist: `--config`, `--run-id`, `--log-file`, `--policy`, `--response-schema`, `--cmd`, `--run-file`.
- [ ] Discovery flags exist: `--help`, `--version`, `--list-commands`, `--describe`, `--health`.
- [ ] `--describe` includes verb tier and destructive/write classification.

## Policy And Capability

- [ ] Policy tier is enforced before execution.
- [ ] Policy violation exits with the contracted code and envelope.
- [ ] Required capabilities are declared in `.ai/tools.capabilities.yaml`.
- [ ] Tool name exists in `.ai/tools.yaml`.
- [ ] Capability names match the closed vocabulary.
- [ ] Tool does not request `audit.append`, policy write, deploy decide, or other never-granted authority.

## Documentation

- [ ] README exists.
- [ ] Architecture doc exists.
- [ ] Command contract exists.
- [ ] AI agent guide exists.
- [ ] Config schema exists.
- [ ] Response schema exists.

## Tests

- [ ] Unit harness passes.
- [ ] Golden/integration tests pass.
- [ ] Schema validation tests pass.
- [ ] Tool health check passes.
- [ ] Trinity registry load test passes.

## Memory-CLI Health Maintenance Guide

Use this when `memory-cli health` returns `data.status=warn` and the only
warning check is `artifact_disk_scan`.

### What The Warning Means

- `artifact_disk_scan.status=warn` with `reason=hash_mismatch` means the file
  still exists, but its current SHA-256 differs from the SHA-256 stored in the
  memory DB.
- This is stale index metadata, not DB corruption, when these checks still
  pass: `integrity_check`, `foreign_key_check`, `schema_version`,
  `fts_row_parity`, `pin_orphans`, and `pack_item_orphans`.
- Typical cause: `.ai/memory/retros/*.md` changed after an earlier index run,
  for example after `git pull`, merge, migration, or manual retro edits.

### Canonical Commands

Use the Trinity memory DB explicitly:

```bash
TRINITY_MEMORY_DB=.ai/.memory/memory.sqlite node ../memory-cli/index.js --cmd "health"
```

If health reports stale retro artifacts, refresh the index from source:

```bash
TRINITY_MEMORY_DB=.ai/.memory/memory.sqlite node ../memory-cli/index.js --cmd "index .ai/memory/retros"
```

Then confirm:

```bash
TRINITY_MEMORY_DB=.ai/.memory/memory.sqlite node ../memory-cli/index.js --cmd "health"
```

Expected healthy result:

- [ ] `data.status` is `pass`.
- [ ] `artifact_disk_scan.detail.stale` is `0`.
- [ ] `artifact_disk_scan.detail.missing` is `0`.
- [ ] `errors` from the index run is `0`.

### Prevention Rules

- [ ] Treat `.ai/memory/retros/*.md` as append-only after `rrr` indexes them.
- [ ] If a retro must be corrected, prefer creating a new retro that supersedes
      or references the old one instead of editing the old file in place.
- [ ] After `git pull`, merge, migration, or any change under
      `.ai/memory/retros/**`, run the reindex command above before trusting
      memory search results.
- [ ] `lll`, `sss`, or session start checks should surface memory health
      warnings with the reindex command as the next action.
- [ ] For COLD-tier work, stale or failed memory indexing should block terminal
      completion until health returns to PASS.

### Do Not Use First

- [ ] Do not use `clean --apply` as the first response to `hash_mismatch`.
      `clean --apply` removes stale artifacts from the DB; it does not refresh
      the DB with the latest file content.
- [ ] Use `clean --apply` only when artifacts are intentionally removed or when
      an operator explicitly wants to drop stale/missing records.
