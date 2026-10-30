"""The canonical `data.csv` as typed JSON, for the JavaScript render harness (`window.ANYPLOT_DATA`).

JavaScript has no reader of its own for the canonical CSV: the plan's JavaScript
runtime gives the page the table as JSON that this module types from the CSV and its
`ColumnKinds` (`kinds.py`), so the canonical data keeps one reader (step 3d of
agentic/specs/261024-agent-all-libraries.md, adopted from the second opinion of
2026-10-30). The render job carries the text next to `data_csv`; the renderer writes it
as `data.json` beside the code file, and `automation/js-render/render.mjs` (sandbox
mode, `ANYPLOT_DATA_JSON`) builds one object per row from it in the page.

The shape is pandas' `split` orientation, which keeps the text near the CSV's size
(records would repeat every column name in every row)::

    {"columns": ["Month", "Sales"], "data": [["2024-01-31", 12.5], ["2024-02-29", null]]}

The value of a cell follows its column's kind:

* `integer` and `big-integer`: the JSON integer as written. JavaScript reads every
  number as a double, so an integer past ±2^53 loses its last digits in the page;
  `ColumnKinds.inexact` counts those cells per column, for the runtime to announce
  (data-fidelity rule, as R's loader does).
* `number`: the float (`data.csv` holds only finite numbers).
* `boolean`: `true` or `false` (`data.csv` writes `True` and `False`).
* `text`: the cell verbatim, also when it looks like a number (`001`, `NA`).
* `date`: the cell verbatim, `YYYY-MM-DD`.
* `datetime`: an ISO string in UTC with milliseconds, `2024-01-31T07:00:00.000Z`, which
  `new Date(...)` reads as the same instant everywhere. A cell with an offset or `Z` is
  converted to UTC (`ColumnKinds.offset` counts the cells that moves to another clock
  time); a cell without one is read as written, as UTC, as R's and Julia's
  loaders read it; a plain date in a timestamp column is its midnight. The fraction is
  truncated to milliseconds, which a JavaScript `Date` holds; `ColumnKinds.submillisecond`
  counts the cells that changes. A cell that UTC would move outside the years 1 to 9999
  (`0001-01-01T00:30:00+01:00`) raises `ValueError`, which no parse writes in practice.
* A missing cell (the empty cell, whatever the kind): `null`.

`json.dumps` escapes nothing for HTML: the harness escapes `<`, U+2028 and U+2029 where
it puts the text into the page. No ADK import: a pure function of the CSV and the kinds.
"""

import csv
import io
import json
import math
import re
from collections.abc import Callable
from datetime import datetime, timedelta

from .kinds import MILLISECOND_DIGITS, TIMESTAMP, ColumnKind, ColumnKinds


def typed_json(csv_text: str, kinds: ColumnKinds) -> str:
    """The canonical `csv_text` as `{"columns": [...], "data": [[...], ...]}`, each cell typed by its column's kind.

    `kinds` is `read_kinds` of the same text: its columns must be the CSV header, in
    order. Raises `ValueError` for a header that does not match, a row of another
    width, or a cell its kind cannot hold (which a canonical CSV never has).
    """
    rows = csv.reader(io.StringIO(csv_text, newline=""))
    header = next(rows, [])
    if header != list(kinds.kinds):
        raise ValueError("the kinds do not name the CSV's columns in order")
    readers = [_READERS[kinds.kinds[name]] for name in header]
    data: list[list[object]] = []
    for number, row in enumerate(rows, start=2):
        if len(row) != len(header):
            raise ValueError(f"line {number} of data.csv has {len(row)} cells for {len(header)} columns")
        data.append([reader(cell) if cell else None for reader, cell in zip(readers, row, strict=True)])
    return json.dumps({"columns": header, "data": data}, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _number(cell: str) -> float:
    value = float(cell)
    if not math.isfinite(value):
        raise ValueError(f"not a finite number: {cell!r}")
    return value


def _boolean(cell: str) -> bool:
    if cell not in ("True", "False"):
        raise ValueError(f"not a canonical boolean: {cell!r}")
    return cell == "True"


def _date(cell: str) -> str:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", cell):
        raise ValueError(f"not a plain ISO date: {cell!r}")
    return cell


def _datetime(cell: str) -> str:
    """The cell as `YYYY-MM-DDTHH:MM:SS.sssZ`: in UTC, the fraction truncated to milliseconds."""
    match = TIMESTAMP.fullmatch(cell)
    if match is None:
        raise ValueError(f"not an ISO timestamp: {cell!r}")
    year, month, day, hour, minute, second, fraction, offset = match.groups()
    milliseconds = int(((fraction or "") + "000")[:MILLISECOND_DIGITS])
    stamp = datetime(
        int(year), int(month), int(day), int(hour or 0), int(minute or 0), int(second or 0), milliseconds * 1000
    )
    if offset and offset != "Z":
        digits = offset[1:].replace(":", "")
        shift = timedelta(hours=int(digits[:2]), minutes=int(digits[2:4] or 0))
        try:
            stamp = stamp - shift if offset[0] == "+" else stamp + shift
        except OverflowError:
            raise ValueError(f"{cell!r} is outside the years 1 to 9999 in UTC") from None
    return (
        f"{stamp.year:04d}-{stamp.month:02d}-{stamp.day:02d}T{stamp.hour:02d}:{stamp.minute:02d}:{stamp.second:02d}"
        f".{stamp.microsecond // 1000:03d}Z"
    )


_READERS: dict[ColumnKind, Callable[[str], object]] = {
    "integer": int,
    "big-integer": int,
    "number": _number,
    "boolean": _boolean,
    "text": str,
    "date": _date,
    "datetime": _datetime,
}
