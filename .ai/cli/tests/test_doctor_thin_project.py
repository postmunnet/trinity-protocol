"""doctor commands resolves COMMAND_MANIFEST from the kernel source root when the
cwd has no local .ai/cli — i.e. when run inside a THIN project (kernel resolves
from the central runtime). Regression for the thin-project manifest gap."""
from __future__ import annotations

from pathlib import Path

from cli.commands.doctor import _find_repo_root, _load_manifest


def test_find_repo_root_falls_back_to_kernel(tmp_path):
    # tmp_path has NO .ai/cli/COMMAND_MANIFEST.yaml (like a thin project's cwd).
    root = _find_repo_root(tmp_path)
    # fallback resolves to the kernel source root, which DOES ship the manifest.
    assert (root / ".ai" / "cli" / "COMMAND_MANIFEST.yaml").exists(), \
        "thin-project fallback should resolve the kernel-source manifest"
    # and it loads without raising FileNotFoundError.
    manifest = _load_manifest(root)
    assert isinstance(manifest, dict)


def test_find_repo_root_prefers_cwd_when_manifest_present(tmp_path):
    # If the cwd ancestor has a manifest, the operator PWD wins (preference kept).
    cli_dir = tmp_path / ".ai" / "cli"
    cli_dir.mkdir(parents=True)
    (cli_dir / "COMMAND_MANIFEST.yaml").write_text("doctor_survey: []\n", encoding="utf-8")
    assert _find_repo_root(tmp_path) == tmp_path.resolve()
