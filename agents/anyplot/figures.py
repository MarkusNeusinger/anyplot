"""The figures a root reply states and the numbers its sources hold: the matcher of the number-provenance check.

A figure written in digits in a reply must come from a source (`plugins/number_provenance.py` names them and acts on
what this module finds), or the reply must say that it is not known. The matcher reads number shapes only, never a
word of any language, so it holds for every model; a figure spelled out in words, or scaled by a word (`1.2 million`),
is not read:

* `figures` reads the numeric tokens of a reply. A token is a run of digits with its sign, its group and decimal
  marks, an exponent (`1.2e-5`, `1.2 × 10⁻⁵`) and a percent sign; a leading-dot decimal (`.625`) is one too, and
  full-width digits read as their ASCII forms, with a full-width comma or full stop between two of them as a mark
  (elsewhere it is the punctuation of Chinese or Japanese text, which separates numbers: `12，15`). A date
  (`14.03.2024`, `2024-03-14`, `03/2024`) or a time (`14:30`) is one token of its own, read as its parts. Each token
  gets every reading its marks allow: a single `.` or `,` before exactly three digits (`1.234`) reads as a decimal
  and as a thousands group, a plain space before three digits (`48 310`) as a group and as two numbers, and the
  marks of every language in `language.NUMBER_FORMATS` count, the narrow no-break space of French among them. A
  token whose marks fit no number (`11,22,33`, `3.10.1`) or that no decimal can hold is unread: no figure the check
  can verify, so it stands when a source holds the identical token, and otherwise counts under `unread`, never as
  unsourced.
* What is structurally no figure is not read: a number joined to letters as a label (`v2`, `CO2`, `Q4`, a spec id
  such as `bar-basic-2`, an identifier such as `1f77b4`), a hex colour, a list marker at the start of a line (also
  in emphasis or after heading marks: `**1.**`, `### 2.`), inline code and code blocks, a ratio such as `16:9` that
  is no time of day, a fraction of two small whole numbers (`3/4`), and a keycap digit. A letter of a script written
  without spaces between words does not join a label: the wide letters of Chinese, Japanese and Korean, and Thai,
  Lao, Khmer and Myanmar (`UNSPACED_SCRIPTS`), so `总额是58,214.37元` holds a figure. A number with a unit written
  onto it (`5kg`), three capitals before a number with marks (`EUR2,904.66`) and a number after a label and a colon
  (`Sum:9,357.48`) are figures. An unsigned whole number of at most `SMALL_WHOLE_MAX` is exempt.
* `Sources` holds the numbers of the sources: a JSON number as it is, and in a text only whole tokens read the same
  way, never a run of digits cut out of a longer token, and an unread token as written; the parts of a date or a
  time count only from a date- or time-shaped token. Each number keeps the closed kind of the source it came from
  (`SourceKind`).
* A reply and a source read signs the same way. The term of an equation after a coefficient and a letter keeps its
  sign, glued or spaced (`y=0.42x-1.35`, `y = 0.42x - 1.35`), unless the same letter follows the number after it: a
  range of glued units (`12h-15h`, `12h - 15h`) has no sign, and neither has a range of two plain numbers (`10-20`,
  `10 - 20`, `10–20`).
* A reply figure is sourced when a source number has at least as many decimals and rounds to it: a reply may round a
  source (`153` for `152.64`), never add precision (`0.0420` for a drawn `0.042`). A number of an exact source
  (`EXACT_KINDS`) also matches when the reply writes the same value with more zeros (`12.50` for `12.5`), though
  never through the decimal reading of a group-shaped token (`3,000` is no `3`). A sign the reply writes (a minus of
  any form, or a plus) must match the source's; a figure written without one matches a source of either sign, since
  words carry the sign (`fell by 3.8 %`), and such a match counts apart (`magnitude_only`). A percent figure also
  matches a fraction a hundred times smaller (`37.5 %` for `0.375`), decided per token, and never a limit of the
  service (`COUNT_KINDS`). A date matches a source date with the same year, month and day, in the orders its shape
  allows (a dotted date is day first), a two-digit year as its four-digit form; a time matches a source time with
  the same parts.

No ADK import.
"""

