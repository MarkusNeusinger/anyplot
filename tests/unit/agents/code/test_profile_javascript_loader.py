"""Tests for agents/anyplot/code/profiles/javascript/loader.py: the placeholder becomes the read of the harness's table."""

import pytest

from agents.anyplot.code.profiles.javascript.loader import LOADER_STATEMENT, loader_span, to_run_form
from agents.anyplot.code.profiles.javascript.validate import validate_security

from .conftest import JS_WORKING, MUIX_WORKING


def test_the_placeholder_becomes_the_read_of_the_injected_table() -> None:
    run_form = to_run_form(JS_WORKING)

    assert run_form == JS_WORKING.replace("const data = loadUserData();", "const data = window.ANYPLOT_DATA;")
    assert LOADER_STATEMENT == "const data = window.ANYPLOT_DATA;"
    assert run_form.count("\n") == JS_WORKING.count("\n")


def test_a_muix_module_takes_the_same_line() -> None:
    run_form = to_run_form(MUIX_WORKING, library="muix")

    assert "const data = window.ANYPLOT_DATA;\n" in run_form
    assert loader_span(run_form, library="muix") == (13, 1)


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("//# anyplot-orientation: landscape\nconst a = 1;\n", "found 0"),
        ("let data = loadUserData();\n", "found 0"),
        ("const data = loadUserData();\nconst data = loadUserData();\n", "found 2"),
        ("const a = (;\n", "does not parse"),
    ],
)
def test_the_working_form_needs_one_top_level_placeholder(code: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        to_run_form(code)


@pytest.mark.parametrize(
    "other",
    ["{\n  const data = loadUserData();\n}\n", "const data2 = loadUserData();\n", "function f() { const data = 1; }\n"],
)
def test_only_the_top_level_statement_named_data_is_the_placeholder(other: str) -> None:
    """The ADAPTATION validator refuses the others (`placeholder-use`); the loader replaces only the placeholder."""
    run_form = to_run_form("const data = loadUserData();\n" + other)

    assert run_form == LOADER_STATEMENT + "\n" + other


def test_the_run_form_is_not_what_the_validator_admits() -> None:
    """The validator refuses `window.ANYPLOT_DATA` in plot code: only the loader's statement reads it."""
    findings = validate_security(to_run_form(JS_WORKING))

    assert [finding.rule for finding in findings] == ["banned-name"]
    assert findings[0].message == "the data comes from const data = loadUserData();, never from window.ANYPLOT_DATA"


def test_no_loader_without_its_statement() -> None:
    assert loader_span(JS_WORKING) is None
