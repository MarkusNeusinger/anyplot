"""Tests for agents/anyplot/data/generate.py: the spec models, the whitelist evaluator, the table, the formula guard."""

import ast
import csv
import io
import math
import random
from typing import Any

import pytest
from pydantic import ValidationError

from agents.anyplot.data.generate import (
    BINARY_FUNCTIONS,
    CONSTANTS,
    MAX_EXPRESSION_CHARS,
    MAX_GRID_ROWS,
    MAX_POINTS,
    MAX_SERIES,
    UNARY_FUNCTIONS,
    Generate,
    Generated,
    GenerateError,
    generate,
    looks_like_formula,
    parse_expression,
)
from agents.anyplot.data.parse import MAX_INPUT_BYTES, parse_dataset
from agents.anyplot.schemas import MAX_NOTE_CHARS


def spec(*series: tuple[str, str], variables: list[dict[str, Any]] | None = None) -> Generate:
    """A spec over `x` from -pi to pi (200 points) unless `variables` says otherwise."""
    return Generate.model_validate(
        {
            "variables": variables or [{"start": "-pi", "stop": "pi"}],
            "series": [{"name": name, "expression": expression} for name, expression in series],
        }
    )


def table(generated: Generated) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(generated.csv)))


def numbers(rows: list[dict[str, str]], column: str) -> list[float | None]:
    return [float(row[column]) if row[column] else None for row in rows]


def code_of(expression: str) -> GenerateError:
    with pytest.raises(GenerateError) as caught:
        generate(spec(("y", expression)))
    return caught.value


class TestTables:
    def test_sine_from_minus_pi_to_pi(self) -> None:
        generated = generate(spec(("y", "sin(x)")))
        rows = table(generated)

        assert len(rows) == 200 and list(rows[0]) == ["x", "y"]
        assert rows[0]["x"] == "-3.1415927" and rows[-1]["x"] == "3.1415927"  # both ends, 8 significant digits
        ys = numbers(rows, "y")
        assert all(value is not None and -1 <= value <= 1 for value in ys)
        assert max(value for value in ys if value is not None) == pytest.approx(1, abs=1e-3)
        assert generated.changes == ["generated 200 rows: x from -3.1416 to 3.1416, y = sin(x)"]
        assert generated.warnings == []

    def test_a_parabola_with_its_points(self) -> None:
        generated = generate(spec(("y", "x**2"), variables=[{"start": -3, "stop": 3, "points": 7}]))
        rows = table(generated)

        assert [row["x"] for row in rows] == ["-3.0", "-2.0", "-1.0", "0.0", "1.0", "2.0", "3.0"]
        assert [row["y"] for row in rows] == ["9.0", "4.0", "1.0", "0.0", "1.0", "4.0", "9.0"]
        assert generated.changes == ["generated 7 rows: x from -3 to 3, y = x**2"]

    def test_a_parametric_circle(self) -> None:
        generated = generate(
            spec(("x", "cos(t)"), ("y", "sin(t)"), variables=[{"name": "t", "start": "0", "stop": "2*pi"}])
        )
        rows = table(generated)

        assert list(rows[0]) == ["t", "x", "y"] and len(rows) == 200
        for row in rows:
            assert float(row["x"]) ** 2 + float(row["y"]) ** 2 == pytest.approx(1, abs=1e-6)
        assert generated.changes == ["generated 200 rows: t from 0 to 6.2832, x = cos(t), y = sin(t)"]

    def test_a_grid_with_the_first_variable_slowest(self) -> None:
        variables = [
            {"name": "x", "start": "-2", "stop": "2", "points": 30},
            {"name": "y", "start": -2, "stop": 2, "points": 30},
        ]
        generated = generate(spec(("z", "sin(x)*cos(y)"), variables=variables))
        rows = table(generated)

        assert len(rows) == 900 and list(rows[0]) == ["x", "y", "z"]
        assert [row["x"] for row in rows[:30]] == ["-2.0"] * 30  # x holds while y runs
        assert rows[0]["y"] == "-2.0" and rows[29]["y"] == "2.0" and rows[30]["x"] != "-2.0"
        for row in rows[::97]:
            expected = math.sin(float(row["x"])) * math.cos(float(row["y"]))
            assert float(row["z"]) == pytest.approx(expected, rel=1e-6, abs=1e-7)
        assert generated.changes == [
            "generated 900 rows: x from -2 to 2 (30 points) and y from -2 to 2 (30 points), z = sin(x)*cos(y)"
        ]

    def test_the_constants(self) -> None:
        generated = generate(spec(("a", "pi"), ("b", "e"), ("c", "tau"), variables=[{"start": "0", "stop": "1"}]))
        row = table(generated)[0]

        assert (row["a"], row["b"], row["c"]) == ("3.1415927", "2.7182818", "6.2831853")
        assert CONSTANTS == {"pi": math.pi, "e": math.e, "tau": math.tau}

    def test_a_descending_range(self) -> None:
        rows = table(generate(spec(("y", "2*x"), variables=[{"start": "pi", "stop": "-pi", "points": 3}])))

        assert [row["x"] for row in rows] == ["3.1415927", "0.0", "-3.1415927"]
        assert [row["y"] for row in rows] == ["6.2831853", "0.0", "-6.2831853"]

    def test_a_series_without_a_variable_is_constant(self) -> None:
        rows = table(generate(spec(("y", "2 + 3"), variables=[{"start": "0", "stop": "1", "points": 2}])))

        assert [row["y"] for row in rows] == ["5.0", "5.0"]

    def test_every_value_has_eight_significant_digits_and_no_negative_zero(self) -> None:
        rows = table(generate(spec(("y", "x/3"), ("z", "-0*x"), variables=[{"start": "-1", "stop": "1", "points": 3}])))

        assert [row["y"] for row in rows] == ["-0.33333333", "0.0", "0.33333333"]
        assert [row["z"] for row in rows] == ["0.0", "0.0", "0.0"]


