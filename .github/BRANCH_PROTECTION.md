# Branch protection policy for `main`

To keep the Trinity Protocol repository safe, enable GitHub branch protection on `main` with these rules:

1. **Require status checks to pass before merging**
   - Add `CI` (from `.github/workflows/ci.yml`) as a required status check.
   - Keep "Require branches to be up to date before merging" enabled so the checks run on the latest code.

2. **Require pull request reviews before merging**
   - Minimum approvals: **1**.
   - Dismiss stale approvals when new commits are pushed.

3. **Optional but recommended**
   - Restrict who can push directly to `main` to repo admins or a release bot.
   - Enable "Require signed commits" if your org mandates it.

These settings ensure every change to `main` is tested by the automated workflow and reviewed by at least one maintainer.
