"""Tests for agents/anyplot/data/prepare.py: every operation, the error codes, the change lines, the round trip.

The parser types a column whose every cell carries the same unit at the paste (`12,5 %`, `7 %` becomes
`Anteil (%)`, numbers), so the unit columns here keep one bare cell (`7`): they stay text, and
`set_type number` has cells to read.
"""

import csv
import io
import random
from dataclasses import replace
from decimal import Decimal
from typing import Any, Literal

import pandas as pd
import pytest
from pydantic import TypeAdapter, ValidationError

from agents.anyplot.data import months as months_module
from agents.anyplot.data import prepare as prepare_module
from agents.anyplot.data.parse import AMBIGUOUS_DATE_ORDER, MAX_COMPUTED_BYTES, RESPELLED, ParsedDataset, parse_dataset
from agents.anyplot.data.prepare import (
    AMBIGUOUS_MONTH_FIRST,
    MAX_CONDITIONS,
    MAX_DROP_COLUMNS,
    MAX_LONGER_COLUMNS,
    MAX_OPERATIONS,
    MAX_RULES,
    MAX_VALIDATION_LINES,
    MAX_VALUE_CHARS,
    MAX_WIDER_COLUMNS,
    Aggregate,
    Condition,
    DropRows,
    Operation,
    Prepared,
    PrepareError,
    Rename,
    apply_operations,
    month_number,
    validation_lines,
    with_date_notes,
)
from agents.anyplot.schemas import MAX_CELL_CHARS, MAX_COLUMN_NAME_CHARS, MAX_COLUMNS, MAX_NOTE_CHARS, MAX_ROWS


OPERATIONS = TypeAdapter(list[Operation])

# A semicolon file with decimal commas, DD.MM.YYYY dates, a total row and a unit column that stays text: one
# bare cell (`7`) next to `12,5 %` cells. With `7 %` the parser would type it as `Anteil (%)` at the paste.
SALES = (
    "Datum;Tier;Anteil;Umsatz\n"
    "05.01.2024;Hund;12,5 %;1.200,50\n"
    "20.01.2024;Katze;7;800,00\n"
    "14.02.2024;Hund;30 %;300,25\n"
    "28.02.2024;Katze;;150,00\n"
    "15.03.2024;Hund;50,5 %;999,75\n"
    "31.03.2024;Gesamt;100 %;3.450,50\n"
)
SALES_CSV = (
    "Datum,Tier,Anteil,Umsatz\n"
    '2024-01-05,Hund,"12,5 %",1200.5\n'
    "2024-01-20,Katze,7,800\n"
    "2024-02-14,Hund,30 %,300.25\n"
    "2024-02-28,Katze,,150\n"
    '2024-03-15,Hund,"50,5 %",999.75\n'
    "2024-03-31,Gesamt,100 %,3450.5\n"
)
# Two series with a missing cell each, for pivot_longer; its long form for pivot_wider.
WIDE = "Monat,Hüte,Schuhe\n2024-01,10,20\n2024-02,15,\n2024-03,,30\n"
LONG = "Monat,series,value\n2024-01,Hüte,10\n2024-02,Hüte,15\n2024-01,Schuhe,20\n2024-03,Schuhe,30\n"


def prepare(text: str, *operations: dict[str, Any]) -> Prepared:
    return apply_operations(parse_dataset(text), OPERATIONS.validate_python(list(operations)))


def failure(text: str, *operations: dict[str, Any]) -> tuple[str, str]:
    with pytest.raises(PrepareError) as caught:
        prepare(text, *operations)
    return caught.value.code, caught.value.message


def rows(prepared: Prepared) -> list[str]:
    return prepared.csv.splitlines()


def cells(prepared: Prepared, index: int) -> list[str]:
    """One column's cells below the header, read with the csv module (a cell may hold a comma)."""
    return [row[index] for row in list(csv.reader(io.StringIO(prepared.csv)))[1:]]


def reparse(prepared: Prepared) -> ParsedDataset:
    """The result as `prepare_data` re-parses it: the columns kept text stay text, the CSV is canonical."""
    return parse_dataset(
        prepared.csv, text_columns=prepared.text_columns, find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True
    )


def dtypes(prepared: Prepared) -> dict[str, str]:
    return dict(reparse(prepared).column_dtypes)


def drop(column: str, test: str, value: object = None) -> dict[str, Any]:
    condition: dict[str, Any] = {"column": column, "test": test}
    if value is not None:
        condition["value"] = value
    return {"op": "drop_rows", "where": [condition]}


class TestModels:
    def test_the_discriminator_picks_the_operation(self) -> None:
        parsed = OPERATIONS.validate_python(
            [
                {"op": "rename", "column": "a", "name": "b"},
                {"op": "drop_rows", "where": [{"column": "a", "test": "eq"}]},
            ]
        )

        assert isinstance(parsed[0], Rename)
        assert isinstance(parsed[1], DropRows)

    def test_defaults(self) -> None:
        sort, longer, aggregate = OPERATIONS.validate_python(
            [
                {"op": "sort", "column": "a"},
                {"op": "pivot_longer", "columns": ["a", "b"]},
                {"op": "aggregate", "by": ["a"], "column": "b", "how": "sum"},
            ]
        )

        assert sort.descending is False
        assert (longer.names_to, longer.values_to) == ("series", "value")
        assert isinstance(aggregate, Aggregate) and aggregate.period is None

    @pytest.mark.parametrize(
        "operation",
        [
            {"op": "melt", "columns": ["a", "b"]},
            {"op": "rename", "column": "a", "name": "b", "extra": 1},
            {"op": "rename", "column": "a", "name": ""},
            {"op": "rename", "column": "a", "name": "x" * (MAX_COLUMN_NAME_CHARS + 1)},
            {"op": "rename", "column": "a", "name": " b"},
            {"op": "rename", "column": "a", "name": "b\tc"},
            {"op": "rename", "column": "a", "name": "b\N{ZERO WIDTH SPACE}"},
            {"op": "drop_columns", "columns": []},
            {"op": "drop_columns", "columns": [f"c{i}" for i in range(MAX_DROP_COLUMNS + 1)]},
            {"op": "drop_rows", "where": [{"column": "a", "test": "eq", "value": "x"}] * (MAX_CONDITIONS + 1)},
            {"op": "drop_rows", "where": [{"column": "a", "test": "eq", "value": "x" * (MAX_VALUE_CHARS + 1)}]},
            {"op": "drop_rows", "where": [{"column": "a", "test": "between", "value": "x"}]},
            {"op": "set_type", "column": "a", "type": "integer"},
            {"op": "set_type", "column": "a", "type": "datetime", "date_format": "%d.%m.%Y"},
            {"op": "set_type", "column": "a", "type": "number", "decimal": ";"},
            {"op": "aggregate", "by": ["a", "b", "c"], "column": "d", "how": "sum"},
            {"op": "aggregate", "by": [], "column": "d", "how": "sum"},
            {"op": "aggregate", "by": ["a"], "column": "d", "how": "median"},
            {"op": "aggregate", "by": ["a"], "column": "d", "how": "sum", "period": "decade"},
            {"op": "aggregate", "by": ["a"], "column": "d", "how": "sum", "period": "minute"},
            {"op": "pivot_longer", "columns": ["a"]},
            {"op": "pivot_longer", "columns": [f"c{i}" for i in range(MAX_LONGER_COLUMNS + 1)]},
            {"op": "pivot_longer", "columns": ["a", "b"], "names_to": "x "},
            {"op": "pivot_wider", "names_from": "a", "values_from": "b", "index": []},
            {"op": "pivot_wider", "names_from": "a", "values_from": "b", "index": ["c", "d", "e"]},
        ],
    )
    def test_malformed_operations_fail_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])

    @pytest.mark.parametrize(("value", "text"), [(100, "100"), (100.0, "100.0"), (-3, "-3"), (1e20, "1e+20")])
    def test_a_number_value_is_read_as_its_text(self, value: object, text: str) -> None:
        """The model writes `"value": 100` for a numeric comparison; a JSON number needs no quoting."""
        condition = Condition.model_validate({"column": "score", "test": "gt", "value": value})

        assert condition.value == text
        # `gt`, so that a row stays for every value (1e20 drops none; `lt` would drop them all).
        prepared = prepare("name,score\nA,10\nB,140\nC,-7\n", drop("score", "gt", value))
        assert cells(prepared, 1) == [cell for cell in ("10", "140", "-7") if float(cell) <= float(text)]

    def test_a_boolean_value_is_not_a_text(self) -> None:
        with pytest.raises(ValidationError):
            Condition.model_validate({"column": "flag", "test": "eq", "value": True})

    def test_validation_lines_name_the_location_and_never_echo_the_input(self) -> None:
        operations = [{"op": "explode"}, {"op": "rename", "column": "Study Hours"}]
        with pytest.raises(ValidationError) as caught:
            OPERATIONS.validate_python(operations)
        lines = validation_lines(caught.value, prefix="operations")

        assert lines[0].startswith("operations[0]: ")
        assert lines[1].startswith("operations[1].rename.name: Field required")
        assert all("Study Hours" not in line for line in lines)

    def test_validation_lines_are_capped(self) -> None:
        with pytest.raises(ValidationError) as caught:
            OPERATIONS.validate_python([{"op": "sort"}] * (MAX_VALIDATION_LINES + 5))

        assert len(validation_lines(caught.value)) == MAX_VALIDATION_LINES


class TestFixture:
    def test_the_sales_fixture_parses_as_designed(self) -> None:
        parsed = parse_dataset(SALES)

        assert parsed.csv == SALES_CSV
        assert parsed.column_dtypes == {"Datum": "datetime", "Tier": "text", "Anteil": "text", "Umsatz": "number"}
        assert parsed.profile.decimal == ","
        # No unit moved into a name (the bare `7` keeps `Anteil` text); only the spelling line for `1.234,50` and the like.
        assert [warning for warning in parsed.warnings if RESPELLED not in warning] == []
        # `1.200,50` and `3.450,50` drop a written zero; `800,00` as `800` is the same whole number, no note.
        assert parsed.warnings[0].startswith(f"2 numbers {RESPELLED}")


class TestRename:
    def test_renames_and_reports(self) -> None:
        prepared = prepare(SALES, {"op": "rename", "column": "Tier", "name": "Segment"})

        assert rows(prepared)[0] == "Datum,Segment,Anteil,Umsatz"
        assert rows(prepared)[1:] == SALES_CSV.splitlines()[1:]
        assert prepared.changes == ["renamed 'Tier' to 'Segment'"]

    def test_unknown_column(self) -> None:
        assert failure(SALES, {"op": "rename", "column": "Art", "name": "Segment"}) == (
            "unknown_column",
            "there is no column 'Art'",
        )

    @pytest.mark.parametrize("name", ["Umsatz", "Tier"])
    def test_an_existing_name_is_refused(self, name: str) -> None:
        code, message = failure(SALES, {"op": "rename", "column": "Tier", "name": name})

        assert code == "invalid_operation"
        assert f"'{name}'" in message


class TestDropColumns:
    def test_one_column(self) -> None:
        prepared = prepare(SALES, {"op": "drop_columns", "columns": ["Anteil"]})

        assert rows(prepared)[:2] == ["Datum,Tier,Umsatz", "2024-01-05,Hund,1200.5"]
        assert prepared.changes == ["dropped column Anteil"]

    def test_several_columns_once_each(self) -> None:
        prepared = prepare(SALES, {"op": "drop_columns", "columns": ["Anteil", "Datum", "Anteil"]})

        assert rows(prepared)[0] == "Tier,Umsatz"
        assert prepared.changes == ["dropped 2 columns: Anteil, Datum"]

    def test_unknown_column(self) -> None:
        assert failure(SALES, {"op": "drop_columns", "columns": ["Anteil", "Art"]})[0] == "unknown_column"

    def test_dropping_every_column_is_empty(self) -> None:
        columns = ["Datum", "Tier", "Anteil", "Umsatz"]

        assert failure(SALES, {"op": "drop_columns", "columns": columns})[0] == "empty_result"


class TestDropRows:
    def test_eq_on_text(self) -> None:
        prepared = prepare(SALES, drop("Tier", "eq", "Gesamt"))

        assert rows(prepared) == SALES_CSV.splitlines()[:-1]
        assert prepared.changes == ["dropped 1 row where Tier = 'Gesamt'"]

    def test_all_conditions_must_hold(self) -> None:
        where = [{"column": "Umsatz", "test": "gt", "value": "500"}, {"column": "Tier", "test": "ne", "value": "Katze"}]
        prepared = prepare(SALES, {"op": "drop_rows", "where": where})

        assert cells(prepared, 1) == ["Katze", "Hund", "Katze"]
        assert prepared.changes == ["dropped 3 rows where Umsatz > 500 and Tier ≠ 'Katze'"]

    def test_numbers_compare_as_numbers(self) -> None:
        prepared = prepare(SALES, drop("Umsatz", "lt", "1e3"))

        assert cells(prepared, 3) == ["1200.5", "3450.5"]

    def test_dates_compare_as_moments(self) -> None:
        prepared = prepare(SALES, drop("Datum", "lt", "2024-02-01"))

        assert len(rows(prepared)) == 5
        assert prepared.changes == ["dropped 2 rows where Datum < 2024-02-01"]

    def test_contains_searches_the_text(self) -> None:
        prepared = prepare(SALES, drop("Anteil", "contains", ",5"))

        assert len(rows(prepared)) == 5
        assert prepared.changes == ["dropped 2 rows where Anteil contains ',5'"]

    def test_contains_on_a_number_uses_its_canonical_text(self) -> None:
        prepared = prepare(SALES, drop("Umsatz", "contains", ".25"))

        assert prepared.changes == ["dropped 1 row where Umsatz contains '.25'"]

    def test_is_missing(self) -> None:
        prepared = prepare(SALES, drop("Anteil", "is_missing"))

        assert len(rows(prepared)) == 6
        assert prepared.changes == ["dropped 1 row where Anteil is missing"]

    def test_not_missing_keeps_the_rows_where_a_cell_is_missing(self) -> None:
        """A `drop_rows` reaches "the rows where Anteil is missing" by dropping the ones where it is not."""
        prepared = prepare(SALES, drop("Anteil", "not_missing"))

        assert cells(prepared, 1) == ["Katze"] and cells(prepared, 2) == [""]
        assert prepared.changes == ["dropped 5 rows where Anteil is not missing"]
        assert "takes no value" in failure(SALES, drop("Anteil", "not_missing", "x"))[1]

    def test_a_drop_of_the_only_rows_below_zero_says_that_the_total_went_up(self) -> None:
        """Persona round of 2026-11-11: the cancelled invoices held negative quantities, so taking them off raised
        the total from the net to the gross figure, and nothing said so."""
        invoices = "Beleg,Art,Menge,Preis\nR1,A,10,4.5\nR2,A,6,4.5\nR3,C,-6,4.5\nR4,A,3,2\nR5,C,-1,2\n"

        prepared = prepare(invoices, drop("Art", "eq", "C"))

        assert prepared.changes == [
            "dropped 2 rows where Art = 'C'; Menge is below 0 only in rows that were dropped, so its total over the "
            "rows kept is higher than before"
        ]

    @pytest.mark.parametrize(
        ("table", "condition"),
        [
            # A row below 0 stays as well: the sign does not tell the dropped rows from the kept ones.
            ("Art,Menge\nA,10\nA,-2\nC,-6\n", drop("Art", "eq", "C")),
            # Nothing below 0 was dropped.
            ("Art,Menge\nA,10\nA,-2\nC,6\n", drop("Art", "eq", "C")),
            # No row that stays is above 0: a column of losses, not of amounts that were taken off.
            ("Art,Menge\nA,0\nA,0\nC,-6\n", drop("Art", "eq", "C")),
            # The dropped rows hold no value there.
            ("Art,Menge\nA,10\nA,4\nC,\n", drop("Art", "eq", "C")),
        ],
    )
    def test_any_other_drop_says_only_what_it_dropped(self, table: str, condition: dict[str, Any]) -> None:
        assert prepare(table, condition).changes == ["dropped 1 row where Art = 'C'"]

    def test_whole_numbers_past_the_int64_range_keep_their_sign(self) -> None:
        """pandas' Int64 sum of these two wraps around to a positive number; the dropped rows are far below 0."""
        table = f"Art,Menge\nA,10\nA,4\nC,{-(2**63)}\nC,-1\n"

        (line,) = prepare(table, drop("Art", "eq", "C")).changes

        assert line.endswith("so its total over the rows kept is higher than before")

    def test_dropped_rows_that_add_up_to_more_than_zero_took_nothing_off(self) -> None:
        """One dropped row is below 0, but the dropped rows together are above it: the total over the rows kept is
        lower than before, so a note that it is higher would be false."""
        table = "Art,Menge\nA,10\nA,4\nC,-5\nC,50\n"

        assert prepare(table, drop("Art", "eq", "C")).changes == ["dropped 2 rows where Art = 'C'"]

    def test_the_note_names_two_columns_at_most(self) -> None:
        table = "Art,Menge,Betrag,Rabatt\nA,10,45,1\nA,6,27,2\nC,-6,-27,-1\n"

        (line,) = prepare(table, drop("Art", "eq", "C")).changes

        assert line.endswith(
            "; Menge and Betrag are below 0 only in rows that were dropped, so their totals over the rows kept are "
            "higher than before"
        )

    def test_a_missing_cell_matches_no_comparison(self) -> None:
        kept_by_ne = prepare(SALES, drop("Anteil", "ne", "7"))
        kept_by_contains = prepare(SALES, drop("Anteil", "contains", "%"))

        assert rows(kept_by_ne)[1:] == ["2024-01-20,Katze,7,800", "2024-02-28,Katze,,150"]
        assert rows(kept_by_contains)[1:] == ["2024-01-20,Katze,7,800", "2024-02-28,Katze,,150"]

    def test_boolean_columns(self) -> None:
        text = "flag,v\ntrue,1\nfalse,2\n,3\n"

        assert rows(prepare(text, drop("flag", "eq", "TRUE")))[1:] == ["False,2", ",3"]
        assert failure(text, drop("flag", "gt", "true"))[0] == "invalid_operation"
        assert failure(text, drop("flag", "ge", "true"))[0] == "invalid_operation"
        assert failure(text, drop("flag", "le", "false"))[0] == "invalid_operation"
        assert failure(text, drop("flag", "eq", "yes"))[0] == "invalid_operation"

    def test_text_orders_as_text(self) -> None:
        prepared = prepare(SALES, drop("Tier", "gt", "Hund"))

        assert cells(prepared, 1) == ["Hund", "Hund", "Hund", "Gesamt"]
        assert cells(prepare(SALES, drop("Tier", "ge", "Hund")), 1) == ["Gesamt"]

    def test_at_least_and_at_most_take_the_value_itself_in(self) -> None:
        """`gt` and `lt` leave the value itself out, so "800 or more" had no form of its own."""
        at_least = prepare(SALES, drop("Umsatz", "ge", 800))
        at_most = prepare(SALES, drop("Umsatz", "le", "800"))

        assert cells(at_least, 3) == ["300.25", "150"]
        assert at_least.changes == ["dropped 4 rows where Umsatz ≥ 800"]
        assert cells(at_most, 3) == ["1200.5", "999.75", "3450.5"]
        assert at_most.changes == ["dropped 3 rows where Umsatz ≤ 800"]

    def test_a_missing_cell_is_neither_at_least_nor_at_most(self) -> None:
        text = "k,v\na,1\nb,\nc,3\n"

        assert rows(prepare(text, drop("v", "ge", 0)))[1:] == ["b,"]
        assert rows(prepare(text, drop("v", "le", 5)))[1:] == ["b,"]

    def test_a_date_without_a_time_is_the_whole_day(self) -> None:
        """ "Until the 31st" takes in that day's rows whatever their time, and "after the 31st" none of them: midnight
        alone would cut the day's rows in two, and `le` and `gt` would both hold for the rows after it."""
        text = "t,v\n2024-01-30T08:00:00,1\n2024-01-31T00:00:00,2\n2024-01-31T10:00:00,3\n2024-02-01T00:00:00,4\n"

        assert cells(prepare(text, drop("t", "le", "2024-01-31")), 1) == ["4"]
        assert cells(prepare(text, drop("t", "gt", "2024-01-31")), 1) == ["1", "2", "3"]
        # The start of a range is the day's first moment either way, and so is the end `lt` names.
        assert cells(prepare(text, drop("t", "ge", "2024-01-31")), 1) == ["1"]
        assert cells(prepare(text, drop("t", "lt", "2024-01-31")), 1) == ["2", "3", "4"]
        # A value with a time is that moment.
        assert cells(prepare(text, drop("t", "le", "2024-01-31T00:00:00")), 1) == ["3", "4"]
        assert cells(prepare(text, drop("t", "gt", "2024-01-31T00:00:00")), 1) == ["1", "2"]

    def test_the_last_day_of_the_calendar_is_a_whole_day_too(self) -> None:
        """The day after it is past what `datetime` holds; the comparison still answers, and never crashes."""
        text = "t,v\n2024-01-30,1\n2024-01-31,2\n"

        assert failure(text, drop("t", "le", "9999-12-31"))[0] == "empty_result"
        assert len(rows(prepare(text, drop("t", "gt", "9999-12-31")))) == 3

    def test_a_day_is_never_guessed_into_a_column_with_utc_offsets(self) -> None:
        """Which zone's day a date alone means there would be a guess, and a day is not 24 hours where the clocks
        change: the value is refused before the whole-day reading, as for every other test."""
        text = "t,v\n2024-03-30T10:00:00+01:00,1\n2024-03-31T10:00:00+02:00,2\n"

        for test in ("le", "gt", "ge", "lt"):
            code, message = failure(text, drop("t", test, "2024-03-31"))
            assert code == "invalid_operation" and "give the value with one" in message

    def test_nothing_matching_is_a_change_line_too(self) -> None:
        prepared = prepare(SALES, drop("Tier", "eq", "Pferd"))

        assert prepared.csv == SALES_CSV
        assert prepared.changes == ["dropped 0 rows where Tier = 'Pferd'"]

    def test_dropping_every_row_is_empty(self) -> None:
        assert failure(SALES, drop("Umsatz", "gt", "0"))[0] == "empty_result"

    @pytest.mark.parametrize(
        ("condition", "fragment"),
        [
            (drop("Tier", "eq"), "needs a value"),
            (drop("Tier", "eq", ""), "is_missing finds empty cells"),
            (drop("Tier", "is_missing", "x"), "takes no value"),
            (drop("Umsatz", "gt", "1,5"), "not a number"),
            (drop("Umsatz", "eq", "Hund"), "not a number"),
            (drop("Datum", "lt", "01.02.2024"), "not an ISO date"),
            (drop("Datum", "lt", "2024-02-01T00:00:00+02:00"), "holds times without a UTC offset"),
        ],
    )
    def test_invalid_conditions(self, condition: dict[str, Any], fragment: str) -> None:
        code, message = failure(SALES, condition)

        assert code == "invalid_operation"
        assert fragment in message
        assert "Hund" not in message and "Gesamt" not in message

    def test_unknown_column(self) -> None:
        assert failure(SALES, drop("Art", "eq", "x"))[0] == "unknown_column"

    def test_change_lines_stay_within_the_note_limit(self) -> None:
        value = "x" * MAX_VALUE_CHARS
        where = [{"column": name, "test": "ne", "value": value} for name in ("Tier", "Anteil", "Datum")]
        where[2] = {"column": "Datum", "test": "lt", "value": "2030-01-01"}
        prepared = prepare(SALES, {"op": "drop_rows", "where": where})

        assert len(prepared.changes[0]) <= MAX_NOTE_CHARS
        assert "'" + "x" * 39 + "…'" in prepared.changes[0]


