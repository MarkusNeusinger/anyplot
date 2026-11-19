"""The forms a text column reads as dates in: a short list, read by the parser's readers at the paste and in a
conversion without a format alike.

The list is what the paste types as dates: an ISO date (`2026-03-01`), also with a time after `T` or a space, seconds,
a fraction and a UTC offset of −12:00 to +14:00; `01.03.2026` and `1.3.2026`, also with a time; `03/15/2026` or
`15/03/2026`, the order of day and month decided once for the column (day first when no cell settles it, named as a
guess); and a month, `2026-03` or a month name with a four-digit year (`Mar 2026`, `März 2026`), as its first day.
A `set_type` to dates without a format (`prepare._date_conversion`), its dry run and a text operation's new column read
exactly these, with the same code: any other cell is unreadable there, and an explicit `date_format` reads a form
outside the list on request.

`LISTED` pins what the list reads, in the conversion and at the paste, as it read before the list; `UNLISTED` and
`DEFECTS` are forms the conversion read through pandas' general reader before and reads no more, among them the forms
that reader got wrong (a range of days, a time range read as an offset of −17:00, hour labels collapsed into one day).
"""

import csv
import io
from dataclasses import dataclass, field
from typing import Any

import dateutil.parser
import pandas as pd
import pytest
from pydantic import TypeAdapter

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import Operation, PrepareError, _cell_text, _date_conversion, apply_operations


OPERATIONS = TypeAdapter(list[Operation])
FORMS = (
    "the chat reads 2026-03-01, 01.03.2026, 03/15/2026, each also with a time, and months such as 2026-03 or Mar 2026"
)


@dataclass(frozen=True)
class Row:
    """A column of `cells` read as dates: the conversion's cells as `data.csv` writes them (None for a missing one),
    whether it writes them with a time, its guess and notice, and the paste's cells and notes for the column."""

    cells: list[str | None]
    values: list[str | None]
    with_time: bool = False
    pasted: list[str] | None = None
    """The paste's cells, when they differ from the conversion's (a fraction keeps its digits as written there)."""
    notes: list[str] = field(default_factory=list)
    guess: str | None = None
    notice: str = ""


def converted(cells: list[str | None]) -> dict[str, Any]:
    conversion = _date_conversion(pd.Series(cells, dtype="str", name="d"), None)
    return {
        "values": [_cell_text(value, conversion.with_time) for value in conversion.values],
        "failed": conversion.failed,
        "with_time": conversion.with_time,
        "guess": conversion.guess,
        "notice": conversion.notice,
    }


def pasted(cells: list[str | None]) -> tuple[str, list[str], list[str]]:
    """The paste of a column `d` of `cells` beside a column of row numbers: its dtype, its cells, its notes. The
    column comes first, under its name or the one a unit gave it (`2026 of` is 2026 in `d (of)`)."""
    text = io.StringIO()
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(["d", "n"])
    writer.writerows(["" if cell is None else cell, index] for index, cell in enumerate(cells))
    parsed = parse_dataset(text.getvalue())
    rows = list(csv.reader(io.StringIO(parsed.csv)))
    notes = [warning for warning in parsed.warnings if warning.startswith("column 'd'")]
    return parsed.column_dtypes[rows[0][0]], [row[0] for row in rows[1:]], notes


