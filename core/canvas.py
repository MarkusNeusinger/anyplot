"""Canvas gate and the deterministic PNG auto-reject checks.

Every render must be exactly 3200x1800 (landscape) or 2400x2400 (square)
within ±16 px. ``check_canvas`` measures a size against the nearer target and,
on drift, builds the VQ-05 defect line (``core.defects.DEFECT_RE``) that names
the actual size, the target, the signed delta, the direction and the library's
most likely cause. ``check_png`` does the same for a PNG file and refuses
anything that does not start with the PNG signature.

The gate is lifted from the "Canvas dimension gate" step of
``.github/workflows/impl-review.yml``, which still runs its inline copy; the
step switches to this module in a later change, once a second consumer (the
agents service, ``docs/concepts/agent-network.md``) exists.
``tests/unit/core/test_canvas.py`` runs the workflow's script and this module on
the same PNGs and requires identical output.

The two auto-reject checks of ``prompts/quality-criteria.md`` that only need the
PNG are here as well: AR-04 (``check_blank``: under 10 KB, or more than 95 % of
the pixels one color) and AR-07 (``check_format``: the file is a PNG). They are
ported from ``scripts/evaluate-plot.py``, which keeps its own copies; AR-04
measures the most common color instead of that script's theme-dependent
near-white rule (see ``MAX_BLANK_RATIO``).

Usage as CLI (exit 0 on target, 1 on drift, 2 when the file is not a readable PNG)::

    python -m core.canvas plot-light.png [--library matplotlib] [--attempt 2] [--out /tmp/anyplot-canvas-gate.txt]

It prints the workflow's ``::notice::canvas_gate …`` line and, on drift, its
``::warning::`` line; with ``--out`` it writes the defect line to that file on
drift and removes a stale one on a pass.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


TOLERANCE = 16  # ≤0.5 % on the 3200-axis
LANDSCAPE = (3200, 1800)
SQUARE = (2400, 2400)
TARGETS = (LANDSCAPE, SQUARE)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# AR-04 (EMPTY_PLOT): a PNG under 10 KB, or one whose most common color
# covers more than 95 % of the canvas. "One color" rather than the "near
# white" / "near black" rule of scripts/evaluate-plot.py: the light page
# #FAF8F1 never counts as white there (channels above 250), and sparse dark
# renders on #1A1A17 count as 95-98 % blank (channels below 60), while the
# densest real renders measured stay at 94 % one color in both themes.
MIN_PLOT_BYTES = 10 * 1024
MAX_BLANK_RATIO = 0.95

# Library-specific likely cause (concrete repair hints, not generic), verbatim
# from impl-review.yml.
LIKELY_CAUSES: dict[str, str] = {
    "matplotlib": "Most likely cause: `bbox_inches='tight'` on `savefig` — remove it (default `bbox_inches=None`).",
    "seaborn": "Most likely cause: `bbox_inches='tight'` on `savefig` — remove it (default `bbox_inches=None`).",
    "altair": "Most likely cause: vl-convert padding title/legend outside `width`/`height`. Add `configure_view(continuousWidth=…, continuousHeight=…)` + zero `padding` and normalize the saved PNG with the PIL crop/pad snippet in `prompts/library/altair.md`.",
    "plotly": "Most likely cause: `autosize=True` or implicit margin growth. Set `autosize=False` and pin `margin=dict(...)` explicitly.",
    "bokeh": "Most likely cause: bokeh toolbar adding ~30-50 px above the figure. Set `toolbar_location=None`.",
    "highcharts": "The harness owns exact pixels (Playwright deviceScaleFactor 2 over a fixed mount). Call `Highcharts.chart('container', {...})` and let it auto-size to `#container` — do NOT set `chart.width`/`chart.height`. Use `//# anyplot-orientation: square` only for square specs.",
    "pygal": "Check that `pygal.<Chart>(width=…, height=…)` and the SVG→PNG conversion don't override dims.",
    "plotnine": "Check `ggsave(width=…, height=…, units='in', dpi=400)` and `theme(figure_size=…)`; do not pass `bbox_inches='tight'`.",
    "letsplot": "Check `ggsize(W, H)` and `ggsave(..., scale=4)` pair — only the two canonical pairs land on target.",
    "ggplot2": "Check `ggsave(width=…, height=…, units='in', dpi=400)` with `ragg::agg_png`.",
    "makie": "Check `Figure(resolution=(1600, 900))` + `save(..., px_per_unit=2)` (landscape) or `resolution=(1200, 1200)` + `px_per_unit=2` (square) — those are the only two canonical pairs.",
    "chartjs": "The harness owns exact pixels (Playwright deviceScaleFactor 2 over a fixed mount). Drift means the snippet forced its own canvas size: set `responsive: true` + `maintainAspectRatio: false` and let the canvas fill `#container` — do NOT set canvas width/height. Use `//# anyplot-orientation: square` only for square specs.",
    "d3": "The harness owns exact pixels (Playwright deviceScaleFactor 2 over a fixed mount). Size the `<svg>` to `window.ANYPLOT_SIZE` (1600×900 landscape / 1200×1200 square) — never hard-code other dimensions. Use `//# anyplot-orientation: square` only for square specs.",
    "echarts": "The harness owns exact pixels (Playwright deviceScaleFactor 2 over a fixed mount). Call `echarts.init(document.getElementById('container'))` with no explicit width/height so it fills the mount; do not pass a `devicePixelRatio` (the page already runs at 2×). Use `//# anyplot-orientation: square` only for square specs.",
    "muix": "The harness owns exact pixels (Playwright deviceScaleFactor 2 over a fixed mount via a MUI ThemeProvider). Size the chart with `width={window.ANYPLOT_SIZE.width}` / `height={window.ANYPLOT_SIZE.height}` (1600×900 landscape / 1200×1200 square) — never hard-code other dimensions. Use `//# anyplot-orientation: square` only for square specs.",
}


class NotAPngError(ValueError):
    """The file does not start with the PNG signature."""


def likely_cause(library: str) -> str:
    """The repair hint the canvas defect line names for ``library``."""
    if library in LIKELY_CAUSES:
        return LIKELY_CAUSES[library]
    if not library:
        return "Review the 'Canvas — hard rule' section of the library prompt in `prompts/library/`."
    return f"Review `prompts/library/{library}.md` 'Canvas — hard rule' section."


def nearest_target(width: int, height: int) -> tuple[int, int]:
    """The target nearer to ``width`` x ``height``, so the repair feedback names the right one."""
    return min(TARGETS, key=lambda t: abs(width - t[0]) + abs(height - t[1]))


@dataclass(frozen=True)
class CanvasVerdict:
    """A render size measured against the nearer canvas target."""

    library: str
    width: int
    height: int
    target: tuple[int, int]

    @property
    def delta(self) -> tuple[int, int]:
        """Signed ``(width, height)`` difference from the target."""
        return self.width - self.target[0], self.height - self.target[1]

    @property
    def ok(self) -> bool:
        """Both sides within ``TOLERANCE`` of the target."""
        dw, dh = self.delta
        return abs(dw) <= TOLERANCE and abs(dh) <= TOLERANCE

    @property
    def status(self) -> str:
        """``pass`` or ``fail``, as the workflow's notice line reports it."""
        return "pass" if self.ok else "fail"

    def notice(self, attempt: str | None = None) -> str:
        """The workflow's ``::notice::canvas_gate`` line; ``attempt`` is left out when None."""
        (tw, th), (dw, dh) = self.target, self.delta
        line = (
            f"::notice::canvas_gate library={self.library} status={self.status} "
            f"actual={self.width}x{self.height} target={tw}x{th} delta={dw:+d}x{dh:+d}"
        )
        return line if attempt is None else f"{line} attempt={attempt}"

    @property
    def defect_line(self) -> str | None:
        """The VQ-05 defect line on drift (what impl-repair reads), None on target.

        It names the actual size, the target, the signed delta, the direction,
        a possible orientation mismatch and the library's likely cause.
        """
        if self.ok:
            return None
        w, h = self.width, self.height
        (tw, th), (dw, dh) = self.target, self.delta

        direction_parts = []
        if dw < 0:
            direction_parts.append(f"width is {-dw} px short")
        elif dw > 0:
            direction_parts.append(f"width is {dw} px over")
        if dh < 0:
            direction_parts.append(f"height is {-dh} px short")
        elif dh > 0:
            direction_parts.append(f"height is {dh} px over")
        direction = "; ".join(direction_parts) or "axes on target individually but combined off"

        # Orientation hint: the actual canvas is landscape-ish but the nearer
        # target is square, or the other way round.
        aspect_note = ""
        actual_aspect = w / h if h else 1
        if (tw, th) == SQUARE and actual_aspect > 1.2:
            aspect_note = " — the implementation rendered a landscape canvas but the closest target is square; reconsider orientation."
        elif (tw, th) == LANDSCAPE and actual_aspect < 0.85:
            aspect_note = " — the implementation rendered a portrait/square canvas but the closest target is landscape; reconsider orientation."

        return (
            f"VQ-05 (both): Canvas dimensions drifted from required target. "
            f"Actual: {w}×{h}. Closest valid target: {tw}×{th} (±{TOLERANCE} px tolerance). "
            f"Signed delta: {dw:+d} × {dh:+d} — {direction}.{aspect_note} "
            f"{likely_cause(self.library)} "
            f"Re-render at exactly {tw}×{th}; the post-render gate enforces this."
        )


