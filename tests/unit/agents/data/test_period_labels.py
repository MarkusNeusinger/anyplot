"""Conditions on the period labels an `aggregate` writes, and the facts the change lines give about them, in
agents/anyplot/data/prepare.py.

A `month`, `quarter` or `year` key is text (`2019-01`, `2019-Q1`, `2019`), compared as text. A bound of another
shape compared wrongly without an error: `2019-01` sorts before `2019-01-01`, so `ge 2019-01-01` left January out.
Such a bound is now refused with the column's form, the aggregate line names that form, and a `keep_rows` line with
`where` names the lowest and the highest value the kept rows have. Every dataset here is invented.
"""

import re
from typing import Any

import pytest

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.schemas import MAX_COLUMN_NAME_CHARS, MAX_NOTE_CHARS

from .test_prepare import cells, classify, dtypes, failure, prepare, rows


MONTHS = [
    "2018-05",
    "2018-06",
    "2018-07",
    "2018-08",
    "2018-09",
    "2018-10",
    "2018-11",
    "2018-12",
    "2019-01",
    "2019-02",
    "2019-03",
    "2019-04",
]
# Two readings a month from May 2018 to April 2019, oldest first.
DAILY_ROWS = [
    row
    for step, month in enumerate(MONTHS)
    for row in (f"{month}-03,Ost,{step + 1}", f"{month}-18,West,{2 * step + 1}.5")
]
DAILY = "Messtag,Kanal,Liter\n" + "\n".join(DAILY_ROWS) + "\n"
BY_MONTH = {"op": "aggregate", "by": ["Messtag"], "column": "Liter", "how": "sum", "period": "month"}
MONTH_FORM = "text labels YYYY-MM, such as 2024-03"
QUARTER_FORM = "text labels YYYY-Qn, such as 2024-Q1"
DIGITS_FORM = "text labels of four digits, such as 2024"
# Four-digit codes kept text by a leading zero, as the parser keeps `007`.
CODES = "Kennung,Lager\n0815,Nord\n4410,Süd\n5020,West\n4410,Ost\n"


def cond(column: str, test: str, value: object = None) -> dict[str, Any]:
    condition: dict[str, Any] = {"column": column, "test": test}
    if value is not None:
        condition["value"] = value
    return condition


def keep(*where: dict[str, Any]) -> dict[str, Any]:
    return {"op": "keep_rows", "where": list(where)}


def refusal(form: str, given: str, column: str = "Messtag") -> tuple[str, str]:
    return (
        "invalid_operation",
        f"column '{column}' holds {form}, which compare as text: give the value in that form, not as {given}",
    )


