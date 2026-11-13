"""The data operations of 2026-11-07 in agents/anyplot/data/prepare.py: `compute`, `diff`, `rolling`, `blank`, the
"any of" conditions, `aggregate` over several columns with `first` and `last`, a `classify` fallback's groups and the
`unsupported` operation.

They come from the persona tests of 2026-11-06, where five of ten personas got no plot because a column could not be
derived. Every dataset here is invented.
"""

import math
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import (
    MAX_ANY_VALUES,
    MAX_INPUTS,
    MAX_OPERATIONS,
    Aggregate,
    PrepareError,
    apply_operations,
)
from agents.anyplot.schemas import MAX_COLUMNS, MAX_NOTE_CHARS

from .test_prepare import OPERATIONS, cells, classify, derive, drop, dtypes, failure, prepare, reparse, rows


def compute(name: str, expression: str, **inputs: str) -> dict[str, Any]:
    return {"op": "compute", "name": name, "expression": expression, "inputs": inputs}


def diff(name: str, column: str, order: str, **extra: Any) -> dict[str, Any]:
    return {"op": "diff", "name": name, "column": column, "order": order, **extra}


def rolling(name: str, column: str, how: str, window: int, order: str, **extra: Any) -> dict[str, Any]:
    return {"op": "rolling", "name": name, "column": column, "how": how, "window": window, "order": order, **extra}


def blank(columns: list[str], *where: dict[str, Any]) -> dict[str, Any]:
    return {"op": "blank", "columns": columns, "where": list(where)}


def any_of(column: str, test: str, *values: object) -> dict[str, Any]:
    return {"column": column, "test": test, "values": list(values)}


# A pendulum lab: lengths and periods with the units in the headers, one period missing and one of 0.
PENDULUM = "Länge l in m,Periode T in s\n0.25,1.003\n0.5,1.419\n0.75,\n1.0,2.006\n1.2,0\n"
LENGTHS = [0.25, 0.5, 0.75, 1.0, 1.2]
PERIODS = [1.003, 1.419, None, 2.006, 0.0]


