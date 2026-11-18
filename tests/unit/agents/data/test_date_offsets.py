"""A date followed directly by a UTC offset and no time (`2026-03-01+01:00`, `2026-03-01-05:00`, `2026-03-01Z`).

Owner decision F4 (option a): the parser keeps such a column as written, as text with a note that names its shape;
`set_type` reads the written day into a new column on request and counts the dropped offsets in its change line; a
filter bound of that shape is the whole day, as a date without a time is; and a sign with digits in any other form
after a date (`-03`, `+0100`, `-05:00:00`) is refused, since `2026-03-01-03` may as well be an hour label. Before the
fix the parser left such cells text without a word, pandas read `-05:00` as the time 05:00 and `-03` as 03:00 (four
hour labels became four equal dates, rated certain), and `datetime.fromisoformat` read a bound's `+01:00` as 01:00.
"""

import csv
import io
from typing import Any

import pytest
from pydantic import TypeAdapter

from agents.anyplot.data.bindings import default_bindings
from agents.anyplot.data.conversions import Candidate, candidates
from agents.anyplot.data.parse import MAX_COMPUTED_BYTES, ParsedDataset, parse_dataset
from agents.anyplot.data.prepare import (
    OFFSET_DAYS_READING,
    Operation,
    Prepared,
    PrepareError,
    apply_operations,
    dry_run,
    read_frame,
)
from agents.anyplot.schemas import MAX_NOTE_CHARS
from core.spec_roles import parse_roles


OPERATIONS = TypeAdapter(list[Operation])
ROLLING = parse_roles(
    [
        "`date` (datetime) - Timestamp values representing points in time",
        "`value` (numeric) - Raw measurements or observations at each timestamp",
        "`rolling_avg` (numeric) - Computed rolling average (e.g., 7-day, 30-day window)",
    ]
)
"""The roles of `line-timeseries-rolling`, whose date role a pasted column of days would fill."""
NOTE = (
    "column 'day': kept as text: every cell is a date followed directly by a UTC offset, with no time "
    "(YYYY-MM-DD±HH:MM or YYYY-MM-DDZ)"
)
SIGN_REFUSAL = (
    "column 'day' holds dates followed directly by a sign and digits in no UTC offset form (such as YYYY-MM-DD-HH or "
    "YYYY-MM-DD±HHMM), which may be an hour as well as an offset, so the column stays as it is: an offset reads in "
    "the form YYYY-MM-DD±HH:MM, a time in the form YYYY-MM-DDTHH:MM"
)


def table(offset: str, column: str = "day") -> str:
    """The table the owner was shown, with `offset` after each day."""
    return f"{column},kWh\n2026-03-01{offset},12\n2026-03-02{offset},15\n2026-03-03{offset},11\n"


def prepare(text: str, *operations: dict[str, Any]) -> Prepared:
    return apply_operations(parse_dataset(text), OPERATIONS.validate_python(list(operations)))


def refusal(text: str, *operations: dict[str, Any]) -> tuple[str, str]:
    with pytest.raises(PrepareError) as caught:
        prepare(text, *operations)
    return caught.value.code, caught.value.message


def column(prepared: Prepared, name: str) -> list[str]:
    rows = list(csv.DictReader(io.StringIO(prepared.csv)))
    return [row[name] for row in rows]


def reparse(prepared: Prepared) -> ParsedDataset:
    return parse_dataset(
        prepared.csv, text_columns=prepared.text_columns, find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True
    )


def to_dates(name: str | None = "day (date)", date_format: str | None = None) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "set_type", "column": "day", "type": "datetime"}
    if name is not None:
        operation["name"] = name
    if date_format is not None:
        operation["date_format"] = date_format
    return operation


def keep(test: str, value: str, name: str = "t") -> dict[str, Any]:
    return {"op": "keep_rows", "where": [{"column": name, "test": test, "value": value}]}