class TestSetTypeNumber:
    def test_decimal_comma_with_a_trailing_unit(self) -> None:
        prepared = prepare(SALES, {"op": "set_type", "column": "Anteil", "type": "number"})

        assert cells(prepared, 2) == ["12.5", "7", "30", "", "50.5", "100"]  # whole numbers as written
        assert prepared.changes == ["Anteil: 5 cells read as numbers, unit '%' removed"]
        assert dtypes(prepared)["Anteil"] == "number"

    def test_dot_decimal_with_thousands_commas_and_whole_values_become_integers(self) -> None:
        text = 'p,v\n"1,200 USD",1\n"3,000 USD",2\n5,3\n'
        assert parse_dataset(text).column_dtypes["p"] == "text"
        prepared = prepare(text, {"op": "set_type", "column": "p", "type": "number"})

        assert rows(prepared)[1:] == ["1200,1", "3000,2", "5,3"]
        assert prepared.changes == ["p: 3 cells read as numbers, unit 'USD' removed"]
        assert dtypes(prepared)["p"] == "integer"

    def test_a_leading_unit_and_spaces_as_thousands_separators(self) -> None:
        text = 'p,v\n"€ 1 200,50",1\n€12,2\n€ -3,3\n'
        prepared = prepare(text, {"op": "set_type", "column": "p", "type": "number", "decimal": ","})

        assert rows(prepared)[1:] == ["1200.5,1", "12,2", "-3,3"]
        assert prepared.changes == ["p: 3 cells read as numbers, unit '€' removed"]

    def test_the_decimal_argument_overrides_the_dataset_decimal(self) -> None:
        text = "p,v\n1.200 kg,1\n7,2\n"
        assert parse_dataset(text).column_dtypes["p"] == "text"
        with_comma = prepare(text, {"op": "set_type", "column": "p", "type": "number", "decimal": ","})
        with_dot = prepare(text, {"op": "set_type", "column": "p", "type": "number", "decimal": "."})

        assert rows(with_comma)[1] == "1200,1"
        assert rows(with_dot)[1] == "1.2,1"

    def test_a_tenth_may_fail_and_becomes_missing(self) -> None:
        text = "p\n" + "".join(f"{n} kg\n" for n in range(9)) + "unknown\n"
        prepared = prepare(text, {"op": "set_type", "column": "p", "type": "number"})

        assert rows(prepared)[-1] == '""'
        assert prepared.changes == [
            "p: 9 cells read as numbers, unit 'kg' removed, 1 cell could not be read and is now missing"
        ]

    def test_more_than_a_tenth_failing_is_a_type_mismatch(self) -> None:
        text = "p\n" + "".join(f"{n} kg\n" for n in range(8)) + "unknown\nn.k.\n"

        assert failure(text, {"op": "set_type", "column": "p", "type": "number"}) == (
            "type_mismatch",
            "column 'p': 2 of 10 cells cannot be read as numbers",
        )

    def test_mixed_units_are_a_type_mismatch(self) -> None:
        code, message = failure("p\n12 kg\n500 g\n", {"op": "set_type", "column": "p", "type": "number"})

        assert code == "type_mismatch"
        assert "kg" not in message and "mixes 2 different units" in message

    def test_a_text_column_is_a_type_mismatch(self) -> None:
        assert failure(SALES, {"op": "set_type", "column": "Tier", "type": "number"})[0] == "type_mismatch"

    def test_booleans_become_ones_and_zeros(self) -> None:
        prepared = prepare("f,v\ntrue,1\nfalse,2\n,3\n", {"op": "set_type", "column": "f", "type": "number"})

        assert rows(prepared)[1:] == ["1,1", "0,2", ",3"]
        assert prepared.changes == ["f: 2 cells read as numbers"]

    def test_a_number_column_stays_as_it_is(self) -> None:
        prepared = prepare(SALES, {"op": "set_type", "column": "Umsatz", "type": "number"})

        assert prepared.csv == SALES_CSV
        assert prepared.changes == ["Umsatz: already numbers, nothing changed"]

    AMBIGUOUS_DOTS = "Stadt;Einwohner\nBern;1.234\nBasel;7.000\nChur;12\n"

    def test_a_decimal_comma_reads_ambiguous_dots_again_from_the_cells_as_pasted(self) -> None:
        """The canonical text says `7`, the paste said `7.000`: read again with a decimal comma, it is 7000."""
        operation = {"op": "set_type", "column": "Einwohner", "type": "number", "decimal": ","}
        prepared = prepare(self.AMBIGUOUS_DOTS, operation)

        assert cells(prepared, 1) == ["1234", "7000", "12"]
        assert prepared.changes == ["Einwohner: 3 cells read as numbers"]

    def test_the_reading_follows_a_rename_and_waits_for_rows_as_pasted(self) -> None:
        renamed = prepare(
            self.AMBIGUOUS_DOTS,
            {"op": "rename", "column": "Einwohner", "name": "Population"},
            {"op": "set_type", "column": "Population", "type": "number", "decimal": ","},
        )
        assert cells(renamed, 1) == ["1234", "7000", "12"]

        # After a sort a row of the frame is no pasted row: the pasted cells cannot be laid over it.
        with pytest.raises(PrepareError) as raised:
            prepare(
                self.AMBIGUOUS_DOTS,
                {"op": "sort", "column": "Stadt"},
                {"op": "set_type", "column": "Einwohner", "type": "number", "decimal": ","},
            )
        assert raised.value.code == "type_mismatch"
        assert "undo to the pasted data first" in str(raised.value)

    def test_the_cells_as_pasted_go_with_their_column_never_to_a_later_one_of_its_name(self) -> None:
        """Dropped, the column takes its pasted cells along: `Alt` renamed to `Einwohner`, or a column derived under
        that name, has none to read again, so the decimal comma is refused and 1.234 never lands on it."""
        text = "Stadt;Einwohner;Alt;Neu\nBern;1.234;5;1\nBasel;7.000;6;1\nChur;12;7;1\n"
        reading = {"op": "set_type", "column": "Einwohner", "type": "number", "decimal": ","}
        dropped = {"op": "drop_columns", "columns": ["Einwohner"]}

        for later in ({"op": "rename", "column": "Alt", "name": "Einwohner"}, derive("Einwohner", "sum", "Alt", "Neu")):
            code, message = failure(text, dropped, later, reading)
            assert code == "type_mismatch" and "only from the pasted data" in message

        renamed = prepare(text, dropped, {"op": "rename", "column": "Alt", "name": "Einwohner"})
        assert cells(renamed, 1) == ["5", "6", "7"]

    def test_a_pasted_number_column_made_text_is_its_cells_as_pasted(self) -> None:
        """`7.000` is stored as the number 7: as text it is `7.000` again, and back to numbers with a decimal comma
        in the same call it is 7000, where the stored text gave 7."""
        as_text = prepare(self.AMBIGUOUS_DOTS, {"op": "set_type", "column": "Einwohner", "type": "text"})
        assert cells(as_text, 1) == ["1.234", "7.000", "12"]

        back = prepare(
            self.AMBIGUOUS_DOTS,
            {"op": "set_type", "column": "Einwohner", "type": "text"},
            {"op": "set_type", "column": "Einwohner", "type": "number", "decimal": ","},
        )
        assert cells(back, 1) == ["1234", "7000", "12"]

    def test_a_declared_missing_mark_stays_missing_when_the_dots_are_read_again(self) -> None:
        prepared = prepare(
            "Fehlwerte: -999\nStadt;Einwohner\nBern;1.234\nBasel;7.000\nChur;-999\nThun;980\n",
            {"op": "set_type", "column": "Einwohner", "type": "number", "decimal": ","},
        )

        assert cells(prepared, 1) == ["1234", "7000", "", "980"]

    def test_a_number_column_without_cells_as_pasted_stays_or_is_refused(self) -> None:
        """A column read the way the request names stays as it is. A later version's column, whose dots the request
        wants read as thousands, has no cells to read again: refused, never a line of a call that goes on to compute
        with the decimal reading and store it."""
        plain = prepare(SALES, {"op": "set_type", "column": "Umsatz", "type": "number", "decimal": "."})
        assert plain.changes == ["Umsatz: already numbers, nothing changed"]
        comma = prepare(SALES, {"op": "set_type", "column": "Umsatz", "type": "number", "decimal": ","})
        assert comma.changes == ["Umsatz: already numbers, nothing changed"]  # a file of decimal commas, read so

        later = replace(parse_dataset(self.AMBIGUOUS_DOTS), pasted_cells={})
        operations = OPERATIONS.validate_python(
            [
                {"op": "set_type", "column": "Einwohner", "type": "number", "decimal": ","},
                {"op": "compute", "name": "Doppelt", "expression": "e * 2", "inputs": {"e": "Einwohner"}},
            ]
        )
        with pytest.raises(PrepareError) as raised:
            apply_operations(later, operations)
        assert raised.value.code == "type_mismatch"
        assert "already holds numbers read with a decimal point" in raised.value.message
        assert "undo to the pasted data first" in raised.value.message

    def test_a_uniform_unit_column_is_typed_at_parse_and_a_mixed_one_by_set_type(self) -> None:
        """The division of labour: when every cell carries the same unit, the parser reads numbers at the paste and
        moves the unit into the name, so `set_type number` has nothing to do; one bare cell keeps the column text."""
        uniform = parse_dataset(SALES.replace("Katze;7;", "Katze;7 %;"))
        assert uniform.column_dtypes["Anteil (%)"] == "number"
        assert uniform.warnings[0] == "column 'Anteil': unit '%' moved from the values into the name 'Anteil (%)'"
        assert len(uniform.warnings) == 2 and RESPELLED in uniform.warnings[1]  # `Umsatz` writes `1.234,50`
        operation = {"op": "set_type", "column": "Anteil (%)", "type": "number"}
        typed = apply_operations(uniform, OPERATIONS.validate_python([operation]))

        assert typed.csv == uniform.csv
        assert cells(typed, 2) == ["12.5", "7", "30", "", "50.5", "100"]
        assert typed.changes == ["Anteil (%): already numbers, nothing changed"]

        assert parse_dataset(SALES).column_dtypes["Anteil"] == "text"
        read = prepare(SALES, {"op": "set_type", "column": "Anteil", "type": "number"})

        assert cells(read, 2) == cells(typed, 2)
        assert read.changes == ["Anteil: 5 cells read as numbers, unit '%' removed"]

    def test_a_mark_outside_three_digit_groups_is_a_decimal_never_a_thousands_separator(self) -> None:
        """`12,5 %` in a dot-decimal file is 12.5, as the parser reads it, never 125 (the verifiers' finding).

        The bare `7` and `14` keep the columns text at parse; with a unit on every cell the parser would read them.
        """
        dot_file = 'name,share,score\nAlpha,"12,5 %",1.5\nBeta,7,2.25\nGamma,30 %,0.75\nDelta,"50,5 %",3.0\n'
        parsed = parse_dataset(dot_file)
        assert parsed.profile.decimal == "." and parsed.column_dtypes["share"] == "text"
        prepared = prepare(dot_file, {"op": "set_type", "column": "share", "type": "number"})

        assert cells(prepared, 1) == ["12.5", "7", "30", "50.5"]
        assert prepared.changes == ["share: 4 cells read as numbers (decimal comma), unit '%' removed"]

        comma_file = "a;p\n1,5;12.5 %\n2,5;13.5 %\n3,5;14\n"
        parsed = parse_dataset(comma_file)
        assert parsed.profile.decimal == "," and parsed.column_dtypes["p"] == "text"
        prepared = prepare(comma_file, {"op": "set_type", "column": "p", "type": "number"})

        assert cells(prepared, 1) == ["12.5", "13.5", "14"]
        assert prepared.changes == ["p: 3 cells read as numbers (decimal point), unit '%' removed"]

    def test_the_other_decimal_is_used_for_the_whole_column_when_fewer_cells_fail(self) -> None:
        """One decimal per column: `1,200` next to `2,5` reads as 1.2 and 2.5 (decimal commas), never 1200 and 2.5."""
        text = "p,v\n1 kg,1\n2,2\n"  # nothing to fall back
        assert parse_dataset(text).column_dtypes["p"] == "text"
        prepared = prepare(text, {"op": "set_type", "column": "p", "type": "number"})
        assert prepared.changes == ["p: 2 cells read as numbers, unit 'kg' removed"]

        text = 'p,v\n"1,200 kg",1\n"2,5 kg",2\n3,3\n'
        assert parse_dataset(text).column_dtypes["p"] == "text"
        prepared = prepare(text, {"op": "set_type", "column": "p", "type": "number"})

        assert cells(prepared, 0) == ["1.2", "2.5", "3"]
        assert prepared.changes == ["p: 3 cells read as numbers (decimal comma), unit 'kg' removed"]

    def test_a_cell_unreadable_with_either_decimal_fails(self) -> None:
        """`1,200,5` and `1.2.3` read with neither mark; `2,5` reads with the comma, so the column falls back to it."""
        text = 'p\n"1,200,5"\n"1.2.3"\n"2,5"\n' + "".join(f"{n}\n" for n in range(7))

        assert failure(text, {"op": "set_type", "column": "p", "type": "number"}) == (
            "type_mismatch",
            "column 'p': 2 of 10 cells cannot be read as numbers",
        )


class TestSetTypeDatetime:
    def test_a_fixed_format_with_optional_times(self) -> None:
        # The junk cell keeps the column text at parse time; it is within the tenth that may fail.
        dates = [f"{day:02d}.02.2024" for day in range(1, 10)] + ["15.03.2024 10:30", "20.03.2024 08:05:09", "", "n.a."]
        text = "t,v\n" + "".join(f"{cell},{n}\n" for n, cell in enumerate(dates))
        operation = {"op": "set_type", "column": "t", "type": "datetime", "date_format": "DD.MM.YYYY"}
        prepared = prepare(text, operation)

        assert cells(prepared, 0)[:1] == ["2024-02-01T00:00:00"]
        assert cells(prepared, 0)[9:] == ["2024-03-15T10:30:00", "2024-03-20T08:05:09", "", ""]
        assert prepared.changes == [
            "t: 11 cells read as dates (DD.MM.YYYY), 1 cell could not be read and is now missing"
        ]
        assert dtypes(prepared)["t"] == "datetime"

    def test_month_first(self) -> None:
        text = "t,v\n" + "".join(f"{m:02d}/{m + 1:02d}/2024,{m}\n" for m in range(1, 10)) + "n.a.,0\n"
        operation = {"op": "set_type", "column": "t", "type": "datetime", "date_format": "MM/DD/YYYY"}
        prepared = prepare(text, operation)

        assert cells(prepared, 0)[:2] == ["2024-01-02", "2024-02-03"]
        assert cells(prepared, 0)[-1] == ""
        assert dtypes(prepared)["t"] == "datetime"

    def test_month_first_on_an_ambiguous_slash_column_swaps_day_and_month(self) -> None:
        text = "t,v\n01/02/2024,1\n03/04/2024 10:30,2\n,3\n"
        parsed = parse_dataset(text)
        operation = {"op": "set_type", "column": "t", "type": "datetime", "date_format": "MM/DD/YYYY"}
        prepared = apply_operations(parsed, OPERATIONS.validate_python([operation]))

        assert parsed.column_dtypes["t"] == "datetime"  # the parser read it day first, with its own warning
        assert cells(prepared, 0) == ["2024-01-02T00:00:00", "2024-03-04T10:30:00", ""]
        assert prepared.changes == ["t: 2 cells re-read as dates (MM/DD/YYYY, day and month swapped)"]

    @pytest.mark.parametrize("date_format", [None, "YYYY-MM-DD", "DD.MM.YYYY", "MM/DD/YYYY"])
    def test_a_datetime_column_is_left_as_it_is(self, date_format: str | None) -> None:
        operation: dict[str, Any] = {"op": "set_type", "column": "Datum", "type": "datetime"}
        if date_format:
            operation["date_format"] = date_format
        prepared = prepare(SALES, operation)  # the days 20, 14, 28 and 31 rule out a month-first reading

        assert prepared.csv == SALES_CSV
        assert prepared.changes == ["Datum: already dates, nothing changed"]

    @pytest.mark.parametrize(
        "text",
        [
            "date,visits\n2024-01-05,10\n2024-02-03,12\n2024-03-09,8\n",  # ISO: the order was never in doubt
            "date,visits\n05.01.2024,10\n03.02.2024,12\n09.03.2024,8\n",  # dotted: day first by definition
            "date,visits\n01/01/2024,10\n02/02/2024,12\n",  # a slash column whose parts never differ: no guess
        ],
        ids=["iso", "dotted", "slash-equal-parts"],
    )
    def test_month_first_leaves_a_column_the_parser_read_without_a_guess_alone(self, text: str) -> None:
        """Only a slash column the parser flagged as ambiguous was guessed; every other order is settled (verifiers)."""
        parsed = parse_dataset(text)
        assert parsed.column_dtypes["date"] == "datetime" and not parsed.warnings
        operation = {"op": "set_type", "column": "date", "type": "datetime", "date_format": "MM/DD/YYYY"}

        prepared = apply_operations(parsed, OPERATIONS.validate_python([operation]))

        assert prepared.csv == parsed.csv
        assert prepared.changes == ["date: already dates, nothing changed"]

    def test_the_swap_follows_a_rename_and_happens_once(self) -> None:
        text = "t,v\n01/02/2024,1\n03/04/2024,2\n"
        swap = {"op": "set_type", "column": "when", "type": "datetime", "date_format": "MM/DD/YYYY"}
        prepared = prepare(text, {"op": "rename", "column": "t", "name": "when"}, swap, swap)

        assert cells(prepared, 0) == ["2024-01-02", "2024-03-04"]
        assert prepared.changes[1:] == [
            "when: 2 cells re-read as dates (MM/DD/YYYY, day and month swapped)",
            "when: already dates, nothing changed",
        ]

    def test_failures_become_missing_within_the_tenth(self) -> None:
        text = "t\n" + "".join(f"{day:02d}.01.2024\n" for day in range(1, 10)) + "n.a.\n"
        operation = {"op": "set_type", "column": "t", "type": "datetime", "date_format": "DD.MM.YYYY"}
        prepared = prepare(text, operation)

        assert rows(prepared)[-1] == '""'
        assert prepared.changes == [
            "t: 9 cells read as dates (DD.MM.YYYY), 1 cell could not be read and is now missing"
        ]

    def test_too_many_failures(self) -> None:
        text = "t,v\n01.02.2024,1\n15.03.2024,2\nn.a.,3\n"
        operation = {"op": "set_type", "column": "t", "type": "datetime", "date_format": "DD.MM.YYYY"}

        assert failure(text, operation) == ("type_mismatch", "column 't': 1 of 3 cells cannot be read as dates")

    def test_without_a_format_the_format_is_inferred_day_first(self) -> None:
        text = "t,v\nJan 2024,1\n2024-02,2\n03/04/2024,3\n15 March 2024,4\n"
        prepared = prepare(text, {"op": "set_type", "column": "t", "type": "datetime"})

        assert cells(prepared, 0) == ["2024-01-01", "2024-02-01", "2024-04-03", "2024-03-15"]
        assert prepared.changes == [
            "t: 4 cells read as dates (format inferred, year first where a cell starts with one, else day before month; "
            "1 cell with a month name and a year as the first day of the month)"
        ]

    def test_a_number_column_is_a_type_mismatch(self) -> None:
        assert failure(SALES, {"op": "set_type", "column": "Umsatz", "type": "datetime"})[0] == "type_mismatch"

    @pytest.mark.parametrize(
        ("months", "dates"),
        [
            (["Okt. 2026", "Nov. 2026", "Dez. 2026"], ["2026-10-01", "2026-11-01", "2026-12-01"]),
            (["2026 März", "2026 Mai"], ["2026-03-01", "2026-05-01"]),
            (["listopad 2026", "grudzień 2026"], ["2026-11-01", "2026-12-01"]),
        ],
    )
    def test_month_names_with_a_year_in_any_of_the_eleven_languages(self, months: list[str], dates: list[str]) -> None:
        """pandas reads English names only; the conversion reads what the parser reads (live test of 2026-11-01)."""
        text = "t;v\n" + "".join(f"{month};{index}\n" for index, month in enumerate(months))
        prepared = apply_operations(
            parse_dataset(text, text_columns=["t"]),
            OPERATIONS.validate_python([{"op": "set_type", "column": "t", "type": "datetime"}]),
        )

        assert cells(prepared, 0) == dates
        assert prepared.changes == [
            f"t: {len(months)} cells read as months (a month name and a year, each as the first day of the month)"
        ]

    def test_a_month_that_repeats_counts_every_cell(self) -> None:
        """Review of #12512: distinct month texts were compared with the cells, so a repeat fell to the inferred wording."""
        text = "t;v\nOkt. 2026;1\nOkt. 2026;2\nNov. 2026;3\n"
        to_dates = OPERATIONS.validate_python([{"op": "set_type", "column": "t", "type": "datetime"}])

        assert apply_operations(parse_dataset(text, text_columns=["t"]), to_dates).changes == [
            "t: 3 cells read as months (a month name and a year, each as the first day of the month)"
        ]

        mixed = "t;v\nOkt. 2026;1\nOkt. 2026;2\n15.03.2026;3\n"
        assert apply_operations(parse_dataset(mixed, text_columns=["t"]), to_dates).changes == [
            "t: 3 cells read as dates (format inferred, day before month; 2 cells with a month name and a year as the "
            "first day of the month)"
        ]

    def test_month_names_leave_no_day_and_month_order_open(self) -> None:
        """`1 Nov 2026` names its month: no `AMBIGUOUS_DATE_ORDER` note travels with it, unlike `01/11/2026`."""
        to_dates = OPERATIONS.validate_python([{"op": "set_type", "column": "t", "type": "datetime"}])
        named = apply_operations(parse_dataset("t,v\n1 Nov 2026,1\n1 Oct 2026,2\n"), to_dates)
        digits = apply_operations(parse_dataset("t,v\n01/11/2026,1\n01/10/2026,2\n", text_columns=["t"]), to_dates)

        assert cells(named, 0) == ["2026-11-01", "2026-10-01"]
        assert named.date_notes == []
        assert digits.date_notes == [f"column 't': {AMBIGUOUS_DATE_ORDER}"]

    @pytest.mark.parametrize(
        "cells",
        [
            ["May", "June", "April"],  # pandas: the year 1
            ["Nov 26", "Oct 26", "Sep 26"],  # pandas: 26 November of the year 1
            ["13:00", "14:00", "15:30"],  # pandas: today at that time
            ["now", "today", "now"],
        ],
    )
    def test_a_date_pandas_would_only_fill_in_is_refused(self, cells: list[str]) -> None:
        text = "t,v\n" + "".join(f"{cell},{index}\n" for index, cell in enumerate(cells))

        code, message = failure(text, {"op": "set_type", "column": "t", "type": "datetime"})

        assert code == "type_mismatch"
        assert message == f"column 't': {len(cells)} of {len(cells)} cells cannot be read as dates"

    def test_the_year_1_written_out_is_a_date(self) -> None:
        """Only a year 1 that pandas filled in fails: `0001-03-01` says it."""
        prepared = apply_operations(
            parse_dataset("t,v\n0001-03-01,1\n2024-03-01,2\n", text_columns=["t"]),
            OPERATIONS.validate_python([{"op": "set_type", "column": "t", "type": "datetime"}]),
        )

        assert cells(prepared, 0) == ["0001-03-01", "2024-03-01"]


