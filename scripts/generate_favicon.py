#!/usr/bin/env python3
"""Generate the site icons in `app/public/` from the real MonoLisa outlines.

The icon is the `ap` monogram over the brand-green square on the paper ground.
It is written as plain `<path>` outlines: an SVG used as a favicon is rendered
in an isolated context that loads no webfonts, so `<text>` in MonoLisa always
fell back to whatever monospace face the viewer's system had. The raster
siblings exist because crawlers and older clients never read the SVG —
Google's fallback is `/favicon.ico`, iOS wants `/apple-touch-icon.png`, and
the schema.org `Organization.logo` needs a square image (`/icon-512.png`).

Usage:
    uv run --with resvg-py python scripts/generate_favicon.py

The outputs are committed; rerun only when the mark or the palette changes.
MonoLisa is fetched through `core.images` (GCS, cached in `/tmp/anyplot-fonts`)
and only its outlines for the two letters end up in the repository.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import resvg_py
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

from core.images import _get_monolisa_font_path


PUBLIC_DIR = Path(__file__).resolve().parent.parent / "app" / "public"

PAPER = "#F5F3EC"  # --bg-page
INK = "#1A1A17"  # --ink
GREEN = "#009E73"  # --imprint-green

VIEWBOX = 32
TEXT = "ap"
WEIGHT = 700
FONT_SIZE = 19.0
BASELINE = 16.5
LETTER_SPACING = -0.4
SQUARE_TOP = 20.0
SQUARE_SIZE = 5.0
CORNER_RADIUS = 6

ICO_SIZES = [(16, 16), (32, 32), (48, 48)]
PNG_OUTPUTS = {"apple-touch-icon.png": 180, "icon-512.png": 512}


def _format(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def build_svg(font_path: Path, corner_radius: int = CORNER_RADIUS) -> str:
    """Outline the monogram at the icon's geometry and return the SVG document."""
    font = TTFont(font_path)
    glyphs = font.getGlyphSet(location={"wght": WEIGHT})
    cmap = font.getBestCmap()
    scale = FONT_SIZE / font["head"].unitsPerEm

    names = [cmap[ord(char)] for char in TEXT]
    width = sum(glyphs[name].width * scale for name in names) + LETTER_SPACING * (len(names) - 1)
    x = VIEWBOX / 2 - width / 2

    commands = []
    ink_left = None
    for name in names:
        transform = (scale, 0, 0, -scale, x, BASELINE)
        pen = SVGPathPen(glyphs, ntos=_format)
        glyphs[name].draw(TransformPen(pen, transform))
        commands.append(pen.getCommands())
        if ink_left is None:
            bounds = BoundsPen(glyphs)
            glyphs[name].draw(TransformPen(bounds, transform))
            ink_left = bounds.bounds[0]
        x += glyphs[name].width * scale + LETTER_SPACING

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX} {VIEWBOX}">\n'
        f'  <rect width="{VIEWBOX}" height="{VIEWBOX}" rx="{corner_radius}" fill="{PAPER}"/>\n'
        f'  <path fill="{INK}" d="{" ".join(commands)}"/>\n'
        f'  <rect x="{_format(ink_left)}" y="{_format(SQUARE_TOP)}" width="{_format(SQUARE_SIZE)}" '
        f'height="{_format(SQUARE_SIZE)}" fill="{GREEN}"/>\n'
        "</svg>\n"
    )


def render_png(svg: str, size: int) -> bytes:
    return bytes(resvg_py.svg_to_bytes(svg_string=svg, width=size, height=size))


def main() -> None:
    font_path = _get_monolisa_font_path()
    if font_path is None:
        raise SystemExit("MonoLisa is unavailable (GCS access needed); refusing to outline a fallback face.")

    svg = build_svg(font_path)
    (PUBLIC_DIR / "favicon.svg").write_text(svg, encoding="utf-8")

    # The large PNGs are full-bleed squares: iOS and Google apply their own mask,
    # and transparent corners would come out black on a home screen.
    square_svg = build_svg(font_path, corner_radius=0)
    for filename, size in PNG_OUTPUTS.items():
        (PUBLIC_DIR / filename).write_bytes(render_png(square_svg, size))

    # Each ICO entry is rendered at its own size rather than downscaled from one
    # large bitmap, so the 16 px entry keeps the hinting resvg gives it.
    frames = [Image.open(BytesIO(render_png(svg, width))) for width, _ in ICO_SIZES]
    frames[-1].save(PUBLIC_DIR / "favicon.ico", format="ICO", sizes=ICO_SIZES, append_images=frames[:-1])

    for filename in ("favicon.svg", "favicon.ico", *PNG_OUTPUTS):
        print(f"{filename}: {(PUBLIC_DIR / filename).stat().st_size} B")


if __name__ == "__main__":
    main()
