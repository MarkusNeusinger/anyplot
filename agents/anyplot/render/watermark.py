"""The footer strip of user plots: "made with any.plot()" on the left, "anyplot.ai/<spec-id>" on the right.

A user plot that leaves the service carries a strip appended below the render, in
the page colour of its theme. It is composited at image level after the run, never
written into the user's code: the exported `plot.py` reproduces the plot without it,
and the gates, the reviewer and the render store keep the raw render. Only the PNG
artifacts the `/v1` routes serve (`plot-light.png`, `plot-dark.png`) and the images
of the feedback bundle carry the strip (`agents/main.py`, `AGENT_WATERMARK`).

The geometry is defined on the 3200 px wide canvas and scales with `width / 3200`,
so the 2400x2400 square gets a 48 px strip (2400x2448) and the 3200x1800 landscape a
64 px one (3200x1864):

* the raw image sits at (0, 0), pixel-identical; the strip is appended below it;
* a 1 px hairline in the ink colour at alpha 0.15 fills the strip's top row, so it
  never covers the plot's last row;
* the text is JetBrains Mono at 22 px, inset 40 px from both sides, its cap height
  (0.73 em) centred vertically in the strip; "made with " and "/<spec-id>" are
  Regular at alpha 0.56, "any", "plot", "anyplot" and "ai" Bold at 0.70, "()"
  Regular at 0.315, all in the theme's ink;
* the dot of "any.plot" and "anyplot.ai" is not a glyph but a brand-green square
  (#009E73 at alpha 0.9) with the geometry of the logo's MonoLisa period: with a
  dot em of 1.45 times the text size, a side of 0.185 em, a cell advance of
  0.640 em, a left bearing of 0.251 em, and its bottom on the baseline.

A spec id too long for the space between the two texts is cut and ends in an
ellipsis, so the texts never come closer than `GAP_PX` (scaled). The fonts are the
vendored, unmodified JetBrains Mono 2.304 files in `fonts/` (SIL OFL 1.1, see
`fonts/README.md`). They load when this module is imported, so a missing file stops
the service at start instead of failing the first request, and they are drawn with
Pillow's BASIC layout engine, so an image without raqm renders the same pixels.

`add_footer` is pure and deterministic; `footer_layout` returns the geometry it
draws, so a test can check positions without rasterising glyphs. No ADK import.
"""

import io
import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from core.canvas import LANDSCAPE
from core.palette import GREEN, neutral_for

from .contract import Theme


FONT_DIR = Path(__file__).resolve().parent / "fonts"
FONT_FILES: dict[bool, Path] = {
    False: FONT_DIR / "JetBrainsMono-Regular.ttf",
    True: FONT_DIR / "JetBrainsMono-Bold.ttf",
}
"""The font file of each weight, keyed by `bold`."""

PAGE: dict[Theme, str] = {"light": "#FAF8F1", "dark": "#1A1A17"}
"""The strip's background: the page colour of each theme."""

REFERENCE_WIDTH = LANDSCAPE[0]
"""The canvas width every length below is defined on; other widths scale by `width / REFERENCE_WIDTH`."""
MIN_WIDTH = 640
"""The narrowest image the strip is drawn on; below it the text would be under 5 px."""

STRIP_PX = 64
HAIRLINE_PX = 1
TEXT_PX = 22.0
INSET_PX = 40.0
GAP_PX = 40.0
"""The closest the left and the right text may come before the spec id is cut."""
CAP_HEIGHT_EM = 0.73
"""JetBrains Mono's cap height; the caps, not the whole line, are centred in the strip."""

DOT_EM = 1.45
"""The dot's em as a multiple of the text size (MonoLisa's period on the logo's scale)."""
DOT_SIDE_EM = 0.185
DOT_ADVANCE_EM = 0.640
DOT_BEARING_EM = 0.251

TEXT_ALPHA = 0.70
"""Bold words: "any", "plot", "anyplot", "ai"."""
SOFT_ALPHA = 0.56
"""Regular words: "made with " and "/<spec-id>"."""
FAINT_ALPHA = 0.315
"""The call parentheses "()"."""
HAIRLINE_ALPHA = 0.15
DOT_ALPHA = 0.9
ELLIPSIS = "…"