class TestSetTypeIntoNewColumn:
    """`set_type` with `name`: the conversion an open role asks for, beside the column it reads (2026-11-01)."""

    TEXT = "Datum;Preis\n26 Nov 2026;$5\n25 Nov 2026;7\n24 Nov 2026;$12\n"

    def test_dates_go_into_a_new_column_and_the_source_stays(self) -> None:
        prepared = prepare(
            self.TEXT, {"op": "set_type", "column": "Datum", "type": "datetime", "name": "Datum (Datum)"}
        )

        assert rows(prepared)[0] == "Datum,Preis,Datum (Datum)"
        assert cells(prepared, 0) == ["26 Nov 2026", "25 Nov 2026", "24 Nov 2026"]
        assert cells(prepared, 2) == ["2026-11-26", "2026-11-25", "2026-11-24"]
        assert prepared.changes == [
            "new column Datum (Datum): 3 cells of Datum read as dates (format inferred, day before month); "
            "Datum stays as it is"
        ]
        assert prepared.converted == {"Datum (Datum)": "Datum"}
        assert dtypes(prepared) == {"Datum": "text", "Preis": "text", "Datum (Datum)": "datetime"}

    def test_numbers_go_into_a_new_column_with_the_unit_named(self) -> None:
        prepared = prepare(self.TEXT, {"op": "set_type", "column": "Preis", "type": "number", "name": "Preis (Zahl)"})

        assert cells(prepared, 2) == ["5", "7", "12"]
        assert prepared.changes == [
            "new column Preis (Zahl): 3 cells of Preis read as numbers, unit '$' removed; Preis stays as it is"
        ]
        assert dtypes(prepared)["Preis (Zahl)"] == "integer"

    def test_a_column_read_in_place_is_its_own_source(self) -> None:
        """Read from text in place, the column fills an open role as a named conversion would (`carry_bindings`)."""
        numbers = prepare(self.TEXT, {"op": "set_type", "column": "Preis", "type": "number"})
        dates = prepare(self.TEXT, {"op": "set_type", "column": "Datum", "type": "datetime"})

        assert numbers.converted == {"Preis": "Preis"} and dtypes(numbers)["Preis"] == "integer"
        assert dates.converted == {"Datum": "Datum"} and dtypes(dates)["Datum"] == "datetime"

    def test_a_column_already_of_its_type_is_no_conversion(self) -> None:
        unchanged = prepare("a,b\n1,2\n3,4\n", {"op": "set_type", "column": "b", "type": "number"})
        texts = prepare(self.TEXT, {"op": "set_type", "column": "Preis", "type": "text"})

        assert unchanged.converted == {} and texts.converted == {}

    def test_a_rename_or_drop_in_the_same_call_follows_the_new_column(self) -> None:
        convert = {"op": "set_type", "column": "Datum", "type": "datetime", "name": "neu"}

        renamed = prepare(self.TEXT, convert, {"op": "rename", "column": "neu", "name": "Tag"})
        dropped = prepare(self.TEXT, convert, {"op": "drop_columns", "columns": ["neu"]})

        assert renamed.converted == {"Tag": "Datum"}
        assert dropped.converted == {}

    def test_a_sort_on_the_new_column_puts_the_dates_oldest_first(self) -> None:
        prepared = prepare(
            self.TEXT,
            {"op": "set_type", "column": "Datum", "type": "datetime", "name": "Datum (Datum)"},
            {"op": "sort", "column": "Datum (Datum)"},
        )

        assert cells(prepared, 2) == ["2026-11-24", "2026-11-25", "2026-11-26"]
        assert reparse(prepared).profile.columns[2].order == "ascending"

    @pytest.mark.parametrize(
        ("operation", "message"),
        [
            (
                {"type": "text", "column": "Datum", "name": "x"},
                "set_type to text changes the column itself: leave name out",
            ),
            ({"type": "datetime", "column": "Datum", "name": "Preis"}, "a column named 'Preis' already exists"),
            ({"type": "number", "column": "n", "name": "x"}, "column 'n' already holds numbers: bind it as it is"),
            ({"type": "datetime", "column": "d", "name": "x"}, "column 'd' already holds dates: bind it as it is"),
        ],
    )
    def test_a_new_column_needs_a_free_name_and_a_conversion(self, operation: dict[str, str], message: str) -> None:
        text = "Datum;Preis;n;d\n26 Nov 2026;$5;1;2024-01-01\n25 Nov 2026;7;2;2024-01-02\n"

        assert failure(text, {"op": "set_type", **operation}) == ("invalid_operation", message)


class TestSetTypeMinus:
    def test_the_minus_sign_reads_as_a_sign_with_its_count(self) -> None:
        """`set_type number` reads `−100` as the parser does, and says how many cells were written so."""
        text = "v;w\n−100;a\n+75;b\n12 %;c\n"
        prepared = prepare(text, {"op": "set_type", "column": "v", "type": "number"})

        assert cells(prepared, 0) == ["-100", "75", "12"]
        assert prepared.changes == [
            "v: 3 cells read as numbers, unit '%' removed, 1 cell with the minus sign '−' read as negative numbers"
        ]

    def test_a_range_is_no_number(self) -> None:
        assert failure("v\n10–20\n5\n", {"op": "set_type", "column": "v", "type": "number"})[0] == "type_mismatch"

    def test_an_en_dash_is_no_minus(self) -> None:
        assert failure("v;w\n–5;a\n–7;b\n", {"op": "set_type", "column": "v", "type": "number"})[0] == "type_mismatch"


class TestDryRun:
    """`dry_run`: what a `set_type` of a text column would do, counted and nothing stored (`conversions.py`)."""

    @staticmethod
    def run(text: str, column: str, target: Literal["number", "datetime"]) -> prepare_module.DryRun | None:
        parsed = parse_dataset(text, text_columns=[column])  # a text column, as the dry run only reads those
        return prepare_module.dry_run(prepare_module.read_frame(parsed), column, target, parsed.profile.decimal)

    def test_a_certain_date_conversion(self) -> None:
        dry = self.run("Datum,v\n26 Nov 2026,1\n25 Nov 2026,2\n24 Nov 2026,3\n", "Datum", "datetime")

        assert dry is not None and dry.certain
        assert (dry.present, dry.read, dry.order) == (3, 3, "descending")
        assert dry.reading == "read as dates (format inferred, day before month)"

    @pytest.mark.parametrize(
        ("cells", "guess"),
        [
            (["1 Nov 2026", "1 Oct 2026"], None),
            (["Nov 2026", "Okt. 2026"], None),
            (["26.11.26", "25.11.26"], "the century of two-digit years"),
            (["01/11/2026", "01/10/2026"], "the day and month order"),
            (["13/11/2026", "01/10/2026"], None),  # a day over 12 settles the order
        ],
    )
    def test_what_a_date_reading_guesses(self, cells: list[str], guess: str | None) -> None:
        dry = self.run("d,v\n" + "".join(f"{cell},1\n" for cell in cells), "d", "datetime")

        assert dry is not None and dry.read == dry.present
        assert dry.guess == guess

    def test_a_column_that_is_no_text_is_no_candidate(self) -> None:
        parsed = parse_dataset("d,v\n2026-01-01,1\n")

        assert prepare_module.dry_run(prepare_module.read_frame(parsed), "d", "datetime") is None

    def test_mixed_cells_within_the_tenth_are_uncertain(self) -> None:
        cells = [f"{day} Nov 2026" for day in range(1, 11)] + ["no date"]
        dry = self.run("d,v\n" + "".join(f"{cell},1\n" for cell in cells), "d", "datetime")

        assert dry is not None and not dry.certain
        assert (dry.present, dry.read) == (11, 10)

    def test_more_than_a_tenth_unreadable_is_no_candidate(self) -> None:
        assert self.run("d,v\nNov 2026 x,1\nOct 2026,2\nwhenever,3\n", "d", "datetime") is None

    def test_a_name_column_is_no_candidate(self) -> None:
        assert self.run("Person,v\nMay,1\nJune,2\nApril,3\n", "Person", "datetime") is None

    def test_numbers_with_a_unit_on_some_cells(self) -> None:
        dry = self.run("p,v\n$5,1\n7,2\n$12,3\n", "p", "number")

        assert dry is not None and dry.certain and dry.reading == "read as numbers, unit '$' removed"

    def test_space_groups_are_a_guess(self) -> None:
        dry = self.run("p;v\n$1 200;1\n7;2\n", "p", "number")

        assert dry is not None and dry.guess == "that spaces or apostrophes separate thousands"

    def test_leading_zeros_are_a_guess(self) -> None:
        """A postal code column the parser kept text must never convert to numbers without a question."""
        dry = self.run("zip;v\n007;1\n$012;2\n105;3\n", "zip", "number")

        assert dry is not None and dry.guess == "that leading zeros are no part of the value"
        assert self.run("p;v\n1.05;1\n0.5;2\n", "p", "number").guess is None  # type: ignore[union-attr]

    def test_rounded_digits_are_a_guess(self) -> None:
        dry = self.run("account;v\n12345678901234567890;1\n5;2\n", "account", "number")

        assert dry is not None and not dry.certain
        assert dry.guess == "that values with more digits than a number holds may be rounded"

    def test_a_date_with_a_month_name_is_no_number(self) -> None:
        """`Nov 26, 2026` read as a number behind a unit `Nov` would be 26.2026."""
        assert self.run("d;v\nNov 26, 2026;1\nNov 25, 2026;2\n", "d", "number") is None

    @pytest.mark.parametrize(
        "text",
        [
            "Season,Wins\n2009-10,5\n2010-11,6\n2011-12,7\n",  # pandas reads each as a month
            "Bin,Share\n2000-05,1\n2005-10,2\n",
            "Saison,Wins\n2024-01,5\n2024-02,6\n",  # shaped like months, its name says spans
            "Version,n\n2024-01,5\n2024-02,6\n",
        ],
    )
    def test_a_column_of_year_spans_is_no_date_candidate(self, text: str) -> None:
        """The parser keeps these text (`_as_periods`), and a `certain` conversion must not rewrite them."""
        parsed = parse_dataset(text)
        column = parsed.profile.columns[0].name

        assert parsed.column_dtypes[column] == "text"
        assert prepare_module.dry_run(prepare_module.read_frame(parsed), column, "datetime") is None

    def test_a_year_run_reads_a_year_column(self) -> None:
        parsed = parse_dataset("Jahr,v\n2022,1\n2021,2\n2020,3\n")

        dry = prepare_module.year_run(prepare_module.read_frame(parsed), "Jahr")

        assert dry.certain and (dry.read, dry.order, dry.date_format) == (3, "descending", "YYYY")
        assert dry.reading == "read as years (YYYY, each as 1 January)"


class TestRowNumber:
    def test_a_new_first_column_numbers_the_rows(self) -> None:
        prepared = prepare("value,note\n1,a\n3,b\n5,c\n4,d\n", {"op": "row_number"})

        assert prepared.csv.splitlines() == ["index,value,note", "1,1,a", "2,3,b", "3,5,c", "4,4,d"]
        assert prepared.changes == ["new first column index: the rows numbered 1 to 4"]
        assert prepared.row_numbers == ["index"]

    def test_it_stays_a_whole_number_column_through_the_reparse(self) -> None:
        prepared = prepare("value\n1\n3\n5\n", {"op": "row_number", "name": "Nr"})
        parsed = parse_dataset(prepared.csv, find_table=False, canonical=True)

        assert parsed.column_dtypes["Nr"] == "integer"

    @pytest.mark.parametrize(
        "text", ["index,value\n1,1\n2,3\n3,5\n", "index,value\n0,1\n1,3\n2,5\n", "index,value\n3,1\n1,3\n2,5\n"]
    )
    def test_a_pasted_row_number_in_front_is_reused_as_it_is(self, text: str) -> None:
        prepared = prepare(text, {"op": "row_number", "name": "index"})

        assert prepared.csv == parse_dataset(text).csv
        assert prepared.changes == ["index already numbers the rows"]
        assert prepared.row_numbers == ["index"]

    def test_a_pasted_row_number_elsewhere_moves_to_the_front_with_its_values(self) -> None:
        prepared = prepare("value,index,note\n1,3,a\n3,1,b\n5,2,c\n", {"op": "row_number", "name": "index"})

        # Only the column order changes: the rows keep their order and every cell its value.
        assert prepared.csv.splitlines() == ["index,value,note", "3,1,a", "1,3,b", "2,5,c"]
        assert prepared.changes == ["index already numbers the rows; moved to the first column"]
        assert prepared.row_numbers == ["index"]

    def test_a_column_of_that_name_with_other_values_is_refused(self) -> None:
        assert failure("value,index\n1,5\n3,5\n", {"op": "row_number"}) == (
            "invalid_operation",
            "a column named 'index' already exists",
        )

    def test_it_follows_a_rename_in_the_same_call(self) -> None:
        prepared = apply_operations(
            parse_dataset("value\n1\n3\n"),
            OPERATIONS.validate_python([{"op": "row_number"}, {"op": "rename", "column": "index", "name": "Nr"}]),
        )

        assert prepared.row_numbers == ["Nr"]

    def test_a_full_table_takes_no_more_columns(self) -> None:
        header = ",".join(f"c{index}" for index in range(MAX_COLUMNS))
        row = ",".join("1" for _ in range(MAX_COLUMNS))

        assert failure(f"{header}\n{row}\n{row}\n", {"op": "row_number"})[0] == "too_wide"


# The owner's case of 2026-11-04, invented: a customers table with an index and subscription dates, no other number.
CUSTOMERS = "Index,First Name,Subscription Date\n1,Mara,2021-04-01\n2,Tobin,2020-02-29\n3,Ilse,\n4,Ravi,2024-12-31\n"


def date_number(unit: str, column: str = "Subscription Date", **extra: str) -> dict[str, Any]:
    return {"op": "date_number", "column": column, "unit": unit, **extra}


