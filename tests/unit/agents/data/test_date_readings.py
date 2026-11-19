"""The forms a text column reads as dates in: a short list, read by the parser's readers at the paste and in a
conversion without a format alike.

The list is what the paste types as dates: an ISO date (`2026-03-01`), also with a time after `T` (or `t`) or a space,
seconds, a fraction and a UTC offset of −12:00 to +14:00; `01.03.2026` and `1.3.2026`, also with a time; `03/15/2026`
or `15/03/2026`, the order of day and month decided once for the column (day first when no cell settles it, named as a
guess, in a column of slash dates; beside other forms only an order its slash dates settle); a day with a month name and a four-digit year (`8 Nov 2026`, `1. März 2026`, `March 1, 2026`), also with a
time; and a month, `2026-03` or a month name with a four-digit year (`Mar 2026`, `März 2026`), as its first day.
A `set_type` to dates without a format (`prepare._date_conversion`), its dry run and a text operation's new column read
exactly these, with the same code: any other cell is unreadable there, and an explicit `date_format` reads a form
outside the list on request.

`LISTED` pins what the list reads, in the conversion and at the paste, as it read before the list; `ADDED` the forms the
list took in later, which the paste types now; `UNLISTED` and `DEFECTS` are forms the conversion read through pandas'
general reader before and reads no more, among them the forms that reader got wrong (a range of days, a time range
read as an offset of −17:00, hour labels collapsed into one day). A new form is one shape in `parse.read_dates` and its
rows here, for the paste and the conversion at once.
"""

import csv
import io
from dataclasses import dataclass, field
from typing import Any

import dateutil.parser
import pandas as pd
import pytest
from pydantic import TypeAdapter

from agents.anyplot.data.bindings import default_bindings
from agents.anyplot.data.parse import DateCells, parse_dataset, read_dates, utc_offset
from agents.anyplot.data.prepare import (
    Operation,
    PrepareError,
    _cell_text,
    _date_conversion,
    apply_operations,
    dry_run,
    read_frame,
)
from core.spec_roles import parse_roles


OPERATIONS = TypeAdapter(list[Operation])
FORMS = (
    "the chat reads 2026-03-01, 01.03.2026, 03/15/2026, 8 Nov 2026, each also with a time, "
    "and months such as 2026-03 or Mar 2026"
)


def slash_order(unread: int) -> str:
    """The clause of `unread` slash dates whose column settles no single order of day and month."""
    return (
        f"its slash dates settle no single order of day and month, so {unread} of them "
        f"{'is' if unread == 1 else 'are'} not read; a date_format of DD/MM/YYYY or MM/DD/YYYY sets the order for a "
        "column of slash dates only"
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


ADDED: dict[str, Row] = {
    "day_month_en": Row(["8 Nov 2026", "9 Nov 2026"], ["2026-11-08", "2026-11-09"]),
    "day_month_en_long": Row(["1 March 2026", "15 March 2026"], ["2026-03-01", "2026-03-15"]),
    "day_month_de": Row(["1. März 2026", "15. Okt. 2026"], ["2026-03-01", "2026-10-15"]),
    "day_month_fr": Row(["1 mars 2026", "15 févr. 2026"], ["2026-03-01", "2026-02-15"]),
    "month_day_en": Row(["March 1, 2026", "Nov. 15, 2026"], ["2026-03-01", "2026-11-15"]),
    "day_month_time": Row(
        ["8 Nov 2026 10:00", "9 Nov 2026 9:05:30"], ["2026-11-08T10:00:00", "2026-11-09T09:05:30"], with_time=True
    ),
    "day_month_de_time": Row(
        ["1. März 2026 10:00", "2. März 2026 11:30"], ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], True
    ),
    "month_day_without_comma": Row(["Mar 1 2026", "Mar 15 2026"], ["2026-03-01", "2026-03-15"]),
    "month_day_long_without_comma": Row(["March 1 2026", "March 15 2026"], ["2026-03-01", "2026-03-15"]),
    "month_day_without_comma_time": Row(
        ["May 5 2026 10:00", "May 6 2026 9:05"], ["2026-05-05T10:00:00", "2026-05-06T09:05:00"], with_time=True
    ),
    "month_day_time": Row(
        ["March 1, 2026 10:00", "March 2, 2026 11:30"], ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], True
    ),
    "lowercase_t": Row(["2026-03-01t10:00", "2026-03-02t11:30"], ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], True),
    "lowercase_t_offset": Row(
        ["2026-03-01t10:00+01:00", "2026-03-02t11:30+01:00"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        with_time=True,
    ),
    "lowercase_z": Row(
        ["2026-03-01T10:00:00z", "2026-03-02T11:30z"],
        ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:00+00:00"],
        with_time=True,
    ),
    "lowercase_t_and_z": Row(
        ["2026-03-01t10:00z", "2026-03-02t11:30:15z"],
        ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:15+00:00"],
        with_time=True,
    ),
}
"""Forms the list took in after the first cut: a day with a month name and a four-digit year, in the eleven languages
of `months.py` and in the orders people write, also with a time; and an ISO time after a lowercase `t`, as RFC 3339
allows. The paste kept every one of them as text before (`1. März 2026` read in no conversion either), and types them
now, without a note: unlike a month, such a cell names its day."""


