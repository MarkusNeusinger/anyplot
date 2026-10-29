"""The catalogue eligibility sweep over a small catalogue: statuses, reason categories, rule ids, outputs."""

import json
import shutil
from pathlib import Path

from agents.evals.eligibility import (
    LIBRARIES,
    implementation_glob,
    main,
    markdown,
    reason_category,
    security_rule,
    sweep,
)


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


def test_the_sweep_covers_every_library_with_a_runtime() -> None:
    from agents.anyplot.render.runtimes import RUNTIME_LIBRARIES

    assert set(LIBRARIES) == RUNTIME_LIBRARIES and len(LIBRARIES) == len(RUNTIME_LIBRARIES)
    assert implementation_glob("matplotlib") == "*/implementations/python/matplotlib.py"
    assert implementation_glob("ggplot2") == "*/implementations/r/ggplot2.R"


def test_the_ggplot2_sweep_over_the_real_catalogue() -> None:
    """The R runtime over all 325 ggplot2 files (2026-10-29, PR 3b; the owner rule of the same day: a missing marker
    is `coupled`, never `blocked`): 4 clean, 306 coupled, 15 blocked, which are the 13 map specs, qrcode-basic (the
    qrcode package and a URL) and maze-circular (`<<-`). Four map specs carry SECURITY findings too."""
    result = sweep(REPO_PLOTS, ("ggplot2",))

    ggplot2 = result["by_library"]["ggplot2"]
    assert (ggplot2["files"], ggplot2["eligible"]) == (325, 310)
    assert ggplot2["statuses"] == {"clean": 4, "coupled": 306, "blocked": 15, "error": 0}
    assert ggplot2["blocked_by_category"] == {"map-spec": 13, "security": 6}
    assert ggplot2["security_rules"] == {"banned-import": 3, "banned-name": 2, "banned-statement": 1, "url-literal": 2}
    security = sorted(item["spec_id"] for item in result["blocked"] if "security" in item["categories"])
    assert security == [
        "flowmap-origin-destination",
        "heatmap-geographic",
        "map-connection-lines",
        "map-projections",
        "maze-circular",
        "qrcode-basic",
    ]
    assert markdown(result, "2026-10-29").splitlines()[4] == "| ggplot2 | 325 | 310 (95.4 %) | 4 | 306 | 15 | 0 |"


def test_the_real_catalogue_keeps_most_pairs_eligible(tmp_path: Path) -> None:
    """A smoke check over a copy of five real specs: the sweep runs on catalogue files as they are."""
    plots = tmp_path / "plots"
    for spec in ("scatter-basic", "line-basic", "bar-grouped", "heatmap-basic", "pie-basic"):
        shutil.copytree(REPO_PLOTS / spec / "implementations" / "python", plots / spec / "implementations" / "python")

    result = sweep(plots)

    for library in ("matplotlib", "seaborn"):
        assert result["by_library"][library]["files"] == 5
        assert result["by_library"][library]["eligible"] == 5
