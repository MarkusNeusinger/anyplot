"""What the shipped plot shows, and whether it shows what the user asked for: the closing reply's ground.

The live tests of 2026-10-14/15 caught the root describing intentions instead of results:
its closing reply came from the adapter's `changes` notes, written before the render. The
user asked for "6,5 Mio." on the axis, the axis showed "6.0 M", and the reply claimed
"about 6,5 Mio."; another reply said the title was not set while the image showed one.

Two measurements, both code:

* `drawn_texts` reads the drawn texts the render's probe reports (`harness.drawn_labels`,
  the `labels` field) by role, every one of them; `plot_texts` clips them into
  `PlotShows.texts`, which the root reads fenced next to the result. The probe is written by
  the code under test, so every value is checked for type and clipped; a probe without
  `labels` (a renderer older than the field, or a failed text report) yields None, and a
  run with requested texts then carries `UNVERIFIED_LINE` instead of a silent pass.
* `expected_misses` checks each of the run's `expected_texts` (the texts and number formats
  the user asked to see, verbatim) against all drawn texts, never the clipped summary. A
  text (`Population 2025`, `Top 10`) must stand whole in one drawn text (case, spacing,
  quotes, dashes and mathtext markup aside). A number-format example (`format_unit`: a
  number with one short unit, `6,5 Mio.`, `12 %`, `CHF 6,5`) must draw its unit, and every
  text it applies to (the texts that draw the unit, and the tick labels of an axis whose
  label or ticks draw it) must use its decimal mark, dates and three-digit groups aside.
  Each miss becomes a residual line, so the result says it honestly, and with
  `AGENT_EXPECT_CHECK=repair` a measured finding the repair round gets.
"""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .schemas import MAX_SHOWN_TEXT_CHARS, ShownGroup


MAX_LABELS = 150
"""The probe entries read (`harness.LABEL_LIMIT`); more is a tampered probe and the rest is ignored."""
MAX_DRAWN_CHARS = 200
"""One drawn text as the check reads it (`harness.LABEL_CHARS`): longer than any requested text."""
GROUP_LIMITS: dict[ShownGroup, int] = {
    "title": 3,
    "x axis label": 2,
    "y axis label": 2,
    "z axis label": 2,
    "other axis labels": 3,
    "legend": 12,
    "x tick labels": 8,
    "y tick labels": 8,
    "z tick labels": 8,
    "annotations": 8,
    "other texts": 6,
}
"""Distinct texts `PlotShows.texts` keeps per role: enough to quote a title or read a tick format, and
at most 62 texts of `MAX_SHOWN_TEXT_CHARS` (about 5 KB) next to the result's other fields."""
UNVERIFIED_LINE = (
    "SC-04 ({theme}): the requested texts could not be checked, since the renderer reported no drawn texts "
    "→ compare them with the image. Likely cause: a renderer without the probe's text report."
)
"""The residual line of a render with requested texts but no `labels` in its probe: never a silent pass."""
EXPECT_LINE_ID = {"text": "SC-04", "format": "SC-02"}
"""The rubric id a missing requested text (title, legend, label) or number format is reported under."""
_MATH_SPACE = re.compile(r"\\[,;:! ]|\\(?:times|cdot|quad|qquad)\b")
"""Mathtext that draws a space or a multiplication sign: read as a space."""
_MATH_MARKUP = re.compile(r"\\[A-Za-z]+|[$\\{}_^]")
"""Any other mathtext command (`\\mathdefault`, `\\mathrm`) and markup character: dropped, so `CO$_2$` reads `CO2`."""
_QUOTES = str.maketrans(dict.fromkeys("\"'„“”«»‚‘’`", ""))
_DASHES = str.maketrans({"−": "-", "–": "-", "—": "-", " ": " ", " ": " ", "\xa0": " "})
_NUMBER = r"[+\-−]?\d(?:[\d.,'’ ]*\d)?"
_FORMAT = re.compile(
    rf"^(?:(?P<pre>[A-Z]{{3}}|[€$£¥]) ?{_NUMBER}|{_NUMBER} ?(?P<post>%|‰|°[CF]?|[€$£¥]|[A-Za-zÄÖÜäöüµ]{{1,4}}\.?))$"
)
"""A number-format example: a number with one unit, a currency code or sign before it (`CHF 6,5`, `€12`), or a
percent sign, a degree or a short unit word after it (`12 %`, `6,5 Mio.`, `1,5 m`). Anything else that holds a
digit (`Population 2025`, `Top 10`, `CO2`, `1960–2023`) is a text and must be drawn as written."""
_DECIMAL = re.compile(r"\d([.,])(\d+)(?!\d)")
_DATE = re.compile(r"\b\d{1,4}[./-]\d{1,2}[./-]\d{1,4}\b")
"""A date such as `31.12.2023` or `2023-12-31`, whose dots are no decimal mark."""


