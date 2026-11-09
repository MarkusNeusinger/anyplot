"""anyplot.ai
contour-density: Density Contour Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import pygal
from contourpy import contour_generator
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# imprint_seq, the sequential Imprint colormap: brand green (low density) to blue (high density)
SEQ_LOW, SEQ_HIGH = "#009E73", "#4467A3"

# Constants: contour levels as shares of the peak density, outermost first
LEVELS = [0.08, 0.18, 0.3, 0.45, 0.62, 0.8]

# Columns: set these to your table's column names
AREA = "Living area (sq ft)"  # role: x
PRICE = "Sale price (USD)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("home_sales.csv")
# Three segments of a housing market: starter, mid-range and premium homes
np.random.seed(42)
df = pd.DataFrame(
    {
        AREA: np.concatenate(
            [np.random.normal(1200, 150, 140), np.random.normal(2000, 200, 160), np.random.normal(3200, 250, 100)]
        ),
        PRICE: np.concatenate(
            [
                np.random.normal(250000, 40000, 140),
                np.random.normal(450000, 60000, 160),
                np.random.normal(750000, 100000, 100),
            ]
        ),
    }
)

# Plot: Gaussian KDE on a grid padded past the data, so every contour closes inside the plot
sample = df[[AREA, PRICE]].dropna().astype(float)
x_lo, x_hi = sample[AREA].min(), sample[AREA].max()
y_lo, y_hi = sample[PRICE].min(), sample[PRICE].max()
x_pad, y_pad = 0.12 * (x_hi - x_lo), 0.12 * (y_hi - y_lo)
gx = np.linspace(x_lo - x_pad, x_hi + x_pad, 160)
gy = np.linspace(y_lo - y_pad, y_hi + y_pad, 160)
# per-axis standardised scales with a narrow kernel keep the segments apart instead of one diagonal blob
scale = sample.std().to_numpy()
kde = gaussian_kde((sample.to_numpy() / scale).T, bw_method=0.32)
grid_x, grid_y = np.meshgrid(gx / scale[0], gy / scale[1])
# density[row, col] is the estimate at (gx[col], gy[row])
density = kde(np.vstack([grid_x.ravel(), grid_y.ravel()])).reshape(grid_x.shape)
peak = density.max()

# Iso-density rings per level from contourpy, matplotlib's non-plotting contour engine (closed rings repeat their start)
contours = contour_generator(x=gx, y=gy, z=density)
rings_by_level = [[list(map(tuple, ring.tolist())) for ring in contours.lines(share * peak)] for share in LEVELS]

# One series per level: its rings filled at low opacity, so the bands deepen towards each peak
corner = (gx[0], gy[0])  # a fill path starts and ends on pygal's zero line; anchored here those stubs have no length
level_colors = []
for t in np.linspace(0, 1, len(LEVELS)):
    rgb = [round(int(SEQ_LOW[k : k + 2], 16) * (1 - t) + int(SEQ_HIGH[k : k + 2], 16) * t) for k in (1, 3, 5)]
    level_colors.append(f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK_SOFT, *level_colors),
    guide_stroke_color=RULE,
    major_guide_stroke_color=RULE,
    guide_stroke_dasharray="none",
    major_guide_stroke_dasharray="none",
    title_font_size=66,
    label_font_size=46,
    major_label_font_size=46,
    legend_font_size=44,
    value_font_size=36,
    opacity=0.17,
    opacity_hover=0.3,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=4,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="contour-density · python · pygal · anyplot.ai",
    x_title=AREA,
    y_title=PRICE,
    xrange=(gx[0], gx[-1]),
    range=(gy[0], gy[-1]),
    zero=gy[0],
    show_x_guides=True,
    show_y_guides=True,
    show_dots=False,
    allow_interruptions=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=40,
    truncate_legend=-1,
    spacing=24,
    margin=40,
    x_value_formatter=lambda area: f"{area:,.0f}",
    value_formatter=lambda price: f"${price / 1e6:.1f}M" if abs(price) >= 1e6 else f"${price / 1000:,.0f}k",
    css=["file://style.css", "file://graph.css", "inline:.serie-0 .dot { fill-opacity: 0.35 !important; }"],
)

# Scatter overlay: every observation as a small faint point at its exact value
chart.add(None, list(zip(sample[AREA], sample[PRICE], strict=True)), stroke=False, show_dots=True, dots_size=5)
for i, (share, rings) in enumerate(zip(LEVELS, rings_by_level, strict=True)):
    values = [corner, (None, None)]
    for ring in rings:
        values += [*ring, (None, None)]
    values.append(corner)
    side = " (outer)" if i == 0 else " (inner)" if i == len(LEVELS) - 1 else ""
    chart.add(f"{share:.0%} of peak density{side}", values, fill=True)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