class TestCompute:
    def test_a_power_with_constants_over_columns_named_with_spaces(self) -> None:
        prepared = prepare(PENDULUM, compute("g", "4*pi**2*l/T**2", l="Länge l in m", T="Periode T in s"))

        expected = [
            "" if period is None or period == 0 else repr(4 * math.pi**2 * length / period**2)
            for length, period in zip(LENGTHS, PERIODS, strict=True)
        ]
        assert cells(prepared, 2) == expected
        assert prepared.changes == [
            "added column g: 4*pi**2*l/T**2 with l = Länge l in m, T = Periode T in s, "
            "2 cells are empty (1 with a missing input, 1 with a division by zero)"
        ]
        assert dtypes(prepared)["g"] == "number"

    def test_the_change_line_quotes_the_checked_expression(self) -> None:
        """Whitespace collapsed and the typographic operators in ASCII, as `generate_data` quotes a formula."""
        prepared = prepare("q,p\n2,3\n", compute("r", "q  ×  p  −  1", q="q", p="p"))

        assert cells(prepared, 2) == ["5"]
        assert prepared.changes == ["added column r: q * p - 1"]

    def test_a_product_of_whole_numbers_stays_exact_past_float_precision(self) -> None:
        """A float64 holds integers only up to 2**53: 9007199254740993 * 3 would come back as ...976."""
        prepared = prepare("q,p\n3,7\n9007199254740993,3\n", compute("Revenue", "q * p", q="q", p="p"))

        assert cells(prepared, 2) == ["21", str(9007199254740993 * 3)]
        assert dtypes(prepared)["Revenue"] == "integer"

    def test_whole_steps_floor_divide_and_count_a_division_by_zero(self) -> None:
        text = "minutes,parts\n135,60\n-7,2\n20,0\n,3\n"
        hours = prepare(text, compute("h", "m // p", m="minutes", p="parts"))
        rest = prepare(text, compute("r", "m % p + abs(m) - abs(m)", m="minutes", p="parts"))

        assert cells(hours, 2) == ["2", "-4", "", ""]  # floor division, as Python and NumPy do it
        assert cells(rest, 2) == ["15", "1", "", ""]
        assert hours.changes[0].endswith("2 cells are empty (1 with a missing input, 1 with a division by zero)")
        assert dtypes(hours)["h"] == "integer"

    def test_a_whole_power_and_the_whole_functions_stay_whole(self) -> None:
        prepared = prepare("a,b\n3,-5\n", compute("c", "a**3 + sign(b) * max(a, b) - min(a, b) + 0**0", a="a", b="b"))

        assert cells(prepared, 2) == [str(3**3 + -1 * 3 - (-5) + 1)]
        assert dtypes(prepared)["c"] == "integer"

    def test_a_result_past_int64_is_stored_as_a_float_and_counted(self) -> None:
        prepared = prepare(f"a\n{2**62}\n3\n", compute("b", "a * a", a="a"))

        assert cells(prepared, 1) == [repr(float(2**124)), "9"]
        assert "1 whole number past 2^53 is stored as decimal numbers" in prepared.changes[0]

    def test_a_whole_result_beyond_any_float_is_empty_and_counted(self) -> None:
        """2**40 to the 200th has 8,001 bits, past any float; 2**200 fits one, stored as a float and counted."""
        prepared = prepare(f"a\n{2**40}\n2\n", compute("b", "a ** 200", a="a"))

        assert cells(prepared, 1) == ["", repr(float(2**200))]
        assert "1 cell is empty (1 outside a function's domain or the number range)" in prepared.changes[0]
        assert "1 whole number past 2^53 is stored as decimal numbers" in prepared.changes[0]

    def test_the_largest_whole_number_a_float_holds_is_kept(self) -> None:
        """Copilot on #12597: 2**1023 has 1,024 bits and is a finite float; only a value past the float range is empty."""
        prepared = prepare("a\n2\n3\n", compute("b", "a ** 1023", a="a"))
        beyond = prepare("a\n2\n1\n", compute("b", "a ** 1024", a="a"))

        assert cells(prepared, 1) == [repr(float(2**1023)), ""]
        assert cells(beyond, 1) == ["", "1"]
        assert "1 outside a function's domain or the number range" in beyond.changes[0]

    @pytest.mark.parametrize(
        ("expression", "computed"),
        [
            ("q / 2", ["1.5", "1"]),
            ("q * 1.5", ["4.5", "3"]),
            ("q ** -1", [repr(1 / 3), "0.5"]),
            ("q * pi", [repr(3 * math.pi), repr(2 * math.pi)]),
        ],
    )
    def test_a_step_that_leaves_whole_numbers_takes_float64(self, expression: str, computed: list[str]) -> None:
        prepared = prepare("q\n3\n2\n", compute("r", expression, q="q"))

        assert cells(prepared, 1) == computed
        assert dtypes(prepared)["r"] == "number"

    def test_whole_inputs_past_2_53_read_as_floats_are_counted(self) -> None:
        """A function takes float64, which reads the input rounded; a plain division is exact until its one rounding."""
        through_a_function = prepare("a\n9007199254740993\n2\n", compute("b", "abs(a) / 1", a="a"))
        divided = prepare("a\n9007199254740993\n2\n", compute("b", "a / 1", a="a"))

        assert "1 whole number past 2^53 in the inputs is read as decimal numbers" in through_a_function.changes[0]
        assert "1 value past 2^53 is stored as decimal numbers" in divided.changes[0]

    @pytest.mark.parametrize(
        ("text", "expression", "computed"),
        [
            ("p,q\n19.99,3\n0.1,0.2\n", "p * q", ["59.97", "0.02"]),
            ("p,q\n0.1,0.2\n1.1,2.2\n", "p + q", ["0.3", "3.3"]),
            # The exact quotient 2.2 / 10.1 rounded once: float64 steps give ...785, one digit off.
            ("p,q\n12.3,10.1\n0.3,0.1\n", "(p - q) / q", [repr(float(Decimal("2.2") / Decimal("10.1"))), "2"]),
            ("p,q\n1e308,10\n5,2\n", "p * q / q", ["1e+308", "5"]),  # no step overflows in decimals
        ],
    )
    def test_plain_arithmetic_is_exact_decimals_with_one_rounding(
        self, text: str, expression: str, computed: list[str]
    ) -> None:
        """`19.99 * 3` is 59.97, never the float noise 59.96999999999999 (review of 2026-11-07)."""
        prepared = prepare(text, compute("r", expression, p="p", q="q"))

        assert cells(prepared, 2) == computed

    def test_a_difference_writes_what_diff_writes(self) -> None:
        text = "t,a,b\n1,12.3,10.1\n2,7.7,5.5\n"
        computed = prepare(text, compute("d", "a - b", a="a", b="b"))
        stepped = prepare(
            "t,a\n1,10.1\n2,12.3\n3,5.5\n4,7.7\n", {"op": "diff", "name": "d", "column": "a", "order": "t"}
        )

        assert cells(computed, 3) == ["2.2", "2.2"]
        assert cells(stepped, 2)[1] == "2.2" and cells(stepped, 2)[3] == "2.2"

    def test_a_unit_conversion(self) -> None:
        prepared = prepare("Stadt,F\nBern,41\nLugano,52\n", compute("C", "(f - 32) * 5 / 9", f="F"))

        assert cells(prepared, 2) == ["5", repr((52 - 32) * 5 / 9)]  # 5.0 written as the parser writes it

    def test_every_empty_cell_is_counted_by_its_reason(self) -> None:
        text = "price,base\n150,1\n100,1\n90,1\n,1\n120,0\n"
        prepared = prepare(text, compute("lx", "log(p - 100) / b", p="price", b="base"))

        assert cells(prepared, 2) == [repr(math.log(50)), "", "", "", ""]
        assert prepared.changes[0].endswith(
            "4 cells are empty (1 with a missing input, 1 with a division by zero, "
            "2 outside a function's domain or the number range)"
        )

    def test_a_step_that_is_undefined_empties_the_cell_even_when_a_later_step_is_finite(self) -> None:
        """atan(1/0) would be pi/2 in float64: a written cell has every step defined."""
        prepared = prepare("a\n1\n2\n", compute("b", "atan(1 / (a - 1))", a="a"))

        assert cells(prepared, 1) == ["", repr(math.atan(1.0))]
        assert "1 with a division by zero" in prepared.changes[0]

    def test_a_rounding_the_user_asks_for_is_written_into_the_new_column(self) -> None:
        prepared = prepare("v\n2.5\n3.7\n", compute("r", "round(v)", v="v"))

        assert cells(prepared, 1) == ["2", "4"]  # half to even, as generate_data rounds
        assert cells(prepared, 0) == ["2.5", "3.7"]

    @pytest.mark.parametrize(
        ("operation", "code", "words"),
        [
            (
                compute("g", "4*pi**2*x/T**2", l="Länge l in m", T="Periode T in s"),
                "invalid_operation",
                "unknown name 'x'",
            ),
            (compute("g", "l * 2", l="Länge l in m", T="Periode T in s"), "invalid_operation", "input 'T' is not in"),
            (compute("g", "l > 1", l="Länge l in m"), "invalid_operation", "comparisons"),
            (compute("g", "__import__(l)", l="Länge l in m"), "invalid_operation", "unknown function"),
            (compute("g", "l * 2", l="Länge"), "unknown_column", "there is no column 'Länge'"),
            (compute("Länge l in m", "l * 2", l="Länge l in m"), "invalid_operation", "already exists"),
        ],
    )
    def test_refusals(self, operation: dict[str, Any], code: str, words: str) -> None:
        found = failure(PENDULUM, operation)

        assert found[0] == code and words in found[1]

    @pytest.mark.parametrize(
        ("text", "hint"), [("t,v\n2024-01-05,1\n", "date_number"), ("t,v\nabc,1\n", "set_type it to number first")]
    )
    def test_an_input_that_holds_no_numbers_names_the_way_to_numbers(self, text: str, hint: str) -> None:
        code, message = failure(text, compute("b", "t + v", t="t", v="v"))

        assert code == "type_mismatch" and hint in message

    def test_a_column_without_any_value_is_refused(self) -> None:
        assert failure("a\n0\n0\n", compute("b", "1 / a", a="a"))[0] == "invalid_operation"

    def test_a_full_table_is_too_wide(self) -> None:
        header = ",".join(f"c{i}" for i in range(MAX_COLUMNS))
        text = f"{header}\n{','.join('1' for _ in range(MAX_COLUMNS))}\n"

        assert failure(text, compute("k", "a + 1", a="c0"))[0] == "too_wide"

    def test_an_input_named_like_a_constant_stands_for_its_column(self) -> None:
        """The root named an export column `e` in the prep eval of 2026-11-07: the input wins, and the line says so."""
        text = "PV,Export\n400,250\n500,350\n"
        prepared = prepare(text, compute("Self", "(pv - e) / pv", pv="PV", e="Export"))
        whole = prepare(text, compute("Rest", "pv - e", pv="PV", e="Export"))

        assert cells(prepared, 2) == ["0.375", "0.3"]
        assert prepared.changes == ["added column Self: (pv - e) / pv with pv = PV, e = Export"]
        assert cells(whole, 2) == ["150", "150"] and dtypes(whole)["Rest"] == "integer"

    @pytest.mark.parametrize(
        "operation",
        [
            compute("g", "1"),
            compute("g", "l", **{"Länge": "Länge l in m"}),
            compute("g", "log * 2", log="Länge l in m"),
            compute("g", "x and 2", **{"and": "Länge l in m"}),
            compute("g", "x" * 201, x="Länge l in m"),
            compute("g", "", x="Länge l in m"),
            compute("g ", "x", x="Länge l in m"),
            compute(
                "g", "+".join(f"x{i}" for i in range(MAX_INPUTS + 1)), **{f"x{i}": "a" for i in range(MAX_INPUTS + 1)}
            ),
            {**compute("g", "x", x="Länge l in m"), "round": 3},
        ],
    )
    def test_malformed_compute_fails_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])

    def test_the_computed_column_feeds_a_sort_in_the_same_call(self) -> None:
        """Quantity times price, then the largest revenue first: the persona's top-sellers request."""
        text = "Product,Quantity,Price\nTea,12,3.5\nCake,4,12\nJam,30,2.25\n"
        prepared = prepare(
            text,
            compute("Revenue", "q * p", q="Quantity", p="Price"),
            {"op": "sort", "column": "Revenue", "descending": True},
        )

        assert rows(prepared) == ["Product,Quantity,Price,Revenue", "Jam,30,2.25,67.5", "Cake,4,12,48", "Tea,12,3.5,42"]


