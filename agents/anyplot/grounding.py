"""What the shipped plot shows, and whether it shows what the user asked for: the closing reply's ground.

The live tests of 2026-10-14/15 caught the root describing intentions instead of results:
its closing reply came from the adapter's `changes` notes, written before the render. The
user asked for "6,5 Mio." on the axis, the axis showed "6.0 M", and the reply claimed
"about 6,5 Mio."; another reply said the title was not set while the image showed one.

Two measurements, both code:

* `drawn_texts` reads the drawn texts the render's probe reports (the `labels` field) by
  role, every one of them; `plot_texts` clips them into `PlotShows.texts`, which the root
  reads fenced next to the result. Every library's render reports them since 2026-11-01:
  matplotlib, seaborn and plotnine through `harness.drawn_labels`, pygal, altair and
  lets-plot through `harness.install_text_probes`, the JavaScript libraries, plotly and bokeh
  through the browser harness (`render.mjs`, `writeTextProbe`), ggplot2 and Makie through the
  text probes their rows load (`text_probe.R`, `text_probe.jl`, `harness.collect_text_probe`).
  The probe is written by the code under test, so every value is checked for type and
  clipped; a probe without `labels` (a failed text report) yields None, which the root never
  sees (`plugins/tool_safety.fence_pipeline_notes` drops it), and a run with requested texts
  then carries `UNVERIFIED_LINE` instead of a silent pass.
* `expected_misses` checks each of the run's `expected_texts` (the texts and number formats
  the user asked to see, verbatim) against all drawn texts, never the clipped summary. A
  text (`Population 2025`, `Top 10`) must stand whole in one drawn text (case, spacing,
  quotes, dashes and mathtext markup aside). A number-format example (`format_unit`: a
  number with one short unit, `6,5 Mio.`, `12 %`, `CHF 6,5`) must draw its unit, and every
  text it applies to (the texts that draw the unit, and the tick labels of an axis whose
  label or ticks draw it) must use its decimal mark, dates and three-digit groups aside.
  Each miss becomes a residual line, so the result says it honestly, and with
  `AGENT_EXPECT_CHECK=repair` a measured finding the repair round gets.

`expected_misses` reads matplotlib's drawn texts only. Every other library is checked by the
reviewer instead (`RuntimeAdapter.review_texts`, owner decision of 2026-10-29): its probe reads
the texts from the library's own roles or chart model, which a plugin's own drawing is not in,
so it grounds the reply but never claims a requested text missing. The review request carries
the requested texts, the reviewer reports each one it cannot find in the image as a defect line
under `EXPECT_LINE_ID` that quotes it, and `reviewed_misses` reads those lines back. Only a
render no readable review answered for keeps `UNVERIFIED_LINE`.
"""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from core.defects import DEFECT_RE

from .schemas import MAX_SHOWN_TEXT_CHARS, ShownGroup


MAX_LABELS = 400
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
    "SC-04 ({theme}): the requested texts could not be checked against the render "
    "→ compare them with the image. Likely cause: no drawn texts to check them against and no readable review."
)
"""The residual line of a render with requested texts that neither matplotlib's drawn texts nor a readable review
answered for (`expected_misses`, `reviewed_misses`): never a silent pass."""
EXPECT_LINE_ID = {"text": "SC-04", "format": "SC-02"}
"""The rubric id a missing requested text (title, legend, label) or number format is reported under."""
_QUOTED = re.compile(r'["“”„«»]([^"“”„«»\n]+)["“”„«»]')
"""A passage of a reviewer's line in straight or typographic double quotes or guillemets."""
_MATH_SPACE = re.compile(r"\\[,;:! ]|\\q?quad\b")
"""Mathtext that draws a space: read as a space."""
MATH_SYMBOLS: dict[str, str] = {
    **dict(
        zip(
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi pi rho sigma tau upsilon "
            "phi chi psi omega".split(),
            "αβγδεζηθικλμνξπρστυφχψω",
            strict=True,
        )
    ),
    **dict(zip("Gamma Delta Theta Lambda Xi Pi Sigma Phi Psi Omega".split(), "ΓΔΘΛΞΠΣΦΨΩ", strict=True)),
    "times": "×",
    "cdot": "·",
    "pm": "±",
    "circ": "°",
    "degree": "°",
    "%": "%",
    "$": "$",
}
"""Mathtext commands that draw one character, read as that character (`$\\alpha$` reads `α`)."""
_MATH_COMMAND = re.compile(r"\\([A-Za-z]+|[%$])")
_MATH_MARKUP = re.compile(r"[\\{}_^]")
"""Mathtext markup characters left after the commands: dropped, so `CO$_2$` reads `CO2`."""
_DOLLAR = re.compile(r"(?<!\\)\$")
_QUOTES = str.maketrans(dict.fromkeys("\"'„“”«»‚‘’`", ""))
_QUOTE_MARKS = str.maketrans(dict.fromkeys("\"'„“”«»‚‘’`", '"'))
"""Every quotation mark as `"`, for the comparison that keeps them (`_norm(quotes=True)`)."""
REQUESTED_MARK = 'requested text "'
"""How a review line cites a requested text it cannot find in the image, as the reviewer's heading prescribes
(`pipeline.REVIEW_EXPECTED_HEADING`), read after `_norm(quotes=True)`."""
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
class DrawnLabel:
    """One drawn text: its probe kind, its text, and for a tick or axis label the index of its axes."""

    kind: str
    text: str
    axes: int | None = None


