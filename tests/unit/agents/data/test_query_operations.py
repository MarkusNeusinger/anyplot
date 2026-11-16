"""The operations only `query_data` takes (`prepare.QueryOperation`): an `aggregate` without `by`, and `fit`.

A grand total took two steps (an `aggregate` needs a key) and a fit had no operation at all, so the root worked such
figures out itself. A question now gets both in one step from the server, and `prepare_data` keeps refusing both,
since its result is stored as the user's table. Every table here is invented.
"""

import random
import typing
from typing import Any

import numpy as np
import pytest
from pydantic import ValidationError

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import (
    FIT_COLUMNS,
    NOTE_HEAD_CHARS,
    QUERY_ONLY_REFUSAL,
    Aggregate,
    Fit,
    Operation,
    PrepareArgs,
    PrepareError,
    QueryAggregate,
    QueryOperation,
    apply_and_parse,
    cast_note,
    whole_rounded,
)
from agents.anyplot.data.query import QueryArgs, QueryResult, run_query
from agents.anyplot.schemas import MAX_NOTE_CHARS


KILNS = (
    "batch,fired,temperature,hardness,lab\n"
    "K1,2025-03-02,612.5,3.41,north\n"
    "K2,2025-03-05,640,3.97,north\n"
    "K3,2025-03-09,655.25,4.18,south\n"
    "K4,2025-03-11,,4.02,south\n"
    "K5,2025-03-14,701.75,5.12,north\n"
    "K6,2025-03-20,733,,south\n"
    "K7,2025-03-23,760.5,6.07,north\n"
)
# The rows with a value in both temperature and hardness, for the references.
TEMPERATURE = [612.5, 640.0, 655.25, 701.75, 760.5]
HARDNESS = [3.41, 3.97, 4.18, 5.12, 6.07]
FIT = {"op": "fit", "x": "temperature", "y": "hardness"}


def query(*operations: dict[str, Any], data: str = KILNS) -> QueryResult:
    args = QueryArgs.model_validate({"operations": list(operations)})
    return run_query(parse_dataset(data), args.operations)


def refusal(*operations: dict[str, Any], data: str = KILNS) -> PrepareError:
    with pytest.raises(PrepareError) as caught:
        query(*operations, data=data)
    return caught.value


def one_row(result: QueryResult) -> dict[str, str]:
    assert result.total_rows == 1 and len(result.rows) == 1
    return dict(zip(result.columns, result.rows[0], strict=True))


def r_squared(x: list[float], y: list[float]) -> float:
    """The reference: 1 - SS_res / SS_tot of numpy's own least-squares line."""
    slope, intercept = np.polyfit(x, y, 1)
    residuals = np.asarray(y) - (slope * np.asarray(x) + intercept)
    return float(1 - (residuals @ residuals) / ((np.asarray(y) - np.mean(y)) @ (np.asarray(y) - np.mean(y))))


