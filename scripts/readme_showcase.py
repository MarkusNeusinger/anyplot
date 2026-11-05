#!/usr/bin/env python3
"""Generate the README's showcase image from the live catalogue.

The layout: the `any.plot()` wordmark with `~/anyplot.ai` on the right; a rule
and "the open plot catalogue · 15 of N specs, one per library"; the title
"N plot specs, 15 libraries, 4 languages." with "4 languages." in MonoLisa's
script italic; a 3 x 5 grid of light previews, one per library, each labelled
with a square in its language's colour and `spec-id · library`; and a footer
with each language's library count, the implementation count and the lines of
code.

Where each part comes from:

* Every number (specs, libraries, languages, implementations, lines of code)
  comes from `https://api.anyplot.ai/stats`.
* The library names and each language's library count come from the registry
  in `core/constants.py`; the language colours are imprint hues from
  `core/palette.py` (`LANGUAGE_COLORS` below names which).
* Each preview is the `_800` light derivative of the implementation's
  `preview_url_light`, read from `https://api.anyplot.ai/specs/{spec_id}`.
* MonoLisa, upright and italic with its `ss01` script set, through the loader
  in `core/images.py`, which reads the fonts from GCS with your ADC (read-only)
  and caches them in `/tmp/anyplot-fonts`. The script stops when either face
  or text shaping (libraqm) is missing: it never falls back to another font.

Usage:
    uv run python scripts/readme_showcase.py [--out docs/assets/readme-showcase.png]

The output is committed. Regenerate it on every release branch
(`agentic/commands/release.md`) and whenever a pick below changes.
"""

from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from core import images, palette
from core.constants import LANGUAGES_METADATA, LIBRARIES_METADATA


ROOT = Path(__file__).resolve().parents[1]
API = "https://api.anyplot.ai"
DEFAULT_OUT = ROOT / "docs" / "assets" / "readme-showcase.png"

# One spec per library, in grid order (row by row). The set must be the registry's libraries.
PICKS: list[tuple[str, str]] = [
    ("polar-bar", "matplotlib"),
    ("raincloud-basic", "seaborn"),
    ("sunburst-basic", "plotly"),
    ("map-tilegrid", "bokeh"),
    ("heatmap-calendar", "altair"),
    ("parliament-basic", "plotnine"),
    ("radar-basic", "pygal"),
    ("marimekko-basic", "letsplot"),
    ("sankey-basic", "ggplot2"),
    ("ridgeline-basic", "makie"),
    ("candlestick-basic", "chartjs"),
    ("heatmap-mandelbrot", "d3"),
    ("treemap-basic", "echarts"),
    ("network-force-directed", "highcharts"),
    ("chord-basic", "muix"),
]

# The imprint hue that marks each language. No language colour exists elsewhere in the code, so this
# mapping is the one place that decides it; the hues themselves are the palette's.
LANGUAGE_COLORS: dict[str, str] = {
    "python": palette.GREEN,
    "r": palette.BLUE,
    "julia": palette.LAVENDER,
    "javascript": palette.OCHRE,
}

WIDTH, HEIGHT = 1600, 2000
PAD = 64
COLS, ROWS = 3, 5
GAP_X = 24
CARD_PADDING = 10
CARD_RADIUS = 14
GRID_TOP = 272
ROW_PITCH = 324
MAX_BYTES = 600_000

THEME = images.LIGHT_THEME


class ShowcaseError(RuntimeError):
    """A source the image depends on is missing or inconsistent; the image is not written."""


# --- fonts -------------------------------------------------------------------------------------


def require_monolisa() -> None:
    """Stop unless both MonoLisa faces load and Pillow can apply `ss01`."""
    upright = images._get_monolisa_font_path(italic=False)
    italic = images._get_monolisa_font_path(italic=True)
    if upright is None or upright.name != Path(images.MONOLISA_FONT_PATH).name:
        raise ShowcaseError("MonoLisa upright could not be loaded from GCS (check your ADC); no fallback font")
    # The loader falls back to the upright face when the italic is missing; that is a failure here.
    if italic is None or italic.name != Path(images.MONOLISA_ITALIC_FONT_PATH).name:
        raise ShowcaseError("MonoLisa italic could not be loaded from GCS (check your ADC); no fallback font")
    if not images.has_text_shaping():
        raise ShowcaseError("Pillow has no libraqm, so the ss01 script italic cannot be drawn")


