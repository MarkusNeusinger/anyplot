"""anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
"""

import math
import os
from itertools import pairwise

import cairosvg
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Imprint diverging ramp for fields: red (negative) -> page color (zero) -> blue (positive)
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]
CORRELATION_RANGE = (-1.0, 1.0)  # fixed color range, so the midpoint is always zero
CANVAS = 2400  # square canvas in pixels

# Columns: the matrix is a labeled square, so the descriptor names are its index and columns
DESCRIPTOR = "Molecular Descriptors"  # role: variables
CORRELATION = "Correlation"  # role: correlation_matrix

# Data: replace this block with your own labeled square matrix, e.g. df = pd.read_csv("corr.csv", index_col=0)
# Correlation matrix of molecular descriptors (cheminformatics QSAR feature set)
variables = [
    "Mol. Weight",
    "LogP",
    "TPSA",
    "H-Bond Donors",
    "H-Bond Acceptors",
    "Rotatable Bonds",
    "Aromatic Rings",
    "LogS",
]
df = pd.DataFrame(
    [
        [1.00, 0.45, 0.55, 0.25, 0.60, 0.70, 0.50, -0.55],
        [0.45, 1.00, -0.75, -0.50, -0.35, 0.20, 0.40, -0.80],
        [0.55, -0.75, 1.00, 0.80, 0.85, 0.15, -0.10, 0.50],
        [0.25, -0.50, 0.80, 1.00, 0.45, 0.10, -0.15, 0.40],
        [0.60, -0.35, 0.85, 0.45, 1.00, 0.25, 0.05, 0.35],
        [0.70, 0.20, 0.15, 0.10, 0.25, 1.00, -0.20, -0.15],
        [0.50, 0.40, -0.10, -0.15, 0.05, -0.20, 1.00, -0.35],
        [-0.55, -0.80, 0.50, 0.40, 0.35, -0.15, -0.35, 1.00],
    ],
    index=variables,
    columns=variables,
)


# Plot: reads only df and the constants above
def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"  # a missing value draws nothing
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def cell_color(value):
    """Diverging fill for a correlation value on the fixed -1..1 range."""
    lo, hi = CORRELATION_RANGE
    return ramp_color(DIV_FIELDS, (value - lo) / (hi - lo))


def text_color_on(bg_color):
    """Dark or light text, whichever contrasts with the fill."""
    if bg_color == "none":
        return INK
    r, g, b = (int(bg_color[i : i + 2], 16) for i in (1, 3, 5))
    return "#FAF8F1" if (r * 299 + g * 587 + b * 114) / 1000 < 140 else "#1A1A17"


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=72,
    legend_font_size=48,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    label_font_size=50,
    major_label_font_size=50,
    value_font_size=44,
    font_family="sans-serif",
)

# pygal has no heatmap type: an empty chart supplies the page and title, the grid is added to its SVG tree
chart = pygal.XY(
    width=CANVAS,
    height=CANVAS,
    style=custom_style,
    title="heatmap-correlation · python · pygal · anyplot.ai",
    show_legend=False,
    dots_size=0,
    margin=0,
    margin_top=60,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
)
chart.add("", [(0, 0)])
overlay = []  # SVG fragments for the grid, spliced into the rendered chart


def add_rect(x, y, width, height, fill, stroke="none", stroke_width=0, radius=0):
    overlay.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" rx="{radius}" ry="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def add_text(x, y, text, size, fill, bold=False, anchor="start", rotate=None):
    weight = "font-weight:bold;" if bold else ""
    turn = f' transform="rotate({rotate}, {x:.2f}, {y:.2f})"' if rotate is not None else ""
    text = text.replace("&", "&amp;").replace("<", "&lt;")
    overlay.append(
        f'<text x="{x:.2f}" y="{y:.2f}" fill="{fill}" text-anchor="{anchor}"{turn} '
        f'style="font-size:{size}px;{weight}font-family:sans-serif">{text}</text>'
    )


n = len(df)
names = [str(name) for name in df.index]
longest = max(len(name) for name in names)
label_size = 46
value_size = 48
row_label_width = longest * label_size * 0.62
col_label_drop = longest * label_size * 0.58 * 0.7071
title_block = 80

left = title_block + row_label_width + 60
right = 380
top = 190
bottom = 25 + col_label_drop + title_block + 50
available_width = CANVAS - left - right
available_height = CANVAS - top - bottom
cell = min(available_width, available_height) / n
gap = cell * 0.02
grid = n * (cell + gap) - gap
x0 = left + (available_width - grid) / 2
y0 = top + (available_height - grid) / 2

# Cells with their values
for i in range(n):
    for j in range(n):
        value = df.iat[i, j]
        fill = cell_color(value)
        x, y = x0 + j * (cell + gap), y0 + i * (cell + gap)
        add_rect(x, y, cell, cell, fill, PAGE_BG, 2, 4)
        if math.isfinite(value):
            add_text(
                x + cell / 2,
                y + cell / 2 + value_size * 0.35,
                f"{value:.2f}",
                value_size,
                text_color_on(fill),
                True,
                "middle",
            )

# Axis titles, row labels and 45-degree column labels, same names in the same order
add_text(title_block / 2 + 20, y0 + grid / 2, DESCRIPTOR, 52, INK, True, "middle", -90)
col_label_y = y0 + grid + 25
add_text(x0 + grid / 2, col_label_y + col_label_drop + 60, DESCRIPTOR, 52, INK, True, "middle")
for i, name in enumerate(names):
    add_text(x0 - 25, y0 + i * (cell + gap) + cell / 2 + label_size * 0.35, name, label_size, INK_SOFT, True, "end")
    add_text(x0 + i * (cell + gap) + cell / 2, col_label_y, name, label_size, INK_SOFT, True, "start", 45)

# Color bar fixed to the full -1..1 range, top = +1
bar_w, bar_h = 55, grid * 0.8
bar_x, bar_y = x0 + grid + 50, y0 + (grid - bar_h) / 2
segments = 60
for k in range(segments):
    value = CORRELATION_RANGE[1] - (CORRELATION_RANGE[1] - CORRELATION_RANGE[0]) * k / (segments - 1)
    add_rect(bar_x, bar_y + k * bar_h / segments, bar_w, bar_h / segments + 1, cell_color(value))
add_rect(bar_x, bar_y, bar_w, bar_h, "none", INK_SOFT, 1)
for frac, tick in ((0.0, "+1.00"), (0.5, " 0.00"), (1.0, "-1.00")):
    add_text(bar_x + bar_w + 15, bar_y + bar_h * frac + 14, tick, 40, INK_SOFT)
add_text(bar_x - 10, bar_y - 40, CORRELATION, 46, INK, True, "start")

# Save
svg_bytes = chart.render().replace(b"</svg>", "".join(overlay).encode("utf-8") + b"</svg>")
with open(f"plot-{THEME}.svg", "wb") as f:
    f.write(svg_bytes)
cairosvg.svg2png(bytestring=svg_bytes, write_to=f"plot-{THEME}.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-correlation - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_bytes.decode("utf-8")}
    </figure>
</body>
</html>
"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
