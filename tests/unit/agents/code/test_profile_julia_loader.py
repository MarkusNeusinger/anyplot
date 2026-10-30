"""Tests for agents/anyplot/code/profiles/julia/loader.py and the Julia counts of agents/anyplot/data/kinds.py.

What Julia reads from the generated statement is measured in the J1 image by test_profile_julia_image.py (skipped
without Docker and the image); these tests pin the statement's text and shape.
"""

import pytest

from agents.anyplot.code.profiles.julia.loader import (
    JULIA_TYPES,
    julia_literal,
    loader_span,
    loader_statement,
    to_run_form,
)
from agents.anyplot.code.profiles.julia.validate import validate_security
from agents.anyplot.code.treesitter import Source, jl_string, syntax_problems, walk
from agents.anyplot.data.kinds import read_kinds

from .conftest import JULIA_WORKING, source


def test_the_placeholder_becomes_the_csv_read() -> None:
    run_form = to_run_form(
        JULIA_WORKING,
        columns=["Month", "Sales (k USD)", "Count"],
        kinds={"Month": "date", "Sales (k USD)": "number", "Count": "integer"},
    )

    assert run_form == JULIA_WORKING.replace(
        "df = load_user_data()",
        source("""
            import CSV, DataFrames, Dates
            df = CSV.read(
                "data.csv",
                DataFrames.DataFrame;
                types = Dict(
                    "Month" => Dates.Date,
                    "Sales (k USD)" => Float64,
                    "Count" => Int64,
                ),
                missingstring = "",
                truestrings = ["True"],
                falsestrings = ["False"],
                strict = true,
                normalizenames = false,
                pool = false,
                stringtype = String,
                ntasks = 1,
            )
        """).rstrip("\n"),
    )
    assert syntax_problems(Source(run_form, "julia").tree) == []


def test_timestamps_and_wide_integers_convert_after_the_read() -> None:
    statement = loader_statement(["When", "Id", "Value"], {"When": "datetime", "Id": "big-integer", "Value": "number"})

    assert statement.startswith("import CSV, DataFrames, Dates, TimeZones\ndf = let\n")
    assert "    integer(cell::AbstractString) = parse(Int64, cell)\n" in statement
    assert "    function utc(cell::AbstractString)\n" in statement
    assert '            "When" => String,\n            "Id" => String,\n            "Value" => Float64,\n' in statement
    assert '    table[!, "When"] = utc.(table[!, "When"])\n    table[!, "Id"] = integer.(table[!, "Id"])\n' in statement
    assert statement.endswith("    table\nend")
    assert syntax_problems(Source(statement + "\n", "julia").tree) == []


@pytest.mark.parametrize(
    ("kind", "julia"),
    [
        ("integer", "Int64"),
        ("big-integer", "String"),
        ("number", "Float64"),
        ("boolean", "Bool"),
        ("text", "String"),
        ("date", "Dates.Date"),
        ("datetime", "String"),
    ],
)
def test_every_kind_has_its_type(kind: str, julia: str) -> None:
    assert JULIA_TYPES[kind] == julia
    assert f'"c" => {julia},' in loader_statement(["c"], {"c": kind})


