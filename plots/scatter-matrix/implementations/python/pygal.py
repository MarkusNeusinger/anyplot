""" anyplot.ai
scatter-matrix: Scatter Plot Matrix
Library: pygal 3.1.3 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.18)" if THEME == "light" else "rgba(240,239,232,0.18)"
BRAND = "#009E73"  # Imprint palette position 1, the single series

# Columns: set these to your table's column names
# The spec's `variables` role is a list of columns: one constant carries the role, the others are extra
SEPAL_LENGTH = "Sepal length (cm)"  # role: variables
SEPAL_WIDTH = "Sepal width (cm)"  # role: extra
PETAL_LENGTH = "Petal length (cm)"  # role: extra
PETAL_WIDTH = "Petal width (cm)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
# Iris-like flower measurements driven by one shared size factor; petals are log-normal, so never negative
np.random.seed(42)
size = np.random.randn(100)
df = pd.DataFrame(
    {
        SEPAL_LENGTH: 5.8 + size * 0.8 + np.random.randn(100) * 0.3,
        SEPAL_WIDTH: 3.0 - size * 0.4 + np.random.randn(100) * 0.25,
        PETAL_LENGTH: 3.7 * np.exp(size * 0.25 + np.random.randn(100) * 0.08),
        PETAL_WIDTH: 1.1 * np.exp(size * 0.33 + np.random.randn(100) * 0.12),
    }
).round(1)

# Plot: one pygal XY chart; each variable is scaled into a unit cell of a square grid
VARIABLES = [SEPAL_LENGTH, SEPAL_WIDTH, PETAL_LENGTH, PETAL_WIDTH]
n = len(VARIABLES)
gap = 0.1  # space between cells, in cell widths
lo, hi, ticks = {}, {}, {}
for column in VARIABLES:
    values = df[column].dropna().astype(float)
    pad = 0.06 * (values.max() - values.min()) or 0.5
    lo[column], hi[column] = values.min() - pad, values.max() + pad
    target_step = (hi[column] - lo[column]) / 3
    magnitude = 10 ** np.floor(np.log10(target_step))
    step = min((m * magnitude for m in (1, 2, 5, 10)), key=lambda candidate: abs(candidate - target_step))
    ticks[column] = np.round(np.arange(np.ceil(lo[column] / step) * step, hi[column], step), 10) + 0.0  # no "-0"
scaled = {column: (df[column].astype(float) - lo[column]) / (hi[column] - lo[column]) for column in VARIABLES}
left = [j * (1 + gap) for j in range(n)]  # x of each column's cell
bottom = [(n - 1 - i) * (1 + gap) for i in range(n)]  # y of each row's cell, row 0 on top

grid, points, bars = [], [], []
for i, row_var in enumerate(VARIABLES):
    for j, col_var in enumerate(VARIABLES):
        x0, y0 = left[j], bottom[i]
        grid += [(x0, y0), (x0 + 1, y0), (x0 + 1, y0 + 1), (x0, y0 + 1), (x0, y0), (None, None)]
        for tick in ticks[col_var]:
            x = x0 + (tick - lo[col_var]) / (hi[col_var] - lo[col_var])
            if 0.01 < x - x0 < 0.99:  # a guide on the frame would double the cell edge
                grid += [(x, y0), (x, y0 + 1), (None, None)]
        if i == j:
            # Diagonal: the variable's histogram as one filled step outline on the cell's floor
            counts, edges = np.histogram(df[col_var].dropna().astype(float), bins="sturges")
            xs = x0 + (edges - lo[col_var]) / (hi[col_var] - lo[col_var])
            heights = y0 + 0.92 * counts / max(counts.max(), 1)
            outline = [(xs[0], y0)]
            for k in range(len(counts)):
                outline += [(xs[k], heights[k]), (xs[k + 1], heights[k])]
            bars += [*outline, (xs[-1], y0), (xs[0], y0), (None, None)]
            continue
        for tick in ticks[row_var]:
            y = y0 + (tick - lo[row_var]) / (hi[row_var] - lo[row_var])
            if 0.01 < y - y0 < 0.99:
                grid += [(x0, y), (x0 + 1, y), (None, None)]
        pair = pd.DataFrame({"x": scaled[col_var], "y": scaled[row_var]}).dropna()
        points += list(zip(x0 + pair["x"], y0 + pair["y"], strict=True))

# Text set as pygal point labels: the label's baseline sits on its point
x_ticks = [
    {"value": (left[j] + (tick - lo[column]) / (hi[column] - lo[column]), -0.11), "label": f"{tick:g}"}
    for j, column in enumerate(VARIABLES)
    for tick in ticks[column]
]
y_ticks = [
    {"value": (-0.04, bottom[i] + (tick - lo[column]) / (hi[column] - lo[column]) - 0.03), "label": f"{tick:g}"}
    for i, column in enumerate(VARIABLES)
    for tick in ticks[column]
]
column_names = [{"value": (left[j] + 0.5, -0.27), "label": column} for j, column in enumerate(VARIABLES)]
row_names = [{"value": (-0.25, bottom[i] + 0.47), "label": column} for i, column in enumerate(VARIABLES)]
name_room = max(len(column) for column in VARIABLES) * 0.06  # cell widths a row name takes at this font size

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    # series order: cell frames and guides, scatter points, histograms, then the four kinds of text
    colors=(RULE, BRAND, BRAND, INK_SOFT, INK_SOFT, INK, INK),
    value_colors=(INK, INK, INK, INK_SOFT, INK_SOFT, INK, INK),
    title_font_size=66,
    label_font_size=40,
    major_label_font_size=40,
    value_font_size=0,
    value_label_font_size=40,
    opacity=0.5,
    opacity_hover=0.8,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=2,
)

chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="scatter-matrix · python · pygal · anyplot.ai",
    xrange=(-0.3 - name_room, n + (n - 1) * gap + 0.02),
    range=(-0.36, n + (n - 1) * gap + 0.02),
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_dots=False,
    allow_interruptions=True,
    print_labels=True,
    margin=40,
    spacing=24,
    css=[
        "file://style.css",
        "file://graph.css",
        "inline:.serie-1 .dot { fill-opacity: 0.65 !important; stroke: none !important; }",
        "inline:.serie-2 .line { fill-opacity: 0.8 !important; stroke-opacity: 0 !important; }",
        "inline:.serie-3 text.label, .serie-5 text.label { text-anchor: middle; }",
        "inline:.serie-4 text.label, .serie-6 text.label { text-anchor: end; }",
        "inline:.serie-5 text.label, .serie-6 text.label { font-weight: bold; }",
    ],
)

chart.add(None, grid)
chart.add(None, points, stroke=False, show_dots=True, dots_size=8)
chart.add(None, bars, fill=True)
for labels in (x_ticks, y_ticks, column_names, row_names):
    chart.add(None, labels, stroke=False, show_dots=True, dots_size=0)

# Save
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