@pytest.mark.parametrize("name", list(ADDED))
def test_an_added_form_converts(name: str) -> None:
    row = ADDED[name]

    assert converted(row.cells) == {
        "values": row.values,
        "failed": 0,
        "with_time": row.with_time,
        "guess": None,
        "notice": "",
    }


@pytest.mark.parametrize("name", list(ADDED))
def test_an_added_form_is_typed_at_the_paste(name: str) -> None:
    """A day with a month name is typed with a note, as months are, since labels can take that form too."""
    row = ADDED[name]
    written_month = not name.startswith("lowercase")
    notes = (
        [f"column 'd': {len(row.cells)} cells read as dates (a day, a month name and a year)"] if written_month else []
    )

    assert pasted(row.cells) == ("datetime", row.values, notes)


class TestDaysWithAMonthName:
    def test_an_impossible_day_is_unreadable(self) -> None:
        reading = converted(["31 Nov 2026", "30 Nov 2026"])

        assert reading["values"] == [None, "2026-11-30"] and reading["failed"] == 1
        assert pasted(["31 Nov 2026", "30 Nov 2026"])[0] == "text"

    def test_beside_iso_dates_such_a_cell_reads_in_a_conversion_and_the_paste_keeps_the_mix(self) -> None:
        cells = ["2026-11-07", "8 Nov 2026", "2026-11-09"]

        assert converted(cells)["values"] == ["2026-11-07", "2026-11-08", "2026-11-09"]
        assert pasted(cells) == ("text", cells, [])

    def test_both_orders_are_one_shape(self) -> None:
        """The name settles which part is the month, so `8 Nov 2026` beside `March 1, 2026` takes no order."""
        cells = ["8 Nov 2026", "March 1, 2026"]

        assert converted(cells)["values"] == ["2026-11-08", "2026-03-01"]
        assert pasted(cells)[1] == ["2026-11-08", "2026-03-01"]

    def test_a_word_that_names_no_month_is_no_date(self) -> None:
        assert converted(["1 am 2026", "2 am 2026"])["failed"] == 2

    def test_a_month_name_a_day_and_a_year_is_that_day_never_a_month(self) -> None:
        """`Nov 26 2026` holds a four-digit year after the day: 26 November 2026, never November of a year 26."""
        assert converted(["Nov 26 2026", "Nov 25 2026"])["values"] == ["2026-11-26", "2026-11-25"]
        assert pasted(["Nov 26 2026", "Nov 25 2026"]) == (
            "datetime",
            ["2026-11-26", "2026-11-25"],
            ["column 'd': 2 cells read as dates (a day, a month name and a year)"],
        )

    def test_labels_that_happen_to_be_such_days_are_typed_with_the_note(self) -> None:
        """Italian month abbreviations with a day and a year: the typing is said, so a request can take it back."""
        cells = ["Gen 2 2026", "Set 1 2026", "Mar 3 2026"]

        assert pasted(cells) == (
            "datetime",
            ["2026-01-02", "2026-09-01", "2026-03-03"],
            ["column 'd': 3 cells read as dates (a day, a month name and a year)"],
        )

    def test_a_month_without_a_day_is_still_its_first_day(self) -> None:
        assert pasted(["Nov 2026", "Dec 2026"]) == ("datetime", ["2026-11-01", "2026-12-01"], [MONTH_NAMES])


