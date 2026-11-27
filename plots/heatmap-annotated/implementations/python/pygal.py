"""anyplot.ai
heatmap-annotated: Annotated Heatmap
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import math
import os
from itertools import pairwise

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


CANVAS = 2400  # square canvas in pixels

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Imprint diverging ramp for fields (colored cells): red, the page color at the midpoint, blue
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]
DARK_TEXT = "#1A1A17"  # annotation on pale cells
LIGHT_TEXT = "#FAF8F1"  # annotation on dark cells

# Columns: set these to your table's labels
X_LABEL = "Variable"  # role: x
Y_LABEL = "Variable"  # role: y
VALUE = "Correlation"  # role: value

# Data: replace this block with your own square table, for example df = pd.read_csv("matrix.csv", index_col=0)
# Correlation matrix of business metrics (symmetric, diagonal = 1.0); R&D spend competes with
# marketing budget and briefly disrupts satisfaction, hence the mild negative values.
variables = ["Revenue", "Marketing", "R&D Spend", "Customers", "Satisfaction", "Retention"]
df = pd.DataFrame(
    [
        [1.00, 0.85, 0.42, 0.78, 0.65, 0.72],
        [0.85, 1.00, -0.18, 0.68, 0.55, 0.62],
        [0.42, -0.18, 1.00, 0.28, -0.12, 0.38],
        [0.78, 0.68, 0.28, 1.00, 0.82, 0.88],
        [0.65, 0.55, -0.12, 0.82, 1.00, 0.75],
        [0.72, 0.62, 0.38, 0.88, 0.75, 1.00],
    ],
    index=variables,
    columns=variables,
)
df.columns.name = X_LABEL
df.index.name = Y_LABEL


# Plot: reads only df and the constants above
def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"  # a missing value draws nothing, never the low end
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def svg_text(x, y, text, size, fill, weight="normal", anchor="start", rotate=0):
    """One SVG text element as a string."""
    transform = f' transform="rotate({rotate}, {x:.1f}, {y:.1f})"' if rotate else ""
    style = f"font-size:{size}px;font-weight:{weight};font-family:sans-serif"
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" text-anchor="{anchor}"{transform} style="{style}">'
        f"{text.replace('&', '&amp;')}</text>"
    )


def svg_rect(x, y, width, height, fill, stroke="none", rx=0):
    """One SVG rect element as a string."""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    )


# Style
title = "heatmap-annotated · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=72,
    legend_font_size=48,
    label_font_size=44,
    major_label_font_size=44,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    value_font_size=38,
    font_family="sans-serif",
)

# pygal has no heatmap type: an empty XY chart supplies the page and title, and the tiles are added to its SVG
chart = pygal.XY(
    width=CANVAS,
    height=CANVAS,
    style=custom_style,
    title=title,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=120,
)
chart.add("", [(0, 0)], show_dots=False, stroke=False)
parts = []  # SVG elements of the tiles, labels and colorbar

matrix = df.to_numpy(dtype=float)
n_rows, n_cols = matrix.shape
min_val, max_val = float(np.nanmin(matrix)), float(np.nanmax(matrix))
# Diverging scale centered on zero, at least the full -1..1 correlation domain
span = max(1.0, float(np.nanmax(np.abs(matrix))))

# Room for the labels around the grid
left, right, top, bottom = 500, 340, 250, 330
available_width = CANVAS - left - right
available_height = CANVAS - top - bottom
cell_width = available_width / n_cols * 0.95
cell_height = available_height / n_rows * 0.95
gap = min(cell_width, cell_height) * 0.03
grid_width = n_cols * (cell_width + gap) - gap
grid_height = n_rows * (cell_height + gap) - gap
x_offset = left + (available_width - grid_width) / 2
y_offset = top + (available_height - grid_height) / 2

# Row labels on the left, column labels below the grid rotated to fit
label_size = min(52, int(cell_height * 0.4))
for i, label in enumerate(df.index.astype(str)):
    y = y_offset + i * (cell_height + gap) + cell_height / 2
    parts.append(svg_text(x_offset - 25, y + label_size * 0.35, label, label_size, INK, "600", "end"))
for j, label in enumerate(df.columns.astype(str)):
    x = x_offset + j * (cell_width + gap) + cell_width / 2
    y = y_offset + n_rows * (cell_height + gap) + 25
    parts.append(svg_text(x, y, label, label_size, INK, "600", rotate=45))

# Cells with the value printed inside, the text switching with the cell's darkness
value_size = min(52, int(min(cell_width, cell_height) * 0.4))
for i in range(n_rows):
    for j in range(n_cols):
        value = float(matrix[i, j])
        color = ramp_color(DIV_FIELDS, (value / span + 1) / 2)
        x = x_offset + j * (cell_width + gap)
        y = y_offset + i * (cell_height + gap)
        parts.append(svg_rect(x, y, cell_width, cell_height, color, PAGE_BG, rx=4))
        if not math.isfinite(value):
            continue
        red, green, blue = (int(color[k : k + 2], 16) for k in (1, 3, 5))
        dark_cell = (red * 299 + green * 587 + blue * 114) / 1000 < 140
        parts.append(
            svg_text(
                x + cell_width / 2,
                y + cell_height / 2 + value_size * 0.35,
                f"{value:.2f}",
                value_size,
                LIGHT_TEXT if dark_cell else DARK_TEXT,
                "bold",
                "middle",
            )
        )

# Colorbar on the right, spanning the data range on the same scale
bar_width = 55
bar_height = grid_height * 0.8
bar_x = x_offset + grid_width + 120
bar_y = y_offset + (grid_height - bar_height) / 2
n_segments = 50
seg_height = bar_height / n_segments
for k in range(n_segments):
    seg_value = max_val - (max_val - min_val) * k / (n_segments - 1)
    seg_color = ramp_color(DIV_FIELDS, (seg_value / span + 1) / 2)
    parts.append(svg_rect(bar_x, bar_y + k * seg_height, bar_width, seg_height + 1, seg_color))
parts.append(svg_rect(bar_x, bar_y, bar_width, bar_height, "none", INK))
tick_size = 40
for frac, tick_value in ((0.0, max_val), (0.5, (min_val + max_val) / 2), (1.0, min_val)):
    tick_y = bar_y + bar_height * frac + tick_size * 0.35
    parts.append(svg_text(bar_x + bar_width + 15, tick_y, f"{tick_value:.2f}", tick_size, INK))
parts.append(svg_text(bar_x + bar_width / 2, bar_y - 35, VALUE, 40, INK, "bold", "middle"))

# Save
chart_svg = chart.render(is_unicode=True).replace("</svg>", f'<g class="annotated-heatmap">{"".join(parts)}</g></svg>')
cairosvg.svg2png(bytestring=chart_svg.encode("utf-8"), write_to=f"plot-{THEME}.png")
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {chart_svg}
    </figure>
</body>
</html>
"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