class TestPaste:
    @pytest.mark.parametrize("offset", ["+01:00", "-05:00", "Z", "+05:30", "-00:00"])
    def test_the_column_stays_as_written_with_a_note_that_names_its_shape(self, offset: str) -> None:
        parsed = parse_dataset(table(offset))

        assert parsed.column_dtypes["day"] == "text"
        assert parsed.csv.splitlines()[1] == f"2026-03-01{offset},12"
        assert NOTE in parsed.warnings

    @pytest.mark.parametrize("offset", ["-03", "+01", "-0500", "+0100", "-05:00:00"])
    def test_a_sign_and_digits_in_no_offset_form_get_no_offset_note(self, offset: str) -> None:
        """`2026-03-01-03` may be an hour label: no sentence calls it an offset; the column is text as before."""
        parsed = parse_dataset(table(offset))

        assert parsed.column_dtypes["day"] == "text"
        assert not any("offset" in warning for warning in parsed.warnings)

    def test_a_column_that_mixes_the_shape_with_plain_dates_stays_text_without_the_note(self) -> None:
        """Decided by the existing rule: a column of one ISO date shape types; any other cell keeps it text."""
        parsed = parse_dataset("day,kWh\n2026-03-01,12\n2026-03-02+01:00,15\n")

        assert parsed.column_dtypes["day"] == "text"
        assert not any("offset" in warning for warning in parsed.warnings)

    def test_an_impossible_day_gets_no_note(self) -> None:
        parsed = parse_dataset("day,kWh\n2026-02-30+01:00,12\n2026-03-02+01:00,15\n")

        assert parsed.column_dtypes["day"] == "text"
        assert NOTE not in parsed.warnings

    @pytest.mark.parametrize(
        ("cell", "canonical"),
        [
            ("2026-03-01T10:00+01:00", "2026-03-01T10:00:00+01:00"),
            ("2026-03-01 10:00-05:00", "2026-03-01T10:00:00-05:00"),
            ("2026-03-01T10:00:00Z", "2026-03-01T10:00:00+00:00"),
            ("2026-03-01", "2026-03-01"),
        ],
    )
    def test_dates_and_times_with_an_offset_read_as_before(self, cell: str, canonical: str) -> None:
        parsed = parse_dataset(f"t,v\n{cell},1\n")

        assert parsed.column_dtypes["t"] == "datetime"
        assert parsed.csv.splitlines()[1] == f"{canonical},1"
        assert not any("kept as text" in warning for warning in parsed.warnings)


