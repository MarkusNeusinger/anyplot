"""Host gates on a render: R1-R3 decide, G3/G5/G7/G8/G9/G10/G11/G12 advise.

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
| G11 | probe (`density`): value labels at a data coordinate on a bar's end or point, dots on bar ends and shadowed bars, per axes: more than `MAX_VALUE_LABELS` labels, bar labels wider than `LABEL_SLOT_FILL` of the space per bar, or more than `MAX_DECORATIONS` decorations | advisory: a VQ-03 line |
| G12 | probe (`labels`, `tick_axes`): numeric annotations, and tick labels of numeric axes (never dates or categories), whose decimal mark is not the plot language's (`language.NUMBER_FORMATS`; `foreign_decimal`, mathtext read as drawn) | advisory: a VQ-06 line |

A pipeline run renders one theme (`PipelineArgs.theme`) and the theme toggle renders
the other one later, so `evaluate` judges exactly the themes of the job it is given:
an output for a theme the job did not ask for is ignored, a missing one fails R1.
Lines that name a theme name the job's single theme, or `both` when a job had two
themes and both share the finding.

The probe is written inside the sandbox by code under test, so G-gates only ever add
feedback lines; they never fail a render. Feedback lines use the defect grammar of
`core/defects.py` where they name a criterion. A render error is summarised by the
runtime's error grammar (`RuntimeAdapter.error_summary`), never by its message: code
under test can raise `ValueError(df["secret"].iloc[0])` or `stop(df$secret[1])`, so the
message may be a cell of the user's data. Python's grammar (`error_summary` here) names
the exception class and the line of `plot.py` that raised it; R's
(`code/profiles/r/errors.py`) the erroring function, its cause and its last calls,
because R prints no line numbers for a script. Only R1 to R3 judge a render without a
probe (R, altair, pygal, lets-plot): the G-gates then have nothing to read.
"""

import builtins
import math
import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from core.canvas import check_canvas

from ..language import NumberFormat, english_name, number_format
from ..schemas import MAX_LINE_CHARS
from .contract import THEMES, RenderResult, Theme
from .png import PngRejected, harden, pad_to
from .polar import rlabel_hint


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
MAX_PLOTTED_POINTS = 500_000
"""G9: scatter marks plus line vertices a plot may draw, past which the code computed points of its own, such
as an oversampled series or a simulated trajectory (stress cases `stress-compute-*`). 200,000 until 2026-10-14,
twice the cells the 200 KB paste cap allowed. A 1 MB paste or 2 MiB of computed data holds up to 20,000 rows
of 50 columns, so the owner raised it to 500,000 (2026-10-14): a dense plot of the user's own data, such as
20,000 rows of 24 series (480,000 points), passes, while the stress cases' 610,000 and 1,000,000 points
still trip it."""
MAX_VALUE_LABELS = 25
"""G11: value labels (texts at a data coordinate on a bar's end or a point) one axes may carry. Q3 of the live test of
2026-10-14: the catalogue's bar-grouped labels, dots and shadows, meant for its 12 bars, on 52 bars of 26 cantons."""
LABEL_SLOT_FILL = 0.9
"""G11: a bar label wider than this share of the space between neighbouring bar centres crowds its neighbours."""
MIN_CRAMPED_LABELS = 6  # fewer labels than this are a few callouts, never crowded
MAX_DECORATIONS = 25  # G11: dots on bar ends and shadowed bars one axes may carry
MAX_DENSITY_AXES = 8  # `harness.DENSITY_AXES_LIMIT`: more entries are a tampered probe, read no further
MAX_CANVAS_PX = 10_000.0  # a pixel size past any canvas the gates accept is a tampered probe
G10_SAMPLE = 3  # code points the G10 line names
G10_NAME_CHARS = 15  # name text per label: a label is then at most 26 characters and the line fits MAX_NOTE_CHARS
MAX_CODEPOINT = 0x10FFFF
MAX_GLYPH_COUNT = 0x110000  # more distinct code points than Unicode has is a tampered probe
GLYPH_LINE_PREFIX = "VQ-01 ("  # only G10 writes VQ-01
G10_TARGET = "in text the code writes, use characters the fonts cover; a user's column name stays"
G10_MATH_TARGET = "keep non-Latin text outside $…$ math strings; a user's column name stays"
CODE_FILE = "plot.py"
"""The file the Python runtime writes the code to; its frames give the error line of Python's grammar."""
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


