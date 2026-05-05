"""Image processing utilities for anyplot.

This module provides reusable functions for image manipulation:
- Thumbnail generation with aspect ratio preservation
- PNG optimization with pngquant
- Branded og:image generation for social media (any.plot() visual style)
- Collage generation for spec overview pages
- Before/after comparison images for update reviews

Usage as CLI:
    python -m core.images thumbnail input.png output.png 400
    python -m core.images process input.png output.png thumb.png
    python -m core.images brand input.png output.png "scatter-basic" "matplotlib"
    python -m core.images collage output.png img1.png img2.png img3.png img4.png
    python -m core.images compare before.png after.png output.png [spec_id] [library]
    python -m core.images home output.png [theme]
"""

import logging
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


logger = logging.getLogger(__name__)

# Responsive image sizes and formats (issue #5191)
RESPONSIVE_SIZES = [1200, 800, 400]
RESPONSIVE_FORMATS: list[tuple[str, str, dict]] = [("png", "PNG", {}), ("webp", "WEBP", {"quality": 80})]
WEBP_FULL_QUALITY = 85

# GCS bucket for static assets (fonts)
GCS_STATIC_BUCKET = "anyplot-static"
MONOLISA_FONT_PATH = "fonts/MonoLisaVariableNormal.ttf"
MONOLISA_ITALIC_FONT_PATH = "fonts/MonoLisaVariableItalic.ttf"
FONT_CACHE_DIR = Path("/tmp/anyplot-fonts")

# =============================================================================
# Design tokens — match docs/reference/style-guide.md (§4 Color System)
# =============================================================================
#
# Theme dicts so OG images can be rendered light or dark from the same code.
# Token names mirror the CSS custom properties defined in the React app
# (`--bg-page`, `--ink`, `--ok-green`, etc.) so the OG cards read as a direct
# translation of the in-product surfaces.

OK_GREEN = "#009E73"  # brand anchor — the dot in any.plot()
OK_VERMILLION = "#D55E00"
OK_BLUE = "#0072B2"
OK_PURPLE = "#CC79A7"
OK_ORANGE = "#E69F00"
OK_SKY = "#56B4E9"
OK_YELLOW = "#F0E442"

OKABE_PALETTE = [OK_GREEN, OK_VERMILLION, OK_BLUE, OK_PURPLE, OK_ORANGE, OK_SKY, OK_YELLOW]

LIGHT_THEME: dict[str, str] = {
    "bg_page": "#F5F3EC",  # warm cream — matches `--bg-page` in app/src/styles/tokens.css
    "bg_surface": "#FAF8F1",  # plot card surface — `--bg-surface`
    "ink": "#1A1A17",  # primary text — `--ink`
    "ink_soft": "#4A4A44",  # secondary text — `--ink-soft`
    "ink_muted": "#6B6A63",  # tertiary / meta — `--ink-muted`
    "rule": "#DFDDD6",  # ~rgba(26,26,23,0.10) flattened on bg_page
    "card_shadow": "#D9D5C8",
}

DARK_THEME: dict[str, str] = {
    "bg_page": "#121210",  # warm near-black — matches dark `--bg-page` in tokens.css
    "bg_surface": "#1A1A17",
    "ink": "#F0EFE8",
    "ink_soft": "#B8B7B0",
    "ink_muted": "#A8A79F",
    "rule": "#1E1E1B",  # ~rgba(240,239,232,0.10) flattened on bg_page
    "card_shadow": "#000000",
}

# Library → Okabe-Ito accent color used for the colored 8x8 chip square
# next to library.method() callouts. Falls back to brand green for unknowns.
LIBRARY_COLORS: dict[str, str] = {
    "matplotlib": OK_BLUE,
    "seaborn": OK_SKY,
    "plotly": OK_PURPLE,
    "bokeh": OK_VERMILLION,
    "altair": OK_GREEN,
    "plotnine": OK_ORANGE,
    "pygal": OK_YELLOW,
    "highcharts": OK_BLUE,
    "letsplot": OK_GREEN,
    "lets-plot": OK_GREEN,
}

# Library → typical method call hint shown inside `library.method()` chips.
# Pure visual texture — these don't have to match any single example exactly.
LIBRARY_METHOD_HINTS: dict[str, str] = {
    "matplotlib": "pyplot.plot()",
    "seaborn": "scatterplot()",
    "plotly": "graph_objects.Figure()",
    "bokeh": "figure()",
    "altair": "Chart.mark_point()",
    "plotnine": "ggplot()",
    "pygal": "Line()",
    "highcharts": "Chart()",
    "letsplot": "ggplot()",
    "lets-plot": "ggplot()",
}

# Backwards-compatible aliases — kept so any external caller / test that imports
# the older constant names doesn't blow up. New code should reference the theme
# dicts above directly.
ANYPLOT_BG = LIGHT_THEME["bg_page"]
ANYPLOT_DARK = LIGHT_THEME["ink"]
ANYPLOT_BLUE = OK_BLUE  # legacy "brand blue" alias — actually Okabe blue now
ANYPLOT_YELLOW = OK_YELLOW
COLOR_LABEL_GRAY = LIGHT_THEME["ink_muted"]
COLOR_PLACEHOLDER_GRAY = LIGHT_THEME["ink_muted"]

# Domain string surfaced in the masthead-style top rule on every variant
# (the issue explicitly requires `anyplot.ai` to be visible on every OG card).
DOMAIN = "anyplot.ai"

# Tagline rotation — keep aligned with style-guide §3.3.
TAGLINE_FULL = "get inspired. grab the code. make it yours."
TAGLINE_SHORT = "any library."

# OG image dimensions (recommended for social media)
OG_WIDTH = 1200
OG_HEIGHT = 630
HEADER_HEIGHT = 80

# --- OG single-card layout ---
OG_OUTER_PADDING = 48  # outer margin around the card content
OG_MASTHEAD_HEIGHT = 38  # top rule height (`any.plot()  …  ~/anyplot.ai`)
OG_MASTHEAD_GAP = 22  # space between masthead rule and section title
OG_SECTION_TITLE_GAP = 16  # space between section title and plot card
OG_FOOTER_GAP = 18  # space between plot card and footer chip row
OG_CARD_PADDING = 18

# --- OG collage layout ---
COLLAGE_TOP_MARGIN = OG_OUTER_PADDING
COLLAGE_SIDE_MARGIN = OG_OUTER_PADDING
COLLAGE_CARD_GAP_X = 14
COLLAGE_CARD_GAP_Y = 30  # extra vertical room so the chip label sits below each card
COLLAGE_CARD_PADDING = 8
COLLAGE_LABEL_GAP = 8
COLLAGE_BOTTOM_MARGIN = OG_OUTER_PADDING
COLLAGE_COLS = 3
COLLAGE_ROWS = 2
COLLAGE_MAX_IMAGES = 6
COLLAGE_CARD_ASPECT = 16 / 9
COLLAGE_CARD_RADIUS = 10
COLLAGE_SHADOW_OFFSET = 2

