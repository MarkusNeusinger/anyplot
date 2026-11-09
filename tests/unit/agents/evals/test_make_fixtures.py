"""The spike-X fixture generator: determinism, the committed files, the schema, and that every case can run."""

import ast
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path

import pytest

from agents.anyplot.code.profiles.javascript.allowlist import REMOVED_EXPORTS
from agents.anyplot.data.bindings import check_bindings
from agents.anyplot.data.parse import RESPELLED, parse_dataset
from agents.anyplot.data.prepare import PrepareArgs, apply_and_parse
from agents.anyplot.dev_fixture import CASES_DIR, snapshot_from_repo
from agents.anyplot.opening import assess
from agents.anyplot.schemas import Binding
from agents.anyplot.settings import AgentSettings
from agents.evals import make_fixtures
from agents.evals.make_fixtures import (
    LIBRARIES,
    LIBRARY_SMOKE,
    PERTURBATIONS,
    SMOKE_CYCLE,
    SMOKE_TAG,
    SPECS,
    case_id,
    render_cases,
)


CASE_KEYS = {"spec_id", "library", "locale", "perturbation", "bindings", "expected", "tags", "source"}
FAMILIES = {"scatter", "line", "bar", "histogram", "box", "heatmap", "area", "violin", "pie", "time-series"}
BLOCKED = frozenset({("line-timeseries", "pygal")})
"""The `(spec, library)` files the readiness scan blocks for SECURITY findings; the generator's docstring says why.

Their cases are written all the same. A change that makes one of them eligible fails the readiness test until
the pair leaves this set and its cell in the docstring's table changes with it.
"""


@pytest.fixture(scope="module")
def files() -> dict[str, str]:
    return render_cases()


def _rows(text: str, delimiter: str = ",") -> list[list[str]]:
    return list(csv.reader(io.StringIO(text), delimiter=delimiter))


def test_two_runs_write_identical_files(files: dict[str, str]) -> None:
    assert render_cases() == files


def test_the_committed_cases_are_what_the_generator_writes() -> None:
    """Rerun `uv run --extra agents python -m agents.evals.make_fixtures` after changing it or upgrading NumPy."""
    assert make_fixtures.stale_files() == []