def _code_frame(code_file: str) -> re.Pattern[str]:
    """A traceback frame line in `code_file`, with its line number as the group."""
    return re.compile(r'^[ \t]*File "(?:[^"\n]*/)?' + re.escape(code_file) + r'", line (\d{1,6})\b', re.MULTILINE)


_CODE_FRAME = _code_frame(CODE_FILE)


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
    repair_hints: list[str] = field(default_factory=list)
    """Measured targets a repair should use if one runs (the free direction for a polar plot's
    radial labels, `polar.rlabel_hint`); they never start a repair and are no defects."""
    failed_gates: list[str] = field(default_factory=list)
    """The ids of the gates that failed or reported, one entry per theme and finding: `R1`,
    `R1-timeout`, `R1-<reason>` for a renderer limit (`R1-memory`, `R1-disk_budget`, ...), `R2`,
    `R3`, then the probe gates `G3`, `G5`, `G7`, `G8`, `G9`, `G10`, `G11`, `G12` in the order the probe checks run
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


def error_summary(stderr_tail: str, *, code_file: str = CODE_FILE) -> str:
    """The exception class of a traceback and the code line that raised it; never the message.

    The class comes from the last line that starts with a known exception class (the
    final exception of a chain), the line number from the innermost frame in
    `code_file` (`CODE_FILE` for a plot, `snippet.py` for a data run). Without such a
    line the summary is a fixed text.
    """
    lines = [line.strip() for line in stderr_tail.splitlines() if line.strip()]
    if not lines:
        return "no error output"
    names = [name for name in map(_exception_class, lines) if name]
    if not names:
        return NO_EXCEPTION_LINE
    frame = _CODE_FRAME if code_file == CODE_FILE else _code_frame(code_file)
    frames = frame.findall(stderr_tail)
    return f"{names[-1]} at line {int(frames[-1])}" if frames else names[-1]


NO_FINAL_LINE = "an error that printed no final error line"
FIGURE_KIND_TEXTS: dict[tuple[str, str | None], str] = {
    ("figure", "NoFigure"): "the plot wrote no figure: keep the final save statement, and let the code reach it",
    ("figure", "FigureTooLarge"): "a figure over 16 MiB: draw fewer points, or aggregate them",
    ("figure", "UnsafeMarkup"): (
        "the figure holds what a browser would run, load or link, or a bokeh model no catalogue plot uses (a"
        " JavaScript, HTML or CSS model, a widget, a tooltip with more than text tags, a link, an image URL): draw"
        " with the catalogue's glyphs, annotations and tools, and write plain text and @column fields"
    ),
    ("figure", None): "a figure the page cannot take (a size outside 320 to 6400 pixels a side, or no figure)",
    ("crash", None): "the plot crashed (out of memory, most likely)",
    ("page", None): "the page could not draw the figure (a part it cannot draw, such as a JavaScript callback)",
    (
        "draw",
        "NoWebGL",
    ): 'a WebGL trace, which the renderer cannot draw: use a 2D trace (go.Scatter, render_mode="svg")',
    ("draw", None): "the figure drew nothing",
    ("timeout", None): "the figure's page did not settle within 15 s",
    ("harness", None): "a harness error (a toolchain fault, not the code)",
}
"""The fixed text of each kind of plotly's and bokeh's figure mode with a class where the kind has several (`None` for
the rest of that kind): the plot step's `figure`, `crash` and `harness` lines (`harness.figure_error_line`) and the
screenshot step's (`render.mjs` with `--figure`)."""
_FIGURE_FINAL = re.compile(
    r"^render: error: (?P<kind>[a-z]{1,16}) (?P<cls>[A-Za-z_$][\w$]{0,63}) (?:-|[^\s:]{1,64}:(?P<line>\d{1,7})): "
)


