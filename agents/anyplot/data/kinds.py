"""The value kinds of a canonical `data.csv`, finer than its dtypes, for loaders that need them.

The parser types each column as one `ColumnDtype` (`parse.py`), which is all pandas
needs: the Python loader reads `Int64`, `float64`, `boolean`, `string` and
`parse_dates` from the dtypes alone (`code/loader.py`, unchanged). Typed readers of other
languages need two more facts that only the cells tell: whether an integer column fits a
32-bit integer (R's `col_integer()` holds -2,147,483,647 to 2,147,483,647, its
`NA_integer_` being the one value below), and whether a datetime column holds plain dates
only (`2024-01-31`, which `data.csv` writes for a column without a time of day) or
timestamps (`2024-01-31T08:00:00+01:00`). `column_kinds` reads them from the canonical
CSV the session holds, without pandas.

Kinds: `integer` (fits 32 bits), `big-integer` (an integer column past them), `number`,
`boolean`, `text`, `date` (every cell a plain ISO date), `datetime`. A missing cell is
the empty cell and never decides a kind.
"""

import csv
import io
import re
from collections.abc import Iterable, Mapping
from typing import Literal

from ..schemas import ColumnDtype


ColumnKind = Literal["integer", "big-integer", "number", "boolean", "text", "date", "datetime"]
INT32_MAX = 2**31 - 1
"""The largest 32-bit integer; R's `NA_integer_` is -2^31, so its integers are symmetric around 0."""
_PLAIN_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def column_kinds(
    csv_text: str, column_dtypes: Mapping[str, ColumnDtype], parse_dates: Iterable[str] = ()
) -> dict[str, ColumnKind]:
    """The kind of every column of the canonical `csv_text`, in its order, from the parser's dtypes.

    A column in `parse_dates` without a dtype is a datetime. Raises `ValueError` when the
    header names a column twice or a typed column is not in it.
    """
    rows = csv.reader(io.StringIO(csv_text, newline=""))
    header = next(rows, [])
    if len(set(header)) != len(header):
        raise ValueError("data.csv names a column twice")
    unknown = sorted(set(column_dtypes) - set(header))
    if unknown:
        raise ValueError(f"unknown columns: {unknown}")
    dates = set(parse_dates)
    dtypes: dict[str, ColumnDtype] = {
        name: column_dtypes.get(name, "datetime" if name in dates else "text") for name in header
    }
    wide: set[str] = set()
    timed: set[str] = set()
    for row in rows:
        for name, cell in zip(header, row, strict=False):
            if not cell:
                continue
            dtype = dtypes[name]
            if dtype == "integer" and name not in wide and abs(int(cell)) > INT32_MAX:
                wide.add(name)
            elif dtype == "datetime" and name not in timed and not _PLAIN_DATE.fullmatch(cell):
                timed.add(name)
    kinds: dict[str, ColumnKind] = {}
    for name in header:
        dtype = dtypes[name]
        if dtype == "integer":
            kinds[name] = "big-integer" if name in wide else "integer"
        elif dtype == "datetime":
            kinds[name] = "datetime" if name in timed else "date"
        else:
            kinds[name] = dtype
    return kinds