class TestAConditionOnPeriodLabels:
    def test_a_day_bound_on_month_labels_is_refused_and_names_their_form(self) -> None:
        """As text, this range would have left January out without a word."""
        year = keep(cond("Messtag", "ge", "2019-01-01"), cond("Messtag", "le", "2019-12-31"))

        assert failure(DAILY, BY_MONTH, year) == refusal(MONTH_FORM, "a date")

    def test_a_bound_in_the_labels_form_keeps_every_month_of_the_range(self) -> None:
        prepared = prepare(DAILY, BY_MONTH, keep(cond("Messtag", "ge", "2019-01"), cond("Messtag", "le", "2019-12")))

        assert cells(prepared, 0) == MONTHS[8:]
        assert prepared.changes[1] == (
            "kept 4 of 12 rows where Messtag ≥ '2019-01' and Messtag ≤ '2019-12', 8 dropped; in the rows kept, "
            "Messtag is at least '2019-01' and at most '2019-04'"
        )

    @pytest.mark.parametrize(
        ("period", "test", "value", "form", "given"),
        [
            ("month", "ne", "2019-01-01", MONTH_FORM, "a date"),
            ("month", "gt", "2018-12-31T23:00", MONTH_FORM, "a date"),
            ("month", "ge", "2019-01-01Z", MONTH_FORM, "a date"),
            ("month", "le", "2019-03-31+01:00", MONTH_FORM, "a date"),
            ("month", "lt", "2019-03-01-0500", MONTH_FORM, "a date"),
            ("month", "ge", "2019-02-01+02", MONTH_FORM, "a date"),
            ("month", "le", "2019", MONTH_FORM, "four digits"),
            ("month", "eq", "2019-Q1", MONTH_FORM, "YYYY-Qn"),
            ("quarter", "le", "2019-06-30", QUARTER_FORM, "a date"),
            ("quarter", "lt", "2019-07", QUARTER_FORM, "YYYY-MM"),
            ("year", "ge", "2018-01-01", DIGITS_FORM, "a date"),
            ("year", "eq", "2019-01", DIGITS_FORM, "YYYY-MM"),
        ],
    )
    def test_a_value_of_another_date_or_period_shape_is_refused(
        self, period: str, test: str, value: str, form: str, given: str
    ) -> None:
        aggregate = {**BY_MONTH, "period": period}

        assert failure(DAILY, aggregate, keep(cond("Messtag", test, value))) == refusal(form, given)

    def test_a_json_number_is_read_as_its_text_and_checked_the_same_way(self) -> None:
        assert failure(DAILY, BY_MONTH, keep(cond("Messtag", "ge", 2019))) == refusal(MONTH_FORM, "four digits")

    def test_one_value_of_another_shape_in_an_any_of_list_refuses_the_condition(self) -> None:
        listed = {"column": "Messtag", "test": "eq", "values": ["2019-01", "2019-02-01"]}

        assert failure(DAILY, BY_MONTH, keep(listed)) == refusal(MONTH_FORM, "a date")

    def test_every_operation_with_conditions_checks_them(self) -> None:
        before_2019 = [cond("Messtag", "lt", "2019-01-01")]

        assert failure(DAILY, BY_MONTH, {"op": "drop_rows", "where": before_2019}) == refusal(MONTH_FORM, "a date")
        assert failure(DAILY, BY_MONTH, classify("Jahr", (before_2019, "alt"), otherwise="neu")) == refusal(
            MONTH_FORM, "a date"
        )

    def test_year_labels_take_a_bound_of_four_digits(self) -> None:
        prepared = prepare(DAILY, {**BY_MONTH, "period": "year"}, keep(cond("Messtag", "ge", "2019")))

        assert cells(prepared, 0) == ["2019"]
        assert prepared.changes[1] == (
            "kept 1 of 2 rows where Messtag ≥ '2019', 1 dropped; in the rows kept, Messtag is '2019'"
        )

    def test_contains_still_searches_the_labels_text(self) -> None:
        prepared = prepare(DAILY, BY_MONTH, keep(cond("Messtag", "contains", "2019")))

        assert cells(prepared, 0) == MONTHS[8:]


class TestFourDigitCodesKeptText:
    """A text column of four-digit codes has the shape of year labels: a value with no date or period shape keeps
    the comparison as text."""

    def test_the_codes_are_text(self) -> None:
        assert parse_dataset(CODES).column_dtypes["Kennung"] == "text"

    def test_eq_ne_and_order_compare_the_codes_as_text(self) -> None:
        assert cells(prepare(CODES, keep(cond("Kennung", "eq", "4410"))), 1) == ["Süd", "Ost"]
        assert cells(prepare(CODES, keep(cond("Kennung", "ne", "4410"))), 1) == ["Nord", "West"]
        assert cells(prepare(CODES, keep(cond("Kennung", "ge", "4410"))), 1) == ["Süd", "West", "Ost"]
        listed = {"column": "Kennung", "test": "eq", "values": ["0815", "5020"]}
        assert cells(prepare(CODES, keep(listed)), 1) == ["Nord", "West"]

    def test_a_value_with_no_date_shape_compares_as_text(self) -> None:
        for value in ("ABC", "481", "12345678", "44100"):
            assert len(rows(prepare(CODES, keep(cond("Kennung", "ne", value))))) == 5

    def test_a_date_on_codes_is_refused_without_calling_them_years(self) -> None:
        code, message = failure(CODES, keep(cond("Kennung", "eq", "2019-01-01")))

        assert (code, message) == refusal(DIGITS_FORM, "a date", column="Kennung")
        assert "year" not in message

    def test_the_kept_line_names_the_lowest_and_highest_kept_code_in_words_that_fit_codes(self) -> None:
        """Codes have the shape of year labels, so their line names the two ends too, as values, not as a span of
        time: the codes between them may be gone."""
        prepared = prepare(CODES, keep(cond("Kennung", "ne", "4410")))

        assert prepared.changes == [
            "kept 2 of 4 rows where Kennung ≠ '4410', 2 dropped; in the rows kept, Kennung is at least '0815' and at "
            "most '5020'"
        ]