LISTED: dict[str, Row] = {
    "iso_date": Row(["2026-03-01", "2026-03-02", "2026-12-31"], ["2026-03-01", "2026-03-02", "2026-12-31"]),
    "iso_t_minutes": Row(
        ["2026-03-01T10:00", "2026-03-02T11:30"], ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], with_time=True
    ),
    "iso_space_minutes": Row(
        ["2026-03-01 10:00", "2026-03-02 11:30"], ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], with_time=True
    ),
    "iso_seconds": Row(
        ["2026-03-01T10:00:00", "2026-03-02T11:30:15"], ["2026-03-01T10:00:00", "2026-03-02T11:30:15"], with_time=True
    ),
    "iso_fraction": Row(
        ["2026-03-01T10:00:00.123", "2026-03-02T11:30:15.5"],
        ["2026-03-01T10:00:00.123000", "2026-03-02T11:30:15.500000"],
        with_time=True,
        pasted=["2026-03-01T10:00:00.123", "2026-03-02T11:30:15.500"],
    ),
    "iso_fraction_comma": Row(
        ["2026-03-01T10:00:00,25", "2026-03-02T11:30:15,5"],
        ["2026-03-01T10:00:00.250000", "2026-03-02T11:30:15.500000"],
        with_time=True,
        pasted=["2026-03-01T10:00:00.25", "2026-03-02T11:30:15.50"],
    ),
    "iso_nanoseconds": Row(
        ["2026-03-01T10:00:00.123456789", "2026-03-02T11:30:15.000000001"],
        ["2026-03-01T10:00:00.123456789", "2026-03-02T11:30:15.000000001"],
        with_time=True,
    ),
    "iso_z": Row(
        ["2026-03-01T10:00:00Z", "2026-03-02T11:30Z"],
        ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:00+00:00"],
        with_time=True,
    ),
    "iso_offset": Row(
        ["2026-03-01T10:00+01:00", "2026-03-02 11:30:00+01:00"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        with_time=True,
    ),
    "iso_offset_compact": Row(
        ["2026-03-01T10:00+0100", "2026-03-02T11:30+0100"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        with_time=True,
    ),
    "iso_offset_hours": Row(
        ["2026-03-01T10:00+01", "2026-03-02T11:30+01"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        with_time=True,
    ),
    "iso_offset_west_edge": Row(
        ["2026-03-01T10:00-12:00", "2026-03-02T10:00-12:00"],
        ["2026-03-01T10:00:00-12:00", "2026-03-02T10:00:00-12:00"],
        with_time=True,
    ),
    "iso_offset_east_edge": Row(
        ["2026-03-01T10:00+14:00", "2026-03-02T10:00+14:00"],
        ["2026-03-01T10:00:00+14:00", "2026-03-02T10:00:00+14:00"],
        with_time=True,
    ),
    "iso_offsets_mixed": Row(
        ["2026-03-01T10:00+01:00", "2026-07-01T10:00+02:00"],
        ["2026-03-01T09:00:00+00:00", "2026-07-01T08:00:00+00:00"],
        with_time=True,
        notes=[
            "column 'd': times with the UTC offsets +01:00, +02:00 written in UTC (+00:00); the instants are the same"
        ],
        notice="times with the UTC offsets +01:00, +02:00 converted to UTC (+00:00); the instants are the same",
    ),
    "iso_fraction_offset": Row(
        ["2026-03-01T10:00:00.5+01:00", "2026-03-02T11:30:00.25+01:00"],
        ["2026-03-01T10:00:00.500000+01:00", "2026-03-02T11:30:00.250000+01:00"],
        with_time=True,
        pasted=["2026-03-01T10:00:00.50+01:00", "2026-03-02T11:30:00.25+01:00"],
    ),
    "iso_some_with_time": Row(
        ["2026-03-01", "2026-03-02T10:00"], ["2026-03-01T00:00:00", "2026-03-02T10:00:00"], with_time=True
    ),
    "iso_missing_cell": Row(
        ["2026-03-01", None, "2026-03-03"], ["2026-03-01", None, "2026-03-03"], pasted=["2026-03-01", "", "2026-03-03"]
    ),
    "iso_far_years": Row(["0001-01-01", "9999-12-31"], ["0001-01-01", "9999-12-31"]),
    "dot": Row(["01.03.2026", "15.03.2026"], ["2026-03-01", "2026-03-15"]),
    "dot_short": Row(["1.3.2026", "15.3.2026"], ["2026-03-01", "2026-03-15"]),
    "dot_time": Row(
        ["01.03.2026 10:00", "15.03.2026 9:05"], ["2026-03-01T10:00:00", "2026-03-15T09:05:00"], with_time=True
    ),
    "dot_seconds": Row(
        ["01.03.2026 10:00:15", "15.03.2026 11:30:00"], ["2026-03-01T10:00:15", "2026-03-15T11:30:00"], with_time=True
    ),
    "slash_day_first": Row(["01/03/2026", "15/03/2026"], ["2026-03-01", "2026-03-15"]),
    "slash_month_first": Row(["03/15/2026", "03/16/2026"], ["2026-03-15", "2026-03-16"]),
    "slash_ambiguous": Row(
        ["01/03/2026", "02/03/2026"],
        ["2026-03-01", "2026-03-02"],
        notes=["column 'd': day and month order is ambiguous; read as DD/MM/YYYY"],
        guess="the day and month order",
    ),
    "slash_day_equals_month": Row(["01/01/2026", "02/02/2026"], ["2026-01-01", "2026-02-02"]),
    "slash_time": Row(
        ["15/03/2026 10:00", "16/03/2026 9:05:30"], ["2026-03-15T10:00:00", "2026-03-16T09:05:30"], with_time=True
    ),
    "slash_month_first_time": Row(
        ["03/15/2026 10:00", "03/16/2026 9:05"], ["2026-03-15T10:00:00", "2026-03-16T09:05:00"], with_time=True
    ),
    "slash_short": Row(["1/3/2026", "15/3/2026"], ["2026-03-01", "2026-03-15"]),
    "year_month": Row(
        ["2026-03", "2026-04"],
        ["2026-03-01", "2026-04-01"],
        notes=["column 'd': 2 cells read as months (YYYY-MM, each as the first day of the month)"],
    ),
    "month_en": Row(["Mar 2026", "Apr 2026"], ["2026-03-01", "2026-04-01"]),
    "month_en_long": Row(["March 2026", "April 2026"], ["2026-03-01", "2026-04-01"]),
    "month_de": Row(["März 2026", "Okt. 2026"], ["2026-03-01", "2026-10-01"]),
    "month_fr": Row(["févr. 2026", "mars 2026"], ["2026-02-01", "2026-03-01"]),
    "month_es": Row(["marzo 2026", "abril 2026"], ["2026-03-01", "2026-04-01"]),
    "month_it": Row(["marzo 2026", "aprile 2026"], ["2026-03-01", "2026-04-01"]),
    "month_pt": Row(["março 2026", "abril 2026"], ["2026-03-01", "2026-04-01"]),
    "month_nl": Row(["maart 2026", "mei 2026"], ["2026-03-01", "2026-05-01"]),
    "month_pl": Row(["marzec 2026", "maja 2026"], ["2026-03-01", "2026-05-01"]),
    "month_ru": Row(["март 2026", "мая 2026"], ["2026-03-01", "2026-05-01"]),
    "month_zh": Row(["2026年3月", "2026年5月"], ["2026-03-01", "2026-05-01"]),
    "month_vi": Row(["tháng 3 năm 2026", "tháng 5 năm 2026"], ["2026-03-01", "2026-05-01"]),
    "month_year_first": Row(["2026 Nov", "2026 Dec"], ["2026-11-01", "2026-12-01"]),
    "month_dash": Row(["Nov-2026", "Dec-2026"], ["2026-11-01", "2026-12-01"]),
}
MONTH_NAMES = "column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"


def _notes(name: str, row: Row) -> list[str]:
    return [MONTH_NAMES] if name.startswith("month_") else row.notes


@pytest.mark.parametrize("name", list(LISTED))
def test_a_listed_form_converts_as_before(name: str) -> None:
    row = LISTED[name]

    assert converted(row.cells) == {
        "values": row.values,
        "failed": 0,
        "with_time": row.with_time,
        "guess": row.guess,
        "notice": row.notice,
    }


@pytest.mark.parametrize("name", list(LISTED))
def test_a_listed_form_is_typed_at_the_paste_as_before(name: str) -> None:
    row = LISTED[name]

    assert pasted(row.cells) == ("datetime", row.pasted or row.values, _notes(name, row))


UNLISTED: dict[str, tuple[list[str], str]] = {
    "two_digit_year": (["01.03.26", "15.03.26"], "text"),
    "am_pm": (["3/15/2026 10:00 AM", "3/16/2026 2:30 PM"], "text"),
    "year_slash": (["2026/03/01", "2026/03/15"], "text"),
    "dashes_day_first": (["15-03-2026", "16-03-2026"], "text"),
    "day_month_name": (["1 March 2026", "15 March 2026"], "text"),
    "day_short_month_name": (["8 Nov 2026", "9 Nov 2026"], "text"),
    "german_day_month_name": (["1. März 2026", "15. März 2026"], "text"),
    "month_name_day": (["March 1, 2026", "March 15, 2026"], "text"),
    "day_dashes_month_name": (["01-Mar-2026", "15-Mar-2026"], "text"),
    "compact": (["20260301", "20260315"], "integer"),
    "program_timestamp": (["Sun Mar 1 10:00:00 2026", "Mon Mar 2 11:00:00 2026"], "text"),
    "hour_without_minutes": (["2026-03-01T10", "2026-03-02T11"], "text"),
    "lowercase_t": (["2026-03-01t10:00", "2026-03-02t11:30"], "text"),
    "years": (["2025", "2026"], "integer"),
    "quarters": (["2026-Q1", "2026-Q2"], "text"),
}
"""Forms outside the list, with the paste's dtype for them: each read as dates through pandas' general reader before."""

DEFECTS: dict[str, list[str]] = {
    "range_of_days": ["2026-03-01-2026-03-05", "2026-03-06-2026-03-10"],
    "hour_labels": ["2026-03-01T00", "2026-03-01T01", "2026-03-01T02", "2026-03-01T03"],
    "space_before_offset": ["2026-03-01 -05:00", "2026-03-02 -05:00"],
    "year_slash_offset": ["2026/03/01-05:00", "2026/03/02-05:00"],
    "dot_offset": ["13.03.2026-05:00", "14.03.2026-05:00"],
    "slash_after_date": ["2026-03-01/05", "2026-03-02/05"],
    "time_range": ["2026-03-01 9:00-17:00", "2026-03-02 9:00-17:00"],
    "time_range_padded": ["2026-03-01 08:00-16:30", "2026-03-02 08:00-16:30"],
    "word_after_date": ["2026-03-01 of", "2026-03-02 of"],
    "word_after_time": ["2026-03-01 10:00 of", "2026-03-02 10:00 of"],
    "month_time_slash": ["2026-03 10:00 / 05", "2026-04 10:00 / 05"],
    "month_label": ["2026-02 February", "2026-03 March"],
    "compact_date": ["20260301", "20260302"],
    "three_small_numbers": ["1.2.3", "1.2.4"],
}
"""Cells the general reader made a date of that was no reading of them: the second date of a range dropped, `-17:00`
taken for an offset, `T00` to `T03` four times the same day, `-05:00` after a space read as 05:00, a word dropped."""


@pytest.mark.parametrize("name", list(UNLISTED))
def test_a_form_outside_the_list_is_unreadable_without_a_format(name: str) -> None:
    cells, _ = UNLISTED[name]

    reading = converted(list(cells))

    assert reading["values"] == [None] * len(cells) and reading["failed"] == len(cells)


@pytest.mark.parametrize("name", list(UNLISTED))
def test_the_paste_keeps_a_form_outside_the_list_as_before(name: str) -> None:
    cells, dtype = UNLISTED[name]

    assert pasted(list(cells))[0] == dtype


@pytest.mark.parametrize("name", list(DEFECTS))
def test_a_defect_form_is_unreadable_without_a_format(name: str) -> None:
    cells = DEFECTS[name]

    reading = converted(list(cells))

    assert reading["values"] == [None] * len(cells) and reading["failed"] == len(cells)


@pytest.mark.parametrize("name", list(DEFECTS))
def test_the_paste_never_types_a_defect_form(name: str) -> None:
    assert pasted(list(DEFECTS[name]))[0] != "datetime"


class TestOneOrderPerColumn:
    """The order of day and month is the column's, as at the paste: never chosen cell by cell."""

    def test_a_cell_of_another_shape_is_unreadable_and_the_order_holds_for_the_rest(self) -> None:
        """`03-01-2026` is no listed form; `03/15/2026` settles month first for the slash cells."""
        reading = converted(["03/15/2026", "03-01-2026", "03/02/2026"])

        assert reading["values"] == ["2026-03-15", None, "2026-03-02"] and reading["failed"] == 1
        assert pasted(["03/15/2026", "03-01-2026", "03/02/2026"])[0] == "text"

    def test_a_time_in_one_cell_keeps_the_column_month_first(self) -> None:
        reading = converted(["03/15/2026", "03/01/2026 10:00", "03/02/2026"])

        assert reading["values"] == ["2026-03-15T00:00:00", "2026-03-01T10:00:00", "2026-03-02T00:00:00"]
        assert reading["failed"] == 0 and reading["guess"] is None
        assert pasted(["03/15/2026", "03/01/2026 10:00", "03/02/2026"])[1] == reading["values"]

    def test_cells_that_settle_both_orders_leave_no_slash_cell_readable(self) -> None:
        """The paste's rule: a column with a first part over 12 and a second part over 12 is no slash date column."""
        reading = converted(["15/03/2026", "03/15/2026", "01/02/2026"])

        assert reading["values"] == [None, None, None] and reading["failed"] == 3
        assert pasted(["15/03/2026", "03/15/2026", "01/02/2026"])[0] == "text"

    def test_dot_dates_are_day_first_without_a_guess_as_at_the_paste(self) -> None:
        reading = converted(["01.03.2026", "02.03.2026"])

        assert reading["values"] == ["2026-03-01", "2026-03-02"] and reading["guess"] is None
        assert pasted(["01.03.2026", "02.03.2026"]) == ("datetime", ["2026-03-01", "2026-03-02"], [])


class TestOneShapePerColumn:
    def test_cells_of_another_listed_shape_are_unreadable(self) -> None:
        """A column has one shape, the one most of its cells have; the paste keeps such a mix as text."""
        cells = ["2026-03-01", "2026-03-02", "2026-03-03", "04.03.2026"]

        reading = converted(cells)

        assert reading["values"] == ["2026-03-01", "2026-03-02", "2026-03-03", None] and reading["failed"] == 1
        assert pasted(cells)[0] == "text"

    def test_a_tie_takes_the_shape_the_paste_tries_first(self) -> None:
        reading = converted(["01.03.2026", "2026-03-02"])

        assert reading["values"] == [None, "2026-03-02"]

    def test_a_month_beside_a_day_is_unreadable(self) -> None:
        reading = converted(["2026-03-01", "2026-03-02", "2026-04"])

        assert reading["values"] == ["2026-03-01", "2026-03-02", None]


class TestOffsetsInUse:
    """A UTC offset counts from −12:00 to +14:00: past them, the sign and digits after a time end a range."""

    @pytest.mark.parametrize("offset", ["-12:30", "+14:30", "-16:30", "+23:00"])
    def test_a_time_with_an_offset_past_those_in_use_is_unreadable(self, offset: str) -> None:
        cells = [f"2026-03-01T08:00{offset}", f"2026-03-02T08:00{offset}"]

        assert converted(cells)["failed"] == 2
        assert pasted(cells)[0] == "text"


class TestNoGeneralReader:
    def test_a_conversion_without_a_format_never_calls_pandas_or_dateutil_to_read(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The list is read by the parser's readers alone: no cell reaches a reader that guesses its format."""

        def refuse(*args: object, **kwargs: object) -> None:
            raise AssertionError("a general date reader was called")

        monkeypatch.setattr(pd, "to_datetime", refuse)
        monkeypatch.setattr(dateutil.parser, "parse", refuse)
        columns = [row.cells for row in LISTED.values()] + [list(cells) for cells, _ in UNLISTED.values()]
        for cells in [*columns, *(list(cells) for cells in DEFECTS.values())]:
            _date_conversion(pd.Series(cells, dtype="str", name="d"), None)


DATES = [
    "2026-03-01",
    "2026-3-1",
    "2026/03/01",
    "01.03.2026",
    "1.3.2026",
    "01/03/2026",
    "03/15/2026",
    "15/03/2026",
    "01-03-2026",
    "01.03.26",
    "1 March 2026",
    "Mar 2026",
    "März 2026",
    "2026-03",
    "2026",
    "2026-Q1",
    "20260301",
]
TIMES = ["", "T10:00", " 10:00", "T10:00:00", " 10:00:00.5", "T10:00Z", " 10:00+01:00", "T08:00-16:30", "T10", " 10"]
TIMES += [" 9:05", " 10:00 PM", "t10:00"]
TRAILING = ["", " of", "-05:00", "/05", "+01:00"]
GENERATED = [date + time + trailing for date in DATES for time in TIMES for trailing in TRAILING]


@pytest.mark.parametrize("trailing", TRAILING)
def test_the_conversion_reads_a_cell_exactly_when_the_paste_types_it(trailing: str) -> None:
    """One reader for both: a cell the paste types converts to the same moment, and one it keeps reads as no date.

    A date followed directly by a UTC offset and no time (`2026-03-01-05:00`) is the one shape the two treat apart on
    purpose: the paste keeps it as written, and a request reads its day, the offset dropped."""
    for cell in (date + time + trailing for date in DATES for time in TIMES):
        dtype, cells, _ = pasted([cell])
        try:
            reading = converted([cell])
        except PrepareError:
            reading = {"values": [None]}
        [value] = reading["values"]
        if dtype == "datetime":
            assert value is not None and pd.Timestamp(value) == pd.Timestamp(cells[0]), cell
        elif trailing in ("-05:00", "+01:00") and cell == f"2026-03-01{trailing}":
            assert value == "2026-03-01", cell
        else:
            assert value is None, cell


class TestMessages:
    def test_a_refused_conversion_names_the_forms_the_chat_reads(self) -> None:
        text = "day,kWh\n" + "".join(f"{day} March 2026,{day}\n" for day in range(1, 13))

        with pytest.raises(PrepareError) as caught:
            apply_operations(
                parse_dataset(text),
                OPERATIONS.validate_python([{"op": "set_type", "column": "day", "type": "datetime"}]),
            )

        assert caught.value.code == "type_mismatch"
        assert caught.value.message == f"column 'day': 12 of 12 cells cannot be read as dates; {FORMS}"

    def test_cells_left_unread_name_the_forms_too(self) -> None:
        text = "day,kWh\n" + "".join(f"2026-03-{day:02d},{day}\n" for day in range(1, 11)) + "1 March 2026,11\n"
        operation = {"op": "set_type", "column": "day", "type": "datetime", "name": "day (date)"}

        [line] = apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).changes

        assert line == (
            "new column day (date): 10 cells of day read as dates (format inferred, year first), 1 cell could not be "
            f"read and is now missing; {FORMS}; day stays as it is"
        )

    def test_a_format_names_no_forms(self) -> None:
        text = "day,kWh\n" + "".join(f"{day} March 2026,{day}\n" for day in range(1, 13))
        operation = {"op": "set_type", "column": "day", "type": "datetime", "date_format": "DD.MM.YYYY"}

        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

        assert caught.value.message == "column 'day': 12 of 12 cells cannot be read as dates"
