"""G16 — ritual-pack self-heal must not revert a COMMITTED contract edit.

Context (session close-P0-safety): ritual.contract.json is in
ritual_pack_loader._PACK_FILES, so load_pack()'s _self_heal_pack_files()
will restore it from git HEAD when the working tree drifts. That makes the
edit→commit→test sequence mandatory: an uncommitted contract edit is
silently reverted mid-run; a committed one survives.

These tests pin that behaviour so a future regression in the self-heal logic
(or a careless uncommitted edit) is caught.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from cli.core.ritual_pack_loader import _self_heal_pack_files

# test file: <root>/.ai/cli/tests/<this> -> parents[3] == <root> (trinity_v2)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_BASELINE = '{"ritual": "close", "allowed_current_states": ["DONE", "FAILED", "ABORTED"]}\n'
_EDITED = (
    '{"ritual": "close", "state_model": {"layer": "conceptual"}, '
    '"allowed_current_states": ["DONE", "FAILED", "ABORTED"]}\n'
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _make_pack_repo(tmp_path: Path):
    """Throwaway git repo with a committed baseline close pack."""
    repo = tmp_path
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    pack = repo / ".ai" / "rituals" / "close"
    pack.mkdir(parents=True)
    (pack / "ritual.contract.json").write_text(_BASELINE, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "baseline")
    return repo, pack


# ─────────── DANGER: uncommitted edit gets reverted ───────────


def test_uncommitted_contract_edit_is_reverted(tmp_path: Path) -> None:
    repo, pack = _make_pack_repo(tmp_path)
    cf = pack / "ritual.contract.json"
    cf.write_text(_EDITED, encoding="utf-8")  # NOT committed
    restored = _self_heal_pack_files(pack)
    assert "ritual.contract.json" in restored, "self-heal should revert uncommitted edit"
    assert "state_model" not in cf.read_text(encoding="utf-8"), "edit not reverted"


# ─────────── SAFE: committed edit survives ───────────


def test_committed_contract_edit_survives(tmp_path: Path) -> None:
    repo, pack = _make_pack_repo(tmp_path)
    cf = pack / "ritual.contract.json"
    cf.write_text(_EDITED, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "label conceptual")  # committed
    restored = _self_heal_pack_files(pack)
    assert restored == [], "self-heal must not touch a committed edit"
    assert "state_model" in cf.read_text(encoding="utf-8"), "committed edit lost"


# ─────────── E2E: the REAL committed state_model is self-heal-safe ───────────


def test_real_committed_conceptual_label_survives_self_heal() -> None:
    """The actual S2 commit (conceptual label in `purpose`) must survive a real
    self-heal. (The label lives in purpose, not a new field, because the
    contract schema is additionalProperties:false.)"""
    pack = _PROJECT_ROOT / ".ai" / "rituals" / "close"
    cf = pack / "ritual.contract.json"
    assert "conceptual" in cf.read_text(encoding="utf-8").lower(), (
        "precondition: conceptual label must be committed (S2) before this runs"
    )
    restored = _self_heal_pack_files(pack)
    assert "ritual.contract.json" not in restored, (
        "self-heal reverted the committed contract — commit did not take"
    )
    assert "conceptual" in cf.read_text(encoding="utf-8").lower()
