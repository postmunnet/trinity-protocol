"""Phase 0.5 — plan_envelope.allowed_paths carve-outs for forbidden_diff.

Regression coverage:
  - allowed_paths=None → identical to pre-Phase-0.5 behaviour
  - allowed_paths matching a forbidden hit → carve-out (not violation)
  - allowed_paths NOT matching a forbidden hit → still a violation
  - glob translation (** → fnmatch *)
  - malformed allowed_paths → safe close-fail (no carve-out granted)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from cli.core.forbidden_diff import (
    FORBIDDEN_PATTERNS,
    ForbiddenDiffReport,
    _matches_allowed,
    _normalise_allowed,
    check,
    record_baseline_untracked,
)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A tmp git repo with an initial commit so `git diff HEAD` works."""
    subprocess.check_call(["git", "init", "-q"], cwd=tmp_path)
    subprocess.check_call(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path
    )
    subprocess.check_call(
        ["git", "config", "user.name", "test"], cwd=tmp_path
    )
    (tmp_path / "README.md").write_text("seed\n")
    subprocess.check_call(["git", "add", "."], cwd=tmp_path)
    subprocess.check_call(
        ["git", "commit", "-q", "-m", "seed"], cwd=tmp_path
    )
    return tmp_path


def _stage_forbidden(repo: Path, relpath: str, body: str = "x\n") -> None:
    target = repo / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body)


# ─────────── normalisation + glob match unit tests ───────────


def test_normalise_allowed_returns_empty_for_none_and_empty():
    assert _normalise_allowed(None) == []
    assert _normalise_allowed([]) == []


def test_normalise_allowed_filters_non_strings_safely():
    assert _normalise_allowed(["docs/specs/X.md", 7, None, ""]) == [
        "docs/specs/X.md"
    ]


def test_normalise_allowed_strips_leading_dot_slash():
    assert _normalise_allowed(["./docs/specs/X.md"]) == ["docs/specs/X.md"]


def test_matches_allowed_handles_double_star_glob():
    assert _matches_allowed(
        "docs/specs/TRINITY_FOO.md", ["docs/specs/TRINITY_*.md"]
    )
    assert _matches_allowed("docs/specs/sub/x.md", ["docs/specs/**"])
    assert not _matches_allowed(
        "docs/migration/x.md", ["docs/specs/**"]
    )


# ─────────── end-to-end check() behaviour ───────────


def test_check_no_allowed_paths_is_identical_to_today(git_repo: Path):
    """Regression: when allowed_paths is None, behaviour matches pre-0.5."""
    _stage_forbidden(git_repo, "docs/specs/TRINITY_X.md")
    report = check(git_repo, baseline="HEAD")
    assert "docs/specs/TRINITY_X.md" in report.violations
    assert report.carve_outs == []
    assert not report.ok


def test_check_forbidden_path_in_allowed_becomes_carve_out(git_repo: Path):
    _stage_forbidden(git_repo, "docs/specs/TRINITY_X.md")
    report = check(
        git_repo,
        baseline="HEAD",
        allowed_paths=["docs/specs/TRINITY_*.md"],
    )
    assert "docs/specs/TRINITY_X.md" in report.carve_outs
    assert report.violations == []
    assert report.ok, "carve-outs must not break the gate"


def test_check_forbidden_path_outside_allowed_is_still_violation(
    git_repo: Path,
):
    _stage_forbidden(git_repo, "docs/specs/SOMETHING_ELSE.md")
    report = check(
        git_repo,
        baseline="HEAD",
        allowed_paths=["docs/specs/TRINITY_*.md"],
    )
    assert "docs/specs/SOMETHING_ELSE.md" in report.violations
    assert report.carve_outs == []
    assert not report.ok


def test_check_mixed_violations_and_carve_outs(git_repo: Path):
    _stage_forbidden(git_repo, "docs/specs/TRINITY_OK.md")
    _stage_forbidden(git_repo, "docs/specs/NOT_ALLOWED.md")
    _stage_forbidden(git_repo, ".ai/policies/something.yaml")
    report = check(
        git_repo,
        baseline="HEAD",
        allowed_paths=["docs/specs/TRINITY_*.md"],
    )
    assert "docs/specs/TRINITY_OK.md" in report.carve_outs
    assert "docs/specs/NOT_ALLOWED.md" in report.violations
    assert ".ai/policies/something.yaml" in report.violations
    assert not report.ok


def test_check_malformed_allowed_paths_is_close_fail(git_repo: Path):
    """Malformed input MUST NOT grant a carve-out. Closed-fail."""
    _stage_forbidden(git_repo, "docs/specs/TRINITY_X.md")
    # Non-list values should be ignored — equivalent to no carve-out.
    for bad in ["", 0, {"foo": "bar"}, [None, 7], "docs/specs/*"]:
        report = check(git_repo, baseline="HEAD", allowed_paths=bad)
        # The string "docs/specs/*" iterates char-by-char — none of those
        # chars match "docs/specs/TRINITY_X.md", so it must still violate.
        assert "docs/specs/TRINITY_X.md" in report.violations, (
            f"malformed allowed_paths={bad!r} must not grant carve-out"
        )


