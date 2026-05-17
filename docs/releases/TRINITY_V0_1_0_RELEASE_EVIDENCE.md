# Trinity v0.1.0 Release Evidence

## Test Command

```bash
python3 -m pytest .ai/cli/tests -q
```

## Result

Source checkout with optional sibling tools available:

```text
1862 passed, 6 skipped in 12.85s
```

Clean GitHub export in a temp clone, without optional sibling tools:

```text
1860 passed, 8 skipped in 14.33s
```

The additional clean-export skips are optional sibling integration checks for
`judge-cli` and `memory-cli`; the CLI suite exits successfully.

## Release Gate Status

- Package cleanliness: PASS
- Clean export UX: PASS
- Audit genesis in export: PASS
- State schema drift: PASS
- RRR memory index contract: PASS
- Full CLI test suite: PASS

## Verified Commit

The verified commit is the commit targeted by the annotated `v0.1.0` tag.
The tag message records the final post-commit test command and result.
