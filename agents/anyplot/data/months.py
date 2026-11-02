"""Month names and abbreviations, for `make_date` and `set_type` (`prepare.py`) and the parser (`parse.py`).

No import of the other data modules, so both the parser and the operations can use it.
The table covers the eleven languages of the fixed refusals (en, de, fr, es, it, pt, nl,
pl with its genitive, zh, vi, ru with its genitive); a name is compared without case and
diacritics and without a trailing dot (`Jan.`, `März`, `févr.`), and `3月`, `tháng 3`
and the digits 1 to 12 are months too (owner decision of 2026-10-15). A month name with a
year in one cell (`Nov 2026`, `Okt. 2026`, `2026 Nov`) is a month of that year
(`month_year`, live test of 2026-11-01).
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
_SEPARATORS = ",./-"
"""What may stand between a month and its year besides whitespace (`Okt. 2026`, `Nov-2026`, `Tháng 4/2026`), and `年`
after a year (`2026年3月`). `month_year` trims them by hand: a regular expression with a lazy name before a run of
separators backtracks polynomially (CodeQL `py/polynomial-redos`, review of #12512)."""
_YEAR_WORD = "nam"
"""Vietnamese `năm` (year), folded, which may stand between the month and the year (`tháng 3 năm 2026`)."""


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


def month_year(text: str) -> tuple[int, int] | None:
    """The year and the month of a cell that names a month and a year, as `(year, month)`; else None.

    `Nov 2026`, `November 2026`, `Okt. 2026`, `März 2026`, `2026 Nov`, `Nov-2026`,
    `2026年3月` and `tháng 3 năm 2026` all read. The month is a name or abbreviation
    (`month_number`, so `3月` and `tháng 3` count), never digits alone: `03/2026` and
    `2026-03` are numeric formats, which the parser (`YYYY-MM`) and `set_type`
    (`MM/YYYY`) read by their own rules. The year has exactly four ASCII digits, and the
    caller checks its range. A two-digit year is no year here (decision of 2026-11-01):
    `Nov 26` is 26 November as often as November 2026, and the century would be a guess,
    as `make_date` refuses a year `24`. A cell with a day (`26 Nov 2026`) is a date, not a
    month, and is None too.
    """
    cell = text.strip()
    if _is_year(cell[-4:]) and len(cell) > 4:
        year, name = cell[-4:], _name_before_year(cell[:-4])
    elif _is_year(cell[:4]) and len(cell) > 4:
        year, name = cell[:4], _name_after_year(cell[4:])
    else:
        return None
    if not name or fold(name).rstrip(".").strip().isdigit():
        return None
    month = month_number(name)
    return None if month is None else (int(year), month)


def _is_year(text: str) -> bool:
    return len(text) == 4 and text.isascii() and text.isdigit()


def _is_separator(char: str, extra: str = "") -> bool:
    return char.isspace() or char in _SEPARATORS or char in extra


def _without_separators(text: str) -> str:
    end = len(text)
    while end and _is_separator(text[end - 1]):
        end -= 1
    return text[:end]


def _name_before_year(head: str) -> str | None:
    """The month before a year: `head` without its trailing separators (one at least) and a trailing `năm`."""
    name = _without_separators(head)
    if name == head:
        return None  # `Nov2026`, `Nov 12026`: no separator before the four digits
    words = name.rsplit(None, 1)
    return _without_separators(words[0]) if len(words) == 2 and fold(words[1]) == _YEAR_WORD else name


def _name_after_year(tail: str) -> str | None:
    """The month after a year: `tail` without its leading separators (one at least, `年` among them)."""
    start = 0
    while start < len(tail) and _is_separator(tail[start], "年"):
        start += 1
    return tail[start:] if start else None


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