import re
import unicodedata
from bisect import bisect_left, bisect_right
from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal, DecimalException
from typing import Any, Literal

from .language import NUMBER_FORMATS


SourceKind = Literal["tool_result", "session", "user", "service", "memory", "plot_notes", "plot_code", "drawn_text"]
SOURCE_KINDS: tuple[SourceKind, ...] = (
    "tool_result",
    "session",
    "user",
    "service",
    "memory",
    "plot_notes",
    "plot_code",
    "drawn_text",
)
"""The closed kinds of a source, in the order a match credits them, most trusted first: a figure that a tool result and
a drawn text both hold counts as the tool result's, so a figure counted under a later kind stands in no earlier one."""
EXACT_KINDS: frozenset[SourceKind] = frozenset({"tool_result", "session", "user", "service"})
"""The kinds whose numbers are exact values (a tool's JSON, the server's facts, the user's own input): a reply may write
such a value with more zeros, which a JSON number drops (`12.50`, `50 %` for `0.5`). A model-written text (drawn
texts, plot notes, plot code, the plot memory) keeps the strict rule: no more decimals than it writes."""
COUNT_KINDS: frozenset[SourceKind] = frozenset({"service"})
"""The kinds whose numbers are counts and sizes, never a share: they source no figure written with a percent sign."""

SMALL_WHOLE_MAX: int | None = 10
"""The largest whole number written bare (no sign, mark, exponent or percent sign) that the check leaves unread, or
None to read every one. A provisional product setting, not a structure: a larger value saves a re-ask for the counts
and ordinals of the reply's own items, and lets an invented count up to that value pass unread."""

DECIMAL_MARKS = frozenset(spec.decimal for spec in NUMBER_FORMATS.values())
"""`.` and `,`: the decimal marks of the server's number formats."""
GROUP_MARKS = frozenset({spec.thousands for spec in NUMBER_FORMATS.values()} | DECIMAL_MARKS | {"'", "’", " ", " "})
"""Every thousands mark: the server's number formats' (the narrow no-break space of French, the no-break space of
Polish and Russian, `.` and `,`), the apostrophes of Swiss usage, the thin space, and a plain space typed in a chat."""
_TIGHT_MARKS = "".join(sorted(GROUP_MARKS - {" "}))
_SPACES = "    "
"""The spaces that may stand before a percent sign or around an exponent's `×`: plain, no-break, narrow and thin."""
_SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")
_FULL_WIDTH = str.maketrans("０１２３４５６７８９％＋－", "0123456789%+-")
"""Full-width digits and signs as their ASCII forms, one character for one, so every offset stays."""
_FULL_WIDTH_MARK = re.compile("(?<=[０-９])[，．](?=[０-９])")
"""A full-width comma or full stop between full-width digits, a group or decimal mark (`５８，２１４．３７`); elsewhere
it is the punctuation of Chinese or Japanese text, which separates numbers (`12，15`)."""
UNSPACED_SCRIPTS: tuple[tuple[int, int], ...] = (
    (0x0E00, 0x0EFF),  # Thai, Lao
    (0x1000, 0x109F),  # Myanmar
    (0x1780, 0x17FF),  # Khmer
    (0xA9E0, 0xA9FF),  # Myanmar Extended-B
    (0xAA60, 0xAA7F),  # Myanmar Extended-A
)
"""Scripts written without spaces between words whose letters are not wide, so their letters stand beside a number."""
_SIGNS = "+-−"
_MINUS = frozenset("-−")

