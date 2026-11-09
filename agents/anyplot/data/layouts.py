"""Two layouts of pasted text that the delimited reader does not see, read by code before any model.

The owner's rule of 2026-11-09: code reads a paste first, and a model reads it as a table only when no rule does (the
transcriber, `transcribe.py`, for text of at most `transcribe.MAX_TRANSCRIBE_CHARS` characters). These two layouts came
from the owner's live session, and both went to the chat as a message before; the page routes them as data with the
same rules (`app/src/sections/agent-chat/routeInput.ts`, the shared cases in `routeInput.cases.json`).

**A web table copied one cell per line** (`cell_lines_table`). A browser copies a table drawn without a `<table>`
element as one line per cell, often with a blank line between the cells:

    Model · score · range
    Alpha
    120
    81.5
    60–97
    Beta
    ...
    score
    range

Each cell gets a kind: a value (a number or a date, by the page's own patterns `NUMBER` and `DATE`), a range of two
numbers (`60–97`), a missing-value token (`MISSING_TOKENS`: `NA`, `-`, `NaN`, ...), or text. The rows are the longest
run of blocks of `k` cells (2 to `MAX_BLOCK`) that repeat one pattern of kinds, start with a text cell (the row's
label), hold at least one value or range, and count at least `MIN_ROWS`, or `MIN_HEADERLESS_ROWS` without a header
line above them (a one-column list `Wert`, `12`, `keine Angabe`, `17` alternates the same way); a missing token
stands in for a value or a range, never for a label. Ties go to the smaller block, and two different patterns that
explain the same cells are ambiguous, so nothing is read. The lines above the rows are the header: one line whose
parts, split at ` · `, `|`, `;`, `,` or a tab, name the `k` columns, or the `k - 1` after the label; or `k` (or
`k - 1`) lines of one name each, under at most one title line. Otherwise the columns get generic names (`label`,
`value 1`, ...). Up to `k` text lines below the rows, such as the table's own column labels repeated at its foot,
are left out. A title and those lines become notes, as the lines the delimited reader leaves out around a table do.
Every other shape is no such table.

A range cell stays one text cell, as pasted (decision of 2026-11-09): the data step splits it into its two numbers
on request (`prepare_data`), and a stored range never changes a value without the user's word.

**An inline list of label/value pairs** (`pair_list_table`): `a:7,b:12,c:5`, `a=7; b=12`, `Apples 7, Pears 12`,
or one pair per line, read as two columns. The pairs are split at `;` and line breaks first, then also at `,`, so a
decimal comma survives where the pairs have another separator (`a: 7,5; b: 12,0`). Every piece must be a pair of the
same form (`label: value`, `label = value` or `label value`) whose value is a number; at least `MIN_ROWS` pairs. A
`label value` pair's label holds a letter and at most `MAX_LABEL_WORDS` words, and a `label:value` pair whose label
ends in a number needs a space after the colon, so a ratio or a clock time (`16:9`, `at 10:30`) is never a pair, while
`Q1:5` and `2024: 7` are. A first
line of a line-per-pair list that holds exactly two words without a digit names the columns; otherwise they are
`label` and `value`.

A change request is never a list (owner decision of 2026-11-09, after `x bis 2030, y bis 60` replaced a user's table
with two `label`/`value` rows): text with a word of a plot wish (`WISH_WORDS`, `LOWERCASE_WISH_WORDS`: `bis`, `max`,
`Titel`, `Linie`, ...) is no pair list, nor is one whose label is an axis letter alone (`x 2030`). While the session
holds data, which a list replaces without `.undo()`, a list takes `MIN_PAIRS_WITH_DATA` pairs (the dataset route's
`min_pairs`). The page reads the same lists (`app/src/sections/agent-chat/wishWords.json`, pinned by a test).

No ADK import.
"""

import re
from dataclasses import dataclass, field
from typing import Literal


