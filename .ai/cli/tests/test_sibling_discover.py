"""Sibling auto-discovery via per-sibling ``trinity.yaml`` manifests.

Phase A1 of the monorepo migration roadmap. Validates the kernel-side
discovery wiring in ``cli.core.tools_registry``:

  - backward-compat: no ``TRINITY_SIBLINGS_ROOT`` env -> behavior unchanged
  - opt-in discovery: env set -> ``<root>/*/trinity.yaml`` merged into registry
  - manifest entries override legacy ``tools.yaml`` by name (refinement D)
  - manifest-vs-manifest name dup -> hard fail (refinement D)
  - strict validation: required fields, relative bin only, schema forward-lock
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.tools_registry import (
    SiblingDuplicateError,
    ToolEntry,
    _validate_manifest,
    discover_siblings,
    load_registry,
)


def _write_manifest(dir_: Path, body: dict, *, name: str = "trinity.yaml") -> Path:
    """Write a manifest dict as YAML at ``dir_/<name>`` and return the path.

    Uses bare yaml.safe_dump rather than f-strings so future schema changes
    don't break tests on whitespace.
    """
    import yaml

    path = dir_ / name
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(body, f)
    return path


def _make_sibling(root: Path, name: str, manifest: dict) -> Path:
    """Scaffold ``root/<name>/trinity.yaml`` + ``root/<name>/index.js``."""
    sib = root / name
    sib.mkdir(parents=True, exist_ok=True)
    (sib / "index.js").write_text("// stub\n", encoding="utf-8")
    return _write_manifest(sib, manifest)


def _minimal_manifest(name: str = "memory-cli") -> dict:
    return {
        "schema_version": "1",
        "name": name,
        "description": "smoke fixture",
        "runtime": "node",
        "bin": "./index.js",
        "contract_version": "0.0.0-test",
        "engines": {"node": ">=22.5.0"},
        "capabilities": ["memory.search"],
    }


# ---------------------------------------------------------------------------
# Core acceptance gates (a-f)
# ---------------------------------------------------------------------------


def test_no_env_unchanged(tmp_path, monkeypatch):
    """Gate (a): no TRINITY_SIBLINGS_ROOT -> registry equals legacy-only path."""
    monkeypatch.delenv("TRINITY_SIBLINGS_ROOT", raising=False)
    # Empty project_root -> no .ai/tools.yaml -> empty registry. The point
    # is that with no env, discover_siblings is never invoked.
    project_root = tmp_path / "proj"
    project_root.mkdir()
    reg = load_registry(project_root)
    assert reg == {}


def test_env_set_discovers(tmp_path, monkeypatch):
    """Gate (b): env set -> scan finds manifest, source='manifest'."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    _make_sibling(siblings_root, "memory-cli", _minimal_manifest("memory-cli"))

    monkeypatch.setenv("TRINITY_SIBLINGS_ROOT", str(siblings_root))
    reg = load_registry(project_root)

    assert "memory-cli" in reg
    assert reg["memory-cli"].source == "manifest"
    assert reg["memory-cli"].manifest_path is not None
    assert reg["memory-cli"].manifest_path.name == "trinity.yaml"


def test_relative_bin_resolves(tmp_path, monkeypatch):
    """Gate (c): bin='./index.js' resolves to <manifest_dir>/index.js."""
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    sib_path = _make_sibling(
        siblings_root, "memory-cli", _minimal_manifest()
    ).parent

    discovered = discover_siblings(siblings_root)
    entry = discovered["memory-cli"]
    # bin_argv = ["node", "<resolved abs path to index.js>"]
    assert entry.bin_argv[0] == "node"
    assert entry.bin_argv[1] == str((sib_path / "index.js").resolve())


def test_manifest_overrides_legacy(tmp_path, monkeypatch):
    """Gate (d): manifest 'memory-cli' overrides legacy tools.yaml 'memory-cli'."""
    project_root = tmp_path / "proj"
    (project_root / ".ai").mkdir(parents=True)
    legacy = {
        "version": "1.0",
        "tools": [{
            "name": "memory-cli",
            "path": "/legacy/path",
            "bin": "node /legacy/path/index.js",
            "schema_version": "1",
            "contract_version": "legacy-version",
        }],
    }
    import yaml
    (project_root / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump(legacy), encoding="utf-8"
    )

    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    _make_sibling(siblings_root, "memory-cli", _minimal_manifest())

    monkeypatch.setenv("TRINITY_SIBLINGS_ROOT", str(siblings_root))
    reg = load_registry(project_root)

    assert reg["memory-cli"].source == "manifest"
    assert reg["memory-cli"].contract_version == "0.0.0-test"