_TOKEN = re.compile(
    r"(?P<sign>[+\-−])?"
    rf"(?P<body>(?:(?<![\w.,])\.(?=[0-9]))?[0-9]+(?:(?:[{re.escape(_TIGHT_MARKS)}]| (?=[0-9]{{3}}(?![0-9])))[0-9]+)*)"
    r"(?P<exp>[eE][+\-−]?[0-9]+(?![0-9])"
    rf"|[{_SPACES}]?[×x·][{_SPACES}]?10(?:\^[+\-−]?[0-9]+|[⁺⁻]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+))?"
    rf"(?P<pct>[{_SPACES}]?%)?"
)
"""A numeric token: a sign, digits with group or decimal marks between them (a plain space only before a group of
exactly three digits, a leading dot only after no word character), an exponent and a percent sign. What the marks mean
is read afterwards (`_readings`)."""
_DATE = re.compile(
    r"(?<![0-9.,/-])"
    r"(?:(?P<iso>[0-9]{4}-[0-9]{1,2}-[0-9]{1,2})"
    r"|(?P<dmy>[0-9]{1,2}[./-][0-9]{1,2}[./-](?:[0-9]{4}|[0-9]{2}))"
    r"|(?P<ym>[0-9]{4}-[0-9]{2})"
    r"|(?P<my>[0-9]{1,2}/[0-9]{4}))"
    r"(?![0-9]|[.,/-][0-9])"
)
"""A date: `2024-03-14`, `14.03.2024`, `03/14/24`, a year and month as `2024-03` or `03/2024`."""
_TIME = re.compile(r"(?<![0-9:.,])([0-9]{1,2}):([0-9]{2})(?::([0-9]{2}))?(?![0-9]|[:.,][0-9])")
"""A time of day: `14:30`, `08:05:59`."""
_RATIO = re.compile(r"(?<![0-9.,:])[0-9]+(?::[0-9]+)+(?![0-9]|[.,:][0-9])")
"""A ratio or an aspect (`16:9`, `3:2:1`), once the times of day are read: no figure of the data."""
_FRACTION = re.compile(r"(?<![0-9.,/])([0-9]{1,2})/([0-9]{1,2})(?![0-9]|[.,/][0-9])")
"""A fraction such as `3/4`, once the dates are read; skipped when both its numbers are small (`SMALL_WHOLE_MAX`)."""
_KEYCAP = re.compile("[0-9#*]️?⃣")
"""A keycap digit (`1️⃣`): a list marker drawn as a symbol. Enclosed digits (`①`) are no ASCII digit and never read."""
_CODE = re.compile(r"(?s)(`{3,}|~{3,}).*?(?:\1|\Z)|`[^`\n]*`")
"""A code block or an inline code span: code, not a statement about the data."""
_LIST_MARKER = re.compile(
    r"(?m)^([ \t]*(?:#{1,6}[ \t]+)?(?:[-*+•][ \t]+)?(?:\*{1,2}|_{1,2})?\(?)([0-9]{1,3})"
    r"(?=[.)](?:\*{1,2}|_{1,2})?(?:[ \t]|$))"
)
"""A numbered list item's marker at the start of a line (`1.`, `2)`, `(3)`, also under a bullet, in emphasis such as
`**1.**`, or after heading marks such as `### 2.`)."""
_JOINERS = "-./"
"""Marks that join a number to the letters before it into one label (`bar-basic-2`, `v.2`). A colon does not: a
number after `Sum:` is that sum."""
_SPACED_TERM = re.compile(r"[0-9]([^\W\d_])[⁰¹²³⁴⁵⁶⁷⁸⁹]* ?([+\-−]) $")
"""The end of an equation's term (a coefficient and one variable, `0.42x`) and the operator after it, spaced
(`0.42x - 1.35`): the number after it is a signed term, unless it is a range of units (`_unit_range`)."""


@dataclass(frozen=True)
class Reading:
    """One reading of a numeric token: its value and its decimals as written (negative for `1.2e5`, rounded to the
    ten thousands)."""

    value: Decimal
    decimals: int
    grouped: bool = False
    """The decimal reading of a token shaped like a thousands group (`8,000` as 8.000): its zeros are no decimals the
    writer chose, so it never matches an exact source by equal value alone, or every round thousand would stand in
    any source that holds its first digits."""


Slot = tuple[int, int, int | None]
"""A date as (year, month, day); a year and month has no day. The year is as written, two digits or four."""


