"""Detect install mode for a target directory.

Modes:
  greenfield  — empty or no Trinity markers
  upgrade-v1  — has ai-docs/ and CLAUDE.md but no .ai/cli/
  upgrade-v2  — has .ai/cli/ (existing trinity_v2-style kernel)
  self        — target IS the trinity_v2 source repo itself
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SELF_INSTALL_MARKER_RELATIVE = Path(".ai/cli/ai")
SELF_INSTALL_SSOT = Path(".ai/ssot.yaml")
V2_MARKER = Path(".ai/cli")
V1_MARKER_DIR = Path("ai-docs")
V1_MARKER_FILE = Path("CLAUDE.md")


@dataclass(frozen=True)
class DetectionResult:
    mode: str
    reasons: tuple[str, ...]

    def is_self(self) -> bool:
        return self.mode == "self"


def detect(target: Path, source_root: Path) -> DetectionResult:
    target = target.resolve()
    source_root = source_root.resolve()

    if target == source_root:
        return DetectionResult(
            mode="self",
            reasons=("target path equals trinity_v2 source root",),
        )

    if (target / SELF_INSTALL_MARKER_RELATIVE).exists() and (target / SELF_INSTALL_SSOT).exists():
        return DetectionResult(
            mode="self",
            reasons=(
                "target has both .ai/cli/ai and .ai/ssot.yaml — looks like trinity_v2 itself",
            ),
        )

    if (target / V2_MARKER).is_dir():
        return DetectionResult(
            mode="upgrade-v2",
            reasons=("target has existing .ai/cli/ directory",),
        )

    has_ai_docs = (target / V1_MARKER_DIR).is_dir()
    has_claude_md = (target / V1_MARKER_FILE).is_file()
    if has_ai_docs or has_claude_md:
        evidence = []
        if has_ai_docs:
            evidence.append("ai-docs/ present")
        if has_claude_md:
            evidence.append("CLAUDE.md present")
        return DetectionResult(
            mode="upgrade-v1",
            reasons=tuple(evidence),
        )

    return DetectionResult(
        mode="greenfield",
        reasons=("no Trinity markers found",),
    )
