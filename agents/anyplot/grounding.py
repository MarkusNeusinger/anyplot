"""What the shipped plot shows, and whether it shows what the user asked for: the closing reply's ground.

The live tests of 2026-10-14/15 caught the root describing intentions instead of results:
its closing reply came from the adapter's `changes` notes, written before the render. The
user asked for "6,5 Mio." on the axis, the axis showed "6.0 M", and the reply claimed
"about 6,5 Mio."; another reply said the title was not set while the image showed one.

Two measurements, both code:

* `plot_texts` groups the drawn texts the render's probe reports (`harness.drawn_labels`,
  the `labels` field) by role into `PlotShows.texts`, which the root reads fenced next to the
  result. The probe is written by the code under test, so every value is checked for type
  and clipped; a probe without `labels` (a renderer older than the field) yields None.
* `expected_misses` checks each of the run's `expected_texts` (the texts and number formats
  the user asked to see, verbatim) against those texts. A text must appear in one drawn text
  (case, spacing, quotes, dashes and mathtext markup aside); a number format must show its
  unit (`Mio.`, `%`, `€`) in a drawn text, and the texts that show it must use its decimal
  mark. Each miss becomes a residual line, so the result says it honestly, and with
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
EXPECT_LINE_ID = {"text": "SC-04", "format": "SC-02"}
"""The rubric id a missing requested text (title, legend, label) or number format is reported under."""
_MATHTEXT = re.compile(r"\\mathrm|\\text|[$\\{}]")
_QUOTES = str.maketrans(dict.fromkeys("\"'„“”«»‚‘’`", ""))
_DASHES = str.maketrans({"−": "-", "–": "-", "—": "-", " ": " ", " ": " ", "\xa0": " "})
_DIGIT = re.compile(r"\d")
_NUMBER_PART = re.compile(r"[\d\s.,'’+\-−]+")
_DECIMAL = re.compile(r"\d([.,])(\d+)(?!\d)")


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


def _one_line(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_SHOWN_TEXT_CHARS else text[: MAX_SHOWN_TEXT_CHARS - 1].rstrip() + "…"


def plot_texts(probe: Any) -> dict[ShownGroup, list[str]] | None:
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
        group = _group(kind)
        texts = groups.setdefault(group, [])
        line = _one_line(text)
        if line not in texts and len(texts) < GROUP_LIMITS[group]:
            texts.append(line)
    return {group: groups[group] for group in GROUP_LIMITS if groups.get(group)}


def _norm(text: str) -> str:
    """A text as the comparison reads it: NFKC, case-folded, without quotes and mathtext markup, one space."""
    text = unicodedata.normalize("NFKC", text).translate(_DASHES).translate(_QUOTES)
    text = _MATHTEXT.sub("", text).replace("_", "").replace("^", "")
    return " ".join(text.casefold().split())


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


def expected_misses(expected: Sequence[str], texts: dict[ShownGroup, list[str]] | None) -> list[ExpectMiss]:
    """The requested texts and number formats the drawn texts do not show; none when the probe reported no texts."""
    if texts is None:
        return []
    drawn = [text for group in texts.values() for text in group]
    normed = [_norm(text) for text in drawn]
    title = _norm(" ".join(texts.get("title", [])))
    misses: list[ExpectMiss] = []
    for token in dict.fromkeys(" ".join(item.split()) for item in expected):
        wanted = _norm(token)
        if not wanted or any(wanted in text for text in normed) or wanted in title:
            continue
        if not _DIGIT.search(token):
            misses.append(ExpectMiss(token, "text", _observed(texts, "text")))
            continue
        # A number format: its unit must be drawn, and the texts that draw it must use its decimal mark.
        unit = _norm(" ".join(_NUMBER_PART.sub(" ", token).split()))
        carriers = [text for text in normed if unit in text] if unit else []
        if not unit:
            # A bare number (a year, `6,5`) is a text: it is drawn or it is not.
            misses.append(ExpectMiss(token, "text", _observed(texts, "format")))
            continue
        mark = _decimal_mark(token)
        wrong = None if mark is None else ("." if mark == "," else ",")
        if not carriers or (
            wrong is not None and any(re.search(rf"\d{re.escape(wrong)}\d{{1,2}}(?!\d)", text) for text in carriers)
        ):
            misses.append(ExpectMiss(token, "format", _observed(texts, "format")))
    return misses
