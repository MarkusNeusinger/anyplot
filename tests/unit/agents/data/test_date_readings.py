"""The readings of every text-to-date conversion, pinned as they were before the strict date rule.

A characterisation table: each row is a column of cells run through the conversion `set_type` makes without a
format (`prepare._date_conversion`) and through the paste (`parse_dataset`), with what came out before the rule that
a cell converts only as a date alone or a date followed by a time. The rows are the forms that read, or fail for a
reason of their own; a change to any of them fails here, so a reading that stops working is seen. Some rows pin a
reading that is wrong (`slash_month_first`, `compact_date`, `time_first`): what they read is a decision of its own,
and the table makes sure it does not change unseen. The rows the rule changes on purpose are listed in `CHANGED`
with their new reading.
"""

import csv
import io
from dataclasses import dataclass
from typing import Any

import pandas as pd
import pytest
from pydantic import TypeAdapter

from agents.anyplot.data import prepare as prepare_module
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import (
    Operation,
    PrepareError,
    _cell_text,
    _date_conversion,
    apply_operations,
    dry_run,
    read_frame,
)


@dataclass(frozen=True)
class Reading:
    """What a conversion of `cells` gives: the cells as `data.csv` writes them (None for a missing one), the cells
    that failed, whether the column is written with a time, the guess and the notice; or the refusal."""

    cells: list[Any]
    """The cells as given: text, None for a missing one, or numbers for a conversion of a number column."""
    values: list[str | None] | None = None
    failed: int = 0
    with_time: bool = False
    guess: str | None = None
    notice: str = ""
    refused: str | None = None


@dataclass(frozen=True)
class Pasted:
    """What the paste makes of the same cells: the column's dtype, its cells when the parser typed it, its notes."""

    dtype: str
    cells: list[str] | None
    warnings: list[str]


def converted(cells: list[str | None]) -> Reading:
    series = pd.Series(cells, dtype="str", name="d")
    try:
        conversion = _date_conversion(series, None)
    except PrepareError as error:
        return Reading(cells, refused=error.message)
    values = [_cell_text(value, conversion.with_time) for value in conversion.values]
    return Reading(cells, values, conversion.failed, conversion.with_time, conversion.guess, conversion.notice)


def pasted(cells: list[str | None]) -> Pasted:
    text = io.StringIO()
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(["d", "n"])
    writer.writerows(["" if cell is None else cell, index] for index, cell in enumerate(cells))
    parsed = parse_dataset(text.getvalue())
    rows = list(csv.reader(io.StringIO(parsed.csv)))
    column = rows[0].index("d")
    dtype = parsed.column_dtypes["d"]
    typed = [row[column] for row in rows[1:]] if dtype != "text" else None
    return Pasted(dtype, typed, [warning for warning in parsed.warnings if warning.startswith("column 'd'")])