# --- Comparison layout ---
COMPARE_WIDTH = 2400
COMPARE_HEIGHT = 800
COMPARE_MARGIN = 48
COMPARE_GAP = 36
COMPARE_HEADER_HEIGHT = 52
COMPARE_LABEL_HEIGHT = 44


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    """Return (width, height) of rendered text via textbbox."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _text_advance(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    """Return the horizontal advance for a string (where the next glyph anchors).

    Uses Pillow's `textlength()` which returns the true font advance — what we
    want for laying out adjacent text runs (the wordmark, method chips, etc).
    `textbbox(...)[2]` would return the rightmost painted pixel instead, which
    drifts on fonts with non-zero side bearings or negative left bearings.
    """
    return int(draw.textlength(text, font=font))


# Optional: pngquant for better compression
try:
    import subprocess

    # `timeout=5` so a wedged binary can't block FastAPI startup forever
    # (this runs at module import time → before app is serving).
    _HAS_PNGQUANT = subprocess.run(["pngquant", "--version"], capture_output=True, timeout=5).returncode == 0
except (FileNotFoundError, subprocess.SubprocessError, subprocess.TimeoutExpired):  # fmt: skip
    _HAS_PNGQUANT = False


def create_thumbnail(input_path: str | Path, output_path: str | Path, width: int = 1200) -> tuple[int, int]:
    """Create a thumbnail maintaining aspect ratio.

    Args:
        input_path: Path to the source image.
        output_path: Path where the thumbnail will be saved.
        width: Target width in pixels (default: 1200). Height is calculated to maintain aspect ratio.

    Returns:
        Tuple of (width, height) of the created thumbnail.

    Raises:
        FileNotFoundError: If input_path does not exist.
        PIL.UnidentifiedImageError: If input is not a valid image.
    """
    img = Image.open(input_path)
    ratio = width / img.width
    new_size = (width, int(img.height * ratio))
    thumb = img.resize(new_size, Image.Resampling.LANCZOS)
    thumb.save(output_path, optimize=True)
    return new_size


def optimize_png(input_path: str | Path, output_path: str | Path | None = None, quality: int = 80) -> int:
    """Optimize PNG file size using pngquant (if available) or Pillow.

    Args:
        input_path: Path to the source PNG image.
        output_path: Path for optimized image. If None, overwrites input.
        quality: Quality level for lossy compression (1-100). Only used with pngquant.

    Returns:
        Size reduction in bytes (positive = smaller file).
    """
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else input_path
    original_size = input_path.stat().st_size

    if _HAS_PNGQUANT:
        import subprocess

        subprocess.run(
            ["pngquant", "--force", "--quality", f"{quality}-100", "--output", str(output_path), str(input_path)],
            timeout=60,
            check=True,
        )
    else:
        # Fallback: Pillow optimize
        img = Image.open(input_path)
        img.save(output_path, optimize=True)

    new_size = output_path.stat().st_size
    return original_size - new_size


def process_plot_image(
    input_path: str | Path,
    output_path: str | Path,
    thumb_path: str | Path | None = None,
    thumb_width: int = 1200,
    optimize: bool = True,
) -> dict[str, str | tuple[int, int] | int]:
    """Process a plot image: optimize and create thumbnail.

    This is the main entry point for image processing in the workflow.
    Combines PNG optimization and thumbnail generation.

    Args:
        input_path: Path to the source plot image.
        output_path: Path for the optimized full-size image.
        thumb_path: Path for the thumbnail. If None, no thumbnail is created.
        thumb_width: Width of the thumbnail in pixels.
        optimize: Whether to optimize PNG file size with pngquant.

    Returns:
        Dictionary with processing results:
        - 'output': Path to the output image
        - 'thumbnail': Path to thumbnail (if created)
        - 'thumb_size': Tuple of thumbnail dimensions (if created)
        - 'bytes_saved': Bytes saved by optimization (if optimized)
    """
    result: dict[str, str | tuple[int, int] | int] = {"output": str(output_path)}

    # Copy image (with basic Pillow optimization)
    img = Image.open(input_path)
    img.save(output_path, optimize=True)

    # Optimize PNG with pngquant
    if optimize:
        bytes_saved = optimize_png(output_path)
        result["bytes_saved"] = bytes_saved

    # Create thumbnail from the processed image
    if thumb_path:
        thumb_size = create_thumbnail(output_path, thumb_path, width=thumb_width)
        # Also optimize thumbnail
        if optimize:
            optimize_png(thumb_path)
        result["thumbnail"] = str(thumb_path)
        result["thumb_size"] = thumb_size

    return result


def create_responsive_variants(
    input_path: str | Path, output_dir: str | Path, sizes: list[int] | None = None, optimize: bool = True
) -> list[dict[str, str | int]]:
    """Generate multi-size, multi-format image variants for responsive delivery.

    Creates sized PNGs and WebPs (400/800/1200) plus a full-size WebP from the
    source image. The input file's stem is used as the basename so theme-aware
    inputs produce theme-aware variants:

        input plot-light.png → plot-light_400.png, plot-light_400.webp,
                               plot-light_800.png, plot-light_800.webp,
                               plot-light_1200.png, plot-light_1200.webp,
                               plot-light.webp
        input plot-dark.png  → plot-dark_400.png, …, plot-dark.webp
        input plot.png       → plot_400.png, …, plot.webp (legacy single-theme)

    Args:
        input_path: Path to the source plot image (plot.png / plot-light.png / plot-dark.png).
        output_dir: Directory where variants will be written.
        sizes: Override default RESPONSIVE_SIZES if needed.
        optimize: Whether to optimize PNGs with pngquant.

    Returns:
        List of dicts, each with 'path', 'width', 'height', 'format'.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Derive the basename from the input stem so plot-light.png → "plot-light",
    # plot-dark.png → "plot-dark", plot.png → "plot".
    basename = input_path.stem

    with Image.open(input_path) as src:
        if src.mode in ("RGBA", "P"):
            img = src.convert("RGB")
        else:
            img = src.copy()

    results: list[dict[str, str | int]] = []
    target_sizes = sizes or RESPONSIVE_SIZES

    # Sized variants (e.g. plot-light_1200.png, plot-light_1200.webp, ...)
    for width in target_sizes:
        # Skip sizes larger than the original
        if width >= img.width:
            continue
        ratio = width / img.width
        actual_width = width
        actual_height = int(img.height * ratio)
        resized = img.resize((actual_width, actual_height), Image.Resampling.LANCZOS)

        for ext, fmt, opts in RESPONSIVE_FORMATS:
            out_path = output_dir / f"{basename}_{width}.{ext}"
            resized.save(out_path, fmt, optimize=True, **opts)

            # Optimize PNG with pngquant
            if optimize and fmt == "PNG":
                optimize_png(out_path)

            results.append({"path": str(out_path), "width": actual_width, "height": actual_height, "format": ext})
            logger.info("Created %s (%dx%d)", out_path.name, actual_width, actual_height)

    # Full-size WebP (e.g. plot-light.webp)
    webp_path = output_dir / f"{basename}.webp"
    img.save(webp_path, "WEBP", quality=WEBP_FULL_QUALITY)
    results.append({"path": str(webp_path), "width": img.width, "height": img.height, "format": "webp"})
    logger.info("Created %s (%dx%d)", webp_path.name, img.width, img.height)

    return results


