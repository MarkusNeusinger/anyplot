"""Tests for agents/anyplot/code/profiles/r/errors.py: R's stderr to a summary that never quotes the message."""

import pytest

from agents.anyplot.code.profiles.r.errors import (
    MISSING_PACKAGE,
    NO_ERROR_LINE,
    NO_ERROR_OUTPUT,
    OUT_OF_MEMORY,
    RECURSION,
    error_summary,
)

from .conftest import source


@pytest.mark.parametrize(
    ("stderr", "summary"),
    [
        (
            source("""
                Error in `geom_point()`:
                ! Problem while computing aesthetics.
                ℹ Error occurred in the 1st layer.
                Caused by error:
                ! object 'Umsatz Zürich' not found
                Backtrace:
                    ▆
                 1. ├─ggplot2::ggsave(...)
                Execution halted
            """),
            "error in geom_point(); in the 1st layer",
        ),
        (
            source("""
                Error in `mutate()`:
                ℹ In argument: `y = log(x)`.
                Caused by error in `log()`:
                ! non-numeric argument to mathematical function
                Execution halted
            """),
            "error in mutate(); caused by log()",
        ),
        (
            source("""
                Error in `dplyr::filter()`:
                ℹ In argument: `.data[["Region"]] == "Nord"`.
                Caused by error in `.data[["Region"]]`:
                ! Column `Region` not found in `.data`.
                Execution halted
            """),
            "error in dplyr::filter()",
        ),
        (
            source("""
                Error in rowsum.default(x, group) : incorrect length for 'group'
                Calls: <Anonymous> ... print.ggplot -> ggplot_build -> by_layer -> f -> rowsum.default
                Execution halted
            """),
            "error in rowsum.default(); calls: by_layer -> f -> rowsum.default",
        ),
        (
            source("""
                Error in df$secret : $ operator is invalid for atomic vectors
                Calls: summarise -> df$secret
                Execution halted
            """),
            "error; calls: summarise",
        ),
        ("Error: object 'secret' not found\nExecution halted\n", "error"),
        ("Error: cannot allocate vector of size 2.1 Gb\nExecution halted\n", OUT_OF_MEMORY),
        ("Error: vector memory limit of 1.0 Gb reached, see mem.maxVSize()\n", OUT_OF_MEMORY),
        ("Error: C stack usage  7971092 is too close to the limit\n", RECURSION),
        ("Error: evaluation nested too deeply: infinite recursion / options(expressions=)?\n", RECURSION),
        ("Error in library(qrcode) : there is no package called ‘qrcode’\n", f"{MISSING_PACKAGE} (qrcode)"),
        ("Error in loadNamespace(x) : there is no package called 'sf'\n", f"{MISSING_PACKAGE} (sf)"),
        ("Warning message:\nIn sprintf(\"\", 7) : one argument not used by format ''\n", NO_ERROR_LINE),
        ("", NO_ERROR_OUTPUT),
        ("   \n", NO_ERROR_OUTPUT),
    ],
)
def test_summaries(stderr: str, summary: str) -> None:
    assert error_summary(stderr) == summary


@pytest.mark.parametrize(
    "stderr",
    [
        'Error in parse_number("Zürich 12,5 %") : could not find function "parse_number"\n',
        "Error in `geom_text()`:\n! Problem with label 'Kunde Müller AG'\nExecution halted\n",
        "Error in f(x) : invalid 'type' (character) of argument\nCalls: lapply -> FUN -> secret.value\n",
    ],
)
def test_the_message_never_reaches_the_summary(stderr: str) -> None:
    summary = error_summary(stderr)

    assert all(word not in summary for word in ("Zürich", "Müller", "invalid", "could not find", "'"))


def test_a_name_that_is_no_r_name_is_left_out() -> None:
    stderr = "Error in `<Zürich>()`:\n! boom\nCalls: <Anonymous> -> `odd name` -> g\n"

    assert error_summary(stderr) == "error; calls: `odd name` -> g"