def check_canvas(width: int, height: int, library: str) -> CanvasVerdict:
    """Measure a ``width`` x ``height`` render of ``library`` against the nearer target."""
    return CanvasVerdict(library=library, width=width, height=height, target=nearest_target(width, height))


def is_png(path: Path) -> bool:
    """The file exists and starts with the PNG signature."""
    try:
        with path.open("rb") as fh:
            return fh.read(len(PNG_SIGNATURE)) == PNG_SIGNATURE
    except OSError:
        return False


def png_size(path: Path) -> tuple[int, int]:
    """Pixel size of a PNG; raises ``NotAPngError`` for any other file."""
    if not is_png(path):
        raise NotAPngError(f"{path} is not a PNG")
    with Image.open(path) as img:
        return img.size


def check_png(path: Path, library: str) -> CanvasVerdict:
    """``check_canvas`` on a PNG file; raises ``NotAPngError`` for a file that is not a PNG."""
    width, height = png_size(path)
    return check_canvas(width, height, library)


@dataclass(frozen=True)
class AutoRejectResult:
    """One auto-reject check (``prompts/quality-criteria.md``): its ID, whether it passed, and why."""

    code: str
    passed: bool
    message: str


def check_format(path: Path) -> AutoRejectResult:
    """AR-07 (WRONG_FORMAT): the output is a PNG, judged by its signature, not its name.

    An interactive library may also emit HTML; that allowance is the caller's,
    since it depends on the library and not on the file.
    """
    if not path.is_file():
        return AutoRejectResult("AR-07", False, f"No output file: {path.name}")
    if not is_png(path):
        return AutoRejectResult("AR-07", False, f"Not a PNG: {path.name} does not start with the PNG signature")
    return AutoRejectResult("AR-07", True, "Correct format: PNG")