class TestDateNumber:
    @pytest.mark.parametrize(
        ("unit", "name", "values", "dtype"),
        [
            ("year", "Subscription Date (year)", ["2021", "2020", "", "2024"], "integer"),
            ("days", "Subscription Date (days)", ["397", "0", "", "1767"], "integer"),
            ("timestamp", "Subscription Date (Unix time)", ["1617235200", "1582934400", "", "1735603200"], "integer"),
            # 90 of 365 days gone by; 59 of the leap year's 366; 365 of 366.
            (
                "decimal_year",
                "Subscription Date (decimal year)",
                [repr(2021 + 90 / 365), repr(2020 + 59 / 366), "", repr(2024 + 365 / 366)],
                "number",
            ),
        ],
    )
    def test_each_unit_adds_a_number_column_and_keeps_the_dates(
        self, unit: str, name: str, values: list[str], dtype: str
    ) -> None:
        prepared = prepare(CUSTOMERS, date_number(unit))

        assert rows(prepared)[0] == f"Index,First Name,Subscription Date,{name}"  # appended last
        assert cells(prepared, 3) == values
        assert cells(prepared, 2) == ["2021-04-01", "2020-02-29", "", "2024-12-31"]  # the original stays as it is
        assert [row[:-1] for row in csv.reader(io.StringIO(prepared.csv))] == list(
            csv.reader(io.StringIO(parse_dataset(CUSTOMERS).csv))
        )
        assert dtypes(prepared) == {
            "Index": "integer",
            "First Name": "text",
            "Subscription Date": "datetime",
            name: dtype,
        }
        # The missing cell stays missing, and the change line counts both.
        assert prepared.changes[0].startswith(f"new column {name}: 3 dates of Subscription Date read as ")
        assert prepared.changes[0].count("1 cell without a date is empty; Subscription Date stays as it is") == 1
        # An open required role that takes numbers takes it, as it takes a `set_type` with `name`.
        assert prepared.converted == {name: "Subscription Date"}

    def test_the_change_lines_say_what_each_number_is(self) -> None:
        lines = [prepare(CUSTOMERS, date_number(unit)).changes[0] for unit in ("year", "days", "timestamp")]

        assert lines[0] == (
            "new column Subscription Date (year): 3 dates of Subscription Date read as calendar years, 1 cell without "
            "a date is empty; Subscription Date stays as it is"
        )
        assert "read as whole days since 2020-02-29, the earliest date, which is 0," in lines[1]
        assert lines[2].endswith("Subscription Date stays as it is, each date counted from its midnight UTC")

    @pytest.mark.parametrize(
        ("language", "name"),
        [("de", "Subscription Date (Tage)"), ("fr", "Subscription Date (jours)"), ("sv", "Subscription Date (days)")],
    )
    def test_the_default_name_is_in_the_session_language(self, language: str, name: str) -> None:
        prepared = apply_operations(
            parse_dataset(CUSTOMERS), OPERATIONS.validate_python([date_number("days")]), language=language
        )

        assert rows(prepared)[0].endswith(f",{name}")

    def test_a_name_the_user_gives_is_used_and_a_taken_one_is_refused(self) -> None:
        named = prepare(CUSTOMERS, date_number("year", name="Jahr"))

        assert rows(named)[0] == "Index,First Name,Subscription Date,Jahr"
        assert failure(CUSTOMERS, date_number("year", name="Index")) == (
            "invalid_operation",
            "a column named 'Index' already exists",
        )

    def test_a_taken_default_name_gets_a_number(self) -> None:
        prepared = prepare(CUSTOMERS, date_number("days"), date_number("days"))

        assert rows(prepared)[0].endswith(",Subscription Date (days),Subscription Date_2 (days)")

    def test_a_time_of_day_counts_for_the_timestamp_but_not_for_the_days(self) -> None:
        """23:00 and 01:00 the next morning are two hours apart, but on two calendar dates: one day."""
        text = "t,v\n2024-06-01 23:00,1\n2024-06-02 01:30:15,2\n"

        days = prepare(text, date_number("days", column="t"))
        stamps = prepare(text, date_number("timestamp", column="t"))
        years = prepare(text, date_number("decimal_year", column="t"))

        assert cells(days, 2) == ["0", "1"]
        # Read as UTC, which the line says: 2024-06-01T00:00:00Z is 1717200000.
        assert cells(stamps, 2) == [str(1717200000 + 23 * 3600), str(1717200000 + 86400 + 5415)]
        assert stamps.changes[0].endswith("t stays as it is, times without a UTC offset read as UTC")
        # 152 days of the leap year 2024 gone by on 1 June, and 23 hours of the 153rd.
        assert cells(years, 2)[0] == repr(2024 + (152 * 86400 + 23 * 3600) / (366 * 86400))

    def test_a_timestamp_converts_a_utc_offset_and_the_other_units_keep_the_columns_clock(self) -> None:
        """At 00:30 on New Year's Day at UTC+02:00 it is still 2024 in UTC: the year is the cell's, the time UTC's."""
        text = "t,v\n2025-01-01T00:30:00+02:00,1\n2025-01-02T12:00:00+02:00,2\n"

        stamps = prepare(text, date_number("timestamp", column="t"))
        years = prepare(text, date_number("year", column="t"))

        assert cells(stamps, 2) == ["1735684200", str(1735684200 + 86400 + 11 * 3600 + 1800)]
        assert stamps.changes[0].endswith("t stays as it is, the moments converted to UTC from UTC+02:00")
        assert cells(years, 2) == ["2025", "2025"]
        assert "read as calendar years, by the clock of UTC+02:00;" in years.changes[0]

    def test_the_days_and_the_decimal_year_keep_the_columns_clock(self) -> None:
        """Both moments fall on 1 January 2025 at UTC+02:00; in UTC the first is still 31 December 2024."""
        text = "t,v\n2025-01-01T00:30:00+02:00,1\n2025-01-01T12:00:00+02:00,2\n"

        days = prepare(text, date_number("days", column="t"))
        years = prepare(text, date_number("decimal_year", column="t"))

        assert cells(days, 2) == ["0", "0"]  # one calendar date on the column's clock, not two in UTC
        clock = "read as whole days since 2025-01-01, the earliest date, which is 0, by the clock of UTC+02:00"
        assert clock in days.changes[0]
        assert cells(years, 2)[0] == repr(2025 + 1800 / (365 * 86400))  # half an hour of 2025 gone by
        assert all(cell.startswith("2025.") for cell in cells(years, 2))

    def test_a_column_the_parser_wrote_in_utc_says_so(self) -> None:
        text = "t,v\n2024-03-30T12:00:00+01:00,1\n2024-04-01T12:00:00+02:00,2\n"  # summer time: two offsets

        stamps = prepare(text, date_number("timestamp", column="t"))

        assert cells(stamps, 2) == ["1711796400", "1711965600"]  # 11:00 and 10:00 UTC
        assert stamps.changes[0].endswith("the moments as stored, in UTC")

    def test_a_fraction_of_a_second_is_kept_as_decimals(self) -> None:
        stamps = prepare("t,v\n2024-06-01 00:00:00.25,1\n2024-06-01 00:00:01,2\n", date_number("timestamp", column="t"))

        assert cells(stamps, 2) == ["1717200000.25", "1717200001"]
        assert dtypes(stamps)["t (Unix time)"] == "number"
        assert stamps.changes[0].endswith("fractions of a second kept as decimals")

    def test_a_fraction_far_from_1970_is_counted_as_rounded(self) -> None:
        stamps = prepare(
            "t,v\n2300-01-01 00:00:00.000001,1\n2024-01-01 00:00:00.5,2\n", date_number("timestamp", column="t")
        )

        assert stamps.changes[0].endswith(", 1 value more than 272 years from 1970 rounded to the float's digits")

    def test_a_whole_second_far_from_1970_is_exact_and_not_counted(self) -> None:
        """Copilot on #12558: 2300-01-01 is 10413792000.0 exactly; only a value whose text loses a digit counts."""
        stamps = prepare("t,v\n2300-01-01 00:00:00,1\n2024-01-01 00:00:00.5,2\n", date_number("timestamp", column="t"))

        assert cells(stamps, 2) == ["10413792000", "1704067200.5"]
        assert stamps.changes[0].endswith("fractions of a second kept as decimals")

    def test_whole_seconds_stay_exact_for_any_year(self) -> None:
        stamps = prepare("t,v\n0001-01-01,1\n9999-12-31 23:59:59,2\n", date_number("timestamp", column="t"))

        assert cells(stamps, 2) == ["-62135596800", "253402300799"]

    @pytest.mark.parametrize(("column", "kind"), [("First Name", "text"), ("Index", "number")])
    def test_a_column_that_is_no_date_is_a_type_mismatch(self, column: str, kind: str) -> None:
        assert failure(CUSTOMERS, date_number("year", column=column)) == (
            "type_mismatch",
            f"column '{column}' is {kind}; date_number needs a datetime column: set_type it to datetime first",
        )

    def test_a_column_of_dates_in_a_compact_format_converts_after_its_set_type_in_the_same_call(self) -> None:
        """The refusal's hint works: `202104` is a number to the parser, a date after `set_type` `YYYYMM`."""
        text = "Kunde,Abo\nA,202104\nB,202002\n"
        assert failure(text, date_number("days", column="Abo"))[0] == "type_mismatch"

        prepared = prepare(
            text,
            {"op": "set_type", "column": "Abo", "type": "datetime", "date_format": "YYYYMM"},
            date_number("days", column="Abo"),
        )

        assert rows(prepared) == ["Kunde,Abo,Abo (days)", "A,2021-04-01,425", "B,2020-02-01,0"]

    def test_a_column_without_any_date_left_is_refused(self) -> None:
        text = "a,d\n1,2024-01-01\n2,\n"

        assert failure(text, drop("d", "eq", "2024-01-01"), date_number("year", column="d")) == (
            "invalid_operation",
            "column 'd' holds no date, so column 'd (year)' would be empty",
        )

    def test_an_unknown_column_is_named(self) -> None:
        assert failure(CUSTOMERS, date_number("year", column="Signup"))[0] == "unknown_column"

    def test_it_follows_a_rename_in_the_same_call(self) -> None:
        prepared = prepare(
            CUSTOMERS, date_number("days"), {"op": "rename", "column": "Subscription Date (days)", "name": "Tage"}
        )

        assert prepared.converted == {"Tage": "Subscription Date"}

    @pytest.mark.parametrize(
        "operation",
        [
            {"op": "date_number", "column": "d"},
            {"op": "date_number", "column": "d", "unit": "months"},
            {"op": "date_number", "column": "d", "unit": "year", "name": " Jahr"},
            {"op": "date_number", "column": "d", "unit": "year", "name": "x" * (MAX_COLUMN_NAME_CHARS + 1)},
            {"op": "date_number", "column": "d", "unit": "year", "format": "%Y"},
        ],
    )
    def test_malformed_operations_fail_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])

    def test_a_full_table_takes_no_more_columns(self) -> None:
        header = ",".join(f"c{index}" for index in range(MAX_COLUMNS - 1))
        row = ",".join("1" for _ in range(MAX_COLUMNS - 1))

        assert failure(f"{header},d\n{row},2024-01-01\n{row},2024-01-02\n", date_number("year", column="d"))[0] == (
            "too_wide"
        )


class TestSetTypeText:
    def test_cells_become_their_canonical_text_and_stay_text_through_the_reparse(self) -> None:
        """The change line is true: the column is text in the next version, not re-typed by its cells (verifiers)."""
        prepared = prepare(SALES, {"op": "set_type", "column": "Datum", "type": "text"})

        assert prepared.csv == SALES_CSV
        assert prepared.changes == ["Datum: 6 cells now text"]
        assert prepared.text_columns == ["Datum"]
        again = reparse(prepared)
        assert again.column_dtypes["Datum"] == "text" and again.text_columns == ["Datum"]
        assert again.profile.columns[0].top == [
            *("2024-01-05", "2024-01-20", "2024-02-14", "2024-02-28", "2024-03-15", "2024-03-31")
        ]  # six distinct dates: every one listed

    def test_a_column_kept_text_stays_text_in_later_versions_until_set_back(self) -> None:
        """The hint travels with the stored version: a later change re-parses with it, and `set_type number` lifts it."""
        text = "year,v\n2023,1\n2024,2\n"
        prepared = prepare(text, {"op": "set_type", "column": "year", "type": "text"})
        version_two = reparse(prepared)
        assert version_two.column_dtypes["year"] == "text" and version_two.text_columns == ["year"]

        renamed = apply_operations(
            version_two, OPERATIONS.validate_python([{"op": "rename", "column": "year", "name": "Jahr"}])
        )
        assert renamed.text_columns == ["Jahr"] and reparse(renamed).column_dtypes["Jahr"] == "text"
        dropped = apply_operations(
            version_two, OPERATIONS.validate_python([{"op": "drop_columns", "columns": ["year"]}])
        )
        assert dropped.text_columns == []
        numbers = apply_operations(
            version_two, OPERATIONS.validate_python([{"op": "set_type", "column": "year", "type": "number"}])
        )
        assert numbers.text_columns == [] and reparse(numbers).column_dtypes["year"] == "integer"
        assert numbers.changes == ["year: 2 cells read as numbers"]

    def test_an_already_text_column_is_kept_text(self) -> None:
        prepared = prepare(SALES, {"op": "set_type", "column": "Tier", "type": "text"})

        assert prepared.csv == SALES_CSV
        assert prepared.changes == ["Tier: already text, nothing changed"]
        assert prepared.text_columns == ["Tier"]

    def test_text_then_back_to_dates(self) -> None:
        prepared = prepare(
            SALES,
            {"op": "set_type", "column": "Datum", "type": "text"},
            {"op": "set_type", "column": "Datum", "type": "datetime", "date_format": "YYYY-MM-DD"},
        )

        assert prepared.csv == SALES_CSV
        assert prepared.changes == ["Datum: 6 cells now text", "Datum: 6 cells read as dates (YYYY-MM-DD)"]
        assert prepared.text_columns == []


class TestAggregate:
    def test_sum_per_month(self) -> None:
        prepared = prepare(
            SALES,
            drop("Tier", "eq", "Gesamt"),
            {"op": "aggregate", "by": ["Datum"], "column": "Umsatz", "how": "sum", "period": "month"},
        )

        assert rows(prepared) == ["Datum,Umsatz", "2024-01,2000.5", "2024-02,450.25", "2024-03,999.75"]
        assert prepared.changes[1] == "summed Umsatz by Datum (month): 3 rows, 2 other columns dropped"
        assert dtypes(prepared) == {"Datum": "text", "Umsatz": "number"}

    @pytest.mark.parametrize(("how", "result"), [("sum", "25.3"), ("mean", "6.325")])
    def test_a_float_total_adds_up_the_cells_as_they_are_written(self, how: str, result: str) -> None:
        """Added as floats these cells give 25.299999999999997, a value no one wrote (`_decimal_total`)."""
        operation = {"op": "aggregate", "by": ["k"], "column": "v", "how": how}

        assert rows(prepare("k,v\na,19.99\na,5.01\na,0.1\na,0.2\n", operation)) == ["k,v", f"a,{result}"]

    @pytest.mark.parametrize(("how", "cell"), [("sum", "0"), ("mean", "")])
    def test_a_group_without_a_value_totals_zero_and_has_no_mean(self, how: str, cell: str) -> None:
        operation = {"op": "aggregate", "by": ["k"], "column": "v", "how": how}

        assert rows(prepare("k,v\na,1.5\nb,\n", operation)) == ["k,v", "a,1.5", f"b,{cell}"]

    def test_count_names_its_column_count(self) -> None:
        prepared = prepare(SALES, {"op": "aggregate", "by": ["Tier"], "column": "Anteil", "how": "count"})

        assert rows(prepared) == ["Tier,count", "Gesamt,1", "Hund,3", "Katze,1"]
        assert prepared.changes == ["counted Anteil by Tier: 3 rows, 2 other columns dropped"]
        assert dtypes(prepared)["count"] == "integer"

    def test_mean_by_two_keys_per_quarter(self) -> None:
        operation = {"op": "aggregate", "by": ["Tier", "Datum"], "column": "Umsatz", "how": "mean", "period": "quarter"}
        prepared = prepare(SALES, operation)

        assert rows(prepared) == [
            "Tier,Datum,Umsatz",
            "Gesamt,2024-Q1,3450.5",
            "Hund,2024-Q1,833.5",
            "Katze,2024-Q1,475",
        ]
        assert prepared.changes == ["averaged Umsatz by Tier and Datum (quarter): 3 rows, 1 other column dropped"]

    def test_year_min_and_max(self) -> None:
        minimum = prepare(
            SALES, {"op": "aggregate", "by": ["Datum"], "column": "Umsatz", "how": "min", "period": "year"}
        )
        maximum = prepare(SALES, {"op": "aggregate", "by": ["Datum"], "column": "Tier", "how": "max", "period": "year"})

        assert rows(minimum) == ["Datum,Umsatz", "2024,150"]
        assert rows(maximum) == ["Datum,Tier", "2024,Katze"]
        assert minimum.changes == ["took the minimum of Umsatz by Datum (year): 1 row, 2 other columns dropped"]
        assert maximum.changes[0].startswith("took the maximum of Tier by Datum (year)")

    def test_a_missing_key_forms_its_own_group(self) -> None:
        prepared = prepare("k,v\na,1\n,2\na,3\n", {"op": "aggregate", "by": ["k"], "column": "v", "how": "sum"})

        assert rows(prepared) == ["k,v", "a,4", ",2"]

    def test_boolean_values_sum_and_average(self) -> None:
        text = "k,f\na,true\na,false\nb,true\n"
        summed = prepare(text, {"op": "aggregate", "by": ["k"], "column": "f", "how": "sum"})
        averaged = prepare(text, {"op": "aggregate", "by": ["k"], "column": "f", "how": "mean"})

        assert rows(summed) == ["k,f", "a,1", "b,1"]
        assert rows(averaged) == ["k,f", "a,0.5", "b,1"]

    @pytest.mark.parametrize(
        ("operation", "code"),
        [
            ({"op": "aggregate", "by": ["Datum"], "column": "Tier", "how": "sum"}, "type_mismatch"),
            ({"op": "aggregate", "by": ["Datum"], "column": "Anteil", "how": "mean"}, "type_mismatch"),
            (
                {"op": "aggregate", "by": ["Tier"], "column": "Umsatz", "how": "sum", "period": "month"},
                "invalid_operation",
            ),
            ({"op": "aggregate", "by": ["Tier"], "column": "Tier", "how": "count"}, "invalid_operation"),
            ({"op": "aggregate", "by": ["Art"], "column": "Umsatz", "how": "sum"}, "unknown_column"),
            ({"op": "aggregate", "by": ["Tier"], "column": "Betrag", "how": "sum"}, "unknown_column"),
        ],
    )
    def test_refusals(self, operation: dict[str, Any], code: str) -> None:
        assert failure(SALES, operation)[0] == code

    def test_a_key_named_count_cannot_take_a_count(self) -> None:
        text = "count,v\na,1\n"

        assert (
            failure(text, {"op": "aggregate", "by": ["count"], "column": "v", "how": "count"})[0] == "invalid_operation"
        )


class TestSort:
    def test_descending(self) -> None:
        prepared = prepare(SALES, {"op": "sort", "column": "Umsatz", "descending": True})

        assert cells(prepared, 3) == ["3450.5", "1200.5", "999.75", "800", "300.25", "150"]
        assert prepared.changes == ["sorted by Umsatz, descending"]

    def test_ascending_is_stable_with_missing_cells_last(self) -> None:
        prepared = prepare(SALES, {"op": "sort", "column": "Anteil"})

        assert cells(prepared, 1) == ["Gesamt", "Hund", "Hund", "Hund", "Katze", "Katze"]
        assert rows(prepared)[-1] == "2024-02-28,Katze,,150"
        assert prepared.changes == ["sorted by Anteil, ascending"]

    def test_unknown_column(self) -> None:
        assert failure(SALES, {"op": "sort", "column": "Art"})[0] == "unknown_column"

    @pytest.mark.parametrize("descending", [False, True])
    def test_month_names_sort_in_calendar_order(self, descending: bool) -> None:
        """Alphabetically `Apr` would come before `Jan` (live test round 4 of 2026-10-15)."""
        prepared = prepare(
            "Monat,Besucher\nMai,5\nJan,1\nApr,4\nJun,6\nFeb,2\nMär,3\n",
            {"op": "sort", "column": "Monat", "descending": descending},
        )
        calendar = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun"]

        assert cells(prepared, 0) == (calendar[::-1] if descending else calendar)
        order = "descending" if descending else "ascending"
        assert prepared.changes == [f"sorted by Monat, {order}, in calendar order of the months"]

    def test_text_that_is_not_all_months_sorts_alphabetically(self) -> None:
        prepared = prepare("k,v\nMai,5\nJan,1\nZoo,9\nApr,4\n", {"op": "sort", "column": "k"})

        assert cells(prepared, 0) == ["Apr", "Jan", "Mai", "Zoo"]
        assert prepared.changes == ["sorted by k, ascending"]


