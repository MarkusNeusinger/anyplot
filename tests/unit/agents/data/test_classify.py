"""Tests for agents/anyplot/data/classify.py: code, a data request, a formula or a table, before any parser reads it."""

import time
from pathlib import Path

import pytest

from agents.anyplot.data.classify import (
    MAX_REQUEST_WORDS,
    classify_paste,
    looks_like_code,
    looks_like_data_request,
    request_for_chat,
)
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


DATA_REQUESTS = [
    pytest.param("Beispieldaten", id="the owner's word"),
    pytest.param("generiere Zufallszahlen mit Kategorien", id="the owner's sentence"),
    pytest.param("Erstelle mir Testdaten mit 5 Gruppen und 20 Zeilen", id="german with its sizes"),
    pytest.param("gib mir ein paar zufällige Werte", id="german adjective"),
    pytest.param("Beispiel-Daten bitte", id="german hyphenated"),
    pytest.param("Zufallswerte zwischen 10 und 100 für 4 Regionen und 12 Monate", id="german with a range"),
    pytest.param("example data", id="english"),
    pytest.param("random numbers with 3 categories", id="english random numbers"),
    pytest.param("example data, 3 categories, 20 rows", id="english with commas"),
    pytest.param("Make up some data for 4 regions", id="english verb"),
    pytest.param("sample sales data for 6 products", id="english with a subject"),
    pytest.param("random numbers with a normal distribution", id="a data request before a curve's name"),
    pytest.param("données d'exemple", id="french"),
    pytest.param("datos de ejemplo", id="spanish"),
    pytest.param("dati di esempio", id="italian"),
    pytest.param("dados aleatórios", id="portuguese"),
    pytest.param("voorbeelddata", id="dutch"),
    pytest.param("przykładowe dane", id="polish"),
]
NOT_DATA_REQUESTS = [
    pytest.param("Hund 7 Katze 3 und Vogel 4", id="prose with values"),
    pytest.param("Beispieldaten: Hund 7, Katze 3, Vogel 4", id="a request word beside its own values"),
    pytest.param("Testdaten,Wert\nA,1\nB,2\n", id="a table under a request word"),
    pytest.param("Zufallszahlen\n3\n5\n8\n", id="a list under a request word"),
    pytest.param('{"Testdaten": [1, 2]}', id="json"),
    pytest.param("Testdatenbank Export", id="a word that only starts like one"),
    pytest.param("Mach die Balken blau", id="a plot request"),
    pytest.param("monthly sales for 4 regions", id="data in words: the transcriber's"),
    pytest.param("y = sin(x) from -pi to pi", id="a formula"),
    pytest.param("import random\nx = [random.random() for _ in range(10)]\n", id="code"),
    pytest.param("", id="empty"),
]


@pytest.mark.parametrize("text", DATA_REQUESTS)
def test_data_request(text: str) -> None:
    assert looks_like_data_request(text) and classify_paste(text) == "data_request"


@pytest.mark.parametrize("text", NOT_DATA_REQUESTS)
def test_not_a_data_request(text: str) -> None:
    assert not looks_like_data_request(text) and classify_paste(text) != "data_request"


def test_a_data_request_is_one_short_line_the_chat_takes() -> None:
    """Prose that mentions random numbers is no request, and neither is a line the chat could not take."""
    long_line = "Beispieldaten " + "bitte " * MAX_REQUEST_WORDS
    assert len(long_line.split()) > MAX_REQUEST_WORDS and not looks_like_data_request(long_line)
    assert not looks_like_data_request("Beispieldaten\nfür meinen Plot")
    assert not looks_like_data_request("Beispieldaten " + "x" * MAX_MESSAGE_CHARS)


def test_the_transcribers_data_request_goes_to_the_chat_only_without_values() -> None:
    """`asks_for_data` from the model is trusted for text the chat takes that holds no data of its own."""
    assert request_for_chat("monthly sales for 4 regions over 12 months")
    assert request_for_chat("Umsätze pro Monat für vier Filialen\nim Jahr 2025")
    assert not request_for_chat("sales: north 12, south 14, east 9")
    assert not request_for_chat("monthly sales " * 200) and not request_for_chat("   ")


def test_the_request_pattern_runs_in_linear_time() -> None:
    """The phrase gaps are bounded: a line of near misses stays fast."""
    line = ("generate me some a an few random " * 6 + "x ") * 40
    started = time.perf_counter()
    looks_like_data_request(line[:MAX_MESSAGE_CHARS])
    classify_paste(line[:MAX_MESSAGE_CHARS])
    assert time.perf_counter() - started < 0.5


def test_no_fixture_dataset_is_code_or_a_formula() -> None:
    """The eval fixtures are real pastes: none may be classified away from the parser."""
    paths = sorted((REPO_ROOT / "agents" / "evals" / "fixtures" / "cases").glob("*/data.csv"))
    assert paths
    assert [path.parent.name for path in paths if classify_paste(path.read_text(encoding="utf-8"))] == []