SPEC_ID_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
"""The spec id pattern of the exported code's header (`code/export.py`); the id becomes visible text."""
_SPEC_ID = re.compile(SPEC_ID_PATTERN)


@dataclass(frozen=True)
class _Text:
    text: str
    bold: bool
    alpha: float


@dataclass(frozen=True)
class _Dot:
    pass


_Part = _Text | _Dot
_DOT = _Dot()


@dataclass(frozen=True)
class Run:
    """One drawn piece of text; `x` is the left edge of its advance box, `width` its advance."""

    text: str
    bold: bool
    alpha: float
    x: int
    width: float

    @property
    def end(self) -> float:
        return self.x + self.width


@dataclass(frozen=True)
class Square:
    """One brand-green dot, in strip coordinates; it covers `side` x `side` pixels from (`left`, `top`)."""

    left: int
    top: int
    side: int


@dataclass(frozen=True)
class FooterLayout:
    """Where everything goes; x in canvas pixels, y in strip rows (row 0 is the hairline)."""

    width: int
    plot_height: int
    strip_height: int
    scale: float
    text_px: float
    baseline: int
    runs: tuple[Run, ...]
    squares: tuple[Square, Square]
    left_span: tuple[float, float]
    right_span: tuple[float, float]
    shown_spec: str
    """The spec id as drawn: the whole id, or its start and an ellipsis."""

    @property
    def height(self) -> int:
        return self.plot_height + self.strip_height


_FONT_BYTES: dict[bool, bytes] = {bold: path.read_bytes() for bold, path in FONT_FILES.items()}
_FONT_LOCK = threading.Lock()
"""Held while fonts measure and draw: a FreeType face is not thread-safe, and the routes compose in worker threads."""


