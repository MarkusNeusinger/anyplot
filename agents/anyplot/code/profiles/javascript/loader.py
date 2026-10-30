"""The JavaScript loader: the working form's placeholder becomes the read of the harness's table in the run form.

The JavaScript counterpart of `profiles/julia/loader.py`. The working form holds exactly one
top-level `const data = loadUserData();`; `to_run_form` replaces that statement with

    const data = window.ANYPLOT_DATA;

which reads the table the harness injects in sandbox mode (`ANYPLOT_DATA_JSON`, JS-2): one
object per row, keyed by the column names, in the canonical CSV's order, with the column
names in `data.columns`, the shape `d3.csvParse` returns. The values are typed by Python
from the column kinds (`agents/anyplot/data/typed_json.py`): integers and numbers as
numbers, `true` and `false`, text as written, dates as `YYYY-MM-DD` strings, datetimes as
UTC ISO strings with milliseconds, `null` for a missing cell. The typing happens before the
page, so the loader is one line for one line, every line of the run form is the working
form's, and the error summary needs no shift (`loader_span` still names the loader's line,
so an error there reads as the data loader). The counts the runtime announces for the
typing (`ColumnKinds.inexact`, `ColumnKinds.submillisecond`) and the job's `data_json` are
JS-4's.

The run form is never validated, only the working form: the validator refuses
`window.ANYPLOT_DATA` in plot code, which only this statement reads.
"""

from ...treesitter import Source, first_line, last_line, statements, syntax_problems
from .regions import DATA_GLOBAL, DATA_NAME, WINDOW, declarator, find_regions, global_read, grammar_for


LOADER_STATEMENT = f"const {DATA_NAME} = {WINDOW}.{DATA_GLOBAL};"


def loader_span(run_form: str, *, library: str = "chartjs") -> tuple[int, int] | None:
    """Where `to_run_form` put the loader in `run_form`: its first line (1-based) and its number of lines (1), or None
    when `run_form` holds no loader statement: the first top-level `const data = window.ANYPLOT_DATA;`."""
    source = Source(run_form, grammar_for(library))
    for node in statements(source.root):
        found = declarator(node)
        name = found.child_by_field_name("name") if found is not None else None
        value = found.child_by_field_name("value") if found is not None else None
        if (
            name is not None
            and value is not None
            and name.type == "identifier"
            and source.text(name) == DATA_NAME
            and global_read(source, value) == DATA_GLOBAL
        ):
            return first_line(node), last_line(node) - first_line(node) + 1
    return None


def to_run_form(working: str, *, library: str = "chartjs") -> str:
    """The working form with its placeholder replaced by `const data = window.ANYPLOT_DATA;`.

    Raises `ValueError` when the top-level placeholder does not occur exactly once or the code has a syntax problem.
    """
    source = Source(working, grammar_for(library))
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        raise ValueError(f"the working form does not parse: {problems[0].message()}")
    placeholders = find_regions(source).placeholders
    if len(placeholders) != 1:
        raise ValueError(
            f"the working form needs exactly one top-level `const data = loadUserData();`, found {len(placeholders)}"
        )
    span = placeholders[0].statement
    assert span is not None
    return working[: span.start] + LOADER_STATEMENT + working[span.end :]
