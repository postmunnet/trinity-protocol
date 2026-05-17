"""Regression tests for `close.py` Claude Code transcript snapshot.

Landed 2026-05-14 as a dogfood amendment to the audit-cli fix session:
the operator pointed out that capture only saw kernel ritual I/O, not
the bidirectional conversation transcript. ``_snapshot_claude_transcript``
in ``close.py`` closes that gap by snapshotting the latest JSONL from
``~/.claude/projects/<slug>*`` into the close ritual's CAPTURE.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import hashlib as _hashlib
import json as _json
from cli.commands.close import (
    _codex_jsonl_cwd_matches_project,
    _jsonl_cwd_matches_project,
    _slugify_project_root,
    _snapshot_claude_transcript,
    _snapshot_codex_transcript,
    _snapshot_conversation_transcripts,
    _snapshot_gemini_transcript,
)


def _write_jsonl(path: Path, cwd: str, n_lines: int = 1):
    """Write a tiny JSONL transcript whose first record carries a cwd field
    (mirrors Claude Code's actual record shape — see record samples in
    ~/.claude/projects/*/<uuid>.jsonl)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for i in range(n_lines):
        lines.append(_json.dumps({
            "type": "user",
            "uuid": f"u-{i}",
            "cwd": cwd,
            "timestamp": f"2026-05-14T07:00:0{i}Z",
            "message": {"role": "user", "content": "hi"},
        }))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# slug encoding: must match Claude Code's empirical scheme
# ---------------------------------------------------------------------------


def test_slugify_collapses_slash_and_underscore_to_dash():
    """Claude Code stores transcripts under a slug computed as
    'collapse non-alphanumeric runs to a single dash'."""
    got = _slugify_project_root(Path("/home/user/projects/example/trinity_v2"))
    assert got == "-home-user-projects-example-trinity-v2"


def test_slugify_handles_relative_path():
    got = _slugify_project_root(Path("foo/bar_baz"))
    assert got == "foo-bar-baz"


# ---------------------------------------------------------------------------
# _snapshot_claude_transcript end-to-end behavior
# ---------------------------------------------------------------------------


def _fake_cap():
    """Build a minimal stub of the recordproxy capture object that records
    runtime() calls so tests can assert on the captured payload."""
    cap = MagicMock()
    cap.runtime_calls = []  # type: ignore[attr-defined]

    def _record(name, content):
        cap.runtime_calls.append((name, content))

    cap.runtime.side_effect = _record
    return cap


def test_snapshot_picks_latest_jsonl_when_multiple_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """When several JSONLs exist under <slug>/, the most recently modified
    one is snapshotted — that's the in-flight conversation."""
    project_root = tmp_path / "Users" / "yai" / "Downloads" / "myproj"
    project_root.mkdir(parents=True)

    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    slug = _slugify_project_root(project_root)
    claude_dir = home / ".claude" / "projects" / slug

    older = claude_dir / "uuid-old.jsonl"
    newer = claude_dir / "uuid-new.jsonl"
    _write_jsonl(older, cwd=str(project_root.resolve()))
    _write_jsonl(newer, cwd=str(project_root.resolve()))
    import os, time
    os.utime(older, (time.time() - 100, time.time() - 100))
    os.utime(newer, (time.time(), time.time()))

    config = SimpleNamespace(project_root=project_root)
    cap = _fake_cap()

    _snapshot_claude_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    assert len(cap.runtime_calls) == 1, "expected exactly one runtime() call"
    name, content = cap.runtime_calls[0]
    assert name == "claude_code_transcript.jsonl"
    assert content == newer.read_bytes(), "should snapshot the newer JSONL"


def test_snapshot_searches_sibling_dirs_with_slug_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """If Claude Code was invoked from a subdir cwd (e.g. ``cd .ai && claude``),
    a sibling project dir is created with the slug separator (e.g. ``-ai``).
    The snapshot must consider these — but ONLY when the JSONL's recorded
    cwd verifies against project_root (cwd-verify ground truth)."""
    project_root = tmp_path / "proj_x"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    slug = _slugify_project_root(project_root)
    primary = home / ".claude" / "projects" / slug
    # Subdir cwd: project_root/.ai → slug becomes <slug>--ai (double-dash
    # because '/' and '.' both collapse separately in some configurations,
    # but the encoder we use does a single collapse — still '-' separator).
    sibling_dir_name = slug + "--ai"
    sibling = home / ".claude" / "projects" / sibling_dir_name

    # Subdir cwd that lives under project_root (true sibling)
    subdir_cwd = str((project_root / ".ai").resolve())
    _write_jsonl(primary / "primary.jsonl", cwd=str(project_root.resolve()))
    _write_jsonl(sibling / "sibling.jsonl", cwd=subdir_cwd)

    import os, time
    os.utime(primary / "primary.jsonl", (time.time() - 60, time.time() - 60))
    os.utime(sibling / "sibling.jsonl", (time.time(), time.time()))

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)

    _snapshot_claude_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    assert len(cap.runtime_calls) == 1
    name, content = cap.runtime_calls[0]
    # Newer (sibling) wins; cwd-verify accepts it because subdir_cwd starts
    # with project_root.
    assert content == (sibling / "sibling.jsonl").read_bytes(), (
        "sibling dir's newer JSONL should win across slug-separator candidates"
    )


def test_snapshot_silent_noop_when_claude_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Codex/Gemini/Warp sessions don't create ~/.claude/projects/ for
    this project. Snapshot must silently no-op, NOT raise."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    # NB: no .claude/ tree at all under home/

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)

    # Must not raise.
    _snapshot_claude_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    assert cap.runtime_calls == []


def test_snapshot_silent_noop_when_slug_dir_has_no_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Edge case: the slug dir exists but contains no JSONL files."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    slug = _slugify_project_root(project_root)
    (home / ".claude" / "projects" / slug).mkdir(parents=True)

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_claude_transcript(session_path=tmp_path / "sess", config=config, cap=cap)
    assert cap.runtime_calls == []


# ---------------------------------------------------------------------------
# Defense against slug-collision (the bug the operator caught at 07:25 UTC)
# ---------------------------------------------------------------------------


def test_snapshot_rejects_sibling_project_with_prefix_colliding_slug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Slug encoding is lossy: '_' and '/' both collapse to '-'. So a
    sibling project ``<user-home>/trinity_v2_backup`` and our project
    ``<user-home>/trinity_v2`` both encode to slugs that share a prefix
    (``-Users-alice-trinity-v2`` vs ``-Users-alice-trinity-v2-backup``).
    A naive ``glob(slug + '*')`` would treat the sibling-project dir as
    a candidate and snapshot its transcript by mistake.

    The fix: separator-aware slug match (accept canonical OR
    ``slug + '-'`` prefix) PLUS cwd-verify. This test simulates the
    collision and asserts the unrelated project is NOT captured."""
    project_root = tmp_path / "trinity_v2"
    other_project = tmp_path / "trinity_v2_backup"
    project_root.mkdir()
    other_project.mkdir()

    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    our_slug = _slugify_project_root(project_root)
    other_slug = _slugify_project_root(other_project)
    # Sanity: the slugs DO share a prefix (this is the collision case
    # the test exists to defend against).
    assert other_slug.startswith(our_slug), (
        "test premise broken — slugs must share a prefix to exercise collision"
    )

    our_dir = home / ".claude" / "projects" / our_slug
    other_dir = home / ".claude" / "projects" / other_slug

    _write_jsonl(our_dir / "ours.jsonl", cwd=str(project_root.resolve()))
    _write_jsonl(other_dir / "theirs.jsonl", cwd=str(other_project.resolve()))

    # Make the OTHER project's transcript newer (mtime); a buggy
    # implementation would snapshot it.
    import os, time
    os.utime(our_dir / "ours.jsonl", (time.time() - 60, time.time() - 60))
    os.utime(other_dir / "theirs.jsonl", (time.time(), time.time()))

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_claude_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    # MUST capture OUR transcript, never the unrelated project's.
    assert len(cap.runtime_calls) == 1
    _, content = cap.runtime_calls[0]
    assert content == (our_dir / "ours.jsonl").read_bytes(), (
        "captured unrelated project's transcript — slug-collision defense regressed"
    )


def test_jsonl_cwd_verify_accepts_exact_match(tmp_path: Path):
    """Ground truth check: cwd-verify accepts a JSONL whose ``cwd`` equals
    project_root exactly."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    jsonl = tmp_path / "t.jsonl"
    _write_jsonl(jsonl, cwd=str(project_root.resolve()))
    assert _jsonl_cwd_matches_project(jsonl, project_root) is True


def test_jsonl_cwd_verify_accepts_subdir_cwd(tmp_path: Path):
    """Subdir cwd (e.g. running ``cd .ai && claude``) is also a true sibling."""
    project_root = tmp_path / "proj"
    (project_root / ".ai").mkdir(parents=True)
    jsonl = tmp_path / "t.jsonl"
    _write_jsonl(jsonl, cwd=str((project_root / ".ai").resolve()))
    assert _jsonl_cwd_matches_project(jsonl, project_root) is True


def test_jsonl_cwd_verify_rejects_unrelated_cwd(tmp_path: Path):
    """A JSONL whose cwd points outside project_root MUST be rejected,
    regardless of which slug dir it lived in."""
    project_root = tmp_path / "trinity_v2"
    other_project = tmp_path / "trinity_v2_backup"
    project_root.mkdir()
    other_project.mkdir()
    jsonl = tmp_path / "t.jsonl"
    _write_jsonl(jsonl, cwd=str(other_project.resolve()))
    assert _jsonl_cwd_matches_project(jsonl, project_root) is False


def test_jsonl_cwd_verify_rejects_jsonl_without_cwd_field(tmp_path: Path):
    """If no record has a ``cwd`` field, we cannot verify ownership — reject."""
    jsonl = tmp_path / "t.jsonl"
    jsonl.write_text('{"role":"user","content":"no cwd here"}\n', encoding="utf-8")
    project_root = tmp_path / "proj"
    project_root.mkdir()
    assert _jsonl_cwd_matches_project(jsonl, project_root) is False


def test_jsonl_cwd_verify_tolerates_corrupt_lines(tmp_path: Path):
    """Corrupt / non-JSON lines do not crash the verifier; subsequent good
    lines may still verify the file."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    jsonl = tmp_path / "t.jsonl"
    good = _json.dumps({"cwd": str(project_root.resolve())})
    jsonl.write_text("not-json garbage\n" + good + "\n", encoding="utf-8")
    assert _jsonl_cwd_matches_project(jsonl, project_root) is True


# ---------------------------------------------------------------------------
# Codex CLI handler — session_meta.cwd ground truth
# ---------------------------------------------------------------------------


def _write_codex_rollout(path: Path, cwd: str, n_response_items: int = 2):
    """Write a Codex-shaped rollout JSONL: first line is session_meta
    (with cwd in payload), followed by N response_item records.

    Mirrors the on-disk shape observed in
    ~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [_json.dumps({
        "type": "session_meta",
        "timestamp": "2026-05-14T07:30:00Z",
        "payload": {
            "id": "test-uuid",
            "cwd": cwd,
            "originator": "codex-tui",
            "cli_version": "0.130.0",
        },
    })]
    for i in range(n_response_items):
        lines.append(_json.dumps({
            "type": "response_item",
            "timestamp": f"2026-05-14T07:30:0{i}Z",
            "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": f"msg {i}"}]},
        }))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_codex_cwd_verify_accepts_matching_session_meta(tmp_path: Path):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    rollout = tmp_path / "rollout.jsonl"
    _write_codex_rollout(rollout, cwd=str(project_root.resolve()))
    assert _codex_jsonl_cwd_matches_project(rollout, project_root) is True


def test_codex_cwd_verify_rejects_unrelated_cwd(tmp_path: Path):
    project_root = tmp_path / "proj"
    other = tmp_path / "other_proj"
    project_root.mkdir()
    other.mkdir()
    rollout = tmp_path / "rollout.jsonl"
    _write_codex_rollout(rollout, cwd=str(other.resolve()))
    assert _codex_jsonl_cwd_matches_project(rollout, project_root) is False


def test_codex_cwd_verify_accepts_subdir_cwd(tmp_path: Path):
    """User ran `cd <proj>/src && codex` — session_meta.cwd is the subdir;
    still belongs to project_root."""
    project_root = tmp_path / "proj"
    (project_root / "src").mkdir(parents=True)
    rollout = tmp_path / "rollout.jsonl"
    _write_codex_rollout(rollout, cwd=str((project_root / "src").resolve()))
    assert _codex_jsonl_cwd_matches_project(rollout, project_root) is True


def test_codex_cwd_verify_rejects_no_session_meta(tmp_path: Path):
    """Edge: file has no session_meta record in first 4 records."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        "\n".join([_json.dumps({"type": "response_item", "payload": {}})] * 5) + "\n",
        encoding="utf-8",
    )
    assert _codex_jsonl_cwd_matches_project(rollout, project_root) is False


def test_snapshot_codex_picks_latest_matching_rollout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Among many Codex rollouts, the snapshot grabs the most recently
    modified one whose session_meta.cwd matches project_root."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    codex_sessions = home / ".codex" / "sessions" / "2026" / "05" / "14"
    older = codex_sessions / "rollout-old.jsonl"
    newer = codex_sessions / "rollout-new.jsonl"
    unrelated = codex_sessions / "rollout-other.jsonl"
    _write_codex_rollout(older, cwd=str(project_root.resolve()))
    _write_codex_rollout(newer, cwd=str(project_root.resolve()))
    _write_codex_rollout(unrelated, cwd=str((tmp_path / "elsewhere").resolve()))
    # Make `unrelated` the absolute newest by mtime — handler must STILL
    # skip it (cwd doesn't match) and pick `newer` as project-owned latest.
    import os, time
    now = time.time()
    os.utime(older, (now - 200, now - 200))
    os.utime(newer, (now - 60, now - 60))
    os.utime(unrelated, (now, now))

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_codex_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    assert len(cap.runtime_calls) == 1
    name, content = cap.runtime_calls[0]
    assert name == "codex_cli_transcript.jsonl"
    assert content == newer.read_bytes(), (
        "expected the newer project-owned rollout; got something else"
    )


def test_snapshot_codex_silent_noop_when_no_codex_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)  # no .codex/ at all

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_codex_transcript(session_path=tmp_path / "sess", config=config, cap=cap)
    assert cap.runtime_calls == []


# ---------------------------------------------------------------------------
# Gemini CLI handler — deterministic sha256(project_root)
# ---------------------------------------------------------------------------


def test_snapshot_gemini_uses_sha256_projecthash_for_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Gemini's projectHash is a cryptographic hash of the absolute project
    path — no slug collision possible. Verify the handler walks to the
    correct hash-named dir."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    project_hash = _hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()
    chats_dir = home / ".gemini" / "tmp" / project_hash / "chats"
    chats_dir.mkdir(parents=True)
    chat_file = chats_dir / "session-2026-05-14T07-30-test.json"
    chat_file.write_text(
        _json.dumps({
            "sessionId": "test",
            "projectHash": project_hash,
            "messages": [{"id": "1", "type": "user", "content": "hi"}],
        }),
        encoding="utf-8",
    )

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_gemini_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    assert len(cap.runtime_calls) == 1
    name, content = cap.runtime_calls[0]
    assert name == "gemini_cli_transcript.json"
    assert content == chat_file.read_bytes()


def test_snapshot_gemini_picks_latest_when_multiple_chats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    project_hash = _hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()
    chats_dir = home / ".gemini" / "tmp" / project_hash / "chats"
    chats_dir.mkdir(parents=True)
    older = chats_dir / "session-old.json"
    newer = chats_dir / "session-new.json"
    older.write_text('{"sessionId":"o"}', encoding="utf-8")
    newer.write_text('{"sessionId":"n"}', encoding="utf-8")
    import os, time
    os.utime(older, (time.time() - 60, time.time() - 60))
    os.utime(newer, (time.time(), time.time()))

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_gemini_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    assert len(cap.runtime_calls) == 1
    _, content = cap.runtime_calls[0]
    assert content == newer.read_bytes()


def test_snapshot_gemini_silent_noop_when_no_chats_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_gemini_transcript(session_path=tmp_path / "sess", config=config, cap=cap)
    assert cap.runtime_calls == []


def test_snapshot_gemini_does_not_match_different_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Different project_root → different sha256 → different chats dir.
    Snapshot for project A must not see chats of project B."""
    project_a = tmp_path / "proj_a"
    project_b = tmp_path / "proj_b"
    project_a.mkdir()
    project_b.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    hash_b = _hashlib.sha256(str(project_b.resolve()).encode()).hexdigest()
    b_chats = home / ".gemini" / "tmp" / hash_b / "chats"
    b_chats.mkdir(parents=True)
    (b_chats / "session.json").write_text('{"sessionId":"b"}', encoding="utf-8")

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_a)  # snapshot project A
    _snapshot_gemini_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    # Project A has no chats; B's chats must NOT leak.
    assert cap.runtime_calls == []


# ---------------------------------------------------------------------------
# Umbrella: dispatch all + tolerate per-handler failure
# ---------------------------------------------------------------------------


def test_umbrella_calls_all_three_handlers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Set up all three vendor dirs; umbrella should snapshot from each."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    # Claude
    slug = _slugify_project_root(project_root)
    claude_dir = home / ".claude" / "projects" / slug
    _write_jsonl(claude_dir / "claude.jsonl", cwd=str(project_root.resolve()))

    # Codex
    codex_dir = home / ".codex" / "sessions" / "2026" / "05" / "14"
    _write_codex_rollout(codex_dir / "rollout-x.jsonl", cwd=str(project_root.resolve()))

    # Gemini
    project_hash = _hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()
    gemini_dir = home / ".gemini" / "tmp" / project_hash / "chats"
    gemini_dir.mkdir(parents=True)
    (gemini_dir / "session-test.json").write_text('{"sessionId":"g"}', encoding="utf-8")

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_conversation_transcripts(session_path=tmp_path / "sess", config=config, cap=cap)

    # 3 runtime() calls — one per vendor
    assert len(cap.runtime_calls) == 3
    names = [c[0] for c in cap.runtime_calls]
    assert "claude_code_transcript.jsonl" in names
    assert "codex_cli_transcript.jsonl" in names
    assert "gemini_cli_transcript.json" in names


def test_umbrella_tolerates_individual_handler_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """If one handler raises, the umbrella logs and continues with the rest.
    Close must NOT fail because of transcript capture."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    # Only Gemini wired correctly
    project_hash = _hashlib.sha256(str(project_root.resolve()).encode()).hexdigest()
    gemini_dir = home / ".gemini" / "tmp" / project_hash / "chats"
    gemini_dir.mkdir(parents=True)
    (gemini_dir / "session-test.json").write_text('{"x":1}', encoding="utf-8")

    # Force the claude handler to blow up by monkeypatching it
    import cli.commands.close as close_mod
    def _boom(*a, **kw): raise RuntimeError("forced failure")
    monkeypatch.setattr(close_mod, "_snapshot_claude_transcript", _boom)

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    # MUST NOT raise
    _snapshot_conversation_transcripts(session_path=tmp_path / "sess", config=config, cap=cap)

    # Gemini still captured despite Claude blowing up
    assert len(cap.runtime_calls) == 1
    assert cap.runtime_calls[0][0] == "gemini_cli_transcript.json"


def test_umbrella_silent_when_no_vendor_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Clean machine with none of the vendor harnesses → umbrella is fully
    silent, zero runtime() calls, zero exceptions."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_conversation_transcripts(session_path=tmp_path / "sess", config=config, cap=cap)
    assert cap.runtime_calls == []


def test_snapshot_records_runtime_kind_not_input_or_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """The transcript documents HOW the session unfolded; it is neither
    a kernel input nor output. It MUST be recorded under kind='runtime'
    so it doesn't pollute the ritual I/O contract."""
    project_root = tmp_path / "proj"
    project_root.mkdir()
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)
    slug = _slugify_project_root(project_root)
    cd = home / ".claude" / "projects" / slug
    _write_jsonl(cd / "u.jsonl", cwd=str(project_root.resolve()))

    cap = _fake_cap()
    config = SimpleNamespace(project_root=project_root)
    _snapshot_claude_transcript(session_path=tmp_path / "sess", config=config, cap=cap)

    # cap.runtime was called; cap.input and cap.output were NOT
    cap.runtime.assert_called_once()
    cap.input.assert_not_called()
    cap.output.assert_not_called()
