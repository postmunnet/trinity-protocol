"""retro-0072 — malformed THINK/03_ACCEPTANCE.yaml must fail clean, not
traceback (which `close --force` could then bury without evidence)."""
from __future__ import annotations

from pathlib import Path

import pytest

from cli.core.acceptance import AcceptanceYamlError, load_acceptance


def test_malformed_yaml_raises_structured_error(tmp_path: Path) -> None:
    p = tmp_path / "03_ACCEPTANCE.yaml"
    # The exact retro-0072 trigger: backtick escape in a double-quoted scalar
    p.write_text(
        'acceptance:\n'
        '- id: A1\n'
        '  required: true\n'
        '  command: "grep -q \'\\`sss\\`\' file.md"\n'
        '  expect_exit: 0\n'
    )
    with pytest.raises(AcceptanceYamlError) as exc_info:
        load_acceptance(p)
    msg = str(exc_info.value)
    assert "acceptance yaml invalid" in msg
    assert "single-quoted" in msg  # actionable tip present


def test_valid_yaml_still_loads(tmp_path: Path) -> None:
    p = tmp_path / "03_ACCEPTANCE.yaml"
    p.write_text(
        "acceptance:\n"
        "- id: A1\n"
        "  required: true\n"
        "  command: 'grep -q \"### \\`sss\\`\" file.md'\n"
        "  expect_exit: 0\n"
    )
    items = load_acceptance(p)
    assert len(items) == 1
    assert items[0].id == "A1"