class TestTheAggregateNamesTheKeysForm:
    @pytest.mark.parametrize(
        ("period", "words", "shape"),
        [
            ("month", "month, as text labels YYYY-MM", r"[0-9]{4}-[0-9]{2}"),
            ("quarter", "quarter, as text labels YYYY-Qn", r"[0-9]{4}-Q[1-4]"),
            ("year", "year, as text labels YYYY", r"[0-9]{4}"),
        ],
    )
    def test_the_line_names_the_text_form_the_key_has(self, period: str, words: str, shape: str) -> None:
        prepared = prepare(DAILY, {**BY_MONTH, "period": period})

        assert prepared.changes[0].startswith(f"summed Liter by Messtag ({words}): ")
        assert all(re.fullmatch(shape, cell) for cell in cells(prepared, 0))
        assert dtypes(prepared)["Messtag"] == "text"

    def test_a_week_stays_a_date_and_its_line_is_unchanged(self) -> None:
        prepared = prepare(DAILY, {**BY_MONTH, "period": "week"})

        assert prepared.changes[0].startswith("summed Liter by Messtag (ISO week, each as its Monday): ")
        assert dtypes(prepared)["Messtag"] == "datetime"


class TestTheLowestAndHighestKeptValue:
    def test_a_date_column_names_its_lowest_and_highest_kept_date_whatever_the_row_order(self) -> None:
        newest_first = "Messtag,Kanal,Liter\n" + "\n".join(reversed(DAILY_ROWS)) + "\n"
        autumn = keep(cond("Messtag", "ge", "2018-08-01"), cond("Messtag", "le", "2018-10-31"))

        prepared = prepare(newest_first, autumn)

        assert cells(prepared, 0)[0] == "2018-10-18"  # the rows keep their order
        assert prepared.changes == [
            "kept 6 of 24 rows where Messtag ≥ 2018-08-01 and Messtag ≤ 2018-10-31, 18 dropped; in the rows kept, "
            "Messtag is at least 2018-08-03 and at most 2018-10-18"
        ]

    def test_an_any_of_selection_names_its_two_ends_without_claiming_the_months_between(self) -> None:
        """July and December only, five months apart: the line names the lowest and the highest kept label, never a
        span from one to the other, since the months between them are dropped."""
        listed = {"column": "Messtag", "test": "eq", "values": ["2018-07", "2018-12"]}

        prepared = prepare(DAILY, BY_MONTH, keep(listed))

        assert cells(prepared, 0) == ["2018-07", "2018-12"]
        assert prepared.changes[1] == (
            "kept 2 of 12 rows where Messtag is '2018-07' or '2018-12', 10 dropped; in the rows kept, Messtag is at "
            "least '2018-07' and at most '2018-12'"
        )

    def test_an_order_test_over_a_month_the_data_lacks_names_the_two_ends_only(self) -> None:
        """The source has no reading in November 2018: the bounds keep three months, and the line's two values do
        not claim the missing one."""
        without_november = "Messtag,Kanal,Liter\n" + "\n".join(r for r in DAILY_ROWS if "2018-11" not in r) + "\n"
        autumn = keep(cond("Messtag", "ge", "2018-09"), cond("Messtag", "le", "2018-12"))

        prepared = prepare(without_november, BY_MONTH, autumn)

        assert cells(prepared, 0) == ["2018-09", "2018-10", "2018-12"]
        assert prepared.changes[1] == (
            "kept 3 of 11 rows where Messtag ≥ '2018-09' and Messtag ≤ '2018-12', 8 dropped; in the rows kept, "
            "Messtag is at least '2018-09' and at most '2018-12'"
        )

    def test_period_labels_and_dates_each_get_their_two_values_in_the_order_of_the_conditions(self) -> None:
        text = "Quartal,Stichtag,Wert\n2017-Q4,2017-12-15,3\n2018-Q1,2018-02-10,5\n2018-Q2,2018-05-20,4\n2018-Q3,,6\n"

        prepared = prepare(text, keep(cond("Quartal", "ge", "2018-Q1"), cond("Stichtag", "le", "2018-06-30")))

        assert dtypes(prepared) == {"Quartal": "text", "Stichtag": "datetime", "Wert": "integer"}
        assert prepared.changes == [
            "kept 2 of 4 rows where Quartal ≥ '2018-Q1' and Stichtag ≤ 2018-06-30, 2 dropped; 1 of them has no "
            "Stichtag; in the rows kept, Quartal is at least '2018-Q1' and at most '2018-Q2' and Stichtag is at "
            "least 2018-02-10 and at most 2018-05-20"
        ]

    def test_one_value_is_named_once(self) -> None:
        prepared = prepare(DAILY, BY_MONTH, keep(cond("Messtag", "eq", "2018-09")))

        assert prepared.changes[1] == (
            "kept 1 of 12 rows where Messtag = '2018-09', 11 dropped; in the rows kept, Messtag is '2018-09'"
        )

    def test_a_line_that_keeps_every_row_names_the_two_values_too(self) -> None:
        prepared = prepare(DAILY, BY_MONTH, keep(cond("Messtag", "ge", "2018-05")))

        assert prepared.changes[1] == (
            "kept all 12 rows; every one matches Messtag ≥ '2018-05'; in the rows kept, Messtag is at least "
            "'2018-05' and at most '2019-04'"
        )

    def test_numbers_other_text_and_a_test_for_empty_cells_name_no_range(self) -> None:
        dated = "Stichtag,Wert\n2018-01-05,1\n,2\n2018-02-01,3\n"

        assert prepare(DAILY, keep(cond("Liter", "ge", 10), cond("Kanal", "eq", "Ost"))).changes == [
            "kept 3 of 24 rows where Liter ≥ 10 and Kanal = 'Ost', 21 dropped"
        ]
        assert prepare(dated, keep(cond("Stichtag", "not_missing"))).changes == [
            "kept 2 of 3 rows where Stichtag is not missing, 1 dropped"
        ]

    def test_a_column_whose_values_do_not_fit_is_left_out_whole_and_the_counts_stay(self) -> None:
        """Three long date columns: the conditions give way first, then a column's two values are left out whole,
        never cut into half a date."""
        names = [letter * MAX_COLUMN_NAME_CHARS for letter in "ABC"]
        header = ",".join(names)
        text = f"{header}\n2017-01-01,2017-02-01,2017-03-01\n2017-01-02,2017-02-02,2017-03-02\n2018-01-01,2018-01-01,2018-01-01\n"
        where = [cond(name, "le", "2017-12-31") for name in names]

        (line,) = prepare(text, keep(*where)).changes

        assert len(line) <= MAX_NOTE_CHARS
        assert line.startswith("kept 2 of 3 rows where ")
        assert line.endswith(
            f", 1 dropped; in the rows kept, {names[0]} is at least 2017-01-01 and at most 2017-01-02 and {names[1]} "
            "is at least 2017-02-01 and at most 2017-02-02"
        )
        assert f"{names[2]} is" not in line
