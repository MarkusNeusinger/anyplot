"""The catalogue eligibility sweep over a small catalogue: statuses, reason categories, rule ids, outputs."""

import json
import shutil
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agents.anyplot.code.profiles.julia.coupling import structure_reasons as julia_structure_reasons
from agents.anyplot.code.profiles.julia.normalise import normalise as normalise_julia
from agents.anyplot.code.profiles.julia.validate import validate_security as validate_julia_security
from agents.anyplot.code.profiles.r.coupling import structure_reasons as r_structure_reasons
from agents.anyplot.code.profiles.r.normalise import normalise as normalise_r
from agents.anyplot.code.profiles.r.validate import validate_security as validate_r_security
from agents.anyplot.code.readiness import MAX_SECURITY_REASONS
from agents.evals.eligibility import (
    LIBRARIES,
    implementation_glob,
    main,
    markdown,
    reason_category,
    security_rule,
    sweep,
)
from core.spec_roles import MAP_SPECS
from core.utils import strip_noqa_comments


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
    assert implementation_glob("makie") == "*/implementations/julia/makie.jl"


PROFILES: dict[str, tuple[Callable[[str], str], Callable[[str], list[Any]], Callable[[str], list[str]]]] = {
    "ggplot2": (normalise_r, validate_r_security, r_structure_reasons),
    "makie": (normalise_julia, validate_julia_security, julia_structure_reasons),
}
"""Each runtime's normaliser, SECURITY profile and structure check, which the sweep's readiness scan applies."""


def assert_the_sweep_follows_the_profiles(library: str, occurring: tuple[str, ...]) -> None:
    """The sweep of `library` over the real catalogue, held to its runtime's own parts: every file gets a status
    and none errors, the `occurring` statuses all occur, a file is blocked exactly when its spec is a map spec, the
    SECURITY profile flags it or its structure fails, and for those reasons only; the counts by category and by
    rule, the eligible share and the Markdown row follow from those files."""
    normalise, validate, structure = PROFILES[library]
    files = sorted(REPO_PLOTS.glob(implementation_glob(library)))
    expected: dict[str, set[str]] = {}
    rules: Counter[str] = Counter()
    for path in files:
        spec_id = path.parents[2].name
        normalised = normalise(strip_noqa_comments(path.read_text(encoding="utf-8")) or "")
        # The scan names the first MAX_SECURITY_REASONS findings and counts the rest, so the sweep sees their rules.
        found = {finding.rule for finding in validate(normalised)[:MAX_SECURITY_REASONS]}
        rules.update(found)
        categories = {reason_category(reason) for reason in structure(normalised)}
        categories |= {"map-spec"} if spec_id in MAP_SPECS else set()
        categories |= {"security"} if found else set()
        if categories:
            expected[spec_id] = categories

    result = sweep(REPO_PLOTS, (library,))
    counts = result["by_library"][library]
    statuses = counts["statuses"]
    assert counts["files"] == len(files) == sum(statuses.values())
    assert statuses["error"] == 0 and all(statuses[status] for status in occurring), statuses
    assert counts["eligible"] == statuses["clean"] + statuses["coupled"]
    blocked = {item["spec_id"]: set(item["categories"]) for item in result["blocked"]}
    assert len(blocked) == statuses["blocked"] and blocked == expected
    assert counts["blocked_by_category"] == dict(sorted(Counter(c for cs in expected.values() for c in cs).items()))
    assert counts["security_rules"] == dict(sorted(rules.items()))
    eligible, total = counts["eligible"], counts["files"]
    row = f"| {library} | {total} | {eligible} ({eligible / total * 100:.1f} %) | {statuses['clean']} | "
    row += f"{statuses['coupled']} | {statuses['blocked']} | 0 |"
    assert markdown(result, "2026-11-09").splitlines()[4] == row


def test_the_ggplot2_sweep_over_the_real_catalogue() -> None:
    """The R runtime over every ggplot2 file (PR 3b, 2026-10-29; the owner rule of the same day: a missing marker
    is `coupled`, never `blocked`). The counts of a day (325 files on 2026-10-29: 4 clean, 306 coupled, 15 blocked,
    which were the 13 map specs, qrcode-basic and maze-circular; four map specs carried SECURITY findings too) move
    with regenerations, so the sweep is held to the rules above, with all three statuses occurring."""
    assert_the_sweep_follows_the_profiles("ggplot2", ("clean", "coupled", "blocked"))


def test_the_makie_sweep_over_the_real_catalogue() -> None:
    """The Julia runtime over every Makie file (J2b, 2026-10-30). The counts of a day (325 files on 2026-10-30: 0
    clean, 308 coupled, 17 blocked: the 13 map specs, qrcode-basic and the three saves inside a
    `with_theme(...) do` block, area-mountain-panorama, bifurcation-basic and scatter-lag) move with regenerations,
    so the sweep is held to the rules above. No Makie file carries column constants, so no file is clean and only
    the coupled and blocked statuses must occur."""
    assert_the_sweep_follows_the_profiles("makie", ("coupled", "blocked"))


def test_the_real_catalogue_keeps_most_pairs_eligible(tmp_path: Path) -> None:
    """A smoke check over a copy of five real specs: the sweep runs on catalogue files as they are."""
    plots = tmp_path / "plots"
    for spec in ("scatter-basic", "line-basic", "bar-grouped", "heatmap-basic", "pie-basic"):
        shutil.copytree(REPO_PLOTS / spec / "implementations" / "python", plots / spec / "implementations" / "python")

    result = sweep(plots)

    for library in ("matplotlib", "seaborn"):
        assert result["by_library"][library]["files"] == 5
        assert result["by_library"][library]["eligible"] == 5
