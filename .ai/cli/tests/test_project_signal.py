from __future__ import annotations

from pathlib import Path

from cli.core.project_signal import collect_project_signal


def test_project_signal_extracts_sourced_retro_sections(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    retro = proj / ".claude" / "retrospectives" / "2026-05" / "0006_coupon.md"
    retro.parent.mkdir(parents=True)
    retro.write_text(
        """# Retro

### 20. Next Session Prep / §29

- Coupon series 100% DEV-complete
- **PROD bundle = 15 features** — MUST write deploy plan next session
- Real-data smoke: still no real coupon-applied order in member 53 history

### 21. Pending Items / §30

- [ ] PROD bundle deploy plan write (15 features stacking)
- [ ] Real-data E2E: place real order with coupon

### 22. Regression Watch / §31

- order_model.php now calls coupon revert at 3 RC transitions.
- Helper is private — shopping_model would need its own version.
""",
        encoding="utf-8",
    )

    signal = collect_project_signal(proj)

    assert signal["available"] is True
    assert signal["sources"] == [".claude/retrospectives/2026-05/0006_coupon.md"]
    assert any("Coupon series" in row["text"] for row in signal["carryover"])
    assert any("PROD bundle deploy plan" in row["text"] for row in signal["pending"])
    assert any("order_model.php" in row["text"] for row in signal["regression_watch"])
    assert any("PROD bundle" in row["text"] for row in signal["deploy_risk"])
    assert any("PROD deploy plan" in row["text"] for row in signal["next_actions"])
    assert all("source" in row and "line" in row for row in signal["pending"])


def test_project_signal_graceful_when_no_retros(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()

    signal = collect_project_signal(proj)

    assert signal["available"] is False
    assert signal["sources"] == []
    assert signal["pending"] == []
    assert signal["next_actions"] == []


def test_project_signal_sorts_retros_by_filename_timestamp(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    root = proj / ".claude" / "retrospectives" / "2026-05"
    root.mkdir(parents=True)
    (root / "0007_2026-05-13_10_30_pm_feat-old.md").write_text(
        "### Pending Items\n\n- old pending\n",
        encoding="utf-8",
    )
    (root / "0006_2026-05-16_03_40_am_feat-new.md").write_text(
        "### Pending Items\n\n- new pending\n",
        encoding="utf-8",
    )

    signal = collect_project_signal(proj)

    assert signal["sources"][0] == ".claude/retrospectives/2026-05/0006_2026-05-16_03_40_am_feat-new.md"
    assert signal["pending"][0]["text"] == "new pending"


def test_project_signal_sees_ai_memory_retros(tmp_path: Path) -> None:
    """Canonical rrr retros (.ai/memory/retros/) are scanned (2026-06-12).

    Before the glob was added, only legacy locations were read, so a
    months-old .claude/retrospectives file dominated lll's Project Signal
    forever while live retros were invisible.
    """
    proj = tmp_path / "proj"
    stale = proj / ".claude" / "retrospectives" / "2025-12_old.md"
    stale.parent.mkdir(parents=True)
    stale.write_text(
        "# Old\n\n## Pending Items\n\n- [ ] STALE deploy plan\n",
        encoding="utf-8",
    )
    fresh = (
        proj / ".ai" / "memory" / "retros"
        / "0090_2026-06-12_9_00_pm_feat-fresh.md"
    )
    fresh.parent.mkdir(parents=True)
    fresh.write_text(
        "# Retro\n\n## Pending Items\n\n- [ ] FRESH follow-up\n",
        encoding="utf-8",
    )

    signal = collect_project_signal(proj)

    assert signal["available"] is True
    texts = [row["text"] for row in signal["pending"]]
    assert any("FRESH" in t for t in texts), texts
    # fresh file (named timestamp) must rank before the stale undated one
    assert signal["sources"][0].endswith("0090_2026-06-12_9_00_pm_feat-fresh.md")


def test_project_signal_max_files_bound_drops_oldest(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    retros = proj / ".ai" / "memory" / "retros"
    retros.mkdir(parents=True)
    # 9 dated retros — bound is 8, the oldest must fall out of sources.
    for i in range(9):
        day = i + 1
        (retros / f"00{i:02d}_2026-06-{day:02d}_1_00_pm_feat-x.md").write_text(
            f"# R\n\n## Pending Items\n\n- [ ] item {i}\n", encoding="utf-8"
        )

    signal = collect_project_signal(proj)

    assert len(signal["sources"]) == 8
    assert not any("2026-06-01" in s for s in signal["sources"])
