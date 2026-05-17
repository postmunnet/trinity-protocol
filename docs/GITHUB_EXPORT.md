# GitHub Export

Use this when you want a clean folder to push to GitHub without local Trinity
runtime history, sessions, audit events, memory DBs, local registry files, or
reference corpora.

```bash
bash scripts/export_github.sh
```

Default output:

```txt
../trinity_v2_github_export
```

Custom output:

```bash
bash scripts/export_github.sh /path/to/export-folder
```

Build a clean zip for upload or transfer:

```bash
bash scripts/package_github_zip.sh
```

Custom folder and zip path:

```bash
bash scripts/package_github_zip.sh /path/to/export-folder /path/to/trinity_v2.clean.zip
```

The export is controlled by `.github-export-ignore`. The script copies source
files with `rsync`, recreates empty runtime placeholder directories, and writes
`EXPORT_MANIFEST.md` in the export folder.

The zip packaging script re-runs the export, strips macOS resource metadata
(`__MACOSX`, `._*`, `.DS_Store`) via `zip -X`, and excludes `.git` /
`.pytest_cache` directories.

Before pushing:

```bash
cd ../trinity_v2_github_export
git init
git status --short
rg -n "SECRET|TOKEN|PASSWORD|PRIVATE KEY|<user-home>" .
```

Do not publish until license, secrets, and project-specific path review are
done.
