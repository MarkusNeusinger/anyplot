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

import pandas as pd
import pytest

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import PrepareError, _cell_text, _date_conversion


@dataclass(frozen=True)
class Reading:
    """What a conversion of `cells` gives: the cells as `data.csv` writes them (None for a missing one), the cells
    that failed, whether the column is written with a time, the guess and the notice; or the refusal."""

    cells: list[str | None]
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
}


CHANGED: dict[str, Reading] = {}
"""The rows whose reading the strict date rule changes on purpose, with the reading they have now."""


def test_the_table_is_broad() -> None:
    assert len(READINGS) >= 60 and set(PASTED) == set(READINGS)


@pytest.mark.parametrize("name", list(READINGS))
def test_a_conversion_reads_as_it_did(name: str) -> None:
    assert converted(READINGS[name].cells) == CHANGED.get(name, READINGS[name])


@pytest.mark.parametrize("name", list(PASTED))
def test_the_paste_types_as_it_did(name: str) -> None:
    assert pasted(READINGS[name].cells) == PASTED[name]