def figure_error_summary(stderr_tail: str, *, code_file: str = CODE_FILE) -> str:
    """Where a plotly or bokeh render failed (the renderer's figure mode, `harness.py --figure`), never the message.

    Both steps end a failure with the JavaScript harness's final error line, `render: error: <kind> <Class>
    <where>: <message>`, the last on stderr. A `plot` line is the plot's own exception: its class and line come from
    the traceback the plot step prints above it, as for every Python plot (`error_summary`), else from the line when
    its class is a builtin exception (`sys.exit` prints no traceback). Every other kind is a fixed text
    (`FIGURE_KIND_TEXTS`). Only the last line counts, since everything above it can quote what the plot printed."""
    lines = [line.rstrip() for line in stderr_tail.splitlines() if line.strip()]
    if not lines:
        return "no error output"
    match = _FIGURE_FINAL.match(lines[-1])
    if match is None:
        return NO_FINAL_LINE
    kind, cls, line = match.group("kind"), match.group("cls"), match.group("line")
    if kind == "plot":
        summary = error_summary("\n".join(lines[:-1]), code_file=code_file)
        if summary not in (NO_EXCEPTION_LINE, "no error output"):
            return summary
        named = _exception_class(cls)
        if named is None:
            return "an error"
        return f"{named} at line {int(line)}" if line is not None else named
    return FIGURE_KIND_TEXTS.get((kind, cls)) or FIGURE_KIND_TEXTS.get((kind, None)) or "an error"


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
            f"render ({theme}): {png} is not a regular file → save the plot to {png} with the code's own final save "
            "statement, never a link or a special file."
        )
    return None


def data_rows(data_csv: str) -> int:
    """Rows of the canonical data.csv (header excluded; the parser writes one row per line)."""
    return max(0, len([line for line in data_csv.split("\n") if line]) - 1)


def evaluate(
    result: RenderResult,
    *,
    themes: Sequence[Theme],
    library: str,
    rows: int,
    plot_language: str | None = None,
    summarise: Callable[[str], str] = error_summary,
) -> GateReport:
    """Run R1-R3 and the advisory gates over every theme of the job; a theme without an output fails R1.

    `plot_language` is the session language the plot text is written in; G12 checks the
    decimal mark of its numbers when the language has a number format (`language.NUMBER_FORMATS`).
    `summarise` turns a failed render's stderr tail into the R1 line's error summary: the
    runtime's error grammar (`RuntimeAdapter.error_summary`), Python's by default.
    """
    wanted = [theme for theme in THEMES if theme in themes]
    if not wanted:
        raise ValueError("a render job names at least one theme")
    numbers = number_format(plot_language) if plot_language else None
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
                reason = f"the code failed with {summarise(output.stderr_tail)}"
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
        for gate, line in _probe_lines(output.probe, rows, numbers, plot_language):
            report.failed_gates.append(gate)
            advisory.setdefault(line, []).append(theme)
        # Both themes draw the same geometry, so the hint comes from the first theme that has one.
        if not report.repair_hints and isinstance(output.probe, dict):
            hint = rlabel_hint(output.probe.get("polar"))
            if hint is not None:
                report.repair_hints.append(_line(hint))
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


def _probe_lines(
    probe: dict[str, Any] | None, rows: int, numbers: NumberFormat | None = None, plot_language: str | None = None
) -> list[tuple[str, str]]:
    """Advisory `(gate, line)` pairs from one theme's probe; a malformed probe yields none, never an exception.

    Each gate is guarded on its own, so a malformed field of one gate never hides another's line.
    """
    lines: list[tuple[str, str]] = []
    checks = (
        lambda: _probe_lines_unchecked(probe, rows),
        lambda: _density_lines(probe),
        lambda: _number_format_lines(probe, numbers, plot_language),
    )
    for check in checks:
        try:
            lines += check()
        except ValueError, TypeError, OverflowError, AttributeError:
            continue
    return lines


def _count(value: Any) -> int | None:
    """A non-negative int of the probe, or None (a bool, a float or a negative number is a tampered probe)."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _pixels(value: Any) -> float | None:
    """A positive finite pixel size of the probe, or None."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    return number if math.isfinite(number) and 0 < number <= MAX_CANVAS_PX else None


