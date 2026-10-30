"""The "what changed" line of a loader that changes cells when it reads `data.csv` (`RuntimeAdapter.loader_notes`).

R reads integer cells past ±2^53 as the nearest double (`runtimes/r.py`), Julia keeps a timestamp to the
millisecond (`runtimes/julia.py`), and JavaScript does both (`runtimes/javascript.py`). Each announces the cells
it changed in one change note with the counts per column (owner rule of 2026-10-15: no silent loss, every change
announced with counts), which the pipeline puts first in the shipped version's "what changed" list (owner
decision of 2026-10-29). All three also read a timestamp with a UTC offset in UTC, which shows it at another clock
time: `offset_note` words that for every such runtime alike (owner decision of 2026-10-30).
"""

from collections.abc import Mapping

from ...schemas import MAX_CHANGE_CHARS


ELLIPSIS = "…"


def counted_note(head: str, counts: Mapping[str, int]) -> str:
    """`head`, then each column of `counts` with its count, as many as fit a change note (`MAX_CHANGE_CHARS`), and
    the rest counted as `and N more columns`; never longer than `MAX_CHANGE_CHARS`, which `PlotResult.changes`
    enforces.

    A column name has at most 64 characters (`schemas.MAX_COLUMN_NAME_CHARS`) and a total count up to seven with
    its thousands comma (50 columns of `schemas.MAX_ROWS`, 20,000 rows each), so a long head ("JavaScript reads
    1,000,000 integers ...") can leave no room for even the first column in full: its name is then cut with an
    ellipsis (second opinion of 2026-10-30 on JS-4a, which measured 201 to 208 characters). `counts` holds at
    least one column.
    """
    items = [f"{count:,} in '{name}'" for name, count in counts.items()]
    for shown in range(len(items), 0, -1):
        more = len(items) - shown
        rest = f", and {more} more column{'s' if more != 1 else ''}" if more else ""
        line = head + ", ".join(items[:shown]) + rest
        if len(line) <= MAX_CHANGE_CHARS:
            return line
    name, count = next(iter(counts.items()))
    room = MAX_CHANGE_CHARS - len(line) + len(name) - len(ELLIPSIS)
    return head + f"{count:,} in '{name[: max(room, 0)]}{ELLIPSIS}'" + rest


def offset_note(language: str, counts: Mapping[str, int]) -> str:
    """The change note of a loader that reads timestamps with a UTC offset in UTC (`ColumnKinds.offset`): the
    instant stays exact, the clock time the plot shows moves (`08:00+01:00` shows as `07:00`). `counts` holds at
    least one column."""
    total = sum(counts.values())
    noun, pronoun = ("timestamp", "its") if total == 1 else ("timestamps", "their")
    head = f"{language} converts {total:,} {noun} with a time-zone offset to UTC, so the plot shows {pronoun} UTC clock time: "
    return counted_note(head, counts)