UNLISTED: dict[str, tuple[list[str], str]] = {
    "two_digit_year": (["01.03.26", "15.03.26"], "text"),
    "day_month_two_digit_year": (["8 Nov 26", "9 Nov 26"], "text"),
    "month_day_without_year": (["Nov 26", "Nov 25"], "text"),
    "date_with_lowercase_z_and_no_time": (["2026-03-01z", "2026-03-02z"], "text"),
    "am_pm": (["3/15/2026 10:00 AM", "3/16/2026 2:30 PM"], "text"),
    "year_slash": (["2026/03/01", "2026/03/15"], "text"),
    "dashes_day_first": (["15-03-2026", "16-03-2026"], "text"),
    "day_dashes_month_name": (["01-Mar-2026", "15-Mar-2026"], "text"),
    "ordinal_day": (["1st March 2026", "2nd March 2026"], "text"),
    "weekday": (["Sunday, March 1, 2026", "Monday, March 2, 2026"], "text"),
    "compact": (["20260301", "20260315"], "integer"),
    "program_timestamp": (["Sun Mar 1 10:00:00 2026", "Mon Mar 2 11:00:00 2026"], "text"),
    "hour_without_minutes": (["2026-03-01T10", "2026-03-02T11"], "text"),
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

    def test_cells_that_settle_both_orders_leave_no_slash_date_readable_that_an_order_turns(self) -> None:
        """The paste's rule: a column with a first part over 12 and a second part over 12 is no slash date column.
        A slash date that names the same day in both orders (`05/05/2026`) depends on no order and reads."""
        reading = converted(["15/03/2026", "03/15/2026", "01/02/2026", "05/05/2026"])

        assert reading["values"] == [None, None, None, "2026-05-05"] and reading["failed"] == 3
        assert pasted(["15/03/2026", "03/15/2026", "01/02/2026", "05/05/2026"])[0] == "text"

    def test_dot_dates_are_day_first_without_a_guess_as_at_the_paste(self) -> None:
        reading = converted(["01.03.2026", "02.03.2026"])

        assert reading["values"] == ["2026-03-01", "2026-03-02"] and reading["guess"] is None
        assert pasted(["01.03.2026", "02.03.2026"]) == ("datetime", ["2026-03-01", "2026-03-02"], [])


class TestEachCellInItsOwnForm:
    """A conversion reads every cell in its own form of the list; the paste types a column of one form only and keeps
    a mix as written. Only the order of day and month of the slash dates is the column's."""

    @pytest.mark.parametrize(
        ("cells", "values"),
        [
            (
                [f"2026-03-{day:02d}" for day in range(1, 11)] + ["11 Mar 2026"],
                [f"2026-03-{day:02d}" for day in range(1, 12)],
            ),
            (["2026-03", "Apr 2026", "2026-05"], ["2026-03-01", "2026-04-01", "2026-05-01"]),
            (["2026-03-01", "01.03.2026"], ["2026-03-01", "2026-03-01"]),
            (["01.03.2026", "2026-03-02", "2026-04"], ["2026-03-01", "2026-03-02", "2026-04-01"]),
        ],
    )
    def test_a_conversion_reads_every_cell_and_the_paste_keeps_the_mix(
        self, cells: list[str], values: list[str]
    ) -> None:
        reading = converted(cells)

        assert reading["values"] == values and reading["failed"] == 0
        assert pasted(cells) == ("text", cells, [])

    def test_the_reading_names_each_form_it_read(self) -> None:
        text = "d,v\n" + "".join(f"2026-03-{day:02d},{day}\n" for day in range(1, 11)) + "11 Mar 2026,11\n"
        operation = {"op": "set_type", "column": "d", "type": "datetime"}

        [line] = apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).changes

        assert (
            line
            == "d: 11 cells read as dates (format inferred cell by cell: year first; a day, a month name and a year)"
        )

    def test_slash_dates_beside_others_read_in_the_order_their_column_settles(self) -> None:
        """`03/15/2026` settles month first for the slash dates; the ISO cell reads as written."""
        assert converted(["03/15/2026", "03/02/2026", "2026-03-03"])["values"] == [
            "2026-03-15",
            "2026-03-02",
            "2026-03-03",
        ]

    def test_slash_dates_beside_others_whose_order_nothing_settles_are_not_read_and_no_question_is_asked(self) -> None:
        """A guessed order in a mix could never be taken back: a later swap would turn the ISO cells too. So the slash
        dates an order turns are unread with their reason; one that reads the same in both orders reads."""
        cells = [f"2026-03-{day:02d}" for day in range(1, 11)]
        reading = converted([*cells, "03/04/2026", "05/05/2026"])
        conversion = _date_conversion(pd.Series([*cells, "03/04/2026"], dtype="str", name="d"), None)

        assert reading["values"][-2:] == [None, "2026-05-05"] and reading["failed"] == 1
        assert reading["guess"] is None and conversion.guess is None and conversion.order is None
        assert conversion.unread == {"slash_order": 1}
        assert read_dates([*cells, "03/04/2026"]).guessed is False

    def test_the_slash_reason_of_a_mix_is_the_reason_of_a_column_that_settles_both_orders(self) -> None:
        """Two settled orders, or none beside cells of another form: one reason, one sentence, whose format advice
        names the column it serves."""
        for cells in (["01.03.2026", "15/03/2026", "03/15/2026"], ["01.03.2026", "02.03.2026", "04/01/2026"]):
            text = "d,v\n" + "".join(f"{cell},{index}\n" for index, cell in enumerate(cells))
            operation = {"op": "set_type", "column": "d", "type": "datetime"}

            with pytest.raises(PrepareError) as caught:
                apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

            unread = len(cells) - 1 if "15/03/2026" in cells else 1
            assert caught.value.message == (
                f"column 'd': {unread} of 3 cells cannot be read as dates; {slash_order(unread)}"
            )
            assert caught.value.unread == {"slash_order": unread}

    @pytest.mark.parametrize(
        "cells",
        [
            ["15/03/2026", "03/15/2026", "31/31/2026"],
            ["2026-03-01", "03/04/2026", "31/31/2026"],
            ["01/02/2026", "31/31/2026"],
        ],
    )
    def test_a_slash_date_of_no_day_in_either_order_keeps_its_own_reason(self, cells: list[str]) -> None:
        assert read_dates(cells).unread["31/31/2026"] == "no_such_date"

    def test_a_column_of_slash_dates_throughout_keeps_the_named_guess(self) -> None:
        reading = converted(["01/02/2026", "03/04/2026", "bad"])

        assert reading["values"] == ["2026-02-01", "2026-04-03", None] and reading["guess"] == "the day and month order"


