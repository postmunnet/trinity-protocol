"""Emit a structured install receipt to <target>/.trinity-install-receipt.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .pack_manifest import PACK_VERSION


RECEIPT_FILENAME = ".trinity-install-receipt.json"


@dataclass
class Receipt:
    pack_version: str
    mode: str
    target: str
    dry_run: bool
    timestamp_utc: str
    file_count: int
    files_installed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    kernel_wire: dict = field(default_factory=dict)


def build_receipt(
    *,
    mode: str,
    target: Path,
    dry_run: bool,
    files_installed: list[str],
    warnings: list[str] | None = None,
    kernel_wire: dict | None = None,
) -> Receipt:
    return Receipt(
        pack_version=PACK_VERSION,
        mode=mode,
        target=str(target.resolve()),
        dry_run=dry_run,
        timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        file_count=len(files_installed),
        files_installed=sorted(files_installed),
        warnings=list(warnings or []),
        kernel_wire=dict(kernel_wire or {}),
    )


def write_receipt(receipt: Receipt, target: Path) -> Path:
    path = target / RECEIPT_FILENAME
    target.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(asdict(receipt), fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path