def font(size: int, weight: int = 500, *, italic: bool = False) -> ImageFont.FreeTypeFont:
    path = images._get_monolisa_font_path(italic=italic)
    if path is None:
        raise ShowcaseError("MonoLisa disappeared from the cache")
    loaded = ImageFont.truetype(str(path), size)
    images._set_variable_weight(loaded, weight)
    return loaded


def advance(
    draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, features: list[str] | None = None
) -> int:
    return int(draw.textlength(text, font=face, features=features))


# --- data --------------------------------------------------------------------------------------


def fetch_stats(client: httpx.Client) -> dict[str, int]:
    response = client.get(f"{API}/stats")
    response.raise_for_status()
    stats = response.json()
    for key in ("specs", "plots", "libraries", "languages", "lines_of_code"):
        if not isinstance(stats.get(key), int):
            raise ShowcaseError(f"/stats has no integer {key!r}")
    return stats


def check_picks(stats: dict[str, int]) -> None:
    libraries = [library for _, library in PICKS]
    registry = {meta["id"] for meta in LIBRARIES_METADATA}
    if len(libraries) != len(set(libraries)) or set(libraries) != registry:
        raise ShowcaseError(f"the picks must name each registry library once: {sorted(registry ^ set(libraries))}")
    if len(PICKS) != stats["libraries"] or len(LANGUAGES_METADATA) != stats["languages"]:
        raise ShowcaseError("the registry and /stats disagree on the library or language count")
    if set(LANGUAGE_COLORS) != {lang["id"] for lang in LANGUAGES_METADATA}:
        raise ShowcaseError("LANGUAGE_COLORS must cover exactly the registry's languages")


def fetch_preview(client: httpx.Client, spec_id: str, library: str) -> Image.Image:
    response = client.get(f"{API}/specs/{spec_id}")
    response.raise_for_status()
    impl = next((i for i in response.json()["implementations"] if i["library_id"] == library), None)
    if impl is None or not str(impl.get("preview_url_light", "")).endswith(".png"):
        raise ShowcaseError(f"{spec_id}/{library} has no light preview")
    url = impl["preview_url_light"].removesuffix(".png") + "_800.png"
    image = client.get(url)
    image.raise_for_status()
    return Image.open(BytesIO(image.content)).convert("RGB")


# --- drawing -----------------------------------------------------------------------------------


def draw_header(draw: ImageDraw.ImageDraw, stats: dict[str, int]) -> None:
    wordmark_size = 56
    wordmark_top = 52
    images._draw_anyplot_wordmark(draw, PAD, wordmark_top, font_size=wordmark_size, theme=THEME)

    domain_face = font(28)
    domain = f"~/{images.DOMAIN}"
    left, top, right, bottom = draw.textbbox((0, 0), domain, font=domain_face)
    domain_y = wordmark_top + int(wordmark_size * 0.62) - (top + bottom) // 2
    draw.text((WIDTH - PAD - (right - left), domain_y), domain, font=domain_face, fill=THEME["ink_muted"])

    eyebrow_face = font(26)
    eyebrow = f"the open plot catalogue · {len(PICKS)} of {stats['specs']} specs, one per library"
    eyebrow_y = 148
    _, top, _, bottom = draw.textbbox((0, 0), eyebrow, font=eyebrow_face)
    rule_y = eyebrow_y + (top + bottom) // 2
    draw.line([(PAD, rule_y), (PAD + 44, rule_y)], fill=THEME["rule"], width=2)
    draw.text((PAD + 64, eyebrow_y), eyebrow, font=eyebrow_face, fill=THEME["ink_muted"])

    title_y = 196
    bold = font(42, 700)
    script = font(42, 400, italic=True)
    lead = f"{stats['specs']} plot specs, {stats['libraries']} libraries, "
    accent = f"{stats['languages']} languages."
    draw.text((PAD, title_y), lead, font=bold, fill=THEME["ink"])
    features = [images.MONOLISA_SCRIPT_FEATURE]
    draw.text(
        (PAD + advance(draw, lead, bold), title_y), accent, font=script, fill=THEME["ink_soft"], features=features
    )


