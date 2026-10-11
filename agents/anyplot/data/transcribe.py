"""A table read out of free text by a model, shown to the user before it becomes the dataset.

The data panel's `.parse()` is deterministic: `parse.parse_dataset` reads CSV, TSV,
semicolon or pipe text and JSON. Text that is none of those ("Hund 7 Katze 3 und
Vogel 4", a list typed one value per line) is read by a model instead, under the
`TranscribedTable` schema, and the service answers with the table it read and nothing
stored; the user confirms the preview, and only that confirmation posts the table's CSV
through the ordinary parse, pre-filter and judge path (owner rule of 2026-10-11: a first
step where the user checks that the data fits, or everything after it is wrong).

This module holds the schema and the pure helpers around it; the model call is
`models.JudgeClient.transcribe` (the judge model under this schema), and the route is
`main.upload_dataset`. No ADK import.
"""

import csv
import io
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..schemas import MAX_COLUMN_NAME_CHARS
from .parse import MAX_INPUT_CELL_CHARS, ParsedDataset


MAX_TRANSCRIBE_CHARS = 4_000
"""The longest pasted text a model reads as a table. A real table of that size is a few
hundred rows, which the model would have to write back cell by cell; above it the
deterministic parser's answer stands (stored, or `422 unparseable`)."""
MAX_TRANSCRIBE_COLUMNS = 20
MAX_TRANSCRIBE_ROWS = 200
"""Bounds of the read table: within the limit that `MAX_TRANSCRIBE_CHARS` of text can
hold, and a cap on the model's output (`models.TRANSCRIBE_MAX_OUTPUT_TOKENS`)."""
MAX_TRANSCRIBE_NOTE_CHARS = 200

Header = Annotated[str, Field(min_length=1, max_length=MAX_COLUMN_NAME_CHARS)]
Cell = Annotated[str, Field(max_length=MAX_INPUT_CELL_CHARS)]
Row = Annotated[list[Cell], Field(min_length=1, max_length=MAX_TRANSCRIBE_COLUMNS)]


class TranscribedTable(BaseModel):
    """The model's reading of the text: column names, rows of cells as text, and a short note."""

    model_config = ConfigDict(extra="forbid")

    columns: list[Header] = Field(min_length=1, max_length=MAX_TRANSCRIBE_COLUMNS)
    rows: list[Row] = Field(min_length=1, max_length=MAX_TRANSCRIBE_ROWS)
    note: str = Field(default="", max_length=MAX_TRANSCRIBE_NOTE_CHARS)


def transcribable(text: str) -> bool:
    """Whether the text is short enough for the model to read as a table (and not blank)."""
    return 0 < len(text.strip()) <= MAX_TRANSCRIBE_CHARS


def looks_like_free_text(parsed: ParsedDataset) -> bool:
    """Whether a parse that succeeded probably read prose or a plain list, not a table.

    The sniffer found no delimiter, so the whole line became one column ("Hund 7" as the
    header, "Katze 3" as a cell). A JSON array or object is never free text: it was written
    as data, and the parser reads or refuses it itself (a quoted JSON string is prose).
    """
    return len(parsed.profile.columns) == 1 and not parsed.profile.source_format.startswith("json")


def table_to_csv(table: TranscribedTable) -> str:
    """The read table as comma-separated text with a header line, the form `.parse()` reads.

    Short rows are padded with empty cells and long rows cut to the header's width, so the
    parser never refuses the table for a ragged row the model wrote.
    """
    width = len(table.columns)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(table.columns)
    for row in table.rows:
        cells = list(row[:width])
        cells.extend([""] * (width - len(cells)))
        writer.writerow(cells)
    return buffer.getvalue()