@dataclass(frozen=True)
class Figure:
    """One numeric token of a text, with every reading of it.

    `numbers` are its readings as a number; `percent` that a percent sign follows it; `signed` that a sign is written
    before it; `date` the parts of a date token as written and `slots` the (year, month, day) readings its shape
    allows; `time` the parts of a time token; `split` the parts of a token whose plain spaces may separate numbers
    rather than group one (`48 310`); `unread` that its marks fit no number, or no decimal holds it."""

    text: str
    numbers: tuple[Reading, ...] = ()
    percent: bool = False
    signed: bool = False
    date: tuple[int, ...] | None = None
    slots: tuple[Slot, ...] = ()
    time: tuple[int, ...] | None = None
    split: tuple["Figure", ...] = ()
    small: bool = False
    """An unsigned whole number at most `SMALL_WHOLE_MAX`, written bare: exempt from the check."""
    unread: bool = False
    at: int = 0
    """Where the token starts in its text, so the figures keep the order they are written in."""


def _decimals(value: Decimal) -> int:
    exponent = value.as_tuple().exponent
    return -exponent if isinstance(exponent, int) else 0


def _group_head(digits: str) -> bool:
    return 1 <= len(digits) <= 3 and digits[0] != "0"


def _groups(runs: list[str]) -> bool:
    return _group_head(runs[0]) and all(len(run) == 3 for run in runs[1:])


def _readings(body: str) -> list[Reading]:
    """Every reading of a token's digits and marks; empty when the marks fit no number (`3.10.1`, `1,23,4`)."""
    marks = [char for char in body if not char.isdigit()]
    runs = re.split(r"[^0-9]", body)
    if not marks:
        return [Reading(Decimal(body), 0)]
    if len(marks) == 1:
        head, tail = runs
        if marks[0] in DECIMAL_MARKS:
            if len(tail) == 3 and _group_head(head):
                # A single mark before exactly three digits is a decimal mark in one language and a group in another.
                return [Reading(Decimal(f"{head}.{tail}"), 3, grouped=True), Reading(Decimal(head + tail), 0)]
            return [Reading(Decimal(f"{head}.{tail}"), len(tail))]
        return [Reading(Decimal(head + tail), 0)] if _groups(runs) else []
    last, before = marks[-1], set(marks[:-1])
    if len(before) == 1 and last in DECIMAL_MARKS and last not in before and _groups(runs[:-1]):
        return [Reading(Decimal("".join(runs[:-1]) + "." + runs[-1]), len(runs[-1]))]
    if len(set(marks)) == 1 and _groups(runs):
        return [Reading(Decimal("".join(runs)), 0)]
    return []


def _exponent(text: str) -> int:
    """The power of ten of an exponent as written: `e-5`, `× 10^-5`, `·10⁻⁵`; raises ValueError past Python's int
    digits."""
    written = text.translate(_SUPERSCRIPTS).replace("−", "-")
    match = re.search(r"(?:[eE]|10\^?)([+-]?[0-9]+)$", written)
    return int(match[1]) if match else 0


def _digit(char: str) -> bool:
    """An ASCII digit; a superscript (`x²`) is an exponent's, not a number's."""
    return "0" <= char <= "9"


def _joins(char: str) -> bool:
    """Whether `char` joins a number into a label: a letter of a script that separates words with spaces, or `_`. A
    wide or full-width letter (Chinese, Japanese, Korean) and a letter of `UNSPACED_SCRIPTS` (Thai, Lao, Khmer,
    Myanmar) stand beside a number without a space in running text."""
    if char == "_":
        return True
    if not char.isalpha() or unicodedata.east_asian_width(char) in ("W", "F"):
        return False
    return not any(low <= ord(char) <= high for low, high in UNSPACED_SCRIPTS)


def _ascii(text: str) -> str:
    """Full-width digits and signs as their ASCII forms, and a full-width comma or full stop between two full-width
    digits as its mark (`_FULL_WIDTH_MARK`), one character for one."""
    return _FULL_WIDTH_MARK.sub(lambda match: "," if match[0] == "，" else ".", text).translate(_FULL_WIDTH)