@dataclass(frozen=True)
class DrawnTexts:
    """Every drawn text the probe reported, unclipped beyond the harness's own cap: what the check reads.

    `complete` is False when the harness left a drawn text out or cut it (`labels_truncated`),
    so a text missing from them may still be drawn and is never claimed missing.
    """

    labels: list[DrawnLabel]
    complete: bool = True

    @property
    def groups(self) -> dict[ShownGroup, list[str]]:
        """The distinct texts by `PlotShows` role, in `GROUP_LIMITS` order."""
        groups: dict[ShownGroup, list[str]] = {}
        for label in self.labels:
            texts = groups.setdefault(_group(label.kind), [])
            if label.text not in texts:
                texts.append(label.text)
        return {group: groups[group] for group in GROUP_LIMITS if groups.get(group)}


def drawn_texts(probe: Any) -> DrawnTexts | None:
    """The drawn texts of a render, from its probe's `labels`; None when the probe has none."""
    if not isinstance(probe, dict):
        return None
    entries = probe.get("labels")
    if not isinstance(entries, list):
        return None
    labels: list[DrawnLabel] = []
    for entry in entries[:MAX_LABELS]:
        if not isinstance(entry, dict):
            continue
        kind, text, axes = entry.get("kind"), entry.get("text"), entry.get("axes")
        if not isinstance(kind, str) or not isinstance(text, str) or not text.strip():
            continue
        index = axes if isinstance(axes, int) and not isinstance(axes, bool) else None
        labels.append(DrawnLabel(kind, _clip(text, MAX_DRAWN_CHARS), index))
    complete = probe.get("labels_truncated") is not True and len(entries) <= MAX_LABELS
    return DrawnTexts(labels, complete)


PROBE_ERRORS = frozenset(
    {
        "Error",
        "TimeoutError",
        "TypeError",
        "ValueError",
        "RangeError",
        "ReferenceError",
        "ParseError",
        "KeyError",
        "IndexError",
        "AttributeError",
        "RecursionError",
        "MemoryError",
        "OSError",
        "RuntimeError",
        "UnicodeDecodeError",
        "JSONDecodeError",
        "MethodError",
        "FieldError",
        "BoundsError",
        "UndefVarError",
        "ArgumentError",
    }
)
"""The exception classes a failed probe names (`{"error": <class>}`: matplotlib's probe, a text probe, Julia's types
among them; R's probe names `Error`) that the attribution log keeps by name; any other value reads `other`, since the
code under test can write the probe."""


def probe_error(probe: Any) -> str | None:
    """The class a probe names for a report that failed, for the `pipeline_render` line: None when it names none."""
    error = probe.get("error") if isinstance(probe, dict) else None
    if error is None:
        return None
    return error if isinstance(error, str) and error in PROBE_ERRORS else "other"


def plot_texts(drawn: DrawnTexts | None) -> dict[ShownGroup, list[str]] | None:
    """`PlotShows.texts`: the drawn texts within `GROUP_LIMITS` and `MAX_SHOWN_TEXT_CHARS`, for the root's reply."""
    if drawn is None:
        return None
    return {
        group: list(dict.fromkeys(_clip(text, MAX_SHOWN_TEXT_CHARS) for text in texts))[: GROUP_LIMITS[group]]
        for group, texts in drawn.groups.items()
    }


def _norm(text: str, *, quotes: bool = False) -> str:
    """A text as the comparison reads it: NFKC, case-folded, without quotes and mathtext markup, one space.

    Mathtext is read as matplotlib draws it: a text with an even number of unescaped `$`
    is math, whose delimiters draw nothing, a command that draws one character
    (`MATH_SYMBOLS`) is that character, a spacing command is a space, and an escaped `\\$`
    is a dollar sign; a lone `$` is a dollar sign too. With `quotes`, every quotation mark
    stays, as `"`, so a quoted passage keeps its ends (`reviewed_misses`).
    """
    text = unicodedata.normalize("NFKC", text).translate(_DASHES).translate(_QUOTE_MARKS if quotes else _QUOTES)
    delimiters = len(_DOLLAR.findall(text))
    if delimiters and delimiters % 2 == 0:
        text = _DOLLAR.sub("", text)
    text = _MATH_SPACE.sub(" ", text)
    text = _MATH_COMMAND.sub(lambda match: MATH_SYMBOLS.get(match[1], ""), text)
    text = _MATH_MARKUP.sub("", text)
    return " ".join(text.casefold().split())