# Cumulative meter readings, several a month and not in order, one reading missing.
METER = (
    "Datum,Bezug,Einspeisung\n"
    "2024-01-28,1180.4,310.2\n"
    "2024-01-03,1100.1,300\n"
    "2024-02-27,1290.6,355.8\n"
    "2024-02-10,1230.3,\n"
    "2024-03-30,1400.7,401.1\n"
)


class TestDiff:
    def test_the_change_from_the_previous_row_in_decimals(self) -> None:
        """`12.3 - 10.1` is 2.2, never the float noise 2.200000000000001."""
        prepared = prepare(
            "Monat,Stand\n2024-03-01,14.6\n2024-01-01,10.1\n2024-02-01,12.3\n", diff("d", "Stand", "Monat")
        )

        assert cells(prepared, 2) == ["2.3", "", "2.2"]
        assert prepared.changes == [
            "added column d: change of Stand from the previous Monat, 1 cell is empty (1 without a row before them)"
        ]

    def test_whole_numbers_stay_exact_past_float_precision(self) -> None:
        prepared = prepare("t,v\n1,9007199254740992\n2,9007199254740993\n", diff("d", "v", "t"))

        assert cells(prepared, 2) == ["", "1"]
        assert dtypes(prepared)["d"] == "integer"

    def test_a_lag_within_groups_in_the_order_given(self) -> None:
        text = "m,g,v\n3,a,30\n1,a,10\n2,b,7\n1,b,5\n2,a,20\n3,b,12\n"
        prepared = prepare(text, diff("d", "v", "m", within=["g"], lag=2))

        assert cells(prepared, 3) == ["20", "", "", "", "", "7"]
        assert prepared.changes == [
            "added column d: change of v from 2 rows before in the order of m within each g, "
            "4 cells are empty (4 without 2 rows before them)"
        ]

    def test_a_missing_value_and_a_row_without_an_order_are_counted(self) -> None:
        prepared = prepare("t,v\n1,10\n2,\n3,15\n,4\n4,20\n", diff("d", "v", "t"))

        assert cells(prepared, 2) == ["", "", "", "", "5"]
        assert prepared.changes[0].endswith(
            "4 cells are empty (1 without a row before them, 2 with a missing value, 1 without a t)"
        )

    def test_the_last_reading_per_month_then_its_change(self) -> None:
        """An aggregate's month labels are text that sorts in time order: the chain needs no set_type."""
        prepared = prepare(
            METER,
            {"op": "aggregate", "by": ["Datum"], "column": "Bezug", "how": "last", "period": "month"},
            diff("Verbrauch", "Bezug", "Datum"),
        )

        assert rows(prepared) == [
            "Datum,Bezug,Verbrauch",
            "2024-01,1180.4,",
            "2024-02,1290.6,110.2",
            "2024-03,1400.7,110.1",
        ]

    def test_a_percent_change_takes_the_month_labels_too(self) -> None:
        prepared = prepare(
            METER,
            {"op": "aggregate", "by": ["Datum"], "column": "Bezug", "how": "last", "period": "month"},
            derive("g", "percent_change", "Bezug", order="Datum"),
        )

        assert cells(prepared, 2)[0] == ""

    def test_month_names_and_repeated_orders_are_refused(self) -> None:
        months = "Monat,Umsatz\nJanuar,10\nFebruar,12\n"
        mixed = "p,v\n2024-01,1\n2024-Q2,2\n"

        assert failure(months, diff("d", "Umsatz", "Monat"))[0] == "type_mismatch"
        assert failure(mixed, diff("d", "v", "p"))[0] == "type_mismatch"  # one label shape throughout
        assert "aggregate first" in failure("t,v\n1,1\n1,2\n", diff("d", "v", "t"))[1]

    @pytest.mark.parametrize(
        ("operation", "code"),
        [
            (diff("d", "Tier", "Datum"), "type_mismatch"),
            (diff("d", "Umsatz", "Umsatz"), "invalid_operation"),
            (diff("d", "Umsatz", "Datum", within=["Umsatz"]), "invalid_operation"),
            (diff("Tier", "Umsatz", "Datum"), "invalid_operation"),
            (diff("d", "Umsatz", "Datum", lag=6), "invalid_operation"),
            (diff("d", "Nope", "Datum"), "unknown_column"),
        ],
    )
    def test_refusals(self, operation: dict[str, Any], code: str) -> None:
        sales = "Datum,Tier,Umsatz\n2024-01-05,Hund,1200.5\n2024-01-20,Katze,800\n"

        assert failure(sales, operation)[0] == code

    @pytest.mark.parametrize("lag", [0, -1, 20_001])
    def test_a_lag_out_of_range_fails_validation(self, lag: int) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([diff("d", "v", "t", lag=lag)])