def _labelled(text: str, start: int) -> bool:
    """Whether the token starting at `start` is joined to letters before it: a label, an id or a colour."""
    before = text[start - 1] if start > 0 else ""
    if before and (_joins(before) or before in "#@"):
        return True
    return before in _JOINERS and start > 1 and _joins(text[start - 2])


def _currency(text: str, start: int, body: str) -> bool:
    """Whether three capitals stand right before a number with group or decimal marks (`EUR2,904.66`): a currency
    code, not a label such as `CO2` or `ID2024`."""
    code = text[max(0, start - 3) : start]
    edge = text[start - 4] if start >= 4 else ""
    bare = not edge or not (edge.isalnum() or edge == "_")
    return len(code) == 3 and code.isascii() and code.isalpha() and code.isupper() and bare and not body.isdigit()


def _identifier_after(text: str, end: int) -> bool:
    """Whether letters follow the token and digits or an underscore follow them: one identifier (`1f77b4`, `2x3`)."""
    index = end
    while index < len(text) and _joins(text[index]) and text[index] != "_":
        index += 1
    if index == end:
        return end < len(text) and text[end] == "_"
    return index < len(text) and (_digit(text[index]) or text[index] == "_")


def _after_term(text: str, sign_at: int) -> bool:
    """Whether the sign at `sign_at` follows an equation's term, a coefficient and one variable (`0.42x-1.35`)."""
    return sign_at >= 2 and _joins(text[sign_at - 1]) and _digit(text[sign_at - 2])


def _unit_range(text: str, letter: str, end: int) -> bool:
    """Whether `letter`, the variable of the term before a sign, also follows the number that ends at `end`: a range
    of units (`12h-15h`, `12h - 15h`), whose dash is no sign. An equation's term ends in no letter (`0.42x-1.35`)."""
    return text[end : end + 1] == letter and not (end + 1 < len(text) and _joins(text[end + 1]))


def _spaced_operator(text: str, body_start: int, end: int) -> tuple[str, int] | None:
    """The operator and its offset when a spaced one stands between an equation's term and this number."""
    window = max(0, body_start - 8)
    match = _SPACED_TERM.search(text[window:body_start])
    if match is None or not _joins(match[1]) or _unit_range(text, match[1], end):
        return None
    return match[2], window + match.start(2)


def _blank(text: str, start: int, end: int) -> str:
    return text[:start] + " " * (end - start) + text[end:]


def _spaces(match: re.Match[str]) -> str:
    return " " * len(match.group(0))


def _date_parts(match: re.Match[str]) -> tuple[int, ...]:
    return tuple(int(part) for part in re.split(r"[./-]", match.group(0)))


def _valid(year: int, month: int, day: int | None) -> bool:
    return 1 <= month <= 12 and (day is None or 1 <= day <= 31)


def _date_slots(match: re.Match[str]) -> tuple[Slot, ...]:
    """The (year, month, day) readings a date token's shape allows; none when no reading is a date. A dotted date
    reads day first; one with slashes or hyphens reads day first and month first, as its parts allow."""
    parts = _date_parts(match)
    if match["iso"]:
        year, month, day = parts
        candidates: list[Slot] = [(year, month, day)]
    elif match["dmy"]:
        first, second, year = parts
        candidates = [(year, second, first)]
        if "." not in match.group(0):
            candidates.append((year, first, second))
    elif match["ym"]:
        candidates = [(parts[0], parts[1], None)]
    else:
        candidates = [(parts[1], parts[0], None)]
    return tuple(dict.fromkeys(slot for slot in candidates if _valid(*slot)))


def _time_parts(match: re.Match[str]) -> tuple[int, ...] | None:
    parts = tuple(int(part) for part in match.groups() if part is not None)
    return parts if parts[0] <= 24 and all(part <= 59 for part in parts[1:]) else None


def _small(first: str, second: str) -> bool:
    return SMALL_WHOLE_MAX is not None and int(first) <= SMALL_WHOLE_MAX and 0 < int(second) <= SMALL_WHOLE_MAX


