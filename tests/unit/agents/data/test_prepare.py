"""Tests for agents/anyplot/data/prepare.py: every operation, the error codes, the change lines, the round trip.

The parser types a column whose every cell carries the same unit at the paste (`12,5 %`, `7 %` becomes
`Anteil (%)`, numbers), so the unit columns here keep one bare cell (`7`): they stay text, and
`set_type number` has cells to read.
"""

import csv
import io
import random
from typing import Any

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
    "2024-01-20,Katze,7,800.0\n"
    "2024-02-14,Hund,30 %,300.25\n"
    "2024-02-28,Katze,,150.0\n"
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
        assert parsed.warnings[0].startswith(f"4 numbers {RESPELLED}")


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

    def test_a_missing_cell_matches_no_comparison(self) -> None:
        kept_by_ne = prepare(SALES, drop("Anteil", "ne", "7"))
        kept_by_contains = prepare(SALES, drop("Anteil", "contains", "%"))

        assert rows(kept_by_ne)[1:] == ["2024-01-20,Katze,7,800.0", "2024-02-28,Katze,,150.0"]
        assert rows(kept_by_contains)[1:] == ["2024-01-20,Katze,7,800.0", "2024-02-28,Katze,,150.0"]

    def test_boolean_columns(self) -> None:
        text = "flag,v\ntrue,1\nfalse,2\n,3\n"

        assert rows(prepare(text, drop("flag", "eq", "TRUE")))[1:] == ["False,2", ",3"]
        assert failure(text, drop("flag", "gt", "true"))[0] == "invalid_operation"
        assert failure(text, drop("flag", "eq", "yes"))[0] == "invalid_operation"

    def test_text_orders_as_text(self) -> None:
        prepared = prepare(SALES, drop("Tier", "gt", "Hund"))

        assert cells(prepared, 1) == ["Hund", "Hund", "Hund", "Gesamt"]

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
            "t: 4 cells read as dates (format inferred, year first where a cell starts with one, else day before month)"
        ]

    def test_a_number_column_is_a_type_mismatch(self) -> None:
        assert failure(SALES, {"op": "set_type", "column": "Umsatz", "type": "datetime"})[0] == "type_mismatch"


