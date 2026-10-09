"""The catalogue eligibility sweep over a small catalogue: statuses, reason categories, rule ids, outputs."""

import json
import shutil
from pathlib import Path

from agents.evals.eligibility import main, markdown, reason_category, security_rule, sweep


REPO_PLOTS = Path(__file__).resolve().parents[4] / "plots"
NO_THEME = """import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
ax.plot([1, 2, 3], [4, 5, 6])
plt.savefig("plot.png")
"""


def catalogue(root: Path) -> Path:
    """Three pairs: an eligible original, a file without THEME and a single-theme target, and a banned import."""
    plots = root / "plots"
    for spec, library, text in (
        (
            "scatter-basic",
            "matplotlib",
            (REPO_PLOTS / "scatter-basic/implementations/python/matplotlib.py").read_text(),
        ),
        ("plain-line", "matplotlib", NO_THEME),
        (
            "scatter-basic",
            "seaborn",
            "import subprocess\n" + (REPO_PLOTS / "scatter-basic/implementations/python/seaborn.py").read_text(),
        ),
    ):
        target = plots / spec / "implementations" / "python" / f"{library}.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return plots


def test_reason_parsing() -> None:
    assert reason_category('no-theme: no module-level THEME = os.getenv("ANYPLOT_THEME", ...)') == "no-theme"
    assert security_rule("security: banned-import at line 1: import of subprocess") == "banned-import"
    assert security_rule("security: url-literal: a URL literal") == "url-literal"
    assert security_rule("security: 3 more findings") is None
    assert security_rule("savefig-target: no savefig call") is None


def test_sweep_counts_statuses_categories_and_rules(tmp_path: Path) -> None:
    result = sweep(catalogue(tmp_path))

    matplotlib, seaborn = result["by_library"]["matplotlib"], result["by_library"]["seaborn"]
    assert matplotlib["files"] == 2 and matplotlib["eligible"] == 1 and matplotlib["statuses"]["blocked"] == 1
    assert {"no-theme", "savefig-target"} <= set(matplotlib["blocked_by_category"])
    assert seaborn["statuses"]["blocked"] == 1 and seaborn["eligible_rate"] == 0.0
    assert seaborn["security_rules"] == {"banned-import": 1}
    assert {(item["spec_id"], item["library"]) for item in result["blocked"]} == {
        ("plain-line", "matplotlib"),
        ("scatter-basic", "seaborn"),
    }
    text = markdown(result, "2026-10-10")
    assert "| matplotlib | 2 | 1 (50.0 %) |" in text and "| `banned-import` | 0 | 1 |" in text


def test_main_writes_the_report(tmp_path: Path) -> None:
    plots = catalogue(tmp_path)

    assert main(["--plots", str(plots), "--out", str(tmp_path / "out")]) == 0

    (report_path,) = (tmp_path / "out").glob("*-eligibility.json")
    report = json.loads(report_path.read_text())
    assert report["by_library"]["matplotlib"]["files"] == 2
    assert report_path.with_suffix(".md").read_text().startswith("# Catalogue eligibility")
    assert main(["--plots", str(tmp_path / "missing"), "--out", str(tmp_path / "out")]) == 2


def test_the_real_catalogue_keeps_most_pairs_eligible(tmp_path: Path) -> None:
    """A smoke check over a copy of five real specs: the sweep runs on catalogue files as they are."""
    plots = tmp_path / "plots"
    for spec in ("scatter-basic", "line-basic", "bar-grouped", "heatmap-basic", "pie-basic"):
        shutil.copytree(REPO_PLOTS / spec / "implementations" / "python", plots / spec / "implementations" / "python")

    result = sweep(plots)

    for library in ("matplotlib", "seaborn"):
        assert result["by_library"][library]["files"] == 5
        assert result["by_library"][library]["eligible"] == 5