class TestRolling:
    def test_a_mean_over_three_rows_adds_the_decimals_as_written(self) -> None:
        """0.1 + 0.2 + 0.3 is 0.6 and its mean 0.2, not 0.6000000000000001 / 3."""
        text = "t,v\n1,0.1\n2,0.2\n3,0.3\n4,0.4\n"
        mean = prepare(text, rolling("m", "v", "mean", 3, "t"))
        total = prepare(text, rolling("s", "v", "sum", 3, "t"))

        assert cells(mean, 2) == ["", "", "0.2", "0.3"]
        assert cells(total, 2) == ["", "", "0.6", "0.9"]
        assert mean.changes == [
            "added column m: mean of v over 3 rows in the order of t, 2 cells are empty (2 before a full window of 3 rows)"
        ]

    def test_a_whole_sum_stays_exact(self) -> None:
        prepared = prepare("t,v\n1,9007199254740993\n2,1\n", rolling("s", "v", "sum", 2, "t"))

        assert cells(prepared, 2) == ["", "9007199254740994"]
        assert dtypes(prepared)["s"] == "integer"

    def test_a_mean_past_2_53_that_a_float_rounds_is_counted(self) -> None:
        """Gemini on #12597: the exact mean of two large ids, 9007199254740993.5, is stored as ...994, never silently."""
        prepared = prepare("t,v\n1,9007199254740993\n2,9007199254740994\n", rolling("m", "v", "mean", 2, "t"))

        assert cells(prepared, 2) == ["", repr(float(9007199254740994))]
        assert "1 value past 2^53 is stored as decimal numbers" in prepared.changes[0]

    def test_a_window_with_a_missing_value_is_empty_and_counted(self) -> None:
        prepared = prepare("t,v\n1,1\n2,\n3,3\n4,4\n5,5\n", rolling("m", "v", "mean", 2, "t"))

        assert cells(prepared, 2) == ["", "", "", "3.5", "4.5"]
        assert prepared.changes[0].endswith(
            "3 cells are empty (1 before a full window of 2 rows, 2 with a missing value in the window)"
        )

    def test_within_groups_in_the_order_given(self) -> None:
        text = "m,g,v\n2,a,20\n1,a,10\n1,b,1\n3,a,30\n2,b,3\n"
        prepared = prepare(text, rolling("s", "v", "sum", 2, "m", within=["g"]))

        assert cells(prepared, 3) == ["30", "", "", "50", "4"]

    def test_a_window_longer_than_every_group_is_refused(self) -> None:
        assert failure("t,v\n1,1\n2,2\n", rolling("m", "v", "mean", 12, "t"))[0] == "invalid_operation"

    @pytest.mark.parametrize(
        "operation",
        [
            rolling("m", "v", "mean", 1, "t"),
            rolling("m", "v", "median", 3, "t"),
            {k: v for k, v in rolling("m", "v", "mean", 3, "t").items() if k != "order"},
            {**rolling("m", "v", "mean", 3, "t"), "days": 7},
        ],
    )
    def test_malformed_rolling_fails_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])