class TestPivotLonger:
    def test_two_unequal_series(self) -> None:
        prepared = prepare(WIDE, {"op": "pivot_longer", "columns": ["Hüte", "Schuhe"]})

        # The paste reads `2024-01` as the month's first day (live test round 7 of 2026-10-16).
        assert rows(prepared) == [
            "Monat,series,value",
            "2024-01-01,Hüte,10",
            "2024-02-01,Hüte,15",
            "2024-03-01,Hüte,",
            "2024-01-01,Schuhe,20",
            "2024-02-01,Schuhe,",
            "2024-03-01,Schuhe,30",
        ]
        assert prepared.changes == ["pivoted 2 columns into series/value: 6 rows"]
        assert dtypes(prepared) == {"Monat": "datetime", "series": "text", "value": "integer"}

    def test_a_melted_columns_name_is_refused_as_a_new_name(self) -> None:
        """pandas' `melt` raises a ValueError for a `value_name` that names an input column (review of #12206)."""
        for names in (("Artikel", "Hüte"), ("Schuhe", "Stück")):
            operation = {
                "op": "pivot_longer",
                "columns": ["Hüte", "Schuhe"],
                "names_to": names[0],
                "values_to": names[1],
            }

            assert failure(WIDE, operation)[0] == "invalid_operation"

    def test_own_names(self) -> None:
        operation = {"op": "pivot_longer", "columns": ["Hüte", "Schuhe"], "names_to": "Artikel", "values_to": "Stück"}

        assert rows(prepare(WIDE, operation))[0] == "Monat,Artikel,Stück"

    def test_mixed_kinds_become_text(self) -> None:
        prepared = prepare("k,a,b\nx,1,t\n", {"op": "pivot_longer", "columns": ["a", "b"]})

        assert rows(prepared)[1:] == ["x,a,1", "x,b,t"]
        assert dtypes(prepared)["value"] == "text"
        assert "value" in prepared.text_columns  # by content the melted cells could type again

    def test_a_source_kept_text_keeps_the_melted_column_text(self) -> None:
        prepared = prepare(
            "k,a,b\nx,2023,2024\n",
            {"op": "set_type", "column": "a", "type": "text"},
            {"op": "set_type", "column": "b", "type": "text"},
            {"op": "pivot_longer", "columns": ["a", "b"]},
        )

        assert prepared.text_columns == ["value"]
        assert parse_dataset(prepared.csv, text_columns=prepared.text_columns).column_dtypes["value"] == "text"
        assert parse_dataset(prepared.csv).column_dtypes["value"] == "integer"  # what the hint prevents

    @pytest.mark.parametrize(
        ("operation", "code"),
        [
            ({"op": "pivot_longer", "columns": ["Hüte", "Hüte"]}, "invalid_operation"),
            ({"op": "pivot_longer", "columns": ["Hüte", "Schuhe"], "names_to": "Monat"}, "invalid_operation"),
            (
                {"op": "pivot_longer", "columns": ["Hüte", "Schuhe"], "names_to": "x", "values_to": "x"},
                "invalid_operation",
            ),
            ({"op": "pivot_longer", "columns": ["Hüte", "Socken"]}, "unknown_column"),
        ],
    )
    def test_refusals(self, operation: dict[str, Any], code: str) -> None:
        assert failure(WIDE, operation)[0] == code

    def test_the_row_cap(self) -> None:
        text = "a,b\n" + "1,2\n" * (MAX_ROWS // 2 + 1)
        code, message = failure(text, {"op": "pivot_longer", "columns": ["a", "b"]})

        assert code == "invalid_operation"
        assert f"{MAX_ROWS:,}" in message

    def test_a_result_over_the_cap_is_refused_before_the_reparse(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The long format of a wide dataset can exceed the computed-data cap; the model hears a code, not `internal`.

        The cap is lowered for the test: at 2 MiB the input would be over the paste cap first.
        """
        monkeypatch.setattr(prepare_module, "MAX_COMPUTED_BYTES", 200 * 1024)
        header = "id," + ",".join(f"t{i}" for i in range(8)) + ",a,b\n"
        # The filler cells differ by row: a column with the same text in every row would move to the notes.
        filler = ["t" * 37 + str(row % 10) for row in range(380)]
        text = header + "".join(f"{row}," + ",".join([filler[row]] * 8) + f",{row},{row * 2}\n" for row in range(380))
        assert len(text.encode()) < 200 * 1024
        code, message = failure(text, {"op": "pivot_longer", "columns": ["a", "b"]})

        assert code == "invalid_operation"
        assert "larger than 200 KB" in message

    def test_a_datetime_with_times_keeps_them_next_to_another_kind(self) -> None:
        """Unlike kinds melt into text: a timestamp is written with its time, as its own column was (verifiers)."""
        prepared = prepare(
            "id,d,v\n1,2024-01-05 10:30,2\n2,2024-02-03 11:00,3\n", {"op": "pivot_longer", "columns": ["d", "v"]}
        )

        assert cells(prepared, 2) == ["2024-01-05T10:30:00", "2024-02-03T11:00:00", "2", "3"]
        assert dtypes(prepared)["value"] == "text"

    def test_fractions_and_offsets_survive_an_operation(self) -> None:
        """Owner rule of 2026-10-15: data keeps its precision and its zone through a change."""
        text = "t,v\n2024-01-05T10:30:00.123456+01:00,2\n2024-01-05T11:00:00.5+01:00,3\n2024-01-05T12:00:00+01:00,4\n"
        prepared = prepare(text, drop("v", "eq", 4))

        assert cells(prepared, 0) == ["2024-01-05T10:30:00.123456+01:00", "2024-01-05T11:00:00.500000+01:00"]
        assert dtypes(prepared)["t"] == "datetime"

    def test_datetime_columns_alone_keep_their_kind_and_time(self) -> None:
        text = "id,start,end\n1,2024-01-05 10:30,2024-01-06 00:00\n"
        prepared = prepare(text, {"op": "pivot_longer", "columns": ["start", "end"]})

        assert cells(prepared, 2) == ["2024-01-05T10:30:00", "2024-01-06T00:00:00"]
        assert dtypes(prepared)["value"] == "datetime"


class TestPivotWider:
    def test_round_trip_with_pivot_longer(self) -> None:
        prepared = prepare(
            WIDE,
            {"op": "pivot_longer", "columns": ["Hüte", "Schuhe"]},
            {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]},
        )

        assert prepared.csv == parse_dataset(WIDE).csv
        assert prepared.changes[1] == "pivoted series into 2 columns with values from value: 3 rows"

    def test_missing_combinations_are_missing_cells(self) -> None:
        operation = {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}
        prepared = prepare(LONG, operation)

        assert rows(prepared) == ["Monat,Hüte,Schuhe", "2024-01-01,10,20", "2024-02-01,15,", "2024-03-01,,30"]
        assert dtypes(prepared) == {"Monat": "datetime", "Hüte": "integer", "Schuhe": "integer"}

    def test_values_kept_text_make_text_columns(self) -> None:
        operation = {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}
        prepared = prepare(LONG, {"op": "set_type", "column": "value", "type": "text"}, operation)

        assert prepared.text_columns == ["Hüte", "Schuhe"]
        assert dtypes(prepared) == {"Monat": "datetime", "Hüte": "text", "Schuhe": "text"}

    def test_text_hints_carry_the_names_the_reparse_gives(self) -> None:
        """A value longer than a column name may be is shortened by the re-parse; the hint must match it."""
        long_name = "x" * 70
        text = f"k,series,value\na,{long_name},2023\nb,{long_name},2024\nc,short,2025\n"
        operation = {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["k"]}
        prepared = prepare(text, {"op": "set_type", "column": "value", "type": "text"}, operation)

        assert prepared.text_columns == ["short", "x" * 64]
        again = parse_dataset(prepared.csv, text_columns=prepared.text_columns)
        assert again.column_dtypes == {"k": "text", "x" * 64: "text", "short": "text"}

    def test_rows_without_a_name_are_left_out_and_other_columns_dropped(self) -> None:
        text = (
            "Monat,series,value,note\n"
            "2024-01,Hüte,10,n\n"
            "2024-02,Hüte,15,o\n"
            "2024-01,Schuhe,20,n\n"
            "2024-03,Schuhe,30,o\n"
            "2024-03,,99,n\n"
        )
        operation = {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}
        prepared = prepare(text, operation)

        assert len(rows(prepared)) == 4
        assert prepared.changes == [
            "pivoted series into 2 columns with values from value: 3 rows, 1 row without a series left out, "
            "1 other column dropped"
        ]

    def test_two_index_columns(self) -> None:
        text = "y,m,s,v\n2024,1,a,1\n2024,1,b,2\n2024,2,a,3\n"
        operation = {"op": "pivot_wider", "names_from": "s", "values_from": "v", "index": ["y", "m"]}

        assert rows(prepare(text, operation)) == ["y,m,a,b", "2024,1,1,2", "2024,2,3,"]

    def test_duplicate_pairs_are_refused(self) -> None:
        operation = {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}
        code, message = failure(LONG + "2024-01,Hüte,99\n", operation)

        assert code == "invalid_operation"
        assert "aggregate first" in message

    def test_too_many_new_columns(self) -> None:
        text = "k,s,v\n" + "".join(f"x{i % 2},s{i},{i}\n" for i in range(MAX_WIDER_COLUMNS + 1))
        operation = {"op": "pivot_wider", "names_from": "s", "values_from": "v", "index": ["k"]}

        assert failure(text, operation)[0] == "too_wide"

    def test_too_many_columns_in_all(self) -> None:
        text = "k,j,s,v\n" + "".join(f"x{i % 2},y{i % 3},s{i},{i}\n" for i in range(MAX_WIDER_COLUMNS - 1))
        operation = {"op": "pivot_wider", "names_from": "s", "values_from": "v", "index": ["k", "j"]}

        assert failure(text, operation)[0] == "too_wide"

    @pytest.mark.parametrize(
        ("operation", "code"),
        [
            (
                {"op": "pivot_wider", "names_from": "series", "values_from": "series", "index": ["Monat"]},
                "invalid_operation",
            ),
            (
                {"op": "pivot_wider", "names_from": "Monat", "values_from": "value", "index": ["Monat"]},
                "invalid_operation",
            ),
            (
                {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Jahr"]},
                "unknown_column",
            ),
        ],
    )
    def test_refusals(self, operation: dict[str, Any], code: str) -> None:
        assert failure(LONG, operation)[0] == code

    def test_a_name_equal_to_an_index_column_is_refused(self) -> None:
        operation = {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}
        code, message = failure(LONG + "2024-03,Monat,1\n", operation)

        assert code == "invalid_operation"
        assert "named like an index column" in message


# The owner's case of 2026-10-12: a sine table and "positive class 1, negative class 2" as a feature column.
SINE = "x,y\n-2,-0.909\n-1,-0.841\n0,0\n1,0.841\n2,0.909\n3,\n"


def classify(name: str, *rules: tuple[list[dict[str, Any]], str], otherwise: str | None = None) -> dict[str, Any]:
    listed = [{"where": where, "label": label} for where, label in rules]
    operation: dict[str, Any] = {"op": "classify", "name": name, "rules": listed}
    if otherwise is not None:
        operation["otherwise"] = otherwise
    return operation


def above(column: str, value: object) -> list[dict[str, Any]]:
    return [{"column": column, "test": "gt", "value": value}]


class TestClassify:
    def test_labels_rows_by_the_first_rule_and_otherwise(self) -> None:
        prepared = prepare(SINE, classify("Klasse", (above("y", 0), "Klasse 1"), otherwise="Klasse 2"))

        assert rows(prepared)[0] == "x,y,Klasse"
        assert cells(prepared, 2) == ["Klasse 2", "Klasse 2", "Klasse 2", "Klasse 1", "Klasse 1", "Klasse 2"]
        assert prepared.changes == [
            "added column Klasse: 'Klasse 1' for 2 rows where y > 0, 'Klasse 2' for the other 4 rows"
        ]
        assert dtypes(prepared)["Klasse"] == "text"

    def test_an_earlier_rule_wins(self) -> None:
        prepared = prepare(
            SINE, classify("Stufe", (above("y", 0.9), "hoch"), (above("y", 0), "mittel"), otherwise="tief")
        )

        assert cells(prepared, 2) == ["tief", "tief", "tief", "mittel", "hoch", "tief"]
        assert prepared.changes == [
            "added column Stufe: 'hoch' for 1 row where y > 0.9, 'mittel' for 1 row where y > 0, 'tief' for the other 4 rows"
        ]

    def test_rows_no_rule_names_stay_missing_without_otherwise(self) -> None:
        prepared = prepare(
            SINE, classify("sign", (above("y", 0), "pos"), ([{"column": "y", "test": "lt", "value": 0}], "neg"))
        )

        assert cells(prepared, 2) == ["neg", "neg", "", "pos", "pos", ""]
        assert prepared.changes == [
            "added column sign: 'pos' for 2 rows where y > 0, 'neg' for 2 rows where y < 0, 2 rows without a label"
        ]

    @pytest.mark.parametrize("label", ["+", "Klasse 1", "1", "0.5", "true", "2024-01-05", "N/A x", "jana-novak.de"])
    def test_an_accepted_label_survives_the_reparse(self, label: str) -> None:
        """The stored version holds the label the change line reports, whatever the parser could read it as."""
        prepared = prepare(SINE, classify("k", (above("y", 0), label)))

        again = reparse(prepared)
        assert again.column_dtypes["k"] == "text"
        assert again.profile.columns[2].top == [label]

    def test_conditions_of_a_rule_must_all_hold(self) -> None:
        where = [{"column": "Tier", "test": "eq", "value": "Hund"}, {"column": "Umsatz", "test": "gt", "value": 500}]
        prepared = prepare(SALES, classify("Gruppe", (where, "grosser Hund"), otherwise="andere"))

        assert cells(prepared, 4) == ["grosser Hund", "andere", "andere", "andere", "grosser Hund", "andere"]

    def test_number_labels_stay_categories_in_later_versions(self) -> None:
        """Labels `1` and `2` would re-parse as numbers; the column is kept text, as `set_type text` keeps it."""
        prepared = prepare(SINE, classify("class", (above("y", 0), "1"), otherwise="2"))

        assert prepared.text_columns == ["class"]
        again = reparse(prepared)
        assert again.column_dtypes["class"] == "text"
        renamed = apply_operations(
            again, OPERATIONS.validate_python([{"op": "rename", "column": "class", "name": "k"}])
        )
        assert reparse(renamed).column_dtypes["k"] == "text"

    def test_a_derived_category_feeds_an_aggregate(self) -> None:
        prepared = prepare(
            SINE,
            classify("Klasse", (above("y", 0), "Klasse 1"), otherwise="Klasse 2"),
            {"op": "aggregate", "by": ["Klasse"], "column": "y", "how": "count"},
        )

        assert rows(prepared) == ["Klasse,count", "Klasse 1,2", "Klasse 2,3"]

    def test_an_existing_name_is_refused(self) -> None:
        code, message = failure(SINE, classify("y", (above("y", 0), "a")))

        assert (code, message) == ("invalid_operation", "a column named 'y' already exists")

    def test_an_unknown_column_in_a_rule(self) -> None:
        assert failure(SINE, classify("k", (above("z", 0), "a")))[0] == "unknown_column"

    def test_a_column_without_any_label_is_refused(self) -> None:
        code, message = failure(SINE, classify("k", (above("y", 5), "a")))

        assert code == "invalid_operation"
        assert message == "no row matches a rule, so column 'k' would hold no label"

    def test_a_full_table_is_too_wide(self) -> None:
        header = ",".join(f"c{i}" for i in range(MAX_COLUMNS))
        text = f"{header}\n{','.join('1' for _ in range(MAX_COLUMNS))}\n"

        assert failure(text, classify("k", (above("c0", 0), "a")))[0] == "too_wide"

    @pytest.mark.parametrize(
        "operation",
        [
            classify("k"),
            {"op": "classify", "name": "k", "rules": [{"where": [], "label": "a"}]},
            classify("k", (above("y", 0), "")),
            classify("k", (above("y", 0), " a")),
            classify("k", (above("y", 0), "a\nb")),
            classify("k", (above("y", 0), "a\x07")),
            classify("k", (above("y", 0), "a b")),
            classify("k", (above("y", 0), "-")),
            classify("k", (above("y", 0), "NA")),
            classify("k", (above("y", 0), "a"), otherwise="null"),
            classify("k", (above("y", 0), "x" * (MAX_CELL_CHARS + 1))),
            classify("k", (above("y", 0), "a"), otherwise=""),
            classify("k ", (above("y", 0), "a")),
            classify("k", *[(above("y", 0), "a")] * (MAX_RULES + 1)),
            classify("k", (above("y", 0) * (MAX_CONDITIONS + 1), "a")),
            {"op": "classify", "name": "k", "rules": [{"where": above("y", 0), "label": "a", "else": "b"}]},
        ],
    )
    def test_malformed_classify_fails_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])


class TestSequences:
    def test_operations_apply_in_order_and_see_earlier_renames(self) -> None:
        prepared = prepare(
            SALES,
            {"op": "rename", "column": "Tier", "name": "Segment"},
            drop("Segment", "eq", "Gesamt"),
            {"op": "set_type", "column": "Anteil", "type": "number"},
            {"op": "aggregate", "by": ["Segment"], "column": "Anteil", "how": "mean"},
            {"op": "sort", "column": "Anteil", "descending": True},
        )

        assert rows(prepared) == ["Segment,Anteil", "Hund,31", "Katze,7"]
        assert prepared.changes == [
            "renamed 'Tier' to 'Segment'",
            "dropped 1 row where Segment = 'Gesamt'",
            "Anteil: 4 cells read as numbers, unit '%' removed",
            "averaged Anteil by Segment: 2 rows, 2 other columns dropped",
            "sorted by Anteil, descending",
        ]

    def test_an_old_name_is_unknown_after_a_rename(self) -> None:
        code, message = failure(SALES, {"op": "rename", "column": "Tier", "name": "Segment"}, drop("Tier", "eq", "x"))

        assert (code, message) == ("unknown_column", "there is no column 'Tier'")

    def test_no_operation(self) -> None:
        with pytest.raises(PrepareError) as caught:
            apply_operations(parse_dataset(SALES), [])

        assert caught.value.code == "invalid_operation"

    def test_too_many_operations(self) -> None:
        operations = [{"op": "sort", "column": "Umsatz"}] * (MAX_OPERATIONS + 1)

        assert failure(SALES, *operations)[0] == "invalid_operation"

    def test_the_error_carries_code_and_message(self) -> None:
        error = PrepareError("too_wide", "the result would have 60 columns")

        assert str(error) == "too_wide: the result would have 60 columns"


class TestRoundTrip:
    @pytest.mark.parametrize(
        ("text", "operations"),
        [
            (SALES, [{"op": "rename", "column": "Tier", "name": "Segment"}]),
            (SALES, [{"op": "drop_columns", "columns": ["Anteil"]}]),
            (SALES, [drop("Tier", "eq", "Gesamt")]),
            (SALES, [{"op": "set_type", "column": "Anteil", "type": "number"}]),
            (SALES, [{"op": "set_type", "column": "Datum", "type": "text"}]),
            (SALES, [{"op": "aggregate", "by": ["Datum"], "column": "Umsatz", "how": "sum", "period": "month"}]),
            (SALES, [{"op": "aggregate", "by": ["Tier"], "column": "Umsatz", "how": "count"}]),
            (SALES, [{"op": "sort", "column": "Datum", "descending": True}]),
            (WIDE, [{"op": "pivot_longer", "columns": ["Hüte", "Schuhe"]}]),
            (LONG, [{"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}]),
            ("d,v\n2024-01-05 10:30,1\n2024-01-06,2\n", [{"op": "sort", "column": "v", "descending": True}]),
            (
                "t,v\n" + "".join(f"{day:02d}.02.2024,{day}\n" for day in range(1, 11)) + "n.a.,0\n",
                [{"op": "set_type", "column": "t", "type": "datetime", "date_format": "DD.MM.YYYY"}],
            ),
            (
                "t,v\n01/02/2024,1\n03/04/2024,2\n",
                [{"op": "set_type", "column": "t", "type": "datetime", "date_format": "MM/DD/YYYY"}],
            ),
            ('n,"a,b"\n0.1,"x, y"\n1e20,"say ""hi"""\n', [{"op": "sort", "column": "n", "descending": True}]),
        ],
    )
    def test_the_result_is_already_canonical(self, text: str, operations: list[dict[str, Any]]) -> None:
        prepared = prepare(text, *operations)
        again = reparse(prepared)

        assert again.csv == prepared.csv
        assert prepared.csv.endswith("\n")
        assert not again.warnings

    def test_an_untouched_column_with_midnight_times_is_written_as_stored(self) -> None:
        """The parser writes a column with a time when any source cell had one; `T00:00:00` stays (verifiers)."""
        parsed = parse_dataset("t,v\n2024-01-15 00:00,1\n2024-01-16 00:00,2\n")
        assert parsed.csv == "t,v\n2024-01-15T00:00:00,1\n2024-01-16T00:00:00,2\n"

        prepared = apply_operations(parsed, OPERATIONS.validate_python([{"op": "rename", "column": "v", "name": "w"}]))

        assert prepared.csv == "t,w\n2024-01-15T00:00:00,1\n2024-01-16T00:00:00,2\n"
        assert reparse(prepared).profile.columns[0].min == "2024-01-15T00:00:00"

    def test_a_date_read_by_an_operation_carries_a_time_when_a_cell_had_one(self) -> None:
        text = "t,v\n15.01.2024 00:00,1\n16.01.2024,2\n"
        operation = {"op": "set_type", "column": "t", "type": "datetime", "date_format": "DD.MM.YYYY"}

        assert cells(prepare(text, operation), 0) == ["2024-01-15T00:00:00", "2024-01-16T00:00:00"]

    def test_the_original_is_untouched(self) -> None:
        parsed = parse_dataset(SALES)
        prepare_csv = parsed.csv
        apply_operations(parsed, OPERATIONS.validate_python([drop("Tier", "eq", "Gesamt")]))

        assert parsed.csv == prepare_csv


# A long table of a population by origin (generalised from the live test of 2026-10-14: "which year has the
# largest share of foreigners?" on Jahr, Staatsangehörigkeit, Bestand).
POPULATION = (
    "Year,Origin,Population\n"
    "2021,Native,6500\n"
    "2021,Foreign,2000\n"
    "2022,Native,6000\n"
    "2022,Foreign,2000\n"
    "2023,Native,6000\n"
    "2023,Foreign,1500\n"
)


def derive(name: str, how: str, *columns: str, **extra: Any) -> dict[str, Any]:
    return {"op": "derive", "name": name, "how": how, "columns": list(columns), **extra}


class TestDerive:
    def test_share_within_a_group_answers_the_largest_share_question(self) -> None:
        prepared = prepare(
            POPULATION,
            derive("Share", "share", "Population", within=["Year"], percent=True),
            drop("Origin", "eq", "Native"),
            {"op": "sort", "column": "Share", "descending": True},
        )

        assert rows(prepared) == [
            "Year,Origin,Population,Share",
            "2022,Foreign,2000,25",
            "2021,Foreign,2000,23.52941176470588",
            "2023,Foreign,1500,20",
        ]
        assert prepared.changes[0] == "added column Share: share of Population in the total of each Year, in percent"
        assert dtypes(prepared)["Share"] == "number"
        assert reparse(prepared).profile.sample[0][0] == "2022"  # the root reads the answer from the profile

    def test_share_of_the_whole_column(self) -> None:
        prepared = prepare("k,v\na,1\nb,3\n", derive("s", "share", "v"))

        assert cells(prepared, 2) == ["0.25", "0.75"]

    @pytest.mark.parametrize("within", [[], ["k"]])
    def test_a_share_divides_by_the_total_of_the_cells(self, within: list[str]) -> None:
        prepared = prepare("k,v\na,19.99\na,5.01\na,0.1\na,0.2\n", derive("s", "share", "v", within=within))

        assert cells(prepared, 2) == [repr(value / 25.3) for value in (19.99, 5.01, 0.1, 0.2)]

    def test_ratio_and_difference_keep_the_column_order(self) -> None:
        text = "k,a,b\nx,6,3\ny,1,0\nz,,2\n"
        ratio = prepare(text, derive("r", "ratio", "a", "b"))
        difference = prepare(text, derive("d", "difference", "b", "a"))

        assert cells(ratio, 3) == ["2", "", ""]
        assert ratio.changes == ["added column r: a / b, 2 cells are empty (a missing input or a division by zero)"]
        assert cells(difference, 3) == ["-3", "-1", ""]

    def test_sum_across_columns_skips_missing_cells(self) -> None:
        prepared = prepare("k,a,b,c\nx,1,2,3\ny,,2,\nz,,,\nw,1,1,1\n", derive("total", "sum", "a", "b", "c"))

        assert cells(prepared, 4) == ["6", "2", "", "3"]

    def test_whole_numbers_stay_exact_past_float_precision(self) -> None:
        """A float64 holds integers only up to 2**53: `9007199254740993 - 9007199254740992` is 1, not 0."""
        prepared = prepare("k,a,b\nx,9007199254740993,9007199254740992\n", derive("d", "difference", "a", "b"))
        summed = prepare("k,a,b\nx,1,1\ny,1.5,2\n", derive("s", "sum", "a", "b"))

        assert cells(prepared, 3) == ["1"]
        assert dtypes(prepared)["d"] == "integer"
        assert cells(summed, 3) == ["2", "3.5"]  # a float column sums as floats, a whole one written without `.0`

    def test_percent_change_within_groups_in_the_order_given(self) -> None:
        shuffled = "Year,Origin,Population\n2022,Foreign,2000\n2021,Foreign,1600\n2021,Native,6400\n2022,Native,6000\n"
        prepared = prepare(shuffled, derive("Growth", "percent_change", "Population", within=["Origin"], order="Year"))

        assert cells(prepared, 3) == ["25", "", "", "-6.25"]
        assert "the first row of each group" in prepared.changes[0]

    def test_running_total_and_index_within_groups_in_the_order_given(self) -> None:
        shuffled = "Year,Origin,Population\n2022,Foreign,2000\n2021,Foreign,1600\n2021,Native,6400\n2022,Native,6000\n"
        running = prepare(shuffled, derive("Total", "cumsum", "Population", within=["Origin"], order="Year"))
        index = prepare(shuffled, derive("Index", "index", "Population", within=["Origin"], order="Year"))

        assert cells(running, 3) == ["3600", "1600", "6400", "12400"]  # whole numbers add up as whole numbers
        assert running.changes == [
            "added column Total: running total of Population in the order of Year within each Origin"
        ]
        assert cells(index, 3) == ["125", "100", "100", "93.75"]

    def test_index_without_groups_starts_at_the_first_value_that_is_there(self) -> None:
        prepared = prepare("Year,Sales\n2021,\n2022,50\n2023,75\n", derive("Index", "index", "Sales", order="Year"))

        assert cells(prepared, 2) == ["", "100", "150"]

    def test_a_text_order_column_is_refused(self) -> None:
        """Month names sort alphabetically (April before Januar): the result would be silently wrong."""
        months = "Monat,Umsatz\nJanuar,10\nFebruar,12\nMärz,15\nApril,18\n"
        for how in ("percent_change", "cumsum", "index"):
            code, message = failure(months, derive("x", how, "Umsatz", order="Monat"))
            assert code == "type_mismatch" and "set_type" in message, how

    def test_rows_without_an_order_value_stay_empty(self) -> None:
        """Two missing order values are no repeated value: those rows have no place in the order."""
        text = "Year,Sales\n2021,10\n,99\n2022,20\n,98\n"
        prepared = prepare(text, derive("Growth", "percent_change", "Sales", order="Year"))

        assert cells(prepared, 2) == ["", "", "100", ""]
        assert "a row without a Year" in prepared.changes[0]

    def test_percent_change_with_repeated_order_values_is_refused(self) -> None:
        code, message = failure(POPULATION, derive("g", "percent_change", "Population", order="Year"))

        assert code == "invalid_operation" and "aggregate first" in message

    @pytest.mark.parametrize(
        ("operation", "code"),
        [
            (derive("r", "ratio", "Population"), "invalid_operation"),
            (derive("r", "ratio", "Population", "Population"), "invalid_operation"),
            (derive("s", "sum", "Population"), "invalid_operation"),
            (derive("s", "share", "Population", "Year"), "invalid_operation"),
            (derive("d", "difference", "Population", "Year", within=["Origin"]), "invalid_operation"),
            (derive("d", "difference", "Population", "Year", percent=True), "invalid_operation"),
            (
                derive("g", "percent_change", "Population", order="Year", within=["Origin"], percent=True),
                "invalid_operation",
            ),
            (derive("s", "share", "Population", order="Year"), "invalid_operation"),
            (derive("g", "percent_change", "Population"), "invalid_operation"),
            (derive("s", "share", "Population", within=["Population"]), "invalid_operation"),
            (derive("Year", "share", "Population"), "invalid_operation"),
            (derive("s", "share", "Origin"), "type_mismatch"),
            (derive("s", "share", "Nope"), "unknown_column"),
            (derive("s", "share", "Population", within=["Nope"]), "unknown_column"),
        ],
    )
    def test_refusals(self, operation: dict[str, Any], code: str) -> None:
        assert failure(POPULATION, operation)[0] == code

    def test_a_column_without_any_value_is_refused(self) -> None:
        assert failure("k,a,b\nx,1,0\ny,2,0\n", derive("r", "ratio", "a", "b"))[0] == "invalid_operation"

    def test_a_total_that_overflows_gives_no_share(self) -> None:
        """Two `1e308` values sum to infinity; dividing by it would claim shares of 0 instead of 50 %."""
        assert failure("k,v\na,1e308\nb,1e308\n", derive("s", "share", "v"))[0] == "invalid_operation"
        prepared = prepare("g,v\nx,1e308\nx,1e308\ny,1\ny,3\n", derive("s", "share", "v", within=["g"]))
        assert cells(prepared, 2) == ["", "", "0.25", "0.75"]

    def test_free_expressions_do_not_validate(self) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([derive("r", "a / b", "a", "b")])
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([{**derive("r", "ratio", "a", "b"), "expression": "a / b"}])

    def test_the_new_column_is_numbers_after_the_reparse(self) -> None:
        prepared = prepare(POPULATION, derive("Share", "share", "Population", within=["Year"]))

        assert dtypes(prepared) == {"Year": "integer", "Origin": "text", "Population": "integer", "Share": "number"}


