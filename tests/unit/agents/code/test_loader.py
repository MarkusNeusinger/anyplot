"""Tests for agents/anyplot/code/loader.py: the placeholder becomes the data.csv read."""

import ast
from pathlib import Path

import pandas as pd
import pytest

from agents.anyplot.code.loader import MAX_LINE_CHARS, to_run_form

from .conftest import source


WORKING = source("""
    import os

    import matplotlib.pyplot as plt
    import pandas as pd


    THEME = os.getenv("ANYPLOT_THEME", "light")
    df = load_user_data()
    plt.plot(df["x"], df["y"])
""")


def loader_call(code: str) -> ast.Call:
    calls = [
        node
        for node in ast.walk(ast.parse(code))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "read_csv"
    ]
    assert len(calls) == 1
    return calls[0]


def keyword(call: ast.Call, name: str) -> object:
    return next((ast.literal_eval(kw.value) for kw in call.keywords if kw.arg == name), None)


def test_placeholder_becomes_read_csv() -> None:
    result = to_run_form(
        WORKING,
        columns=["x", "y", "when", "s", "b"],
        dtypes={"x": "integer", "y": "number", "when": "datetime", "s": "text", "b": "boolean"},
        parse_dates=[],
    )

    assert "load_user_data" not in result
    assert result == WORKING.replace(
        "df = load_user_data()",
        'df = pd.read_csv("data.csv", dtype={"x": "Int64", "y": "float64", "s": "string", "b": "boolean"}, '
        'parse_dates=["when"])',
    )


def test_parse_dates_follow_column_order_and_empty_arguments_are_left_out() -> None:
    result = to_run_form(WORKING, columns=["a", "b", "c"], dtypes={"c": "datetime"}, parse_dates=["a"])
    assert 'df = pd.read_csv("data.csv", parse_dates=["a", "c"])' in result

    plain = to_run_form(WORKING, columns=["a"], dtypes={}, parse_dates=[])
    assert 'df = pd.read_csv("data.csv")\n' in plain


def test_pandas_import_is_added_after_the_last_import() -> None:
    working = WORKING.replace("import pandas as pd\n", "")
    result = to_run_form(working, columns=["x"], dtypes={}, parse_dates=[])

    assert "import matplotlib.pyplot as plt\nimport pandas as pd\n" in result
    assert result.count("import pandas as pd") == 1


def test_pandas_import_without_any_import() -> None:
    assert to_run_form("df = load_user_data()\n", columns=["x"], dtypes={}, parse_dates=[]).startswith(
        "import pandas as pd\n\ndf = pd.read_csv"
    )
    with_doc = to_run_form('"""Doc."""\ndf = load_user_data()\n', columns=["x"], dtypes={}, parse_dates=[])
    assert with_doc.startswith('"""Doc."""\n\nimport pandas as pd\ndf = pd.read_csv')


@pytest.mark.parametrize(
    "working",
    [
        "x = 1\n",
        "df = load_user_data()\ndf = load_user_data()\n",
        'text = "df = load_user_data()"  # df = load_user_data()\n',
        "df = load_user_data(1)\n",
    ],
)
def test_placeholder_count_must_be_one(working: str) -> None:
    with pytest.raises(ValueError, match="exactly one"):
        to_run_form(working, columns=["x"], dtypes={}, parse_dates=[])


@pytest.mark.parametrize(
    ("columns", "dtypes", "parse_dates", "message"),
    [
        (["x"], {"y": "number"}, [], "unknown columns"),
        (["x"], {}, ["d"], "unknown columns"),
        (["x"], {"x": "float"}, [], "unknown column dtypes"),
        (["x"], {"x": "number"}, ["x"], "other than datetime"),
        (["x", "x"], {}, [], "unique"),
    ],
)
def test_invalid_columns_and_dtypes(
    columns: list[str], dtypes: dict[str, str], parse_dates: list[str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        to_run_form(WORKING, columns=columns, dtypes=dtypes, parse_dates=parse_dates)


def test_unparseable_working_form() -> None:
    with pytest.raises(ValueError, match="does not parse"):
        to_run_form("def broken(:\n", columns=["x"], dtypes={}, parse_dates=[])


def test_long_loader_spans_lines_and_keeps_indentation() -> None:
    working = "import pandas as pd\n\nif True:\n    df = load_user_data()  # data\n"
    columns = [f"measurement_{i}" for i in range(12)]
    result = to_run_form(working, columns=columns, dtypes=dict.fromkeys(columns, "number"), parse_dates=[])

    assert all(len(line) <= MAX_LINE_CHARS for line in result.splitlines())
    assert "    df = pd.read_csv(\n" in result and "\n    )  # data\n" in result
    call = loader_call(result)
    assert keyword(call, "dtype") == dict.fromkeys(columns, "float64")


def test_column_names_are_escaped() -> None:
    columns = ['say "hi"', "back\\slash", "Größe (m²)"]
    result = to_run_form(WORKING, columns=columns, dtypes=dict.fromkeys(columns, "text"), parse_dates=[])

    assert keyword(loader_call(result), "dtype") == dict.fromkeys(columns, "string")


def test_generated_loader_reads_the_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "data.csv").write_text(
        "n,v,when,flag,name\n1,1.5,2024-01-01,true,a\n,2.5,2024-02-01,false,\n", encoding="utf-8"
    )
    statement = to_run_form(
        "df = load_user_data()\n",
        columns=["n", "v", "when", "flag", "name"],
        dtypes={"n": "integer", "v": "number", "when": "datetime", "flag": "boolean", "name": "text"},
        parse_dates=[],
    )
    monkeypatch.chdir(tmp_path)
    namespace: dict[str, object] = {"pd": pd}
    exec(compile(statement, "plot.py", "exec"), namespace)

    df = namespace["df"]
    assert isinstance(df, pd.DataFrame)
    assert str(df["n"].dtype) == "Int64" and df["n"].isna().sum() == 1
    assert str(df["v"].dtype) == "float64"
    assert pd.api.types.is_datetime64_any_dtype(df["when"])
    assert str(df["flag"].dtype) == "boolean"
    assert pd.api.types.is_string_dtype(df["name"])
