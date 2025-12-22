# Trinity CI Workflow (Lean, Full Suite)

Goal: กัน regression/silent failure โดยไม่ช้าเกินไป

## Stages
1) Lint / Format (เร็ว)
   - `ruff` หรือ `flake8` (fail fast)

2) Unit Tests
   - `pytest -q` (core logic: state, patch, fs, vault)

3) CLI Selftest
   - `./.ai/cli/ai verify selftest`
   - ตรวจ gate logic และ fixture generation

4) Integration Smoke (minimal)
   - สร้าง temp project
   - `ai session new` → `ai snapshot run` → `ai verify dev` (dry)
   - เป้าหมาย: ไม่มี crash, gate ทำงาน

Optional (ภายหลัง)
- Diff/risk summary dry-run
- `ai doctor` (เมื่อมี) เพื่อตรวจ config/state/locks

## Branch Protection Suggestion
- Require CI pass
- Prefer squash merge
- (Optional) Require 1 reviewer

## Example GitHub Actions Sketch
```yaml
name: ci
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r .ai/requirements.txt ruff
      - run: ruff check .ai/cli
  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r .ai/requirements.txt pytest
      - run: pytest -q .ai/cli/tests
  selftest:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r .ai/requirements.txt
      - run: cd .ai && python -m cli.main verify selftest
  smoke:
    runs-on: ubuntu-latest
    needs: selftest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r .ai/requirements.txt
      - name: Smoke flow
        run: |
          cd .ai
          python -m cli.main session new "ci_smoke"
          python -m cli.main snapshot run
          python -m cli.main verify dev
```