class TestMonthsOfASpanColumn:
    """`2009-10` in a column of seasons: the paste and an open role leave it text, a request reads it by its shape."""

    TEXT = "Season,Wins\n2009-10,5\n2010-11,6\n2011-12,7\n"

    def test_the_paste_keeps_it_text_and_no_dry_run_proposes_it(self) -> None:
        parsed = parse_dataset(self.TEXT)

        assert parsed.column_dtypes["Season"] == "text"
        assert dry_run(read_frame(parsed), "Season", "datetime") is None

    def test_a_request_reads_its_cells_as_months(self) -> None:
        operation = {"op": "set_type", "column": "Season", "type": "datetime"}

        prepared = apply_operations(parse_dataset(self.TEXT), OPERATIONS.validate_python([operation]))

        assert [row.split(",")[0] for row in prepared.csv.splitlines()[1:]] == [
            "2009-10-01",
            "2010-11-01",
            "2011-12-01",
        ]
        assert prepared.changes == ["Season: 3 cells read as dates (format inferred, year first)"]


def test_times_with_and_without_an_offset_stay_text_at_the_paste_and_are_refused_on_request() -> None:
    """No time is given a zone by guess. The paste keeps such a column as text; a request is refused with the reason.
    The other places the two differ are pinned beside their rule: `TestMonthsOfASpanColumn`, the days with a UTC offset
    in `test_date_offsets.py`, and a fraction's written form in `LISTED` (`iso_fraction`)."""
    cells = ["2026-03-01T10:00+01:00", "2026-03-02T10:00", "2026-03-03T10:00+01:00"]

    assert pasted(cells)[0] == "text"
    with pytest.raises(PrepareError) as caught:
        converted(cells)
    assert caught.value.message == (
        "column 'd' holds 2 cells with a UTC offset and 1 cell without one; no cell is given a zone by guess, so the "
        "column stays as it is"
    )


