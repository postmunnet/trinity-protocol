# Version Lineage

Language: English | [ไทย](VERSION_LINEAGE_TH.md)

Trinity uses separate version lines for architecture, runtime, and tool
contracts. They should not be collapsed into one number.

```text
Trinity Protocol v2  = architecture / constitution generation
Runtime v0.1.0       = first public executable runtime line
Tool Contract        = v1.0 freeze candidate, v1.1 draft working spec
```

## v0.1.0

Trinity v0.1.0 is the first stable-ready public release line for the
standalone `trinity_v2` repository.

This repository previously contained earlier experimental Trinity Protocol
materials. From `v0.1.0` onward, the root tree is the canonical Trinity v2
executable governance kernel. Legacy materials remain available through Git
history.

Release evidence:

- [`docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md`](releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md)

Verified command:

```bash
python3 -m pytest .ai/cli/tests -q
```

Verified result:

```text
Source checkout: 1862 passed, 6 skipped
Clean export without optional sibling tools: 1860 passed, 8 skipped
```

## Lineage

- Source family: `TRINITY_ULTIMAT` kernel lessons and migration evidence.
- Current repo: `trinity_v2`, clean public bootstrap/runtime target.
- Public export: generated with `scripts/export_github.sh` and
  `scripts/package_github_zip.sh`.

## Release Discipline

A stable tag must point to the commit that passed verification. Do not tag a
dirty worktree. Do not tag an older commit with evidence from newer files.
