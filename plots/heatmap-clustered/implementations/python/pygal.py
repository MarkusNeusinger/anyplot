"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Constants
# Imprint diverging ramp for filled cells: the midpoint is the page color
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's labels
DRUG = "Drug"  # role: row_labels
CELL_LINE = "Cell line"  # role: column_labels
SENSITIVITY = "Sensitivity (log IC50)"  # role: matrix

# Data: replace this block with your own labeled matrix, for example df = pd.read_csv("ic50.csv", index_col=0)
np.random.seed(42)

drugs = [
    "Paclitaxel",
    "Doxorubicin",
    "Cisplatin",
    "Gemcitabine",
    "5-Fluorouracil",
    "Irinotecan",
    "Bortezomib",
    "Sorafenib",
    "Sunitinib",
    "Erlotinib",
    "Gefitinib",
    "Lapatinib",
]
cell_lines = ["A549", "HCT116", "HT29", "MCF7", "MDA231", "OVCAR3", "SKOV3", "SW480", "U87", "KHOS"]

sensitivity = np.zeros((len(drugs), len(cell_lines)))

# Chemotherapy drugs: higher sensitivity (lower IC50) in epithelial-origin lung/colon lines
for i in [0, 1, 2, 3, 4, 5]:
    for j in [0, 1, 2, 7]:
        sensitivity[i, j] = np.random.randn() * 0.6 - 1.2
    for j in [3, 4]:
        sensitivity[i, j] = np.random.randn() * 0.6 + 0.9
    for j in [5, 6, 8, 9]:
        sensitivity[i, j] = np.random.randn() * 0.7

# Targeted drugs: strongest response in the EGFR-mutant lines
for i in [6, 7, 8, 9, 10, 11]:
    for j in [8, 9]:
        sensitivity[i, j] = np.random.randn() * 0.5 - 1.3
    for j in [0, 1, 2, 3]:
        sensitivity[i, j] = np.random.randn() * 0.5 + 0.5
    for j in [4, 5, 6, 7]:
        sensitivity[i, j] = np.random.randn() * 0.6

df = pd.DataFrame(sensitivity, index=pd.Index(drugs, name=DRUG), columns=pd.Index(cell_lines, name=CELL_LINE))

# Plot: reads only df and the constants above
row_dend = dendrogram(linkage(pdist(df.to_numpy()), method="ward"), no_plot=True)
col_dend = dendrogram(linkage(pdist(df.to_numpy().T), method="ward"), no_plot=True)
clustered = df.iloc[row_dend["leaves"], col_dend["leaves"]]
values = clustered.to_numpy()
n_rows, n_cols = values.shape
abs_max = float(np.nanmax(np.abs(values)))

# Layout in data units: one unit is about one pixel of the plot area
cw, ch, gap = 175, 93, 4
mat_w, mat_h = n_cols * cw, n_rows * ch
dend_gap, row_dend_w, col_dend_h = 30, 330, 230
bar_x, bar_w, n_seg = mat_w + dend_gap + row_dend_w + 230, 56, 40
bar_h = mat_h * 0.8
bar_y = (mat_h - bar_h) / 2
x_max, y_max = bar_x + bar_w + 190, mat_h + dend_gap + col_dend_h


def rect(x0, y0, x1, y1):
    """A closed outline: pygal fills it down to the baseline along the shared edge, so it draws a solid box."""
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


chart_series, colors = [], []

# Cells: one filled box per value, page-colored gap between neighbours through the inset
for i in range(n_rows):
    for j in range(n_cols):
        t = (values[i, j] + abs_max) / (2 * abs_max)
        top = mat_h - i * ch
        chart_series.append(
            (
                f"{clustered.index[i]} / {clustered.columns[j]}",
                rect(j * cw + gap / 2, top - ch + gap / 2, (j + 1) * cw - gap / 2, top - gap / 2),
                True,
            )
        )
        colors.append(ramp_color(DIV_FIELDS, t))

# Dendrogram links: leaves at the cell centres, merge height as distance from the matrix
row_top, col_top = max(max(d) for d in row_dend["dcoord"]), max(max(d) for d in col_dend["dcoord"])
for ic, dc in zip(row_dend["icoord"], row_dend["dcoord"], strict=True):
    pts = [
        (mat_w + dend_gap + row_dend_w * d / row_top, mat_h * (1 - c / (n_rows * 10)))
        for c, d in zip(ic, dc, strict=True)
    ]
    chart_series.append(("row merge", pts, False))
    colors.append(INK_SOFT)
for ic, dc in zip(col_dend["icoord"], col_dend["dcoord"], strict=True):
    pts = [
        (mat_w * c / (n_cols * 10), mat_h + dend_gap + col_dend_h * d / col_top) for c, d in zip(ic, dc, strict=True)
    ]
    chart_series.append(("column merge", pts, False))
    colors.append(INK_SOFT)

# Colorbar: stacked boxes along the same ramp, high values on top
for k in range(n_seg):
    y_lo = bar_y + k * bar_h / n_seg
    chart_series.append((f"colorbar {k}", rect(bar_x, y_lo, bar_x + bar_w, y_lo + bar_h / n_seg + 1), True))
    colors.append(ramp_color(DIV_FIELDS, (k + 0.5) / n_seg))

# Texts on the colorbar: ticks beside it, two-line title above it
tick_labels = [
    {"value": (bar_x + bar_w + 20, bar_y + bar_h - dy + 28), "label": f"{tick:+.1f}"}
    for tick, dy in ((abs_max, 0), (0.0, bar_h / 2), (-abs_max, bar_h))
]
bar_titles = [
    {"value": (bar_x - 10, bar_y + bar_h + 150), "label": "Sensitivity"},
    {"value": (bar_x - 10, bar_y + bar_h + 100), "label": "(log IC50)"},
]

title = "heatmap-clustered · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(colors + [INK] * 3),
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=40,
    value_label_font_size=40,
    value_colors=(INK,) * (len(colors) + 3),
    opacity="1",
    opacity_hover="1",
    stroke_width=2.5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=CELL_LINE,
    y_title=DRUG,
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    show_dots=False,
    print_labels=True,
    truncate_label=-1,
    stroke_style={"width": 0.1},
    xrange=(0, x_max),
    range=(0, y_max),
    include_x_axis=False,
    zero=bar_y,
    x_labels=[{"value": (j + 0.5) * cw, "label": str(name)} for j, name in enumerate(clustered.columns)],
    y_labels=[{"value": mat_h - (i + 0.5) * ch, "label": str(name)} for i, name in enumerate(clustered.index)],
    margin=40,
)
for name, points, filled in chart_series:
    if filled:
        chart.add(name, points, fill=True, stroke_style={"width": 0.1})
    else:
        chart.add(name, points, stroke_style={"width": 4, "linecap": "round", "linejoin": "round"})
chart.add("colorbar ticks", tick_labels, stroke=False, show_dots=True, dots_size=0.1)
chart.add("colorbar title", bar_titles, stroke=False, show_dots=True, dots_size=0.1)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
