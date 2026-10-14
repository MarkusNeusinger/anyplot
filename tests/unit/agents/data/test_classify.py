"""Tests for agents/anyplot/data/classify.py: code, formula or a table, before any parser reads the paste."""

import time
from pathlib import Path

import pytest

from agents.anyplot.data.classify import classify_paste, looks_like_code
from agents.anyplot.schemas import MAX_MESSAGE_CHARS


REPO_ROOT = Path(__file__).resolve().parents[4]

CODE = [
    pytest.param("np.linspace(0, 10, 100)", id="numpy call that parses as a one-row table"),
    pytest.param("import numpy as np\nx = np.linspace(0, 1)\ny = np.sin(x)\n", id="python"),
    pytest.param("from scipy import stats\nd = stats.norm.rvs(size=100)\n", id="python from-import"),
    pytest.param("squares = [x**2 for x in range(10)]\n", id="python comprehension"),
    pytest.param("for i in range(10):\n    print(i)\n", id="python loop"),
    pytest.param(
        "let data = [];\nfor (let i = 0; i < 100; i++) {\n  data.push({x: i, y: Math.random()});\n}\n",
        id="javascript loop",
    ),
    pytest.param("const ys = xs.map(x => x * x);\n", id="javascript arrow"),
    pytest.param("function f(x) {\n  return x * x;\n}\n", id="javascript function"),
    pytest.param("set.seed(42)\nx <- seq(1, 100)\ny <- rnorm(100)\ndf <- data.frame(x, y)\n", id="R"),
    pytest.param("x = rnorm(100, mean = 5)\n", id="R with ="),
    pytest.param("library(ggplot2)\nggplot(df, aes(x, y)) + geom_point()\n", id="R library"),
]
NOT_CODE = [
    pytest.param("x,y\n1,2\n3,4\n", id="csv"),
    pytest.param("Datum;Wert\n2024-01-01;3,5\n2024-01-02;4,1\n", id="semicolon csv"),
    pytest.param("Hund 7 Katze 3 und Vogel 4", id="prose"),
    pytest.param('[{"x": 1, "y": 2}, {"x": 2, "y": 3}]', id="json"),
    pytest.param("name\tvalue\nprint(x)\t3\nfoo\t4\nbar\t5\n", id="a table with one code-like cell"),
    pytest.param("# sales 2024\nJan 10\nFeb 12\n", id="a commented list"),
    pytest.param('cat_day = {"Mo": 3, "Di": 5}', id="a literal the parser reads"),
    pytest.param("y = sin(x) from -pi to pi", id="a formula"),
    pytest.param("", id="empty"),
]


@pytest.mark.parametrize("text", CODE)
def test_code(text: str) -> None:
    assert looks_like_code(text) and classify_paste(text) == "code"


@pytest.mark.parametrize("text", NOT_CODE)
def test_not_code(text: str) -> None:
    assert not looks_like_code(text)


@pytest.mark.parametrize("text", ["y = sin(x) from -pi to pi", "zeichne sin(x) von -pi bis pi", "y = x**2"])
def test_formula(text: str) -> None:
    assert classify_paste(text) == "formula"


def test_a_formula_past_the_chat_cap_is_left_to_the_parser_but_code_is_not() -> None:
    formula = "y = sin(x) from -pi to pi\n" + "note: drawn for the report\n" * 90
    code = "import numpy as np\n" + "x = np.arange(10)\n" * 200
    assert len(formula) > MAX_MESSAGE_CHARS and classify_paste(formula) is None
    assert len(code) > MAX_MESSAGE_CHARS and classify_paste(code) == "code"


@pytest.mark.parametrize(
    "line",
    [")" + " " * 200_000 + "x", "if " + " " * 200_000 + "x", "}" + " " * 100_000 + ";" + " " * 100_000 + "x"],
    ids=["paren-spaces", "if-spaces", "brace-semicolon-spaces"],
)
def test_long_space_runs_classify_in_linear_time(line: str) -> None:
    """CodeQL's polynomial-regex inputs (#12172 review): stripped, capped lines keep the patterns linear."""
    started = time.perf_counter()
    looks_like_code(line * 3)
    assert time.perf_counter() - started < 0.5


def test_no_fixture_dataset_is_code_or_a_formula() -> None:
    """The eval fixtures are real pastes: none may be classified away from the parser."""
    paths = sorted((REPO_ROOT / "agents" / "evals" / "fixtures" / "cases").glob("*/data.csv"))
    assert paths
    assert [path.parent.name for path in paths if classify_paste(path.read_text(encoding="utf-8"))] == []
