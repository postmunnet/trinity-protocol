# Release Gate

A Trinity release must bind test evidence to the actual commit being tagged.

## Forbidden

```text
dirty worktree -> run tests -> tag old HEAD
```

That creates a tag that does not point at the verified state.

## Correct Sequence

```bash
git status
git diff --stat
git add .
git commit -m "chore(release): prepare Trinity v0.1.0 stable"
python3 -m pytest .ai/cli/tests -q
git tag -a v0.1.0 -m "Trinity v0.1.0 stable"
```

## Gate Checklist

- Worktree is clean after commit.
- Full CLI test suite passes on that commit.
- Release evidence exists in `docs/releases/`.
- Git tag points to the verified commit.
- Export package passes cleanliness scan.
- Push happens only after local provenance is correct.

## Current v0.1.0 Evidence

See:

```text
docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md
```
