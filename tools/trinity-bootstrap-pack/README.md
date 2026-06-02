# trinity-bootstrap-pack — v1.2

Install Trinity OS into a target project directory in **one command**.

> v1.2 (2026-05-23) fixes v1.1 bug where `sss`/`vvv` crashed in bootstrap-installed
> projects because the kernel needs `templates/`, `graphs/`, `schemas/`, `shims/`,
> and `checklists/` at runtime — not just `cli/` + `rituals/`. v1.2 symlinks
> all 7 kernel-canonical dirs (was 2). Also fixes kernel `session.py` to store
> absolute `current_session` paths (was relative under bootstrap setups).

## Quick start — three flavours

### 1. From a local trinity_v2 clone (most common)

```bash
bash tools/trinity-bootstrap-pack/install.sh ~/code/my-app --project-name my-app
```

### 2. From the GitHub repo (curl|bash — single line)

```bash
curl -fsSL https://raw.githubusercontent.com/postmunnet/trinity-protocol/main/tools/trinity-bootstrap-pack/bootstrap.sh \
    | bash -s -- ~/code/my-app --project-name my-app
```

### 3. From a `git clone`d kernel cache

```bash
git clone https://github.com/postmunnet/trinity-protocol.git ~/.trinity-kernel
bash ~/.trinity-kernel/tools/trinity-bootstrap-pack/install.sh ~/code/my-app --project-name my-app
```

After install, the target has a **fully-wired Trinity setup**:
- `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` entrypoints (project name substituted)
- `.ai/` project-customizable files: `ssot.yaml`, `tools.yaml`, `policies/`
- `.ai/cli/`, `.ai/rituals/`, `.ai/graphs/`, `.ai/schemas/`, `.ai/shims/`, `.ai/templates/`, `.ai/checklists/` ← all symlinked (or copied) from trinity_v2 — the kernel-canonical runtime
- `.ai/requirements.txt`, `.ai/tools.capabilities.yaml` ← always copied
- `ai-docs/`: `QUICK_START.md`, `SHORT_CODES.md`, `CORE_RULES.md`, `WORKFLOW.md`
- `.trinity-install-receipt.json` with pack version + sha256 manifest + kernel-wire info

Then operator runs:
```bash
cd ~/code/my-app
pip install -r .ai/requirements.txt   # one-time
bash .ai/cli/ai lll                   # smoke test
```

## install.sh flags

| Flag | Purpose |
|---|---|
| `<target>` (positional) **OR** `--target <dir>` | Target project root. |
| `--project-name <name>` | Substitution value for `{{PROJECT_NAME}}` placeholders. |
| `--mode <auto\|greenfield\|upgrade-v1\|upgrade-v2\|self>` | Default `auto`. |
| `--with-kernel <symlink\|copy\|none>` | Default `symlink`. `copy` makes the install standalone; `none` skips kernel wiring entirely. |
| `--no-kernel` | Alias for `--with-kernel none`. |
| `--ref <git-ref>` | Informational; pin is enforced by `bootstrap.sh`. |
| `--dry-run` | Emit receipt; do not write files. |
| `--force` | Overwrite non-empty target (and existing kernel-wire targets). |
| `--allow-self-install` | Permit install into trinity_v2 itself (refused by default). |

## bootstrap.sh (curl|bash entry)

| Flag | Purpose |
|---|---|
| `--ref <git-ref>` | Branch / tag / commit (default: `main`). |
| `--kernel-cache <path>` | Override `$TRINITY_KERNEL_CACHE` (default: `~/.trinity-kernel`). |
| `--no-update` | Skip `git pull` if cache exists (offline-friendly). |

Env: `TRINITY_KERNEL_CACHE`, `TRINITY_REPO_URL` override defaults.

All remaining args are passed through to `install.sh`.

## Kernel wiring modes

| Mode | Behaviour | When to use |
|---|---|---|
| `symlink` (default) | `.ai/cli`, `.ai/rituals` → symlinks to trinity_v2 source | Local dev: one source of truth, kernel updates flow through |
| `copy` | Deep-copies kernel into target | Standalone projects, archival, when target may move |
| `submodule` | (reserved for v1.2) | Team repos with pinned kernel version |
| `none` | Bootstrap layer only; operator wires manually | Power users, snapshot pack distribution |

## Modes (auto-detect)

| Mode | Trigger | Behaviour |
|---|---|---|
| `greenfield` | Target has no Trinity markers | Lay down full pack |
| `upgrade-v1` | Target has `ai-docs/` or `CLAUDE.md` but no `.ai/cli/` | Lay down `.ai/` skeleton; skip files that already exist |
| `upgrade-v2` | Target has `.ai/cli/` already | Lay down only NEW files; preserve existing kernel |
| `self` | Target IS trinity_v2 source root | Refused unless `--allow-self-install` |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK (install or dry-run) |
| 10 | Preflight failure (bash / python / git missing) |
| 20 | Target unsafe (non-empty without `--force`, or self-install without flag) |
| 30 | Unknown / unsupported mode |
| 40 | Pack source missing |
| 50 | Unexpected error |

## Requirements

- bash 3.2+ (matches macOS default; spec 09 §1.1 lists 4+ aspirationally)
- Python 3.9+ (PEP 585 generics via `from __future__ import annotations`)
- git
- sqlite3 (warn-only — needed for memory-cli later)

## Verify

```bash
bash tools/trinity-bootstrap-pack/verify-install.sh --target /path/to/installed/project
```

## Test

```bash
python3 -m pytest tools/trinity-bootstrap-pack/tests -q
```

## Re-snapshot cadence

The pack ships a frozen snapshot under `pack/`. To re-snapshot from a newer
trinity_v2 commit, manually update files under `pack/` and run the pytest
suite — `test_pack_manifest.py` rebuilds the sha256 list at test time, so
the manifest stays self-consistent. Auto-sync is deferred to v2.

## Boundary contract

Per [Article XXV] in [`docs/constitution/TRINITY_CONSTITUTION_V1.md`](../../docs/constitution/TRINITY_CONSTITUTION_V1.md),
the installer NEVER mutates the upstream trinity_v2 repo:
- It only writes under `--target` (and the receipt under `--target/.trinity-install-receipt.json`).
- It refuses self-install by default (`--allow-self-install` overrides for power users).
- It does not run network ops, `git push`, or modify hooks.
