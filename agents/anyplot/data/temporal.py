"""Integer columns that say when, not how much: years and the parts of a date (month, quarter, week).

Shared by the default bindings (`bindings.weak_measures`, the ranks of a year) and the wide-table
suggestion (`shape.long_suggestion`, which keeps such a column as a key instead of melting it with the
measures). Its own module so `shape` can use it without importing `bindings`, which imports `shape`.
No ADK import.
"""

import re

from ..schemas import ColumnProfile, DatasetProfile


YEAR_RANGE = (1000, 2200)
"""The values a year column holds, inclusive."""
MAX_YEAR_SPAN = 300
"""The widest range of an integer column that counts as years without a year name."""
YEAR_WORDS: frozenset[str] = frozenset(
    {"year", "years", "yr", "jahr", "jahre", "année", "annee", "an", "año", "ano", "anno", "jaar", "år", "rok"}
)
"""Column-name words that say the column holds years (`Jahr`, `year`, `Année`), compared in lower case."""
DATE_PART_WORDS: dict[str, int] = {
    **dict.fromkeys(("month", "monat", "mois", "mes", "mese", "maand", "månad", "miesiac", "miesiąc"), 12),
    **dict.fromkeys(("quarter", "quartal", "trimestre", "kwartaal", "kwartal"), 4),
    **dict.fromkeys(("week", "woche", "kalenderwoche", "semaine", "semana", "settimana"), 53),
}
"""Column-name words that say an integer column numbers a month, a quarter or a week of the year, with the
largest value it then holds. Singular only, and no unit words: `Months since start`, `Dauer (Minuten)`,
`Days to ship` and a `kW` column are measures (review of 2026-10-15)."""

CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
WORDS = re.compile(r"[^\W_]+")


def year_score(column: ColumnProfile) -> int:
    """2 for an integer column of years named so (`Jahr`, `year`), 1 for an unnamed run of whole years, else 0.

    Values count as years when all lie within `YEAR_RANGE` and span at most `MAX_YEAR_SPAN`.
    Without a year name that is not enough (review of 2026-10-15: prices, rents or calories of
    1000 to 2200 look the same): the column must also hold every year of its range, at least
    three (`unique == max - min + 1`), as a yearly series does, in a wide or a long table.
    """
    if column.dtype != "integer" or not isinstance(column.min, float | int) or not isinstance(column.max, float | int):
        return 0
    low, high = YEAR_RANGE
    if not (low <= column.min and column.max <= high and column.max - column.min <= MAX_YEAR_SPAN):
        return 0
    if YEAR_WORDS & set(WORDS.findall(column.name.casefold())):
        return 2
    return 1 if column.unique >= 3 and column.unique == int(column.max - column.min) + 1 else 0


def date_part(column: ColumnProfile, *, has_year: bool) -> bool:
    """An integer column that numbers a month, a quarter or a week of the year.

    Named so (`Month`, `Monat`, `Quartal`, `Woche`, `DATE_PART_WORDS`) and within that
    part's range, or, right after a column of years (`has_year`, see `time_keys`), every
    value from 1 to 12 or from 1 to 4 (live test of 2026-10-15: the `Month` of a
    MeteoSwiss table of `Year`, `Month`, `Temperature` was bound as the value of a time
    series). Durations and units (`Months since start` up to 36, `Dauer (Minuten)`, a
    `kW` column) are measures.
    """
    if column.dtype != "integer" or not isinstance(column.min, float | int) or not isinstance(column.max, float | int):
        return False
    words = WORDS.findall(CAMEL.sub(" ", column.name).casefold())
    highest = max((DATE_PART_WORDS.get(word, 0) for word in words), default=0)
    if highest and 1 <= column.min and column.max <= highest:
        return True
    return has_year and column.min == 1 and column.max in (4, 12) and column.unique == column.max


def time_keys(profile: DatasetProfile) -> set[str]:
    """The integer columns of years or of a part of a date (`year_score`, `date_part`): where a value sits.

    An unnamed 1-to-12 or 1-to-4 column counts as a month or quarter only right after a column of years that
    repeats (`Year, Month, Temperature`: each year once per month): anywhere beside one was too loose (review
    of #12204: in `Jahr, CH, AT, DE`, one row per year, a country whose values ran 1 to 4 became a key).
    """
    columns = profile.columns
    keys: set[str] = set()
    for index, column in enumerate(columns):
        before = columns[index - 1] if index > 0 else None
        after_year = before is not None and year_score(before) > 0 and before.unique < profile.rows
        if year_score(column) or date_part(column, has_year=after_year):
            keys.add(column.name)
    return keys
