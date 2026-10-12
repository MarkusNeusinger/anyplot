"""Host gates on a render: R1-R3 decide, G3/G5/G7/G8/G9/G10 advise.

| Gate | Checks | Effect |
|---|---|---|
| R1 | an output for each of the job's themes, exit code 0, no timeout, no renderer limit hit (`limit_line`, reported as `R1-<reason>`), a PNG per theme | blocking: the render is discarded, the error becomes repair feedback |
| R2 | PNG hardening (`png.harden`): signature, decode, size and pixel caps, not blank, re-encoded | blocking, like R1 |
| R3 | canvas within 16 px of 3200x1800 or 2400x2400 (`core.canvas.check_canvas`) | repair-triggering: the VQ-05 defect line goes to the repair; a padded copy of each missed theme is kept as the fallback |
| G3 | probe: boxes of drawn text beyond the canvas edge (tick labels outside the view or on a hidden axis are never drawn, so never count) | advisory: an AR-09 line |
| G5 | probe: annotations outside their axes | advisory: a DQ-03 line |
| G7 | probe: overlapping drawn tick labels, and any other drawn text (axis label, title, legend text, annotation) overlapping a text by more than 3 px | advisory: a VQ-02 line each |
| G8 | probe: more point marks than data rows (fabricated data) | advisory: a DQ-03 line |
| G9 | probe: scatter marks plus line vertices over `MAX_PLOTTED_POINTS` (computed mass data) | advisory: a DQ-03 line |
| G10 | probe: characters without a glyph in any font of their text, plain text and mathtext (the harness records matplotlib's own reports) | advisory: a VQ-01 line |

A pipeline run renders one theme (`PipelineArgs.theme`) and the theme toggle renders
the other one later, so `evaluate` judges exactly the themes of the job it is given:
an output for a theme the job did not ask for is ignored, a missing one fails R1.
Lines that name a theme name the job's single theme, or `both` when a job had two
themes and both share the finding.

The probe is written inside the sandbox by code under test, so G-gates only ever add
feedback lines; they never fail a render. Feedback lines use the defect grammar of
`core/defects.py` where they name a criterion. A render error is summarised as the
exception class and the line of the code file that raised it, never the message: code
under test can raise `ValueError(df["secret"].iloc[0])`, so the message may be a cell
of the user's data.
"""

import builtins
import math
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from core.canvas import check_canvas

from ..schemas import MAX_LINE_CHARS
from .contract import THEMES, RenderResult, Theme
from .png import PngRejected, harden, pad_to