def figures(text: str, *, reply: bool = True) -> list[Figure]:
    """The figures of `text` in the order they are written, each with its text as written.

    `reply` leaves out what a reply writes as structure, not as a statement (code, list markers, keycaps, ratios,
    small fractions). A source keeps code and list markers, since a number in a tool's code or list is still that
    tool's number. Both keep a token they cannot read as `unread`.
    """
    written = text
    text = _ascii(text)
    found: list[Figure] = []
    if reply:
        text = _CODE.sub(_spaces, text)
        text = _KEYCAP.sub(_spaces, text)
        text = _LIST_MARKER.sub(lambda match: match[1] + " " * len(match[2]), text)
    for match in list(_DATE.finditer(text)):
        if _labelled(text, match.start()):
            continue
        slots = _date_slots(match)
        if slots:
            at, end = match.span()
            found.append(Figure(written[at:end], date=_date_parts(match), slots=slots, at=at))
            text = _blank(text, at, end)
    for match in list(_TIME.finditer(text)):
        if _labelled(text, match.start()):
            continue
        parts = _time_parts(match)
        if parts is not None:
            at, end = match.span()
            found.append(Figure(written[at:end], time=parts, at=at))
            text = _blank(text, at, end)
    if reply:
        text = _RATIO.sub(_spaces, text)
        text = _FRACTION.sub(lambda match: _spaces(match) if _small(match[1], match[2]) else match[0], text)
    for match in _TOKEN.finditer(text):
        figure = _figure(text, written, match)
        if figure is not None:
            found.append(figure)
    return sorted(found, key=lambda figure: figure.at)


def _figure(text: str, written: str, match: re.Match[str]) -> Figure | None:
    """The figure of one token match, or None when it is structurally no figure."""
    sign = match["sign"] or ""
    start, body_start, end = match.start(), match.start("body"), match.end()
    body = match["body"]
    ranged = False
    if sign:
        before = text[start - 1] if start > 0 else ""
        if _digit(before):
            sign, start = "", body_start  # a range (`10-20`): the dash is no minus
        elif before and _joins(before):
            if not _after_term(text, start):
                return None  # an identifier (`x-2`)
            if _unit_range(text, before, end):
                sign, start, ranged = "", body_start, True  # a range of glued units (`12h-15h`)
    else:
        operator = _spaced_operator(text, body_start, end)
        if operator is not None:
            sign, start = operator
    if not sign and not ranged and _labelled(text, body_start) and not _currency(text, body_start, body):
        return None
    if not match["pct"] and _identifier_after(text, end):
        return None
    shown = written[start:end].strip()
    negative = sign in _MINUS
    percent = bool(match["pct"])
    split: tuple[Figure, ...] = ()
    if " " in body:
        # A plain space may group a number (`48 310`) or stand between two (`2023 120`): both readings.
        split = tuple(_plain(part) for part in body.split(" "))
    try:
        exponent = _exponent(match["exp"]) if match["exp"] else 0
        numbers = tuple(
            Reading(
                (-reading.value if negative else reading.value).scaleb(exponent),
                reading.decimals - exponent,
                reading.grouped,
            )
            for reading in _readings(body)
        )
    except DecimalException, ValueError:
        return Figure(shown, signed=bool(sign), unread=True, at=start)  # no decimal holds it (`4e2345678`)
    if not numbers and not split:
        return Figure(shown, signed=bool(sign), unread=True, at=start)
    small = (
        SMALL_WHOLE_MAX is not None
        and not sign
        and not exponent
        and not percent
        and body.isdigit()
        and len(body) <= 6
        and int(body) <= SMALL_WHOLE_MAX
    )
    return Figure(shown, numbers, percent=percent, signed=bool(sign), split=split, small=small, at=start)


def _plain(part: str) -> Figure:
    try:
        return Figure(part, tuple(_readings(part)))
    except DecimalException:
        return Figure(part)


Held = tuple[SourceKind, bool]
"""Where a figure stands: the most trusted kind of source that holds it, and whether it held only by magnitude (the
reply wrote no sign, and every source that holds it is negative)."""


