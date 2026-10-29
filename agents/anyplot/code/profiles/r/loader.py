"""The R loader: the working form's placeholder becomes the `data.csv` read of the run form.

The R counterpart of `code/loader.py`. The working form holds exactly one
`df <- load_user_data()`; `to_run_form` replaces that statement with

    df <- readr::read_csv(
      "data.csv",
      col_types = readr::cols(
        "Month" = readr::col_date(format = "%Y-%m-%d"),
        "Sales (k USD)" = readr::col_double()
      ),
      na = "",
      num_threads = 1,
      progress = FALSE,
      lazy = FALSE,
      show_col_types = FALSE
    )

with a relative path, so the exported `plot.R` runs next to the downloaded `data.csv`.
Every column is typed from its kind (`data/kinds.py`, read from the canonical CSV):
`integer` is `col_integer()`, an integer column past 32 bits (`big-integer`)
`col_double()`, which holds integers exactly up to 2^53, `number` `col_double()`,
`boolean` `col_logical()` (`data.csv` writes `True` and `False`), `text`
`col_character()` (a text column stays text, also when its cells look like numbers),
`date` `col_date(format = "%Y-%m-%d")` when every cell is a plain ISO date, and
`datetime` `col_datetime()`, readr's ISO 8601 reader, which turns an offset into UTC and
reads a time without one as UTC. `data.csv` writes a missing cell as an empty cell and
nothing else, so `na = ""` makes only that one missing, and a text cell such as `NA`
(Namibia) stays a value. One thread, no progress bar and an eager read keep the render's
process and output quiet. readr is in the toolchain image for this read alone; the
validator does not admit it for the plot code (`validate.LIBRARY_ALLOWLIST`), and the
run form is never validated, only the working form.
"""

import json

from ...treesitter import Source, first_line, syntax_problems, walk
from .regions import is_placeholder


DATA_FILE = "data.csv"
INDENT = "  "
"""R's customary two spaces, as the catalogue indents."""
READR_TYPES: dict[str, str] = {
    "integer": "readr::col_integer()",
    "big-integer": "readr::col_double()",
    "number": "readr::col_double()",
    "boolean": "readr::col_logical()",
    "text": "readr::col_character()",
    "date": 'readr::col_date(format = "%Y-%m-%d")',
    "datetime": "readr::col_datetime()",
}
"""The readr column type of each kind (`data.kinds.ColumnKind`)."""
READ_OPTIONS = ('na = ""', "num_threads = 1", "progress = FALSE", "lazy = FALSE", "show_col_types = FALSE")


def r_literal(text: str) -> str:
    """A double-quoted R string literal: JSON's escapes (`\\"`, `\\\\`, `\\n`, `\\u001f`) are R's too."""
    return json.dumps(text, ensure_ascii=False)


def loader_statement(columns: list[str], kinds: dict[str, str], indent: str = "") -> str:
    """The `readr::read_csv` statement for `columns` in `data.csv` order; its first line carries no indent."""
    if len(set(columns)) != len(columns):
        raise ValueError("columns must be unique")
    missing = [name for name in columns if name not in kinds]
    if missing:
        raise ValueError(f"no kind for columns {missing}")
    unknown = sorted({kind for kind in kinds.values() if kind not in READR_TYPES})
    if unknown:
        raise ValueError(f"unknown column kinds {unknown}; expected one of {sorted(READR_TYPES)}")
    inner, entry = indent + INDENT, indent + 2 * INDENT
    lines = ["df <- readr::read_csv(", f"{inner}{r_literal(DATA_FILE)},"]
    if columns:
        types = [f"{entry}{r_literal(name)} = {READR_TYPES[kinds[name]]}" for name in columns]
        lines += [f"{inner}col_types = readr::cols(", ",\n".join(types), f"{inner}),"]
    lines += [f"{inner}{option}," for option in READ_OPTIONS[:-1]]
    lines += [f"{inner}{READ_OPTIONS[-1]}", f"{indent})"]
    return "\n".join(lines)


def to_run_form(working: str, *, columns: list[str], kinds: dict[str, str]) -> str:
    """The working form with its placeholder replaced by the `data.csv` loader.

    `columns` is the order of `data.csv` and `kinds` maps each column to its kind
    (`data.kinds.column_kinds`). Raises `ValueError` when the placeholder does not occur
    exactly once, when the code has a syntax problem, or when a column or kind is unknown.
    """
    source = Source(working, "r")
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        raise ValueError(f"the working form does not parse: {problems[0].message()}")
    placeholders = [node for node in walk(source.root) if is_placeholder(source, node)]
    if len(placeholders) != 1:
        raise ValueError(f"the working form needs exactly one `df <- load_user_data()`, found {len(placeholders)}")
    node = placeholders[0]
    span = source.node_span(node)
    line = source.line_text(first_line(node))
    indent = line[: len(line) - len(line.lstrip(" \t"))]
    statement = loader_statement(columns, kinds, indent)
    return working[: span.start] + statement + working[span.end :]
