"""Host gates on a render: R1-R3 decide, G3/G5/G7/G8 advise.

| Gate | Checks | Effect |
|---|---|---|
| R1 | exit code 0, no timeout, a PNG per theme | blocking: the render is discarded, the error becomes repair feedback |
| R2 | PNG hardening (`png.harden`): signature, decode, size and pixel caps, not blank, re-encoded | blocking, like R1 |
| R3 | canvas within 16 px of 3200x1800 or 2400x2400 (`core.canvas.check_canvas`) | repair-triggering: the VQ-05 defect line goes to the repair; a padded copy is kept as the fallback |
| G3 | probe: text boxes beyond the canvas edge | advisory: an AR-09 line |
| G5 | probe: annotations outside their axes | advisory: a DQ-03 line |
| G7 | probe: overlapping tick labels | advisory: a VQ-02 line |
| G8 | probe: more point marks than data rows (fabricated data) | advisory: a DQ-03 line |

The probe is written inside the sandbox by code under test, so G-gates only ever add
feedback lines; they never fail a render. Feedback lines use the defect grammar of
`core/defects.py` where they name a criterion. A render error is summarised from the
last line of stderr with every quoted string elided, so no cell of the user's data
reaches a prompt through a traceback.
"""

import math
import re
from dataclasses import dataclass, field
from typing import Any

from core.canvas import check_canvas

from ..schemas import MAX_LINE_CHARS
from .contract import THEMES, RenderResult, Theme
from .png import PngRejected, harden, pad_to


CLIP_TOLERANCE_PX = 2
MAX_ERROR_CHARS = 200
G8_SLACK = 10
G8_FACTOR = 1.5

_QUOTED = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"")
_ERROR_LINE = re.compile(r"^[A-Za-z_][\w.]*(Error|Exception|Warning)\b.*")


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

    @property
    def defects(self) -> list[str]:
        """Every line the single repair should act on: canvas first, then the advisory gates."""
        return [*self.canvas_defects, *self.advisory]


def _line(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= MAX_LINE_CHARS else text[: MAX_LINE_CHARS - 1] + "…"


def error_summary(stderr_tail: str) -> str:
    """The exception line of a traceback with quoted text elided, or a generic note."""
    lines = [line.strip() for line in stderr_tail.splitlines() if line.strip()]
    candidates = [line for line in lines if _ERROR_LINE.match(line)]
    chosen = candidates[-1] if candidates else (lines[-1] if lines else "no error output")
    return _QUOTED.sub("'…'", chosen)[:MAX_ERROR_CHARS]


def data_rows(data_csv: str) -> int:
    """Rows of the canonical data.csv (header excluded; the parser writes one row per line)."""
    return max(0, len([line for line in data_csv.split("\n") if line]) - 1)


def evaluate(result: RenderResult, *, library: str, rows: int) -> GateReport:
    """Run R1-R3 and the advisory gates over every theme of `result`."""
    report = GateReport(passed_host_gates=True, canvas_ok=True)
    advisory: dict[str, list[Theme]] = {}
    for theme in THEMES:
        output = result.outputs.get(theme)
        if output is None:
            continue
        if output.timed_out:
            report.blocking.append(_line(f"render ({theme}): the code did not finish within the time limit"))
            report.passed_host_gates = False
            continue
        if output.exit_code != 0 or output.png is None:
            if output.exit_code == 0:
                reason = "the code ran but saved no plot-" + theme + ".png"
            else:
                reason = f"the code failed with {error_summary(output.stderr_tail)}"
            report.blocking.append(_line(f"render ({theme}): {reason}; fix the code so it runs on the user's data"))
            report.passed_host_gates = False
            continue
        try:
            hardened = harden(output.png)
        except PngRejected as exc:
            report.blocking.append(_line(f"render ({theme}): {exc}"))
            report.passed_host_gates = False
            continue
        report.pngs[theme] = hardened.data
        verdict = check_canvas(hardened.width, hardened.height, library)
        if not verdict.ok:
            report.canvas_ok = False
            if verdict.defect_line and verdict.defect_line not in report.canvas_defects:
                report.canvas_defects.append(_line(verdict.defect_line))
            report.padded_pngs[theme] = pad_to(hardened.data, verdict.target)
        for line in _probe_lines(output.probe, rows):
            advisory.setdefault(line, []).append(theme)
    for line, themes in advisory.items():
        theme_label = "both" if len(themes) > 1 else themes[0]
        report.advisory.append(_line(line.replace("(THEME)", f"({theme_label})")))
    if not report.pngs or len(report.pngs) != len(result.outputs):
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


def _probe_lines(probe: dict[str, Any] | None, rows: int) -> list[str]:
    """Advisory defect lines from one theme's probe; a malformed probe yields none, never an exception."""
    try:
        return _probe_lines_unchecked(probe, rows)
    except (ValueError, TypeError, OverflowError, AttributeError):
        return []


def _probe_lines_unchecked(probe: dict[str, Any] | None, rows: int) -> list[str]:
    """Advisory defect lines from one theme's probe; `(THEME)` is filled in by the caller."""
    if not isinstance(probe, dict):
        return []
    lines: list[str] = []
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
                f"AR-09 (THEME): text extends {round(worst)} px beyond the canvas edge → keep every text inside "
                "the canvas. Likely cause: a label position, a long tick label or a large font size."
            )
    overlaps = probe.get("tick_overlaps")
    if isinstance(overlaps, int) and overlaps > 0:
        lines.append(
            f"VQ-02 (THEME): {overlaps} pairs of tick labels overlap → no overlapping tick labels. "
            "Likely cause: too many ticks for the axis length, or unrotated long labels."
        )
    outside = probe.get("annotations_outside")
    if isinstance(outside, int) and outside > 0:
        lines.append(
            f"DQ-03 (THEME): {outside} annotations lie outside their axes → place annotations from a rule over df "
            "or remove them. Likely cause: an annotation at a data coordinate of the example data."
        )
    points = probe.get("points")
    if isinstance(points, int) and rows > 0 and points > rows * G8_FACTOR + G8_SLACK:
        lines.append(
            f"DQ-03 (code): the plot draws {points} point marks for {rows} data rows → draw marks only from df. "
            "Likely cause: generated or duplicated data."
        )
    return lines