# =============================================================================
# Font loading (MonoLisa from GCS, with system-font fallback)
# =============================================================================


def _get_monolisa_font_path(local_only: bool = False, italic: bool = False) -> Path | None:
    """Get path to MonoLisa font, downloading from GCS if needed.

    Args:
        local_only: If True, only return the font if already cached locally.
        italic: If True, prefer the italic variant (script accents). Falls back
            to upright when the italic file is unavailable.

    Returns:
        Path to font file, or None if unavailable.
    """
    cache_filename = "MonoLisaVariableItalic.ttf" if italic else "MonoLisaVariableNormal.ttf"
    gcs_blob = MONOLISA_ITALIC_FONT_PATH if italic else MONOLISA_FONT_PATH
    cached_font = FONT_CACHE_DIR / cache_filename

    # Return cached font if exists
    if cached_font.exists():
        return cached_font

    if local_only:
        # If italic was requested but isn't cached, fall through to upright cache.
        if italic:
            upright_cached = FONT_CACHE_DIR / "MonoLisaVariableNormal.ttf"
            if upright_cached.exists():
                return upright_cached
        return None

    # Try to download from GCS
    try:
        from google.cloud import storage

        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        client = storage.Client()
        bucket = client.bucket(GCS_STATIC_BUCKET)
        blob = bucket.blob(gcs_blob)
        blob.download_to_filename(str(cached_font))
        logger.info(f"Downloaded MonoLisa font to {cached_font}")
        return cached_font
    except Exception as e:
        logger.warning(f"Could not load MonoLisa font from GCS ({gcs_blob}): {e}")
        # Italic missing → fall back to upright so we still get *some* MonoLisa.
        if italic:
            return _get_monolisa_font_path(local_only=local_only, italic=False)
        return None


