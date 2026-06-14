"""Thin-client kernel-source fallback for ritual pack loading (retro-0062).

Callers pass `rituals_root=project_root/.ai/rituals`. A thin-linked client
strips that dir, so `load_pack` raised PackNotFoundError, the caller swallowed
it, and the session ran WITHOUT appending to the hash-chained audit log — a
silent integrity hole. The fix falls back to the kernel's own packs. Same
pattern as retro-0055 (doctor) and retro-0061 (templates).
"""
import shutil
from pathlib import Path

import pytest

from cli.core import ritual_pack_loader
from cli.core.ritual_pack_loader import load_pack, PackNotFoundError

KERNEL_RITUALS = Path(ritual_pack_loader.__file__).resolve().parents[2] / "rituals"


def test_load_pack_falls_back_to_kernel_when_project_local_missing(tmp_path):
    # Simulate a thin client: a rituals_root that does not contain the pack.
    thin_rituals = tmp_path / "thin" / ".ai" / "rituals"
    thin_rituals.mkdir(parents=True)
    assert not (thin_rituals / "sss").exists()

    pack = load_pack("sss", rituals_root=thin_rituals)

    assert pack.ritual == "sss"
    assert pack.root == KERNEL_RITUALS / "sss"
    assert pack.root.is_dir()


def test_load_pack_prefers_project_local_when_present(tmp_path):
    # A fat project with its own valid pack keeps using it (no fallback).
    local_rituals = tmp_path / ".ai" / "rituals"
    local_rituals.mkdir(parents=True)
    shutil.copytree(KERNEL_RITUALS / "sss", local_rituals / "sss")

    pack = load_pack("sss", rituals_root=local_rituals)

    assert pack.root == local_rituals / "sss"


def test_load_pack_still_raises_when_both_missing(tmp_path):
    # No project-local pack AND no kernel pack for this name -> fail loud.
    thin_rituals = tmp_path / ".ai" / "rituals"
    thin_rituals.mkdir(parents=True)
    with pytest.raises(PackNotFoundError):
        load_pack("definitely-not-a-real-ritual", rituals_root=thin_rituals)


def test_kernel_ships_the_core_ritual_packs():
    # Guards the fallback target.
    for ritual in ("sss", "vvv", "nnn", "gogogo", "rrr"):
        assert (KERNEL_RITUALS / ritual).is_dir()
