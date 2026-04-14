"""Image processing utilities for anyplot.

This module provides reusable functions for image manipulation:
- Thumbnail generation with aspect ratio preservation
- PNG optimization with pngquant
- Branded og:image generation for social media
- Collage generation for spec overview pages
- Before/after comparison images for update reviews

Usage as CLI:
    python -m core.images thumbnail input.png output.png 400
    python -m core.images process input.png output.png thumb.png
    python -m core.images brand input.png output.png "scatter-basic" "matplotlib"
    python -m core.images collage output.png img1.png img2.png img3.png img4.png
    python -m core.images compare before.png after.png output.png [spec_id] [library]
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
FONT_CACHE_DIR = Path("/tmp/anyplot-fonts")

# Brand colors from website
ANYPLOT_BLUE = "#3776AB"  # Brand blue
ANYPLOT_YELLOW = "#FFD43B"  # Brand yellow
ANYPLOT_DARK = "#1f2937"  # Dark gray
ANYPLOT_BG = "#f8f9fa"  # Light background

# OG image dimensions (recommended for social media)
OG_WIDTH = 1200
OG_HEIGHT = 630
HEADER_HEIGHT = 80

# Brand text
TAGLINE = "library-agnostic, ai-powered plotting."

# Shared colors
COLOR_LABEL_GRAY = "#6b7280"
COLOR_PLACEHOLDER_GRAY = "#9ca3af"

# --- OG Single Image Layout ---
OG_TOP_MARGIN = 25
OG_LOGO_FONT_SIZE = 42
OG_LOGO_HEIGHT = 55
OG_TAGLINE_FONT_SIZE = 22
OG_TAGLINE_GAP = 18
OG_HEADER_GAP = 25
OG_SIDE_MARGIN = 60
OG_CARD_PADDING = 12
OG_LABEL_FONT_SIZE = 20
OG_LABEL_GAP = 15
OG_BOTTOM_MARGIN = 45

# --- OG Collage Layout ---
COLLAGE_TOP_MARGIN = 20
COLLAGE_SIDE_MARGIN = 40
COLLAGE_LOGO_FONT_SIZE = 38
COLLAGE_TAGLINE_FONT_SIZE = 18
COLLAGE_TAGLINE_Y_OFFSET = 58
COLLAGE_CARD_GAP_X = 20
COLLAGE_CARD_GAP_Y = 8
COLLAGE_CARD_PADDING = 6
COLLAGE_LABEL_FONT_SIZE = 13
COLLAGE_LABEL_HEIGHT = 18
COLLAGE_LABEL_GAP = 4
COLLAGE_BOTTOM_MARGIN = 15
COLLAGE_COLS = 3
COLLAGE_ROWS = 2
COLLAGE_MAX_IMAGES = 6
COLLAGE_CARD_ASPECT = 16 / 9
COLLAGE_CARD_RADIUS = 10
COLLAGE_SHADOW_OFFSET = 2

# --- Comparison Layout ---  (supplement existing COMPARE_* constants)
COMPARE_HEADER_FONT_SIZE = 28
COMPARE_LABEL_FONT_SIZE = 22
COMPARE_PLACEHOLDER_FONT_SIZE = 20
COMPARE_LABEL_Y_OFFSET = 8


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    """Return (width, height) of rendered text via textbbox."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# Optional: pngquant for better compression
try:
    import subprocess

    _HAS_PNGQUANT = subprocess.run(["pngquant", "--version"], capture_output=True).returncode == 0
