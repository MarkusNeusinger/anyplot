#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "colorspacious>=1.1.2",
#   "numpy>=2.0",
#   "matplotlib>=3.10",
#   "pillow>=11.0",
# ]
# ///
"""Palette baseline diagnostic for anyplot.

Generates a single self-contained HTML page that visualises the current anyplot
palette across three domains, each evaluated for normal vision and three
100%-severity CVD simulations (deuteranopia, protanopia, tritanopia):

  A. Categorical plot palette (Okabe-Ito 7 + 2 adaptive neutrals)
  B. Continuous plot colormaps (viridis, cividis, BrBG)
  C. Website surface & chrome tokens — including homepage hero mockup

Run::

    uv run --script scripts/palette-analysis.py
    uv run --script scripts/palette-analysis.py --out /tmp/palette.html

Default output: ``docs/reference/palette-analysis.html``. Shared rendering
helpers live in ``scripts/_palette_common.py`` so they can be reused by
``scripts/palette-variants.py``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from core.images import OK_GREEN, OKABE_PALETTE  # noqa: E402
from _palette_common import (  # noqa: E402
    DARK_THEME_FULL,
    LIGHT_THEME_FULL,
    NEUTRAL_DARK,
    NEUTRAL_LIGHT,
    PAGE_CSS,
    PAGE_JS,
    hex_to_rgb1,
    render_colormap_row,
    render_first_n_summary,
    render_hero_mockup_pair,
    render_legend,
    render_matrix_block,
    render_sample_charts,
    render_surface_section,
    render_swatch_table,
)


DEFAULT_OUTPUT = REPO_ROOT / "docs" / "reference" / "palette-analysis.html"

OKABE_NAMES = ["green", "vermillion", "blue", "purple", "orange", "sky", "yellow"]
CATEGORICAL_HEX = [*OKABE_PALETTE, NEUTRAL_LIGHT, NEUTRAL_DARK]
CATEGORICAL_LABELS = [*OKABE_NAMES, "neutral·light", "neutral·dark"]
COLORMAPS = ["viridis", "cividis", "BrBG"]


def render_page() -> str:
    cat_rgb = np.array([hex_to_rgb1(hx) for hx in CATEGORICAL_HEX])
    cat_swatches = render_swatch_table(CATEGORICAL_HEX, CATEGORICAL_LABELS)
    cat_matrix = render_matrix_block(cat_rgb, CATEGORICAL_LABELS)
    sample_charts = render_sample_charts(OKABE_PALETTE, n_series=4)
    first_n = render_first_n_summary(OKABE_PALETTE, OKABE_NAMES)

    cmap_rows = "\n".join(render_colormap_row(name) for name in COLORMAPS)

    hero_pair = render_hero_mockup_pair(OK_GREEN)
    surface_light = render_surface_section(LIGHT_THEME_FULL, "light theme")
    surface_dark = render_surface_section(DARK_THEME_FULL, "dark theme")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>anyplot palette — baseline diagnostic</title>
<style>{PAGE_CSS}</style>
</head>
<body>
<header class="masthead">
    <h1>any<span class="dot">.</span>plot() — palette baseline</h1>
    <div class="meta">CAM02-UCS · colorspacious · severity 100%</div>
    <button class="theme-toggle">◐ dark</button>
</header>

<section class="domain">
    <h2>A. categorical plot palette</h2>
    <p class="lede">okabe-ito (positions 1–7) plus the two adaptive neutrals.
    sample charts render the first-4 case on the production bg-page surfaces.
    matrices side-by-side: <em>normal vision</em> left, <em>worst of the 3 cvd
    conditions</em> right. the "first-n" table below answers the practical question —
    at what palette size does the weakest pair drop below comfortable distinguishability?</p>
    {sample_charts}
    {first_n}
    {cat_swatches}
    {cat_matrix}
    {render_legend()}
</section>

<section class="domain">
    <h2>B. continuous plot colormaps</h2>
    <p class="lede">256-step samples of the three sequential / diverging colormaps named in
    style-guide §9.2. badge reports the worst-case adjacent-sample ΔE across normal + 3 cvd —
    a value above ~2.5 indicates visible banding under at least one condition.</p>
    {cmap_rows}
</section>

<section class="domain">
    <h2>C. website chrome — homepage hero &amp; surface tokens</h2>
    <p class="lede">tiny renditions of the anyplot.ai hero (style-guide §5.3) for both themes,
    with every visible text/UI element tagged with its live wcag contrast ratio. badges turn
    red the moment a colour change drops a pair below aa — that is the lighthouse-green
    check at a glance. surface tokens, ΔE matrices and wcag tables drill down below.</p>
    {hero_pair}
    {surface_light}
    {surface_dark}
    {render_legend()}
</section>

<footer class="notes">
    <p>method: ΔE is euclidean distance in CAM02-UCS (Luo et al. 2006), computed via
    <code>colorspacious.cspace_convert(rgb, "sRGB1", "CAM02-UCS")</code>.
    cvd simulation uses the machado et al. (2009) model exposed by
    <code>colorspacious</code>'s <code>sRGB1+CVD</code> space at <code>severity=100</code>
    for deuteranomaly, protanomaly, and tritanomaly.</p>
    <p>palette source: <code>core/images.py</code> · spec: <code>docs/reference/style-guide.md §4, §9</code>.
    references: okabe &amp; ito (2008), wong (2011), machado et al. (2009), petroff (2021).</p>
</footer>

<script>{PAGE_JS}</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help=f"Output HTML path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )
    log = logging.getLogger("palette-analysis")

    log.info("computing palette diagnostic …")
    html = render_page()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    size_kb = args.out.stat().st_size / 1024
    log.info("wrote %s (%.1f kB)", args.out, size_kb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