READINGS: dict[str, Reading] = {
    "iso_date": Reading(
        ["2026-03-01", "2026-03-02", "2026-12-31"], ["2026-03-01", "2026-03-02", "2026-12-31"], 0, False, None, ""
    ),
    "iso_minutes": Reading(
        ["2026-03-01T10:00", "2026-03-02T11:30"], ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], 0, True, None, ""
    ),
    "iso_seconds": Reading(
        ["2026-03-01T10:00:00", "2026-03-02T11:30:15"],
        ["2026-03-01T10:00:00", "2026-03-02T11:30:15"],
        0,
        True,
        None,
        "",
    ),
    "iso_space_seconds": Reading(
        ["2026-03-01 10:00:00", "2026-03-02 11:30:15"],
        ["2026-03-01T10:00:00", "2026-03-02T11:30:15"],
        0,
        True,
        None,
        "",
    ),
    "iso_lower_t": Reading(
        ["2026-03-01t10:00", "2026-03-02t11:30"], ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], 0, True, None, ""
    ),
    "iso_fraction": Reading(
        ["2026-03-01T10:00:00.123", "2026-03-02T11:30:15.5"],
        ["2026-03-01T10:00:00.123000", "2026-03-02T11:30:15.500000"],
        0,
        True,
        None,
        "",
    ),
    "iso_fraction_comma": Reading(
        ["2026-03-01T10:00:00,25", "2026-03-02T11:30:15,5"],
        ["2026-03-01T10:00:00.250000", "2026-03-02T11:30:15.500000"],
        0,
        True,
        None,
        "",
    ),
    "iso_nanoseconds": Reading(
        ["2026-03-01T10:00:00.123456789", "2026-03-02T11:30:15.000000001"],
        ["2026-03-01T10:00:00.123456789", "2026-03-02T11:30:15.000000001"],
        0,
        True,
        None,
        "",
    ),
    "iso_z": Reading(
        ["2026-03-01T10:00:00Z", "2026-03-02T11:30:00Z"],
        ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:00+00:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_offset": Reading(
        ["2026-03-01T10:00+01:00", "2026-03-02T11:30+01:00"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_offsets_mixed": Reading(
        ["2026-03-01T10:00:00+01:00", "2026-07-01T10:00:00+02:00"],
        ["2026-03-01T09:00:00+00:00", "2026-07-01T08:00:00+00:00"],
        0,
        True,
        None,
        "times with the UTC offsets +01:00, +02:00 converted to UTC (+00:00); the instants are the same",
    ),
    "iso_offset_compact": Reading(
        ["2026-03-01T10:00-0500", "2026-03-02T11:30-0500"],
        ["2026-03-01T10:00:00-05:00", "2026-03-02T11:30:00-05:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_offset_hours": Reading(
        ["2026-03-01T10:00+01", "2026-03-02T11:30+01"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_space_offset": Reading(
        ["2026-03-01 10:00:00+01:00", "2026-03-02 11:30:00+01:00"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_date_and_time": Reading(
        ["2026-03-01 10:00", "2026-03-02"], ["2026-03-01T10:00:00", "2026-03-02T00:00:00"], 0, True, None, ""
    ),
    "iso_single_digits": Reading(["2026-3-1", "2026-3-15"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "year_slash": Reading(["2026/03/01", "2026/03/15"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "year_dot": Reading(["2026.03.01", "2026.03.15"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "year_slash_time": Reading(
        ["2026/03/01 10:00", "2026/03/15 11:30"], ["2026-03-01T10:00:00", "2026-03-15T11:30:00"], 0, True, None, ""
    ),
    "dot_date": Reading(["01.03.2026", "15.03.2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "dot_single_digits": Reading(["1.3.2026", "15.3.2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "dot_time": Reading(
        ["01.03.2026 10:00", "15.03.2026 11:30"], ["2026-03-01T10:00:00", "2026-03-15T11:30:00"], 0, True, None, ""
    ),
    "dot_seconds": Reading(
        ["01.03.2026 10:00:05", "15.03.2026 11:30:59"],
        ["2026-03-01T10:00:05", "2026-03-15T11:30:59"],
        0,
        True,
        None,
        "",
    ),
    "slash_day_first": Reading(["01/03/2026", "15/03/2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "slash_month_first": Reading(["03/15/2026", "03/01/2026"], ["2026-03-15", "2026-01-03"], 0, False, None, ""),
    "slash_ambiguous": Reading(
        ["01/03/2026", "02/04/2026"], ["2026-03-01", "2026-04-02"], 0, False, "the day and month order", ""
    ),
    "slash_time": Reading(
        ["01/03/2026 10:00", "15/03/2026 23:59"], ["2026-03-01T10:00:00", "2026-03-15T23:59:00"], 0, True, None, ""
    ),
    "dash_day_first": Reading(["01-03-2026", "15-03-2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "dash_month_first": Reading(["03-15-2026", "03-01-2026"], ["2026-03-15", "2026-01-03"], 0, False, None, ""),
    "dot_two_digit_year": Reading(
        ["01.03.26", "15.03.26"], ["2026-03-01", "2026-03-15"], 0, False, "the century of two-digit years", ""
    ),
    "slash_two_digit_year": Reading(
        ["01/03/26", "15/03/26"], ["2026-03-01", "2026-03-15"], 0, False, "the century of two-digit years", ""
    ),
    "two_digit_year_century": Reading(
        ["26.11.26", "27.11.26"], ["2026-11-26", "2026-11-27"], 0, False, "the century of two-digit years", ""
    ),
    "name_day_month_year": Reading(["1 March 2026", "15 March 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "name_month_day_comma": Reading(
        ["March 1, 2026", "March 15, 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""
    ),
    "name_abbreviated": Reading(["Mar 1 2026", "Mar 15 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "name_dashes": Reading(["1-Mar-2026", "15-Mar-2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "name_dashes_two_digit": Reading(
        ["01-Mar-26", "15-Mar-26"], ["2026-03-01", "2026-03-15"], 0, False, "the century of two-digit years", ""
    ),
    "name_year_first": Reading(["2026-Mar-01", "2026-Mar-15"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "name_weekday": Reading(
        ["Sunday, March 1, 2026", "Sunday, March 15, 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""
    ),
    "name_ordinal": Reading(["1st March 2026", "15th March 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "name_with_time": Reading(
        ["1 Mar 2026 10:00", "15 Mar 2026 11:30"], ["2026-03-01T10:00:00", "2026-03-15T11:30:00"], 0, True, None, ""
    ),
    "name_lower": Reading(["1 march 2026", "15 march 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "month_year_en": Reading(["Nov 2026", "Dec 2026"], ["2026-11-01", "2026-12-01"], 0, False, None, ""),
    "month_year_de": Reading(["Okt. 2026", "Nov. 2026"], ["2026-10-01", "2026-11-01"], 0, False, None, ""),
    "month_year_de_umlaut": Reading(["März 2026", "April 2026"], ["2026-03-01", "2026-04-01"], 0, False, None, ""),
    "month_year_fr": Reading(["févr. 2026", "mars 2026"], ["2026-02-01", "2026-03-01"], 0, False, None, ""),
    "month_year_es": Reading(["marzo 2026", "abril 2026"], ["2026-03-01", "2026-04-01"], 0, False, None, ""),
    "month_year_it": Reading(["marzo 2026", "aprile 2026"], ["2026-03-01", "2026-04-01"], 0, False, None, ""),
    "month_year_year_first": Reading(["2026 Nov", "2026 Dec"], ["2026-11-01", "2026-12-01"], 0, False, None, ""),
    "day_month_year_de": Reading(["1. März 2026", "15. März 2026"], [None, None], 2, False, None, ""),
    "year_month": Reading(["2026-03", "2026-04"], ["2026-03-01", "2026-04-01"], 0, False, None, ""),
    "quarter": Reading(["2026-Q1", "2026-Q2"], ["2026-01-01", "2026-04-01"], 0, False, None, ""),
    "quarter_first": Reading(["Q1 2026", "Q2 2026"], [None, None], 2, False, None, ""),
    "year_text": Reading(["2026", "2027"], ["2026-01-01", "2027-01-01"], 0, False, None, ""),
    "am_pm_slash": Reading(
        ["03/01/2026 10:00 AM", "03/15/2026 2:30 PM"], ["2026-01-03T10:00:00", "2026-03-15T14:30:00"], 0, True, None, ""
    ),
    "am_pm_iso": Reading(
        ["2026-03-01 10:00 am", "2026-03-01 2:30 pm"], ["2026-03-01T10:00:00", "2026-03-01T14:30:00"], 0, True, None, ""
    ),
    "am_pm_compact": Reading(["2026-03-01 10am", "2026-03-01 2pm"], ["2026-03-01", "2026-03-01"], 0, False, None, ""),
    "compact_date": Reading(["20260301", "20260315"], ["2026-01-03", "2026-03-15"], 0, False, None, ""),
    "compact_date_time": Reading(["20260301T1000", "20260315T1130"], ["2026-01-03", "2026-03-15"], 0, False, None, ""),
    "iso_compact_time": Reading(
        ["2026-03-01T1000", "2026-03-15T1130"], ["2026-03-01", "2026-03-15"], 0, False, None, ""
    ),
    "empty_cells": Reading(["2026-03-01", None, "2026-03-03"], ["2026-03-01", None, "2026-03-03"], 0, False, None, ""),
    "one_unreadable": Reading(
        ["01.03.2026", "15.03.2026", "unknown"], ["2026-03-01", "2026-03-15", None], 1, False, None, ""
    ),
    "filled_in_month": Reading(["May", "2026-03-01"], [None, "2026-03-01"], 1, False, None, ""),
    "time_alone": Reading(["13:00", "2026-03-01"], [None, "2026-03-01T00:00:00"], 1, True, None, ""),
    "now_word": Reading(["today", "2026-03-01"], [None, "2026-03-01"], 1, False, None, ""),
    "impossible_day": Reading(["2026-02-30", "2026-03-01"], [None, "2026-03-01"], 1, False, None, ""),
    "far_years": Reading(["0001-01-01", "9999-12-31"], ["0001-01-01", "9999-12-31"], 0, False, None, ""),
    "century_turn": Reading(["1999-12-31", "2000-01-01"], ["1999-12-31", "2000-01-01"], 0, False, None, ""),
    "naive_and_zoned": Reading(
        ["2026-03-01T10:00:00+01:00", "2026-03-01T10:00:00"],
        refused="column 'd' holds times with a UTC offset and times without one; no time is given a zone by guess, so the column stays as it is",
    ),
    "f4_offset_east": Reading(
        ["2026-03-01+01:00", "2026-03-02+01:00"],
        ["2026-03-01", "2026-03-02"],
        0,
        False,
        "the days of 2 dates with a UTC offset as written, the offset dropped",
        "",
    ),
    "f4_offset_west": Reading(
        ["2026-03-01-05:00", "2026-03-02-05:00"],
        ["2026-03-01", "2026-03-02"],
        0,
        False,
        "the days of 2 dates with a UTC offset as written, the offset dropped",
        "",
    ),
    "f4_z": Reading(
        ["2026-03-01Z", "2026-03-02Z"],
        ["2026-03-01", "2026-03-02"],
        0,
        False,
        "the days of 2 dates with a UTC offset as written, the offset dropped",
        "",
    ),
    "f4_mixed_plain": Reading(
        ["2026-03-01", "2026-03-02+01:00"],
        ["2026-03-01", "2026-03-02"],
        0,
        False,
        "the days of 1 date with a UTC offset as written, the offset dropped",
        "",
    ),
    "f4_hour_labels": Reading(
        ["2026-03-01-03", "2026-03-01-04"],
        refused="column 'd' holds dates followed directly by a sign and digits in no UTC offset form (such as YYYY-MM-DD-HH or YYYY-MM-DD±HHMM), which may be an hour as well as an offset, so the column stays as it is: an offset reads in the form YYYY-MM-DD±HH:MM, a time in the form YYYY-MM-DDTHH:MM",
    ),
    "f4_beside_times": Reading(
        ["2026-03-01+01:00", "2026-03-02T10:00"],
        refused="column 'd' holds dates with a UTC offset and no time beside times; such a date names a day, not a moment, so the column stays as it is",
    ),
    "f4_beside_unreadable": Reading(
        ["2026-03-01+01:00", "n.a.: none"],
        ["2026-03-01", None],
        1,
        False,
        "the days of 1 date with a UTC offset as written, the offset dropped",
        "",
    ),
    "lone_hour_t": Reading(
        ["2026-03-01T00", "2026-03-01T01", "2026-03-01T02", "2026-03-01T03"],
        ["2026-03-01", "2026-03-01", "2026-03-01", "2026-03-01"],
        0,
        False,
        None,
        "",
    ),
    "lone_hour_space": Reading(["2026-03-01 10", "2026-03-01 11"], ["2026-03-01", "2026-03-01"], 0, False, None, ""),
    "utc_word_time": Reading(
        ["2026-03-01 10:00 UTC", "2026-03-02 11:30 UTC"],
        ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:00+00:00"],
        0,
        True,
        None,
        "",
    ),
    "utc_word_date": Reading(["2026-03-01 UTC", "2026-03-02 UTC"], [None, None], 2, False, None, ""),
    "space_before_offset": Reading(
        ["2026-03-01 10:00:00 +01:00", "2026-03-02 11:30:00 +01:00"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        0,
        True,
        None,
        "",
    ),
    "name_comma_time_am": Reading(
        ["Mar 1, 2026 10:00 AM", "Mar 15, 2026 2:30 PM"],
        ["2026-03-01T10:00:00", "2026-03-15T14:30:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_fraction_offset": Reading(
        ["2026-03-01T10:00:00.5+01:00", "2026-03-02T11:30:00.25+01:00"],
        ["2026-03-01T10:00:00.500000+01:00", "2026-03-02T11:30:00.250000+01:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_hour_z": Reading(["2026-03-01T10Z", "2026-03-02T11Z"], ["2026-03-01", "2026-03-02"], 0, False, None, ""),
    "iso_hour_offset": Reading(
        ["2026-03-01T10+01:00", "2026-03-02T11+01:00"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:00:00+01:00"],
        0,
        True,
        None,
        "",
    ),
    "name_comma_time": Reading(
        ["1 Mar 2026, 10:00", "15 Mar 2026, 11:30"], ["2026-03-01T10:00:00", "2026-03-15T11:30:00"], 0, True, None, ""
    ),
    "iso_space_z": Reading(
        ["2026-03-01T10:00:00 Z", "2026-03-02T11:30:00 Z"],
        ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:00+00:00"],
        0,
        True,
        None,
        "",
    ),
    "dot_comma_time": Reading(
        ["01.03.2026, 10:00", "15.03.2026, 11:30"], ["2026-03-01T10:00:00", "2026-03-15T11:30:00"], 0, True, None, ""
    ),
    "dot_time_dot": Reading(["2026-03-01 10.30", "2026-03-02 11.45"], [None, None], 2, False, None, ""),
    "time_first": Reading(
        ["10:00 2026-03-01", "11:30 2026-03-02"],
        ["2026-01-03T10:00:00", "2026-02-03T11:30:00"],
        0,
        True,
        "the day and month order",
        "",
    ),
    "hour_am_no_minutes": Reading(
        ["03/01/2026 10 AM", "03/15/2026 2 PM"], ["2026-01-03", "2026-03-15"], 0, False, None, ""
    ),
    "at_word": Reading(
        ["2026-03-01 at 10:00", "2026-03-02 at 11:30"],
        ["2026-03-01T10:00:00", "2026-03-02T11:30:00"],
        0,
        True,
        None,
        "",
    ),
    "name_ordinal_comma": Reading(
        ["Mar 1st, 2026", "Mar 15th, 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""
    ),
    "iso_week": Reading(["2026-W09-7", "2026-W10-1"], [None, None], 2, False, None, ""),
    "iso_ordinal_day": Reading(["2026-060", "2026-074"], [None, None], 2, False, None, ""),
    "iso_fraction_z": Reading(
        ["2026-03-01T10:00:00.123Z", "2026-03-02T11:30:00.5Z"],
        ["2026-03-01T10:00:00.123000+00:00", "2026-03-02T11:30:00.500000+00:00"],
        0,
        True,
        None,
        "",
    ),
    "iso_seconds_compact_offset": Reading(
        ["2026-03-01T10:00:00+0100", "2026-03-02T11:30:00+0100"],
        ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"],
        0,
        True,
        None,
        "",
    ),
    "compact_seconds": Reading(
        ["20260301T100000", "20260315T113000"], ["2026-01-03", "2026-03-15"], 0, False, None, ""
    ),
    "compact_dash_time": Reading(
        ["20260301 10:00", "20260315 11:30"], ["2026-01-03T10:00:00", "2026-03-15T11:30:00"], 0, True, None, ""
    ),
    "month_slash_year": Reading(
        ["03/2026", "04/2026"], ["2026-03-01", "2026-04-01"], 0, False, "the day and month order", ""
    ),
    "year_month_slash": Reading(["2026/03", "2026/04"], ["2026-03-01", "2026-04-01"], 0, False, None, ""),
    "iso_hours_minutes_am": Reading(
        ["2026-03-01 10:00AM", "2026-03-01 02:30PM"], ["2026-03-01T10:00:00", "2026-03-01T14:30:00"], 0, True, None, ""
    ),
    "dot_am_pm": Reading(
        ["01.03.2026 10:00 PM", "15.03.2026 11:30 AM"],
        ["2026-03-01T22:00:00", "2026-03-15T11:30:00"],
        0,
        True,
        None,
        "",
    ),
    "weekday_short": Reading(["Sun 1 Mar 2026", "Sun 15 Mar 2026"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "rfc2822": Reading(
        ["Sun, 01 Mar 2026 10:00:00 +0100", "Sun, 15 Mar 2026 11:30:00 +0100"],
        ["2026-03-01T10:00:00+01:00", "2026-03-15T11:30:00+01:00"],
        0,
        True,
        None,
        "",
    ),
    "lone_hour_t_lower": Reading(["2026-03-01t05", "2026-03-01t06"], ["2026-03-01", "2026-03-01"], 0, False, None, ""),
    "lone_hour_dot_date": Reading(["01.03.2026 10", "15.03.2026 11"], ["2026-03-01", "2026-03-15"], 0, False, None, ""),
    "lone_hour_slash_date": Reading(
        ["01/03/2026T10", "15/03/2026T11"], ["2026-03-01", "2026-03-15"], 0, False, None, ""
    ),
    "space_number_name_year": Reading(
        ["1 March 23", "15 March 23"], ["2023-03-01", "2023-03-15"], 0, False, "the century of two-digit years", ""
    ),
    "space_number_three_groups": Reading(
        ["01 03 23", "15 03 23"], ["2023-03-01", "2023-03-15"], 0, False, "the century of two-digit years", ""
    ),
    "space_number_name_first": Reading(
        ["Mar 1 23", "Mar 15 23"], ["2023-03-01", "2023-03-15"], 0, False, "the century of two-digit years", ""
    ),
    "space_number_after_month": Reading(["2026-03 10", "2026-04 11"], ["2026-03-10", "2026-04-11"], 0, False, None, ""),
    "zone_cet": Reading(["2026-03-01 10:00 CET", "2026-03-02 11:30 CET"], [None, None], 2, True, None, ""),
    "zone_est": Reading(["2026-03-01 10:00 EST", "2026-03-02 11:30 EST"], [None, None], 2, True, None, ""),
    "zone_gmt": Reading(
        ["2026-03-01 10:00 GMT", "2026-03-02 11:30 GMT"],
        ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:00+00:00"],
        0,
        True,
        None,
        "",
    ),
    "month_with_clock": Reading(
        ["2026-03 10:00", "2026-04 11:30"], ["2026-03-01T10:00:00", "2026-04-01T11:30:00"], 0, True, None, ""
    ),
    "month_name_with_clock": Reading(
        ["Nov 2026 10:00", "Dec 2026 11:30"], ["2026-11-01T10:00:00", "2026-12-01T11:30:00"], 0, True, None, ""
    ),
    "year_with_clock": Reading(
        ["2026 10:00", "2027 11:30"], ["2026-01-01T10:00:00", "2027-01-01T11:30:00"], 0, True, None, ""
    ),
    "month_lone_hour": Reading(["2026-03T10", "2026-04T11"], ["2026-03-10", "2026-04-11"], 0, False, None, ""),
}
PASTED: dict[str, Pasted] = {
    "iso_date": Pasted("datetime", ["2026-03-01", "2026-03-02", "2026-12-31"], []),
    "iso_minutes": Pasted("datetime", ["2026-03-01T10:00:00", "2026-03-02T11:30:00"], []),
    "iso_seconds": Pasted("datetime", ["2026-03-01T10:00:00", "2026-03-02T11:30:15"], []),
    "iso_space_seconds": Pasted("datetime", ["2026-03-01T10:00:00", "2026-03-02T11:30:15"], []),
    "iso_lower_t": Pasted("text", None, []),
    "iso_fraction": Pasted("datetime", ["2026-03-01T10:00:00.123", "2026-03-02T11:30:15.500"], []),
    "iso_fraction_comma": Pasted("datetime", ["2026-03-01T10:00:00.25", "2026-03-02T11:30:15.50"], []),
    "iso_nanoseconds": Pasted("datetime", ["2026-03-01T10:00:00.123456789", "2026-03-02T11:30:15.000000001"], []),
    "iso_z": Pasted("datetime", ["2026-03-01T10:00:00+00:00", "2026-03-02T11:30:00+00:00"], []),
    "iso_offset": Pasted("datetime", ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"], []),
    "iso_offsets_mixed": Pasted(
        "datetime",
        ["2026-03-01T09:00:00+00:00", "2026-07-01T08:00:00+00:00"],
        ["column 'd': times with the UTC offsets +01:00, +02:00 written in UTC (+00:00); the instants are the same"],
    ),
    "iso_offset_compact": Pasted("datetime", ["2026-03-01T10:00:00-05:00", "2026-03-02T11:30:00-05:00"], []),
    "iso_offset_hours": Pasted("datetime", ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"], []),
    "iso_space_offset": Pasted("datetime", ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"], []),
    "iso_date_and_time": Pasted("datetime", ["2026-03-01T10:00:00", "2026-03-02T00:00:00"], []),
    "iso_single_digits": Pasted("text", None, []),
    "year_slash": Pasted("text", None, []),
    "year_dot": Pasted("text", None, []),
    "year_slash_time": Pasted("text", None, []),
    "dot_date": Pasted("datetime", ["2026-03-01", "2026-03-15"], []),
    "dot_single_digits": Pasted("datetime", ["2026-03-01", "2026-03-15"], []),
    "dot_time": Pasted("datetime", ["2026-03-01T10:00:00", "2026-03-15T11:30:00"], []),
    "dot_seconds": Pasted("datetime", ["2026-03-01T10:00:05", "2026-03-15T11:30:59"], []),
    "slash_day_first": Pasted("datetime", ["2026-03-01", "2026-03-15"], []),
    "slash_month_first": Pasted("datetime", ["2026-03-15", "2026-03-01"], []),
    "slash_ambiguous": Pasted(
        "datetime", ["2026-03-01", "2026-04-02"], ["column 'd': day and month order is ambiguous; read as DD/MM/YYYY"]
    ),
    "slash_time": Pasted("datetime", ["2026-03-01T10:00:00", "2026-03-15T23:59:00"], []),
    "dash_day_first": Pasted("text", None, []),
    "dash_month_first": Pasted("text", None, []),
    "dot_two_digit_year": Pasted("text", None, []),
    "slash_two_digit_year": Pasted("text", None, []),
    "two_digit_year_century": Pasted("text", None, []),
    "name_day_month_year": Pasted("text", None, []),
    "name_month_day_comma": Pasted("text", None, []),
    "name_abbreviated": Pasted("text", None, []),
    "name_dashes": Pasted("text", None, []),
    "name_dashes_two_digit": Pasted("text", None, []),
    "name_year_first": Pasted("text", None, []),
    "name_weekday": Pasted("text", None, []),
    "name_ordinal": Pasted("text", None, []),
    "name_with_time": Pasted("text", None, []),
    "name_lower": Pasted("text", None, []),
    "month_year_en": Pasted(
        "datetime",
        ["2026-11-01", "2026-12-01"],
        ["column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"],
    ),
    "month_year_de": Pasted(
        "datetime",
        ["2026-10-01", "2026-11-01"],
        ["column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"],
    ),
    "month_year_de_umlaut": Pasted(
        "datetime",
        ["2026-03-01", "2026-04-01"],
        ["column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"],
    ),
    "month_year_fr": Pasted(
        "datetime",
        ["2026-02-01", "2026-03-01"],
        ["column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"],
    ),
    "month_year_es": Pasted(
        "datetime",
        ["2026-03-01", "2026-04-01"],
        ["column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"],
    ),
    "month_year_it": Pasted(
        "datetime",
        ["2026-03-01", "2026-04-01"],
        ["column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"],
    ),
    "month_year_year_first": Pasted(
        "datetime",
        ["2026-11-01", "2026-12-01"],
        ["column 'd': 2 cells read as months (a month name and a year, each as the first day of the month)"],
    ),
    "day_month_year_de": Pasted("text", None, []),
    "year_month": Pasted(
        "datetime",
        ["2026-03-01", "2026-04-01"],
        ["column 'd': 2 cells read as months (YYYY-MM, each as the first day of the month)"],
    ),
    "quarter": Pasted("text", None, []),
    "quarter_first": Pasted("text", None, []),
    "year_text": Pasted("integer", ["2026", "2027"], []),
    "am_pm_slash": Pasted("text", None, []),
    "am_pm_iso": Pasted("text", None, []),
    "am_pm_compact": Pasted("text", None, []),
    "compact_date": Pasted("integer", ["20260301", "20260315"], []),
    "compact_date_time": Pasted("text", None, []),
    "iso_compact_time": Pasted("text", None, []),
    "empty_cells": Pasted("datetime", ["2026-03-01", "", "2026-03-03"], []),
    "one_unreadable": Pasted("text", None, []),
    "filled_in_month": Pasted("text", None, []),
    "time_alone": Pasted("text", None, []),
    "now_word": Pasted("text", None, []),
    "impossible_day": Pasted("text", None, []),
    "far_years": Pasted("datetime", ["0001-01-01", "9999-12-31"], []),
    "century_turn": Pasted("datetime", ["1999-12-31", "2000-01-01"], []),
    "naive_and_zoned": Pasted("text", None, []),
    "f4_offset_east": Pasted(
        "text",
        None,
        [
            "column 'd': kept as text: every cell is a date followed directly by a UTC offset, with no time (YYYY-MM-DD±HH:MM or YYYY-MM-DDZ)"
        ],
    ),
    "f4_offset_west": Pasted(
        "text",
        None,
        [
            "column 'd': kept as text: every cell is a date followed directly by a UTC offset, with no time (YYYY-MM-DD±HH:MM or YYYY-MM-DDZ)"
        ],
    ),
    "f4_z": Pasted(
        "text",
        None,
        [
            "column 'd': kept as text: every cell is a date followed directly by a UTC offset, with no time (YYYY-MM-DD±HH:MM or YYYY-MM-DDZ)"
        ],
    ),
    "f4_mixed_plain": Pasted("text", None, []),
    "f4_hour_labels": Pasted("text", None, []),
    "f4_beside_times": Pasted("text", None, []),
    "f4_beside_unreadable": Pasted("text", None, []),
    "lone_hour_t": Pasted("text", None, []),
    "lone_hour_space": Pasted("text", None, []),
    "utc_word_time": Pasted("text", None, []),
    "utc_word_date": Pasted("text", None, []),
    "space_before_offset": Pasted("text", None, []),
    "name_comma_time_am": Pasted("text", None, []),
    "iso_fraction_offset": Pasted("datetime", ["2026-03-01T10:00:00.50+01:00", "2026-03-02T11:30:00.25+01:00"], []),
    "iso_hour_z": Pasted("text", None, []),
    "iso_hour_offset": Pasted("text", None, []),
    "name_comma_time": Pasted("text", None, []),
    "iso_space_z": Pasted("text", None, []),
    "dot_comma_time": Pasted("text", None, []),
    "dot_time_dot": Pasted("text", None, []),
    "time_first": Pasted("text", None, []),
    "hour_am_no_minutes": Pasted("text", None, []),
    "at_word": Pasted("text", None, []),
    "name_ordinal_comma": Pasted("text", None, []),
    "iso_week": Pasted("text", None, []),
    "iso_ordinal_day": Pasted("text", None, []),
    "iso_fraction_z": Pasted("datetime", ["2026-03-01T10:00:00.123+00:00", "2026-03-02T11:30:00.500+00:00"], []),
    "iso_seconds_compact_offset": Pasted("datetime", ["2026-03-01T10:00:00+01:00", "2026-03-02T11:30:00+01:00"], []),
    "compact_seconds": Pasted("text", None, []),
    "compact_dash_time": Pasted("text", None, []),
    "month_slash_year": Pasted("text", None, []),
    "year_month_slash": Pasted("text", None, []),
    "iso_hours_minutes_am": Pasted("text", None, []),
    "dot_am_pm": Pasted("text", None, []),
    "weekday_short": Pasted("text", None, []),
    "rfc2822": Pasted("text", None, []),
    "lone_hour_t_lower": Pasted("text", None, []),
    "lone_hour_dot_date": Pasted("text", None, []),
    "lone_hour_slash_date": Pasted("text", None, []),
    "space_number_name_year": Pasted("text", None, []),
    "space_number_three_groups": Pasted("text", None, []),
    "space_number_name_first": Pasted("text", None, []),
    "space_number_after_month": Pasted("text", None, []),
    "zone_cet": Pasted("text", None, []),
    "zone_est": Pasted("text", None, []),
    "zone_gmt": Pasted("text", None, []),
    "month_with_clock": Pasted("text", None, []),
    "month_name_with_clock": Pasted("text", None, []),
    "year_with_clock": Pasted("text", None, []),
    "month_lone_hour": Pasted("text", None, []),
}


def _timed(name: str, values: list[str | None]) -> Reading:
    """The row `name` read as before, now written with the times it holds."""
    return Reading(READINGS[name].cells, values, READINGS[name].failed, True, READINGS[name].guess, "")


CHANGED: dict[str, Reading] = {
    # A time after the date is read by its shape, not by a colon: these cells were read with their time and
    # written without it.
    "lone_hour_t": _timed(
        "lone_hour_t", ["2026-03-01T00:00:00", "2026-03-01T01:00:00", "2026-03-01T02:00:00", "2026-03-01T03:00:00"]
    ),
    "lone_hour_t_lower": _timed("lone_hour_t_lower", ["2026-03-01T05:00:00", "2026-03-01T06:00:00"]),
    # A number alone after a space is no hour (it may be a count or a label), where pandas read it as one: unread.
    "lone_hour_space": Reading(READINGS["lone_hour_space"].cells, [None, None], 2),
    "lone_hour_dot_date": Reading(READINGS["lone_hour_dot_date"].cells, [None, None], 2),
    "lone_hour_slash_date": _timed("lone_hour_slash_date", ["2026-03-01T10:00:00", "2026-03-15T11:00:00"]),
    "iso_hour_z": _timed("iso_hour_z", ["2026-03-01T10:00:00+00:00", "2026-03-02T11:00:00+00:00"]),
    "am_pm_compact": _timed("am_pm_compact", ["2026-03-01T10:00:00", "2026-03-01T14:00:00"]),
    "hour_am_no_minutes": _timed("hour_am_no_minutes", ["2026-01-03T10:00:00", "2026-03-15T14:00:00"]),
    "iso_compact_time": _timed("iso_compact_time", ["2026-03-01T10:00:00", "2026-03-15T11:30:00"]),
    "compact_date_time": _timed("compact_date_time", ["2026-01-03T10:00:00", "2026-03-15T11:30:00"]),
    "compact_seconds": _timed("compact_seconds", ["2026-01-03T10:00:00", "2026-03-15T11:30:00"]),
    # A colon in a cell that did not read no longer writes the others with a midnight nobody wrote.
    "time_alone": Reading(["13:00", "2026-03-01"], [None, "2026-03-01"], 1),
    "zone_cet": Reading(READINGS["zone_cet"].cells, [None, None], 2),
    "zone_est": Reading(READINGS["zone_est"].cells, [None, None], 2),
    "fmt_dot_unreadable_colon": Reading(
        ["01.03.2026", "n.a.: none"], ["2026-03-01", None], 1, guess="the day and month order"
    ),
    # A time before the date is more after the date than a time: unreadable, where pandas read 3 January.
    "time_first": Reading(READINGS["time_first"].cells, [None, None], 2),
    # A time stands only after a date that names a day: after a month or a year it is no reading of the parser's,
    # and pandas took a lone hour there for the day (`2026-03T10` as 10 March).
    "month_with_clock": Reading(READINGS["month_with_clock"].cells, [None, None], 2),
    "month_name_with_clock": Reading(READINGS["month_name_with_clock"].cells, [None, None], 2),
    "year_with_clock": Reading(READINGS["year_with_clock"].cells, [None, None], 2),
    "month_lone_hour": Reading(READINGS["month_lone_hour"].cells, [None, None], 2),
}
"""The rows whose reading the strict date rule changes on purpose, with the reading they have now."""


def test_the_table_is_broad() -> None:
    assert len(READINGS) >= 60 and set(PASTED) == set(READINGS)


@pytest.mark.parametrize("name", list(READINGS))
def test_a_conversion_reads_as_it_did(name: str) -> None:
    assert converted(READINGS[name].cells) == CHANGED.get(name, READINGS[name])


@pytest.mark.parametrize("name", list(PASTED))
def test_the_paste_types_as_it_did(name: str) -> None:
    assert pasted(READINGS[name].cells) == PASTED[name]


FORMATTED: dict[str, tuple[str, bool, Reading]] = {
    "fmt_dot": ("DD.MM.YYYY", False, Reading(["01.03.2026", "15.03.2026"], ["2026-03-01", "2026-03-15"])),
    "fmt_dot_time": (
        "DD.MM.YYYY",
        False,
        Reading(["01.03.2026 10:00", "15.03.2026"], ["2026-03-01T10:00:00", "2026-03-15T00:00:00"], with_time=True),
    ),
    "fmt_dot_unreadable_colon": (
        "DD.MM.YYYY",
        False,
        Reading(["01.03.2026", "n.a.: none"], ["2026-03-01T00:00:00", None], 1, True, "the day and month order"),
    ),
    "fmt_iso_t_seconds": (
        "YYYY-MM-DD",
        False,
        Reading(["2026-03-01T10:00:05", "2026-03-15"], ["2026-03-01T10:00:05", "2026-03-15T00:00:00"], with_time=True),
    ),
    "fmt_iso_offsets": (
        "YYYY-MM-DD",
        False,
        Reading(
            ["2026-03-01+01:00", "2026-03-02+01:00"],
            ["2026-03-01", "2026-03-02"],
            guess="the days of 2 dates with a UTC offset as written, the offset dropped",
        ),
    ),
    "fmt_iso_lone_hour": ("YYYY-MM-DD", False, Reading(["2026-03-01T00", "2026-03-01T01"], [None, None], 2)),
    "fmt_month_first": ("MM/DD/YYYY", False, Reading(["03/15/2026", "03/01/2026"], ["2026-03-15", "2026-03-01"])),
    "fmt_compact": ("YYYYMMDD", False, Reading(["20260301", "20260315"], ["2026-03-01", "2026-03-15"])),
    "fmt_year_month": ("YYYY-MM", False, Reading(["2026-03", "2026-04"], ["2026-03-01", "2026-04-01"])),
    "fmt_month_year_slash": ("MM/YYYY", False, Reading(["03/2026", "04/2026"], ["2026-03-01", "2026-04-01"])),
    "fmt_year": ("YYYY", False, Reading(["2026", "2027"], ["2026-01-01", "2027-01-01"])),
    "fmt_month_year_numbers": ("MM.YYYY", True, Reading([3.202, 4.2026], ["2020-03-01", "2026-04-01"])),
    "fmt_year_month_time": (
        "YYYY-MM",
        False,
        Reading(["2026-03 10:00", "2026-04 11:30"], ["2026-03-01T10:00:00", "2026-04-01T11:30:00"], with_time=True),
    ),
    "fmt_year_month_t_time": (
        "YYYY-MM",
        False,
        Reading(["2026-03T10:00", "2026-04T11:30"], ["2026-03-01T10:00:00", "2026-04-01T11:30:00"], with_time=True),
    ),
    "fmt_month_slash_year_time": (
        "MM/YYYY",
        False,
        Reading(["03/2026 10:00", "04/2026 11:30"], ["2026-03-01T10:00:00", "2026-04-01T11:30:00"], with_time=True),
    ),
    "fmt_month_dot_year_time": (
        "MM.YYYY",
        False,
        Reading(["03.2026 10:00", "04.2026 11:30"], ["2026-03-01T10:00:00", "2026-04-01T11:30:00"], with_time=True),
    ),
    "fmt_dot_range": (
        "DD.MM.YYYY",
        False,
        Reading(["01.03.2026-05.03.2026", "06.03.2026"], [None, "2026-03-06"], 1, guess="the day and month order"),
    ),
}
"""Conversions with a format, which read every cell in exactly that format and an optional time after it."""

SET_TYPE: dict[str, tuple[str, dict[str, str], dict[str, object]]] = {
    "set_type_integer_compact": (
        "d,v\n20260301,1\n20260315,2\n",
        {"op": "set_type", "column": "d", "type": "datetime", "name": "e"},
        {
            "csv": "d,v,e\n20260301,1,2026-01-03\n20260315,2,2026-03-15\n",
            "changes": [
                "new column e: 2 cells of d read as dates (format inferred, day before month); d stays as it is"
            ],
        },
    ),
    "set_type_text_dates": (
        "d,v\n1 March 2026,1\n15 March 2026,2\n",
        {"op": "set_type", "column": "d", "type": "datetime", "name": "e"},
        {
            "csv": "d,v,e\n1 March 2026,1,2026-03-01\n15 March 2026,2,2026-03-15\n",
            "changes": [
                "new column e: 2 cells of d read as dates (format inferred, day before month); d stays as it is"
            ],
        },
    ),
    "set_type_in_place": (
        "d,v\n01.03.2026 10:00,1\nunknown,2\n",
        {"op": "set_type", "column": "d", "type": "datetime"},
        {"refused": "column 'd': 1 of 2 cells cannot be read as dates"},
    ),
    "set_type_numbers_years": (
        "d,v\n2026,1\n2027,2\n",
        {"op": "set_type", "column": "d", "type": "datetime", "date_format": "YYYY", "name": "e"},
        {
            "csv": "d,v,e\n2026,1,2026-01-01\n2027,2,2027-01-01\n",
            "changes": ["new column e: 2 cells of d read as years (YYYY, each as 1 January); d stays as it is"],
        },
    ),
}
"""Whole `set_type` operations on a pasted column, the stored cells and the change line included."""
OPERATIONS = TypeAdapter(list[Operation])


def formatted(cells: list[Any], date_format: str, numbers: bool) -> Reading:
    series = pd.Series(cells, dtype="float64" if numbers else "str", name="d")
    try:
        conversion = _date_conversion(series, date_format)
    except PrepareError as error:
        return Reading(cells, refused=error.message)
    values = [_cell_text(value, conversion.with_time) for value in conversion.values]
    return Reading(cells, values, conversion.failed, conversion.with_time, conversion.guess, conversion.notice)


@pytest.mark.parametrize("name", list(FORMATTED))
def test_a_conversion_with_a_format_reads_as_it_did(name: str) -> None:
    date_format, numbers, reading = FORMATTED[name]

    assert formatted(list(reading.cells), date_format, numbers) == CHANGED.get(name, reading)


@pytest.mark.parametrize("name", list(SET_TYPE))
def test_a_set_type_stores_as_it_did(name: str) -> None:
    text, operation, expected = SET_TYPE[name]
    try:
        prepared = apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))
    except PrepareError as error:
        assert {"refused": error.message} == expected
        return
    assert {"csv": prepared.csv, "changes": prepared.changes} == expected


UNREADABLE: dict[str, list[str | None]] = {
    "a range of days": ["2026-03-01-2026-03-05", "2026-03-06-2026-03-09", "2026-03-10-2026-03-12"],
    "a sign and digits after a space": ["2026-03-01 -05:00", "2026-03-02 -05:00"],
    "a sign and digits after a slash date": ["2026/03/01-05:00", "2026/03/02-05:00"],
    "a sign and digits after a dot date": ["13.03.2026-05:00", "14.03.2026-05:00"],
    "a sign and digits after the T": ["2026-03-01T-05:00", "2026-03-02T-05:00"],
    "an interval of days": ["2026-03-01/05", "2026-03-06/09"],
    "an offset after a space and no time": ["2026-03-01 +01:00", "2026-03-02 +01:00"],
    "an interval ending at 00": ["2026-03-01/00", "2026-03-02/00"],
    "a zero offset after a space": ["2026-03-01 -00:00", "2026-03-02 -00:00"],
    "a zero offset after the T": ["2026-03-01T-00:00", "2026-03-02T-00:00"],
    "an hour with am after a month": ["2026-03 10am", "2026-04 11am"],
    "an hour with AM after a year": ["2026 10 AM", "2027 11 AM"],
    "a spaced dash and a number": ["2026-03-01 - 05", "2026-03-02 - 06"],
    "a spaced slash and a number": ["2026-03-01 / 05", "2026-03-06 / 09"],
    "a spaced dash and an hour": ["2026-03-01 - 05:00", "2026-03-02 - 05:00"],
    "a spaced dash after a dot date": ["01.03.2026 - 05", "02.03.2026 - 06"],
    "a number after a space": ["2026-03-01 10", "2026-03-01 11"],
    "a number after a comma": ["2026-03-01, 10", "2026-03-02, 11"],
}
"""Cells with more after their date than a time: pandas read a range as days with made-up offsets (2, 7 and 11
March, beside a notice of offsets no cell holds), a sign and digits as 05:00, and an interval as its first day."""


class TestStrictRule:
    """A cell converts only as a date alone or a date followed by a time; anything else after the date is unread."""

    @pytest.mark.parametrize("cells", list(UNREADABLE.values()), ids=list(UNREADABLE))
    def test_more_after_the_date_than_a_time_is_unreadable(self, cells: list[str | None]) -> None:
        assert converted(cells) == Reading(cells, [None] * len(cells), len(cells), False, None, "")

    @pytest.mark.parametrize(
        "cells", [*UNREADABLE.values(), ["2026-03-01T00", "2026-03-01T01"]], ids=[*UNREADABLE, "lone hours"]
    )
    def test_the_paste_keeps_such_cells_as_text(self, cells: list[str | None]) -> None:
        """The parser types none of these forms: the rule is the conversion's, after the paste."""
        assert pasted(cells) == Pasted("text", None, [])

    @pytest.mark.parametrize(
        ("cells", "reason"),
        [
            (
                ["2026-03-01-2026-03-05", "2026-03-06-2026-03-09", "2026-03-10-2026-03-12"],
                "3 of them hold more after their date than a time",
            ),
            (["13.03.2026-05:00", "unknown", "14.03.2026"], "1 of them holds more after its date than a time"),
        ],
    )
    def test_the_refusal_says_why_the_cells_are_no_dates(self, cells: list[str], reason: str) -> None:
        """The cells that hold a date and more are named by that shape, beside the count of the refusal, so the reply
        can say why: a refusal without a reason was the first defect of the dates with an offset."""
        text = "d,v\n" + "".join(f"{cell},{index}\n" for index, cell in enumerate(cells))
        operation = {"op": "set_type", "column": "d", "type": "datetime", "name": "e"}

        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

        failed = sum(cell != "14.03.2026" for cell in cells)
        assert caught.value.message == (
            f"column 'd': {failed} of 3 cells cannot be read as dates; {reason} (such as a second date, more numbers "
            "or a sign and digits), which no reading guesses"
        )

    def test_a_cell_the_gate_passes_as_a_date_alone_still_holds_no_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Fail closed: should the gate take a cell with more after its date for a date alone, the time pandas finds
        in it makes it unreadable, never a date with that time dropped. Reached by breaking the gate here."""
        monkeypatch.setattr(prepare_module, "_date_cell", lambda text: False)
        cells: list[str | None] = ["2026-03-01 -05:00", "2026-03-02 -05:00", "2026-03-03"]

        assert converted(cells) == Reading(cells, [None, None, "2026-03-03"], 2)

    def test_a_refusal_for_cells_of_no_date_keeps_its_words(self) -> None:
        text = "d,v\nunknown,1\nn.a.: none,2\n2026-03-01,3\n"
        operation = {"op": "set_type", "column": "d", "type": "datetime", "name": "e"}

        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(text), OPERATIONS.validate_python([operation]))

        assert caught.value.message == "column 'd': 2 of 3 cells cannot be read as dates"

    def test_a_lone_hour_is_read_as_that_hour_and_written_with_it(self) -> None:
        cells: list[str | None] = ["2026-03-01T00", "2026-03-01T01", "2026-03-01T02", "2026-03-01T03"]

        assert converted(cells) == Reading(
            cells,
            ["2026-03-01T00:00:00", "2026-03-01T01:00:00", "2026-03-01T02:00:00", "2026-03-01T03:00:00"],
            0,
            True,
            None,
            "",
        )

    def test_one_such_cell_among_dates_is_counted_and_makes_the_reading_uncertain(self) -> None:
        cells: list[str | None] = [f"2026-03-{day:02d}" for day in range(1, 11)] + ["2026-03-11-2026-03-15"]

        reading = converted(cells)

        assert reading.failed == 1 and reading.values == [*cells[:10], None] and reading.notice == ""
        dry = dry_run(read_frame(parse_dataset("d\n" + "\n".join(str(cell) for cell in cells) + "\n")), "d", "datetime")
        assert dry is not None and (dry.read, dry.present, dry.certain) == (10, 11, False)
