"""Doc-coupling drift guard (v1) — manifest, checker, snapshot, changelog, command."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from cli.core import doc_coupling as dc

MANIFEST = textwrap.dedent(
    """
    version: 1
    defaults: {changelog_required: true, timezone: Asia/Bangkok}
    couplings:
      - id: close-ritual
        severity: block
        when_changed: ["core/trinity_v2/.ai/cli/commands/close.py"]
        require_update: ["docs/RITUALS.md"]
        reason: close changed
      - id: sib
        severity: warn
        when_changed: ["siblings/REGISTRY.md"]
        require_update: ["CLAUDE.md"]
        reason: roster
    """
)


def _project(tmp: Path) -> Path:
    (tmp / ".ai" / "policies").mkdir(parents=True)
    (tmp / ".ai" / "policies" / "doc_coupling.yaml").write_text(MANIFEST)
    cp = tmp / "core" / "trinity_v2" / ".ai" / "cli" / "commands"
    cp.mkdir(parents=True)
    (cp / "close.py").write_text("print(1)")
    (tmp / "docs").mkdir()
    (tmp / "docs" / "RITUALS.md").write_text("# rituals")
    (tmp / "siblings").mkdir()
    (tmp / "siblings" / "REGISTRY.md").write_text("19")
    (tmp / "CLAUDE.md").write_text("# claude")
    (tmp / ".state").mkdir()
    return tmp


# ── manifest ────────────────────────────────────────────────────────────
def test_manifest_loads(tmp_path):
    _project(tmp_path)
    m = dc.load_manifest(tmp_path)
    assert m is not None
    assert [c.id for c in m.couplings] == ["close-ritual", "sib"]
    assert m.couplings[0].severity == "block"
    assert m.changelog_required is True


@pytest.fixture
def no_manifest(monkeypatch):
    """Simulate 'no manifest anywhere' by neutralising the kernel-source fallback
    (in-tree, resolve_ai_resource always finds the shipped manifest otherwise)."""
    from cli.core import kernel_resource
    monkeypatch.setattr(kernel_resource, "resolve_ai_resource", lambda *a, **k: (None, "none"))


def test_manifest_missing_returns_none(tmp_path, no_manifest):
    assert dc.load_manifest(tmp_path) is None


def test_manifest_malformed_raises(tmp_path):
    (tmp_path / ".ai" / "policies").mkdir(parents=True)
    (tmp_path / ".ai" / "policies" / "doc_coupling.yaml").write_text(
        "couplings:\n  - severity: block\n"  # missing id
    )
    with pytest.raises(dc.DocCouplingManifestError):
        dc.load_manifest(tmp_path)


def test_bad_severity_raises(tmp_path):
    (tmp_path / ".ai" / "policies").mkdir(parents=True)
    (tmp_path / ".ai" / "policies" / "doc_coupling.yaml").write_text(
        "couplings:\n  - id: x\n    severity: nope\n"
    )
    with pytest.raises(dc.DocCouplingManifestError):
        dc.load_manifest(tmp_path)


# ── glob ────────────────────────────────────────────────────────────────
def test_glob_star_is_single_segment():
    assert dc._glob_to_re("a/*.py").match("a/x.py")
    assert not dc._glob_to_re("a/*.py").match("a/b/x.py")


def test_glob_doublestar_recurses():
    assert dc._glob_to_re("siblings/**/package.json").match("siblings/m/package.json")
    assert dc._glob_to_re("siblings/**/package.json").match("siblings/a/b/package.json")


# ── snapshot + changed-set ──────────────────────────────────────────────
def test_snapshot_stamps_referenced_files(tmp_path):
    _project(tmp_path)
    dc.record_coupling_hashes(tmp_path / ".state", tmp_path)
    stamp = json.loads((tmp_path / ".state" / "doc_coupling_hashes.json").read_text())
    assert "core/trinity_v2/.ai/cli/commands/close.py" in stamp
    assert "docs/RITUALS.md" in stamp and "CLAUDE.md" in stamp


def test_snapshot_noop_without_manifest(tmp_path, no_manifest):
    (tmp_path / ".state").mkdir()
    dc.record_coupling_hashes(tmp_path / ".state", tmp_path)
    assert not (tmp_path / ".state" / "doc_coupling_hashes.json").exists()


def test_changed_set_detects_hash_change(tmp_path):
    _project(tmp_path)
    dc.record_coupling_hashes(tmp_path / ".state", tmp_path)
    (tmp_path / "docs" / "RITUALS.md").write_text("# rituals v2")
    m = dc.load_manifest(tmp_path)
    changed = dc.compute_changed_set(tmp_path, tmp_path / ".state", m)
    assert "docs/RITUALS.md" in changed


# ── check verdicts ──────────────────────────────────────────────────────
def _stamp_then(tmp: Path, mutate):
    _project(tmp)
    dc.record_coupling_hashes(tmp / ".state", tmp)
    mutate(tmp)
    return dc.check(tmp, tmp / ".state", "sess-1")


def test_block_when_code_changed_doc_not(tmp_path):
    def m(t):
        (t / "core/trinity_v2/.ai/cli/commands/close.py").write_text("print(2)")
    r = _stamp_then(tmp_path, m)
    assert r.verdict == "block"
    assert r.blocking[0].coupling_id == "close-ritual"
    assert r.blocking[0].kind == "missing_update"


def test_clean_when_doc_updated_with_changelog(tmp_path):
    def m(t):
        (t / "core/trinity_v2/.ai/cli/commands/close.py").write_text("print(2)")
        (t / "docs/RITUALS.md").write_text(
            "# rituals\n<!-- 2026-06-15T07:42:17+07:00 session sess-1 -->"
        )
    r = _stamp_then(tmp_path, m)
    assert r.verdict == "clean"
    assert r.findings == []


def test_warn_severity_does_not_block(tmp_path):
    def m(t):
        (t / "siblings/REGISTRY.md").write_text("21")
    r = _stamp_then(tmp_path, m)
    assert r.verdict == "warn"
    assert not r.blocking
    assert r.warnings[0].coupling_id == "sib"


def test_missing_changelog_flags(tmp_path):
    def m(t):
        (t / "core/trinity_v2/.ai/cli/commands/close.py").write_text("print(2)")
        (t / "docs/RITUALS.md").write_text("# rituals changed but no changelog entry")
    r = _stamp_then(tmp_path, m)
    kinds = {(f.coupling_id, f.kind) for f in r.findings}
    assert ("close-ritual", "missing_changelog") in kinds
    assert r.verdict == "block"


def test_no_change_is_clean(tmp_path):
    _project(tmp_path)
    dc.record_coupling_hashes(tmp_path / ".state", tmp_path)
    r = dc.check(tmp_path, tmp_path / ".state", "sess-1")
    assert r.verdict == "clean" and not r.findings


def test_no_stamp_is_clean_backward_compat(tmp_path):
    # session created before the sss snapshot hook: no doc_coupling_hashes.json.
    # Changes must NOT false-trigger every coupling (no baseline => git-only => clean).
    _project(tmp_path)
    (tmp_path / "core/trinity_v2/.ai/cli/commands/close.py").write_text("print(2)")
    r = dc.check(tmp_path, tmp_path / ".state", "sess-1")  # .state has no stamp
    assert r.verdict == "clean" and not r.findings


def test_no_manifest_skipped(tmp_path, no_manifest):
    (tmp_path / ".state").mkdir()
    r = dc.check(tmp_path, tmp_path / ".state", "sess-1")
    assert r.skipped is True and r.verdict == "clean"


# ── command serialization ───────────────────────────────────────────────
def test_report_to_dict_shape(tmp_path):
    from cli.commands.doc_drift import report_to_dict

    def m(t):
        (t / "core/trinity_v2/.ai/cli/commands/close.py").write_text("print(2)")
    r = _stamp_then(tmp_path, m)
    d = report_to_dict(r)
    assert d["verdict"] == "block"
    assert d["findings"][0]["coupling_id"] == "close-ritual"
    assert "route" in d["findings"][0]