MIN_ROWS = 2
"""The fewest rows either layout reads: a single pair or a single block is no table."""
MIN_PAIRS_WITH_DATA = 3
"""The fewest pairs of a list while the session holds data: two are as often a change request in words."""
WISH_WORDS: tuple[str, ...] = (
    "please",
    "bitte",
    "make",
    "set",
    "use",
    "change",
    "plot",
    "show",
    "draw",
    "add",
    "remove",
    "color",
    "colour",
    "title",
    "axis",
    "axes",
    "legend",
    "log",
    "scale",
    "from",
    "to",
    "between",
    "line",
    "lines",
    "font",
    "tick",
    "ticks",
    "grid",
    "limit",
    "limits",
    "range",
    "width",
    "height",
    "mach",
    "mache",
    "setze",
    "zeig",
    "zeige",
    "zeichne",
    "füge",
    "ändere",
    "achse",
    "achsen",
    "titel",
    "von",
    "bis",
    "linie",
    "linien",
    "schrift",
    "schriftgröße",
    "gitter",
    "farbe",
    "breite",
    "höhe",
    "bereich",
    "grenze",
    "margin",
    "margins",
    "padding",
    "dpi",
    "opacity",
    "alpha",
    "bins",
    "rand",
    "abstand",
    "rahmen",
    "transparenz",
    "deckkraft",
)
"""Words of a plot wish or a change request, matched as whole words in any case: the page's `wishWords.json`
(`words`), which `tests/unit/agents/data/test_layouts.py` pins to this tuple."""
LOWERCASE_WISH_WORDS: tuple[str, ...] = ("max", "min")
"""Wish words matched in lowercase or in capitals (`max`, `MAX`), never capitalised: `Max` and `Min` with a capital
are first names (`lowercase_only`)."""
_AXIS_LABEL = re.compile(r"^[xyz]$", re.IGNORECASE)
"""A label that is an axis letter alone: `x 2030` asks about the axis, it is no row."""


def _word_pattern(words: tuple[str, ...], flags: int = 0) -> re.Pattern[str]:
    """Whole words of `words`, bounded by anything that is no letter (`5bis`, `y-Achse`), as the page's `\\p{L}`."""
    return re.compile(rf"(?<![^\W\d_])(?:{'|'.join(map(re.escape, words))})(?![^\W\d_])", flags)


_WISH = _word_pattern(WISH_WORDS, re.IGNORECASE)
_LOWERCASE_WISH = _word_pattern(LOWERCASE_WISH_WORDS + tuple(word.upper() for word in LOWERCASE_WISH_WORDS))


def is_wish(text: str) -> bool:
    """Whether the text holds a word of a plot wish or an instruction (`x bis 2030`, `y max 60`): what the user meant
    to say, however many numbers it holds."""
    return bool(_WISH.search(text) or _LOWERCASE_WISH.search(text))


MIN_HEADERLESS_ROWS = 3
"""The fewest blocks of a one-cell-per-line copy without a header line above them."""
MISSING_TOKENS: frozenset[str] = frozenset(
    {"-", "NA", "N/A", "n/a", "NaN", "nan", "-NaN", "-nan", "null", "NULL", "None", "<NA>", "#N/A", "#N/A N/A", "#NA"}
    | {"1.#IND", "-1.#IND", "1.#QNAN", "-1.#QNAN"}
)
"""The parser's missing-value tokens (`parse.MISSING_VALUES` without the empty cell; a test holds them equal), and the
page's (`routeInput.ts`)."""
MAX_BLOCK = 12
"""The most cells per row a one-cell-per-line copy may hold."""
MAX_LABEL_WORDS = 3
"""The most words of a `label value` pair's label: `New York 5`, never a clause such as `x from 1 to 10`."""
MAX_LABEL_CHARS = 40
LABEL_COLUMN = "label"
VALUE_COLUMN = "value"