def test_a_day_beside_zoned_times_is_counted_as_a_cell_never_a_time() -> None:
    cells = [f"2026-03-{day:02d}T10:00:00+01:00" for day in range(1, 11)] + ["11.03.2026"]

    with pytest.raises(PrepareError) as caught:
        converted(cells)
    assert caught.value.message == (
        "column 'd' holds 10 cells with a UTC offset and 1 cell without one; no cell is given a zone by guess, so the "
        "column stays as it is"
    )


class TestInvisibleSpaces:
    """A no-break, a narrow no-break or a figure space, as spreadsheets and typeset pages write one, is a plain space
    for reading a date; a column that stays text keeps its cells as written."""

    CELLS = ["1\N{NO-BREAK SPACE}March\N{NO-BREAK SPACE}2026", "2\N{FIGURE SPACE}March 2026"]

    def test_a_date_with_such_spaces_reads_at_the_paste_and_in_a_conversion(self) -> None:
        assert converted(list(self.CELLS))["values"] == ["2026-03-01", "2026-03-02"]
        assert pasted(list(self.CELLS))[:2] == ("datetime", ["2026-03-01", "2026-03-02"])
        timed = ["2026-03-01\N{NARROW NO-BREAK SPACE}10:00", "2026-03-02\N{NO-BREAK SPACE}11:30"]
        assert converted(timed)["values"] == ["2026-03-01T10:00:00", "2026-03-02T11:30:00"]
        assert pasted(timed)[:2] == ("datetime", ["2026-03-01T10:00:00", "2026-03-02T11:30:00"])

    def test_a_column_that_stays_text_keeps_the_spaces(self) -> None:
        assert pasted([self.CELLS[0], "soon"]) == ("text", [self.CELLS[0], "soon"], [])