@dataclass
class Sources:
    """The numbers, dates and times of a turn's sources, each with the kind of its source (`SourceKind`)."""

    _numbers: list[tuple[Decimal, int, int]] = field(default_factory=list)
    _dates: list[tuple[tuple[Slot, ...], int]] = field(default_factory=list)
    _times: list[tuple[tuple[int, ...], int]] = field(default_factory=list)
    _tokens: dict[str, int] = field(default_factory=dict)
    """The unread tokens as written, each with the rank of the most trusted source that holds it."""
    _sorted: bool = True

    def add_number(self, value: Decimal, decimals: int, kind: SourceKind) -> None:
        self._numbers.append((value, decimals, SOURCE_KINDS.index(kind)))
        self._sorted = False

    def add_text(self, text: str, kind: SourceKind) -> None:
        """Every whole numeric token of `text`, with every reading; a date's or a time's parts also as numbers, and an
        unread token as written."""
        for figure in figures(text, reply=False):
            self._add_figure(figure, kind)

    def _add_figure(self, figure: Figure, kind: SourceKind) -> None:
        rank = SOURCE_KINDS.index(kind)
        if figure.unread:
            self._tokens[figure.text] = min(rank, self._tokens.get(figure.text, rank))
            return
        if figure.slots:
            self._dates.append((figure.slots, rank))
        if figure.time is not None:
            self._times.append((figure.time, rank))
        for number in (*(figure.date or ()), *(figure.time or ())):
            self.add_number(Decimal(number), 0, kind)
        for reading in figure.numbers:
            self.add_number(reading.value, reading.decimals, kind)
        for part in figure.split:
            self._add_figure(part, kind)

    def add_json(self, value: Any, kind: SourceKind) -> None:
        """Every number of a JSON value: a JSON number as it is, a string's whole tokens (`add_text`)."""
        if isinstance(value, bool) or value is None:
            return
        if isinstance(value, int):
            self.add_number(Decimal(value), 0, kind)
        elif isinstance(value, float):
            if value == value and abs(value) != float("inf"):
                exact = Decimal(repr(value))
                self.add_number(exact, _decimals(exact), kind)
        elif isinstance(value, str):
            self.add_text(value, kind)
        elif isinstance(value, dict):
            for item in value.values():
                self.add_json(item, kind)
        elif isinstance(value, list | tuple):
            for item in value:
                self.add_json(item, kind)

    def kind_of(self, figure: Figure) -> SourceKind | None:
        """The kind of the most trusted source that holds `figure` (`SOURCE_KINDS`), or None when none does."""
        held = self.held(figure)
        return None if held is None else held[0]

    def held(self, figure: Figure) -> Held | None:
        """Where `figure` stands (`Held`), or None when no source holds it. An unread token stands only where a source
        holds the identical token."""
        if figure.unread:
            rank = self._tokens.get(figure.text)
            return None if rank is None else (SOURCE_KINDS[rank], False)
        if figure.slots:
            ranks = [rank for slots, rank in self._dates if _same_date(figure.slots, slots)]
            return (SOURCE_KINDS[min(ranks)], False) if ranks else None
        if figure.time is not None:
            ranks = [rank for parts, rank in self._times if parts[: len(figure.time)] == figure.time]
            return (SOURCE_KINDS[min(ranks)], False) if ranks else None
        direct: list[int] = []
        flipped: list[int] = []
        for reading in figure.numbers:
            direct += self._ranks(reading, reading.value, figure.percent)
            if not figure.signed and reading.value:
                flipped += self._ranks(reading, -reading.value, figure.percent)
        if direct or flipped:
            return SOURCE_KINDS[min(direct + flipped)], not direct
        if figure.split:
            # Read as separate numbers, each must stand in a source; the least trusted of them names the kind.
            kinds = [self.kind_of(part) for part in figure.split]
            known = [kind for kind in kinds if kind is not None]
            if len(known) == len(kinds):
                return max(known, key=SOURCE_KINDS.index), False
        return None

    def _ranks(self, reading: Reading, value: Decimal, percent: bool) -> list[int]:
        """The ranks of the sources that hold `reading` with `value` (its own, or its sign flipped)."""
        if not self._sorted:
            self._numbers.sort()
            self._sorted = True
        wanted = [(value, reading.decimals)]
        if percent:
            # A share written as a percent may stand in a source as its fraction (`37.5 %` for `0.375`).
            wanted.append((value.scaleb(-2), reading.decimals + 2))
        ranks: list[int] = []
        for target, places in wanted:
            ranks += self._near(target, places, equal=not reading.grouped)
        # A limit of the service is a count or a size, never a share.
        return [rank for rank in ranks if SOURCE_KINDS[rank] not in COUNT_KINDS] if percent else ranks

    def _near(self, value: Decimal, decimals: int, *, equal: bool) -> Iterator[int]:
        """The ranks of the source numbers that round to `value` at `decimals` with at least as many decimals, and,
        with `equal`, of the exact ones that equal it."""
        try:
            half = Decimal(5).scaleb(-decimals - 1)
            low = bisect_left(self._numbers, (value - half,))
            high = bisect_right(self._numbers, (value + half, float("inf")))
        except DecimalException:
            return
        for held_value, held, rank in self._numbers[low:high]:
            if held >= decimals or (equal and held_value == value and SOURCE_KINDS[rank] in EXACT_KINDS):
                yield rank


