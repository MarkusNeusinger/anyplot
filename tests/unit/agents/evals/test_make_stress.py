"""The stress-case generator: determinism, the committed files, the exact sizes at and past the caps, the schema."""

import csv
import io
import json

import numpy as np
import pytest

from agents.anyplot.data.parse import MAX_INPUT_BYTES, MAX_INPUT_CELL_CHARS, ParseError, parse_dataset
from agents.anyplot.dev_fixture import CASES_DIR
from agents.anyplot.schemas import MAX_COLUMNS, MAX_ROWS
from agents.evals import make_stress
from agents.evals.cases import MAX_CHANGE_REQUEST_CHARS, load_case
from agents.evals.make_stress import OVER_BYTES, PREFIX, STANDIN_FILE, exact_rows, render_cases, with_decimals


GROUPS = {"cap", "over-cap", "categories", "degenerate", "injection", "compute"}
CASE_KEYS = {"spec_id", "library", "locale", "expected", "tags", "source", "bound_expected", "needs_model", "static"}


@pytest.fixture(scope="module")
def files() -> dict[str, str]:
    return render_cases()


def _data(files: dict[str, str], name: str) -> str:
    return files[f"{PREFIX}{name}/data.csv"]


def _records(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text.removeprefix("﻿"))))


def test_two_runs_write_identical_files(files: dict[str, str]) -> None:
    assert render_cases() == files


def test_the_committed_cases_are_what_the_generator_writes() -> None:
    """Rerun `uv run --extra agents python -m agents.evals.make_stress` after changing the generator."""
    assert make_stress.stale_files() == []


def test_check_mode_reports_a_changed_and_a_stray_file(tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    make_stress.write_cases(tmp_path)
    assert make_stress.main(["--check", "--out", str(tmp_path)]) == 0
    (tmp_path / "stress-single-row" / "data.csv").write_text("Store\n")
    (tmp_path / "stress-single-row" / "notes.txt").write_text("left over")

    assert make_stress.main(["--check", "--out", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "stale: stress-single-row/data.csv" in err and "stale: stress-single-row/notes.txt" in err


def test_the_cap_cases_sit_exactly_at_the_parsers_limits(files: dict[str, str]) -> None:
    rows = _data(files, "cap-rows")
    assert len(rows.encode("utf-8")) == MAX_INPUT_BYTES
    assert len(_records(rows)) - 1 == MAX_ROWS

    columns = _data(files, "cap-columns")
    assert len(columns.encode("utf-8")) == MAX_INPUT_BYTES and columns.startswith("﻿")
    parsed = parse_dataset(columns)
    assert len(parsed.profile.columns) == MAX_COLUMNS
    raw = _records(columns)
    assert max(len(cell) for row in raw[1:] for cell in row) > MAX_INPUT_CELL_CHARS  # format characters in it
    assert any(len(cell) == MAX_INPUT_CELL_CHARS for row in raw[1:] for cell in row)

    for name in ("cap-profile", "csv-expansion"):
        assert len(_data(files, name).encode("utf-8")) == MAX_INPUT_BYTES, name
        parse_dataset(_data(files, name))  # accepted


@pytest.mark.parametrize(
    ("name", "code"),
    [("over-rows", "too_many_rows"), ("over-columns", "too_many_columns"), ("over-cell", "cell_too_long")],
)
def test_each_over_cap_case_breaks_exactly_one_limit(files: dict[str, str], name: str, code: str) -> None:
    with pytest.raises(ParseError) as caught:
        parse_dataset(_data(files, name))
    assert caught.value.code == code
    assert len(_data(files, name).encode("utf-8")) <= MAX_INPUT_BYTES


def test_over_bytes_is_one_kibibyte_past_the_cap_and_otherwise_valid(files: dict[str, str]) -> None:
    text = _data(files, "over-bytes")
    assert len(text.encode("utf-8")) == OVER_BYTES == MAX_INPUT_BYTES + 1024
    assert len(_records(text)) - 1 < MAX_ROWS
    with pytest.raises(ParseError) as caught:
        parse_dataset(text)
    assert caught.value.code == "too_long"


@pytest.mark.parametrize("extra", [0, 2, 3, 7, 19, 20, 21, 39, 40, 41, 1000])
def test_with_decimals_adds_exactly_the_requested_characters(extra: int) -> None:
    values = list(range(1, 21))
    padded = with_decimals(values, extra, np.random.default_rng(0))

    assert sum(len(text) for text in padded) - sum(len(str(value)) for value in values) == extra
    assert [float(text) // 1 for text in padded] == [float(value) for value in values]  # only decimals were added


def test_with_decimals_refuses_what_it_cannot_pad() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="already too long"):
        with_decimals([1, 2], -1, rng)
    with pytest.raises(ValueError, match="one character"):
        with_decimals([1, 2], 1, rng)


def test_exact_rows_fills_the_target_through_the_last_cell() -> None:
    text = exact_rows("a,b,note\n", lambda index: [str(index), str(index * 7)], target=5_000)

    assert len(text.encode("utf-8")) == 5_000
    rows = _records(text)[1:]
    assert all(len(row[2]) <= MAX_INPUT_CELL_CHARS and row[2] == row[2].strip() for row in rows)


def test_case_json_schema_and_the_groups(files: dict[str, str]) -> None:
    cases = {name.split("/")[0]: json.loads(text) for name, text in files.items() if name.endswith("case.json")}

    assert len(cases) == 23 and all(case_id.startswith(PREFIX) for case_id in cases)
    groups = set()
    for case_id, case in cases.items():
        assert CASE_KEYS <= set(case) <= CASE_KEYS | {"bindings", "render", "marker"}, case_id
        assert case["tags"][0] == "stress" and case["tags"][2] == "synthetic", case_id
        groups.add(case["tags"][1])
        assert case["bound_expected"] and isinstance(case["needs_model"], bool) and case["static"], case_id
        assert case["expected"] in ("accepted", "rejected", "unknown"), case_id
    assert groups == GROUPS
    assert sorted(case_id for case_id, case in cases.items() if case["needs_model"]) == [
        "stress-compute-distances",
        "stress-compute-lorenz",
        "stress-compute-oversample",
        "stress-pie-30-slices",
    ]
    rejected = sorted(case_id for case_id, case in cases.items() if case["expected"] == "rejected")
    assert rejected == [
        "stress-all-nan-column",
        "stress-mixed-decimals",
        "stress-over-bytes",
        "stress-over-cell",
        "stress-over-columns",
        "stress-over-rows",
    ]


def test_requests_and_stand_ins(files: dict[str, str]) -> None:
    requests = {name.split("/")[0] for name in files if name.endswith("change_request.txt")}
    standins = {name.split("/")[0] for name in files if name.endswith(STANDIN_FILE)}

    assert requests == {f"{PREFIX}compute-lorenz", f"{PREFIX}compute-oversample", f"{PREFIX}compute-distances"}
    assert standins == requests | {f"{PREFIX}bar-100-categories", f"{PREFIX}pie-30-slices"}
    for case_id in requests:
        assert 0 < len(files[f"{case_id}/change_request.txt"].strip()) <= MAX_CHANGE_REQUEST_CHARS
    for case_id in standins:
        body = files[f"{case_id}/{STANDIN_FILE}"]
        assert body.count("df = load_user_data()") == 1, case_id
        assert "savefig" not in body and "THEME" not in body, case_id  # the catalogue file supplies both


def test_every_committed_stress_case_loads() -> None:
    for directory in sorted(CASES_DIR.glob(PREFIX + "*")):
        case = load_case(directory)
        assert "stress" in case.tags and case.data_text