class TestTheTableFinder:
    """A line of a form of the list is a value when the parser finds the table: a list of such dates is one column of
    dates, never pairs of a label and a number, and a first row of such dates may be data."""

    def test_a_headerless_list_of_days_with_a_month_name_is_one_date_column(self) -> None:
        parsed = parse_dataset("8 Nov 2026\n9 Nov 2026\n10 Nov 2026\n")

        assert parsed.csv.splitlines() == ["value", "2026-11-08", "2026-11-09", "2026-11-10"]
        assert parsed.warnings[0].startswith("no header line: the first line is a value, kept as the first row")

    def test_a_headerless_list_of_months_is_one_column_of_months(self) -> None:
        parsed = parse_dataset("Nov 2026\nDec 2026\nJan 2027\n")

        assert parsed.csv.splitlines() == ["value", "2026-11-01", "2026-12-01", "2027-01-01"]

    def test_a_headerless_two_column_table_warns_that_its_first_row_may_be_data(self) -> None:
        parsed = parse_dataset("8 Nov 2026,3\n9 Nov 2026,4\n10 Nov 2026,5\n")

        assert "every header looks like a value; the first row may be data rather than column names" in parsed.warnings

    def test_a_wide_table_with_such_dates_as_headers_keeps_them_as_names(self) -> None:
        parsed = parse_dataset("Name,8 Nov 2026,9 Nov 2026,10 Nov 2026\nA,1,2,3\nB,4,5,6\n")

        assert list(parsed.column_dtypes) == ["Name", "8 Nov 2026", "9 Nov 2026", "10 Nov 2026"]
        assert parsed.warnings == []

    def test_pairs_of_a_label_and_a_number_are_still_pairs(self) -> None:
        assert parse_dataset("Hund 7\nKatze 3\nMaus 2\n").csv.splitlines()[:2] == ["label,value", "Hund,7"]

    def test_a_headerless_list_of_seasons_keeps_its_first_line(self) -> None:
        parsed = parse_dataset("2009-10\n2010-11\n2011-12\n")

        assert parsed.csv.splitlines() == ["value", "2009-10", "2010-11", "2011-12"]
        assert parsed.column_dtypes == {"value": "text"}

    HEADS = {
        "months": ["2026-01", "2026-02", "2026-03"],
        "seasons": ["2009-10", "2010-11", "2011-12"],
        "written days": ["8 Nov 2026", "9 Nov 2026", "10 Nov 2026"],
        "iso times": ["2026-03-01T10:00:00Z", "2026-03-01T11:00:00Z", "2026-03-01T12:00:00Z"],
    }
    """Header cells of forms of the list: finding the table takes them for names, as it did before the list."""

    @pytest.mark.parametrize("form", list(HEADS))
    def test_a_title_above_a_wide_table_of_such_headers_is_set_aside(self, form: str) -> None:
        heads = self.HEADS[form]
        parsed = parse_dataset(f"Monthly sales report\nProduct,{','.join(heads)}\nA,1,2,3\nB,4,5,6\nC,7,8,9\n")

        assert parsed.csv.splitlines()[0] == ",".join(["Product", *heads])
        assert parsed.column_dtypes == {"Product": "text", **dict.fromkeys(heads, "integer")}
        assert parsed.profile.rows == 3
        assert parsed.warnings == ["left out 1 line above the table (a title, notes or metadata)"]

    @pytest.mark.parametrize("form", list(HEADS))
    def test_a_second_header_line_of_such_headers_is_the_header(self, form: str) -> None:
        heads = self.HEADS[form]
        parsed = parse_dataset(f"Product,Sales,Sales,Sales\nName,{','.join(heads)}\nA,1,2,3\nB,4,5,6\nC,7,8,9\n")

        assert parsed.csv.splitlines()[0] == ",".join(["Name", *heads])
        assert parsed.column_dtypes == {"Name": "text", **dict.fromkeys(heads, "integer")}
        assert parsed.warnings == ["left out 1 line above the table (a title, notes or metadata)"]

    @pytest.mark.parametrize(
        ("text", "bindings"),
        [
            ("Season,Points\n2009-10,30\n2010-11,40\n2011-12,35\n", {"category": "Season", "value": "Points"}),
            ("When,Points\n2009-10,30\n2010-11,40\n2011-12,35\n", {"category": "When", "value": "Points"}),
            ("2009-10,5\n2010-11,6\n2011-12,7\n", {"category": "2009-10", "value": "5"}),
        ],
    )
    def test_a_text_column_of_seasons_beside_numbers_is_the_category(self, text: str, bindings: dict[str, str]) -> None:
        parsed = parse_dataset(text)
        roles = parse_roles(["`category` (categorical) - The groups", "`value` (numeric) - The value of each group"])

        assert {binding.role: binding.column for binding in default_bindings(roles, parsed.profile)} == bindings