def _same_year(a: int, b: int) -> bool:
    return a == b or (a < 100 <= b and a == b % 100) or (b < 100 <= a and b == a % 100)


def _same_date(wanted: tuple[Slot, ...], held: tuple[Slot, ...]) -> bool:
    """Whether a reading of one date is a reading of the other: year with year (a two-digit year as its four-digit
    form), month with month, day with day."""
    return any(_same_year(a[0], b[0]) and a[1:] == b[1:] for a in wanted for b in held)


@dataclass(frozen=True)
class Provenance:
    """What the check found in one reply: the figures it read, the unsourced ones, and the sourced ones by kind."""

    checked: int
    unsourced: tuple[str, ...]
    """The unsourced figures as the reply writes them, each once, in order."""
    by_kind: dict[SourceKind, int]
    exempt: int = 0
    unread: int = 0
    """The tokens whose marks fit no number or that no decimal holds, and that no source holds as the identical token:
    no figure the check can verify, so never unsourced."""
    magnitude_only: int = 0
    """Of the sourced figures, those written without a sign whose every source is negative."""
    missing: tuple[Figure, ...] = ()
    """The unsourced figures themselves, for a check against another text (`number_provenance.replacement_allowed`);
    never logged."""

    def counts(self) -> dict[str, int]:
        """The content-free counts the attribution line carries; the sourced ones under `from_<kind>`, since the
        line's own `user` and `session` fields name the caller and the session hash."""
        return {
            "figures": self.checked,
            "unsourced": len(self.unsourced),
            "exempt": self.exempt,
            "unread": self.unread,
            "magnitude_only": self.magnitude_only,
            **{f"from_{kind}": self.by_kind.get(kind, 0) for kind in SOURCE_KINDS},
        }


def provenance(reply: str, sources: Sources) -> Provenance:
    """Each figure of `reply` checked against `sources`."""
    unsourced: list[str] = []
    missing: list[Figure] = []
    by_kind: dict[SourceKind, int] = {}
    checked = exempt = unread = magnitude_only = 0
    for figure in figures(reply):
        if figure.small:
            exempt += 1
            continue
        checked += 1
        held = sources.held(figure)
        if held is None:
            if figure.unread:
                unread += 1  # no figure the check can verify: counted, never a reason to ask or withhold
                continue
            missing.append(figure)
            if figure.text not in unsourced:
                unsourced.append(figure.text)
            continue
        kind, by_magnitude = held
        by_kind[kind] = by_kind.get(kind, 0) + 1
        magnitude_only += by_magnitude
    return Provenance(checked, tuple(unsourced), by_kind, exempt, unread, magnitude_only, tuple(missing))