def dominant_color(image: Image.Image) -> tuple[tuple[int, int, int], float]:
    """The most common RGB color of an image and its share of the pixels (exact count)."""
    pixels = np.asarray(image.convert("RGB"))
    if not pixels.size:
        return (0, 0, 0), 1.0
    packed = pixels[..., 0].astype(np.uint32) << 16
    packed |= pixels[..., 1].astype(np.uint32) << 8
    packed |= pixels[..., 2]
    values, counts = np.unique(packed, return_counts=True)
    top = int(counts.argmax())
    value = int(values[top])
    return (value >> 16, (value >> 8) & 0xFF, value & 0xFF), int(counts[top]) / packed.size


def blank_ratio(image: Image.Image) -> float:
    """Share of the pixels that have the image's most common color: 1.0 for an empty canvas."""
    return dominant_color(image)[1]


def check_blank(
    path: Path, *, min_bytes: int = MIN_PLOT_BYTES, max_blank_ratio: float = MAX_BLANK_RATIO
) -> AutoRejectResult:
    """AR-04 (EMPTY_PLOT): the PNG has at least ``min_bytes`` and at most ``max_blank_ratio`` of one color.

    The defaults are the rubric's (10 KB, 95 %). A gate with another cutoff
    passes its own: the agents' R2 check uses 98 %, which is more permissive,
    because only an image above ``max_blank_ratio`` fails.
    """
    if not path.is_file():
        return AutoRejectResult("AR-04", False, f"No PNG to check: {path.name}")
    size = path.stat().st_size
    size_kb = size / 1024
    if size < min_bytes:
        return AutoRejectResult("AR-04", False, f"Plot too small: {size_kb:.1f}KB")
    if not is_png(path):
        return AutoRejectResult("AR-04", False, f"Not a PNG: {path.name}")
    with Image.open(path) as img:
        (r, g, b), ratio = dominant_color(img)
    if ratio > max_blank_ratio:
        return AutoRejectResult("AR-04", False, f"Plot is {ratio * 100:.0f}% one color (#{r:02X}{g:02X}{b:02X})")
    return AutoRejectResult("AR-04", True, f"Plot OK ({size_kb:.0f}KB)")


def is_blank_png(path: Path) -> bool:
    """AR-04 fails for this PNG with the rubric's thresholds."""
    return not check_blank(path).passed


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: 0 on target, 1 on drift, 2 when the file is not a readable PNG."""
    parser = argparse.ArgumentParser(
        prog="python -m core.canvas", description="Check a rendered PNG against the 3200x1800 / 2400x2400 canvas."
    )
    parser.add_argument("png", type=Path, help="the rendered PNG (the pipeline gates plot-light.png)")
    parser.add_argument("--library", default="", help="library id; picks the likely-cause hint")
    parser.add_argument("--attempt", default=None, help="attempt number for the notice line")
    parser.add_argument("--out", type=Path, default=None, help="write the defect line here on drift")
    args = parser.parse_args(argv)

    if args.out is not None:
        args.out.unlink(missing_ok=True)  # the file exists only when this run drifted
    try:
        verdict = check_png(args.png, args.library)
    except (OSError, ValueError) as exc:
        print(f"::error::canvas_gate cannot read {args.png}: {exc}")
        return 2

    print(verdict.notice(args.attempt))
    weakness = verdict.defect_line
    if weakness is None:
        return 0
    if args.out is not None:
        args.out.write_text(weakness, encoding="utf-8")
        print(f"::warning::Canvas gate FAILED — wrote synthetic weakness to {args.out}: {weakness}")
    else:
        print(f"::warning::Canvas gate FAILED: {weakness}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