def _density_lines(probe: dict[str, Any] | None) -> list[tuple[str, str]]:
    """The G11 line: per-mark value labels or decorations past what the plot's marks leave room for.

    The probe's `density` field (`harness.density_report`) describes each axes; the line
    names the worst one. Labels crowd when more than `MAX_VALUE_LABELS` bar positions carry
    one (`labelled_bars`: a stacked bar's segment labels count once), or, on an axes without
    bars, more than that many numeric labels sit on points (`numeric_labels`: named points
    are the point of scatter-annotated),
    or when a bar label is wider than `LABEL_SLOT_FILL` of the space between bar centres
    (from `MIN_CRAMPED_LABELS` labels on); decorations (dots on bar ends, shadowed bars)
    when there are more than `MAX_DECORATIONS`. Only counts and pixels reach the line.
    """
    entries = probe.get("density") if isinstance(probe, dict) else None
    if not isinstance(entries, list):
        return []
    worst: tuple[int, str] | None = None
    for entry in entries[:MAX_DENSITY_AXES]:
        if not isinstance(entry, dict):
            continue
        bars, marks = _count(entry.get("bars")), _count(entry.get("marks"))
        labelled, decorated = _count(entry.get("labelled")) or 0, _count(entry.get("decorated")) or 0
        if bars is None or marks is None:
            continue
        numeric = _count(entry.get("numeric_labels"))
        positions = _count(entry.get("labelled_bars"))
        # With bars the cap counts labelled bar positions, so a stacked bar's segment labels count once; without
        # bars only numbers count: named points (scatter-annotated asks for 10 to 50) do not.
        if bars:
            capped = labelled if positions is None else min(positions, labelled)
        else:
            capped = labelled if numeric is None else min(numeric, labelled)
        slot, label = _pixels(entry.get("slot_px")), _pixels(entry.get("label_px"))
        cramped = (
            bars > 0
            and labelled >= MIN_CRAMPED_LABELS
            and slot is not None
            and label is not None
            and label > slot * LABEL_SLOT_FILL
        )
        many_labels = capped > MAX_VALUE_LABELS
        many_decorations = decorated > MAX_DECORATIONS
        if not (cramped or many_labels or many_decorations):
            continue
        observed: list[str] = []
        if cramped or many_labels:
            room = f" ({round(label)} px wide on {round(slot)} px per bar)" if cramped and label and slot else ""
            observed.append(f"{labelled if bars else capped} value labels{room}")
        if many_decorations:
            observed.append(f"{decorated} dots or shadows")
        marks_text = f"{bars} bars" if bars else f"{marks} marks"
        line = (
            f"VQ-03 (THEME): {marks_text} carry {' and '.join(observed)} → at most {MAX_VALUE_LABELS} labels, each "
            "fitting its mark, and no per-mark dots or shadows past that: drop them or label only the extremes. "
            "Likely cause: the catalogue's per-mark labels, dots or shadows repeated on every mark of the data."
        )
        severity = labelled + decorated
        if worst is None or severity > worst[0]:
            worst = (severity, line)
    return [] if worst is None else [("G11", worst[1])]


_NUMBER_LABEL = re.compile(
    r"^[+\-−]?(?:[$€£¥]\s?)?[+\-−]?(?P<body>\d[\d.,    ']*\d|\d)"
    r"(?:\s?(?:%|‰|[$€£¥]|[^\W\d_]{1,5}\.?(?:\s[^\W\d_]{1,5}\.?)?))?$"
)
"""A label that is one number: an optional sign and currency sign in either order, digits with marks, an optional
unit, word or trailing currency sign (`%`, `Mio.`, `k`, `mil M`, `5,30 €`, `-$5.30`). Dates (`14.10.`,
`2024-10-14`), ranges, times and words with digits never match."""
_DAY_MONTH = re.compile(r"^(0[1-9]|[12]\d|3[01])[.](0[1-9]|1[0-2])$")
"""`14.10`: a day and month as `%d.%m` writes them, both zero-padded. Read as a date in an annotation, where no axis
says what it is; a decimal written with two digits each side (`10.12`) is the one number this lets through."""
NUMBER_LABEL_KINDS = frozenset({"annotation", "text"})
"""The label kinds whose numbers G12 checks besides every tick label (`x tick label`, `y tick label`, `z tick label`,
`colorbar tick label`, `harness.drawn_labels`); titles, axis titles and legend entries may name a version or a code."""


NUMERIC_TICKS = "number"
"""`harness.tick_axes`'s kind for an axis whose tick labels are numbers; dates, categories and labels the code set
itself (`fixed`) are never checked."""
_MATH_MARKUP = re.compile(r"\\mathdefault|\\mathrm|\\,|[{}$]")


def plain_text(text: str) -> str:
    """A label as it reads on the canvas when it is one mathtext string: `$\\mathdefault{5.30}$` reads `5.30` and
    `$5{,}30$` reads `5,30`. Any other text stays as it is, a currency dollar included."""
    stripped = text.strip()
    if len(stripped) > 2 and stripped.startswith("$") and stripped.endswith("$") and stripped.count("$") == 2:
        return _MATH_MARKUP.sub("", stripped).replace("\\ ", " ").strip()
    return stripped