class TestBlank:
    def test_missing_codes_are_emptied_and_the_rows_stay(self) -> None:
        text = "station,u\nA,-0.99\nB,1.5\nC,-1\nD,2\nE,\n"
        prepared = prepare(text, blank(["u"], any_of("u", "eq", -0.99, -1)))

        assert rows(prepared) == ["station,u", "A,", "B,1.5", "C,", "D,2", "E,"]
        assert prepared.changes == ["emptied 2 cells of u where u is -0.99 or -1; the rows stay"]
        assert dtypes(prepared)["u"] == "number"

    def test_several_columns_by_a_condition_on_another_count_per_column(self) -> None:
        text = "flag,a,b\nbad,1,\nok,2,3\nbad,4,5\n"
        prepared = prepare(text, blank(["a", "b"], {"column": "flag", "test": "eq", "value": "bad"}))

        assert rows(prepared) == ["flag,a,b", "bad,,", "ok,2,3", "bad,,"]
        assert prepared.changes == ["emptied 3 cells (2 of a, 1 of b) where flag = 'bad'; the rows stay"]
        assert dtypes(prepared)["a"] == "integer"

    def test_text_and_boolean_cells_are_emptied_too(self) -> None:
        text = "k,note,ok\na,n/v,true\nb,fine,false\n"
        prepared = prepare(text, blank(["note", "ok"], any_of("note", "contains", "n/v", "n.a.")))

        assert rows(prepared) == ["k,note,ok", "a,,", "b,fine,False"]

    def test_a_column_that_would_lose_every_value_is_refused(self) -> None:
        code, message = failure("u\n-1\n-1\n", blank(["u"], {"column": "u", "test": "eq", "value": -1}))

        assert code == "invalid_operation" and "drop_columns" in message

    def test_nothing_is_filled_and_an_empty_cell_counts_nothing(self) -> None:
        prepared = prepare("k,u\na,1\nb,\nc,3\n", blank(["u"], {"column": "u", "test": "is_missing"}))

        assert cells(prepared, 1) == ["1", "", "3"]
        assert prepared.changes == ["emptied 0 cells of u where u is missing; the rows stay"]

    def test_a_blanked_cell_never_comes_back_from_the_paste(self) -> None:
        """A re-reading of the pasted cells (`set_type` with a decimal comma) would restore what `blank` emptied, so
        after a `blank` the column has no pasted cells and the re-reading is refused; read first, it works."""
        parsed = parse_dataset("k;v\na;1.234\nb;-99\n")
        emptied = blank(["v"], {"column": "v", "test": "eq", "value": -99})
        reading = {"op": "set_type", "column": "v", "type": "number", "decimal": ","}

        with pytest.raises(PrepareError) as raised:
            apply_operations(parsed, OPERATIONS.validate_python([emptied, reading]))
        assert raised.value.code == "type_mismatch"

        prepared = apply_operations(parsed, OPERATIONS.validate_python([reading, emptied]))
        assert cells(prepared, 1) == ["1234", ""]

    @pytest.mark.parametrize(
        "operation",
        [
            {"op": "blank", "columns": [], "where": [{"column": "u", "test": "is_missing"}]},
            {"op": "blank", "columns": ["u"], "where": []},
            {"op": "blank", "columns": ["u"], "where": [{"column": "u", "test": "is_missing"}], "fill": "0"},
        ],
    )
    def test_malformed_blank_fails_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])