class TestUndefinedValues:
    def test_log_of_negatives_leaves_cells_empty_with_a_warning(self) -> None:
        generated = generate(spec(("y", "log(x)"), variables=[{"start": "-1", "stop": "1", "points": 5}]))

        assert numbers(table(generated), "y") == [None, None, None, pytest.approx(math.log(0.5)), 0.0]
        assert generated.warnings == ["y: 3 of 5 values are undefined and left empty"]

    def test_one_over_x_at_zero_is_one_missing_cell(self) -> None:
        generated = generate(spec(("y", "1/x"), variables=[{"start": "-1", "stop": "1", "points": 3}]))

        assert numbers(table(generated), "y") == [-1.0, None, 1.0]
        assert generated.warnings == ["y: 1 of 3 values is undefined and left empty"]

    def test_an_overflow_is_missing_never_an_exception(self) -> None:
        """Python would raise `OverflowError` for `10.0**400`; float64 under `errstate` gives inf, a missing cell."""
        generated = generate(
            spec(("a", "exp(1000*x)"), ("b", "x**400*10"), variables=[{"start": "0", "stop": "10", "points": 2}])
        )
        rows = table(generated)

        assert numbers(rows, "a") == [1.0, None]  # exp(10000) is inf
        assert numbers(rows, "b") == [0.0, None]  # 10**400 is inf
        assert generated.warnings == [
            "a: 1 of 2 values is undefined and left empty",
            "b: 1 of 2 values is undefined and left empty",
        ]
        assert code_of("10**400").code == "undefined"  # every value inf: refused, but as a GenerateError

    def test_a_series_without_any_defined_value_is_refused(self) -> None:
        error = code_of("sqrt(-1 - x**2)")

        assert error.code == "undefined" and error.message.startswith("y: no value is defined")

    def test_a_long_integer_literal_is_a_float_never_a_python_big_int(self) -> None:
        literal = "9" * 190
        rows = table(generate(spec(("y", f"{literal}*x*0+1"), variables=[{"start": "0", "stop": "1", "points": 2}])))

        assert numbers(rows, "y") == [1.0, 1.0]