KIND_GROUPS: dict[str, ShownGroup] = {
    "title": "title",
    "suptitle": "title",
    "x axis label": "x axis label",
    "y axis label": "y axis label",
    "z axis label": "z axis label",
    "legend text": "legend",
    "x tick label": "x tick labels",
    "y tick label": "y tick labels",
    "z tick label": "z tick labels",
    "annotation": "annotations",
}
"""The `PlotShows.texts` role of each probe `kind` (`harness._text_kinds` and `drawn_labels`'s tick labels)."""
TICK_GROUPS: tuple[ShownGroup, ...] = ("y tick labels", "x tick labels", "z tick labels")


def _group(kind: str) -> ShownGroup:
    """The role of a probe `kind`; a polar or figure axis label is another axis label, anything else another text."""
    if kind in KIND_GROUPS:
        return KIND_GROUPS[kind]
    return "other axis labels" if kind.endswith("axis label") else "other texts"


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


@dataclass(frozen=True)
class DrawnTexts:
    """Every drawn text the probe reported, by role, unclipped beyond the harness's own cap: what the check reads.

    `complete` is False when the harness dropped texts other than tick labels for its
    entry cap (`labels_truncated`), so a text missing from them may still be drawn.
    """

    groups: dict[ShownGroup, list[str]]
    complete: bool = True


def drawn_texts(probe: Any) -> DrawnTexts | None:
    """The drawn texts of a render by role, from its probe's `labels`; None when the probe has none."""
    if not isinstance(probe, dict):
        return None
    labels = probe.get("labels")
    if not isinstance(labels, list):
        return None
    groups: dict[ShownGroup, list[str]] = {}
    for entry in labels[:MAX_LABELS]:
        if not isinstance(entry, dict):
            continue
        kind, text = entry.get("kind"), entry.get("text")
        if not isinstance(kind, str) or not isinstance(text, str) or not text.strip():
            continue
        texts = groups.setdefault(_group(kind), [])
        line = _clip(text, MAX_DRAWN_CHARS)
        if line not in texts:
            texts.append(line)
    complete = probe.get("labels_truncated") is not True and len(labels) <= MAX_LABELS
    return DrawnTexts({group: groups[group] for group in GROUP_LIMITS if groups.get(group)}, complete)


def plot_texts(drawn: DrawnTexts | None) -> dict[ShownGroup, list[str]] | None:
    """`PlotShows.texts`: the drawn texts within `GROUP_LIMITS` and `MAX_SHOWN_TEXT_CHARS`, for the root's reply."""
    if drawn is None:
        return None
    return {
        group: list(dict.fromkeys(_clip(text, MAX_SHOWN_TEXT_CHARS) for text in texts))[: GROUP_LIMITS[group]]
        for group, texts in drawn.groups.items()
    }


def _norm(text: str) -> str:
    """A text as the comparison reads it: NFKC, case-folded, without quotes and mathtext markup, one space."""
    text = unicodedata.normalize("NFKC", text).translate(_DASHES).translate(_QUOTES)
    text = _MATH_MARKUP.sub("", _MATH_SPACE.sub(" ", text))
    return " ".join(text.casefold().split())


def _contains(text: str, wanted: str) -> bool:
    """`wanted` stands in `text` as a whole: `Kanton 2` is not in `Kanton 20`, `Zürich` is in `Kanton Zürich`."""
    return re.search(rf"(?<!\w){re.escape(wanted)}(?!\w)", text) is not None


def _has_unit(text: str, unit: str) -> bool:
    """`unit` stands in `text` with no letter right before or after it: `m` in `1,5 m` and `(m)`, not in `im`."""
    return re.search(rf"(?<![^\W\d_]){re.escape(unit)}(?![^\W\d_])", text) is not None


def _wrong_mark(text: str, wrong: str) -> bool:
    """Whether `text` writes a number with the `wrong` decimal mark, dates aside.

    A mark before one, two or four and more digits is a decimal mark (`6.0`, `6.25`,
    `1.1250`); before exactly three it is ambiguous, as likely a thousands separator
    (`1.125` reads as 1125 in German), so it is never counted as wrong.
    """
    text = _DATE.sub(" ", text)
    return re.search(rf"\d{re.escape(wrong)}(?:\d{{1,2}}|\d{{4,}})(?!\d)", text) is not None