def _contains(text: str, wanted: str) -> bool:
    """`wanted` stands in `text` as a whole: `Kanton 2` is not in `Kanton 20`, `Zürich` is in `Kanton Zürich`.

    The boundary holds only at a word character's edge, so a symbol stands anywhere: `%` is in `12%`.
    """
    before = r"(?<!\w)" if re.match(r"\w", wanted) else ""
    after = r"(?!\w)" if re.search(r"\w$", wanted) else ""
    return re.search(before + re.escape(wanted) + after, text) is not None


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


def _ticks_of(label: DrawnLabel) -> str | None:
    """The tick-label kind a tick or axis label shares an axis with (`y axis label` → `y tick label`), or None."""
    if label.kind.endswith("tick label"):
        return label.kind
    if label.kind == "colorbar label":
        return "colorbar tick label"
    axis = label.kind.removesuffix(" axis label")
    return f"{axis} tick label" if axis in ("x", "y", "z") else None


def _format_texts(drawn: DrawnTexts, unit: str) -> list[str]:
    """The texts a number format applies to: every text that draws its unit, and when that text is a tick label
    or an axis or colorbar label, every tick label of that axis of that axes (`Bevölkerung (Mio.)` over ticks
    `6.0`, `7.0`), never another subplot's or a twin axis's. Without axes indices (a tampered probe) the kind
    alone decides."""
    texts: list[str] = []
    for label in drawn.labels:
        if not _has_unit(_norm(label.text), unit):
            continue
        texts.append(label.text)
        ticks = _ticks_of(label)
        if ticks is not None:
            texts += [
                other.text
                for other in drawn.labels
                if other.kind == ticks and (label.axes is None or other.axes is None or other.axes == label.axes)
            ]
    return list(dict.fromkeys(texts))


def expected_misses(expected: Sequence[str], drawn: DrawnTexts | None) -> list[ExpectMiss]:
    """The requested texts and number formats the drawn texts do not show; none when the probe reported no texts.

    A text must be drawn as written within one drawn text (case, spacing, quotes, dashes and
    mathtext aside); when the harness left texts out, a missing text is not claimed. A number
    format (`format_unit`) must draw its unit, and every text it applies to (`_format_texts`)
    must use its decimal mark, also when one of them matches the example; a unit that is
    nowhere is claimed missing only when the report is complete, a wrong mark always.
    """
    if drawn is None:
        return []
    shown = plot_texts(drawn) or {}
    normed = [_norm(label.text) for label in drawn.labels]
    misses: list[ExpectMiss] = []
    for token in dict.fromkeys(" ".join(item.split()) for item in expected):
        wanted = _norm(token)
        if not wanted:
            continue
        unit = format_unit(token)
        unit_norm = _norm(unit) if unit is not None else ""
        if not unit_norm:
            if drawn.complete and not any(_contains(text, wanted) for text in normed):
                misses.append(ExpectMiss(token, "text", _observed(shown, "text")))
            continue
        applies = [_norm(text) for text in _format_texts(drawn, unit_norm)]
        mark = _decimal_mark(token)
        wrong = None if mark is None else ("." if mark == "," else ",")
        if (not applies and drawn.complete) or (wrong is not None and any(_wrong_mark(t, wrong) for t in applies)):
            misses.append(ExpectMiss(token, "format", _observed(shown, "format")))
    return misses


def reviewed_misses(expected: Sequence[str], lines: Sequence[str]) -> list[tuple[str, str]]:
    """The requested texts a review reports missing from the image, each with the first defect line that does.

    For a render without drawn texts the reviewer gets the requested texts and reports each one
    it cannot find as a defect line under `EXPECT_LINE_ID` (SC-04, or SC-02 for a number format)
    in the form its heading prescribes, `the requested text "<text>"`. A line in that form names
    exactly the texts it cites so, compared with every quotation mark kept (`_norm(quotes=True)`:
    case, spacing and dashes aside), so a cited `Temperatur (°C)` never names a requested
    `Temperatur`, a text with quotes of its own (`Zone "A"`) is still named whole, and a passage
    the line quotes for what the image shows instead names nothing. A line in another form names
    a text when one of its quoted passages reads as that text; when it quotes none, or the text
    has quotes of its own or is a number format (a line may quote only the number it saw), when it
    holds the text whole (`_contains`). Any other line, and a text no line names, is no miss: the
    reviewer found it.
    """
    misses: list[tuple[str, str]] = []
    for token in dict.fromkeys(" ".join(item.split()) for item in expected):
        wanted = _norm(token)
        if not wanted:
            continue
        cited = f'{REQUESTED_MARK}{_norm(token, quotes=True)}"'
        loose = token.translate(_QUOTES) != token or format_unit(token) is not None
        for line in lines:
            match = DEFECT_RE.match(line)
            if match is None or not set(EXPECT_LINE_ID.values()) & set(match["ids"].split(", ")):
                continue
            marked = _norm(line, quotes=True)
            if REQUESTED_MARK in marked:
                named = cited in marked
            else:
                quoted = [_norm(passage) for passage in _QUOTED.findall(line)]
                named = wanted in quoted or ((loose or not quoted) and _contains(_norm(line), wanted))
            if named:
                misses.append((token, line))
                break
    return misses