class TestConversion:
    @pytest.mark.parametrize("date_format", [None, "YYYY-MM-DD"])
    def test_the_written_days_go_into_a_new_column_and_the_dropped_offsets_are_counted(
        self, date_format: str | None
    ) -> None:
        prepared = prepare(table("-05:00"), to_dates(date_format=date_format))

        assert column(prepared, "day (date)") == ["2026-03-01", "2026-03-02", "2026-03-03"]
        assert column(prepared, "day") == ["2026-03-01-05:00", "2026-03-02-05:00", "2026-03-03-05:00"]
        [line] = prepared.changes
        assert line.startswith("new column day (date): 3 cells of day read as dates (")
        assert line.endswith(
            "; day stays as it is, 3 dates had the UTC offset -05:00, which was dropped; the days are as written"
        )
        again = reparse(prepared)
        assert again.column_dtypes["day (date)"] == "datetime" and again.column_dtypes["day"] == "text"

    @pytest.mark.parametrize("offset", ["+01:00", "Z"])
    def test_offsets_east_of_utc_and_z_read_the_same_way(self, offset: str) -> None:
        prepared = prepare(table(offset), to_dates())

        assert column(prepared, "day (date)") == ["2026-03-01", "2026-03-02", "2026-03-03"]
        assert prepared.changes[0].endswith(
            f"3 dates had the UTC offset {offset}, which was dropped; the days are as written"
        )

    def test_one_date_is_said_in_the_singular(self) -> None:
        prepared = prepare("day,kWh\n2026-03-01+01:00,1\n", to_dates())

        assert prepared.changes[0].endswith(
            "1 date had the UTC offset +01:00, which was dropped; the day is as written"
        )

    def test_several_offsets_are_each_counted(self) -> None:
        text = "day,kWh\n2026-03-01+01:00,1\n2026-03-02-05:00,2\n2026-03-03+01:00,3\n"

        prepared = prepare(text, to_dates())

        assert column(prepared, "day (date)") == ["2026-03-01", "2026-03-02", "2026-03-03"]
        assert prepared.changes[0].endswith(
            "3 dates had the UTC offsets -05:00 (1) and +01:00 (2), which were dropped; the days are as written"
        )

    def test_the_count_and_the_step_survive_the_line_cap_with_many_offsets(self) -> None:
        """Offsets past what the line holds are summed up, so the line still names its step, the count and the span."""
        offsets = [f"{sign}{hours:02d}:{minutes:02d}" for sign in "+-" for hours in range(1, 12) for minutes in (0, 30)]
        text = "day,kWh\n" + "".join(
            f"2026-03-{1 + index % 28:02d}{off},{index}\n" for index, off in enumerate(offsets)
        )

        [line] = prepare(text, to_dates()).changes

        assert len(line) <= MAX_NOTE_CHARS
        assert line.startswith("new column day (date): 44 cells of day read as dates (")
        assert line.endswith(
            "44 dates had 44 different UTC offsets, from -11:30 to +11:30, which were dropped; the days are as written"
        )

    def test_a_column_that_mixes_the_shape_with_plain_dates_reads_every_day(self) -> None:
        prepared = prepare("day,kWh\n2026-03-01,12\n2026-03-02+01:00,15\n", to_dates())

        assert column(prepared, "day (date)") == ["2026-03-01", "2026-03-02"]
        assert prepared.changes[0].endswith(
            "1 date had the UTC offset +01:00, which was dropped; the day is as written"
        )

    @pytest.mark.parametrize("timed", ["2026-03-02T10:00+01:00", "2026-03-02 10:00"])
    def test_beside_times_the_column_stays_as_it_is(self, timed: str) -> None:
        """A date with an offset names a day, not a moment: no midnight is made up for it, at any offset."""
        code, message = refusal(f"day,kWh\n2026-03-01+01:00,12\n{timed},15\n", to_dates())

        assert code == "type_mismatch"
        assert message == (
            "column 'day' holds dates with a UTC offset and no time beside times; such a date names a day, not a "
            "moment, so the column stays as it is"
        )

    @pytest.mark.parametrize("offset", ["-03", "+01", "-0500", "+0100", "-05:00:00"])
    @pytest.mark.parametrize("date_format", [None, "YYYY-MM-DD"])
    def test_a_sign_and_digits_in_no_offset_form_are_refused(self, offset: str, date_format: str | None) -> None:
        assert refusal(table(offset), to_dates(date_format=date_format)) == ("type_mismatch", SIGN_REFUSAL)

    def test_one_such_cell_among_plain_dates_refuses_the_column(self) -> None:
        text = "day,kWh\n" + "".join(f"2026-03-{day:02d},{day}\n" for day in range(1, 20)) + "2026-03-20-03,20\n"

        assert refusal(text, to_dates()) == ("type_mismatch", SIGN_REFUSAL)

    def test_hour_labels_never_collapse_into_equal_dates(self) -> None:
        """The fourth defect: `-00` to `-03` were read as midnight to 03:00 and written as one date four times."""
        text = "day,kWh\n2026-03-01-00,1\n2026-03-01-01,2\n2026-03-01-02,3\n2026-03-01-03,4\n"

        assert refusal(text, to_dates()) == ("type_mismatch", SIGN_REFUSAL)

    def test_a_conversion_in_place_counts_the_dropped_offsets_too(self) -> None:
        prepared = prepare(table("+01:00"), to_dates(name=None))

        assert column(prepared, "day") == ["2026-03-01", "2026-03-02", "2026-03-03"]
        assert prepared.changes[0].endswith(
            "3 dates had the UTC offset +01:00, which was dropped; the days are as written"
        )

    @pytest.mark.parametrize(
        ("cell", "canonical"),
        [("2026-03-01T10:00:00+01:00", "2026-03-01T10:00:00+01:00"), ("2026-03-01", "2026-03-01")],
    )
    def test_times_with_an_offset_and_plain_dates_convert_as_before(self, cell: str, canonical: str) -> None:
        parsed = parse_dataset(f"day,kWh\n{cell},1\n{cell},2\n", text_columns=["day"])

        prepared = apply_operations(parsed, OPERATIONS.validate_python([to_dates()]))

        assert column(prepared, "day (date)") == [canonical, canonical]
        assert "offset" not in prepared.changes[0]

    def test_a_text_operation_keeps_such_cells_as_text(self) -> None:
        """A `strip` that leaves dates with an offset types its new column as text: only a request drops the offset."""
        text = "day,kWh\n2026-03-01-05:00 h,12\n2026-03-02-05:00 h,15\n"

        prepared = prepare(text, {"op": "strip", "column": "day", "suffix": " h", "name": "clean"})

        assert column(prepared, "clean") == ["2026-03-01-05:00", "2026-03-02-05:00"]
        assert "clean" in prepared.text_columns
        assert OFFSET_DAYS_READING in prepared.changes[0]

    def test_a_text_operation_never_reads_hour_labels_as_dates(self) -> None:
        text = "day,kWh\n2026-03-01-00 h,1\n2026-03-01-01 h,2\n"

        prepared = prepare(text, {"op": "strip", "column": "day", "suffix": " h", "name": "clean"})

        assert column(prepared, "clean") == ["2026-03-01-00", "2026-03-01-01"]
        assert "clean" in prepared.text_columns