def test_check_audit_events_ndjson_still_skipped(git_repo: Path):
    """The events.ndjson exception is preserved across the refactor."""
    _stage_forbidden(git_repo, ".ai/audit/events.ndjson", "{}\n")
    report = check(git_repo, baseline="HEAD")
    assert ".ai/audit/events.ndjson" not in report.violations
    assert report.skipped_audit_chain is True


# ─────────── docs/constitution/ protection (Addendum v1.0.2) ───────────


def test_check_docs_constitution_is_forbidden_without_allowlist(
    git_repo: Path,
):
    """docs/constitution/** is protected at the same authority as docs/specs/**.

    Added 2026-05-13 by Constitution Addendum v1.0.2 — relocation of the
    six canonical constitutional documents from docs/specs/ to
    docs/constitution/ must not downgrade D1 protection.
    """
    _stage_forbidden(
        git_repo, "docs/constitution/TRINITY_CONSTITUTION_V1.md"
    )
    report = check(git_repo, baseline="HEAD")
    assert (
        "docs/constitution/TRINITY_CONSTITUTION_V1.md"
        in report.violations
    )
    assert report.carve_outs == []
    assert not report.ok


def test_check_docs_constitution_carve_out_via_allowlist(git_repo: Path):
    """A plan envelope may carve out docs/constitution/** explicitly."""
    _stage_forbidden(
        git_repo, "docs/constitution/TRINITY_RITUAL_CONTRACT_V1.md"
    )
    report = check(
        git_repo,
        baseline="HEAD",
        allowed_paths=["docs/constitution/**"],
    )
    assert (
        "docs/constitution/TRINITY_RITUAL_CONTRACT_V1.md"
        in report.carve_outs
    )
    assert report.violations == []
    assert report.ok


def test_carve_outs_field_is_audit_visible(git_repo: Path):
    """Article XXIII — carve-outs are recorded for audit, not silenced."""
    _stage_forbidden(git_repo, "docs/specs/TRINITY_X.md")
    report = check(
        git_repo,
        baseline="HEAD",
        allowed_paths=["docs/specs/**"],
    )
    # carve_outs is on the report dataclass — visible to audit collectors
    assert isinstance(report, ForbiddenDiffReport)
    assert len(report.carve_outs) == 1
    assert report.ok  # but it doesn't fail the gate


# ─────────── .ai/-prefixed carve-out regression (lstrip leading-dot bug) ───────────


def test_normalise_preserves_leading_dot_for_ai_paths():
    """Regression: `.ai/schemas/foo.json` MUST normalise to itself, not
    `ai/schemas/foo.json`. The old `lstrip("./")` ate the leading dot
    because lstrip treats `./` as a char-set, silently breaking carve-outs
    for every `.ai/...` path. Fix: removeprefix("./") strips only the
    literal "./" prefix.
    """
    out = _normalise_allowed([
        ".ai/schemas/ritual_contract.schema.json",
        ".ai/rituals/**",
        ".ai/policies/foo.yaml",
    ])
    assert out == [
        ".ai/schemas/ritual_contract.schema.json",
        ".ai/rituals/**",
        ".ai/policies/foo.yaml",
    ], (
        f"_normalise_allowed must preserve leading dot for .ai/ paths; got {out}"
    )


def test_normalise_still_strips_literal_dot_slash_prefix():
    """The original intent of lstrip("./") was to remove a literal `./` prefix
    (e.g. `./docs/specs/**` → `docs/specs/**`). The fix MUST preserve that
    behaviour while no longer eating a bare leading `.`."""
    out = _normalise_allowed(["./docs/specs/**", "./.ai/policies/x.yaml"])
    assert out == ["docs/specs/**", ".ai/policies/x.yaml"], (
        f"removeprefix('./') must strip literal './' prefix only; got {out}"
    )


def test_check_ai_schemas_carve_out_now_works(git_repo: Path):
    """End-to-end: a .ai/schemas/ file declared in allowed_paths is a
    carve-out, not a violation. Pre-fix, the lstrip bug caused every such
    declaration to be silently rejected. This is the exact scenario that
    bit the ritual-template-packs-bootstrap session."""
    _stage_forbidden(git_repo, ".ai/schemas/ritual_contract.schema.json")
    report = check(
        git_repo,
        baseline="HEAD",
        allowed_paths=[".ai/schemas/ritual_contract.schema.json"],
    )
    assert ".ai/schemas/ritual_contract.schema.json" in report.carve_outs, (
        f"expected .ai/schemas/ritual_contract.schema.json in carve_outs; got {report.carve_outs} / violations={report.violations}"
    )
    assert report.violations == []
    assert report.ok


