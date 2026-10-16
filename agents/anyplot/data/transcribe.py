"""A table read out of free text by a model, shown to the user before it becomes the dataset.

The data panel's `.parse()` is deterministic: `parse.parse_dataset` reads CSV, TSV,
semicolon or pipe text and JSON. Text that is none of those ("Hund 7 Katze 3 und
Vogel 4", a list of names typed one per line; never one column of numbers or dates, which
is a table: `looks_like_free_text`) is read by a model instead, under the
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
import re
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


MAX_TRANSCRIBE_LINES = MAX_TRANSCRIBE_ROWS + 1
"""The most non-blank lines of text the model reads as a table: a header and `MAX_TRANSCRIBE_ROWS`
rows. Text of more lines would need a longer table than the model may write, and a model
does not copy hundreds of lines reliably within `models.TRANSCRIBE_TIMEOUT_S` (live round 7
of 2026-10-16: 800 lines of numbers timed out every time); above it the parser's answer stands."""

MAX_CATEGORY_WORDS = 4
"""The most words a cell of a one-column category list holds; a longer line reads as prose."""

_NUMBER_TOKEN = re.compile(r"(?:^|\s)[-+]?\.?\d")
"""A number that stands as a word of its own, as in `Hund 7`: a label with its value, no category."""
_SENTENCE_END = (".", "!", "?", ":", ";")


def transcribe_refusal(text: str) -> str | None:
    """Why the model would not read the text as a table, in words for the user; None when it would.

    The text is blank, longer than `MAX_TRANSCRIBE_CHARS` characters, or holds more than
    `MAX_TRANSCRIBE_LINES` non-blank lines.
    """
    stripped = text.strip()
    if not stripped:
        return "the text is empty"
    if len(stripped) > MAX_TRANSCRIBE_CHARS:
        return (
            f"the text is longer than the {MAX_TRANSCRIBE_CHARS:,} characters the model that reads free text "
            "as a table takes"
        )
    lines = sum(1 for line in stripped.splitlines() if line.strip())
    if lines > MAX_TRANSCRIBE_LINES:
        return f"the text has {lines:,} lines, more than the {MAX_TRANSCRIBE_LINES:,} the model that reads free text as a table takes"
    return None


def transcribable(text: str) -> bool:
    """Whether the text is short enough for the model to read as a table (and not blank)."""
    return transcribe_refusal(text) is None


def looks_like_free_text(parsed: ParsedDataset) -> bool:
    """Whether a parse that succeeded probably read prose or a plain list, not a table.

    The sniffer found no delimiter, so the whole line became one column ("Hund 7" as the
    header, "Katze 3" as a cell). A JSON array or object is never free text: it was written
    as data, and the parser reads or refuses it itself (a quoted JSON string is prose).

    One column is a table, not free text, when its cells are typed values (integers, numbers,
    dates, booleans: the canonical input of a histogram, a density or a box plot; live round 7
    of 2026-10-16) or a clean category list under a header (`_category_list`). A list of values
    without a header line reads its first value as a data row (`parse._header_as_row`), so no
    model is needed for it either. Prose and `label value` lines without a delimiter stay free text.
    """
    if len(parsed.profile.columns) != 1 or parsed.profile.source_format.startswith("json"):
        return False
    column = parsed.profile.columns[0]
    if column.dtype != "text":
        return False
    return not _category_list(column.name, parsed)


def _category_list(header: str, parsed: ParsedDataset) -> bool:
    """Whether a one-column text parse is a list of categories under a header line.

    Every cell is a short label (at most `MAX_CATEGORY_WORDS` words, no number standing as a
    word of its own, no sentence ending), at least one category repeats (a list of counts, not
    a list of names typed one per line, whose first line the transcriber must tell from a
    header), and the header is none of the categories (so it is a name, not the first value).
    """
    rows = list(csv.reader(io.StringIO(parsed.csv)))[1:]
    cells = [row[0] for row in rows if row and row[0]]
    if not cells or len(set(cells)) == len(cells):
        return False
    if header.casefold() in {cell.casefold() for cell in cells}:
        return False
    return all(_label(cell) for cell in [header, *cells])


def _label(cell: str) -> bool:
    return (
        len(cell.split()) <= MAX_CATEGORY_WORDS
        and not _NUMBER_TOKEN.search(cell)
        and not cell.rstrip().endswith(_SENTENCE_END)
    )


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
