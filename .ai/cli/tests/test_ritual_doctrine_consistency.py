"""Lock-step consistency test — RITUALS.md ↔ graph ↔ kernel commands.

The bug this prevents:
  Between 2026-05-25 21:08 and 23:30, someone refactored
  core/trinity_v2/.ai/graphs/standard.yaml to fire `nnn_pass` from THINK
  (a "plan first" order). RITUALS.md was NOT updated, so the canonical
  doctrine kept saying `sss → vvv → nnn → gogogo` while graph + nnn.py +
  CLAUDE.md said the opposite. The monorepo root graph was also not synced.
  Result: `ai nnn` crashed with `TransitionNotFound` for every new session
  because the graph it actually loaded (monorepo root) disagreed with the
  graph nnn.py assumed.

This test asserts the invariants RITUALS.md guarantees:

  1. RITUALS.md sequence is exactly sss → vvv → nnn → gogogo → ddd → rrr → close.
  2. THINK→SANDBOX is triggered by vvv_pass (verifier-decided).
  3. SANDBOX→DO is triggered by nnn_pass (kernel-decided).
  4. The kernel CLAUDE.md "Sequence (do not skip)" line matches RITUALS.md.
  5. Kernel CLAUDE.md does NOT claim "planning passes first" or "nnn first".

If any of these drift again, this test fails loud.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


def _repo_root() -> Path:
    """core/trinity_v2 root regardless of pytest cwd."""
    return Path(__file__).resolve().parents[3]


def _load_graph() -> dict:
    graph_path = _repo_root() / ".ai" / "graphs" / "standard.yaml"
    return yaml.safe_load(graph_path.read_text(encoding="utf-8"))


def _load_rituals_md() -> str:
    return (_repo_root() / "docs" / "RITUALS.md").read_text(encoding="utf-8")


def _load_kernel_claude_md() -> str:
    return (_repo_root() / "CLAUDE.md").read_text(encoding="utf-8")


def test_rituals_md_canonical_sequence_unchanged():
    """RITUALS.md must declare the canonical sequence verbatim."""
    rituals = _load_rituals_md()
    # Match in a code fence (text block); allow whitespace flexibility.
    pattern = r"sss\s*->\s*vvv\s*->\s*nnn\s*->\s*gogogo\s*->\s*ddd\s*->\s*rrr\s*->\s*close"
    assert re.search(pattern, rituals), (
        "RITUALS.md canonical sequence must read "
        "'sss -> vvv -> nnn -> gogogo -> ddd -> rrr -> close'. "
        "If you intentionally changed canonical doctrine, also amend this test "
        "and bump RITUALS.md's version header."
    )


def test_graph_think_to_sandbox_is_vvv_pass_verifier():
    """THINK→SANDBOX must be triggered by vvv_pass (verifier-decided)."""
    graph = _load_graph()
    matches = [
        t for t in graph["transitions"]
        if t["from"] == "THINK" and t["to"] == "SANDBOX"
    ]
    assert len(matches) == 1, (
        f"Expected exactly one THINK→SANDBOX transition; got {len(matches)}"
    )
    t = matches[0]
    assert t["trigger"] == "vvv_pass", (
        f"THINK→SANDBOX trigger must be 'vvv_pass'; got {t['trigger']!r}. "
        "Per RITUALS.md, vvv answers the 5 questions and transitions out of "
        "THINK; nnn does not fire this transition."
    )
    assert t["decided_by"] == "verifier", (
        f"THINK→SANDBOX decided_by must be 'verifier'; got {t['decided_by']!r}."
    )


def test_graph_sandbox_to_do_is_nnn_pass_kernel():
    """SANDBOX→DO must be triggered by nnn_pass (kernel-decided)."""
    graph = _load_graph()
    matches = [
        t for t in graph["transitions"]
        if t["from"] == "SANDBOX" and t["to"] == "DO"
    ]
    assert len(matches) == 1, (
        f"Expected exactly one SANDBOX→DO transition; got {len(matches)}"
    )
    t = matches[0]
    assert t["trigger"] == "nnn_pass", (
        f"SANDBOX→DO trigger must be 'nnn_pass'; got {t['trigger']!r}. "
        "Per RITUALS.md, nnn locks the plan and transitions out of SANDBOX."
    )
    assert t["decided_by"] == "kernel", (
        f"SANDBOX→DO decided_by must be 'kernel'; got {t['decided_by']!r}."
    )


def test_kernel_claude_md_sequence_matches_rituals():
    """Kernel CLAUDE.md 'Sequence (do not skip)' must match RITUALS.md."""
    claude = _load_kernel_claude_md()
    pattern = r"sss\s*->\s*vvv\s*->\s*nnn\s*->\s*gogogo\s*->\s*ddd\s*->\s*rrr"
    assert re.search(pattern, claude), (
        "Kernel CLAUDE.md must include the canonical sequence "
        "'sss -> vvv -> nnn -> gogogo -> ddd -> rrr'. "
        "If you reordered rituals, also update RITUALS.md and bump its version."
    )


def test_kernel_claude_md_does_not_claim_nnn_first():
    """Kernel CLAUDE.md must NOT claim plan-first / nnn-first order."""
    claude = _load_kernel_claude_md()
    forbidden_phrases = [
        "planning passes first",
        "nnn_pass.*first",
        "nnn.*before.*vvv",
        # 2026-06-14: the SHORT_CODES "When" column drifted to vvv-after-nnn
        # ("vvv | … | After nnn pass (post-plan confirm)") contradicting the
        # Sequence line + ratified vvv-first doctrine (retro-0011). Lock it.
        "after nnn pass",
        "post-plan confirm",
    ]
    for phrase in forbidden_phrases:
        assert not re.search(phrase, claude, re.IGNORECASE), (
            f"Kernel CLAUDE.md contains forbidden phrase matching "
            f"{phrase!r}. The bug log from 2026-05-28 documents how this "
            f"phrasing introduced graph/code drift. Use RITUALS.md wording."
        )