# A monthly station series aligned with spaces, as weather services publish it: year and month, no date
# column (live test of 2026-10-15, generalised; a missing month and a missing value included).
STATION = (
    "Year  Month  Temperature  Precipitation\n"
    "2023     11          4.1           62.0\n"
    "2023     12          1.2           80.3\n"
    "2024      1         -0.7           55.1\n"
    "2024      2          3.4           41.9\n"
    "2024                 5.0           38.2\n"
)


def make_date(name: str, **parts: str) -> dict[str, Any]:
    return {"op": "make_date", "name": name, **parts}


class TestMakeDate:
    def test_year_and_month_give_the_first_day_of_each_month(self) -> None:
        prepared = prepare(STATION, make_date("Datum", year="Year", month="Month"))

        assert cells(prepared, 4) == ["2023-11-01", "2023-12-01", "2024-01-01", "2024-02-01", ""]
        assert prepared.changes == [
            "added column Datum: dates from Year and Month (the first day of each month), "
            "1 cell is empty (a missing part)"
        ]
        assert dtypes(prepared)["Datum"] == "datetime"
        assert list(dtypes(prepared))[:4] == ["Year", "Month", "Temperature", "Precipitation"]

    def test_year_month_and_day(self) -> None:
        prepared = prepare(
            "J;M;T;Wert\n2024;2;29;1\n2024;3;1;2\n2023;12;31;3\n", make_date("d", year="J", month="M", day="T")
        )

        assert cells(prepared, 4) == ["2024-02-29", "2024-03-01", "2023-12-31"]
        assert prepared.changes == ["added column d: dates from J, M and T"]

    def test_year_and_quarter_give_the_first_day_of_each_quarter(self) -> None:
        prepared = prepare(
            "Jahr,Quartal,Umsatz\n2024,1,10\n2024,2,12\n2024,3,9\n2024,4,15\n",
            make_date("Beginn", year="Jahr", quarter="Quartal"),
        )

        assert cells(prepared, 3) == ["2024-01-01", "2024-04-01", "2024-07-01", "2024-10-01"]
        assert "(the first day of each quarter)" in prepared.changes[0]

    def test_year_and_week_give_the_monday_of_the_iso_week(self) -> None:
        prepared = prepare("year,week,cases\n2024,1,5\n2020,53,7\n", make_date("date", year="year", week="week"))

        assert cells(prepared, 3) == ["2024-01-01", "2020-12-28"]

    def test_a_year_alone_gives_the_first_of_january(self) -> None:
        prepared = prepare("year,value\n2020,1\n2021,2\n", make_date("date", year="year"))

        assert cells(prepared, 2) == ["2020-01-01", "2021-01-01"]
        assert prepared.changes == ["added column date: dates from year (1 January of each year)"]

    def test_a_month_out_of_range_is_refused(self) -> None:
        code, message = failure(
            "Year,Month,v\n2024,1,1\n2024,13,2\n2024,0,3\n", make_date("d", year="Year", month="Month")
        )

        assert code == "invalid_operation"
        assert message == "column 'Month' holds 2 values outside 1 to 12, so it is not a month"

    def test_a_two_digit_year_is_refused(self) -> None:
        code, message = failure("Jahr,Monat,v\n24,1,1\n24,2,2\n", make_date("d", year="Jahr", month="Monat"))

        assert code == "invalid_operation"
        assert "a year of four digits" in message

    def test_a_row_that_is_no_calendar_date_is_refused_never_moved(self) -> None:
        code, message = failure(
            "y,m,d,v\n2024,4,31,1\n2023,2,29,2\n2024,5,1,3\n", make_date("date", year="y", month="m", day="d")
        )

        assert code == "invalid_operation"
        assert message.startswith("2 rows of y, m and d are no calendar date")
        assert failure("y,w,v\n2021,53,1\n", make_date("date", year="y", week="w"))[0] == "invalid_operation"

    @pytest.mark.parametrize(
        ("parts", "expected"),
        [
            ({"year": "y", "day": "d"}, "make_date with a day needs a month column too"),
            ({"year": "y", "month": "m", "quarter": "q"}, "make_date with a quarter takes only a year besides it"),
            ({"year": "y", "quarter": "q", "week": "w"}, "make_date with a quarter takes only a year besides it"),
            ({"year": "y", "month": "m", "week": "w"}, "make_date with a week takes only a year besides it"),
            ({"year": "y", "month": "y"}, "make_date needs a different column for each part"),
        ],
    )
    def test_invalid_combinations_are_refused(self, parts: dict[str, str], expected: str) -> None:
        assert failure("y,m,d,q,w\n2024,1,1,1,1\n", make_date("date", **parts)) == ("invalid_operation", expected)

    def test_a_text_or_fractional_part_is_a_type_mismatch(self) -> None:
        code, message = failure("Year,Q,v\n2024,Q1,1\n2024,Q2,2\n", make_date("d", year="Year", quarter="Q"))
        assert code == "type_mismatch"
        assert "set_type it to number first" in message
        assert failure("y,m\n2024,1.5\n2024,2\n", make_date("d", year="y", month="m"))[0] == "type_mismatch"

    @pytest.mark.parametrize(
        ("names", "language"),
        [
            (["January", "Feb", "Mar.", "apr"], "en"),
            (["Jänner", "Februar", "Mrz", "April"], "de"),
            (["janvier", "févr.", "mars", "Avril"], "fr"),
            (["enero", "Feb", "marzo", "abr"], "es"),
            (["gennaio", "febbraio", "mar", "aprile"], "it"),
            (["janeiro", "fev", "março", "abril"], "pt"),
            (["januari", "februari", "maart", "apr"], "nl"),
            (["styczeń", "lutego", "marzec", "kwi"], "pl"),
            (["一月", "2月", "三月", "4 月"], "zh"),
            (["Tháng 1", "tháng 2", "THÁNG 3", "tháng 04"], "vi"),
            (["Январь", "февраля", "мар", "Апр"], "ru"),
        ],
    )
    def test_month_names_in_every_refusal_language(self, names: list[str], language: str) -> None:
        text = "Jahr;Monat;Wert\n" + "".join(f"2024;{name};{n}\n" for n, name in enumerate(names, 1))
        prepared = prepare(text, make_date("Datum", year="Jahr", month="Monat"))

        assert cells(prepared, 3) == ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"], language

    def test_may_without_diacritics_and_the_whole_year(self) -> None:
        assert [month_number(name) for name in ("Май", "мая", "MAI", "maj", "mei", "Dez", "dic", "out", "lis")] == [
            5,
            5,
            5,
            5,
            5,
            12,
            12,
            10,
            11,
        ]

    def test_an_unknown_month_name_is_refused(self) -> None:
        code, message = failure(
            "Year;Month;v\n2024;Jan;1\n2024;Foo;2\n2024;13;3\n", make_date("d", year="Year", month="Month")
        )

        assert code == "type_mismatch"
        assert message == "column 'Month' holds 2 values that are no month name or number from 1 to 12"

    def test_no_name_maps_to_two_months(self) -> None:
        seen: dict[str, int] = {}
        for number, words in enumerate(months_module._MONTH_WORDS, 1):
            for word in words:
                key = months_module.fold(word)
                assert seen.setdefault(key, number) == number, word

    def test_week_one_may_start_in_december_and_the_change_line_says_so(self) -> None:
        prepared = prepare("year,week,v\n2025,1,1\n2025,2,2\n", make_date("date", year="year", week="week"))

        assert cells(prepared, 3) == ["2024-12-30", "2025-01-06"]
        assert "week 1 can start in late December of the year before" in prepared.changes[0]

    def test_a_year_far_from_today_is_a_date_not_a_crash(self) -> None:
        prepared = prepare("y,m,v\n1500,1,1\n9000,12,2\n", make_date("date", year="y", month="m"))

        assert cells(prepared, 3) == ["1500-01-01", "9000-12-01"]

    def test_unknown_columns_and_taken_names(self) -> None:
        assert failure(STATION, make_date("d", year="Jahr"))[0] == "unknown_column"
        assert failure(STATION, make_date("Month", year="Year"))[0] == "invalid_operation"

    def test_a_date_with_no_row_complete_is_refused(self) -> None:
        assert failure("y,m,v\n2024,,1\n,3,2\n", make_date("d", year="y", month="m"))[0] == "invalid_operation"

    def test_free_text_does_not_validate(self) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([{**make_date("d", year="y"), "format": "%Y-%m"}])


class TestSetTypeDateFormats:
    @pytest.mark.parametrize(
        ("csv_text", "date_format", "expected"),
        [
            ("d,v\n20240115,1\n20240216,2\n", "YYYYMMDD", ["2024-01-15", "2024-02-16"]),
            ("d,v\n2024-01,1\n2024-02,2\n", "YYYY-MM", ["2024-01-01", "2024-02-01"]),
            ("d;v\n03/2024;1\n04/2024;2\n", "MM/YYYY", ["2024-03-01", "2024-04-01"]),
            ("d;v\n03.2024;1\n11.2024;2\n", "MM.YYYY", ["2024-03-01", "2024-11-01"]),
            # Read as numbers by the parser (3.202, 11.2): four decimals give the trailing zeros back.
            ("d,v\n03.2020,1\n11.2000,2\n12.2010,3\n", "MM.YYYY", ["2020-03-01", "2000-11-01", "2010-12-01"]),
            ("d,v\n01.2020,1\n02.2020,2\n10.2020,3\n", "MM.YYYY", ["2020-01-01", "2020-02-01", "2020-10-01"]),
            ("d,v\n1500,1\n1600,2\n1700,3\n", "YYYY", ["1500-01-01", "1600-01-01", "1700-01-01"]),
            ("d,v\n202401,1\n202412,2\n", "YYYYMM", ["2024-01-01", "2024-12-01"]),
            ("d,v\n13/01/2024,1\n02/03/2024,2\n", "DD/MM/YYYY", ["2024-01-13", "2024-03-02"]),
        ],
    )
    def test_a_format_reads_the_column_as_dates(self, csv_text: str, date_format: str, expected: list[str]) -> None:
        prepared = prepare(csv_text, {"op": "set_type", "column": "d", "type": "datetime", "date_format": date_format})

        assert cells(prepared, 0) == expected
        assert dtypes(prepared)["d"] == "datetime"

    def test_mm_yyyy_never_rounds_a_malformed_number_into_a_date(self) -> None:
        """`03.20249` is no MM.YYYY cell: four decimals would make it March 2025, so it stays as it is and fails."""
        code, _ = failure(
            "d,v\n03.20249,1\n11.20001,2\n",
            {"op": "set_type", "column": "d", "type": "datetime", "date_format": "MM.YYYY"},
        )

        assert code == "type_mismatch"

    @pytest.mark.parametrize("values", ["2.2\n2.3\n2.1", "3.5\n3.6", "1.25\n1.5"])
    def test_mm_yyyy_refuses_ordinary_decimals(self, values: str) -> None:
        """`2.2` would be February 2000 and `3.5` March 5000: a column of decimals is no month.year column."""
        text = "d\n" + values + "\n"
        code, message = failure(text, {"op": "set_type", "column": "d", "type": "datetime", "date_format": "MM.YYYY"})

        assert code == "type_mismatch"
        assert "month.year" in message

    @pytest.mark.parametrize(
        ("values", "date_format"),
        [
            ("2024115\n20240115\n2024011\n", "YYYYMMDD"),
            ("20241\n202401\n20242\n", "YYYYMM"),
            ("202411\n202401\n202412\n", "YYYYMMDD"),
            ("24\n2024\n25\n", "YYYY"),
        ],
    )
    def test_compact_formats_take_exactly_their_digits(self, values: str, date_format: str) -> None:
        text = "d,v\n" + "".join(f"{value},{n}\n" for n, value in enumerate(values.split()))
        operation = {"op": "set_type", "column": "d", "type": "datetime", "date_format": date_format}

        assert failure(text, operation)[0] == "type_mismatch"

    def test_yyyy_says_it_read_years(self) -> None:
        prepared = prepare(
            "price,n\n1450,1\n1890,2\n2100,3\n",
            {"op": "set_type", "column": "price", "type": "datetime", "date_format": "YYYY"},
        )

        assert prepared.changes == ["price: 3 cells read as years (YYYY, each as 1 January)"]


def set_dates(date_format: str | None = None, column: str = "d") -> dict[str, Any]:
    operation: dict[str, Any] = {"op": "set_type", "column": column, "type": "datetime"}
    if date_format:
        operation["date_format"] = date_format
    return operation


class TestDateOrder:
    """The order of day and month stays open while every day is at most 12 and can be switched both ways."""

    def test_switching_back_and_forth_across_versions(self) -> None:
        """The pasted slash dates are read day first by guess; the note travels with every version."""
        pasted = parse_dataset("d,v\n05/03/2024,1\n06/04/2024,2\n")
        assert any(AMBIGUOUS_DATE_ORDER in warning for warning in pasted.warnings)

        month_first = apply_operations(pasted, OPERATIONS.validate_python([set_dates("MM/DD/YYYY")]))
        assert cells(month_first, 0) == ["2024-05-03", "2024-06-04"]
        assert month_first.date_notes == [f"column 'd': {AMBIGUOUS_MONTH_FIRST}"]
        second = with_date_notes(reparse(month_first), month_first)

        day_first = apply_operations(second, OPERATIONS.validate_python([set_dates("DD/MM/YYYY")]))
        assert cells(day_first, 0) == ["2024-03-05", "2024-04-06"]
        assert day_first.changes == ["d: 2 cells re-read as dates (DD/MM/YYYY, day and month swapped)"]
        assert day_first.date_notes == [f"column 'd': {AMBIGUOUS_DATE_ORDER}"]

        third = with_date_notes(reparse(day_first), day_first)
        again = apply_operations(third, OPERATIONS.validate_python([set_dates("DD.MM.YYYY")]))
        assert again.changes == ["d: already dates, nothing changed"]

    def test_an_unrelated_change_keeps_the_order_open(self) -> None:
        pasted = parse_dataset("d,v\n05/03/2024,1\n06/04/2024,2\n")
        renamed = apply_operations(pasted, OPERATIONS.validate_python([{"op": "rename", "column": "v", "name": "w"}]))
        later = with_date_notes(reparse(renamed), renamed)

        swapped = apply_operations(later, OPERATIONS.validate_python([set_dates("MM/DD/YYYY")]))
        assert cells(swapped, 0) == ["2024-05-03", "2024-06-04"]

    def test_a_set_type_read_with_days_up_to_12_stays_open(self) -> None:
        """A text column the parser left text (one stray cell), read day first by `set_type`, can still swap."""
        text = "d,v\n05/03/2024,1\n06/04/2024,2\nunknown,3\n07/02/2024,4\n08/01/2024,5\n09/02/2024,6\n10/03/2024,7\n"
        text += "11/04/2024,8\n12/05/2024,9\n01/06/2024,10\n02/07/2024,11\n"
        first = prepare(text, set_dates())
        assert first.date_notes == [f"column 'd': {AMBIGUOUS_DATE_ORDER}"]

    def test_iso_or_a_day_over_12_settles_the_order(self) -> None:
        assert prepare("d,v\n2024-01-05,1\n2024-02-06,2\n", set_dates("MM/DD/YYYY")).changes == [
            "d: already dates, nothing changed"
        ]
        assert prepare("d,v\n13/03/2024,1\n06/04/2024,2\n", set_dates("MM/DD/YYYY")).date_notes == []


class TestOutOfBounds:
    def test_an_operation_that_overflows_pandas_dates_is_a_refusal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def explode(*_: Any) -> Any:
            raise pd.errors.OutOfBoundsDatetime("out of bounds")

        monkeypatch.setattr(prepare_module, "_sort", explode)
        code, message = failure("a,b\n1,2\n", {"op": "sort", "column": "a"})

        assert (code, message) == ("invalid_operation", "a date would lie outside the years the data can hold")


class TestNaCategory:
    def test_a_na_category_survives_every_operation_and_the_reparse(self) -> None:
        """`NA` (North America) from a JSON object's keys stays a category through `_read`, a sort and the re-parse."""
        prepared = prepare('{"NA": 3, "EU": 4, "AS": 1}', {"op": "sort", "column": "value"})

        assert rows(prepared) == ["category,value", "AS,1", "NA,3", "EU,4"]
        assert reparse(prepared).profile.columns[0].missing == 0
        kept = prepare('{"NA": 3, "EU": 4, "AS": 1}', drop("category", "eq", "NA"))
        assert rows(kept) == ["category,value", "EU,4", "AS,1"]


def from_text(text: str, column: str, *operations: dict[str, Any]) -> Prepared:
    """`operations` on a dataset whose `column` is kept text, as `set_type text` leaves it."""
    parsed = parse_dataset(text, text_columns=[column])
    return apply_operations(parsed, OPERATIONS.validate_python(list(operations)))