class TestOpenRole:
    def test_the_conversion_is_proposed_never_certain(self) -> None:
        parsed = parse_dataset(table("-05:00"))

        [candidate] = candidates(default_bindings(ROLLING, parsed.profile), ROLLING, parsed.profile, parsed)

        assert isinstance(candidate, Candidate) and not candidate.certain
        assert candidate.dry.read == candidate.dry.present == 3
        guess = "uncertain: the reading guesses the days of 3 dates with a UTC offset as written, the offset dropped"
        assert guess in candidate.line()
        assert candidate.operations() == [{"op": "set_type", "column": "day", "type": "datetime", "name": "day (date)"}]

    @pytest.mark.parametrize("offset", ["+01:00", "Z"])
    def test_offsets_that_failed_to_read_are_proposed_too(self, offset: str) -> None:
        dry = dry_run(read_frame(parse_dataset(table(offset))), "day", "datetime")

        assert dry is not None and dry.read == 3 and not dry.certain

    @pytest.mark.parametrize("offset", ["-00", "-03", "-0500"])
    def test_a_sign_and_digits_in_no_offset_form_are_no_candidate(self, offset: str) -> None:
        assert dry_run(read_frame(parse_dataset(table(offset))), "day", "datetime") is None


class TestFilterBound:
    NAIVE = "t,v\n2026-02-28T23:00:00,1\n2026-03-01T00:00:00,2\n2026-03-01T10:00:00,3\n2026-03-02T00:00:00,4\n"
    """Times without an offset, two of them on 1 March: a bound that names a day must take or leave both."""
    ZONED = (
        "t,v\n2026-02-28T23:30:00+01:00,1\n2026-03-01T00:30:00+01:00,2\n2026-03-01T23:30:00+01:00,3\n"
        "2026-03-02T00:30:00+01:00,4\n"
    )

    @pytest.mark.parametrize(
        ("test", "value", "kept"),
        [
            ("ge", "2026-03-01+01:00", ["2", "3", "4"]),
            ("ge", "2026-03-01-05:00", ["2", "3", "4"]),
            ("lt", "2026-03-01Z", ["1"]),
            ("le", "2026-03-01-05:00", ["1", "2", "3"]),
            ("le", "2026-03-01+01:00", ["1", "2", "3"]),
            ("gt", "2026-03-01Z", ["4"]),
            ("gt", "2026-03-01+01:00", ["4"]),
        ],
    )
    def test_on_times_without_an_offset_the_bound_is_the_written_day(
        self, test: str, value: str, kept: list[str]
    ) -> None:
        assert column(prepare(self.NAIVE, keep(test, value)), "v") == kept

    @pytest.mark.parametrize(("test", "kept"), [("ge", ["2", "3", "4"]), ("le", ["1", "2", "3"]), ("gt", ["4"])])
    def test_a_plain_date_is_the_whole_day_as_before(self, test: str, kept: list[str]) -> None:
        assert column(prepare(self.NAIVE, keep(test, "2026-03-01")), "v") == kept

    @pytest.mark.parametrize(
        ("test", "value", "kept"),
        [
            ("ge", "2026-03-01+01:00", ["2", "3", "4"]),
            ("le", "2026-03-01+01:00", ["1", "2", "3"]),
            ("gt", "2026-03-01+01:00", ["4"]),
            # 1 March at -05:00 runs from 06:00 to 06:00 the next day at +01:00.
            ("ge", "2026-03-01-05:00", ["3", "4"]),
            ("le", "2026-03-01-05:00", ["1", "2", "3", "4"]),
        ],
    )
    def test_on_times_with_an_offset_the_bound_is_the_day_at_its_offset(
        self, test: str, value: str, kept: list[str]
    ) -> None:
        assert column(prepare(self.ZONED, keep(test, value)), "v") == kept

    def test_a_bound_on_the_converted_column_takes_the_day_as_written(self) -> None:
        """The flow of the defect: the pasted days converted, then "from 1 March" with the value as pasted."""
        prepared = prepare(table("+01:00"), to_dates(), keep("ge", "2026-03-01+01:00", "day (date)"))

        assert column(prepared, "kWh") == ["12", "15", "11"]

    @pytest.mark.parametrize("value", ["2026-03-01-03", "2026-03-01+0100", "2026-03-01-05:00:00"])
    @pytest.mark.parametrize("zoned", [False, True])
    def test_a_sign_and_digits_in_no_offset_form_are_refused(self, value: str, zoned: bool) -> None:
        code, message = refusal(self.ZONED if zoned else self.NAIVE, keep("ge", value))

        assert code == "invalid_operation"
        assert message == (
            "the value for column 't' is a date followed directly by a sign and digits in no UTC offset form, which "
            "may be an hour as well as an offset: give the date alone (YYYY-MM-DD), a time (YYYY-MM-DDTHH:MM) or the "
            "offset in the form YYYY-MM-DD±HH:MM"
        )

    @pytest.mark.parametrize(
        ("value", "kept"), [("2026-03-01T10:00:00+01:00", ["3", "4"]), ("2026-02-28T23:00:00Z", ["2", "3", "4"])]
    )
    def test_a_time_with_an_offset_compares_moments_as_before(self, value: str, kept: list[str]) -> None:
        assert column(prepare(self.ZONED, keep("ge", value)), "v") == kept

    @pytest.mark.parametrize("value", ["2026-03-01+01:00", "2026-03-01Z", "2026-03-01-03", "2026-03-01-05:00:00"])
    def test_a_column_of_period_labels_still_refuses_the_shapes(self, value: str) -> None:
        """Month labels compare as text, as an `aggregate` writes them: a date-shaped bound is refused there."""
        labels = parse_dataset("month,v\n2026-02,1\n2026-03,2\n", text_columns=["month"])

        with pytest.raises(PrepareError) as caught:
            apply_operations(labels, OPERATIONS.validate_python([keep("ge", value, "month")]))

        assert caught.value.code == "invalid_operation"
        assert caught.value.message == (
            "column 'month' holds text labels YYYY-MM, such as 2024-03, which compare as text: give the value in that "
            "form, not as a date"
        )