class TestForbiddenConstructs:
    @pytest.mark.parametrize(
        ("expression", "named"),
        [
            ("__import__('os')", "unknown function '__import__'"),
            ("x.__class__", "attributes"),
            ("x[0]", "indexing"),
            ("'a'", "strings are not allowed"),
            ("1 if x else 2", "conditional expressions"),
            ("lambda: 0", "lambda is not allowed"),
            ("(x for x in y)", "comprehensions are not allowed"),
            ("[x for x in y]", "comprehensions are not allowed"),
            ("f(x=1)", "keyword arguments"),
            ("sin(x=1)", "keyword arguments"),
            ("x ^ 2", "'^' is not a power; write x**2"),
            ("2x", "'2x' needs an operator: write 2*x"),
            ("2pi", "'2pi' needs an operator: write 2*pi"),
            ("x²", "write x**2"),
            ("x > 0", "comparisons"),
            ("x and 1", "'and' and 'or'"),
            ("not x", "'not' is not allowed"),
            ("~x", "'~' is not allowed"),
            ("x & 1", "'&' is not allowed"),
            ("x @ x", "'@' is not allowed"),
            ("(x := 1)", "':=' is not allowed"),
            ("[x, 1]", "lists, tuples, sets and dicts"),
            ("(x, 1)", "lists, tuples, sets and dicts"),
            ("{x: 1}", "lists, tuples, sets and dicts"),
            ("f'{x}'", "strings are not allowed"),
            ("1j", "complex numbers"),
            ("True", "True, False, None"),
            ("None", "True, False, None"),
            ("sin(*x)", "starred arguments"),
            ("sin", "'sin' is a function; write sin(x)"),
            ("sin(x, 1)", "sin takes 1 argument"),
            ("atan2(x)", "atan2 takes 2 arguments"),
            ("q + 1", "unknown name 'q'"),
            ("sin(π)", "write pi for π"),
            ("foo(x)", "unknown function 'foo'"),
            ("x(1 + x)", "'x(' needs an operator"),
            ("2(1 + x)", "a number before '(' needs an operator"),
            ("x.real(1)", "attributes"),
            ("x +", "the expression cannot be read"),
        ],
    )
    def test_is_invalid_and_named(self, expression: str, named: str) -> None:
        error = code_of(expression)

        assert error.code == "invalid_expression"
        assert error.message.startswith("y: ") and named in error.message, error.message

    def test_the_hint_lists_the_allowed_constructs(self) -> None:
        message = code_of("True").message

        assert "names, numbers, + - * / ** % //, parentheses and the functions sin, cos" in message
        assert message.endswith("atan2, min, max only")

    def test_more_than_a_hundred_nodes_is_refused(self) -> None:
        bomb = "+".join(["x"] * 60)
        assert len(bomb) <= MAX_EXPRESSION_CHARS

        error = code_of(bomb)

        assert error.code == "invalid_expression" and "more than 100 parts" in error.message

    def test_deep_nesting_is_bounded_without_a_crash(self) -> None:
        parentheses = "(" * 99 + "x" + ")" * 99  # one node: allowed
        assert len(table(generate(spec(("y", parentheses))))) == 200
        assert "more than 100 parts" in code_of("-" * 199 + "x").message  # 200 nodes
        assert "cannot be read" in code_of("(" * 200).message  # the parser's own nesting limit, a SyntaxError

    def test_endpoints_take_constants_only(self) -> None:
        for start, message in (
            ("x", "x.start: start and stop take numbers and the constants pi, e, tau only"),
            ("'1'", "x.start: strings are not allowed"),
        ):
            with pytest.raises(GenerateError) as caught:
                generate(spec(("y", "x"), variables=[{"start": start, "stop": "1"}]))
            assert caught.value.code == "invalid_expression" and caught.value.message.startswith(message)
        rows = table(generate(spec(("y", "x"), variables=[{"start": "sin(pi/2)", "stop": "-2*pi", "points": 2}])))
        assert [row["x"] for row in rows] == ["1.0", "-6.2831853"]

    @pytest.mark.parametrize(
        ("start", "stop", "message"),
        [
            ("1", "1", "x: start and stop are the same value"),
            ("pi", "3.14159265358979311599796346854", "x: start and stop are the same value"),
            ("1e999", "1", "x.start: the value is not a finite number"),
            ("log(0)", "1", "x.start: the value is not a finite number"),
            ("-1e308", "1e308", "x: the range is wider than a number can hold"),
        ],
    )
    def test_invalid_ranges(self, start: str, stop: str, message: str) -> None:
        with pytest.raises(GenerateError) as caught:
            generate(spec(("y", "x"), variables=[{"start": start, "stop": stop}]))

        assert (caught.value.code, caught.value.message) == ("invalid_range", message)