@pytest.mark.parametrize(
    "name",
    [
        'Quote " and backslash \\',
        "Dollar $ sign",
        "Interpolation $(run(`ls`))",
        "$x",
        "Tab\there",
        "Zürich · 3 °C",
        "line\nbreak",
        "control\x1f",
    ],
)
def test_column_names_are_julia_string_literals(name: str) -> None:
    """`$` interpolates in Julia strings, so it is escaped; the literal decodes to the name, never to code."""
    literal = julia_literal(name)
    statement = loader_statement([name], {name: "text"})
    parsed = Source(f"x = {literal}\n", "julia")
    string = next(node for node in walk(parsed.root) if node.type == "string_literal")

    assert jl_string(parsed, string) == name
    assert not any(node.type == "string_interpolation" for node in walk(parsed.root))
    assert syntax_problems(Source(statement + "\n", "julia").tree) == []


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("x = 1\n", "exactly one"),
        ("df = load_user_data()\ndf = load_user_data()\n", "found 2"),
        ("function f()\n    df = load_user_data()\nend\n", "found 0"),
        ("df = load_user_data(\n", "does not parse"),
    ],
)
def test_the_working_form_needs_one_top_level_placeholder(code: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        to_run_form(code, columns=["a"], kinds={"a": "text"})


@pytest.mark.parametrize(
    ("columns", "kinds", "message"),
    [(["a", "a"], {"a": "text"}, "unique"), (["a"], {}, "no kind"), (["a"], {"a": "complex"}, "unknown column kinds")],
)
def test_bad_columns_or_kinds(columns: list[str], kinds: dict[str, str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        loader_statement(columns, kinds)


def test_the_run_form_is_not_what_the_validator_admits() -> None:
    """CSV and TimeZones are the loader's alone: the validator refuses them in the working form, which is all it sees."""
    run_form = to_run_form(JULIA_WORKING, columns=["When"], kinds={"When": "datetime"})

    assert any(finding.rule == "banned-import" for finding in validate_security(run_form))
    assert validate_security(JULIA_WORKING) == []


@pytest.mark.parametrize(
    "kinds",
    [{"x": "number"}, {"x": "number", "t": "datetime"}, {"x": "big-integer", "t": "datetime", "d": "date"}],
    ids=["plain", "timestamps", "every-conversion"],
)
def test_the_loader_span_is_where_the_placeholder_was(kinds: dict[str, str]) -> None:
    """The loader replaces the one placeholder line: its span starts there, and every line after it moves down by
    the span's length minus one (J2b, the error summary's working-form lines)."""
    run_form = to_run_form(JULIA_WORKING, columns=list(kinds), kinds=kinds)
    working, run = JULIA_WORKING.splitlines(), run_form.splitlines()
    placeholder = working.index("df = load_user_data()") + 1

    span = loader_span(run_form)
    assert span is not None
    first, count = span
    assert first == placeholder and run[first - 1].startswith("import CSV, DataFrames")
    assert count == len(run) - len(working) + 1 and run[first - 1 + count] == working[placeholder]
    assert run[first + count - 2] in (")", "end")
    assert loader_span(JULIA_WORKING) is None


# --- data/kinds.py: the Julia counts --------------------------------------------------------


def test_timestamps_below_the_millisecond_are_counted_per_column() -> None:
    """Julia's DateTime holds milliseconds: the loader truncates the rest (owner decision of 2026-10-29), so the
    kinds count the cells that truncation changes, for the runtime to announce."""
    csv = (
        "a,b,c,d\n"
        "2024-01-31T08:00:00.123456+01:00,2024-01-31T08:00:00.120000,2024-01-31,2024-01-31T08:00:00\n"
        "2024-01-31T08:00:00.000001,2024-01-31T08:00:00.123000,2024-02-01,2024-01-31 08:00:00.5\n"
        ",2024-01-31T08:00:00.999999999,,\n"
    )
    kinds = read_kinds(csv, {"a": "datetime", "b": "datetime", "c": "datetime", "d": "datetime"})

    assert kinds.kinds == {"a": "datetime", "b": "datetime", "c": "date", "d": "datetime"}
    assert kinds.submillisecond == {"a": 2, "b": 1}
    assert kinds.inexact == {}


def test_integer_cells_need_no_julia_count() -> None:
    """Julia reads both integer kinds as Int64: `inexact` is R's count (2^53) and stays as it was."""
    csv = "id\n9007199254740993\n-9223372036854775807\n"
    kinds = read_kinds(csv, {"id": "integer"})

    assert kinds.kinds == {"id": "big-integer"}
    assert kinds.inexact == {"id": 2}
    assert kinds.submillisecond == {}