def _get_font(
    size: int = 32, weight: int = 700, local_only: bool = False, italic: bool = False
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a suitable font for text rendering.

    Tries to load MonoLisa from GCS cache, falls back to system fonts.

    Args:
        size: Font size in pixels
        weight: Font weight (100-900, default 700 for bold like website)
        local_only: If True, skip GCS download and only use locally cached or system fonts.
        italic: If True, prefer the italic MonoLisa subset (script accent for taglines).
    """
    # Try MonoLisa (from local cache, or download from GCS if allowed)
    monolisa_path = _get_monolisa_font_path(local_only=local_only, italic=italic)
    if monolisa_path:
        try:
            font = ImageFont.truetype(str(monolisa_path), size)
            # Set variable font weight (MonoLisa supports 100-1000)
            try:
                font.set_variation_by_axes([weight])
            except Exception:
                logger.debug("Font variation not supported for MonoLisa at weight=%d", weight)
            return font
        except OSError:
            logger.warning("Failed to load MonoLisa font from %s", monolisa_path)

    # Fallback to system fonts
    fallback_fonts = ["DejaVuSansMono-Bold.ttf", "DejaVuSansMono.ttf", "LiberationMono-Bold.ttf", "FreeMono.ttf"]

    for font_name in fallback_fonts:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue

    # Fallback to default
    return ImageFont.load_default()


# =============================================================================
# Brand drawing primitives (any.plot() wordmark, method chips, masthead)
# =============================================================================


def _draw_anyplot_wordmark(
    draw: ImageDraw.ImageDraw, x: int, y: int, font_size: int = 36, theme: dict[str, str] | None = None
) -> int:
    """Draw the `any.plot()` wordmark in the new visual style.

    - `any` and `plot` in `--ink`, MonoLisa Bold
    - `.` is the actual MonoLisa period glyph recolored to brand green (matches
      the website where the dot is a `.` character with `color: var(--ok-green)`)
    - `()` in `--ink` at 45% opacity, normal weight (not bold)

    Args:
        draw: ImageDraw instance to draw on
        x: X coordinate for text start (top-left)
        y: Y coordinate for text top
        font_size: Font size in pixels
        theme: Theme dict (defaults to LIGHT_THEME)

    Returns:
        Total horizontal advance of the rendered wordmark.
    """
    theme = theme or LIGHT_THEME
    bold_font = _get_font(font_size, weight=700)
    light_font = _get_font(font_size, weight=400)

    ink = theme["ink"]
    # Approximate `--ink` at 45% opacity by blending against `bg_page`.
    paren_color = _blend(ink, theme["bg_page"], 0.45)

    cursor_x = x

    # "any" — bold ink
    draw.text((cursor_x, y), "any", fill=ink, font=bold_font)
    cursor_x += _text_advance(draw, "any", bold_font)

    # "." — the actual MonoLisa period glyph, recolored brand green. Matches the
    # website where the dot is a `.` character with `color: var(--ok-green)` and
    # a 1.3× scale, NOT a filled circle (which used to read way too heavy).
    draw.text((cursor_x, y), ".", fill=OK_GREEN, font=bold_font)
    cursor_x += _text_advance(draw, ".", bold_font)

    # "plot" — bold ink
    draw.text((cursor_x, y), "plot", fill=ink, font=bold_font)
    cursor_x += _text_advance(draw, "plot", bold_font)

    # "()" — ghosted, regular weight
    draw.text((cursor_x, y), "()", fill=paren_color, font=light_font)
    cursor_x += _text_advance(draw, "()", light_font)

    return cursor_x - x


# Legacy alias — the function was previously named `_draw_anyplot_logo`. Kept so
# any external consumer (and the existing test suite) keeps working.
_draw_anyplot_logo = _draw_anyplot_wordmark


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Parse `#RRGGBB` into an (r, g, b) tuple."""
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _blend(fg: str, bg: str, alpha: float) -> tuple[int, int, int]:
    """Blend `fg` over `bg` at `alpha` opacity. Returns an (r, g, b) tuple.

    Used to fake CSS `opacity: 0.45` on opaque PIL canvases — `()` in the
    wordmark, dotted underlines, soft labels.
    """
    fr, fg_, fb = _hex_to_rgb(fg)
    br, bg_, bb = _hex_to_rgb(bg)
    return (
        int(fr * alpha + br * (1 - alpha)),
        int(fg_ * alpha + bg_ * (1 - alpha)),
        int(fb * alpha + bb * (1 - alpha)),
    )


def _draw_masthead(
    draw: ImageDraw.ImageDraw,
    canvas_width: int,
    top_y: int,
    theme: dict[str, str],
    *,
    font_size: int = 22,
    show_domain: bool = True,
) -> int:
    """Draw the top brand bar: `any.plot()` wordmark on the left, `~/anyplot.ai` on the right.

    Mirrors the React app's <Masthead> component (style-guide §6.4) so the OG
    card immediately reads as a slice of the site.

    Returns:
        The y-coordinate of the rule line drawn underneath the masthead.
    """
    wordmark_y = top_y
    _draw_anyplot_wordmark(draw, OG_OUTER_PADDING, wordmark_y, font_size=font_size, theme=theme)

    if show_domain:
        domain_font = _get_font(int(font_size * 0.62), weight=500)
        domain_text = f"~/{DOMAIN}"
        domain_w, _ = _text_size(draw, domain_text, domain_font)
        domain_x = canvas_width - OG_OUTER_PADDING - domain_w
        # Vertically center against the wordmark's cap-height.
        domain_y = wordmark_y + int(font_size * 0.32)
        draw.text((domain_x, domain_y), domain_text, fill=theme["ink_muted"], font=domain_font)

    rule_y = wordmark_y + font_size + int(font_size * 0.55)
    draw.line([(OG_OUTER_PADDING, rule_y), (canvas_width - OG_OUTER_PADDING, rule_y)], fill=theme["rule"], width=1)
    return rule_y


def _draw_section_title(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    theme: dict[str, str],
    *,
    title_size: int = 30,
    prompt: str = "❯",
) -> int:
    """Draw a `❯ section-title` line in the section-header pattern (style-guide §6.3).

    The chevron sits in `--ink-muted`, the title in `--ink`. Returns the bottom
    y-coordinate (caller advances from there).
    """
    prompt_font = _get_font(int(title_size * 0.7), weight=500)
    title_font = _get_font(title_size, weight=500)

    cursor_x = x
    # Prompt is offset down a hair so the chevron's optical center aligns with the title baseline.
    draw.text((cursor_x, y + int(title_size * 0.08)), prompt, fill=theme["ink_muted"], font=prompt_font)
    cursor_x += _text_advance(draw, prompt, prompt_font) + int(title_size * 0.35)
    draw.text((cursor_x, y), text, fill=theme["ink"], font=title_font)
    return y + int(title_size * 1.2)


def _draw_eyebrow_and_domain(
    draw: ImageDraw.ImageDraw,
    theme: dict[str, str],
    *,
    eyebrow_text: str,
    pad: int = 56,
    font_size: int = 20,
    with_wordmark: bool = False,
    wordmark_size: int = 30,
) -> int:
    """Top frame for an OG card — eyebrow rule + text on the left, `~/{domain}` on the right.

    When `with_wordmark` is set, the `any.plot()` brand wordmark is rendered
    above the eyebrow row (left-aligned, with the domain centered against it on
    the right). Used by branded + collage variants so `any.plot()` shows on
    every share card; home omits it because the giant centered headline IS the
    wordmark.
    Returns the y-coord directly below the rendered top frame.
    """
    font = _get_font(font_size, weight=500)
    domain_text = f"~/{DOMAIN}"
    domain_w, _ = _text_size(draw, domain_text, font)
    rule_w = 32

    if with_wordmark:
        # Row 1 — any.plot() wordmark left + domain right
        _draw_anyplot_wordmark(draw, pad, pad, font_size=wordmark_size, theme=theme)
        domain_y = pad + (wordmark_size - font_size) // 2 + 4
        draw.text((OG_WIDTH - pad - domain_w, domain_y), domain_text, fill=theme["ink_muted"], font=font)
        # Row 2 — eyebrow rule + text
        eyebrow_y = pad + wordmark_size + 18
        rule_y = eyebrow_y + 14
        draw.line([(pad, rule_y), (pad + rule_w, rule_y)], fill=theme["rule"], width=1)
        draw.text((pad + rule_w + 16, eyebrow_y), eyebrow_text, fill=theme["ink_muted"], font=font)
        return eyebrow_y + font_size + 18

    # Single-row layout (home): eyebrow left, domain right.
    rule_y = pad + 14
    draw.line([(pad, rule_y), (pad + rule_w, rule_y)], fill=theme["rule"], width=1)
    draw.text((pad + rule_w + 16, pad), eyebrow_text, fill=theme["ink_muted"], font=font)
    draw.text((OG_WIDTH - pad - domain_w, pad), domain_text, fill=theme["ink_muted"], font=font)
    return pad + font_size + 18


def _draw_method_chip(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    library: str,
    method: str | None,
    theme: dict[str, str],
    *,
    chip_size: int = 18,
) -> int:
    """Draw a colored 8x8 square + `library.method()` label (style-guide §7.4).

    Returns the horizontal advance of the rendered chip.
    """
    color = LIBRARY_COLORS.get(library.lower(), OK_GREEN)
    method = method or LIBRARY_METHOD_HINTS.get(library.lower(), "plot()")
    label = f"{library}.{method}"

    label_font = _get_font(chip_size, weight=500)

    # Colored square — 8x8 visual unit per the style guide, scaled with chip size.
    square = max(int(chip_size * 0.55), 8)
    square_y = y + (chip_size - square) // 2 + int(chip_size * 0.12)
    draw.rectangle([x, square_y, x + square, square_y + square], fill=color)

    text_x = x + square + int(chip_size * 0.55)
    draw.text((text_x, y), label, fill=theme["ink"], font=label_font)
    return _text_advance(draw, label, label_font) + (text_x - x)


# =============================================================================
# Card / image utilities
# =============================================================================


def _draw_rounded_card(
    base: Image.Image,
    content: Image.Image,
    x: int,
    y: int,
    padding: int = 12,
    radius: int = 16,
    shadow_offset: int = 4,
    shadow_blur: int = 8,
    *,
    surface_color: str | tuple[int, int, int] = "#FAF8F1",
    rule_color: str | tuple[int, int, int] = "#E2DFD6",
    shadow_color: str | tuple[int, int, int] = "#D9D5C8",
) -> None:
    """Draw a rounded card with shadow containing the content image.

    Args:
        base: Base image to draw on
        content: Content image to put in the card
        x: X position for the card
        y: Y position for the card
        padding: Padding inside the card
        radius: Corner radius
        shadow_offset: Shadow offset in pixels
        shadow_blur: Shadow blur amount (kept for backwards compat — unused)
        surface_color: Card background fill
        rule_color: 1px border color around the card
        shadow_color: Soft shadow fill
    """
    del shadow_blur  # kept in signature for backwards compatibility
    card_width = content.width + 2 * padding
    card_height = content.height + 2 * padding

    # Soft shadow rectangle, offset down-right.
    shadow = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([0, 0, card_width - 1, card_height - 1], radius=radius, fill=shadow_color)
    base.paste(shadow, (x + shadow_offset, y + shadow_offset), shadow)

    # Card surface + thin rule border (matches `border: 1px solid var(--rule)` per §7.2).
    card = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    card_draw.rounded_rectangle(
        [0, 0, card_width - 1, card_height - 1], radius=radius, fill=surface_color, outline=rule_color, width=1
    )
    base.paste(card, (x, y), card)

    # Paste content (the actual plot)
    base.paste(content, (x + padding, y + padding))


def _load_plot_image(source: str | Path | Image.Image | bytes) -> Image.Image:
    """Load a plot image from various sources, converting to RGB."""
    if isinstance(source, bytes):
        img = Image.open(BytesIO(source))
    elif isinstance(source, Image.Image):
        img = source
    else:
        img = Image.open(source)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    return img


def _finalize_og_image(
    final: Image.Image, output_path: str | Path | None, theme: dict[str, str] | None = None
) -> Image.Image | bytes:
    """Composite RGBA→RGB and either save or return bytes."""
    theme = theme or LIGHT_THEME
    final_rgb = Image.new("RGB", final.size, theme["bg_page"])
    final_rgb.paste(final, mask=final.split()[3] if final.mode == "RGBA" else None)

    if output_path:
        final_rgb.save(output_path, "PNG", optimize=True)
        return final_rgb

    buffer = BytesIO()
    final_rgb.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


# =============================================================================
# Before/After Comparison Images
# =============================================================================


def create_comparison_image(
    before_path: str | Path | None,
    after_path: str | Path,
    output_path: str | Path,
    spec_id: str = "",
    library: str = "",
    *,
    theme: str = "light",
) -> None:
    """Create a side-by-side before/after comparison image in the new any.plot() style.

    Layout: [margin] [BEFORE card] [gap] [AFTER card] [margin]
    with an `any.plot()` masthead on top and a method chip below the panels.
    """
    theme_dict = DARK_THEME if theme == "dark" else LIGHT_THEME

    canvas = Image.new("RGB", (COMPARE_WIDTH, COMPARE_HEIGHT), theme_dict["bg_page"])
    draw = ImageDraw.Draw(canvas)

    # --- Masthead: any.plot() left, ~/anyplot.ai right ---
    rule_y = _draw_masthead(draw, COMPARE_WIDTH, COMPARE_MARGIN, theme_dict, font_size=28)

    # --- Section title: ❯ {spec_id} (or library if no spec_id) ---
    section_title = spec_id or library or "compare"
    title_y = rule_y + 18
    _draw_section_title(draw, section_title, COMPARE_MARGIN, title_y, theme_dict, title_size=26)

    panel_top = title_y + 56
    panel_height = COMPARE_HEIGHT - panel_top - COMPARE_MARGIN - 60  # leave room for chip row
    panel_width = (COMPARE_WIDTH - 2 * COMPARE_MARGIN - COMPARE_GAP) // 2

    # --- Panel labels (BEFORE / AFTER) ---
    label_font = _get_font(20, weight=500)
    before_label = "before — current"
    after_label = "after — updated"

    label_y = panel_top - 28
    draw.text((COMPARE_MARGIN, label_y), before_label, fill=theme_dict["ink_muted"], font=label_font)
    after_panel_x = COMPARE_MARGIN + panel_width + COMPARE_GAP
    draw.text((after_panel_x, label_y), after_label, fill=theme_dict["ink_muted"], font=label_font)

    # --- Before card ---
    canvas_rgba = canvas.convert("RGBA")
    if before_path and Path(before_path).exists():
        before_img = _load_plot_image(before_path)
        before_img = _fit_image(before_img, panel_width - 2 * OG_CARD_PADDING, panel_height - 2 * OG_CARD_PADDING)
        card_x = COMPARE_MARGIN + (panel_width - before_img.width - 2 * OG_CARD_PADDING) // 2
        card_y = panel_top + (panel_height - before_img.height - 2 * OG_CARD_PADDING) // 2
        _draw_rounded_card(
            canvas_rgba,
            before_img,
            card_x,
            card_y,
            padding=OG_CARD_PADDING,
            surface_color=theme_dict["bg_surface"],
            rule_color=theme_dict["rule"],
            shadow_color=theme_dict["card_shadow"],
        )
    else:
        # Empty placeholder card with `no previous version` text.
        placeholder_w = panel_width - 60
        placeholder_h = panel_height - 60
        placeholder = Image.new("RGB", (placeholder_w, placeholder_h), theme_dict["bg_surface"])
        card_x = COMPARE_MARGIN + (panel_width - placeholder_w - 2 * OG_CARD_PADDING) // 2
        card_y = panel_top + (panel_height - placeholder_h - 2 * OG_CARD_PADDING) // 2
        _draw_rounded_card(
            canvas_rgba,
            placeholder,
            card_x,
            card_y,
            padding=OG_CARD_PADDING,
            surface_color=theme_dict["bg_surface"],
            rule_color=theme_dict["rule"],
            shadow_color=theme_dict["card_shadow"],
        )
        placeholder_draw = ImageDraw.Draw(canvas_rgba)
        placeholder_font = _get_font(22, weight=400)
        placeholder_text = "no previous version"
        text_w, text_h = _text_size(placeholder_draw, placeholder_text, placeholder_font)
        placeholder_draw.text(
            (
                card_x + (placeholder_w + 2 * OG_CARD_PADDING - text_w) // 2,
                card_y + (placeholder_h + 2 * OG_CARD_PADDING - text_h) // 2,
            ),
            placeholder_text,
            fill=theme_dict["ink_muted"],
            font=placeholder_font,
        )

    # --- After card ---
    after_img = _load_plot_image(after_path)
    after_img = _fit_image(after_img, panel_width - 2 * OG_CARD_PADDING, panel_height - 2 * OG_CARD_PADDING)
    after_card_x = after_panel_x + (panel_width - after_img.width - 2 * OG_CARD_PADDING) // 2
    after_card_y = panel_top + (panel_height - after_img.height - 2 * OG_CARD_PADDING) // 2
    _draw_rounded_card(
        canvas_rgba,
        after_img,
        after_card_x,
        after_card_y,
        padding=OG_CARD_PADDING,
        surface_color=theme_dict["bg_surface"],
        rule_color=theme_dict["rule"],
        shadow_color=theme_dict["card_shadow"],
    )

    # --- Footer chip: library.method() + tagline ---
    footer_draw = ImageDraw.Draw(canvas_rgba)
    footer_y = COMPARE_HEIGHT - COMPARE_MARGIN - 30
    if library:
        _draw_method_chip(footer_draw, COMPARE_MARGIN, footer_y, library, None, theme_dict, chip_size=22)

    tagline_font = _get_font(18, weight=400)
    tagline_w, _ = _text_size(footer_draw, TAGLINE_FULL, tagline_font)
    footer_draw.text(
        (COMPARE_WIDTH - COMPARE_MARGIN - tagline_w, footer_y + 2),
        TAGLINE_FULL,
        fill=theme_dict["ink_muted"],
        font=tagline_font,
    )

    canvas_rgba.convert("RGB").save(output_path, "PNG", optimize=True)


def _fit_image(img: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """Scale an image to fit within max_width x max_height, preserving aspect ratio."""
    scale = min(max_width / img.width, max_height / img.height, 1.0)
    if scale < 1.0:
        return img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    return img


# =============================================================================
# OG image generation — public API (any.plot() visual style)
# =============================================================================


def create_branded_header(width: int = OG_WIDTH, height: int = HEADER_HEIGHT) -> Image.Image:
    """Create a branded header strip with the any.plot() wordmark.

    Kept for backwards compatibility with anything that consumed the old
    `_draw_anyplot_logo` strip — internally redrawn in the new style.
    """
    header = Image.new("RGB", (width, height), LIGHT_THEME["bg_page"])
    draw = ImageDraw.Draw(header)

    font_size = max(int(height * 0.45), 18)
    # Approximate width of "any.plot()" so we can center it. We render at (0, 0)
    # to a throwaway draw to measure, then re-render at the centered coordinates.
    measure = Image.new("RGB", (width, height))
    measure_draw = ImageDraw.Draw(measure)
    rendered_width = _draw_anyplot_wordmark(measure_draw, 0, 0, font_size=font_size, theme=LIGHT_THEME)

    x = (width - rendered_width) // 2
    y = (height - font_size) // 2 - max(int(font_size * 0.05), 1)
    _draw_anyplot_wordmark(draw, x, y, font_size=font_size, theme=LIGHT_THEME)

    return header


def _draw_text_with_features(
    draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, *, font, fill, features: list[str] | None = None
) -> None:
    """Draw text with optional OpenType features (e.g. `ss02` for MonoLisa Italic swashes).

    Falls back to plain `draw.text(...)` when Pillow is built without libraqm
    (no feature support) or when the font doesn't supply the requested feature.
    """
    try:
        if features:
            draw.text(xy, text, font=font, fill=fill, features=features)
        else:
            draw.text(xy, text, font=font, fill=fill)
    except Exception:
        draw.text(xy, text, font=font, fill=fill)


def create_home_og_image(
    output_path: str | Path | None = None,
    *,
    theme: str = "light",
    tagline: str = TAGLINE_FULL,  # legacy kwarg, ignored — hero copy is fixed below
    hero_plot: str | Path | Image.Image | bytes | None = None,  # reserved for the future "with image" variant
) -> Image.Image | bytes:
    """Render the home/plots OG card — typographic, centered, hero-style.

    1200×630 layout:

        ┌──────────────────────────────────────────────────────────────┐
        │ ── the open plot catalogue                    ~/anyplot.ai   │
        │                                                              │
        │                                                              │
        │              any.plot()                                      │
        │              — any library.                                  │
        │                                                              │
        │              from .md to art._                               │
        │                                                              │
        └──────────────────────────────────────────────────────────────┘

    `hero_plot` is reserved — a future iteration will swap this for the
    two-column hero-with-plot variant. For now it's ignored.
    """
    del tagline, hero_plot  # held for forward-compat, not used in the simple variant

    theme_dict = DARK_THEME if theme == "dark" else LIGHT_THEME
    final = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT), theme_dict["bg_page"])
    draw = ImageDraw.Draw(final)

    _draw_eyebrow_and_domain(draw, theme_dict, eyebrow_text="the open plot catalogue")

    # --- Center hero block: any.plot() / — any library. / from .md to art. ---
    wm_size = 130
    accent_size = int(wm_size * 0.72)
    md_size = 36

    # Measure each line so we can build a left-aligned block, centered as a whole.
    measure = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT))
    measure_draw = ImageDraw.Draw(measure)
    wm_w = _draw_anyplot_wordmark(measure_draw, 0, 0, font_size=wm_size, theme=theme_dict)

    accent_font = _get_font(accent_size, weight=400, italic=True)
    accent_text = f"— {TAGLINE_SHORT}"
    accent_w, _ = _text_size(measure_draw, accent_text, accent_font)

    # Headline block — `any.plot()` and `— any library.` share the same left
    # edge (matches the H1 on the site, where both lines are inside the same
    # left-aligned heading). Block left = center of the wider of the two.
    block_w = max(wm_w, accent_w)
    block_left = (OG_WIDTH - block_w) // 2

    # Vertical: headline (2 lines) sits in the upper half; `from .md to art.`
    # gets generous breathing room below.
    line_gap_headline = 24  # extra leading between any.plot() and — any library.
    md_gap = 86  # generous separation before the mono accent
    headline_h = wm_size + line_gap_headline + accent_size
    block_top = 158  # below the eyebrow row

    # Line 1 — `any.plot()`
    _draw_anyplot_wordmark(draw, block_left, block_top, font_size=wm_size, theme=theme_dict)

    # Line 2 — italic `— any library.`, same left edge as the wordmark
    accent_y = block_top + wm_size + line_gap_headline
    _draw_text_with_features(
        draw, (block_left, accent_y), accent_text, font=accent_font, fill=theme_dict["ink"], features=["ss02"]
    )

    # Line 3 — mono accent `from .md to art.` (centered in canvas, big gap above)
    md_font = _get_font(md_size, weight=500)
    md_text = "from .md to art."
    md_w, _ = _text_size(draw, md_text, md_font)
    md_x = (OG_WIDTH - md_w) // 2
    md_y = block_top + headline_h + md_gap
    draw.text((md_x, md_y), md_text, fill=theme_dict["ink_soft"], font=md_font)

    return _finalize_og_image(final, output_path, theme=theme_dict)