except (FileNotFoundError, subprocess.SubprocessError):  # fmt: skip
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
    source image.  File naming follows the convention expected by the frontend:
        plot_1200.png, plot_1200.webp, plot_800.png, plot_800.webp,
        plot_400.png, plot_400.webp, plot.webp

    Args:
        input_path: Path to the source plot image (plot.png).
        output_dir: Directory where variants will be written.
        sizes: Override default RESPONSIVE_SIZES if needed.
        optimize: Whether to optimize PNGs with pngquant.

    Returns:
        List of dicts, each with 'path', 'width', 'height', 'format'.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as src:
        if src.mode in ("RGBA", "P"):
            img = src.convert("RGB")
        else:
            img = src.copy()

    results: list[dict[str, str | int]] = []
    target_sizes = sizes or RESPONSIVE_SIZES

    # Sized variants (e.g. plot_1200.png, plot_1200.webp, plot_800.png, ...)
    for width in target_sizes:
        # Skip sizes larger than the original
        if width >= img.width:
            continue
        else:
            ratio = width / img.width
            actual_width = width
            actual_height = int(img.height * ratio)
            resized = img.resize((actual_width, actual_height), Image.Resampling.LANCZOS)

        for ext, fmt, opts in RESPONSIVE_FORMATS:
            out_path = output_dir / f"plot_{width}.{ext}"
            resized.save(out_path, fmt, optimize=True, **opts)

            # Optimize PNG with pngquant
            if optimize and fmt == "PNG":
                optimize_png(out_path)

            results.append({"path": str(out_path), "width": actual_width, "height": actual_height, "format": ext})
            logger.info("Created %s (%dx%d)", out_path.name, actual_width, actual_height)

    # Full-size WebP
    webp_path = output_dir / "plot.webp"
    img.save(webp_path, "WEBP", quality=WEBP_FULL_QUALITY)
    results.append({"path": str(webp_path), "width": img.width, "height": img.height, "format": "webp"})
    logger.info("Created plot.webp (%dx%d)", img.width, img.height)

    return results


# =============================================================================
# Before/After Comparison Images
# =============================================================================

# Comparison image dimensions
COMPARE_WIDTH = 2400
COMPARE_HEIGHT = 800
COMPARE_MARGIN = 30
COMPARE_GAP = 30
COMPARE_HEADER_HEIGHT = 50
COMPARE_LABEL_HEIGHT = 40


