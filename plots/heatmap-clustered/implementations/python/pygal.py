"""anyplot.ai
heatmap-clustered: Clustered Heatmap
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

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
abs_max = float(np.nanmax(np.abs(clustered.to_numpy())))


class ClusteredHeatmap(Graph):
    """Clustered heatmap drawn straight into pygal's SVG tree, so PNG and HTML share one drawing."""

    def __init__(self, *args, **kwargs):
        self.table = kwargs.pop("table")
        self.row_dend = kwargs.pop("row_dend")
        self.col_dend = kwargs.pop("col_dend")
        self.limit = kwargs.pop("limit")
        self.row_title = kwargs.pop("row_title")
        self.col_title = kwargs.pop("col_title")
        self.bar_title = kwargs.pop("bar_title")
        super().__init__(*args, **kwargs)

    def _text(self, group, x, y, text, size, anchor="start", weight="normal", fill=INK, rotate=False):
        node = self.svg.node(group, "text", x=x, y=y)
        node.set("text-anchor", anchor)
        node.set("style", f"fill:{fill};font-size:{size}px;font-weight:{weight};font-family:sans-serif")
        if rotate:
            node.set("transform", f"rotate(-90, {x}, {y})")
        node.text = text

    def _branches(self, group, dend, x0, y0, width, height, along):
        """Draw dendrogram links; leaves sit at the cell centres, the root at the far side."""
        n_leaves = len(dend["leaves"])
        top = max(max(d) for d in dend["dcoord"])
        for ic, dc in zip(dend["icoord"], dend["dcoord"], strict=True):
            pos = [c / (n_leaves * 10) for c in ic]
            dep = [d / top for d in dc]
            if along == "rows":  # leaves at the right edge, root on the left
                pts = [(x0 + width * (1 - d), y0 + height * p) for p, d in zip(pos, dep, strict=True)]
            else:  # leaves at the bottom edge, root on top
                pts = [(x0 + width * p, y0 + height * (1 - d)) for p, d in zip(pos, dep, strict=True)]
            path = self.svg.node(group, "path")
            path.set("d", "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts))
            path.set("style", f"fill:none;stroke:{INK_SOFT};stroke-width:4;stroke-linecap:round;stroke-linejoin:round")

    def _plot(self):
        values = self.table.to_numpy()
        n_rows, n_cols = values.shape
        group = self.svg.node(self.nodes["plot"], class_="clustered-heatmap")

        full_w, full_h = self.view.width, self.view.height
        left_title, row_dend_w, gap = 70, 260, 14
        col_dend_h = 190
        bottom = 190
        right = 640
        mx = left_title + row_dend_w + gap
        my = col_dend_h + gap
        mw = full_w - mx - right
        mh = full_h - my - bottom
        cw, ch = mw / n_cols, mh / n_rows

        self._branches(group, self.row_dend, left_title, my, row_dend_w, mh, "rows")
        self._branches(group, self.col_dend, mx, 0, mw, col_dend_h, "cols")

        for i in range(n_rows):
            for j in range(n_cols):
                t = (values[i, j] + self.limit) / (2 * self.limit)
                self.svg.node(
                    group,
                    "rect",
                    x=mx + j * cw,
                    y=my + i * ch,
                    width=cw - 2,
                    height=ch - 2,
                    style=f"fill:{ramp_color(DIV_FIELDS, t)};stroke:{PAGE_BG};stroke-width:1",
                )

        for i, label in enumerate(self.table.index):
            self._text(group, mx + mw + 24, my + (i + 0.5) * ch + 15, str(label), 44, weight="600")
        for j, label in enumerate(self.table.columns):
            self._text(group, mx + (j + 0.5) * cw, my + mh + 58, str(label), 40, anchor="middle", weight="600")

        self._text(group, left_title - 20, my + mh / 2, self.row_title, 48, anchor="middle", weight="bold", rotate=True)
        self._text(group, mx + mw / 2, my + mh + 142, self.col_title, 48, anchor="middle", weight="bold")

        bar_x, bar_w, bar_h = mx + mw + 470, 52, mh * 0.8
        bar_y = my + (mh - bar_h) / 2
        n_seg = 80
        for k in range(n_seg):
            self.svg.node(
                group,
                "rect",
                x=bar_x,
                y=bar_y + k * bar_h / n_seg,
                width=bar_w,
                height=bar_h / n_seg + 1,
                style=f"fill:{ramp_color(DIV_FIELDS, 1 - (k + 0.5) / n_seg)}",
            )
        self.svg.node(
            group,
            "rect",
            x=bar_x,
            y=bar_y,
            width=bar_w,
            height=bar_h,
            style=f"fill:none;stroke:{INK_MUTED};stroke-width:2",
        )
        for tick, y in [(self.limit, bar_y), (0.0, bar_y + bar_h / 2), (-self.limit, bar_y + bar_h)]:
            self._text(group, bar_x + bar_w + 14, y + 14, f"{tick:+.1f}", 40)
        self._text(group, bar_x - 130, bar_y - 90, self.bar_title[0], 40, weight="bold")
        self._text(group, bar_x - 130, bar_y - 40, self.bar_title[1], 40, weight="bold")

    def _compute(self):
        self._box.xmin, self._box.xmax = 0, len(self.table.columns)
        self._box.ymin, self._box.ymax = 0, len(self.table.index)


title = "heatmap-clustered · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = ClusteredHeatmap(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    table=clustered,
    row_dend=row_dend,
    col_dend=col_dend,
    limit=abs_max,
    row_title=DRUG,
    col_title=CELL_LINE,
    bar_title=("Sensitivity", "(log IC50)"),
    show_legend=False,
    margin=40,
    show_x_labels=False,
    show_y_labels=False,
)
chart.add("", [0])

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