def create_branded_og_image(
    plot_image: str | Path | Image.Image | bytes,
    output_path: str | Path | None = None,
    spec_id: str | None = None,
    library: str | None = None,
    *,
    theme: str = "light",
    language: str | None = None,
) -> Image.Image | bytes:
    """Render a branded OG card for a single implementation in the any.plot() style.

    Layout (1200×630):

        ┌──────────────────────────────────────────────────────────────┐
        │  any.plot()                                    ~/anyplot.ai  │
        │   ── scatter-basic                                           │
        │                                                              │
        │             ┌────────────────────────────────────┐           │
        │             │      [ plot rendered here ]        │           │
        │             └────────────────────────────────────┘           │
        │                                                              │
        │  python matplotlib                          from .md to art. │
        └──────────────────────────────────────────────────────────────┘

    Args:
        plot_image: Path to plot image, PIL Image, or bytes
        output_path: If provided, save to this path
        spec_id: Spec slug rendered in the eyebrow row above the plot card
        library: Library name shown in the bottom-left footer label
        theme: "light" (cream `#F5F3EC`) or "dark" (`#121210`) surface — values
            kept in sync with the website tokens in `app/src/styles/tokens.css`
        language: Implementation language (e.g. "python") for the footer label;
            defaults to "python" when unset
    """
    theme_dict = DARK_THEME if theme == "dark" else LIGHT_THEME
    img = _load_plot_image(plot_image)

    final = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT), theme_dict["bg_page"])
    draw = ImageDraw.Draw(final)

    # --- Top frame: any.plot() wordmark + spec_id eyebrow + domain ---
    eyebrow_bottom = _draw_eyebrow_and_domain(
        draw, theme_dict, eyebrow_text=spec_id or "specification", with_wordmark=True
    )

    # --- Plot card ---
    chip_row_height = 30
    available_top = eyebrow_bottom + 18
    available_bottom = OG_HEIGHT - OG_OUTER_PADDING - chip_row_height - OG_FOOTER_GAP
    available_height = available_bottom - available_top - 2 * OG_CARD_PADDING
    available_width = OG_WIDTH - 2 * OG_OUTER_PADDING - 2 * OG_CARD_PADDING

    scale = min(available_width / img.width, available_height / img.height)
    new_width = int(img.width * scale)
    new_height = int(img.height * scale)
    plot_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    card_x = (OG_WIDTH - new_width - 2 * OG_CARD_PADDING) // 2
    card_y = available_top + (available_height - new_height) // 2
    _draw_rounded_card(
        final,
        plot_resized,
        card_x,
        card_y,
        padding=OG_CARD_PADDING,
        radius=14,
        surface_color=theme_dict["bg_surface"],
        rule_color=theme_dict["rule"],
        shadow_color=theme_dict["card_shadow"],
    )

    # --- Footer (refresh draw context after `_draw_rounded_card` paste) ---
    # Bottom-left: `language library` (e.g. "python matplotlib"); bottom-right:
    # `from .md to art.` Same eyebrow font size as the home OG so the editorial
    # surface reads as one consistent typographic system.
    footer_draw = ImageDraw.Draw(final)
    footer_pad = 56
    footer_font = _get_font(20, weight=500)
    footer_y = OG_HEIGHT - footer_pad - 20

    if library:
        impl_label = f"{language or 'python'} {library}"
        footer_draw.text((footer_pad, footer_y), impl_label, fill=theme_dict["ink_muted"], font=footer_font)

    md_text = "from .md to art."
    md_w, _ = _text_size(footer_draw, md_text, footer_font)
    footer_draw.text((OG_WIDTH - footer_pad - md_w, footer_y), md_text, fill=theme_dict["ink_muted"], font=footer_font)

    return _finalize_og_image(final, output_path, theme=theme_dict)