class TestFidelity:
    """Owner rule of 2026-10-15: an operation keeps every digit and every moment, or its change line counts the loss."""

    def test_numbers_pass_untouched_operations_with_every_digit(self) -> None:
        generator = random.Random(20261015)
        values = [generator.uniform(-1, 1) * 10.0 ** generator.randint(-300, 300) for _ in range(500)]
        whole = [2**53 + position for position in range(len(values))]
        text = "k,v,n\n" + "".join(f"{p % 3},{v!r},{n}\n" for p, (v, n) in enumerate(zip(values, whole, strict=True)))
        prepared = prepare(text, {"op": "sort", "column": "k", "descending": True}, {"op": "sort", "column": "k"})
        again = reparse(prepared)
        frame = pd.read_csv(io.StringIO(again.csv), dtype={"n": "Int64"})

        # The shortest round-trip text, a whole number below 2**53 without `.0` (owner decision of 2026-10-15).
        canonical = [
            repr(value)[:-2] if repr(value).endswith(".0") and abs(value) < 2**53 else repr(value) for value in values
        ]
        assert sorted(cells(prepared, 1)) == sorted(canonical)
        assert sorted(frame["v"].tolist()) == sorted(values) and sorted(frame["n"].tolist()) == whole
        assert again.warnings == []

    def test_set_type_number_reads_whole_numbers_exactly(self) -> None:
        prepared = from_text("k,a\nx,9007199254740993\ny,-9223372036854775808\n", "a", set_number("a"))

        assert cells(prepared, 1) == ["9007199254740993", "-9223372036854775808"]
        assert dtypes(prepared)["a"] == "integer" and prepared.changes == ["a: 2 cells read as numbers"]

    def test_set_type_number_counts_the_cells_it_rounds(self) -> None:
        prepared = from_text("k,a\nx,0.1234567890123456789\ny,1.50\nz,123456789012345678901234\n", "a", set_number("a"))

        assert cells(prepared, 1) == ["0.12345678901234568", "1.5", repr(123456789012345678901234.0)]
        assert prepared.changes == [
            "a: 3 cells read as numbers, 2 values with more significant digits than a number holds (15 to 17) "
            "are stored rounded to the nearest number"
        ]

    def test_an_integer_sum_never_wraps_around(self) -> None:
        big = 2**63 - 1000
        prepared = prepare(f"g,a\nx,{big}\nx,{big}\ny,{2**53 + 2}\ny,1\n", aggregate_sum("a"))

        # Once one total leaves int64 the column is float64, and 2**53 + 3 is rounded with it: both counted.
        assert cells(prepared, 1) == [repr(float(2 * big)), repr(float(2**53 + 3))]
        assert prepared.changes == [f"summed a by g: 2 rows, {prepare_module.whole_rounded(2)}"]
        assert prepare_module.whole_rounded(2).startswith("2 whole numbers past 2^53 are stored as decimal numbers")
        exact = prepare(f"g,a\nx,{2**53 + 1}\nx,1\n,5\n,\n", aggregate_sum("a"))
        assert rows(exact) == ["g,a", f"x,{2**53 + 2}", ",5"] and exact.changes == ["summed a by g: 2 rows"]

    def test_a_running_total_and_a_row_sum_of_whole_numbers_stay_exact(self) -> None:
        text = f"o,a,b\n2,1,{2**53}\n1,{2**53 + 1},1\n3,,2\n"
        running = prepare(text, derive("t", "cumsum", "a", order="o"))
        summed = prepare(text, derive("s", "sum", "a", "b"))
        over = prepare(f"o,a\n1,{2**63 - 1}\n2,1\n", derive("t", "cumsum", "a", order="o"))

        assert cells(running, 3) == [str(2**53 + 2), str(2**53 + 1), ""]
        assert cells(summed, 3) == [str(2**53 + 1), str(2**53 + 2), "2"]
        assert cells(over, 2) == [repr(float(2**63 - 1)), repr(float(2**63))]
        # 2**63 is a float exactly but written `9.223372036854776e+18`: both values past 2**53 are counted.
        assert over.changes[0].endswith(f", {prepare_module.whole_rounded(2)}")

    def test_a_result_that_is_exact_as_a_float_is_still_announced(self) -> None:
        """2**62 + 2**62 = 2**63 leaves int64 although a float holds it exactly (review of #12196)."""
        prepared = prepare(f"g,a\nx,{2**62}\nx,{2**62}\n", aggregate_sum("a"))

        assert cells(prepared, 1) == ["9.223372036854776e+18"]
        assert prepared.changes == [f"summed a by g: 1 row, {prepare_module.whole_rounded(1)}"]

    def test_an_exact_running_total_groups_keys_as_pandas_does(self) -> None:
        """`-0.0` and `0.0` are one group, as in pandas' own groupby (review of #12196)."""
        prepared = prepare(
            "g,o,a\n-0.0,1,10\n0.0,2,20\n-0.0,3,30\n,4,1\n,5,2\n", derive("t", "cumsum", "a", within=["g"], order="o")
        )

        assert cells(prepared, 3) == ["10", "30", "60", "1", "3"]

    def test_the_rounding_count_survives_the_line_cap_with_long_names(self) -> None:
        """A change line is clipped to `MAX_NOTE_CHARS`; the count of rounded values is never the part cut."""
        names = [f"{letter * 29}x" for letter in "abcdefghij"]
        header = ",".join(names)
        row = ",".join(str(2**63 - 1) for _ in names)
        summed = prepare(f"{header}\n{row}\n{row}\n", derive("s", "sum", *names))
        order = "o" * 60
        running = prepare(
            f"{order},{'v' * 60}\n1,{2**63 - 1}\n2,{2**63 - 1}\n", derive("t" * 60, "cumsum", "v" * 60, order=order)
        )

        for prepared in (summed, running):
            (line,) = prepared.changes
            assert len(line) <= MAX_NOTE_CHARS
            assert line.endswith("(15 to 17 significant digits; a digit past them is rounded)")
            assert "…" in line or prepared is running

    def test_derived_ratios_and_percents_keep_full_precision(self) -> None:
        prepared = prepare("a,b\n1,3\n2,7\n", derive("r", "ratio", "a", "b", percent=True))

        assert cells(prepared, 2) == [repr(1 / 3 * 100), repr(2 / 7 * 100)]

    def test_pivoting_whole_numbers_beside_decimals_counts_the_rounded_ones(self) -> None:
        prepared = prepare(f"g,a,b\nx,{2**53 + 1},1.5\ny,7,2.5\n", {"op": "pivot_longer", "columns": ["a", "b"]})

        assert cells(prepared, 2) == [repr(float(2**53)), "7", "1.5", "2.5"]  # `7` as written, `.0` past 2**53
        assert prepared.changes == [
            "pivoted 2 columns into series/value: 4 rows, 1 whole number past 2^53 beside the decimals of value is "
            "read as decimal numbers (15 to 17 significant digits; a digit past them is rounded)"
        ]

    def test_float_results_count_their_whole_number_inputs_past_2_53(self) -> None:
        """A ratio or a mean reads Int64 inputs as float64; past 2**53 that is counted (review of #12196)."""
        ratio = prepare(f"a,b\n{2**53 + 1},2.0\n4,2.0\n", derive("r", "ratio", "a", "b"))
        mean = prepare(f"g,a\nx,{2**53 + 1}\nx,1\n", {"op": "aggregate", "by": ["g"], "column": "a", "how": "mean"})

        assert ratio.changes[0].endswith(f", {prepare_module.cast_note(1, 'in the inputs')}")
        assert mean.changes == [f"averaged a by g: 1 row, {prepare_module.cast_note(1, 'in a')}"]

    def test_set_type_datetime_keeps_fractions_of_a_second_and_offsets(self) -> None:
        fractions = prepare("label,t\nx,2024-03-05 12:00:00.25\ny,2024-03-05 12:00:01.5\n", set_dates(column="t"))
        offsets = prepare("k,t\nx,2024-03-05T12:00:00+02:00\ny,2024-03-06T13:00:00+02:00\n", set_dates(column="t"))

        assert cells(fractions, 1) == ["2024-03-05T12:00:00.250000", "2024-03-05T12:00:01.500000"]
        assert cells(offsets, 1) == ["2024-03-05T12:00:00+02:00", "2024-03-06T13:00:00+02:00"]

    def test_year_first_dates_are_never_read_day_first(self) -> None:
        """`2024-06-01T13:00:00Z` is 1 June: pandas with `dayfirst` read it as 6 January (review of 2026-10-15)."""
        prepared = prepare("k,t\nx,2024-06-01T13:00:00Z\ny,2024-01-31T08:00:00Z\n", set_dates(column="t"))

        assert cells(prepared, 1) == ["2024-06-01T13:00:00+00:00", "2024-01-31T08:00:00+00:00"]

    def test_one_cell_of_another_shape_never_turns_year_first_dates_around(self) -> None:
        """The order is chosen per cell: a tolerated unreadable cell kept `dayfirst` for the column (review of #12196)."""
        dates = [f"2024-06-0{n}T13:00:00Z" for n in range(1, 10)]
        column = [*dates[:4], "soon", *dates[4:]]  # the text cell keeps the column text at the paste
        prepared = prepare(
            "label,t\n" + "".join(f"x{n},{cell}\n" for n, cell in enumerate(column)), set_dates(column="t")
        )

        expected = [f"2024-06-0{n}T13:00:00+00:00" for n in range(1, 10)]
        assert cells(prepared, 1) == [*expected[:4], "", *expected[4:]]
        assert prepared.changes == [
            "t: 9 cells read as dates (format inferred, year first), 1 cell could not be read and is now missing"
        ]

    def test_conditions_on_a_column_with_an_offset_compare_moments(self) -> None:
        """A `Z` or offset column took a naive value into a `TypeError` that crashed the tool (review of #12196)."""
        text = "label,t\na,2023-12-31T23:30:00Z\nb,2024-01-01T00:00:00Z\nc,2024-01-01T00:30:00Z\n"
        utc = prepare(text, drop("t", "lt", "2024-01-01T00:00:01+00:00"))
        berlin = prepare(text, drop("t", "lt", "2024-01-01T01:00:01+01:00"))  # the same moment
        code, message = failure(text, drop("t", "lt", "2024-01-01T00:00:01"))

        assert rows(utc) == rows(berlin) == ["label,t", "c,2024-01-01T00:30:00+00:00"]
        assert code == "invalid_operation" and "give the value with one" in message
        classified = prepare(
            text, classify("late", ([{"column": "t", "test": "gt", "value": "2024-01-01T00:00:00Z"}], "y"))
        )
        assert cells(classified, 2) == ["", "", "y"]

    def test_conditions_on_whole_numbers_compare_exactly(self) -> None:
        """`9007199254740992` and `9007199254740993` are one float64 but two ids (review of #12196)."""
        text = f"id,v\n{2**53},1\n{2**53 + 1},2\n{2**63 - 1},3\n"

        assert rows(prepare(text, drop("id", "eq", str(2**53)))) == ["id,v", f"{2**53 + 1},2", f"{2**63 - 1},3"]
        assert rows(prepare(text, drop("id", "ne", str(2**53 + 1)))) == ["id,v", f"{2**53 + 1},2"]
        assert rows(prepare(text, drop("id", "gt", f"{2**53}.5"))) == ["id,v", f"{2**53},1"]
        assert rows(prepare(text, drop("id", "lt", f"{2**53}.5"))) == ["id,v", f"{2**53 + 1},2", f"{2**63 - 1},3"]
        unchanged = ["id,v", f"{2**53},1", f"{2**53 + 1},2", f"{2**63 - 1},3"]
        assert rows(prepare(text, drop("id", "eq", f"{2**53}.5"))) == unchanged  # a fraction equals no whole number
        assert rows(prepare(text, drop("id", "gt", str(2**64)))) == unchanged  # past int64: above every cell
        assert failure(text, drop("id", "lt", str(2**64)))[0] == "empty_result"

    def test_at_least_and_at_most_on_whole_numbers_compare_exactly(self) -> None:
        text = f"id,v\n{2**53},1\n{2**53 + 1},2\n{2**63 - 1},3\n"
        unchanged = ["id,v", f"{2**53},1", f"{2**53 + 1},2", f"{2**63 - 1},3"]

        assert rows(prepare(text, drop("id", "ge", str(2**53 + 1)))) == ["id,v", f"{2**53},1"]
        assert rows(prepare(text, drop("id", "le", str(2**53)))) == ["id,v", f"{2**53 + 1},2", f"{2**63 - 1},3"]
        # A fraction equals no whole number, so "at least 2**53 + 0.5" starts at the next one.
        assert rows(prepare(text, drop("id", "ge", f"{2**53}.5"))) == ["id,v", f"{2**53},1"]
        assert rows(prepare(text, drop("id", "le", f"{2**53}.5"))) == ["id,v", f"{2**53 + 1},2", f"{2**63 - 1},3"]
        # Past int64 on either side: at least a value above every cell holds for none, at most it for all.
        assert rows(prepare(text, drop("id", "ge", str(2**64)))) == unchanged
        assert failure(text, drop("id", "le", str(2**64)))[0] == "empty_result"
        assert failure(text, drop("id", "ge", str(-(2**64))))[0] == "empty_result"
        assert rows(prepare(text, drop("id", "le", str(-(2**64))))) == unchanged
        # A fraction past int64, and one whose next whole number is: compared, never overflowed.
        for value in (f"{2**64}.5", f"{2**63 - 1}.5"):
            assert rows(prepare(text, drop("id", "ge", value))) == unchanged
            assert rows(prepare(text, drop("id", "gt", value))) == unchanged
            assert failure(text, drop("id", "le", value))[0] == "empty_result"
            assert failure(text, drop("id", "lt", value))[0] == "empty_result"

    def test_an_exponent_past_the_decimal_range_is_read_as_its_float(self) -> None:
        prepared = from_text(
            "k,a\nx,1e-9999999999999999999\ny,0e999999999999999999999999\nz,2.5\n", "a", set_number("a")
        )

        assert cells(prepared, 1) == ["0", "0", "2.5"]
        assert prepared.changes[0].startswith("a: 3 cells read as numbers, 1 value with more significant digits")

    def test_different_utc_offsets_are_converted_to_utc_and_named(self) -> None:
        """Owner decision of 2026-10-15, as the parser writes such a column: UTC, with the offsets in the change line."""
        text = "label,t\nx,05.01.2024 12:00 +01:00\ny,05.07.2024 12:00 +02:00\nz,2024-08-01 09:30 +02:00\n"
        prepared = prepare(text, set_dates(column="t"))

        assert cells(prepared, 1) == [
            "2024-01-05T11:00:00+00:00",
            "2024-07-05T10:00:00+00:00",
            "2024-08-01T07:30:00+00:00",
        ]
        assert prepared.changes == [
            "t: 3 cells read as dates (format inferred, year first where a cell starts with one, else day before "
            "month), times with the UTC offsets +01:00, "
            "+02:00 converted to UTC (+00:00); the instants are the same"
        ]

    def test_times_with_and_without_an_offset_are_refused(self) -> None:
        text = "label,t\nx,05.01.2024 12:00 +01:00\ny,05.07.2024 12:00\nz,2024-08-01 09:30 +02:00\n"
        code, message = failure(text, set_dates(column="t"))

        assert code == "type_mismatch" and "no time is given a zone by guess" in message


def set_number(column: str) -> dict[str, Any]:
    return {"op": "set_type", "column": column, "type": "number"}


def aggregate_sum(column: str) -> dict[str, Any]:
    return {"op": "aggregate", "by": ["g"], "column": column, "how": "sum"}


# Live test round 5 of 2026-10-15, generalised: readings every 13 minutes of several sensors ("Tagesmittel pro
# Sensor" was refused, the periods stopped at month). Synthetic values.
READINGS = (
    "timestamp,sensor,temp_c\n"
    "2026-01-04 23:50,S1,10.0\n"  # a Sunday
    "2026-01-05 00:03,S1,11.5\n"  # Monday: a new ISO week
    "2026-01-05 00:16,S2,20.0\n"
    "2026-01-05 01:02,S1,12.5\n"
    "2026-01-06 09:00,S2,22.0\n"
)


def per_period(period: str, how: str = "mean", by: tuple[str, ...] = ("timestamp", "sensor")) -> dict[str, Any]:
    return {"op": "aggregate", "by": list(by), "column": "temp_c", "how": how, "period": period}


class TestTimeBuckets:
    def test_a_daily_mean_per_sensor(self) -> None:
        prepared = prepare(READINGS, per_period("day"))

        assert rows(prepared) == [
            "timestamp,sensor,temp_c",
            "2026-01-04,S1,10",
            "2026-01-05,S1,12",
            "2026-01-05,S2,20",
            "2026-01-06,S2,22",
        ]
        assert prepared.changes == ["averaged temp_c by timestamp and sensor (day): 4 rows"]
        assert dtypes(prepared)["timestamp"] == "datetime"  # a date axis, never text labels

    def test_iso_weeks_start_on_monday(self) -> None:
        prepared = prepare(READINGS, per_period("week", "max", ("timestamp",)))

        assert rows(prepared) == ["timestamp,temp_c", "2025-12-29,10", "2026-01-05,22"]
        assert prepared.changes == [
            "took the maximum of temp_c by timestamp (ISO week, each as its Monday): 2 rows, 1 other column dropped"
        ]

    def test_hours_keep_their_time(self) -> None:
        prepared = prepare(READINGS, per_period("hour", "count", ("timestamp",)))

        assert cells(prepared, 0) == [
            "2026-01-04T23:00:00",
            "2026-01-05T00:00:00",
            "2026-01-05T01:00:00",
            "2026-01-06T09:00:00",
        ]
        assert cells(prepared, 1) == ["1", "2", "1", "1"]

    def test_an_offset_column_is_cut_by_its_own_clock(self) -> None:
        text = "t,v\n2024-03-30T23:30:00+01:00,1\n2024-03-31T00:30:00+01:00,2\n2024-03-31T01:30:00+01:00,4\n"
        daily = prepare(text, {"op": "aggregate", "by": ["t"], "column": "v", "how": "sum", "period": "day"})
        hourly = prepare(text, {"op": "aggregate", "by": ["t"], "column": "v", "how": "sum", "period": "hour"})

        assert rows(daily) == ["t,v", "2024-03-30,1", "2024-03-31,6"]
        assert daily.changes == ["summed v by t (day, by the clock of UTC+01:00): 2 rows"]
        assert cells(hourly, 0)[0] == "2024-03-30T23:00:00+01:00"

    def test_mixed_offsets_stored_in_utc_are_cut_at_utc_midnight(self) -> None:
        """The parser writes a column of several offsets in UTC; the day follows that clock, and the line says so."""
        text = "t,v\n2024-07-31T00:30:00+02:00,1\n2024-01-31T00:30:00+01:00,2\n"
        prepared = prepare(text, {"op": "aggregate", "by": ["t"], "column": "v", "how": "sum", "period": "day"})

        assert rows(prepared) == ["t,v", "2024-01-30,2", "2024-07-30,1"]
        assert "by the clock of UTC" in prepared.changes[0]

    def test_the_month_labels_stay_as_they_were(self) -> None:
        prepared = prepare(READINGS, per_period("month", "count", ("timestamp",)))

        assert rows(prepared) == ["timestamp,count", "2026-01,5"]
        assert dtypes(prepared)["timestamp"] == "text"


class TestWholeNumberForms:
    """A whole number keeps the form it was written in through the operations (live test round 5 of 2026-10-15)."""

    def test_wide_to_long_keeps_87000_beside_decimals(self) -> None:
        text = "Branch,Q1,Q2\nNorth,120500.5,130100\nEast,87000,90500.25\n"
        prepared = prepare(text, {"op": "pivot_longer", "columns": ["Q1", "Q2"], "names_to": "Quarter"})

        assert cells(prepared, 2) == ["120500.5", "87000", "130100", "90500.25"]
        assert prepared.changes == ["pivoted 2 columns into Quarter/value: 4 rows"]
        assert reparse(prepared).csv == prepared.csv

    def test_a_whole_number_is_written_without_dot_zero_through_every_operation(self) -> None:
        """Owner decision of 2026-10-15: `30` and `30.0` are the same number; one canonical form, no note."""
        text = "k,a,b\nx,2.0,1.5\ny,3.5,7\n"
        melted = prepare(text, {"op": "pivot_longer", "columns": ["a", "b"]})
        sorted_ = prepare(text, {"op": "sort", "column": "a"}, {"op": "rename", "column": "a", "name": "w"})
        typed = prepare(text, {"op": "set_type", "column": "a", "type": "text"})

        assert cells(melted, 2) == ["2", "3.5", "1.5", "7"]
        assert melted.changes == ["pivoted 2 columns into series/value: 4 rows"]
        assert cells(sorted_, 1) == ["2", "3.5"]
        assert cells(typed, 1) == ["2", "3.5"]

    def test_a_whole_number_past_2_53_keeps_its_dot_zero(self) -> None:
        """Past 2**53 a float may hold a whole number only rounded: its `.0` stays, and a change line counts it."""
        prepared = prepare(f"k,a,b\nx,{2**60},1.5\n", {"op": "pivot_longer", "columns": ["a", "b"]})

        assert cells(prepared, 2) == [repr(float(2**60)), "1.5"]

    @pytest.mark.parametrize("seed", [1, 2, 3])
    def test_no_value_is_ever_rounded_silently_by_an_operation_that_moves_it(self, seed: int) -> None:
        """Owner decision of 2026-10-15: only the spelling of a whole number may change, never a value unsaid. Every
        number up to 15 significant digits, whole or not, comes out of the operations that move or reshape cells
        with its exact value, and a whole number without `.0`."""
        generator = random.Random(seed)
        values = [
            str(round(generator.uniform(-1e6, 1e6), generator.randint(0, 8))) if index % 4 else str(index * 1000)
            for index in range(1, 81)
        ]
        rows_ = "".join(f"r{n},{values[2 * n]},{values[2 * n + 1]}\n" for n in range(40))
        text = "k,a,b\n" + rows_
        operations: list[list[dict[str, Any]]] = [
            [{"op": "pivot_longer", "columns": ["a", "b"]}],
            [{"op": "sort", "column": "b", "descending": True}],
            [{"op": "rename", "column": "a", "name": "c"}],
            [drop("a", "gt", "0")],
            [{"op": "set_type", "column": "b", "type": "text"}],
            [
                {"op": "pivot_longer", "columns": ["a", "b"]},
                {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["k"]},
            ],
        ]
        expected = {Decimal(value) for value in values}
        for ops in operations:
            prepared = prepare(text, *ops)
            numbers = [
                cell
                for row in csv.reader(io.StringIO(prepared.csv))
                for cell in row[1:]
                if cell and cell[0] in "-0123456789"
            ]
            assert numbers, ops
            for cell in numbers:
                if cell in ("a", "b"):
                    continue
                assert Decimal(cell) in expected, (ops, cell)  # the exact value, never a rounded one
                if Decimal(cell) == Decimal(cell).to_integral_value():
                    assert "." not in cell and "e" not in cell, (ops, cell)  # a whole number without `.0`
            assert not any("rounded" in change or "decimal numbers" in change for change in prepared.changes), ops


def split(column: str, separator: str, *names: str) -> dict[str, Any]:
    return {"op": "split", "column": column, "separator": separator, "names": list(names)}


# A range table as the agent case triage met it, invented: a count, an average and the ranges as text.
RANGES = "team;games;mean;min–max\nalpha;140;61.5;48–80\nbeta;146;67.2;52–77\ngamma;143;64.0;45–79\n"


