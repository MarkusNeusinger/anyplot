"""The loader: the working form's placeholder becomes the `data.csv` read of the run form.

The working form holds exactly one `df = load_user_data()`. `to_run_form` replaces it
with `df = pd.read_csv("data.csv", dtype={...}, parse_dates=[...])`. The path is
relative, so the exported `plot.py` runs next to the downloaded `data.csv`, in a shell
or a notebook. `data.csv` is the parser's canonical file (comma separated, dot decimal,
ISO dates), so no `sep`, `decimal` or date format is needed. The column dtypes from
the dataset profile map to pandas dtypes that keep missing values (`integer` to
`Int64`, `number` to `float64`, `boolean` to `boolean`, `text` to `string`); datetime
columns go to `parse_dates`. `import pandas as pd` is added after the last module-level
import when the file does not have it.
"""

import ast
import json
from typing import get_args

from ..schemas import ColumnDtype
from .regions import SourceIndex, is_placeholder


DATA_FILE = "data.csv"
PANDAS_DTYPES: dict[str, str] = {"integer": "Int64", "number": "float64", "boolean": "boolean", "text": "string"}
DATETIME = "datetime"
MAX_LINE_CHARS = 120  # the repository's ruff line length
PANDAS_IMPORT = "import pandas as pd"

_COLUMN_DTYPES = frozenset(get_args(ColumnDtype))


def to_run_form(working: str, *, columns: list[str], dtypes: dict[str, str], parse_dates: list[str]) -> str:
    """The working form with its placeholder replaced by the `data.csv` loader.

    `columns` is the order of `data.csv`; `dtypes` maps a column to its `ColumnDtype`
    name; `parse_dates` lists further columns to parse as dates. Raises `ValueError`
    when the placeholder does not occur exactly once, when the code does not parse,
    or when a column or dtype is unknown or contradictory.
    """
    dtype_map, dates = _loader_arguments(columns, dtypes, parse_dates)
    try:
        tree = ast.parse(working)
    except SyntaxError as exc:
        raise ValueError(f"the working form does not parse at line {exc.lineno}") from exc
    placeholders = [node for node in ast.walk(tree) if is_placeholder(node) and isinstance(node, ast.Assign)]
    if len(placeholders) != 1:
        raise ValueError(f"the working form needs exactly one `df = load_user_data()`, found {len(placeholders)}")

    index = SourceIndex(working)
    span = index.node_span(placeholders[0])
    line = index.line_text(span.first_line)
    indent = line[: len(line) - len(line.lstrip(" \t"))]
    statement = _statement(indent, dtype_map, dates)
    code = working[: span.start] + statement + working[span.end :]
    return _ensure_pandas(code)


def _loader_arguments(
    columns: list[str], dtypes: dict[str, str], parse_dates: list[str]
) -> tuple[dict[str, str], list[str]]:
    if len(set(columns)) != len(columns):
        raise ValueError("columns must be unique")
    known = set(columns)
    unknown = [name for name in [*dtypes, *parse_dates] if name not in known]
    if unknown:
        raise ValueError(f"unknown columns: {sorted(set(unknown))}")
    invalid = sorted({dtype for dtype in dtypes.values() if dtype not in _COLUMN_DTYPES})
    if invalid:
        raise ValueError(f"unknown column dtypes {invalid}; expected one of {sorted(_COLUMN_DTYPES)}")
    conflicting = sorted(name for name in parse_dates if dtypes.get(name, DATETIME) != DATETIME)
    if conflicting:
        raise ValueError(f"columns in parse_dates with a dtype other than datetime: {conflicting}")
    wanted = set(parse_dates)
    dates = [name for name in columns if name in wanted or dtypes.get(name) == DATETIME]
    dtype_map = {name: PANDAS_DTYPES[dtypes[name]] for name in columns if dtypes.get(name, DATETIME) != DATETIME}
    return dtype_map, dates


def _literal(text: str) -> str:
    """A double-quoted Python string literal (JSON escapes are valid Python escapes)."""
    return json.dumps(text, ensure_ascii=False)


def _statement(indent: str, dtype_map: dict[str, str], dates: list[str]) -> str:
    """The loader statement, on one line when it fits, else one entry per line."""
    dtype_items = [f"{_literal(name)}: {_literal(dtype)}" for name, dtype in dtype_map.items()]
    date_items = [_literal(name) for name in dates]
    arguments = [_literal(DATA_FILE)]
    if dtype_items:
        arguments.append("dtype={" + ", ".join(dtype_items) + "}")
    if date_items:
        arguments.append("parse_dates=[" + ", ".join(date_items) + "]")
    single = f"df = pd.read_csv({', '.join(arguments)})"
    if len(indent) + len(single) <= MAX_LINE_CHARS:
        return single

    inner, entry = indent + "    ", indent + "        "
    lines = ["df = pd.read_csv(", f"{inner}{_literal(DATA_FILE)},"]
    if dtype_items:
        lines += [f"{inner}dtype={{", *(f"{entry}{item}," for item in dtype_items), f"{inner}}},"]
    if date_items:
        lines += [f"{inner}parse_dates=[", *(f"{entry}{item}," for item in date_items), f"{inner}],"]
    lines.append(f"{indent})")
    return "\n".join(lines)


def _has_pandas(tree: ast.Module) -> bool:
    return any(
        isinstance(stmt, ast.Import) and any(alias.name == "pandas" and alias.asname == "pd" for alias in stmt.names)
        for stmt in tree.body
    )


def _ensure_pandas(code: str) -> str:
    """Add `import pandas as pd` after the last module-level import when it is missing."""
    tree = ast.parse(code)
    if _has_pandas(tree):
        return code
    imports = [stmt for stmt in tree.body if isinstance(stmt, ast.Import | ast.ImportFrom)]
    index = SourceIndex(code)
    if imports:
        at = index.lines_span(imports[-1]).end
        before = code[:at] if code[:at].endswith(("\n", "\r")) else code[:at] + "\n"
        return before + PANDAS_IMPORT + "\n" + code[at:]
    first = tree.body[0] if tree.body else None
    docstring = (
        isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)
    )
    if first is not None and docstring:
        at = index.lines_span(first).end
        before = code[:at] if code[:at].endswith(("\n", "\r")) else code[:at] + "\n"
        return before + "\n" + PANDAS_IMPORT + "\n" + code[at:]
    return PANDAS_IMPORT + "\n\n" + code