def draw_grid(canvas: Image.Image, draw: ImageDraw.ImageDraw, previews: list[Image.Image]) -> None:
    card_w = (WIDTH - 2 * PAD - (COLS - 1) * GAP_X) // COLS
    content_w = card_w - 2 * CARD_PADDING
    content_h = round(content_w * 9 / 16)
    names = {meta["id"]: meta["name"].lower() for meta in LIBRARIES_METADATA}
    languages = {meta["id"]: meta["language_id"] for meta in LIBRARIES_METADATA}
    square = 14

    for index, ((spec_id, library), preview) in enumerate(zip(PICKS, previews, strict=True)):
        col, row = index % COLS, index // COLS
        x = PAD + col * (card_w + GAP_X)
        y = GRID_TOP + row * ROW_PITCH

        content = Image.new("RGB", (content_w, content_h), THEME["bg_surface"])
        fitted = images._fit_image(preview, content_w, content_h)
        content.paste(fitted, ((content_w - fitted.width) // 2, (content_h - fitted.height) // 2))
        images._draw_rounded_card(
            canvas,
            content,
            x,
            y,
            padding=CARD_PADDING,
            radius=CARD_RADIUS,
            shadow_offset=4,
            surface_color=THEME["bg_surface"],
            rule_color=THEME["rule"],
            shadow_color=THEME["card_shadow"],
        )

        spec_text, lib_text = spec_id, f" · {names[library]}"
        # 21 px is the reference's size; a label wider than its card steps down until it fits.
        for size in range(21, 15, -1):
            label_face = font(size)
            text_w = advance(draw, spec_text, label_face) + advance(draw, lib_text, label_face)
            total_w = square + 12 + text_w
            if total_w <= card_w:
                break
        else:
            raise ShowcaseError(f"the label {spec_text}{lib_text} does not fit its card")
        label_x = x + (card_w - total_w) // 2
        label_y = y + content_h + 2 * CARD_PADDING + 16
        _, top, _, bottom = draw.textbbox((0, 0), spec_text, font=label_face)
        square_y = label_y + (top + bottom) // 2 - square // 2
        draw.rectangle(
            [label_x, square_y, label_x + square, square_y + square], fill=LANGUAGE_COLORS[languages[library]]
        )
        text_x = label_x + square + 12
        draw.text((text_x, label_y), spec_text, font=label_face, fill=THEME["ink"])
        draw.text(
            (text_x + advance(draw, spec_text, label_face), label_y), lib_text, font=label_face, fill=THEME["ink_muted"]
        )


def draw_footer(draw: ImageDraw.ImageDraw, stats: dict[str, int]) -> None:
    rule_y = 1904
    draw.line([(PAD, rule_y), (WIDTH - PAD, rule_y)], fill=THEME["rule"], width=2)
    face = font(23)
    text_y = 1930
    _, top, _, bottom = draw.textbbox((0, 0), "python", font=face)
    square = 14
    square_y = text_y + (top + bottom) // 2 - square // 2

    counts = {lang["id"]: 0 for lang in LANGUAGES_METADATA}
    for meta in LIBRARIES_METADATA:
        counts[meta["language_id"]] += 1
    right = f"{stats['plots']:,} implementations · {round(stats['lines_of_code'] / 1000)}k lines of code"
    right_x = WIDTH - PAD - advance(draw, right, face)

    x = PAD
    for lang_id, count in counts.items():
        label = f"{lang_id} ({count})"
        if x + square + 12 + advance(draw, label, face) + 40 > right_x:
            raise ShowcaseError("the footer's languages run into its counts")
        draw.rectangle([x, square_y, x + square, square_y + square], fill=LANGUAGE_COLORS[lang_id])
        draw.text((x + square + 12, text_y), label, font=face, fill=THEME["ink_soft"])
        x += square + 12 + advance(draw, label, face) + 32
    draw.text((right_x, text_y), right, font=face, fill=THEME["ink_muted"])


def save(canvas: Image.Image, out: Path) -> int:
    """Write the PNG, quantized to 256 colours when the full-colour file is over MAX_BYTES."""
    out.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    canvas.save(buffer, "PNG", optimize=True)
    if buffer.tell() > MAX_BYTES:
        buffer = BytesIO()
        quantized = canvas.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        quantized.save(buffer, "PNG", optimize=True)
    out.write_bytes(buffer.getvalue())
    return buffer.tell()


def build(out: Path) -> tuple[dict[str, int], int]:
    require_monolisa()
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        stats = fetch_stats(client)
        check_picks(stats)
        previews = [fetch_preview(client, spec_id, library) for spec_id, library in PICKS]

    canvas = Image.new("RGB", (WIDTH, HEIGHT), THEME["bg_page"])
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, stats)
    draw_grid(canvas, draw, previews)
    draw_footer(draw, stats)
    return stats, save(canvas, out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output PNG (default: {DEFAULT_OUT})")
    args = parser.parse_args()
    try:
        stats, size = build(args.out)
    except (ShowcaseError, httpx.HTTPError) as error:
        print(f"readme_showcase: {error}", file=sys.stderr)
        return 1
    print(f"wrote {args.out} ({size:,} bytes) from /stats {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