class TestLimits:
    def test_too_many_points_in_a_grid(self) -> None:
        variables = [
            {"name": "x", "start": "0", "stop": "1", "points": 101},
            {"name": "y", "start": "0", "stop": "1", "points": 100},
        ]
        with pytest.raises(GenerateError) as caught:
            generate(spec(("z", "x*y"), variables=variables))

        assert caught.value.code == "too_many_points"
        assert (
            caught.value.message == "a grid of 101 x 100 points has 10,100 rows; at most 10,000 fit, use fewer points"
        )
        # 10,000 rows fit when the cells are short (whole numbers here); eight-digit cells hit the 200 KB cap first.
        whole = [{"name": name, "start": "0", "stop": "99", "points": 100} for name in ("x", "y")]
        assert len(table(generate(spec(("z", "x - y"), variables=whole)))) == MAX_GRID_ROWS
        with pytest.raises(GenerateError) as caught:
            generate(spec(("z", "x*y"), variables=[{**item, "stop": "1"} for item in whole]))
        assert caught.value.code == "too_large"

    def test_too_large_a_table(self) -> None:
        variables = [
            {"name": "x", "start": "0", "stop": "1", "points": 100},
            {"name": "y", "start": "0", "stop": "1", "points": 100},
        ]
        series = [(f"s{index}", f"sin(x*{index + 1.123})*cos(y)") for index in range(MAX_SERIES)]
        with pytest.raises(GenerateError) as caught:
            generate(spec(*series, variables=variables))

        assert caught.value.code == "too_large"
        kilobytes = MAX_INPUT_BYTES // 1024
        assert (
            caught.value.message == f"the table would be larger than {kilobytes} KB; use fewer points or fewer series"
        )

    def test_the_models_bound_every_field(self) -> None:
        good = {"variables": [{"start": "0", "stop": "1"}], "series": [{"name": "y", "expression": "x"}]}
        assert Generate.model_validate(good).variables[0].points == 200
        for bad in (
            {**good, "variables": []},
            {**good, "variables": [good["variables"][0]] * 3},
            {**good, "series": []},
            {**good, "series": [{"name": f"s{index}", "expression": "x"} for index in range(MAX_SERIES + 1)]},
            {**good, "variables": [{"start": "0", "stop": "1", "points": 1}]},
            {**good, "variables": [{"start": "0", "stop": "1", "points": MAX_POINTS + 1}]},
            {**good, "series": [{"name": "y", "expression": "x" * (MAX_EXPRESSION_CHARS + 1)}]},
            {**good, "series": [{"name": "y", "expression": ""}]},
            {**good, "series": [{"name": "x", "expression": "x"}]},  # a series named like a variable
            {**good, "series": [{"name": "y", "expression": "x"}] * 2},
            {**good, "series": [{"name": " y", "expression": "x"}]},  # surrounding whitespace in a name
            {**good, "variables": [{"name": "sin", "start": "0", "stop": "1"}]},
            {**good, "variables": [{"name": "pi", "start": "0", "stop": "1"}]},
            {**good, "variables": [{"name": "lambda", "start": "0", "stop": "1"}]},
            {**good, "variables": [{"name": "Zeit (s)", "start": "0", "stop": "1"}]},
            {**good, "extra": 1},
            {**good, "series": [{"name": "y", "expression": "x", "unit": "m"}]},
        ):
            with pytest.raises(ValidationError):
                Generate.model_validate(bad)


class TestRoundTrip:
    def test_the_table_reparses_as_numbers_and_round_trips(self) -> None:
        generated = generate(spec(("y", "sin(x)"), ("w", "log(x)")))
        parsed = parse_dataset(generated.csv)

        assert parsed.column_dtypes == {"x": "number", "y": "number", "w": "number"}
        assert parsed.csv == generated.csv
        assert parsed.profile.rows == 200 and parsed.profile.columns[2].missing == 100
        assert len(generated.csv.encode("utf-8")) <= MAX_INPUT_BYTES

    def test_the_change_line_is_capped(self) -> None:
        long = "+".join(["x"] * 45)
        series = [(f"s{index}", long) for index in range(MAX_SERIES)]
        (line,) = generate(spec(*series, variables=[{"start": "0", "stop": "1", "points": 2}])).changes

        assert len(line) == MAX_NOTE_CHARS and line.endswith("…")


