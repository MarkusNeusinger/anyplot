"""The "what changed" line of a loader that changes cells when it reads `data.csv` (`RuntimeAdapter.loader_notes`).

R reads integer cells past ±2^53 as the nearest double (`runtimes/r.py`) and Julia keeps a timestamp to the
millisecond (`runtimes/julia.py`). Each announces the cells it changed in one change note with the counts per
column (owner rule of 2026-10-15: no silent loss, every change announced with counts), which the pipeline puts
first in the shipped version's "what changed" list (owner decision of 2026-10-29).
"""

from collections.abc import Mapping

from ...schemas import MAX_CHANGE_CHARS


def counted_note(head: str, counts: Mapping[str, int]) -> str:
    """`head`, then each column of `counts` with its count, as many as fit a change note (`MAX_CHANGE_CHARS`), and
    the rest counted as `and N more columns`.

    The first column always fits when `head` leaves room for it: a column name has at most 64 characters
    (`schemas.MAX_COLUMN_NAME_CHARS`) and a count at most six with its thousands comma (`schemas.MAX_ROWS`, 20,000).
    `counts` holds at least one column.
    """
    items = [f"{count:,} in '{name}'" for name, count in counts.items()]
    line = head + items[0]
    for shown in range(len(items), 0, -1):
        more = len(items) - shown
        rest = f", and {more} more column{'s' if more != 1 else ''}" if more else ""
        line = head + ", ".join(items[:shown]) + rest
        if len(line) <= MAX_CHANGE_CHARS:
            break
    return line
