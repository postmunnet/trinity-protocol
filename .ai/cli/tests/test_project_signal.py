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
