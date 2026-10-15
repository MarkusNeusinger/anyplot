"""Month names and abbreviations, for `make_date` (`prepare.py`) and the profile's month hint (`parse.py`).

No import of the other data modules, so both the parser and the operations can use it.
The table covers the eleven languages of the fixed refusals (en, de, fr, es, it, pt, nl,
pl with its genitive, zh, vi, ru with its genitive); a name is compared without case and
diacritics and without a trailing dot (`Jan.`, `März`, `févr.`), and `3月`, `tháng 3`
and the digits 1 to 12 are months too (owner decision of 2026-10-15).
"""

import re
import unicodedata


_MONTH_WORDS: tuple[tuple[str, ...], ...] = (
    # One tuple per month: the names and common abbreviations in the eleven languages of the fixed refusals
    # (en, de, fr, es, it, pt, nl, pl with its genitive, zh, vi, ru with its genitive); compared folded (`fold`).
    (
        *("january", "jan", "januar", "janner", "jaenner", "janvier", "janv", "enero", "ene", "gennaio", "gen"),
        *("janeiro", "januari", "styczen", "stycznia", "sty", "一月", "январь", "января", "янв"),
    ),
    (
        *("february", "feb", "februar", "fevrier", "fevr", "fev", "febrero", "febbraio", "fevereiro", "februari"),
        *("luty", "lutego", "lut", "二月", "февраль", "февраля", "фев"),
    ),
    (
        *("march", "mar", "marz", "maerz", "mrz", "mars", "marzo", "marco", "maart", "mrt", "marzec", "marca"),
        *("三月", "март", "марта", "мар"),
    ),
    (
        *("april", "apr", "avril", "avr", "abril", "abr", "aprile", "kwiecien", "kwietnia", "kwi", "四月"),
        *("апрель", "апреля", "апр"),
    ),
    ("may", "mai", "mayo", "maggio", "mag", "maio", "mei", "maj", "maja", "五月", "маи", "мая"),
    (
        *("june", "jun", "juni", "juin", "junio", "giugno", "giu", "junho", "czerwiec", "czerwca", "cze", "六月"),
        *("июнь", "июня", "июн"),
    ),
    (
        *("july", "jul", "juli", "juillet", "juil", "julio", "luglio", "lug", "julho", "lipiec", "lipca", "lip"),
        *("七月", "июль", "июля", "июл"),
    ),
    (
        *("august", "aug", "aout", "agosto", "ago", "augustus", "sierpien", "sierpnia", "sie", "八月", "август"),
        *("августа", "авг"),
    ),
    (
        *("september", "sep", "sept", "septembre", "septiembre", "setiembre", "set", "settembre", "setembro"),
        *("wrzesien", "wrzesnia", "wrz", "九月", "сентябрь", "сентября", "сен", "сент"),
    ),
    (
        *("october", "oct", "oktober", "okt", "octobre", "octubre", "ottobre", "ott", "outubro", "out"),
        *("pazdziernik", "pazdziernika", "paz", "十月", "октябрь", "октября", "окт"),
    ),
    (
        *("november", "nov", "novembre", "noviembre", "novembro", "listopad", "listopada", "lis", "十一月"),
        *("ноябрь", "ноября", "ноя"),
    ),
    (
        *("december", "dec", "dezember", "dez", "decembre", "diciembre", "dic", "dicembre", "dezembro", "grudzien"),
        *("grudnia", "gru", "十二月", "декабрь", "декабря", "дек"),
    ),
)
MIN_NAMED_MONTHS = 3
"""The distinct months from which a text column of month names is a calendar (`named_months`)."""
_NUMBERED_MONTH = re.compile(r"(?:thang\s*)?([0-9]{1,2})\s*(?:月)?")
"""A month written with its number: `3月` (Chinese), `tháng 3` (Vietnamese, folded to `thang 3`), `03`."""


def fold(text: str) -> str:
    """Lower case without diacritics: `März` is `marz`, `Février` `fevrier`, `Май` `маи`."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


MONTH_NAMES: dict[str, int] = {fold(word): number for number, words in enumerate(_MONTH_WORDS, 1) for word in words}
"""A folded month name or abbreviation (`marz`, `fevr`, `маи`) to its number, from `_MONTH_WORDS`."""


def month_number(text: str) -> int | None:
    """The month 1 to 12 a cell names, or None."""
    key = fold(text).rstrip(".").strip()
    if key.isascii() and key.isdigit():
        return int(key) if 1 <= int(key) <= 12 else None
    if (match := _NUMBERED_MONTH.fullmatch(key)) is not None:
        number = int(match.group(1))
        return number if 1 <= number <= 12 else None
    return MONTH_NAMES.get(key)


def named_months(cells: list[str]) -> list[int] | None:
    """The months a text column names, ascending and distinct, when every cell is a month by its name; else None.

    Every non-empty cell must read as a month (`month_number`) and at least one must be a
    name rather than digits (a column of `1` to `12` is a number column, or kept text on
    purpose). At least `MIN_NAMED_MONTHS` distinct months: two short words such as `set` and
    `out` are more likely a category than September and October. The profile carries the
    result (`ColumnProfile.months`), because its five top values cannot say whether `Jan` to
    `Mai` is the whole column or the start of `Jan` to `Jun` (live test of 2026-10-15).
    """
    present = {cell for cell in cells if cell}
    if not present or all(fold(cell).rstrip(".").strip().isdigit() for cell in present):
        return None
    months: set[int] = set()
    for cell in present:
        month = month_number(cell)
        if month is None:
            return None
        months.add(month)
    return sorted(months) if len(months) >= MIN_NAMED_MONTHS else None
