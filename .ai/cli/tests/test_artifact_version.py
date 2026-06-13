"""Q24.10 step 2 — generic artifact_version storage layer tests.

artifact_version.py must stay semantics-free: it versions any named JSON
artifact with immutability, active-pointer, history and amendment records,
and knows nothing about plan/goal_contract meaning.
"""
from __future__ import annotations

import pytest

from cli.core import artifact_version as av


def test_write_and_resolve_latest(tmp_path):
    av.write_version(tmp_path, "goal_contract", {"k": 1}, 1)
    assert av.resolve_latest(tmp_path, "goal_contract") == {"k": 1}
    assert av.active_version(tmp_path, "goal_contract") == 1
    assert (tmp_path / ".state" / "goal_contract.v1.json").exists()
    assert (tmp_path / ".state" / "goal_contract.json").exists()  # snapshot


def test_versions_are_immutable(tmp_path):
    av.write_version(tmp_path, "goal_contract", {"k": 1}, 1)
    with pytest.raises(FileExistsError):
        av.write_version(tmp_path, "goal_contract", {"k": 2}, 1)


def test_latest_and_historical_readable(tmp_path):
    av.write_version(tmp_path, "goal_contract", {"v": 1}, 1)
    av.write_version(tmp_path, "goal_contract", {"v": 2}, 2)
    assert av.active_version(tmp_path, "goal_contract") == 2
    assert av.resolve_latest(tmp_path, "goal_contract") == {"v": 2}
    # historical still on disk + readable
    import json
    v1 = json.loads((tmp_path / ".state" / "goal_contract.v1.json").read_text())
    assert v1 == {"v": 1}
    assert av.list_versions(tmp_path, "goal_contract") == [1, 2]


def test_amendment_record(tmp_path):
    av.write_version(tmp_path, "goal_contract", {"v": 1}, 1)
    rfile, rec = av.write_amendment_record(
        tmp_path, "goal_contract", 1, 2, "because", ["confirm_q1"]
    )
    assert rfile.exists()
    assert rec["artifact"] == "goal_contract"
    assert rec["from_version"] == 1 and rec["to_version"] == 2
    assert rec["reason"] == "because" and rec["changes"] == ["confirm_q1"]
    assert av.list_amendment_records(tmp_path, "goal_contract")[0]["seq"] == 1


def test_name_isolation(tmp_path):
    # two different artifact names do not collide
    av.write_version(tmp_path, "goal_contract", {"a": 1}, 1)
    av.write_version(tmp_path, "plan", {"b": 1}, 1)
    assert av.resolve_latest(tmp_path, "goal_contract") == {"a": 1}
    assert av.resolve_latest(tmp_path, "plan") == {"b": 1}
    assert av.list_versions(tmp_path, "goal_contract") == [1]
    assert av.list_versions(tmp_path, "plan") == [1]


def test_resolve_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        av.resolve_latest(tmp_path, "nonexistent")
