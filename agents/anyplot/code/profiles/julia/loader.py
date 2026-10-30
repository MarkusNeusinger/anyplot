"""The Julia loader: the working form's placeholder becomes the `data.csv` read of the run form.

The Julia counterpart of `profiles/r/loader.py`. The working form holds exactly one
top-level `df = load_user_data()`; `to_run_form` replaces that statement with an import
line and the read, for a table without timestamps and with integers that fit 32 bits:

    import CSV, DataFrames, Dates
    df = CSV.read(
        "data.csv",
        DataFrames.DataFrame;
        types = Dict(
            "Month" => Dates.Date,
            "Sales (k USD)" => Float64,
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

with a relative path, so the exported `plot.jl` runs next to the downloaded `data.csv`.
`import` (not `using`) puts only the module names in scope, so nothing the plot names
changes; the validator refuses `CSV` and `TimeZones` in the plot code and the binding of
any of these names. Every column is typed from its kind (`data/kinds.py`, read from the
canonical CSV): `integer` is `Int64`, `number` `Float64`, `boolean` `Bool` with the true
and false strings named (`data.csv` writes `True` and `False`), `text` `String` (a text
column stays text, also when its cells look like numbers), `date` `Dates.Date` (every
cell a plain ISO date). `data.csv` writes a missing cell as an empty cell and nothing
else, so `missingstring = ""` makes only that one missing, and a text cell such as `NA`
(Namibia) stays a value. `strict = true` fails on a cell that does not parse instead of
making it missing; `normalizenames = false` keeps the column names as written,
`pool = false` and `stringtype = String` keep plain `String` columns (no pooled or inline
strings), and `ntasks = 1` reads on one thread.

Two kinds are read as `String` and converted after the read, inside a `let` block that
keeps the helpers local, because the read alone is not exact for them:

* `big-integer` (integer cells past 32 bits) with Base's `parse(Int64, cell)`. CSV.jl
  0.10.17 (Parsers 2.8.8) reads the eight negative values -9223372036854775807 to
  -9223372036854775800 as their positive magnitude, silently (measured in the J1 image
  on 2026-10-29: 8 wrong of 200,782 boundary and random values, every other value of
  that sample exact, and 0 wrong of 249,964 floats against Base's `parse`); `parse` is
  exact over the whole `Int64` range, which holds every integer cell (`data/parse.py`
  keeps a whole number past int64 as text). An `integer` column fits 32 bits and reads
  directly. So Julia needs no integer note: R's 2^53 line has no Julia counterpart.
* `datetime` through TimeZones.jl (owner decision of 2026-10-29): a cell
  `YYYY-MM-DD(T| )HH:MM[:SS][.fraction][Z|±HH[:MM]]` becomes a `Dates.DateTime`. A cell
  with an offset or `Z` is converted to UTC, as readr does (`TimeZones.ZonedDateTime`
  with the format `yyyy-mm-ddTHH:MM:SS.ssszzzz`, then `Dates.DateTime(zdt,
  TimeZones.UTC)`); a cell without one is read as written, which readr also reads as UTC.
  A fraction is truncated to milliseconds, because Julia's `DateTime` holds milliseconds;
  `data/kinds.py` counts the cells per column whose digits below the millisecond are not
  all zero, for the runtime to announce (data-fidelity rule). Measured in the J1 image
  (Julia 1.13.2, TimeZones 1.22.3): `Dates.DateTime(s)` refuses a space separator,
  `Z`, `+01:00` and more than three fraction digits, which is why the cell is rewritten
  first; the format reads `+01:00`, `-05:30`, `+0100`, `+01` and `Z`.

The run form is never validated, only the working form; the loader's own code may use
what the validator refuses in plot code (`CSV`, `TimeZones`, `parse`).
"""

import json

from ...treesitter import Source, first_line, last_line, statements, syntax_problems
from .regions import find_regions


DATA_FILE = "data.csv"
LOADER_IMPORT = "import CSV, DataFrames"
"""The start of the loader's first line, whatever modules follow (`loader_statement`)."""
INDENT = "    "
"""Julia's customary four spaces, as the catalogue indents."""
JULIA_TYPES: dict[str, str] = {
    "integer": "Int64",
    "big-integer": "String",
    "number": "Float64",
    "boolean": "Bool",
    "text": "String",
    "date": "Dates.Date",
    "datetime": "String",
}
"""The type `CSV.read` reads each kind as (`data.kinds.ColumnKind`); `big-integer` and `datetime` are converted after."""
CONVERSIONS: dict[str, str] = {"big-integer": "integer", "datetime": "utc"}
"""The kinds read as `String` and the local function that converts each column after the read."""
READ_OPTIONS = (
    'missingstring = ""',
    'truestrings = ["True"]',
    'falsestrings = ["False"]',
    "strict = true",
    "normalizenames = false",
    "pool = false",
    "stringtype = String",
    "ntasks = 1",
)
ISO_DATETIME = r'r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(:\d{2})?(?:[.,](\d{1,9}))?(Z|[+-]\d{2}(?::?\d{2})?)?$"'
"""The cell forms `utc` reads: ISO 8601 with `T` or a space, optional seconds and fraction, and an optional offset."""
ZONED_FORMAT = 'Dates.dateformat"yyyy-mm-ddTHH:MM:SS.ssszzzz"'
INTEGER_HELPER = ("integer(cell::Missing) = missing", "integer(cell::AbstractString) = parse(Int64, cell)")
UTC_HELPER = (
    "utc(cell::Missing) = missing",
    "function utc(cell::AbstractString)",
    f"    m = match({ISO_DATETIME}, cell)",
    '    m === nothing && throw(ArgumentError("not an ISO 8601 date and time: $(repr(cell))"))',
    '    stamp = string(m[1], "T", m[2], something(m[3], ":00"), ".", rpad(something(m[4], ""), 3, \'0\')[1:3])',
    "    m[5] === nothing && return Dates.DateTime(stamp)",
    f"    return Dates.DateTime(TimeZones.ZonedDateTime(stamp * m[5], {ZONED_FORMAT}), TimeZones.UTC)",
    "end",
)
"""The local converters: Base's exact integer parse, and a datetime to UTC through TimeZones (module docstring)."""


