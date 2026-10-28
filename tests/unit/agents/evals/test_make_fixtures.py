"""The spike-X fixture generator: determinism, the committed files, the schema, and that every case can run."""

import csv
import io
import json
from collections import Counter

import pytest

from agents.anyplot.data.bindings import check_bindings
from agents.anyplot.data.parse import RESPELLED, parse_dataset
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
from core.spec_roles import parse_roles


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


def test_ten_specs_of_ten_families_times_six_libraries_times_six_perturbations(files: dict[str, str]) -> None:
    assert len(SPECS) == 10 and {spec.family for spec in SPECS} == FAMILIES
    assert LIBRARIES == ("matplotlib", "seaborn", "plotnine", "altair", "pygal", "letsplot")
    ids = {name.split("/")[0] for name in files}
    assert len(ids) == 360
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
        assert set(case) == CASE_KEYS, name
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

    assert len(smoke) == len(SPECS) + len(LIBRARY_SMOKE) == 14
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
        "scatter-basic-altair-renamed",
        "scatter-basic-letsplot-renamed",
        "scatter-basic-matplotlib-renamed",
        "scatter-basic-plotnine-renamed",
        "scatter-basic-pygal-renamed",
        "violin-basic-seaborn-x10",
    ]


@pytest.mark.parametrize("spec", SPECS, ids=lambda spec: spec.spec_id)
def test_every_case_parses_binds_and_is_eligible(spec: make_fixtures.SpecFixture, files: dict[str, str]) -> None:
    """The cases test the adaptation, never the parser: no warning, complete bindings, an eligible pair.

    The `BLOCKED` pairs are the exception: blocked, and for SECURITY findings, not for a disabled library.
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
        roles = parse_roles(snapshot.data_roles)
        for perturbation in PERTURBATIONS:
            directory = case_id(spec.spec_id, library, perturbation)
            case = json.loads(files[f"{directory}/case.json"])
            parsed = parse_dataset(files[f"{directory}/data.csv"])
            # The spelling line (`12.50` written `12.5`) says what the canonical form changed; it is no parse issue.
            assert [warning for warning in parsed.warnings if RESPELLED not in warning] == [], directory
            check = check_bindings([Binding(**item) for item in case["bindings"]], roles, parsed.profile)
            assert check.complete and not check.errors, (directory, check.errors)


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
    for spec in SPECS:
        directory = case_id(spec.spec_id, "seaborn", "n5000")
        rows = _rows(files[f"{directory}/data.csv"])[1:]
        columns = spec.make(make_fixtures._rng(spec, 0), spec.base_rows)
        groups = [index for index, column in enumerate(columns) if column.role and not column.measure]
        repeats = Counter(tuple(row[index] for index in groups) for row in rows)
        base = Counter(tuple(row[index] for index in groups) for row in _rows(to_text(spec, files))[1:])
        if spec.aggregates:
            assert max(repeats.values()) > 1 and max(base.values()) == 1, spec.spec_id
        tags = json.loads(files[f"{directory}/case.json"])["tags"]
        assert ("aggregation" in tags) == spec.aggregates


def to_text(spec: make_fixtures.SpecFixture, files: dict[str, str]) -> str:
    """The base data (the `x10` case keeps the base headers and rows)."""
    return files[f"{case_id(spec.spec_id, 'seaborn', 'x10')}/data.csv"]


def test_the_hand_written_cases_stay() -> None:
    for name in ("scatter-basic-matplotlib", "bar-grouped-seaborn"):
        case = json.loads((CASES_DIR / name / "case.json").read_text())
        assert SMOKE_TAG in case["tags"] and case["expected"] == "accepted"
