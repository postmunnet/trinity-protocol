"""Regression + new-feature tests for vvv `--answers-file` parsing.

Covers:
- JSON file parses (backwards-compatible)
- YAML file parses (new)
- Malformed input emits a typer.Exit(2) with a message that mentions both formats
- Non-mapping YAML root is rejected with a clear message
"""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from cli.commands.vvv import _load_answers_file, _parse_answers


def test_json_answers_backwards_compatible(tmp_path: Path) -> None:
    p = tmp_path / "answers.json"
    p.write_text('{"1": "goal", "2": "scope", "3": "x", "4": "y", "5": "z"}', encoding="utf-8")
    data = _load_answers_file(p)
    assert data == {"1": "goal", "2": "scope", "3": "x", "4": "y", "5": "z"}


def test_yaml_answers_parsed(tmp_path: Path) -> None:
    p = tmp_path / "answers.yaml"
    p.write_text(
        '"1": "goal text"\n'
        '"2": "scope text"\n'
        '"3": "constraints text"\n'
        '"4": "acceptance text"\n'
        '"5": "risk text"\n',
        encoding="utf-8",
    )
    data = _load_answers_file(p)
    assert data["1"] == "goal text"
    assert data["5"] == "risk text"


def test_yaml_block_scalar_parsed(tmp_path: Path) -> None:
    p = tmp_path / "answers.yaml"
    p.write_text(
        '"1": |\n'
        "  multi-line\n"
        "  goal\n"
        '"2": "scope"\n',
        encoding="utf-8",
    )
    data = _load_answers_file(p)
    assert "multi-line\ngoal" in data["1"]
    assert data["2"] == "scope"


def test_malformed_input_exits_with_helpful_message(tmp_path: Path, capsys) -> None:
    p = tmp_path / "junk.txt"
    # Mixed flow markers force both JSON and YAML parsers to fail (YAML is
    # otherwise extremely permissive about treating plain text as a scalar).
    p.write_text("{[: this } is ] broken: : :\n  - unbalanced", encoding="utf-8")
    with pytest.raises(typer.Exit) as exc_info:
        _load_answers_file(p)
    assert exc_info.value.exit_code == 2


def test_yaml_non_mapping_rejected(tmp_path: Path) -> None:
    p = tmp_path / "list.yaml"
    p.write_text("- a\n- b\n- c\n", encoding="utf-8")
    with pytest.raises(typer.Exit) as exc_info:
        _load_answers_file(p)
    assert exc_info.value.exit_code == 2


def test_parse_answers_merges_flags_and_file(tmp_path: Path) -> None:
    p = tmp_path / "answers.yaml"
    p.write_text('"1": "from yaml"\n"2": "from yaml"\n', encoding="utf-8")
    result = _parse_answers(answer_flags=["3=cli-override", "4=another"], answers_file=p)
    assert result[1] == "from yaml"
    assert result[2] == "from yaml"
    assert result[3] == "cli-override"
    assert result[4] == "another"


def test_parse_answers_flags_override_file(tmp_path: Path) -> None:
    p = tmp_path / "answers.json"
    p.write_text('{"1": "from json"}', encoding="utf-8")
    result = _parse_answers(answer_flags=["1=cli-wins"], answers_file=p)
    assert result[1] == "cli-wins"