class TestSetTypeText:
    def test_cells_become_their_canonical_text_and_stay_text_through_the_reparse(self) -> None:
        """The change line is true: the column is text in the next version, not re-typed by its cells (verifiers)."""
        prepared = prepare(SALES, {"op": "set_type", "column": "Datum", "type": "text"})

        assert prepared.csv == SALES_CSV
        assert prepared.changes == ["Datum: 6 cells now text"]
        assert prepared.text_columns == ["Datum"]
        again = reparse(prepared)
        assert again.column_dtypes["Datum"] == "text" and again.text_columns == ["Datum"]
        assert again.profile.columns[0].top == ["2024-01-05", "2024-01-20", "2024-02-14", "2024-02-28", "2024-03-15"]

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
            "Katze,2024-Q1,475.0",
        ]
        assert prepared.changes == ["averaged Umsatz by Tier and Datum (quarter): 3 rows, 1 other column dropped"]

    def test_year_min_and_max(self) -> None:
        minimum = prepare(
            SALES, {"op": "aggregate", "by": ["Datum"], "column": "Umsatz", "how": "min", "period": "year"}
        )
        maximum = prepare(SALES, {"op": "aggregate", "by": ["Datum"], "column": "Tier", "how": "max", "period": "year"})

        assert rows(minimum) == ["Datum,Umsatz", "2024,150.0"]
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

        assert cells(prepared, 3) == ["3450.5", "1200.5", "999.75", "800.0", "300.25", "150.0"]
        assert prepared.changes == ["sorted by Umsatz, descending"]

    def test_ascending_is_stable_with_missing_cells_last(self) -> None:
        prepared = prepare(SALES, {"op": "sort", "column": "Anteil"})

        assert cells(prepared, 1) == ["Gesamt", "Hund", "Hund", "Hund", "Katze", "Katze"]
        assert rows(prepared)[-1] == "2024-02-28,Katze,,150.0"
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

        assert rows(prepared) == [
            "Monat,series,value",
            "2024-01,Hüte,10",
            "2024-02,Hüte,15",
            "2024-03,Hüte,",
            "2024-01,Schuhe,20",
            "2024-02,Schuhe,",
            "2024-03,Schuhe,30",
        ]
        assert prepared.changes == ["pivoted 2 columns into series/value: 6 rows"]
        assert dtypes(prepared) == {"Monat": "text", "series": "text", "value": "integer"}

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

        assert rows(prepared) == ["Monat,Hüte,Schuhe", "2024-01,10,20", "2024-02,15,", "2024-03,,30"]
        assert dtypes(prepared) == {"Monat": "text", "Hüte": "integer", "Schuhe": "integer"}

    def test_values_kept_text_make_text_columns(self) -> None:
        operation = {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}
        prepared = prepare(LONG, {"op": "set_type", "column": "value", "type": "text"}, operation)

        assert prepared.text_columns == ["Hüte", "Schuhe"]
        assert dtypes(prepared) == {"Monat": "text", "Hüte": "text", "Schuhe": "text"}

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
        frame = pd.read_csv(io.StringIO(again.csv), float_precision="round_trip", dtype={"n": "Int64"})

        assert sorted(cells(prepared, 1)) == sorted(repr(value) for value in values)
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
            "2026-01-04,S1,10.0",
            "2026-01-05,S1,12.0",
            "2026-01-05,S2,20.0",
            "2026-01-06,S2,22.0",
        ]
        assert prepared.changes == ["averaged temp_c by timestamp and sensor (day): 4 rows"]
        assert dtypes(prepared)["timestamp"] == "datetime"  # a date axis, never text labels

    def test_iso_weeks_start_on_monday(self) -> None:
        prepared = prepare(READINGS, per_period("week", "max", ("timestamp",)))

        assert rows(prepared) == ["timestamp,temp_c", "2025-12-29,10.0", "2026-01-05,22.0"]
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

    def test_a_column_written_with_dot_zero_keeps_it(self) -> None:
        text = "k,v\na,2.0\nb,1.5\nc,3.0\n"
        prepared = prepare(text, {"op": "sort", "column": "v"}, {"op": "rename", "column": "v", "name": "w"})

        assert cells(prepared, 1) == ["1.5", "2.0", "3.0"]

    def test_each_melted_cell_keeps_its_columns_form(self) -> None:
        prepared = prepare("k,a,b\nx,2.0,1.5\ny,3.5,7\n", {"op": "pivot_longer", "columns": ["a", "b"]})

        assert cells(prepared, 2) == ["2.0", "3.5", "1.5", "7"]
        assert prepared.changes == ["pivoted 2 columns into series/value: 4 rows"]

    def test_one_number_written_both_ways_takes_one_form_and_is_counted(self) -> None:
        prepared = prepare("k,a,b\nx,2.0,2\ny,1.5,3.5\n", {"op": "pivot_longer", "columns": ["a", "b"]})

        assert cells(prepared, 2) == ["2", "1.5", "2", "3.5"]
        assert prepared.changes == [
            "pivoted 2 columns into series/value: 4 rows, 1 whole number that the columns wrote both with and "
            "without '.0' written without it"
        ]

    def test_wide_columns_take_the_form_of_their_values(self) -> None:
        long = "Monat,series,value\nJan,a,2.0\nJan,b,1.5\nFeb,a,3.5\nFeb,b,4.0\n"
        prepared = prepare(
            long, {"op": "pivot_wider", "names_from": "series", "values_from": "value", "index": ["Monat"]}
        )

        assert rows(prepared)[1:] == ["Feb,3.5,4.0", "Jan,2.0,1.5"]

    def test_set_type_text_keeps_the_written_form(self) -> None:
        prepared = prepare("k,v\na,2.0\nb,1.5\nc,87000\n", {"op": "set_type", "column": "v", "type": "text"})

        assert cells(prepared, 1) == ["2.0", "1.5", "87000"]