CLIP_TOLERANCE_PX = 2
TEXT_OVERLAP_TOLERANCE_PX = 3.0
"""The harness's own tolerance (`harness.TEXT_OVERLAP_TOLERANCE_PX`), checked again because the probe is untrusted."""
TEXT_KINDS = frozenset(
    {
        "tick label",
        "x axis label",
        "y axis label",
        "z axis label",
        "angular axis label",
        "radial axis label",
        "figure axis label",
        "title",
        "suptitle",
        "annotation",
        "legend text",
        "text",
    }
)
"""The text roles the harness names (`harness._text_kinds`); any other probe value reads "text"."""
G8_SLACK = 10
G8_FACTOR = 1.5
MAX_PLOTTED_POINTS = 200_000
"""G9: scatter marks plus line vertices a plot may draw. The parser's 200 KB cap holds at most about
102,000 cells (two bytes each), so a plot past twice that drew points the code computed, such as an
oversampled series or a simulated trajectory (stress cases `stress-compute-*`)."""
G10_SAMPLE = 3  # code points the G10 line names
G10_NAME_CHARS = 15  # name text per label: a label is then at most 26 characters and the line fits MAX_NOTE_CHARS
MAX_CODEPOINT = 0x10FFFF
MAX_GLYPH_COUNT = 0x110000  # more distinct code points than Unicode has is a tampered probe
GLYPH_LINE_PREFIX = "VQ-01 ("  # only G10 writes VQ-01; the pipeline carries this line into the residual
G10_TARGET = "in text the code writes, use characters the fonts cover; a user's column name stays"
G10_MATH_TARGET = "keep non-Latin text outside $…$ math strings; a user's column name stays"
CODE_FILE = "plot.py"
"""The file the Python runtime writes the code to; its frames give the error line."""
ERROR_CLASSES = frozenset(
    {
        "pandas.errors.ParserError",
        "pandas.errors.EmptyDataError",
        "pandas.errors.MergeError",
        "pandas.errors.IndexingError",
        "pandas.errors.InvalidIndexError",
        "pandas.errors.OutOfBoundsDatetime",
        "pandas.errors.IntCastingNaNError",
        "pandas.errors.SettingWithCopyError",
        "pandas.errors.SpecificationError",
        "pandas.errors.DataError",
        "pandas.errors.UndefinedVariableError",
        "numpy.exceptions.AxisError",
        "numpy.exceptions.DTypePromotionError",
        "numpy.exceptions.TooHardError",
        "numpy.linalg.LinAlgError",
        "numpy._core._exceptions.UFuncTypeError",
        "numpy._core._exceptions._UFuncNoLoopError",
        "numpy._core._exceptions._ArrayMemoryError",
        "matplotlib.units.ConversionError",
        "matplotlib._api.deprecation.MatplotlibDeprecationWarning",
        "PIL.UnidentifiedImageError",
        "PIL.Image.DecompressionBombError",
        "dateutil.parser._parser.ParserError",
        "dateutil.parser.ParserError",
        "scipy.linalg.LinAlgError",
        "scipy.linalg._misc.LinAlgError",
        "sklearn.exceptions.NotFittedError",
        "statsmodels.tools.sm_exceptions.PerfectSeparationError",
        "statsmodels.tools.sm_exceptions.MissingDataError",
    }
)
"""The qualified exception classes of the plotting libraries that a render error may name.

An exact allowlist: a dotted name the code under test made up (`pandas.Alice_Error`)
would otherwise carry data into the repair feedback.
"""
NO_EXCEPTION_LINE = "an error that printed no exception line"
UNLISTED_CLASS = "an error of an unlisted exception class"

_ERROR_CLASS = re.compile(r"^((?:[A-Za-z_]\w*\.)*[A-Za-z_]\w*)(?::|$)")
_CODE_FRAME = re.compile(r'^[ \t]*File "(?:[^"\n]*/)?' + re.escape(CODE_FILE) + r'", line (\d{1,6})\b', re.MULTILINE)


@dataclass
class GateReport:
    """The verdict on one render and the PNGs that may ship."""

    passed_host_gates: bool
    canvas_ok: bool
    pngs: dict[Theme, bytes] = field(default_factory=dict)
    padded_pngs: dict[Theme, bytes] = field(default_factory=dict)
    blocking: list[str] = field(default_factory=list)
    canvas_defects: list[str] = field(default_factory=list)
    advisory: list[str] = field(default_factory=list)
    failed_gates: list[str] = field(default_factory=list)
    """The ids of the gates that failed or reported, one entry per theme and finding: `R1`,
    `R1-timeout`, `R1-<reason>` for a renderer limit (`R1-memory`, `R1-disk_budget`, ...), `R2`,
    `R3`, then the probe gates `G3`, `G5`, `G7`, `G8`, `G9`, `G10` in the order the probe checks run
    (not sorted). Content-free, for the attribution log."""

    @property
    def defects(self) -> list[str]:
        """Every line the single repair should act on: canvas first, then the advisory gates."""
        return [*self.canvas_defects, *self.advisory]

    @property
    def shipped_pngs(self) -> dict[Theme, bytes]:
        """The PNGs a passing render ships: every hardened PNG, replaced by its padded copy where the canvas missed.

        Padding covers only the themes that missed the canvas, so the padded copies
        go over the complete hardened set rather than replacing it.
        """
        return {**self.pngs, **self.padded_pngs}