@dataclass(frozen=True)
class ExpectMiss:
    """A requested text or number format the drawn texts do not show, with what they show instead."""

    expected: str
    kind: str
    """`text` or `format`."""
    observed: str

    def line(self, theme: str) -> str:
        what = "number format" if self.kind == "format" else "text"
        return (
            f'{EXPECT_LINE_ID[self.kind]} ({theme}): the plot does not show the requested {what} "{self.expected}" '
            f"({self.observed}) → write it exactly as the user asked"
            + (", in the tick formatter or the value labels" if self.kind == "format" else "")
            + ". Likely cause: the adaptation wrote another text or format, or none."
        )


def _decimal_mark(token: str) -> str | None:
    """The decimal mark a number token uses: `,` in `6,5`, `.` in `6.5`; a group of three reads as thousands."""
    match = _DECIMAL.search(token)
    if match is None:
        return None
    if len(match[2]) == 3:
        return "," if match[1] == "." else "."
    return match[1]


def _quote(texts: Sequence[str], limit: int = 3) -> str:
    return ", ".join(f'"{text}"' for text in texts[:limit])


def _observed(texts: dict[ShownGroup, list[str]], kind: str) -> str:
    """What the plot shows instead, for the miss's line: the tick labels for a format, the title for a text."""
    if kind == "format":
        for group in TICK_GROUPS:
            if texts.get(group):
                return f"its {group} read {_quote(texts[group])}"
        return "it shows no tick labels"
    if texts.get("title"):
        return f"its title reads {_quote(texts['title'], 1)}"
    return "it has no title"


def format_unit(token: str) -> str | None:
    """The unit of a number-format example (`Mio.` in `6,5 Mio.`, `%` in `12 %`, `CHF` in `CHF 6,5`), or None.

    Only a number with one short unit before or after it is a format example; a text with a
    number in it (`Population 2025`, `1960–2023`) is a text and must be drawn as written.
    """
    match = _FORMAT.match(" ".join(unicodedata.normalize("NFKC", token).split()))
    if match is None:
        return None
    return match["pre"] or match["post"]


def _format_texts(drawn: DrawnTexts, unit: str) -> list[str]:
    """The texts a number format applies to: every text that draws its unit, with all tick labels of its axis
    when that text is a tick label or the axis label (`Bevölkerung (Mio.)` over ticks `6.0`, `7.0`)."""
    texts: list[str] = []
    for group, entries in drawn.groups.items():
        if not any(_has_unit(_norm(text), unit) for text in entries):
            continue
        if group.endswith("tick labels"):
            texts += entries
            continue
        texts += [text for text in entries if _has_unit(_norm(text), unit)]
        axis = group.removesuffix(" axis label")
        if axis in ("x", "y", "z"):
            texts += drawn.groups.get(TICK_OF_AXIS[axis], [])
    return texts


TICK_OF_AXIS: dict[str, ShownGroup] = {"x": "x tick labels", "y": "y tick labels", "z": "z tick labels"}


def expected_misses(expected: Sequence[str], drawn: DrawnTexts | None) -> list[ExpectMiss]:
    """The requested texts and number formats the drawn texts do not show; none when the probe reported no texts.

    A text must be drawn as written within one drawn text (case, spacing, quotes, dashes and
    mathtext aside); when the harness dropped texts for its cap, a missing text is not claimed.
    A number format (`format_unit`) must draw its unit, and every text it applies to
    (`_format_texts`) must use its decimal mark, also when one of them matches the example.
    """
    if drawn is None:
        return []
    shown = plot_texts(drawn) or {}
    normed = [_norm(text) for texts in drawn.groups.values() for text in texts]
    title = _norm(" ".join(drawn.groups.get("title", [])))
    misses: list[ExpectMiss] = []
    for token in dict.fromkeys(" ".join(item.split()) for item in expected):
        wanted = _norm(token)
        if not wanted:
            continue
        unit = format_unit(token)
        if unit is None:
            if not (any(_contains(text, wanted) for text in normed) or _contains(title, wanted)) and drawn.complete:
                misses.append(ExpectMiss(token, "text", _observed(shown, "text")))
            continue
        applies = [_norm(text) for text in _format_texts(drawn, _norm(unit))]
        mark = _decimal_mark(token)
        wrong = None if mark is None else ("." if mark == "," else ",")
        if not applies or (wrong is not None and any(_wrong_mark(text, wrong) for text in applies)):
            misses.append(ExpectMiss(token, "format", _observed(shown, "format")))
    return misses