class TestTheCrowdedLine:
    def test_the_reading_words_never_give_way_to_the_reason(self) -> None:
        """The line holds its step and counts but not the forms beside them: the forms give way, and the order the
        slash dates were read in stays whole (placed beside the start of the step alone, they cut it)."""
        name = "Ablesedatum des Stromzaehlers"
        cells = [f"03/{day}/2026" for day in range(13, 23)] + ["1st March 2026"]
        text = f"{name},kWh\n" + "".join(f"{cell},{index}\n" for index, cell in enumerate(cells))
        operation = {"op": "set_type", "column": name, "type": "datetime", "name": f"{name} (Datum)"}

        [line] = apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).changes

        assert line == (
            f"new column {name} (Datum): 10 cells of {name} read as dates (format inferred, month before day), "
            f"1 cell could not be read as a date and is now missing; {name} stays as it is"
        )


class TestEdges:
    @pytest.mark.parametrize("offset", ["+01:60", "+01:75", "-05:99"])
    def test_minutes_of_an_offset_past_59_are_no_offset(self, offset: str) -> None:
        assert utc_offset(offset) is None
        cells = [f"2026-03-01T10:00{offset}", f"2026-03-02T10:00{offset}"]
        assert converted(cells)["failed"] == 2 and pasted(cells)[0] == "text"

    def test_a_zoned_time_with_nanoseconds_keeps_its_digits_on_both_sides(self) -> None:
        cells = ["2026-03-01T10:00:00.123456789+01:00", "2026-03-02T10:00:00.5+01:00"]

        assert converted(cells)["values"] == ["2026-03-01T10:00:00.123456789+01:00", "2026-03-02T10:00:00.500000+01:00"]
        assert pasted(cells)[:2] == (
            "datetime",
            ["2026-03-01T10:00:00.123456789+01:00", "2026-03-02T10:00:00.500000000+01:00"],
        )

    def test_no_cell_reads_as_no_shape(self) -> None:
        assert read_dates([]) == DateCells()


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
        columns = [row.cells for row in [*LISTED.values(), *ADDED.values()]]
        columns += [list(cells) for cells, _ in UNLISTED.values()]
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
        text = "day,kWh\n" + "".join(f"2026/03/{day:02d},{day}\n" for day in range(1, 13))

        with pytest.raises(PrepareError) as caught:
            apply_operations(
                parse_dataset(text),
                OPERATIONS.validate_python([{"op": "set_type", "column": "day", "type": "datetime"}]),
            )

        assert caught.value.code == "type_mismatch"
        assert caught.value.message == f"column 'day': 12 of 12 cells cannot be read as dates; {FORMS}"

    def test_cells_left_unread_name_the_forms_too(self) -> None:
        text = "day,kWh\n" + "".join(f"2026-03-{day:02d},{day}\n" for day in range(1, 11)) + "2026/03/11,11\n"
        operation = {"op": "set_type", "column": "day", "type": "datetime", "name": "day (date)"}

        [line] = apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).changes

        assert line == (
            "new column day (date): 10 cells of day read as dates (format inferred, year first), 1 cell could not be "
            f"read as a date and is now missing; {FORMS}; day stays as it is"
        )

    @pytest.mark.parametrize("unread", [1, 3])
    def test_a_crowded_line_keeps_the_count_and_says_as_dates(self, unread: int) -> None:
        """Where the forms do not fit beside a long name and many offsets, the count of the cells left missing is
        whole, and it says what they were not read as; a format's line is as it was."""
        name = "Ablesedatum des Stromzaehlers im Hauptgebaeude laut Monatsbe"  # 60 characters, the cap
        offsets = [f"{sign}{hours:02d}:30" for sign in "+-" for hours in range(1, 9)] * 2
        cells = [f"2026-03-{1 + index % 28:02d}{offset}" for index, offset in enumerate(offsets)]
        cells += [f"2026/03/{20 + index}" for index in range(unread)]  # no form of the list
        text = f"{name},kWh\n" + "".join(f"{cell},{index}\n" for index, cell in enumerate(cells))
        operation = {"op": "set_type", "column": name, "type": "datetime", "name": name[:50] + " (Datum)"}

        [line] = apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).changes

        words = "1 cell could not be read as a date and is now" if unread == 1 else "3 cells could not be read as dates"
        assert len(line) <= 300 and f", {words}" in line
        assert FORMS not in line  # the forms gave way, the count did not
        assert line.endswith("which were dropped; the days are as written")

    def test_a_refusal_always_names_the_forms_beside_a_long_name(self) -> None:
        name = "Ablesedatum des Stromzaehlers im Hauptgebaeude laut Monatsbe"
        text = f"{name},kWh\n" + "".join(f"2026/03/{day:02d}+01:00,{day}\n" for day in range(1, 13))

        with pytest.raises(PrepareError) as caught:
            apply_operations(
                parse_dataset(text),
                OPERATIONS.validate_python([{"op": "set_type", "column": name, "type": "datetime"}]),
            )

        assert caught.value.message == f"column '{name}': 12 of 12 cells cannot be read as dates; {FORMS}"

    def test_a_slash_column_that_settles_both_orders_is_refused_with_its_reason(self) -> None:
        """No order fits the column, as at the paste: no majority of cells decides it, and its cells are in a form of
        the list, so the refusal says why instead of naming the forms."""
        text = "d,v\n15/03/2026,1\n03/15/2026,2\n01/02/2026,3\n"
        operation = {"op": "set_type", "column": "d", "type": "datetime"}

        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

        assert caught.value.message == f"column 'd': 3 of 3 cells cannot be read as dates; {slash_order(3)}"
        assert caught.value.unread == {"slash_order": 3}

    def test_days_that_do_not_exist_are_refused_with_their_count(self) -> None:
        text = "d,v\n31 Nov 2026,1\n29 Feb 2025,2\n29 Feb 2024,3\n"
        operation = {"op": "set_type", "column": "d", "type": "datetime"}

        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

        assert caught.value.message == (
            "column 'd': 2 of 3 cells cannot be read as dates; 2 cells name a day that does not exist, such as 31 November"
        )
        assert caught.value.unread == {"no_such_date": 2}

    def test_each_reason_has_its_clause_in_one_refusal(self) -> None:
        text = "d,v\n31 Nov 2026,1\n1st March 2026,2\n2026-03-03,3\n"
        operation = {"op": "set_type", "column": "d", "type": "datetime"}

        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

        assert caught.value.message == (
            "column 'd': 2 of 3 cells cannot be read as dates; 1 cell names a day that does not exist, such as 31 "
            f"November; {FORMS}"
        )
        assert caught.value.unread == {"no_such_date": 1, "no_form": 1}

    def test_a_missing_day_beside_many_dates_is_said_in_the_change_line(self) -> None:
        text = "d,v\n" + "".join(f"2026-11-{day:02d},{day}\n" for day in range(1, 11)) + "31 Nov 2026,11\n"
        operation = {"op": "set_type", "column": "d", "type": "datetime", "name": "d (date)"}

        [line] = apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation])).changes

        assert line == (
            "new column d (date): 10 cells of d read as dates (format inferred, year first), 1 cell could not be read "
            "as a date and is now missing; 1 cell names a day that does not exist, such as 31 November; d stays as it is"
        )

    def test_a_format_names_no_forms(self) -> None:
        text = "day,kWh\n" + "".join(f"2026/03/{day:02d},{day}\n" for day in range(1, 13))
        operation = {"op": "set_type", "column": "day", "type": "datetime", "date_format": "DD.MM.YYYY"}

        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

        assert caught.value.message == "column 'day': 12 of 12 cells cannot be read as dates"