def _number_label_kind(label: dict[str, Any], ticks: list[Any] | None) -> str | None:
    """`tick labels` or `annotations` for a label G12 checks, else None.

    An annotation or text always counts. A tick label counts only when the probe's
    `tick_axes` (`harness.tick_axes`) names its axis numeric: an axis of dates (`14.10`) or
    of the data's own categories (`3.11`) writes no decimals. Without `tick_axes` (a renderer
    older than G12) no tick label counts.
    """
    kind = label.get("kind")
    if not isinstance(kind, str):
        return None
    if kind in NUMBER_LABEL_KINDS:
        return "annotations"
    if not kind.endswith("tick label") or ticks is None:
        return None
    index = label.get("axes")
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(ticks):
        return None
    entry = ticks[index]
    if not isinstance(entry, dict):
        return None
    names = ("x", "y") if kind == "colorbar tick label" else (kind[0],)
    return "tick labels" if any(entry.get(name) == NUMERIC_TICKS for name in names) else None


def foreign_decimal(text: str, numbers: NumberFormat) -> bool:
    """Whether a numeric label writes its decimals with the other mark than the plot language's.

    Only a label that is one number counts (`_NUMBER_LABEL`). With a decimal comma, a single
    point followed by other than three digits (`5.30`, `6.0 M`) is foreign, and so is a point
    after a comma (`1,234.5`) or more than one comma (`1,234,567`); a single point with three
    digits (`1.234`) is a thousands mark and passes, unless the whole part is 0 (`0.125`). A
    zero-padded day and month (`14.10`, `_DAY_MONTH`) is a date and passes. A decimal point mirrors this, except that
    several points (`7.184.003`) pass, because a version-like label writes them too.
    """
    shown = plain_text(text)
    match = _NUMBER_LABEL.match(shown)
    if match is None or _DAY_MONTH.match(shown):
        return False
    body = match.group("body")
    marks = [char for char in body if char in ".,"]
    if not marks:
        return False
    other = "." if numbers.decimal == "," else ","
    own = numbers.decimal
    if own in marks and other in marks:
        return marks[-1] == other  # the decimal mark comes last
    if other not in marks:
        return own == "," and marks.count(own) > 1  # `1,234,567` groups with commas: English
    if marks.count(other) > 1:
        return False  # `7.184.003` or `1,234,567` group thousands the other way: ambiguous, never named
    whole, decimals = body.rsplit(other, 1)
    # `0.125` is never a thousands group: a leading 0 makes the mark a decimal one.
    return len(decimals) != 3 or whole == "0"


def _number_format_lines(
    probe: dict[str, Any] | None, numbers: NumberFormat | None, plot_language: str | None
) -> list[tuple[str, str]]:
    """The G12 line: numeric tick labels or annotations whose decimal mark is not the plot language's.

    Reads the probe's `labels` field (`{"kind", "text", "axes"}` per drawn text) and its
    `tick_axes`, which say which tick labels are numbers (`_number_label_kind`). No label text
    reaches the line: a tick label can be a cell of the user's data. The language is named
    by its English name from the server's table, never by the session's free-text value.
    Only matplotlib's probe has `tick_axes`; a probe without it (the text probe of a library
    that draws without matplotlib, whose formatters the line's advice does not name) gets no line.
    """
    labels = probe.get("labels") if isinstance(probe, dict) else None
    ticks = probe.get("tick_axes") if isinstance(probe, dict) else None
    if numbers is None or not isinstance(labels, list) or not isinstance(ticks, list):
        return []
    numeric = foreign = 0
    kinds: set[str] = set()
    for label in labels:
        kind = _number_label_kind(label, ticks) if isinstance(label, dict) else None
        if kind is None:
            continue
        text = label.get("text")
        if not isinstance(text, str) or _NUMBER_LABEL.match(plain_text(text)) is None:
            continue
        numeric += 1
        if foreign_decimal(text, numbers):
            foreign += 1
            kinds.add(kind)
    if not foreign:
        return []
    name = english_name(plot_language or "") or "the plot language"
    own, other = ("comma", "point") if numbers.decimal == "," else ("point", "comma")
    thousands = {".": "a point", ",": "a comma"}.get(numbers.thousands, "a space")
    words = ", ".join(word for _, word in numbers.suffixes)
    return [
        (
            "G12",
            f"VQ-06 (THEME): {foreign} of {numeric} numeric {' and '.join(sorted(kinds))} use a decimal {other}; "
            f"{name} writes a decimal {own} → decimal {own}, {thousands} for thousands, {words} for large numbers. "
            'Likely cause: a default formatter or fmt="%.2f" instead of a FuncFormatter or f-string with these marks.',
        )
    ]


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