class TestTotalOverAllRows:
    @pytest.mark.parametrize("by", [{}, {"by": []}, {"by": None}], ids=["left_out", "empty", "null"])
    def test_an_aggregate_without_by_is_one_row_over_every_row(self, by: dict[str, Any]) -> None:
        result = query({"op": "aggregate", "column": "hardness", "how": "sum", **by})

        assert one_row(result) == {"hardness": "26.77"}  # added as the cells are written, never 26.770000000000003
        # K6 has no hardness: the total is over 6 values, and the line says so beside the 7 rows it read.
        assert result.changes == [
            "summed hardness over all 7 rows: 1 row, 4 other columns dropped, 1 row without a value in hardness left out"
        ]

    def test_a_mean_and_a_count_say_which_rows_they_leave_out(self) -> None:
        mean = query({"op": "aggregate", "column": "temperature", "how": "mean"})
        count = query({"op": "aggregate", "column": "temperature", "how": "count"})
        every = query({"op": "aggregate", "column": "batch", "how": "count"})

        assert one_row(mean) == {"temperature": repr(4103 / 6)}  # K4 has no temperature: a mean of 6 cells
        assert mean.changes == [
            "averaged temperature over all 7 rows: 1 row, 4 other columns dropped, "
            "1 row without a value in temperature left out"
        ]
        assert one_row(count) == {"count": "6"}
        assert count.changes == [
            "counted temperature over all 7 rows: 1 row, 4 other columns dropped, "
            "1 row without a value in temperature left out"
        ]
        assert one_row(every) == {"count": "7"}
        assert every.changes == ["counted batch over all 7 rows: 1 row, 4 other columns dropped"]

    def test_several_columns_count_the_rows_each_one_leaves_out(self) -> None:
        both = query({"op": "aggregate", "columns": ["temperature", "hardness"], "how": "max"})
        apart = query(
            {"op": "aggregate", "columns": ["north", "south"], "how": "mean"},
            data="plot,north,south\nA,4,\nB,,7\nC,5,\nD,6,9\n",
        )

        assert one_row(both) == {"temperature": "760.5", "hardness": "6.07"}
        assert both.changes == [
            "took the maximum of temperature and hardness over all 7 rows: 1 row, 3 other columns dropped, "
            "1 row without a value in temperature left out, 1 row without a value in hardness left out"
        ]
        assert one_row(apart) == {"north": "5", "south": "8"}
        assert apart.changes == [
            "averaged north and south over all 4 rows: 1 row, 1 other column dropped, "
            "1 row without a value in north left out, 2 rows without a value in south left out"
        ]

    def test_many_long_column_names_never_cut_the_counts(self) -> None:
        """Past the room the line leaves them, the names give way to the total of the empty cells, so the line's clip
        cuts names only."""
        names = [f"reading_{index}_" + "q" * 50 for index in range(10)]
        # Column c has no value in row c, except the last column, which misses no row.
        rows = [
            f"r{row}," + ",".join("" if column == row != 9 else str(row + column) for column in range(10))
            for row in range(10)
        ]
        data = "key," + ",".join(names) + "\n" + "\n".join(rows) + "\n"

        (line,) = query({"op": "aggregate", "columns": names, "how": "sum"}, data=data).changes

        assert len(line) <= MAX_NOTE_CHARS
        assert line.endswith(", 9 empty cells in 9 of the 10 value columns left out")

    def test_three_columns_of_ordinary_names_keep_a_count_each(self) -> None:
        names = ["Snowmelt 2021 (cm)", "Snowmelt 2022 (cm)", "Snowmelt 2023 (cm)"]
        data = "Cairn," + ",".join(names) + "\nA,10,,30\nB,,20,31\nC,12,,\nD,13,23,33\nE,14,24,34\n"

        result = query({"op": "aggregate", "columns": names, "how": "mean"}, data=data)

        # The columns miss 1, 2 and 1 rows: each mean is over its own count of values, and the line says which.
        assert one_row(result) == {names[0]: "12.25", names[1]: repr(67 / 3), names[2]: "32"}
        assert result.changes == [
            "averaged Snowmelt 2021 (cm), Snowmelt 2022 (cm) and Snowmelt 2023 (cm) over all 5 rows: 1 row, "
            "1 other column dropped, 1 row without a value in Snowmelt 2021 (cm) left out, "
            "2 rows without a value in Snowmelt 2022 (cm) left out, 1 row without a value in Snowmelt 2023 (cm) left out"
        ]

    @pytest.mark.parametrize("past", [0, 1], ids=["fits", "one_past"])
    def test_a_rounded_notice_and_the_count_share_the_line(self, past: int) -> None:
        """The count per column takes the room the rounded notice and the shortest start of the line leave; one
        character past it, the column's name gives way. Neither notice is cut: the start of the line gives way."""
        notice = whole_rounded(1)
        room = MAX_NOTE_CHARS - NOTE_HEAD_CHARS - len(", ") - len(notice) - len(", ")
        gauge = "west_gauge_" + "m" * (room - len("1 row without a value in west_gauge_ left out") + past)
        big = 9_000_000_000_000_000_000  # two of them leave the 64-bit whole-number range
        data = f"weir,{gauge},runoff\nA,4,{big}\nB,,{big}\nC,5,1\n"

        (line,) = query({"op": "aggregate", "columns": [gauge, "runoff"], "how": "sum"}, data=data).changes

        head = f"summed {gauge} and runoff over all 3 rows: 1 row, 1 other column dropped"
        note = f"1 row without a value in {gauge} left out"
        assert len(note) == room + past
        assert len(line) <= MAX_NOTE_CHARS
        if past:
            assert line.endswith(f"…, 1 empty cell in 1 of the 2 value columns left out, {notice}")
        else:
            assert line == f"{head[: NOTE_HEAD_CHARS - 1]}…, {note}, {notice}"

    def test_a_notice_longer_than_the_line_keeps_its_count_first(self) -> None:
        """A decimal notice that names many long columns leaves the start of the line nothing: the start gives way
        to its ellipsis, so the count still opens the notice, and columns that miss no row add no count of 0."""
        names = [f"gauge_{index}_" + "p" * 42 for index in range(5)]
        rows = [
            f"r{row}," + ",".join(str(9007199254740993 + 2 * row if c == 0 else row + c) for c in range(5))
            for row in range(3)
        ]
        data = "key," + ",".join(names) + "\n" + "\n".join(rows) + "\n"

        (line,) = query({"op": "aggregate", "columns": names, "how": "mean"}, data=data).changes

        assert len(cast_note(3, "in " + ", ".join(names))) > MAX_NOTE_CHARS
        assert len(line) == MAX_NOTE_CHARS
        assert line.startswith(f"…, 3 whole numbers past 2^53 in {names[0]}, ")
        assert "empty cell" not in line and "without a value" not in line

    def test_the_counts_join_a_rounded_and_a_decimal_notice(self) -> None:
        big = 9_000_000_000_000_000_000
        summed = query(
            {"op": "aggregate", "column": "grains", "how": "sum"},
            data=f"silo,grains,lot\nS1,{big},1\nS2,{big},2\nS3,,3\n",
        )
        averaged = query(
            {"op": "aggregate", "column": "grains", "how": "mean"},
            data="silo,grains,lot\nS1,9007199254740993,1\nS2,9007199254740995,2\nS3,,3\n",
        )

        assert summed.changes == [
            "summed grains over all 3 rows: 1 row, 2 other columns dropped, "
            f"1 row without a value in grains left out, {whole_rounded(1)}"
        ]
        assert averaged.changes == [
            "averaged grains over all 3 rows: 1 row, 2 other columns dropped, "
            f"1 row without a value in grains left out, {cast_note(2, 'in grains')}"
        ]

    def test_an_earlier_step_chooses_the_rows_it_totals(self) -> None:
        north = {"op": "keep_rows", "where": [{"column": "lab", "test": "eq", "value": "north"}]}
        first = {"op": "keep_rows", "n": 1}

        result = query(north, {"op": "aggregate", "column": "hardness", "how": "sum"})
        single = query(first, {"op": "aggregate", "column": "hardness", "how": "sum"})

        assert one_row(result) == {"hardness": "18.57"}
        assert result.changes[1] == "summed hardness over all 4 rows: 1 row, 4 other columns dropped"
        assert single.changes[1] == "summed hardness over the 1 row: 1 row, 4 other columns dropped"

    def test_a_period_still_needs_a_date_key(self) -> None:
        error = refusal({"op": "aggregate", "column": "hardness", "how": "sum", "period": "month"})

        assert (error.code, error.message) == ("invalid_operation", "a period needs a datetime column among the keys")