NUMBER = re.compile(r"^[+\-−]?[$€£]?\s?(?:\d{1,3}(?:[.,' ]\d{3})+|\d+)?(?:[.,]\d+)?(?:[eE][+-]?\d+)?\s?(?:%|[$€£])?$")
"""A number as a table cell writes it, the page's `NUMBER` (`routeInput.ts`): a sign, thousands groups, a decimal mark,
an exponent, `%`, a currency. A cell must hold a digit as well."""
DATE = re.compile(
    r"^(?:\d{4}-\d{1,2}(?:-\d{1,2})?(?:[T ]\d{1,2}:\d{2}(?::\d{2})?)?|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
    r"|\d{1,2}:\d{2}(?::\d{2})?)$"
)
"""A date or a time, the page's `DATE`: ISO, day-month-year with `.`, `/` or `-`, a clock time."""
RANGE = re.compile(r"^[+\-−]?\d[\d.,']*\s*[-–—]\s*[+\-−]?\d[\d.,']*$")
"""Two numbers joined by a hyphen or a dash: `60–97`, `1,5-2,5`."""
_HEADER_SPLIT = re.compile(r"\s+·\s+|\s*[|;\t]\s*|\s*,\s+")
_PAIR_SPLIT_STRONG = re.compile(r"[;\n]")
_PAIR_SPLIT_ALL = re.compile(r"[,;\n]")
_COLON_PAIR = re.compile(r"^(?P<label>[^:=;,\t]{1,40}?)\s*:(?P<space>\s*)(?P<value>\S.*)$")
_EQUALS_PAIR = re.compile(r"^(?P<label>[^:=;,\t]{1,40}?)\s*=\s*(?P<value>\S.*)$")
_SPACE_PAIR = re.compile(r"^(?P<label>[^:=;,\t]*\S)\s+(?P<value>\S+)$")
_LINE_BREAK = re.compile(r"\r\n|\r|\n")
"""The line breaks the page splits at (`routeInput.ts`); `str.splitlines` would also split at `\\u2028`."""


@dataclass(frozen=True)
class Layout:
    """A table read from a layout: which one, its column names, its rows of cells as pasted, and what the reading
    did, for the paste's warnings (the summary names a reading that changed the text's form)."""

    kind: Literal["cell_lines", "pair_list"]
    headers: list[str]
    rows: list[list[str]]
    note: str
    notes: list[str] = field(default_factory=list)
    """Lines the reading left out (a title, the labels repeated below the rows), for the paste's notes."""


def is_value(cell: str) -> bool:
    """Whether a cell reads as a number or a date, as the page reads it (`routeInput.ts`, `isValue`)."""
    text = cell.strip()
    return bool(text) and any(c.isdigit() for c in text) and bool(NUMBER.match(text) or DATE.match(text))


def cell_kind(cell: str) -> str:
    """`value`, `range`, `missing` or `text`: what a cell of a one-cell-per-line copy is, for the pattern of a row."""
    text = cell.strip()
    if text in MISSING_TOKENS:
        return "missing"
    if is_value(text):
        return "value"
    return "range" if RANGE.match(text) else "text"


def _fits(kind: str, expected: str) -> bool:
    """Whether a cell of `kind` fills a place of the pattern: its kind, or a missing token where a value goes."""
    return kind == expected or "text" not in (kind, expected) and "missing" in (kind, expected)


def read_layout(text: str, *, min_pairs: int = MIN_ROWS) -> Layout | None:
    """The table one of the two layouts reads from the text, the pair list first; None for any other shape."""
    return pair_list_table(text, min_pairs=min_pairs) or cell_lines_table(text)


# --- A web table copied one cell per line -------------------------------------------------