# Bank statement lines with a free-text purpose and a booked category.
STATEMENT = (
    "Zweck,Kategorie,Betrag\n"
    "Miete Mai,Miete,-900\n"
    "Stadtwerke,Strom,-80\n"
    "REWE Markt,Lebensmittel,-54.2\n"
    "EDEKA,Lebensmittel,-31.5\n"
    "Spende,Spenden,-20\n"
    "Spende,Spenden,-30\n"
    "Kontoführung,Bank,-5\n"
)


class TestAnyOf:
    def test_several_values_into_one_label(self) -> None:
        prepared = prepare(
            STATEMENT,
            classify(
                "Gruppe",
                ([any_of("Kategorie", "eq", "Miete", "Strom")], "Wohnen"),
                ([any_of("Zweck", "contains", "REWE", "EDEKA")], "Essen"),
                otherwise="Sonstiges",
            ),
        )

        assert cells(prepared, 3) == ["Wohnen", "Wohnen", "Essen", "Essen", "Sonstiges", "Sonstiges", "Sonstiges"]
        assert prepared.changes[0].startswith(
            "added column Gruppe: 'Wohnen' for 2 rows where Kategorie is 'Miete' or 'Strom', "
            "'Essen' for 2 rows where Zweck contains 'REWE' or 'EDEKA'"
        )

    def test_drop_rows_takes_the_list_too(self) -> None:
        prepared = prepare(STATEMENT, {"op": "drop_rows", "where": [any_of("Kategorie", "eq", "Bank", "Spenden")]})

        assert len(rows(prepared)) == 5
        assert prepared.changes == ["dropped 3 rows where Kategorie is 'Bank' or 'Spenden'"]

    def test_a_long_list_shows_three_values_and_how_many_more(self) -> None:
        values = [f"v{i}" for i in range(6)]
        prepared = prepare("k\nv1\nx\n", {"op": "drop_rows", "where": [any_of("k", "eq", *values)]})

        assert prepared.changes == ["dropped 1 row where k is 'v0', 'v1', 'v2' or 3 more"]

    @pytest.mark.parametrize(
        ("condition", "words"),
        [
            ({**any_of("Betrag", "gt", 1, 2)}, "takes the test eq or contains, not gt"),
            ({**any_of("Betrag", "eq", 1, 2), "value": "1"}, "value or values, not both"),
            (any_of("Betrag", "eq", "abc"), "is not a number"),
        ],
    )
    def test_refusals(self, condition: dict[str, Any], words: str) -> None:
        code, message = failure(STATEMENT, {"op": "drop_rows", "where": [condition]})

        assert code == "invalid_operation" and words in message

    @pytest.mark.parametrize("values", [[], [str(i) for i in range(MAX_ANY_VALUES + 1)]])
    def test_an_empty_or_too_long_list_fails_validation(self, values: list[str]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python(
                [{"op": "drop_rows", "where": [{"column": "k", "test": "eq", "values": values}]}]
            )


class TestClassifyFallback:
    def test_the_fallback_names_its_largest_groups_by_the_text_column(self) -> None:
        """The persona's "Sonstiges" took two categories silently: the line now says which."""
        prepared = prepare(
            STATEMENT,
            classify(
                "Gruppe", ([any_of("Kategorie", "eq", "Miete", "Strom", "Lebensmittel")], "Fix"), otherwise="Sonstiges"
            ),
        )

        assert prepared.changes[0].endswith(
            "'Sonstiges' for the other 3 rows, the largest by Kategorie: 'Spenden' 2, 'Bank' 1"
        )

    def test_rows_without_a_label_name_their_groups_too(self) -> None:
        prepared = prepare(STATEMENT, classify("Gruppe", ([any_of("Kategorie", "eq", "Miete")], "Fix")))

        assert prepared.changes[0].endswith(
            "6 rows without a label, the largest by Kategorie: 'Lebensmittel' 2, 'Spenden' 2, 'Strom' 1"
        )

    def test_a_number_column_tested_as_often_never_hides_the_text_groups(self) -> None:
        """Gemini on #12597: one rule on Betrag and one on Kategorie; the groups are still named by Kategorie."""
        prepared = prepare(
            STATEMENT,
            classify(
                "k",
                ([{"column": "Betrag", "test": "lt", "value": -500}], "big"),
                ([any_of("Kategorie", "eq", "Lebensmittel")], "food"),
                otherwise="Rest",
            ),
        )

        assert prepared.changes[0].endswith(
            "'Rest' for the other 4 rows, the largest by Kategorie: 'Spenden' 2, 'Strom' 1, 'Bank' 1"
        )

    def test_a_threshold_on_numbers_names_no_groups(self) -> None:
        prepared = prepare(
            STATEMENT, classify("k", ([{"column": "Betrag", "test": "lt", "value": -50}], "big"), otherwise="small")
        )

        assert prepared.changes[0].endswith("'small' for the other 4 rows")

    def test_the_fallback_survives_a_long_line(self) -> None:
        rules = [([any_of("Kategorie", "eq", f"{'x' * 30}{i}", "y" * 40)], f"L{i}") for i in range(6)]
        prepared = prepare(STATEMENT, classify("k", *rules, otherwise="Rest"))

        assert len(prepared.changes[0]) <= MAX_NOTE_CHARS
        assert prepared.changes[0].endswith(
            "'Rest' for the other 7 rows, the largest by Kategorie: 'Lebensmittel' 2, 'Spenden' 2, 'Miete' 1"
        )


class TestAggregateSeveral:
    def test_the_last_readings_of_each_month_by_time(self) -> None:
        prepared = prepare(
            METER,
            {"op": "aggregate", "by": ["Datum"], "columns": ["Bezug", "Einspeisung"], "how": "last", "period": "month"},
        )

        # February's latest Einspeisung is missing: its last value that is there is the one before.
        assert rows(prepared) == [
            "Datum,Bezug,Einspeisung",
            "2024-01,1180.4,310.2",
            "2024-02,1290.6,355.8",
            "2024-03,1400.7,401.1",
        ]
        assert prepared.changes == ["took the last value (by time) of Bezug and Einspeisung by Datum (month): 3 rows"]

    def test_two_date_keys_order_by_the_first_then_the_second_and_keep_ties_in_row_order(self) -> None:
        """Two stable passes: the first key decides, the second breaks its ties, and equal moments keep their rows."""
        text = (
            "Start,Ende,v\n"
            "2024-01-10,2024-02-05,1\n"
            "2024-01-10,2024-02-01,2\n"
            "2024-01-05,2024-02-20,3\n"
            "2024-01-10,2024-02-05,4\n"
            "2024-03-01,2024-03-02,5\n"
        )
        operation = {"op": "aggregate", "by": ["Start", "Ende"], "column": "v", "period": "month"}

        last = prepare(text, {**operation, "how": "last"})
        first = prepare(text, {**operation, "how": "first"})

        assert rows(last) == ["Start,Ende,v", "2024-01,2024-02,4", "2024-03,2024-03,5"]
        assert rows(first) == ["Start,Ende,v", "2024-01,2024-02,3", "2024-03,2024-03,5"]

    def test_the_first_value_in_row_order_without_a_date_key(self) -> None:
        prepared = prepare(
            "g,v,w\na,3,x\nb,1,y\na,2,z\n", {"op": "aggregate", "by": ["g"], "columns": ["v", "w"], "how": "first"}
        )

        assert rows(prepared) == ["g,v,w", "a,3,x", "b,1,y"]
        assert prepared.changes == ["took the first value (in row order) of v and w by g: 2 rows"]

    def test_a_date_key_without_a_period_takes_the_row_order(self) -> None:
        """Every row of a group has the same moment then, so the line says the rows' order decided (Gemini, #12597)."""
        prepared = prepare(
            "Tag,v\n2024-01-02,5\n2024-01-01,1\n2024-01-02,7\n",
            {"op": "aggregate", "by": ["Tag"], "column": "v", "how": "last"},
        )

        assert rows(prepared) == ["Tag,v", "2024-01-01,1", "2024-01-02,7"]
        assert prepared.changes == ["took the last value (in row order) of v by Tag: 2 rows"]

    def test_a_sum_of_several_whole_columns_stays_exact(self) -> None:
        prepared = prepare(
            "g,a,b\nx,9007199254740993,1\nx,1,2.5\ny,4,1\n",
            {"op": "aggregate", "by": ["g"], "columns": ["a", "b"], "how": "sum"},
        )

        assert rows(prepared) == ["g,a,b", "x,9007199254740994,3.5", "y,4,1"]

    def test_one_column_in_a_list_is_the_one_value_column(self) -> None:
        model = Aggregate.model_validate({"op": "aggregate", "by": ["g"], "columns": ["v"], "how": "max"})

        assert (model.column, model.columns) == ("v", None)

    def test_count_takes_one_column(self) -> None:
        operation = {"op": "aggregate", "by": ["g"], "columns": ["v", "w"], "how": "count"}

        assert failure("g,v,w\na,1,2\n", operation)[0] == "invalid_operation"

    @pytest.mark.parametrize(
        "operation",
        [
            {"op": "aggregate", "by": ["g"], "how": "sum"},
            {"op": "aggregate", "by": ["g"], "column": "v", "columns": ["v", "w"], "how": "sum"},
            {"op": "aggregate", "by": ["g"], "columns": [f"c{i}" for i in range(11)], "how": "sum"},
            {"op": "aggregate", "by": ["g"], "column": "v", "how": "median"},
            {"op": "aggregate", "by": ["g"], "columns": ["v", "v"], "how": "sum"},
        ],
    )
    def test_malformed_aggregate_fails_validation(self, operation: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([operation])


class TestKeepRows:
    def test_the_top_n_after_a_sort(self) -> None:
        """The owner's top N of 2026-11-07: revenue computed, sorted and its top 2 kept, counted."""
        text = "Product,Quantity,Price\nTea,12,3.5\nCake,4,12\nJam,30,2.25\nHoney,7,8.4\n"
        prepared = prepare(
            text,
            compute("Revenue", "q * p", q="Quantity", p="Price"),
            {"op": "sort", "column": "Revenue", "descending": True},
            {"op": "keep_rows", "n": 2},
        )

        assert rows(prepared) == ["Product,Quantity,Price,Revenue", "Jam,30,2.25,67.5", "Honey,7,8.4,58.8"]
        assert prepared.changes[2] == "kept the first 2 of 4 rows, 2 dropped"

    def test_a_table_no_longer_than_n_keeps_every_row(self) -> None:
        prepared = prepare("k,v\na,1\nb,2\nc,3\n", {"op": "keep_rows", "n": 10})

        assert len(rows(prepared)) == 4
        assert prepared.changes == ["kept all 3 rows; there were no more than 10"]

    def test_the_pasted_cells_are_no_longer_the_rows(self) -> None:
        """A decimal comma read again from the paste needs the rows as pasted, which `keep_rows` changed."""
        operations = [{"op": "keep_rows", "n": 1}, {"op": "set_type", "column": "v", "type": "number", "decimal": ","}]
        parsed = parse_dataset("k;v\na;1.234\nb;7.000\n")

        with pytest.raises(PrepareError) as caught:
            apply_operations(parsed, OPERATIONS.validate_python(operations))

        assert caught.value.code == "type_mismatch"

    @pytest.mark.parametrize("n", [0, -1, 20_001, "ten"])
    def test_a_count_out_of_range_fails_validation(self, n: object) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([{"op": "keep_rows", "n": n}])


class TestUnsupported:
    def test_a_gap_refuses_the_whole_call_before_anything_runs(self) -> None:
        with pytest.raises(PrepareError) as caught:
            prepare(STATEMENT, drop("Kategorie", "eq", "Bank"), {"op": "unsupported", "family": "fill_values"})

        assert caught.value.code == "unsupported_operation"
        assert caught.value.message == "no operation can fill in, interpolate or invent values"

    def test_an_unknown_family_fails_validation(self) -> None:
        with pytest.raises(ValidationError):
            OPERATIONS.validate_python([{"op": "unsupported", "family": "excel"}])

    def test_the_cap_of_five_operations_holds_for_the_new_ones(self) -> None:
        operations = [compute(f"c{i}", "a + 1", a="Betrag") for i in range(MAX_OPERATIONS + 1)]

        assert failure(STATEMENT, *operations)[0] == "invalid_operation"


def test_the_new_columns_round_trip_as_canonical_csv() -> None:
    prepared = prepare(
        METER,
        compute("Netto", "b - x", b="Bezug", x="Einspeisung"),
        diff("Zuwachs", "Bezug", "Datum"),
        rolling("Mittel", "Bezug", "mean", 2, "Datum"),
        blank(["Einspeisung"], {"column": "Einspeisung", "test": "gt", "value": 400}),
    )
    again = reparse(prepared)

    assert again.csv == prepared.csv
    assert again.column_dtypes["Netto"] == again.column_dtypes["Zuwachs"] == "number"
