# Release Gate

Release ของ Trinity ต้องผูก test evidence กับ commit จริง

## ห้ามทำ

```text
dirty worktree -> run tests -> tag old HEAD
```

เพราะ tag จะไม่ชี้ไป state ที่ verify แล้วจริง

## ลำดับที่ถูก

```bash
git status
git diff --stat
git add .
git commit -m "chore(release): prepare Trinity v0.1.0 stable"
python3 -m pytest .ai/cli/tests -q
git tag -a v0.1.0 -m "Trinity v0.1.0 stable"
```

## Gate Checklist

- Worktree clean after commit
- Full CLI test suite passes on that commit
- Release evidence exists in `docs/releases/`
- Git tag points to verified commit
- Export package passes cleanliness scan
- Push happens only after local provenance is correct

## Current v0.1.0 Evidence

See:

```text
docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md
```