def cell_lines_table(text: str) -> Layout | None:
    """The table of a one-cell-per-line copy (see the module notes), or None when the text has no such shape."""
    cells = [line.strip() for line in _LINE_BREAK.split(text) if line.strip()]
    if len(cells) < 2 * MIN_ROWS:
        return None
    kinds = [cell_kind(cell) for cell in cells]
    found = _blocks(kinds)
    if found is None:
        return None
    start, size, count = found
    lead, rest = cells[:start], cells[start + size * count :]
    rows = [cells[start + i * size : start + (i + 1) * size] for i in range(count)]
    headers, lead_note, notes = _header(lead, size)
    parts = [f"read one cell per line: {count} rows of {size} columns"]
    if lead_note:
        parts.append(lead_note)
    if rest:
        parts.append(f"left out {_lines(len(rest))} below the table, kept as a note")
        notes.append(", ".join(rest))
    return Layout(kind="cell_lines", headers=headers, rows=rows, note="; ".join(parts), notes=notes)


def _blocks(kinds: list[str]) -> tuple[int, int, int] | None:
    """`(start, size, count)` of the rows: the run that explains the most cells, or None when none or two do."""
    found: list[tuple[int, int, int, tuple[str, ...]]] = []
    for size in range(2, MAX_BLOCK + 1):
        # The header above the rows is one line, or one line per column (with or without the label's, under a title).
        for start in sorted({0, 1, size - 1, size, size + 1}):
            run = _run(kinds, start, size)
            if run is not None:
                found.append((start, size, run[0], run[1]))
    if not found:
        return None
    most = max(size * count for _, size, count, _ in found)
    best = [item for item in found if item[1] * item[2] == most]
    start, size, count, pattern = min(best, key=lambda item: (item[1], item[0]))
    # Another pattern that explains as many cells, and is not this one repeated: no rule tells which is meant.
    if any(not _repeats(pattern, other) for _, _, _, other in best):
        return None
    return start, size, count


def _run(kinds: list[str], start: int, size: int) -> tuple[int, tuple[str, ...]] | None:
    """The rows of `size` cells from `start` that repeat one pattern, and the pattern; None when it is no table."""
    if start >= len(kinds) or any(kind != "text" for kind in kinds[:start]):
        return None
    pattern = tuple(kinds[start : start + size])
    if len(pattern) < size or pattern[0] != "text" or not {"value", "range"} & set(pattern):
        return None
    count = 0
    while len(block := kinds[start + count * size : start + (count + 1) * size]) == size and all(
        _fits(kind, expected) for kind, expected in zip(block, pattern, strict=True)
    ):
        count += 1
    rest = kinds[start + count * size :]
    # Below the rows only a label block may stand, such as the column labels a table repeats at its foot.
    least = MIN_ROWS if start else MIN_HEADERLESS_ROWS
    if count < least or len(rest) > size or any(kind != "text" for kind in rest):
        return None
    return count, pattern