def create_comparison_image(
    before_path: str | Path | None,
    after_path: str | Path,
    output_path: str | Path,
    spec_id: str = "",
    library: str = "",
) -> None:
    """Create a side-by-side before/after comparison image.

    Layout: [margin] [BEFORE image] [gap] [AFTER image] [margin]
    with a header bar and labels above each image.

    Args:
        before_path: Path to the "before" image, or None for new implementations.
        after_path: Path to the "after" image.
        output_path: Path where the comparison image will be saved.
        spec_id: Spec ID for the header label.
        library: Library name for the header label.
    """
    canvas = Image.new("RGB", (COMPARE_WIDTH, COMPARE_HEIGHT), ANYPLOT_BG)
    draw = ImageDraw.Draw(canvas)

    panel_width = (COMPARE_WIDTH - 2 * COMPARE_MARGIN - COMPARE_GAP) // 2
    panel_top = COMPARE_HEADER_HEIGHT + COMPARE_LABEL_HEIGHT
    panel_height = COMPARE_HEIGHT - panel_top - COMPARE_MARGIN

    # Header bar
    header_text = f"{library} · {spec_id}" if library and spec_id else library or spec_id
    if header_text:
        header_font = _get_font(COMPARE_HEADER_FONT_SIZE, weight=700, local_only=True)
        text_w, text_h = _text_size(draw, header_text, header_font)
        draw.text(
            ((COMPARE_WIDTH - text_w) // 2, (COMPARE_HEADER_HEIGHT - text_h) // 2),
            header_text,
            fill=ANYPLOT_DARK,
            font=header_font,
        )

    # Labels
    label_font = _get_font(COMPARE_LABEL_FONT_SIZE, weight=400, local_only=True)
    before_label = "BEFORE (current)"
    after_label = "AFTER (updated)"

    before_label_w, _ = _text_size(draw, before_label, label_font)
    draw.text(
        (COMPARE_MARGIN + (panel_width - before_label_w) // 2, COMPARE_HEADER_HEIGHT + COMPARE_LABEL_Y_OFFSET),
        before_label,
        fill=COLOR_LABEL_GRAY,
        font=label_font,
    )

    after_label_w, _ = _text_size(draw, after_label, label_font)
    after_panel_x = COMPARE_MARGIN + panel_width + COMPARE_GAP
    draw.text(
        (after_panel_x + (panel_width - after_label_w) // 2, COMPARE_HEADER_HEIGHT + COMPARE_LABEL_Y_OFFSET),
        after_label,
        fill=COLOR_LABEL_GRAY,
        font=label_font,
    )

    # Load and place BEFORE image (or placeholder)
    if before_path and Path(before_path).exists():
        before_img = Image.open(before_path)
        if before_img.mode in ("RGBA", "P"):
            before_img = before_img.convert("RGB")
        before_img = _fit_image(before_img, panel_width, panel_height)
        before_x = COMPARE_MARGIN + (panel_width - before_img.width) // 2
        before_y = panel_top + (panel_height - before_img.height) // 2
        canvas.paste(before_img, (before_x, before_y))
    else:
        placeholder_font = _get_font(COMPARE_PLACEHOLDER_FONT_SIZE, weight=400, local_only=True)
        placeholder_text = "No previous version"
        placeholder_w, placeholder_h = _text_size(draw, placeholder_text, placeholder_font)
        placeholder_x = COMPARE_MARGIN + (panel_width - placeholder_w) // 2
        placeholder_y = panel_top + (panel_height - placeholder_h) // 2
        draw.text((placeholder_x, placeholder_y), placeholder_text, fill=COLOR_PLACEHOLDER_GRAY, font=placeholder_font)

    # Load and place AFTER image
    after_img = Image.open(after_path)
    if after_img.mode in ("RGBA", "P"):
        after_img = after_img.convert("RGB")
    after_img = _fit_image(after_img, panel_width, panel_height)
    after_x = after_panel_x + (panel_width - after_img.width) // 2
    after_y = panel_top + (panel_height - after_img.height) // 2
    canvas.paste(after_img, (after_x, after_y))

    canvas.save(output_path, "PNG", optimize=True)


def _fit_image(img: Image.Image, max_width: int, max_height: int) -> Image.Image:
    """Scale an image to fit within max_width x max_height, preserving aspect ratio."""
    scale = min(max_width / img.width, max_height / img.height, 1.0)
    if scale < 1.0:
        return img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    return img


# =============================================================================
# OG Image Branding Functions
# =============================================================================


def _get_monolisa_font_path(local_only: bool = False) -> Path | None:
    """Get path to MonoLisa font, downloading from GCS if needed.

    Args:
        local_only: If True, only return the font if already cached locally.

    Returns:
        Path to font file, or None if unavailable.
    """
    cached_font = FONT_CACHE_DIR / "MonoLisaVariableNormal.ttf"

    # Return cached font if exists
    if cached_font.exists():
        return cached_font

    if local_only:
        return None

    # Try to download from GCS
    try:
        from google.cloud import storage

        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        client = storage.Client()
        bucket = client.bucket(GCS_STATIC_BUCKET)
        blob = bucket.blob(MONOLISA_FONT_PATH)
        blob.download_to_filename(str(cached_font))
        logger.info(f"Downloaded MonoLisa font to {cached_font}")
        return cached_font
    except Exception as e:
        logger.warning(f"Could not load MonoLisa font from GCS: {e}")
        return None


def _get_font(
    size: int = 32, weight: int = 700, local_only: bool = False
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a suitable font for text rendering.

    Tries to load MonoLisa from GCS cache, falls back to system fonts.

    Args:
        size: Font size in pixels
        weight: Font weight (100-900, default 700 for bold like website)
        local_only: If True, skip GCS download and only use locally cached or system fonts.
    """
    # Try MonoLisa (from local cache, or download from GCS if allowed)
    monolisa_path = _get_monolisa_font_path(local_only=local_only)
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


def _draw_anyplot_logo(draw: ImageDraw.ImageDraw, x: int, y: int, font_size: int = 36) -> int:
    """Draw the anyplot.ai logo with proper colors.

    Args:
        draw: ImageDraw instance to draw on
        x: X coordinate for text start
        y: Y coordinate for text baseline
        font_size: Font size in pixels

    Returns:
        Total width of drawn text
    """
    font = _get_font(font_size)

    # Draw each part with its color
    parts = [("any", ANYPLOT_BLUE), ("plot", ANYPLOT_YELLOW), (".ai", ANYPLOT_DARK)]

    current_x = x
    for text, color in parts:
        draw.text((current_x, y), text, fill=color, font=font)
        bbox = draw.textbbox((current_x, y), text, font=font)
        current_x = bbox[2]  # Move to end of this text

    return current_x - x


def _draw_branded_header(
    draw: ImageDraw.ImageDraw,
    canvas_width: int,
    top_y: int,
    logo_font_size: int,
    tagline_font_size: int,
    tagline_y: int,
) -> None:
    """Draw centered anyplot.ai logo + tagline onto an existing canvas.

    Args:
        draw: ImageDraw instance to draw on
        canvas_width: Width of the canvas (for centering)
        top_y: Y coordinate for the logo
        logo_font_size: Font size for the logo
        tagline_font_size: Font size for the tagline
        tagline_y: Y coordinate for the tagline
    """
    logo_font = _get_font(logo_font_size)
    logo_text = "anyplot.ai"
    logo_width, _ = _text_size(draw, logo_text, logo_font)
    logo_x = (canvas_width - logo_width) // 2
    _draw_anyplot_logo(draw, logo_x, top_y, logo_font_size)

    tagline_font = _get_font(tagline_font_size, weight=400)
    tagline_width, _ = _text_size(draw, TAGLINE, tagline_font)
    tagline_x = (canvas_width - tagline_width) // 2
    draw.text((tagline_x, tagline_y), TAGLINE, fill=COLOR_LABEL_GRAY, font=tagline_font)


def create_branded_header(width: int = OG_WIDTH, height: int = HEADER_HEIGHT) -> Image.Image:
    """Create a branded header strip with anyplot.ai logo.

    Args:
        width: Width of the header in pixels
        height: Height of the header in pixels

    Returns:
        PIL Image with the branded header
    """
    header = Image.new("RGB", (width, height), ANYPLOT_BG)
    draw = ImageDraw.Draw(header)

    # Center the logo
    font_size = height // 2
    font = _get_font(font_size)

    # Calculate total text width for centering
    test_text = "anyplot.ai"
    text_width, text_height = _text_size(draw, test_text, font)

    x = (width - text_width) // 2
    y = (height - text_height) // 2 - 5  # Slight adjustment for visual centering

    _draw_anyplot_logo(draw, x, y, font_size)

    return header


def _draw_rounded_card(
    base: Image.Image,
    content: Image.Image,
    x: int,
    y: int,
    padding: int = 12,
    radius: int = 16,
    shadow_offset: int = 4,
    shadow_blur: int = 8,
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
        shadow_blur: Shadow blur amount (not used, simplified shadow)
    """
    card_width = content.width + 2 * padding
    card_height = content.height + 2 * padding

    # Create shadow (simple gray rectangle offset)
    shadow_color = "#d1d5db"  # Light gray shadow
    shadow = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([0, 0, card_width - 1, card_height - 1], radius=radius, fill=shadow_color)
    base.paste(shadow, (x + shadow_offset, y + shadow_offset), shadow)

    # Create card background (white)
    card = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    card_draw.rounded_rectangle([0, 0, card_width - 1, card_height - 1], radius=radius, fill="#ffffff")
    base.paste(card, (x, y), card)

    # Paste content
    base.paste(content, (x + padding, y + padding))


def _load_plot_image(source: str | Path | Image.Image | bytes) -> Image.Image:
    """Load a plot image from various sources, converting to RGB.

    Args:
        source: Path to plot image, PIL Image, or bytes

    Returns:
        PIL Image in RGB mode
    """
    if isinstance(source, bytes):
        img = Image.open(BytesIO(source))
    elif isinstance(source, Image.Image):
        img = source
    else:
        img = Image.open(source)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    return img


def _finalize_og_image(final: Image.Image, output_path: str | Path | None) -> Image.Image | bytes:
    """Composite RGBA→RGB and either save or return bytes.

    Args:
        final: RGBA image to finalize
        output_path: If provided, save to this path and return the RGB image.
            If None, return PNG bytes.

    Returns:
        PIL Image if output_path is given, otherwise bytes of PNG
    """
    final_rgb = Image.new("RGB", final.size, ANYPLOT_BG)
    final_rgb.paste(final, mask=final.split()[3] if final.mode == "RGBA" else None)

    if output_path:
        final_rgb.save(output_path, "PNG", optimize=True)
        return final_rgb

    buffer = BytesIO()
    final_rgb.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def create_branded_og_image(
    plot_image: str | Path | Image.Image | bytes,
    output_path: str | Path | None = None,
    spec_id: str | None = None,
    library: str | None = None,
) -> Image.Image | bytes:
    """Create a branded OG image by adding anyplot.ai header to a plot.

    Design matches og-image.png style:
    - anyplot.ai logo at top
    - Tagline "Beautiful Python plotting made easy."
    - Plot in rounded paper card with shadow
    - spec_id · library label below

    Args:
        plot_image: Path to plot image, PIL Image, or bytes
        output_path: If provided, save to this path
        spec_id: Optional spec ID for subtitle
        library: Optional library name for subtitle

    Returns:
        PIL Image if output_path is None, otherwise bytes of PNG
    """
    img = _load_plot_image(plot_image)

    # Available space for the card
    tagline_height = 35
    label_height = 30
    header_total = OG_TOP_MARGIN + OG_LOGO_HEIGHT + tagline_height + OG_HEADER_GAP
    footer_total = label_height + OG_BOTTOM_MARGIN
    available_height = OG_HEIGHT - header_total - footer_total - 2 * OG_CARD_PADDING
    available_width = OG_WIDTH - 2 * OG_SIDE_MARGIN

    # Scale plot to fit
    scale = min(available_width / img.width, available_height / img.height)
    new_width = int(img.width * scale)
    new_height = int(img.height * scale)
    plot_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create canvas and draw header
    final = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT), ANYPLOT_BG)
    draw = ImageDraw.Draw(final)
    tagline_y = OG_TOP_MARGIN + OG_LOGO_HEIGHT + OG_TAGLINE_GAP
    _draw_branded_header(draw, OG_WIDTH, OG_TOP_MARGIN, OG_LOGO_FONT_SIZE, OG_TAGLINE_FONT_SIZE, tagline_y)

    # Draw card with plot
    card_x = (OG_WIDTH - new_width - 2 * OG_CARD_PADDING) // 2
    card_y = header_total
    _draw_rounded_card(final, plot_resized, card_x, card_y, padding=OG_CARD_PADDING)

    # Draw label below card
    if spec_id or library:
        label_parts = [p for p in (spec_id, library) if p]
        label = " · ".join(label_parts)
        label_font = _get_font(OG_LABEL_FONT_SIZE, weight=400)
        draw = ImageDraw.Draw(final)  # Refresh draw after card paste
        label_width, _ = _text_size(draw, label, label_font)
        label_x = (OG_WIDTH - label_width) // 2
        label_y = card_y + new_height + 2 * OG_CARD_PADDING + OG_LABEL_GAP
        draw.text((label_x, label_y), label, fill=ANYPLOT_DARK, font=label_font)

    return _finalize_og_image(final, output_path)


def _calculate_collage_grid(grid_top: int, grid_bottom: int) -> tuple[int, int, int, int]:
    """Calculate card slot and inner dimensions for the collage grid.

    Returns:
        (slot_width, slot_height, inner_width, inner_height)
    """
    available_width = OG_WIDTH - 2 * COLLAGE_SIDE_MARGIN - (COLLAGE_COLS - 1) * COLLAGE_CARD_GAP_X
    available_height = (
        grid_bottom
        - grid_top
        - (COLLAGE_ROWS - 1) * COLLAGE_CARD_GAP_Y
        - COLLAGE_ROWS * (COLLAGE_LABEL_HEIGHT + COLLAGE_LABEL_GAP)
    )

    slot_width = available_width // COLLAGE_COLS
    slot_height = available_height // COLLAGE_ROWS

    # Max inner size that fits in slot while being 16:9
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
) -> None:
    """Draw each card + label into the collage grid."""
    label_font = _get_font(COLLAGE_LABEL_FONT_SIZE, weight=400)

    for i, img in enumerate(loaded_images):
        row = i // COLLAGE_COLS
        col = i % COLLAGE_COLS

        slot_x = COLLAGE_SIDE_MARGIN + col * (slot_width + COLLAGE_CARD_GAP_X)
        slot_y = grid_top + row * (slot_height + COLLAGE_CARD_GAP_Y + COLLAGE_LABEL_HEIGHT + COLLAGE_LABEL_GAP)

        # Scale image to fit in 16:9 inner area
        scale = min(inner_width / img.width, inner_height / img.height)
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center card in slot
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
        )

        if labels and i < len(labels):
            draw = ImageDraw.Draw(final)
            lbl_width, _ = _text_size(draw, labels[i], label_font)
            label_x = slot_x + (slot_width - lbl_width) // 2
            label_y = card_y + actual_card_height + COLLAGE_LABEL_GAP
            draw.text((label_x, label_y), labels[i], fill=ANYPLOT_DARK, font=label_font)