def julia_literal(text: str) -> str:
    """A double-quoted Julia string literal: JSON's escapes (`\\"`, `\\\\`, `\\n`, `\\u001f`) are Julia's too, and
    `$`, which Julia interpolates, is escaped as `\\$`."""
    return json.dumps(text, ensure_ascii=False).replace("$", "\\$")


def loader_statement(columns: list[str], kinds: dict[str, str], indent: str = "") -> str:
    """The import line and the `CSV.read` statement for `columns` in `data.csv` order; the first line carries no
    indent."""
    if len(set(columns)) != len(columns):
        raise ValueError("columns must be unique")
    missing = [name for name in columns if name not in kinds]
    if missing:
        raise ValueError(f"no kind for columns {missing}")
    unknown = sorted({kind for kind in kinds.values() if kind not in JULIA_TYPES})
    if unknown:
        raise ValueError(f"unknown column kinds {unknown}; expected one of {sorted(JULIA_TYPES)}")
    used = {kinds[name] for name in columns}
    modules = ["CSV", "DataFrames"]
    if used & {"date", "datetime"}:
        modules.append("Dates")
    if "datetime" in used:
        modules.append("TimeZones")
    lines = [f"import {', '.join(modules)}"]
    converted = [name for name in columns if kinds[name] in CONVERSIONS]
    if not converted:
        lines += _read("df", columns, kinds)
    else:
        helpers: list[str] = []
        if "big-integer" in used:
            helpers += INTEGER_HELPER
        if "datetime" in used:
            helpers += UTC_HELPER
        body = [*helpers, *_read("table", columns, kinds)]
        for name in converted:
            literal = julia_literal(name)
            body.append(f"table[!, {literal}] = {CONVERSIONS[kinds[name]]}.(table[!, {literal}])")
        lines += ["df = let", *(f"{INDENT}{line}" for line in [*body, "table"]), "end"]
    return "\n".join([lines[0], *(f"{indent}{line}" for line in lines[1:])])


def _read(target: str, columns: list[str], kinds: dict[str, str]) -> list[str]:
    """The lines of `target = CSV.read(...)`, unindented."""
    lines = [f"{target} = CSV.read(", f'{INDENT}"{DATA_FILE}",', f"{INDENT}DataFrames.DataFrame;"]
    if columns:
        entries = [f"{2 * INDENT}{julia_literal(name)} => {JULIA_TYPES[kinds[name]]}," for name in columns]
        lines += [f"{INDENT}types = Dict(", *entries, f"{INDENT}),"]
    lines += [f"{INDENT}{option}," for option in READ_OPTIONS]
    return [*lines, ")"]


def loader_span(run_form: str) -> tuple[int, int] | None:
    """Where `to_run_form` put the loader in `run_form`: its first line (1-based) and its number of lines, or None
    when `run_form` holds no loader statement.

    The loader is the top-level `import CSV, DataFrames...` line and the statement after it (`df = CSV.read(...)` or
    `df = let ... end`); the plot code never imports `CSV` (`validate.LOADER_PACKAGES`), so the first such import is
    the loader's. It replaced the one line of the working form's placeholder, so a run-form line after it lies the
    loader's line count minus one behind the working form's, which the adapter edits (`errors.error_summary`).
    """
    source = Source(run_form, "julia")
    top = statements(source.tree.root_node)
    for index, node in enumerate(top[:-1]):
        if node.type == "import_statement" and source.text(node).startswith(LOADER_IMPORT):
            first = first_line(node)
            return first, last_line(top[index + 1]) - first + 1
    return None


def to_run_form(working: str, *, columns: list[str], kinds: dict[str, str]) -> str:
    """The working form with its placeholder replaced by the `data.csv` loader.

    `columns` is the order of `data.csv` and `kinds` maps each column to its kind
    (`data.kinds.column_kinds`). Raises `ValueError` when the top-level placeholder does
    not occur exactly once, when the code has a syntax problem, or when a column or kind
    is unknown.
    """
    source = Source(working, "julia")
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        raise ValueError(f"the working form does not parse: {problems[0].message()}")
    placeholders = find_regions(source).placeholders
    if len(placeholders) != 1:
        raise ValueError(
            f"the working form needs exactly one top-level `df = load_user_data()`, found {len(placeholders)}"
        )
    span = placeholders[0].statement
    assert span is not None
    line = source.line_text(span.first_line)
    indent = line[: len(line) - len(line.lstrip(" \t"))]
    statement = loader_statement(columns, kinds, indent)
    return working[: span.start] + statement + working[span.end :]