def _repeats(pattern: tuple[str, ...], other: tuple[str, ...]) -> bool:
    """Whether one pattern is the other repeated (`text value` and `text value text value`): the same reading."""
    short, long = sorted((pattern, other), key=len)
    return len(long) % len(short) == 0 and short * (len(long) // len(short)) == long


def _header(lead: list[str], size: int) -> tuple[list[str], str, list[str]]:
    """The column names the lines above the rows give, what the reading made of them, and the lines kept as notes
    (a title, or lines that named no columns), as the parser keeps the lines it leaves out around a table."""
    generic = [LABEL_COLUMN, *([VALUE_COLUMN] if size == 2 else [f"{VALUE_COLUMN} {i}" for i in range(1, size)])]
    if not lead:
        return generic, "no header line, so the columns are named " + ", ".join(generic), []
    title: list[str] = []
    if len(lead) == 1:
        names = [part.strip() for part in _HEADER_SPLIT.split(lead[0]) if part.strip()]
    elif len(lead) == size + 1:
        title, names = lead[:1], lead[1:]
    else:
        names = lead
    titled = "the line above the column names kept as a note" if title else ""
    if len(names) == size:
        return names, titled, title
    if len(names) == size - 1:
        said = "; ".join(filter(None, [titled, f"the first column is named {LABEL_COLUMN}"]))
        return [LABEL_COLUMN, *names], said, title
    said = f"{_lines(len(lead))} above the rows named no columns and are kept as a note, so the columns are named "
    return generic, said + ", ".join(generic), [", ".join(lead)]


def _lines(count: int) -> str:
    return f"{count} line{'s' if count != 1 else ''}"


# --- An inline list of label/value pairs ----------------------------------------------------


def pair_list_table(text: str, *, min_pairs: int = MIN_ROWS) -> Layout | None:
    """The two-column table of a list of label/value pairs (see the module notes), or None for any other text, a
    change request (`is_wish`) included. `min_pairs`: `MIN_PAIRS_WITH_DATA` while the session holds data."""
    stripped = text.strip()
    if not stripped or is_wish(stripped):
        return None
    for split in (_PAIR_SPLIT_STRONG, _PAIR_SPLIT_ALL):
        pieces = [piece.strip() for piece in split.split(stripped) if piece.strip()]
        headers = [LABEL_COLUMN, VALUE_COLUMN]
        if "\n" in stripped and len(pieces) > MIN_ROWS and (names := _pair_header(pieces[0])) is not None:
            headers, pieces = names, pieces[1:]
        rows = _pair_rows(pieces, min_pairs)
        if rows is None:
            continue
        named = "" if headers != [LABEL_COLUMN, VALUE_COLUMN] else f", named {LABEL_COLUMN} and {VALUE_COLUMN}"
        note = f"read a list of {len(rows)} label/value pairs as two columns{named}"
        return Layout(kind="pair_list", headers=headers, rows=rows, note=note)
    return None


def _pair_rows(pieces: list[str], min_pairs: int = MIN_ROWS) -> list[list[str]] | None:
    """The `[label, value]` rows of the pieces when every one is a pair of one form, at least `min_pairs`; None at
    the first piece that is not, so a long text that is no list costs one look at its first pieces."""
    if len(pieces) < min_pairs:
        return None
    rows: list[list[str]] = []
    form = None
    for piece in pieces:
        pair = _pair(piece)
        if pair is None or form not in (None, pair[0]):
            return None
        form = pair[0]
        rows.append([pair[1], pair[2]])
    return rows


def is_pair(cell: str) -> bool:
    """Whether a cell is a label with its value (`Hund 7`, `a: 7`), which a header line of names never holds."""
    return _pair(cell.strip()) is not None


def _pair(piece: str) -> tuple[str, str, str] | None:
    """`(form, label, value)` of one piece of the list, or None when it is no label with a number."""
    if match := _COLON_PAIR.match(piece):
        label, value = match.group("label").strip(), match.group("value").strip()
        # `16:9`, `at 10:30`: a ratio or a clock time, never a label and its value (`Q1:5` is one).
        if label and _number(label.split()[-1]) and not match.group("space"):
            return None
        return ("colon", label, value) if label and not _AXIS_LABEL.match(label) and _number(value) else None
    if match := _EQUALS_PAIR.match(piece):
        label, value = match.group("label").strip(), match.group("value").strip()
        return ("equals", label, value) if label and not _AXIS_LABEL.match(label) and _number(value) else None
    if match := _SPACE_PAIR.match(piece):
        label, value = match.group("label").strip(), match.group("value").strip()
        words = label.split()
        # A letter as the page's `\p{L}` reads one (`str.isalpha`: the letter categories alone).
        if not any(c.isalpha() for c in label) or len(words) > MAX_LABEL_WORDS or len(label) > MAX_LABEL_CHARS:
            return None
        return ("space", label, value) if not _AXIS_LABEL.match(label) and _number(value) else None
    return None


def _number(cell: str) -> bool:
    return any(c.isdigit() for c in cell) and NUMBER.match(cell) is not None


def _pair_header(line: str) -> list[str] | None:
    """The two column names a list's first line gives (`Monat Umsatz`), or None when it is no such line."""
    words = line.split()
    if len(words) != 2 or any(c.isdigit() or c in ":=" for c in line):
        return None
    return words