@lru_cache(maxsize=16)
def _font(bold: bool, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(io.BytesIO(_FONT_BYTES[bold]), size, layout_engine=ImageFont.Layout.BASIC)


# Read and parse both faces at import, so a missing or broken file stops the service at start.
_font(False, TEXT_PX)
_font(True, TEXT_PX)


def _alpha(value: float) -> int:
    return round(value * 255)


def _rgb(colour: str) -> tuple[int, int, int]:
    red, green, blue = ImageColor.getrgb(colour)[:3]
    return red, green, blue


def _made_with() -> list[_Part]:
    return [
        _Text("made with ", False, SOFT_ALPHA),
        _Text("any", True, TEXT_ALPHA),
        _DOT,
        _Text("plot", True, TEXT_ALPHA),
        _Text("()", False, FAINT_ALPHA),
    ]


def _address(spec: str) -> list[_Part]:
    return [
        _Text("anyplot", True, TEXT_ALPHA),
        _DOT,
        _Text("ai", True, TEXT_ALPHA),
        _Text("/" + spec, False, SOFT_ALPHA),
    ]


def _width(parts: list[_Part], size: float) -> float:
    dot_advance = DOT_ADVANCE_EM * DOT_EM * size
    return sum(dot_advance if isinstance(part, _Dot) else _font(part.bold, size).getlength(part.text) for part in parts)


def _place(parts: list[_Part], x: float, size: float, baseline: int) -> tuple[list[Run], list[Square]]:
    """The runs and squares of one line starting at `x`; every run starts on a whole pixel, so glyphs stay crisp."""
    dot_em = DOT_EM * size
    side = max(1, round(DOT_SIDE_EM * dot_em))
    runs: list[Run] = []
    squares: list[Square] = []
    cursor = x
    for part in parts:
        if isinstance(part, _Dot):
            squares.append(Square(round(cursor + DOT_BEARING_EM * dot_em), baseline - side, side))
            cursor += DOT_ADVANCE_EM * dot_em
            continue
        start = round(cursor)
        width = _font(part.bold, size).getlength(part.text)
        runs.append(Run(part.text, part.bold, part.alpha, start, width))
        cursor = start + width
    return runs, squares


def _fits(spec: str, right_edge: float, left_end: float, gap: float, size: float) -> bool:
    return right_edge - _width(_address(spec), size) >= left_end + gap


def _shown_spec(spec_id: str, right_edge: float, left_end: float, gap: float, size: float) -> str:
    """The spec id, or its longest start plus an ellipsis that keeps `gap` to the left text."""
    if _fits(spec_id, right_edge, left_end, gap, size):
        return spec_id
    low, high = 0, len(spec_id) - 1  # the longest prefix that fits with the ellipsis
    while low < high:
        middle = (low + high + 1) // 2
        if _fits(spec_id[:middle] + ELLIPSIS, right_edge, left_end, gap, size):
            low = middle
        else:
            high = middle - 1
    return spec_id[:low] + ELLIPSIS


def footer_layout(width: int, height: int, *, spec_id: str) -> FooterLayout:
    """The strip's geometry for a `width` x `height` render; raises `ValueError` on a bad spec id or size."""
    if not _SPEC_ID.fullmatch(spec_id):
        raise ValueError(f"not a spec id: {spec_id!r}")
    if width < MIN_WIDTH or height < 1:
        raise ValueError(f"the image is {width}x{height}; the footer needs at least {MIN_WIDTH} px of width")
    scale = width / REFERENCE_WIDTH
    strip_height = round(STRIP_PX * scale)
    size = TEXT_PX * scale
    inset = INSET_PX * scale
    baseline = round((strip_height + CAP_HEIGHT_EM * size) / 2)
    left_runs, left_squares = _place(_made_with(), inset, size, baseline)
    left_end = max(run.end for run in left_runs)
    right_edge = width - inset
    shown = _shown_spec(spec_id, right_edge, left_end, GAP_PX * scale, size)
    address = _address(shown)
    right_start = right_edge - _width(address, size)
    right_runs, right_squares = _place(address, right_start, size, baseline)
    return FooterLayout(
        width=width,
        plot_height=height,
        strip_height=strip_height,
        scale=scale,
        text_px=size,
        baseline=baseline,
        runs=tuple(left_runs + right_runs),
        squares=(left_squares[0], right_squares[0]),
        left_span=(left_runs[0].x, left_end),
        right_span=(right_runs[0].x, max(run.end for run in right_runs)),
        shown_spec=shown,
    )


def _strip(layout: FooterLayout, theme: Theme) -> Image.Image:
    """The strip as an RGB image: the page colour under an RGBA overlay of hairline, text and squares."""
    size = (layout.width, layout.strip_height)
    coverage = Image.new("L", size, 0)
    pen = ImageDraw.Draw(coverage)
    pen.rectangle([0, 0, layout.width - 1, HAIRLINE_PX - 1], fill=_alpha(HAIRLINE_ALPHA))
    for run in layout.runs:
        font = _font(run.bold, layout.text_px)
        pen.text((run.x, layout.baseline), run.text, fill=_alpha(run.alpha), font=font, anchor="ls")
    # Coverage times alpha is the overlay's alpha over a solid ink colour, so antialiased
    # glyph edges keep the ink's hue instead of fading toward black.
    overlay = Image.new("RGBA", size, (*_rgb(neutral_for(theme)), 0))
    overlay.putalpha(coverage)
    marks = ImageDraw.Draw(overlay)
    for square in layout.squares:
        right, bottom = square.left + square.side - 1, square.top + square.side - 1
        marks.rectangle([square.left, square.top, right, bottom], fill=(*_rgb(GREEN), _alpha(DOT_ALPHA)))
    strip = Image.new("RGBA", size, (*_rgb(PAGE[theme]), 255))
    strip.alpha_composite(overlay)
    return strip.convert("RGB")


def add_footer(png: bytes, *, theme: Theme, spec_id: str) -> bytes:
    """`png` with the footer strip appended below it, as an RGB PNG; the raw pixels are kept unchanged."""
    if theme not in PAGE:
        raise ValueError(f"not a theme: {theme!r}")
    with Image.open(io.BytesIO(png)) as source:
        raw = source.convert("RGB")
    with _FONT_LOCK:
        layout = footer_layout(raw.width, raw.height, spec_id=spec_id)
        strip = _strip(layout, theme)
    canvas = Image.new("RGB", (layout.width, layout.height), PAGE[theme])
    canvas.paste(raw, (0, 0))
    canvas.paste(strip, (0, layout.plot_height))
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()