def _calculate_collage_grid(grid_top: int, grid_bottom: int) -> tuple[int, int, int, int]:
    """Calculate card slot and inner dimensions for the collage grid."""
    available_width = OG_WIDTH - 2 * COLLAGE_SIDE_MARGIN - (COLLAGE_COLS - 1) * COLLAGE_CARD_GAP_X
    label_height = 22  # height reserved for the chip label under each card

    available_height = (
        grid_bottom
        - grid_top
        - (COLLAGE_ROWS - 1) * COLLAGE_CARD_GAP_Y
        - COLLAGE_ROWS * (label_height + COLLAGE_LABEL_GAP)
    )

    slot_width = available_width // COLLAGE_COLS
    slot_height = available_height // COLLAGE_ROWS

    slot_inner_width = slot_width - 2 * COLLAGE_CARD_PADDING
    slot_inner_height = slot_height - 2 * COLLAGE_CARD_PADDING

    if slot_inner_width / slot_inner_height > COLLAGE_CARD_ASPECT:
        inner_height = slot_inner_height
        inner_width = int(inner_height * COLLAGE_CARD_ASPECT)
    else:
        inner_width = slot_inner_width
        inner_height = int(inner_width / COLLAGE_CARD_ASPECT)

    return slot_width, slot_height, inner_width, inner_height