def _line(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_LINE_CHARS else text[: MAX_LINE_CHARS - 1] + "…"


def _exception_class(line: str) -> str | None:
    """The exception class an exception line starts with, if it names a known one.

    A builtin exception, or a qualified class in `ERROR_CLASSES`. A qualified name that
    is not listed counts as an exception line but is reported as `UNLISTED_CLASS`, so
    neither the message nor a made-up class name is ever returned.
    """
    match = _ERROR_CLASS.match(line)
    if match is None:
        return None
    name = match.group(1)
    if "." in name:
        return name if name in ERROR_CLASSES else UNLISTED_CLASS
    value = getattr(builtins, name, None)
    return name if isinstance(value, type) and issubclass(value, BaseException) else None


def error_summary(stderr_tail: str) -> str:
    """The exception class of a traceback and the code line that raised it; never the message.

    The class comes from the last line that starts with a known exception class (the
    final exception of a chain), the line number from the innermost frame in
    `CODE_FILE`. Without such a line the summary is a fixed text.
    """
    lines = [line.strip() for line in stderr_tail.splitlines() if line.strip()]
    if not lines:
        return "no error output"
    names = [name for name in map(_exception_class, lines) if name]
    if not names:
        return NO_EXCEPTION_LINE
    frames = _CODE_FRAME.findall(stderr_tail)
    return f"{names[-1]} at line {int(frames[-1])}" if frames else names[-1]


def _mib(value: int | None) -> str:
    return "more than allowed" if value is None else f"{value / (1024 * 1024):.1f} MiB"


def limit_line(theme: Theme, reason: str | None, measured: int | None, limit: int | None) -> str | None:
    """The R1 line for a run the renderer stopped or refused at one of its limits, naming the value and the limit.

    None for any other reason: a timeout has its own line, and `launcher` never gets
    here (the `remote` backend raises `RendererUnavailable` for it). The numbers come
    from the renderer, never from the code under test.
    """
    png = f"plot-{theme}.png"
    if reason == "disk_budget":
        return (
            f"render ({theme}): the code wrote {_mib(measured)} to its working directory, over the {_mib(limit)} "
            f"limit, and was stopped → save only {png} and write no other files. Likely cause: data, caches or "
            "extra images saved to disk."
        )
    if reason == "file_budget":
        made = "a directory tree too deep to measure" if measured is None else f"{measured} files and directories"
        return (
            f"render ({theme}): the code created {made}, over the limit of {limit}, and was stopped → write no "
            f"files besides {png}. Likely cause: a file written per row or per group, or nested output folders."
        )
    if reason == "memory":
        return (
            f"render ({theme}): the renderer's free memory fell to {measured} MiB, below its {limit} MiB floor, and "
            "the code was stopped → use less memory. Likely cause: very many marks, a huge figure or large "
            "temporary files."
        )
    if reason == "output_rejected":
        if measured is not None and limit is not None:
            return (
                f"render ({theme}): {png} is {_mib(measured)}, over the {_mib(limit)} limit → save it once at the "
                "catalogue canvas size. Likely cause: a high dpi or a very large figure size."
            )
        return (
            f'render ({theme}): {png} is not a regular file → save the figure with fig.savefig("{png}"), never a '
            "link or a special file."
        )
    return None


def data_rows(data_csv: str) -> int:
    """Rows of the canonical data.csv (header excluded; the parser writes one row per line)."""
    return max(0, len([line for line in data_csv.split("\n") if line]) - 1)


def evaluate(result: RenderResult, *, themes: Sequence[Theme], library: str, rows: int) -> GateReport:
    """Run R1-R3 and the advisory gates over every theme of the job; a theme without an output fails R1."""
    wanted = [theme for theme in THEMES if theme in themes]
    if not wanted:
        raise ValueError("a render job names at least one theme")
    report = GateReport(passed_host_gates=True, canvas_ok=True)
    advisory: dict[str, list[Theme]] = {}
    missed: list[Theme] = []
    for theme in wanted:
        output = result.outputs.get(theme)
        if output is None:
            report.blocking.append(_line(f"render ({theme}): the renderer returned no output for this theme"))
            report.failed_gates.append("R1")
            report.passed_host_gates = False
            continue
        if output.timed_out:
            report.blocking.append(_line(f"render ({theme}): the code did not finish within the time limit"))
            report.failed_gates.append("R1-timeout")
            report.passed_host_gates = False
            continue
        stopped = limit_line(theme, output.reason, output.measured, output.limit)
        if stopped is not None:
            report.blocking.append(_line(stopped))
            report.failed_gates.append(f"R1-{output.reason}")
            report.passed_host_gates = False
            continue
        if output.exit_code != 0 or output.png is None:
            if output.exit_code == 0:
                reason = "the code ran but saved no plot-" + theme + ".png"
            else:
                reason = f"the code failed with {error_summary(output.stderr_tail)}"
            report.blocking.append(_line(f"render ({theme}): {reason}; fix the code so it runs on the user's data"))
            report.failed_gates.append("R1")
            report.passed_host_gates = False
            continue
        try:
            hardened = harden(output.png)
        except PngRejected as exc:
            report.blocking.append(_line(f"render ({theme}): {exc}"))
            report.failed_gates.append("R2")
            report.passed_host_gates = False
            continue
        report.pngs[theme] = hardened.data
        verdict = check_canvas(hardened.width, hardened.height, library)
        if not verdict.ok:
            report.canvas_ok = False
            missed.append(theme)
            report.failed_gates.append("R3")
            if verdict.defect_line and verdict.defect_line not in report.canvas_defects:
                report.canvas_defects.append(_line(verdict.defect_line))
            report.padded_pngs[theme] = pad_to(hardened.data, verdict.target)
        for gate, line in _probe_lines(output.probe, rows):
            report.failed_gates.append(gate)
            advisory.setdefault(line, []).append(theme)
    if len(missed) == 1:
        # `core.canvas` writes the line as `(both)`; name the one theme that missed.
        report.canvas_defects = [line.replace("(both):", f"({missed[0]}):", 1) for line in report.canvas_defects]
    for line, found_in in advisory.items():
        theme_label = "both" if len(found_in) > 1 else found_in[0]
        report.advisory.append(_line(line.replace("(THEME)", f"({theme_label})")))
    # Compare with the job's themes, not with what came back: a missing PNG fails the render.
    if set(report.pngs) != set(wanted):
        report.passed_host_gates = False
    return report


def _finite(values: Any, count: int) -> list[float] | None:
    """`values` as `count` finite floats, or None (the probe is written by the code under test)."""
    if not isinstance(values, list) or len(values) != count:
        return None
    if not all(isinstance(value, int | float) and not isinstance(value, bool) for value in values):
        return None
    numbers = [float(value) for value in values]
    return numbers if all(math.isfinite(number) for number in numbers) else None


_NAME_SUFFIX_RE = re.compile(r"-[0-9A-F]{4,6}$")  # CJK UNIFIED IDEOGRAPH-9500 → CJK UNIFIED IDEOGRAPH
_NAME_STOP_WORDS = frozenset({"with", "of", "and", "for"})  # CHART WITH UPWARDS TREND → chart


def _glyph_sample(values: Any) -> list[int]:
    """At most `G10_SAMPLE` distinct code points of a probe's sample; whatever is not a code point is dropped.

    Printable ASCII (U+0020–U+007E) is in every font the image has, so a "missing" ASCII letter
    is a tampered probe. A C0 control (TAB, CR) is reported by matplotlib and draws a box, so it
    is kept and the line can name it; surrogates are not characters.
    """
    if not isinstance(values, list):
        return []
    kept: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        if not 0 <= value <= MAX_CODEPOINT or 0x20 <= value <= 0x7E or 0xD800 <= value <= 0xDFFF:
            continue
        if value not in kept:
            kept.append(value)
        if len(kept) == G10_SAMPLE:
            break
    return kept


def _glyph_label(codepoint: int) -> str:
    """`U+XXXX`, the character itself when it is a letter, number, punctuation or symbol, and a short name.

    The name is the first two words of the Unicode name when they fit `G10_NAME_CHARS`, else the
    first word cut to that length, so a label is at most 26 characters (`U+` and six hex digits, a
    space and the character, a space and the name) and three of them fit the reviewer's note next
    to a seven-digit count. A format, bidi or control character (`Cf`, `Cc`, `Cs`) and whitespace
    are never echoed: the line reaches the adapter's and the reviewer's prompts and the user's notes.
    """
    char = chr(codepoint)
    category = unicodedata.category(char)
    words = _NAME_SUFFIX_RE.sub("", unicodedata.name(char, "")).split()[:2]
    if len(words) == 2 and words[1].lower() in _NAME_STOP_WORDS:
        words = words[:1]
    text = " ".join(words).lower()
    if len(text) > G10_NAME_CHARS:
        text = words[0].lower()[:G10_NAME_CHARS]
    if not text:
        text = {"Co": "private use", "Cc": "control"}.get(category, "unnamed")
    shown = f" {char}" if category[0] in "LNPS" else ""
    return f"U+{codepoint:04X}{shown} {text}"


def _text_overlap_line(probe: dict[str, Any]) -> str | None:
    """The G7 line for texts other than two tick labels that overlap: the deepest pair, named by role.

    The probe's roles are untrusted strings, so only the harness's own vocabulary
    (`TEXT_KINDS`) is named; anything else reads "a text". No text content is ever
    quoted: a tick label can be a cell of the user's data, and the line reaches the
    adapter's prompt.
    """
    pairs = probe.get("text_overlaps")
    total = probe.get("text_overlaps_total")
    if not isinstance(pairs, list) or not pairs or not isinstance(pairs[0], dict):
        return None
    first = pairs[0]
    depth = first.get("px")
    if isinstance(depth, bool) or not isinstance(depth, int | float) or not math.isfinite(depth):
        return None
    if depth <= TEXT_OVERLAP_TOLERANCE_PX:
        return None
    a, b = (_text_kind(first.get(key)) for key in ("a", "b"))
    count = total if isinstance(total, int) and not isinstance(total, bool) and total >= 1 else len(pairs)
    others = f" ({count} pairs of texts overlap)" if count > 1 else ""
    if first.get("polar") is True and "axis label" in f"{a} {b}":
        cause = (
            "polar axes place the radial axis label beside the angular tick labels; move it "
            "(ax.set_rlabel_position, labelpad) or name the axis in the title instead"
        )
    else:
        cause = "a label, title, legend or annotation placed over other text, or a font too large for the space"
    return (
        f"VQ-02 (THEME): the {a} overlaps the {b} by {round(depth)} px{others} → no text drawn over another text. "
        f"Likely cause: {cause}."
    )


def _text_kind(value: Any) -> str:
    return value if isinstance(value, str) and value in TEXT_KINDS else "text"


def _probe_lines(probe: dict[str, Any] | None, rows: int) -> list[tuple[str, str]]:
    """Advisory `(gate, line)` pairs from one theme's probe; a malformed probe yields none, never an exception."""
    try:
        return _probe_lines_unchecked(probe, rows)
    except (ValueError, TypeError, OverflowError, AttributeError):
        return []


def _probe_lines_unchecked(probe: dict[str, Any] | None, rows: int) -> list[tuple[str, str]]:
    """Advisory `(gate, line)` pairs from one theme's probe; `(THEME)` is filled in by the caller."""
    if not isinstance(probe, dict):
        return []
    lines: list[tuple[str, str]] = []
    canvas = _finite(probe.get("canvas"), 2)
    texts = probe.get("texts")
    if canvas is not None and isinstance(texts, list):
        width, height = canvas
        worst = 0.0
        for text in texts:
            box = _finite(text.get("box") if isinstance(text, dict) else None, 4)
            if box is None:
                continue
            x0, y0, x1, y1 = box
            worst = max(worst, -x0, -y0, x1 - width, y1 - height)
        if worst > CLIP_TOLERANCE_PX:
            lines.append(
                (
                    "G3",
                    f"AR-09 (THEME): text extends {round(worst)} px beyond the canvas edge → keep every text inside "
                    "the canvas. Likely cause: a label position, a long tick label or a large font size.",
                )
            )
    overlaps = probe.get("tick_overlaps")
    if isinstance(overlaps, int) and overlaps > 0:
        lines.append(
            (
                "G7",
                f"VQ-02 (THEME): {overlaps} pairs of tick labels overlap → no overlapping tick labels. "
                "Likely cause: too many ticks for the axis length, or unrotated long labels.",
            )
        )
    text_line = _text_overlap_line(probe)
    if text_line is not None:
        lines.append(("G7", text_line))
    outside = probe.get("annotations_outside")
    if isinstance(outside, int) and outside > 0:
        lines.append(
            (
                "G5",
                f"DQ-03 (THEME): {outside} annotations lie outside their axes → place annotations from a rule over "
                "df or remove them. Likely cause: an annotation at a data coordinate of the example data.",
            )
        )
    points = probe.get("points")
    if isinstance(points, int) and rows > 0 and points > rows * G8_FACTOR + G8_SLACK:
        lines.append(
            (
                "G8",
                f"DQ-03 (code): the plot draws {points} point marks for {rows} data rows → draw marks only from df. "
                "Likely cause: generated or duplicated data.",
            )
        )
    plotted = sum(
        value
        for value in (points, probe.get("line_points"))
        if isinstance(value, int) and not isinstance(value, bool) and value > 0
    )
    if plotted > MAX_PLOTTED_POINTS:
        lines.append(
            (
                "G9",
                f"DQ-03 (code): the plot draws {plotted} points, over the limit of {MAX_PLOTTED_POINTS} for "
                f"{rows} data rows → plot the rows of df, at most one mark or line vertex per row and series. "
                "Likely cause: data computed, interpolated or resampled in the code.",
            )
        )
    glyphs = probe.get("missing_glyphs")
    if isinstance(glyphs, dict):
        count = glyphs.get("count")
        math_count = glyphs.get("math")
        if isinstance(count, int) and not isinstance(count, bool) and 0 < count <= MAX_GLYPH_COUNT:
            sample = _glyph_sample(glyphs.get("sample"))
            labels = ", ".join(_glyph_label(codepoint) for codepoint in sample)
            shown = f" ({labels}{', …' if count > G10_SAMPLE else ''})" if labels else ""
            in_math = isinstance(math_count, int) and not isinstance(math_count, bool) and math_count > 0
            if in_math:
                drawn, target, cause = "boxes or ¤", G10_MATH_TARGET, "a $…$ math string, which has no font fallback"
            elif any(codepoint < 0x20 for codepoint in sample):
                drawn, target, cause = "boxes", G10_TARGET, "a tab or carriage return in a label"
            else:
                drawn, target, cause = "boxes", G10_TARGET, "an emoji, a flag or a script the fonts lack"
            noun = "character has" if count == 1 else "characters have"
            lines.append(
                (
                    "G10",
                    f"VQ-01 (THEME): {count} {noun} no glyph, drawn as {drawn}{shown} → {target}. "
                    f"Likely cause: {cause}.",
                )
            )
    return lines