class TestPrepareDataStillRefusesThem:
    @pytest.mark.parametrize(
        "operation",
        [
            {"op": "aggregate", "column": "hardness", "how": "sum"},
            {"op": "aggregate", "by": [], "column": "hardness", "how": "sum"},
            {"op": "aggregate", "by": None, "column": "hardness", "how": "sum"},
            FIT,
        ],
    )
    def test_the_models_refuse_them(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            PrepareArgs.model_validate({"operations": [operation]})

    @pytest.mark.parametrize(
        "operation",
        [QueryAggregate(op="aggregate", column="hardness", how="sum"), Fit(op="fit", x="temperature", y="hardness")],
    )
    def test_the_path_to_a_stored_version_refuses_them_too(self, operation: Aggregate | Fit) -> None:
        # Past the models, as a caller that built the operation itself would pass it.
        operations: list[Any] = [operation]
        with pytest.raises(PrepareError) as caught:
            apply_and_parse(parse_dataset(KILNS), operations)

        assert (caught.value.code, caught.value.message) == ("invalid_operation", QUERY_ONLY_REFUSAL)

    def test_the_query_operations_are_prepare_datas_with_the_two_of_a_question(self) -> None:
        """A new `prepare_data` operation joins `QueryOperation` too, or a question could not take it."""
        shared = list(typing.get_args(typing.get_args(Operation)[0]))
        asked = list(typing.get_args(typing.get_args(QueryOperation)[0]))

        assert asked == [QueryAggregate if model is Aggregate else model for model in shared] + [Fit]


class TestFit:
    def test_the_line_is_numpys_least_squares_line(self) -> None:
        result = query(FIT)

        slope, intercept = np.polyfit(TEMPERATURE, HARDNESS, 1)
        found = one_row(result)
        assert result.columns == list(FIT_COLUMNS)
        assert float(found["slope"]) == pytest.approx(slope, abs=1e-12)
        assert float(found["intercept"]) == pytest.approx(intercept, abs=1e-12)
        assert float(found["r_squared"]) == pytest.approx(r_squared(TEMPERATURE, HARDNESS), abs=1e-12)
        assert found["n"] == "5"

    @pytest.mark.parametrize("seed", [3, 11, 29])
    def test_invented_points_match_numpy(self, seed: int) -> None:
        generator = random.Random(seed)
        x = [round(generator.uniform(-40, 90), 3) for _ in range(60)]
        y = [round(-2.75 * value + 18 + generator.gauss(0, 9), 4) for value in x]
        data = "x,y\n" + "".join(f"{a},{b}\n" for a, b in zip(x, y, strict=True))

        found = one_row(query({"op": "fit", "x": "x", "y": "y"}, data=data))

        slope, intercept = np.polyfit(x, y, 1)
        assert float(found["slope"]) == pytest.approx(slope, rel=1e-12, abs=1e-12)
        assert float(found["intercept"]) == pytest.approx(intercept, rel=1e-12, abs=1e-12)
        assert float(found["r_squared"]) == pytest.approx(r_squared(x, y), rel=1e-12, abs=1e-12)

    def test_the_server_rounds_nothing(self) -> None:
        """A slope of exactly one third comes back with every digit a float holds, as exact sums give it."""
        found = one_row(query({"op": "fit", "x": "x", "y": "y"}, data="x,y\n0,0.5\n3,1.5\n6,2.5\n9,3.5\n"))

        assert (found["slope"], found["intercept"], found["r_squared"]) == (repr(1 / 3), "0.5", "1")

    @pytest.mark.parametrize(
        ("data", "line"),
        [
            ("x,y\n1,0.1\n2,0.2\n3,0.3\n", ("0.1", "0", "1")),
            ("year,value\n2020,1.5\n2021,1.7\n2022,2.2\n", ("0.35", "-705.55", repr(49 / 52))),
        ],
        ids=["tenths", "years"],
    )
    def test_decimal_cells_give_the_decimal_line(self, data: str, line: tuple[str, str, str]) -> None:
        """The sums are of the cells as written (0.1, not the float nearest to it), so a line that is exact in
        decimals comes back as those decimals: in binary sums the slope would be 0.09999999999999999 and the
        intercept 1.850371707708594e-17, or 0.3500000000000001 and -705.5500000000002."""
        x, y = data.split("\n", 1)[0].split(",")

        found = one_row(query({"op": "fit", "x": x, "y": y}, data=data))

        assert (found["slope"], found["intercept"], found["r_squared"]) == line

    def test_a_later_compute_uses_the_fit_row(self) -> None:
        per_hundred = {"op": "compute", "name": "degrees", "expression": "100/m", "inputs": {"m": "slope"}}
        crossing = {
            "op": "compute",
            "name": "zero_at",
            "expression": "-b/m",
            "inputs": {"b": "intercept", "m": "slope"},
        }

        found = one_row(query(FIT, per_hundred, crossing))

        slope, intercept = np.polyfit(TEMPERATURE, HARDNESS, 1)
        assert float(found["degrees"]) == pytest.approx(100 / slope, rel=1e-12)
        assert float(found["zero_at"]) == pytest.approx(-intercept / slope, rel=1e-12)

    def test_an_earlier_step_chooses_the_rows_it_fits(self) -> None:
        north = {"op": "keep_rows", "where": [{"column": "lab", "test": "eq", "value": "north"}]}

        found = one_row(query(north, FIT))

        slope, _ = np.polyfit([612.5, 640, 701.75, 760.5], [3.41, 3.97, 5.12, 6.07], 1)
        assert float(found["slope"]) == pytest.approx(slope, abs=1e-12) and found["n"] == "4"

    def test_rows_without_both_values_are_left_out_and_counted(self) -> None:
        result = query(FIT)

        assert result.changes == [
            "fit of hardness on temperature by least squares over 5 rows: 1 row of slope, intercept, r_squared and "
            "n, 2 rows without a value in temperature or hardness left out"
        ]

    def test_a_y_with_one_value_has_a_line_but_no_r_squared(self) -> None:
        result = query({"op": "fit", "x": "x", "y": "y"}, data="x,y\n1,4\n2,4\n5,4\n")

        assert one_row(result) == {"slope": "0", "intercept": "4", "r_squared": "", "n": "3"}
        assert result.changes[0].endswith("r_squared is empty: y has one value in all 3 rows")

    @pytest.mark.parametrize(
        ("operations", "data", "code", "words"),
        [
            ([{"op": "fit", "x": "lab", "y": "hardness"}], KILNS, "type_mismatch", "set_type it to number first"),
            ([{"op": "fit", "x": "fired", "y": "hardness"}], KILNS, "type_mismatch", "date_number turns dates"),
            ([{"op": "fit", "x": "depth", "y": "hardness"}], KILNS, "unknown_column", "no column 'depth'"),
            (
                [{"op": "keep_rows", "where": [{"column": "batch", "test": "eq", "value": "K1"}]}, FIT],
                KILNS,
                "invalid_operation",
                "at least 2 rows with a value in temperature and hardness; 1 row has",
            ),
            (
                [{"op": "fit", "x": "x", "y": "y"}],
                "x,y\n2,1\n2,3\n,5\n2,8\n",
                "invalid_operation",
                "column 'x' has one value in all 3 rows the fit reads, so no line fits",
            ),
        ],
    )
    def test_refusals(self, operations: list[dict[str, Any]], data: str, code: str, words: str) -> None:
        error = refusal(*operations, data=data)

        assert error.code == code and words in error.message

    @pytest.mark.parametrize(
        "operation",
        [
            {"op": "fit", "x": "temperature"},
            {"op": "fit", "x": "temperature", "y": "hardness", "how": "linear"},
            {"op": "fit", "x": "temperature", "y": "hardness", "by": ["lab"]},
        ],
    )
    def test_malformed_fits_fail_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            QueryArgs.model_validate({"operations": [operation]})