def _draw_collage_cards(
    final: Image.Image,
    loaded_images: list[Image.Image],
    labels: list[str] | None,
    grid_top: int,
    slot_width: int,
    slot_height: int,
    inner_width: int,
    inner_height: int,
    theme: dict[str, str],
) -> None:
    """Draw each card + label into the collage grid."""
    chip_font = _get_font(15, weight=500)
    label_height = 22

    for i, img in enumerate(loaded_images):
        row = i // COLLAGE_COLS
        col = i % COLLAGE_COLS

        slot_x = COLLAGE_SIDE_MARGIN + col * (slot_width + COLLAGE_CARD_GAP_X)
        slot_y = grid_top + row * (slot_height + COLLAGE_CARD_GAP_Y + label_height + COLLAGE_LABEL_GAP)

        scale = min(inner_width / img.width, inner_height / img.height)
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        actual_card_width = new_width + 2 * COLLAGE_CARD_PADDING
        actual_card_height = new_height + 2 * COLLAGE_CARD_PADDING
        card_x = slot_x + (slot_width - actual_card_width) // 2
        card_y = slot_y + (slot_height - actual_card_height) // 2

        _draw_rounded_card(
            final,
            resized,
            card_x,
            card_y,
            padding=COLLAGE_CARD_PADDING,
            radius=COLLAGE_CARD_RADIUS,
            shadow_offset=COLLAGE_SHADOW_OFFSET,
            surface_color=theme["bg_surface"],
            rule_color=theme["rule"],
            shadow_color=theme["card_shadow"],
        )

        if labels and i < len(labels):
            draw = ImageDraw.Draw(final)
            label_text = labels[i]
            # Labels arrive as either "spec · library" (collage helper) or just "library".
            # Treat the trailing token as the library so the chip color picks correctly.
            library = label_text.split("·")[-1].strip().lower()
            color = LIBRARY_COLORS.get(library, OK_GREEN)
            label_y = card_y + actual_card_height + COLLAGE_LABEL_GAP
            square = 10
            square_y = label_y + 4
            chip_x = slot_x + (slot_width - _measure_chip_width(draw, label_text, chip_font, square)) // 2
            draw.rectangle([chip_x, square_y, chip_x + square, square_y + square], fill=color)
            draw.text((chip_x + square + 6, label_y), label_text, fill=theme["ink_soft"], font=chip_font)