def _random_expression(rng: random.Random, depth: int = 0) -> str:
    """One expression of the grammar: numbers, x, the constants, unary minus, the operators and every function."""
    if depth > 3 or rng.random() < 0.3:
        return rng.choice(["x", "pi", "e", "tau", str(rng.randint(-5, 5)), f"{rng.uniform(-9, 9):.3f}", "0"])
    kind = rng.choice(["unary", "binary", "call1", "call2", "paren"])
    if kind == "unary":
        return f"-{_random_expression(rng, depth + 1)}"
    if kind == "binary":
        operator = rng.choice(["+", "-", "*", "/", "**", "%", "//"])
        return f"{_random_expression(rng, depth + 1)} {operator} {_random_expression(rng, depth + 1)}"
    if kind == "call1":
        return f"{rng.choice(sorted(UNARY_FUNCTIONS))}({_random_expression(rng, depth + 1)})"
    if kind == "call2":
        arguments = f"{_random_expression(rng, depth + 1)}, {_random_expression(rng, depth + 1)}"
        return f"{rng.choice(sorted(BINARY_FUNCTIONS))}({arguments})"
    return f"({_random_expression(rng, depth + 1)})"


def test_random_valid_expressions_raise_nothing_but_generate_errors() -> None:
    """Property check: for 50 expressions of the grammar the evaluator either computes or answers `GenerateError`."""
    rng = random.Random(20261011)
    computed = 0
    for _ in range(50):
        expression = _random_expression(rng)[:MAX_EXPRESSION_CHARS]
        try:
            generated = generate(spec(("y", expression), variables=[{"start": "-3", "stop": "3", "points": 50}]))
        except GenerateError as exc:
            assert exc.code in ("invalid_expression", "undefined"), (expression, exc.code)
            continue
        computed += 1
        assert parse_dataset(generated.csv).profile.rows == 50
    assert computed >= 25  # most of them are defined somewhere on the range


class TestParseExpression:
    def test_returns_the_checked_tree(self) -> None:
        tree = parse_expression("sin(x) * 2", frozenset({"x"}), "y")

        assert isinstance(tree, ast.BinOp) and isinstance(tree.left, ast.Call)

    def test_any_name_passes_without_known_variables(self) -> None:
        assert isinstance(parse_expression("price * qty", None, "rhs"), ast.BinOp)
        with pytest.raises(GenerateError):
            parse_expression("sin + 1", None, "rhs")


class TestLooksLikeFormula:
    @pytest.mark.parametrize(
        "text",
        [
            "zeichne sin(x) von -pi bis pi",
            "Sin(x) from 0 to 2pi",
            "exp(-t) von 0 bis 5",
            "y = x**2",
            "y = x^2 from -3 to 3",
            "f(x) = 2x + 1",
            "y = x",
            "y = (x+1)**2",
            "y = x² von -2 bis 2",
            "sin x von -pi bis pi",
            "x squared from -3 to 3",
            "plot the parabola from -3 to 3",
            "eine Parabel von -3 bis 3",
            "Normalverteilung von -3 bis 3",
            "a circle: x = cos(t), y = sin(t) for t from 0 to 2 pi",
            "z = sin(x)*cos(y) for x and y from -2 to 2, 30 points each",
            "y = sin(x)\nx von -pi bis pi",
        ],
    )
    def test_formulas(self, text: str) -> None:
        assert looks_like_formula(text)

    @pytest.mark.parametrize(
        "text",
        [
            "Hund 7 Katze 3 und Vogel 4",
            "Milch 2\nEier 10\nBrot 1",
            "Milch 2\nEier 10\nBrot 1\nButter 1\nKäse 3",
            "Umsatz from Monday to Friday",
            "Umsatz von Montag bis Freitag",
            'cat_day = {"Mo": 3, "Di": 5}',
            'cat_day = {"Mo": 3, "Di": }',
            "Umsatz von 2020 bis 2024: 10 12 15 18 20",
            "Temperatur von -5 bis 30 Grad: Mo 3, Di 5",
            "Laufzeit von 10 bis 30 min: Mo 12 Di 15",
            "T-Shirts von 10 bis 20 Stück",
            "Tier = Hund\nAnzahl = 7",
            "x = 1, 2, 3, 4",
            "what is a bar chart?",
            "Alice, Bob und Carol",
            "a,b\n1,2,3,4",
            "x,y\nsin(1),2,3",
            "value\n1\n2\n3\nsin(4)",
            "",
            "sin(x) " + "a" * 300,
        ],
    )
    def test_not_formulas(self, text: str) -> None:
        assert not looks_like_formula(text)