def create_og_collage(
    images: list[str | Path | Image.Image | bytes],
    output_path: str | Path | None = None,
    labels: list[str] | None = None,
) -> Image.Image | bytes:
    """Create a collage OG image from multiple plot images.

    Creates a 2x3 grid (2 rows, 3 columns) with anyplot.ai branding:
    - Large dominant logo and tagline at top
    - 6 plots in 16:9 rounded cards arranged in 2 rows
    - Labels below each card

    Args:
        images: List of plot images (paths, PIL Images, or bytes), up to 6
        output_path: If provided, save to this path
        labels: Optional list of labels for each image (e.g., library names)

    Returns:
        PIL Image if output_path is None, otherwise bytes of PNG
    """
    if not images:
        raise ValueError("At least one image is required")

    loaded_images = [_load_plot_image(img) for img in images[:COLLAGE_MAX_IMAGES]]

    # Create canvas and draw header
    final = Image.new("RGBA", (OG_WIDTH, OG_HEIGHT), ANYPLOT_BG)
    draw = ImageDraw.Draw(final)
    tagline_y = COLLAGE_TOP_MARGIN + COLLAGE_TAGLINE_Y_OFFSET
    _draw_branded_header(
        draw, OG_WIDTH, COLLAGE_TOP_MARGIN, COLLAGE_LOGO_FONT_SIZE, COLLAGE_TAGLINE_FONT_SIZE, tagline_y
    )

    # Calculate grid layout and draw cards
    grid_top = tagline_y + 35
    grid_bottom = OG_HEIGHT - COLLAGE_BOTTOM_MARGIN
    slot_width, slot_height, inner_width, inner_height = _calculate_collage_grid(grid_top, grid_bottom)
    _draw_collage_cards(final, loaded_images, labels, grid_top, slot_width, slot_height, inner_width, inner_height)

    return _finalize_og_image(final, output_path)


if __name__ == "__main__":
    import sys

    def print_usage() -> None:
        print("Usage:")
        print("  python -m core.images thumbnail <input> <output> [width]")
        print("  python -m core.images process <input> <output> [thumb]")
        print("  python -m core.images responsive <input> <output_dir>")
        print("  python -m core.images brand <input> <output> [spec_id] [library]")
        print("  python -m core.images collage <output> <img1> [img2] [img3] [img4]")
        print("  python -m core.images compare <before> <after> <output> [spec_id] [library]")
        print("")
        print("Examples:")
        print("  python -m core.images thumbnail plot.png thumb.png 400")
        print("  python -m core.images process plot.png out.png thumb.png")
        print("  python -m core.images responsive plot.png ./output/")
        print("  python -m core.images brand plot.png og.png scatter-basic matplotlib")
        print("  python -m core.images collage og.png img1.png img2.png img3.png img4.png")
        print("  python -m core.images compare before.png after.png comparison.png area-basic matplotlib")
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
        create_branded_og_image(input_file, output_file, spec_id, library)
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

    else:
        print(f"Unknown command: {command}")
        print_usage()