def _measure_chip_width(
    draw: ImageDraw.ImageDraw, label: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, square: int
) -> int:
    """Total width of `■ label` chip — used to center it under the card."""
    return square + 6 + _text_advance(draw, label, font)


def create_og_collage(
    images: list[str | Path | Image.Image | bytes],
    output_path: str | Path | None = None,
    labels: list[str] | None = None,
    *,
    spec_id: str | None = None,
    theme: str = "light",
) -> Image.Image | bytes:
    """Create a collage OG image from multiple plot images.

    Creates a 2×3 grid (2 rows, 3 columns) with the any.plot() masthead and
    chip-style labels under each card. Used by `/og/{spec_id}.png` to show one
    spec rendered across multiple libraries.

    Args:
        images: List of plot images (paths, PIL Images, or bytes), up to 6
        output_path: If provided, save to this path
        labels: Optional labels (typically "spec_id · library_id")
        spec_id: Optional spec slug for the `❯ {spec_id} — every library.` title
        theme: "light" or "dark"
    """
    if not images:
        raise ValueError("At least one image is required")

    theme_dict = DARK_THEME if theme == "dark" else LIGHT_THEME
    loaded_images = [_load_plot_image(img) for img in images[:COLLAGE_MAX_IMAGES]]

    final = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT), theme_dict["bg_page"])
    draw = ImageDraw.Draw(final)

    # --- Top frame: any.plot() wordmark + spec eyebrow + domain ---
    collage_eyebrow = f"{spec_id} — {TAGLINE_SHORT}" if spec_id else TAGLINE_SHORT
    eyebrow_bottom = _draw_eyebrow_and_domain(draw, theme_dict, eyebrow_text=collage_eyebrow, with_wordmark=True)

    # --- Grid ---
    grid_top = eyebrow_bottom + 6
    grid_bottom = OG_HEIGHT - COLLAGE_BOTTOM_MARGIN
    slot_width, slot_height, inner_width, inner_height = _calculate_collage_grid(grid_top, grid_bottom)
    _draw_collage_cards(
        final, loaded_images, labels, grid_top, slot_width, slot_height, inner_width, inner_height, theme_dict
    )

    return _finalize_og_image(final, output_path, theme=theme_dict)


if __name__ == "__main__":
    import sys

    def print_usage() -> None:
        print("Usage:")
        print("  python -m core.images thumbnail <input> <output> [width]")
        print("  python -m core.images process <input> <output> [thumb]")
        print("  python -m core.images responsive <input> <output_dir>")
        print("  python -m core.images brand <input> <output> [spec_id] [library] [theme]")
        print("  python -m core.images collage <output> <img1> [img2] [img3] [img4]")
        print("  python -m core.images compare <before> <after> <output> [spec_id] [library]")
        print("  python -m core.images home <output> [theme]")
        print("")
        print("Examples:")
        print("  python -m core.images thumbnail plot.png thumb.png 400")
        print("  python -m core.images process plot.png out.png thumb.png")
        print("  python -m core.images responsive plot.png ./output/")
        print("  python -m core.images brand plot.png og.png scatter-basic matplotlib")
        print("  python -m core.images collage og.png img1.png img2.png img3.png img4.png")
        print("  python -m core.images compare before.png after.png comparison.png area-basic matplotlib")
        print("  python -m core.images home home.png light")
        sys.exit(1)

    if len(sys.argv) < 2:
        print_usage()

    command = sys.argv[1]

    if command == "thumbnail":
        if len(sys.argv) < 4:
            print_usage()
        input_file, output_file = sys.argv[2], sys.argv[3]
        width = int(sys.argv[4]) if len(sys.argv) > 4 else 1200
        w, h = create_thumbnail(input_file, output_file, width)
        print(f"Thumbnail: {w}x{h}px")

    elif command == "process":
        if len(sys.argv) < 4:
            print_usage()
        input_file, output_file = sys.argv[2], sys.argv[3]
        thumb_file = sys.argv[4] if len(sys.argv) > 4 else None
        res = process_plot_image(input_file, output_file, thumb_file)
        print(f"Processed: {res}")

    elif command == "responsive":
        if len(sys.argv) < 4:
            print_usage()
        input_file, output_dir = sys.argv[2], sys.argv[3]
        variants = create_responsive_variants(input_file, output_dir)
        print(f"Created {len(variants)} responsive variants in {output_dir}:")
        for v in variants:
            print(f"  {Path(v['path']).name}: {v['width']}x{v['height']} ({v['format']})")

    elif command == "brand":
        if len(sys.argv) < 4:
            print_usage()
        input_file, output_file = sys.argv[2], sys.argv[3]
        spec_id = sys.argv[4] if len(sys.argv) > 4 else None
        library = sys.argv[5] if len(sys.argv) > 5 else None
        theme_arg = sys.argv[6] if len(sys.argv) > 6 else "light"
        create_branded_og_image(input_file, output_file, spec_id, library, theme=theme_arg)
        print(f"Branded OG image: {output_file} ({OG_WIDTH}x{OG_HEIGHT}px)")

    elif command == "collage":
        if len(sys.argv) < 4:
            print_usage()
        output_file = sys.argv[2]
        input_files = sys.argv[3:]
        create_og_collage(input_files, output_file)
        print(f"Collage: {output_file} ({OG_WIDTH}x{OG_HEIGHT}px, {len(input_files)} images)")

    elif command == "compare":
        if len(sys.argv) < 5:
            print_usage()
        before_file = sys.argv[2]
        after_file = sys.argv[3]
        output_file = sys.argv[4]
        spec_id = sys.argv[5] if len(sys.argv) > 5 else ""
        library = sys.argv[6] if len(sys.argv) > 6 else ""
        before = None if before_file == "none" else before_file
        create_comparison_image(before, after_file, output_file, spec_id, library)
        print(f"Comparison: {output_file} ({COMPARE_WIDTH}x{COMPARE_HEIGHT}px)")

    elif command == "home":
        if len(sys.argv) < 3:
            print_usage()
        output_file = sys.argv[2]
        theme_arg = sys.argv[3] if len(sys.argv) > 3 else "light"
        create_home_og_image(output_file, theme=theme_arg)
        print(f"Home OG image: {output_file} ({OG_WIDTH}x{OG_HEIGHT}px, {theme_arg})")

    else:
        print(f"Unknown command: {command}")
        print_usage()