class TestSplit:
    def test_a_range_becomes_two_number_columns_beside_its_source(self) -> None:
        prepared = prepare(RANGES, split("min–max", "–", "min", "max"))

        assert prepared.changes == [
            "split min–max at '–' into min and max: 3 of 3 cells split; min and max read as numbers; "
            "min–max stays as it is"
        ]
        assert rows(prepared)[0] == "team,games,mean,min–max,min,max"
        assert cells(prepared, 3) == ["48–80", "52–77", "45–79"]  # the source stays as it was
        assert (cells(prepared, 4), cells(prepared, 5)) == (["48", "52", "45"], ["80", "77", "79"])
        assert dtypes(prepared)["min"] == dtypes(prepared)["max"] == "integer"
        assert prepared.converted == {"min": "min–max", "max": "min–max"}  # an open role takes them
        assert prepared.text_columns == []

    def test_a_cell_without_the_separator_and_one_with_more_are_counted(self) -> None:
        prepared = prepare("k,r\na,1-2\nb,7\nc,3-4-5\n", split("r", "-", "lo", "hi"))

        assert prepared.changes == [
            "split r at '-' into lo and hi: 2 of 3 cells split, 1 cell without it kept whole in lo, 1 with more "
            "keep the rest in hi; lo read as numbers; hi kept as text; r stays as it is"
        ]
        assert (cells(prepared, 2), cells(prepared, 3)) == (["1", "7", "3"], ["2", "", "4-5"])

    def test_a_minus_sign_is_never_a_cut(self) -> None:
        prepared = prepare("k,r\na,-5-10\nb,-10--5\nc,5 - -3\nd,-.5-1\n", split("r", "-", "lo", "hi"))

        assert (cells(prepared, 2), cells(prepared, 3)) == (["-5", "-10", "5", "-0.5"], ["10", "-5", "-3", "1"])
        assert "4 of 4 cells split;" in prepared.changes[0]

    def test_a_separator_of_spaces_cuts_at_every_run_of_spaces(self) -> None:
        prepared = prepare("name,v\nAda  Lovelace,1\nAlan Turing,2\nPlato,3\n", split("name", " ", "first", "last"))

        assert prepared.changes[0].startswith("split name at spaces into first and last: 2 of 3 cells split")
        assert (cells(prepared, 2), cells(prepared, 3)) == (["Ada", "Alan", "Plato"], ["Lovelace", "Turing", ""])
        assert {"first", "last"} <= set(prepared.text_columns)

    def test_a_longer_separator_is_taken_literally(self) -> None:
        prepared = prepare("k,r\na,10 to 20\nb,5 to 8\n", split("r", " to ", "from", "to"))

        assert (cells(prepared, 2), cells(prepared, 3)) == (["10", "5"], ["20", "8"])

    @pytest.mark.parametrize(
        ("text", "low", "high"),
        [
            # Decimal commas keep their reading in a semicolon file with decimal commas.
            ("Ort;Spanne;Wert\nA;1,5–2,5;3,5\nB;0,5–1,25;4,0\n", ["1.5", "0.5"], ["2.5", "1.25"]),
            # Thousands dots keep theirs there too: `1.200` is 1200.
            ("Ort;Spanne;Wert\nA;1.200–2.500;3,5\nB;900–1.100;4,0\n", ["1200", "900"], ["2500", "1100"]),
            # And thousands commas in a file with decimal points.
            ('Ort,Spanne,Wert\nA,"1,200–2,500",3.5\nB,900–1100,4.0\n', ["1200", "900"], ["2500", "1100"]),
        ],
    )
    def test_the_parts_read_with_the_datasets_decimal_mark(self, text: str, low: list[str], high: list[str]) -> None:
        prepared = prepare(text, split("Spanne", "–", "lo", "hi"))

        assert (cells(prepared, 3), cells(prepared, 4)) == (low, high)

    def test_a_part_that_mostly_fails_as_numbers_stays_text(self) -> None:
        """More than a tenth of the cells failing keeps the part text, as `set_type` would refuse it."""
        ranges = "".join(f"r{n},{n}–{n + 5}\n" for n in range(8))
        prepared = prepare("k,t\n" + ranges + "s,x–y\n", split("t", "–", "lo", "hi"))

        assert "lo and hi kept as text" in prepared.changes[0]
        assert {"lo", "hi"} <= set(prepared.text_columns) and prepared.converted == {}

    def test_a_tenth_of_failing_cells_is_counted_and_left_missing(self) -> None:
        ranges = "".join(f"r{n},{n}–{n + 5}\n" for n in range(10))
        prepared = prepare("k,t\n" + ranges + "s,x–9\n", split("t", "–", "lo", "hi"))

        assert "lo and hi read as numbers; 1 cell of lo could not be read and is now missing" in prepared.changes[0]
        assert cells(prepared, 2)[-1] == "" and cells(prepared, 3)[-1] == "9"

    def test_an_iso_date_column_stays_dates_when_the_user_splits_it(self) -> None:
        prepared = prepare("d,v\n2024-11-03,1\n2024-01-15,2\n", split("d", "-", "year", "month", "day"))

        assert dtypes(prepared)["d"] == "datetime" and dtypes(prepared)["year"] == "integer"
        assert cells(prepared, 3) == ["11", "01"]  # leading zeros keep a part text, as the parser keeps them

    def test_a_part_reads_as_numbers_only_as_the_parser_reads_one(self) -> None:
        """`10 kg` is a number with its unit, as the parser reads it; `Q1` is a label, never 1 behind a unit `Q`."""
        prepared = prepare("k,t\na,10 kg–20 kg\nb,5 kg–8 kg\n", split("t", "–", "lo", "hi"))
        quarters = prepare("k,t\na,2024-Q1\nb,2024-Q2\n", split("t", "-", "year", "quarter"))

        assert "lo and hi read as numbers, unit 'kg' removed" in prepared.changes[0]
        assert cells(quarters, 3) == ["Q1", "Q2"] and "quarter kept as text" in quarters.changes[0]

    def test_an_id_splits_only_when_asked_and_keeps_its_letters(self) -> None:
        prepared = prepare("code,v\nA-12,1\nB-7,2\n", split("code", "-", "letter", "number"))

        assert (cells(prepared, 2), cells(prepared, 3)) == (["A", "B"], ["12", "7"])
        assert "letter kept as text; number read as numbers" in prepared.changes[0]

    @pytest.mark.parametrize(
        ("operation", "code", "message"),
        [
            (split("min–max", "/", "a", "b"), "invalid_operation", "no cell of column 'min–max' holds '/'"),
            (
                split("min–max", "–", "a", "b", "c"),
                "invalid_operation",
                "no cell has a part for column 'c'; split into fewer columns",
            ),
            (split("min–max", "–", "mean", "b"), "invalid_operation", "a column named 'mean' already exists"),
            (split("min–max", "–", "a", "a"), "invalid_operation", "the new columns need different names"),
            (split("ghost", "–", "a", "b"), "unknown_column", "there is no column 'ghost'"),
        ],
    )
    def test_refusals(self, operation: dict[str, Any], code: str, message: str) -> None:
        assert failure(RANGES, operation) == (code, message)

    def test_a_split_wider_than_the_column_cap_is_too_wide(self) -> None:
        header = ",".join(f"c{n}" for n in range(MAX_COLUMNS - 1))
        text = f"{header},r\n" + ",".join("1" for _ in range(MAX_COLUMNS - 1)) + ",1-2\n"

        assert failure(text, split("r", "-", "a", "b"))[0] == "too_wide"

    @pytest.mark.parametrize(
        "operation",
        [
            split("r", "", "a", "b"),
            split("r", "-", "a"),
            split("r", "-", *(f"p{n}" for n in range(11))),
            split("r", "\t", "a", "b"),
            split("r", "-" * (MAX_CELL_CHARS + 1), "a", "b"),
        ],
    )
    def test_the_model_refuses_a_malformed_split(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])


class TestExtract:
    @pytest.mark.parametrize(
        ("text", "numbers", "reading"),
        [
            ("t,v\n#12345,1\n#7,2\n", ["12345", "7"], "read as numbers"),
            ("t,v\nCHF 1'200,1\nCHF 950,2\nca. 15,3\n", ["1200", "950", "15"], "read as numbers"),
            ("t;v\nca. -3,5 °C;1\n12 °C;2\n", ["-3.5", "12"], "read as numbers (decimal comma)"),
            ("t,v\nNr.5,1\n.5 l,2\n", ["5", "0.5"], "read as numbers"),
            ("t,v\nA-12,1\nB-7,2\n", ["12", "7"], "read as numbers"),  # a dash after a letter is no minus sign
            # A minus before or after a currency is the sign, never dropped.
            (
                "t,v\n$-100,1\n-$250,2\n€-50,3\nUSD-20,4\nca.-15,5\n",
                ["-100", "-250", "-50", "-20", "-15"],
                "read as numbers",
            ),
        ],
    )
    def test_the_one_number_of_each_cell(self, text: str, numbers: list[str], reading: str) -> None:
        prepared = prepare(text, {"op": "extract", "column": "t", "keep": "number", "name": "n"})

        assert cells(prepared, 2) == numbers
        assert prepared.changes[0].endswith(f"of t, {reading}; t stays as it is")
        assert prepared.converted == {"n": "t"}

    def test_a_cell_with_two_numbers_or_none_has_no_number(self) -> None:
        values = "".join(f"r{n},ca. {n}\n" for n in range(10))
        prepared = prepare(
            "k,t\n" + values + "s,10–20\n", {"op": "extract", "column": "t", "keep": "number", "name": "n"}
        )

        assert prepared.changes == [
            "new column n: the number in 10 of 11 cells of t, read as numbers, 1 cell without exactly one number is "
            "missing; t stays as it is"
        ]
        assert cells(prepared, 2)[-1] == ""

    def test_more_than_a_tenth_without_a_number_is_refused(self) -> None:
        assert failure(
            "t,v\n10–20,1\n12,2\nx,3\n", {"op": "extract", "column": "t", "keep": "number", "name": "n"}
        ) == ("type_mismatch", "column 't': 2 of 3 cells hold no number, or more than one")

    def test_digits_keep_leading_zeros_as_text(self) -> None:
        prepared = prepare("t,v\n#00123,1\n#00456,2\n", {"op": "extract", "column": "t", "keep": "digits", "name": "d"})

        assert cells(prepared, 2) == ["00123", "00456"] and "d" in prepared.text_columns
        assert dtypes(prepared)["d"] == "text"

    def test_digits_without_a_leading_zero_read_as_numbers(self) -> None:
        prepared = prepare(
            "p,v\n+41 79 123,1\n+41 44 555,2\n", {"op": "extract", "column": "p", "keep": "digits", "name": "d"}
        )

        assert cells(prepared, 2) == ["4179123", "4144555"]
        assert prepared.changes == [
            "new column d: the digits of 2 of 2 cells of p; d read as numbers; p stays as it is"
        ]

    def test_letters_keep_the_spaces_between_words(self) -> None:
        prepared = prepare(
            "t,v\nNew York 10001,1\n12 kg,2\n7,3\n", {"op": "extract", "column": "t", "keep": "letters", "name": "l"}
        )

        assert cells(prepared, 2) == ["New York", "kg", ""]
        assert prepared.changes == [
            "new column l: the letters of 2 of 3 cells of t, 1 cell without a letter is empty; l kept as text; "
            "t stays as it is"
        ]

    def test_a_column_without_any_digit_is_refused(self) -> None:
        assert failure("t,v\nab,1\ncd,2\n", {"op": "extract", "column": "t", "keep": "digits", "name": "d"}) == (
            "invalid_operation",
            "no cell of column 't' holds a digit",
        )


class TestStripAndReplace:
    def test_a_prefix_comes_off(self) -> None:
        prepared = prepare("t,v\n#12,1\n#7,2\n3,3\n", {"op": "strip", "column": "t", "prefix": "#", "name": "n"})

        assert cells(prepared, 2) == ["12", "7", "3"]
        assert prepared.changes == [
            "new column n: '#' off the start of 2 of 3 cells of t; n read as numbers; t stays as it is"
        ]

    def test_a_prefix_and_a_suffix_with_spaces_around_them(self) -> None:
        prepared = prepare(
            "t,v\nCHF 100 net,1\nCHF 200 net,2\n",
            {"op": "strip", "column": "t", "prefix": "CHF ", "suffix": " net", "name": "n"},
        )

        assert cells(prepared, 2) == ["100", "200"]
        assert prepared.changes[0].startswith("new column n: 'CHF' off the start and 'net' off the end of 2 of 2 cells")

    def test_strip_refusals(self) -> None:
        assert failure("t,v\na,1\nb,2\n", {"op": "strip", "column": "t", "name": "n"}) == (
            "invalid_operation",
            "strip needs a prefix, a suffix or both",
        )
        assert failure(
            "t,v\na,1\nb,2\n", {"op": "strip", "column": "t", "prefix": "#", "suffix": "x", "name": "n"}
        ) == ("invalid_operation", "no cell of column 't' starts with '#' or ends with 'x'")
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([{"op": "strip", "column": "t", "prefix": "  ", "name": "n"}])

    def test_replace_writes_a_new_text_and_types_the_result(self) -> None:
        prepared = prepare(
            "t,v\n1.5 / 2,1\n2.5 / 3,2\n", {"op": "replace", "column": "t", "old": " / ", "new": "–", "name": "r"}
        )

        assert cells(prepared, 2) == ["1.5–2", "2.5–3"]
        assert prepared.changes == [
            "new column r: ' / ' replaced with '–' in 2 of 2 cells of t; r kept as text; t stays as it is"
        ]

    def test_replace_with_nothing_removes(self) -> None:
        prepared = prepare("t,v\n1 200 Fr.,1\n950 Fr.,2\n", {"op": "replace", "column": "t", "old": "Fr.", "name": "r"})

        assert prepared.changes[0].startswith("new column r: 'Fr.' removed in 2 of 2 cells of t; r read as numbers")
        assert cells(prepared, 2) == ["1200", "950"]

    def test_replace_refusals(self) -> None:
        assert failure("t,v\nx,1\ny,2\n", {"op": "replace", "column": "t", "old": "z", "name": "r"}) == (
            "invalid_operation",
            "no cell of column 't' holds 'z'",
        )
        long = "x" * 101
        text = f"t,v\n{long},1\ny,2\n"
        assert failure(text, {"op": "replace", "column": "t", "old": "x", "new": "yy", "name": "r"}) == (
            "invalid_operation",
            "a cell would be longer than the 200 characters a cell may hold",
        )
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([{"op": "replace", "column": "t", "old": "x", "new": "a\nb", "name": "r"}])

    def test_a_mark_of_a_number_column_is_no_text_to_work_on(self) -> None:
        """`1,5` in a decimal-comma file is the number 1.5, stored `1.5`, and `12.50` is stored `12.5`: an operation
        on the `.` or `,` of such a column would work on another text than the user's, so it is refused."""
        for text, old in (("p;v\n1,5;1\n2,5;2\n", ","), ("p,v\n12.50,1\n7.25,2\n", ".")):
            code, message = failure(text, {"op": "replace", "column": "p", "old": old, "name": "n"})
            assert code == "type_mismatch" and "column 'p' holds numbers" in message
        code, _ = failure("p,v\n12.50,1\n7.25,2\n", split("p", ".", "whole", "part"))
        assert code == "type_mismatch"

    def test_a_number_column_keeps_its_other_text_operations(self) -> None:
        """A text operation that looks for no mark reads the canonical text as before."""
        prepared = prepare("p,v\n-12,1\n-7,2\n", {"op": "strip", "column": "p", "prefix": "-", "name": "n"})

        assert cells(prepared, 2) == ["12", "7"]

    def test_a_pasted_number_column_is_read_as_pasted(self) -> None:
        """A column whose dots could be decimals or thousands keeps its cells as pasted: removing the dots works on
        `7.000`, never on the stored `7`."""
        prepared = prepare(
            "Stadt;Einwohner\nBern;1.234\nBasel;7.000\nChur;12\n",
            {"op": "replace", "column": "Einwohner", "old": ".", "name": "n"},
        )

        assert cells(prepared, 2) == ["1234", "7000", "12"]
        with pytest.raises(PrepareError) as raised:  # after a sort a row of the frame is no pasted row any more
            prepare(
                "Stadt;Einwohner\nBern;1.234\nBasel;7.000\nChur;12\n",
                {"op": "sort", "column": "Stadt"},
                {"op": "replace", "column": "Einwohner", "old": ".", "name": "n"},
            )
        assert raised.value.code == "type_mismatch"

    FOOTNOTE = (
        "District\t2024\t2025\nOld Town\t22.497\t26.215\nHarbour\t41.377\t57.902\n"
        "University\t45.454\t38.790*\nPark\t49.000\t58.953\n"
    )
    """Invented counts with thousands dots and one footnote star, which keeps `2025` text at the paste."""

    def test_a_result_whose_decimal_mark_is_open_stays_text_for_set_type(self) -> None:
        """`38.790` with its star taken off is 38.79 or 38790: typed by a guess, the zero would be gone for good."""
        prepared = prepare(
            self.FOOTNOTE,
            {"op": "strip", "column": "2025", "suffix": "*", "name": "c"},
            {"op": "set_type", "column": "c", "type": "number", "decimal": ","},
        )

        assert cells(prepared, 3) == ["26215", "57902", "38790", "58953"]
        assert prepared.changes[0] == (
            "new column c: '*' off the end of 1 of 4 cells of 2025; c kept as text, since its cells read as numbers "
            'with either decimal mark: set_type to number with "decimal" reads them; 2025 stays as it is'
        )
        assert prepared.changes[1] == "c: 4 cells read as numbers"

    def test_the_dots_of_such_a_result_are_removed_from_its_text(self) -> None:
        prepared = prepare(
            self.FOOTNOTE,
            {"op": "strip", "column": "2025", "suffix": "*", "name": "c"},
            {"op": "replace", "column": "c", "old": ".", "name": "n"},
        )

        assert cells(prepared, 3) == ["26.215", "57.902", "38.790", "58.953"]  # text, as written
        assert cells(prepared, 4) == ["26215", "57902", "38790", "58953"]
        assert dtypes(prepared)["c"] == "text" and dtypes(prepared)["n"] == "integer"

    def test_set_type_says_which_mark_it_took_when_none_was_named(self) -> None:
        """The one operation that reads the column directly: with the mark named it reads the thousands, the star
        taken off; without, it takes the dataset's mark and says how to get the other reading."""
        named = prepare(self.FOOTNOTE, {"op": "set_type", "column": "2025", "type": "number", "decimal": ","})
        assert cells(named, 2) == ["26215", "57902", "38790", "58953"]
        assert named.changes == ["2025: 4 cells read as numbers, unit '*' removed"]

        guessed = prepare(self.FOOTNOTE, {"op": "set_type", "column": "2025", "type": "number"})
        assert cells(guessed, 2) == ["26.215", "57.902", "38.79", "58.953"]
        assert guessed.changes[0].endswith(
            'dots read as the decimal mark; if they separate thousands, undo this and set "decimal": ","'
        )

    def test_the_digits_of_a_number_column_need_its_cells_as_pasted(self) -> None:
        """The digits of `7.000` are 7000, and of the stored `7` only 7: read from the pasted cells, else refused."""
        pasted = "Stadt;Einwohner\nBern;1.234\nBasel;7.000\nChur;12\n"
        digits = {"op": "extract", "column": "Einwohner", "keep": "digits", "name": "d"}

        assert cells(prepare(pasted, digits), 2) == ["1234", "7000", "12"]
        code, message = failure(pasted, {"op": "sort", "column": "Stadt"}, digits)
        assert code == "type_mismatch" and "column 'Einwohner' holds numbers" in message
        assert failure("p,v\n12.50,1\n7.25,2\n", {"op": "extract", "column": "p", "keep": "digits", "name": "d"})[
            0
        ] == ("type_mismatch")

    def test_a_cell_no_mark_reads_leaves_the_mark_open(self) -> None:
        """One cell of words among ten says nothing about the mark: the column stays text, and a `set_type` that
        names no mark still says which one it took."""
        counts = ("26.215", "38.790", "57.902", "48.449", "39.303", "38.799", "10.093", "45.511", "58.953", "k. A.")
        text = "k\tn\n" + "".join(f"{name}\t{count}*\n" for name, count in zip("abcdefghij", counts, strict=True))

        stripped = prepare(text, {"op": "strip", "column": "n", "suffix": "*", "name": "c"})
        assert (
            dtypes(stripped)["c"] == "text" and "kept as text, since its cells read as numbers" in stripped.changes[0]
        )

        read = prepare(text, {"op": "set_type", "column": "n", "type": "number"})
        assert "1 cell could not be read and is now missing" in read.changes[0]
        assert read.changes[0].endswith('undo this and set "decimal": ","')

    def test_decimal_commas_that_could_separate_thousands_stay_text_too(self) -> None:
        """The same in a file of decimal commas: `38,790` is 38.79 there, and 38790 with a decimal point."""
        text = "Ort;Wert;Zahl\nA;3,5;26,215\nB;4,0;38,790*\n"
        star = {"op": "strip", "column": "Zahl", "suffix": "*", "name": "n"}
        prepared = prepare(text, star)

        assert dtypes(prepared)["n"] == "text" and cells(prepared, 3) == ["26,215", "38,790"]
        read = prepare(text, star, {"op": "set_type", "column": "n", "type": "number", "decimal": "."})
        assert cells(read, 3) == ["26215", "38790"]

    def test_a_mark_the_file_reads_as_thousands_is_no_open_mark(self) -> None:
        """In a file of decimal commas a dot between three-digit groups separates thousands: the part is a number."""
        prepared = prepare(
            "Ort;Wert;Menge\nA;3,5;1.200 Stk\nB;4,0;900\n",
            {"op": "strip", "column": "Menge", "suffix": "Stk", "name": "n"},
        )

        assert cells(prepared, 3) == ["1200", "900"] and "n read as numbers" in prepared.changes[0]


class TestTextChains:
    def test_strip_then_split_then_keep_the_digits_in_one_call(self) -> None:
        prepared = prepare(
            "t,v\n#A-12-x3,1\n#B-7-x4,2\n",
            {"op": "strip", "column": "t", "prefix": "#", "name": "t2"},
            split("t2", "-", "kind", "number", "rest"),
            {"op": "extract", "column": "rest", "keep": "digits", "name": "digit"},
        )

        assert len(prepared.changes) == 3
        assert rows(prepared)[0] == "t,v,t2,kind,number,rest,digit"
        assert rows(prepared)[1:] == ["#A-12-x3,1,A-12-x3,A,12,x3,3", "#B-7-x4,2,B-7-x4,B,7,x4,4"]
        assert dtypes(prepared)["number"] == dtypes(prepared)["digit"] == "integer"
        assert prepared.converted == {"number": "t2", "digit": "rest"}

    def test_a_split_of_a_renamed_column_is_carried_under_the_new_name(self) -> None:
        prepared = prepare(
            RANGES, split("min–max", "–", "lo", "hi"), {"op": "rename", "column": "lo", "name": "Minimum"}
        )

        assert prepared.converted == {"Minimum": "min–max", "hi": "min–max"}

    def test_the_source_data_is_untouched(self) -> None:
        """The operations work on a copy: the version before stays as it was for `.undo()`."""
        parsed = parse_dataset(RANGES)
        before = parsed.csv

        apply_operations(parsed, OPERATIONS.validate_python([split("min–max", "–", "min", "max")]))

        assert parsed.csv == before
