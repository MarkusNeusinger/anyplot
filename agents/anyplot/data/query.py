"""The `query_data` tool's core: a question about the data answered from a copy, never stored.

A live test of 2026-10-15 asked "Welches Land hatte 2023 den höchsten Pro-Kopf-Ausstoss?";
the root answered it correctly, but by filtering the user's dataset to the five rows of 2023
with `prepare_data`, which stores a new version, and then asked the user to `.undo()` it. A
question must never change the data. `run_query` applies the same operations as
`prepare_data` (`prepare.Operation`, the same closed vocabulary: no free expression, no row
the model writes) to the canonical CSV of the current version and returns a small table: the
first `limit` rows (at most `MAX_QUERY_ROWS`) of the result, in at most `MAX_QUERY_COLUMNS`
columns (the ones named in `columns`, else the first ones), every cell clipped like the
profile's (`parse.display_copy`). Nothing is stored and the bindings and the confirmation stay
as they are.

To keep only some rows, `drop_rows` drops the others (`ne 2023` keeps 2023); a top-N is a
`sort` with `limit`; a share or a trend is a `derive`, an aggregate an `aggregate`. The
operations raise `PrepareError` as in `prepare_data`; a column in `columns` that the result
lacks is `unknown_column`. No ADK import.
"""

import csv
import io
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from ..schemas import ColumnName
from .parse import ParsedDataset, display_copy
from .prepare import MAX_OPERATIONS, Operation, PrepareError, apply_operations


MAX_QUERY_ROWS = 25
"""The rows a query returns at most: enough for a top 10, a year per row over two decades, or a few groups."""
DEFAULT_QUERY_ROWS = 10
MAX_QUERY_COLUMNS = 8
"""The columns a query returns at most; with a name of 64 and cells of 40 characters, 25 rows fit the result cap."""


class QueryArgs(BaseModel):
    """The arguments of `query_data`, validated by ToolSafety and the tool alike."""

    model_config = ConfigDict(extra="forbid")

    operations: list[Operation] = Field(default_factory=list, max_length=MAX_OPERATIONS)
    columns: list[ColumnName] | None = Field(default=None, max_length=MAX_QUERY_COLUMNS)
    limit: int = Field(default=DEFAULT_QUERY_ROWS, ge=1, le=MAX_QUERY_ROWS)


@dataclass(frozen=True)
class QueryResult:
    """A bounded table of a query's result and the change lines of its operations."""

    columns: list[str]
    rows: list[list[str]]
    total_rows: int
    """The rows of the whole result, of which `rows` are the first."""
    changes: list[str]
    truncated: bool
    """Whether rows past `limit`, or columns past `MAX_QUERY_COLUMNS` (more named, or none named), were left out."""


def run_query(
    parsed: ParsedDataset,
    operations: list[Operation],
    columns: list[str] | None = None,
    limit: int = DEFAULT_QUERY_ROWS,
) -> QueryResult:
    """The operations applied to a copy of `parsed`, cut to `limit` rows and the `columns` asked for; raises `PrepareError`.

    `parsed` is never changed and nothing is stored: `apply_operations` reads its canonical
    CSV into a new frame. Without operations the result is the data as it is.
    """
    limit = max(1, min(limit, MAX_QUERY_ROWS))
    changes: list[str] = []
    text = parsed.csv
    if operations:
        prepared = apply_operations(parsed, operations)
        text, changes = prepared.csv, prepared.changes
    records = list(csv.reader(io.StringIO(text)))
    header, body = records[0], records[1:]
    if columns:
        missing = [name for name in columns if name not in header]
        if missing:
            raise PrepareError("unknown_column", f"the result has no column '{missing[0]}'")
        wanted = list(dict.fromkeys(columns))
    else:
        wanted = header
    chosen = wanted[:MAX_QUERY_COLUMNS]
    positions = [header.index(name) for name in chosen]
    rows = [[display_copy(row[position]) for position in positions] for row in body[:limit]]
    truncated = len(rows) < len(body) or len(chosen) < len(wanted)
    return QueryResult(columns=chosen, rows=rows, total_rows=len(body), changes=changes, truncated=truncated)