def test_check_ai_rituals_glob_carve_out_works(git_repo: Path):
    """`.ai/rituals/**` glob must carve out anything under .ai/rituals/."""
    _stage_forbidden(git_repo, ".ai/schemas/ritual_check_template.schema.json")
    _stage_forbidden(git_repo, ".ai/schemas/ritual_context.schema.json")
    report = check(
        git_repo,
        baseline="HEAD",
        allowed_paths=[
            ".ai/schemas/ritual_check_template.schema.json",
            ".ai/schemas/ritual_context.schema.json",
        ],
    )
    assert set(report.carve_outs) == {
        ".ai/schemas/ritual_check_template.schema.json",
        ".ai/schemas/ritual_context.schema.json",
    }
    assert report.violations == []
    assert report.ok


def test_check_ai_policies_still_violates_without_allowlist(git_repo: Path):
    """Sanity guard: the leading-dot fix must NOT widen the gate. A
    .ai/policies/ file without an explicit allowlist MUST still violate."""
    _stage_forbidden(git_repo, ".ai/policies/safety.yaml")
    report = check(git_repo, baseline="HEAD", allowed_paths=None)
    assert ".ai/policies/safety.yaml" in report.violations
    assert not report.ok


# ─────────── baseline_untracked filter (cross-session fix, 2026-05-14) ───────────
# Closes feedback_rrr_cross_session_forbidden_diff. A parallel HOLD session's
# untracked deliverables in a forbidden prefix were surfacing as the current
# session's violations because the working-tree scan is path-scoped, not
# session-scoped. Approach A: at sss time we snapshot pre-existing untracked
# files; rrr then filters them out of the scan.


def test_forbidden_diff_filters_baseline_untracked(git_repo: Path):
    """Three-file regression scenario (A2):

      * pre_existing_forbidden:  ``docs/specs/PRE_A.md``       — should be ignored
      * pre_existing_neutral:    ``DOCS_NEUTRAL.md``           — should be ignored
      * new_forbidden_post_baseline: ``docs/specs/NEW_B.md``   — MUST be reported

    The baseline_untracked list is what `record_baseline_untracked` would have
    captured at sss time. The third file is created AFTER the snapshot to
    simulate THIS session's own deliverable.
    """
    _stage_forbidden(git_repo, "docs/specs/PRE_A.md")
    _stage_forbidden(git_repo, "DOCS_NEUTRAL.md")
    baseline_untracked = ["docs/specs/PRE_A.md", "DOCS_NEUTRAL.md"]

    _stage_forbidden(git_repo, "docs/specs/NEW_B.md")

    report = check(
        git_repo,
        baseline="HEAD",
        baseline_untracked=baseline_untracked,
    )
    assert "docs/specs/NEW_B.md" in report.violations
    assert "docs/specs/PRE_A.md" not in report.violations
    assert "DOCS_NEUTRAL.md" not in report.violations
    assert not report.ok  # the new file still fails the gate


def test_forbidden_diff_baseline_untracked_default_noop(git_repo: Path):
    """A3 — backward compatibility: invoking ``check()`` WITHOUT the new
    parameter, or with ``baseline_untracked=None``, must produce identical
    results. Sessions created before the sss snapshot landed must keep
    working unchanged."""
    _stage_forbidden(git_repo, "docs/specs/LEGACY.md")

    without_param = check(git_repo, baseline="HEAD")
    with_none = check(git_repo, baseline="HEAD", baseline_untracked=None)
    with_empty = check(git_repo, baseline="HEAD", baseline_untracked=[])

    assert set(without_param.violations) == set(with_none.violations) == set(with_empty.violations)
    assert "docs/specs/LEGACY.md" in without_param.violations


def test_record_baseline_untracked_writes_json_array(git_repo: Path, tmp_path: Path):
    """``record_baseline_untracked`` writes a JSON array to
    ``<session_state_dir>/baseline_untracked.json`` containing exactly the
    untracked-file list returned. Also creates the state dir on demand."""
    # Pre-existing untracked file BEFORE the snapshot is taken.
    _stage_forbidden(git_repo, "docs/specs/EXISTING.md")

    state_dir = tmp_path / "session-x" / ".state"
    assert not state_dir.exists()  # helper must mkdir on demand

    recorded = record_baseline_untracked(state_dir, git_repo)

    target = state_dir / "baseline_untracked.json"
    assert target.is_file()
    parsed = json.loads(target.read_text(encoding="utf-8"))
    assert isinstance(parsed, list)
    assert parsed == recorded
    assert "docs/specs/EXISTING.md" in parsed
