"""Frozen manifest of pack contents.

Records every file shipped under pack/ with its sha256 so re-snapshot drift
is detectable. The manifest is built lazily by walking pack/ at module import
time so tests stay self-validating: if a file is added to pack/ but the
manifest helper still reports a clean state, the test still passes because
the walk picks it up; if a snapshot file is mutated post-commit, sha256 will
shift on next walk and the diff against committed sha256s (if any) will flag.

For v1 we keep it simple: walk pack/, return list of (relpath, sha256).
A future v2 may snapshot expected sha256s to a JSON file and diff.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


PACK_VERSION = "trinity-bootstrap-pack-v1"


@dataclass(frozen=True)
class ManifestEntry:
    relpath: str
    sha256: str
    size: int


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(pack_root: Path) -> list[ManifestEntry]:
    pack_root = pack_root.resolve()
    if not pack_root.is_dir():
        raise FileNotFoundError(f"pack root not found: {pack_root}")

    entries: list[ManifestEntry] = []
    for p in sorted(pack_root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(pack_root).as_posix()
            entries.append(
                ManifestEntry(
                    relpath=rel,
                    sha256=_sha256_of(p),
                    size=p.stat().st_size,
                )
            )
    return entries


def manifest_to_dict(entries: list[ManifestEntry]) -> dict:
    return {
        "pack_version": PACK_VERSION,
        "file_count": len(entries),
        "files": [
            {"relpath": e.relpath, "sha256": e.sha256, "size": e.size}
            for e in entries
        ],
    }
