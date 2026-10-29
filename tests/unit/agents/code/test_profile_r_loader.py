"""Tests for agents/anyplot/code/profiles/r/loader.py and agents/anyplot/data/kinds.py."""

import pytest

from agents.anyplot.code.profiles.r.loader import loader_statement, r_literal, to_run_form
from agents.anyplot.code.profiles.r.validate import validate_security
from agents.anyplot.code.treesitter import Source, r_string, syntax_problems
from agents.anyplot.data.kinds import DOUBLE_EXACT_MAX, INT32_MAX, column_kinds, read_kinds
from agents.anyplot.data.parse import parse_dataset

from .conftest import source


WORKING = source("""
    library(ggplot2)
    THEME <- Sys.getenv("ANYPLOT_THEME", "light")
    MONTH <- "Month"  # role: x
    df <- load_user_data()
    p <- ggplot(df, aes(x = .data[[MONTH]])) + geom_bar()
    ggsave(filename = sprintf("plot-%s.png", THEME), plot = p, device = ragg::agg_png, width = 8, height = 4.5,
           units = "in", dpi = 400)
""")


def test_the_placeholder_becomes_the_readr_read() -> None:
    run_form = to_run_form(
        WORKING,
        columns=["Month", "Sales (k USD)", "Count"],
        kinds={"Month": "date", "Sales (k USD)": "number", "Count": "integer"},
    )

    assert run_form == WORKING.replace(
        "df <- load_user_data()",
        source("""
            df <- readr::read_csv(
              "data.csv",
              col_types = readr::cols(
                "Month" = readr::col_date(format = "%Y-%m-%d"),
                "Sales (k USD)" = readr::col_double(),
                "Count" = readr::col_integer()
              ),
              na = "",
              num_threads = 1,
              progress = FALSE,
              lazy = FALSE,
              show_col_types = FALSE
            )
        """).rstrip("\n"),
    )
    assert syntax_problems(Source(run_form, "r").tree) == []


@pytest.mark.parametrize(
    ("kind", "readr"),
    [
        ("integer", "readr::col_integer()"),
        ("big-integer", "readr::col_double()"),
        ("number", "readr::col_double()"),
        ("boolean", "readr::col_logical()"),
        ("text", "readr::col_character()"),
        ("date", 'readr::col_date(format = "%Y-%m-%d")'),
        ("datetime", "readr::col_datetime()"),
    ],
)
def test_every_kind_has_its_readr_type(kind: str, readr: str) -> None:
    assert f'"c" = {readr}' in loader_statement(["c"], {"c": kind})


def test_an_indented_placeholder_keeps_its_indent() -> None:
    code = "f <- function() {\n  df <- load_user_data()\n  df\n}\n"
    run_form = to_run_form(code, columns=["a"], kinds={"a": "text"})

    assert '  df <- readr::read_csv(\n    "data.csv",\n' in run_form
    assert run_form.endswith("    show_col_types = FALSE\n  )\n  df\n}\n")


@pytest.mark.parametrize(
    "name", ['Quote " and backslash \\', "Tab\there", "Zürich · 3 °C", "line\nbreak", "`backtick`"]
)
def test_column_names_are_r_string_literals(name: str) -> None:
    assert r_string(r_literal(name)) == name
    statement = loader_statement([name], {name: "text"})
    assert syntax_problems(Source(statement, "r").tree) == []


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("x <- 1\n", "exactly one"),
        ("df <- load_user_data()\ndf <- load_user_data()\n", "found 2"),
        ("df <- load_user_data(\n", "does not parse"),
    ],
)
def test_the_working_form_needs_one_placeholder(code: str, message: str) -> None:
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
    """readr is for the loader alone: the validator refuses it in the working form, which is all it sees."""
    run_form = to_run_form(WORKING, columns=["Month"], kinds={"Month": "text"})

    assert any(finding.rule == "banned-import" for finding in validate_security(run_form))
    assert validate_security(WORKING) == []


# --- data/kinds.py ---------------------------------------------------------------------------


def test_kinds_from_a_parsed_dataset() -> None:
    parsed = parse_dataset(
        "City,Day,Stamp,Count,Big,Share,Open\n"
        "NA,2024-01-01,2024-01-01T08:00:00,3,3000000000,0.5,true\n"
        "Bern,2024-01-02,2024-01-02,4,4,1.5,false\n"
    )
    kinds = column_kinds(parsed.csv, parsed.column_dtypes, parsed.parse_dates)

    assert kinds == {
        "City": "text",
        "Day": "date",
        "Stamp": "datetime",
        "Count": "integer",
        "Big": "big-integer",
        "Share": "number",
        "Open": "boolean",
    }


def test_integer_cells_beyond_two_to_the_53_are_counted_per_column() -> None:
    """col_double() reads 9007199254740993 as …992 (toolchain image, 2026-10-29): the owner's data-fidelity rule
    wants such cells announced with counts, so the kinds expose them."""
    csv = (
        "id,small,ok\n"
        f"{DOUBLE_EXACT_MAX + 1},1,{DOUBLE_EXACT_MAX}\n"
        f"{-(DOUBLE_EXACT_MAX + 3)},2,{-DOUBLE_EXACT_MAX}\n"
        ",3,4\n"
    )
    kinds = read_kinds(csv, {"id": "integer", "small": "integer", "ok": "integer"})

    assert kinds.kinds == {"id": "big-integer", "small": "integer", "ok": "big-integer"}
    assert kinds.inexact == {"id": 2}


def test_the_int32_edge_and_missing_cells() -> None:
    csv = f"a,b,c\n{INT32_MAX},{-INT32_MAX - 1},\n,1,\n"

    assert column_kinds(csv, {"a": "integer", "b": "integer", "c": "datetime"}) == {
        "a": "integer",
        "b": "big-integer",
        "c": "date",
    }


def test_parse_dates_without_a_dtype_and_unknown_columns() -> None:
    assert column_kinds("a,b\n2024-01-01 10:00,x\n", {}, ["a"]) == {"a": "datetime", "b": "text"}
    with pytest.raises(ValueError, match="unknown columns"):
        column_kinds("a\n1\n", {"z": "integer"})
    with pytest.raises(ValueError, match="twice"):
        column_kinds("a,a\n1,2\n", {})