def test_check_mode_reports_a_stale_file(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    make_fixtures.write_cases(tmp_path)
    assert make_fixtures.main(["--check", "--out", str(tmp_path)]) == 0
    (tmp_path / "pie-basic-seaborn-n12" / "data.csv").write_text("Expense Category,Amount (CHF)\n")

    assert make_fixtures.main(["--check", "--out", str(tmp_path)]) == 1
    assert "stale: pie-basic-seaborn-n12/data.csv" in capsys.readouterr().err


def test_ten_specs_of_ten_families_times_fifteen_libraries_times_six_perturbations(files: dict[str, str]) -> None:
    from agents.anyplot.render.runtimes import RUNTIME_LIBRARIES

    assert len(SPECS) == 10 and {spec.family for spec in SPECS} == FAMILIES
    assert LIBRARIES == (
        "matplotlib",
        "seaborn",
        "plotnine",
        "altair",
        "pygal",
        "letsplot",
        "plotly",
        "bokeh",
        "ggplot2",
        "makie",
        "chartjs",
        "d3",
        "echarts",
        "highcharts",
        "muix",
    )
    assert set(LIBRARIES) == RUNTIME_LIBRARIES  # every library the registry serves has its 60 cases
    ids = {name.split("/")[0] for name in files}
    assert len(ids) == 900
    assert ids == {
        case_id(spec.spec_id, library, perturbation)
        for spec in SPECS
        for library in LIBRARIES
        for perturbation in PERTURBATIONS
    }


def test_the_libraries_of_a_spec_share_its_datasets_and_bindings(files: dict[str, str]) -> None:
    """Only `library`, the smoke tag and the case id tell the libraries of one spec and perturbation apart."""
    for spec in SPECS:
        for perturbation in PERTURBATIONS:
            directories = [case_id(spec.spec_id, library, perturbation) for library in LIBRARIES]
            assert len({files[f"{directory}/data.csv"] for directory in directories}) == 1
            cases = [json.loads(files[f"{directory}/case.json"]) for directory in directories]
            for case in cases:
                del case["library"]
                case["tags"] = [tag for tag in case["tags"] if tag != SMOKE_TAG]
            assert all(case == cases[0] for case in cases), (spec.spec_id, perturbation)


def test_case_json_schema(files: dict[str, str]) -> None:
    for name, text in files.items():
        if not name.endswith("case.json"):
            continue
        case = json.loads(text)
        assert set(case) - {"before_operations"} == CASE_KEYS, name
        assert ("before_operations" in case) == ("aggregation" in case["tags"]), name
        assert case["expected"] == "accepted"
        assert case["perturbation"] in PERTURBATIONS
        assert case["library"] in LIBRARIES
        assert case["bindings"] and all(set(item) == {"role", "column"} for item in case["bindings"])
        assert case["perturbation"] in case["tags"] and "synthetic" in case["tags"]
        assert case["source"].startswith("synthetic: agents/evals/make_fixtures.py")
        assert name.split("/")[0] == case_id(case["spec_id"], case["library"], case["perturbation"])


def test_smoke_covers_every_spec_perturbation_and_library(files: dict[str, str]) -> None:
    smoke = [json.loads(text) for name, text in files.items() if name.endswith("case.json")]
    smoke = [case for case in smoke if SMOKE_TAG in case["tags"]]
    cycle = [case for case in smoke if case["library"] in SMOKE_CYCLE]

    assert len(smoke) == len(SPECS) + len(LIBRARY_SMOKE) == 23
    assert set(SMOKE_CYCLE) | set(LIBRARY_SMOKE) == set(LIBRARIES) and not set(SMOKE_CYCLE) & set(LIBRARY_SMOKE)
    assert len(cycle) == len(SPECS)
    assert {case["spec_id"] for case in cycle} == {spec.spec_id for spec in SPECS}
    assert {case["perturbation"] for case in cycle} == set(PERTURBATIONS)
    assert {case["library"] for case in cycle} == set(SMOKE_CYCLE)
    others = {case["library"]: (case["spec_id"], case["perturbation"]) for case in smoke if case not in cycle}
    assert others == LIBRARY_SMOKE


def test_a_new_library_never_moves_the_smoke_cycle(files: dict[str, str]) -> None:
    """The ten cycle cases are the ones of `--cases smoke` before step 1b; every later library adds one."""
    smoke = sorted(
        name.split("/")[0]
        for name, text in files.items()
        if name.endswith("case.json") and SMOKE_TAG in json.loads(text)["tags"]
    )
    assert smoke == [
        "area-basic-matplotlib-renamed",
        "bar-grouped-matplotlib-n12",
        "box-basic-matplotlib-date",
        "heatmap-basic-seaborn-decimal-comma",
        "histogram-basic-seaborn-n5000",
        "line-basic-seaborn-x10",
        "line-timeseries-seaborn-n5000",
        "pie-basic-matplotlib-n12",
        "pie-basic-muix-renamed",
        "scatter-basic-altair-renamed",
        "scatter-basic-bokeh-renamed",
        "scatter-basic-chartjs-renamed",
        "scatter-basic-d3-renamed",
        "scatter-basic-echarts-renamed",
        "scatter-basic-ggplot2-renamed",
        "scatter-basic-highcharts-renamed",
        "scatter-basic-letsplot-renamed",
        "scatter-basic-makie-renamed",
        "scatter-basic-matplotlib-renamed",
        "scatter-basic-plotly-renamed",
        "scatter-basic-plotnine-renamed",
        "scatter-basic-pygal-renamed",
        "violin-basic-seaborn-x10",
    ]


@pytest.mark.parametrize("spec", SPECS, ids=lambda spec: spec.spec_id)
def test_every_case_parses_binds_and_is_eligible(spec: make_fixtures.SpecFixture, files: dict[str, str]) -> None:
    """The cases test the adaptation, never the parser: no warning, complete bindings, an eligible pair.

    The `BLOCKED` pairs are the exception: blocked, and for SECURITY findings, not for a disabled library. The
    plot draws every row it gets (owner decision of 2026-11-08), so no case hands it a key that the rows repeat: the
    raw records of `n5000` that repeat one take their data step first (`before_operations`), and the bindings hold
    on the table it leaves.
    """
    settings = AgentSettings(libraries=list(LIBRARIES))  # the default enables matplotlib and seaborn only
    for library in LIBRARIES:
        snapshot = snapshot_from_repo(spec.spec_id, library)
        eligibility, _ = assess(snapshot, library, settings)
        if (spec.spec_id, library) in BLOCKED:
            assert eligibility.status == "blocked", (library, eligibility.reasons)
            assert any(reason.startswith("security: ") for reason in eligibility.reasons), eligibility.reasons
        else:
            assert eligibility.status in ("clean", "coupled"), (library, eligibility.reasons)
        roles = snapshot.roles()  # as the session reads them, the key roles marked (`fidelity.mark_keys`)
        for perturbation in PERTURBATIONS:
            directory = case_id(spec.spec_id, library, perturbation)
            case = json.loads(files[f"{directory}/case.json"])
            parsed = parse_dataset(files[f"{directory}/data.csv"])
            # The spelling line (`12.50` written `12.5`) says what the canonical form changed; it is no parse issue.
            assert [warning for warning in parsed.warnings if RESPELLED not in warning] == [], directory
            bindings = [Binding(**item) for item in case["bindings"]]
            raw = check_bindings(bindings, roles, parsed.profile)
            assert raw.complete and not raw.errors, (directory, raw.errors)
            for operations in case.get("before_operations", []):
                args = PrepareArgs.model_validate({"operations": operations})
                _, parsed = apply_and_parse(parsed, args.operations, language="en")
            check = check_bindings(bindings, roles, parsed.profile)
            assert check.complete and not check.errors and check.repeated_key is None, (directory, check.warnings)
            assert ("before_operations" in case) == (raw.repeated_key is not None), directory


MUIX_7 = re.compile(r"^// Library: muix 7\.", re.MULTILINE)
"""The header line of a MUI X file written for MUI X 7."""
MUIX_7_IMPORT = re.compile(
    r'"@mui/x-charts/ChartContainer"'
    rf'|import\s*\{{[^}}]*\b(?:{"|".join(REMOVED_EXPORTS)})\b[^}}]*\}}\s*from\s*"@mui/x-charts"'
)
"""An import MUI X 9 lacks: the module `@mui/x-charts/ChartContainer`, or a removed name from the package root."""


def test_the_muix_files_split_by_the_version_they_were_written_for() -> None:
    """JS-4c (2026-10-31): a MUI X file is served whichever version it was written for, never blocked for its version
    (the plan's question 13). A file written for MUI X 7 is `coupled`, and one that imports MUI X 7's `ChartContainer`
    carries `deprecated-api`, which the adapter rewrites (`scatter-basic` on 2026-10-31); a `clean` file is one written
    for MUI X 9 (five of the ten then). The smoke case avoids MUI X 7, since the eval harness's preflight renders the
    catalogue file unchanged. The MUI X 9 pass regenerates these files, so the test holds the rules, not the split."""
    settings = AgentSettings(libraries=list(LIBRARIES))
    plots = Path(__file__).parents[4] / "plots"
    texts: dict[str, str] = {}
    statuses: set[str] = set()
    for spec in SPECS:
        text = (plots / spec.spec_id / "implementations" / "javascript" / "muix.tsx").read_text(encoding="utf-8")
        texts[spec.spec_id] = text
        eligibility, _ = assess(snapshot_from_repo(spec.spec_id, "muix"), "muix", settings)
        statuses.add(eligibility.status)
        deprecated = any(reason.startswith("deprecated-api") for reason in eligibility.reasons)
        assert eligibility.status in ("clean", "coupled"), (spec.spec_id, eligibility.status)
        assert deprecated == bool(MUIX_7_IMPORT.search(text)), spec.spec_id
        assert not MUIX_7.search(text) or eligibility.status == "coupled", spec.spec_id
    assert "clean" in statuses  # the clean class occurs at all
    assert not MUIX_7.search(texts[LIBRARY_SMOKE["muix"][0]])


@pytest.mark.parametrize("library", ["plotly", "bokeh"])
def test_the_plotly_and_bokeh_files_are_eligible_with_their_figure_save(library: str) -> None:
    """PB-2a (2026-10-31): every one of the ten plotly and bokeh files is eligible, `coupled` but bokeh's `bar-grouped`,
    and its normalised form ends on the pinned figure save the renderer's figure mode draws (`code/figure.py`);
    bokeh's `histogram-basic` is eligible through the normaliser's `.format` rewrite of its hex colours."""
    from agents.anyplot.code.figure import figure_saves
    from agents.anyplot.code.normalise import normalise

    settings = AgentSettings(libraries=list(LIBRARIES))
    statuses = {}
    for spec in SPECS:
        snapshot = snapshot_from_repo(spec.spec_id, library)
        eligibility, _ = assess(snapshot, library, settings)
        statuses[spec.spec_id] = eligibility.status
        tree = ast.parse(normalise(snapshot.code, library=library))
        assert figure_saves(tree, library) and figure_saves(tree, library)[-1][0] is tree.body[-1], spec.spec_id
    clean = {"bar-grouped"} if library == "bokeh" else set()
    assert {spec for spec, status in statuses.items() if status == "clean"} == clean
    assert {spec for spec, status in statuses.items() if status == "coupled"} == set(statuses) - clean
    assert LIBRARY_SMOKE[library] == ("scatter-basic", "renamed")


@pytest.mark.parametrize("spec", SPECS, ids=lambda spec: spec.spec_id)
def test_perturbations_change_what_they_name(spec: make_fixtures.SpecFixture, files: dict[str, str]) -> None:
    def data(perturbation: str, delimiter: str = ",") -> list[list[str]]:
        return _rows(files[f"{case_id(spec.spec_id, 'matplotlib', perturbation)}/data.csv"], delimiter)

    renamed, scaled = data("renamed"), data("x10")
    assert renamed[0] != scaled[0] and len(renamed) == len(scaled) == spec.base_rows + 1
    columns = spec.make(make_fixtures._rng(spec, 0), spec.base_rows)
    measures = [(index, column.decimals) for index, column in enumerate(columns) if column.measure]
    assert measures
    for index, decimals in measures:
        rounding = 6 * 10**-decimals  # both sides are rounded to the column's decimals
        for before, after in zip(renamed[1:], scaled[1:], strict=True):
            assert float(after[index]) == pytest.approx(float(before[index]) * 10, abs=rounding)
    assert len(data("n12")) == 13 and len(data("n5000")) == 5001

    dated = data("date")
    header = dated[0]
    dmy, iso = header.index(spec.date_names[0]), header.index(spec.date_names[1])
    assert all(row[dmy][2] == "." and row[dmy][5] == "." for row in dated[1:])
    assert all(row[iso][4] == "-" for row in dated[1:])

    semicolon = data("decimal-comma", ";")
    assert semicolon[0] == scaled[0]  # the base headers
    assert all(len(row) == len(semicolon[0]) for row in semicolon)
    assert any("," in cell for row in semicolon[1:] for cell in row)
    assert parse_dataset(files[f"{case_id(spec.spec_id, 'seaborn', 'decimal-comma')}/data.csv"]).profile.decimal == ","


def test_n5000_needs_aggregation_where_the_spec_draws_one_mark_per_group(files: dict[str, str]) -> None:
    """Those raw records repeat their keys, and the data step combines them per key before the plot."""
    for spec in SPECS:
        directory = case_id(spec.spec_id, "seaborn", "n5000")
        rows = _rows(files[f"{directory}/data.csv"])[1:]
        columns = spec.make(make_fixtures._rng(spec, 0), spec.base_rows)
        groups = [index for index, column in enumerate(columns) if column.role and not column.measure]
        repeats = Counter(tuple(row[index] for index in groups) for row in rows)
        base = Counter(tuple(row[index] for index in groups) for row in _rows(to_text(spec, files))[1:])
        case = json.loads(files[f"{directory}/case.json"])
        if spec.aggregate:
            assert max(repeats.values()) > 1 and max(base.values()) == 1, spec.spec_id
            keys = [columns[index].name for index in groups]
            (value,) = (column.name for column in columns if column.role and column.measure)
            assert case["before_operations"] == [
                [{"op": "aggregate", "by": keys, "column": value, "how": spec.aggregate}]
            ]
        else:
            assert "before_operations" not in case
        assert ("aggregation" in case["tags"]) == (spec.aggregate is not None)


def to_text(spec: make_fixtures.SpecFixture, files: dict[str, str]) -> str:
    """The base data (the `x10` case keeps the base headers and rows)."""
    return files[f"{case_id(spec.spec_id, 'seaborn', 'x10')}/data.csv"]


def test_the_hand_written_cases_stay() -> None:
    for name in ("scatter-basic-matplotlib", "bar-grouped-seaborn"):
        case = json.loads((CASES_DIR / name / "case.json").read_text())
        assert SMOKE_TAG in case["tags"] and case["expected"] == "accepted"
