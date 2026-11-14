"""The `query_data` tool's core: a question about the data answered from a copy, never stored.

A live test of 2026-10-15 asked "Welches Land hatte 2023 den höchsten Pro-Kopf-Ausstoss?";
the root answered it correctly, but by filtering the user's dataset to the five rows of 2023
with `prepare_data`, which stores a new version, and then asked the user to `.undo()` it. A
question must never change the data. `run_query` applies the same operations as
`prepare_data` (`prepare.Operation`, the same closed vocabulary: no code, only a `compute`
expression the whitelist checks, no row the model writes) to the canonical CSV of the current
version (or of the earlier version `from_version` names, since 2026-11-07: the pace per run after a weekly sum)
and returns a small table: the
first `limit` rows (at most `MAX_QUERY_ROWS`) of the result, in at most `MAX_QUERY_COLUMNS`
columns (the ones named in `columns`, else the first ones), every cell clipped like the
profile's (`parse.display_copy`). Nothing is stored and the bindings and the confirmation stay
as they are.

To keep only some rows, `drop_rows` drops the others (`ne 2023` keeps 2023); a top-N is a
`sort` with `limit`; a share or a trend is a `derive`, the change from the row before a `diff`,
another formula a `compute`, an aggregate an `aggregate`. The
operations raise `PrepareError` as in `prepare_data`; a column in `columns` that the result
lacks is `unknown_column`. No ADK import.
"""

import csv
import io
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from ..language import DEFAULT_LANGUAGE
from ..schemas import ColumnName, FromVersion
from .parse import MAX_COMPUTED_BYTES, ParsedDataset, display_copy, parse_dataset
from .prepare import MAX_OPERATIONS, Operation, Prepared, PrepareError, apply_operations, cut_note


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
    from_version: FromVersion = "current"
    """The version the question reads (`dataset_versions.resolve_version`): the current one by default."""


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
    *,
    language: str = DEFAULT_LANGUAGE,
) -> QueryResult:
    """The operations applied to a copy of `parsed`, cut to `limit` rows and the `columns` asked for; raises `PrepareError`.

    `parsed` is never changed and nothing is stored: `apply_operations` reads its canonical
    CSV into a new frame. Without operations the result is the data as it is. `language` is
    the session language, which names the column of a `date_number` that names none.
    """
    limit = max(1, min(limit, MAX_QUERY_ROWS))
    changes: list[str] = []
    text = parsed.csv
    prepared: Prepared | None = None
    if operations:
        prepared = apply_operations(parsed, operations, language=language)
        text, changes = prepared.csv, list(prepared.changes)
    records = list(csv.reader(io.StringIO(text)))
    header, body = records[0], records[1:]
    if prepared is not None and prepared.sorted_by is not None and len(body) > limit:
        # The cut of a ranking, like a top N's: "which 3 are largest" must not name three of five equals as the
        # answer without a word. The note is one more line of the result; the cut itself stays at `limit`.
        ranked = parse_dataset(
            prepared.csv,
            text_columns=prepared.text_columns,
            find_table=False,
            max_bytes=MAX_COMPUTED_BYTES,
            canonical=True,
        )
        tie = cut_note(ranked, prepared.sorted_by, limit)
        if tie:
            changes.append(f"the first {limit} of {len(body)} rows are returned; {tie}")
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