def test_invalid_manifest_warns_no_crash(tmp_path, monkeypatch, caplog):
    """Gate (e): manifest missing 'name' -> warn + skip + no crash."""
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    bad = _minimal_manifest()
    del bad["name"]
    _make_sibling(siblings_root, "broken-sibling", bad)

    with caplog.at_level("WARNING"):
        discovered = discover_siblings(siblings_root)

    assert discovered == {}
    assert any("skipping invalid manifest" in r.message for r in caplog.records)


def test_status_shows_source(tmp_path, monkeypatch):
    """Gate (f): every ToolEntry exposes source; downstream ``ai status``
    formatters can read it without conditional probing.
    """
    project_root = tmp_path / "proj"
    (project_root / ".ai").mkdir(parents=True)
    import yaml
    (project_root / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump({
            "tools": [{
                "name": "notify-cli",
                "path": "/x",
                "bin": "node /x/index.js",
                "schema_version": "1",
                "contract_version": "legacy",
            }],
        }),
        encoding="utf-8",
    )
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    _make_sibling(siblings_root, "memory-cli", _minimal_manifest())

    monkeypatch.setenv("TRINITY_SIBLINGS_ROOT", str(siblings_root))
    reg = load_registry(project_root)

    assert reg["notify-cli"].source == "legacy"
    assert reg["memory-cli"].source == "manifest"


# ---------------------------------------------------------------------------
# Refinement gates (g-j)
# ---------------------------------------------------------------------------


def test_manifest_dup_hard_fails(tmp_path):
    """Gate (g): two manifests claiming the same name -> SiblingDuplicateError."""
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    _make_sibling(siblings_root, "sib-a", _minimal_manifest("same-name"))
    _make_sibling(siblings_root, "sib-b", _minimal_manifest("same-name"))

    with pytest.raises(SiblingDuplicateError) as exc_info:
        discover_siblings(siblings_root)

    assert exc_info.value.name == "same-name"


def test_absolute_bin_rejected(tmp_path, caplog):
    """Gate (h): bin='/usr/local/bin/foo' rejected by default."""
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    bad = _minimal_manifest()
    bad["bin"] = "/usr/local/bin/foo"
    _make_sibling(siblings_root, "absolute-sib", bad)

    with caplog.at_level("WARNING"):
        discovered = discover_siblings(siblings_root)

    assert "memory-cli" not in discovered
    assert any("absolute bin rejected" in r.message for r in caplog.records)


def test_schema_v2_rejected(tmp_path, caplog):
    """Gate (i): schema_version='2' rejected (forward-lock)."""
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    future = _minimal_manifest()
    future["schema_version"] = "2"
    _make_sibling(siblings_root, "future-sib", future)

    with caplog.at_level("WARNING"):
        discovered = discover_siblings(siblings_root)

    assert discovered == {}
    assert any(
        "forward-lock" in r.message for r in caplog.records
    )


def test_source_field_populated(tmp_path, monkeypatch):
    """Gate (j): every ToolEntry has source set to 'manifest' or 'legacy'."""
    project_root = tmp_path / "proj"
    (project_root / ".ai").mkdir(parents=True)
    import yaml
    (project_root / ".ai" / "tools.yaml").write_text(
        yaml.safe_dump({
            "tools": [{
                "name": "legacy-only",
                "path": "/x", "bin": "node /x/index.js",
                "schema_version": "1", "contract_version": "v0",
            }],
        }),
        encoding="utf-8",
    )
    siblings_root = tmp_path / "siblings"
    siblings_root.mkdir()
    _make_sibling(siblings_root, "manifest-only", _minimal_manifest("manifest-only"))

    monkeypatch.setenv("TRINITY_SIBLINGS_ROOT", str(siblings_root))
    reg = load_registry(project_root)

    for name, entry in reg.items():
        assert entry.source in {"legacy", "manifest"}, (
            f"tool {name!r} has unexpected source={entry.source!r}"
        )


# ---------------------------------------------------------------------------
# Direct unit tests for _validate_manifest (path-traversal coverage)
# ---------------------------------------------------------------------------


def test_validate_rejects_path_traversal(tmp_path):
    """bin='../escape.js' must be rejected even though it's relative."""
    sib_dir = tmp_path / "sib"
    sib_dir.mkdir()
    manifest_path = sib_dir / "trinity.yaml"
    manifest_path.write_text("# stub\n", encoding="utf-8")

    m = _minimal_manifest()
    m["bin"] = "../escape.js"
    ok, reason = _validate_manifest(m, manifest_path)
    assert not ok
    assert "traversal" in reason
